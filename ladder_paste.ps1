# ladder_paste.ps1 — mette un rung/i XML (formato Sysmac "ladderSnippetXML") negli appunti.
# Uso: powershell -STA -NoProfile -ExecutionPolicy Bypass -File ladder_paste.ps1 <file.xml>
# Poi in Sysmac: selezionare un rung nell'editor ladder e premere Ctrl+V.
# Le variabili nuove vanno registrate: click sull'elemento -> Ctrl+Alt+R -> Variabile interna/globale. Compilare con F8.
param([Parameter(Mandatory=$true)][string]$XmlFile)
Add-Type -AssemblyName System.Windows.Forms
$xml = Get-Content -Path $XmlFile -Raw
$dobj = New-Object System.Windows.Forms.DataObject
$dobj.SetData("ladderSnippetXML", $xml)
[System.Windows.Forms.Clipboard]::SetDataObject($dobj, $true)
Write-Host "ladderSnippetXML negli appunti ($($xml.Length) caratteri). Incolla in Sysmac con Ctrl+V."
