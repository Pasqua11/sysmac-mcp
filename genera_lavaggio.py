# -*- coding: utf-8 -*-
"""
genera_lavaggio.py - linea di lavaggio a N vasche, PARAMETRICA
28/08/2026

Impianto tipo wetbench SYNTECH: un carro traslante porta il cestello dal carico
alle vasche in sequenza e infine allo scarico. Ogni vasca ha permanenza,
riscaldamento con termostato, sorveglianza livello e allarmi.

Serve a misurare come scalano generazione, collaudo e import al crescere del
programma: si sceglie il numero di vasche e i rung crescono di conseguenza.

    python genera_lavaggio.py 4      ->  ~45 rung
    python genera_lavaggio.py 10     ->  ~85 rung
    python genera_lavaggio.py 20     -> ~150 rung

Rung per vasca (6): ingresso, permanenza, uscita, riscaldamento, allarme
livello, allarme temperatura. Piu' una ventina di rung di contorno.
"""
import json, os, sys

D = r"C:\Users\tecni\Claude\sysmac-mcp"


def costruisci(n_vasche):
    G, I, R = [], [], []

    # ---------------------------------------------------------- variabili fisse
    G += [
        ("IN_Emergenza", "BOOL", "fungo di emergenza"),
        ("IN_Protezioni", "BOOL", "protezioni chiuse"),
        ("IN_Press_Aria", "BOOL", "pressostato aria"),
        ("IN_Pos_Carico", "BOOL", "carro in posizione di carico"),
        ("IN_Pos_Scarico", "BOOL", "carro in posizione di scarico"),
        ("IN_Carro_Alto", "BOOL", "cestello sollevato"),
        ("IN_Carro_Basso", "BOOL", "cestello abbassato"),
        ("IN_Presenza_Cesto", "BOOL", "cestello presente al carico"),
        ("V_S_Auto", "BOOL", "selettore automatico"),
        ("V_P_Start", "BOOL", "start ciclo"),
        ("V_P_Stop", "BOOL", "stop ciclo"),
        ("V_P_Reset", "BOOL", "reset allarmi"),
        ("OUT_Carro_Avanti", "BOOL", "traslazione avanti"),
        ("OUT_Carro_Indietro", "BOOL", "traslazione indietro"),
        ("OUT_Solleva", "BOOL", "sollevamento cestello"),
        ("OUT_Abbassa", "BOOL", "abbassamento cestello"),
        ("V_L_Ciclo", "BOOL", "spia ciclo"),
        ("V_L_Allarme", "BOOL", "spia allarme cumulativo"),
        ("V_L_Fine_Ciclo", "BOOL", "spia ciclo completato"),
        ("V_S_Cicli_Fatti", "INT", "cicli completati"),
        ("SET_T_Traslazione", "TIME", "tempo massimo di traslazione"),
    ]
    I += [
        ("Consensi", "BOOL", "consensi di sicurezza"),
        ("Mem_Ciclo", "BOOL", "ciclo in corso"),
        ("Mem_Carico", "BOOL", "passo: prelievo al carico"),
        ("Mem_Scarico", "BOOL", "passo: deposito allo scarico"),
        ("Mem_Pieno", "BOOL", "carro con cestello"),
        ("Mem_Fine", "BOOL", "ciclo completato"),
        ("Mem_Target", "BOOL", "carro fermo sopra la vasca da fare"),
        ("Mem_Estrai", "BOOL", "cestello da sollevare fuori dalla vasca"),
        ("Seq_Attiva", "BOOL", "un passo qualsiasi in corso"),
        ("Tim_Traslazione", "TON", "sorveglianza traslazione"),
    ]

    # ---------------------------------------------------------- per ogni vasca
    for k in range(1, n_vasche + 1):
        G += [
            ("IN_Pos_V%d" % k, "BOOL", "carro sopra la vasca %d" % k),
            ("IN_Livello_V%d" % k, "BOOL", "livello vasca %d ok" % k),
            ("IN_Temp_V%d" % k, "BOOL", "termostato vasca %d in temperatura" % k),
            ("OUT_Risc_V%d" % k, "BOOL", "riscaldamento vasca %d" % k),
            ("SET_T_V%d" % k, "TIME", "permanenza in vasca %d" % k),
            ("V_S_Usa_V%d" % k, "BOOL", "vasca %d inclusa nella ricetta" % k),
            ("V_S_All_Liv_V%d" % k, "BOOL", "allarme livello vasca %d" % k),
            ("V_S_All_Temp_V%d" % k, "BOOL", "allarme temperatura vasca %d" % k),
        ]
        I += [
            ("Mem_V%d" % k, "BOOL", "passo: permanenza in vasca %d" % k),
            ("End_V%d" % k, "BOOL", "vasca %d completata" % k),
            ("Tim_V%d" % k, "TON", "permanenza vasca %d" % k),
            ("Tim_Temp_V%d" % k, "TON", "ritardo allarme temperatura vasca %d" % k),
        ]

    # ---------------------------------------------------------------- contorno
    R += [
        {"cmt": "CONSENSI DI SICUREZZA",
         "chain": ["/IN_Emergenza", "IN_Protezioni", "IN_Press_Aria", "(Consensi)"]},
        # Mem_Fine va azzerato QUI, non piu' in basso: il rung di arresto che
        # segue lo legge nello stesso scan e senza questo il ciclo successivo
        # veniva fermato subito dopo essere partito.
        {"cmt": "START CICLO (azzera anche il fine ciclo precedente)",
         "chain": ["^V_P_Start", "Consensi", "V_S_Auto", "IN_Presenza_Cesto",
                   "/Seq_Attiva"],
         "out": [["(R Mem_Fine)"], ["(S Mem_Ciclo)"]]},
        {"cmt": "ARRESTO CICLO",
         "chain": [{"or": ["^V_P_Stop", "/Consensi", "Mem_Fine"]}, "(R Mem_Ciclo)"]},
    ]

    passi = ["Mem_Carico"] + ["Mem_V%d" % k for k in range(1, n_vasche + 1)] + ["Mem_Scarico"]
    R.append({"cmt": "SEQUENZA ATTIVA: un passo qualsiasi in corso",
              "chain": [{"or": passi}, "(Seq_Attiva)"]})

    R.append({"cmt": "CARRO SOPRA LA VASCA DA FARE: qui si ferma e cala il cestello",
              "chain": ["Mem_Ciclo", "Mem_Pieno",
                        {"or": [["V_S_Usa_V%d" % k, "/End_V%d" % k, "IN_Pos_V%d" % k]
                                for k in range(1, n_vasche + 1)]},
                        "(Mem_Target)"]})

    R.append({"cmt": "AZZERAMENTO PASSI A INIZIO CICLO",
              "chain": ["^V_P_Start"],
              "out": [["(R End_V%d)" % k] for k in range(1, n_vasche + 1)]})

    # --- prelievo al carico
    R += [
        {"cmt": "PRELIEVO AL CARICO",
         "chain": ["Mem_Ciclo", "IN_Pos_Carico", "IN_Presenza_Cesto", "/Mem_Pieno",
                   "(S Mem_Carico)"]},
        {"cmt": "CESTELLO PRELEVATO",
         "chain": ["Mem_Carico", "IN_Carro_Alto"],
         "out": [["(S Mem_Pieno)"], ["(R Mem_Carico)"]]},
    ]

    # --- una tripletta di rung per ogni vasca
    for k in range(1, n_vasche + 1):
        prec = "Mem_Pieno" if k == 1 else "End_V%d" % (k - 1)
        R += [
            {"cmt": "INGRESSO VASCA %d" % k,
             "chain": ["Mem_Ciclo", "Mem_Pieno", "V_S_Usa_V%d" % k,
                       "IN_Pos_V%d" % k, "IN_Carro_Basso", prec,
                       "/End_V%d" % k, "(S Mem_V%d)" % k]},
            {"cmt": "PERMANENZA IN VASCA %d" % k,
             "chain": ["Mem_V%d" % k,
                       {"fb": "TON", "inst": "Tim_V%d" % k, "p": {"PT": "SET_T_V%d" % k}}]},
            {"cmt": "USCITA DALLA VASCA %d" % k,
             "chain": [{"or": ["Tim_V%d.Q" % k, "/V_S_Usa_V%d" % k]},
                       {"or": ["Mem_V%d" % k, ["Mem_Ciclo", "/V_S_Usa_V%d" % k, prec]]}],
             "out": [["(S End_V%d)" % k], ["(R Mem_V%d)" % k], ["(S Mem_Estrai)"]]},
            {"cmt": "RISCALDAMENTO VASCA %d (solo se in ricetta e livello ok)" % k,
             "chain": ["V_S_Usa_V%d" % k, "IN_Livello_V%d" % k, "/IN_Temp_V%d" % k,
                       "Consensi", "(OUT_Risc_V%d)" % k]},
            {"cmt": "ALLARME LIVELLO VASCA %d" % k,
             "chain": ["V_S_Usa_V%d" % k, "/IN_Livello_V%d" % k, "Mem_Ciclo",
                       "(S V_S_All_Liv_V%d)" % k]},
            {"cmt": "ALLARME TEMPERATURA VASCA %d (fuori range da troppo tempo)" % k,
             "chain": ["V_S_Usa_V%d" % k, "/IN_Temp_V%d" % k, "Mem_V%d" % k,
                       {"fb": "TON", "inst": "Tim_Temp_V%d" % k, "p": {"PT": "T#120s"}}],
             "out": [["(S V_S_All_Temp_V%d)" % k]]},
        ]

    ultima = "End_V%d" % n_vasche
    R += [
        {"cmt": "DEPOSITO ALLO SCARICO",
         "chain": ["Mem_Ciclo", ultima, "IN_Pos_Scarico", "IN_Carro_Basso",
                   "Mem_Pieno", "(S Mem_Scarico)"]},
        {"cmt": "CESTELLO DEPOSITATO",
         "chain": ["Mem_Scarico", "IN_Carro_Alto"],
         "out": [["(R Mem_Pieno)"], ["(R Mem_Scarico)"], ["(S Mem_Fine)"],
                 [{"f": "@Inc", "p": {"InOut": "V_S_Cicli_Fatti",
                                       "OUT:InOut": "V_S_Cicli_Fatti"}}]]},
        {"cmt": "TRASLAZIONE AVANTI: verso la vasca successiva o lo scarico",
         "chain": ["Mem_Ciclo", "Mem_Pieno", "IN_Carro_Alto", "/Mem_Target",
                   "/IN_Pos_Scarico", "Consensi", "(OUT_Carro_Avanti)"]},
        {"cmt": "TRASLAZIONE INDIETRO: rientro a vuoto al carico",
         "chain": ["Mem_Ciclo", "/Mem_Pieno", "IN_Carro_Alto", "/IN_Pos_Carico",
                   "Consensi", "(OUT_Carro_Indietro)"]},
        {"cmt": "SORVEGLIANZA TEMPO DI TRASLAZIONE",
         "chain": [{"or": ["OUT_Carro_Avanti", "OUT_Carro_Indietro"]},
                   {"fb": "TON", "inst": "Tim_Traslazione",
                    "p": {"PT": "SET_T_Traslazione"}}]},
        {"cmt": "FINE ESTRAZIONE DALLA VASCA",
         "chain": ["IN_Carro_Alto", "(R Mem_Estrai)"]},
        {"cmt": "SOLLEVAMENTO CESTELLO",
         "chain": [{"or": ["Mem_Carico", "Mem_Scarico", "Mem_Estrai"]}, "/IN_Carro_Alto",
                   "Consensi", "(OUT_Solleva)"]},
        {"cmt": "ABBASSAMENTO CESTELLO (in vasca o sulla stazione di scarico)",
         "chain": [{"or": ["Mem_Target",
                           ["Mem_Ciclo", "Mem_Pieno", ultima, "IN_Pos_Scarico"]]},
                   "/IN_Carro_Basso", "/Mem_Estrai",
                   "Consensi", "(OUT_Abbassa)"]},
        {"cmt": "RESET ALLARMI",
         "chain": ["^V_P_Reset"],
         "out": ([["(R V_S_All_Liv_V%d)" % k] for k in range(1, n_vasche + 1)] +
                 [["(R V_S_All_Temp_V%d)" % k] for k in range(1, n_vasche + 1)])},
        {"cmt": "SPIA ALLARME CUMULATIVO",
         "chain": [{"or": (["V_S_All_Liv_V%d" % k for k in range(1, n_vasche + 1)] +
                            ["V_S_All_Temp_V%d" % k for k in range(1, n_vasche + 1)] +
                            ["/Consensi"])},
                   "(V_L_Allarme)"]},
        {"cmt": "SPIA CICLO", "chain": ["Mem_Ciclo", "(V_L_Ciclo)"]},
        {"cmt": "SPIA FINE CICLO", "chain": ["Mem_Fine", "(V_L_Fine_Ciclo)"]},
        {"cmt": "ALLARME TRASLAZIONE: il carro non arriva entro il tempo",
         "chain": ["Tim_Traslazione.Q", "(S V_S_All_Traslazione)"]},
        {"cmt": "RESET ALLARME TRASLAZIONE",
         "chain": ["^V_P_Reset", "(R V_S_All_Traslazione)"]},
        {"cmt": "RISCALDAMENTO IN CORSO: almeno una resistenza inserita",
         "chain": [{"or": ["OUT_Risc_V%d" % k for k in range(1, n_vasche + 1)]},
                   "(V_L_Riscaldamento)"]},
        {"cmt": "MACCHINA PRONTA: consensi presenti e nessun allarme",
         "chain": ["Consensi", "/V_L_Allarme", "/V_S_All_Traslazione",
                   "(V_L_Pronto)"]},
    ]
    G += [
        ("V_S_All_Traslazione", "BOOL", "allarme tempo di traslazione superato"),
        ("V_L_Riscaldamento", "BOOL", "spia riscaldamento in corso"),
        ("V_L_Pronto", "BOOL", "spia macchina pronta"),
    ]
    return G, I, R


def scenario(n_vasche, salta=None):
    """Ciclo completo su tutte le vasche, con una vasca esclusa dalla ricetta
    per verificare il salto, piu' allarmi livello/temperatura ed emergenza."""
    salta = salta or []
    tempi = {"SET_T_Traslazione": "T#20s"}
    for k in range(1, n_vasche + 1):
        tempi["SET_T_V%d" % k] = "T#1s"

    iniziale = {"IN_Emergenza": False, "IN_Protezioni": True, "IN_Press_Aria": True,
                "IN_Pos_Carico": True, "IN_Pos_Scarico": False,
                "IN_Carro_Alto": False, "IN_Carro_Basso": True,
                "IN_Presenza_Cesto": True, "V_S_Auto": True, "V_S_Cicli_Fatti": 0}
    for k in range(1, n_vasche + 1):
        iniziale["IN_Pos_V%d" % k] = False
        iniziale["IN_Livello_V%d" % k] = True
        iniziale["IN_Temp_V%d" % k] = True
        iniziale["V_S_Usa_V%d" % k] = (k not in salta)

    P = [{"descrizione": "azzeramento e stato iniziale: carro al carico con cestello",
          "set": iniziale, "impulso": ["V_P_Reset"], "attendi": 0.5,
          "verifica": {"OUT_Carro_Avanti": False, "OUT_Solleva": False,
                       "V_L_Ciclo": False, "V_L_Allarme": False}},

         {"descrizione": "START: aggancio del cestello al carico",
          "impulso": ["V_P_Start"], "attendi": 0.4,
          "verifica": {"V_L_Ciclo": True, "OUT_Solleva": True}},

         {"descrizione": "cestello sollevato: il carro parte in traslazione",
          "set": {"IN_Carro_Alto": True, "IN_Carro_Basso": False}, "attendi": 0.4,
          "verifica": {"OUT_Solleva": False, "OUT_Carro_Avanti": True}}]

    attive = [k for k in range(1, n_vasche + 1) if k not in salta]
    for j, k in enumerate(attive):
        P += [
            {"descrizione": "carro sopra la vasca %d: si ferma e cala" % k,
             "set": {"IN_Pos_V%d" % k: True, "IN_Pos_Carico": False},
             "attendi": 0.35,
             "verifica": {"OUT_Carro_Avanti": False, "OUT_Abbassa": True}},
            {"descrizione": "cestello in vasca %d: parte la permanenza" % k,
             "set": {"IN_Carro_Alto": False, "IN_Carro_Basso": True},
             "attendi": 0.35,
             "verifica": {"OUT_Abbassa": False, "End_V%d" % k: False}},
            {"descrizione": "permanenza scaduta in vasca %d: si solleva" % k,
             "attendi": 1.0,
             "verifica": {"End_V%d" % k: True, "OUT_Solleva": True}},
            {"descrizione": "cestello fuori dalla vasca %d: riparte" % k,
             "set": {"IN_Carro_Alto": True, "IN_Carro_Basso": False,
                     "IN_Pos_V%d" % k: False},
             "attendi": 0.4,
             "verifica": {"OUT_Solleva": False,
                          "OUT_Carro_Avanti": True}},
        ]
        if j == 0 and salta:
            P[-1]["verifica"]["End_V%d" % salta[0]] = (salta[0] < k)

    for k in salta:
        P.append({"descrizione": "la vasca %d era esclusa dalla ricetta: saltata" % k,
                  "attendi": 0.2,
                  "verifica": {"End_V%d" % k: True, "OUT_Risc_V%d" % k: False}})

    ult = attive[-1]
    P += [
        {"descrizione": "carro allo scarico: cala il cestello",
         "set": {"IN_Pos_Scarico": True}, "attendi": 0.4,
         "verifica": {"OUT_Carro_Avanti": False, "OUT_Abbassa": True}},
        {"descrizione": "cestello appoggiato allo scarico",
         "set": {"IN_Carro_Alto": False, "IN_Carro_Basso": True}, "attendi": 0.4,
         "verifica": {"OUT_Solleva": True}},
        {"descrizione": "cestello rilasciato: ciclo completato e contatore a 1",
         "set": {"IN_Carro_Alto": True, "IN_Carro_Basso": False}, "attendi": 0.4,
         "verifica": {"V_L_Fine_Ciclo": True, "V_S_Cicli_Fatti": 1,
                      "V_L_Ciclo": False}},
        {"descrizione": "rientro a vuoto verso il carico",
         "set": {"IN_Pos_Scarico": False}, "attendi": 0.3,
         "verifica": {"OUT_Carro_Indietro": False}},
        {"descrizione": "riscaldamento vasca 1: sotto temperatura il resistore va",
         "set": {"IN_Temp_V1": False}, "attendi": 0.3,
         "verifica": {"OUT_Risc_V1": True}},
        {"descrizione": "in temperatura il riscaldamento si spegne",
         "set": {"IN_Temp_V1": True}, "attendi": 0.3,
         "verifica": {"OUT_Risc_V1": False}},
        {"descrizione": "livello basso in vasca 1: niente riscaldamento",
         "set": {"IN_Livello_V1": False, "IN_Temp_V1": False}, "attendi": 0.3,
         "verifica": {"OUT_Risc_V1": False}},
        {"descrizione": "nuovo ciclo con livello basso: allarme livello vasca 1",
         "set": {"IN_Pos_Carico": True, "IN_Carro_Alto": False,
                 "IN_Carro_Basso": True},
         "impulso": ["V_P_Start"], "attendi": 0.5,
         "verifica": {"V_S_All_Liv_V1": True, "V_L_Allarme": True}},
        {"descrizione": "livello ripristinato e RESET: allarme rientrato",
         "set": {"IN_Livello_V1": True, "IN_Temp_V1": True},
         "impulso": ["V_P_Reset"], "attendi": 0.4,
         "verifica": {"V_S_All_Liv_V1": False, "V_L_Allarme": False}},
        {"descrizione": "EMERGENZA: cadono tutti i comandi",
         "set": {"IN_Emergenza": True}, "attendi": 0.4,
         "verifica": {"OUT_Carro_Avanti": False, "OUT_Carro_Indietro": False,
                      "OUT_Solleva": False, "OUT_Abbassa": False,
                      "OUT_Risc_V1": False, "V_L_Allarme": True,
                      "V_L_Ciclo": False}},
    ]
    for k in range(2, min(n_vasche, 4) + 1):
        P[-1]["verifica"]["OUT_Risc_V%d" % k] = False
    _ = ult
    return {"nome": "Linea di lavaggio a %d vasche - collaudo" % n_vasche,
            "tempi": tempi, "passi": P}


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    G, I, R = costruisci(n)
    nome = "lavaggio%d" % n
    spec = {"out_dir": os.path.join(D, "out"),
            "variables": [{"name": a, "type": b, "comment": c} for a, b, c in I],
            "sections": {"Lavaggio": R}}
    json.dump(spec, open(os.path.join(D, "%s_spec.json" % nome), "w", encoding="utf-8"),
              indent=1, ensure_ascii=False)
    for suffisso, dati in (("globali", G), ("interne", I)):
        with open(os.path.join(D, "%s_%s.txt" % (nome, suffisso)), "w", encoding="utf-8") as f:
            for a, b, c in dati:
                f.write("%s\t%s\t%s\n" % (a, b, c))
    with open(os.path.join(D, "%s_esterne.txt" % nome), "w", encoding="utf-8") as f:
        for a, _b, _c in G:
            f.write("%s\n" % a)
    salta = [3] if n >= 4 else []
    sc = scenario(n, salta)
    json.dump(sc, open(os.path.join(D, "%s_scenario.json" % nome), "w", encoding="utf-8"),
              indent=1, ensure_ascii=False)
    # Il simulatore di Sysmac espone SOLO le variabili globali: la stessa
    # verifica su una variabile interna torna "Invalid parameter". Seconda
    # copia dello scenario ripulita, cosi' lo stesso collaudo gira in Python
    # (che vede tutto) e su Sysmac senza falsi negativi.
    glob = set(a for a, _b, _c in G)
    sc_s = json.loads(json.dumps(sc))
    for p in sc_s["passi"]:
        if "verifica" in p:
            p["verifica"] = {k: v for k, v in p["verifica"].items() if k in glob}
    sc_s["passi"] = [p for p in sc_s["passi"]
                     if p.get("verifica") or "durata" in p or "impulso" in p or "set" in p]
    json.dump(sc_s,
              open(os.path.join(D, "%s_scenario_sysmac.json" % nome), "w",
                   encoding="utf-8"), indent=1, ensure_ascii=False)
    print("vasche %d -> rung %d | globali %d | interne %d" % (n, len(R), len(G), len(I)))


if __name__ == "__main__":
    main()
