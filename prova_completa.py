"""Prova completa del ciclo: chiude il progetto, riscrive due rung offline con
spec2rung, riapre, compila, avvia la simulazione e collauda.

Serve anche a validare le correzioni del 27/08/2026: coordinate relative alla
finestra, rilevazione dei dialoghi, chiusura/apertura del progetto.

I due rung precedenti usavano un TON auto-resettante: la sua uscita dura UN
SOLO CICLO e non si riesce a osservare nemmeno campionando a 6.000 letture al
secondo. Qui si usa una forma stabile: dopo 3 s di marcia l'uscita va a 1 e ci
resta.
"""
import io
import json
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sysmac_api as A          # noqa: E402
import spec2rung                # noqa: E402
import sysmac_project as SP     # noqa: E402

PROG = "Semaforo_Incrocio"

RUNG = [
    {"cmt": "PROVA spec2rung: ritardo 3 s alla marcia",
     "chain": ["IN_MARCIA",
               {"fb": "TON", "inst": "Tim_Offline", "p": {"PT": "T#3s"}}]},
    {"cmt": "PROVA spec2rung: uscita del ritardo",
     "chain": ["Tim_Offline.Q", "(OFFLINE_TON_Q)"]},
]


def main():
    print("1) chiusura progetto:", A.chiudi_progetto())
    if A.S._progetto_aperto():
        return 1

    sez = [s for s in SP.sections(SP.find_project(PROG))
           if s["nome"].lower().startswith("sezione")][0]
    righe = [r for r in io.open(sez["file"], encoding="utf-8-sig",
                                newline="").read().splitlines() if r.strip()]
    print("2) rung presenti: %d -> tengo i primi %d e riscrivo gli ultimi 2"
          % (len(righe), len(righe) - 2))
    bom = "﻿"
    testa = bom + "\r\n".join(r.lstrip("﻿") for r in righe[:-2]) + "\r\n"
    io.open(sez["file"], "w", encoding="utf-8", newline="").write(testa)
    spec2rung.scrivi_sezione(sez["file"], RUNG, backup=False)
    print("   nuovi rung scritti.")

    print("3) riapertura:", A.apri_progetto(PROG))
    print("4) compilazione:", A.compila(25))
    print("   salvataggio:", A.salva())
    time.sleep(3)

    print("5) avvio simulazione...")
    try:
        print("   in RUN dopo %.0f s" % A.sim_avvia(attesa=140))
    except Exception as e:
        print("   NON partito:", e)
        return 1

    print("6) collaudo del rung generato offline:")
    esito = A.collauda({
        "nome": "ritardo 3 s generato da spec2rung",
        "passi": [
            {"set": {"IN_MARCIA": 0}},
            {"attendi": 1.5},
            {"verifica": {"OFFLINE_TON_Q": False},
             "descrizione": "a riposo l'uscita e' spenta"},
            {"set": {"IN_MARCIA": 1}},
            {"attendi": 1.5},
            {"verifica": {"OFFLINE_TON_Q": False},
             "descrizione": "dopo 1,5 s il ritardo non e' ancora scaduto"},
            {"attendi": 3.0},
            {"verifica": {"OFFLINE_TON_Q": True},
             "descrizione": "dopo 4,5 s l'uscita e' attiva"},
            {"set": {"IN_MARCIA": 0}},
            {"attendi": 1.0},
            {"verifica": {"OFFLINE_TON_Q": False},
             "descrizione": "tolta la marcia l'uscita cade"},
        ]})
    for p in esito["passi"]:
        if "ESITO" in p:
            print("   %-45s %s %s" % (p.get("descrizione", ""), p["ESITO"],
                                      p.get("differenze", "")))
    print("\nESITO COMPLESSIVO:", "PASS" if esito["ok"] else "FAIL",
          "(%.1f s)" % esito["durata_s"])
    A.chiudi()
    return 0 if esito["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
