"""Native V3.1 H1 PCB with conservative mating-plug fit reservations.
The orange parts are supplier-dimension envelopes, not detailed plug CAD.
"""
from pathlib import Path
from build123d import import_step, Box, Align, Axis, Color
from cadpy.assembly import AssemblyHelper
ROOT=Path(__file__).resolve().parent
PCB_TOP=1.63
HEADERS={'J3':(5,62.5,-131.0,-90,'1836105'),
         'J5':(10,69.58,-173.0,0,'1836150'),
         'J7':(4,121.5,-173.0,0,'1836095'),
         'J8':(5,142.5,-125.66,90,'1836105')}
def plug_envelope(n):
    # Supplier MC plug: width n*5.08, depth 11.1, mating-axis length 15.5.
    # Add 3 mm each side across the pin row for unknown exact offset.
    return Box(n*5.08,17.1,15.5,align=(Align.MIN,Align.CENTER,Align.MIN)).translate((-2.54,0,PCB_TOP+10))
def gen_step():
    asm=AssemblyHelper('V3.1 H1 PCB and conservative plug reservations')
    board=asm.add(import_step(ROOT/'pcb.step'),'Native KiCad PCB with vertical signal headers')
    for ref,(n,x,y,a,mpn) in HEADERS.items():
        p=plug_envelope(n).rotate(Axis.Z,a).translate((x,y,0))
        p.label=f'{ref} plug {mpn} conservative envelope'
        item=asm.add(p,p.label)
        item.color=Color(0.95,0.55,0.12,0.4)
    return asm.build()
