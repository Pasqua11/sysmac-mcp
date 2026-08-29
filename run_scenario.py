import sys,io,json,time; sys.path.insert(0,".")
import server as S
t0=time.time()
r = S.sysmac_sim_test(r"scenari\semaforo.json")
print("DURATA CHIAMATA: %.1f s" % (time.time()-t0))
open("out/esito_semaforo.json","w",encoding="utf-8").write(r)
d=json.loads(r)
print("ESITO:", "PASS" if d["ok"] else "FAIL", "- passi falliti:", d["falliti"], "- durata scenario:", d["durata_s"], "s")
for p in d["passi"]:
    if "ESITO" in p:
        print(" ", p.get("descrizione",""), "->", p["ESITO"], p.get("differenze",""))
