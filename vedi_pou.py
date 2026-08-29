import sys, re, glob, os
sys.path.insert(0, r"C:\Users\tecni\Claude\sysmac-mcp")
import smc2
with smc2.progetto(r"C:\OMRON\Data\Lib\ST_Essiccatore.smc2", sola_lettura=True) as p:
    for oem in glob.glob(os.path.join(p.cartella, "*.oem")):
        t = open(oem, encoding="utf-8-sig", errors="ignore").read()
        for m in re.finditer(r"<Entity[^>]*>", t):
            e = m.group(0)
            if "Programma1" in e:
                print(e[:300])
