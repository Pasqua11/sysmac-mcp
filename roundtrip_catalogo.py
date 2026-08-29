"""roundtrip_catalogo.py - misura quanto di TUTTO il ladder gia' scritto in
azienda e' riproducibile offline da spec2rung.

Per ogni rung di ogni progetto in C:\\OMRON\\Data\\Solution:
    JSON su disco --json2spec--> spec --spec2rung--> JSON --json2spec--> spec
Le due spec devono coincidere. Se non coincidono e' un BUG del generatore, ed
e' esattamente quello che va scoperto qui e non in un quadro in produzione.
"""

import collections
import io
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import json2spec                                   # noqa: E402
import spec2rung                                   # noqa: E402

RADICE = r"C:\OMRON\Data\Solution"


def file_di_sezione(radice=RADICE, max_mb=6):
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
    t0 = time.time()
    tot = ok = 0
    non_decod = collections.Counter()
    non_gener = collections.Counter()
    diversi = []
    for fp in file_di_sezione():
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
            except json2spec.TopologiaNonSupportata as e:
                non_decod[str(e).split(":")[0][:60]] += 1
                continue
            try:
                rifatto = spec2rung.rung_da_spec(spec)
            except spec2rung.NonSupportato as e:
                non_gener[str(e).split(":")[0][:60]] += 1
                continue
            try:
                spec2 = json2spec.rung_to_spec(rifatto)
            except json2spec.TopologiaNonSupportata as e:
                diversi.append((fp, nriga, "rigenerato non rileggibile: %s" % e))
                continue
            if spec2 == spec:
                ok += 1
            else:
                diversi.append((fp, nriga, "atteso %s\n        ottenuto %s"
                                % (json.dumps(spec, ensure_ascii=False)[:220],
                                   json.dumps(spec2, ensure_ascii=False)[:220])))

    print("RUNG ESAMINATI: %d   (in %.1f s)" % (tot, time.time() - t0))
    print("  round-trip ESATTO ......... %5d  (%.1f%% del totale)"
          % (ok, 100.0 * ok / max(tot, 1)))
    nd = sum(non_decod.values())
    ng = sum(non_gener.values())
    print("  non decodificabili a monte  %5d  (%.1f%%) - limite di json2spec"
          % (nd, 100.0 * nd / max(tot, 1)))
    print("  non generabili .............%5d  (%.1f%%) - limite dichiarato"
          % (ng, 100.0 * ng / max(tot, 1)))
    print("  DIVERGENTI (bug) ...........%5d" % len(diversi))
    generabili = ok + len(diversi)
    if generabili:
        print("\nAFFIDABILITA' su cio' che il generatore accetta: %.2f%%"
              % (100.0 * ok / generabili))
    print("\nmotivi 'non generabile':")
    for m, n in non_gener.most_common(8):
        print("   %5d  %s" % (n, m))
    print("\nmotivi 'non decodificabile':")
    for m, n in non_decod.most_common(6):
        print("   %5d  %s" % (n, m))
    if diversi:
        print("\nPRIMI CASI DIVERGENTI:")
        for fp, nr, msg in diversi[:5]:
            print("  %s riga %d\n        %s" % (os.path.basename(fp), nr, msg))
    return 0 if not diversi else 1


if __name__ == "__main__":
    sys.exit(main())
