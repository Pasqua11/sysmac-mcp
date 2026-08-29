# -*- coding: utf-8 -*-
"""istruzioni.py - il linguaggio di Sysmac Studio, dalla fonte ufficiale.

Costruisce un catalogo strutturato delle istruzioni NJ/NX leggendo i manuali di
riferimento installati con Sysmac Studio (Help\\en-US\\*.chm, estratti da
indicizza_manuale.py). Serve a proporre soluzioni che NON siano solo la
ricombinazione dei pattern gia' usati in azienda: qui c'e' tutto l'insieme di
istruzioni disponibile, non solo le 92 che compaiono nei progetti esistenti.

Per ogni istruzione:
    nome, tipo (FB o FUN), descrizione, espressione ST, parametri con i TIPI
    AMMESSI presi dalla matrice del manuale, e il testo della sezione
    "Function" (semantica) troncato.

    import istruzioni
    istruzioni.costruisci()            # una volta: analizza ~510 pagine
    istruzioni.cerca("timer")          # ricerca per nome o descrizione
    istruzioni.dettaglio("TON")        # scheda completa
    istruzioni.testo_completo("TON")   # la pagina intera del manuale
"""
import html as _html
import io
import json
import os
import re

D = os.path.dirname(os.path.abspath(__file__))
INDICE = os.path.join(D, "manuale", "indice_istruzioni.json")
CATALOGO = os.path.join(D, "manuale", "istruzioni.json")

TIPI = ["BOOL", "BYTE", "WORD", "DWORD", "LWORD", "USINT", "UINT", "UDINT",
        "ULINT", "SINT", "INT", "DINT", "LINT", "REAL", "LREAL", "TIME",
        "DATE", "TOD", "DT", "STRING"]

_cache = None


# ------------------------------------------------------------------ analisi
def _celle(percorso):
    t = io.open(percorso, encoding="utf-8", errors="replace").read()
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", t)
    t = re.sub(r"<[^>]+>", "\x00", t)
    t = _html.unescape(t)
    return [re.sub(r"\s+", " ", c).strip() for c in t.split("\x00")]


def _righe_tabelle(percorso):
    """[[cella, ...], ...] di tutte le righe di tabella della pagina."""
    t = io.open(percorso, encoding="utf-8", errors="replace").read()
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", t)
    out = []
    for riga in re.findall(r"(?is)<tr[^>]*>(.*?)</tr>", t):
        celle = []
        for c in re.findall(r"(?is)<t[dh][^>]*>(.*?)</t[dh]>", riga):
            c = re.sub(r"<[^>]+>", " ", c)
            celle.append(re.sub(r"\s+", " ", _html.unescape(c)).strip())
        if celle:
            out.append(celle)
    return out


def _analizza(percorso, nome):
    c = [x for x in _celle(percorso) if x]
    righe = _righe_tabelle(percorso)
    voce = {"nome": nome, "tipo": "", "descrizione": "", "st": "",
            "parametri": [], "funzione": ""}

    for x in c[:40]:
        if len(x) > 25 and (nome in x or x.lower().startswith("the ")):
            voce["descrizione"] = x
            break

    # FB o FUN: la cella dopo l'intestazione "Graphic expression"
    try:
        g = next(k for k, x in enumerate(c[:80]) if x == "Graphic expression")
        voce["tipo"] = next(x for x in c[g:g + 20] if x in ("FB", "FUN"))
    except StopIteration:
        for x in c[:80]:
            if x in ("FB", "FUN"):
                voce["tipo"] = x
                break

    for x in c[:120]:
        if x.endswith(");") and "(" in x and len(x) < 400:
            voce["st"] = x
            break

    # tabella "Variables": nome | significato | I/O | descrizione | range | ...
    versi, significati = {}, {}
    for r in righe:
        if len(r) >= 3 and r[2] in ("Input", "Output", "In-out"):
            p = r[0].strip()
            if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_\[\]]{0,30}", p):
                versi[p] = r[2]
                significati[p] = r[1][:60]

    # matrice dei tipi ammessi: riga di intestazione con i 20 tipi, poi una
    # riga per parametro con "OK" nelle colonne consentite
    inizio = None
    for k, r in enumerate(righe):
        celle = [x.upper() for x in r]
        if all(t in celle for t in ("BOOL", "INT", "REAL", "STRING")):
            inizio = k
            colonne = [x.upper() for x in r]
            break
    if inizio is not None:
        indice = {}
        for j, x in enumerate(colonne):
            if x in TIPI and x not in indice:
                indice[x] = j
        for r in righe[inizio + 1:]:
            if not r:
                break
            p = r[0].strip()
            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_\[\]]{0,30}", p):
                break
            ammessi = [t for t, j in indice.items()
                       if j < len(r) and r[j].strip().upper() == "OK"]
            voce["parametri"].append({"nome": p, "tipi": ammessi,
                                      "verso": versi.get(p, ""),
                                      "significato": significati.get(p, "")})
    if not voce["parametri"] and versi:
        for p, v in versi.items():
            voce["parametri"].append({"nome": p, "tipi": [], "verso": v,
                                      "significato": significati.get(p, "")})

    try:
        j = next(k for k in range(len(c)) if c[k] == "Function")
        voce["funzione"] = " ".join(c[j + 1:j + 26])[:900]
    except StopIteration:
        pass
    return voce


def costruisci(forza=False):
    """Analizza tutte le pagine e salva manuale\\istruzioni.json."""
    global _cache
    if os.path.exists(CATALOGO) and not forza:
        return carica()
    idx = json.load(io.open(INDICE, encoding="utf-8"))
    out, errori = {}, []
    for nome, v in idx.items():
        p = os.path.join(D, v["file"])
        try:
            voce = _analizza(p, nome)
            voce["origine"] = v["origine"]
            voce["file"] = v["file"]
            out[nome] = voce
        except Exception as e:
            errori.append((nome, str(e)))
    with io.open(CATALOGO, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1, sort_keys=True)
    _cache = out
    return out, errori


def carica():
    global _cache
    if _cache is None:
        _cache = json.load(io.open(CATALOGO, encoding="utf-8"))
    return _cache


# ------------------------------------------------------------------ consulta
def cerca(testo, max_risultati=25):
    """Cerca per nome o nella descrizione. Ritorna righe compatte."""
    t = testo.lower()
    cat = carica()
    esatti, parziali = [], []
    for n, v in cat.items():
        if t == n.lower():
            esatti.append(v)
        elif t in n.lower():
            parziali.append(v)
        elif t in (v.get("descrizione", "") + v.get("funzione", "")).lower():
            parziali.append(v)
    ris = esatti + parziali
    righe = []
    for v in ris[:max_risultati]:
        righe.append("%-26s %-4s %s" % (v["nome"], v.get("tipo", ""),
                                        (v.get("descrizione") or "")[:78]))
    if len(ris) > max_risultati:
        righe.append("... e altre %d" % (len(ris) - max_risultati))
    return "\n".join(righe) if righe else "nessuna istruzione trovata per %r" % testo


def dettaglio(nome):
    cat = carica()
    v = cat.get(nome)
    if v is None:
        simili = [n for n in cat if nome.lower() in n.lower()][:8]
        return "istruzione '%s' non trovata.%s" % (
            nome, (" Forse: " + ", ".join(simili)) if simili else "")
    r = ["%s  (%s, manuale: %s)" % (v["nome"], v.get("tipo") or "?", v["origine"]),
         v.get("descrizione", "")]
    if v.get("st"):
        r.append("ST:  " + v["st"])
    if v.get("parametri"):
        r.append("parametri:")
        for p in v["parametri"]:
            r.append("   %-14s %-8s %-28s %s"
                     % (p["nome"], p.get("verso", ""),
                        ", ".join(p["tipi"])[:28] or "-",
                        p.get("significato", "")[:34]))
    if v.get("funzione"):
        r.append("funzionamento: " + v["funzione"][:700])
    return "\n".join(r)


def testo_completo(nome, max_caratteri=6000):
    """La pagina intera del manuale, per i casi in cui serve il dettaglio."""
    v = carica().get(nome)
    if v is None:
        return "istruzione '%s' non trovata" % nome
    c = [x for x in _celle(os.path.join(D, v["file"])) if x]
    return " ".join(c)[:max_caratteri]


def riepilogo():
    cat = carica()
    per_tipo, con_st = {}, 0
    for v in cat.values():
        per_tipo[v.get("tipo") or "?"] = per_tipo.get(v.get("tipo") or "?", 0) + 1
        if v.get("st"):
            con_st += 1
    return {"istruzioni": len(cat), "per_tipo": per_tipo,
            "con_espressione_ST": con_st,
            "con_parametri": sum(1 for v in cat.values() if v["parametri"])}


if __name__ == "__main__":
    import sys
    if "--costruisci" in sys.argv:
        r = costruisci(forza=True)
        cat = r[0] if isinstance(r, tuple) else r
        print("catalogo costruito:", len(cat), "istruzioni")
        print(json.dumps(riepilogo(), ensure_ascii=False))
    elif len(sys.argv) > 1:
        print(dettaglio(sys.argv[1]))
    else:
        print(json.dumps(riepilogo(), ensure_ascii=False, indent=1))
