"""Check the routed parts (tubes, thermistor cable): length, bends, gaps, overlaps.

The routes are read from the `tubes` list in hardware/v6/partcad.yaml, so edit
them there and run this again. Needs a Python with CadQuery.

    python hardware/tools/check_tubes.py
        Length, tightest bend and tube-to-tube gaps. Takes seconds.

    python hardware/tools/check_tubes.py --step microlab.step --cache <dir>
        Also builds each tube with parts/silicone-tube.py and measures its
        exact overlap with every part its path comes near. The STEP is an
        export of the microlab assembly; --cache keeps one BREP per part so
        that later runs skip the slow STEP read.

    ... --move 1/2=0,50,0
        Shift the parts under a tree path first, to try a new unit position
        without exporting again.

    ... --only tube-heat-pump-to-coil
        Check some tubes only. An overlap with a peristaltic pump takes about
        8 minutes to measure, so run tubes in separate processes.

Parts placed directly in the exported assembly (tree paths like 1/5) are the
tubes of the previous export and are skipped; --skip adds more.
"""

import argparse
import ast
import itertools
import re
import sys
import time
from pathlib import Path

import cadquery as cq
from cadquery import cqgi
from OCP.BRep import BRep_Builder
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.BRepLProp import BRepLProp_CLProps
from OCP.BRepTools import BRepTools
from OCP.gp import gp_Trsf, gp_Vec
from OCP.TopLoc import TopLoc_Location
from OCP.TopoDS import TopoDS_Shape

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_overlaps  # noqa: E402

V6 = Path(__file__).resolve().parents[1] / "v6"
SCRIPT = V6 / "parts" / "silicone-tube.py"
SLEEVE_BORE = 6.4
MIN_VOLUME = check_overlaps.DEFAULT_MIN_VOLUME


def read_routes():
    """Return {part name: script parameters} from the `tubes` list in partcad.yaml."""
    text = (V6 / "partcad.yaml").read_text(encoding="utf-8")
    rows = ast.literal_eval(re.search(r"\{% set tubes = (\[.*?\]) %\}", text, re.S).group(1))
    return {
        name: dict(tube_od=float(od), tube_id=float(inner), points=points,
                   start_sleeve=float(start), end_sleeve=float(end))
        for name, _part_id, od, inner, start, end, points in rows
    }


def centreline(points):
    """The two straight ends and the spline between them, as the part script draws them."""
    route = [cq.Vector(*[float(v) for v in p.split(",")]) for p in points.split(";") if p.strip()]
    start_dir = (route[1] - route[0]).normalized()
    end_dir = (route[-1] - route[-2]).normalized()
    spline = cq.Edge.makeSpline(route[1:-1], tangents=[start_dir, end_dir], scale=False)
    return route, spline


def samples(route, spline, step=1.0):
    pts = []
    for a, b in ((route[0], route[1]), (route[-2], route[-1])):
        n = max(2, int((b - a).Length / step))
        pts += [a + (b - a) * (i / n) for i in range(n + 1)]
    n = max(2, int(spline.Length() / step))
    return pts + [spline.positionAt(i / n) for i in range(n + 1)]


def tightest_bend(spline):
    curve = BRepAdaptor_Curve(spline.wrapped)
    first, last = curve.FirstParameter(), curve.LastParameter()
    worst = (float("inf"), None)
    for i in range(401):
        props = BRepLProp_CLProps(curve, first + (last - first) * i / 400.0, 2, 1e-6)
        k = props.Curvature()
        if k > 1e-9 and 1 / k < worst[0]:
            worst = (1 / k, props.Value())
    return worst


def outer_radius(params):
    radius = params["tube_od"] / 2
    if params["start_sleeve"] or params["end_sleeve"]:
        radius += (SLEEVE_BORE - params["tube_id"]) / 2
    return radius


def load_parts(step, cache):
    """Return {tree path: shape}, from the cache when it has been filled."""
    if cache and any(cache.glob("*.brep")):
        parts = {}
        for f in cache.glob("*.brep"):
            shape = TopoDS_Shape()
            BRepTools.Read_s(shape, str(f), BRep_Builder())
            parts[f.stem.replace("_", "/")] = shape
        return parts
    if not step:
        sys.exit("the cache is empty; pass --step to fill it")
    parts = check_overlaps.read_parts(step)
    if cache:
        cache.mkdir(parents=True, exist_ok=True)
        for key, shape in parts.items():
            BRepTools.Write_s(shape, str(cache / (key.replace("/", "_") + ".brep")))
    return parts


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--step", help="STEP export of the microlab assembly")
    parser.add_argument("--cache", type=Path, help="directory of per-part BREP files")
    parser.add_argument("--move", action="append", default=[], metavar="PATH=DX,DY,DZ", help="shift the parts under a tree path")
    parser.add_argument("--skip", nargs="+", default=[], help="tree paths to leave out")
    parser.add_argument("--only", nargs="+", default=[], help="tube names to check")
    args = parser.parse_args()

    routes = read_routes()
    unknown = [name for name in args.only if name not in routes]
    if unknown:
        sys.exit("no such tube: %s (have %s)" % (", ".join(unknown), ", ".join(routes)))
    chosen = {name: p for name, p in routes.items() if not args.only or name in args.only}
    status = 0

    lines = {}
    for name, params in routes.items():
        route, spline = centreline(params["points"])
        lines[name] = samples(route, spline)
        if name in chosen:
            length = (route[1] - route[0]).Length + (route[-1] - route[-2]).Length + spline.Length()
            radius, at = tightest_bend(spline)
            print("%-20s length %4.0f mm, tightest bend %3.0f mm at (%.0f, %.0f, %.0f)"
                  % (name, length, radius, at.X(), at.Y(), at.Z()))
            if radius < params["tube_od"]:
                print("   KINK: bend radius under the tube's diameter")
                status = 1

    print("tube-to-tube gaps under 10 mm:")
    for a, b in itertools.combinations(routes, 2):
        if a not in chosen and b not in chosen:
            continue
        distance, _, p = min(((p - q).Length, i, p) for i, p in enumerate(lines[a]) for q in lines[b])
        gap = distance - outer_radius(routes[a]) - outer_radius(routes[b])
        if gap < 10:
            print("   %-20s x %-20s %5.1f mm near (%.0f, %.0f, %.0f)%s"
                  % (a, b, gap, p.x, p.y, p.z, "  CLASH" if gap < 0.1 else ""))
            if gap < 0.1:
                status = 1

    if not (args.step or args.cache):
        return status

    parts = load_parts(args.step, args.cache)
    for move in args.move:
        prefix, delta = move.split("=")
        trsf = gp_Trsf()
        trsf.SetTranslation(gp_Vec(*[float(v) for v in delta.split(",")]))
        for key in parts:
            if key == prefix or key.startswith(prefix + "/"):
                parts[key] = parts[key].Moved(TopLoc_Location(trsf))
    skipped = [k for k in parts if k.count("/") == 1 or any(k == s or k.startswith(s + "/") for s in args.skip)]
    boxes = {k: check_overlaps.bounding_box(s) for k, s in parts.items() if k not in skipped}
    print("%d parts, %d skipped" % (len(parts), len(skipped)))

    model = cqgi.parse(SCRIPT.read_text(encoding="utf-8"))
    for name, params in chosen.items():
        result = model.build(build_parameters=params)
        if not result.success:
            print("%s: BUILD FAILED: %s" % (name, result.exception))
            status = 1
            continue
        tube = result.results[0].shape.val().wrapped
        margin = outer_radius(params) + 1.0
        near = [
            key for key, b in boxes.items()
            if any(b[0] - margin <= p.x <= b[3] + margin and b[1] - margin <= p.y <= b[4] + margin
                   and b[2] - margin <= p.z <= b[5] + margin for p in lines[name])
        ]
        print("%s: %d parts near its path" % (name, len(near)), flush=True)
        for key in near:
            started = time.time()
            volume = check_overlaps.overlap_volume(tube, parts[key])
            bad = volume < 0 or volume > MIN_VOLUME
            print("   %-10s %s %8.2f mm^3 (%.0f s)" % (key, "OVERLAP" if bad else "ok", volume, time.time() - started), flush=True)
            status = status or int(bad)
    return status


if __name__ == "__main__":
    code = main()
    sys.stdout.flush()
    # OCP can crash while the interpreter tears down large shapes.
    import os
    os._exit(code)
