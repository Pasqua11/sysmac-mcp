"""
json2spec.py - Converte i rung salvati su disco da Sysmac (JSON) nella spec
compatta di ladder_gen.py.

PERCHE': ladder_gen.py sa gia' generare il ladderSnippetXML da una spec, e
rung2spec.py sa ricavare la spec dall'XML degli appunti. Mancava il pezzo che
parte dal DISCO: con questo, qualunque rung di uno qualunque dei progetti in
C:\\Omron\\Data\\Solution diventa riutilizzabile senza aprire quel progetto,
senza selezionare il rung a mano e senza passare dagli appunti.

Catena completa:
    disco (JSON)  --json2spec-->  spec  --ladder_gen-->  ladderSnippetXML
                                                          --> incolla in Sysmac

GEOMETRIA (ricavata dai file reali, 26/08/2026):
  ogni cella ha X = colonna, Y = riga (assenti = 0); Ix = id interno
  VLs = collegamenti verticali: {"Ix":n,"X":c} unisce le righe alla colonna c
  LRI / RRI = id della barra sinistra / destra
Da questa griglia si ricava la topologia serie/parallelo della spec.

ONESTA' SUI LIMITI: vengono riconosciute le forme che ricorrono nei progetti
SYNTECH (serie; fork con rami di uscita indipendenti; OR che si richiude).
Una topologia non riconosciuta NON viene tradotta a caso: solleva
TopologiaNonSupportata con la descrizione della griglia, cosi' si vede subito
cosa manca invece di generare un rung sbagliato.
"""

import json
import os


class TopologiaNonSupportata(Exception):
    pass


# --------------------------------------------------------------- celle

def cella_to_spec(c: dict):
    """Una cella JSON -> elemento della spec di ladder_gen."""
    t = c.get("__type")

    if t == "LD":
        s = c.get("Var", "")
        if c.get("Up"):
            s = "^" + s
        elif c.get("Dwn"):
            s = "v" + s          # fronte di discesa, come lo scrive rung2spec
        if c.get("Not"):
            s = "/" + s
        return s

    if t == "ST":
        if c.get("Up") or c.get("Dwn"):
            raise TopologiaNonSupportata(
                "bobina differenziale (ST con fronte) su '%s': la spec non la "
                "rappresenta, rigenerarla la trasformerebbe in una bobina "
                "normale" % c.get("Var", ""))
        v = c.get("Var", "")
        if c.get("S"):
            return f"(S {v})"
        if c.get("RS"):
            return f"(R {v})"
        if c.get("Not"):
            return f"(/{v})"
        return f"({v})"

    if t in ("FB", "F"):
        for pin in (c.get("In") or []) + (c.get("Out") or []):
            if pin.get("__type") == "PF" and (pin.get("Up") or pin.get("Dwn")):
                raise TopologiaNonSupportata(
                    "fronte sul pin '%s' di %s: la spec non lo rappresenta"
                    % (pin.get("Arg", "?"), c.get("Name", "?")))
        p = {}
        for pin in (c.get("In") or []):
            if pin.get("__type") == "PRM":
                p[pin.get("Arg", "?")] = pin.get("Var", "")
        for pin in (c.get("Out") or []):
            if pin.get("__type") == "PRM":
                p["OUT:" + pin.get("Arg", "?")] = pin.get("Var", "")
        if t == "FB":
            return {"fb": c.get("Name", ""), "inst": c.get("Var", ""), "p": p}
        return {"f": c.get("Name", ""), "p": p}

    if t == "IST":
        return {"ist": c.get("TXT", "")}

    if t == "HL":
        return None              # solo collegamento grafico

    raise TopologiaNonSupportata(f"tipo di cella sconosciuto: {t} -> {json.dumps(c, ensure_ascii=False)[:200]}")


def _righe(obj: dict) -> dict:
    """{Y: [celle ordinate per X]}, senza i collegamenti orizzontali."""
    out = {}
    for c in obj.get("CLs", []):
        if not isinstance(c, dict) or c.get("__type") == "HL":
            continue
        out.setdefault(c.get("Y", 0), []).append(c)
    for y in out:
        out[y].sort(key=lambda c: c.get("X", 0))
    return out


def _serie(celle) -> list:
    out = []
    for c in celle:
        e = cella_to_spec(c)
        if e is not None:
            out.append(e)
    return out


def _ramo(celle):
    """Un ramo: lista se ha piu' elementi, elemento singolo altrimenti."""
    s = _serie(celle)
    if len(s) == 1:
        return s[0]
    return s


# --------------------------------------------------------------- rung

def rung_to_spec(obj: dict) -> dict:
    """Un rung JSON di disco -> dict spec {cmt, chain, [out]}."""
    righe = _righe(obj)
    spec = {}
    if obj.get("CMT"):
        spec["cmt"] = obj["CMT"]

    if not righe:
        spec["chain"] = []
        return spec

    # Coordinate ripetute = la riga (Y) NON e' la riga visiva: Sysmac impila
    # piu' rami sulla stessa Y e la posizione reale dipende dall'ordine e dai
    # collegamenti verticali. Il modello esatto non e' ancora stato ricavato,
    # quindi questi rung NON vengono tradotti: meglio segnalarli che produrre
    # una logica diversa dall'originale.
    # Caso reale che ha fatto scoprire il problema: Sezione1 R5 di
    # test_import_ladder (SET/RESET con OR su un solo ramo).
    viste = set()
    for y in righe:
        for c in righe[y]:
            k = (c.get("X", 0), y)
            if k in viste:
                raise TopologiaNonSupportata(
                    "celle sovrapposte alla stessa coordinata X=%d Y=%d: "
                    "impilamento di rami non ancora decodificato" % k)
            viste.add(k)

    vls = [v for v in (obj.get("VLs") or []) if isinstance(v, dict)]
    vl = sorted({v.get("X", 0) for v in vls})
    ys = sorted(righe)

    # Ogni barra verticale deve collegare TUTTE le righe: (n_righe - 1)
    # segmenti. Se ne ha meno, alcuni rami non si richiudono e la topologia
    # non e' l'OR/fork che questo decodificatore sa rappresentare.
    if len(ys) > 1:
        for col in vl:
            segmenti = sum(1 for v in vls if v.get("X", 0) == col)
            if segmenti != len(ys) - 1:
                raise TopologiaNonSupportata(
                    "collegamento verticale alla colonna %d su %d segmenti "
                    "invece di %d: alcuni rami non si richiudono (rami con "
                    "uscita propria di lunghezza diversa)"
                    % (col, segmenti, len(ys) - 1))

    # --- caso 1: una sola riga = tutto in serie
    if len(ys) == 1 and not vl:
        spec["chain"] = _serie(righe[ys[0]])
        return spec

    if len(ys) == 1 and vl:
        # collegamento verticale senza seconda riga: capita con bobine multiple
        spec["chain"] = _serie(righe[ys[0]])
        return spec

    # --- caso 2: un solo collegamento verticale
    if len(vl) == 1:
        c = vl[0]
        altre = [y for y in ys if y != ys[0]]
        secondarie_prima = any(any(cel.get("X", 0) < c for cel in righe[y]) for y in altre)

        if not secondarie_prima:
            # biforcazione: prefisso comune poi rami di uscita indipendenti
            spec["chain"] = _serie([x for x in righe[ys[0]] if x.get("X", 0) < c])
            rami = []
            for y in ys:
                dopo = [x for x in righe[y] if x.get("X", 0) >= c]
                if dopo:
                    rami.append(_ramo(dopo))
            spec["out"] = rami
            return spec

        # OR che parte dalla barra sinistra e si chiude alla colonna c
        rami = []
        for y in ys:
            prima = [x for x in righe[y] if x.get("X", 0) < c]
            if prima:
                rami.append(_ramo(prima))
        chain = [{"or": rami}]
        dopo0 = [x for x in righe[ys[0]] if x.get("X", 0) >= c]
        dopo_altre = [y for y in altre if any(x.get("X", 0) >= c for x in righe[y])]
        if dopo_altre:
            # dopo l'OR ci sono piu' bobine/rami in parallelo
            spec["chain"] = chain
            spec["out"] = [_ramo([x for x in righe[y] if x.get("X", 0) >= c])
                           for y in ys if any(x.get("X", 0) >= c for x in righe[y])]
            return spec
        spec["chain"] = chain + _serie(dopo0)
        return spec

    # --- caso 3: due collegamenti verticali = OR che si apre e si richiude
    if len(vl) == 2:
        a, b = vl
        fuori = []
        for y in ys[1:]:
            for cel in righe[y]:
                if not (a <= cel.get("X", 0) < b):
                    fuori.append(cel)
        if not fuori:
            rami = []
            for y in ys:
                dentro = [x for x in righe[y] if a <= x.get("X", 0) < b]
                if dentro:
                    rami.append(_ramo(dentro))
            chain = _serie([x for x in righe[ys[0]] if x.get("X", 0) < a])
            chain.append({"or": rami})
            chain += _serie([x for x in righe[ys[0]] if x.get("X", 0) >= b])
            spec["chain"] = chain
            return spec

    raise TopologiaNonSupportata(
        "griglia non riconosciuta: righe=%s VLs=%s" %
        ({y: [(c.get('X', 0), c.get('__type')) for c in righe[y]] for y in ys}, vl))


# --------------------------------------------------------------- sezioni

def sezione_to_spec(path_file: str, nome_sezione: str = "Sezione") -> dict:
    """File di sezione (JSON per riga) -> spec completa {"sections": {...}}.

    I rung non convertibili non vengono inventati: restano nel risultato come
    {"cmt": ..., "_errore": "..."} in modo che si veda esattamente quali sono.
    """
    rung = []
    with open(path_file, encoding="utf-8-sig", errors="ignore") as fh:
        for riga in fh:
            if not riga.strip():
                continue
            obj = json.loads(riga)
            if not obj.get("CLs"):
                continue                      # rung vuoto: non si esporta
            try:
                rung.append(rung_to_spec(obj))
            except TopologiaNonSupportata as e:
                rung.append({"cmt": obj.get("CMT", ""), "_errore": str(e)})
    return {"sections": {nome_sezione: rung}}


def progetto_to_spec(nome_progetto: str, nome_sezione: str = "") -> dict:
    """Spec di una sezione (o di tutte) di un progetto, presa dal disco."""
    import sysmac_project as P
    pr = P.find_project(nome_progetto)
    sez = P.sections(pr)
    if nome_sezione:
        sez = [s for s in sez if nome_sezione.lower() in s["nome"].lower()]
        if not sez:
            raise LookupError(f"sezione '{nome_sezione}' non trovata")
    out = {"sections": {}}
    for s in sez:
        out["sections"][s["nome"]] = sezione_to_spec(s["file"], s["nome"])["sections"][s["nome"]]
    return out


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    if len(sys.argv) < 3:
        print("uso: json2spec.py <progetto> <sezione> [file_uscita.json]")
        raise SystemExit(1)
    spec = progetto_to_spec(sys.argv[1], sys.argv[2])
    testo = json.dumps(spec, ensure_ascii=False, indent=1)
    if len(sys.argv) > 3:
        open(sys.argv[3], "w", encoding="utf-8").write(testo)
        n = sum(len(v) for v in spec["sections"].values())
        err = testo.count('"_errore"')
        print(f"scritti {n} rung in {sys.argv[3]} ({err} non convertiti)")
    else:
        print(testo)
