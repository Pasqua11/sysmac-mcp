# traccia_build.ps1 - osserva (SOLO LETTURA) come Sysmac Studio invoca il compilatore
#
# Durante una compilazione F8 registra:
#   1) ogni processo creato, con la RIGA DI COMANDO completa (nexcc, clang, ld, as...)
#   2) i file temporanei nuovi o modificati nella finestra di osservazione
#      (di solito contengono i sorgenti intermedi e i file di risposta del compilatore)
#
# NON modifica nulla: nessun file di progetto, nessuna impostazione di sistema,
# nessuna scrittura fuori dal proprio log. Serve PowerShell come amministratore
# per vedere la riga di comando dei processi elevati (Sysmac si auto-eleva).
#
# Uso:
#   powershell -NoProfile -ExecutionPolicy Bypass -File C:\Users\tecni\Claude\traccia_build.ps1 -Secondi 90
#   ...poi in Sysmac Studio premere F8 entro la finestra di osservazione.
#
# Log: C:\Users\tecni\Claude\traccia_build.log

param(
    [int]$Secondi = 90,
    [string]$Log = "C:\Users\tecni\Claude\traccia_build.log",
    [int]$IntervalloMs = 30,
    [switch]$SoloRilevanti
)

$ErrorActionPreference = 'Stop'

# processi di contorno, esclusi dal log
$Rumore = 'conhost|SearchProtocolHost|SearchFilterHost|backgroundTaskHost|RuntimeBroker|WmiPrvSE|dllhost|svchost|MoUsoCoreWorker|TrustedInstaller|smartscreen|SecurityHealth|Norton|icarus|NisSrv|MsMpEng|audiodg|ctfmon'

# processi che ci interessano davvero: la catena di compilazione
$Rilevante = 'nexcc|clang|llvm|arm-pc-scpa|^ld|^as\.exe|^ar\.exe|objcopy|objdump|Nex|Sysmac|Build|Ebutil|EbCheck'

function Scrivi($t) {
    $riga = "{0:HH:mm:ss.fff}  {1}" -f (Get-Date), $t
    Add-Content -Path $Log -Value $riga -Encoding UTF8
    Write-Host $riga
}

# --- inizializzazione -------------------------------------------------------
"" | Set-Content -Path $Log -Encoding UTF8
Scrivi "=== TRACCIA BUILD SYSMAC ==="
Scrivi "finestra: $Secondi s   campionamento: $IntervalloMs ms"

$id = [Security.Principal.WindowsIdentity]::GetCurrent()
$admin = (New-Object Security.Principal.WindowsPrincipal $id).IsInRole(
             [Security.Principal.WindowsBuiltInRole]::Administrator)
Scrivi "amministratore: $admin"
if (-not $admin) {
    Scrivi "ATTENZIONE: senza privilegi elevati la riga di comando dei processi di Sysmac non sara' visibile"
}

$sysmac = Get-CimInstance Win32_Process -Filter "Name='SysmacStudio.exe'" -ErrorAction SilentlyContinue
if ($sysmac) { Scrivi "Sysmac Studio PID $($sysmac.ProcessId)" }
else         { Scrivi "ATTENZIONE: Sysmac Studio non risulta in esecuzione" }

$inizio = Get-Date

# istantanea dei file prima della compilazione
$dirOsservate = @("$env:TEMP", 'C:\Omron\Data')
$prima = @{}
foreach ($d in $dirOsservate) {
    if (Test-Path $d) {
        $prima[$d] = @(Get-ChildItem $d -Force -ErrorAction SilentlyContinue |
                       Select-Object -ExpandProperty FullName)
    }
}

# PID gia' esistenti: non vanno segnalati
$noti = @{}
foreach ($p in (Get-CimInstance Win32_Process)) { $noti[$p.ProcessId] = $true }

Scrivi "---------------------------------------------------------------"
Scrivi ">>> ORA premere F8 in Sysmac Studio <<<"
Scrivi "---------------------------------------------------------------"

# --- campionamento dei nuovi processi ---------------------------------------
$conteggio = 0
$rilevanti = 0
$fine = $inizio.AddSeconds($Secondi)

while ((Get-Date) -lt $fine) {
    foreach ($p in (Get-CimInstance Win32_Process -ErrorAction SilentlyContinue)) {
        if ($noti[$p.ProcessId]) { continue }
        $noti[$p.ProcessId] = $true

        if ($p.Name -match $Rumore) { continue }

        $int = $p.Name -match $Rilevante
        if ($SoloRilevanti -and -not $int) { continue }

        $conteggio++
        if ($int) { $rilevanti++ }
        $tag = if ($int) { '>>> ' } else { '    ' }

        Scrivi "$tag$($p.Name)   PID=$($p.ProcessId)  padre=$($p.ParentProcessId)"
        if ($p.CommandLine)      { Scrivi "         CMD: $($p.CommandLine)" }
        if ($p.ExecutablePath)   { Scrivi "         EXE: $($p.ExecutablePath)" }
    }
    Start-Sleep -Milliseconds $IntervalloMs
}

Scrivi "---------------------------------------------------------------"
Scrivi "processi nuovi registrati: $conteggio (della catena di build: $rilevanti)"
if ($rilevanti -eq 0) {
    Scrivi "NESSUN processo di compilazione intercettato."
    Scrivi "Possibili cause: F8 non premuto nella finestra; compilazione incrementale"
    Scrivi "saltata perche' il progetto era gia' compilato (modificare un rung e riprovare);"
    Scrivi "oppure la compilazione avviene in-process, dentro SysmacStudio.exe."
}

# --- file toccati durante la finestra ---------------------------------------
Scrivi ""
Scrivi "=== FILE NUOVI O MODIFICATI DURANTE LA FINESTRA ==="
foreach ($d in $dirOsservate) {
    if (-not (Test-Path $d)) { continue }
    $dopo = Get-ChildItem $d -Force -ErrorAction SilentlyContinue |
            Where-Object { $_.LastWriteTime -ge $inizio }
    if (-not $dopo) { continue }
    Scrivi "--- $d ---"
    foreach ($f in ($dopo | Sort-Object LastWriteTime | Select-Object -First 60)) {
        $stato = if ($prima[$d] -contains $f.FullName) { 'modificato' } else { 'NUOVO     ' }
        $tipo  = if ($f.PSIsContainer) { '[dir] ' } else { '      ' }
        Scrivi "  $stato $tipo $($f.Name)"
    }
}

Scrivi ""
Scrivi "=== FINE - log completo in $Log ==="
