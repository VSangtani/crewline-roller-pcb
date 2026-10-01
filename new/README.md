# Crewline primary board, brake and E-stop revision

This folder holds the live KiCad 10 project. The revision label on the board is still V3.1-H1.
The previous revision and its reports are in `../history/`.

## What changed since the previous revision

- J7 grows from 4 to 7 positions and carries the brake lines.
- J10 is new, 7 positions, and carries the E-stop lines.
- J8 is removed. Its arming loop now sits on J3 pins 2 to 5, beside MODE_SEL on pin 1.
- J6 is now the seat sensor connector, 3 positions with one spare.
- J2 and all test points are removed.
- J3, J5, J6, J7 and J10 are Molex Micro-Fit 3.0 single-row vertical through-hole headers.
  J1 (XT60) and J4 (Phoenix MKDS screw terminal block) are unchanged.
- Four relays are new: K_BRAKE_CAT1, K_BRAKE_CAT2, ESTOP_COM_RELAY1 and ESTOP_COM_RELAY2.
  The existing brake relay is now K_BRAKE_SEAT_BOMAG1.
- All relay logic for brake and E-stop sits on the child sheet `brake-estop.kicad_sch`.
- D1, the flyback diode across the POWER1 coil, is turned round so its cathode is on ARMED_HOT.
  The original drawing had it forward-biased across the coil.
- R_ARMED_PD1 is removed. The POWER1 coil already ties ARMED_HOT to ground.
- The six red LEDs use the standard LED symbol, pin 1 cathode, so they match the footprint mark
  and the assembler's library convention.
- The six DNP flags on C1, J1, J9 and the three DPDT relays are cleared. All are fitted.
- Every part number was checked against the JLCPCB parts library. See the BOM section.
- The custom symbols and footprints live in `lib/` and are registered in the project library tables.
- The board is 136 by 132 mm. It grew 56.5 mm to the right for the Phoenix headers, then shrank 21.5 mm after the Molex swap.

## Files

- `CREWLINE-PRIM-PCB-001.kicad_pro`, `.kicad_sch`, `.kicad_pcb` are the project, root sheet and board.
- `brake-estop.kicad_sch` is the child sheet with the relay logic.
- `schematic.pdf` is the two-page schematic export.
- `pcb-top.png` and `pcb-bottom.png` are the native renders.
- `pcb.step` is the native solid model.
- `bom.csv` is the bill of materials, grouped by value, footprint and part number.
- `netlist.xml` is the schematic netlist.
- `erc.json` and `drc.json` are the rule check reports.
- `lib/` holds the project symbol and footprint libraries. `V31_H1.pretty` holds the Phoenix headers
  of the previous revision, kept for reference.
- `models/` holds the 3D models.
- `tools/` holds the grid router and its helpers. See `tools/README.md`.

## Connectors

| Ref | Function | Part | Mating housing | Fitted by |
|---|---|---|---|---|
| J1 | Battery | Amass XT60PW-M | XT60 plug | JLCPCB |
| J3 | Mode select and arming loop, 5 way | Molex 43650-0515 | 43645-0500 | JLCPCB |
| J4 | Power outputs, 10 way screw terminal | Phoenix MKDS 1,5/10-5,08, 1715802 | none, screw | Customer |
| J5 | CAN cables, 10 way | Molex 43650-1015 | 43645-1000 | JLCPCB |
| J6 | Seat sensor, 3 way | Molex 43650-0315 | 43645-0300 | JLCPCB |
| J7 | Brake, 7 way | Molex 43650-0715 | 43645-0700 | JLCPCB |
| J9 | Converter shield, 2 by 6 pin header | 2.54 mm header | shield | JLCPCB |
| J10 | E-stop, 7 way | Molex 43650-0715 | 43645-0700 | JLCPCB |

J7 and J10 take the same plug. Label both ends of each harness. Harness contacts are the Molex
43030 series, in the 18 to 20 AWG and 20 to 24 AWG versions, crimped with the Molex tool.

### Pin tables

| Pin | J3 | J6 | J7 | J10 |
|---|---|---|---|---|
| 1 | MODE_SEL | ECU_SEAT | BRAKE_JET | ESTOP_JOY_NG |
| 2 | +12V_GATED | SEAT | BRAKE_JOY | ESTOP_JOY |
| 3 | loop, joined to 4 | spare | BRAKE_ECU | ESTOP_ECU |
| 4 | loop, joined to 3 | | BRAKE_JOY_NF | ESTOP_REMOTE |
| 5 | ARMED_HOT | | BRAKE_JOY_NG | ESTOP_ECU_NF |
| 6 | | | BRAKE_ECU_NF | ESTOP_ECU_NF |
| 7 | | | BRAKE_ECU_NG | ESTOP_ECU_NG |

J10 pins 5 and 6 are the same net because ESTOP_JOY_NF is wired directly to ESTOP_ECU_NF.

| Pin | J5 | J4 |
|---|---|---|
| 1 | ECU_CANL | STARLINK_PWR_P |
| 2 | JET2_CANL | GND |
| 3 | JET2_CANH | JET_DIO_PWR_P |
| 4 | ECU_CANH | GND |
| 5 | JOY_CANH | LED_PWR_P |
| 6 | JET1_CANH | GND |
| 7 | JET1_CANH | JETSON_PWR_P |
| 8 | JET1_CANL | GND |
| 9 | JET1_CANL | STEER_PWR_P |
| 10 | JOY_CANL | GND |

J5 pins 6 and 7, and 8 and 9, are doubled so two cables can land on the JET1 bus without a splice.

## Relay coils

Every coil returns through MODE_SEL_DRV, which Q_MODE1 pulls low when MODE_SEL is high.

| Relay | Coil supply | Series diode |
|---|---|---|
| K_BRAKE_SEAT_BOMAG1 | +12V_KIT | none |
| K_BRAKE_CAT1 | +12V_KIT | none |
| K_BRAKE_CAT2 | BRAKE_JET | D_BRAKEJET_SER1 |
| ESTOP_COM_RELAY1 | +12V_KIT | none |
| ESTOP_COM_RELAY2 | ESTOP_REMOTE | D_ESTOPREMOTE_SER1 |

BRAKE_JET and ESTOP_REMOTE come from the Syslogic carrier outputs, which are isolated high-side
switches at 12 V maximum. The series diode blocks any reverse path into them. With MODE_SEL_DRV
floating near 12 V in manual mode, the two coils fed from those outputs see no useful voltage and
stay released. If a later carrier ever drives these lines from 24 V, or from a supply that is live
while the kit is disarmed, return those two coils through a relay contact instead of MODE_SEL_DRV.
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

- J5, J7 and J10 sit on the bottom edge between the mounting holes. J3 and J6 sit on the left edge.
- The seven DPDT relays sit in one row at Y 143.22 mm. Each has its flyback diode 3 mm above the
  coil pads and its LED and resistor above that.
- The inner layers are the ground plane (In1.Cu) and the +12V_KIT plane (In2.Cu). The front layer
  carries a ground fill in the gaps. Every pad on those nets joins its fill with thermal spokes.
- Track and via sizes follow the net classes: 2.5 mm tracks with 1.0/0.5 mm vias for +12V_GATED,
  1.0 mm tracks with 0.8/0.4 mm vias for +12V_KIT and the power outputs, 0.4 to 0.6 mm tracks with
  0.6/0.3 mm vias for signals.
- No track runs inside a mounting hole washer area or closer than 1.8 mm to the board edge.
- The mounting holes are H1 to H4 on a 120 by 115 mm rectangle: (60, 58), (180, 58), (60, 173)
  and (180, 173) in board coordinates. They are board-only footprints with no schematic symbol.
- The connector swap and the final relay routing were done by hand in the editor. The first routing
  pass used `tools/router.py`.

## BOM

`bom.csv` carries a manufacturer part number, an LCSC number and, where JLCPCB does not fit the
part, an Assembly field reading "Customer fitted". Every LCSC number was opened on the JLCPCB parts
page and checked for package, value, rating, stock and assembly type. Parts fitted by the customer
after assembly:

- J4, Phoenix 1715802, screw terminal block.
- F_MAIN1, F_STEER1, F_JET1, F_CONV1, F_DIO1 and F_LED1, Keystone 3568 blade fuse holders.
  The fuses themselves are not on the BOM: 30 A main, 15 A steering, 10 A Jetson, 10 A converter,
  5 A DIO and 3 A LED.

## Verification

- ERC reports one warning. ESTOP_ECU_NF and ESTOP_JOY_NF name the same net by design.
- DRC reports zero errors, zero warnings and zero unconnected items.
- Every pad net on the board was compared with the schematic netlist. All 245 match.
- The netlist was compared before and after every scripted schematic edit. Only the intended nets
  changed each time.
- An independent review of the schematic, the board and the BOM was run after the first routing.
- These checks are switched off in the project settings and were confirmed clean when switched on:
  ERC single_global_label, four_way_junction and footprint_filter; DRC missing_courtyard and
  footprint_type_mismatch. The track_not_centered_on_via check is switched on.

## Open items before manufacture

- Run Update PCB from Schematic once more so the footprint fields take the audited part numbers.
  Until then the parity check lists 52 field differences.
- Decide whether the six fuse holders stay customer fitted or move to a JLCPCB-stocked holder. A
  replacement must match the Keystone 3568 footprint: two 1.78 mm holes per terminal, 3.4 mm apart,
  with the terminals 9.92 mm apart.
- Bump the revision label before the order and add a revision text on the silkscreen. The schematic
  title blocks are empty.
- Confirm the harness contact and crimp tool part numbers from the Molex site before ordering.
- The Molex header 3D models are not installed on the design machine, so `pcb.step` and the renders show the five Micro-Fit headers as bare pads. Installing the KiCad 3D model package, `kicad-packages3d` on Arch, fixes this without any change to the project.
- Manufacturing outputs are not generated yet.

## Open questions for the original board designer

- JOY_TERM_R1 and STEER_TERM_R1 are both 120 ohm across JET1_CANH and JET1_CANL, which puts 60 ohm
  on that bus from this board alone. Both are fitted on the boards in service. A CAN bus normally has
  one 120 ohm terminator at each end and none in the middle. Was this intended, for example because
  the board sits at the end of two separate cable runs?
- D1 on the boards in service: the original drawing had it forward-biased across the POWER1 coil, so
  the fitted part is either reversed relative to the drawing or has failed open.

## Tools

The first routing pass was made with `tools/router.py` under the KiCad Python interpreter. Run the
rule check after every change. The router is not a substitute for it.
