# -*- coding: utf-8 -*-
import io
import json
import sys

sys.path.insert(0, r"C:\Users\tecni\Claude\sysmac-mcp")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import st_gen

spec = json.load(open(r"C:\Users\tecni\Claude\sysmac-mcp\semaforo_spec.json",
                      encoding="utf-8-sig"))
cerca = ("OUT_EO_Verde", "V_L_Ped_NS_Prenotato")
for nome, rung in spec["sections"].items():
    for i, r in enumerate(rung):
        testo = json.dumps(r, ensure_ascii=False)
        if any(c in testo for c in cerca):
            print("--- %s rung %d" % (nome, i))
            print(json.dumps(r, ensure_ascii=False, indent=1)[:700])
            g = st_gen.GeneratoreST({"sections": {"x": [r]}})
            print("  ST generato:")
            for riga in g.genera("x").splitlines():
                if riga.strip() and not riga.startswith("//="):
                    print("   ", riga)
            print()
