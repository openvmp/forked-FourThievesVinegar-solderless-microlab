"""Arduino CNC shield v3 with three stepper drivers (CU-CNC, CU-SMD), an approximation.

Built in the frame of `//pub/electronics/sbcs/arduino:unoR3`, so the port at the
Uno's `corner-bottom-back-left` seats it on the Uno.

Where the values come from:
- Board outline: the Uno's, 68.4 x 52 mm, from the unoR3 STEP (x -33..35.4).
- Height: the shield rests on the Uno's USB-B and power jacks (top z 13.9 in
  the unoR3 STEP), above the Uno's headers (top z 11.1). The male pins that
  reach down into the Uno's headers are left out, since the unoR3 STEP models
  its headers as solid blocks.
- Drivers: A4988 carrier, 15.24 x 20.32 mm, on 8.5 mm female headers, with a
  9 x 9 x 5 mm heatsink. Three in the X, Y and Z sockets, the A socket empty,
  laid out 2 x 2 as in docs/media/control-unit/case_assembled.jpeg (guessed).
- 12V screw terminal: generic 2-pole 5.0 mm block (guessed).
"""
import cadquery as cq

if "show_object" not in globals():
    def show_object(*args, **kwargs):
        pass

pcb_x = (-33.0, 35.4)
pcb_y = (-26.0, 26.0)
pcb_z = (14.0, 15.6)
socket_height = 8.5
driver_size = (15.24, 20.32, 1.6)
heatsink_size = (9.0, 9.0, 5.0)


def block(x0, x1, y0, y1, z0, z1):
    return (
        cq.Workplane("XY")
        .box(x1 - x0, y1 - y0, z1 - z0, centered=False)
        .translate((x0, y0, z0))
    )


top = pcb_z[1]
shield = block(*pcb_x, *pcb_y, *pcb_z)

# Socket centres: X, Y, Z filled, A empty.
sockets = [(-12.0, 12.0, True), (-12.0, -12.0, True), (14.0, -12.0, True), (14.0, 12.0, False)]
for cx, cy, filled in sockets:
    dx, dy, dz = driver_size
    # Two 1x8 female headers under each driver, along its long side.
    for side in (-1, 1):
        hx = cx + side * (dx / 2 - 1.27)
        shield = shield.union(
            block(hx - 1.27, hx + 1.27, cy - dy / 2, cy + dy / 2, top, top + socket_height)
        )
    if filled:
        z0 = top + socket_height
        shield = shield.union(block(cx - dx / 2, cx + dx / 2, cy - dy / 2, cy + dy / 2, z0, z0 + dz))
        hx, hy, hz = heatsink_size
        shield = shield.union(
            block(cx - hx / 2, cx + hx / 2, cy - hy / 2, cy + hy / 2, z0 + dz, z0 + dz + hz)
        )

# 12V power screw terminal.
shield = shield.union(block(26.0, 34.0, -25.0, -15.0, top, top + 10.0))

show_object(shield)
