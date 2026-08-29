# -*- coding: utf-8 -*-
"""Prepara OFFLINE il progetto Movimentazione_6Vasche.

Creare un progetto nuovo dalla GUI si e' rivelato inaffidabile, quindi si parte
da `test_import_ladder` (progetto di scarto nato dagli esperimenti di import) e
lo si trasforma interamente da disco: rinomina del progetto, rinomina delle tre
sezioni, azzeramento delle tabelle variabili, scrittura di variabili e ladder.

Tutto a progetto CHIUSO, con backup .bak_mov di ogni file toccato.
E' IDEMPOTENTE: rilanciarlo non scombina nulla (la prima versione rinominava le
sezioni per posizione e al secondo giro le ha rese tutte uguali).
"""
import io
import os
import re
import shutil
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import slwd                     # noqa: E402
import spec2rung                # noqa: E402
import movimentazione as M      # noqa: E402

ORIGINE = "test_import_ladder"
NUOVO = "Movimentazione_6Vasche"
SEZIONI = ["Movimentazione", "Uscite", "Allarmi"]


def bak(f):
    if not os.path.exists(f + ".bak_mov"):
        shutil.copyfile(f, f + ".bak_mov")


def ripristina(cart):
    n = 0
    for f in os.listdir(cart):
        if f.endswith(".bak_mov"):
            shutil.copyfile(os.path.join(cart, f),
                            os.path.join(cart, f[:-len(".bak_mov")]))
            n += 1
    return n


def cartella():
    nomi = dict(slwd.elenco_progetti())
    for n in (NUOVO, ORIGINE):
        if n in nomi:
            return nomi[n]
    raise LookupError("ne' %s ne' %s trovati" % (NUOVO, ORIGINE))


def _oem(cart):
    f = os.path.join(cart, [x for x in os.listdir(cart) if x.endswith(".oem")][0])
    return f, io.open(f, encoding="utf-8", newline="").read()


def sezioni_del_progetto(cart):
    """[(nome, file)] delle sezioni, nell'ordine in cui compaiono nell'albero."""
    _f, t = _oem(cart)
    out = []
    for m in re.finditer(r'<Entity type="PouBody"[^>]*>', t):
        tag = m.group(0)
        i = re.search(r'id="([0-9a-fA-F-]+)"', tag)
        n = re.search(r'name="([^"]*)"', tag)
        if i and n:
            out.append((n.group(1), os.path.join(cart, i.group(1) + ".xml")))
    return out


def rinomina_progetto(cart, nuovo):
    n = 0
    for f in os.listdir(cart):
        if f.endswith((".manifest", ".manifest2")):
            p = os.path.join(cart, f)
            bak(p)
            t = io.open(p, encoding="utf-8", newline="").read()
            t2 = re.sub(r'solutionName="[^"]*"', 'solutionName="%s"' % nuovo, t)
            if t2 != t:
                io.open(p, "w", encoding="utf-8", newline="").write(t2)
                n += 1
    return n


def rinomina_sezioni(cart, nomi):
    """Rinomina le sezioni per POSIZIONE nell'albero, e solo se serve."""
    attuali = [n for n, _f in sezioni_del_progetto(cart)]
    if attuali == list(nomi):
        return "gia' corrette: %s" % attuali
    f, t = _oem(cart)
    bak(f)
    pezzi, ultimo, k = [], 0, 0
    for m in re.finditer(r'<Entity type="PouBody"[^>]*>', t):
        tag = m.group(0)
        if k < len(nomi):
            tag = re.sub(r'name="[^"]*"', 'name="%s"' % nomi[k], tag, count=1)
            tag = re.sub(r'DN="[^"]*"', 'DN="%s"' % nomi[k], tag, count=1)
        pezzi.append(t[ultimo:m.start()])
        pezzi.append(tag)
        ultimo = m.end()
        k += 1
    pezzi.append(t[ultimo:])
    io.open(f, "w", encoding="utf-8", newline="").write("".join(pezzi))
    return "%s -> %s" % (attuali, nomi)


def azzera_variabili(cart):
    for f in (slwd.file_globali(cart), slwd.file_locali(cart)):
        bak(f)
        testa, gruppi = slwd.leggi(f)
        slwd.scrivi(f, testa, [(i, []) for i, _r in gruppi])


def main():
    t0 = time.time()
    cart = cartella()
    if slwd.aperto_in_sysmac(cart):
        print("ERRORE: progetto aperto in Sysmac, chiuderlo prima.")
        return 1
    print("cartella:", cart)
    if "--ripristina" in sys.argv:
        print("file ripristinati dai backup:", ripristina(cart))
        return 0

    print("rinomina progetto:", rinomina_progetto(cart, NUOVO), "file")
    print("rinomina sezioni :", rinomina_sezioni(cart, SEZIONI))
    azzera_variabili(cart)

    g, e, i = M.variabili()
    r = slwd.crea_variabili(cart, globali=g, interne=i, esterne=e)
    print("variabili: globali %d, interne %d, esterne %d"
          % (len(r["globali"]["aggiunte"]), len(r["interne"]["aggiunte"]),
             len(r["esterne"]["aggiunte"])))

    sez = dict(sezioni_del_progetto(cart))
    gruppi = M.per_sezione()
    tot = 0
    for nome, rungs in gruppi.items():
        f = sez.get(nome)
        if f is None:
            print("   ATTENZIONE: sezione '%s' non trovata (%s)"
                  % (nome, list(sez)))
            return 1
        bak(f)
        spec2rung.scrivi_sezione(f, rungs, in_coda=False, backup=False)
        print("   %-16s %2d rung" % (nome, len(rungs)))
        tot += len(rungs)
    print("TOTALE %d rung. Preparazione offline: %.2f s"
          % (tot, time.time() - t0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
