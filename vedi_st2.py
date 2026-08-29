# -*- coding: utf-8 -*-
"""Trova dove sta il CORPO dei POU in Structured Text."""
import glob
import io
import os
import re
import sys

sys.path.insert(0, r"C:\Users\tecni\Claude\sysmac-mcp")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import sysmac_project as sp

nome = sys.argv[1] if len(sys.argv) > 1 else "CFE300_V4"
p = [x for x in sp.list_projects() if nome.lower() in x["nome"].lower()][0]
print("progetto:", p["nome"], "\ncartella:", p["path"])

# un corpo ST contiene assegnazioni ":=" e parole chiave IF/CASE/FOR
segni = re.compile(r"\b(IF|CASE|FOR|WHILE)\b.{0,400}?\bTHEN\b|:=", re.S)
trovati = []
for f in glob.glob(os.path.join(p["path"], "*")):
    if os.path.isdir(f):
        continue
    try:
        t = open(f, encoding="utf-8-sig", errors="ignore").read()
    except OSError:
        continue
    if "[SLWD" in t[:40]:
        continue                       # tabella variabili, gia' nota
    if t.lstrip().startswith("{") or t.lstrip().startswith("<?xml"):
        pass
    n = len(segni.findall(t))
    if n >= 3 and "IF " in t.upper():
        trovati.append((n, os.path.basename(f), os.path.getsize(f), t))

trovati.sort(reverse=True)
print("file con aspetto di codice ST: %d" % len(trovati))
for n, f, dim, _ in trovati[:6]:
    print("  %-40s %6d byte  (%d segni)" % (f, dim, n))

if trovati:
    _, f, _, t = trovati[0]
    print()
    print("=== %s - primi 1000 caratteri ===" % f)
    print(t[:1000])
