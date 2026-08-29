# -*- coding: utf-8 -*-
"""
rung2spec.py - converte i rung ladder dei progetti Sysmac (database offline)
nella spec JSON di ladder_gen.py.

Formato sorgente (un JSON per riga in <sezione>.xml):
  CLs: elementi. Ognuno ha X (colonna, default 0) e Y (riga, default 0) e
       collega il nodo (X,Y) al nodo (X+1,Y).
       __type: LD contatto | ST bobina | FB blocco | F funzione |
               HL filo orizzontale | IST ST inline
  VLs: montanti verticali {X, Y}: uniscono il nodo (X,Y) al nodo (X,Y+1).
  LRI/RRI: indici barra sinistra/destra.

Metodo: griglia -> union-find sui montanti -> grafo di archi -> riduzione
serie/parallelo -> spec {chain, or, out}.

USO:
  python rung2spec.py --progetto <guid> [--out cartella]
  python rung2spec.py --tutti [--out cartella]      (progetti deduplicati per versione)
  python rung2spec.py --report                       (solo statistiche di copertura)
"""
import json, os, re, sys, argparse, collections

SOL = r"C:\OMRON\Data\Solution"


# --------------------------------------------------------------- union-find
class UF:
    def __init__(self):
        self.p = {}

    def find(self, x):
        self.p.setdefault(x, x)
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[rb] = ra


# --------------------------------------------------------------- elementi
def el_to_spec(el):
    """elemento Sysmac -> item della spec. Ritorna (item, kind) o (None, motivo)."""
    t = el.get("__type")
    if t == "HL":
        return None, "HL"
    if t == "LD":
        v = el.get("Var", "")
        if el.get("Not"):
            v = "/" + v
        if el.get("Up"):
            v = "^" + v
        if el.get("Dwn"):
            return "v" + v, "C"
        return v, "C"
    if t == "ST":
        v = el.get("Var", "")
        if el.get("Not"):
            return "(/%s)" % v, "O"
        if el.get("S"):
            return "(S %s)" % v, "O"
        if el.get("RS"):
            return "(R %s)" % v, "O"
        return "(%s)" % v, "O"
    if t == "IST":
        return {"ist": el.get("TXT", "")}, "IST"
    if t in ("FB", "F"):
        p = {}
        for pin in el.get("In", []):
            if pin.get("__type") == "PRM" and pin.get("Var", "") != "":
                p[pin["Arg"]] = pin["Var"]
        for pin in el.get("Out", []):
            if pin.get("__type") == "PRM" and pin.get("Var", "") != "":
                p["OUT:" + pin["Arg"]] = pin["Var"]
        if t == "FB":
            return {"fb": el.get("Name", ""), "inst": el.get("Var", ""), "p": p}, "FB"
        return {"f": el.get("Name", ""), "p": p}, "F"
    return None, "tipo elemento sconosciuto: %s" % t


# --------------------------------------------------------------- grafo
class Fail(Exception):
    pass


def build_graph(rung):
    """restituisce (archi, src, snk); arco = (nodo_u, nodo_v, payload)"""
    cls = rung.get("CLs", [])
    if not cls:
        raise Fail("rung vuoto")
    uf = UF()
    for vl in rung.get("VLs", []):
        x, y = vl.get("X", 0), vl.get("Y", 0)
        uf.union(("N", x, y), ("N", x, y + 1))

    maxx = max(el.get("X", 0) for el in cls)
    edges = []
    rows_at_0, rows_at_max = set(), set()
    for el in cls:
        x, y = el.get("X", 0), el.get("Y", 0)
        item, kind = el_to_spec(el)
        if kind not in ("HL", "C", "O", "FB", "F", "IST"):
            raise Fail(kind)
        edges.append((("N", x, y), ("N", x + 1, y), (item, kind, y)))
        if x == 0:
            rows_at_0.add(y)
        if x == maxx:
            rows_at_max.add(y)

    if not rows_at_0:
        raise Fail("nessun elemento sulla prima colonna")
    src = ("N", 0, min(rows_at_0))
    for y in rows_at_0:
        uf.union(src, ("N", 0, y))
    snk = ("N", maxx + 1, min(rows_at_max))
    for y in rows_at_max:
        uf.union(snk, ("N", maxx + 1, y))

    edges = [(uf.find(u), uf.find(v), p) for (u, v, p) in edges]
    return edges, uf.find(src), uf.find(snk)


# --------------------------------------------------------------- riduzione SP
# payload dell'arco ridotto: ("SEQ", [payload...]) | ("PAR", [payload...]) | ("EL", item, kind)
def ymin_of(node):
    return node[-1]


def reduce_sp(edges, src, snk):
    edges = [(u, v, ("EL", p[0], p[1], p[2]) if p[1] != "HL" else ("NOP", p[2]))
             for (u, v, p) in edges]
    changed = True
    guard = 0
    while changed:
        guard += 1
        if guard > 500:
            raise Fail("riduzione non convergente")
        changed = False

        # --- parallelo: archi con stessi estremi
        groups = collections.defaultdict(list)
        for e in edges:
            groups[(e[0], e[1])].append(e)
        for (u, v), grp in groups.items():
            if len(grp) > 1:
                rest = [e for e in edges if e not in grp]
                branches = sorted([g[2] for g in grp], key=ymin_of)
                edges = rest + [(u, v, ("PAR", branches, ymin_of(branches[0])))]
                changed = True
                break
        if changed:
            continue

        # --- serie: nodo intermedio con un solo arco entrante e uno uscente
        indeg = collections.defaultdict(list)
        outdeg = collections.defaultdict(list)
        for e in edges:
            outdeg[e[0]].append(e)
            indeg[e[1]].append(e)
        for node in list(set(list(indeg) + list(outdeg))):
            if node in (src, snk):
                continue
            if len(indeg[node]) == 1 and len(outdeg[node]) == 1:
                a, b = indeg[node][0], outdeg[node][0]
                if a is b:
                    continue
                edges = [e for e in edges if e is not a and e is not b]
                edges.append((a[0], b[1], ("SEQ", [a[2], b[2]], min(ymin_of(a[2]), ymin_of(b[2])))))
                changed = True
                break

    if len(edges) != 1 or edges[0][0] != src or edges[0][1] != snk:
        raise Fail("rung non serie-parallelo (%d archi residui)" % len(edges))
    return edges[0][2]


# --------------------------------------------------------------- albero -> spec
def flatten(node):
    """albero SP -> lista di item della spec (una catena in serie)"""
    kind = node[0]
    if kind == "NOP":
        return []
    if kind == "EL":
        return [node[1]]
    if kind == "SEQ":
        out = []
        for ch in node[1]:
            out.extend(flatten(ch))
        return out
    if kind == "PAR":
        branches = []
        for ch in node[1]:
            b = flatten(ch)
            if not b:
                raise Fail("ramo parallelo vuoto (bypass) non rappresentabile")
            # un ramo che e' a sua volta un solo parallelo -> fondi i suoi rami qui
            if len(b) == 1 and isinstance(b[0], dict) and "or" in b[0]:
                branches.extend(b[0]["or"])
            else:
                branches.append(b if len(b) > 1 else b[0])
        return [{"or": branches}]
    raise Fail("nodo albero sconosciuto")


def is_output_branch(branch):
    """il ramo termina con una bobina o un blocco (quindi e' un'uscita)?"""
    last = branch[-1] if isinstance(branch, list) else branch
    if isinstance(last, str):
        return last.startswith("(")
    return isinstance(last, dict) and ("fb" in last or "f" in last or "ist" in last)


def tree_to_spec(node, cmt):
    chain = flatten(node)
    spec = {"cmt": cmt}
    # se l'ultimo elemento e' un parallelo di rami che finiscono in uscite -> "out"
    if chain and isinstance(chain[-1], dict) and "or" in chain[-1]:
        branches = chain[-1]["or"]
        if all(is_output_branch(b) for b in branches):
            spec["chain"] = chain[:-1]
            spec["out"] = branches
            return spec
    spec["chain"] = chain
    return spec


def convert_rung(rung):
    edges, src, snk = build_graph(rung)
    tree = reduce_sp(edges, src, snk)
    return tree_to_spec(tree, rung.get("CMT", ""))


# --------------------------------------------------------------- progetti
ent_re = re.compile(r'<Entity ([^>]+)>')
attr_re = re.compile(r'(\w+)="([^"]*)"')
VER_RE = re.compile(r'[ _\-]?[Vv](\d+)\b')


def project_list():
    """(nome, guid, versione, mtime) per ogni progetto con ladder"""
    out = []
    for guid in os.listdir(SOL):
        d = os.path.join(SOL, guid)
        man = os.path.join(d, guid + ".manifest")
        oem = os.path.join(d, guid + ".oem")
        if not (os.path.isdir(d) and os.path.exists(man) and os.path.exists(oem)):
            continue
        try:
            txt = open(man, encoding="utf-8-sig", errors="ignore").read()
        except OSError:
            continue
        m = re.search(r'solutionName="([^"]+)"', txt)
        if not m:
            continue
        name = m.group(1)
        vm = VER_RE.search(name)
        ver = int(vm.group(1)) if vm else 0
        base = VER_RE.sub("", name).strip().lower()
        base = re.sub(r"\s+", " ", base)
        out.append((name, guid, base, ver, os.path.getmtime(d)))
    return out


def pick_latest(projects):
    """per ogni nome base tiene la versione V piu' alta; a parita', la piu' recente"""
    best = {}
    for (name, guid, base, ver, mt) in projects:
        cur = best.get(base)
        if cur is None or (ver, mt) > (cur[3], cur[4]):
            best[base] = (name, guid, base, ver, mt)
    return sorted(best.values(), key=lambda t: t[0].lower())


def sections_of(guid):
    d = os.path.join(SOL, guid)
    otxt = open(os.path.join(d, guid + ".oem"), encoding="utf-8-sig", errors="ignore").read()
    for t in ent_re.findall(otxt):
        a = dict(attr_re.findall(t))
        if a.get("type") == "PouBody" and a.get("subtype") == "Ladder":
            f = os.path.join(d, a.get("id", "") + ".xml")
            if os.path.exists(f):
                yield a.get("name", "?"), f



VAR_RE = re.compile(r"^\+\+D=(?P<type>[^\t]*)\t(?P<rest>.*)$")


def read_variables(guid):
    """{nome_minuscolo: {name,type,retain,comment}} da tutte le tabelle del progetto"""
    d = os.path.join(SOL, guid)
    otxt = open(os.path.join(d, guid + ".oem"), encoding="utf-8-sig", errors="ignore").read()
    out = {}
    for t in ent_re.findall(otxt):
        a = dict(attr_re.findall(t))
        if a.get("type") != "Variables":
            continue
        f = os.path.join(d, a.get("id", "") + ".xml")
        if not os.path.exists(f):
            continue
        try:
            raw = open(f, encoding="utf-8-sig", errors="ignore").read()
        except OSError:
            continue
        for line in raw.splitlines():
            line = line.rstrip("\r\n")
            m = VAR_RE.match(line)
            if not m:
                continue
            fields = dict()
            for part in m.group("rest").split("\t"):
                if "=" in part:
                    k, v = part.split("=", 1)
                    fields[k] = v
            name = fields.get("N", "")
            if not name:
                continue
            out.setdefault(name.lower(), {
                "name": name,
                "type": m.group("type"),
                "retain": fields.get("R") == "1",
                "comment": fields.get("Com", ""),
            })
    return out



ST_KEYWORDS = {
    "if", "then", "else", "elsif", "end_if", "for", "to", "do", "end_for",
    "while", "end_while", "repeat", "until", "end_repeat", "case", "of",
    "end_case", "return", "exit", "and", "or", "xor", "not", "mod", "true",
    "false", "int", "uint", "dint", "udint", "real", "lreal", "bool", "word",
    "time", "t", "byte", "sint", "usint", "lint", "ulint", "string",
}


def ist_names(text):
    """identificatori citati in un blocco ST inline (esclusi commenti e parole
    chiave); i nomi non presenti nella tabella variabili vengono scartati dopo."""
    txt = re.sub(r"\(\*.*?\*\)", " ", text, flags=re.S)
    txt = re.sub(r"//[^\n]*", " ", txt)
    out = set()
    for m in re.finditer(r"[A-Za-z_][A-Za-z_0-9]*", txt):
        w = m.group(0)
        if w.lower() in ST_KEYWORDS:
            continue
        out.add(w)
    return out


NAME_RE = re.compile(r"[A-Za-z_][A-Za-z_0-9]*")


def names_in(obj, acc):
    """nomi citati in una spec di rung (contatti, bobine, istanze, parametri)"""
    if isinstance(obj, str):
        s = obj.strip()
        m = re.fullmatch(r"\((?:S |R )?/?([^)]+)\)", s)
        if m:
            s = m.group(1).strip()
        else:
            s = s.lstrip("/^v")
        base = s.split(".")[0].split("[")[0]
        if NAME_RE.fullmatch(base):
            acc.add(base)
    elif isinstance(obj, dict):
        if "inst" in obj and obj["inst"]:
            acc.add(obj["inst"].split(".")[0])
        if "ist" in obj and obj["ist"]:
            acc |= ist_names(obj["ist"])
        for k, v in obj.items():
            if k in ("cmt", "fb", "f", "ist"):
                continue
            names_in(v, acc)
    elif isinstance(obj, list):
        for x in obj:
            names_in(x, acc)
    return acc


def convert_project(guid, name):
    """-> (spec_sezioni, ok, fail, motivi)"""
    sections = {}
    ok = fail = 0
    motivi = collections.Counter()
    vartab = read_variables(guid)
    for sec_name, path in sections_of(guid):
        raw = open(path, encoding="utf-8-sig", errors="ignore").read()
        if not raw.lstrip().startswith("{"):
            continue
        rungs = []
        for line in raw.splitlines():
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            if "CLs" not in r:
                continue
            try:
                rungs.append(convert_rung(r))
                ok += 1
            except Fail as e:
                fail += 1
                motivi[str(e)[:60]] += 1
                rungs.append({"cmt": r.get("CMT", ""), "_NON_CONVERTITO": str(e)})
            except Exception as e:
                fail += 1
                motivi["errore interno: " + type(e).__name__] += 1
                rungs.append({"cmt": r.get("CMT", ""), "_NON_CONVERTITO": repr(e)})
        if rungs:
            acc = set()
            for r in rungs:
                names_in(r, acc)
            vars_sec = [vartab[n.lower()] for n in sorted(acc) if n.lower() in vartab]
            key = sec_name
            k = 2
            while key in sections:
                key = "%s#%d" % (sec_name, k)
                k += 1
            sections[key] = {"rungs": rungs, "variables": vars_sec}
    return sections, ok, fail, motivi


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--progetto")
    ap.add_argument("--tutti", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--out", default=r"C:\Users\tecni\Claude\sysmac-mcp\specs")
    args = ap.parse_args()

    projs = pick_latest(project_list())
    if args.progetto:
        projs = [p for p in projs if p[1] == args.progetto or p[0] == args.progetto]
        if not projs:
            all_p = project_list()
            projs = [p for p in all_p if p[1] == args.progetto or p[0] == args.progetto]

    os.makedirs(args.out, exist_ok=True)
    tot_ok = tot_fail = 0
    motivi_tot = collections.Counter()
    righe = []
    for (name, guid, base, ver, mt) in projs:
        sections, ok, fail, motivi = convert_project(guid, name)
        tot_ok += ok
        tot_fail += fail
        motivi_tot += motivi
        if not sections:
            continue
        safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", name)
        if not args.report:
            with open(os.path.join(args.out, safe + ".json"), "w", encoding="utf-8") as f:
                json.dump({"progetto": name, "guid": guid, "sections": sections},
                          f, ensure_ascii=False, indent=1)
        pct = 100.0 * ok / max(1, ok + fail)
        righe.append((pct, ok, fail, name))

    print("PROGETTI: %d" % len(righe))
    for (pct, ok, fail, name) in sorted(righe):
        print("  %6.1f%%  ok=%-5d ko=%-4d  %s" % (pct, ok, fail, name))
    print("\nTOTALE rung: %d convertiti, %d non convertiti (%.1f%%)"
          % (tot_ok, tot_fail, 100.0 * tot_ok / max(1, tot_ok + tot_fail)))
    print("\nMOTIVI DI FALLIMENTO:")
    for k, v in motivi_tot.most_common(20):
        print("  %5d  %s" % (v, k))


if __name__ == "__main__":
    main()
