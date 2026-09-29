from build123d import import_step, Solid, Plane, export_step
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
SRC=ROOT/'outputs/v31-pcb-review/models/Cap_1000uF.3dshapes/ECA1EM102.step'
OUT=Path(__file__).resolve().parent/'models/Cap_1000uF.3dshapes/ECA1EM102.step'
s=import_step(SRC)
keep=Solid.make_box(100,100,100,Plane(origin=(-50,-3,-50)))
s=s & keep
assert s.is_valid
s.label='C1_1000uF_leads_trimmed_to_3mm_for_assembly'
export_step(s,OUT)
print('C1 display lead tails trimmed to 3 mm; electrical footprint unchanged')
