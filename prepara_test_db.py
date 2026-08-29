# -*- coding: utf-8 -*-
"""Costruisce una sezione di prova con rung REALI presi dalle spec convertite,
usando SOLO tipi la cui firma viene da pins.json (mai campionati a mano).
Genera anche il TSV delle variabili citate, cosi' l'import e' autosufficiente."""
import json, os, re, sys, collections

sys.path.insert(0, r"C:\Users\tecni\Claude\sysmac-mcp")
from ladder_gen import LadderGen, vars_tsv

SPECS = r"C:\Users\tecni\Claude\sysmac-mcp\specs"
OUTDIR = r"C:\Users\tecni\Claude\sysmac-mcp\out"
gen = LadderGen(r"C:\Users\tecni\Claude\sysmac-mcp\templates")

WANT = {"ScaleTrans", "LIMIT", "INT_TO_REAL", "Get1sClk", "TOF", "@Inc", ">", "<", ">=", "MOVE"}


def types_in(item, acc):
    if isinstance(item, dict):
        if "fb" in item:
            acc.add(item["fb"])
        if "f" in item:
            acc.add(item["f"])
        if "or" in item:
            for b in item["or"]:
                for x in (b if isinstance(b, list) else [b]):
                    types_in(x, acc)
    return acc


def rung_types(r):
    acc = set()
    for it in r.get("chain", []):
        types_in(it, acc)
    for b in r.get("out", []):
        for x in (b if isinstance(b, list) else [b]):
            types_in(x, acc)
    return acc


def rung_vars(r):
    """nomi variabile citati nel rung (contatti, bobine, istanze FB, parametri)"""
    out = []

    def walk(it):
        if isinstance(it, str):
            s = it.strip()
            m = re.fullmatch(r"\((?:S |R )?/?([^)]+)\)", s)
            if m:
                out.append(("coil", m.group(1).strip()))
                return
            s = s.lstrip("/^v")
            out.append(("contact", s))
            return
        if isinstance(it, dict):
            if "or" in it:
                for b in it["or"]:
                    for x in (b if isinstance(b, list) else [b]):
                        walk(x)
                return
            if "fb" in it:
                out.append(("fb", it.get("inst", ""), it["fb"]))
            for k, v in (it.get("p") or {}).items():
                out.append(("par", v))

    for it in r.get("chain", []):
        walk(it)
    for b in r.get("out", []):
        for x in (b if isinstance(b, list) else [b]):
            walk(x)
    return out


CONST = re.compile(r"^(?:[-+]?\d+(?:\.\d+)?|(?:INT|UINT|DINT|WORD|REAL|LREAL|BOOL|TIME|T)#.*|"
                   r"TIME#.*|T#.*|'.*'|_e.*|P_On|P_Off|P_First_Run)$", re.I)

chosen = []
for fn in sorted(os.listdir(SPECS)):
    if not fn.endswith(".json"):
        continue
    data = json.load(open(os.path.join(SPECS, fn), encoding="utf-8"))
    for sec, rungs in data.get("sections", {}).items():
        for r in rungs:
            if "_NON_CONVERTITO" in r:
                continue
            tp = rung_types(r)
            if not tp:
                continue
            if not (tp & WANT):
                continue
            # solo tipi presi dal database (non campionati) o gia' noti, e mai FB utente
            if any(gen.user_type.get(t) for t in tp):
                continue
            if not all(t in gen.pins for t in tp):
                continue
            if not any(t in gen.from_db for t in tp):
                continue
            chosen.append((data["progetto"], sec, r, tp))

print("rung candidati:", len(chosen))
sel, used_types = [], set()
for (proj, sec, r, tp) in chosen:
    new = tp - used_types
    if not new:
        continue
    sel.append((proj, sec, r, tp))
    used_types |= tp
    if len(sel) >= 8:
        break

print("selezionati %d rung, tipi coperti: %s" % (len(sel), ", ".join(sorted(used_types))))

variables, seen = [], set()
rungs_out = []
for (proj, sec, r, tp) in sel:
    r = dict(r)
    r["cmt"] = "[%s / %s] %s" % (proj, sec, r.get("cmt", ""))
    rungs_out.append(r)
    for v in rung_vars(r):
        kind, name = v[0], v[1]
        if not name or name in seen or CONST.match(name):
            continue
        if "." in name or "[" in name:      # membri di struttura / array: saltati nel test
            continue
        seen.add(name)
        if kind == "fb":
            variables.append({"name": name, "type": v[2]})
        elif kind == "par":
            variables.append({"name": name, "type": "REAL"})
        else:
            variables.append({"name": name, "type": "BOOL"})

spec = {"out_dir": OUTDIR, "sections": {"Test_DB_Pins": rungs_out}, "variables": variables}
os.makedirs(OUTDIR, exist_ok=True)
p = os.path.join(OUTDIR, "spec_test_db.json")
json.dump(spec, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("spec ->", p, "| variabili:", len(variables))
for r in rungs_out:
    print("  -", r["cmt"][:100])
