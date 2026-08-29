"""Estrae esemplari completi (JSON grezzo) dei circuiti ricorrenti."""
import json, os, re
from collections import defaultdict

SOL = r"C:\OMRON\Data\Solution"
OUT = r"C:\Users\tecni\Claude\sysmac-mcp\library"
PREF = ["Scrubber Ammoniaca", "Cappa Ceramiche V2", "Scrubber Tower", "Scrubber FL530",
        "Abbattimento_Fumi_Fuxa", "CAPPA_ETCH_RELASE2", "Scrubber Biogas 2Pump_V1"]

ent_re = re.compile(r'<Entity ([^>]+)>')
attr_re = re.compile(r'(\w+)="([^"]*)"')

def categories(line, r):
    cats = []
    txt = line
    if '"Name":"TON"' in txt: cats.append("ton_ritardo")
    if '"Name":"TOF"' in txt: cats.append("tof")
    if '"Name":"Contatore"' in txt: cats.append("contaore_fb")
    if '"Name":"Controllo_EV"' in txt: cats.append("elettrovalvola_fb")
    if '"Name":"PIDAT"' in txt: cats.append("pid")
    if '"Name":"TimeProportionalOut"' in txt: cats.append("time_proportional")
    if '"Name":"CTD"' in txt: cats.append("contatore_ctd")
    if 'Get1minClk' in txt or 'Get1sClk' in txt or 'Get100msClk' in txt: cats.append("clock")
    if 'ScaleTrans' in txt: cats.append("scala_analogica")
    if '@MovingAverage' in txt: cats.append("media_mobile")
    if 'MTCP_Server' in txt: cats.append("modbus_tcp")
    if '"Name":"MC_Power"' in txt: cats.append("motion_power")
    if '@Inc' in txt and '"Up":true' in txt: cats.append("conteggio_impulsi")
    return cats

byname = {}
for guid in os.listdir(SOL):
    man = os.path.join(SOL, guid, guid + ".manifest")
    if os.path.exists(man):
        m = re.search(r'solutionName="([^"]+)"', open(man, encoding="utf-8-sig").read())
        if m: byname.setdefault(m.group(1), guid)

exemplars = defaultdict(list)
MAX_PER_CAT = 2
for pname in PREF:
    guid = byname.get(pname)
    if not guid: continue
    pdir = os.path.join(SOL, guid)
    otxt = open(os.path.join(pdir, guid + ".oem"), encoding="utf-8-sig", errors="ignore").read()
    for tag in ent_re.findall(otxt):
        a = dict(attr_re.findall(tag))
        if a.get("type") == "PouBody" and a.get("subtype") == "Ladder":
            f = os.path.join(pdir, a["id"] + ".xml")
            if not os.path.exists(f): continue
            for line in open(f, encoding="utf-8-sig", errors="ignore").read().splitlines():
                line = line.strip()
                if not line.startswith("{"): continue
                try: r = json.loads(line)
                except Exception: continue
                if "CLs" not in r: continue
                for c in categories(line, r):
                    if len(exemplars[c]) < MAX_PER_CAT:
                        exemplars[c].append({"project": pname, "section": a.get("name"), "cmt": r.get("CMT",""), "raw": r})

with open(os.path.join(OUT, "esemplari.json"), "w", encoding="utf-8") as f:
    json.dump(exemplars, f, ensure_ascii=False, indent=1)
for c, lst in sorted(exemplars.items()):
    print(f"{c}: {len(lst)}  ({'; '.join(x['project']+'/'+x['section'] for x in lst)})")
