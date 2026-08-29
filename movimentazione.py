# -*- coding: utf-8 -*-
"""Movimentazione a 6 vasche con carico e scarico, nello stile SYNTECH.

Stile ripreso dai progetti reali (WETBENCH_PDCO_UP_V3 / Vasca1_PdCo1):
  V_P_*  comandi da SCADA        V_L_*  spie verso SCADA      V_S_* selettori
  IN_*   ingressi fisici         OUT_*  uscite fisiche
  Mem_*  memorie di stato con SET/RESET (SET su comando + consensi,
         RESET su annulla/allarme/fine passo)
  Seq_*  sequenza attiva = OR delle memorie
  Tim_*  istanze TON             Allarme_Bit[n] array allarmi
  P_On   in testa ai rami di SET
  le uscite fisiche stanno in fondo, in serie con i consensi

Differenza dichiarata rispetto ai progetti reali: per il tempo di permanenza in
vasca si usa un TON con setpoint TIME invece del blocco funzione `Contatore`,
che e' un FB custom presente solo nei progetti che lo definiscono; in un
progetto nuovo non esiste.
"""

import io
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

N_VASCHE = 6


# ---------------------------------------------------------------- variabili
def variabili():
    g, e, i = [], [], []          # globali, esterne (nomi), interne

    def G(nome, tipo="BOOL", commento="", iniziale=""):
        v = {"nome": nome, "tipo": tipo}
        if commento:
            v["commento"] = commento
        if iniziale:
            v["iniziale"] = iniziale
        g.append(v)
        e.append(nome)

    G("V_S_Auto", commento="selettore AUTOMATICO")
    G("V_P_Start_Ciclo", commento="comando START da SCADA")
    G("V_P_Stop_Ciclo", commento="comando STOP da SCADA")
    G("V_P_Annulla", commento="annulla ciclo da SCADA")
    G("V_L_Ciclo_Attivo", commento="spia ciclo in corso")
    G("V_L_Carro_Carico", commento="spia carro con pezzo")
    G("V_L_Allarme", commento="spia allarme cumulativo")

    G("IN_EMERGENZA", commento="fungo di emergenza (NC)")
    G("IN_PRESS_ARIA", commento="pressostato aria")
    G("IN_PRESENZA_PEZZO", commento="pezzo presente al carico")
    G("IN_POS_CARICO", commento="carro in posizione di carico")
    G("IN_POS_SCARICO", commento="carro in posizione di scarico")
    for n in range(1, N_VASCHE + 1):
        G("IN_POS_V%d" % n, commento="carro sopra la vasca %d" % n)
    G("IN_CARRO_ALTO", commento="carro sollevato")
    G("IN_CARRO_BASSO", commento="carro abbassato")

    G("OUT_CARRO_AVANTI", commento="traslazione avanti")
    G("OUT_CARRO_INDIETRO", commento="traslazione indietro")
    G("OUT_SOLLEVA", commento="sollevamento cestello")
    G("OUT_ABBASSA", commento="abbassamento cestello")

    G("Enable_Ciclo", commento="consenso generale")
    G("Mem_Ciclo", commento="ciclo automatico in corso")
    G("Mem_Pieno", commento="carro con pezzo a bordo")
    G("Mem_Carico", commento="passo: prelievo al carico")
    G("Mem_Scarico", commento="passo: deposito allo scarico")
    G("Seq_Attiva", commento="un passo qualsiasi e' in corso")
    G("Mem_Fine_Ciclo", commento="ciclo completato")
    G("Clock_1Sec", commento="clock 1 s di sistema")
    for n in range(1, N_VASCHE + 1):
        G("Mem_V%d" % n, commento="passo: permanenza in vasca %d" % n)
        G("End_V%d" % n, commento="tempo vasca %d scaduto" % n)
        G("SET_Tempo_V%d" % n, "TIME", "tempo di permanenza vasca %d" % n,
          "T#%ds" % (10 + n))
    G("Allarme_Bit", "ARRAY[1..16] OF BOOL", "allarmi macchina")

    for n in range(1, N_VASCHE + 1):
        i.append({"nome": "Tim_V%d" % n, "tipo": "TON"})
    i.append({"nome": "Tim_All_Aria", "tipo": "TON"})
    i.append({"nome": "Tim_All_Traslazione", "tipo": "TON"})
    return g, e, i


# -------------------------------------------------------------------- rung
def rung():
    r = []

    def R(cmt, chain, out=None):
        v = {"cmt": cmt, "chain": chain}
        if out:
            v["out"] = out
        r.append(v)

    R("CLOCK 1 SECONDO",
      ["P_On", {"f": "Get1sClk", "p": {}}, "(Clock_1Sec)"])
    R("CONSENSO GENERALE",
      ["/IN_EMERGENZA", "IN_PRESS_ARIA", "V_S_Auto", "(Enable_Ciclo)"])
    R("START CICLO",
      ["P_On", "V_P_Start_Ciclo", "Enable_Ciclo", "/Seq_Attiva", "(S Mem_Ciclo)"])
    R("ARRESTO E ANNULLAMENTO CICLO",
      [{"or": ["V_P_Stop_Ciclo", "V_P_Annulla", "IN_EMERGENZA",
               "Allarme_Bit[1]", "Mem_Fine_Ciclo"]}, "(R Mem_Ciclo)"])
    R("SEQUENZA ATTIVA",
      [{"or": ["Mem_Carico", "Mem_Scarico"] +
              ["Mem_V%d" % n for n in range(1, N_VASCHE + 1)]},
       "(Seq_Attiva)"])

    R("AZZERAMENTO PASSI A INIZIO CICLO",
      [{"or": ["V_P_Start_Ciclo", "V_P_Annulla"]}],
      out=["(R End_V%d)" % n for n in range(1, N_VASCHE + 1)])
    R("PRELIEVO AL CARICO",
      ["P_On", "Mem_Ciclo", "IN_POS_CARICO", "IN_PRESENZA_PEZZO",
       "/Mem_Pieno", "(S Mem_Carico)"])
    R("PEZZO PRELEVATO",
      ["Mem_Carico", "IN_CARRO_ALTO", "(S Mem_Pieno)"])
    R("FINE PASSO DI CARICO",
      ["Mem_Pieno", "(R Mem_Carico)"])

    for n in range(1, N_VASCHE + 1):
        consenso = "Mem_Pieno" if n == 1 else "End_V%d" % (n - 1)
        R("INGRESSO VASCA %d" % n,
          ["P_On", "Mem_Ciclo", "Mem_Pieno", "IN_POS_V%d" % n,
           "IN_CARRO_BASSO", consenso, "/End_V%d" % n, "(S Mem_V%d" % n + ")"])
        R("TEMPO DI PERMANENZA VASCA %d" % n,
          ["Mem_V%d" % n,
           {"fb": "TON", "inst": "Tim_V%d" % n,
            "p": {"PT": "SET_Tempo_V%d" % n}},
           "(S End_V%d)" % n])
        R("USCITA VASCA %d" % n,
          ["End_V%d" % n, "(R Mem_V%d)" % n])

    R("DEPOSITO ALLO SCARICO",
      ["P_On", "Mem_Ciclo", "End_V%d" % N_VASCHE, "IN_POS_SCARICO",
       "IN_CARRO_BASSO", "Mem_Pieno", "(S Mem_Scarico)"])
    R("PEZZO DEPOSITATO",
      ["Mem_Scarico", "IN_CARRO_ALTO", "(R Mem_Pieno)"])
    R("FINE PASSO DI SCARICO",
      ["Mem_Scarico", "/Mem_Pieno", "(R Mem_Scarico)"])
    R("CICLO COMPLETATO",
      ["Mem_Ciclo", "End_V%d" % N_VASCHE, "/Mem_Pieno", "/Mem_Scarico",
       "(S Mem_Fine_Ciclo)"])
    R("RIPRISTINO FINE CICLO",
      [{"or": ["V_P_Start_Ciclo", "V_P_Annulla"]}, "(R Mem_Fine_Ciclo)"])

    R("TRASLAZIONE AVANTI",
      ["Enable_Ciclo", "Mem_Ciclo", "Mem_Pieno", "IN_CARRO_ALTO",
       "/IN_POS_SCARICO", "(OUT_CARRO_AVANTI)"])
    R("TRASLAZIONE INDIETRO",
      ["Enable_Ciclo", "Mem_Ciclo", "/Mem_Pieno", "IN_CARRO_ALTO",
       "/IN_POS_CARICO", "(OUT_CARRO_INDIETRO)"])
    R("SOLLEVAMENTO CESTELLO",
      [{"or": ["Mem_Carico", "Mem_Scarico"]}, "Enable_Ciclo",
       "/IN_CARRO_ALTO", "(OUT_SOLLEVA)"])
    R("ABBASSAMENTO CESTELLO",
      [{"or": ["Mem_V%d" % n for n in range(1, N_VASCHE + 1)]},
       "Enable_Ciclo", "/IN_CARRO_BASSO", "(OUT_ABBASSA)"])

    R("SPIA CICLO ATTIVO", ["Mem_Ciclo", "(V_L_Ciclo_Attivo)"])
    R("SPIA CARRO CARICO", ["Mem_Pieno", "(V_L_Carro_Carico)"])
    R("SPIA ALLARME CUMULATIVO",
      [{"or": ["Allarme_Bit[1]", "Allarme_Bit[2]", "Allarme_Bit[3]"]},
       "(V_L_Allarme)"])

    R("ALLARME 1: EMERGENZA PREMUTA", ["IN_EMERGENZA", "(Allarme_Bit[1])"])
    R("ALLARME 2: MANCANZA ARIA COMPRESSA",
      ["Mem_Ciclo", "/IN_PRESS_ARIA",
       {"fb": "TON", "inst": "Tim_All_Aria", "p": {"PT": "T#3s"}},
       "(Allarme_Bit[2])"])
    R("ALLARME 3: TEMPO TRASLAZIONE SUPERATO",
      [{"or": ["OUT_CARRO_AVANTI", "OUT_CARRO_INDIETRO"]},
       {"fb": "TON", "inst": "Tim_All_Traslazione", "p": {"PT": "T#60s"}},
       "(Allarme_Bit[3])"])
    return r


def per_sezione():
    """Il programma diviso nelle sezioni, come nei progetti reali."""
    tutti = rung()
    out = {"Movimentazione": [], "Uscite": [], "Allarmi": []}
    for r in tutti:
        c = r["cmt"]
        if c.startswith(("TRASLAZIONE", "SOLLEVAMENTO", "ABBASSAMENTO")):
            out["Uscite"].append(r)
        elif c.startswith(("SPIA", "ALLARME")):
            out["Allarmi"].append(r)
        else:
            out["Movimentazione"].append(r)
    return out


# ------------------------------------------------------------------- main
def main():
    import spec2rung
    g, e, i = variabili()
    rr = rung()
    print("PROGRAMMA GENERATO")
    print("  variabili globali : %d" % len(g))
    print("  variabili interne : %d" % len(i))
    print("  dichiarazioni esterne: %d" % len(e))
    print("  rung              : %d" % len(rr))

    t = time.time()
    righe, rifiutati = [], []
    for x in rr:
        try:
            righe.append(spec2rung.riga_rung(x))
        except spec2rung.NonSupportato as err:
            rifiutati.append((x["cmt"], str(err)))
    d = time.time() - t
    print("  generazione JSON  : %.0f ms (%d rung, %d rifiutati)"
          % (d * 1000, len(righe), len(rifiutati)))
    for c, err in rifiutati:
        print("     RIFIUTATO %s -> %s" % (c, err[:90]))

    spec = {"variabili": {"globali": g, "interne": i, "esterne": e},
            "sections": {"Movimentazione": rr}}
    with io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "specs", "Movimentazione_6Vasche.json"),
                 "w", encoding="utf-8") as fh:
        json.dump(spec, fh, ensure_ascii=False, indent=1)
    print("  spec salvata in specs\\Movimentazione_6Vasche.json")
    return 0 if not rifiutati else 1


if __name__ == "__main__":
    sys.exit(main())
