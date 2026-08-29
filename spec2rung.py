"""spec2rung.py - da spec compatta al JSON del rung come lo scrive Sysmac.

E' l'inverso di json2spec.py e chiude il cerchio: permette di scrivere ladder
DIRETTAMENTE nei file di progetto, senza GUI e senza clipboard.

    spec  --spec2rung-->  JSON  --scritto nel file di sezione-->  Sysmac

GEOMETRIA (dedotta dai file reali e verificata con il round-trip):
  ogni cella ha X = colonna e Y = riga (omessi quando valgono 0)
  Ix = identificativo univoco della cella; LRI/RRI = id barra sinistra/destra
  VLs = collegamenti verticali: piu' segmenti che condividono lo stesso Ix,
        alla colonna X dove passa la barra verticale, con Y = riga superiore
        del segmento
  OR che parte dalla barra sinistra -> UN solo collegamento verticale, alla
        colonna di chiusura
  OR in mezzo alla catena           -> DUE collegamenti: apertura e chiusura
  rami di uscita indipendenti (fork) -> UN collegamento alla colonna in cui
        i rami si separano

BLOCCHI FUNZIONE E FUNZIONI: nel JSON ogni parametro porta anche il TIPO di
dato, che la spec non conserva. Il tipo viene quindi ripreso da
`pin_reali.json`, la firma ESATTA di ogni blocco ricavata dai 17.566 rung gia'
scritti in azienda (ordine dei pin, quale e' il pin di power flow, quali sono
in-out, flag UD/PL di cella). Un blocco che nell'archivio compare con firme
diverse, o che non compare affatto, NON viene generato: solleva NonSupportato.
Mai un'approssimazione silenziosa.
"""

import json
import re


class NonSupportato(Exception):
    pass


_FIRME = None


def firme(ricarica=False):
    """Firme reali dei blocchi, da pin_reali.json (v. estrai_pin_reali.py)."""
    global _FIRME
    if _FIRME is None or ricarica:
        import os
        p = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "pin_reali.json")
        with open(p, encoding="utf-8") as fh:
            _FIRME = json.load(fh)
    return _FIRME


def _cella_blocco(elemento, x, y):
    """{"fb": nome, "inst": istanza, "p": {...}} -> cella FB/F completa,
    con i tipi dei parametri presi dalla firma reale."""
    nome = elemento.get("fb") or elemento.get("f")
    atteso = "FB" if "fb" in elemento else "F"
    f = firme().get(nome)
    if f is None:
        raise NonSupportato(
            "firma di '%s' sconosciuta: il blocco non compare in nessun "
            "progetto in archivio, quindi non si conoscono i tipi dei suoi "
            "parametri -> usare l'incolla XML" % nome)
    if f.get("ambigui"):
        raise NonSupportato(
            "'%s' compare in archivio con firme diverse: non e' generabile "
            "automaticamente senza rischiare un rung sbagliato" % nome)
    if f.get("kind") != atteso:
        raise NonSupportato("'%s' in archivio e' %s, nella spec e' %s"
                            % (nome, f.get("kind"), atteso))
    p = elemento.get("p") or {}
    noti = {q["arg"] for q in f["in"] if not q["pf"]}
    noti |= {"OUT:" + q["arg"] for q in f["out"] if not q["pf"]}
    ignoti = [k for k in p if k not in noti]
    if ignoti:
        raise NonSupportato("parametri non previsti dalla firma di '%s': %s"
                            % (nome, ignoti))

    def lato(pins, prefisso):
        out = []
        for q in pins:
            if q["pf"]:
                out.append({"__type": "PF", "Arg": q["arg"]})
                continue
            voce = {"__type": "PRM", "Arg": q["arg"]}
            if q.get("io"):
                voce["IO"] = True
            voce["Type"] = q["tipo"]
            voce["Var"] = p.get(prefisso + q["arg"], "")
            out.append(voce)
        return out

    c = {"__type": atteso, "Name": nome,
         "In": lato(f["in"], ""), "Out": lato(f["out"], "OUT:")}
    if f.get("UD"):
        c["UD"] = True
    if f.get("PL"):
        c["PL"] = True
    if atteso == "FB":
        if not elemento.get("inst"):
            raise NonSupportato("blocco funzione '%s' senza nome di istanza"
                                % nome)
        c["Var"] = elemento["inst"]
    if x:
        c["X"] = x
    if y:
        c["Y"] = y
    return c


# ----------------------------------------------------------------- celle
def cella(elemento, x=0, y=0):
    """Un elemento della spec -> una cella JSON (senza Ix, assegnato dopo)."""
    if isinstance(elemento, dict):
        if "ist" in elemento:
            import uuid
            # EID: identificativo della casella di ST inline. Nei file reali
            # c'e' sempre; H e W (altezza e larghezza della casella) vengono
            # invece ricalcolate da Sysmac all'apertura, quindi si omettono.
            c = {"__type": "IST", "EID": str(uuid.uuid4()),
                 "TXT": elemento["ist"]}
        elif "fb" in elemento or "f" in elemento:
            return _cella_blocco(elemento, x, y)
        else:
            raise NonSupportato("elemento non riconosciuto: %r" % (elemento,))
    elif isinstance(elemento, str):
        t = elemento.strip()
        if t.startswith("(") and t.endswith(")"):
            interno = t[1:-1].strip()
            c = {"__type": "ST"}
            if interno.startswith("S "):
                c["S"] = True
                interno = interno[2:].strip()
            elif interno.startswith("R "):
                c["RS"] = True
                interno = interno[2:].strip()
            elif interno.startswith("/"):
                c["Not"] = True
                interno = interno[1:].strip()
            c["Var"] = interno
        else:
            c = {"__type": "LD"}
            v = t
            if v.startswith("/"):
                c["Not"] = True
                v = v[1:]
            if v.startswith("^"):
                c["Up"] = True
                v = v[1:]
            elif v.startswith("v"):
                c["Dwn"] = True
                v = v[1:]
            c["Var"] = v
    else:
        raise NonSupportato("elemento non riconosciuto: %r" % (elemento,))
    if x:
        c["X"] = x
    if y:
        c["Y"] = y
    return c


def _seq(ramo):
    """Un ramo puo' essere un singolo elemento o una lista."""
    return list(ramo) if isinstance(ramo, list) else [ramo]


# ------------------------------------------------------------------ rung
def rung_da_spec(spec):
    """spec {cmt, chain, out} -> dict del rung come lo salva Sysmac."""
    if spec.get("_errore"):
        raise NonSupportato("rung gia' segnalato come non convertibile: %s"
                            % spec["_errore"])
    celle = []
    colonne_vl = []          # colonne dove passa una barra verticale
    righe_vl = []            # quante righe collega ciascuna barra
    x = 0

    for e in spec.get("chain", []):
        if isinstance(e, dict) and "or" in e:
            rami = e["or"]
            if len(rami) < 2:
                raise NonSupportato("blocco 'or' con meno di due rami")
            larghezza = max(len(_seq(r)) for r in rami)
            for y, r in enumerate(rami):
                s = _seq(r)
                if len(s) != larghezza and y > 0 and len(s) > larghezza:
                    raise NonSupportato("rami dell'or di lunghezza incoerente")
                for k, el in enumerate(s):
                    celle.append(cella(el, x + k, y))
            if x > 0:                       # or in mezzo: apertura + chiusura
                colonne_vl.append(x)
                righe_vl.append(len(rami))
            colonne_vl.append(x + larghezza)
            righe_vl.append(len(rami))
            x += larghezza
        else:
            celle.append(cella(e, x, 0))
            x += 1

    rami_out = spec.get("out")
    if rami_out:
        if len(rami_out) < 2:
            raise NonSupportato("'out' con un solo ramo")
        colonne_vl.append(x)
        righe_vl.append(len(rami_out))
        for y, r in enumerate(rami_out):
            for k, el in enumerate(_seq(r)):
                celle.append(cella(el, x + k, y))

    if not celle:
        raise NonSupportato("rung senza celle")

    # Identificativi. Ordine ricavato dai file reali: per ogni cella prima i
    # suoi parametri di ingresso, poi quelli di uscita, poi la cella stessa;
    # infine barra sinistra, barra destra e collegamenti verticali.
    prossimo = 0
    for c in celle:
        for lato_ in ("In", "Out"):
            for pin in c.get(lato_, []):
                if pin.get("__type") == "PRM":
                    pin["Ix"] = prossimo
                    prossimo += 1
        if prossimo:
            c["Ix"] = prossimo
        prossimo += 1
    n = prossimo
    rung = {"CLs": celle}
    if spec.get("cmt"):
        rung["CMT"] = spec["cmt"]
    rung["LRI"] = n
    rung["RRI"] = n + 1

    # Una sola barra verticale per colonna: un OR che si richiude alla stessa
    # colonna in cui si aprono rami di uscita e' UNA barra sola, non due.
    per_colonna = {}
    for col, nrighe in zip(colonne_vl, righe_vl):
        per_colonna[col] = max(per_colonna.get(col, 0), nrighe)

    vls = []
    ix = n + 2
    for col, nrighe in sorted(per_colonna.items()):
        for y in range(nrighe - 1):
            v = {"Ix": ix, "X": col}
            if y:
                v["Y"] = y
            vls.append(v)
        ix += 1
    rung["VLs"] = vls
    return rung


def riga_rung(spec):
    """Il rung serializzato come UNA riga, pronta per il file di sezione."""
    return json.dumps(rung_da_spec(spec), ensure_ascii=False,
                      separators=(",", ":"))


# --------------------------------------------------------------- sezione
def scrivi_sezione(path_file, spec_rungs, in_coda=True, backup=True):
    """Aggiunge (o sostituisce) i rung nel file di una sezione.

    ATTENZIONE: il progetto deve essere CHIUSO in Sysmac Studio, e dopo la
    modifica serve un F8 (compilazione) prima di poter avviare la simulazione.
    Il file ha BOM UTF-8 e fine riga CRLF: vengono preservati.
    """
    import io
    import os
    import shutil
    if backup and not os.path.exists(path_file + ".bak_spec2rung"):
        shutil.copyfile(path_file, path_file + ".bak_spec2rung")
    testo = io.open(path_file, encoding="utf-8", newline="").read()
    nuove = "\r\n".join(riga_rung(s) for s in spec_rungs)
    if in_coda:
        testo = testo.rstrip("\r\n") + "\r\n" + nuove + "\r\n"
    else:
        bom = "﻿" if testo.startswith("﻿") else ""
        testo = bom + nuove + "\r\n"
    io.open(path_file, "w", encoding="utf-8", newline="").write(testo)
    return len(spec_rungs)


# ------------------------------------------------------------ round-trip
def verifica_roundtrip(spec):
    """spec -> JSON -> spec: le due spec devono coincidere.
    Ritorna (True, None) oppure (False, spec_ottenuta)."""
    import json2spec
    rung = rung_da_spec(spec)
    ri = json2spec.rung_to_spec(json.loads(json.dumps(rung)))
    pulita = {k: v for k, v in spec.items() if k != "_errore"}
    return (ri == pulita), (None if ri == pulita else ri)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        spec = json.load(open(sys.argv[1], encoding="utf-8-sig"))
        rungs = spec["sections"][list(spec["sections"])[0]] \
            if "sections" in spec else [spec]
        for r in rungs:
            try:
                print(riga_rung(r))
            except NonSupportato as e:
                print("// NON SUPPORTATO: %s" % e)
    else:
        esempi = [
            {"cmt": "serie semplice", "chain": ["IN_MARCIA", "/IN_TERMICO", "(OUT_POMPA)"]},
            {"cmt": "autoritenuta", "chain": [{"or": ["PB_Start", "Motore"]}, "/PB_Stop", "(Motore)"]},
            {"cmt": "set/reset", "chain": ["P_On", "(S Mem)"]},
            {"cmt": "uscite multiple", "chain": ["IN_MARCIA"], "out": ["(Luce1)", "(Luce2)"]},
        ]
        for e in esempi:
            print(e["cmt"], "->", riga_rung(e))
            ok, ott = verifica_roundtrip(e)
            print("   round-trip:", "OK" if ok else "DIVERSO -> %s" % ott)
