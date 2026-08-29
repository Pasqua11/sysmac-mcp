# -*- coding: utf-8 -*-
"""
confronta_ladder_st.py - la stessa spec, i due linguaggi, lo stesso collaudo.

Prende una spec, la esegue come ladder con sim_spec e come Structured Text
generato con st_gen, e confronta gli esiti passo per passo. Se la traduzione
e' fedele i due devono comportarsi in modo identico: e' la verifica piu'
severa che si possa fare su un generatore, e non richiede Sysmac.
"""
import io
import json
import os
import sys

sys.path.insert(0, r"C:\Users\tecni\Claude\sysmac-mcp")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import st_gen
from sim_spec import SimSpec
from sim_st import SimST


def confronta(spec_path, scenario_path):
    sc = json.load(open(scenario_path, encoding="utf-8-sig"))
    nome = os.path.basename(spec_path)

    ladder = SimSpec(spec_path, tempi=sc.get("tempi", {})).scenario(sc)

    testo, fronti = st_gen.genera(spec_path)
    st_file = os.path.splitext(spec_path)[0].replace("_spec", "") + "_gen.st"
    with open(st_file, "w", encoding="utf-8") as f:
        f.write(testo)

    # i tipi delle istanze di blocco funzione stanno nella spec
    istanze = {}
    for v in json.load(open(spec_path, encoding="utf-8-sig")).get("variables", []):
        if v.get("type", "").upper() in ("TON", "TOF", "TP", "CTU", "CTD"):
            istanze[v["name"]] = v["type"].upper()

    st = SimST(testo, tempi=sc.get("tempi", {}), istanze=istanze).scenario(sc)

    print("=== %s" % nome)
    print("    ladder: %s  (%d/%d)"
          % ("PASS" if ladder["ok"] else "FAIL",
             len(ladder["passi"]) - ladder["falliti"], len(ladder["passi"])))
    print("    ST:     %s  (%d/%d)   [%d righe, %d memorie di fronte]"
          % ("PASS" if st["ok"] else "FAIL",
             len(st["passi"]) - st["falliti"], len(st["passi"]),
             len(testo.splitlines()), len(fronti)))

    diverse = []
    for a, b in zip(ladder["passi"], st["passi"]):
        if a.get("ESITO") != b.get("ESITO"):
            diverse.append((a["n"], a.get("descrizione", ""),
                            a.get("ESITO"), b.get("ESITO"),
                            b.get("differenze")))
    if diverse:
        print("    PASSI CHE SI COMPORTANO IN MODO DIVERSO: %d" % len(diverse))
        for n, d, ea, eb, diff in diverse[:8]:
            print("      %2d  %-42s ladder=%s  ST=%s" % (n, d[:42], ea, eb))
            if diff:
                print("          %s" % json.dumps(diff, ensure_ascii=False)[:130])
    else:
        print("    -> i due linguaggi si comportano in modo IDENTICO")
    return not diverse


if __name__ == "__main__":
    if len(sys.argv) >= 3:
        ok = confronta(sys.argv[1], sys.argv[2])
        sys.exit(0 if ok else 1)
    D = r"C:\Users\tecni\Claude\sysmac-mcp"
    coppie = [
        ("lavaggio4_spec.json", "lavaggio4_scenario.json"),
        ("lavaggio11_spec.json", "lavaggio11_scenario.json"),
        ("pompe_spec.json", "pompe_scenario.json"),
        ("nastro_spec.json", "nastro_scenario.json"),
        ("semaforo_spec.json", "semaforo_scenario.json"),
        ("cfe_spec.json", "cfe_scenario.json"),
    ]
    tutti = True
    for s, c in coppie:
        ps, pc = os.path.join(D, s), os.path.join(D, c)
        if os.path.exists(ps) and os.path.exists(pc):
            try:
                tutti &= confronta(ps, pc)
            except Exception as e:
                tutti = False
                print("=== %s\n    ERRORE: %s: %s" % (s, type(e).__name__, str(e)[:150]))
            print()
    print("ESITO COMPLESSIVO:", "traduzione fedele" if tutti else "ci sono differenze")
