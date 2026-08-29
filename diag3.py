# -*- coding: utf-8 -*-
import io
import json
import sys

sys.path.insert(0, r"C:\Users\tecni\Claude\sysmac-mcp")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import notte

s = 24
G, I, sez, sc, el = notte.componi((s % 6) + 3, s * 977)
print("moduli:", el)
spec = {"out_dir": "out",
        "variables": [{"name": a, "type": b, "comment": c} for a, b, c in I],
        "sections": sez}
p = r"C:\Users\tecni\Claude\sysmac-mcp\_d3.json"
with open(p, "w", encoding="utf-8") as f:
    json.dump(spec, f, indent=1, ensure_ascii=False)
e = notte.collaudo_python(p, sc)
print("ok=%s falliti=%s" % (e.get("ok"), e.get("falliti")))
for x in e["passi"]:
    print("%3s | %-8s | %s" % (x.get("n"), x.get("ESITO", "?"),
                               x.get("descrizione", "")[:56]))
    for k in x:
        if k not in ("n", "ESITO", "descrizione"):
            print("        %s = %s" % (k, json.dumps(x[k], ensure_ascii=False)[:120]))
