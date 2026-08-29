# -*- coding: utf-8 -*-
"""Round-trip: prova a RIGENERARE con ladder_gen ogni rung convertito da rung2spec.
Misura quanti rung tornano indietro e quali tipi FB/F mancano nei template."""
import json, os, re, sys, collections

sys.path.insert(0, r"C:\Users\tecni\Claude\sysmac-mcp")
from ladder_gen import LadderGen

SPECS = r"C:\Users\tecni\Claude\sysmac-mcp\specs"
TEMPLATES = r"C:\Users\tecni\Claude\sysmac-mcp\templates"

gen = LadderGen(TEMPLATES)
ok = ko = 0
missing = collections.Counter()
errors = collections.Counter()
per_proj = []

for fn in sorted(os.listdir(SPECS)):
    if not fn.endswith(".json"):
        continue
    data = json.load(open(os.path.join(SPECS, fn), encoding="utf-8"))
    p_ok = p_ko = 0
    for sec, rungs in data.get("sections", {}).items():
        for r in rungs:
            if "_NON_CONVERTITO" in r:
                p_ko += 1
                errors["non convertito da rung2spec"] += 1
                continue
            try:
                gen.rung(r)
                p_ok += 1
            except ValueError as e:
                p_ko += 1
                m = re.match(r"Tipo '([^']+)' sconosciuto", str(e))
                if m:
                    missing[m.group(1)] += 1
                    errors["tipo mancante nei template"] += 1
                else:
                    errors[str(e)[:70]] += 1
            except Exception as e:
                p_ko += 1
                errors["%s: %s" % (type(e).__name__, str(e)[:50])] += 1
    ok += p_ok
    ko += p_ko
    per_proj.append((p_ok, p_ko, data.get("progetto", fn)))

print("RIGENERATI: %d   FALLITI: %d   (%.1f%%)" % (ok, ko, 100.0 * ok / max(1, ok + ko)))
print("\nPROGETTI CON FALLIMENTI:")
for (a, b, n) in sorted(per_proj, key=lambda t: -t[1])[:15]:
    if b:
        print("  ok=%-5d ko=%-5d  %s" % (a, b, n))
print("\nCAUSE:")
for k, v in errors.most_common(15):
    print("  %6d  %s" % (v, k))
print("\nTIPI FB/F MANCANTI NEI TEMPLATE (i piu' usati):")
for k, v in missing.most_common(40):
    print("  %6d  %s" % (v, k))
