# ============================================================================
#  sysmac_ui.ps1 - Libreria UI Automation per Sysmac Studio
#  Creata il 26/08/2026. Funzioni ricavate e testate pilotando la finestra
#  "Personalizzazione tasti di scelta rapida" di Sysmac Studio (32bit).
#
#  USO:   . C:\Users\tecni\Claude\sysmac_ui.ps1
#         $d = Get-SysmacDialog 'Personalizzazione tasti di scelta rapida'
#
#  PERCHE': Sysmac Studio e' WPF e espone l'intera UI via UI Automation.
#  Leggere/pilotare con UIA e' molto piu' affidabile dei click a coordinate,
#  che si rompono se la finestra si sposta o cambia zoom/risoluzione.
#
#  NOTA SOLO-ASCII: niente lettere accentate nel file, per evitare problemi
#  di encoding con Windows PowerShell 5.
# ============================================================================

Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes, System.Windows.Forms

$script:AE   = [System.Windows.Automation.AutomationElement]
$script:TRUE_COND = [System.Windows.Automation.Condition]::TrueCondition

# Mappa nome -> ControlType (solo quelli che servono davvero)
$script:CT = @{
    Button   = [System.Windows.Automation.ControlType]::Button
    Edit     = [System.Windows.Automation.ControlType]::Edit
    Text     = [System.Windows.Automation.ControlType]::Text
    Tree     = [System.Windows.Automation.ControlType]::Tree
    TreeItem = [System.Windows.Automation.ControlType]::TreeItem
    List     = [System.Windows.Automation.ControlType]::List
    ListItem = [System.Windows.Automation.ControlType]::ListItem
    MenuItem = [System.Windows.Automation.ControlType]::MenuItem
    Menu     = [System.Windows.Automation.ControlType]::Menu
    Table    = [System.Windows.Automation.ControlType]::Table
    DataItem = [System.Windows.Automation.ControlType]::DataItem
    DataGrid = [System.Windows.Automation.ControlType]::DataGrid
    RadioButton = [System.Windows.Automation.ControlType]::RadioButton
    Custom   = [System.Windows.Automation.ControlType]::Custom
    Pane     = [System.Windows.Automation.ControlType]::Pane
    Window   = [System.Windows.Automation.ControlType]::Window
    Tab      = [System.Windows.Automation.ControlType]::Tab
    TabItem  = [System.Windows.Automation.ControlType]::TabItem
    ComboBox = [System.Windows.Automation.ControlType]::ComboBox
    CheckBox = [System.Windows.Automation.ControlType]::CheckBox
}

# --- P/Invoke per foreground window ------------------------------------------
if (-not ('SysmacWin32' -as [type])) {
    Add-Type -Namespace SysmacNative -Name Win -MemberDefinition @'
[DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
[DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
[DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
[DllImport("user32.dll")] public static extern void mouse_event(uint f, uint dx, uint dy, uint d, int e);
'@ -PassThru | Out-Null
}

# ============================================================================
#  PROCESSO E FINESTRE
# ============================================================================

function Get-SysmacProcess {
    <# Restituisce il processo di Sysmac Studio, o $null se non e' in esecuzione. #>
    Get-Process -Name 'SysmacStudio' -ErrorAction SilentlyContinue | Select-Object -First 1
}

function Set-SysmacForeground {
    <# Porta Sysmac Studio in primo piano. Da chiamare SEMPRE prima di inviare tasti. #>
    $p = Get-SysmacProcess
    if (-not $p) { Write-Warning 'Sysmac Studio non e in esecuzione'; return $false }
    [SysmacNative.Win]::ShowWindow($p.MainWindowHandle, 9) | Out-Null   # SW_RESTORE
    [SysmacNative.Win]::SetForegroundWindow($p.MainWindowHandle) | Out-Null
    Start-Sleep -Milliseconds 500
    return $true
}

function Get-SysmacMainWindow {
    <#
      Elemento UIA della finestra principale (il titolo contiene il progetto aperto).
      Se MainWindowHandle e' 0 (app in avvio, splash screen) ripiega sulla ricerca
      per ProcessId tra le finestre di primo livello: situazione reale incontrata
      subito dopo un riavvio di Sysmac.
    #>
    $p = Get-SysmacProcess
    if (-not $p) { return $null }
    if ($p.MainWindowHandle -ne 0) { return $script:AE::FromHandle($p.MainWindowHandle) }
    $cond = New-Object System.Windows.Automation.PropertyCondition($script:AE::ProcessIdProperty, $p.Id)
    $w = $script:AE::RootElement.FindAll([System.Windows.Automation.TreeScope]::Children, $cond)
    for ($i = 0; $i -lt $w.Count; $i++) {
        if ($w.Item($i).Current.Name) { return $w.Item($i) }
    }
    if ($w.Count -gt 0) { return $w.Item(0) }
    Write-Warning 'Sysmac in avvio: nessuna finestra ancora disponibile'
    return $null
}

function Wait-SysmacReady {
    <# Attende che Sysmac abbia una finestra utilizzabile (dopo avvio/riavvio). #>
    param([int]$TimeoutSec = 120)
    $t0 = Get-Date
    while (((Get-Date) - $t0).TotalSeconds -lt $TimeoutSec) {
        $m = Get-SysmacMainWindow
        if ($m -and $m.Current.Name) { return $m }
        Start-Sleep -Seconds 3
    }
    Write-Warning "Sysmac non pronto entro $TimeoutSec secondi"
    return $null
}

function Get-SysmacDialog {
    <#
      Trova una finestra di dialogo per titolo esatto.
      Es: Get-SysmacDialog 'Personalizzazione tasti di scelta rapida'
    #>
    param([Parameter(Mandatory)][string]$Title)
    $c = New-Object System.Windows.Automation.PropertyCondition($script:AE::NameProperty, $Title)
    $script:AE::RootElement.FindFirst([System.Windows.Automation.TreeScope]::Descendants, $c)
}

# ============================================================================
#  RICERCA ELEMENTI
# ============================================================================

function Find-UiElement {
    <#
      Cerca UN elemento sotto $Root per nome e/o tipo.
      IMPORTANTE: filtrare SEMPRE anche per -Type quando si cerca un pulsante.
      Nella finestra scorciatoie esistono righe di griglia chiamate "Annulla":
      cercare solo per nome restituisce la riga, non il pulsante, e l'Invoke
      non fa nulla (errore realmente incontrato il 26/08/2026).
    #>
    param(
        [Parameter(Mandatory)]$Root,
        [string]$Name,
        [string]$Type,
        [switch]$DirectChildren
    )
    $conds = @()
    if ($Name) { $conds += New-Object System.Windows.Automation.PropertyCondition($script:AE::NameProperty, $Name) }
    if ($Type) {
        if (-not $script:CT.ContainsKey($Type)) { throw "Tipo '$Type' non mappato. Tipi: $($script:CT.Keys -join ', ')" }
        $conds += New-Object System.Windows.Automation.PropertyCondition($script:AE::ControlTypeProperty, $script:CT[$Type])
    }
    if ($conds.Count -eq 0) { $cond = $script:TRUE_COND }
    elseif ($conds.Count -eq 1) { $cond = $conds[0] }
    else { $cond = New-Object System.Windows.Automation.AndCondition($conds[0], $conds[1]) }

    $scope = if ($DirectChildren) { [System.Windows.Automation.TreeScope]::Children }
             else { [System.Windows.Automation.TreeScope]::Descendants }
    $Root.FindFirst($scope, $cond)
}

function Find-UiElements {
    <# Come Find-UiElement ma restituisce tutti i risultati (array). #>
    param(
        [Parameter(Mandatory)]$Root,
        [string]$Name,
        [string]$Type,
        [switch]$DirectChildren
    )
    $conds = @()
    if ($Name) { $conds += New-Object System.Windows.Automation.PropertyCondition($script:AE::NameProperty, $Name) }
    if ($Type) { $conds += New-Object System.Windows.Automation.PropertyCondition($script:AE::ControlTypeProperty, $script:CT[$Type]) }
    if ($conds.Count -eq 0) { $cond = $script:TRUE_COND }
    elseif ($conds.Count -eq 1) { $cond = $conds[0] }
    else { $cond = New-Object System.Windows.Automation.AndCondition($conds[0], $conds[1]) }
    $scope = if ($DirectChildren) { [System.Windows.Automation.TreeScope]::Children }
             else { [System.Windows.Automation.TreeScope]::Descendants }
    $res = $Root.FindAll($scope, $cond)
    $out = @()
    foreach ($e in $res) { $out += $e }
    $out
}

function Get-UiTexts {
    <# Nomi dei figli di tipo Text di un elemento: in una griglia sono le celle della riga. #>
    param([Parameter(Mandatory)]$Element)
    $v = @()
    foreach ($t in (Find-UiElements -Root $Element -Type Text -DirectChildren)) { $v += $t.Current.Name }
    $v
}

function Get-UiDump {
    <#
      Dump diagnostico: tipo | nome di tutti i discendenti. Serve per capire
      com'e' fatta una finestra sconosciuta prima di automatizzarla.
    #>
    param([Parameter(Mandatory)]$Root, [int]$Max = 500)
    $all = $Root.FindAll([System.Windows.Automation.TreeScope]::Descendants, $script:TRUE_COND)
    $n = [Math]::Min($all.Count, $Max)
    for ($i = 0; $i -lt $n; $i++) {
        $e = $all.Item($i)
        '{0,-28} | {1}' -f $e.Current.ControlType.ProgrammaticName.Replace('ControlType.',''), $e.Current.Name
    }
    if ($all.Count -gt $Max) { "... (troncato: $($all.Count) elementi totali)" }
}

# ============================================================================
#  AZIONI
# ============================================================================

function Invoke-UiElement {
    <# Preme un elemento tramite InvokePattern. #>
    param([Parameter(Mandatory)]$Element)
    $ip = $null
    if ($Element.TryGetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern, [ref]$ip)) {
        $ip.Invoke(); Start-Sleep -Milliseconds 300; return $true
    }
    Write-Warning 'Elemento senza InvokePattern'
    return $false
}

function Invoke-UiButton {
    <#
      Preme il pulsante $Name dentro $Root. Filtra per ControlType Button:
      e' il modo corretto per premere OK / Annulla / Assegna / Esporta.
    #>
    param([Parameter(Mandatory)]$Root, [Parameter(Mandatory)][string]$Name)
    $b = Find-UiElement -Root $Root -Name $Name -Type Button
    if (-not $b) {
        # molti pulsanti espongono l'acceleratore nel nome ("_Crea", "_Salva")
        # o hanno spazi/etichette lunghe: si ripiega su corrispondenza parziale
        foreach ($c in @(Find-UiElements -Root $Root -Type Button)) {
            $n = $c.Current.Name
            if ($n -and (($n -replace '_','') -eq $Name -or $n -like ("*" + $Name + "*"))) { $b = $c; break }
        }
    }
    if (-not $b) { Write-Warning "Pulsante '$Name' non trovato"; return $false }
    if (-not $b.Current.IsEnabled) { Write-Warning "Pulsante '$Name' disabilitato"; return $false }
    Invoke-UiElement -Element $b
}

function Send-SysmacKeys {
    <#
      Invia tasti a Sysmac (sintassi SendKeys: ^ = Ctrl, % = Alt, + = Shift).
      Porta prima la finestra in primo piano, altrimenti i tasti finiscono altrove.
      ATTENZIONE: alcune combinazioni non arrivano (es. Ctrl+Alt+S risulta
      intercettata dal sistema): verificare sempre l'effetto.
    #>
    param([Parameter(Mandatory)][string]$Keys, [int]$DelayMs = 150)
    Set-SysmacForeground | Out-Null
    [System.Windows.Forms.SendKeys]::SendWait($Keys)
    Start-Sleep -Milliseconds $DelayMs
}

function Invoke-UiClickPoint {
    <# Click fisico al centro di un elemento UIA (usare solo se manca InvokePattern). #>
    param([Parameter(Mandatory)]$Element, [int]$OffsetX = 0, [int]$OffsetY = 0)
    $r = $Element.Current.BoundingRectangle
    $x = [int]($r.X + $r.Width / 2 + $OffsetX)
    $y = [int]($r.Y + $r.Height / 2 + $OffsetY)
    [SysmacNative.Win]::SetCursorPos($x, $y) | Out-Null
    Start-Sleep -Milliseconds 120
    [SysmacNative.Win]::mouse_event(0x0002, 0, 0, 0, 0)
    [SysmacNative.Win]::mouse_event(0x0004, 0, 0, 0, 0)
    Start-Sleep -Milliseconds 200
}

# ============================================================================
#  MENU PRINCIPALE
# ============================================================================

function Invoke-SysmacMenu {
    <#
      Apre una voce di menu per NOME, senza click a coordinate.
      Es: Invoke-SysmacMenu -Path 'Strumenti','Personalizza tasti di scelta rapida...'
      (testato: apre la finestra di personalizzazione scorciatoie)
    #>
    param([Parameter(Mandatory)][string[]]$Path)
    $main = Get-SysmacMainWindow
    if (-not $main) { Write-Warning 'Finestra principale non trovata'; return $false }
    # deve essere il MenuItem: cercando per solo nome si prende il Text
    # dell'etichetta ('_Chiudi'), che non ha InvokePattern e non fa nulla
    $top = Find-UiElement -Root $main -Name $Path[0] -Type MenuItem
    if (-not $top) { $top = Find-UiElement -Root $main -Name $Path[0] }
    if (-not $top) { Write-Warning "Menu '$($Path[0])' non trovato"; return $false }
    $ep = $null
    if ($top.TryGetCurrentPattern([System.Windows.Automation.ExpandCollapsePattern]::Pattern, [ref]$ep)) {
        $ep.Expand(); Start-Sleep -Milliseconds 800
    }
    if ($Path.Count -eq 1) { return $true }
    for ($i = 1; $i -lt $Path.Count; $i++) {
        $item = Find-UiElement -Root $top -Name $Path[$i] -Type MenuItem
        if (-not $item) { $item = Find-UiElement -Root $main -Name $Path[$i] -Type MenuItem }
        if (-not $item) { $item = Find-UiElement -Root $top -Name $Path[$i] }
        if (-not $item) { $item = Find-UiElement -Root $main -Name $Path[$i] }
        if (-not $item) {
            Write-Warning "Voce '$($Path[$i])' non trovata"
            if ($ep) { $ep.Collapse() }
            return $false
        }
        if ($i -eq $Path.Count - 1) { return (Invoke-UiElement -Element $item) }
        $ep2 = $null
        if ($item.TryGetCurrentPattern([System.Windows.Automation.ExpandCollapsePattern]::Pattern, [ref]$ep2)) {
            $ep2.Expand(); Start-Sleep -Milliseconds 500
        }
        $top = $item
    }
    return $false
}

# ============================================================================
#  GRIGLIE E ALBERI
# ============================================================================

function Expand-UiTree {
    <#
      Espande TUTTI i nodi di un albero WPF.
      Metodo: seleziona la prima riga, Ctrl+Home, poi Destra+Giu' ripetuti.
      Serve perche' i nodi sono virtualizzati: finche' non vengono espansi e
      scorsi, UIA non li vede proprio (ExpandCollapsePattern qui NON esiste
      sulle righe: l'espansore e' un Button figlio).
    #>
    param([Parameter(Mandatory)]$Tree, [int]$Steps = 400)
    $items = Find-UiElements -Root $Tree -Type TreeItem -DirectChildren
    if ($items.Count -eq 0) { Write-Warning 'Albero vuoto'; return 0 }
    $items[0].SetFocus(); Start-Sleep -Milliseconds 300
    [System.Windows.Forms.SendKeys]::SendWait('^{HOME}'); Start-Sleep -Milliseconds 200
    for ($i = 0; $i -lt $Steps; $i++) {
        [System.Windows.Forms.SendKeys]::SendWait('{RIGHT}'); Start-Sleep -Milliseconds 10
        [System.Windows.Forms.SendKeys]::SendWait('{DOWN}');  Start-Sleep -Milliseconds 10
    }
    Start-Sleep -Milliseconds 500
    (Find-UiElements -Root $Tree -Type TreeItem -DirectChildren).Count
}

function Get-UiTreeRows {
    <#
      Legge tutte le righe di un albero/griglia come oggetti.
      Nella finestra scorciatoie: Cells[0] = tasto assegnato, Cells[-1] = comando.
    #>
    param([Parameter(Mandatory)]$Tree)
    $items = Find-UiElements -Root $Tree -Type TreeItem -DirectChildren
    $out = @()
    for ($i = 0; $i -lt $items.Count; $i++) {
        $cells = Get-UiTexts -Element $items[$i]
        $out += [PSCustomObject]@{
            Index   = $i
            Comando = if ($cells.Count) { $cells[-1] } else { '' }
            Tasto   = if ($cells.Count -gt 1) { $cells[0] } else { '' }
            Cells   = $cells
        }
    }
    $out
}

function Select-UiTreeRow {
    <#
      Seleziona la riga con indice $Index e verifica di esserci arrivato.
      Le righe NON espongono SelectionItemPattern e ScrollIntoView non funziona:
      l'unico metodo affidabile e' la navigazione da tastiera dall'alto.
      Restituisce $true solo se la riga col focus e' quella attesa.
    #>
    param([Parameter(Mandatory)]$Tree, [Parameter(Mandatory)][int]$Index)
    $items = Find-UiElements -Root $Tree -Type TreeItem -DirectChildren
    if ($Index -ge $items.Count) { Write-Warning "Indice $Index fuori range ($($items.Count) righe)"; return $false }
    $items[0].SetFocus(); Start-Sleep -Milliseconds 300
    [System.Windows.Forms.SendKeys]::SendWait('^{HOME}'); Start-Sleep -Milliseconds 300
    for ($i = 0; $i -lt $Index; $i++) {
        [System.Windows.Forms.SendKeys]::SendWait('{DOWN}'); Start-Sleep -Milliseconds 12
    }
    Start-Sleep -Milliseconds 400
    $atteso = (Get-UiTexts -Element $items[$Index]) | Select-Object -Last 1
    $focus  = (Get-UiTexts -Element $script:AE::FocusedElement) | Select-Object -Last 1
    if ($atteso -ne $focus) { Write-Warning "Selezione fallita: atteso '$atteso', trovato '$focus'"; return $false }
    return $true
}

function Get-UiGridRows {
    <#
      Legge le righe di una griglia generica (DataItem / ListItem).
      Pensata per il pannello Compila (errori/avvisi) e la tabella variabili.
      NON ANCORA VERIFICATA su quei pannelli: controllare l'output prima di fidarsi.
    #>
    param([Parameter(Mandatory)]$Root)
    $rows = @()
    foreach ($tipo in @('DataItem', 'ListItem')) {
        foreach ($r in (Find-UiElements -Root $Root -Type $tipo)) {
            $cells = Get-UiTexts -Element $r
            if ($cells.Count -eq 0 -and $r.Current.Name) { $cells = @($r.Current.Name) }
            if ($cells.Count) { $rows += , $cells }
        }
    }
    $rows
}

function Get-SysmacBuildPane {
    <#
      Pannello "Compila". Identificato per AutomationId 'buildWindowsViewWindow':
      e' stabile e non dipende dalla lingua dell'interfaccia ne' da dove il
      pannello e' agganciato. Cercarlo per NOME ('Compila') restituisce invece
      la piccola linguetta della scheda, che non contiene la griglia:
      errore verificato il 26/08/2026.
    #>
    $m = Get-SysmacMainWindow
    if (-not $m) { return $null }
    $c = New-Object System.Windows.Automation.PropertyCondition($script:AE::AutomationIdProperty, 'buildWindowsViewWindow')
    $m.FindFirst([System.Windows.Automation.TreeScope]::Descendants, $c)
}

function Get-SysmacBuildErrors {
    <#
      Legge il pannello "Compila" come TESTO invece di fotografarlo:
      contatori "N Errori / M Avvisi" + una riga per ciascun errore
      (Descrizione | Programma | Posizione).

      Struttura reale verificata il 26/08/2026 su Sysmac Studio (32bit):
        Pane  AutomationId='buildWindowsViewWindow'
          +- Button  -> figli Text: '0' , 'Errori'
          +- Button  -> figli Text: '0' , 'Avvisi'
          +- DataGrid -> intestazioni Descrizione / Programma / Posizione
                         righe = DataItem
      Contatori e struttura verificati con 0 errori. Il formato esatto delle
      celle di una riga di errore non e' stato osservato dal vivo (il progetto
      di prova compilava pulito): le celle vengono restituite cosi' come sono.
    #>
    param([int]$Max = 30, [switch]$IncludiLog)
    $m = Get-SysmacMainWindow
    if (-not $m) { return 'SYSMAC_SENZA_FINESTRA (in avvio, oppure nessun progetto aperto)' }

    $pan = Get-SysmacBuildPane
    if (-not $pan) {
        return 'PANNELLO_COMPILA_NON_TROVATO (aprirlo con Visualizza > Scheda Compilazione, cioe Alt+6)'
    }

    $err = '?'; $avv = '?'
    foreach ($b in (Find-UiElements -Root $pan -Type Button)) {
        $t = Get-UiTexts -Element $b
        if ($t.Count -ge 2) {
            if     ($t[-1] -match 'Errori|Errors')   { $err = $t[0] }
            elseif ($t[-1] -match 'Avvisi|Warnings') { $avv = $t[0] }
        }
    }

    $out = @("ERRORI=$err AVVISI=$avv")
    $grid = Find-UiElement -Root $pan -Type DataGrid
    if (-not $grid) {
        $out += '  (griglia non trovata dentro il pannello)'
        return $out
    }

    # La griglia e' virtualizzata: UIA vede solo le righe gia' disegnate.
    # Con 60 avvisi se ne leggevano 9. Quindi si scorre con ScrollPattern
    # raccogliendo le righe nuove finche' non si arriva in fondo o a $Max.
    $viste = New-Object System.Collections.Specialized.OrderedDictionary
    $sp = $null
    $scrollabile = $false
    if ($grid.TryGetCurrentPattern([System.Windows.Automation.ScrollPattern]::Pattern, [ref]$sp)) {
        $scrollabile = $sp.Current.VerticallyScrollable
    }
    if ($scrollabile) { $sp.SetScrollPercent(-1, 0); Start-Sleep -Milliseconds 250 }

    for ($giro = 0; $giro -lt 60; $giro++) {
        foreach ($r in (Find-UiElements -Root $grid -Type DataItem)) {
            $c = Get-UiTexts -Element $r
            if ($c.Count -eq 0 -and $r.Current.Name) { $c = @($r.Current.Name) }
            if ($c.Count) {
                $riga = ($c -join ' | ')
                if (-not $viste.Contains($riga)) { $viste.Add($riga, $true) }
            }
        }
        if ($viste.Count -ge $Max) { break }
        if (-not $scrollabile) { break }
        if ($sp.Current.VerticalScrollPercent -ge 100) { break }
        $sp.Scroll([System.Windows.Automation.ScrollAmount]::NoAmount,
                   [System.Windows.Automation.ScrollAmount]::LargeIncrement)
        Start-Sleep -Milliseconds 200
    }

    $n = 0
    foreach ($k in $viste.Keys) {
        $n++
        $out += ('  ' + $k)
        if ($n -ge $Max) { break }
    }
    if ($n -eq 0) { $out += '  (nessuna riga in griglia)' }
    elseif ($viste.Count -gt $n) { $out += "  ... (mostrate $n righe su $($viste.Count) lette; alzare -Max)" }

    if ($IncludiLog) {
        $out += '--- log Uscita ---'
        foreach ($l in (Get-SysmacOutputLog -Max 10)) { $out += ('  ' + $l) }
    }
    $out
}

function Get-SysmacOutputLog {
    <#
      Righe del pannello "Uscita" (log operazioni), es.
      "Information<TAB>Compilazione non riuscita: Programma0.Sezione1".
      Utile insieme a Get-SysmacBuildErrors: dice QUALE sezione ha fallito
      anche quando la griglia degli errori e' stata svuotata.
      Individua la lista dai suoi elementi (LogItemViewModel), non da posizione
      o nome: verificato il 26/08/2026.
    #>
    param([int]$Max = 20)
    $m = Get-SysmacMainWindow
    if (-not $m) { return 'SYSMAC_SENZA_FINESTRA' }
    $out = @()
    foreach ($lst in (Find-UiElements -Root $m -Type List)) {
        $items = Find-UiElements -Root $lst -Type ListItem
        if ($items.Count -eq 0) { continue }
        if ($items[0].Current.Name -notmatch 'LogItemViewModel') { continue }
        foreach ($it in $items) {
            $c = Get-UiTexts -Element $it
            if ($c.Count) { $out += ($c -join ' ') }
            if ($out.Count -ge $Max) { break }
        }
        if ($out.Count) { break }
    }
    if ($out.Count -eq 0) { return '(log Uscita vuoto o non trovato)' }
    $out
}

# ============================================================================
#  SCORCIATOIE (finestra "Personalizzazione tasti di scelta rapida")
# ============================================================================

function Get-SysmacShortcutDialog {
    <# Apre (se serve) e restituisce la finestra di personalizzazione scorciatoie. #>
    $d = Get-SysmacDialog 'Personalizzazione tasti di scelta rapida'
    if (-not $d) {
        Invoke-SysmacMenu -Path 'Strumenti', 'Personalizza tasti di scelta rapida...' | Out-Null
        Start-Sleep -Seconds 3
        $d = Get-SysmacDialog 'Personalizzazione tasti di scelta rapida'
    }
    $d
}

function Set-SysmacShortcut {
    <#
      Assegna una scorciatoia alla riga $Index dell'albero comandi.
      $Combo e' in sintassi SendKeys (es. '^%x' = Ctrl+Alt+X).
      Controlla i conflitti prima di assegnare e non forza nulla:
      se "Assegna" resta disabilitato, il comando non e' personalizzabile.
      Le modifiche diventano definitive solo premendo OK sulla finestra.
    #>
    param(
        [Parameter(Mandatory)]$Dialog,
        [Parameter(Mandatory)][int]$Index,
        [Parameter(Mandatory)][string]$Combo,
        [switch]$Apply
    )
    $tree = Find-UiElement -Root $Dialog -Type Tree
    if (-not (Select-UiTreeRow -Tree $tree -Index $Index)) { return $null }

    $ed = Find-UiElement -Root $Dialog -Type Edit
    $ed.SetFocus(); Start-Sleep -Milliseconds 250
    [System.Windows.Forms.SendKeys]::SendWait($Combo); Start-Sleep -Milliseconds 400

    $vp = $null; $ed.TryGetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern, [ref]$vp) | Out-Null
    $campo = if ($vp) { $vp.Current.Value } else { '' }

    $lista = Find-UiElement -Root $Dialog -Type List
    $conflitti = @()
    if ($lista) {
        foreach ($x in (Find-UiElements -Root $lista)) { if ($x.Current.Name) { $conflitti += $x.Current.Name } }
    }
    $btn = Find-UiElement -Root $Dialog -Name 'Assegna' -Type Button

    $res = [PSCustomObject]@{
        Index      = $Index
        Campo      = $campo
        Conflitti  = $conflitti
        Assegnabile= $btn.Current.IsEnabled
        Assegnato  = $false
    }
    if ($Apply -and $btn.Current.IsEnabled -and $conflitti.Count -eq 0) {
        if (Invoke-UiElement -Element $btn) {
            Start-Sleep -Milliseconds 500
            $righe = Get-UiTreeRows -Tree $tree
            $res.Assegnato = ($righe[$Index].Tasto -ne '')
        }
    }
    $res
}

function Export-SysmacShortcuts {
    <# Esporta le scorciatoie personalizzate in un .json (pulsante Esporta). #>
    param([Parameter(Mandatory)]$Dialog, [Parameter(Mandatory)][string]$Path)
    Invoke-UiButton -Root $Dialog -Name 'Esporta' | Out-Null
    Start-Sleep -Seconds 2
    [System.Windows.Forms.SendKeys]::SendWait($Path); Start-Sleep -Milliseconds 500
    [System.Windows.Forms.SendKeys]::SendWait('{ENTER}'); Start-Sleep -Seconds 2
    Test-Path $Path
}

# ============================================================================
#  PROMEMORIA OPERATIVI (dall'esperienza del 26/08/2026)
# ============================================================================
#  * Chiamate PowerShell oltre ~2 minuti vanno in timeout lato MCP:
#    fare operazioni brevi e ripetibili, non lotti lunghi.
#  * Le griglie WPF sono virtualizzate: quello che non e' mai stato scorso
#    NON esiste per UIA. Espandere/scorrere prima di leggere.
#  * Cercare i pulsanti sempre con nome + ControlType Button.
#  * Verificare sempre l'effetto di una scorciatoia: alcune combinazioni
#    (es. Ctrl+Alt+S) non arrivano all'applicazione.
#  * Mappa completa dei tasti: C:\Users\tecni\Claude\sysmac_scorciatoie.md
# ============================================================================


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
    if (-not $it) {
        # Sysmac espone le voci come "[Chiave, Etichetta]" (es.
        # "[Standard, Libreria regolare]"): la ricerca per nome esatto fallisce,
        # si ripiega su una corrispondenza parziale.
        foreach ($radice in @($cb, $script:AE::RootElement)) {
            foreach ($c in @(Find-UiElements -Root $radice -Type ListItem)) {
                if ($c.Current.Name -like ("*" + $Item + "*")) { $it = $c; break }
            }
            if ($it) { break }
        }
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
