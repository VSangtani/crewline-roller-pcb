"""Remove the router-created items of one net and drop them from the record."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kp import *
HERE = os.path.dirname(os.path.abspath(__file__))
SP = os.path.join(HERE, 'work')
PCB = os.path.join(HERE, '..', 'CREWLINE-PRIM-PCB-001.kicad_pcb')
nets = set(sys.argv[1:])
rec = SP + '/router-created.json'
created = set(json.load(open(rec)))
b = pcbnew.LoadBoard(PCB); zl = zones(b)
gone = set(); k = 0
for t in tracks(b):
    u = t.m_Uuid.AsString()
    if u in created and t.GetNetname() in nets:
        b.Remove(t); gone.add(u); k += 1
pcbnew.ZONE_FILLER(b).Fill(zl); b.Save(PCB)
json.dump(sorted(created - gone), open(rec, 'w'))
print('removed', k)
