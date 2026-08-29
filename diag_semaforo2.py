# -*- coding: utf-8 -*-
import io
import json
import sys

sys.path.insert(0, r"C:\Users\tecni\Claude\sysmac-mcp")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

spec = json.load(open(r"C:\Users\tecni\Claude\sysmac-mcp\semaforo_spec.json",
                      encoding="utf-8-sig"))

print("=== rung con una bobina NON in ultima posizione ===")
for nome, rung in spec["sections"].items():
    for i, r in enumerate(rung):
        ch = r.get("chain") or []
        for j, el in enumerate(ch):
            if isinstance(el, str) and el.strip().startswith("(") and j != len(ch) - 1:
                print("  %s rung %d: %s" % (nome, i, json.dumps(ch, ensure_ascii=False)[:160]))
                break

print()
print("=== rung che scrivono Mem_F4 o Mem_Ped_NS ===")
for nome, rung in spec["sections"].items():
    for i, r in enumerate(rung):
        t = json.dumps(r, ensure_ascii=False)
        if ("Mem_F4)" in t or "Mem_Ped_NS)" in t):
            print("  %s rung %2d | %s" % (nome, i, r.get("cmt", "")[:52]))
            print("      %s" % json.dumps(r, ensure_ascii=False)[:300])
