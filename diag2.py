# -*- coding: utf-8 -*-
import io
import json
import sys

sys.path.insert(0, r"C:\Users\tecni\Claude\sysmac-mcp")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import notte

for seme, nmod in ((4 * 977, 7), (24 * 977, 3), (30 * 977, 3)):
    G, I, sez, sc, el = notte.componi(nmod, seme)
    spec = {"out_dir": "out",
            "variables": [{"name": a, "type": b, "comment": c} for a, b, c in I],
            "sections": sez}
    p = r"C:\Users\tecni\Claude\sysmac-mcp\_d2.json"
    json.dump(spec, open(p, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    e = notte.collaudo_python(p, sc)
    print("=== seme %d: %s" % (seme, ", ".join(el)))
    for x in e["passi"]:
        if x.get("ESITO") == "FAIL":
            print("  n.%s %s" % (x.get("n"), x.get("descrizione", "")[:70]))
            print("      %s" % json.dumps(x.get("differenze"), ensure_ascii=False)[:180])
    print()
