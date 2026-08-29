# -*- coding: utf-8 -*-
"""patch_F.py - le due rifiniture rimaste aperte (28/08/2026).

F1  sysmac_save controllava il dialogo "Salva progetto" dopo 2,5 s fissi. Sui
    progetti grossi il dialogo compare dopo 4-5 s: il tool rispondeva
    "salvato" mentre il salvataggio non era ancora partito. Ora attende fino
    a 12 s, e appena il dialogo appare lo compila.

F2  sysmac_apri_sezione cercava i nodi come TreeItem e non trovava niente.
    Motivo: l'Explorer multivista NON e' WPF, e' un TreeView Win32
    (WindowsForms10.SysTreeView32) ospitato in un WindowsFormsHost, e UI
    Automation non ne pubblica i nodi. Si pilota da TASTIERA, con la ricerca
    incrementale del common control:
      - una sola coordinata, il centro del WindowsFormsHost, per dare il fuoco
      - HOME per salire in cima
      - si digita "Programmazione" (ricerca incrementale) e si preme * del
        tastierino, che nei TreeView Win32 espande TUTTO il sottoalbero
      - si digita il nome della sezione e si preme INVIO
    La verifica e' che compaia la scheda "<sezione> - <programma>" fra i Pane.
"""
import os
import shutil

MCP = r"C:\Users\tecni\Claude\sysmac-mcp"
SRV = os.path.join(MCP, "server.py")


def backup(p, tag):
    b = p + ".bak_" + tag
    if not os.path.exists(b):
        shutil.copy2(p, b)


def sostituisci(testo, vecchio, nuovo, etichetta):
    if testo.count(vecchio) != 1:
        raise SystemExit("aggancio %r: %d occorrenze" % (etichetta, testo.count(vecchio)))
    return testo.replace(vecchio, nuovo)


backup(SRV, "pre_patchF")
s = open(SRV, encoding="utf-8").read()

# ------------------------------------------------------------------ F1
s = sostituisci(
    s,
    '''    _send_keys("^s")
    time.sleep(2.5)
    albero = sysmac_ui_dump("", 4) or ""
    if "Salva progetto" not in albero:
        return "Salvataggio inviato (Ctrl+S)."''',
    '''    _send_keys("^s")
    # Il dialogo puo' metterci qualche secondo ad aprirsi: su un progetto da
    # 700 rung ne ha impiegati 4-5. Con l'attesa fissa di 2,5 s il tool
    # rispondeva "salvato" mentre non aveva salvato niente.
    albero = ""
    for _ in range(12):
        time.sleep(1)
        albero = sysmac_ui_dump("", 4) or ""
        if "Salva progetto" in albero:
            break
    if "Salva progetto" not in albero:
        return "Salvataggio inviato (Ctrl+S)."''',
    "F1 attesa dialogo")

# ------------------------------------------------------------------ F2
inizio = s.index("@mcp.tool()\ndef sysmac_apri_sezione(")
fine = s.index("@mcp.tool()\ndef sysmac_save(")
NUOVO = '''@mcp.tool()
def sysmac_apri_sezione(sezione: str = "Sezione0", programma: str = "") -> str:
    """Apre una SEZIONE ladder nell'editor senza clic a coordinate fisse.

    L'Explorer multivista NON e' un albero WPF: e' un TreeView Win32
    (WindowsForms10.SysTreeView32) dentro un WindowsFormsHost, e UI Automation
    non ne pubblica i nodi - cercarli come TreeItem non trova nulla. Si pilota
    quindi da tastiera, con la ricerca incrementale del common control:
    HOME, si digita "Programmazione", si preme * del tastierino (che nei
    TreeView Win32 espande tutto il sottoalbero), si digita il nome della
    sezione e si conferma con INVIO.

    L'unica coordinata usata e' il centro del WindowsFormsHost, letto da UIA:
    segue il pannello se viene spostato o ridimensionato.

    sezione    nome della sezione (default "Sezione0")
    programma  nome del POU, solo per il messaggio di verifica
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
        return ("FALLITO: pannello Explorer multivista non trovato. "
                "Il progetto e' aperto? %s" % (out or "").strip()[:150])
    x, y, w, h = [int(v) for v in riga[-1].split(";")]

    # fuoco sull'albero: primo nodo, poco sotto il bordo alto del pannello
    _click(x + min(w // 2, 120), y + 14)
    time.sleep(0.6)
    _send_keys("{HOME}")
    time.sleep(0.3)
    _send_keys("Programmazione")      # ricerca incrementale sul nodo radice
    time.sleep(0.6)
    _send_keys("{MULTIPLY}")          # espande TUTTO il sottoalbero
    time.sleep(2.0)
    _send_keys(sezione)               # ricerca incrementale sulla sezione
    time.sleep(0.8)
    _send_keys("{ENTER}")

    atteso = sezione.lower()
    for _ in range(12):
        time.sleep(1)
        albero = sysmac_ui_dump("", 400) or ""
        for r in albero.splitlines():
            if "Pane" in r and atteso in r.lower() and "-" in r:
                return "Sezione %r aperta: scheda %r." % (sezione, r.split("|")[-1].strip())
    return ("FALLITO: la scheda della sezione %r non e' comparsa. Verificare il "
            "nome esatto della sezione." % sezione)


'''
s = s[:inizio] + NUOVO + s[fine:]

open(SRV, "w", encoding="utf-8").write(s)

import py_compile
py_compile.compile(SRV, doraise=True)
print("F1 sysmac_save: attesa del dialogo fino a 12 s")
print("F2 sysmac_apri_sezione: navigazione da tastiera nel TreeView Win32")
print("sintassi OK")
