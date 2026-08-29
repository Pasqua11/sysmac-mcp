# -*- coding: utf-8 -*-
"""
genera_cfe.py - wetbench a N vasche con ricette, robot e allarmi
28/08/2026

Ricalca la struttura del programma piu' lungo della libreria SYNTECH,
CFE300_V4 (711 rung in 29 sezioni): sei vasche di processo, robot di
movimentazione cesti, gestione ricetta con controllo di congruenza, cicli
automatico e semiautomatico, portelli, conteggio soluzioni, log e un blocco
allarmi molto esteso.

Non e' una copia: e' un impianto scritto da zero con la stessa scala e la
stessa articolazione, per misurare quanto costa produrre un programma "vero"
da ~700 rung.

    python genera_cfe.py 6      -> ~700 rung
"""
import json
import os
import sys

D = r"C:\Users\tecni\Claude\sysmac-mcp"


def costruisci(nv=6):
    G, I, S = [], [], {}

    # ================================================== variabili di impianto
    G += [
        ("IN_Emergenza", "BOOL", "fungo di emergenza"),
        ("IN_Protezioni", "BOOL", "protezioni perimetrali chiuse"),
        ("IN_Press_Aria", "BOOL", "pressostato aria compressa"),
        ("IN_Aspirazione", "BOOL", "flussostato aspirazione cappa"),
        ("IN_DIW_Press", "BOOL", "pressostato acqua deionizzata"),
        ("IN_Termico_Gen", "BOOL", "termico generale (NC: TRUE = ok)"),
        ("V_S_Auto", "BOOL", "selettore automatico"),
        ("V_S_Semiauto", "BOOL", "selettore semiautomatico"),
        ("V_P_Start", "BOOL", "start ciclo"),
        ("V_P_Stop", "BOOL", "stop ciclo"),
        ("V_P_Reset", "BOOL", "reset allarmi"),
        ("V_P_Pausa", "BOOL", "pausa ciclo"),
        ("V_S_Ricetta_Sel", "INT", "numero ricetta selezionata da SCADA"),
        ("V_S_Ricetta_Att", "INT", "ricetta in esecuzione"),
        ("V_S_Passo", "INT", "passo di ricetta in corso"),
        ("V_S_Cesti_Fatti", "INT", "cesti processati"),
        ("V_S_Allarmi_Att", "INT", "numero di allarmi attivi"),
        ("V_L_Pronto", "BOOL", "spia macchina pronta"),
        ("V_L_Ciclo", "BOOL", "spia ciclo in corso"),
        ("V_L_Allarme", "BOOL", "spia allarme cumulativo"),
        ("V_L_Pausa", "BOOL", "spia pausa"),
        ("V_L_Fine_Ciclo", "BOOL", "spia ciclo completato"),
        ("V_S_All_Emergenza", "BOOL", "allarme emergenza premuta"),
        ("V_S_All_Protezioni", "BOOL", "allarme protezioni aperte"),
        ("V_S_All_Aria", "BOOL", "allarme mancanza aria"),
        ("V_S_All_Aspirazione", "BOOL", "allarme aspirazione insufficiente"),
        ("V_S_All_DIW", "BOOL", "allarme mancanza acqua DI"),
        ("V_S_All_Termico", "BOOL", "allarme termico generale"),
        ("V_S_All_Ricetta", "BOOL", "allarme ricetta non congruente"),
        ("V_S_All_Robot", "BOOL", "allarme robot in posizione errata"),
        ("V_S_All_Timeout", "BOOL", "allarme timeout movimento"),
        ("V_S_All_Portello", "BOOL", "allarme portello aperto in ciclo"),
    ]
    I += [
        ("Consensi", "BOOL", "consensi di sicurezza presenti"),
        ("Mem_Ciclo", "BOOL", "ciclo automatico in corso"),
        ("Mem_Pausa", "BOOL", "ciclo in pausa"),
        ("Mem_Fine", "BOOL", "ciclo completato"),
        ("Mem_Ricetta_Ok", "BOOL", "ricetta verificata e congruente"),
        ("Mem_Cesto", "BOOL", "cesto presente sul robot"),
        ("Mem_Anomalia", "BOOL", "una qualunque anomalia bloccante"),
        ("Mem_Impianto_Ok", "BOOL", "servizi di impianto disponibili"),
    ]

    # ==================================================== variabili per vasca
    for k in range(1, nv + 1):
        G += [
            ("IN_Liv_Min_V%d" % k, "BOOL", "livello minimo vasca %d" % k),
            ("IN_Liv_Max_V%d" % k, "BOOL", "livello massimo vasca %d" % k),
            ("IN_Temp_Ok_V%d" % k, "BOOL", "termostato vasca %d in banda" % k),
            ("IN_Temp_Alta_V%d" % k, "BOOL", "termostato di sicurezza vasca %d" % k),
            ("IN_Ricircolo_V%d" % k, "BOOL", "flussostato ricircolo vasca %d" % k),
            ("IN_Robot_Su_V%d" % k, "BOOL", "robot in posizione vasca %d" % k),
            ("OUT_Risc_V%d" % k, "BOOL", "riscaldamento vasca %d" % k),
            ("OUT_Pompa_V%d" % k, "BOOL", "pompa ricircolo vasca %d" % k),
            ("OUT_Carico_V%d" % k, "BOOL", "elettrovalvola carico vasca %d" % k),
            ("OUT_Scarico_V%d" % k, "BOOL", "elettrovalvola scarico vasca %d" % k),
            ("SET_T_Perm_V%d" % k, "TIME", "permanenza in vasca %d" % k),
            ("SET_T_Carico_V%d" % k, "TIME", "tempo massimo di carico vasca %d" % k),
            ("SET_Cicli_Max_V%d" % k, "INT", "cicli oltre i quali cambiare la soluzione"),
            ("V_S_Cicli_V%d" % k, "INT", "cicli fatti con la soluzione della vasca %d" % k),
            ("V_S_Usa_V%d" % k, "BOOL", "vasca %d prevista dalla ricetta" % k),
            ("V_S_Soluzione_Vecchia_V%d" % k, "BOOL", "soluzione vasca %d da sostituire" % k),
            ("V_S_All_Liv_V%d" % k, "BOOL", "allarme livello vasca %d" % k),
            ("V_S_All_Temp_V%d" % k, "BOOL", "allarme temperatura vasca %d" % k),
            ("V_S_All_TempAlta_V%d" % k, "BOOL", "allarme sovratemperatura vasca %d" % k),
            ("V_S_All_Ricircolo_V%d" % k, "BOOL", "allarme ricircolo vasca %d" % k),
            ("V_S_All_Carico_V%d" % k, "BOOL", "allarme carico vasca %d non riuscito" % k),
            ("V_L_Vasca_Ready_V%d" % k, "BOOL", "vasca %d pronta al processo" % k),
            ("V_S_Passo_V%d" % k, "INT", "passo di ricetta assegnato alla vasca %d" % k),
            # chimica e servizi della vasca
            ("IN_Cond_Bassa_V%d" % k, "BOOL", "conducibilita' vasca %d sotto soglia" % k),
            ("IN_Cond_Alta_V%d" % k, "BOOL", "conducibilita' vasca %d sopra soglia" % k),
            ("IN_pH_Basso_V%d" % k, "BOOL", "pH vasca %d sotto soglia" % k),
            ("IN_pH_Alto_V%d" % k, "BOOL", "pH vasca %d sopra soglia" % k),
            ("IN_Liv_Sfioro_V%d" % k, "BOOL", "sfioro vasca %d intervenuto" % k),
            ("IN_Filtro_Sporco_V%d" % k, "BOOL", "pressostato differenziale filtro %d" % k),
            ("IN_Chim_A_Min_V%d" % k, "BOOL", "livello minimo tanica chimico A vasca %d" % k),
            ("IN_Chim_B_Min_V%d" % k, "BOOL", "livello minimo tanica chimico B vasca %d" % k),
            ("OUT_Dos_A_V%d" % k, "BOOL", "pompa dosatrice chimico A vasca %d" % k),
            ("OUT_Dos_B_V%d" % k, "BOOL", "pompa dosatrice chimico B vasca %d" % k),
            ("OUT_Rabbocco_V%d" % k, "BOOL", "elettrovalvola rabbocco vasca %d" % k),
            ("OUT_Agitazione_V%d" % k, "BOOL", "aria di agitazione vasca %d" % k),
            ("OUT_Cascata_V%d" % k, "BOOL", "lavaggio a cascata vasca %d" % k),
            ("SET_T_Dos_V%d" % k, "TIME", "durata di una dosata vasca %d" % k),
            ("SET_T_Rabbocco_V%d" % k, "TIME", "tempo massimo di rabbocco vasca %d" % k),
            ("SET_T_Pausa_Dos_V%d" % k, "TIME", "attesa di omogeneizzazione fra due dosate"),
            ("V_S_Dosate_V%d" % k, "INT", "dosate eseguite in vasca %d" % k),
            ("V_S_All_Cond_V%d" % k, "BOOL", "allarme conducibilita' vasca %d" % k),
            ("V_S_All_pH_V%d" % k, "BOOL", "allarme pH vasca %d" % k),
            ("V_S_All_Sfioro_V%d" % k, "BOOL", "allarme sfioro vasca %d" % k),
            ("V_S_All_Filtro_V%d" % k, "BOOL", "allarme filtro intasato vasca %d" % k),
            ("V_S_All_Chim_V%d" % k, "BOOL", "allarme chimico esaurito vasca %d" % k),
            ("V_S_All_Rabbocco_V%d" % k, "BOOL", "allarme rabbocco vasca %d" % k),
        ]
        I += [
            ("Mem_V%d" % k, "BOOL", "processo in corso in vasca %d" % k),
            ("End_V%d" % k, "BOOL", "vasca %d completata" % k),
            ("Rdy_V%d" % k, "BOOL", "vasca %d pronta" % k),
            ("Req_Carico_V%d" % k, "BOOL", "richiesta di carico vasca %d" % k),
            ("Req_Scarico_V%d" % k, "BOOL", "richiesta di scarico vasca %d" % k),
            ("Tim_Perm_V%d" % k, "TON", "permanenza vasca %d" % k),
            ("Tim_Carico_V%d" % k, "TON", "sorveglianza carico vasca %d" % k),
            ("Tim_Temp_V%d" % k, "TON", "ritardo allarme temperatura vasca %d" % k),
            ("Tim_Ric_V%d" % k, "TON", "ritardo allarme ricircolo vasca %d" % k),
            ("Req_Dos_A_V%d" % k, "BOOL", "richiesta dosata chimico A vasca %d" % k),
            ("Req_Dos_B_V%d" % k, "BOOL", "richiesta dosata chimico B vasca %d" % k),
            ("Req_Rabb_V%d" % k, "BOOL", "richiesta rabbocco vasca %d" % k),
            ("Tim_Dos_A_V%d" % k, "TON", "durata dosata A vasca %d" % k),
            ("Tim_Dos_B_V%d" % k, "TON", "durata dosata B vasca %d" % k),
            ("Tim_Rabb_V%d" % k, "TON", "sorveglianza rabbocco vasca %d" % k),
            ("Tim_Cond_V%d" % k, "TON", "ritardo allarme conducibilita' vasca %d" % k),
            ("Tim_pH_V%d" % k, "TON", "ritardo allarme pH vasca %d" % k),
            ("Tim_Pausa_A_V%d" % k, "TON", "attesa fra due dosate A in vasca %d" % k),
            ("Tim_Pausa_B_V%d" % k, "TON", "attesa fra due dosate B in vasca %d" % k),
        ]

    # ================================================= robot di movimentazione
    G += [
        ("IN_Robot_Carico", "BOOL", "robot in posizione di carico"),
        ("IN_Robot_Scarico", "BOOL", "robot in posizione di scarico"),
        ("IN_Robot_Alto", "BOOL", "robot in quota alta"),
        ("IN_Robot_Basso", "BOOL", "robot in quota bassa"),
        ("IN_Cesto_Presente", "BOOL", "cesto presente in pinza"),
        ("IN_Cesto_Carico", "BOOL", "cesto in attesa al carico"),
        ("IN_Portello_1", "BOOL", "portello anteriore chiuso"),
        ("IN_Portello_2", "BOOL", "portello posteriore chiuso"),
        ("OUT_Robot_Avanti", "BOOL", "traslazione robot avanti"),
        ("OUT_Robot_Indietro", "BOOL", "traslazione robot indietro"),
        ("OUT_Robot_Sale", "BOOL", "sollevamento robot"),
        ("OUT_Robot_Scende", "BOOL", "discesa robot"),
        ("OUT_Pinza_Chiudi", "BOOL", "chiusura pinza"),
        ("OUT_Pinza_Apri", "BOOL", "apertura pinza"),
        ("OUT_Blocco_Portelli", "BOOL", "elettroserratura portelli"),
        ("SET_T_Mov", "TIME", "tempo massimo di un movimento"),
        ("V_S_Pos_Robot", "INT", "posizione corrente del robot"),
        ("V_S_Pos_Target", "INT", "posizione richiesta al robot"),
    ]
    I += [
        ("Mem_Rob_Target", "BOOL", "robot fermo sulla posizione richiesta"),
        ("Mem_Rob_Estrai", "BOOL", "cesto da estrarre dalla vasca"),
        ("Mem_Rob_Carico", "BOOL", "passo di prelievo al carico"),
        ("Mem_Rob_Scarico", "BOOL", "passo di deposito allo scarico"),
        ("Mem_Rob_Muove", "BOOL", "un movimento del robot e' in corso"),
        ("Man_Avanti", "BOOL", "comando manuale di traslazione avanti"),
        ("Man_Indietro", "BOOL", "comando manuale di traslazione indietro"),
        ("Tim_Mov", "TON", "sorveglianza tempo di movimento"),
        ("Tim_Log", "TON", "base tempi per il log"),
        ("Tim_Debounce", "TON", "filtro sui consensi di impianto"),
    ]

    # ======================================================== SEZIONE Servizi
    R = [
        {"cmt": "SERVIZI DI IMPIANTO: aria, aspirazione, acqua DI, termico",
         "chain": ["IN_Press_Aria", "IN_Aspirazione", "IN_DIW_Press",
                   "IN_Termico_Gen", "(Mem_Impianto_Ok)"]},
        {"cmt": "FILTRO SUI SERVIZI: devono restare presenti per 2 s",
         "chain": ["Mem_Impianto_Ok",
                   {"fb": "TON", "inst": "Tim_Debounce", "p": {"PT": "T#2s"}}]},
        {"cmt": "CONSENSI DI SICUREZZA",
         "chain": ["/IN_Emergenza", "IN_Protezioni", "Tim_Debounce.Q",
                   "(Consensi)"]},
        {"cmt": "PORTELLI CHIUSI: consenso al ciclo automatico",
         "chain": ["IN_Portello_1", "IN_Portello_2", "Consensi",
                   "(OUT_Blocco_Portelli)"]},
        {"cmt": "ANOMALIA BLOCCANTE",
         "chain": [{"or": ["/Consensi", "V_S_All_Robot", "V_S_All_Timeout",
                           "V_S_All_Portello", "V_S_All_Ricetta"]},
                   "(Mem_Anomalia)"]},
        {"cmt": "MACCHINA PRONTA",
         "chain": ["Consensi", "/Mem_Anomalia", "Mem_Ricetta_Ok",
                   "(V_L_Pronto)"]},
        # I comandi manuali stanno QUI e non nella sezione ausiliari: se
        # scrivessero direttamente OUT_Robot_* finirebbero per azzerare i
        # comandi dell'automatico, perche' su una stessa uscita comanda
        # l'ultima bobina eseguita nella scansione. Qui producono solo una
        # memoria, e il comando finale al robot resta uno solo.
        {"cmt": "MANUALE: traslazione avanti in semiautomatico",
         "chain": ["V_S_Semiauto", "/Mem_Ciclo", "Consensi", "V_P_Start",
                   "IN_Robot_Alto", "(Man_Avanti)"]},
        {"cmt": "MANUALE: traslazione indietro in semiautomatico",
         "chain": ["V_S_Semiauto", "/Mem_Ciclo", "Consensi", "V_P_Stop",
                   "IN_Robot_Alto", "(Man_Indietro)"]},
    ]
    S["Servizi"] = R

    # ========================================================= SEZIONE Ricetta
    R = [
        {"cmt": "RICETTA: acquisizione della selezione da SCADA",
         "chain": ["/Mem_Ciclo",
                   {"f": "MOVE", "p": {"In": "V_S_Ricetta_Sel",
                                        "OUT:Out": "V_S_Ricetta_Att"}}]},
    ]
    for k in range(1, nv + 1):
        R += [
            {"cmt": "RICETTA: la vasca %d e' usata se ha un passo assegnato" % k,
             "chain": [{"f": ">", "p": {"In1": "V_S_Passo_V%d" % k, "In2": "0"}},
                       "(V_S_Usa_V%d)" % k]},
            {"cmt": "CHECK RICETTA: la vasca %d usata deve essere pronta" % k,
             "chain": ["V_S_Usa_V%d" % k, "/Rdy_V%d" % k, "Mem_Ciclo",
                       "(S V_S_All_Ricetta)"]},
            {"cmt": "CHECK RICETTA: la vasca %d usata deve avere un tempo" % k,
             "chain": ["V_S_Usa_V%d" % k,
                       {"f": "=", "p": {"In1": "V_S_Passo_V%d" % k, "In2": "0"}},
                       "(S V_S_All_Ricetta)"]},
            {"cmt": "CHECK RICETTA: soluzione vasca %d esaurita" % k,
             "chain": [{"f": ">=", "p": {"In1": "V_S_Cicli_V%d" % k,
                                          "In2": "SET_Cicli_Max_V%d" % k}},
                       "(V_S_Soluzione_Vecchia_V%d)" % k]},
            {"cmt": "CHECK RICETTA: vasca %d con soluzione vecchia non parte" % k,
             "chain": ["V_S_Usa_V%d" % k, "V_S_Soluzione_Vecchia_V%d" % k,
                       "^V_P_Start", "(S V_S_All_Ricetta)"]},
        ]
    R += [
        {"cmt": "RICETTA CONGRUENTE: nessun allarme di congruenza",
         "chain": ["/V_S_All_Ricetta",
                   {"f": ">", "p": {"In1": "V_S_Ricetta_Att", "In2": "0"}},
                   "(Mem_Ricetta_Ok)"]},
        {"cmt": "RESET ALLARME RICETTA",
         "chain": ["^V_P_Reset", "(R V_S_All_Ricetta)"]},
    ]
    S["Ricetta"] = R

    # =========================================================== SEZIONE Cicli
    R = [
        # Questo rung va PRIMA dello start e NON deve avere "/Mem_Ciclo": sul
        # fronte di V_P_Start il rung di avvio ha gia' messo Mem_Ciclo a 1
        # nella stessa scansione, quindi quella condizione sarebbe sempre
        # falsa e gli End_V* del ciclo precedente non verrebbero mai azzerati.
        # Effetto: dal secondo cesto in poi la macchina non riparte. Trovato
        # sul simulatore Sysmac il 28/08/2026 e non in Python, dove ogni
        # collaudo partiva da uno stato vergine.
        {"cmt": "AZZERAMENTO PASSI A INIZIO CICLO",
         "chain": ["^V_P_Start"],
         "out": ([["(R End_V%d)" % k] for k in range(1, nv + 1)] +
                 [["(R Mem_Fine)"], ["(R Mem_Rob_Estrai)"]])},
        {"cmt": "START CICLO AUTOMATICO",
         "chain": ["^V_P_Start", "Consensi", "V_S_Auto", "Mem_Ricetta_Ok",
                   "IN_Cesto_Carico", "/Mem_Anomalia", "/Mem_Rob_Muove"],
         "out": [["(R Mem_Fine)"], ["(S Mem_Ciclo)"]]},
        {"cmt": "ARRESTO CICLO",
         "chain": [{"or": ["^V_P_Stop", "Mem_Anomalia", "Mem_Fine"]},
                   "(R Mem_Ciclo)"]},
        {"cmt": "PAUSA CICLO",
         "chain": ["^V_P_Pausa", "Mem_Ciclo", "(S Mem_Pausa)"]},
        {"cmt": "RIPRESA DALLA PAUSA",
         "chain": ["^V_P_Start", "Mem_Pausa", "(R Mem_Pausa)"]},
        {"cmt": "PASSO DI RICETTA IN CORSO",
         "chain": [{"or": ["Mem_V%d" % k for k in range(1, nv + 1)]},
                   "(V_L_Ciclo)"]},
    ]
    for k in range(1, nv + 1):
        prec = "Mem_Cesto" if k == 1 else "End_V%d" % (k - 1)
        R += [
            {"cmt": "INGRESSO IN VASCA %d" % k,
             "chain": ["Mem_Ciclo", "/Mem_Pausa", "Mem_Cesto", "V_S_Usa_V%d" % k,
                       "IN_Robot_Su_V%d" % k, "IN_Robot_Basso", prec,
                       "/End_V%d" % k, "Rdy_V%d" % k, "(S Mem_V%d)" % k]},
            {"cmt": "PERMANENZA IN VASCA %d" % k,
             "chain": ["Mem_V%d" % k, "/Mem_Pausa",
                       {"fb": "TON", "inst": "Tim_Perm_V%d" % k,
                        "p": {"PT": "SET_T_Perm_V%d" % k}}]},
            {"cmt": "USCITA DALLA VASCA %d (o salto se non in ricetta)" % k,
             "chain": [{"or": ["Tim_Perm_V%d.Q" % k, "/V_S_Usa_V%d" % k]},
                       {"or": ["Mem_V%d" % k,
                               ["Mem_Ciclo", "/V_S_Usa_V%d" % k, prec]]}],
             "out": [["(S End_V%d)" % k], ["(R Mem_V%d)" % k]]},
            {"cmt": "CONTEGGIO CICLI DELLA SOLUZIONE IN VASCA %d" % k,
             "chain": ["^End_V%d" % k, "V_S_Usa_V%d" % k,
                       {"f": "@Inc", "p": {"InOut": "V_S_Cicli_V%d" % k,
                                            "OUT:InOut": "V_S_Cicli_V%d" % k}}]},
        ]
    ultima = "End_V%d" % nv
    R += [
        {"cmt": "CICLO COMPLETATO",
         "chain": ["Mem_Ciclo", ultima, "/Mem_Cesto", "(S Mem_Fine)"]},
        {"cmt": "CONTEGGIO CESTI PROCESSATI",
         "chain": ["^Mem_Fine",
                   {"f": "@Inc", "p": {"InOut": "V_S_Cesti_Fatti",
                                        "OUT:InOut": "V_S_Cesti_Fatti"}}]},
        {"cmt": "SPIA FINE CICLO", "chain": ["Mem_Fine", "(V_L_Fine_Ciclo)"]},
        {"cmt": "SPIA PAUSA", "chain": ["Mem_Pausa", "(V_L_Pausa)"]},
    ]
    S["Cicli"] = R

    # ========================================================== SEZIONE Vasche
    R = []
    for k in range(1, nv + 1):
        R += [
            {"cmt": "VASCA %d - RICHIESTA DI CARICO SOTTO IL MINIMO" % k,
             "chain": ["/IN_Liv_Min_V%d" % k, "Consensi", "/V_S_All_Liv_V%d" % k,
                       "(S Req_Carico_V%d)" % k]},
            {"cmt": "VASCA %d - FINE CARICO AL MASSIMO" % k,
             "chain": [{"or": ["IN_Liv_Max_V%d" % k, "/Consensi"]},
                       "(R Req_Carico_V%d)" % k]},
            {"cmt": "VASCA %d - ELETTROVALVOLA DI CARICO" % k,
             "chain": ["Req_Carico_V%d" % k, "IN_DIW_Press", "Consensi",
                       "/Mem_V%d" % k, "(OUT_Carico_V%d)" % k]},
            {"cmt": "VASCA %d - SORVEGLIANZA TEMPO DI CARICO" % k,
             "chain": ["OUT_Carico_V%d" % k,
                       {"fb": "TON", "inst": "Tim_Carico_V%d" % k,
                        "p": {"PT": "SET_T_Carico_V%d" % k}}]},
            {"cmt": "VASCA %d - ALLARME CARICO NON RIUSCITO" % k,
             "chain": ["Tim_Carico_V%d.Q" % k, "(S V_S_All_Carico_V%d)" % k]},
            {"cmt": "VASCA %d - RICHIESTA DI SCARICO SOLUZIONE ESAURITA" % k,
             "chain": ["V_S_Soluzione_Vecchia_V%d" % k, "/Mem_Ciclo",
                       "Consensi", "(S Req_Scarico_V%d)" % k]},
            {"cmt": "VASCA %d - FINE SCARICO SOTTO IL MINIMO" % k,
             "chain": [{"or": ["/IN_Liv_Min_V%d" % k, "/Consensi"]},
                       "(R Req_Scarico_V%d)" % k]},
            {"cmt": "VASCA %d - ELETTROVALVOLA DI SCARICO" % k,
             "chain": ["Req_Scarico_V%d" % k, "Consensi",
                       "/OUT_Carico_V%d" % k, "(OUT_Scarico_V%d)" % k]},
            {"cmt": "VASCA %d - AZZERAMENTO CICLI DOPO IL CAMBIO SOLUZIONE" % k,
             "chain": ["^Req_Scarico_V%d" % k, "IN_Liv_Max_V%d" % k,
                       {"f": "MOVE", "p": {"In": "0",
                                            "OUT:Out": "V_S_Cicli_V%d" % k}}]},
            {"cmt": "VASCA %d - POMPA DI RICIRCOLO" % k,
             "chain": ["IN_Liv_Min_V%d" % k, "Consensi", "/Req_Scarico_V%d" % k,
                       "(OUT_Pompa_V%d)" % k]},
            {"cmt": "VASCA %d - RISCALDAMENTO" % k,
             "chain": ["IN_Liv_Min_V%d" % k, "/IN_Temp_Ok_V%d" % k,
                       "/IN_Temp_Alta_V%d" % k, "OUT_Pompa_V%d" % k,
                       "Consensi", "(OUT_Risc_V%d)" % k]},
            {"cmt": "VASCA %d - PRONTA AL PROCESSO" % k,
             "chain": ["IN_Liv_Min_V%d" % k, "IN_Temp_Ok_V%d" % k,
                       "IN_Ricircolo_V%d" % k, "/V_S_Soluzione_Vecchia_V%d" % k,
                       "(Rdy_V%d)" % k]},
            {"cmt": "VASCA %d - SPIA PRONTA" % k,
             "chain": ["Rdy_V%d" % k, "(V_L_Vasca_Ready_V%d)" % k]},
        ]
    S["Vasche"] = R

    # ========================================================= SEZIONE Chimica
    R = []
    for k in range(1, nv + 1):
        R += [
            # attesa di omogeneizzazione fra due dosate: senza questa il set
            # della richiesta si riarmava a ogni scansione (la sonda legge
            # ancora basso) e la pompa dosatrice non si fermava piu'
            {"cmt": "VASCA %d - ATTESA FRA DUE DOSATE A" % k,
             "chain": ["/Req_Dos_A_V%d" % k,
                       {"fb": "TON", "inst": "Tim_Pausa_A_V%d" % k,
                        "p": {"PT": "SET_T_Pausa_Dos_V%d" % k}}]},
            {"cmt": "VASCA %d - RICHIESTA DOSATA A: conducibilita' bassa" % k,
             "chain": ["IN_Cond_Bassa_V%d" % k, "IN_Liv_Min_V%d" % k,
                       "OUT_Pompa_V%d" % k, "/V_S_All_Chim_V%d" % k,
                       "Tim_Pausa_A_V%d.Q" % k,
                       "Consensi", "(S Req_Dos_A_V%d)" % k]},
            {"cmt": "VASCA %d - DOSATA A: comando della pompa dosatrice" % k,
             "chain": ["Req_Dos_A_V%d" % k, "IN_Chim_A_Min_V%d" % k,
                       "/IN_Liv_Max_V%d" % k, "(OUT_Dos_A_V%d)" % k]},
            {"cmt": "VASCA %d - DOSATA A: durata della dosata" % k,
             "chain": ["OUT_Dos_A_V%d" % k,
                       {"fb": "TON", "inst": "Tim_Dos_A_V%d" % k,
                        "p": {"PT": "SET_T_Dos_V%d" % k}}]},
            {"cmt": "VASCA %d - DOSATA A: fine dosata e conteggio" % k,
             "chain": ["Tim_Dos_A_V%d.Q" % k],
             "out": [["(R Req_Dos_A_V%d)" % k],
                     [{"f": "@Inc", "p": {"InOut": "V_S_Dosate_V%d" % k,
                                           "OUT:InOut": "V_S_Dosate_V%d" % k}}]]},
            {"cmt": "VASCA %d - ATTESA FRA DUE DOSATE B" % k,
             "chain": ["/Req_Dos_B_V%d" % k,
                       {"fb": "TON", "inst": "Tim_Pausa_B_V%d" % k,
                        "p": {"PT": "SET_T_Pausa_Dos_V%d" % k}}]},
            {"cmt": "VASCA %d - RICHIESTA DOSATA B: pH fuori banda" % k,
             "chain": ["IN_pH_Basso_V%d" % k, "IN_Liv_Min_V%d" % k,
                       "OUT_Pompa_V%d" % k, "Tim_Pausa_B_V%d.Q" % k,
                       "Consensi", "(S Req_Dos_B_V%d)" % k]},
            {"cmt": "VASCA %d - DOSATA B: comando della pompa dosatrice" % k,
             "chain": ["Req_Dos_B_V%d" % k, "IN_Chim_B_Min_V%d" % k,
                       "/IN_Liv_Max_V%d" % k, "(OUT_Dos_B_V%d)" % k]},
            {"cmt": "VASCA %d - DOSATA B: durata della dosata" % k,
             "chain": ["OUT_Dos_B_V%d" % k,
                       {"fb": "TON", "inst": "Tim_Dos_B_V%d" % k,
                        "p": {"PT": "SET_T_Dos_V%d" % k}}]},
            {"cmt": "VASCA %d - DOSATA B: fine dosata" % k,
             "chain": ["Tim_Dos_B_V%d.Q" % k, "(R Req_Dos_B_V%d)" % k]},
            {"cmt": "VASCA %d - CHIMICO ESAURITO" % k,
             "chain": [{"or": [["Req_Dos_A_V%d" % k, "/IN_Chim_A_Min_V%d" % k],
                               ["Req_Dos_B_V%d" % k, "/IN_Chim_B_Min_V%d" % k]]},
                       "(S V_S_All_Chim_V%d)" % k]},
            {"cmt": "VASCA %d - RICHIESTA RABBOCCO per evaporazione" % k,
             "chain": ["/IN_Liv_Max_V%d" % k, "IN_Liv_Min_V%d" % k,
                       "IN_Temp_Ok_V%d" % k, "/Mem_V%d" % k, "Consensi",
                       "(S Req_Rabb_V%d)" % k]},
            {"cmt": "VASCA %d - RABBOCCO: elettrovalvola" % k,
             "chain": ["Req_Rabb_V%d" % k, "IN_DIW_Press",
                       "/OUT_Carico_V%d" % k, "(OUT_Rabbocco_V%d)" % k]},
            {"cmt": "VASCA %d - RABBOCCO: sorveglianza del tempo" % k,
             "chain": ["OUT_Rabbocco_V%d" % k,
                       {"fb": "TON", "inst": "Tim_Rabb_V%d" % k,
                        "p": {"PT": "SET_T_Rabbocco_V%d" % k}}]},
            {"cmt": "VASCA %d - RABBOCCO: fine al livello massimo" % k,
             "chain": [{"or": ["IN_Liv_Max_V%d" % k, "Tim_Rabb_V%d.Q" % k]},
                       "(R Req_Rabb_V%d)" % k]},
            {"cmt": "VASCA %d - ALLARME rabbocco troppo lungo" % k,
             "chain": ["Tim_Rabb_V%d.Q" % k, "/IN_Liv_Max_V%d" % k,
                       "(S V_S_All_Rabbocco_V%d)" % k]},
            {"cmt": "VASCA %d - AGITAZIONE ad aria durante il processo" % k,
             "chain": ["Mem_V%d" % k, "IN_Press_Aria", "IN_Liv_Min_V%d" % k,
                       "Consensi", "(OUT_Agitazione_V%d)" % k]},
            {"cmt": "VASCA %d - LAVAGGIO A CASCATA nelle vasche di risciacquo" % k,
             "chain": ["Mem_V%d" % k, "IN_DIW_Press", "/IN_Liv_Sfioro_V%d" % k,
                       "Consensi", "(OUT_Cascata_V%d)" % k]},
            {"cmt": "VASCA %d - CONDUCIBILITA' fuori banda da troppo tempo" % k,
             "chain": [{"or": ["IN_Cond_Alta_V%d" % k,
                               ["IN_Cond_Bassa_V%d" % k, "/Req_Dos_A_V%d" % k]]},
                       "IN_Liv_Min_V%d" % k,
                       {"fb": "TON", "inst": "Tim_Cond_V%d" % k,
                        "p": {"PT": "T#300s"}}]},
            {"cmt": "VASCA %d - ALLARME conducibilita'" % k,
             "chain": ["Tim_Cond_V%d.Q" % k, "(S V_S_All_Cond_V%d)" % k]},
            {"cmt": "VASCA %d - pH fuori banda da troppo tempo" % k,
             "chain": [{"or": ["IN_pH_Alto_V%d" % k,
                               ["IN_pH_Basso_V%d" % k, "/Req_Dos_B_V%d" % k]]},
                       "IN_Liv_Min_V%d" % k,
                       {"fb": "TON", "inst": "Tim_pH_V%d" % k,
                        "p": {"PT": "T#300s"}}]},
            {"cmt": "VASCA %d - ALLARME pH" % k,
             "chain": ["Tim_pH_V%d.Q" % k, "(S V_S_All_pH_V%d)" % k]},
            {"cmt": "VASCA %d - ALLARME sfioro intervenuto" % k,
             "chain": ["IN_Liv_Sfioro_V%d" % k, "(S V_S_All_Sfioro_V%d)" % k]},
            {"cmt": "VASCA %d - lo sfioro chiude carico e rabbocco" % k,
             "chain": ["V_S_All_Sfioro_V%d" % k],
             "out": [["(R Req_Carico_V%d)" % k], ["(R Req_Rabb_V%d)" % k]]},
            {"cmt": "VASCA %d - ALLARME filtro intasato" % k,
             "chain": ["IN_Filtro_Sporco_V%d" % k, "OUT_Pompa_V%d" % k,
                       "(S V_S_All_Filtro_V%d)" % k]},
            {"cmt": "VASCA %d - RESET allarmi di chimica" % k,
             "chain": ["^V_P_Reset"],
             "out": [["(R V_S_All_Cond_V%d)" % k], ["(R V_S_All_pH_V%d)" % k],
                     ["(R V_S_All_Sfioro_V%d)" % k],
                     ["(R V_S_All_Filtro_V%d)" % k],
                     ["(R V_S_All_Chim_V%d)" % k],
                     ["(R V_S_All_Rabbocco_V%d)" % k]]},
            {"cmt": "VASCA %d - la vasca non e' pronta con allarmi di chimica" % k,
             "chain": [{"or": ["V_S_All_Cond_V%d" % k, "V_S_All_pH_V%d" % k,
                               "V_S_All_Sfioro_V%d" % k,
                               "V_S_All_Chim_V%d" % k]},
                       "(R Rdy_V%d)" % k]},
        ]
    S["Chimica"] = R

    # ==================================================== SEZIONE Movimentazione
    R = [
        {"cmt": "ROBOT: prelievo del cesto al carico",
         "chain": ["Mem_Ciclo", "/Mem_Pausa", "IN_Robot_Carico",
                   "IN_Cesto_Carico", "/Mem_Cesto", "IN_Robot_Basso",
                   "(S Mem_Rob_Carico)"]},
        {"cmt": "ROBOT: chiusura pinza sul cesto",
         "chain": ["Mem_Rob_Carico", "/IN_Cesto_Presente", "Consensi",
                   "(OUT_Pinza_Chiudi)"]},
        {"cmt": "ROBOT: cesto agganciato",
         "chain": ["Mem_Rob_Carico", "IN_Cesto_Presente", "IN_Robot_Alto"],
         "out": [["(S Mem_Cesto)"], ["(R Mem_Rob_Carico)"]]},
        # L'estrazione si arma solo sulle vasche DAVVERO fatte: le vasche fuori
        # ricetta vengono completate d'ufficio e, armando anche loro questa
        # memoria, la lasciavano alta a fine ciclo. Restando alta teneva su
        # Mem_Rob_Muove e il ciclo successivo non partiva piu'.
        {"cmt": "ROBOT: cesto da estrarre dalla vasca appena terminata",
         "chain": [{"or": [["^End_V%d" % k, "V_S_Usa_V%d" % k]
                           for k in range(1, nv + 1)]},
                   "Mem_Cesto", "(S Mem_Rob_Estrai)"]},
        {"cmt": "ROBOT: fine estrazione dalla vasca",
         "chain": ["IN_Robot_Alto", "(R Mem_Rob_Estrai)"]},
        {"cmt": "ROBOT: posizione di destinazione raggiunta",
         "chain": ["Mem_Ciclo", "Mem_Cesto",
                   {"or": [["V_S_Usa_V%d" % k, "/End_V%d" % k,
                            "IN_Robot_Su_V%d" % k] for k in range(1, nv + 1)]},
                   "(Mem_Rob_Target)"]},
        {"cmt": "ROBOT: traslazione avanti (automatico o manuale)",
         "chain": [{"or": [["Mem_Ciclo", "/Mem_Pausa", "Mem_Cesto",
                            "IN_Robot_Alto", "/Mem_Rob_Target",
                            "/IN_Robot_Scarico"],
                           "Man_Avanti"]},
                   "Consensi", "(OUT_Robot_Avanti)"]},
        {"cmt": "ROBOT: rientro a vuoto (automatico o manuale)",
         "chain": [{"or": [["Mem_Ciclo", "/Mem_Cesto", "IN_Robot_Alto",
                            "/IN_Robot_Carico"],
                           "Man_Indietro"]},
                   "Consensi", "(OUT_Robot_Indietro)"]},
        {"cmt": "ROBOT: discesa in vasca o allo scarico",
         "chain": [{"or": ["Mem_Rob_Target",
                           ["Mem_Ciclo", "Mem_Cesto", ultima,
                            "IN_Robot_Scarico"]]},
                   "/IN_Robot_Basso", "/Mem_Rob_Estrai", "/Mem_Pausa",
                   "Consensi", "(OUT_Robot_Scende)"]},
        {"cmt": "ROBOT: salita",
         "chain": [{"or": ["Mem_Rob_Carico", "Mem_Rob_Scarico",
                           "Mem_Rob_Estrai"]},
                   "/IN_Robot_Alto", "/Mem_Pausa", "Consensi",
                   "(OUT_Robot_Sale)"]},
        {"cmt": "ROBOT: deposito allo scarico",
         "chain": ["Mem_Ciclo", ultima, "IN_Robot_Scarico", "IN_Robot_Basso",
                   "Mem_Cesto", "(S Mem_Rob_Scarico)"]},
        {"cmt": "ROBOT: apertura pinza allo scarico",
         "chain": ["Mem_Rob_Scarico", "IN_Robot_Basso", "Consensi",
                   "(OUT_Pinza_Apri)"]},
        {"cmt": "ROBOT: cesto rilasciato",
         "chain": ["Mem_Rob_Scarico", "/IN_Cesto_Presente"],
         "out": [["(R Mem_Cesto)"], ["(R Mem_Rob_Scarico)"]]},
        {"cmt": "ROBOT: un movimento e' in corso",
         "chain": [{"or": ["OUT_Robot_Avanti", "OUT_Robot_Indietro",
                           "OUT_Robot_Sale", "OUT_Robot_Scende"]},
                   "(Mem_Rob_Muove)"]},
        {"cmt": "ROBOT: sorveglianza del tempo di movimento",
         "chain": ["Mem_Rob_Muove",
                   {"fb": "TON", "inst": "Tim_Mov", "p": {"PT": "SET_T_Mov"}}]},
        {"cmt": "ROBOT: allarme timeout movimento",
         "chain": ["Tim_Mov.Q", "(S V_S_All_Timeout)"]},
        {"cmt": "ROBOT: posizione corrente allo scarico",
         "chain": ["IN_Robot_Scarico",
                   {"f": "MOVE", "p": {"In": "99", "OUT:Out": "V_S_Pos_Robot"}}]},
        {"cmt": "ROBOT: posizione corrente al carico",
         "chain": ["IN_Robot_Carico",
                   {"f": "MOVE", "p": {"In": "0", "OUT:Out": "V_S_Pos_Robot"}}]},
    ]
    for k in range(1, nv + 1):
        R += [
            {"cmt": "ROBOT: posizione corrente sulla vasca %d" % k,
             "chain": ["IN_Robot_Su_V%d" % k,
                       {"f": "MOVE", "p": {"In": str(k),
                                            "OUT:Out": "V_S_Pos_Robot"}}]},
            # senza il vincolo sulla vasca precedente ogni rung sovrascriveva
            # il precedente e in V_S_Pos_Target restava l'ULTIMA vasca da
            # fare invece della prossima
            {"cmt": "ROBOT: destinazione vasca %d quando e' la prossima" % k,
             "chain": ["Mem_Ciclo", "Mem_Cesto", "V_S_Usa_V%d" % k,
                       "/End_V%d" % k] +
                      ([] if k == 1 else ["End_V%d" % (k - 1)]) +
                      [{"f": "MOVE", "p": {"In": str(k),
                                            "OUT:Out": "V_S_Pos_Target"}}]},
            {"cmt": "ROBOT: allarme se scende su una vasca non pronta (%d)" % k,
             "chain": ["IN_Robot_Su_V%d" % k, "IN_Robot_Basso",
                       "V_S_Usa_V%d" % k, "/Rdy_V%d" % k,
                       "(S V_S_All_Robot)"]},
        ]
    R += [
        {"cmt": "RESET MOVIMENTI: allarmi di movimentazione azzerati",
         "chain": ["^V_P_Reset"],
         "out": [["(R V_S_All_Timeout)"], ["(R V_S_All_Robot)"],
                 ["(R Mem_Rob_Carico)"], ["(R Mem_Rob_Scarico)"],
                 ["(R Mem_Rob_Estrai)"]]},
    ]
    S["Movimentazione"] = R

    # ========================================================= SEZIONE Allarmi
    R = []
    fissi = [
        ("V_S_All_Emergenza", "IN_Emergenza", True, "emergenza premuta"),
        ("V_S_All_Protezioni", "IN_Protezioni", False, "protezioni aperte"),
        ("V_S_All_Aria", "IN_Press_Aria", False, "mancanza aria compressa"),
        ("V_S_All_Aspirazione", "IN_Aspirazione", False, "aspirazione insufficiente"),
        ("V_S_All_DIW", "IN_DIW_Press", False, "mancanza acqua deionizzata"),
        ("V_S_All_Termico", "IN_Termico_Gen", False, "termico generale intervenuto"),
    ]
    for allarme, ingresso, diretto, testo in fissi:
        R.append({"cmt": "ALLARME: %s" % testo,
                  "chain": [ingresso if diretto else "/" + ingresso,
                            "(S %s)" % allarme]})
        R.append({"cmt": "RESET allarme %s" % testo,
                  "chain": ["^V_P_Reset",
                            ingresso if not diretto else "/" + ingresso,
                            "(R %s)" % allarme]})
    R.append({"cmt": "ALLARME: portello aperto durante il ciclo",
              "chain": ["Mem_Ciclo",
                        {"or": ["/IN_Portello_1", "/IN_Portello_2"]},
                        "(S V_S_All_Portello)"]})
    R.append({"cmt": "RESET allarme portello",
              "chain": ["^V_P_Reset", "IN_Portello_1", "IN_Portello_2",
                        "(R V_S_All_Portello)"]})

    for k in range(1, nv + 1):
        R += [
            {"cmt": "ALLARME VASCA %d: livello sotto il minimo in processo" % k,
             "chain": ["Mem_V%d" % k, "/IN_Liv_Min_V%d" % k,
                       "(S V_S_All_Liv_V%d)" % k]},
            {"cmt": "ALLARME VASCA %d: fuori temperatura da troppo tempo" % k,
             "chain": ["V_S_Usa_V%d" % k, "/IN_Temp_Ok_V%d" % k, "Mem_V%d" % k,
                       {"fb": "TON", "inst": "Tim_Temp_V%d" % k,
                        "p": {"PT": "T#180s"}}]},
            {"cmt": "ALLARME VASCA %d: memoria temperatura" % k,
             "chain": ["Tim_Temp_V%d.Q" % k, "(S V_S_All_Temp_V%d)" % k]},
            {"cmt": "ALLARME VASCA %d: sovratemperatura (sicurezza)" % k,
             "chain": ["IN_Temp_Alta_V%d" % k, "(S V_S_All_TempAlta_V%d)" % k]},
            {"cmt": "ALLARME VASCA %d: ricircolo assente con pompa in marcia" % k,
             "chain": ["OUT_Pompa_V%d" % k, "/IN_Ricircolo_V%d" % k,
                       {"fb": "TON", "inst": "Tim_Ric_V%d" % k,
                        "p": {"PT": "T#10s"}}]},
            {"cmt": "ALLARME VASCA %d: memoria ricircolo" % k,
             "chain": ["Tim_Ric_V%d.Q" % k, "(S V_S_All_Ricircolo_V%d)" % k]},
            {"cmt": "RESET allarmi della vasca %d" % k,
             "chain": ["^V_P_Reset"],
             "out": [["(R V_S_All_Liv_V%d)" % k], ["(R V_S_All_Temp_V%d)" % k],
                     ["(R V_S_All_TempAlta_V%d)" % k],
                     ["(R V_S_All_Ricircolo_V%d)" % k],
                     ["(R V_S_All_Carico_V%d)" % k]]},
            {"cmt": "VASCA %d: il riscaldamento cade sugli allarmi" % k,
             "chain": [{"or": ["V_S_All_TempAlta_V%d" % k,
                               "V_S_All_Liv_V%d" % k,
                               "V_S_All_Ricircolo_V%d" % k]},
                       "(R OUT_Risc_V%d)" % k]},
        ]

    tutti = (["V_S_All_%s" % n for n in
              ("Emergenza", "Protezioni", "Aria", "Aspirazione", "DIW",
               "Termico", "Ricetta", "Robot", "Timeout", "Portello")] +
             ["V_S_All_Liv_V%d" % k for k in range(1, nv + 1)] +
             ["V_S_All_Temp_V%d" % k for k in range(1, nv + 1)] +
             ["V_S_All_TempAlta_V%d" % k for k in range(1, nv + 1)] +
             ["V_S_All_Ricircolo_V%d" % k for k in range(1, nv + 1)] +
             ["V_S_All_Carico_V%d" % k for k in range(1, nv + 1)] +
             ["V_S_All_Cond_V%d" % k for k in range(1, nv + 1)] +
             ["V_S_All_pH_V%d" % k for k in range(1, nv + 1)] +
             ["V_S_All_Sfioro_V%d" % k for k in range(1, nv + 1)] +
             ["V_S_All_Filtro_V%d" % k for k in range(1, nv + 1)] +
             ["V_S_All_Chim_V%d" % k for k in range(1, nv + 1)] +
             ["V_S_All_Rabbocco_V%d" % k for k in range(1, nv + 1)])
    R.append({"cmt": "SPIA ALLARME CUMULATIVO",
              "chain": [{"or": tutti}, "(V_L_Allarme)"]})
    R.append({"cmt": "CONTEGGIO ALLARMI ATTIVI: azzeramento a ogni scansione",
              "chain": [{"f": "MOVE", "p": {"In": "0",
                                             "OUT:Out": "V_S_Allarmi_Att"}}]})
    for a in tutti:
        R.append({"cmt": "CONTEGGIO ALLARMI: %s" % a,
                  "chain": [a, {"f": "@Inc",
                                "p": {"InOut": "V_S_Allarmi_Att",
                                      "OUT:InOut": "V_S_Allarmi_Att"}}]})
    S["Allarmi"] = R

    # ==================================================== SEZIONE Ausiliari/Log
    R = [
        {"cmt": "BASE TEMPI DEL LOG: un impulso al secondo",
         "chain": ["Mem_Ciclo", "/Tim_Log.Q",
                   {"fb": "TON", "inst": "Tim_Log", "p": {"PT": "T#1s"}}]},
        {"cmt": "LOG: passo di ricetta in corso verso lo SCADA",
         "chain": ["^Tim_Log.Q",
                   {"f": "MOVE", "p": {"In": "V_S_Pos_Robot",
                                        "OUT:Out": "V_S_Passo"}}]},
    ]
    for k in range(1, nv + 1):
        R.append({"cmt": "SEMIAUTOMATICO: carico manuale della vasca %d" % k,
                  "chain": ["V_S_Semiauto", "/Mem_Ciclo", "Consensi",
                            "/IN_Liv_Max_V%d" % k, "IN_DIW_Press",
                            "(S Req_Carico_V%d)" % k]})
    S["Ausiliari"] = R

    return G, I, S


def scenario(nv, in_ricetta=(1, 2, 3)):
    """Collaudo: avviamento servizi, verifica ricetta, un cesto completo sulle
    vasche in ricetta, dosaggio chimico, allarmi e arresto in emergenza."""
    tempi = {"SET_T_Mov": "T#20s"}
    ini = {"IN_Emergenza": False, "IN_Protezioni": True, "IN_Press_Aria": True,
           "IN_Aspirazione": True, "IN_DIW_Press": True, "IN_Termico_Gen": True,
           "IN_Portello_1": True, "IN_Portello_2": True,
           "IN_Robot_Carico": True, "IN_Robot_Scarico": False,
           "IN_Robot_Alto": False, "IN_Robot_Basso": True,
           "IN_Cesto_Presente": False, "IN_Cesto_Carico": True,
           "V_S_Auto": True, "V_S_Semiauto": False,
           "V_S_Ricetta_Sel": 1, "V_S_Cesti_Fatti": 0}
    for k in range(1, nv + 1):
        tempi["SET_T_Perm_V%d" % k] = "T#1s"
        tempi["SET_T_Carico_V%d" % k] = "T#30s"
        tempi["SET_T_Dos_V%d" % k] = "T#1s"
        tempi["SET_T_Rabbocco_V%d" % k] = "T#30s"
        tempi["SET_T_Pausa_Dos_V%d" % k] = "T#2s"
        ini.update({
            "IN_Liv_Min_V%d" % k: True, "IN_Liv_Max_V%d" % k: True,
            "IN_Temp_Ok_V%d" % k: True, "IN_Temp_Alta_V%d" % k: False,
            "IN_Ricircolo_V%d" % k: True, "IN_Robot_Su_V%d" % k: False,
            "IN_Cond_Bassa_V%d" % k: False, "IN_Cond_Alta_V%d" % k: False,
            "IN_pH_Basso_V%d" % k: False, "IN_pH_Alto_V%d" % k: False,
            "IN_Liv_Sfioro_V%d" % k: False, "IN_Filtro_Sporco_V%d" % k: False,
            "IN_Chim_A_Min_V%d" % k: True, "IN_Chim_B_Min_V%d" % k: True,
            "SET_Cicli_Max_V%d" % k: 50, "V_S_Cicli_V%d" % k: 0,
            "V_S_Dosate_V%d" % k: 0,
            "V_S_Passo_V%d" % k: (k if k in in_ricetta else 0),
        })

    P = [
        {"descrizione": "avviamento: servizi presenti, filtro di 2 s non ancora scaduto",
         "set": ini, "impulso": ["V_P_Reset"], "attendi": 0.5,
         "verifica": {"V_L_Ciclo": False, "OUT_Robot_Avanti": False}},
        {"descrizione": "passati i 2 s i consensi ci sono e le vasche sono pronte",
         "attendi": 2.2,
         "verifica": {"V_L_Vasca_Ready_V1": True, "V_L_Vasca_Ready_V2": True,
                      "V_L_Pronto": True, "V_L_Allarme": False}},
        {"descrizione": "ricetta 1 acquisita: solo le vasche 1-3 sono in ricetta",
         "attendi": 0.4,
         "verifica": {"V_S_Ricetta_Att": 1, "V_S_Usa_V1": True,
                      "V_S_Usa_V3": True, "V_S_Usa_V4": False,
                      "V_S_All_Ricetta": False}},
        {"descrizione": "START: il robot chiude la pinza sul cesto",
         "impulso": ["V_P_Start"], "attendi": 0.5,
         "verifica": {"OUT_Pinza_Chiudi": True, "V_L_Fine_Ciclo": False}},
        {"descrizione": "cesto agganciato: il robot sale",
         "set": {"IN_Cesto_Presente": True}, "attendi": 0.4,
         "verifica": {"OUT_Robot_Sale": True}},
        {"descrizione": "robot in alto: trasla verso la prima vasca",
         "set": {"IN_Robot_Alto": True, "IN_Robot_Basso": False,
                 "IN_Robot_Carico": False}, "attendi": 0.4,
         "verifica": {"OUT_Robot_Avanti": True, "V_S_Pos_Target": 1}},
    ]
    for j, k in enumerate(in_ricetta):
        P += [
            {"descrizione": "robot sopra la vasca %d: si ferma e scende" % k,
             "set": {"IN_Robot_Su_V%d" % k: True}, "attendi": 0.4,
             "verifica": {"OUT_Robot_Avanti": False, "OUT_Robot_Scende": True,
                          "V_S_Pos_Robot": k}},
            {"descrizione": "cesto immerso in vasca %d: agitazione e permanenza" % k,
             "set": {"IN_Robot_Alto": False, "IN_Robot_Basso": True},
             "attendi": 0.4,
             "verifica": {"OUT_Robot_Scende": False,
                          "OUT_Agitazione_V%d" % k: True}},
            {"descrizione": "permanenza scaduta in vasca %d: il robot risale" % k,
             "attendi": 1.1,
             "verifica": {"OUT_Robot_Sale": True,
                          "OUT_Agitazione_V%d" % k: False}},
            {"descrizione": "cesto estratto dalla vasca %d" % k,
             "set": {"IN_Robot_Alto": True, "IN_Robot_Basso": False,
                     "IN_Robot_Su_V%d" % k: False}, "attendi": 0.5,
             "verifica": {"OUT_Robot_Sale": False,
                          "V_S_Cicli_V%d" % k: 1}},
        ]
        if j == 0:
            P[-1]["verifica"]["OUT_Robot_Avanti"] = True
    P += [
        {"descrizione": "robot allo scarico: scende e apre la pinza",
         "set": {"IN_Robot_Scarico": True}, "attendi": 0.4,
         "verifica": {"OUT_Robot_Scende": True}},
        {"descrizione": "cesto appoggiato: pinza aperta",
         "set": {"IN_Robot_Alto": False, "IN_Robot_Basso": True},
         "attendi": 0.4,
         "verifica": {"OUT_Pinza_Apri": True}},
        {"descrizione": "cesto rilasciato: ciclo completato, contatore a 1",
         "set": {"IN_Cesto_Presente": False}, "attendi": 0.5,
         "verifica": {"V_L_Fine_Ciclo": True, "V_S_Cesti_Fatti": 1,
                      "V_L_Ciclo": False}},
        # Il secondo cesto e' la prova che conta: e' qui che si vede se i passi
        # del ciclo precedente sono stati davvero azzerati. Senza questo passo
        # il collaudo passava in Python e falliva sull'impianto.
        {"descrizione": "SECONDO CESTO: robot tornato al carico",
         "set": {"IN_Robot_Scarico": False, "IN_Robot_Carico": True,
                 "IN_Robot_Alto": False, "IN_Robot_Basso": True,
                 "IN_Cesto_Carico": True}, "attendi": 0.5,
         "verifica": {"V_L_Ciclo": False}},
        {"descrizione": "SECONDO CESTO: lo START deve far ripartire il ciclo",
         "impulso": ["V_P_Start"], "attendi": 0.6,
         "verifica": {"OUT_Pinza_Chiudi": True, "V_L_Fine_Ciclo": False}},
        {"descrizione": "SECONDO CESTO: agganciato, si riparte dalla vasca 1",
         "set": {"IN_Cesto_Presente": True}, "attendi": 0.4,
         "verifica": {"OUT_Robot_Sale": True}},
        {"descrizione": "SECONDO CESTO: destinazione la prima vasca, non l'ultima",
         "set": {"IN_Robot_Alto": True, "IN_Robot_Basso": False,
                 "IN_Robot_Carico": False}, "attendi": 0.5,
         "verifica": {"OUT_Robot_Avanti": True, "V_S_Pos_Target": 1}},
        {"descrizione": "SECONDO CESTO: interrotto con lo STOP",
         "impulso": ["V_P_Stop"], "attendi": 0.5,
         "verifica": {"V_L_Ciclo": False, "OUT_Robot_Avanti": False}},
        {"descrizione": "conducibilita' bassa in vasca 1: parte la dosata A",
         "set": {"IN_Cond_Bassa_V1": True, "IN_Liv_Max_V1": False},
         "attendi": 0.5,
         "verifica": {"OUT_Dos_A_V1": True}},
        {"descrizione": "dosata A conclusa dopo 1 s: contatore dosate a 1",
         "attendi": 1.2,
         "verifica": {"OUT_Dos_A_V1": False, "V_S_Dosate_V1": 1}},
        {"descrizione": "tanica del chimico A vuota: alla dosata successiva scatta l'allarme",
         "set": {"IN_Chim_A_Min_V1": False}, "attendi": 2.8,
         "verifica": {"V_S_All_Chim_V1": True, "OUT_Dos_A_V1": False,
                      "V_L_Allarme": True}},
        {"descrizione": "pH basso in vasca 2: parte la dosata B",
         "set": {"IN_pH_Basso_V2": True, "IN_Liv_Max_V2": False},
         "attendi": 0.5,
         "verifica": {"OUT_Dos_B_V2": True}},
        {"descrizione": "sfioro in vasca 3: allarme e chiusura del rabbocco",
         "set": {"IN_Liv_Sfioro_V3": True}, "attendi": 0.5,
         "verifica": {"V_S_All_Sfioro_V3": True, "OUT_Rabbocco_V3": False}},
        {"descrizione": "filtro intasato in vasca 4: allarme filtro",
         "set": {"IN_Filtro_Sporco_V4": True}, "attendi": 0.5,
         "verifica": {"V_S_All_Filtro_V4": True}},
        {"descrizione": "sovratemperatura in vasca 5: riscaldamento tolto",
         "set": {"IN_Temp_Alta_V5": True, "IN_Temp_Ok_V5": False},
         "attendi": 0.5,
         "verifica": {"V_S_All_TempAlta_V5": True, "OUT_Risc_V5": False}},
        {"descrizione": "ricircolo assente in vasca 6: dopo 10 s allarme",
         "set": {"IN_Ricircolo_V6": False}, "attendi": 10.6,
         "verifica": {"V_S_All_Ricircolo_V6": True}},
        {"descrizione": "RESET generale con i guasti ancora presenti: restano",
         "impulso": ["V_P_Reset"], "attendi": 0.6,
         "verifica": {"V_S_All_Sfioro_V3": True, "V_L_Allarme": True}},
        {"descrizione": "guasti rimossi e RESET: allarmi rientrati",
         "set": {"IN_Chim_A_Min_V1": True, "IN_Liv_Sfioro_V3": False,
                 "IN_Filtro_Sporco_V4": False, "IN_Temp_Alta_V5": False,
                 "IN_Temp_Ok_V5": True, "IN_Ricircolo_V6": True,
                 "IN_Cond_Bassa_V1": False, "IN_pH_Basso_V2": False},
         "impulso": ["V_P_Reset"], "attendi": 0.8,
         "verifica": {"V_S_All_Sfioro_V3": False, "V_S_All_Chim_V1": False,
                      "V_S_All_Filtro_V4": False,
                      "V_S_All_TempAlta_V5": False,
                      "V_S_All_Ricircolo_V6": False, "V_L_Allarme": False}},
        {"descrizione": "portello aperto fuori ciclo: nessun allarme",
         "set": {"IN_Portello_1": False}, "attendi": 0.5,
         "verifica": {"V_S_All_Portello": False,
                      "OUT_Blocco_Portelli": False}},
        {"descrizione": "EMERGENZA: cadono tutti i comandi",
         "set": {"IN_Portello_1": True, "IN_Emergenza": True}, "attendi": 0.6,
         "verifica": {"OUT_Robot_Avanti": False, "OUT_Robot_Indietro": False,
                      "OUT_Robot_Sale": False, "OUT_Robot_Scende": False,
                      "OUT_Pompa_V1": False, "OUT_Risc_V1": False,
                      "OUT_Agitazione_V1": False,
                      "V_S_All_Emergenza": True, "V_L_Allarme": True,
                      "V_L_Pronto": False}},
    ]
    return {"nome": "Wetbench CFE %d vasche - collaudo" % nv,
            "tempi": tempi, "passi": P}


def main():
    nv = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    G, I, S = costruisci(nv)
    tot = sum(len(v) for v in S.values())
    spec = {"out_dir": os.path.join(D, "out"),
            "variables": [{"name": a, "type": b, "comment": c} for a, b, c in I],
            "sections": S}
    json.dump(spec, open(os.path.join(D, "cfe_spec.json"), "w", encoding="utf-8"),
              indent=1, ensure_ascii=False)
    for suffisso, dati in (("globali", G), ("interne", I)):
        with open(os.path.join(D, "cfe_%s.txt" % suffisso), "w",
                  encoding="utf-8") as f:
            for a, b, c in dati:
                f.write("%s\t%s\t%s\n" % (a, b, c))
    with open(os.path.join(D, "cfe_esterne.txt"), "w", encoding="utf-8") as f:
        for a, _b, _c in G:
            f.write("%s\n" % a)
    sc = scenario(nv)
    json.dump(sc, open(os.path.join(D, "cfe_scenario.json"), "w",
                       encoding="utf-8"), indent=1, ensure_ascii=False)
    glob = set(a for a, _b, _c in G)
    sc_s = json.loads(json.dumps(sc))
    for p in sc_s["passi"]:
        if "verifica" in p:
            p["verifica"] = {k: v for k, v in p["verifica"].items() if k in glob}
    json.dump(sc_s, open(os.path.join(D, "cfe_scenario_sysmac.json"), "w",
                         encoding="utf-8"), indent=1, ensure_ascii=False)
    print("vasche %d -> %d rung in %d sezioni | globali %d | interne %d"
          % (nv, tot, len(S), len(G), len(I)))
    for n, v in S.items():
        print("   %4d  %s" % (len(v), n))


if __name__ == "__main__":
    main()
