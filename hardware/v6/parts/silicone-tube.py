"""Silicone tube or cable along a route (TC-ST7 7 x 5 mm, SP-STB 8 x 5 mm, RU-TMP cable).

APPROXIMATION: the tubes are flexible and cut by hand, so they have no fixed
shape. Each route is drawn for the layout in microlab.assy, in that assembly's
frame, and has to be redrawn when a unit moves.

- points: "x,y,z; x,y,z; ..." in mm. The first and the last segment are
  straight (a tube pushed on a nozzle or hanging in a jar); a spline through
  the points in between joins them.
- start_sleeve, end_sleeve: length over which the tube is stretched onto
  something wider than its bore, such as the 6.35 mm copper tube.
  sleeve_id is the stretched bore; the wall keeps its thickness.
- tube_id 0 gives a solid cable.
"""

import cadquery as cq

if "show_object" not in globals():
    def show_object(*args, **kwargs):
        pass

tube_od = 7.0
tube_id = 5.0
points = "0,0,0; 0,0,20; 30,0,60; 60,0,20; 60,0,0"
start_sleeve = 0.0
end_sleeve = 0.0
sleeve_id = 6.4

route = [cq.Vector(*[float(v) for v in p.split(",")]) for p in points.split(";") if p.strip()]


def sweep(edge, outer, inner):
    p = edge.startPoint()
    t = edge.tangentAt(0)
    side = cq.Vector(0, 0, 1) if abs(t.z) < 0.9 else cq.Vector(1, 0, 0)
    plane = cq.Plane(origin=p, xDir=t.cross(side).normalized(), normal=t)
    profile = cq.Workplane(plane).circle(outer / 2)
    if inner > 0:
        profile = profile.circle(inner / 2)
    return (
        profile
        .sweep(cq.Workplane(obj=cq.Wire.assembleEdges([edge])))
        .val()
    )


def straight(p0, p1, sleeve, sleeve_at_start):
    """A straight end, with its outer `sleeve` mm stretched."""
    direction = (p1 - p0).normalized()
    length = (p1 - p0).Length
    sleeve = min(sleeve, length)
    split = p0 + direction * sleeve if sleeve_at_start else p1 - direction * sleeve
    wide = (sleeve_id + tube_od - tube_id, sleeve_id)
    plain = (tube_od, tube_id)
    pieces = []
    if sleeve > 0:
        ends = (p0, split) if sleeve_at_start else (split, p1)
        pieces.append(sweep(cq.Edge.makeLine(*ends), *wide))
    if sleeve < length:
        ends = (split, p1) if sleeve_at_start else (p0, split)
        pieces.append(sweep(cq.Edge.makeLine(*ends), *plain))
    return pieces


start_dir = (route[1] - route[0]).normalized()
end_dir = (route[-1] - route[-2]).normalized()

pieces = straight(route[0], route[1], start_sleeve, True)
pieces += straight(route[-2], route[-1], end_sleeve, False)
if len(route) > 3:
    spline = cq.Edge.makeSpline(route[1:-1], tangents=[start_dir, end_dir], scale=False)
    pieces.append(sweep(spline, tube_od, tube_id))

tube = cq.Workplane("XY")
for piece in pieces:
    tube = tube.union(piece)

show_object(tube)
