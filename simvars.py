"""simvars.py - legge la TABELLA VARIABILI GLOBALI di un progetto Sysmac
direttamente dai file su disco (C:\\OMRON\\Data\\Solution), senza aprire la GUI.

Formato scoperto (file <guid-entita-Global>.xml del progetto):

    [SLWD version=1.0]
    _EN=Variables
    +GN=VAR_GLOBAL<TAB>GVT=GlobalNamespaceGroup
    ++D=BOOL<TAB>N=IN_MARCIA<TAB>NTP=PublicationOnly<TAB>G=VAR_GLOBAL<TAB>Com=...
    ++D=ARRAY[1..40] OF bool<TAB>N=Allarme_Bit<TAB>...
    ++D=INT<TAB>N=SET_Timer_V1<TAB>R=1<TAB>...

    D  = tipo dato      N  = nome         AT = assegnazione I/O
    R=1= ritentivo      NTP= pubblicazione di rete       Com = commento

Serve a dare al collegamento col simulatore (simlink.py) il TIPO ESATTO di
ogni variabile: dall'indirizzo il simulatore restituisce solo la dimensione in
bit, quindi REAL e DINT (32 bit) sarebbero indistinguibili.
"""

import os
import re

RADICE = r"C:\OMRON\Data\Solution"


def _testo(path, max_bytes=8_000_000):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read(max_bytes)


def elenco_progetti(radice=RADICE):
    """[(nome_progetto, cartella)] leggendo i .manifest."""
    out = []
    if not os.path.isdir(radice):
        return out
    for d in os.listdir(radice):
        p = os.path.join(radice, d)
        if not os.path.isdir(p):
            continue
        for f in os.listdir(p):
            if f.endswith(".manifest"):
                try:
                    t = _testo(os.path.join(p, f), 200000)
                except OSError:
                    continue
                m = re.search(r'solutionName="([^"]*)"', t) or \
                    re.search(r"<solutionName>([^<]*)</solutionName>", t)
                if m:
                    out.append((m.group(1), p))
                break
    return out


def trova_progetto(nome, radice=RADICE):
    """Cartella del progetto: match esatto, poi parziale (case-insensitive)."""
    prog = elenco_progetti(radice)
    for n, p in prog:
        if n == nome:
            return p
    b = nome.lower()
    cand = [(n, p) for n, p in prog if b in n.lower()]
    if len(cand) == 1:
        return cand[0][1]
    if len(cand) > 1:
        raise ValueError("nome ambiguo '%s': %s" % (nome, [n for n, _ in cand]))
    raise ValueError("progetto '%s' non trovato in %s" % (nome, radice))


def _file_variabili_globali(cartella):
    oem = [f for f in os.listdir(cartella) if f.endswith(".oem")]
    if not oem:
        raise ValueError("nessun .oem in %s" % cartella)
    t = _testo(os.path.join(cartella, oem[0]))
    m = re.search(
        r'<Entity[^>]*type="Variables"[^>]*subtype="Global"[^>]*id="([0-9a-fA-F-]+)"', t)
    if not m:
        m = re.search(
            r'<Entity[^>]*subtype="Global"[^>]*type="Variables"[^>]*id="([0-9a-fA-F-]+)"', t)
    if not m:
        raise ValueError("entita' 'Variabili globali' non trovata nel .oem")
    f = os.path.join(cartella, m.group(1) + ".xml")
    if not os.path.exists(f):
        raise ValueError("file tabella variabili mancante: %s" % f)
    return f


_RE_CAMPO = re.compile(r"(?:^|\t)([A-Za-z]+)=")


def _campi(riga):
    """Spezza '++D=BOOL\\tN=X\\tG=VAR_GLOBAL' in {'D':'BOOL','N':'X',...}."""
    riga = riga[2:] if riga.startswith("++") else riga
    out = {}
    pezzi = riga.split("\t")
    for p in pezzi:
        if "=" in p:
            k, v = p.split("=", 1)
            k = k.strip()
            if k and k not in out:
                out[k] = v
    return out


def normalizza_tipo(d):
    """'ARRAY[1..40] OF bool' -> ('BOOL', (1,40));  'INT' -> ('INT', None)."""
    d = (d or "").strip()
    m = re.match(r"ARRAY\s*\[\s*(-?\d+)\s*\.\.\s*(-?\d+)\s*\]\s*OF\s+(.+)$", d, re.I)
    if m:
        return m.group(3).strip().upper(), (int(m.group(1)), int(m.group(2)))
    return d.upper(), None


def variabili_globali(progetto):
    """{nome: tipo} di tutte le variabili globali (array espansi indice per
    indice). `progetto` = nome progetto, cartella, oppure file .smc2."""
    if isinstance(progetto, str) and progetto.lower().endswith(
            (".smc2", ".smc", ".csm2")):
        # progetto gestito nel FILE: non sta nell'archivio, si legge dallo zip
        import smc2
        return smc2.variabili_globali(progetto)
    cartella = progetto if os.path.isdir(progetto) else trova_progetto(progetto)
    f = _file_variabili_globali(cartella)
    tipi = {}
    for riga in _testo(f).splitlines():
        if not riga.startswith("++D="):
            continue
        c = _campi(riga)
        nome = c.get("N")
        if not nome:
            continue
        tipo, rng = normalizza_tipo(c.get("D"))
        if rng:
            tipi[nome] = "ARRAY OF " + tipo
            for i in range(rng[0], rng[1] + 1):
                tipi["%s[%d]" % (nome, i)] = tipo
        else:
            tipi[nome] = tipo
    return tipi


def dettaglio_globali(progetto):
    """Come variabili_globali ma con tutti i campi (AT, ritentivo, commento)."""
    cartella = progetto if os.path.isdir(progetto) else trova_progetto(progetto)
    f = _file_variabili_globali(cartella)
    out = []
    for riga in _testo(f).splitlines():
        if not riga.startswith("++D="):
            continue
        c = _campi(riga)
        if not c.get("N"):
            continue
        tipo, rng = normalizza_tipo(c.get("D"))
        out.append({
            "nome": c["N"],
            "tipo": c.get("D", "").strip(),
            "tipo_base": tipo,
            "array": list(rng) if rng else None,
            "AT": c.get("AT", ""),
            "ritentivo": c.get("R", "") == "1",
            "pubblicazione": c.get("NTP", ""),
            "commento": (c.get("Com", "") or "").replace("$t", " ").strip(),
        })
    return out


def righe_tsv(variabili):
    """Genera le righe TSV nel formato che la TABELLA VARIABILI di Sysmac
    accetta con Ctrl+V (verificato 27/08/2026):
       Nome  Tipo  ValoreIniziale  AT  Ritentivo  Costante  PubblicazioneRete  Commento

    `variabili` = lista di dict {nome, tipo, [iniziale], [at], [ritentivo],
    [costante], [pubblicazione], [commento]} oppure tuple (nome, tipo).
    """
    righe = []
    for v in variabili:
        if isinstance(v, (list, tuple)):
            v = {"nome": v[0], "tipo": v[1]}
        righe.append("\t".join([
            str(v.get("nome", "")),
            str(v.get("tipo", "")),
            str(v.get("iniziale", "")),
            str(v.get("at", "")),
            "True" if v.get("ritentivo") else "False",
            "True" if v.get("costante") else "False",
            str(v.get("pubblicazione", "Non pubblicare")),
            str(v.get("commento", "")),
        ]))
    return "\r\n".join(righe) + "\r\n"


if __name__ == "__main__":
    import json
    import sys
    if len(sys.argv) < 2:
        print("uso: python simvars.py <progetto> [--dettaglio]")
        print("     python simvars.py --elenco")
        sys.exit(1)
    if sys.argv[1] == "--elenco":
        for n, p in sorted(elenco_progetti()):
            print("%-45s %s" % (n, p))
        sys.exit(0)
    if "--dettaglio" in sys.argv:
        print(json.dumps(dettaglio_globali(sys.argv[1]), ensure_ascii=False, indent=1))
    else:
        t = variabili_globali(sys.argv[1])
        print(json.dumps(t, ensure_ascii=False, indent=1))
        print("TOTALE:", len(t))
