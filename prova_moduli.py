# -*- coding: utf-8 -*-
"""Collauda il catalogo: ogni modulo da solo, poi 30 combinazioni casuali."""
import io
import json
import os
import sys
import time

sys.path.insert(0, r"C:\Users\tecni\Claude\sysmac-mcp")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import notte
import moduli

TMP = r"C:\Users\tecni\Claude\sysmac-mcp\_prova.json"


def prova(G, I, sez, sc, etichetta):
    spec = {"out_dir": "out",
            "variables": [{"name": a, "type": b, "comment": c} for a, b, c in I],
            "sections": sez}
    json.dump(spec, open(TMP, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    t0 = time.time()
    try:
        e = notte.collaudo_python(TMP, sc)
    except Exception as ex:
        print("%-34s ERRORE %s" % (etichetta, str(ex)[:90]))
        return False
    n = sum(len(v) for v in sez.values())
    esito = "PASS" if e["ok"] else "FAIL %d/%d" % (e["falliti"], len(e["passi"]))
    print("%-34s %4d rung  %-10s %.2fs" % (etichetta, n, esito, time.time() - t0))
    if not e["ok"]:
        for x in e["passi"]:
            if x.get("ESITO") == "FAIL":
                print("      %s -> %s" % (x.get("descrizione", "")[:58],
                                          json.dumps(x.get("differenze"),
                                                     ensure_ascii=False)[:110]))
    return e["ok"]


print("=== ogni modulo da solo ===")
tutti_ok = True
for f in moduli.CATALOGO:
    m = f(1)
    G = [("IN_Emergenza", "BOOL", "emergenza"), ("IN_Protezioni", "BOOL", "protezioni"),
         ("V_P_Reset", "BOOL", "reset"), ("V_L_Allarme", "BOOL", "allarme"),
         ("V_L_Pronto", "BOOL", "pronto")] + m["globali"]
    I = [("Consensi", "BOOL", "consensi")] + m["interne"]
    sez = {"Sicurezze": [{"cmt": "CONSENSI",
                          "chain": ["/IN_Emergenza", "IN_Protezioni", "(Consensi)"]}],
           "Modulo": m["rung"],
           "Allarmi": [
               {"cmt": "ALLARME CUMULATIVO",
                "chain": [{"or": (m["allarmi"] or []) + ["/Consensi"]},
                          "(V_L_Allarme)"]},
               {"cmt": "PRONTO", "chain": ["Consensi", "/V_L_Allarme", "(V_L_Pronto)"]}]}
    ini = {"IN_Emergenza": False, "IN_Protezioni": True}
    ini.update(m.get("iniziale", {}))
    sc = {"nome": m["nome"], "tempi": m.get("tempi", {}),
          "passi": [{"descrizione": "stato iniziale", "set": ini,
                     "impulso": ["V_P_Reset"], "attendi": 0.6,
                     "verifica": {"V_L_Pronto": True}}] + m["passi"]}
    tutti_ok &= prova(G, I, sez, sc, m["nome"])

print()
print("=== 30 combinazioni casuali ===")
falliti = []
for s in range(1, 31):
    G, I, sez, sc, el = notte.componi((s % 6) + 3, s * 977)
    if not prova(G, I, sez, sc, "seme %d (%d moduli)" % (s, len(el))):
        falliti.append((s, el))

print()
if falliti:
    print("COMBINAZIONI FALLITE: %d" % len(falliti))
    for s, el in falliti:
        print("  seme %d: %s" % (s, ", ".join(el)))
else:
    print("TUTTE LE COMBINAZIONI PASSANO")
os.path.exists(TMP) and os.remove(TMP)
