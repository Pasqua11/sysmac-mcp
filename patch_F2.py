# -*- coding: utf-8 -*-
"""patch_F2.py - sysmac_apri_sezione, versione che funziona davvero.

Cosa si e' scoperto provandolo sul campo (28/08/2026):

1. L'Explorer multivista NON e' WPF: e' un TreeView Win32
   (WindowsForms10.SysTreeView32) dentro un WindowsFormsHost. UI Automation
   non ne pubblica i nodi, quindi cercarli come TreeItem non trova nulla.
2. La RICERCA INCREMENTALE (digitare il nome del nodo) non risponde.
3. Il tasto * del tastierino NON espande ricorsivamente: apre un livello solo.
4. Il tasto FRECCIA DESTRA invece fa due cose a seconda dello stato: se il
   nodo e' chiuso lo apre, se e' gia' aperto scende al PRIMO FIGLIO. Quindi
   premendolo abbastanza volte si arriva sempre alla prima foglia del ramo -
   che sotto Programmazione e' POUs > Programmi > Programma0 > Sezione0.
   Arrivati alla foglia, i tasti in piu' non fanno danno.
5. Ogni chiamata a _send_keys costa un avvio di PowerShell: mandare 12 tasti
   separati costava 12 s. In una sola sequenza ("{RIGHT 12}") ne costa uno.
"""
import os
import shutil

SRV = r"C:\Users\tecni\Claude\sysmac-mcp\server.py"

b = SRV + ".bak_pre_patchF2"
if not os.path.exists(b):
    shutil.copy2(SRV, b)

s = open(SRV, encoding="utf-8").read()

inizio = s.index("@mcp.tool()\ndef sysmac_apri_sezione(")
fine = s.index("@mcp.tool()\ndef sysmac_save(")

NUOVO = '''@mcp.tool()
def sysmac_apri_sezione(sezione: str = "", programma: str = "") -> str:
    """Apre una SEZIONE ladder nell'editor senza clic a coordinate fisse.

    L'Explorer multivista non e' un albero WPF ma un TreeView Win32 dentro un
    WindowsFormsHost: UI Automation non ne pubblica i nodi e cercarli come
    TreeItem non trova niente. Si pilota da tastiera sfruttando il fatto che
    la FRECCIA DESTRA apre il nodo chiuso e, se e' gia' aperto, scende al
    primo figlio: ripetendola si arriva alla prima foglia del ramo, cioe'
    Programmazione > POUs > Programmi > <primo programma> > <prima sezione>.

    L'unica coordinata e' il centro del pannello, letto da UIA: segue il
    pannello se viene spostato o ridimensionato.

    sezione   nome atteso della sezione; vuoto = apre la prima e basta.
              Se il nome non corrisponde, scende di una riga e riprova.
    programma nome del POU, usato solo nel messaggio finale.
    """
    _focus_sysmac()
    out = _uia(
        "$w = Get-SysmacMainWindow; "
        "$c = New-Object System.Windows.Automation.PropertyCondition("
        "[System.Windows.Automation.AutomationElement]::ClassNameProperty, "
        "'WindowsFormsHost'); "
        "$h = $w.FindFirst([System.Windows.Automation.TreeScope]::Descendants, $c); "
        "if ($h) { $r = $h.Current.BoundingRectangle; "
        "'{0};{1};{2};{3}' -f [int]$r.X, [int]$r.Y, [int]$r.Width, [int]$r.Height } "
        "else { 'NOHOST' }")
    riga = [r for r in (out or "").splitlines() if r.count(";") == 3]
    if not riga:
        return ("FALLITO: pannello Explorer multivista non trovato - il "
                "progetto e' aperto? %s" % (out or "").strip()[:150])
    x, y, w, h = [int(v) for v in riga[-1].split(";")]

    def _schede():
        alb = sysmac_ui_dump("", 400) or ""
        return [r.split("|")[-1].strip() for r in alb.splitlines()
                if "Pane" in r and " - " in r]

    prima = set(_schede())
    # fuoco sull'albero, poi: in cima, chiudi il primo ramo, scendi su
    # Programmazione e vai giu' fino alla prima foglia. Tutto in una sola
    # sequenza: ogni chiamata separata costerebbe un avvio di PowerShell.
    _click(x + min(w // 2, 120), y + 14)
    time.sleep(0.5)
    _send_keys("{HOME}{LEFT}{DOWN}")
    time.sleep(0.8)
    _send_keys("{RIGHT 12}")
    time.sleep(2.0)
    _send_keys("{ENTER}")

    for tentativo in range(12):
        for _ in range(6):
            time.sleep(0.8)
            nuove = [t for t in _schede() if t not in prima]
            if nuove:
                break
        else:
            nuove = []
        if nuove:
            aperta = nuove[-1]
            if not sezione or sezione.lower() in aperta.lower():
                return "Sezione aperta: %s" % aperta
            prima.add(aperta)
        # nome diverso da quello chiesto: scendo di una riga e riprovo
        _send_keys("{DOWN}{ENTER}")

    return ("FALLITO: non ho aperto una scheda di nome %r. Verificare il nome "
            "esatto della sezione nell'Explorer." % sezione)


'''

open(SRV, "w", encoding="utf-8").write(s[:inizio] + NUOVO + s[fine:])

import py_compile
py_compile.compile(SRV, doraise=True)
print("F2 riscritto: freccia destra ripetuta, una sola sequenza di tasti")
