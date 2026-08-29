# -*- coding: utf-8 -*-
"""Apre Movimentazione_6Vasche, compila, avvia la simulazione e collauda il
ciclo completo: carico -> 6 vasche -> scarico, piu' la catena degli allarmi.
Cronometra ogni fase."""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sysmac_api as A          # noqa: E402
import movimentazione as M      # noqa: E402

PROG = "test_import_ladder"
T = {}


def fase(nome, t0):
    T[nome] = round(time.time() - t0, 1)
    print("   [%6.1f s] %s" % (T[nome], nome), flush=True)
    return time.time()


def main():
    avvio = t = time.time()
    if A.S._progetto_aperto():
        print("chiusura progetto aperto:", A.chiudi_progetto(), flush=True)
    print("apertura:", A.apri_progetto(PROG, attesa=60), flush=True)
    t = fase("apertura progetto", t)

    out = A.compila(35)
    print("compilazione:", out.splitlines()[0], flush=True)
    if "ERRORI=0" not in out:
        print(out[:3000])
        return 1
    A.salva()
    time.sleep(3)
    t = fase("compilazione", t)

    # Sysmac chiede una ricompilazione anche dopo un F8 andato a buon fine,
    # perche' l'avvio della simulazione usa la build scaricabile: si insiste
    # rispondendo al dialogo, ricompilando e risalvando.
    partita = False
    for tentativo in range(1, 4):
        d = A.dialogo_aperto()
        if d:
            print("   dialogo: %r -> OK" % d, flush=True)
            A.chiudi_dialogo("OK")
            time.sleep(1.5)
        print("   ricompilo (tentativo %d):" % tentativo,
              A.compila(35).splitlines()[0], flush=True)
        A.salva()
        time.sleep(8)
        try:
            A.sim_avvia(attesa=200, auto=False)
            partita = True
            break
        except Exception as ex:
            print("   non partita:", str(ex)[:160], flush=True)
    if not partita:
        return 1
    t = fase("avvio simulazione", t)

    s = A.sim()
    passi = []

    def V(desc, attese):
        letti = s.read_many(list(attese))
        ok = all(bool(letti[k]) == v for k, v in attese.items())
        passi.append(ok)
        print("   %-46s %s%s" % (desc, "PASS" if ok else "FAIL",
                                 "" if ok else "   letto %s" % letti),
              flush=True)

    # tempi di ricetta accorciati a 1 s DALL'ESTERNO, senza toccare il programma
    for n in range(1, M.N_VASCHE + 1):
        s.write("SET_Tempo_V%d" % n, 1_000_000_000)
    for n in range(1, M.N_VASCHE + 1):
        s.write("IN_POS_V%d" % n, False)
    A.scrivi(IN_EMERGENZA=0, IN_PRESS_ARIA=1, V_S_Auto=1, IN_POS_CARICO=1,
             IN_PRESENZA_PEZZO=1, IN_CARRO_BASSO=1, IN_CARRO_ALTO=0,
             IN_POS_SCARICO=0, V_P_Start_Ciclo=0, V_P_Stop_Ciclo=0,
             V_P_Annulla=1)
    time.sleep(0.6)
    s.write("V_P_Annulla", False)
    time.sleep(0.6)

    V("consenso generale attivo", {"Enable_Ciclo": True})
    s.write("V_P_Start_Ciclo", True)
    time.sleep(0.5)
    s.write("V_P_Start_Ciclo", False)
    time.sleep(0.5)
    V("ciclo avviato, passo di carico attivo",
      {"Mem_Ciclo": True, "Mem_Carico": True, "Seq_Attiva": True})
    V("comanda il sollevamento", {"OUT_SOLLEVA": True})
    s.write("IN_CARRO_BASSO", False)
    s.write("IN_CARRO_ALTO", True)
    time.sleep(0.6)
    V("pezzo a bordo e traslazione avanti",
      {"Mem_Pieno": True, "Mem_Carico": False, "OUT_CARRO_AVANTI": True})

    for n in range(1, M.N_VASCHE + 1):
        s.write("IN_POS_CARICO", False)
        s.write("IN_POS_V%d" % n, True)
        s.write("IN_CARRO_ALTO", False)
        s.write("IN_CARRO_BASSO", True)
        time.sleep(0.5)
        V("vasca %d: passo attivo" % n, {"Mem_V%d" % n: True})
        time.sleep(1.8)
        V("vasca %d: tempo scaduto e passo chiuso" % n,
          {"End_V%d" % n: True, "Mem_V%d" % n: False})
        s.write("IN_POS_V%d" % n, False)
        s.write("IN_CARRO_BASSO", False)
        s.write("IN_CARRO_ALTO", True)
        time.sleep(0.3)

    s.write("IN_POS_SCARICO", True)
    s.write("IN_CARRO_ALTO", False)
    s.write("IN_CARRO_BASSO", True)
    time.sleep(0.6)
    V("scarico: passo attivo", {"Mem_Scarico": True})
    s.write("IN_CARRO_BASSO", False)
    s.write("IN_CARRO_ALTO", True)
    time.sleep(0.8)
    V("pezzo depositato e ciclo completato",
      {"Mem_Pieno": False, "Mem_Fine_Ciclo": True, "Mem_Ciclo": False})

    s.write("IN_EMERGENZA", True)
    time.sleep(0.6)
    V("emergenza: allarme 1, consenso caduto, spia accesa",
      {"Allarme_Bit[1]": True, "Enable_Ciclo": False, "V_L_Allarme": True})
    s.write("IN_EMERGENZA", False)
    t = fase("collaudo ciclo completo", t)

    print("\n== TEMPI ==", flush=True)
    for k, v in T.items():
        print("   %-26s %6.1f s" % (k, v))
    print("   %-26s %6.1f s" % ("TOTALE questa fase", time.time() - avvio))
    print("   verifiche superate: %d/%d" % (sum(passi), len(passi)))
    A.chiudi()
    return 0 if all(passi) else 1


if __name__ == "__main__":
    sys.exit(main())
