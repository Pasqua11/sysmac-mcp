# -*- coding: utf-8 -*-
"""
sim_st.py - interprete di Structured Text, per collaudare senza aprire Sysmac.

Esegue il codice ST come lo eseguirebbe il PLC: una scansione dopo l'altra,
leggendo gli ingressi all'inizio e scrivendo le uscite alla fine. Serve a fare
sul codice ST quello che sim_spec fa sul ladder - trovare i difetti di logica
in una frazione di secondo, prima di toccare Sysmac Studio.

Copre il sottoinsieme che si usa davvero negli impianti:
  assegnazioni, IF/ELSIF/ELSE, CASE, FOR, WHILE, REPEAT, EXIT
  operatori booleani (AND OR XOR NOT), confronti, aritmetica, MOD
  chiamate a blocco funzione con parametri nominali - Tim(In:=x, PT:=T#2s)
  accesso ai membri - Tim.Q, Tim.ET
  temporizzatori TON, TOF, TP e contatori CTU, CTD
  costanti di tempo T#1s500ms, letterali 16#FF, TRUE/FALSE
  commenti // e (* *)

Uso:
    s = SimST(open("prog.st").read())
    s.set(IN_Start=True)
    s.corri(2.0)
    s.leggi("OUT_Pompa")
    s.scenario(json.load(open("scenario.json")))
"""
import json
import re
import sys

SCAN = 0.01          # durata della scansione simulata, in secondi


# ============================================================== analisi lessicale
PAROLE = {
    "IF", "THEN", "ELSIF", "ELSE", "END_IF", "CASE", "OF", "END_CASE",
    "FOR", "TO", "BY", "DO", "END_FOR", "WHILE", "END_WHILE",
    "REPEAT", "UNTIL", "END_REPEAT", "EXIT", "RETURN",
    "AND", "OR", "XOR", "NOT", "MOD", "TRUE", "FALSE",
}

RE_TOKEN = re.compile(r"""
      (?P<spazio>\s+)
    | (?P<commento1>//[^\n]*)
    | (?P<commento2>\(\*.*?\*\))
    | (?P<tempo>[Tt]\#[0-9]+(?:\.[0-9]+)?(?:ms|s|m|h|d)(?:[0-9]+(?:ms|s|m|h|d))*)
    | (?P<esa>16\#[0-9A-Fa-f_]+)
    | (?P<reale>[0-9]+\.[0-9]+)
    | (?P<intero>[0-9][0-9_]*)
    | (?P<stringa>'[^']*')
    | (?P<nome>[A-Za-z_][A-Za-z_0-9]*)
    | (?P<assegna>:=)
    | (?P<confronto><=|>=|<>)
    | (?P<simbolo>[-+*/()\[\];,.:<>=])
""", re.X | re.S)

RE_DURATA = re.compile(r"([0-9]+(?:\.[0-9]+)?)(ms|s|m|h|d)")
FATTORE = {"ms": 0.001, "s": 1.0, "m": 60.0, "h": 3600.0, "d": 86400.0}


def durata(testo):
    """'T#1s500ms' -> 1.5 secondi."""
    tot = 0.0
    for n, u in RE_DURATA.findall(testo.split("#", 1)[-1].lower()):
        tot += float(n) * FATTORE[u]
    return tot


def tokenizza(sorgente):
    fuori = []
    i = 0
    while i < len(sorgente):
        m = RE_TOKEN.match(sorgente, i)
        if not m:
            raise SyntaxError("carattere non riconosciuto alla posizione %d: %r"
                              % (i, sorgente[i:i + 20]))
        i = m.end()
        tipo = m.lastgroup
        testo = m.group()
        if tipo in ("spazio", "commento1", "commento2"):
            continue
        if tipo == "nome" and testo.upper() in PAROLE:
            fuori.append(("kw", testo.upper()))
        elif tipo == "nome":
            fuori.append(("nome", testo))
        elif tipo == "tempo":
            fuori.append(("cost", durata(testo)))
        elif tipo == "esa":
            fuori.append(("cost", int(testo.split("#")[1].replace("_", ""), 16)))
        elif tipo == "reale":
            fuori.append(("cost", float(testo)))
        elif tipo == "intero":
            fuori.append(("cost", int(testo.replace("_", ""))))
        elif tipo == "stringa":
            fuori.append(("cost", testo[1:-1]))
        else:
            fuori.append(("sim", testo))
    fuori.append(("fine", None))
    return fuori


# ==================================================================== sintassi
class Parser(object):
    """Discesa ricorsiva: produce un albero fatto di tuple."""

    def __init__(self, token):
        self.t = token
        self.i = 0

    def sbircia(self):
        return self.t[self.i]

    def avanti(self):
        self.i += 1
        return self.t[self.i - 1]

    def e(self, tipo, testo=None):
        t = self.t[self.i]
        return t[0] == tipo and (testo is None or t[1] == testo)

    def pretendi(self, tipo, testo=None):
        if not self.e(tipo, testo):
            raise SyntaxError("atteso %s %r, trovato %r"
                              % (tipo, testo, self.t[self.i]))
        return self.avanti()

    # ------------------------------------------------------------- istruzioni
    def blocco(self, fine, dentro_case=False):
        istr = []
        while not (self.e("fine") or (self.e("kw") and self.sbircia()[1] in fine)):
            # dentro un CASE il corpo di un ramo finisce anche quando comincia
            # l'etichetta del ramo successivo, che e' una costante seguita da
            # due punti o da una virgola
            if dentro_case and self.e("cost"):
                j = self.i + 1
                while self.t[j] == ("sim", ","):
                    j += 2
                if self.t[j] == ("sim", ":"):
                    break
            istr.append(self.istruzione())
        return istr

    def istruzione(self):
        if self.e("kw", "IF"):
            return self.i_if()
        if self.e("kw", "CASE"):
            return self.i_case()
        if self.e("kw", "FOR"):
            return self.i_for()
        if self.e("kw", "WHILE"):
            return self.i_while()
        if self.e("kw", "REPEAT"):
            return self.i_repeat()
        if self.e("kw", "EXIT"):
            self.avanti()
            self.opzionale_pv()
            return ("exit",)
        if self.e("kw", "RETURN"):
            self.avanti()
            self.opzionale_pv()
            return ("return",)
        return self.i_assegna_o_chiamata()

    def opzionale_pv(self):
        while self.e("sim", ";"):
            self.avanti()

    def i_if(self):
        self.pretendi("kw", "IF")
        cond = self.espressione()
        self.pretendi("kw", "THEN")
        allora = self.blocco({"ELSIF", "ELSE", "END_IF"})
        rami = [(cond, allora)]
        altrimenti = []
        while self.e("kw", "ELSIF"):
            self.avanti()
            c = self.espressione()
            self.pretendi("kw", "THEN")
            rami.append((c, self.blocco({"ELSIF", "ELSE", "END_IF"})))
        if self.e("kw", "ELSE"):
            self.avanti()
            altrimenti = self.blocco({"END_IF"})
        self.pretendi("kw", "END_IF")
        self.opzionale_pv()
        return ("if", rami, altrimenti)

    def i_case(self):
        self.pretendi("kw", "CASE")
        val = self.espressione()
        self.pretendi("kw", "OF")
        rami = []
        altrimenti = []
        while not (self.e("kw", "END_CASE") or self.e("kw", "ELSE")):
            etichette = [self.valore_costante()]
            while self.e("sim", ","):
                self.avanti()
                etichette.append(self.valore_costante())
            self.pretendi("sim", ":")
            corpo = self.blocco({"END_CASE", "ELSE"}, dentro_case=True)
            rami.append((etichette, corpo))
            if self.e("fine"):
                break
        if self.e("kw", "ELSE"):
            self.avanti()
            altrimenti = self.blocco({"END_CASE"})
        self.pretendi("kw", "END_CASE")
        self.opzionale_pv()
        return ("case", val, rami, altrimenti)

    def valore_costante(self):
        t = self.avanti()
        if t[0] == "cost":
            v = t[1]
        elif t[0] == "nome":
            v = ("nome", t[1])
        elif t[0] == "kw" and t[1] in ("TRUE", "FALSE"):
            v = (t[1] == "TRUE")
        else:
            raise SyntaxError("etichetta di CASE non valida: %r" % (t,))
        if self.e("sim", ".") and self.t[self.i + 1][0] == "sim":
            pass
        return v

    def i_for(self):
        self.pretendi("kw", "FOR")
        var = self.pretendi("nome")[1]
        self.pretendi("sim", ":=")
        da = self.espressione()
        self.pretendi("kw", "TO")
        a = self.espressione()
        passo = ("cost", 1)
        if self.e("kw", "BY"):
            self.avanti()
            passo = self.espressione()
        self.pretendi("kw", "DO")
        corpo = self.blocco({"END_FOR"})
        self.pretendi("kw", "END_FOR")
        self.opzionale_pv()
        return ("for", var, da, a, passo, corpo)

    def i_while(self):
        self.pretendi("kw", "WHILE")
        cond = self.espressione()
        self.pretendi("kw", "DO")
        corpo = self.blocco({"END_WHILE"})
        self.pretendi("kw", "END_WHILE")
        self.opzionale_pv()
        return ("while", cond, corpo)

    def i_repeat(self):
        self.pretendi("kw", "REPEAT")
        corpo = self.blocco({"UNTIL"})
        self.pretendi("kw", "UNTIL")
        cond = self.espressione()
        self.pretendi("kw", "END_REPEAT")
        self.opzionale_pv()
        return ("repeat", corpo, cond)

    def i_assegna_o_chiamata(self):
        rif = self.riferimento()
        if self.e("sim", ":="):
            self.avanti()
            val = self.espressione()
            self.opzionale_pv()
            return ("assegna", rif, val)
        if self.e("sim", "("):
            args = self.argomenti()
            self.opzionale_pv()
            return ("chiama", rif, args)
        self.opzionale_pv()
        return ("espr", rif)

    def argomenti(self):
        self.pretendi("sim", "(")
        nominali, posizionali = [], []
        while not self.e("sim", ")"):
            if (self.e("nome") and self.t[self.i + 1] == ("sim", ":=")):
                n = self.avanti()[1]
                self.avanti()
                nominali.append((n, self.espressione()))
            else:
                posizionali.append(self.espressione())
            if self.e("sim", ","):
                self.avanti()
        self.pretendi("sim", ")")
        return (nominali, posizionali)

    def riferimento(self):
        parti = [self.pretendi("nome")[1]]
        while True:
            if self.e("sim", "."):
                self.avanti()
                parti.append(self.pretendi("nome")[1])
            elif self.e("sim", "["):
                self.avanti()
                idx = self.espressione()
                self.pretendi("sim", "]")
                parti.append(("[]", idx))
            else:
                break
        return ("rif", parti)

    # ------------------------------------------------------------ espressioni
    def espressione(self):
        return self.e_or()

    def e_or(self):
        s = self.e_xor()
        while self.e("kw", "OR"):
            self.avanti()
            s = ("or", s, self.e_xor())
        return s

    def e_xor(self):
        s = self.e_and()
        while self.e("kw", "XOR"):
            self.avanti()
            s = ("xor", s, self.e_and())
        return s

    def e_and(self):
        s = self.e_confronto()
        while self.e("kw", "AND") or self.e("sim", "&"):
            self.avanti()
            s = ("and", s, self.e_confronto())
        return s

    # tutti i confronti arrivano dal lexer come ("sim", ...): <= >= <> sono
    # un token solo, ma restano di tipo "sim" come = < >
    CONFRONTI = ("=", "<", ">", "<=", ">=", "<>")

    def e_confronto(self):
        s = self.e_somma()
        while self.e("sim") and self.sbircia()[1] in self.CONFRONTI:
            op = self.avanti()[1]
            s = ("cmp", op, s, self.e_somma())
        return s

    def e_somma(self):
        s = self.e_prodotto()
        while self.e("sim", "+") or self.e("sim", "-"):
            op = self.avanti()[1]
            s = ("bin", op, s, self.e_prodotto())
        return s

    def e_prodotto(self):
        s = self.e_unario()
        while self.e("sim", "*") or self.e("sim", "/") or self.e("kw", "MOD"):
            op = self.avanti()[1]
            s = ("bin", op, s, self.e_unario())
        return s

    def e_unario(self):
        if self.e("kw", "NOT"):
            self.avanti()
            return ("not", self.e_unario())
        if self.e("sim", "-"):
            self.avanti()
            return ("neg", self.e_unario())
        if self.e("sim", "+"):
            self.avanti()
            return self.e_unario()
        return self.e_primario()

    def e_primario(self):
        if self.e("sim", "("):
            self.avanti()
            v = self.espressione()
            self.pretendi("sim", ")")
            return v
        if self.e("cost"):
            return ("cost", self.avanti()[1])
        if self.e("kw", "TRUE"):
            self.avanti()
            return ("cost", True)
        if self.e("kw", "FALSE"):
            self.avanti()
            return ("cost", False)
        if self.e("nome"):
            rif = self.riferimento()
            if self.e("sim", "("):
                return ("funz", rif, self.argomenti())
            return rif
        raise SyntaxError("espressione non valida presso %r" % (self.sbircia(),))


def analizza(sorgente):
    p = Parser(tokenizza(sorgente))
    corpo = p.blocco(set())
    if not p.e("fine"):
        raise SyntaxError("codice non consumato presso %r" % (p.sbircia(),))
    return corpo


# ================================================================== esecuzione
class Uscita(Exception):
    pass


class Ritorno(Exception):
    pass


class SimST(object):
    """Esegue il programma ST scansione per scansione."""

    def __init__(self, sorgente, tempi=None, istanze=None):
        """istanze: {"Tim_Ritardo": "TOF", ...} - il tipo delle istanze di
        blocco funzione. In un progetto vero sta nella tabella variabili;
        senza indicazione si assume TON, che e' il caso di gran lunga piu'
        frequente."""
        self.albero = analizza(sorgente)
        self.v = {}
        self.blocchi = {}          # istanze di FB: nome -> stato
        self.istanze = {k: v.upper() for k, v in (istanze or {}).items()}
        self.t = 0.0
        self.tempi = dict(tempi or {})
        for k, x in list(self.tempi.items()):
            if isinstance(x, str) and x.upper().startswith("T#"):
                self.tempi[k] = durata(x)
        self.v.update(self.tempi)

    # ------------------------------------------------------------- interfaccia
    def set(self, **kw):
        for k, x in kw.items():
            if isinstance(x, str) and x.upper().startswith("T#"):
                x = durata(x)
            self.v[k] = x
        return self

    def leggi(self, *nomi):
        if len(nomi) == 1:
            return self._leggi(nomi[0])
        return {n: self._leggi(n) for n in nomi}

    def _leggi(self, nome):
        if "." in nome:
            base, campo = nome.split(".", 1)
            st = self.blocchi.get(base, {})
            return st.get(campo, False)
        return self.v.get(nome, False)

    def corri(self, secondi):
        n = max(1, int(round(secondi / SCAN)))
        for _ in range(n):
            self.t += SCAN
            self._scan()
        return self

    def _scan(self):
        try:
            self._esegui(self.albero)
        except (Uscita, Ritorno):
            pass

    # -------------------------------------------------------------- istruzioni
    def _esegui(self, istr):
        for i in istr:
            self._una(i)

    def _una(self, i):
        tipo = i[0]
        if tipo == "assegna":
            self._scrivi(i[1], self._val(i[2]))
        elif tipo == "if":
            for cond, corpo in i[1]:
                if self._vero(cond):
                    self._esegui(corpo)
                    return
            self._esegui(i[2])
        elif tipo == "case":
            v = self._val(i[1])
            for etichette, corpo in i[2]:
                for e in etichette:
                    ev = self._val(e) if isinstance(e, tuple) else e
                    if v == ev:
                        self._esegui(corpo)
                        return
            self._esegui(i[3])
        elif tipo == "for":
            _, var, da, a, passo, corpo = i
            k = self._val(da)
            fine = self._val(a)
            st = self._val(passo) or 1
            giri = 0
            while (st > 0 and k <= fine) or (st < 0 and k >= fine):
                self.v[var] = k
                try:
                    self._esegui(corpo)
                except Uscita:
                    break
                k += st
                giri += 1
                if giri > 100000:
                    raise RuntimeError("FOR senza fine su %r" % var)
        elif tipo == "while":
            giri = 0
            while self._vero(i[1]):
                try:
                    self._esegui(i[2])
                except Uscita:
                    break
                giri += 1
                if giri > 100000:
                    raise RuntimeError("WHILE senza fine")
        elif tipo == "repeat":
            giri = 0
            while True:
                try:
                    self._esegui(i[1])
                except Uscita:
                    break
                if self._vero(i[2]):
                    break
                giri += 1
                if giri > 100000:
                    raise RuntimeError("REPEAT senza fine")
        elif tipo == "chiama":
            self._chiama(i[1], i[2])
        elif tipo == "exit":
            raise Uscita()
        elif tipo == "return":
            raise Ritorno()
        elif tipo == "espr":
            self._val(i[1])

    def _nome(self, rif):
        parti = []
        for p in rif[1]:
            if isinstance(p, tuple):
                parti.append("[%s]" % self._val(p[1]))
            else:
                parti.append(p)
        return ".".join(parti) if len(parti) > 1 else parti[0]

    def _scrivi(self, rif, valore):
        nome = self._nome(rif)
        if "." in nome:
            base, campo = nome.split(".", 1)
            self.blocchi.setdefault(base, {})[campo] = valore
        else:
            self.v[nome] = valore

    # -------------------------------------------------------------- espressioni
    def _vero(self, e):
        return bool(self._val(e))

    def _val(self, e):
        if not isinstance(e, tuple):
            return e
        t = e[0]
        if t == "cost":
            return e[1]
        if t == "rif":
            return self._leggi(self._nome(e))
        if t == "and":
            return bool(self._val(e[1])) and bool(self._val(e[2]))
        if t == "or":
            return bool(self._val(e[1])) or bool(self._val(e[2]))
        if t == "xor":
            return bool(self._val(e[1])) != bool(self._val(e[2]))
        if t == "not":
            return not self._val(e[1])
        if t == "neg":
            return -self._val(e[1])
        if t == "cmp":
            a, b = self._val(e[2]), self._val(e[3])
            op = e[1]
            if op == "=":
                return a == b
            if op == "<>":
                return a != b
            if op == "<":
                return a < b
            if op == ">":
                return a > b
            if op == "<=":
                return a <= b
            if op == ">=":
                return a >= b
        if t == "bin":
            a, b = self._val(e[2]), self._val(e[3])
            op = e[1]
            if op == "+":
                return a + b
            if op == "-":
                return a - b
            if op == "*":
                return a * b
            if op == "/":
                if b == 0:
                    return 0
                if isinstance(a, int) and isinstance(b, int):
                    return int(a / b)
                return a / b
            if op == "MOD":
                return a % b if b else 0
        if t == "funz":
            return self._chiama(e[1], e[2])
        raise RuntimeError("espressione sconosciuta: %r" % (e,))

    # ------------------------------------------------------- blocchi e funzioni
    def _chiama(self, rif, args):
        nome = self._nome(rif)
        nominali, posizionali = args
        p = {n: self._val(v) for n, v in nominali}
        pos = [self._val(v) for v in posizionali]

        maiusc = nome.upper()
        # funzioni standard senza stato
        if maiusc in FUNZIONI:
            return FUNZIONI[maiusc](*(pos or list(p.values())))

        # istanza di blocco funzione: il tipo si deduce dai parametri passati
        st = self.blocchi.setdefault(nome, {})
        tipo = (self.istanze.get(nome) or st.get("__tipo__")
                or self._indovina(p))
        st["__tipo__"] = tipo
        if tipo in ("TON", "TOF", "TP"):
            self._temporizzatore(st, tipo, p)
        elif tipo in ("CTU", "CTD"):
            self._contatore(st, tipo, p)
        else:
            # blocco non riconosciuto: si registrano i parametri, cosi' il
            # codice che legge i suoi membri trova almeno qualcosa
            st.update(p)
        return st.get("Q", False)

    @staticmethod
    def _indovina(p):
        if "PT" in p:
            return "TON"
        if "PV" in p or "CU" in p:
            return "CTU"
        return "?"

    def _temporizzatore(self, st, tipo, p):
        ingresso = bool(p.get("In", p.get("IN", False)))
        pt = p.get("PT", 0)
        if isinstance(pt, str):
            pt = durata(pt)
        if tipo == "TON":
            if ingresso:
                if st.get("_da") is None:
                    st["_da"] = self.t
                st["ET"] = self.t - st["_da"]
                st["Q"] = st["ET"] >= pt
            else:
                st["_da"] = None
                st["ET"] = 0.0
                st["Q"] = False
        elif tipo == "TOF":
            if ingresso:
                st["_da"] = None
                st["Q"] = True
                st["ET"] = 0.0
            else:
                if st.get("_da") is None:
                    st["_da"] = self.t
                st["ET"] = self.t - st["_da"]
                st["Q"] = st["ET"] < pt
        elif tipo == "TP":
            if ingresso and not st.get("_prec"):
                st["_da"] = self.t
            if st.get("_da") is not None:
                st["ET"] = self.t - st["_da"]
                st["Q"] = st["ET"] < pt
            st["_prec"] = ingresso

    def _contatore(self, st, tipo, p):
        cu = bool(p.get("CU", p.get("CD", False)))
        reset = bool(p.get("Reset", p.get("R", False)))
        pv = p.get("PV", 0)
        if reset:
            st["CV"] = 0
        elif cu and not st.get("_prec"):
            st["CV"] = st.get("CV", 0) + (1 if tipo == "CTU" else -1)
        st["_prec"] = cu
        st["Q"] = (st.get("CV", 0) >= pv) if tipo == "CTU" else (st.get("CV", 0) <= 0)

    def durata(self, var, valore=True, tmax=300, da_ora=False):
        """Quanto resta `var` al valore indicato, agganciando il FRONTE.

        Identica a sim_spec.durata, e deve restarlo: si aspetta prima lo
        stato OPPOSTO e poi l'inizio vero, altrimenti misurando da uno stato
        gia' attivo si ottiene una frazione di secondo invece della durata
        intera - e, cosa peggiore, si consuma meno tempo simulato, sfasando
        tutti i passi successivi rispetto al ladder."""
        t0 = self.t
        if not da_ora:
            while bool(self._leggi(var)) == bool(valore) and self.t - t0 < tmax:
                self.corri(SCAN)
            while bool(self._leggi(var)) != bool(valore) and self.t - t0 < tmax:
                self.corri(SCAN)
        inizio = self.t
        while bool(self._leggi(var)) == bool(valore) and self.t - t0 < tmax:
            self.corri(SCAN)
        return round(self.t - inizio, 3)

    # ---------------------------------------------------------------- scenario
    def scenario(self, sc):
        """Esegue uno scenario di collaudo, nello stesso formato usato per il
        ladder: cosi' lo stesso file vale per ST, per sim_spec e per Sysmac."""
        esito = {"nome": sc.get("nome", "collaudo"), "passi": [], "falliti": 0}
        for n, passo in enumerate(sc.get("passi", []), 1):
            p = {"n": n, "descrizione": passo.get("descrizione", "")}
            # L'ordine e la durata dell'impulso devono essere gli STESSI di
            # sim_spec e del simulatore di Sysmac: set, attendi, impulso.
            # Con un ordine diverso lo stesso scenario da' esiti diversi e i
            # confronti fra linguaggi non valgono piu' niente (29/08/2026).
            if "set" in passo:
                self.set(**passo["set"])
            if "attendi" in passo:
                self.corri(float(passo["attendi"]))
            if passo.get("impulso"):
                for var in passo["impulso"]:
                    self.set(**{var: True})
                self.corri(float(passo.get("durata_impulso", 0.3)))
                for var in passo["impulso"]:
                    self.set(**{var: False})
                # niente attesa aggiuntiva qui: sim_spec non ce l'ha, e un
                # ritardo in piu' a ogni impulso sfasa progressivamente i
                # tempi. Su un impianto a fasi temporizzate si vede subito.
            if "durata" in passo:
                d = passo["durata"]
                mis = self.durata(d["variabile"], d.get("valore", True),
                                  da_ora=bool(d.get("da_ora", False)))
                p["misurata"] = mis
                lo, hi = d.get("min", 0), d.get("max", 1e9)
                if not (lo <= mis <= hi):
                    p["ESITO"] = "FAIL (attesa fra %s e %s)" % (lo, hi)
                    esito["falliti"] += 1
                    esito["passi"].append(p)
                    continue
                p["ESITO"] = "ok"
            diff = {}
            for k, atteso in (passo.get("verifica") or {}).items():
                ott = self._leggi(k)
                if isinstance(atteso, bool):
                    ott = bool(ott)
                if ott != atteso:
                    diff[k] = [atteso, ott]
            p["ESITO"] = "FAIL" if diff else "ok"
            if diff:
                p["differenze"] = diff
                esito["falliti"] += 1
            esito["passi"].append(p)
        esito["ok"] = esito["falliti"] == 0
        return esito


FUNZIONI = {
    "ABS": abs,
    "MAX": max,
    "MIN": min,
    "SQRT": lambda x: x ** 0.5,
    "LIMIT": lambda mn, x, mx: max(mn, min(x, mx)),
    "SEL": lambda g, a, b: b if g else a,
    "MUX": lambda k, *v: v[int(k)] if 0 <= int(k) < len(v) else 0,
    "TRUNC": int,
    "REAL_TO_INT": lambda x: int(round(x)),
    "INT_TO_REAL": float,
    "BOOL_TO_INT": lambda x: 1 if x else 0,
}


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return
    sorgente = open(sys.argv[1], encoding="utf-8-sig").read()
    sc = json.load(open(sys.argv[2], encoding="utf-8-sig"))
    s = SimST(sorgente, tempi=sc.get("tempi"))
    e = s.scenario(sc)
    for p in e["passi"]:
        print("  %2d  %-48s %s" % (p["n"], p["descrizione"][:48],
                                   p.get("ESITO", "")))
        if p.get("differenze"):
            print("      %s" % json.dumps(p["differenze"], ensure_ascii=False)[:150])
    print("\n%s: %s (%d passi, %d falliti)"
          % (e["nome"], "PASS" if e["ok"] else "FAIL", len(e["passi"]), e["falliti"]))
    sys.exit(0 if e["ok"] else 1)


if __name__ == "__main__":
    main()
