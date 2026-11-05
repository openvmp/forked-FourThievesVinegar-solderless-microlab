"""3.5 inch GPIO touchscreen for the Raspberry Pi (CU-SCR), an approximation.

Built in the frame of `//pub/electronics/sbcs/raspberrypi:rpi4b`, so the port
at the Pi's `corner-bottom-front-left` seats it on the Pi.

Where the values come from:
- The docs use a 3.5 inch screen that plugs onto GPIO pins 1-26
  (docs/assembly-control-unit.md, cu_pi_screen.jpeg), with a board about the
  size of the Pi's (85 x 56 mm).
- Height: the board rests on the Pi's USB and Ethernet jacks (top z 16.6 in the
  rpi4b STEP), as these screens do.
- Header: a 2 x 13 female header over the Pi's pins 1-26 (pin centres from the
  rpi4b STEP). It starts above the pin tips (z 10.1), because the rpi4b STEP
  models the pins as solids; the real header reaches further down.
- Display module 80 x 54.5 x 4 mm on top (guessed from the photos).
- The flat box lid's front tab reaches 0.5 mm over the Pi's front edge, so the
  board starts 0.6 mm behind it (85 x 55.4 mm); real boards vary this much.
"""
import cadquery as cq

if "show_object" not in globals():
    def show_object(*args, **kwargs):
        pass

pcb_z = (16.7, 18.3)
pin_x = (8.25, 8.25 + 12 * 2.54)
pin_y = (51.25, 53.75)


def block(x0, x1, y0, y1, z0, z1):
    return (
        cq.Workplane("XY")
        .box(x1 - x0, y1 - y0, z1 - z0, centered=False)
        .translate((x0, y0, z0))
    )


screen = block(0.0, 85.0, 0.6, 56.0, *pcb_z)
screen = screen.union(block(0.0, 80.0, 1.0, 55.5, pcb_z[1], pcb_z[1] + 4.0))
screen = screen.union(
    block(pin_x[0] - 1.27, pin_x[1] + 1.27, pin_y[0] - 1.27, pin_y[1] + 1.27, 10.2, pcb_z[0])
)

show_object(screen)
