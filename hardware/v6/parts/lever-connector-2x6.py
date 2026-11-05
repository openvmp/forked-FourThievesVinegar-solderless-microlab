"""Lever wire connector, 2-in-6-out, with mounting ears (CU-WCL), an approximation.

Frame: origin at the centre of the body's underside.

Where the values come from:
- The sellers' pages give no dimensions. Body 25 x 28 x 18 mm is scaled from
  docs/media/control-unit/case_assembled.jpeg, using the box's 188 mm width.
- Ear holes 38.57 mm apart: three rows of the control box's floor hole grid,
  the nearest spacing that clears the body. The docs fix it with two M3
  screws; ear thickness 3 mm is guessed.
"""
import cadquery as cq

if "show_object" not in globals():
    def show_object(*args, **kwargs):
        pass

body = (25.0, 28.0, 18.0)
hole_spacing = 38.57
ear_thickness = 3.0
hole_diameter = 3.4

part = cq.Workplane("XY").box(*body, centered=(True, True, False))
ears = (
    cq.Workplane("XY")
    .slot2D(hole_spacing + 8.0, 8.0, angle=90)
    .extrude(ear_thickness)
    .faces(">Z")
    .workplane()
    .pushPoints([(0, -hole_spacing / 2), (0, hole_spacing / 2)])
    .hole(hole_diameter)
)
part = part.union(ears)

show_object(part)
