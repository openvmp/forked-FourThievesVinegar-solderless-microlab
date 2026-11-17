"""USB dongle of the thermistor (RX-TMPD), an approximation.

The parts list calls it a "USB dongle for thermistor" and links to the same
AliExpress listing as the probe, with no model or size.
docs/media/ML_case_cabled.jpeg shows it: a blue USB-A stick plugged straight
into the control box's lower USB socket, the probe's cable leaving its far end.

- USB-A plug: the standard 12.0 x 4.5 mm shell, 12 mm long. The shell is
  solid here; its tongue is left out, like the socket's.
- Body 18 x 9 x 40 mm with rounded edges: estimated from the photo against
  the 8-pin connector beside it. Its length is set so the body ends where the
  thermistor cable's route ends.

Frame: origin at the centre of the socket's window on the wall's outer face.
+Y points away from the wall; the plug goes into the socket along -Y and the
cable leaves the far end at y = 40.
"""
import cadquery as cq

if "show_object" not in globals():
    def show_object(*args, **kwargs):
        pass

body_width = 18.0
body_thickness = 9.0
body_length = 40.0
body_round = 3.0
gap = 0.1

plug_width = 12.0
plug_height = 4.5
plug_length = 12.0

body = (
    cq.Workplane("XY")
    .box(body_width, body_length - gap, body_thickness, centered=(True, False, True))
    .translate((0, gap, 0))
    .edges("|Y")
    .fillet(body_round)
    .faces(">Y")
    .edges()
    .fillet(1.5)
)
plug = (
    cq.Workplane("XY")
    .box(plug_width, plug_length + gap, plug_height, centered=(True, False, True))
    .translate((0, -plug_length, 0))
)

show_object(body.union(plug))
