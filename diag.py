# -*- coding: utf-8 -*-
import sys, json, io
sys.path.insert(0, r"C:\Users\tecni\Claude\sysmac-mcp")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import notte

G, I, sez, sc, el = notte.componi(5, 12345)
spec = {"out_dir": "out",
        "variables": [{"name": a, "type": b, "comment": c} for a, b, c in I],
        "sections": sez}
p = r"C:\Users\tecni\Claude\sysmac-mcp\esercizio_prova.json"
json.dump(spec, open(p, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
e = notte.collaudo_python(p, sc)
print("ok=%s falliti=%s passi=%d" % (e.get("ok"), e.get("falliti"), len(e["passi"])))
for x in e["passi"]:
    es = x.get("ESITO", "-")
    if es != "ok":
        print("%3s %-8s %s" % (x.get("n"), es, x.get("descrizione", "")[:60]))
        if x.get("differenze"):
            print("        ", json.dumps(x["differenze"], ensure_ascii=False)[:160])
