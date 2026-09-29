# Crewline primary board, brake and E-stop revision

This folder holds the live KiCad 10 project. The revision label on the board is still V3.1-H1.
The previous revision and its reports are in `../history/`.

## What changed

- J7 grows from 4 to 7 positions and carries the brake lines.
- J10 is new, 7 positions, and carries the E-stop lines.
- Both use the Phoenix MCV 1.5 vertical header 1836341 with the MC 1.5 plug 1836121.
- Four relays are new: K_BRAKE_CAT1, K_BRAKE_CAT2, ESTOP_COM_RELAY1 and ESTOP_COM_RELAY2.
- The existing brake relay is now K_BRAKE_BOMAG1.
- All relay logic for brake and E-stop sits on the child sheet `brake-estop.kicad_sch`.
- Five test points are new: BRK_ECU_NG_TP1, BRK_ECU_NF_TP1, ESTP_ECU_TP1, ESTP_ECU_NG_TP1 and ESTP_ECU_NF_TP1.
- The six DNP flags on C1, J1, J9 and the three DPDT relays are cleared. All six parts are fitted.
- The custom symbols and footprints live in `lib/` and are registered in the project library tables.
- The board is 157.5 by 132 mm. It grew 56.5 mm to the right.

## Files

- `CREWLINE-PRIM-PCB-001.kicad_pro`, `.kicad_sch`, `.kicad_pcb` are the project, root sheet and board.
- `brake-estop.kicad_sch` is the child sheet with the relay logic.
- `schematic.pdf` is the two-page schematic export.
- `pcb-top.png` and `pcb-bottom.png` are the native renders.
- `pcb.step` is the native solid model.
- `bom.csv` is the bill of materials, grouped by value, footprint and part number.
- `netlist.xml` is the schematic netlist.
- `erc.json` and `drc.json` are the rule check reports.
- `lib/` holds the project symbol and footprint libraries. `V31_H1.pretty` holds the Phoenix headers with 2.6 mm pads.
- `models/` holds the 3D models.
- `tools/` holds the grid router and its helpers. See `tools/README.md`.

## Relay coils

Every coil returns through MODE_SEL_DRV, which Q_MODE1 pulls low when MODE_SEL is high.

| Relay | Coil supply | Series diode |
|---|---|---|
| K_BRAKE_BOMAG1 | +12V_KIT | none |
| K_BRAKE_CAT1 | +12V_KIT | none |
| K_BRAKE_CAT2 | BRAKE_JET | D_BRAKEJET_SER1 |
| ESTOP_COM_RELAY1 | +12V_KIT | none |
| ESTOP_COM_RELAY2 | ESTOP_REMOTE | D_ESTOPREMOTE_SER1 |

BRAKE_JET and ESTOP_REMOTE come from the Syslogic carrier outputs. Those outputs are isolated
high-side switches for 12 or 24 V. The series diode blocks any reverse path into them.
Each coil draws about 17 mA and each indicator LED about 5 mA.

## Brake behaviour

| Mode | BRAKE_JET | BRAKE_ECU | BRAKE_ECU_NG | BRAKE_ECU_NF |
|---|---|---|---|---|
| manual | any | BRAKE_JOY | BRAKE_JOY_NG | BRAKE_JOY_NF |
| autonomy | 12 V, released | BRAKE_JET | GND | open |
| autonomy | 0 V, applied, or Jetson dead | BRAKE_JET | open | GND |

## E-stop behaviour

ESTOP_ECU_NF is wired directly to ESTOP_JOY_NF.

| Mode | ESTOP_REMOTE | ESTOP_ECU | ESTOP_ECU_NG | ESTOP_ECU_NF |
|---|---|---|---|---|
| manual | any | ESTOP_JOY | ESTOP_JOY_NG | ESTOP_JOY_NF |
| autonomy | 12 V | ESTOP_JOY | ESTOP_JOY_NG | ESTOP_JOY_NF |
| autonomy | 0 V, or Jetson dead | GND | open | ESTOP_JOY_NF and ESTOP_JOY_NG, tied together |

In the E-stop stop state the NF line takes whatever the joystick NG line carries. It is not
grounded from the board. Confirm that the Bomag input accepts this before the first vehicle test.

## Board layout

- J5, J7 and J10 sit on the bottom edge between the mounting holes with a 1.5 mm gap between housings.
- J8, J6, the right-hand test point column and the right-hand mounting holes moved with the right edge.
- The seven DPDT relays sit in one row at Y 143.22 mm. Each has its flyback diode 3 mm above the coil pads and its LED and resistor above that.
- The right-hand test points form two columns at X 188 and X 202 mm.
- The inner layers stay as the ground plane and the +12V_KIT plane.
- New copper is on F.Cu and B.Cu only. Track widths follow the net classes: 2.5 mm for +12V_GATED, 0.4 mm for signals.
- No track runs inside a mounting hole washer area or closer than 1.8 mm to the board edge.

## Verification

- ERC reports one warning. ESTOP_ECU_NF and ESTOP_JOY_NF name the same net by design.
- DRC reports zero errors, zero warnings and zero unconnected items.
- Every pad net on the board was compared with the schematic netlist. All 271 match.
- The netlist was compared before and after every schematic edit. Only the intended nets changed.

## Open items before manufacture

- The current rating of the Syslogic digital outputs is in the product manual, not the datasheet. Confirm it covers 22 mA on each output.
- Check the plug coding scheme. J3 and J8 share a 5-way plug. J7 and J10 share a 7-way plug.
- The red LEDs use the stock 0805 footprint. Pad 1 is the anode on this board. The footprint mark says cathode. The boards in service work, so the assembler followed the pin numbers.
- The 20 A supply path through Q1 and the main fuse is unchanged and unreviewed.
- Manufacturing outputs are not generated yet.

## Tools

The board was routed with `tools/router.py` under the KiCad Python interpreter. Run the rule
check after every change. The router is not a substitute for it.
