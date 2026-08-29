# -*- coding: utf-8 -*-
"""
pins_from_db.py - ricava la FIRMA DEI PIN di ogni FB/funzione direttamente dai
rung dei progetti Sysmac, senza doverli campionare a mano con copia/incolla.

Nel JSON di un rung ogni blocco ha:
  In / Out : lista di pin, __type "PF" (power flow) o "PRM" (dato),
             Arg = nome pin, Type = tipo dato, IO = true se InOut.
Da qui si ricostruisce il <PinViewModel .../> del formato ladderSnippetXML.

Produce: sysmac-mcp\pins.json  { tipo: {kind, user, pins:[...]} }
"""
import json, os, re, sys, collections

SOL = r"C:\OMRON\Data\Solution"
OUT = r"C:\Users\tecni\Claude\sysmac-mcp\pins.json"
ent_re = re.compile(r'<Entity ([^>]+)>')
attr_re = re.compile(r'(\w+)="([^"]*)"')

sys.path.insert(0, r"C:\Users\tecni\Claude\sysmac-mcp")
from rung2spec import pick_latest, project_list, sections_of

# --- FB definiti dall'utente (entita' FunctionBlock nei progetti)
user_types = set()
for guid in os.listdir(SOL):
    f = os.path.join(SOL, guid, guid + ".oem")
    if not os.path.exists(f):
        continue
    try:
        t = open(f, encoding="utf-8-sig", errors="ignore").read()
    except OSError:
        continue
    for tag in ent_re.findall(t):
        a = dict(attr_re.findall(tag))
        if a.get("type") == "FunctionBlock" and a.get("name"):
            user_types.add(a["name"])

sig_count = collections.defaultdict(collections.Counter)   # tipo -> firma -> n
kind_of = {}

def signature(el):
    pins = []
    for io_key, is_input in (("In", True), ("Out", False)):
        for p in el.get(io_key, []):
            t = p.get("__type")
            if t not in ("PF", "PRM"):
                continue
            pins.append((is_input, p.get("Arg", ""), p.get("Type", "BOOL"),
                         t == "PF", bool(p.get("IO"))))
    return tuple(pins)

n = 0
for (name, guid, base, ver, mt) in pick_latest(project_list()):
    for sec_name, path in sections_of(guid):
        raw = open(path, encoding="utf-8-sig", errors="ignore").read()
        if not raw.lstrip().startswith("{"):
            continue
        for line in raw.splitlines():
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            for el in r.get("CLs", []):
                if el.get("__type") not in ("FB", "F"):
                    continue
                tname = el.get("Name", "")
                if not tname:
                    continue
                sig = signature(el)
                if not sig:
                    continue
                sig_count[tname][sig] += 1
                kind_of[tname] = el["__type"]
                n += 1

out = {}
for tname, sigs in sig_count.items():
    # firma piu' frequente; a parita', quella con piu' pin
    best = sorted(sigs.items(), key=lambda kv: (-kv[1], -len(kv[0])))[0][0]
    pins = [{"is_input": a, "name": b, "datatype": c, "power": d, "inout": e}
            for (a, b, c, d, e) in best]
    out[tname] = {
        "kind": "FB" if kind_of[tname] == "FB" else "F",
        "user": tname in user_types,
        "varianti": len(sigs),
        "usi": sum(sigs.values()),
        "pins": pins,
    }

json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("blocchi analizzati: %d" % n)
print("tipi raccolti: %d -> %s" % (len(out), OUT))
multi = [(v["varianti"], k, v["usi"]) for k, v in out.items() if v["varianti"] > 1]
print("\ntipi con firme diverse tra progetti (uso la piu' frequente):")
for (v, k, u) in sorted(multi, reverse=True)[:15]:
    print("  %2d varianti  %-28s %d usi" % (v, k, u))
print("\nFB definiti dall'utente riconosciuti:",
      ", ".join(sorted(k for k, v in out.items() if v["user"])))
