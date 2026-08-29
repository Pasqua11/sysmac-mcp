# -*- coding: utf-8 -*-
"""
patch_D2.py - sysmac_vars: selezione della RIGA via UI Automation

Primo tentativo fallito e perche':
  - "Crea nuovo" + ESC lascia il fuoco sulla CELLA, non sulla riga: l'Incolla
    del menu contestuale finisce dentro la cella Nome (si vede il TSV intero
    scritto li' dentro: "e False Non pubblica...").
  - Shift+Spazio, che nelle griglie standard seleziona la riga, qui non fa nulla.

Quello che funziona e' cliccare il SELETTORE DI RIGA (la colonnina grigia a
sinistra della colonna Nome). Non serve pero' una coordinata fissa: le righe
sono esposte come DataItem con il loro rettangolo, quindi il punto si calcola:
    x = rettangolo.X + 8      y = rettangolo.Y + altezza/2
Verificato: 4 -> 9 variabili globali, le 5 attese piu' la riga vuota tecnica.

La riga vuota creata da "Crea nuovo" resta al suo posto anche dopo l'incolla
(le nuove righe vanno sotto), quindi si elimina ricliccando lo stesso punto.
"""
import os, re, shutil, sys

SRV = r"C:\Users\tecni\Claude\sysmac-mcp\server.py"
BAK = SRV + ".bak_pre_riga_uia"

HELPER = '''

def _selettore_ultima_riga():
    """(x, y) del selettore dell'ULTIMA riga della griglia a fuoco, in
    coordinate schermo, ricavato dal rettangolo della riga via UI Automation.

    Serve perche' l'Incolla del menu contestuale si applica alla CELLA se non
    e' selezionata la riga intera: il TSV finirebbe scritto dentro la cella."""
    ps = ("$w = Get-SysmacMainWindow; $best = $null; "
          "foreach ($r in @(Find-UiElements -Root $w -Type DataItem)) { "
          "  $b = $r.Current.BoundingRectangle; "
          "  if ($b.Width -gt 100) { if (-not $best -or $b.Y -gt $best.Y) { $best = $b } } }; "
          "if ($best) { '' + [int]$best.X + ';' + [int]$best.Y + ';' + [int]$best.Height } "
          "else { 'NIENTE' }")
    out = _uia(ps).strip().splitlines()
    ultima = out[-1].strip() if out else ""
    if ";" not in ultima:
        raise RuntimeError("nessuna riga di griglia trovata: la tabella variabili "
                           "e' aperta e ha almeno una riga?")
    x, y, h = [int(v) for v in ultima.split(";")]
    return x + 8, y + h // 2
'''

NUOVO_CORPO = '''    tab = (tabella or "globali").strip().lower()
    if tab not in ("globali", "interne", "esterne"):
        raise ValueError("tabella deve essere 'globali', 'interne' o 'esterne'")
    tsv = _tsv_variabili(variabili, tab)
    attese = tsv.count("\\r\\n") + 1

    prima = _conta_variabili(tab, programma)

    _ps("Add-Type -AssemblyName System.Windows.Forms; "
        "[System.Windows.Forms.Clipboard]::SetText(" + _ps_quote(tsv) + ")", sta=True)

    _clickf(riga_x, riga_y)          # unico click "cieco": fuoco alla griglia
    time.sleep(0.4)
    _send_keys("^{END}")             # ultima riga
    time.sleep(0.8)

    # riga nuova in fondo (fa da cuscinetto: incollare su una riga esistente la
    # sovrascriverebbe), dal menu contestuale aperto da tastiera
    _send_keys("+{F10}"); time.sleep(1.0)
    if "OK" not in _uia("if (Invoke-UiMenuItem -Name 'Crea nuovo') { 'OK' } else { 'KO' }"):
        _send_keys("{ESC}")
        raise RuntimeError("non sono riuscito a creare la riga nuova in fondo.")
    time.sleep(0.8)
    _send_keys("{ESC}")              # esce dall'editing della cella
    time.sleep(0.5)

    # seleziona la RIGA intera cliccandone il selettore, calcolato via UIA
    sel_x, sel_y = _selettore_ultima_riga()
    _click(sel_x, sel_y)
    time.sleep(0.5)

    _send_keys("+{F10}"); time.sleep(1.0)
    if "OK" not in _uia("if (Invoke-UiMenuItem -Name 'Incolla') { 'OK' } else { 'KO' }"):
        _send_keys("{ESC}")
        raise RuntimeError("Incolla non disponibile nel menu contestuale.")
    time.sleep(1.8)

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

    # la riga vuota resta dov'era (le nuove vanno sotto): stesso punto, Elimina
    _click(sel_x, sel_y)
    time.sleep(0.4)
    _send_keys("+{F10}"); time.sleep(1.0)
    _uia("Invoke-UiMenuItem -Name 'Elimina' | Out-Null")
    time.sleep(0.8)

    _send_keys("^s"); time.sleep(2.2)
    dopo = _conta_variabili(tab, programma)
    if prima >= 0 and dopo >= 0:
        delta = dopo - prima
        if delta <= 0:
            raise RuntimeError(
                "VARIABILI NON CREATE: la tabella %s aveva %d righe e ne ha %d "
                "(attese +%d). Controllare che sia aperta la tabella giusta e "
                "che il primo click (%d,%d) cada su una sua cella."
                % (tab, prima, dopo, attese, riga_x, riga_y))
        avviso = "" if delta == attese else " ATTENZIONE: attese %d, create %d." % (attese, delta)
        return ("Create %d variabili in '%s' (%d -> %d).%s%s"
                % (delta, tab, prima, dopo, conflitti, avviso))
    return ("Incollate %d variabili in '%s' (verifica su disco non disponibile).%s"
            % (attese, tab, conflitti))
'''


def main():
    dry = "--dry" in sys.argv
    s = open(SRV, encoding="utf-8").read()
    assert "_selettore_ultima_riga" not in s, "patch D2: gia' applicata"

    # 1) helper prima di _tsv_variabili
    ancora = "\ndef _tsv_variabili("
    assert ancora in s, "patch D2: ancora _tsv_variabili non trovata"
    s2 = s.replace(ancora, HELPER + ancora, 1)

    # 2) sostituisce il corpo di sysmac_vars (dalla fine della docstring alla riga vuota
    #    che precede la funzione seguente)
    i = s2.find("def sysmac_vars(")
    assert i > 0, "patch D2: sysmac_vars non trovata"
    d0 = s2.find('"""', i)
    d1 = s2.find('"""', d0 + 3)
    assert d1 > d0, "patch D2: docstring di sysmac_vars non trovata"
    fine = s2.find("\n@mcp.tool", d1)
    if fine < 0:
        fine = s2.find("\ndef sysmac_vars_crea(", d1)
    assert fine > d1, "patch D2: fine di sysmac_vars non trovata"
    s2 = s2[:d1 + 3] + "\n" + NUOVO_CORPO + s2[fine:]

    print("server.py: %d -> %d (%+d)" % (len(s), len(s2), len(s2) - len(s)))
    if dry:
        print("(dry run)")
        return
    if not os.path.exists(BAK):
        shutil.copyfile(SRV, BAK)
    open(SRV, "w", encoding="utf-8").write(s2)
    print("scritto (backup .bak_pre_riga_uia)")


if __name__ == "__main__":
    main()
