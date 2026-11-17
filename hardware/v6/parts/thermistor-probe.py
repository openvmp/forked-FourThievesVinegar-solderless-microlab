"""Steel sleeve of the DS18B20 thermistor probe (RU-TMP), an approximation.

The parts list links to a USB DS18B20 probe but names no model. The sleeve is
the common waterproof one, 6 mm across and 50 mm long; the size is a guess
from typical listings. Its cable is the `thermistor-cable` part.

Frame: origin at the centre of the sleeve's top, where the cable leaves it.
The sleeve hangs down along -Z.
"""
import cadquery as cq

if "show_object" not in globals():
    def show_object(*args, **kwargs):
        pass

sleeve_diameter = 6.0
sleeve_length = 50.0

sleeve = cq.Workplane("XY").circle(sleeve_diameter / 2).extrude(-sleeve_length)

show_object(sleeve)
