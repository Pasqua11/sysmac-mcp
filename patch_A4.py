# -*- coding: utf-8 -*-
"""
patch_A4.py - _clickf() e l'offset negativo della finestra massimizzata

Le coordinate "note" del progetto (es. 317,187 = numero del rung 0) sono state
misurate SULLO SCHERMO con Sysmac massimizzato. _clickf le trattava come
coordinate relative alla finestra e ci sommava l'origine, che a finestra
massimizzata vale (-9, -9): ogni click finiva 9 px piu' in alto e a sinistra.

Sul numero di un rung 9 px bastano a cadere nella banda gialla del commento
invece che sul rung: il rung appare selezionato, ma il Ctrl+V successivo non
incolla nulla. Verificato il 28/08/2026:
    _clickf(317, 187) + Ctrl+V  -> 137 rung, nessun incollaggio
    _click (318, 188) + Ctrl+V  -> 138 rung, incollato

Correzione: l'origine si somma solo se POSITIVA. A finestra massimizzata le
coordinate note valgono cosi' come sono; a finestra ridotta l'offset serve
ancora e continua a essere applicato.
"""
import os, shutil, sys

SRV = r"C:\Users\tecni\Claude\sysmac-mcp\server.py"
BAK = SRV + ".bak_pre_offsetclick"

VECCHIO = '''    _focus_sysmac()
    if massimizza:
        _massimizza()
    l, t, _r, _b = _rect_sysmac()
    _click(x + l, y + t, button, double)'''

NUOVO = '''    _focus_sysmac()
    if massimizza:
        _massimizza()
    l, t, _r, _b = _rect_sysmac()
    # A finestra massimizzata l'origine e' (-9, -9) (bordi invisibili di
    # Windows 11) e le coordinate note, misurate sullo schermo, vanno usate
    # tali e quali: sommare un offset negativo sposta il click di 9 px e su un
    # numero di rung basta a mancarlo (il Ctrl+V poi non incolla nulla).
    _click(x + max(l, 0), y + max(t, 0), button, double)'''


def main():
    dry = "--dry" in sys.argv
    s = open(SRV, encoding="utf-8").read()
    assert VECCHIO in s, "blocco _clickf non trovato"
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
