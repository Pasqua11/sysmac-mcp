import html, io, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
codice = open(r"C:\Users\tecni\Claude\sysmac-mcp\st_essiccatore.st", encoding="utf-8").read()
xml = ('<StructuredTextModel xmlns="http://schemas.datacontract.org/2004/07/'
       'Omron.Cxap.Modules.StructuredText.Core" '
       'xmlns:i="http://www.w3.org/2001/XMLSchema-instance"><Text>'
       + html.escape(codice).replace("\n", "&#xD;\n")
       + '</Text></StructuredTextModel>')
p = r"C:\Users\tecni\Claude\sysmac-mcp\st_essiccatore_import.xml"
open(p, "w", encoding="utf-8").write(xml)
print("scritto", p, os.path.getsize(p), "byte")
