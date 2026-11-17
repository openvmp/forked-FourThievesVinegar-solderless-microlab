"""Panel-mount USB-A extension socket (CU-USB), an approximation.

Frame: origin at the centre of the wall's window, on the wall's inner face.
+Y points out through the wall, which is 4 mm thick. The flange sits inside the
case, as in docs/media/control-unit/case_assembled.jpeg.

Where the values come from:
- Window 16 x 8 mm and ear holes 30 mm apart: the control box's cut-outs,
  measured from its STEP.
- Flange 38 x 11.8 x 4 mm and a 12 mm cable boot are guessed from the photos.
  The cable itself is left out.
- USB-A receptacle (docs/media/control-unit/cu_case_side.jpeg), sizes from
  the dimensions table of https://en.wikipedia.org/wiki/USB_hardware:
  opening 12.5 x 5.12 mm, 8.88 mm deep. Its plastic tongue sits "above the
  center", the "plastic rectangle at the top" of
  docs/assembly-control-unit.md. The tongue (11 x 1.85 mm, ending 1 mm inside
  the opening) is sized to fit inside a 12.0 x 4.5 mm plug shell with
  0.3 mm walls; it is derived, not sourced.
- Four contacts on the tongue's underside, 1 mm wide at x = -3.5, -1.0, 1.0
  and 3.5 mm: positions recalled from the USB-A layout, NOT verified.
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

receptacle_width = 12.5
receptacle_height = 5.12
receptacle_depth = 8.88
tongue_width = 11.0
tongue_bottom = 0.0
tongue_top = 1.85
tongue_recess = 1.0
contact_width = 1.0
contact_thickness = 0.15

back = wall - receptacle_depth
part = part.cut(block(
    -receptacle_width / 2, receptacle_width / 2,
    back, wall + 0.1,
    -receptacle_height / 2, receptacle_height / 2,
))
part = part.union(block(
    -tongue_width / 2, tongue_width / 2,
    back, wall - tongue_recess,
    tongue_bottom, tongue_top,
))
for x in (-3.5, -1.0, 1.0, 3.5):  # contact centres
    part = part.union(block(
        x - contact_width / 2, x + contact_width / 2,
        back + 1.0, wall - tongue_recess - 0.3,
        tongue_bottom - contact_thickness, tongue_bottom,
    ))

show_object(part)
