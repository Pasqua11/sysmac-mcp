# -*- coding: utf-8 -*-
import sys, time, json
sys.path.insert(0, r"C:\Users\tecni\Claude\sysmac-mcp")
import sysmac_project as sp

t0 = time.time()
righe = []
for p in sp.list_projects():
    try:
        sez = sp.sections(p)
    except Exception:
        continue
    tot = sum(s["rung"] for s in sez)
    righe.append({"rung": tot, "nome": p["nome"], "mod": p["modificato"],
                  "n_sez": len(sez),
                  "sezioni": sorted([(s["nome"], s["rung"]) for s in sez],
                                    key=lambda x: -x[1])[:8]})
righe.sort(key=lambda r: -r["rung"])
print("progetti: %d in %.1f s\n" % (len(righe), time.time()-t0))
for r in righe[:20]:
    print("%5d rung  %-42s %2d sez  %s" % (r["rung"], r["nome"][:42], r["n_sez"], r["mod"][:10]))
json.dump(righe, open("censimento_libreria.json","w",encoding="utf-8"), indent=1, ensure_ascii=False)
