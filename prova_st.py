# -*- coding: utf-8 -*-
"""Batteria di prove dell'interprete ST: ogni costrutto, uno alla volta."""
import io
import sys

sys.path.insert(0, r"C:\Users\tecni\Claude\sysmac-mcp")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from sim_st import SimST

ok = fail = 0


def prova(nome, codice, ingressi, attesi, secondi=0.1, tempi=None, istanze=None):
    global ok, fail
    try:
        s = SimST(codice, tempi=tempi, istanze=istanze)
        s.set(**ingressi)
        s.corri(secondi)
        diff = {}
        for k, v in attesi.items():
            got = s.leggi(k)
            if isinstance(v, bool):
                got = bool(got)
            if isinstance(v, float):
                if abs(got - v) > 0.06:
                    diff[k] = (v, got)
            elif got != v:
                diff[k] = (v, got)
        if diff:
            fail += 1
            print("  FAIL  %-34s %s" % (nome, diff))
        else:
            ok += 1
            print("  ok    %s" % nome)
    except Exception as e:
        fail += 1
        print("  ERR   %-34s %s: %s" % (nome, type(e).__name__, str(e)[:90]))


# ---------------------------------------------------------------- espressioni
prova("assegnazione booleana", "B := A;", {"A": True}, {"B": True})
prova("AND / OR / NOT",
      "C := A AND NOT B; D := A OR B;", {"A": True, "B": False},
      {"C": True, "D": True})
prova("XOR", "C := A XOR B;", {"A": True, "B": True}, {"C": False})
prova("parentesi e precedenza",
      "C := A OR B AND FALSE;", {"A": False, "B": True}, {"C": False})
prova("confronti", "C := X > 5; D := X <= 5; E := X <> 3;",
      {"X": 7}, {"C": True, "D": False, "E": True})
prova("aritmetica", "Y := (X + 3) * 2 - 1;", {"X": 4}, {"Y": 13})
prova("divisione intera", "Y := X / 3;", {"X": 10}, {"Y": 3})
prova("MOD", "Y := X MOD 4;", {"X": 10}, {"Y": 2})
prova("costante esadecimale", "Y := 16#FF;", {}, {"Y": 255})
prova("reali", "Y := X * 1.5;", {"X": 2.0}, {"Y": 3.0})
prova("funzioni standard", "Y := ABS(-4) + MIN(3, 9) + MAX(1, 2);", {},
      {"Y": 9})
prova("LIMIT e SEL", "Y := LIMIT(0, X, 10); Z := SEL(G, 1, 2);",
      {"X": 25, "G": True}, {"Y": 10, "Z": 2})

# ---------------------------------------------------------------- istruzioni
prova("IF semplice",
      "IF A THEN B := TRUE; END_IF;", {"A": True}, {"B": True})
prova("IF/ELSE",
      "IF A THEN B := 1; ELSE B := 2; END_IF;", {"A": False}, {"B": 2})
prova("IF/ELSIF/ELSE",
      "IF X = 1 THEN Y := 10; ELSIF X = 2 THEN Y := 20; ELSE Y := 30; END_IF;",
      {"X": 2}, {"Y": 20})
prova("CASE",
      "CASE Passo OF 1: Y := 11; 2: Y := 22; 3: Y := 33; ELSE Y := 99; END_CASE;",
      {"Passo": 3}, {"Y": 33})
prova("CASE con ELSE",
      "CASE Passo OF 1: Y := 11; ELSE Y := 99; END_CASE;",
      {"Passo": 7}, {"Y": 99})
prova("CASE etichette multiple",
      "CASE P OF 1,2,3: Y := 1; 4,5: Y := 2; END_CASE;", {"P": 5}, {"Y": 2})
prova("FOR",
      "Tot := 0; FOR i := 1 TO 5 DO Tot := Tot + i; END_FOR;", {},
      {"Tot": 15})
prova("FOR con BY",
      "Tot := 0; FOR i := 0 TO 10 BY 2 DO Tot := Tot + 1; END_FOR;", {},
      {"Tot": 6})
prova("FOR con EXIT",
      "Tot := 0; FOR i := 1 TO 100 DO Tot := Tot + 1; "
      "IF i >= 3 THEN EXIT; END_IF; END_FOR;", {}, {"Tot": 3})
prova("WHILE",
      "N := 0; WHILE N < 4 DO N := N + 1; END_WHILE;", {}, {"N": 4})
prova("REPEAT",
      "N := 0; REPEAT N := N + 1; UNTIL N >= 3 END_REPEAT;", {}, {"N": 3})
prova("commenti // e (* *)",
      "// commento\nA := TRUE; (* altro commento *) B := A;", {},
      {"A": True, "B": True})

# ------------------------------------------------------------ temporizzatori
prova("TON non ancora scaduto",
      "Tim(In := Marcia, PT := T#2s); Fatto := Tim.Q;",
      {"Marcia": True}, {"Fatto": False}, secondi=1.0)
prova("TON scaduto",
      "Tim(In := Marcia, PT := T#2s); Fatto := Tim.Q;",
      {"Marcia": True}, {"Fatto": True}, secondi=2.3)
prova("TON azzerato dall'ingresso",
      "Tim(In := Marcia, PT := T#1s); Fatto := Tim.Q;",
      {"Marcia": False}, {"Fatto": False}, secondi=2.0)
prova("TON con PT da variabile",
      "Tim(In := Marcia, PT := SET_T); Fatto := Tim.Q;",
      {"Marcia": True}, {"Fatto": True}, secondi=1.3,
      tempi={"SET_T": "T#1s"})
prova("TON.ET",
      "Tim(In := TRUE, PT := T#10s); Passato := Tim.ET;",
      {}, {"Passato": 1.0}, secondi=1.0)
prova("TOF tiene su l'uscita",
      "Tim(In := Marcia, PT := T#2s); Usc := Tim.Q;",
      {"Marcia": False}, {"Usc": True}, secondi=1.0,
      istanze={"Tim": "TOF"})
prova("TOF scaduto",
      "Tim(In := Marcia, PT := T#1s); Usc := Tim.Q;",
      {"Marcia": False}, {"Usc": False}, secondi=1.4,
      istanze={"Tim": "TOF"})
prova("CTU conta i fronti",
      "Cnt(CU := Imp, PV := 3); Fatto := Cnt.Q; N := Cnt.CV;",
      {"Imp": True}, {"N": 1, "Fatto": False}, secondi=0.3,
      istanze={"Cnt": "CTU"})
prova("durata composta T#1s500ms",
      "Tim(In := TRUE, PT := T#1s500ms); Q := Tim.Q;",
      {}, {"Q": False}, secondi=1.2)

# ------------------------------------------------------------------ impianto
IMPIANTO = """
// logica di una pompa di travaso
Consensi := NOT IN_Emergenza AND IN_Protezioni;

IF V_P_Start AND Consensi AND NOT IN_Liv_Max THEN
    Mem_Ciclo := TRUE;
END_IF;
IF V_P_Stop OR NOT Consensi OR IN_Liv_Max THEN
    Mem_Ciclo := FALSE;
END_IF;

OUT_Pompa := Mem_Ciclo AND IN_Liv_Min AND Consensi;

Tim_Secco(In := OUT_Pompa AND NOT IN_Liv_Min, PT := T#2s);
IF Tim_Secco.Q THEN
    V_S_Secco := TRUE;
END_IF;

V_L_Allarme := V_S_Secco OR NOT Consensi;
"""
prova("impianto: la pompa parte",
      IMPIANTO,
      {"IN_Emergenza": False, "IN_Protezioni": True, "IN_Liv_Min": True,
       "IN_Liv_Max": False, "V_P_Start": True, "V_P_Stop": False},
      {"OUT_Pompa": True, "V_L_Allarme": False})
prova("impianto: emergenza ferma tutto",
      IMPIANTO,
      {"IN_Emergenza": True, "IN_Protezioni": True, "IN_Liv_Min": True,
       "IN_Liv_Max": False, "V_P_Start": True, "V_P_Stop": False},
      {"OUT_Pompa": False, "V_L_Allarme": True})

print()
print("PROVE: %d superate, %d fallite" % (ok, fail))
sys.exit(0 if fail == 0 else 1)
