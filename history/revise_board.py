"""Reproduce V3.1 H1 from the preserved ordered project. Run with KiCad Python."""
from pathlib import Path
import pcbnew, shutil, json, re, csv
ROOT=Path(__file__).resolve().parents[3]
SRC=ROOT/'outputs/v31-pcb-review'
OUT=Path(__file__).resolve().parent
BASE='CREWLINE-PRIM-PCB-001'
STD=Path('/Applications/KiCad/KiCad.app/Contents/SharedSupport')
LIB=OUT/'V31_H1.pretty'
LIB.mkdir(exist_ok=True)
shutil.copytree(SRC/'models',OUT/'models',dirs_exist_ok=True)
for ext in ['kicad_sch','kicad_pro']:
 shutil.copy2(SRC/f'{BASE}.{ext}',OUT/f'{BASE}.{ext}')
b=pcbnew.LoadBoard(str(SRC/f'{BASE}.kicad_pcb'))
selections={'J3':(5,'1836325','1836105'),'J5':(10,'1836370','1836150'),'J7':(4,'1836312','1836095'),'J8':(5,'1836325','1836105')}
changes={}
uuids={}
pinmap=[]
for ref,(n,mpn,plug) in selections.items():
 old=b.FindFootprintByReference(ref)
 footprint=f'PhoenixContact_MCV_1,5_{n}-G-5.08_1x{n:02}_P5.08mm_Vertical'
 name=f'MCV_1.5_{n}_5.08_Pad2.6'
 libid=f'V31_H1:{name}'
 new=pcbnew.FootprintLoad(str(STD/'footprints/Connector_Phoenix_MC_HighVoltage.pretty'),footprint)
 new.SetFPID(pcbnew.LIB_ID('V31_H1',name))
 # Preserve the original copper pad boundary. Use the supplier 1.2 mm plated hole.
 for p in new.Pads():
  p.SetSize(pcbnew.VECTOR2I(pcbnew.FromMM(2.6),pcbnew.FromMM(2.6)))
  p.SetDrillSize(pcbnew.VECTOR2I(pcbnew.FromMM(1.2),pcbnew.FromMM(1.2)))
 for m in new.Models():
  source=STD/'3dmodels'/m.m_Filename.split('}/',1)[1]
  dst=OUT/'models'/source.parent.name/source.name
  dst.parent.mkdir(exist_ok=True)
  shutil.copy2(source,dst)
  m.m_Filename='${KIPRJMOD}/models/'+source.parent.name+'/'+source.name
 pcbnew.PCB_IO_MGR.FindPlugin(pcbnew.PCB_IO_MGR.KICAD_SEXP).FootprintSave(str(LIB),new)
 # KiCad model iteration returns copies. Resolve the saved path explicitly.
 saved_fp=LIB/(name+'.kicad_mod')
 saved_fp.write_text(saved_fp.read_text().replace('${KICAD10_3DMODEL_DIR}/','${KIPRJMOD}/models/'))
 new.SetPosition(old.GetPosition())
 new.SetOrientation(old.GetOrientation())
 uuids[new.m_Uuid.AsString()]=old.m_Uuid.AsString()
 new.SetPath(old.GetPath())
 new.SetAttributes(old.GetAttributes())
 new.SetFields({f.GetName():f.GetText() for f in old.GetFields()})
 new.SetField('MPN',mpn)
 new.SetField('Manufacturer','Phoenix Contact')
 new.SetField('Mating plug',plug)
 new.SetField('LCSC Part','')
 url='https://www.phoenixcontact.com/us/products/'+mpn
 new.SetField('Datasheet',url)
 new.SetField('Description',f'{n}-position vertical pluggable signal header, 5.08 mm pitch, 8 A nominal')
 new.SetReference(ref)
 new.SetValue(old.GetValue())
 # Keep known readable reference locations. All procurement fields are hidden.
 new.Reference().SetPosition(old.Reference().GetPosition())
 new.Reference().SetTextAngle(old.Reference().GetTextAngle())
 new.Reference().SetTextSize(old.Reference().GetTextSize())
 new.Reference().SetTextThickness(old.Reference().GetTextThickness())
 for field in new.GetFields():
  if field.GetName() not in ['Reference']:
   field.SetVisible(False)
 oldpads={p.GetNumber():p for p in old.Pads()}
 for p in new.Pads():
  o=oldpads[p.GetNumber()]
  assert p.GetPosition()==o.GetPosition(),(ref,p.GetNumber())
  p.SetNet(o.GetNet())
  uuids[p.m_Uuid.AsString()]=o.m_Uuid.AsString()
  pinmap.append({'reference':ref,'pin':p.GetNumber(),'net':p.GetNetname(),'x_mm':pcbnew.ToMM(p.GetPosition().x),'y_mm':pcbnew.ToMM(p.GetPosition().y),'hole_before_mm':1.3,'hole_after_mm':1.2,'header_mpn':mpn,'plug_mpn':plug})
 b.Remove(old)
 b.Add(new)
 changes[ref]={'Footprint':libid,'Datasheet':url,'Description':new.GetFieldText('Description'),'MPN':mpn,'Manufacturer':'Phoenix Contact','Mating plug':plug,'LCSC Part':''}
f=b.FindFootprintByReference('F_MAIN1')
f.SetField('MPN','0297030.U')
f.SetField('Datasheet','https://www.littelfuse.com/products/fuses-overcurrent-protection/fuses/automotive-fuses/blade-fuses-shunt/mini/297/0297030-u')
changes['F_MAIN1']={'MPN':'0297030.U','Datasheet':f.GetFieldText('Datasheet')}
for field in f.GetFields():
 if field.GetName() not in ['Reference','Value']:field.SetVisible(False)
b.GetTitleBlock().SetRevision('V3.1-H1')
pcbnew.SaveBoard(str(OUT/f'{BASE}.kicad_pcb'),b)
path=OUT/f'{BASE}.kicad_pcb'
content=path.read_text().replace('${KICAD10_3DMODEL_DIR}/','${KIPRJMOD}/models/')
for a,b_id in uuids.items():content=content.replace(a,b_id)
path.write_text(content)
# Patch only root placed symbol objects. Do not rewrite library symbols or connectivity.
s=(OUT/f'{BASE}.kicad_sch').read_text()
def spans(text):
 depth=0;quoted=False;escaped=False;start=0
 for i,ch in enumerate(text):
  if quoted:
   if escaped:escaped=False
   elif ch=='\\':escaped=True
   elif ch=='"':quoted=False
  elif ch=='"':quoted=True
  elif ch=='(':
   if depth==1:start=i
   depth+=1
  elif ch==')':
   if depth==2:yield start,i+1
   depth-=1
for a,z in reversed(list(spans(s))):
 block=s[a:z]
 if not block.startswith('(symbol\n'):continue
 match=re.search(r'\(property "Reference" "([^"]+)"',block)
 if not match or match.group(1) not in changes:continue
 for k,v in changes[match.group(1)].items():
  pattern=r'(\(property '+re.escape(json.dumps(k))+r' )"(?:[^"\\]|\\.)*"'
  if re.search(pattern,block):block=re.sub(pattern,lambda m:m.group(1)+json.dumps(v),block,count=1)
  else:
   prop=f'\n\t\t(property {json.dumps(k)} {json.dumps(v)} (at 0 0 0) (hide yes) (effects (font (size 1.27 1.27))))'
   block=block[:-1]+prop+'\n\t)'
 s=s[:a]+block+s[z:]
(OUT/f'{BASE}.kicad_sch').write_text(s)
(OUT/'fp-lib-table').write_text('(fp_lib_table\n  (version 7)\n  (lib (name "V31_H1")(type "KiCad")(uri "${KIPRJMOD}/V31_H1.pretty")(options "")(descr "V3.1 H1 verified header pattern with original 2.6 mm pads"))\n)\n')
with (OUT/'signal-pin-map.csv').open('w',newline='') as fh:
 w=csv.DictWriter(fh,fieldnames=list(pinmap[0]));w.writeheader();w.writerows(pinmap)
(OUT/'revision-changes.json').write_text(json.dumps(changes,indent=2)+'\n')
print(json.dumps({'output':str(OUT),'changed_headers':list(selections),'preserved_signal_pin_centres':len(pinmap),'tracks':len(b.GetTracks()),'zones':len(b.Zones())}))
