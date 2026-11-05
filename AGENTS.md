# AGENTS.md

Notes for agents and contributors working on the PartCAD model of the MicroLab.

## Layout

- `partcad.yaml` (root) declares the package and imports `hardware/v6` as the `v6` package, with `includePaths: [".."]` so it can read `hardware/urls.j2`.
- `hardware/v6/partcad.yaml` defines the sketches, interfaces, parts and assemblies.
- `hardware/v6/parts/` holds the CadQuery part scripts. The `.assy` files in `hardware/v6/` place parts by connecting their ports.
- `docs/microlab-parts-list.xlsx` is the bill of materials. Its part IDs (e.g. `TC-CTB`) are not linked to PartCAD part names.

## Running PartCAD

Run `pc` from the repository root. From `hardware/v6` the `urls.j2` import fails.

- Parts: `pc test v6:<part>`, `pc render -t png -O <dir> v6:<part>`.
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
3. Before committing: `--full`, which measures all candidate pairs and runs `pc test --assembly -f interference`.

The STEP export loses instance names. Parts are listed by tree path (e.g. `1/3/16`), in the order of the `.assy` links. Use `--list` to identify them.

## Sweeps

- A `type: sweep` part sweeps a sketch along one Bezier curve built from its `axis` points, starting at the sketch origin. More points raise the curve's degree; they don't add separate sections, so a sweep can't have exactly straight segments joined to an arc.
- A curved path with exactly vertical end tangents crashes OCC's pipe sweep. Tilt the control points slightly (0.5 mm in X works).

## Design constraints

- Reactor core: the outer jar is upright, with its rim against the manifold lid's underside and its band resting on the upper neck flange. The two neck flanges clamp the stand's C-part (8 mm thick). The inner jar hangs from its band under the manifold core.
- `parts/mason-jar-32oz-wide-mouth.py` is shared by the reactor core's outer jar and the cooling unit's jar.
- Stir paddle: it must not touch the inner jar's bottom or sides (`docs/assembly-reactor-unit.md`). Its `paddle_length` and `shaft_length` are part parameters; the builder cuts the real shaft to fit.

## Known issues

- `stir-rod`, `stir-rod-motor` and `stir-rod-coupler` are CadQuery approximations with guessed dimensions, not models of the linked products. `stir-rod.py` says where each value comes from.
- The pumps box's front slot sits 2 mm higher than its side slots allow for part C's tab. C is raised 2.1 mm (H `eye-front-1`, with the stand's `core-holder`) and floats about 1.85 mm above its seat on H.
- The pump models (`peristaltic-pump.step`, `circulation-pump.step`) disagree with the pumps box, which is the built 4TV design:
  - The circulation pump's barrel is 27.2 mm across in the box's 27.0 mm hole (34 mm³ each).
  - The peristaltic pump's hole pattern is 37.5 x 54 mm against the box's 37.9 x 55, so its lower M3 screws cut into the hole walls. `pc test` skips these screws as invalid solids.
  - The fix belongs in the parts repo's STEP files.
- The peristaltic pumps stand 1 mm off the box's front: their head screws stick out 1 mm behind the mounting plate.
- The control box holds the Pi by four corner posts with catches, built for the Pi 3 Model B the docs call for (`CU-RPI`). The model uses `rpi4b`, the only Pi in the PartCAD index. The Pi 4's front USB stack sticks out 3 mm past the board edge, but the post's inner face is only 1.5 mm past it, so they overlap by 10 mm³. The Pi can't shift to clear it. Whether a real Pi 3's Ethernet jack in that corner clears the post is unmeasured.
- The flat lid's left screw hole is at (-90.5, -88.5) in its STEP, not the mirror of the right one at (91, -89), so it sits 0.7 mm off the box's hole. The screw follows the box's hole and cuts 0.34 mm³ of the lid.
- The control unit's boards and connectors (`relay-board`, `stepdown-converter`, `cnc-shield`, `rpi-lcd-35`, `lever-connector`, `panel-connector-*`, `usb-panel-socket`, `barrel-jack`) are CadQuery approximations. Outlines come from the cases and box cut-outs they fit; their scripts say what is measured and what is guessed.
- The relay case, the converter case and the lever connector are placed only in the flat box, the one the build guide describes. The regular box's floor holes fit none of them.
- The docs screw the converter case to the flat box's floor, but the box has no hole there, so the case rests unscrewed. The lever connector's two screws are left out: 12 mm M3 screws through its (guessed) 3 mm ears would come out under the floor.
- `cold-unit-tube` and `hot-unit-tube` are CadQuery approximations of the hand-bent coils; their scripts say where each value comes from.
- `hot-unit-heater` is a single solid of about 1300 faces. Exact booleans against it can take minutes; screen with plane sections first.

## Conventions

- Keep comments in `partcad.yaml` and `.assy` files short.
- Keep commit messages concise: a short subject and at most a few short body lines.
- Never commit API keys or local output such as `rendered/`.
