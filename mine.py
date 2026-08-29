"""Miner: analizza tutti i progetti Sysmac in C:\OMRON\Data\Solution
e produce un catalogo dei rung ladder (JSON) + statistiche."""
import json, os, re, sys
from collections import Counter

SOL = r"C:\OMRON\Data\Solution"
OUT = r"C:\Users\tecni\Claude\sysmac-mcp\library"
os.makedirs(OUT, exist_ok=True)

ent_re = re.compile(r'<Entity ([^>]+)>')
attr_re = re.compile(r'(\w+)="([^"]*)"')

def parse_rung_line(line):
    try:
        return json.loads(line)
    except Exception:
        return None

def summarize_rung(r):
    contacts, coils, fbs, funcs, sts = [], [], [], [], []
    for el in r.get("CLs", []):
        t = el.get("__type")
        if t == "LD":
            v = el.get("Var", "")
            if el.get("Not"): v = "/" + v
            if el.get("Up"): v = "^" + v
            if el.get("Down"): v = "v" + v
            contacts.append(v)
        elif t == "ST":
            v = el.get("Var", "")
            if el.get("Set"): v = "S:" + v
            if el.get("Reset"): v = "R:" + v
            if el.get("Not"): v = "/" + v
            coils.append(v)
        elif t == "FB":
            prm = [f"{p.get('Arg')}={p.get('Var')}" for p in el.get("In", []) if p.get("__type") == "PRM"]
            fbs.append(f"{el.get('Name')}({el.get('Var','')};{','.join(prm)})")
        elif t == "IST":
            sts.append(el.get("TXT", ""))
        elif t == "F":
            prm = [f"{p.get('Arg')}={p.get('Var')}" for p in el.get("In", []) if p.get("__type") == "PRM"]
            funcs.append(f"{el.get('Name')}({','.join(prm)})")
    out = {"CMT": r.get("CMT", ""), "contacts": contacts, "coils": coils, "fbs": fbs, "funcs": funcs}
    if sts:
        out["st"] = sts
    return out

catalog = []
fb_counter = Counter(); func_counter = Counter()
n_proj = 0; n_rungs = 0

for guid in os.listdir(SOL):
    pdir = os.path.join(SOL, guid)
    if not os.path.isdir(pdir):
        continue
    man = os.path.join(pdir, guid + ".manifest")
    oem = os.path.join(pdir, guid + ".oem")
    if not (os.path.exists(man) and os.path.exists(oem)):
        continue
    try:
        mtxt = open(man, encoding="utf-8-sig").read()
        m = re.search(r'solutionName="([^"]+)"', mtxt)
        pname = m.group(1) if m else "(senza nome)"
        otxt = open(oem, encoding="utf-8-sig", errors="ignore").read()
    except Exception:
        continue
    n_proj += 1
    proj = {"project": pname, "guid": guid, "sections": []}
    for tag in ent_re.findall(otxt):
        a = dict(attr_re.findall(tag))
        if a.get("type") == "PouBody" and a.get("subtype") == "Ladder":
            sec_id = a.get("id"); sec_name = a.get("name", "?")
            f = os.path.join(pdir, sec_id + ".xml")
            if not os.path.exists(f):
                continue
            try:
                raw = open(f, encoding="utf-8-sig", errors="ignore").read()
            except Exception:
                continue
            if not raw.lstrip().startswith("{"):
                continue
            rungs = []
            for line in raw.splitlines():
                line = line.strip()
                if not line.startswith("{"):
                    continue
                r = parse_rung_line(line)
                if not r or "CLs" not in r:
                    continue
                s = summarize_rung(r)
                rungs.append(s)
                n_rungs += 1
                if s.get("st"): func_counter["<ST inline>"] += 1
                for fb in s["fbs"]: fb_counter[fb.split("(")[0]] += 1
                for fn in s["funcs"]: func_counter[fn.split("(")[0]] += 1
            if rungs:
                proj["sections"].append({"name": sec_name, "file": sec_id, "rungs": rungs})
    if proj["sections"]:
        catalog.append(proj)

with open(os.path.join(OUT, "catalog.json"), "w", encoding="utf-8") as f:
    json.dump(catalog, f, ensure_ascii=False, indent=1)

with open(os.path.join(OUT, "stats.txt"), "w", encoding="utf-8") as f:
    f.write(f"progetti con ladder: {len(catalog)} (su {n_proj})\nrung totali: {n_rungs}\n\n")
    f.write("=== FB piu usati ===\n")
    for k, v in fb_counter.most_common(40): f.write(f"{v:6d}  {k}\n")
    f.write("\n=== Funzioni piu usate ===\n")
    for k, v in func_counter.most_common(40): f.write(f"{v:6d}  {k}\n")

print(f"progetti con ladder: {len(catalog)}/{n_proj}, rung totali: {n_rungs}")
print("catalogo:", os.path.join(OUT, "catalog.json"))

