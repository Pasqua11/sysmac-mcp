"""slwd.py - lettura e SCRITTURA OFFLINE delle tabelle variabili di un progetto
Sysmac Studio, direttamente sui file in C:\\OMRON\\Data\\Solution.

Elimina l'ultimo passaggio via GUI: niente clipboard, niente coordinate, niente
click. Centinaia di variabili create in millisecondi.

ATTENZIONE: il progetto NON deve essere aperto in Sysmac Studio (le modifiche
verrebbero sovrascritte al salvataggio). Le funzioni controllano il file di
lock e rifiutano di scrivere se il progetto risulta aperto.

Formato dei file (testo, tab-separati):

    [SLWD version=1.0]
    _EN=Variables
    +GN=VAR_GLOBAL<TAB>GVT=GlobalNamespaceGroup          <- gruppo
    ++D=BOOL<TAB>N=IN_MARCIA<TAB>G=VAR_GLOBAL            <- variabile

Gruppi noti:
    +GN=VAR_GLOBAL   GVT=GlobalNamespaceGroup   variabili globali
    +GN=VAR          GVT=DefaultGroup           variabili interne del POU
    +GN=VAR_EXTERNAL GA=External GVT=ExternalGroup   variabili esterne del POU

Campi della variabile:
    D  = tipo dato            N   = nome
    AT = assegnazione I/O     R=1 = ritentivo         C=1 = costante
    IV = valore iniziale      NTP = pubblicazione di rete
    Com= commento (i TAB interni sono codificati come $t)
"""

import os
import re
import shutil
import xml.etree.ElementTree as ET

RADICE = r"C:\OMRON\Data\Solution"

GRUPPI = {
    "globali": "+GN=VAR_GLOBAL\tGVT=GlobalNamespaceGroup",
    "interne": "+GN=VAR\tGVT=DefaultGroup",
    "esterne": "+GN=VAR_EXTERNAL\tGA=External\tGVT=ExternalGroup",
}
SIGLA = {"globali": "VAR_GLOBAL", "interne": "VAR", "esterne": "VAR_EXTERNAL"}

# tipi che sono ISTANZE di blocco funzione: vanno nella tabella INTERNE,
# non sono ammessi fra le globali
_BASE = {
    "BOOL", "SINT", "INT", "DINT", "LINT", "USINT", "UINT", "UDINT", "ULINT",
    "BYTE", "WORD", "DWORD", "LWORD", "REAL", "LREAL", "TIME", "DATE",
    "TIME_OF_DAY", "TOD", "DATE_AND_TIME", "DT",
}


def e_istanza_fb(tipo, tipi_utente=()):
    """True se `tipo` e' un'istanza di blocco funzione (TON, CTU, MC_Power,
    FB custom...) e quindi deve stare fra le variabili INTERNE."""
    t = (tipo or "").strip().upper()
    m = re.match(r"ARRAY\s*\[.*?\]\s*OF\s+(.+)$", t, re.I)
    if m:
        t = m.group(1).strip().upper()
    if t.startswith("STRING"):
        return False
    if t in _BASE:
        return False
    if t in {x.upper() for x in tipi_utente}:
        return False          # struttura/enum definita dall'utente: e' un dato
    return True


# --------------------------------------------------------------- progetto
def _testo(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def elenco_progetti(radice=RADICE):
    out = []
    for d in os.listdir(radice):
        p = os.path.join(radice, d)
        if not os.path.isdir(p):
            continue
        for f in os.listdir(p):
            if f.endswith(".manifest"):
                m = re.search(r'solutionName="([^"]*)"', _testo(os.path.join(p, f)))
                if m:
                    out.append((m.group(1), p))
                break
    return out


def trova_progetto(nome, radice=RADICE):
    if os.path.isdir(nome):
        return nome
    prog = elenco_progetti(radice)
    for n, p in prog:
        if n == nome:
            return p
    cand = [(n, p) for n, p in prog if nome.lower() in n.lower()]
    if len(cand) == 1:
        return cand[0][1]
    if cand:
        raise ValueError("nome ambiguo '%s': %s" % (nome, [n for n, _ in cand]))
    raise ValueError("progetto '%s' non trovato" % nome)


def aperto_in_sysmac(cartella):
    """True se esiste un .applicationlock di un processo Sysmac ancora vivo."""
    import subprocess
    pid_vivi = set()
    try:
        r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq SysmacStudio.exe",
                            "/FO", "CSV", "/NH"], capture_output=True, text=True, errors="replace",
                           timeout=30)
        for riga in r.stdout.splitlines():
            c = [x.strip('"') for x in riga.split('","')]
            if len(c) > 1 and c[1].isdigit():
                pid_vivi.add(c[1])
    except Exception:
        return True          # nel dubbio si considera aperto
    for f in os.listdir(cartella):
        if f.endswith(".applicationlock"):
            if f.split(".")[0] in pid_vivi:
                return True
    return False


def _entita(cartella):
    oem = [f for f in os.listdir(cartella) if f.endswith(".oem")]
    if not oem:
        raise ValueError("nessun .oem in %s" % cartella)
    return ET.parse(os.path.join(cartella, oem[0])).getroot()


def file_globali(cartella):
    for e in _entita(cartella).iter("Entity"):
        if e.get("type") == "Variables" and e.get("subtype") == "Global":
            return os.path.join(cartella, e.get("id") + ".xml")
    raise ValueError("tabella variabili globali non trovata")


def file_locali(cartella, programma=""):
    """File della tabella variabili (interne + esterne) di un POU."""
    trovati = []

    def cerca(e, prog=None):
        if e.get("type") in ("Program", "FunctionBlock", "Function"):
            prog = e.get("name")
        if e.get("type") == "Variables" and e.get("subtype") != "Global":
            trovati.append((prog, os.path.join(cartella, e.get("id") + ".xml")))
        for c in e:
            cerca(c, prog)

    for e in _entita(cartella):
        cerca(e)
    if not trovati:
        raise ValueError("nessuna tabella variabili locali trovata")
    if programma:
        for p, f in trovati:
            if p == programma:
                return f
        raise ValueError("POU '%s' non trovato: presenti %s"
                         % (programma, [p for p, _ in trovati]))
    if len(trovati) > 1:
        raise ValueError("il progetto ha piu' POU (%s): indicare 'programma'"
                         % [p for p, _ in trovati])
    return trovati[0][1]


# --------------------------------------------------------------- parsing
def leggi(path):
    """[(riga_intestazione_gruppo, [righe_variabile...]), ...] preservando
    tutto il resto del file."""
    testo = _testo(path)
    righe = testo.splitlines()
    testa, gruppi = [], []
    for r in righe:
        if r.startswith("+GN="):
            gruppi.append((r, []))
        elif r.startswith("++") and gruppi:
            gruppi[-1][1].append(r)
        elif not gruppi:
            testa.append(r)
    return testa, gruppi


def scrivi(path, testa, gruppi):
    out = list(testa)
    for intest, righe in gruppi:
        out.append(intest)
        out.extend(righe)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write("\r\n".join(out) + "\r\n")


def riga_variabile(v, gruppo):
    """dict -> riga '++D=...\\tN=...'. v: nome, tipo, [iniziale], [at],
    [ritentivo], [costante], [pubblicazione], [commento]."""
    campi = ["D=%s" % v.get("tipo", "BOOL"), "N=%s" % v["nome"]]
    if v.get("iniziale"):
        campi.append("IV=%s" % v["iniziale"])
    if v.get("at"):
        campi.append("AT=%s" % v["at"])
    if v.get("ritentivo"):
        campi.append("R=1")
    if v.get("costante"):
        campi.append("C=1")
    if v.get("pubblicazione"):
        campi.append("NTP=%s" % v["pubblicazione"])
    campi.append("G=%s" % SIGLA[gruppo])
    if v.get("commento"):
        campi.append("Com=%s" % str(v["commento"]).replace("\t", "$t"))
    return "++" + "\t".join(campi)


def campo(riga, chiave):
    """Valore di un campo della riga variabile ('D', 'N', 'AT', 'Com'...).
    Attenzione: il primo campo e' preceduto da '++', non da un TAB."""
    m = re.search(r"(?:^\+\+|\t)%s=([^\t\r\n]*)" % re.escape(chiave), riga)
    return m.group(1) if m else None


def nomi(righe):
    return [n for n in (campo(r, "N") for r in righe) if n is not None]


# --------------------------------------------------------------- scrittura
def aggiungi(path, gruppo, variabili, sostituisci=False, backup=True):
    """Aggiunge variabili al gruppo indicato ('globali'|'interne'|'esterne').
    Le variabili gia' presenti (stesso nome) vengono saltate, oppure
    sostituite se sostituisci=True. Ritorna (aggiunte, saltate)."""
    if backup and not os.path.exists(path + ".bak_slwd"):
        shutil.copyfile(path, path + ".bak_slwd")
    testa, gruppi = leggi(path)
    idx = None
    for k, (intest, _r) in enumerate(gruppi):
        if intest.startswith("+GN=%s\t" % SIGLA[gruppo]) or \
           intest.strip() == "+GN=%s" % SIGLA[gruppo]:
            idx = k
            break
    if idx is None:
        # il gruppo non c'e': lo si crea nella posizione corretta
        gruppi.append((GRUPPI[gruppo], []))
        idx = len(gruppi) - 1
    intest, righe = gruppi[idx]
    esistenti = set(nomi(righe))
    aggiunte, saltate = [], []
    for v in variabili:
        if isinstance(v, (list, tuple)):
            v = {"nome": v[0], "tipo": v[1] if len(v) > 1 else "BOOL"}
        n = v["nome"]
        if n in esistenti:
            if not sostituisci:
                saltate.append(n)
                continue
            righe = [r for r in righe if ("\tN=%s\t" % n) not in r + "\t"]
        righe.append(riga_variabile(v, gruppo))
        esistenti.add(n)
        aggiunte.append(n)
    gruppi[idx] = (intest, righe)
    scrivi(path, testa, gruppi)
    return aggiunte, saltate


def ripristina(path):
    if os.path.exists(path + ".bak_slwd"):
        shutil.copyfile(path + ".bak_slwd", path)
        return True
    return False


# --------------------------------------------------------- API di comodo
def crea_variabili(progetto, globali=(), interne=(), esterne=(),
                   programma="", forza=False):
    """Crea in un colpo solo le variabili nelle tre tabelle di un progetto
    CHIUSO. `esterne` puo' essere una lista di soli nomi: il tipo viene preso
    dalle globali corrispondenti.

    Ritorna un riepilogo. Solleva un errore se il progetto e' aperto in Sysmac
    (a meno di forza=True)."""
    cart = trova_progetto(progetto)
    if not forza and aperto_in_sysmac(cart):
        raise RuntimeError(
            "il progetto risulta APERTO in Sysmac Studio: chiuderlo prima di "
            "scrivere le variabili offline (altrimenti il salvataggio di "
            "Sysmac sovrascrive le modifiche)")
    res = {"progetto": os.path.basename(cart)}
    if globali:
        f = file_globali(cart)
        a, s = aggiungi(f, "globali", globali)
        res["globali"] = {"aggiunte": a, "gia_presenti": s}
    if interne or esterne:
        f = file_locali(cart, programma)
        if interne:
            a, s = aggiungi(f, "interne", interne)
            res["interne"] = {"aggiunte": a, "gia_presenti": s}
        if esterne:
            tipi = {}
            for _intest, righe_g in leggi(file_globali(cart))[1]:
                for riga in righe_g:
                    n_, d_ = campo(riga, "N"), campo(riga, "D")
                    if n_ and d_:
                        tipi[n_] = d_
            lista = []
            for v in esterne:
                n = v["nome"] if isinstance(v, dict) else (
                    v[0] if isinstance(v, (list, tuple)) else v)
                lista.append({"nome": n, "tipo": tipi.get(n, "BOOL")})
            a, s = aggiungi(f, "esterne", lista)
            res["esterne"] = {"aggiunte": a, "gia_presenti": s}
    return res


if __name__ == "__main__":
    import json
    import sys
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    cart = trova_progetto(sys.argv[1])
    print("cartella:", cart)
    print("aperto in Sysmac:", aperto_in_sysmac(cart))
    print("file globali:", file_globali(cart))
    try:
        print("file locali :", file_locali(cart))
    except ValueError as e:
        print("file locali : %s" % e)
    for f in (file_globali(cart),):
        testa, g = leggi(f)
        for intest, righe in g:
            print("  %s -> %d variabili" % (intest.split("\t")[0], len(righe)))
