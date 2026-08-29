# -*- coding: utf-8 -*-
"""
genera_nastro.py - nastro trasportatore con conteggio e scarto pezzi
Esercizio 1 (28/08/2026): misura dei tempi con il metodo attuale.

IMPIANTO
  Nastro comandato da inverter (marcia/arresto + consenso velocita').
  Fotocellula di conteggio all'ingresso, sensore di presenza in uscita,
  deviatore di scarto comandato dal controllo qualita'.
  Ciclo: marcia -> conta i pezzi -> a lotto completo ferma e segnala.

FUNZIONI
  - marcia/arresto con ritenuta e consensi (emergenza, protezioni, aria)
  - conteggio pezzi in transito (fronte della fotocellula)
  - lotto: raggiunto SET_Pezzi_Lotto ferma il nastro e accende la spia
  - scarto: se IN_Qualita_KO e' basso al passaggio, devia il pezzo per
    SET_T_Deviatore e incrementa il contatore scarti
  - allarme inceppamento: pezzo presente in uscita per piu' di SET_T_Inceppo
  - reset conteggi da SCADA
"""
import json, os

D = r"C:\Users\tecni\Claude\sysmac-mcp"

GLOBALI = [
    ("IN_Emergenza", "BOOL", "fungo di emergenza premuto"),
    ("IN_Protezioni", "BOOL", "protezioni chiuse (NC: TRUE = ok)"),
    ("IN_Press_Aria", "BOOL", "pressostato aria ok"),
    ("IN_Foto_Ingresso", "BOOL", "fotocellula conteggio pezzi"),
    ("IN_Pres_Uscita", "BOOL", "sensore presenza pezzo in uscita"),
    ("IN_Qualita_KO", "BOOL", "esito controllo qualita': TRUE = pezzo da scartare"),
    ("V_P_Start", "BOOL", "pulsante START da SCADA"),
    ("V_P_Stop", "BOOL", "pulsante STOP da SCADA"),
    ("V_P_Reset_Conteggi", "BOOL", "azzera i contatori"),
    ("SET_Pezzi_Lotto", "INT", "pezzi per lotto"),
    ("SET_T_Deviatore", "TIME", "durata comando deviatore di scarto"),
    ("SET_T_Inceppo", "TIME", "tempo oltre il quale il pezzo in uscita e' inceppato"),
    ("OUT_Nastro_Marcia", "BOOL", "comando marcia inverter nastro"),
    ("OUT_Deviatore", "BOOL", "elettrovalvola deviatore di scarto"),
    ("V_L_Ciclo", "BOOL", "spia ciclo in corso"),
    ("V_L_Lotto_Completo", "BOOL", "spia lotto completato"),
    ("V_L_Allarme", "BOOL", "spia allarme cumulativo"),
    ("V_S_Pezzi_Contati", "INT", "pezzi transitati"),
    ("V_S_Pezzi_Scartati", "INT", "pezzi deviati allo scarto"),
    ("V_S_Allarme_Inceppo", "BOOL", "allarme inceppamento in uscita"),
]

INTERNE = [
    ("Mem_Ciclo", "BOOL", "nastro in ciclo"),
    ("Consensi", "BOOL", "consensi di sicurezza presenti"),
    ("Mem_Lotto_Pieno", "BOOL", "lotto completato"),
    ("Mem_Scarto", "BOOL", "scarto in corso"),
    ("Tim_Deviatore", "TON", "durata comando deviatore"),
    ("Tim_Inceppo", "TON", "sorveglianza inceppamento"),
]

RUNG = [
    {"cmt": "CONSENSI DI SICUREZZA (emergenza, protezioni, aria)",
     "chain": ["/IN_Emergenza", "IN_Protezioni", "IN_Press_Aria", "(Consensi)"]},

    {"cmt": "START CICLO",
     "chain": ["^V_P_Start", "Consensi", "/Mem_Lotto_Pieno", "(S Mem_Ciclo)"]},

    {"cmt": "ARRESTO CICLO: stop, mancanza consensi, lotto completo o inceppamento",
     "chain": [{"or": ["^V_P_Stop", "/Consensi", "Mem_Lotto_Pieno", "V_S_Allarme_Inceppo"]},
               "(R Mem_Ciclo)"]},

    {"cmt": "COMANDO MARCIA NASTRO",
     "chain": ["Mem_Ciclo", "Consensi", "(OUT_Nastro_Marcia)"]},

    {"cmt": "CONTEGGIO PEZZI IN TRANSITO (fronte della fotocellula)",
     "chain": ["^IN_Foto_Ingresso", "Mem_Ciclo",
               {"f": "@Inc", "p": {"InOut": "V_S_Pezzi_Contati",
                                    "OUT:InOut": "V_S_Pezzi_Contati"}}]},

    {"cmt": "PEZZO DA SCARTARE: memorizza al passaggio in fotocellula",
     "chain": ["^IN_Foto_Ingresso", "IN_Qualita_KO", "Mem_Ciclo"],
     "out": [["(S Mem_Scarto)"],
             [{"f": "@Inc", "p": {"InOut": "V_S_Pezzi_Scartati",
                                   "OUT:InOut": "V_S_Pezzi_Scartati"}}]]},

    {"cmt": "TEMPO DI DEVIAZIONE ALLO SCARTO",
     "chain": ["Mem_Scarto", {"fb": "TON", "inst": "Tim_Deviatore",
                              "p": {"PT": "SET_T_Deviatore"}}]},

    {"cmt": "COMANDO DEVIATORE",
     "chain": ["Mem_Scarto", "(OUT_Deviatore)"]},

    {"cmt": "FINE DEVIAZIONE",
     "chain": ["Tim_Deviatore.Q", "(R Mem_Scarto)"]},

    {"cmt": "LOTTO COMPLETATO: pezzi contati >= pezzi impostati",
     "chain": [{"f": ">=", "p": {"In1": "V_S_Pezzi_Contati", "In2": "SET_Pezzi_Lotto"}},
               "Mem_Ciclo", "(S Mem_Lotto_Pieno)"]},

    {"cmt": "SORVEGLIANZA INCEPPAMENTO IN USCITA",
     "chain": ["IN_Pres_Uscita", "Mem_Ciclo",
               {"fb": "TON", "inst": "Tim_Inceppo", "p": {"PT": "SET_T_Inceppo"}}]},

    {"cmt": "ALLARME INCEPPAMENTO",
     "chain": ["Tim_Inceppo.Q", "(S V_S_Allarme_Inceppo)"]},

    {"cmt": "RESET CONTEGGI E ALLARMI DA SCADA",
     "chain": ["^V_P_Reset_Conteggi"],
     "out": [["(R Mem_Lotto_Pieno)"], ["(R V_S_Allarme_Inceppo)"],
             [{"f": "MOVE", "p": {"In": "0", "OUT:Out": "V_S_Pezzi_Contati"}}],
             [{"f": "MOVE", "p": {"In": "0", "OUT:Out": "V_S_Pezzi_Scartati"}}]]},

    {"cmt": "SPIA CICLO", "chain": ["Mem_Ciclo", "(V_L_Ciclo)"]},
    {"cmt": "SPIA LOTTO COMPLETO", "chain": ["Mem_Lotto_Pieno", "(V_L_Lotto_Completo)"]},
    {"cmt": "SPIA ALLARME CUMULATIVO",
     "chain": [{"or": ["V_S_Allarme_Inceppo", "/Consensi"]}, "(V_L_Allarme)"]},
]


def main():
    spec = {"out_dir": os.path.join(D, "out"),
            "variables": [{"name": n, "type": t, "comment": c} for n, t, c in INTERNE],
            "sections": {"Nastro": RUNG}}
    json.dump(spec, open(os.path.join(D, "nastro_spec.json"), "w", encoding="utf-8"),
              indent=1, ensure_ascii=False)
    for nome, dati in (("nastro_globali.txt", GLOBALI), ("nastro_interne.txt", INTERNE)):
        with open(os.path.join(D, nome), "w", encoding="utf-8") as f:
            for n, t, c in dati:
                f.write("%s\t%s\t%s\n" % (n, t, c))
    with open(os.path.join(D, "nastro_esterne.txt"), "w", encoding="utf-8") as f:
        for n, _t, _c in GLOBALI:
            f.write("%s\n" % n)
    print("rung:", len(RUNG), "| globali:", len(GLOBALI), "| interne:", len(INTERNE))


if __name__ == "__main__":
    main()
