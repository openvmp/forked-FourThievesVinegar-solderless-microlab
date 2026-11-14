"""Copper heat exchanger coil of the heating unit (TC-CTB).

APPROXIMATION: the builder bends this by hand (docs/assembly-temperature-
exchangers-unit.md), so it has no fixed shape. As in cold-unit-tube.py, one
end drops inside the coil to the bottom and the tube winds back up as a helix
to the other lid hole.

- Tube: 1/4 in OD x 3/16 in ID, from the parts list.
- Frame: the lid's. The holes are at x = +-24 mm, the lid's top face is z = 0
  and the jar is towards +z. The jar is the 32 oz one from the parts list
  (TC-JAR); its inside bottom is at z = 166.
- The immersion heater (hot-unit-heater) hangs from the lid's pocket with its
  element turned toward the jar axis, so it stays within 17.1 mm of the axis.
  The docs ask to "leave space for the heating coil".
- coil_radius, turns, coil_top, coil_bottom: as the cooling coil. 30 mm passes
  the jar's 74 mm mouth.
- leg_x: the down-leg runs between the heater and the coil, 22 mm from the
  axis (about 7 mm from the heater, 1.6 mm from the coil).
- turns must be a whole number plus a half so that the coil ends under the
  second hole. Other values are guesses.
"""

import cadquery as cq

if "show_object" not in globals():
    def show_object(*args, **kwargs):
        pass

tube_od = 6.35
tube_id = 4.7625
hole_x = 24.0
stick_out = 40.0
bend_z = 15.0
coil_radius = 30.0
turns = 8.5
coil_top = 40.0
coil_bottom = 155.0
leg_x = 22.0

down = cq.Vector(0, 0, 1)
up = cq.Vector(0, 0, -1)


def sweep(edge, frenet=False):
    p = edge.startPoint()
    t = edge.tangentAt(0)
    side = cq.Vector(0, 0, 1) if abs(t.z) < 0.9 else cq.Vector(1, 0, 0)
    plane = cq.Plane(origin=p, xDir=t.cross(side).normalized(), normal=t)
    return (
        cq.Workplane(plane)
        .circle(tube_od / 2)
        .circle(tube_id / 2)
        .sweep(cq.Workplane(obj=cq.Wire.assembleEdges([edge])), isFrenet=frenet)
        .val()
    )


def bend(p0, t0, p3, t3, d):
    return cq.Edge.makeBezier([p0, p0 + t0 * d, p3 - t3 * d, p3])


# The helix starts at (-coil_radius, 0, coil_bottom) and ends at
# (coil_radius, 0, coil_top).
helix = cq.Wire.makeHelix(
    pitch=(coil_bottom - coil_top) / turns,
    height=coil_bottom - coil_top,
    radius=coil_radius,
    center=cq.Vector(0, 0, coil_bottom),
    dir=up,
).Edges()[0]

leg_top = cq.Vector(-hole_x, 0, -stick_out)
leg_bend = cq.Vector(-hole_x, 0, bend_z)
inner_top = cq.Vector(-leg_x, 0, bend_z + 25)
inner_bottom = cq.Vector(-leg_x, 0, coil_bottom - 15)
riser_bend = cq.Vector(hole_x, 0, bend_z)
riser_top = cq.Vector(hole_x, 0, -stick_out)

edges = [
    (cq.Edge.makeLine(leg_top, leg_bend), False),
    (bend(leg_bend, down, inner_top, down, 12), False),
    (cq.Edge.makeLine(inner_top, inner_bottom), False),
    # A longer bend here makes the sweep fail.
    (bend(inner_bottom, down, helix.startPoint(), helix.tangentAt(0), 10), False),
    (helix, True),
    (bend(helix.endPoint(), helix.tangentAt(1), riser_bend, up, 15), False),
    (cq.Edge.makeLine(riser_bend, riser_top), False),
]

tube = cq.Workplane("XY")
for edge, frenet in edges:
    tube = tube.union(sweep(edge, frenet))

show_object(tube)
