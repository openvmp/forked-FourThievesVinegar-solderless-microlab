"""List features of a STEP file, to find where things attach.

Prints the cylindrical faces in a radius range (nozzles, holes, tube stubs)
with their axis and extent, and optionally every face within a height band.
Needs a Python with CadQuery's OCP.

    python hardware/tools/step_features.py pump.step --radius 0.9 6
        A part's own STEP file, in the part's frame.

    python hardware/tools/step_features.py microlab.step --parts 1/4/2/17 --radius 0.9 1.1
        Parts of an assembly export, in the assembly's frame.

    python hardware/tools/step_features.py pump.step --band 61.5 80
        Solids, and every face between two Z heights.
"""

import argparse
import sys
from pathlib import Path

from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import GeomAbs_Cylinder
from OCP.STEPControl import STEPControl_Reader
from OCP.TopAbs import TopAbs_FACE, TopAbs_REVERSED, TopAbs_SOLID
from OCP.TopExp import TopExp_Explorer
from OCP.TopoDS import TopoDS

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_overlaps  # noqa: E402

SURFACES = {0: "plane", 1: "cylinder", 2: "cone", 3: "sphere", 4: "torus"}


def extent(shape):
    b = check_overlaps.bounding_box(shape)
    return "x[%.1f, %.1f] y[%.1f, %.1f] z[%.1f, %.1f]" % (b[0], b[3], b[1], b[4], b[2], b[5])


def faces(shape):
    explorer = TopExp_Explorer(shape, TopAbs_FACE)
    while explorer.More():
        yield TopoDS.Face_s(explorer.Current())
        explorer.Next()


def cylinders(shape, rmin, rmax):
    seen = set()
    rows = []
    for face in faces(shape):
        surface = BRepAdaptor_Surface(face)
        if surface.GetType() != GeomAbs_Cylinder:
            continue
        cylinder = surface.Cylinder()
        radius = cylinder.Radius()
        if not rmin <= radius <= rmax:
            continue
        d = cylinder.Axis().Direction()
        kind = "hole" if face.Orientation() == TopAbs_REVERSED else "boss"
        row = "r=%.2f axis=(%.2f, %.2f, %.2f) %s %s" % (radius, d.X(), d.Y(), d.Z(), kind, extent(face))
        if row not in seen:
            seen.add(row)
            rows.append((radius, row))
    for _, row in sorted(rows):
        print("  " + row)


def band(shape, zmin, zmax):
    explorer = TopExp_Explorer(shape, TopAbs_SOLID)
    while explorer.More():
        print("  solid " + extent(explorer.Current()))
        explorer.Next()
    rows = set()
    for face in faces(shape):
        b = check_overlaps.bounding_box(face)
        if b[2] >= zmin - 0.01 and b[5] <= zmax + 0.01:
            kind = SURFACES.get(int(BRepAdaptor_Surface(face).GetType()), "other")
            rows.add("%-8s %s" % (kind, extent(face)))
    for row in sorted(rows):
        print("  " + row)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("step", help="STEP file")
    parser.add_argument("--parts", nargs="+", help="tree paths in an assembly export, e.g. 1/4/2/17")
    parser.add_argument("--radius", nargs=2, type=float, metavar=("MIN", "MAX"), help="list cylinders in this radius range")
    parser.add_argument("--band", nargs=2, type=float, metavar=("ZMIN", "ZMAX"), help="list faces between these heights")
    args = parser.parse_args()
    if not (args.radius or args.band):
        parser.error("pass --radius, --band or both")

    if args.parts:
        placed = check_overlaps.read_parts(args.step)
        shapes = {key: placed[key] for key in args.parts}
    else:
        reader = STEPControl_Reader()
        reader.ReadFile(args.step)
        reader.TransferRoots()
        shapes = {Path(args.step).name: reader.OneShape()}

    for name, shape in shapes.items():
        print("%s: %s" % (name, extent(shape)))
        if args.radius:
            cylinders(shape, *args.radius)
        if args.band:
            band(shape, *args.band)


if __name__ == "__main__":
    main()
