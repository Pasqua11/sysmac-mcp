# -*- coding: utf-8 -*-
"""
genera_pompe.py - gestione di due pompe con alternanza, riserva e ore di marcia
Esercizio 2 (28/08/2026): stesso giro dell'esercizio 1, ma partendo dal
progetto template. Serve a misurare il guadagno.

IMPIANTO (ricorre negli scrubber e nei lavaggi SYNTECH)
  Due pompe sullo stesso collettore. Una lavora, l'altra e' di riserva.
  Livello vasca con due sonde (minimo e massimo). Pressostato di mandata.

FUNZIONI
  - richiesta di marcia dal livello: parte al minimo, si ferma al massimo
  - alternanza a ogni avvio: lavora la pompa che ha meno ore
  - riserva: se la pompa in marcia non fa pressione entro SET_T_Pressione,
    la si ferma, si segnala il guasto e parte l'altra
  - marcia a secco: livello sotto il minimo per SET_T_Secco -> blocco
  - conteggio ore di marcia per pompa (impulso al minuto)
  - reset allarmi
"""
import json, os

D = r"C:\Users\tecni\Claude\sysmac-mcp"

# le variabili di impianto standard (IN_Emergenza, V_P_Start, ...) sono gia'
# nel template SYNTECH: qui solo quelle specifiche dell'impianto pompe
GLOBALI = [
    ("IN_Livello_Min", "BOOL", "sonda livello minimo vasca"),
    ("IN_Livello_Max", "BOOL", "sonda livello massimo vasca"),
    ("IN_Press_Mandata", "BOOL", "pressostato di mandata"),
    ("IN_Termico_P1", "BOOL", "termico pompa 1 (NC: TRUE = ok)"),
    ("IN_Termico_P2", "BOOL", "termico pompa 2 (NC: TRUE = ok)"),
    ("V_S_Pompa_Manuale", "INT", "0 = alternanza, 1 = solo P1, 2 = solo P2"),
    ("SET_T_Pressione", "TIME", "attesa pressione di mandata prima del guasto"),
    ("SET_T_Secco", "TIME", "marcia a secco tollerata"),
    ("OUT_Pompa_1", "BOOL", "contattore pompa 1"),
    ("OUT_Pompa_2", "BOOL", "contattore pompa 2"),
    ("V_S_Ore_P1", "INT", "minuti di marcia pompa 1"),
    ("V_S_Ore_P2", "INT", "minuti di marcia pompa 2"),
    ("V_S_Guasto_P1", "BOOL", "pompa 1 in guasto"),
    ("V_S_Guasto_P2", "BOOL", "pompa 2 in guasto"),
    ("V_S_Marcia_Secco", "BOOL", "allarme marcia a secco"),
    ("V_L_P1_Marcia", "BOOL", "spia pompa 1 in marcia"),
    ("V_L_P2_Marcia", "BOOL", "spia pompa 2 in marcia"),
]

INTERNE = [
    ("Mem_Richiesta", "BOOL", "richiesta di pompaggio dal livello"),
    ("Mem_P1_Sel", "BOOL", "tocca alla pompa 1"),
    ("Mem_P2_Sel", "BOOL", "tocca alla pompa 2"),
    ("Tim_Press_P1", "TON", "attesa pressione con pompa 1 in marcia"),
    ("Tim_Press_P2", "TON", "attesa pressione con pompa 2 in marcia"),
    ("Tim_Secco", "TON", "marcia a secco"),
    ("Tim_Minuto", "TON", "base tempi per le ore di marcia"),
]

RUNG = [
    {"cmt": "CONSENSI DI SICUREZZA",
     "chain": ["/IN_Emergenza", "IN_Protezioni", "(Consensi)"]},

    {"cmt": "RICHIESTA DI POMPAGGIO: parte al livello minimo",
     "chain": ["/IN_Livello_Min", "Consensi", "V_S_Auto", "(S Mem_Richiesta)"]},

    {"cmt": "FINE POMPAGGIO: livello massimo raggiunto o consensi caduti",
     "chain": [{"or": ["IN_Livello_Max", "/Consensi", "/V_S_Auto"]}, "(R Mem_Richiesta)"]},

    {"cmt": "ALTERNANZA: alla richiesta tocca alla pompa con meno minuti",
     "chain": ["^Mem_Richiesta",
               {"f": "<=", "p": {"In1": "V_S_Ore_P1", "In2": "V_S_Ore_P2"}},
               "/V_S_Guasto_P1", "IN_Termico_P1"],
     "out": [["(S Mem_P1_Sel)"], ["(R Mem_P2_Sel)"]]},

    {"cmt": "ALTERNANZA: altrimenti tocca alla pompa 2",
     "chain": ["^Mem_Richiesta",
               {"f": ">", "p": {"In1": "V_S_Ore_P1", "In2": "V_S_Ore_P2"}},
               "/V_S_Guasto_P2", "IN_Termico_P2"],
     "out": [["(S Mem_P2_Sel)"], ["(R Mem_P1_Sel)"]]},

    {"cmt": "SELEZIONE MANUALE POMPA 1 DA SCADA",
     "chain": [{"f": "=", "p": {"In1": "V_S_Pompa_Manuale", "In2": "1"}}],
     "out": [["(S Mem_P1_Sel)"], ["(R Mem_P2_Sel)"]]},

    {"cmt": "SELEZIONE MANUALE POMPA 2 DA SCADA",
     "chain": [{"f": "=", "p": {"In1": "V_S_Pompa_Manuale", "In2": "2"}}],
     "out": [["(S Mem_P2_Sel)"], ["(R Mem_P1_Sel)"]]},

    {"cmt": "COMANDO POMPA 1",
     "chain": ["Mem_Richiesta", "Mem_P1_Sel", "Consensi", "IN_Termico_P1",
               "/V_S_Guasto_P1", "/V_S_Marcia_Secco", "(OUT_Pompa_1)"]},

    {"cmt": "COMANDO POMPA 2",
     "chain": ["Mem_Richiesta", "Mem_P2_Sel", "Consensi", "IN_Termico_P2",
               "/V_S_Guasto_P2", "/V_S_Marcia_Secco", "(OUT_Pompa_2)"]},

    {"cmt": "SORVEGLIANZA PRESSIONE, POMPA 1 (un timer per pompa: quello unico"
            " lasciava alla riserva il tempo gia' scaduto)",
     "chain": ["OUT_Pompa_1", "/IN_Press_Mandata",
               {"fb": "TON", "inst": "Tim_Press_P1", "p": {"PT": "SET_T_Pressione"}}]},

    {"cmt": "SORVEGLIANZA PRESSIONE, POMPA 2",
     "chain": ["OUT_Pompa_2", "/IN_Press_Mandata",
               {"fb": "TON", "inst": "Tim_Press_P2", "p": {"PT": "SET_T_Pressione"}}]},

    {"cmt": "GUASTO POMPA 1: niente pressione o termico intervenuto",
     "chain": [{"or": ["Tim_Press_P1.Q", "/IN_Termico_P1"]},
               "(S V_S_Guasto_P1)"]},

    {"cmt": "GUASTO POMPA 2: niente pressione o termico intervenuto",
     "chain": [{"or": ["Tim_Press_P2.Q", "/IN_Termico_P2"]},
               "(S V_S_Guasto_P2)"]},

    {"cmt": "PASSAGGIO ALLA RISERVA: se P1 e' guasta tocca a P2",
     "chain": ["V_S_Guasto_P1", "Mem_Richiesta", "/V_S_Guasto_P2", "IN_Termico_P2"],
     "out": [["(S Mem_P2_Sel)"], ["(R Mem_P1_Sel)"]]},

    {"cmt": "PASSAGGIO ALLA RISERVA: se P2 e' guasta tocca a P1",
     "chain": ["V_S_Guasto_P2", "Mem_Richiesta", "/V_S_Guasto_P1", "IN_Termico_P1"],
     "out": [["(S Mem_P1_Sel)"], ["(R Mem_P2_Sel)"]]},

    {"cmt": "MARCIA A SECCO: livello sotto il minimo con pompa in marcia",
     "chain": [{"or": ["OUT_Pompa_1", "OUT_Pompa_2"]}, "/IN_Livello_Min",
               {"fb": "TON", "inst": "Tim_Secco", "p": {"PT": "SET_T_Secco"}}]},

    {"cmt": "ALLARME MARCIA A SECCO",
     "chain": ["Tim_Secco.Q", "(S V_S_Marcia_Secco)"]},

    {"cmt": "BASE TEMPI PER LE ORE DI MARCIA (impulso al minuto)",
     "chain": [{"or": ["OUT_Pompa_1", "OUT_Pompa_2"]}, "/Tim_Minuto.Q",
               {"fb": "TON", "inst": "Tim_Minuto", "p": {"PT": "T#60s"}}]},

    {"cmt": "CONTA MINUTI POMPA 1",
     "chain": ["^Tim_Minuto.Q", "OUT_Pompa_1",
               {"f": "@Inc", "p": {"InOut": "V_S_Ore_P1", "OUT:InOut": "V_S_Ore_P1"}}]},

    {"cmt": "CONTA MINUTI POMPA 2",
     "chain": ["^Tim_Minuto.Q", "OUT_Pompa_2",
               {"f": "@Inc", "p": {"InOut": "V_S_Ore_P2", "OUT:InOut": "V_S_Ore_P2"}}]},

    {"cmt": "RESET ALLARMI DA SCADA O DA BORDO MACCHINA",
     "chain": [{"or": ["^V_P_Reset", "^IN_Reset"]}],
     "out": [["(R V_S_Guasto_P1)"], ["(R V_S_Guasto_P2)"], ["(R V_S_Marcia_Secco)"]]},

    {"cmt": "SPIE DI MARCIA", "chain": ["OUT_Pompa_1", "(V_L_P1_Marcia)"]},
    {"cmt": "SPIA MARCIA POMPA 2", "chain": ["OUT_Pompa_2", "(V_L_P2_Marcia)"]},
    {"cmt": "SPIA CICLO", "chain": ["Mem_Richiesta", "(V_L_Ciclo)"]},
    {"cmt": "SPIA ALLARME CUMULATIVO",
     "chain": [{"or": ["V_S_Guasto_P1", "V_S_Guasto_P2", "V_S_Marcia_Secco", "/Consensi"]},
               "(V_L_Allarme)"]},
    {"cmt": "MACCHINA PRONTA",
     "chain": ["Consensi", "/V_S_Marcia_Secco", "(V_L_Pronto)"]},
]


def main():
    spec = {"out_dir": os.path.join(D, "out"),
            "variables": [{"name": n, "type": t, "comment": c} for n, t, c in INTERNE],
            "sections": {"Pompe": RUNG}}
    json.dump(spec, open(os.path.join(D, "pompe_spec.json"), "w", encoding="utf-8"),
              indent=1, ensure_ascii=False)
    for nome, dati in (("pompe_globali.txt", GLOBALI), ("pompe_interne.txt", INTERNE)):
        with open(os.path.join(D, nome), "w", encoding="utf-8") as f:
            for n, t, c in dati:
                f.write("%s\t%s\t%s\n" % (n, t, c))
    with open(os.path.join(D, "pompe_esterne.txt"), "w", encoding="utf-8") as f:
        for n, _t, _c in GLOBALI:
            f.write("%s\n" % n)
    print("rung:", len(RUNG), "| globali nuove:", len(GLOBALI), "| interne:", len(INTERNE))


if __name__ == "__main__":
    main()
