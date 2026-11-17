"""6 oz regular-mouth jar, the reactor core's inner chamber (RU-COR).

APPROXIMATION: the parts list asks for a "6 oz regular mouth mason jar" and
names no model. Ball sells no 6 oz quilted jar; its quilted half-pint holds
about 6 oz to the neck but is about 98 x 70 mm. This model keeps the earlier
model's overall size instead (81 mm tall, about 200 ml) and sizes its mouth
to the parts it has to fit:

- Finish: 61 mm across, the thread size of `mason-jar-band-regular-mouth.py`,
  which leaves about 1 mm to the band's thread ridges.
- Thread: right-hand, 3.5 mm pitch like the band's, 1.7 turns, ridges out to
  r 31.45 (the band's reach in to r 31.55). It sits halfway between the band's
  ridges for the placement in reactor-unit-reactor-core.assy: there the band's
  ridge crosses this frame's +X axis at z 82.125 (measured on an export), so
  this one crosses it at 82.125 - 3.5 / 2 - 2 x 3.5 = 73.375. If the band or
  either part's port changes, measure again and update thread_start.
- Opening 55 mm: clears the stir paddle (48 mm across), the thermistor probe
  and the reagent tubes.
- Body 64 mm: passes the outer jar's 74 mm neck. Shoulder and neck sit below
  the band's lower edge (21.8 mm under the rim).
- Wall 1.5 mm, as before; real glass is thicker. Shoulder shape is guessed.

Frame: base at z = 0, rim at z = 81, axis along +Z.
"""
import cadquery as cq

if "show_object" not in globals():
    def show_object(*args, **kwargs):
        pass

height = 81.0
wall = 1.5
base_radius = 29.0
body_radius = 32.0
base_round = 6.0
shoulder_start = 60.0
neck_start = 68.0
neck_radius = 29.0
finish_start = 71.0
finish_radius = 30.5
opening_radius = 27.5
thread_pitch = 3.5
thread_turns = 1.7
thread_start = 73.375
thread_profile_radius = 0.95


def profile(points):
    """Revolve a closed (r, z) outline about Z. Each item is a point, or a
    (point, start tangent, end tangent) spline to that point."""
    sketch = cq.Workplane("XZ").moveTo(*points[0])
    for item in points[1:]:
        if isinstance(item[0], tuple):
            end, t0, t1 = item
            sketch = sketch.spline([end], tangents=[t0, t1], includeCurrent=True)
        else:
            sketch = sketch.lineTo(*item)
    return sketch.close().revolve(360, (0, 0, 0), (0, 1, 0))


outside = profile([
    (0, 0),
    (base_radius, 0),
    ((body_radius, base_round), (1, 1), (0, 1)),
    (body_radius, shoulder_start),
    ((neck_radius, neck_start), (0, 1), (0, 1)),
    (neck_radius, finish_start - 1.0),
    (finish_radius, finish_start),
    (finish_radius, height),
    (0, height),
])

inside = profile([
    (0, wall),
    (base_radius - wall, wall),
    ((body_radius - wall, base_round + wall / 2), (1, 1), (0, 1)),
    (body_radius - wall, shoulder_start),
    ((opening_radius, neck_start + wall / 2), (0, 1), (0, 1)),
    (opening_radius, height + 1.0),
    (0, height + 1.0),
])

jar = outside.cut(inside)

# A circle swept along a right-hand helix on the finish, starting on +X.
helix = cq.Wire.makeHelix(
    pitch=thread_pitch,
    height=thread_pitch * thread_turns,
    radius=finish_radius,
    center=cq.Vector(0, 0, thread_start),
)
thread = (
    cq.Workplane(cq.Plane(origin=(finish_radius, 0, thread_start), xDir=(1, 0, 0), normal=(0, 1, 0)))
    .circle(thread_profile_radius)
    .sweep(cq.Workplane(obj=helix), isFrenet=True)
)
jar = jar.union(thread)

show_object(jar)
