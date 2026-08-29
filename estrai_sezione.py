# -*- coding: utf-8 -*-
"""Estrae UNA sezione da una spec convertita e la prepara per l'import:
spec ladder_gen + TSV variabili (con i tipi REALI del progetto d'origine).

USO: python estrai_sezione.py <file_spec.json> <nome_sezione> [max_rung]
"""
import json, os, sys

SPECS = r"C:\Users\tecni\Claude\sysmac-mcp\specs"
OUT = r"C:\Users\tecni\Claude\sysmac-mcp\out"

f = sys.argv[1]
sec = sys.argv[2]
limit = int(sys.argv[3]) if len(sys.argv) > 3 else 0

path = f if os.path.isabs(f) else os.path.join(SPECS, f)
data = json.load(open(path, encoding="utf-8"))
s = data["sections"][sec]
rungs = s["rungs"] if isinstance(s, dict) else s
variables = s.get("variables", []) if isinstance(s, dict) else []
rungs = [r for r in rungs if "_NON_CONVERTITO" not in r]
if limit:
    rungs = rungs[:limit]
    used = set()
    def walk(o):
        if isinstance(o, str):
            used.add(o)
        elif isinstance(o, dict):
            for k, v in o.items():
                walk(v)
        elif isinstance(o, list):
            for x in o:
                walk(x)
    walk(rungs)
    txt = json.dumps(rungs, ensure_ascii=False)
    variables = [v for v in variables if v["name"] in txt]

SYSTEM_TYPES = ("_sAXIS_REF", "_sGROUP_REF")
sistema = [v["name"] for v in variables if v["type"] in SYSTEM_TYPES]
variables = [v for v in variables if v["type"] not in SYSTEM_TYPES]
if sistema:
    print("variabili di sistema escluse (registrarle come ESTERNE):", ", ".join(sistema))

secname = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in sec)
spec = {"out_dir": OUT, "sections": {secname: rungs}, "variables": variables}
p = os.path.join(OUT, "spec_" + secname + ".json")
json.dump(spec, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("progetto:", data["progetto"])
print("sezione :", sec, "->", len(rungs), "rung,", len(variables), "variabili")
print("spec    :", p)
tipi = sorted({v["type"] for v in variables})
print("tipi variabile:", ", ".join(tipi[:20]))
