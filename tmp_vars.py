import sys,time; sys.path.insert(0,r"C:\Users\tecni\Claude\sysmac-mcp")
import server as S
D=r"C:\Users\tecni\Claude\sysmac-mcp"
g=open(D+r"\lavaggio11_globali.txt",encoding="utf-8").read()
i=open(D+r"\lavaggio11_interne.txt",encoding="utf-8").read()
e=open(D+r"\lavaggio11_esterne.txt",encoding="utf-8").read()
t=time.time()
print(S.sysmac_vars_offline(progetto=r"C:\OMRON\Data\Lib\Lavaggio_11_Vasche.smc2",globali=g,interne=i,esterne=e))
print("VARIABILI: %.1f s"%(time.time()-t))
