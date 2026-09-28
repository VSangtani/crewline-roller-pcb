# V3.1 H1 PCB assembly

Preserve the ordered board outline, pad centres, net assignments, copper tracks and relay circuit.
Replace J3, J5, J7 and J8 with vertical Phoenix MCV 1.5 headers at 5.08 mm pitch.
Use the official 1.2 mm plated hole and retain the original 2.6 mm copper pad boundary.
Keep J4 and J1 power connectors unchanged.

Export the native KiCad assembly as pcb.step with its original coordinate system.
The PCB bottom is Z 0 mm. Positive Z is above the PCB.
STEP uses negative Y for the positive KiCad board Y direction.
Trim only the C1 display model lead tails to 3 mm below its mounting plane.
The supplier capacitor model has 17 mm untrimmed tails that do not describe the installed part.
Do not change the capacitor body, pin positions or electrical design.

Model mating plugs as labelled conservative envelopes because the exact supplier CAD is not available.
The step.parts searches for MC plugs and MVSTBR returned no exact plug models.
Use native KiCad header models.
Use the supplier plug bounds of n times 5.08 mm, 11.1 mm and 15.5 mm.
The conservative mated height is 10 mm plus 15.5 mm above the PCB top.
Use 17.1 mm across the pin row to include 3 mm position uncertainty on each side.
This is a fit reservation, not the final shape of the plug or its strain relief.
Reserve a further 15 mm vertical travel with the lid removed for plug removal.
Check the DRC difference, pin map, native netlist, copper invariants, exported model bounds and top render.
