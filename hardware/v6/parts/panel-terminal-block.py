"""Panel-mount pluggable terminal block (SP-PC12, SP-PC8, SP-PC2), an approximation.

The docs' connector has three pieces: a mount plate screwed to the outside of
the case, a socket with screw terminals plugged into it from inside, and a
plug for the cable outside. The plug belongs to the cable and is left out.

Frame: origin at the centre of the wall's window, on the wall's inner face.
+Y points out through the wall, which is `wall` mm thick.

Where the values come from:
- Window, screw hole spacing and hole height (above the window's bottom
  edge): the control box's cut-outs, measured from its STEP (passed in as
  parameters).
- Pitch 3.81 mm: the 8- and 12-pin cut-outs both fit n x 3.81 mm plus a fixed
  margin, which points to 3.81 mm pluggable blocks.
- Plate thickness, socket depth and widths are guessed from the photos.
"""
import cadquery as cq

if "show_object" not in globals():
    def show_object(*args, **kwargs):
        pass

pins = 8
pitch = 3.81
window_width = 41.5
window_height = 12.5
hole_spacing = 47.0
hole_height = 4.85
wall = 4.0

plate_thickness = 2.5
socket_depth = 14.0
clearance = 0.1
hole_diameter = 3.4


def block(x0, x1, y0, y1, z0, z1):
    return (
        cq.Workplane("XY")
        .box(x1 - x0, y1 - y0, z1 - z0, centered=False)
        .translate((x0, y0, z0))
    )


hole_dz = hole_height - window_height / 2
half_w = window_width / 2 - clearance
half_h = window_height / 2 - clearance
# Header body filling the window, flush with the outer face.
part = block(-half_w, half_w, 0.0, wall, -half_h, half_h)

# Mount plate on the outside, covering the window and the screw holes.
plate_x = hole_spacing / 2 + 3.5
plate_z0 = min(-window_height / 2 - 1.0, hole_dz - 3.5)
plate_z1 = max(window_height / 2 + 1.0, hole_dz + 3.5)
plate = block(-plate_x, plate_x, wall, wall + plate_thickness, plate_z0, plate_z1)
for x in (-hole_spacing / 2, hole_spacing / 2):
    hole = (
        cq.Workplane("XZ")
        .center(x, hole_dz)
        .circle(hole_diameter / 2)
        .extrude(-(plate_thickness + 0.2))
        .translate((0, wall - 0.1, 0))
    )
    plate = plate.cut(hole)
part = part.union(plate)

# Socket with screw terminals, plugged in from inside.
socket_x = min(pins * pitch / 2 + 1.0, half_w)
part = part.union(block(-socket_x, socket_x, -socket_depth, 0.0, -half_h, half_h))

show_object(part)
