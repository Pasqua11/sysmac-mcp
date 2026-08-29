# -*- coding: utf-8 -*-
"""
patch_A2.py - correzione di _cartella_progetto_aperto()

In C:\\OMRON\\Data\\Solution restano file <pid>.applicationlock ORFANI di
sessioni chiuse male (28/08/2026: 9 su 10, il piu' vecchio del febbraio 2025).
Cercare "un lock qualsiasi" trovava quindi la cartella sbagliata.

Correzione: si accetta solo il lock il cui nome corrisponde al PID del processo
Sysmac che possiede la finestra (via GetWindowThreadProcessId, senza PowerShell).
"""
import os, shutil, sys

SRV = r"C:\Users\tecni\Claude\sysmac-mcp\server.py"
BAK = SRV + ".bak_pre_lockpid"

VECCHIO = '''def _cartella_progetto_aperto() -> str:
    """Cartella di lavoro del progetto APERTO, riconosciuta dal file
    <pid>.applicationlock. Copre sia l'archivio (Solution) sia i progetti
    aperti da file .smc2 (ProjFileTmp)."""
    for radice in (r"C:\\OMRON\\Data\\Solution", r"C:\\OMRON\\Data\\ProjFileTmp"):
        if not os.path.isdir(radice):
            continue
        try:
            sotto = os.listdir(radice)
        except OSError:
            continue
        for d in sotto:
            p = os.path.join(radice, d)
            if not os.path.isdir(p):
                continue
            try:
                if any(f.endswith(".applicationlock") for f in os.listdir(p)):
                    return p
            except OSError:
                continue
    return ""'''

NUOVO = '''def _pid_sysmac() -> int:
    """PID del processo che possiede la finestra di Sysmac (niente PowerShell)."""
    try:
        h = _sysmac_hwnd()
    except Exception:
        return 0
    pid = ctypes.c_ulong(0)
    user32.GetWindowThreadProcessId(h, ctypes.byref(pid))
    return int(pid.value)


def _cartella_progetto_aperto() -> str:
    """Cartella di lavoro del progetto APERTO, riconosciuta dal file
    <pid>.applicationlock. Copre sia l'archivio (Solution) sia i progetti
    aperti da file .smc2 (ProjFileTmp).

    ATTENZIONE: restano lock ORFANI di sessioni chiuse male (28/08/2026: 9 su
    10, il piu' vecchio di febbraio 2025). Si accetta quindi SOLO il lock il cui
    nome corrisponde al PID del Sysmac attualmente in esecuzione."""
    pid = _pid_sysmac()
    if not pid:
        return ""
    atteso = "%d.applicationlock" % pid
    for radice in (r"C:\\OMRON\\Data\\Solution", r"C:\\OMRON\\Data\\ProjFileTmp"):
        if not os.path.isdir(radice):
            continue
        try:
            sotto = os.listdir(radice)
        except OSError:
            continue
        for d in sotto:
            p = os.path.join(radice, d)
            if not os.path.isdir(p):
                continue
            try:
                if atteso in os.listdir(p):
                    return p
            except OSError:
                continue
    return ""'''


def main():
    dry = "--dry" in sys.argv
    s = open(SRV, encoding="utf-8").read()
    assert VECCHIO in s, "blocco _cartella_progetto_aperto non trovato"
    s2 = s.replace(VECCHIO, NUOVO, 1)
    print("modifiche: %d -> %d caratteri (%+d)" % (len(s), len(s2), len(s2) - len(s)))
    if dry:
        print("(dry run)")
        return
    if not os.path.exists(BAK):
        shutil.copyfile(SRV, BAK)
        print("backup:", BAK)
    open(SRV, "w", encoding="utf-8").write(s2)
    print("scritto:", SRV)


if __name__ == "__main__":
    main()
