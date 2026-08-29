# -*- coding: utf-8 -*-
"""Come sono memorizzati i POU in Structured Text nei progetti Sysmac."""
import io
import os
import re
import sys

sys.path.insert(0, r"C:\Users\tecni\Claude\sysmac-mcp")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import sysmac_project as sp

nome = sys.argv[1] if len(sys.argv) > 1 else "CFE300_V4"
p = [x for x in sp.list_projects() if nome.lower() in x["nome"].lower()][0]
print("progetto:", p["nome"])

oem = os.path.join(p["path"], p["id"] + ".oem")
testo = open(oem, encoding="utf-8-sig", errors="ignore").read()

# entita' con subtype StructuredText: id e nome
trovate = []
for m in re.finditer(r'<Entity[^>]*>', testo):
    e = m.group(0)
    if 'StructuredText' in e:
        i = re.search(r'id="([^"]+)"', e)
        n = re.search(r'name="([^"]*)"', e)
        trovate.append((i.group(1) if i else "?", n.group(1) if n else ""))

print("POU in ST trovati: %d" % len(trovate))
for i, n in trovate[:8]:
    f = os.path.join(p["path"], i + ".xml")
    esiste = os.path.exists(f)
    dim = os.path.getsize(f) if esiste else 0
    print("  %-28s file=%s  %d byte" % (n[:28], "si" if esiste else "NO", dim))

# contenuto del primo
for i, n in trovate:
    f = os.path.join(p["path"], i + ".xml")
    if os.path.exists(f) and os.path.getsize(f) > 200:
        print()
        print("=== contenuto di '%s' (primi 1200 caratteri) ===" % n)
        print(open(f, encoding="utf-8-sig", errors="ignore").read()[:1200])
        break
