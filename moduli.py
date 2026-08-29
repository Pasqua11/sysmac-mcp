# -*- coding: utf-8 -*-
"""
moduli.py - catalogo di moduli funzionali per comporre impianti sempre nuovi.

Ogni modulo e' un pezzo di automazione che negli impianti SYNTECH ricorre
davvero: un motore con termico, una pompa con pressostato, una valvola con
finecorsa, un riscaldamento con termostato di sicurezza, un passo di
sequenza, un conteggio pezzi. Ciascuno sa dichiarare le proprie variabili,
i propri rung E i propri passi di collaudo: componendo moduli a caso si
ottiene un impianto diverso ogni volta, gia' collaudabile.

Convenzioni:
  - ogni modulo riceve un indice `i` e prefissa le proprie variabili
  - "Consensi" e "V_P_Reset" sono forniti dall'ossatura comune
  - i passi di collaudo usano solo variabili GLOBALI, cosi' lo stesso
    scenario vale per il simulatore Python e per quello di Sysmac
"""


def motore(i):
    """Motore con marcia/arresto, termico e spia. Il mattone piu' comune."""
    p = "M%d" % i
    return {
        "nome": "motore %d" % i,
        "globali": [
            ("IN_%s_Termico" % p, "BOOL", "termico motore %d (NC: TRUE = ok)" % i),
            ("V_P_%s_Marcia" % p, "BOOL", "comando di marcia motore %d" % i),
            ("V_P_%s_Arresto" % p, "BOOL", "comando di arresto motore %d" % i),
            ("OUT_%s" % p, "BOOL", "contattore motore %d" % i),
            ("V_S_%s_Guasto" % p, "BOOL", "guasto motore %d" % i),
            ("V_L_%s" % p, "BOOL", "spia motore %d in marcia" % i),
        ],
        "interne": [("Mem_%s" % p, "BOOL", "richiesta di marcia motore %d" % i)],
        "rung": [
            {"cmt": "MOTORE %d - MARCIA" % i,
             "chain": ["^V_P_%s_Marcia" % p, "Consensi", "IN_%s_Termico" % p,
                       "/V_S_%s_Guasto" % p, "(S Mem_%s)" % p]},
            {"cmt": "MOTORE %d - ARRESTO" % i,
             "chain": [{"or": ["^V_P_%s_Arresto" % p, "/Consensi",
                               "/IN_%s_Termico" % p]},
                       "(R Mem_%s)" % p]},
            {"cmt": "MOTORE %d - COMANDO" % i,
             "chain": ["Mem_%s" % p, "Consensi", "IN_%s_Termico" % p,
                       "(OUT_%s)" % p]},
            {"cmt": "MOTORE %d - GUASTO TERMICO" % i,
             "chain": ["/IN_%s_Termico" % p, "(S V_S_%s_Guasto)" % p]},
            {"cmt": "MOTORE %d - RESET GUASTO" % i,
             "chain": ["^V_P_Reset", "IN_%s_Termico" % p,
                       "(R V_S_%s_Guasto)" % p]},
            {"cmt": "MOTORE %d - SPIA" % i,
             "chain": ["OUT_%s" % p, "(V_L_%s)" % p]},
        ],
        "iniziale": {"IN_%s_Termico" % p: True},
        "passi": [
            {"descrizione": "motore %d: la marcia parte" % i,
             "impulso": ["V_P_%s_Marcia" % p], "attendi": 0.4,
             "verifica": {"OUT_%s" % p: True, "V_L_%s" % p: True}},
            {"descrizione": "motore %d: l'arresto lo ferma" % i,
             "impulso": ["V_P_%s_Arresto" % p], "attendi": 0.4,
             "verifica": {"OUT_%s" % p: False}},
            {"descrizione": "motore %d: il termico impedisce la marcia" % i,
             "set": {"IN_%s_Termico" % p: False},
             "impulso": ["V_P_%s_Marcia" % p], "attendi": 0.4,
             "verifica": {"OUT_%s" % p: False, "V_S_%s_Guasto" % p: True}},
            {"descrizione": "motore %d: ripristino e reset" % i,
             "set": {"IN_%s_Termico" % p: True},
             "impulso": ["V_P_Reset"], "attendi": 0.4,
             "verifica": {"V_S_%s_Guasto" % p: False}},
        ],
        "allarmi": ["V_S_%s_Guasto" % p],
    }


def pompa(i):
    """Pompa con pressostato di mandata: se non fa pressione va in guasto."""
    p = "P%d" % i
    return {
        "nome": "pompa %d" % i,
        "globali": [
            ("IN_%s_Press" % p, "BOOL", "pressostato mandata pompa %d" % i),
            ("IN_%s_Liv_Min" % p, "BOOL", "livello minimo aspirazione pompa %d" % i),
            ("V_P_%s_Marcia" % p, "BOOL", "comando marcia pompa %d" % i),
            ("SET_T_%s_Press" % p, "TIME", "attesa pressione pompa %d" % i),
            ("OUT_%s" % p, "BOOL", "contattore pompa %d" % i),
            ("V_S_%s_Guasto" % p, "BOOL", "guasto pompa %d: manca pressione" % i),
        ],
        "interne": [
            ("Mem_%s" % p, "BOOL", "richiesta pompa %d" % i),
            ("Tim_%s" % p, "TON", "sorveglianza pressione pompa %d" % i),
        ],
        "rung": [
            {"cmt": "POMPA %d - RICHIESTA" % i,
             "chain": ["V_P_%s_Marcia" % p, "Consensi", "/V_S_%s_Guasto" % p,
                       "(Mem_%s)" % p]},
            {"cmt": "POMPA %d - COMANDO (non gira a secco)" % i,
             "chain": ["Mem_%s" % p, "IN_%s_Liv_Min" % p, "(OUT_%s)" % p]},
            {"cmt": "POMPA %d - SORVEGLIANZA PRESSIONE" % i,
             "chain": ["OUT_%s" % p, "/IN_%s_Press" % p,
                       {"fb": "TON", "inst": "Tim_%s" % p,
                        "p": {"PT": "SET_T_%s_Press" % p}}]},
            {"cmt": "POMPA %d - GUASTO" % i,
             "chain": ["Tim_%s.Q" % p, "(S V_S_%s_Guasto)" % p]},
            {"cmt": "POMPA %d - RESET" % i,
             "chain": ["^V_P_Reset", "(R V_S_%s_Guasto)" % p]},
        ],
        "iniziale": {"IN_%s_Liv_Min" % p: True, "IN_%s_Press" % p: True,
                     "V_P_%s_Marcia" % p: False},
        "tempi": {"SET_T_%s_Press" % p: "T#2s"},
        "passi": [
            {"descrizione": "pompa %d: parte e fa pressione" % i,
             "set": {"V_P_%s_Marcia" % p: True}, "attendi": 0.4,
             "verifica": {"OUT_%s" % p: True}},
            {"descrizione": "pompa %d: senza pressione va in guasto dopo 2 s" % i,
             "set": {"IN_%s_Press" % p: False}, "attendi": 2.5,
             "verifica": {"V_S_%s_Guasto" % p: True, "OUT_%s" % p: False}},
            {"descrizione": "pompa %d: reset e ripartenza" % i,
             "set": {"IN_%s_Press" % p: True}, "impulso": ["V_P_Reset"],
             "attendi": 0.5,
             "verifica": {"V_S_%s_Guasto" % p: False, "OUT_%s" % p: True}},
            {"descrizione": "pompa %d: a secco non gira" % i,
             "set": {"IN_%s_Liv_Min" % p: False}, "attendi": 0.4,
             "verifica": {"OUT_%s" % p: False}},
            {"descrizione": "pompa %d: livello ripristinato" % i,
             "set": {"IN_%s_Liv_Min" % p: True, "V_P_%s_Marcia" % p: False},
             "attendi": 0.4, "verifica": {"OUT_%s" % p: False}},
        ],
        "allarmi": ["V_S_%s_Guasto" % p],
    }


def valvola(i):
    """Elettrovalvola con finecorsa e allarme se non arriva in posizione."""
    p = "EV%d" % i
    return {
        "nome": "valvola %d" % i,
        "globali": [
            ("IN_%s_Aperta" % p, "BOOL", "finecorsa valvola %d aperta" % i),
            ("IN_%s_Chiusa" % p, "BOOL", "finecorsa valvola %d chiusa" % i),
            ("V_P_%s_Apri" % p, "BOOL", "comando apertura valvola %d" % i),
            ("SET_T_%s" % p, "TIME", "tempo di manovra valvola %d" % i),
            ("OUT_%s" % p, "BOOL", "solenoide valvola %d" % i),
            ("V_S_%s_All" % p, "BOOL", "allarme manovra valvola %d" % i),
        ],
        "interne": [("Tim_%s" % p, "TON", "sorveglianza manovra valvola %d" % i)],
        "rung": [
            {"cmt": "VALVOLA %d - COMANDO" % i,
             "chain": ["V_P_%s_Apri" % p, "Consensi", "/V_S_%s_All" % p,
                       "(OUT_%s)" % p]},
            {"cmt": "VALVOLA %d - SORVEGLIANZA MANOVRA" % i,
             "chain": ["OUT_%s" % p, "/IN_%s_Aperta" % p,
                       {"fb": "TON", "inst": "Tim_%s" % p,
                        "p": {"PT": "SET_T_%s" % p}}]},
            {"cmt": "VALVOLA %d - ALLARME MANOVRA" % i,
             "chain": ["Tim_%s.Q" % p, "(S V_S_%s_All)" % p]},
            {"cmt": "VALVOLA %d - RESET" % i,
             "chain": ["^V_P_Reset", "(R V_S_%s_All)" % p]},
        ],
        "iniziale": {"IN_%s_Chiusa" % p: True, "IN_%s_Aperta" % p: False,
                     "V_P_%s_Apri" % p: False},
        "tempi": {"SET_T_%s" % p: "T#2s"},
        "passi": [
            {"descrizione": "valvola %d: apre al comando" % i,
             "set": {"V_P_%s_Apri" % p: True}, "attendi": 0.4,
             "verifica": {"OUT_%s" % p: True}},
            {"descrizione": "valvola %d: arriva aperta, nessun allarme" % i,
             "set": {"IN_%s_Aperta" % p: True, "IN_%s_Chiusa" % p: False},
             "attendi": 0.5,
             "verifica": {"V_S_%s_All" % p: False}},
            {"descrizione": "valvola %d: se non arriva, allarme dopo 2 s" % i,
             "set": {"IN_%s_Aperta" % p: False}, "attendi": 2.5,
             "verifica": {"V_S_%s_All" % p: True, "OUT_%s" % p: False}},
            {"descrizione": "valvola %d: reset" % i,
             "set": {"V_P_%s_Apri" % p: False}, "impulso": ["V_P_Reset"],
             "attendi": 0.4, "verifica": {"V_S_%s_All" % p: False}},
        ],
        "allarmi": ["V_S_%s_All" % p],
    }


def riscaldamento(i):
    """Riscaldamento con termostato di regolazione e uno di sicurezza."""
    p = "R%d" % i
    return {
        "nome": "riscaldamento %d" % i,
        "globali": [
            ("IN_%s_Temp_Ok" % p, "BOOL", "termostato %d in temperatura" % i),
            ("IN_%s_Temp_Alta" % p, "BOOL", "termostato di sicurezza %d" % i),
            ("IN_%s_Livello" % p, "BOOL", "livello sopra le resistenze %d" % i),
            ("V_S_%s_Abilita" % p, "BOOL", "riscaldamento %d abilitato" % i),
            ("OUT_%s" % p, "BOOL", "teleruttore resistenze %d" % i),
            ("V_S_%s_All" % p, "BOOL", "allarme sovratemperatura %d" % i),
        ],
        "interne": [],
        "rung": [
            {"cmt": "RISCALDAMENTO %d - COMANDO" % i,
             "chain": ["V_S_%s_Abilita" % p, "IN_%s_Livello" % p,
                       "/IN_%s_Temp_Ok" % p, "/IN_%s_Temp_Alta" % p,
                       "/V_S_%s_All" % p, "Consensi", "(OUT_%s)" % p]},
            {"cmt": "RISCALDAMENTO %d - SOVRATEMPERATURA" % i,
             "chain": ["IN_%s_Temp_Alta" % p, "(S V_S_%s_All)" % p]},
            {"cmt": "RISCALDAMENTO %d - RESET (solo a temperatura rientrata)" % i,
             "chain": ["^V_P_Reset", "/IN_%s_Temp_Alta" % p,
                       "(R V_S_%s_All)" % p]},
        ],
        "iniziale": {"IN_%s_Livello" % p: True, "IN_%s_Temp_Ok" % p: False,
                     "IN_%s_Temp_Alta" % p: False, "V_S_%s_Abilita" % p: True},
        "passi": [
            {"descrizione": "riscaldamento %d: sotto temperatura scalda" % i,
             "attendi": 0.4, "verifica": {"OUT_%s" % p: True}},
            {"descrizione": "riscaldamento %d: in temperatura si spegne" % i,
             "set": {"IN_%s_Temp_Ok" % p: True}, "attendi": 0.4,
             "verifica": {"OUT_%s" % p: False}},
            {"descrizione": "riscaldamento %d: senza liquido non scalda" % i,
             "set": {"IN_%s_Temp_Ok" % p: False, "IN_%s_Livello" % p: False},
             "attendi": 0.4, "verifica": {"OUT_%s" % p: False}},
            {"descrizione": "riscaldamento %d: sovratemperatura blocca" % i,
             "set": {"IN_%s_Livello" % p: True, "IN_%s_Temp_Alta" % p: True},
             "attendi": 0.4,
             "verifica": {"V_S_%s_All" % p: True, "OUT_%s" % p: False}},
            {"descrizione": "riscaldamento %d: reset a caldo NON deve ripristinare" % i,
             "impulso": ["V_P_Reset"], "attendi": 0.4,
             "verifica": {"V_S_%s_All" % p: True}},
            {"descrizione": "riscaldamento %d: rientrata, il reset vale" % i,
             "set": {"IN_%s_Temp_Alta" % p: False}, "impulso": ["V_P_Reset"],
             "attendi": 0.4, "verifica": {"V_S_%s_All" % p: False}},
        ],
        "allarmi": ["V_S_%s_All" % p],
    }


def livello(i):
    """Vasca con carico automatico fra minimo e massimo, e allarme di troppo pieno."""
    p = "L%d" % i
    return {
        "nome": "livello %d" % i,
        "globali": [
            ("IN_%s_Min" % p, "BOOL", "sonda minimo vasca %d" % i),
            ("IN_%s_Max" % p, "BOOL", "sonda massimo vasca %d" % i),
            ("IN_%s_Sfioro" % p, "BOOL", "troppo pieno vasca %d" % i),
            ("SET_T_%s" % p, "TIME", "tempo massimo di carico vasca %d" % i),
            ("OUT_%s_Carico" % p, "BOOL", "elettrovalvola carico vasca %d" % i),
            ("V_S_%s_All" % p, "BOOL", "allarme carico vasca %d" % i),
        ],
        "interne": [
            ("Req_%s" % p, "BOOL", "richiesta di carico vasca %d" % i),
            ("Tim_%s" % p, "TON", "sorveglianza carico vasca %d" % i),
        ],
        "rung": [
            {"cmt": "VASCA %d - RICHIESTA DI CARICO AL MINIMO" % i,
             "chain": ["/IN_%s_Min" % p, "Consensi", "/V_S_%s_All" % p,
                       "(S Req_%s)" % p]},
            {"cmt": "VASCA %d - FINE CARICO AL MASSIMO" % i,
             "chain": [{"or": ["IN_%s_Max" % p, "IN_%s_Sfioro" % p,
                               "/Consensi"]},
                       "(R Req_%s)" % p]},
            # l'allarme deve togliere il comando, non solo accendere una spia:
            # senza "/V_S_..._All" la valvola restava aperta dopo l'allarme di
            # carico troppo lungo, che e' proprio il caso in cui va chiusa
            {"cmt": "VASCA %d - ELETTROVALVOLA" % i,
             "chain": ["Req_%s" % p, "/IN_%s_Sfioro" % p, "/V_S_%s_All" % p,
                       "(OUT_%s_Carico)" % p]},
            {"cmt": "VASCA %d - SORVEGLIANZA TEMPO DI CARICO" % i,
             "chain": ["OUT_%s_Carico" % p,
                       {"fb": "TON", "inst": "Tim_%s" % p,
                        "p": {"PT": "SET_T_%s" % p}}]},
            {"cmt": "VASCA %d - ALLARME CARICO TROPPO LUNGO" % i,
             "chain": ["Tim_%s.Q" % p],
             "out": [["(S V_S_%s_All)" % p], ["(R Req_%s)" % p]]},
            {"cmt": "VASCA %d - RESET" % i,
             "chain": ["^V_P_Reset", "(R V_S_%s_All)" % p]},
        ],
        "iniziale": {"IN_%s_Min" % p: True, "IN_%s_Max" % p: True,
                     "IN_%s_Sfioro" % p: False},
        "tempi": {"SET_T_%s" % p: "T#3s"},
        "passi": [
            {"descrizione": "vasca %d: piena, non carica" % i,
             "attendi": 0.4, "verifica": {"OUT_%s_Carico" % p: False}},
            {"descrizione": "vasca %d: sotto il minimo, carica" % i,
             "set": {"IN_%s_Min" % p: False, "IN_%s_Max" % p: False},
             "attendi": 0.4, "verifica": {"OUT_%s_Carico" % p: True}},
            {"descrizione": "vasca %d: al massimo si ferma" % i,
             "set": {"IN_%s_Min" % p: True, "IN_%s_Max" % p: True},
             "attendi": 0.4, "verifica": {"OUT_%s_Carico" % p: False}},
            {"descrizione": "vasca %d: carico che non finisce, allarme dopo 3 s" % i,
             "set": {"IN_%s_Min" % p: False, "IN_%s_Max" % p: False},
             "attendi": 3.4,
             "verifica": {"V_S_%s_All" % p: True, "OUT_%s_Carico" % p: False}},
            {"descrizione": "vasca %d: reset" % i,
             "set": {"IN_%s_Min" % p: True, "IN_%s_Max" % p: True},
             "impulso": ["V_P_Reset"], "attendi": 0.4,
             "verifica": {"V_S_%s_All" % p: False}},
        ],
        "allarmi": ["V_S_%s_All" % p],
    }


def conteggio(i):
    """Nastro con fotocellula, conteggio pezzi e lotto completo."""
    p = "C%d" % i
    return {
        "nome": "conteggio %d" % i,
        "globali": [
            ("IN_%s_Foto" % p, "BOOL", "fotocellula conteggio %d" % i),
            ("SET_%s_Lotto" % p, "INT", "pezzi per lotto %d" % i),
            ("V_S_%s_Pezzi" % p, "INT", "pezzi contati %d" % i),
            ("V_P_%s_Azzera" % p, "BOOL", "azzeramento conteggio %d" % i),
            ("V_L_%s_Lotto" % p, "BOOL", "lotto %d completo" % i),
        ],
        "interne": [],
        "rung": [
            {"cmt": "CONTEGGIO %d - INCREMENTO AL PASSAGGIO DEL PEZZO" % i,
             "chain": ["^IN_%s_Foto" % p, "/V_L_%s_Lotto" % p,
                       {"f": "@Inc", "p": {"InOut": "V_S_%s_Pezzi" % p,
                                            "OUT:InOut": "V_S_%s_Pezzi" % p}}]},
            {"cmt": "CONTEGGIO %d - LOTTO COMPLETO" % i,
             "chain": [{"f": ">=", "p": {"In1": "V_S_%s_Pezzi" % p,
                                          "In2": "SET_%s_Lotto" % p}},
                       "(V_L_%s_Lotto)" % p]},
            {"cmt": "CONTEGGIO %d - AZZERAMENTO" % i,
             "chain": ["^V_P_%s_Azzera" % p,
                       {"f": "MOVE", "p": {"In": "0",
                                            "OUT:Out": "V_S_%s_Pezzi" % p}}]},
        ],
        "iniziale": {"IN_%s_Foto" % p: False, "V_S_%s_Pezzi" % p: 0,
                     "SET_%s_Lotto" % p: 3},
        "passi": [
            {"descrizione": "conteggio %d: primo pezzo" % i,
             "impulso": ["IN_%s_Foto" % p], "attendi": 0.3,
             "verifica": {"V_S_%s_Pezzi" % p: 1, "V_L_%s_Lotto" % p: False}},
            {"descrizione": "conteggio %d: secondo pezzo" % i,
             "impulso": ["IN_%s_Foto" % p], "attendi": 0.3,
             "verifica": {"V_S_%s_Pezzi" % p: 2}},
            {"descrizione": "conteggio %d: terzo pezzo, lotto completo" % i,
             "impulso": ["IN_%s_Foto" % p], "attendi": 0.3,
             "verifica": {"V_S_%s_Pezzi" % p: 3, "V_L_%s_Lotto" % p: True}},
            {"descrizione": "conteggio %d: a lotto pieno non conta piu'" % i,
             "impulso": ["IN_%s_Foto" % p], "attendi": 0.3,
             "verifica": {"V_S_%s_Pezzi" % p: 3}},
            {"descrizione": "conteggio %d: azzeramento" % i,
             "impulso": ["V_P_%s_Azzera" % p], "attendi": 0.4,
             "verifica": {"V_S_%s_Pezzi" % p: 0, "V_L_%s_Lotto" % p: False}},
        ],
        "allarmi": [],
    }


def sequenza(i, passi=4):
    """Sequenza a passi con temporizzazione: l'ossatura di ogni ciclo automatico."""
    p = "S%d" % i
    g = [
        ("V_P_%s_Start" % p, "BOOL", "avvio sequenza %d" % i),
        ("V_P_%s_Stop" % p, "BOOL", "arresto sequenza %d" % i),
        ("V_S_%s_Passo" % p, "INT", "passo corrente sequenza %d" % i),
        ("V_L_%s_Ciclo" % p, "BOOL", "sequenza %d in corso" % i),
        ("V_L_%s_Fine" % p, "BOOL", "sequenza %d completata" % i),
    ]
    it = [("Mem_%s_Ciclo" % p, "BOOL", "sequenza %d attiva" % i),
          ("Mem_%s_Fine" % p, "BOOL", "sequenza %d completata" % i)]
    r = [
        {"cmt": "SEQUENZA %d - AZZERAMENTO ALL'AVVIO" % i,
         "chain": ["^V_P_%s_Start" % p],
         "out": ([["(R End_%s_%d)" % (p, k)] for k in range(1, passi + 1)] +
                 [["(R Mem_%s_Fine)" % p],
                  [{"f": "MOVE", "p": {"In": "0",
                                       "OUT:Out": "V_S_%s_Passo" % p}}]])},
        {"cmt": "SEQUENZA %d - AVVIO" % i,
         "chain": ["^V_P_%s_Start" % p, "Consensi", "(S Mem_%s_Ciclo)" % p]},
        {"cmt": "SEQUENZA %d - ARRESTO" % i,
         "chain": [{"or": ["^V_P_%s_Stop" % p, "/Consensi", "Mem_%s_Fine" % p]},
                   "(R Mem_%s_Ciclo)" % p]},
    ]
    for k in range(1, passi + 1):
        g.append(("SET_T_%s_%d" % (p, k), "TIME", "durata passo %d sequenza %d" % (k, i)))
        g.append(("OUT_%s_%d" % (p, k), "BOOL", "uscita del passo %d sequenza %d" % (k, i)))
        it.append(("Mem_%s_%d" % (p, k), "BOOL", "passo %d in corso" % k))
        it.append(("End_%s_%d" % (p, k), "BOOL", "passo %d completato" % k))
        it.append(("Tim_%s_%d" % (p, k), "TON", "temporizzatore passo %d" % k))
        prec = "Mem_%s_Ciclo" % p if k == 1 else "End_%s_%d" % (p, k - 1)
        r += [
            {"cmt": "SEQUENZA %d - INGRESSO PASSO %d" % (i, k),
             "chain": ["Mem_%s_Ciclo" % p, prec, "/End_%s_%d" % (p, k),
                       "(S Mem_%s_%d)" % (p, k)]},
            {"cmt": "SEQUENZA %d - PASSO %d IN CORSO" % (i, k),
             "chain": ["Mem_%s_%d" % (p, k),
                       {"fb": "TON", "inst": "Tim_%s_%d" % (p, k),
                        "p": {"PT": "SET_T_%s_%d" % (p, k)}}]},
            {"cmt": "SEQUENZA %d - USCITA DEL PASSO %d" % (i, k),
             "chain": ["Mem_%s_%d" % (p, k), "Consensi",
                       "(OUT_%s_%d)" % (p, k)]},
            {"cmt": "SEQUENZA %d - FINE PASSO %d" % (i, k),
             "chain": ["Tim_%s_%d.Q" % (p, k)],
             "out": [["(S End_%s_%d)" % (p, k)], ["(R Mem_%s_%d)" % (p, k)],
                     [{"f": "MOVE", "p": {"In": str(k),
                                          "OUT:Out": "V_S_%s_Passo" % p}}]]},
        ]
    r += [
        {"cmt": "SEQUENZA %d - COMPLETATA" % i,
         "chain": ["Mem_%s_Ciclo" % p, "End_%s_%d" % (p, passi),
                   "(S Mem_%s_Fine)" % p]},
        {"cmt": "SEQUENZA %d - SPIE" % i,
         "chain": ["Mem_%s_Ciclo" % p, "(V_L_%s_Ciclo)" % p]},
        {"cmt": "SEQUENZA %d - SPIA FINE" % i,
         "chain": ["Mem_%s_Fine" % p, "(V_L_%s_Fine)" % p]},
    ]
    tempi = {"SET_T_%s_%d" % (p, k): "T#1s" for k in range(1, passi + 1)}
    # Attenzione ai tempi del collaudo: verificare passo per passo con
    # un'attesa di 1,2 s su timer da 1 s accumula 0,2 s di deriva a ogni
    # passo, e dopo cinque passi si verifica il passo sbagliato. Qui si
    # controllano solo il primo cambio di passo e il completamento totale.
    passi_test = [
        {"descrizione": "sequenza %d: avvio, primo passo attivo" % i,
         "impulso": ["V_P_%s_Start" % p], "attendi": 0.4,
         "verifica": {"V_L_%s_Ciclo" % p: True, "OUT_%s_1" % p: True,
                      "V_L_%s_Fine" % p: False}},
        {"descrizione": "sequenza %d: dal passo 1 si passa al 2" % i,
         "attendi": 0.9,
         "verifica": {"V_S_%s_Passo" % p: 1, "OUT_%s_1" % p: False,
                      "OUT_%s_2" % p: True} if passi > 1 else
                     {"V_S_%s_Passo" % p: 1}},
        {"descrizione": "sequenza %d: completata dopo tutti i %d passi"
                        % (i, passi),
         "attendi": 1.0 * (passi - 1) + 0.8,
         "verifica": {"V_L_%s_Fine" % p: True, "V_L_%s_Ciclo" % p: False,
                      "V_S_%s_Passo" % p: passi,
                      "OUT_%s_%d" % (p, passi): False}},
        # il secondo giro e' la prova che i passi siano stati azzerati davvero
        {"descrizione": "sequenza %d: SECONDO CICLO, deve ripartire" % i,
         "impulso": ["V_P_%s_Start" % p], "attendi": 0.5,
         "verifica": {"V_L_%s_Ciclo" % p: True, "OUT_%s_1" % p: True,
                      "V_L_%s_Fine" % p: False}},
        {"descrizione": "sequenza %d: arresto dal secondo ciclo" % i,
         "impulso": ["V_P_%s_Stop" % p], "attendi": 0.4,
         "verifica": {"V_L_%s_Ciclo" % p: False}},
    ]
    return {"nome": "sequenza %d (%d passi)" % (i, passi),
            "globali": g, "interne": it, "rung": r, "iniziale": {},
            "tempi": tempi, "passi": passi_test, "allarmi": []}


def lampeggio(i):
    """Base tempi per le spie: un classico che serve in ogni quadro."""
    p = "B%d" % i
    return {
        "nome": "lampeggio %d" % i,
        "globali": [("V_L_%s_Lampeggio" % p, "BOOL", "uscita lampeggiante %d" % i)],
        "interne": [("Tim_%s_On" % p, "TON", "tempo acceso %d" % i),
                    ("Tim_%s_Off" % p, "TON", "tempo spento %d" % i)],
        "rung": [
            {"cmt": "LAMPEGGIO %d - MEZZO PERIODO ACCESO" % i,
             "chain": ["/Tim_%s_Off.Q" % p,
                       {"fb": "TON", "inst": "Tim_%s_On" % p,
                        "p": {"PT": "T#1s"}}]},
            {"cmt": "LAMPEGGIO %d - MEZZO PERIODO SPENTO" % i,
             "chain": ["Tim_%s_On.Q" % p,
                       {"fb": "TON", "inst": "Tim_%s_Off" % p,
                        "p": {"PT": "T#1s"}}]},
            {"cmt": "LAMPEGGIO %d - USCITA" % i,
             "chain": ["Tim_%s_On.Q" % p, "/Tim_%s_Off.Q" % p,
                       "(V_L_%s_Lampeggio)" % p]},
        ],
        "iniziale": {},
        "passi": [],
        "allarmi": [],
    }


CATALOGO = [motore, pompa, valvola, riscaldamento, livello, conteggio,
            sequenza, lampeggio]
