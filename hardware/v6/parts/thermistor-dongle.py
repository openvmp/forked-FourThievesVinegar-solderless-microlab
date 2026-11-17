"""USB dongle of the thermistor (RX-TMPD), an approximation.

The parts list calls it a "USB dongle for thermistor" and links to the same
AliExpress listing as the probe, with no model or size.
docs/media/ML_case_cabled.jpeg shows it: a blue USB-A stick plugged straight
into the control box's lower USB socket, the probe's cable leaving its far end.

- USB-A plug, sizes from the dimensions table of
  https://en.wikipedia.org/wiki/USB_hardware: shell 12.0 x 4.5 mm, at least
  11.75 mm long (12 here), entering the 8.88 mm deep receptacle, so about
  3.1 mm of it stays outside. Shell walls 0.3 mm (assumed). The insulator
  insert fills the lower half of the shell, as the article says; the
  receptacle's tongue enters the upper half.
- Four contacts on the insert, 1 mm wide at x = -3.5, -1.0, 1.0 and 3.5 mm
  (recalled from the USB-A layout, NOT verified). The two data contacts
  (inner) are recessed behind the power ones, as the article says.
- Body 18 x 9 mm with rounded edges, estimated from the photo against the
  8-pin connector beside it. It runs from the plug to y = 40, where the
  thermistor cable's route ends.

Frame: origin at the centre of the socket's window on the wall's outer face.
+Y points away from the wall; the plug goes into the socket along -Y.
"""
import cadquery as cq

if "show_object" not in globals():
    def show_object(*args, **kwargs):
        pass

receptacle_depth = 8.88
gap = 0.1

plug_width = 12.0
plug_height = 4.5
plug_length = 12.0
shell_wall = 0.3
insert_top = -0.35
contact_width = 1.0
contact_thickness = 0.15
data_recess = 0.7

body_width = 18.0
body_thickness = 9.0
body_end = 40.0
body_round = 3.0


def block(x0, x1, y0, y1, z0, z1):
    return (
        cq.Workplane("XY")
        .box(x1 - x0, y1 - y0, z1 - z0, centered=False)
        .translate((x0, y0, z0))
    )


plug_front = -(receptacle_depth - gap)
plug_back = plug_front + plug_length
inner_x = plug_width / 2 - shell_wall
inner_z = plug_height / 2 - shell_wall

shell = block(-plug_width / 2, plug_width / 2, plug_front, plug_back, -plug_height / 2, plug_height / 2)
shell = shell.cut(block(-inner_x, inner_x, plug_front - 0.1, plug_back - 0.5, -inner_z, inner_z))
insert = block(-inner_x, inner_x, plug_front + 0.3, plug_back - 0.5, -inner_z, insert_top)
plug = shell.union(insert)
for x in (-3.5, -1.0, 1.0, 3.5):  # contact centres
    start = plug_front + 0.6 + (data_recess if abs(x) < 2 else 0.0)
    plug = plug.union(block(
        x - contact_width / 2, x + contact_width / 2,
        start, plug_back - 1.5,
        insert_top, insert_top + contact_thickness,
    ))

body_start = plug_back - 0.4
body = (
    block(-body_width / 2, body_width / 2, body_start, body_end, -body_thickness / 2, body_thickness / 2)
    .edges("|Y")
    .fillet(body_round)
    .faces(">Y")
    .edges()
    .fillet(1.5)
)

show_object(body.union(plug))
