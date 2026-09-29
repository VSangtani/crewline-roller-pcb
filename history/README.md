# V3.1 H1 connector revision

This revision replaces 4 sideways signal terminals with vertical pluggable headers.
It retains the ordered board outline, relay circuit, all pin centres and all net assignments.
It retains J1 and J4 for power.
It does not establish a 20 A rating for the board.

## Files

- `CREWLINE-PRIM-PCB-001.kicad_pcb` is the revised native board.
- `CREWLINE-PRIM-PCB-001.kicad_sch` is the matching native schematic.
- `schematic.pdf` is the schematic export.
- `pcb-top.png` is the native KiCad top render.
- `pcb.step` is the native KiCad solid model.
- `pcb_mated.step` adds conservative orange envelopes for the mating plugs.
- `signal-pin-map.csv` gives every changed connector pin and its unchanged net.
- `bom-delta.csv` lists the replacement headers, plugs and main fuse.
- `validation.json` records the electrical and geometry checks.
- `drc-before.json` and `drc-after.json` preserve both rule checks.
- `V31_H1.pretty` contains the local footprints.

## Selected connectors

| Board connector | Function | Header | Mating plug | Positions |
|---|---|---|---|---:|
| J3 | DIO | Phoenix 1836325 | Phoenix 1836105 | 5 |
| J5 | CAN | Phoenix 1836370 | Phoenix 1836150 | 10 |
| J7 | Brake | Phoenix 1836312 | Phoenix 1836095 | 4 |
| J8 | Enable circuit | Phoenix 1836325 | Phoenix 1836105 | 5 |

Each header and plug has an 8 A nominal rating.
These connectors carry signals and relay-coil current in the present circuit.
They do not carry the complete kit load.
Use the separate power review for J1, J4, the converter and the 20 A supply path.

The selected MCV header has a 5.08 mm pitch and a 1.2 mm plated hole.
The copper pads retain their original 2.6 mm size.
The original terminal holes are 1.3 mm.
This package defines a new board revision with the supplier hole size.
A physical replacement on an existing board needs a solder-joint and fit check before batch work.

The larger MSTBVA family fails the first fit check at J5 and J7.
Its closed housings overlap at the existing connector positions.
The smaller MCV family avoids that conflict without a change to the pin positions.

## Harness and service access

The standard MC plug has its wire entry opposite its mating face.
With the vertical MCV header, the wires leave above the board.
Prepare each harness at the bench, then insert its plug from above.
The plug screws remain accessible before the harness enters the enclosure.
The plug has no positive latch.
Use a removable screwed restraint to prevent upward movement under vibration.
Support the board beside the connector during insertion and removal.
The manufacturer gives approximately 5 N withdrawal force per contact for this family.

J3 and J8 use the same 5-way plug.
Their common shape does not prevent an incorrect connection.
Mark both ends of each harness with its connector reference and function.
Use different coding positions for DIO and ENABLE after a sample fit check.
Phoenix lists CP-MSTB 1734634 coding profiles for the MC 1.5 family.
The final slot positions and matching header treatment remain a physical check.
Do not cut an electrical contact to create a key.

The plug accepts flexible wire from 0.08 mm² to 1.5 mm².
With an insulated ferrule, the listed range is 0.25 mm² to 0.5 mm².
With an uninsulated ferrule, the listed range is 0.25 mm² to 1.5 mm².
Choose the wire size from the circuit current and harness conditions.
Strip 7 mm of insulation.
Tighten each screw to 0.22 Nm through 0.25 Nm.
Remove power before insertion or removal.

## CAD limits

The exact supplier plug CAD was not available from the searched catalogues.
The orange plug parts are conservative fit envelopes.
They are not detailed connector shapes.
The envelope height is 25.5 mm above the PCB top.
The envelope length is the number of contacts times 5.08 mm.
The envelope width across the row is 17.1 mm.
This width includes 3 mm on each side for an uncertain mating offset.
Reserve another 15 mm of vertical travel for removal with the lid removed.
This travel is an assembly allowance, not a supplier specification.
Do not use the envelope surface as an exact restraint contact surface.

The native STEP export omits 23 existing models that only have VRML geometry.
These include J1, Q1, small diodes and test points.
The top render includes those models.
The complete list is in `validation.json`.
The enclosure must retain a separate allowance for J1 and its cable.
C1 uses a derived display model with its lead tails trimmed to 3 mm.
Its original supplier model has 17 mm lead tails.
The capacitor body and electrical footprint remain unchanged.

## Main fuse

F_MAIN1 now specifies Littelfuse 0297030.U, from the MINI 297 family.
The original 0287030.PXCN belongs to the wider ATOF family.
The PCB footprint is for a Keystone 3568 MINI holder.
The 30 A fuse value remains unchanged in this revision.
This correction fixes the fuse family only.
It does not approve the existing 30 A protection choice for the wiring or PCB.

## Validation

The rule checks have the same findings before and after the revision.
Both contain 30 board warnings and 24 schematic-parity warnings.
Both contain zero errors and zero unconnected items.
The remaining findings concern source library metadata, population differences, duplicate mechanical references and existing silkscreen.

The comparison confirms all 379 tracks and vias remain unchanged.
Every named pad retains its position and net.
The exported schematic has the same net graph as the source.
The native PCB STEP contains 67 valid solids.
Its bounds are X 51.5 to 152.5 mm, Y −180.5 to −48.5 mm, Z −1.87 to 22.03 mm.
The mated assembly contains 71 solids and passes the CAD inspection.
No plug envelope has a positive-volume intersection with the exported board solids.
This check excludes the 23 omitted VRML models.
The native top render, STEP snapshot and schematic PDF were inspected.
The schematic export retains the source population flags.
Several fitted-looking parts have a source DNP flag and appear crossed out.
Resolve these population differences before the schematic becomes a build instruction.

Before the next board order, check the physical plug fit and the coding scheme.
Confirm the fitted component population against the repeat order.
Perform continuity and manual-mode tests before the vehicle receives power.
Verify the power and stop functions with the agreed vehicle test procedure.
The header revision does not change or validate those functions.

## Reproduction

Run `revise_board.py` with the bundled KiCad Python interpreter.
Run the native DRC with zone refill and save the revised board.
Run `prepare_models.py` with `work/cad-python` to restore the trimmed display model.
Export `pcb.step` through the native KiCad CLI.
Use absolute output paths with the KiCad export command.
Run the CAD generator on `pcb_mated.py`.

## Supplier references

- [MCV 5-way header 1836325](https://www.phoenixcontact.com/en-us/products/pcb-header-mcv-15-5-g-508-1836325)
- [MCV 10-way header 1836370](https://www.phoenixcontact.com/en-us/products/pcb-header-mcv-1510-g-508-1836370)
- [MCV 4-way header 1836312](https://www.phoenixcontact.com/en-us/products/pcb-header-mcv-15-4-g-508-1836312)
- [MC 5-way plug 1836105](https://www.phoenixcontact.com/en-us/products/pcb-plug-mc-15-5-st-508-1836105)
- [MC 10-way plug 1836150](https://www.phoenixcontact.com/en-us/products/pcb-plug-mc-1510-st-508-1836150)
- [MC 4-way plug 1836095](https://www.phoenixcontact.com/en-us/products/pcb-plug-mc-15-4-st-508-1836095)
- [CP-MSTB coding profile 1734634](https://www.phoenixcontact.com/en-gb/products/coding-element-cp-mstb-1734634)
- [Phoenix catalogue for coding compatibility](https://assets.phoenixcontact.com/file/b0f2db1c-a2f9-4a58-b43f-3cf8a6ec2121/media/original?1789158_DC_Catalog_2025-2027.pdf=)
- [Keystone 3568 MINI holder](https://www.keyelco.com/product.cfm/product_id/306)
- [Littelfuse 297 MINI family](https://www.littelfuse.com/~/media/automotive/datasheets/fuses/passenger-car-and-commercial-vehicle/blade-fuses/littelfuse_mini_datasheet.pdf)
