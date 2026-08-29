# -*- coding: utf-8 -*-
"""
tempi_progetto.py - tempi di PROVA e tempi REALI in un progetto Sysmac

Il collaudo di una macchina a fasi si fa con tempi accorciati: il semaforo con
i tempi veri ha un ciclo di 55 s, e osservarne due significa aspettare due
minuti di orologio. Con i tempi di prova il ciclo scende a 20 s e il collaudo
va quattro volte piu' veloce; alla fine si rimettono i valori reali.

I tempi sono variabili TIME ritentive: si cambiano nei valori INIZIALI, senza
toccare il ladder. Il progetto deve essere CHIUSO (si scrivono i file).

Uso:
    python tempi_progetto.py <progetto> prova     applica i tempi di collaudo
    python tempi_progetto.py <progetto> reali     rimette i tempi di esercizio
    python tempi_progetto.py <progetto> mostra    stampa quelli impostati
"""
import json, os, sys

sys.path.insert(0, r"C:\Users\tecni\Claude\sysmac-mcp")
import slwd

# I due set. Modificare qui, non nel ladder.
TEMPI = {
    "reali": {
        "SET_T_Verde_NS":   "T#25s",
        "SET_T_Verde_EO":   "T#20s",
        "SET_T_Giallo":     "T#3s",
        "SET_T_TuttoRosso": "T#2s",
        "SET_T_Verde_Min":  "T#8s",
    },
    "prova": {
        "SET_T_Verde_NS":   "T#6s",
        "SET_T_Verde_EO":   "T#5s",
        "SET_T_Giallo":     "T#2s",
        "SET_T_TuttoRosso": "T#1s",
        "SET_T_Verde_Min":  "T#3s",
    },
}


def applica(progetto, quale):
    if quale not in TEMPI:
        raise ValueError("set sconosciuto: %r (ammessi: %s)" % (quale, ", ".join(TEMPI)))
    cart = slwd.trova_progetto(progetto)
    if slwd.aperto_in_sysmac(cart):
        raise RuntimeError("il progetto e' APERTO in Sysmac: chiuderlo prima "
                           "(altrimenti il salvataggio sovrascrive le modifiche)")
    f = slwd.file_globali(cart)
    vals = [{"nome": n, "tipo": "TIME", "iniziale": v, "ritentivo": True,
             "commento": "tempo di fase (%s)" % quale}
            for n, v in TEMPI[quale].items()]
    a, _s = slwd.aggiungi(f, "globali", vals, sostituisci=True)
    return a


def mostra(progetto):
    cart = slwd.trova_progetto(progetto)
    f = slwd.file_globali(cart)
    _t, gruppi = slwd.leggi(f)
    for _intest, righe in gruppi:
        for r in righe:
            if "N=SET_T_" in r:
                nome = r.split("N=")[1].split("\t")[0]
                iv = r.split("IV=")[1].split("\t")[0] if "IV=" in r else "(vuoto)"
                print("  %-20s %s" % (nome, iv))


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    prog, cmd = sys.argv[1], sys.argv[2].lower()
    if cmd == "mostra":
        mostra(prog)
    else:
        n = applica(prog, cmd)
        print("tempi '%s' applicati a %s: %s" % (cmd, prog, ", ".join(n)))
