param([Parameter(Mandatory=$true)][string]$File)
Add-Type -AssemblyName System.Windows.Forms
$t = Get-Content -Path $File -Raw
[System.Windows.Forms.Clipboard]::SetText($t)
Write-Output ("Testo negli appunti: {0} caratteri da {1}. Incollare con Ctrl+V." -f $t.Length, (Split-Path $File -Leaf))
