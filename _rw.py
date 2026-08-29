
import sys, time; sys.path.insert(0, r"C:\Users\tecni\Claude\sysmac-mcp")
import smc2, spec2rung, movimentazione as M
F = r"C:\Users\tecni\Claude\sysmac-mcp\out\Commessa_Movimentazione.smc2"
t = time.time()
rr = M.rung()
with smc2.progetto(F) as p:
    spec2rung.scrivi_sezione(p.sezioni()[0][1], rr, in_coda=False, backup=False)
    p.tocca()
print("riscritti %d rung nel file in %.2f s" % (len(rr), time.time()-t))
print("verifica:", smc2.informazioni(F)["sezioni"])
