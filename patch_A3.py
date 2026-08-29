# -*- coding: utf-8 -*-
"""
patch_A3.py - _massimizza() affidabile (28/08/2026)

Il test "e' gia' massimizzata" era basato sulle DIMENSIONI:
    if r - l >= sw - 20 and b - t >= sh - 80: return False
Dopo un ciclo nascondi/ripristina la finestra risultava in stato NORMALE ma con
rettangolo (0, 90, 1938, 1128): piu' larga e piu' alta delle soglie, quindi il
test la dava per massimizzata e non agiva. Tutte le coordinate note finivano
90 px piu' in alto del dovuto e i click cadevano nel posto sbagliato: e' cosi'
che un import poteva "riuscire" senza incollare niente.

Ora lo stato si legge da GetWindowPlacement().showCmd (3 = massimizzata), che
e' il dato vero e non un'inferenza sulle misure.
"""
import os, shutil, sys

SRV = r"C:\Users\tecni\Claude\sysmac-mcp\server.py"
BAK = SRV + ".bak_pre_massimizza"

VECCHIO = '''def _massimizza():
    """Porta Sysmac a schermo intero: e' la condizione in cui sono state
    misurate tutte le coordinate note. Ritorna True se ha dovuto agire."""
    SW_MAXIMIZE = 3
    h = _sysmac_hwnd()
    l, t, r, b = _rect_sysmac()
    sw, sh = _screen_wh()
    if r - l >= sw - 20 and b - t >= sh - 80:
        return False
    user32.ShowWindow(h, SW_MAXIMIZE)
    time.sleep(0.6)
    return True'''

NUOVO = '''class _WINDOWPLACEMENT(ctypes.Structure):
    _fields_ = [("length", ctypes.c_uint), ("flags", ctypes.c_uint),
                ("showCmd", ctypes.c_uint),
                ("ptMinX", ctypes.c_long), ("ptMinY", ctypes.c_long),
                ("ptMaxX", ctypes.c_long), ("ptMaxY", ctypes.c_long),
                ("rcLeft", ctypes.c_long), ("rcTop", ctypes.c_long),
                ("rcRight", ctypes.c_long), ("rcBottom", ctypes.c_long)]


def _stato_finestra(h: int) -> int:
    """showCmd della finestra: 1 = normale, 2 = minimizzata, 3 = massimizzata."""
    wp = _WINDOWPLACEMENT()
    wp.length = ctypes.sizeof(_WINDOWPLACEMENT)
    if not user32.GetWindowPlacement(h, ctypes.byref(wp)):
        return 0
    return int(wp.showCmd)


def _massimizza():
    """Porta Sysmac a schermo intero: e' la condizione in cui sono state
    misurate tutte le coordinate note. Ritorna True se ha dovuto agire.

    Lo stato si legge da GetWindowPlacement, non dalle dimensioni: dopo un
    ciclo nascondi/ripristina la finestra puo' essere in stato NORMALE ma piu'
    grande dello schermo (0, 90, 1938, 1128), e il vecchio test sulle misure la
    dava per massimizzata lasciando tutte le coordinate sfalsate di 90 px."""
    SW_MAXIMIZE = 3
    h = _sysmac_hwnd()
    if _stato_finestra(h) == SW_MAXIMIZE:
        return False
    user32.ShowWindow(h, SW_MAXIMIZE)
    time.sleep(0.8)
    return True'''


def main():
    dry = "--dry" in sys.argv
    s = open(SRV, encoding="utf-8").read()
    assert VECCHIO in s, "blocco _massimizza non trovato"
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
