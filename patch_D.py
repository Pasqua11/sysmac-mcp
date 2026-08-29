# -*- coding: utf-8 -*-
"""
patch_D.py - Intervento D: variabili in blocco SENZA chiudere il progetto

Finora per creare variabili si faceva: chiudi progetto -> vars_offline (scrive
i file) -> riapri. Due-tre minuti a giro, quattro giri nella sola sessione
della batteria, e ogni riapertura poteva lasciare la finestra nascosta.

sysmac_vars() lo fa a progetto APERTO e senza click a coordinate: il menu
contestuale si apre con Shift+F10 e le voci si scelgono per NOME
("Crea nuovo", "Incolla", "Elimina"), verificato leggibile via UI Automation.

Al termine conta le variabili sul disco prima e dopo: se non sono aumentate,
fallisce invece di dire che ha funzionato.
"""
import os, shutil, sys

PS1 = r"C:\Users\tecni\Claude\sysmac_ui.ps1"
SRV = r"C:\Users\tecni\Claude\sysmac-mcp\server.py"
BAK_PS1 = PS1 + ".bak_pre_vars"
BAK_SRV = SRV + ".bak_pre_vars"

MENUITEM = r'''

function Invoke-UiMenuItem {
    <#
      Preme la voce $Name di un menu APERTO (contestuale o di finestra).
      Il menu contestuale si apre da tastiera con Shift+F10: cosi' non servono
      coordinate e la voce si sceglie per nome.
    #>
    param([Parameter(Mandatory)][string]$Name)
    $root = [System.Windows.Automation.AutomationElement]::RootElement
    $mi = Find-UiElement -Root $root -Name $Name -Type MenuItem
    if (-not $mi) { Write-Warning "Voce di menu '$Name' non trovata"; return $false }
    if (-not $mi.Current.IsEnabled) { Write-Warning "Voce '$Name' disabilitata"; return $false }
    Invoke-UiElement -Element $mi
}
'''

TOOL = '''

def _tsv_variabili(variabili: str, tab: str) -> str:
    """Righe 'NOME TIPO [commento]' -> TSV con le colonne della tabella scelta.
    Stessi formati di sysmac_vars_crea, verificati su Sysmac Studio 1.66."""
    righe = []
    for r in (variabili or "").splitlines():
        r = r.strip()
        if not r:
            continue
        if "\\t" in r:
            p = r.split("\\t")
        elif ":" in r and " " not in r.split(":")[0]:
            p = r.split(":", 1)
        else:
            p = r.split(None, 1)
        nome = p[0].strip()
        tipo = p[1].strip() if len(p) > 1 else ""
        com = p[2].strip() if len(p) > 2 else ""
        if tab != "esterne" and not tipo:
            raise ValueError("riga senza tipo: %r (atteso NOME TIPO)" % r)
        if tab == "globali":
            righe.append("\\t".join([nome, tipo, "", "", "False", "False",
                                    "Non pubblicare", com]))
        elif tab == "interne":
            righe.append("\\t".join([nome, tipo, "", "", "False", "False", com]))
        else:
            righe.append("\\t".join([nome, "False", com]))
    if not righe:
        raise ValueError("nessuna variabile indicata")
    return "\\r\\n".join(righe)


def _conta_variabili(tab: str, programma: str = "") -> int:
    """Quante variabili ci sono nella tabella indicata, lette dal DISCO."""
    cart = _cartella_progetto_aperto()
    if not cart:
        return -1
    d = os.path.dirname(os.path.abspath(__file__))
    if d not in sys.path:
        sys.path.insert(0, d)
    import slwd
    try:
        f = slwd.file_globali(cart) if tab == "globali" else slwd.file_locali(cart, programma)
        _testa, gruppi = slwd.leggi(f)
    except Exception:
        return -1
    sigla = {"globali": "VAR", "interne": "VAR", "esterne": "VAR_EXTERNAL"}[tab]
    tot = 0
    for intest, righe in gruppi:
        if ("GN=%s" % sigla) in intest:
            tot += len(righe)
    return tot


@mcp.tool()
def sysmac_vars(variabili: str, tabella: str = "globali", programma: str = "",
                riga_x: int = 385, riga_y: int = 225) -> str:
    """Crea VARIABILI in blocco a progetto APERTO, senza chiuderlo e senza
    click a coordinate sui menu.

    variabili: una per riga, "NOME TIPO" (o "NOME:TIPO", o TSV completo).
               Per la tabella "esterne" basta il nome.
    tabella:   "globali" | "interne" | "esterne"
    programma: nome del POU per interne/esterne (serve solo alla verifica)

    PRIMA di chiamarlo: aprire la tabella giusta in Sysmac (Variabili globali
    dall'albero, oppure la barra "Variabili" sopra l'editor della sezione per
    interne/esterne). riga_x/riga_y servono solo al primo click, che da' il
    fuoco alla griglia: tutto il resto (ultima riga, menu contestuale, crea
    riga, incolla, elimina la riga vuota) va da se'.

    Sostituisce il giro chiudi progetto -> vars_offline -> riapri, che costava
    2-3 minuti e rischiava di lasciare la finestra nascosta."""
    tab = (tabella or "globali").strip().lower()
    if tab not in ("globali", "interne", "esterne"):
        raise ValueError("tabella deve essere 'globali', 'interne' o 'esterne'")
    tsv = _tsv_variabili(variabili, tab)
    attese = tsv.count("\\r\\n") + 1

    prima = _conta_variabili(tab, programma)

    _ps("Add-Type -AssemblyName System.Windows.Forms; "
        "[System.Windows.Forms.Clipboard]::SetText(" + _ps_quote(tsv) + ")", sta=True)

    _clickf(riga_x, riga_y)          # unico click: da' il fuoco alla griglia
    time.sleep(0.4)
    _send_keys("^{END}")             # ultima riga
    time.sleep(0.8)

    # riga nuova in fondo, dal menu contestuale aperto da tastiera
    _send_keys("+{F10}"); time.sleep(1.0)
    out = _uia("if (Invoke-UiMenuItem -Name 'Crea nuovo') { 'OK' } else { 'KO' }")
    if "OK" not in out:
        _send_keys("{ESC}")
        raise RuntimeError("non sono riuscito a creare la riga nuova: %s" % out.strip())
    time.sleep(0.8)
    _send_keys("{ESC}")              # esce dall'editing della cella
    time.sleep(0.4)

    # incolla il blocco
    _send_keys("+{F10}"); time.sleep(1.0)
    out = _uia("if (Invoke-UiMenuItem -Name 'Incolla') { 'OK' } else { 'KO' }")
    if "OK" not in out:
        _send_keys("{ESC}")
        raise RuntimeError("Incolla non disponibile nel menu contestuale: %s" % out.strip())
    time.sleep(1.5)

    # eventuale dialogo "Risolvi conflitti operazione Incolla"
    conflitti = ""
    if _find_window("Risolvi conflitti"):
        ps1 = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "risolvi_conflitti.ps1")
        if os.path.exists(ps1):
            r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                                "-File", ps1], capture_output=True, text=True,
                               timeout=90, errors="replace").stdout.strip()
            conflitti = " (dialogo conflitti: %s)" % r
        time.sleep(1.0)

    # elimina la riga vuota rimasta dalla "Crea nuovo"
    _send_keys("+{F10}"); time.sleep(1.0)
    _uia("Invoke-UiMenuItem -Name 'Elimina' | Out-Null")
    time.sleep(0.8)

    _send_keys("^s"); time.sleep(2.0)
    dopo = _conta_variabili(tab, programma)
    if prima >= 0 and dopo >= 0:
        delta = dopo - prima
        if delta <= 0:
            raise RuntimeError(
                "VARIABILI NON CREATE: la tabella %s aveva %d righe e ne ha %d "
                "(attese +%d). Controllare che la tabella giusta sia aperta e "
                "che il primo click (%d,%d) cada su una sua cella."
                % (tab, prima, dopo, attese, riga_x, riga_y))
        return ("Create %d variabili in '%s' (attese %d; %d -> %d).%s"
                % (delta, tab, attese, prima, dopo, conflitti))
    return ("Incollate %d variabili in '%s' (verifica su disco non disponibile).%s"
            % (attese, tab, conflitti))
'''


def main():
    dry = "--dry" in sys.argv

    ps = open(PS1, encoding="utf-8", errors="replace").read()
    assert "function Invoke-UiMenuItem" not in ps, "patch D: gia' applicata a sysmac_ui.ps1"
    ps2 = ps + MENUITEM

    s = open(SRV, encoding="utf-8").read()
    assert "def sysmac_vars(" not in s, "patch D: gia' applicata a server.py"
    ancora = "\ndef sysmac_vars_crea("
    assert ancora in s, "patch D: ancora sysmac_vars_crea non trovata"
    s2 = s.replace(ancora, TOOL + ancora, 1)

    print("sysmac_ui.ps1: %d -> %d (%+d)" % (len(ps), len(ps2), len(ps2) - len(ps)))
    print("server.py    : %d -> %d (%+d)" % (len(s), len(s2), len(s2) - len(s)))
    if dry:
        print("(dry run)")
        return
    if not os.path.exists(BAK_PS1):
        shutil.copyfile(PS1, BAK_PS1)
    if not os.path.exists(BAK_SRV):
        shutil.copyfile(SRV, BAK_SRV)
    open(PS1, "w", encoding="utf-8").write(ps2)
    open(SRV, "w", encoding="utf-8").write(s2)
    print("scritti (backup .bak_pre_vars)")


if __name__ == "__main__":
    main()
