# -*- coding: utf-8 -*-
"""
genera_semaforo.py - spec ladder per la gestione di un incrocio stradale
28/08/2026

INCROCIO A DUE DIREZIONI: NS (Nord-Sud) e EO (Est-Ovest), con attraversamenti
pedonali su entrambe.

MODALITA'
  AUTOMATICO  ciclo a 6 fasi (i due "tutto rosso" sono di sicurezza)
  NOTTE       giallo lampeggiante in tutte le direzioni (V_S_Notte)
  EMERGENZA   tutto rosso (IN_Emergenza o guasto di una lampada rossa)

CICLO
  F1  verde NS   / rosso EO    SET_T_Verde_NS   (25 s)   + verde pedonale EO
  F2  giallo NS  / rosso EO    SET_T_Giallo     (3 s)
  F3  tutto rosso              SET_T_TuttoRosso (2 s)
  F4  rosso NS   / verde EO    SET_T_Verde_EO   (20 s)   + verde pedonale NS
  F5  rosso NS   / giallo EO   SET_T_Giallo     (3 s)
  F6  tutto rosso              SET_T_TuttoRosso (2 s)  -> torna a F1

PEDONI
  La chiamata (V_P_Chiam_Ped_NS/EO) accende la spia di prenotazione e, se il
  verde della direzione opposta e' gia' durato il minimo (Tim_F1min/F4min),
  ne anticipa la fine. Il verde pedonale di una direzione coincide con il
  verde veicolare della direzione trasversale.

Uso:  python genera_semaforo.py     -> semaforo_spec.json + elenco variabili
"""
import json, os

D = os.path.dirname(os.path.abspath(__file__))

# --------------------------------------------------------------- variabili
GLOBALI = [
    # comandi e stato impianto
    ("IN_Marcia", "BOOL", "selettore di marcia impianto"),
    ("IN_Emergenza", "BOOL", "fungo di emergenza (contatto NA: TRUE = premuto)"),
    ("IN_Guasto_Rosso_NS", "BOOL", "guasto lampada rossa NS"),
    ("IN_Guasto_Rosso_EO", "BOOL", "guasto lampada rossa EO"),
    ("V_S_Auto", "BOOL", "selettore AUTOMATICO da SCADA"),
    ("V_S_Notte", "BOOL", "selettore NOTTE: giallo lampeggiante"),
    ("V_P_Chiam_Ped_NS", "BOOL", "pulsante pedonale attraversamento NS"),
    ("V_P_Chiam_Ped_EO", "BOOL", "pulsante pedonale attraversamento EO"),
    # tempi (ritentivi: impostabili da SCADA)
    ("SET_T_Verde_NS", "TIME", "durata verde Nord-Sud"),
    ("SET_T_Verde_EO", "TIME", "durata verde Est-Ovest"),
    ("SET_T_Giallo", "TIME", "durata giallo"),
    ("SET_T_TuttoRosso", "TIME", "sicurezza: tutto rosso fra le fasi"),
    ("SET_T_Verde_Min", "TIME", "verde minimo prima di accettare la chiamata pedonale"),
    # uscite lampade veicolari
    ("OUT_NS_Rosso", "BOOL", "lampada rossa Nord-Sud"),
    ("OUT_NS_Giallo", "BOOL", "lampada gialla Nord-Sud"),
    ("OUT_NS_Verde", "BOOL", "lampada verde Nord-Sud"),
    ("OUT_EO_Rosso", "BOOL", "lampada rossa Est-Ovest"),
    ("OUT_EO_Giallo", "BOOL", "lampada gialla Est-Ovest"),
    ("OUT_EO_Verde", "BOOL", "lampada verde Est-Ovest"),
    # uscite pedonali
    ("OUT_Ped_NS_Rosso", "BOOL", "pedonale NS rosso"),
    ("OUT_Ped_NS_Verde", "BOOL", "pedonale NS verde"),
    ("OUT_Ped_EO_Rosso", "BOOL", "pedonale EO rosso"),
    ("OUT_Ped_EO_Verde", "BOOL", "pedonale EO verde"),
    # segnalazioni
    ("V_L_Ciclo_Attivo", "BOOL", "spia impianto in ciclo"),
    ("V_L_Notte", "BOOL", "spia modalita notte"),
    ("V_L_Emergenza", "BOOL", "spia emergenza / tutto rosso"),
    ("V_L_Ped_NS_Prenotato", "BOOL", "spia chiamata pedonale NS"),
    ("V_L_Ped_EO_Prenotato", "BOOL", "spia chiamata pedonale EO"),
    ("V_S_Cicli_Completati", "INT", "contatore cicli completati"),
]

INTERNE = [
    ("Clock_1s", "BOOL", "clock 1 s di sistema"),
    ("Mem_Ciclo", "BOOL", "impianto in ciclo automatico"),
    ("Mem_F1", "BOOL", "fase 1: verde NS"),
    ("Mem_F2", "BOOL", "fase 2: giallo NS"),
    ("Mem_F3", "BOOL", "fase 3: tutto rosso"),
    ("Mem_F4", "BOOL", "fase 4: verde EO"),
    ("Mem_F5", "BOOL", "fase 5: giallo EO"),
    ("Mem_F6", "BOOL", "fase 6: tutto rosso"),
    ("Mem_Ped_NS", "BOOL", "chiamata pedonale NS prenotata"),
    ("Mem_Ped_EO", "BOOL", "chiamata pedonale EO prenotata"),
    ("Mem_Emergenza", "BOOL", "condizione di emergenza attiva"),
    ("Tim_F1", "TON", "durata fase 1"),
    ("Tim_F2", "TON", "durata fase 2"),
    ("Tim_F3", "TON", "durata fase 3"),
    ("Tim_F4", "TON", "durata fase 4"),
    ("Tim_F5", "TON", "durata fase 5"),
    ("Tim_F6", "TON", "durata fase 6"),
    ("Tim_F1min", "TON", "verde minimo fase 1"),
    ("Tim_F4min", "TON", "verde minimo fase 4"),
]

# ------------------------------------------------------------------ rung
def ton(inst, pt):
    return {"fb": "TON", "inst": inst, "p": {"PT": pt}}

RUNG = [
    {"cmt": "CLOCK 1 SECONDO (lampeggio giallo notturno)",
     "chain": ["P_On", {"f": "Get1sClk", "p": {}}, "(Clock_1s)"]},

    {"cmt": "EMERGENZA: fungo premuto o lampada rossa guasta",
     "chain": [{"or": ["IN_Emergenza", "IN_Guasto_Rosso_NS", "IN_Guasto_Rosso_EO"]},
               "(Mem_Emergenza)"]},

    {"cmt": "CONSENSO AL CICLO AUTOMATICO",
     "chain": ["IN_Marcia", "V_S_Auto", "/V_S_Notte", "/Mem_Emergenza", "(Mem_Ciclo)"]},

    {"cmt": "PARTENZA CICLO DALLA FASE 1",
     "chain": ["Mem_Ciclo",
               "/Mem_F1", "/Mem_F2", "/Mem_F3", "/Mem_F4", "/Mem_F5", "/Mem_F6",
               "(S Mem_F1)"]},

    {"cmt": "ARRESTO CICLO: azzera tutte le fasi",
     "chain": ["/Mem_Ciclo",
               "out"],
     "out": [["(R Mem_F1)"], ["(R Mem_F2)"], ["(R Mem_F3)"],
             ["(R Mem_F4)"], ["(R Mem_F5)"], ["(R Mem_F6)"]]},

    # --- fase 1: verde NS -------------------------------------------------
    {"cmt": "FASE 1 - VERDE NORD-SUD: durata e verde minimo",
     "chain": ["Mem_F1"],
     "out": [[ton("Tim_F1", "SET_T_Verde_NS")], [ton("Tim_F1min", "SET_T_Verde_Min")]]},

    {"cmt": "FINE FASE 1 -> FASE 2 (anticipata dalla chiamata pedonale NS)",
     "chain": ["Mem_F1",
               {"or": ["Tim_F1.Q", ["Mem_Ped_NS", "Tim_F1min.Q"]]}],
     "out": [["(R Mem_F1)"], ["(S Mem_F2)"], ["(R Mem_Ped_NS)"]]},

    # --- fase 2: giallo NS ------------------------------------------------
    {"cmt": "FASE 2 - GIALLO NORD-SUD",
     "chain": ["Mem_F2", ton("Tim_F2", "SET_T_Giallo")]},
    {"cmt": "FINE FASE 2 -> FASE 3",
     "chain": ["Mem_F2", "Tim_F2.Q"],
     "out": [["(R Mem_F2)"], ["(S Mem_F3)"]]},

    # --- fase 3: tutto rosso ---------------------------------------------
    {"cmt": "FASE 3 - TUTTO ROSSO DI SICUREZZA",
     "chain": ["Mem_F3", ton("Tim_F3", "SET_T_TuttoRosso")]},
    {"cmt": "FINE FASE 3 -> FASE 4",
     "chain": ["Mem_F3", "Tim_F3.Q"],
     "out": [["(R Mem_F3)"], ["(S Mem_F4)"]]},

    # --- fase 4: verde EO -------------------------------------------------
    {"cmt": "FASE 4 - VERDE EST-OVEST: durata e verde minimo",
     "chain": ["Mem_F4"],
     "out": [[ton("Tim_F4", "SET_T_Verde_EO")], [ton("Tim_F4min", "SET_T_Verde_Min")]]},

    {"cmt": "FINE FASE 4 -> FASE 5 (anticipata dalla chiamata pedonale EO)",
     "chain": ["Mem_F4",
               {"or": ["Tim_F4.Q", ["Mem_Ped_EO", "Tim_F4min.Q"]]}],
     "out": [["(R Mem_F4)"], ["(S Mem_F5)"], ["(R Mem_Ped_EO)"]]},

    # --- fase 5: giallo EO ------------------------------------------------
    {"cmt": "FASE 5 - GIALLO EST-OVEST",
     "chain": ["Mem_F5", ton("Tim_F5", "SET_T_Giallo")]},
    {"cmt": "FINE FASE 5 -> FASE 6",
     "chain": ["Mem_F5", "Tim_F5.Q"],
     "out": [["(R Mem_F5)"], ["(S Mem_F6)"]]},

    # --- fase 6: tutto rosso e chiusura ciclo -----------------------------
    {"cmt": "FASE 6 - TUTTO ROSSO DI SICUREZZA",
     "chain": ["Mem_F6", ton("Tim_F6", "SET_T_TuttoRosso")]},
    {"cmt": "FINE FASE 6 -> FASE 1: ciclo completato",
     "chain": ["Mem_F6", "Tim_F6.Q"],
     "out": [["(R Mem_F6)"], ["(S Mem_F1)"],
             [{"f": "@Inc", "p": {"InOut": "V_S_Cicli_Completati",
                                   "OUT:InOut": "V_S_Cicli_Completati"}}]]},

    # --- chiamate pedonali ------------------------------------------------
    {"cmt": "CHIAMATA PEDONALE NORD-SUD",
     "chain": ["^V_P_Chiam_Ped_NS", "(S Mem_Ped_NS)"]},
    {"cmt": "CHIAMATA PEDONALE EST-OVEST",
     "chain": ["^V_P_Chiam_Ped_EO", "(S Mem_Ped_EO)"]},
    {"cmt": "SPIE DI PRENOTAZIONE PEDONALE",
     "chain": ["Mem_Ped_NS", "(V_L_Ped_NS_Prenotato)"]},
    {"cmt": "SPIA PRENOTAZIONE PEDONALE EST-OVEST",
     "chain": ["Mem_Ped_EO", "(V_L_Ped_EO_Prenotato)"]},

    # --- lampade veicolari ------------------------------------------------
    {"cmt": "VERDE NORD-SUD",
     "chain": ["Mem_F1", "(OUT_NS_Verde)"]},
    {"cmt": "GIALLO NORD-SUD (anche lampeggiante di notte)",
     "chain": [{"or": ["Mem_F2", ["V_S_Notte", "Clock_1s"]]}, "(OUT_NS_Giallo)"]},
    {"cmt": "ROSSO NORD-SUD (tutte le fasi in cui NS e' fermo, ed emergenza)",
     "chain": [{"or": ["Mem_F3", "Mem_F4", "Mem_F5", "Mem_F6", "Mem_Emergenza"]},
               "/V_S_Notte", "(OUT_NS_Rosso)"]},

    {"cmt": "VERDE EST-OVEST",
     "chain": ["Mem_F4", "(OUT_EO_Verde)"]},
    {"cmt": "GIALLO EST-OVEST (anche lampeggiante di notte)",
     "chain": [{"or": ["Mem_F5", ["V_S_Notte", "Clock_1s"]]}, "(OUT_EO_Giallo)"]},
    {"cmt": "ROSSO EST-OVEST (tutte le fasi in cui EO e' fermo, ed emergenza)",
     "chain": [{"or": ["Mem_F1", "Mem_F2", "Mem_F3", "Mem_F6", "Mem_Emergenza"]},
               "/V_S_Notte", "(OUT_EO_Rosso)"]},

    # --- lampade pedonali -------------------------------------------------
    {"cmt": "PEDONALE NORD-SUD VERDE (si attraversa NS mentre i veicoli EO vanno)",
     "chain": ["Mem_F4", "/Mem_Emergenza", "(OUT_Ped_NS_Verde)"]},
    {"cmt": "PEDONALE NORD-SUD ROSSO",
     "chain": ["/Mem_F4", "(OUT_Ped_NS_Rosso)"]},
    {"cmt": "PEDONALE EST-OVEST VERDE (si attraversa EO mentre i veicoli NS vanno)",
     "chain": ["Mem_F1", "/Mem_Emergenza", "(OUT_Ped_EO_Verde)"]},
    {"cmt": "PEDONALE EST-OVEST ROSSO",
     "chain": ["/Mem_F1", "(OUT_Ped_EO_Rosso)"]},

    # --- segnalazioni -----------------------------------------------------
    {"cmt": "SPIA CICLO ATTIVO",
     "chain": ["Mem_Ciclo", "(V_L_Ciclo_Attivo)"]},
    {"cmt": "SPIA MODALITA NOTTE",
     "chain": ["V_S_Notte", "(V_L_Notte)"]},
    {"cmt": "SPIA EMERGENZA",
     "chain": ["Mem_Emergenza", "(V_L_Emergenza)"]},
]


def main():
    # il rung "ARRESTO CICLO" usa il segnaposto "out" nella catena: lo tolgo
    for r in RUNG:
        if r.get("chain") and r["chain"][-1] == "out":
            r["chain"] = r["chain"][:-1]

    spec = {
        "out_dir": os.path.join(r"C:\Users\tecni\Claude\sysmac-mcp", "out"),
        "variables": [{"name": n, "type": t, "comment": c} for n, t, c in INTERNE],
        "sections": {"Semaforo": RUNG},
    }
    dest = os.path.join(r"C:\Users\tecni\Claude\sysmac-mcp", "semaforo_spec.json")
    json.dump(spec, open(dest, "w", encoding="utf-8"), indent=1, ensure_ascii=False)

    # elenchi variabili pronti per sysmac_vars / vars_offline
    with open(os.path.join(r"C:\Users\tecni\Claude\sysmac-mcp", "semaforo_globali.txt"),
              "w", encoding="utf-8") as f:
        for n, t, c in GLOBALI:
            f.write("%s\t%s\t%s\n" % (n, t, c))
    with open(os.path.join(r"C:\Users\tecni\Claude\sysmac-mcp", "semaforo_interne.txt"),
              "w", encoding="utf-8") as f:
        for n, t, c in INTERNE:
            f.write("%s\t%s\t%s\n" % (n, t, c))
    with open(os.path.join(r"C:\Users\tecni\Claude\sysmac-mcp", "semaforo_esterne.txt"),
              "w", encoding="utf-8") as f:
        for n, _t, _c in GLOBALI:
            f.write("%s\n" % n)

    print("spec:", dest)
    print("rung:", len(RUNG))
    print("globali:", len(GLOBALI), "| interne:", len(INTERNE))


if __name__ == "__main__":
    main()
