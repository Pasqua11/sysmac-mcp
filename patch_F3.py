# -*- coding: utf-8 -*-
"""patch_F3.py - sysmac_save che salva davvero su file (28/08/2026).

Il dialogo "Salva progetto" e' il common dialog di Windows, non WPF, e UIA lo
espone in modo ingannevole:

  - il campo "Nome file" NON e' un Edit: e' un **Pane** con ClassName 'Edit' e
    AutomationId '1001'. Cercando `-Type Edit` si prendeva invece la colonna
    "Nome" della lista dei file, e la scrittura finiva nel vuoto.
  - quel Pane non espone ValuePattern, quindi SetValue non si puo' usare.
  - anche i pulsanti Salva/Annulla sono **Pane** con ClassName 'Button', per
    cui Invoke-UiButton (che filtra per ControlType Button) non li trova.

Quello che funziona: leggere da UIA il RETTANGOLO del campo (cosi' non ci sono
coordinate fisse), cliccarci dentro, Ctrl+A, digitare il percorso e INVIO.
Misurato: 5,6 s, file creato.
"""
import os
import shutil

SRV = r"C:\Users\tecni\Claude\sysmac-mcp\server.py"

b = SRV + ".bak_pre_patchF3"
if not os.path.exists(b):
    shutil.copy2(SRV, b)

s = open(SRV, encoding="utf-8").read()

vecchio = '''    _uia("$w = Get-SysmacDialog 'Salva progetto'; "
         "$e = Find-UiElement -Root $w -Type Edit; "
         "if ($e) { $vp = $e.GetCurrentPattern("
         "[System.Windows.Automation.ValuePattern]::Pattern); "
         "$vp.SetValue(%s); 'SCRITTO' } else { 'CAMPO NON TROVATO' }"
         % _ps_quote(file))
    time.sleep(0.6)
    _uia("$w = Get-SysmacDialog 'Salva progetto'; "
         "[void](Invoke-UiButton -Root $w -Name 'Salva')")
    for _ in range(30):
        time.sleep(1)
        if "Salva progetto" not in (sysmac_ui_dump("", 3) or ""):
            return "Progetto salvato in %s" % file
    return "FALLITO: il dialogo 'Salva progetto' e' ancora aperto."'''

nuovo = '''    # Il campo "Nome file" e' un Pane con ClassName 'Edit' e AutomationId
    # '1001', senza ValuePattern: si trova solo cosi'. Di lui prendo il
    # rettangolo (niente coordinate fisse) e ci scrivo dentro da tastiera.
    out = _uia(
        "$w = Get-SysmacDialog 'Salva progetto'; "
        "$c1 = New-Object System.Windows.Automation.PropertyCondition("
        "[System.Windows.Automation.AutomationElement]::AutomationIdProperty, '1001'); "
        "$c2 = New-Object System.Windows.Automation.PropertyCondition("
        "[System.Windows.Automation.AutomationElement]::ClassNameProperty, 'Edit'); "
        "$and = New-Object System.Windows.Automation.AndCondition($c1, $c2); "
        "$e = $w.FindFirst([System.Windows.Automation.TreeScope]::Descendants, $and); "
        "if ($e) { $r = $e.Current.BoundingRectangle; "
        "'{0};{1};{2};{3}' -f [int]$r.X, [int]$r.Y, [int]$r.Width, [int]$r.Height } "
        "else { 'NOCAMPO' }")
    riga = [r for r in (out or "").splitlines() if r.count(";") == 3]
    if not riga:
        _send_keys("{ESC}")
        return ("FALLITO: campo 'Nome file' non trovato nel dialogo. %s"
                % (out or "").strip()[:150])
    cx, cy, cw, ch = [int(v) for v in riga[-1].split(";")]
    _click(cx + cw // 2, cy + ch // 2)
    time.sleep(0.5)
    _send_keys("^a")
    time.sleep(0.3)
    _send_keys(file)
    time.sleep(0.8)
    _send_keys("{ENTER}")
    for _ in range(40):
        time.sleep(1)
        if "Salva progetto" not in (sysmac_ui_dump("", 3) or ""):
            if os.path.exists(file):
                return "Progetto salvato in %s" % file
            return ("Dialogo chiuso ma il file %s non risulta creato: "
                    "controllare il percorso." % file)
    return "FALLITO: il dialogo 'Salva progetto' e' ancora aperto."'''

if s.count(vecchio) != 1:
    raise SystemExit("aggancio non trovato (%d occorrenze)" % s.count(vecchio))

open(SRV, "w", encoding="utf-8").write(s.replace(vecchio, nuovo))

import py_compile
py_compile.compile(SRV, doraise=True)
print("F3 sysmac_save: campo 'Nome file' trovato per AutomationId+ClassName")
