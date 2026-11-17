# AGENTS.md

Notes for agents and contributors working on the PartCAD model of the MicroLab.

## Layout

- `partcad.yaml` (root) declares the package and imports `hardware/v6` as the `v6` package, with `includePaths: [".."]` so it can read `hardware/urls.j2`.
- `hardware/v6/partcad.yaml` defines the sketches, interfaces, parts and assemblies.
- `hardware/v6/parts/` holds the CadQuery part scripts. The `.assy` files in `hardware/v6/` place parts by connecting their ports.
- `docs/microlab-parts-list.xlsx` is the bill of materials. Its part IDs (e.g. `TC-CTB`) are not linked to PartCAD part names.

## Running PartCAD

Run `pc` from the repository root. From `hardware/v6` the `urls.j2` import fails.

- Parts: `pc qual test v6:<part>`, `pc render -t png -O <dir> v6:<part>`.
- A PartCAD without partcad/partcad#828 needs `--assembly` (`-a`) for an assembly: `pc test --assembly v6:<assembly>`, `pc export -a -t step -O <dir> v6:<assembly>`, or it says "not found". With it, the kind is found by name and the flag is optional. `pc render` does not work for assemblies here.
- `pc` keeps a daemon (`partcad_service_json_rpc`, started from the miniconda Python) that holds built shapes in memory. If an export still shows a part as it was before you edited its script, stop that process and export again.
- Parameters in `partcad.yaml` reach CadQuery scripts only with partcad's CQGI fix for Python 3.14 (branch `fix/cqgi-parameters-python-3.14`). Without it every script builds with its own defaults, so the three `panel-connector-*` parts all come out as the 8-pin one.
- Custom parts with no supplier fail the `manufacturability` check. Until a part has a purchase or manufacturing definition, mark it `manufacturable: false` with a TODO.

## Ports and placement

- A port is `[[x, y, z], [rotation axis], angle]`: the port frame is rotated by `angle` degrees about the axis. The middle element is not the direction the port faces. To flip a part along Z, toggle its port's rotation about X between 0 and 180.
- Which way a port offset moves the mated part depends on both ports' frames. Measure the result of every offset change instead of reasoning out its sign.
- With `connectPorts` and the part's own port at `[[...], [0, 0, 1], 0]`, the parent port's rotation sets the part's orientation: 180 about `[-0.71, -0.71, 0]` leaves it unrotated, 180 about `[0.71, -0.71, 0]` turns it 180 degrees about Z, 180 about `[0, 1, 0]` turns it +90 about Z (measured). To build a child in its parent's frame, give the parent a port `[[0, 0, 0], [0, 0, 1], 0]` and the child `[[0, 0, 0], [-0.71, -0.71, 0], 180]`.
- Write port offsets to 0.1 mm. Part dimensions aren't always whole tenths (the jar flanges are 2.54 mm thick), so faces that should touch can't always meet exactly. Round toward a small gap, never toward a crossing: a gap under 0.1 mm bounds no volume, while a crossing of even 0.01 mm shows up as an overlap.
- The PartCAD viewer may show an assembly upright or upside down. Don't judge orientation from a screenshot alone.

## Checking overlaps

Check cheapest first, with `hardware/tools/check_overlaps.py` (needs a Python with CadQuery's OCP):

1. Bounding-box screen of every part pair on a STEP export, in seconds.
2. Exact overlap volumes for the pairs involving the parts you changed: `--parts <tree paths>`. Do this after every edit.
3. Before committing: `--full`, which measures all candidate pairs and runs `pc qual test --assembly -f interference`.

`check_overlaps.py` records each pair's time and volume in `hardware/tools/.timings/<assembly>.json` (not committed). `--slowest` lists the slowest recorded pairs; `--skip-slower 60` leaves out pairs that took over 60 s last time and lists them with their last volume. A pair whose part changed is measured again. Don't skip pairs before a commit that touches them.

The scripts measure overlaps with a fuzzy value of 0.001 mm. Without it OCC returned an empty result for the stir rod mount's screws against the manifold core, where `pc qual test` finds 3.6 and 4.1 mm³. Where the fuzzy boolean comes out with a negative volume (faces that touch, such as the reactor core's outer jar on its lower flange), they use the plain one. If the scripts and `pc qual test` ever disagree, `pc qual test` is the reference.

The STEP export loses instance names. Parts are listed by tree path (e.g. `1/3/16`), in the order of the `.assy` links. Use `--list` to identify them.

## Tubes

The routes of the `tube-*` parts and the `thermistor-cable` are the `tubes` list in `hardware/v6/partcad.yaml`: part name, parts list ID, outer and inner diameter (0 for a solid cable), sleeve lengths, points. Check them with `hardware/tools/check_tubes.py` (needs a Python with CadQuery):

1. With no arguments: each tube's length, tightest bend and gaps to the other tubes, in seconds. Do this after every route edit. Keep bends at or above the tube's diameter.
2. `--step <microlab export> --cache <dir>`: exact overlaps with the parts near each tube's path. `--move 1/2=dx,dy,dz` tries a new unit position without another export. An overlap with a peristaltic pump takes about 8 minutes to measure, so run tubes in separate processes with `--only`.

Lay turns out on arcs: waypoints placed by eye give kinks. `hardware/tools/step_features.py` lists a STEP file's cylinders and faces, to find nozzles and holes.

## Sweeps

- A `type: sweep` part sweeps a sketch along one Bezier curve built from its `axis` points, starting at the sketch origin. More points raise the curve's degree; they don't add separate sections, so a sweep can't have exactly straight segments joined to an arc.
- A curved path with exactly vertical end tangents crashes OCC's pipe sweep. Tilt the control points slightly (0.5 mm in X works).

## Design constraints

- Reactor core: the outer jar is upright, with its rim against the manifold lid's underside and its band resting on the upper neck flange. The two neck flanges clamp the stand's C-part (8 mm thick). The inner jar hangs from its band under the manifold core.
- `parts/mason-jar-32oz-wide-mouth.py` is shared by the reactor core's outer jar and the cooling and heating units' jars (`TC-JAR` is 32 oz).
- Stir paddle: it must not touch the inner jar's bottom or sides (`docs/assembly-reactor-unit.md`). Its `paddle_length` and `shaft_length` are part parameters; the builder cuts the real shaft to fit.

## Known issues

- `stir-rod`, `stir-rod-motor` and `stir-rod-coupler` are CadQuery approximations with guessed dimensions, not models of the linked products. `stir-rod.py` says where each value comes from.
- The pumps box's front slot sits 2 mm higher than its side slots allow for part C's tab. C is raised 2.1 mm (H `eye-front-1`, with the stand's `core-holder`) and floats about 1.85 mm above its seat on H.
- The pump models (`peristaltic-pump.step`, `circulation-pump.step`) disagree with the pumps box, which is the built 4TV design:
  - The circulation pump's barrel is 27.2 mm across in the box's 27.0 mm hole (34 mm³ each).
  - The peristaltic pump's hole pattern is 37.5 x 54 mm against the box's 37.9 x 55, so its lower M3 screws cut into the hole walls. `pc qual test` skips these screws as invalid solids.
  - The fix belongs in the parts repo's STEP files.
- The peristaltic pumps stand 1 mm off the box's front: their head screws stick out 1 mm behind the mounting plate.
- The control box holds the Pi by four corner posts with catches, built for the Pi 3 Model B the docs call for (`CU-RPI`). The model uses `rpi4b`, the only Pi in the PartCAD index. The Pi 4's front USB stack sticks out 3 mm past the board edge, but the post's inner face is only 1.5 mm past it, so they overlap by 10 mm³. The Pi can't shift to clear it. Whether a real Pi 3's Ethernet jack in that corner clears the post is unmeasured.
- The flat lid's left screw hole is at (-90.5, -88.5) in its STEP, not the mirror of the right one at (91, -89), so it sits 0.7 mm off the box's hole. The screw follows the box's hole and cuts 0.34 mm³ of the lid.
- The control unit's boards and connectors (`relay-board`, `stepdown-converter`, `cnc-shield`, `rpi-lcd-35`, `lever-connector`, `panel-connector-*`, `usb-panel-socket`, `barrel-jack`) are CadQuery approximations. Outlines come from the cases and box cut-outs they fit; their scripts say what is measured and what is guessed.
- The relay case, the converter case and the lever connector are placed only in the flat box, the one the build guide describes. The regular box's floor holes fit none of them.
- The docs screw the converter case to the flat box's floor, but the box has no hole there, so the case rests unscrewed. The lever connector's two screws are left out: 12 mm M3 screws through its (guessed) 3 mm ears would come out under the floor.
- `cold-unit-tube` and `hot-unit-tube` are CadQuery approximations of the hand-bent coils; their scripts say where each value comes from.
- The `tube-*` parts (`parts/silicone-tube.py`) are approximations of flexible tubing. Each route is a list of points in the `microlab` assembly's frame, drawn for the unit positions in `microlab.assy`; moving a unit means redrawing its tubes. The circulation tubes match the docs' 16 in and 8 in lengths. The reagent tubes' lengths are guessed, and they butt against the peristaltic pump model's own tube stubs with no connector.
- The thermistor (assembly `thermistor`: `thermistor-probe`, `thermistor-cable`, `thermistor-dongle`) is an approximation. The cable is the assembly's root and is drawn in the microlab frame; the probe and dongle hang off its ports. The assembly implements `usb-a-plug` and plugs into the `control-unit` assembly's `usb-lower` (`usb-a-receptacle`). Those receptacle ports hold for the flat profile only, and moving either unit means redrawing the cable; the parts list names no model. The probe is a 6 x 50 mm sleeve, the cable 3.5 mm, the dongle 18 x 9 x 40 mm, all guessed from typical USB DS18B20 listings. Only the manifold core's holes reach the inner jar, so the cable shares the back hole with `tube-reagent-pump-y`: 8 mm tube, 3.5 mm cable and 0.3 mm between them in the 12 mm hole. A 4 mm cable would not fit. That tube ends at the core's underside so the sleeve can hang beside it, tip 6.6 mm above the stir paddle's blades. The dongle is the blue USB-A stick of `docs/media/ML_case_cabled.jpeg`, its body sized from that photo; its plug sits in the lower socket's USB-A opening (standard 12.5 x 5.12 mm, tongue left out).
- The circulation pump model's two nozzles sit front and back. The docs and the photo `docs/media/pumps-unit/pumps-unit-complete-rear.jpg` have them top and bottom. Turning the model would push its ears through the box's front wall, so the model is at fault. The front nozzle goes to the manifold, the back one to the coil.
- The stir rod mount's left and right screw holes sit about 0.7 mm off the manifold core's, so those two screws cut the core's hole walls (3.6 and 4.1 mm³). The mount is placed by its back hole, which lines up. The fix belongs in the parts repo's STEP files.
- The circulation tubes end 45 mm below the manifold lid's top. Straight down from the lid's holes they would meet the inner jar's band, so "a couple inches below the liquid's surface" is not modelled.
- The stir rod mount's screw holes are 3.0 mm across, the same as the M3 thread (the lid's and core's are 3.2 mm), so each of its three screws overlaps it by 3.7 to 4.0 mm³ along the thread. The fix belongs in the parts repo's STEP file.
- The inner jar (`parts/mason-jar-6oz-regular-mouth.py`) is a shaped approximation that keeps the earlier model's 81 mm height; the parts list names no jar, and Ball's quilted half-pint (6 oz to the neck) is about 98 x 70 mm. Its 61 mm finish and thread fit the inner band (`mason-jar-band-regular-mouth.py`), which is smaller than a real 70 mm regular-mouth band, so the manifold core's 66 mm disc sits on top of the band instead of inside it. The jar's thread is phased to the band's for their current ports; `thread_start` in the script says how to measure it again.
- `hot-unit-heater` is a single solid of about 1300 faces. Exact booleans against it can take minutes; screen with plane sections first.

## Conventions

- Keep comments in `partcad.yaml` and `.assy` files short.
- Keep commit messages concise: a short subject and at most a few short body lines.
- Never commit API keys or local output such as `rendered/`.
