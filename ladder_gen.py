"""
ladder_gen.py - Generatore ladderSnippetXML per Sysmac Studio (SYNTECH / Luca)
Creato 26/08/2026 con Claude. Testato su: Ascensore_3Piani, Movimentazione_2Assi.

Genera rung ladder nel formato clipboard proprietario di Sysmac (ladderSnippetXML)
da una specifica JSON compatta. I tipi di FunctionBlock/Function vengono appresi
automaticamente dai template campionati in templates\\ (rung copiati da progetti
reali con sysmac_copy_rung): per insegnare un blocco nuovo basta copiare un rung
che lo contiene e salvarlo nella cartella template.

USO:
  python ladder_gen.py spec.json            -> genera i file XML delle sezioni
  python ladder_gen.py --tipi               -> elenca i tipi FB/F noti dai template
  python ladder_gen.py --autotest           -> autotest interno

SINTASSI SPEC (JSON):
{
  "out_dir": ".",                       # opzionale, default cartella della spec
  "variables": [                        # opzionale -> genera <nome>_vars.txt (TSV)
     {"name":"IN_MARCIA","type":"BOOL","comment":"0=MARCIA ON"},
     {"name":"X_V1","type":"LREAL","init":"700","retain":true}
  ],
  "sections": {
    "Marcia": [
      {"cmt":"GIRO IL BIT DI MARCIA", "chain":["/IN_MARCIA","(Marcia_ON)"]},
      {"cmt":"RITARDO", "chain":["Marcia_ON",
          {"fb":"TON","inst":"Tim_Marcia","p":{"PT":"T#3s"}}]},
      {"cmt":"POWER X", "par":["MC_X.DrvStatus.Ready","MC_X.DrvStatus.ServoOn"],
       "chain":["Tim_Marcia.Q",
          {"fb":"MC_Power","inst":"Power_X","p":{"Axis":"MC_X","OUT:Axis":"MC_X"}}]}
    ]
  }
}

ELEMENTI della catena ("chain", eseguiti in serie):
  "Nome"          contatto N.O.        "/Nome"      contatto N.C.
  "^Nome"         fronte di salita     "/^Nome"     N.C. con fronte (raro)
  "(Nome)"        bobina               "(S Nome)"   bobina SET   "(R Nome)" RESET
  {"fb":"TON","inst":"Tim_1","p":{"PT":"T#3s","OUT:ET":""}}      blocco funzione
  {"f":"=","p":{"In1":"Clock","In2":"INT#1"}}                    funzione (=,>,MOVE,@Inc...)
  {"ist":"X_PRESA:=X_STAZ_A;\nY_PRESA:=Y_STAZ_A;"}               ST inline
  "par": [contatto_A, contatto_B]      parallelo di 2 contatti in TESTA al rung

USCITE MULTIPLE e OR (dal 26/08/2026):
  "out": [ramo, ramo, ...]     piu' rami di uscita in parallelo, ognuno con la
                               propria bobina/FB (es. MC_Power X e Y nello
                               stesso rung). Un ramo e' una lista di elementi
                               in serie, oppure un elemento singolo.
  {"or": [ramo, ramo, ...]}    parallelo verticale a N rami, in QUALUNQUE punto
                               della catena; ogni ramo puo' essere in serie.
  "par": [ramo, ramo, ...]     come prima ma ora senza il limite di 2 contatti:
                               e' un OR in testa al rung.

LIMITI RESIDUI:
  - i rami non si possono annidare a piu' di un livello con "par" (usare "or").
  - pin non-power non collegati -> Variable vuota (ok per Sysmac).
"""
import html
import json
import os
import re
import sys
import uuid
import glob as globmod


def esc(s):
    """escape XML per attributi: indispensabile per i tipi '<', '<=', '<>'"""
    return html.escape(str(s), quote=True)


class LadderGen:
    def __init__(self, templates_dir, pins_json=None):
        self._id = 0x200000
        self.pins = {}            # typename -> [pin dict]
        self.is_function = {}     # typename -> bool
        self.user_type = {}       # typename -> bool (FB definito dall'utente)
        self.from_db = set()      # tipi ricavati dal database, non da template
        self._load_templates(templates_dir)
        if pins_json is None:
            pins_json = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pins.json")
        self._load_pins_json(pins_json)

    PIN_TPL = ('<PinViewModel IsInput="{inp}" Name="{name}" Datatype="{dt}" '
               'Comment="" Negated="false" IsInOutVariable="{io}" '
               'PowerPin="{pw}" Visible="true" EdgeDirectionType="NoEdge" />')

    def _load_pins_json(self, path):
        """firme dei pin ricavate dai progetti reali: usate solo per i tipi
        che non hanno un template campionato."""
        if not os.path.exists(path):
            return
        try:
            data = json.load(open(path, encoding="utf-8"))
        except Exception:
            return
        for tname, info in data.items():
            if tname in self.pins:
                continue          # il template campionato vince
            pins = []
            for p in info.get("pins", []):
                raw = self.PIN_TPL.format(
                    inp=str(bool(p["is_input"])).lower(),
                    name=html.escape(str(p.get("name", "")), quote=True),
                    dt=html.escape(str(p.get("datatype", "BOOL")), quote=True),
                    io=str(bool(p.get("inout"))).lower(),
                    pw=str(bool(p.get("power"))).lower())
                pins.append({"is_input": bool(p["is_input"]), "name": p.get("name", ""),
                             "inout": bool(p.get("inout")), "power": bool(p.get("power")),
                             "raw": raw})
            if not pins:
                continue
            if not any(p["power"] and p["is_input"] for p in pins) or \
               not any(p["power"] and not p["is_input"] for p in pins):
                continue          # senza pin di potenza non e' collegabile al rung
            self.pins[tname] = pins
            self.is_function[tname] = (info.get("kind") == "F")
            self.user_type[tname] = bool(info.get("user"))
            self.from_db.add(tname)

    # ------------------------------------------------ template / pin registry
    def _load_templates(self, tdir):
        for fn in globmod.glob(os.path.join(tdir, "*.xml")):
            try:
                t = open(fn, encoding="utf-8-sig", errors="replace").read()
            except OSError:
                continue
            for m in re.finditer(
                    r'<LadderElement instanceID="0x\w+" ladderElementType="(FunctionBlock|Function)"'
                    r'[^>]*?typeName="([^"]+)"', t):
                kind, tname = m.group(1), m.group(2)
                if tname in self.pins:
                    continue
                blk = t[m.start():t.find("</LadderElement>", m.start())]
                pins = []
                for pm in re.finditer(
                        r'<PinViewModel IsInput="(\w+)" Name="([^"]*)" Datatype="([^"]*)" '
                        r'Comment="([^"]*)" Negated="\w+" IsInOutVariable="(\w+)" '
                        r'PowerPin="(\w+)"[^>]*/>', blk):
                    pins.append({
                        "is_input": pm.group(1) == "true",
                        "name": pm.group(2),
                        "inout": pm.group(5) == "true",
                        "power": pm.group(6) == "true",
                        "raw": pm.group(0),
                    })
                if pins:
                    self.pins[tname] = pins
                    self.is_function[tname] = (kind == "Function")

    # ------------------------------------------------ primitive
    def nid(self):
        self._id += 1
        return f"0x{self._id:08X}"

    def _new_rung(self, comment):
        self.els, self.edges, self.comment = [], [], comment

    def _el(self, xml_open, cps, xml_close='    </LadderElement>\n'):
        eid = self.nid()
        self.els.append({"open": xml_open.replace("@ID@", eid),
                         "cps": cps, "close": xml_close})
        return eid

    def _edge(self, src, tgt, foc=True):
        e = self.nid()
        self.edges.append((e, src, tgt, foc))
        return e

    def _contact(self, var, inv=False, up=False, down=False):
        ci, co = self.nid(), self.nid()
        self._el(
            f'    <LadderElement instanceID="@ID@" ladderElementType="Contact" '
            f'inverted="{str(inv).lower()}" diffUp="{str(up).lower()}" diffDown="{str(down).lower()}" '
            f'elementComment="" variableName="{esc(var)}" baseVariableName="{esc(var)}" '
            f'ProgramName="Programma0" baseVariableDataType="BOOL">\n',
            [(ci, "input", None), (co, "output", None)])
        return ci, co

    def _coil(self, var, mode=""):
        ci, co = self.nid(), self.nid()
        s = "true" if mode == "S" else "false"
        r = "true" if mode == "R" else "false"
        nn = "true" if mode == "N" else "false"
        self._el(
            f'    <LadderElement instanceID="@ID@" ladderElementType="Coil" inverted="{nn}" '
            f'diffUp="false" diffDown="false" set="{s}" reset="{r}" elementComment="" '
            f'variableName="{esc(var)}" baseVariableName="{esc(var)}" ProgramName="Programma0" '
            f'baseVariableDataType="BOOL">\n',
            [(ci, "input", None), (co, "output", None)])
        return ci, co

    def _variable(self, name, direction):
        cp = self.nid()
        self._el(
            f'    <LadderElement instanceID="@ID@" ladderElementType="Variable" '
            f'variableName="{esc(name)}" baseVariableName="{esc(name)}" ProgramName="Programma0">\n',
            [(cp, "output" if direction == "feed" else "input", None)])
        return cp

    def _fblock(self, tname, inst, params):
        if tname not in self.pins:
            raise ValueError(
                f"Tipo '{tname}' sconosciuto: campionare un rung che lo contiene "
                f"(sysmac_copy_rung) e salvarlo nella cartella templates. "
                f"Tipi noti: {', '.join(sorted(self.pins))}")
        pins = self.pins[tname]
        used = {p["name"] for p in pins if p["is_input"]} | \
               {"OUT:" + p["name"] for p in pins if not p["is_input"]}
        for k in params:
            if k not in used:
                raise ValueError(f"{tname}: pin '{k}' inesistente. Pin validi: {sorted(used)}")
        cps = [(self.nid(), "input" if p["is_input"] else "output", p["power"]) for p in pins]
        pinrows = "".join("      " + p["raw"] + "\n" for p in pins)
        if self.is_function[tname]:
            poly = "true" if tname in ("=", ">", "<", ">=", "<=", "<>") else "false"
            openx = (f'    <LadderElement instanceID="@ID@" ladderElementType="Function" '
                     f'elementComment="" typeName="{esc(tname)}" IsPolynomial="{poly}" '
                     f'IsUserDefinedType="false" ArePinsGeneratedByVariableTableOrder="false">\n')
        else:
            udt = "true" if self.user_type.get(tname) else "false"
            openx = (f'    <LadderElement instanceID="@ID@" ladderElementType="FunctionBlock" '
                     f'elementComment="" typeName="{esc(tname)}" IsUserDefinedType="{udt}" '
                     f'ArePinsGeneratedByVariableTableOrder="false" variableName="{esc(inst)}" '
                     f'baseVariableName="{esc(inst)}" ProgramName="Programma0">\n')
        self._el(openx, cps, xml_close=pinrows + '    </LadderElement>\n')
        pin_cp = list(zip([c for c, _, _ in cps], pins))
        p_in = next(c for c, p in pin_cp if p["is_input"] and p["power"])
        p_out = next(c for c, p in pin_cp if not p["is_input"] and p["power"])
        for c, p in pin_cp:
            if p["power"]:
                continue
            key = p["name"] if p["is_input"] else "OUT:" + p["name"]
            var = params.get(key, "")
            if p["is_input"]:
                vcp = self._variable(var, "feed")
                self._edge(vcp, c, foc=False)
            else:
                vcp = self._variable(var, "sink")
                self._edge(c, vcp, foc=False)
        return p_in, p_out

    def _inline_st(self, text):
        ci, co = self.nid(), self.nid()
        txt = html.escape(text, quote=True).replace("\n", "&#xD;&#xA;")
        self._el(
            f'    <LadderElement instanceID="@ID@" '
            f'ladderElementType="InlineStructuredTextServices.InsertInlineST" '
            f'textEntityID="{uuid.uuid4()}" text="{txt}">\n',
            [(ci, "input", None), (co, "output", None)])
        return ci, co

    # ------------------------------------------------ parsing item della spec
    @staticmethod
    def _parse_item(it):
        """stringa/dict della spec -> tupla interna"""
        if isinstance(it, dict):
            if "fb" in it:
                return ("FB", it["fb"], it.get("inst", ""), it.get("p", {}))
            if "f" in it:
                return ("F", it["f"], "", it.get("p", {}))
            if "ist" in it:
                return ("IST", it["ist"])
            if "or" in it:
                return ("OR", [LadderGen._parse_branch(b) for b in it["or"]])
            raise ValueError(f"item dict non riconosciuto: {it}")
        s = str(it).strip()
        m = re.fullmatch(r"\((S |R )?\s*(/?)([^)]+)\)", s)
        if m:
            mode = (m.group(1) or "").strip()
            if m.group(2) == "/":
                mode = "N"
            return ("O", m.group(3).strip(), mode)
        inv = s.startswith("/")
        if inv:
            s = s[1:]
        up = s.startswith("^")
        if up:
            s = s[1:]
        down = (not up) and s.startswith("v") and len(s) > 1 and (s[1].isupper() or s[1] == "_")
        if down:
            s = s[1:]
        return ("C", s, inv, up, down)

    @staticmethod
    def _parse_branch(b):
        """un ramo = lista di item in serie; accetta anche un item singolo"""
        if isinstance(b, list):
            return [LadderGen._parse_item(i) for i in b]
        return [LadderGen._parse_item(b)]

    # ------------------------------------------------ costruzione rung
    # altezze empiriche (px) misurate sui rung reali di Sysmac
    H_FB = 190.0     # blocco funzione/funzione con pin
    H_LINE = 45.0    # riga con soli contatti/bobine
    H_IST_ROW = 22.0

    @classmethod
    def _branch_h(cls, branch):
        """altezza di un ramo (lista di item gia' parsati)"""
        h = cls.H_LINE
        for it in branch:
            k = it[0]
            if k in ("FB", "F"):
                h = max(h, cls.H_FB)
            elif k == "IST":
                h = max(h, 80.0 + cls.H_IST_ROW * (it[1].count("\n") + 2))
            elif k == "OR":
                h = max(h, sum(cls._branch_h(b) for b in it[1]))
        return h

    def _node(self, n_in, n_out):
        """Connection intermedia: n_in CP di ingresso, n_out CP di uscita.
        Un CP porta UN solo edge: per diramare si aggiungono CP."""
        cin = [self.nid() for _ in range(n_in)]
        cout = [self.nid() for _ in range(n_out)]
        self._el('    <LadderElement instanceID="@ID@" ladderElementType="Connection" '
                 'IsLeftPowerRail="false" IsRightPowerRail="false">\n',
                 [(c, "input", None) for c in cin] + [(c, "output", None) for c in cout])
        return cin, cout

    def rung(self, spec):
        self._new_rung(spec.get("cmt", ""))
        chain = [self._parse_item(i) for i in spec.get("chain", [])]
        par = spec.get("par")
        outs = spec.get("out")
        lrail_cps, rrail_cps = [], []
        state = {"head": None, "used": False}

        def sources(cur, n):
            """n punti di partenza a valle di cur (o direttamente dalla barra sx)"""
            if cur == state["head"] and not state["used"]:
                extra = [self.nid() for _ in range(n - 1)]
                lrail_cps.extend(extra)
                return [cur] + extra
            cin, cout = self._node(1, n)
            self._edge(cur, cin[0])
            return cout

        def run(items, cur):
            for it in items:
                k = it[0]
                if k == "OR":
                    branches = it[1]
                    srcs = sources(cur, len(branches))
                    ends = [run(br, s) for br, s in zip(branches, srcs)]
                    cin, cout = self._node(len(branches), 1)
                    for e, c in zip(ends, cin):
                        self._edge(e, c)
                    cur = cout[0]
                    state["used"] = True
                    continue
                if k == "C":
                    ci, co = self._contact(it[1], it[2], it[3], it[4] if len(it) > 4 else False)
                elif k == "O":
                    ci, co = self._coil(it[1], it[2])
                elif k == "FB":
                    ci, co = self._fblock(it[1], it[2], it[3])
                elif k == "F":
                    ci, co = self._fblock(it[1], "", it[3])
                elif k == "IST":
                    ci, co = self._inline_st(it[1])
                else:
                    raise ValueError(f"elemento non gestito: {it}")
                self._edge(cur, ci)
                state["used"] = True
                cur = co
            return cur

        cp0 = self.nid()
        lrail_cps.append(cp0)
        state["head"] = cp0
        cur = cp0

        if par:
            branches = [self._parse_branch(b) for b in par]
            cur = run([("OR", branches)], cur)

        def to_right(end):
            rr = self.nid()
            rrail_cps.append(rr)
            self._edge(end, rr)

        out_branches = [self._parse_branch(b) for b in outs] if outs else []

        # nodo unico: OR in coda alla catena + piu' uscite -> una sola Connection
        # (n_in rami dell'OR, n_out rami di uscita). Due Connection in cascata
        # fanno sovrapporre graficamente i blocchi in Sysmac.
        if len(out_branches) > 1 and chain and chain[-1][0] == "OR":
            cur = run(chain[:-1], cur)
            or_branches = chain[-1][1]
            srcs = sources(cur, len(or_branches))
            ends = [run(br, s) for br, s in zip(or_branches, srcs)]
            cin, cout = self._node(len(or_branches), len(out_branches))
            for e, c in zip(ends, cin):
                self._edge(e, c)
            for br, s in zip(out_branches, cout):
                to_right(run(br, s))
        else:
            cur = run(chain, cur)
            if out_branches:
                if len(out_branches) == 1:
                    to_right(run(out_branches[0], cur))
                else:
                    srcs = sources(cur, len(out_branches))
                    for br, s in zip(out_branches, srcs):
                        to_right(run(br, s))
            else:
                to_right(cur)

        by_cp = {}
        for (e, s, t, f) in self.edges:
            by_cp.setdefault(s, []).append(e)
            by_cp.setdefault(t, []).append(e)

        def cpxml(cpid, tp, power):
            pw = "" if power is None else f' PowerPin="{str(power).lower()}"'
            out = f'      <ConnectionPoint connectionPointType="{tp}" instanceID="{cpid}"{pw}>\n'
            for e in by_cp.get(cpid, []):
                out += f'        <Edge instanceID="{e}" />\n'
            return out + '      </ConnectionPoint>\n'

        body = f'    <LadderElement instanceID="{self.nid()}" ladderElementType="Connection" ' \
               f'IsLeftPowerRail="true" IsRightPowerRail="false">\n'
        for c in lrail_cps:
            body += cpxml(c, "output", None)
        body += '    </LadderElement>\n'
        body += f'    <LadderElement instanceID="{self.nid()}" ladderElementType="Connection" ' \
                f'IsLeftPowerRail="false" IsRightPowerRail="true">\n'
        for c in rrail_cps:
            body += cpxml(c, "input", None)
        body += '    </LadderElement>\n'
        for el in self.els:
            body += el["open"]
            for (cpid, tp, power) in el["cps"]:
                body += cpxml(cpid, tp, power)
            body += el["close"]
        for (e, s, t, f) in self.edges:
            body += (f'    <LadderElement instanceID="{e}" ladderElementType="Edge" '
                     f'sourceID="{s}" targetID="{t}" Focusable="{str(f).lower()}" />\n')
        cmt = html.escape(self.comment, quote=True)
        h_chain = self._branch_h(chain) if chain else self.H_LINE
        if par:
            h_chain += sum(self._branch_h(self._parse_branch(b)) for b in par)
        if outs:
            h_out = sum(self._branch_h(self._parse_branch(b)) for b in outs)
        else:
            h_out = 0.0
        h = 60.0 + max(h_chain, self.H_LINE) + h_out
        return f'  <RungXML Comment="{cmt}" Label="" Height="{h}" Width="1100">\n{body}  </RungXML>\n'

    # ------------------------------------------------ verifica coerenza
    @staticmethod
    def validate(xml):
        errs = []
        for i, r in enumerate(xml.split("<RungXML")[1:]):
            edge_full = re.findall(
                r'<LadderElement instanceID="(0x\w+)" ladderElementType="Edge" '
                r'sourceID="(0x\w+)" targetID="(0x\w+)"', r)
            cpids = set(re.findall(r'connectionPointType="(?:input|output)" instanceID="(0x\w+)"', r))
            declared = {c: re.findall(r'Edge instanceID="(0x\w+)"', b)
                        for c, b in re.findall(
                            r'<ConnectionPoint connectionPointType="\w+" instanceID="(0x\w+)"[^>]*>'
                            r'((?:\s*<Edge instanceID="0x\w+" />)+)', r)}
            eids = {e[0] for e in edge_full}
            for (eid, s, t) in edge_full:
                if s not in cpids or t not in cpids:
                    errs.append(f"rung {i}: edge {eid} -> CP inesistente")
                for ep in (s, t):
                    if eid not in declared.get(ep, []):
                        errs.append(f"rung {i}: edge {eid} non dichiarato in CP {ep}")
            for c, el in declared.items():
                for e in el:
                    if e not in eids:
                        errs.append(f"rung {i}: CP {c} dichiara edge inesistente")
            empty = [c for c in cpids if c not in declared]
            if empty:
                errs.append(f"rung {i}: {len(empty)} CP senza edge")
        return errs


def vars_tsv(variables):
    rows = []
    for v in variables:
        rows.append("\t".join([
            v["name"], v.get("type", "BOOL"), str(v.get("init", "")), "",
            "True" if v.get("retain") else "False",
            "True" if v.get("const") else "False",
            v.get("comment", "")]))
    return "\r\n".join(rows)


DEFAULT_TEMPLATES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")


def build_spec(spec_path):
    spec = json.load(open(spec_path, encoding="utf-8-sig"))
    out_dir = spec.get("out_dir") or os.path.dirname(os.path.abspath(spec_path))
    g = LadderGen(spec.get("templates_dir", DEFAULT_TEMPLATES))
    report = []
    for name, rungs in spec.get("sections", {}).items():
        xml = "<Rungs>\n"
        for rs in rungs:
            if isinstance(rs, str) and rs.startswith("@file:"):
                raw = open(os.path.join(out_dir, rs[6:]), encoding="utf-8-sig").read()
                m = re.search(r'(  <RungXML.*</RungXML>)', raw, re.S)
                xml += m.group(1) + "\n"
                continue
            xml += g.rung(rs)
        xml += "</Rungs>"
        errs = LadderGen.validate(xml)
        if errs:
            raise SystemExit(f"SEZIONE {name}: ERRORI DI COERENZA:\n" + "\n".join(errs))
        out = os.path.join(out_dir, f"sec_{name}.xml")
        open(out, "w", encoding="utf-8").write(xml)
        report.append(f"{name}: {len(rungs)} rung -> {out} ({len(xml)} byte) OK")
    if spec.get("variables"):
        vout = os.path.join(out_dir, "vars.txt")
        open(vout, "w", encoding="utf-8").write(vars_tsv(spec["variables"]))
        report.append(f"variabili: {len(spec['variables'])} -> {vout}")
    return "\n".join(report)


def autotest():
    g = LadderGen(DEFAULT_TEMPLATES)
    xml = "<Rungs>\n"
    xml += g.rung({"cmt": "TEST 1", "chain": ["/IN_A", "^IN_B", "(S OUT_X)"]})
    xml += g.rung({"cmt": "TEST 2", "par": ["IN_C", "Mem_C"],
                   "chain": ["/IN_D", "(Mem_C)"]})
    if "TON" in g.pins:
        xml += g.rung({"cmt": "TEST 3", "chain": [
            "IN_E", {"fb": "TON", "inst": "Tim_T", "p": {"PT": "T#1s"}}]})
    if "=" in g.pins:
        xml += g.rung({"cmt": "TEST 4", "chain": [
            "IN_F", {"f": "=", "p": {"In1": "Cnt", "In2": "INT#3"}}, "(OUT_Y)"]})
    xml += g.rung({"cmt": "TEST 5", "chain": [
        "P_On", {"ist": "A:=B+1;\nC:=D*2;"}]})
    xml += "</Rungs>"
    errs = LadderGen.validate(xml)
    print(f"autotest: {xml.count('<RungXML')} rung, {len(xml)} byte, "
          f"{'OK' if not errs else 'ERRORI: ' + '; '.join(errs)}")
    print("tipi noti:", ", ".join(sorted(g.pins)) or "(nessun template)")
    return 0 if not errs else 1


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] == "--autotest":
        sys.exit(autotest())
    if sys.argv[1] == "--tipi":
        g = LadderGen(DEFAULT_TEMPLATES)
        for t in sorted(g.pins):
            kind = "F " if g.is_function[t] else "FB"
            ins = [p["name"] for p in g.pins[t] if p["is_input"] and not p["power"]]
            outs = [p["name"] for p in g.pins[t] if not p["is_input"] and not p["power"]]
            print(f"{kind} {t:<18} in: {', '.join(ins) or '-'}  out: {', '.join(outs) or '-'}")
        sys.exit(0)
    print(build_spec(sys.argv[1]))
