# -*- coding: utf-8 -*-
"""patch_H.py - il flusso Structured Text nel server (29/08/2026).

Aggiunge due strumenti:

  sysmac_st_nuovo(codice, nome)   crea un POU in ST sotto Programmi e ci
                                  scrive dentro il codice
  sysmac_st_scrivi(codice)        sostituisce il contenuto del POU ST gia'
                                  aperto nell'editor

Il POU si crea dal menu contestuale su "Programmi": Aggiungi > ST. Il menu si
apre col tasto destro e si percorre da tastiera ({DOWN} per "Aggiungi",
{RIGHT} per aprire il sottomenu, {DOWN} per passare da Ladder a ST): i clic
sulle voci di un menu popup non funzionano, perche' il popup e' una finestra
separata e portare Sysmac in primo piano lo chiude.

Il codice si incolla dagli appunti: l'ST e' testo, quindi non serve nessun
formato speciale - a differenza del ladder, che richiede l'XML degli appunti.
"""
import os
import shutil

SRV = r"C:\Users\tecni\Claude\sysmac-mcp\server.py"
b = SRV + ".bak_pre_patchH"
if not os.path.exists(b):
    shutil.copy2(SRV, b)

s = open(SRV, encoding="utf-8").read()

NUOVO = '''@mcp.tool()
def sysmac_st_nuovo(codice: str = "", nome: str = "") -> str:
    """Crea un POU in STRUCTURED TEXT sotto Programmi e ci scrive il codice.

    Meta' del codice dei progetti SYNTECH e' in ST, e l'ST e' molto piu'
    semplice del ladder da produrre: e' testo, non XML con celle e coordinate.
    Incollarlo costa 3-4 secondi contro i 14 dell'import ladder.

    codice  il testo ST da scrivere (vuoto = crea il POU e basta)
    nome    nome da dare al POU; vuoto = lascia quello proposto da Sysmac

    Richiede il progetto aperto. Il POU viene creato in coda a Programmi.
    """
    _focus_sysmac()
    time.sleep(0.4)

    # l'albero va espanso fino a "Programmi": i nodi sono di un TreeView Win32
    # che UIA non espone, quindi si usano i triangolini a coordinate note
    for cx, cy in ((19, 233), (54, 259), (84, 285)):
        _clickf(cx, cy)
        time.sleep(0.9)
    _clickf(140, 285)                 # seleziona "Programmi"
    time.sleep(0.7)
    _clickf(140, 285, "right")        # menu contestuale
    time.sleep(1.8)
    # da qui in poi solo tastiera: il popup e' una finestra a se' e un clic
    # che porti Sysmac in primo piano lo farebbe sparire
    _send_keys("{DOWN}")              # "Aggiungi"
    time.sleep(0.6)
    _send_keys("{RIGHT}")             # apre il sottomenu Ladder / ST
    time.sleep(1.2)
    _send_keys("{DOWN}")              # da Ladder a ST
    time.sleep(0.5)
    _send_keys("{ENTER}")
    time.sleep(3.5)

    if nome:
        _send_keys("{F2}")
        time.sleep(0.8)
        _send_keys("^a")
        _scrivi_appunti(nome)
        time.sleep(0.5)
        _send_keys("{ENTER}")
        time.sleep(1.5)

    # apre il POU appena creato: e' l'ultima riga sotto Programmi
    albero_prima = sysmac_ui_dump("", 400) or ""
    for y in (337, 363, 389, 415):
        _clickf(178, y, "left", True)
        time.sleep(2.5)
        dump = sysmac_ui_dump("", 400) or ""
        aperte = [r for r in dump.splitlines()
                  if "Pane" in r and "Programma" in r and "Sezione" not in r]
        if aperte and dump != albero_prima:
            break
    else:
        return "FALLITO: POU creato ma non sono riuscito ad aprirlo."

    if codice:
        return sysmac_st_scrivi(codice)
    return "POU in ST creato e aperto."


@mcp.tool()
def sysmac_st_scrivi(codice: str) -> str:
    """Scrive il codice nel POU in Structured Text gia' aperto nell'editor.

    Sostituisce tutto il contenuto (Ctrl+A) e incolla dagli appunti. Verifica
    poi che il testo sia davvero finito nell'editor confrontando la prima riga
    non vuota."""
    _focus_sysmac()
    time.sleep(0.3)
    _clickf(700, 300)                 # cursore dentro l'area di testo
    time.sleep(0.6)
    _send_keys("^a")
    time.sleep(0.3)
    _scrivi_appunti(codice)
    time.sleep(1.5)
    prima = ""
    for riga in codice.splitlines():
        if riga.strip():
            prima = riga.strip()[:30]
            break
    dump = sysmac_ui_dump("", 600) or ""
    if prima and prima not in dump:
        return ("Codice incollato (%d righe), ma non ho potuto verificarlo "
                "nell'albero: controllare l'editor." % len(codice.splitlines()))
    return "Codice ST scritto: %d righe." % len(codice.splitlines())


'''

ancora = "@mcp.tool()\ndef sysmac_save("
if s.count(ancora) != 1:
    raise SystemExit("aggancio non trovato")
s = s.replace(ancora, NUOVO + ancora)

# helper per scrivere dagli appunti, se non c'e' gia'
if "def _scrivi_appunti(" not in s:
    HELPER = '''
def _scrivi_appunti(testo: str) -> None:
    """Mette il testo negli appunti e lo incolla con Ctrl+V.

    Per il codice ST e' l'unica strada sensata: SendKeys interpreta le
    parentesi, il piu' e le graffe come comandi, e un programma di cento
    righe battuto tasto per tasto ci metterebbe minuti."""
    _ps("Add-Type -AssemblyName System.Windows.Forms; "
        "[System.Windows.Forms.Clipboard]::SetText(%s)" % _ps_quote(testo))
    time.sleep(0.4)
    _send_keys("^v")


'''
    s = s.replace("\n@mcp.tool()\ndef sysmac_st_nuovo(", HELPER + "\n@mcp.tool()\ndef sysmac_st_nuovo(", 1)

open(SRV, "w", encoding="utf-8").write(s)

import py_compile
py_compile.compile(SRV, doraise=True)
print("H: sysmac_st_nuovo e sysmac_st_scrivi aggiunti al server")
