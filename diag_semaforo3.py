# -*- coding: utf-8 -*-
"""Esegue ladder e ST fianco a fianco e ferma al primo scostamento."""
import io
import json
import sys

sys.path.insert(0, r"C:\Users\tecni\Claude\sysmac-mcp")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import st_gen
from sim_spec import SimSpec
from sim_st import SimST

D = r"C:\Users\tecni\Claude\sysmac-mcp"
spec = D + r"\semaforo_spec.json"
sc = json.load(open(D + r"\semaforo_scenario.json", encoding="utf-8-sig"))

testo, _ = st_gen.genera(spec)
dati = json.load(open(spec, encoding="utf-8-sig"))
istanze = {v["name"]: v["type"].upper() for v in dati.get("variables", [])
           if v.get("type", "").upper() in ("TON", "TOF", "TP", "CTU", "CTD")}

a = SimSpec(spec, tempi=sc.get("tempi", {}))
b = SimST(testo, tempi=sc.get("tempi", {}), istanze=istanze)

osserva = ["Mem_Ciclo", "Mem_F1", "Mem_F2", "Mem_F3", "Mem_F4", "Mem_F5",
           "Mem_Ped_NS", "Mem_Ped_EO", "Tim_F1.Q", "Tim_F1min.Q", "Tim_F2.Q",
           "OUT_EO_Verde", "OUT_NS_Rosso", "OUT_Ped_NS_Verde",
           "OUT_Ped_EO_Verde", "V_L_Ped_NS_Prenotato", "OUT_NS_Verde"]

for n, passo in enumerate(sc["passi"], 1):
    for s in (a, b):
        if "set" in passo:
            s.set(**passo["set"])
        if "attendi" in passo:
            s.corri(float(passo["attendi"]))
        if passo.get("impulso"):
            for v in passo["impulso"]:
                s.set(**{v: True})
            s.corri(0.3)
            for v in passo["impulso"]:
                s.set(**{v: False})
    diff = {}
    for v in osserva:
        va, vb = a.leggi(v), b.leggi(v)
        if bool(va) != bool(vb):
            diff[v] = (bool(va), bool(vb))
    stato = "ok" if not diff else "DIVERSO"
    print("%2d %-46s %s %s" % (n, passo.get("descrizione", "")[:46], stato,
                               diff if diff else ""))
    if diff:
        print("   (ladder, ST) - mi fermo qui")
        break
