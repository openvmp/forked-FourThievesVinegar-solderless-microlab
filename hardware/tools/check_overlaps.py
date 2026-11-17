"""Check a PartCAD assembly for overlapping parts, cheapest checks first.

1. Export the placed assembly to STEP and compare every pair's bounding box.
   Pairs whose boxes don't meet can't overlap.
2. Measure exact overlap volumes for the candidate pairs that involve --parts.
3. With --full: measure all candidate pairs, then run
   `pc qual test --assembly -f interference` as the final gate.

Run it with a Python that has CadQuery's OCP, from anywhere in the repo:

    python hardware/tools/check_overlaps.py reactor-unit --list
    python hardware/tools/check_overlaps.py reactor-unit --parts 1/3/16 1/3/17
    python hardware/tools/check_overlaps.py heating-unit --full

The STEP export loses instance names, so parts are identified by their
position in the assembly tree (e.g. 1/3/16). The order follows the links
in the .assy files; use --list to see each part's bounding box.

Every measured pair's time and volume are kept in .timings/<assembly>.json
next to this script. A pair whose part changed since (another face count or
box size) is measured again. To leave out pairs that were slow before:

    python hardware/tools/check_overlaps.py microlab --full --skip-slower 60

Skipped pairs are listed with their last time and volume; they are not
measured, so a change that touches them goes unnoticed. --slowest prints the
recorded times without measuring anything.
"""

import argparse
import itertools
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from OCP.Bnd import Bnd_Box
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TCollection import TCollection_ExtendedString
from OCP.TopAbs import TopAbs_FACE
from OCP.TDF import TDF_Label, TDF_LabelSequence
from OCP.TDocStd import TDocStd_Document
from OCP.TopExp import TopExp_Explorer
from OCP.TopLoc import TopLoc_Location
from OCP.TopTools import TopTools_ListOfShape
from OCP.XCAFDoc import XCAFDoc_DocumentTool

REPO_ROOT = Path(__file__).resolve().parents[2]

# PartCAD's interference test uses the same floor to absorb boolean noise.
DEFAULT_MIN_VOLUME = 0.05
# mm; the smallest value that found the overlaps pc qual test reports.
FUZZY = 0.001
TIMINGS_DIR = Path(__file__).resolve().parent / ".timings"
# Seconds; a pair this slow is printed as it finishes.
SLOW = 10.0


def export_step(pc, package, assembly, out_dir):
    subprocess.run(
        [pc, "--no-ansi", "export", "-a", "-t", "step", "-O", str(out_dir), f"{package}:{assembly}"],
        cwd=REPO_ROOT,
        check=True,
    )
    return Path(out_dir) / f"{assembly}.step"


def read_parts(step_path):
    """Return {tree path: placed shape} for every leaf part in the STEP file."""
    doc = TDocStd_Document(TCollection_ExtendedString("doc"))
    reader = STEPCAFControl_Reader()
    reader.ReadFile(str(step_path))
    reader.Transfer(doc)
    tool = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    parts = {}

    def walk(label, location, path):
        if tool.IsAssembly_s(label):
            components = TDF_LabelSequence()
            tool.GetComponents_s(label, components)
            for i in range(1, components.Length() + 1):
                component = components.Value(i)
                referred = TDF_Label()
                tool.GetReferredShape_s(component, referred)
                walk(referred, location * tool.GetLocation_s(component), path + [str(i)])
        else:
            parts["/".join(path)] = tool.GetShape_s(label).Moved(location)

    roots = TDF_LabelSequence()
    tool.GetFreeShapes(roots)
    for i in range(1, roots.Length() + 1):
        walk(roots.Value(i), TopLoc_Location(), [str(i)])
    return dict(sorted(parts.items(), key=lambda item: [int(p) for p in item[0].split("/")]))


def bounding_box(shape):
    box = Bnd_Box()
    BRepBndLib.Add_s(shape, box)
    return box.Get()


def boxes_meet(a, b):
    return not (a[0] > b[3] or b[0] > a[3] or a[1] > b[4] or b[1] > a[4] or a[2] > b[5] or b[2] > a[5])


def _common_volume(a, b, fuzzy):
    """Volume of the boolean common, or None if it fails or comes out invalid."""
    first, second = TopTools_ListOfShape(), TopTools_ListOfShape()
    first.Append(a)
    second.Append(b)
    common = BRepAlgoAPI_Common()
    common.SetArguments(first)
    common.SetTools(second)
    if fuzzy:
        common.SetFuzzyValue(fuzzy)
    common.Build()
    if not common.IsDone():
        return None
    props = GProp_GProps()
    BRepGProp.VolumeProperties_s(common.Shape(), props)
    volume = props.Mass()
    return volume if volume >= 0 else None


def overlap_volume(a, b):
    """Volume two shapes share, or -1 if no boolean gives a valid answer.

    Without a fuzzy value OCC can return an empty result for a real overlap
    (a threaded screw off-centre in a hole), which reads as no overlap. With
    one, faces that touch can give a negative volume (the reactor core's jar
    on its flange); then the plain boolean answers.
    """
    volume = _common_volume(a, b, FUZZY)
    if volume is None:
        volume = _common_volume(a, b, 0.0)
    return -1.0 if volume is None else volume


def fingerprint(shape, box):
    """Face count and box size: what changes when a part's model changes."""
    faces = 0
    explorer = TopExp_Explorer(shape, TopAbs_FACE)
    while explorer.More():
        faces += 1
        explorer.Next()
    return "%d faces %.1f x %.1f x %.1f" % (faces, box[3] - box[0], box[4] - box[1], box[5] - box[2])


def load_timings(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_timings(path, timings):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(timings, indent=1, sort_keys=True), encoding="utf-8")


def recorded(timings, a, b, prints):
    """The pair's last measurement, if neither part has changed since."""
    entry = timings.get("%s x %s" % (a, b))
    if entry and entry["a"] == prints[a] and entry["b"] == prints[b]:
        return entry
    return None


def involves(key, prefixes):
    return any(key == p or key.startswith(p + "/") for p in prefixes)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("assembly", help="assembly name in the package, e.g. reactor-unit")
    parser.add_argument("--package", default="v6", help="PartCAD package (default: v6)")
    parser.add_argument("--step", help="use an existing STEP export instead of exporting")
    parser.add_argument("--parts", nargs="+", default=[], help="tree paths to check exactly, e.g. 1/3/16")
    parser.add_argument("--full", action="store_true", help="check all candidate pairs and run pc qual test")
    parser.add_argument("--list", action="store_true", help="print every part's bounding box")
    parser.add_argument("--min-volume", type=float, default=DEFAULT_MIN_VOLUME, help="mm^3 below which an overlap is noise")
    parser.add_argument("--pc", default="pc", help="PartCAD command (default: pc)")
    parser.add_argument("--skip-slower", type=float, metavar="SECONDS", help="skip pairs that took longer than this last time")
    parser.add_argument("--slowest", type=int, nargs="?", const=20, metavar="N", help="print the N slowest recorded pairs and stop")
    parser.add_argument("--timings", type=Path, help="timings file (default: .timings/<assembly>.json here)")
    args = parser.parse_args()
    timings_path = args.timings or TIMINGS_DIR / ("%s.json" % args.assembly)
    timings = load_timings(timings_path)

    if args.slowest:
        rows = sorted(timings.items(), key=lambda item: -item[1]["seconds"])[: args.slowest]
        if not rows:
            print("no timings recorded in %s" % timings_path)
        for key, entry in rows:
            print("%7.1f s  %-24s %7.2f mm^3  (%s)" % (entry["seconds"], key, entry["volume"], entry["when"]))
        return 0

    with tempfile.TemporaryDirectory() as tmp:
        step = Path(args.step) if args.step else export_step(args.pc, args.package, args.assembly, tmp)
        parts = read_parts(step)

    boxes = {key: bounding_box(shape) for key, shape in parts.items()}
    if args.list:
        for key, b in boxes.items():
            print("%-14s x[%8.1f, %8.1f] y[%8.1f, %8.1f] z[%8.1f, %8.1f]" % (key, b[0], b[3], b[1], b[4], b[2], b[5]))

    candidates = [(a, b) for a, b in itertools.combinations(parts, 2) if boxes_meet(boxes[a], boxes[b])]
    print("tier 1: %d parts, %d of %d pairs have touching bounding boxes"
          % (len(parts), len(candidates), len(parts) * (len(parts) - 1) // 2))

    if args.full:
        pairs = candidates
    else:
        pairs = [(a, b) for a, b in candidates if involves(a, args.parts) or involves(b, args.parts)]
    if not pairs:
        print("tier 2: nothing to measure; pass --parts or --full")
        return 0

    involved = {key for pair in pairs for key in pair}
    prints = {key: fingerprint(parts[key], boxes[key]) for key in involved}
    skipped = []
    if args.skip_slower is not None:
        for a, b in pairs:
            entry = recorded(timings, a, b, prints)
            if entry and entry["seconds"] > args.skip_slower:
                skipped.append((a, b, entry))
        pairs = [(a, b) for a, b in pairs if (a, b) not in {(s[0], s[1]) for s in skipped}]

    print("tier %d: measuring %d candidate pairs" % (3 if args.full else 2, len(pairs)), flush=True)
    found = 0
    started = time.time()
    this_run = []
    for i, (a, b) in enumerate(pairs, 1):
        t0 = time.time()
        volume = overlap_volume(parts[a], parts[b])
        seconds = time.time() - t0
        this_run.append((seconds, a, b))
        timings["%s x %s" % (a, b)] = {
            "a": prints[a], "b": prints[b], "seconds": round(seconds, 1),
            "volume": round(volume, 3), "when": time.strftime("%Y-%m-%d"),
        }
        if volume < 0:
            found += 1
            print("  FAILED  %s x %s: no boolean gave a valid volume" % (a, b), flush=True)
        elif volume > args.min_volume:
            found += 1
            print("  overlap %s x %s: %.2f mm^3" % (a, b, volume), flush=True)
        if seconds >= SLOW:
            print("  slow    %s x %s: %.0f s" % (a, b, seconds), flush=True)
            save_timings(timings_path, timings)
        if i % 25 == 0:
            print("  ... %d of %d pairs, %.0f min" % (i, len(pairs), (time.time() - started) / 60), flush=True)
    save_timings(timings_path, timings)
    print("  %d overlapping pairs, %.0f min" % (found, (time.time() - started) / 60))
    if this_run:
        print("  slowest this run: " + ", ".join("%s x %s %.0f s" % (a, b, s) for s, a, b in sorted(this_run, reverse=True)[:5]))
    if skipped:
        overlapped = sum(1 for _, _, entry in skipped if entry["volume"] > args.min_volume)
        print("  %d pairs skipped as slower than %g s last time, not measured (%d overlapped then):"
              % (len(skipped), args.skip_slower, overlapped))
        for a, b, entry in skipped:
            mark = "  overlap" if entry["volume"] > args.min_volume else ""
            print("    %s x %s: %.0f s, %.2f mm^3 on %s%s" % (a, b, entry["seconds"], entry["volume"], entry["when"], mark))

    status = 1 if found else 0
    if args.full:
        print("tier 3: pc qual test --assembly -f interference %s:%s" % (args.package, args.assembly))
        test = subprocess.run(
            [args.pc, "--no-ansi", "qual", "test", "--assembly", "-f", "interference", f"{args.package}:{args.assembly}"],
            cwd=REPO_ROOT,
        )
        status = status or test.returncode
    return status


if __name__ == "__main__":
    sys.exit(main())
