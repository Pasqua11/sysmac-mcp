# -*- coding: utf-8 -*-
"""patch_G.py - sysmac_apri_sezione piu' robusto (29/08/2026, notte).

Il primo esercizio autonomo si e' fermato qui: la selezione finiva su "Task"
invece che sulla sezione. Causa: "{RIGHT 12}" mandato in un colpo solo arriva
troppo in fretta e il TreeView Win32, mentre espande i nodi, perde dei tasti.
Provato a mano con le pause funzionava; lanciato in sequenza no.

Rimedio: i tasti vanno in gruppi di tre con una pausa in mezzo - restano 4
chiamate invece di 12, quindi si tiene quasi tutto il guadagno - e alla fine
si verifica di essere davvero su una foglia: se la scheda non si apre, si
riprova ripartendo dall'alto.
"""
import os
import shutil

SRV = r"C:\Users\tecni\Claude\sysmac-mcp\server.py"
b = SRV + ".bak_pre_patchG"
if not os.path.exists(b):
    shutil.copy2(SRV, b)

s = open(SRV, encoding="utf-8").read()

vecchio = '''    _click(x + min(w // 2, 120), y + 14)
    time.sleep(0.5)
    _send_keys("{HOME}{LEFT}{DOWN}")
    time.sleep(0.8)
    _send_keys("{RIGHT 12}")
    time.sleep(2.0)
    _send_keys("{ENTER}")

    for tentativo in range(12):'''

nuovo = '''    _click(x + min(w // 2, 120), y + 14)
    time.sleep(0.5)
    _send_keys("{HOME}{LEFT}{DOWN}")
    time.sleep(0.9)
    # A gruppi di tre: mandati tutti insieme, il TreeView ne perde qualcuno
    # mentre sta espandendo i nodi e la selezione finisce altrove.
    for _ in range(4):
        _send_keys("{RIGHT 3}")
        time.sleep(0.6)
    time.sleep(1.2)
    _send_keys("{ENTER}")

    for tentativo in range(12):'''

if s.count(vecchio) != 1:
    raise SystemExit("aggancio non trovato (%d)" % s.count(vecchio))

s = s.replace(vecchio, nuovo)

# secondo giro completo se la scheda non si apre: si riparte dall'alto
vecchio2 = '''        # nome diverso da quello chiesto: scendo di una riga e riprovo
        _send_keys("{DOWN}{ENTER}")'''
nuovo2 = '''        # nome diverso da quello chiesto: scendo di una riga e riprovo.
        # A meta' dei tentativi si riparte dalla cima dell'albero: se la
        # discesa si era persa, insistere con DOWN non porta da nessuna parte.
        if tentativo == 5:
            _send_keys("{HOME}{LEFT}{DOWN}")
            time.sleep(0.9)
            for _ in range(4):
                _send_keys("{RIGHT 3}")
                time.sleep(0.6)
            _send_keys("{ENTER}")
        else:
            _send_keys("{DOWN}{ENTER}")'''

if s.count(vecchio2) != 1:
    raise SystemExit("aggancio 2 non trovato")
s = s.replace(vecchio2, nuovo2)

open(SRV, "w", encoding="utf-8").write(s)

import py_compile
py_compile.compile(SRV, doraise=True)
print("G: apri_sezione a gruppi di 3 tasti, con ripartenza dall'alto")
