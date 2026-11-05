"""12V to 5V stepdown converter with a USB output (CU-SDC), an approximation.

Built in the frame of `stepdown-case` (the case it slides into), so the port
at the origin seats it in the case's slot.

Where the values come from:
- Board outline 63 x 27.3 mm: the case is named "63x27x14" and its slot walls
  are 27.5 mm apart (27.3 mm leaves 0.1 mm per side).
- Board height (PCB z 4.3..5.9): the case's slot, measured from its STEP.
- Components stay under the case's 17.65 mm ceiling. Their sizes and places
  (input terminal, inductor, capacitors, USB-A socket) are guessed from a
  typical module; the docs only say it has a USB port for the Pi's cable.
"""
import cadquery as cq

if "show_object" not in globals():
    def show_object(*args, **kwargs):
        pass

pcb_x = (1.25, 64.25)
pcb_y = (2.1, 29.4)
pcb_z = (4.3, 5.9)


def block(x0, x1, y0, y1, z0, z1):
    return (
        cq.Workplane("XY")
        .box(x1 - x0, y1 - y0, z1 - z0, centered=False)
        .translate((x0, y0, z0))
    )


def cylinder(x, y, z0, diameter, height):
    return cq.Workplane("XY").circle(diameter / 2).extrude(height).translate((x, y, z0))


top = pcb_z[1]
board = block(*pcb_x, *pcb_y, *pcb_z)
# Input screw terminal (12V in) at one end.
board = board.union(block(2.0, 9.5, 8.0, 18.0, top, top + 10.0))
# Inductor and two electrolytic capacitors.
board = board.union(block(14.0, 26.0, 8.0, 20.0, top, top + 7.0))
board = board.union(cylinder(33.0, 15.5, top, 8.0, 11.0))
board = board.union(cylinder(43.0, 15.5, top, 8.0, 11.0))
# USB-A socket at the other end, facing out of the case's open end.
board = board.union(block(50.0, 64.25, 9.0, 22.1, top, top + 5.7))

show_object(board)
