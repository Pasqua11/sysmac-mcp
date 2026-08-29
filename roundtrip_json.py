"""roundtrip_json.py - la verifica SEVERA di spec2rung.

Il round-trip sulla spec (roundtrip_catalogo.py) non puo' accorgersi di un
errore nei TIPI dei parametri, perche' json2spec i tipi li butta via. Qui si
confronta invece il JSON RIGENERATO con il JSON ORIGINALE scritto da Sysmac:

    JSON originale --json2spec--> spec --spec2rung--> JSON rigenerato
    normalizza(originale)  ==  normalizza(rigenerato)  ?

Normalizzazione: si tolgono gli identificativi arbitrari (Ix, Id, LRI, RRI e
l'Ix dei collegamenti verticali) e si ordinano celle e collegamenti. Restano
confrontati: tipo di ogni cella, variabile, negazioni/fronti, SET/RESET,
posizione X/Y, nome del blocco, ordine dei pin, **tipo di ogni parametro**,
flag UD/PL, commento del rung e geometria dei collegamenti verticali.
"""

import io
import json
import os
import sys
import time
import collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import json2spec                                   # noqa: E402
import spec2rung                                   # noqa: E402
from estrai_pin_reali import sezioni               # noqa: E402

# Ix/Id/EID sono identificativi arbitrari; H e W sono la
# dimensione a video della casella di ST inline, ricalcolata
# da Sysmac: nessuno dei due e' logica.
IGNORA = {"Ix", "Id", "EID", "H", "W"}


def norm_pin(p):
    return {k: v for k, v in p.items() if k not in IGNORA}


def norm_cella(c):
    out = {}
    for k, v in c.items():
        if k in IGNORA:
            continue
        if k in ("In", "Out"):
            out[k] = [norm_pin(p) for p in v]
        else:
            out[k] = v
    out.setdefault("X", 0)
    out.setdefault("Y", 0)
    return out


def norm_rung(r):
    celle = [norm_cella(c) for c in r.get("CLs", [])
             if isinstance(c, dict) and c.get("__type") != "HL"]
    celle.sort(key=lambda c: (c["Y"], c["X"], c.get("__type", "")))
    vls = sorted(((v.get("X", 0), v.get("Y", 0))
                  for v in (r.get("VLs") or []) if isinstance(v, dict)))
    return {"CLs": celle, "CMT": r.get("CMT", ""), "VLs": vls}


def main():
    t0 = time.time()
    tot = ok = 0
    saltati = collections.Counter()
    diff = []
    for fp in sezioni():
        try:
            testo = io.open(fp, encoding="utf-8-sig", errors="replace").read()
        except OSError:
            continue
        for nriga, riga in enumerate(testo.splitlines()):
            riga = riga.strip()
            if not riga.startswith("{"):
                continue
            try:
                obj = json.loads(riga)
            except ValueError:
                continue
            if not obj.get("CLs"):
                continue
            tot += 1
            try:
                spec = json2spec.rung_to_spec(obj)
            except json2spec.TopologiaNonSupportata:
                saltati["non decodificabile"] += 1
                continue
            try:
                rif = spec2rung.rung_da_spec(spec)
            except spec2rung.NonSupportato:
                saltati["non generabile"] += 1
                continue
            a, b = norm_rung(obj), norm_rung(rif)
            if a == b:
                ok += 1
            else:
                diff.append((fp, nriga, a, b))

    confrontati = ok + len(diff)
    print("RUNG ESAMINATI: %d  (%.1f s)" % (tot, time.time() - t0))
    print("  confrontati a livello JSON ..... %5d" % confrontati)
    print("  IDENTICI all'originale ......... %5d  (%.2f%% dei confrontati)"
          % (ok, 100.0 * ok / max(confrontati, 1)))
    print("  diversi ........................ %5d" % len(diff))
    for m, n in saltati.most_common():
        print("  saltati (%s): %d" % (m, n))
    if diff:
        print("\nPRIMI CASI DIVERSI:")
        for fp, nr, a, b in diff[:4]:
            print("  --- %s riga %d" % (os.path.basename(fp), nr))
            ca = {json.dumps(c, sort_keys=True, ensure_ascii=False) for c in a["CLs"]}
            cb = {json.dumps(c, sort_keys=True, ensure_ascii=False) for c in b["CLs"]}
            for x in list(ca - cb)[:2]:
                print("      solo nell'ORIGINALE : %s" % x[:200])
            for x in list(cb - ca)[:2]:
                print("      solo nel RIGENERATO : %s" % x[:200])
            if a["VLs"] != b["VLs"]:
                print("      VLs orig=%s  rigen=%s" % (a["VLs"], b["VLs"]))
            if a["CMT"] != b["CMT"]:
                print("      CMT diverso")
    return 0 if not diff else 1


if __name__ == "__main__":
    sys.exit(main())
