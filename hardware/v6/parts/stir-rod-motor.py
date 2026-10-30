import cadquery as cq

if "show_object" not in globals():
    def show_object(*args, **kwargs):
        pass

body_width = 12.0
body_height = 10.0
body_length = 16.0
gearbox_diameter = 10.0
gearbox_length = 9.0
shaft_diameter = 3.0
shaft_length = 8.0
# Guessed: short vertical stubs from the end cap tabs, not the real leads
wire_length = 5.0
wire_radius = 0.8
wire_spacing = 6.0

body = (
    cq.Workplane("XY")
    .box(body_width, body_height, body_length)
    .translate((0, 0, shaft_length + gearbox_length + body_length / 2))
)

gearbox = (
    cq.Workplane("XY")
    .circle(gearbox_diameter / 2)
    .extrude(gearbox_length)
    .translate((0, 0, shaft_length))
)

shaft = (
    cq.Workplane("XY")
    .circle(shaft_diameter / 2)
    .extrude(shaft_length)
)

wire_red = (
    cq.Workplane("XY")
    .center(wire_spacing / 2, 0)
    .circle(wire_radius)
    .extrude(wire_length)
    .translate((0, 0, shaft_length + gearbox_length + body_length))
)

wire_black = (
    cq.Workplane("XY")
    .center(-wire_spacing / 2, 0)
    .circle(wire_radius)
    .extrude(wire_length)
    .translate((0, 0, shaft_length + gearbox_length + body_length))
)

motor = body.union(gearbox).union(shaft).union(wire_red).union(wire_black)

show_object(motor)
