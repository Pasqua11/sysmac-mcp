# -*- coding: utf-8 -*-
"""
patch_C.py - Intervento C: pilotare i dialoghi per NOME invece che a coordinate

Aggiunge a sysmac_ui.ps1 le quattro operazioni che mancavano (scrivere in un
campo, spuntare una casella, scegliere da una tendina, selezionare una riga) e
a server.py il tool sysmac_dialogo() che le mette insieme in una sola chiamata.

Nei dialoghi WPF di Sysmac i campi Edit non hanno un Name proprio: l'etichetta
e' un elemento Text separato. Find-UiEditByLabel lo risolve per geometria,
prendendo il campo alla stessa altezza dell'etichetta e subito a destra.

Tutto il PowerShell resta SOLO-ASCII come il resto del file.
"""
import os, shutil, sys

PS1 = r"C:\Users\tecni\Claude\sysmac_ui.ps1"
SRV = r"C:\Users\tecni\Claude\sysmac-mcp\server.py"
BAK_PS1 = PS1 + ".bak_pre_dialoghi"
BAK_SRV = SRV + ".bak_pre_dialoghi"

# --- 1) tipi di controllo mancanti nella mappa -------------------------------
CT_VECCHIO = """    Pane     = [System.Windows.Automation.ControlType]::Pane"""
CT_NUOVO = """    RadioButton = [System.Windows.Automation.ControlType]::RadioButton
    Custom   = [System.Windows.Automation.ControlType]::Custom
    Pane     = [System.Windows.Automation.ControlType]::Pane"""

# --- 2) nuove funzioni, in coda al file -------------------------------------
FUNZIONI = r'''

# ============================================================================
#  SCRITTURA NEI DIALOGHI (28/08/2026)
#  Fino a ieri i dialoghi si pilotavano a coordinate: le tre librerie .slr sono
#  costate ~50 click a pixel con uno screenshot di verifica dopo ognuno, e le
#  coordinate valgono solo a finestra massimizzata. Queste funzioni lavorano
#  per NOME e non si rompono se la finestra si sposta.
# ============================================================================

function Find-UiEditByLabel {
    <#
      Il campo di testo associato a un'ETICHETTA. Nei dialoghi WPF di Sysmac
      l'Edit non ha Name: l'etichetta e' un Text separato alla sua sinistra.
      Si sceglie quindi per geometria: stessa altezza, subito a destra.
    #>
    param(
        [Parameter(Mandatory)]$Root,
        [Parameter(Mandatory)][string]$Label,
        [string]$Type = "Edit"
    )
    $e = Find-UiElement -Root $Root -Name $Label -Type $Type
    if ($e) { return $e }

    $lab = Find-UiElement -Root $Root -Name $Label -Type Text
    if (-not $lab) { return $null }
    $lr = $lab.Current.BoundingRectangle
    $cy = $lr.Y + $lr.Height / 2

    $best = $null
    $bestDx = 1e9
    foreach ($c in @(Find-UiElements -Root $Root -Type $Type)) {
        $r = $c.Current.BoundingRectangle
        if ($r.Width -le 1) { continue }
        $ccy = $r.Y + $r.Height / 2
        if ([Math]::Abs($ccy - $cy) -le ([Math]::Max($r.Height, $lr.Height) / 2 + 8)) {
            $dx = $r.X - ($lr.X + $lr.Width)
            if ($dx -ge -8 -and $dx -lt $bestDx) { $bestDx = $dx; $best = $c }
        }
    }
    $best
}

function Set-UiValue {
    <# Scrive $Value nel campo indicato da $Name (nome del campo o etichetta). #>
    param(
        [Parameter(Mandatory)]$Root,
        [Parameter(Mandatory)][string]$Name,
        [Parameter(Mandatory)][AllowEmptyString()][string]$Value
    )
    $e = Find-UiEditByLabel -Root $Root -Label $Name
    if (-not $e) { Write-Warning "Campo '$Name' non trovato"; return $false }
    try {
        $vp = $e.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern)
    } catch {
        Write-Warning "Campo '$Name' non supporta ValuePattern"; return $false
    }
    if ($vp.Current.IsReadOnly) { Write-Warning "Campo '$Name' in sola lettura"; return $false }
    $vp.SetValue($Value)
    Start-Sleep -Milliseconds 120
    return $true
}

function Set-UiToggle {
    <# Porta la casella $Name nello stato voluto (-On / -On:$false). #>
    param(
        [Parameter(Mandatory)]$Root,
        [Parameter(Mandatory)][string]$Name,
        [bool]$On = $true
    )
    $e = Find-UiElement -Root $Root -Name $Name -Type CheckBox
    if (-not $e) { Write-Warning "Casella '$Name' non trovata"; return $false }
    try {
        $tp = $e.GetCurrentPattern([System.Windows.Automation.TogglePattern]::Pattern)
    } catch {
        Write-Warning "Casella '$Name' non supporta TogglePattern"; return $false
    }
    $voluto = if ($On) { "On" } else { "Off" }
    $giri = 0
    while ("$($tp.Current.ToggleState)" -ne $voluto -and $giri -lt 3) {
        $tp.Toggle(); Start-Sleep -Milliseconds 150; $giri++
    }
    return ("$($tp.Current.ToggleState)" -eq $voluto)
}

function Select-UiComboItem {
    <# Sceglie la voce $Item dalla tendina indicata da $Name (nome o etichetta). #>
    param(
        [Parameter(Mandatory)]$Root,
        [Parameter(Mandatory)][string]$Name,
        [Parameter(Mandatory)][string]$Item
    )
    $cb = Find-UiEditByLabel -Root $Root -Label $Name -Type ComboBox
    if (-not $cb) { Write-Warning "Tendina '$Name' non trovata"; return $false }
    try {
        $ec = $cb.GetCurrentPattern([System.Windows.Automation.ExpandCollapsePattern]::Pattern)
        $ec.Expand(); Start-Sleep -Milliseconds 250
    } catch { }
    $it = Find-UiElement -Root $cb -Name $Item -Type ListItem
    if (-not $it) {
        $it = Find-UiElement -Root $script:AE::RootElement -Name $Item -Type ListItem
    }
    if (-not $it) { Write-Warning "Voce '$Item' non trovata nella tendina '$Name'"; return $false }
    try {
        $si = $it.GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern)
        $si.Select()
    } catch {
        Invoke-UiElement -Element $it | Out-Null
    }
    Start-Sleep -Milliseconds 200
    try { $ec.Collapse() } catch { }
    return $true
}

function Select-UiGridRow {
    <# Seleziona la riga di tabella/lista che contiene $Text. #>
    param(
        [Parameter(Mandatory)]$Root,
        [Parameter(Mandatory)][string]$Text
    )
    foreach ($t in @("DataItem", "ListItem", "TreeItem", "Custom")) {
        $e = Find-UiElement -Root $Root -Name $Text -Type $t
        if ($e) {
            try {
                $si = $e.GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern)
                $si.Select()
                return $true
            } catch {
                try { $e.SetFocus(); return $true } catch { }
            }
        }
    }
    Write-Warning "Riga '$Text' non trovata"
    return $false
}
'''

# --- 3) il tool che mette tutto insieme -------------------------------------
TOOL = '''

@mcp.tool()
def sysmac_dialogo(titolo: str = "", campi: str = "", caselle: str = "",
                   tendine: str = "", pulsante: str = "",
                   riga: str = "") -> str:
    """Compila un dialogo di Sysmac per NOME, senza coordinate.

    titolo   titolo esatto del dialogo; vuoto = finestra principale
    campi    "Etichetta=valore" separati da ';'  (campi di testo)
    caselle  "Etichetta=on|off" separati da ';'  (caselle di spunta)
    tendine  "Etichetta=voce" separati da ';'    (menu a tendina)
    riga     testo della riga di tabella/lista da selezionare
    pulsante nome del pulsante da premere alla fine (OK, Salva, Annulla...)

    Esempio (Impostazione libreria, che prima costava una decina di click):
      sysmac_dialogo(titolo="Impostazione libreria",
                     campi="Nome=SYNTECH_FB_Cappa; Societa=SYNTECH",
                     caselle="Disattiva visualizzazione sorgente=off",
                     pulsante="OK")

    I campi di testo si trovano per ETICHETTA: nei dialoghi WPF di Sysmac
    l'Edit non ha un nome proprio, quindi si prende quello alla stessa altezza
    dell'etichetta e subito a destra."""

    def _coppie(t):
        fuori = []
        for pezzo in (t or "").split(";"):
            pezzo = pezzo.strip()
            if not pezzo:
                continue
            if "=" not in pezzo:
                raise ValueError("atteso 'Etichetta=valore', trovato: %r" % pezzo)
            k, v = pezzo.split("=", 1)
            fuori.append((k.strip(), v.strip()))
        return fuori

    root = f"Get-SysmacDialog {_ps_quote(titolo)}" if titolo else "Get-SysmacMainWindow"
    righe = [f"$r = {root}",
             "if (-not $r) { 'FINESTRA_NON_TROVATA'; exit }"]
    esiti = []
    for k, v in _coppie(campi):
        righe.append(f"if (Set-UiValue -Root $r -Name {_ps_quote(k)} -Value {_ps_quote(v)}) "
                     f"{{ 'OK campo {k}' }} else {{ 'KO campo {k}' }}")
        esiti.append("campo " + k)
    for k, v in _coppie(caselle):
        on = "$true" if v.lower() in ("on", "si", "true", "1", "x") else "$false"
        righe.append(f"if (Set-UiToggle -Root $r -Name {_ps_quote(k)} -On {on}) "
                     f"{{ 'OK casella {k}' }} else {{ 'KO casella {k}' }}")
        esiti.append("casella " + k)
    for k, v in _coppie(tendine):
        righe.append(f"if (Select-UiComboItem -Root $r -Name {_ps_quote(k)} -Item {_ps_quote(v)}) "
                     f"{{ 'OK tendina {k}' }} else {{ 'KO tendina {k}' }}")
        esiti.append("tendina " + k)
    if riga:
        righe.append(f"if (Select-UiGridRow -Root $r -Text {_ps_quote(riga)}) "
                     f"{{ 'OK riga' }} else {{ 'KO riga' }}")
        esiti.append("riga")
    if pulsante:
        righe.append(f"if (Invoke-UiButton -Root $r -Name {_ps_quote(pulsante)}) "
                     f"{{ 'OK pulsante' }} else {{ 'KO pulsante' }}")
        esiti.append("pulsante " + pulsante)

    if len(righe) == 2:
        raise ValueError("niente da fare: indicare almeno campi, caselle, tendine, riga o pulsante.")

    out = _uia("; ".join(righe))
    if "FINESTRA_NON_TROVATA" in out:
        raise RuntimeError("dialogo %r non trovato." % (titolo or "finestra principale"))
    ko = [r for r in out.splitlines() if r.strip().startswith("KO")]
    if ko:
        raise RuntimeError("dialogo %r: %s. Esito completo: %s"
                           % (titolo or "principale", "; ".join(ko), out.strip()))
    return "dialogo %r: %s -> tutto riuscito." % (titolo or "principale", ", ".join(esiti))
'''


def main():
    dry = "--dry" in sys.argv

    ps = open(PS1, encoding="utf-8", errors="replace").read()
    assert CT_VECCHIO in ps, "patch C1: mappa ControlType non trovata"
    assert "function Set-UiValue" not in ps, "patch C: gia' applicata a sysmac_ui.ps1"
    ps2 = ps.replace(CT_VECCHIO, CT_NUOVO, 1) + FUNZIONI

    s = open(SRV, encoding="utf-8").read()
    assert "def sysmac_dialogo(" not in s, "patch C: gia' applicata a server.py"
    ancora = "\ndef sysmac_ui_dump("
    assert ancora in s, "patch C2: ancora sysmac_ui_dump non trovata"
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
    print("scritti (backup .bak_pre_dialoghi)")


if __name__ == "__main__":
    main()
