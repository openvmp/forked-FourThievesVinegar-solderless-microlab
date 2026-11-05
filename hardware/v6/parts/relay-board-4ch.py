"""4-channel 5V relay board (CU-RLY), an approximation.

Built in the frame of `relay-case-no-top` (the open-top case it slides into),
so the port at the origin seats it in the case's slot.

Where the values come from:
- Board outline 50 x 72 mm: the case is named "50x73", its slot walls are
  73 mm apart and its ridges 72 mm apart. The slot is a V-groove narrowing
  toward the wall; a 1.6 mm board fits only up to the ridge tips (0.1 mm gap).
- Board height (PCB z 3.0..4.6): the case's slot, measured from its STEP.
- Relays: JQC-3FF-S-Z datasheet body, 19.0 x 15.5 x 15.3 mm. Four in a row along
  the long edge, as in docs/media/control-unit/relay.png.
- Terminal blocks (3 x 4 outputs, 6 inputs), jumper block: generic 5.0 mm pitch
  blocks, sized and placed from the product photo (guessed).
"""
import cadquery as cq

if "show_object" not in globals():
    def show_object(*args, **kwargs):
        pass

pcb_x = (0.0, 50.0)
pcb_y = (4.5, 76.5)
pcb_z = (3.0, 4.6)
relay_size = (19.0, 15.5, 15.3)


def block(x0, x1, y0, y1, z0, z1):
    return (
        cq.Workplane("XY")
        .box(x1 - x0, y1 - y0, z1 - z0, centered=False)
        .translate((x0, y0, z0))
    )


top = pcb_z[1]
board = block(*pcb_x, *pcb_y, *pcb_z)

# Relays in a row along the long edge.
relay_pitch = 17.0
y_start = (pcb_y[0] + pcb_y[1]) / 2 - 1.5 * relay_pitch - relay_size[1] / 2
for i in range(4):
    y0 = y_start + i * relay_pitch
    board = board.union(
        block(9.5, 9.5 + relay_size[0], y0, y0 + relay_size[1], top, top + relay_size[2])
    )

# Output terminal blocks (NO/COM/NC x 4) along the edge at x = 0.
board = board.union(block(0.5, 8.0, 5.0, 66.0, top, top + 10.0))
# Input terminal block (DC+, DC-, IN1..IN4) at the opposite edge.
board = board.union(block(42.0, 49.5, 5.0, 35.0, top, top + 10.0))
# Trigger-level jumper block.
board = board.union(block(42.0, 47.0, 50.0, 60.0, top, top + 8.5))

show_object(board)
