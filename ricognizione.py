# -*- coding: utf-8 -*-
"""
ricognizione.py - che cosa usano davvero i progetti SYNTECH dentro Sysmac.

Serve a decidere su quali funzionalita' di Sysmac Studio vale la pena
lavorare: non quelle che il manuale considera importanti, ma quelle che
compaiono nei progetti veri.
"""
import io
import os
import re
import sys
from collections import Counter

sys.path.insert(0, r"C:\Users\tecni\Claude\sysmac-mcp")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import sysmac_project as sp

conta = Counter()
tipi_pou = Counter()
progetti = sp.list_projects()

for p in progetti:
    oem = os.path.join(p["path"], p["id"] + ".oem")
    try:
        with open(oem, encoding="utf-8-sig", errors="ignore") as f:
            testo = f.read()
    except OSError:
        continue

    def ha(pat):
        return re.search(pat, testo, re.I) is not None

    if ha(r'subtype="StructuredText"'):
        conta["POU in Structured Text"] += 1
    if ha(r'type="PouFunctionBlock"|"FunctionBlock"'):
        conta["blocchi funzione propri"] += 1
    if ha(r'type="PouFunction"'):
        conta["funzioni proprie"] += 1
    if ha(r'DataTypeStructure|"Structure"'):
        conta["strutture dati proprie"] += 1
    if ha(r'DataTypeEnum|"Enumeration"'):
        conta["enumerazioni"] += 1
    if ha(r'EtherCAT'):
        conta["configurazione EtherCAT"] += 1
    if ha(r'EtherNet/IP|EtherNetIP'):
        conta["EtherNet/IP"] += 1
    if ha(r'MotionAxis|"Axis"|AxesGroup'):
        conta["assi di movimento"] += 1
    if ha(r'CamProfile|CamTable'):
        conta["profili camma"] += 1
    if ha(r'DataTrace|"Trace"'):
        conta["Data Trace"] += 1
    if ha(r'"Task"'):
        conta["task configurati"] += 1
    if ha(r'UserAlarm|UserEvent|EventSetting'):
        conta["eventi/allarmi utente"] += 1
    if ha(r'"Unit"|"IOMap"|IoMap'):
        conta["mappa I/O"] += 1
    if ha(r'"NA5|"NA_|HmiApplication'):
        conta["progetto HMI (NA)"] += 1
    if ha(r'Safety|"NX-SL'):
        conta["sicurezza NX-SL"] += 1

    for m in re.finditer(r'subtype="([A-Za-z]+)"', testo):
        tipi_pou[m.group(1)] += 1

print("progetti esaminati: %d" % len(progetti))
print()
print("=== funzionalita' presenti, per numero di progetti ===")
for k, v in conta.most_common():
    print("  %-28s %3d  (%d%%)" % (k, v, round(100.0 * v / len(progetti))))
print()
print("=== sottotipi di POU trovati ===")
for k, v in tipi_pou.most_common(12):
    print("  %-24s %d" % (k, v))
