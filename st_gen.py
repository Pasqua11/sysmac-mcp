# -*- coding: utf-8 -*-
"""
st_gen.py - genera Structured Text dalla STESSA specifica che produce il ladder.

La spec e' quella gia' in uso con ladder_gen: liste di rung fatti di `chain`,
`or`, `out`, blocchi funzione e funzioni. Qui invece dei rung esce testo ST.

Perche' conviene averli entrambi dalla stessa fonte:
  - si sceglie il linguaggio in base a cosa conviene, non a cosa so generare
  - la traduzione si verifica da sola: lo stesso scenario di collaudo deve
    dare lo stesso esito sul ladder (sim_spec) e sull'ST (sim_st)

Traduzione:
    "A"                     A
    "/A"                    NOT A
    "^A"                    (A AND NOT _fp_A)        fronte di salita
    "vA"                    (NOT A AND _fp_A)        fronte di discesa
    {"or": [x, y]}          (x OR y)
    [a, b]  dentro un or    (a AND b)
    "(X)"                   X := <condizione>;
    "(S X)" / "(R X)"       IF <condizione> THEN X := TRUE/FALSE; END_IF;
    {"fb": "TON", ...}      Tim(In := <condizione>, PT := ...);  poi Tim.Q
    {"f": "@Inc", ...}      X := X + 1;   sotto condizione
    {"f": "MOVE", ...}      X := <In>;    sotto condizione
    {"f": ">=", ...}        (a >= b)      confronto dentro la condizione

Le memorie dei fronti (`_fp_<nome>`) vengono dichiarate e aggiornate in fondo
al programma, dopo tutti gli usi: e' l'unico modo di riprodurre in ST il
comportamento del contatto di fronte del ladder.

Uso:
    python st_gen.py lavaggio4_spec.json          -> lavaggio4.st
    python st_gen.py cfe_spec.json Allarmi        -> solo quella sezione
"""
import io
import json
import os
import re
import sys

CONFRONTI = {"=": "=", "<>": "<>", "<": "<", ">": ">", "<=": "<=", ">=": ">="}


class GeneratoreST(object):
    def __init__(self, spec):
        if isinstance(spec, str):
            with open(spec, encoding="utf-8-sig") as f:
                spec = json.load(f)
        self.spec = spec
        self.fronti = []          # nomi che richiedono una memoria di fronte
        self.righe = []
        self.prima = []           # chiamate da emettere prima della condizione

    # ------------------------------------------------------------- espressioni
    def _memoria_fronte(self, nome):
        pulito = "_fp_" + re.sub(r"[^A-Za-z0-9_]", "_", nome)
        # self.fronti contiene tuple: il confronto va fatto sul primo campo,
        # altrimenti la stessa memoria finisce dichiarata piu' volte
        if pulito not in [m for m, _ in self.fronti]:
            self.fronti.append((pulito, nome))
        return pulito

    def _contatto(self, s):
        s = s.strip()
        if s.startswith("/"):
            return "NOT %s" % s[1:]
        if s.startswith("^"):
            n = s[1:]
            return "(%s AND NOT %s)" % (n, self._memoria_fronte(n))
        if s.startswith("v"):
            # attenzione: solo se e' davvero un fronte di discesa, cioe' se il
            # resto e' un nome valido. I nomi che cominciano per v sono comuni.
            n = s[1:]
            if n and (n[0].isupper() or n[0] == "_"):
                return "(NOT %s AND %s)" % (n, self._memoria_fronte(n))
        return s

    def _elemento(self, el, condizione):
        """Un elemento della catena. Restituisce l'espressione che il flusso
        assume dopo di esso, oppure None se l'elemento non e' una condizione
        (per esempio una bobina o una funzione di scrittura)."""
        if isinstance(el, str):
            s = el.strip()
            if s.startswith("("):
                return None                     # bobina: gestita a parte
            return self._contatto(s)

        if isinstance(el, list):
            parti = [self._elemento(e, condizione) for e in el]
            parti = [p for p in parti if p]
            return "(%s)" % " AND ".join(parti) if parti else "TRUE"

        if "or" in el:
            rami = []
            for r in el["or"]:
                v = self._elemento(r, condizione)
                if v:
                    rami.append(v)
            return "(%s)" % " OR ".join(rami) if rami else "FALSE"

        if "fb" in el:
            inst = el.get("inst") or el["fb"]
            p = dict(el.get("p") or {})
            arg = ["In := %s" % (condizione or "TRUE")]
            for k, v in p.items():
                if k.startswith("OUT:"):
                    continue
                arg.append("%s := %s" % (k, self._valore(v)))
            self.prima.append("%s(%s);" % (inst, ", ".join(arg)))
            return "%s.Q" % inst

        if "f" in el:
            f = el["f"]
            p = dict(el.get("p") or {})
            if f in CONFRONTI:
                return "(%s %s %s)" % (self._valore(p.get("In1")), CONFRONTI[f],
                                       self._valore(p.get("In2")))
            if f in ("@Inc", "Inc"):
                dest = p.get("OUT:InOut") or p.get("InOut")
                return ("SCRITTURA", "%s := %s + 1;" % (dest, dest))
            if f in ("@Dec", "Dec"):
                dest = p.get("OUT:InOut") or p.get("InOut")
                return ("SCRITTURA", "%s := %s - 1;" % (dest, dest))
            if f == "MOVE":
                dest = p.get("OUT:Out") or p.get("Out")
                return ("SCRITTURA", "%s := %s;" % (dest, self._valore(p.get("In"))))
            # funzione non prevista: la si scrive come chiamata, cosi' salta
            # all'occhio invece di sparire
            arg = ", ".join("%s := %s" % (k, self._valore(v))
                            for k, v in p.items() if not k.startswith("OUT:"))
            return ("SCRITTURA", "// DA COMPLETARE: %s(%s);" % (f, arg))
        return None

    @staticmethod
    def _valore(v):
        if v is None:
            return "0"
        if isinstance(v, bool):
            return "TRUE" if v else "FALSE"
        return str(v)

    # ------------------------------------------------------------------ rung
    def rung(self, r):
        self.prima = []
        catena = list(r.get("chain") or [])
        bobine = []
        scritture = []
        condizioni = []

        for el in catena:
            if isinstance(el, str) and el.strip().startswith("("):
                bobine.append(el.strip()[1:-1].strip())
                continue
            v = self._elemento(el, self._unisci(condizioni))
            if isinstance(v, tuple):
                scritture.append(v[1])
            elif v:
                condizioni.append(v)

        cond = self._unisci(condizioni)

        for gruppo in (r.get("out") or []):
            for el in gruppo:
                if isinstance(el, str) and el.strip().startswith("("):
                    bobine.append(el.strip()[1:-1].strip())
                else:
                    v = self._elemento(el, cond)
                    if isinstance(v, tuple):
                        scritture.append(v[1])

        if r.get("cmt"):
            self.righe.append("// %s" % r["cmt"])
        self.righe.extend(self.prima)

        semplici = [b for b in bobine if not b.startswith(("S ", "R "))]
        speciali = [b for b in bobine if b.startswith(("S ", "R "))]

        for b in semplici:
            self.righe.append("%s := %s;" % (b, cond or "TRUE"))

        if speciali or scritture:
            corpo = []
            for b in speciali:
                nome = b[2:].strip()
                corpo.append("%s := %s;" % (nome, "TRUE" if b[0] == "S" else "FALSE"))
            corpo.extend(scritture)
            if cond and cond != "TRUE":
                self.righe.append("IF %s THEN" % cond)
                self.righe.extend("    " + c for c in corpo)
                self.righe.append("END_IF;")
            else:
                self.righe.extend(corpo)
        self.righe.append("")

    @staticmethod
    def _unisci(parti):
        parti = [p for p in parti if p]
        if not parti:
            return ""
        if len(parti) == 1:
            return parti[0]
        return " AND ".join(parti)

    # -------------------------------------------------------------- programma
    def genera(self, sezione=""):
        sezioni = self.spec.get("sections", {})
        nomi = [sezione] if sezione else list(sezioni)
        self.righe = []
        for n in nomi:
            self.righe.append("//" + "=" * 74)
            self.righe.append("//  SEZIONE %s" % n.upper())
            self.righe.append("//" + "=" * 74)
            self.righe.append("")
            for r in sezioni[n]:
                self.rung(r)

        if self.fronti:
            self.righe.append("//" + "-" * 74)
            self.righe.append("// Memorie dei fronti: aggiornate alla FINE, dopo tutti gli usi.")
            self.righe.append("// E' cosi' che il contatto di fronte del ladder si rende in ST.")
            self.righe.append("//" + "-" * 74)
            for mem, nome in self.fronti:
                self.righe.append("%s := %s;" % (mem, nome))
        return "\n".join(self.righe)

    def variabili_fronti(self):
        """Le memorie da dichiarare fra le variabili interne."""
        return [(m, "BOOL", "memoria di fronte per %s" % n) for m, n in self.fronti]


def genera(spec, sezione=""):
    g = GeneratoreST(spec)
    testo = g.genera(sezione)
    return testo, g.variabili_fronti()


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if len(sys.argv) < 2:
        print(__doc__)
        return
    spec = sys.argv[1]
    sezione = sys.argv[2] if len(sys.argv) > 2 else ""
    testo, extra = genera(spec, sezione)
    fuori = os.path.splitext(spec)[0].replace("_spec", "") + ".st"
    with open(fuori, "w", encoding="utf-8") as f:
        f.write(testo)
    print("%s -> %s" % (spec, fuori))
    print("righe: %d | memorie di fronte da dichiarare: %d"
          % (len(testo.splitlines()), len(extra)))
    for n, t, c in extra:
        print("   %s\t%s\t%s" % (n, t, c))


if __name__ == "__main__":
    main()
