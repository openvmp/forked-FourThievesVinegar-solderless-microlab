"""Panel-mount 5.5 x 2.1 mm DC barrel jack with its nut (CU-PLG), an approximation.

Frame: origin at the centre of the wall's hole, on the wall's inner face.
+Y points out through the wall, which is 4 mm thick.

Where the values come from:
- 11 mm hole: the control box's cut-out, measured from its STEP. A DC-022 style
  jack has a 10.9 mm thread.
- Flange 13 x 2 mm, nut 14 mm across flats x 3 mm, body 14 mm deep inside:
  generic DC-022 sizes (guessed).
"""
import cadquery as cq

if "show_object" not in globals():
    def show_object(*args, **kwargs):
        pass

wall = 4.0


def rod(diameter, y0, y1):
    return cq.Workplane("XZ").circle(diameter / 2).extrude(-(y1 - y0)).translate((0, y0, 0))


part = rod(10.9, -14.0, wall)
part = part.union(rod(13.0, wall, wall + 2.0))
# Flats facing +-X, so the nut is 14 mm wide along the wall.
nut = (
    cq.Workplane("XZ")
    .polygon(6, 14.0 / 0.866)
    .extrude(-3.0)
    .rotate((0, 0, 0), (0, 1, 0), 30)
    .translate((0, -3.0, 0))
)
part = part.union(nut)

show_object(part)
