# risolvi_conflitti.ps1 - gestisce il dialogo "Risolvi conflitti operazione Incolla"
# di Sysmac Studio via UI Automation (InvokePattern): i click del mouse sui
# pulsanti non sono affidabili, l'Invoke si'.
# Sequenza: "Copia tutto da destra a sinistra" -> attende "Applica" abilitato ->
#           "Applica" -> "Chiudi".
# Esce con 0 se applicato, 1 se il dialogo non c'era, 2 in caso di errore.

Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes
$AE = [System.Windows.Automation.AutomationElement]
$TS = [System.Windows.Automation.TreeScope]
$CT = [System.Windows.Automation.ControlType]

function Get-Dialog {
    $cond = New-Object System.Windows.Automation.PropertyCondition(
        $AE::ControlTypeProperty, $CT::Window)
    foreach ($w in $AE::RootElement.FindAll($TS::Children, $cond)) {
        if ($w.Current.Name -like "Risolvi conflitti*") { return $w }
    }
    return $null
}

function Get-Buttons($win) {
    $cb = New-Object System.Windows.Automation.PropertyCondition(
        $AE::ControlTypeProperty, $CT::Button)
    return $win.FindAll($TS::Descendants, $cb)
}

function Invoke-Button($b) {
    $b.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke()
}

$win = Get-Dialog
if ($null -eq $win) { Write-Output "NESSUN_DIALOGO"; exit 1 }

try {
    # 1) "Copia tutto da destra a sinistra": non ha Name (icona + testo),
    #    lo si riconosce come il pulsante largo 200-300 px della barra in alto
    #    fra i pulsanti del dialogo.
    $btns = Get-Buttons $win
    $copia = $null
    foreach ($b in $btns) {
        $r = $b.Current.BoundingRectangle
        if ($b.Current.Name -eq "" -and $r.Width -ge 200 -and $r.Width -le 300) {
            if ($null -eq $copia -or $r.X -gt $copia.Current.BoundingRectangle.X) { $copia = $b }
        }
    }
    if ($null -eq $copia) { Write-Output "PULSANTE_COPIA_NON_TROVATO"; exit 2 }
    Invoke-Button $copia
    Start-Sleep -Milliseconds 700

    # 2) "Applica" (attende che si abiliti)
    $ok = $false
    for ($i = 0; $i -lt 12; $i++) {
        $win = Get-Dialog
        if ($null -eq $win) { break }
        foreach ($b in (Get-Buttons $win)) {
            if ($b.Current.Name -eq "Applica" -and $b.Current.IsEnabled) {
                Invoke-Button $b; $ok = $true; break
            }
        }
        if ($ok) { break }
        Start-Sleep -Milliseconds 400
    }
    if (-not $ok) { Write-Output "APPLICA_NON_ABILITATO"; exit 2 }
    Start-Sleep -Milliseconds 700

    # 3) "Chiudi"
    $win = Get-Dialog
    if ($null -ne $win) {
        foreach ($b in (Get-Buttons $win)) {
            if ($b.Current.Name -eq "Chiudi") { Invoke-Button $b; break }
        }
    }
    Start-Sleep -Milliseconds 500
    if ($null -eq (Get-Dialog)) { Write-Output "APPLICATO_E_CHIUSO"; exit 0 }
    Write-Output "APPLICATO_DIALOGO_ANCORA_APERTO"; exit 0
}
catch {
    Write-Output ("ERRORE: " + $_.Exception.Message); exit 2
}
