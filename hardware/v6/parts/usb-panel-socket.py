"""Panel-mount USB-A extension socket (CU-USB), an approximation.

Frame: origin at the centre of the wall's window, on the wall's inner face.
+Y points out through the wall, which is 4 mm thick. The flange sits inside the
case, as in docs/media/control-unit/case_assembled.jpeg.

Where the values come from:
- Window 16 x 8 mm and ear holes 30 mm apart: the control box's cut-outs,
  measured from its STEP.
- Flange 38 x 11.8 x 4 mm and a 12 mm cable boot are guessed from the photos.
  The cable itself is left out.
"""
import cadquery as cq

if "show_object" not in globals():
    def show_object(*args, **kwargs):
        pass

wall = 4.0
hole_spacing = 30.0
hole_diameter = 3.4


def block(x0, x1, y0, y1, z0, z1):
    return (
        cq.Workplane("XY")
        .box(x1 - x0, y1 - y0, z1 - z0, centered=False)
        .translate((x0, y0, z0))
    )


part = block(-7.9, 7.9, 0.0, wall, -3.9, 3.9)
flange = block(-19.0, 19.0, -4.0, 0.0, -5.9, 5.9)
for x in (-hole_spacing / 2, hole_spacing / 2):
    hole = (
        cq.Workplane("XZ")
        .center(x, 0)
        .circle(hole_diameter / 2)
        .extrude(4.2)
        .translate((0, 0.1, 0))
    )
    flange = flange.cut(hole)
part = part.union(flange)
part = part.union(block(-7.0, 7.0, -16.0, -4.0, -4.0, 4.0))

show_object(part)
