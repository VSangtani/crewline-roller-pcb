# Board tools

Run these with the KiCad Python interpreter, `/usr/bin/python3.14` on the design machine.
They write their working files to `tools/work/`.

- `kp.py` loads pcbnew and repairs its Python 3.14 iterators.
- `router.py` routes every connection that DRC reports as missing, on F.Cu and B.Cu,
  with a grid maze search that keeps the clearance rules, the mounting hole washer areas
  and a 2 mm edge margin. `router.py NET` limits it to one net. `router.py --pair A B`
  routes B in the corridor beside A. It records what it created in `work/router-created.json`.
- `ripup.py NET...` removes what the router created for those nets, so they can be routed again.

Always finish with `kicad-cli pcb drc` and read the report. The scripts do not replace it.
