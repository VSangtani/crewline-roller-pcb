# Manufacturing outputs

Generated from the board with `kicad-cli` 10.0.6. Regenerate all three after any board change.

- `CREWLINE-PRIM-PCB-001-gerbers.zip` is the fabrication set: four copper layers, both masks, both
  paste layers, both silkscreens, the outline, the PTH and NPTH drill files with their maps, and the
  job file. Upload this one file to JLCPCB.
- `jlc-bom.csv` is the assembly bill of materials in JLCPCB's column order. It lists only the 23
  lines JLCPCB fits. J4 and the six fuse holders are customer fitted and are not in it.
- `jlc-cpl.csv` is the placement file in JLCPCB's column order, 68 parts, all on the top side.
- `gerbers/` holds the unzipped set for inspection.

Order settings: 4 layers, 1.6 mm, standard stackup, green mask, white silkscreen, surface finish
to taste, 2 oz outer copper is not required. Assembly: top side, through-hole parts by wave
soldering. In the placement preview check the orientation of every polarised part against the
silkscreen before confirming: the relays, D1, D2, the twelve SOD-323 diodes, TVS1, Q1, Q_MODE1,
the fourteen LEDs, J1 and the five Micro-Fit headers.
