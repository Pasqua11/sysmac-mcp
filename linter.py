# -*- coding: utf-8 -*-
"""
linter.py - controlli automatici sul ladder, senza aprire Sysmac.

Cerca i difetti che la compilazione NON segnala e che si pagano in cantiere:

  DOPPIA BOBINA   la stessa uscita comandata da piu' rung con OUT: comanda
                  l'ultimo eseguito, gli altri sono codice morto che sembra
                  funzionante. E' il difetto che ha azzerato i comandi del
                  robot nel wetbench del 28/08.
  MAI RESETTATA   variabile messa a 1 con SET e mai riportata a 0: un allarme
                  che non si puo' azzerare, o una memoria che resta appesa.
  MAI LETTA       uscita o memoria scritta e mai usata da nessuna parte:
                  di solito e' un residuo, a volte e' un comando dimenticato.
  MAI SCRITTA     contatto su una variabile che nessuno comanda: quasi sempre
                  un nome sbagliato, e il PLC non se ne accorge.

Uso:
    python linter.py                 tutti i progetti della libreria
    python linter.py NomeProgetto    un progetto solo
"""
import io
import re
import sys

sys.path.insert(0, r"C:\Users\tecni\Claude\sysmac-mcp")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import sysmac_project as sp

# nel testo decodificato: "OUT nome", "SET nome", "RESET nome"
RE_OUT = re.compile(r"\bOUT\s+([A-Za-z_][A-Za-z0-9_.\[\]]*)")
RE_SET = re.compile(r"\bSET\s+([A-Za-z_][A-Za-z0-9_.\[\]]*)")
RE_RST = re.compile(r"\bRESET\s+([A-Za-z_][A-Za-z0-9_.\[\]]*)")
RE_LD = re.compile(r"\bLDN?\s+([A-Za-z_][A-Za-z0-9_.\[\]]*)")
RE_ASSEGNA = re.compile(r"([A-Za-z_][A-Za-z0-9_.\[\]]*)\s*:=")


def analizza(proj):
    """Restituisce i quattro elenchi di segnalazioni per un progetto."""
    out_rung = {}      # nome -> [(sezione, rung), ...]  bobine OUT
    set_rung = {}
    rst_rung = {}
    letti = set()
    scritti = set()

    for s in sp.sections(proj):
        if not s["rung"]:
            continue
        try:
            testo = sp.read_section(proj, s["nome"])
        except Exception:
            continue
        rung = -1
        for riga in testo.splitlines():
            m = re.match(r"R(\d+)\b", riga.strip())
            if m:
                rung = int(m.group(1))
                continue
            for n in RE_OUT.findall(riga):
                out_rung.setdefault(n, []).append((s["nome"], rung))
                scritti.add(n)
            for n in RE_SET.findall(riga):
                set_rung.setdefault(n, []).append((s["nome"], rung))
                scritti.add(n)
            for n in RE_RST.findall(riga):
                rst_rung.setdefault(n, []).append((s["nome"], rung))
                scritti.add(n)
            for n in RE_ASSEGNA.findall(riga):
                scritti.add(n)
            for n in RE_LD.findall(riga):
                letti.add(n)

    # Conta solo le bobine su rung DIVERSI: due bobine nello stesso rung sono
    # quasi sempre rami paralleli, cioe' codice legittimo. Il difetto vero e'
    # la stessa uscita comandata in punti diversi del programma, dove a
    # decidere e' soltanto l'ordine di esecuzione.
    doppie = {}
    for n, v in out_rung.items():
        distinti = sorted(set(v))
        if len(distinti) > 1:
            doppie[n] = distinti
    senza_reset = sorted(n for n in set_rung if n not in rst_rung)
    # una variabile con il punto e' un campo di blocco (Tim.Q): non conta
    mai_letti = sorted(n for n in scritti
                       if n not in letti and "." not in n and not n.startswith("P_"))
    mai_scritti = sorted(n for n in letti
                         if n not in scritti and "." not in n
                         and not n.startswith(("P_", "IN_", "_")))
    return doppie, senza_reset, mai_letti, mai_scritti


def stampa(proj, dettaglio=True):
    doppie, senza_reset, mai_letti, mai_scritti = analizza(proj)
    tot = len(doppie) + len(senza_reset)
    print("%-38s doppie bobine %3d | SET senza reset %3d | mai lette %3d | "
          "mai scritte %3d" % (proj["nome"][:38], len(doppie), len(senza_reset),
                               len(mai_letti), len(mai_scritti)))
    if dettaglio and doppie:
        for n, dove in sorted(doppie.items(), key=lambda x: -len(x[1]))[:12]:
            posti = ", ".join("%s/R%d" % d for d in dove[:5])
            print("    %-28s comandata in %d punti: %s"
                  % (n, len(dove), posti + (" ..." if len(dove) > 5 else "")))
    return tot


def main():
    if len(sys.argv) > 1:
        prog = [p for p in sp.list_projects() if sys.argv[1].lower() in p["nome"].lower()]
        for p in prog:
            stampa(p)
        return

    print("=== controllo automatico su tutta la libreria ===")
    print()
    righe = []
    for p in sp.list_projects():
        try:
            d, sr, ml, ms = analizza(p)
        except Exception:
            continue
        if d or sr:
            righe.append((len(d), len(sr), p["nome"]))
    righe.sort(reverse=True)
    print("%-40s %8s %8s" % ("progetto", "doppie", "no-reset"))
    for d, sr, nome in righe[:25]:
        print("%-40s %8d %8d" % (nome[:40], d, sr))
    print()
    print("progetti con almeno una doppia bobina: %d su %d"
          % (len([r for r in righe if r[0]]), len(sp.list_projects())))
    print("doppie bobine totali: %d" % sum(r[0] for r in righe))


if __name__ == "__main__":
    main()
