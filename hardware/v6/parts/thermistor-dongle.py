"""USB dongle of the thermistor (RX-TMPD), an approximation.

The parts list calls it a "USB dongle for thermistor" and links to the same
listing as the probe, with no model or size. The body, 18 x 9 x 40 mm, is a
guess at a USB stick of that kind.

The USB-A plug would sit inside the control box's USB socket, but
`usb-panel-socket` models the socket as a solid block, so the plug is left
out and the body stops 0.1 mm off the wall.

Frame: origin at the centre of the socket's window on the wall's outer face.
+Y points away from the wall; the cable leaves the far end at y = 40.
"""
import cadquery as cq

if "show_object" not in globals():
    def show_object(*args, **kwargs):
        pass

width = 18.0
thickness = 9.0
length = 40.0
gap = 0.1

body = (
    cq.Workplane("XY")
    .box(width, length - gap, thickness, centered=(True, False, True))
    .translate((0, gap, 0))
    .edges("|Y")
    .fillet(2.0)
)

show_object(body)
