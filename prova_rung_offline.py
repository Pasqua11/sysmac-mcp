"""Prova pratica: generare offline due rung CON UN BLOCCO FUNZIONE (TON) e
verificare che Sysmac li accetti e compili.

Sequenza: chiude il progetto -> crea la variabile globale mancante -> scrive i
rung nel file di sezione -> riapre -> compila.
"""
import sys
import time
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import server as S      # noqa: E402
import slwd             # noqa: E402
import spec2rung        # noqa: E402
import sysmac_project as SP  # noqa: E402

PROG = "Semaforo_Incrocio"


def titolo():
    return S._ps("Get-Process SysmacStudio -ErrorAction SilentlyContinue | "
                 "ForEach-Object { $_.MainWindowTitle }").strip()


def chiudi_progetto(tentativi=3):
    for k in range(tentativi):
        if " - " not in titolo():
            return True
        S._focus_sysmac()
        time.sleep(0.8)
        S._send_keys("%f")          # menu File
        time.sleep(0.8)
        S._send_keys("{DOWN}{ENTER}")   # prima voce = Chiudi
        time.sleep(8)
    return " - " not in titolo()


def _offset_y():
    """La finestra di Sysmac non e' sempre a schermo intero: le coordinate
    note valgono a partire dal bordo superiore della finestra."""
    import ctypes
    from ctypes import wintypes
    r = wintypes.RECT()
    ctypes.windll.user32.GetWindowRect(S._sysmac_hwnd(), ctypes.byref(r))
    return r.top


def apri_progetto():
    dy = _offset_y()
    S._focus_sysmac()
    time.sleep(0.8)
    S._click(116, 186 + dy)                  # "Apri progetto"
    time.sleep(3)
    S._click(497, 218 + dy, double=True)     # prima riga = ultimo modificato
    time.sleep(28)
    return titolo()


def main():
    print("titolo iniziale:", titolo())
    if not chiudi_progetto():
        print("NON sono riuscito a chiudere il progetto: interrompo "
              "(scrivere offline con il progetto aperto e' inutile).")
        return 1
    print("progetto chiuso.")

    cart = slwd.trova_progetto(PROG)
    r = slwd.crea_variabili(
        PROG,
        globali=[{"nome": "OFFLINE_TON_Q", "tipo": "BOOL",
                  "commento": "rung generato da spec2rung"}],
        esterne=["OFFLINE_TON_Q"])
    print("variabili:", r)

    sezione = [s for s in SP.sections(SP.find_project(PROG))
               if s["nome"].lower().startswith("sezione")][0]
    print("sezione:", sezione["nome"], sezione["file"])

    rungs = [
        {"cmt": "PROVA spec2rung: temporizzatore lampeggio 5 s",
         "chain": ["IN_MARCIA", "/Tim_Offline.Q",
                   {"fb": "TON", "inst": "Tim_Offline", "p": {"PT": "T#5s"}}]},
        {"cmt": "PROVA spec2rung: uscita del temporizzatore",
         "chain": ["Tim_Offline.Q", "(OFFLINE_TON_Q)"]},
    ]
    for x in rungs:
        print("  ->", spec2rung.riga_rung(x)[:150])
    n = spec2rung.scrivi_sezione(sezione["file"], rungs)
    print("scritti %d rung nel file di sezione." % n)

    print("riapro il progetto...")
    print("titolo:", apri_progetto())
    print("compilazione:", S.sysmac_compile_text(20))
    return 0


if __name__ == "__main__":
    sys.exit(main())
