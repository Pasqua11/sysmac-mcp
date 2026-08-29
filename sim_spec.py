# -*- coding: utf-8 -*-
"""
sim_spec.py - esegue la LOGICA di una spec ladder senza Sysmac
28/08/2026

Perche' esiste: il 28/08 un errore logico nel semaforo (due chiamate pedonali
invertite) e' costato 20 minuti di simulazione in Sysmac per emergere e 6 per
essere corretto. La stessa spec, eseguita qui, lo mostra in meno di un secondo.

Interpreta la struttura della spec usata da ladder_gen:
  contatti   "Nome"  "/Nome" (NC)  "^Nome" (fronte salita)  "vNome" (discesa)
  bobine     "(Nome)"  "(S Nome)"  "(R Nome)"  "(/Nome)" (negata)
  parallelo  {"or": [ramo, ramo, ...]}      ramo = stringa o lista in serie
  uscite     "out": [[ramo], [ramo], ...]   rami in parallelo a fine catena
  blocchi    {"fb": "TON", "inst": "T1", "p": {"PT": "SET_T"}}
  funzioni   {"f": "Get1sClk"} {"f": "@Inc", "p": {"InOut": "N", "OUT:InOut": "N"}}

Scansione ciclica come il PLC: i rung si valutano in ordine, una volta per scan.

Uso:
    from sim_spec import SimSpec
    s = SimSpec("semaforo_spec.json", tempi={"SET_T_Verde_NS": 25.0, ...})
    s.set(IN_Marcia=True, V_S_Auto=True)
    s.corri(60)                       # 60 secondi simulati
    s.leggi("OUT_NS_Verde")
    esito = s.scenario(json.load(open("semaforo_scenario.json")))

    python sim_spec.py <spec.json> <scenario.json>     -> PASS/FAIL
"""
import json, re, sys, os

SCAN = 0.01          # 10 ms di scansione simulata


def _durata(v):
    """'T#25s' / 'T#1500ms' / 25 -> secondi (float)."""
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().upper().replace("T#", "")
    tot, num = 0.0, ""
    for ch in s:
        if ch.isdigit() or ch == ".":
            num += ch
        else:
            num += "|" + ch
    for pezzo in [p for p in re.findall(r"([\d.]+)\|?([A-Z]*)", s) if p[0]]:
        val, u = float(pezzo[0]), pezzo[1]
        if u.startswith("MS"):
            tot += val / 1000.0
        elif u.startswith("S"):
            tot += val
        elif u.startswith("M"):
            tot += val * 60
        elif u.startswith("H"):
            tot += val * 3600
        else:
            tot += val
    return tot


class SimSpec:
    def __init__(self, spec, tempi=None, sezione=None):
        if isinstance(spec, str):
            spec = json.load(open(spec, encoding="utf-8-sig"))
        self.spec = spec
        sezioni = spec.get("sections", {})
        # Senza indicazione si eseguono TUTTE le sezioni, nell'ordine in cui
        # sono dichiarate: e' quello che fa il PLC. Prima ne veniva presa solo
        # la prima e su un programma a 8 sezioni si simulava il 12% del codice
        # senza che nulla lo segnalasse (28/08/2026).
        if sezione:
            self.rung = sezioni[sezione]
        else:
            self.rung = [r for nome in sezioni for r in sezioni[nome]]
        self.sezioni_usate = [sezione] if sezione else list(sezioni)
        self.v = {}                  # variabili booleane e numeriche
        self.t = 0.0                 # tempo simulato
        self.ton = {}                # istanza TON -> {"start":, "q":, "et":}
        self.fronti = {}             # memoria per ^ e v
        self.tempi = {k: _durata(x) for k, x in (tempi or {}).items()}
        self.log = []                # timeline dei cambiamenti
        self._osserva = None
        self._ctx = ""               # posizione nel programma: identifica il fronte

    # ------------------------------------------------------------ accessori
    def set(self, **kw):
        for k, x in kw.items():
            self.v[k] = x
        return self

    def leggi(self, *nomi):
        if len(nomi) == 1:
            return self.v.get(nomi[0], False)
        return {n: self.v.get(n, False) for n in nomi}

    def _val(self, nome):
        """Valore di un operando: costante numerica, tempo, o variabile."""
        if isinstance(nome, (int, float, bool)):
            return nome
        s = str(nome).strip()
        if s in self.tempi:
            return self.tempi[s]
        if re.fullmatch(r"-?\d+", s):
            return int(s)
        if re.fullmatch(r"-?\d*\.\d+", s):
            return float(s)
        if s.upper().startswith("T#"):
            return _durata(s)
        if "." in s:                                   # es. Tim_X.Q
            base, campo = s.split(".", 1)
            st = self.ton.get(base, {})
            return st.get("q", False) if campo.upper() == "Q" else st.get("et", 0.0)
        return self.v.get(s, False)

    # ------------------------------------------------- valutazione elementi
    def _contatto(self, s):
        neg = s.startswith("/")
        if neg:
            s = s[1:]
        up = s.startswith("^")
        if up:
            s = s[1:]
        down = (not up) and s.startswith("v") and len(s) > 1 and (s[1].isupper() or s[1] == "_")
        if down:
            s = s[1:]
        if s == "P_On":
            val = True
        elif s == "P_Off":
            val = False
        elif "." in s:                                   # es. Tim_F1.Q
            base, campo = s.split(".", 1)
            st = self.ton.get(base, {})
            val = st.get("q", False) if campo.upper() == "Q" else st.get("et", 0.0)
        else:
            val = bool(self.v.get(s, False))
        if up or down:
            chiave = "%s|%s" % (self._ctx, s)
            prec = self.fronti.get(chiave, False)
            self.fronti[chiave] = bool(val)
            val = (val and not prec) if up else (prec and not val)
        return (not val) if neg else bool(val)

    def _bobina(self, s, potenza):
        m = re.fullmatch(r"\((S |R )?\s*(/?)([^)]+)\)", s.strip())
        mode = (m.group(1) or "").strip()
        nome = m.group(3).strip()
        if m.group(2) == "/":
            self.v[nome] = not potenza
        elif mode == "S":
            if potenza:
                self.v[nome] = True
        elif mode == "R":
            if potenza:
                self.v[nome] = False
        else:
            self.v[nome] = potenza

    def _blocco(self, el, potenza):
        """TON e funzioni. Ritorna la potenza in uscita."""
        if "fb" in el:
            tipo, inst = el["fb"], el.get("inst", "")
            p = el.get("p", {})
            if tipo == "TON":
                st = self.ton.setdefault(inst, {"start": None, "q": False, "et": 0.0})
                pt = self._val(p.get("PT", 0)) if isinstance(p.get("PT"), str) else _durata(p.get("PT", 0))
                if not isinstance(pt, (int, float)):
                    pt = 0.0
                if potenza:
                    if st["start"] is None:
                        st["start"] = self.t
                    st["et"] = self.t - st["start"]
                    st["q"] = st["et"] >= pt
                else:
                    st["start"], st["q"], st["et"] = None, False, 0.0
                return st["q"]
            return potenza                     # altri FB: passanti in simulazione
        if "f" in el:
            f, p = el["f"], el.get("p", {})
            if f in ("Get1sClk", "Get100msClk", "Get1minClk", "Get10msClk"):
                periodo = {"Get1sClk": 1.0, "Get100msClk": 0.1,
                           "Get1minClk": 60.0, "Get10msClk": 0.01}[f]
                return (self.t % periodo) < (periodo / 2)
            if f in ("@Inc", "Inc") and potenza:
                n = p.get("InOut")
                if n:
                    self.v[n] = int(self.v.get(n, 0)) + 1
                return potenza
            if f in ("=", "<>", "<", ">", "<=", ">=", "EQ", "NE", "LT", "GT", "LE", "GE"):
                a, b = self._val(p.get("In1")), self._val(p.get("In2"))
                try:
                    a, b = float(a), float(b)
                except (TypeError, ValueError):
                    return False
                confronto = {"=": a == b, "EQ": a == b, "<>": a != b, "NE": a != b,
                             "<": a < b, "LT": a < b, ">": a > b, "GT": a > b,
                             "<=": a <= b, "LE": a <= b, ">=": a >= b, "GE": a >= b}[f]
                return potenza and confronto
            if f in ("MOVE", "@MOVE") and potenza:
                src, dst = p.get("In"), p.get("OUT:Out") or p.get("Out")
                if src is not None and dst:
                    self.v[dst] = self._val(src) if isinstance(src, str) else src
                return potenza
            return potenza
        return potenza

    def _elemento(self, el, potenza):
        if isinstance(el, dict):
            if "or" in el:
                risultato = False
                for ramo in el["or"]:
                    risultato = self._ramo(ramo, potenza) or risultato
                return risultato
            return self._blocco(el, potenza)
        s = str(el).strip()
        if s.startswith("("):
            self._bobina(s, potenza)
            return potenza
        return potenza and self._contatto(s)

    def _ramo(self, ramo, potenza):
        if not isinstance(ramo, list):
            ramo = [ramo]
        p = potenza
        for el in ramo:
            p = self._elemento(el, p)
        return p

    # --------------------------------------------------------------- motore
    def _scan(self):
        for i, r in enumerate(self.rung):
            p = True
            for j, el in enumerate(r.get("chain", [])):
                self._ctx = "r%d.c%d" % (i, j)
                p = self._elemento(el, p)
            for k, ramo in enumerate(r.get("out", [])):
                self._ctx = "r%d.o%d" % (i, k)
                self._ramo(ramo, p)

    def corri(self, secondi, osserva=None):
        """Avanza la simulazione. `osserva` = lista di variabili da tracciare."""
        if osserva:
            self._osserva = osserva
            prec = {k: self.leggi(k) for k in osserva}
            self.log.append({"t": round(self.t, 3), "valori": dict(prec)})
        fine = self.t + secondi
        while self.t < fine:
            self._scan()
            self.t += SCAN
            if osserva:
                ora = {k: self.leggi(k) for k in osserva}
                if ora != prec:
                    self.log.append({"t": round(self.t, 3), "valori": dict(ora)})
                    prec = ora
        return self

    def durata(self, var, valore=True, tmax=300, da_ora=False):
        """Quanto resta `var` al valore indicato, agganciando il FRONTE:
        aspetta prima lo stato opposto, poi misura. Errore classico del
        28/08: misurare da uno stato gia' attivo dava 0,4 s invece di 8."""
        t0 = self.t
        if not da_ora:
            # aspetta il FRONTE: prima lo stato opposto, poi l'inizio vero
            while self.leggi(var) == valore and self.t - t0 < tmax:
                self._scan(); self.t += SCAN
            while self.leggi(var) != valore and self.t - t0 < tmax:
                self._scan(); self.t += SCAN
        inizio = self.t
        while self.leggi(var) == valore and self.t - t0 < tmax:
            self._scan(); self.t += SCAN
        return round(self.t - inizio, 3)

    # ------------------------------------------------------------- scenario
    def scenario(self, sc):
        """Stesso formato di sysmac_api.collauda(): set / attendi / verifica /
        watch / durata. Ritorna un esito PASS-FAIL."""
        if isinstance(sc, str):
            sc = json.load(open(sc, encoding="utf-8-sig"))
        esito = {"nome": sc.get("nome", "scenario"), "dove": "python", "passi": [],
                 "ok": True, "falliti": 0}
        for k, passo in enumerate(sc.get("passi", []), 1):
            voce = {"n": k, "t": round(self.t, 2)}
            if "descrizione" in passo:
                voce["descrizione"] = passo["descrizione"]
            if "set" in passo:
                self.set(**passo["set"]); voce["set"] = passo["set"]
            if "attendi" in passo:
                self.corri(float(passo["attendi"])); voce["attendi"] = passo["attendi"]
            if "impulso" in passo:                   # pulsante: ON breve poi OFF
                for n in passo["impulso"]:
                    self.set(**{n: True})
                self.corri(0.3)
                for n in passo["impulso"]:
                    self.set(**{n: False})
                voce["impulso"] = passo["impulso"]
            if "durata" in passo:
                d = passo["durata"]
                mis = self.durata(d["variabile"], d.get("valore", True),
                                  da_ora=bool(d.get("da_ora", False)))
                voce["misurata"] = mis
                lo, hi = d.get("min", 0), d.get("max", 1e9)
                if not (lo <= mis <= hi):
                    voce["ESITO"] = "FAIL (attesa fra %s e %s)" % (lo, hi)
                    esito["ok"] = False; esito["falliti"] += 1
                else:
                    voce["ESITO"] = "ok"
            if "verifica" in passo:
                atteso = passo["verifica"]
                letti = {n: self.leggi(n) for n in atteso}
                diff = {n: (atteso[n], letti[n]) for n in atteso if bool(letti[n]) != bool(atteso[n])}
                voce["verifica"] = letti
                if diff:
                    voce["ESITO"] = "FAIL " + json.dumps(diff)
                    esito["ok"] = False; esito["falliti"] += 1
                else:
                    voce["ESITO"] = "ok"
            esito["passi"].append(voce)
        return esito


def main():
    if len(sys.argv) < 3:
        print(__doc__); return
    spec, scen = sys.argv[1], sys.argv[2]
    sc = json.load(open(scen, encoding="utf-8-sig"))
    s = SimSpec(spec, tempi=sc.get("tempi", {}))
    e = s.scenario(sc)
    for p in e["passi"]:
        print("  %2d  %-46s %s" % (p["n"], p.get("descrizione", "")[:46],
                                    p.get("ESITO", p.get("misurata", ""))))
    print("\n%s: %s (%d passi, %d falliti)" %
          (e["nome"], "PASS" if e["ok"] else "FAIL", len(e["passi"]), e["falliti"]))
    sys.exit(0 if e["ok"] else 1)


if __name__ == "__main__":
    main()
