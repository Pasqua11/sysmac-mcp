"""estrai_pin_reali.py - ricava dai rung REALI la firma esatta di ogni blocco
funzione e funzione: ordine dei pin, quale e' il pin di power flow, quali sono
in-out, e soprattutto la stringa `Type` che Sysmac scrive davvero.

Serve a spec2rung: senza il `Type` giusto un rung con FB sembra corretto ma non
lo e'. La documentazione (pins.json) dichiara tipi generici tipo
"ANY_ELEMENTARY, ENUM": qui si guarda cosa c'e' scritto nei file veri.

Uscita: pin_reali.json = {nome: {"kind": "FB"|"F",
                                "in":  [{"arg","tipo","pf","io"}...],
                                "out": [...], "usi": n, "ambigui": [...]}}
"""

import collections
import io
import json
import os
import sys

RADICE = r"C:\OMRON\Data\Solution"


def sezioni(radice=RADICE, max_mb=6):
    for d in sorted(os.listdir(radice)):
        p = os.path.join(radice, d)
        if not os.path.isdir(p):
            continue
        for f in os.listdir(p):
            if not f.endswith(".xml"):
                continue
            fp = os.path.join(p, f)
            try:
                if os.path.getsize(fp) > max_mb * 1024 * 1024:
                    continue
                with io.open(fp, encoding="utf-8-sig", errors="replace") as fh:
                    testa = fh.read(400)
                if not testa.lstrip().startswith("{") or '"CLs"' not in testa:
                    continue
            except OSError:
                continue
            yield fp


def main():
    # nome -> lato -> posizione -> Counter di (arg, tipo, pf, io)
    firme = collections.defaultdict(
        lambda: {"kind": None, "in": collections.defaultdict(collections.Counter),
                 "out": collections.defaultdict(collections.Counter), "usi": 0})
    for fp in sezioni():
        try:
            testo = io.open(fp, encoding="utf-8-sig", errors="replace").read()
        except OSError:
            continue
        for riga in testo.splitlines():
            riga = riga.strip()
            if not riga.startswith("{"):
                continue
            try:
                obj = json.loads(riga)
            except ValueError:
                continue
            for c in obj.get("CLs", []):
                if not isinstance(c, dict) or c.get("__type") not in ("FB", "F"):
                    continue
                nome = c.get("Name", "")
                if not nome:
                    continue
                f = firme[nome]
                f["kind"] = c["__type"]
                f["usi"] += 1
                f.setdefault("flag", collections.Counter())
                for k in ("UD", "PL"):
                    if c.get(k):
                        f["flag"][k] += 1
                for lato in ("In", "Out"):
                    for i, p in enumerate(c.get(lato) or []):
                        chiave = (p.get("Arg", ""),
                                  p.get("Type", "") if p.get("__type") == "PRM" else "",
                                  p.get("__type") == "PF",
                                  bool(p.get("IO")))
                        f[lato.lower()][i][chiave] += 1

    out = {}
    ambigui_tot = 0
    for nome, f in firme.items():
        flag = f.get("flag", {})
        voce = {"kind": f["kind"], "usi": f["usi"], "in": [], "out": [],
                "ambigui": [],
                # flag di cella tenuti solo se presenti in TUTTI gli usi:
                # se sono a meta' non sappiamo la regola e non li generiamo
                "UD": flag.get("UD", 0) == f["usi"],
                "PL": flag.get("PL", 0) == f["usi"],
                "flag_incerti": [k for k in ("UD", "PL")
                                 if 0 < flag.get(k, 0) < f["usi"]]}
        for lato in ("in", "out"):
            for i in sorted(f[lato]):
                cnt = f[lato][i]
                (arg, tipo, pf, io_), n = cnt.most_common(1)[0]
                if len(cnt) > 1:
                    voce["ambigui"].append(
                        {"lato": lato, "pos": i,
                         "varianti": [{"arg": a, "tipo": t, "pf": p, "io": o,
                                       "n": k} for (a, t, p, o), k in cnt.most_common()]})
                    ambigui_tot += 1
                voce[lato].append({"arg": arg, "tipo": tipo, "pf": pf, "io": io_})
        out[nome] = voce

    with io.open("pin_reali.json", "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1, sort_keys=True)

    print("blocchi/funzioni trovati: %d" % len(out))
    print("posizioni di pin ambigue (piu' firme per lo stesso blocco): %d"
          % ambigui_tot)
    print("\ni piu' usati:")
    for nome, v in sorted(out.items(), key=lambda kv: -kv[1]["usi"])[:12]:
        segn = "!" if v["ambigui"] else " "
        print("  %s %-22s %-3s usi=%-5d in=%s  out=%s" % (
            segn, nome, v["kind"], v["usi"],
            [(p["arg"], p["tipo"] or "PF") for p in v["in"]],
            [(p["arg"], p["tipo"] or "PF") for p in v["out"]]))
    amb = [(n, v) for n, v in out.items() if v["ambigui"]]
    if amb:
        print("\nBLOCCHI CON FIRME MULTIPLE (da NON generare automaticamente):")
        for n, v in sorted(amb, key=lambda kv: -kv[1]["usi"])[:10]:
            print("   %-22s usi=%-5d posizioni ambigue=%d"
                  % (n, v["usi"], len(v["ambigui"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
