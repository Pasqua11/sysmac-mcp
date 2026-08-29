"""
sysmac_project.py - Lettura DIRETTA dei progetti Sysmac Studio dal disco.

SCOPERTA (26/08/2026): Sysmac Studio non tiene i progetti in un file binario
opaco. Ogni progetto e' una cartella in C:\\Omron\\Data\\Solution\\<guid>\\ dove:

  <guid>.oem      = albero delle entita' (XML): programmi, sezioni, variabili,
                    task... ognuna con type / subtype / name / id
  <id-sezione>.xml = corpo della sezione ladder. Nonostante l'estensione .xml
                    il contenuto e' JSON: UNA RIGA PER RUNG.

Esempio di rung reale:
  {"CLs":[{"__type":"LD","Not":true,"Var":"IN_MARCIA"},
          {"__type":"ST","Ix":1,"Var":"Marcia_ON","X":1}],
   "CMT":"GIRO IL BIT DI MARCIA","LRI":2,"RRI":3,"VLs":[]}

Tipi di cella osservati su 1475 sezioni ladder di 112 progetti reali:
  LD  contatto            (Var, Not=NC, Up/Dwn = differenziazione)
  ST  bobina / uscita     (Var, S / RS = set-reset, Not = uscita NOT)
  FB  blocco funzione     (Name = tipo, Var = istanza, In[] / Out[])
  F   funzione            (Name, In[] / Out[])
  IST ST in linea         (TXT = codice)
  PRM parametro di FB/F   (Arg = nome pin, Type, Var = valore, IO = in-out)
  PF  pin di power flow   (Arg)
  HL  collegamento oriz.  (solo grafica)
  X, Y = posizione in griglia; Ix = identificatore interno della cella
  VLs  = collegamenti verticali (rami paralleli)
  LRI / RRI = indici barra sinistra / destra

A COSA SERVE: leggere e cercare dentro un progetto senza aprirlo in Sysmac e
senza screenshot. E' l'operazione piu' frequente e finora la piu' costosa.

SOLA LETTURA. Questo modulo non scrive nulla dentro C:\\Omron.
"""

import json
import os
import re
import xml.etree.ElementTree as ET

SOLUTION_DIR = r"C:\Omron\Data\Solution"


# --------------------------------------------------------------- progetti

def list_projects(filtro: str = "") -> list:
    """Progetti presenti sul disco: nome, data di modifica, cartella.

    filtro = sottostringa (case-insensitive) sul nome.
    """
    out = []
    if not os.path.isdir(SOLUTION_DIR):
        return out
    for d in os.listdir(SOLUTION_DIR):
        p = os.path.join(SOLUTION_DIR, d)
        oem = os.path.join(p, d + ".oem")
        if not os.path.isdir(p) or not os.path.exists(oem):
            continue
        nome = ""
        try:
            # il nome sta nella prima entita' Solution: si legge senza
            # parsare tutto il file (alcuni .oem sono grossi)
            with open(oem, encoding="utf-8-sig", errors="ignore") as fh:
                testa = fh.read(4000)
            m = re.search(r'type="Solution"[^>]*?name="([^"]*)"', testa)
            if m:
                nome = m.group(1)
        except OSError:
            continue
        if filtro and filtro.lower() not in nome.lower():
            continue
        out.append({
            "nome": nome or "(senza nome)",
            "id": d,
            "path": p,
            "modificato": _mtime(oem),
        })
    out.sort(key=lambda r: r["modificato"], reverse=True)
    return out


def _mtime(path: str) -> str:
    import datetime
    return datetime.datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d %H:%M")


def find_project(nome_o_id: str) -> dict:
    """Progetto per nome esatto, sottostringa del nome, o GUID."""
    prog = list_projects()
    for p in prog:
        if p["id"] == nome_o_id or p["nome"] == nome_o_id:
            return p
    cand = [p for p in prog if nome_o_id.lower() in p["nome"].lower()]
    if len(cand) == 1:
        return cand[0]
    if not cand:
        raise LookupError(f"Nessun progetto corrisponde a '{nome_o_id}'.")
    raise LookupError("Piu' progetti corrispondono a '%s': %s" %
                      (nome_o_id, ", ".join(p["nome"] for p in cand[:10])))


def entities(proj: dict) -> list:
    """Tutte le entita' del progetto (type, subtype, name, id)."""
    oem = os.path.join(proj["path"], proj["id"] + ".oem")
    tree = ET.parse(oem)
    out = []
    for e in tree.iter("Entity"):
        out.append({
            "type": e.get("type") or "",
            "subtype": e.get("subtype") or "",
            "name": e.get("name") or "",
            "id": e.get("id") or "",
        })
    return out


def sections(proj: dict) -> list:
    """Sezioni ladder del progetto, con numero di rung e file."""
    out = []
    for e in entities(proj):
        if e["type"] == "PouBody" and e["subtype"] == "Ladder":
            f = os.path.join(proj["path"], e["id"] + ".xml")
            n = 0
            if os.path.exists(f):
                with open(f, encoding="utf-8-sig", errors="ignore") as fh:
                    n = sum(1 for r in fh if r.strip())
            out.append({"nome": e["name"], "id": e["id"], "file": f, "rung": n})
    return out


# --------------------------------------------------------------- decodifica

def _pins(lista) -> str:
    """Parametri di FB / F: PRM (Arg:=Var) e PF (pin di power flow)."""
    parti = []
    for p in lista or []:
        t = p.get("__type")
        if t == "PRM":
            v = p.get("Var", "")
            arg = p.get("Arg", "?")
            io = "<=>" if p.get("IO") else ":="
            parti.append(f"{arg}{io}{v}" if v != "" else f"{arg}:=-")
        elif t == "PF":
            parti.append(f"{p.get('Arg', '?')}=<flusso>")
        else:
            parti.append(json.dumps(p, ensure_ascii=False))
    return ", ".join(parti)


def _cella(c: dict) -> str:
    t = c.get("__type")
    if t == "LD":
        s = "LDN" if c.get("Not") else "LD"
        if c.get("Up"):
            s += "^"       # differenziazione sul fronte di salita
        if c.get("Dwn"):
            s += "v"       # fronte di discesa
        return f"{s} {c.get('Var', '?')}"
    if t == "ST":
        s = "OUT"
        if c.get("Not"):
            s = "OUT-NOT"
        if c.get("S"):
            s = "SET"
        if c.get("RS"):
            s = "RESET"
        return f"{s} {c.get('Var', '?')}"
    if t == "FB":
        return "%s %s(%s) => %s" % (c.get("Name", "?"), c.get("Var", ""),
                                    _pins(c.get("In")), _pins(c.get("Out")))
    if t == "F":
        return "%s(%s) => %s" % (c.get("Name", "?"), _pins(c.get("In")),
                                 _pins(c.get("Out")))
    if t == "IST":
        txt = (c.get("TXT") or "").replace("\r\n", " / ").replace("\n", " / ")
        return "ST-INLINE { " + txt + " }"
    if t == "HL":
        return ""          # solo grafica: nessun contenuto logico
    # tipo non ancora incontrato: si mostra grezzo invece di inventare
    return "?" + json.dumps(c, ensure_ascii=False)


def decode_rung(obj: dict, numero: int = -1) -> str:
    """Un rung JSON -> testo leggibile. Le celle sono ordinate per riga (Y)
    e poi per colonna (X), come si leggono a schermo."""
    righe = []
    if obj.get("CMT"):
        righe.append(("// " + str(obj["CMT"]).replace("\r\n", " ")).rstrip())
    celle = [c for c in obj.get("CLs", []) if isinstance(c, dict)]
    celle.sort(key=lambda c: (c.get("Y", 0), c.get("X", 0)))
    per_riga = {}
    for c in celle:
        s = _cella(c)
        if s:
            per_riga.setdefault(c.get("Y", 0), []).append(s)
    for y in sorted(per_riga):
        righe.append("   " + " -- ".join(per_riga[y]))
    if not per_riga:
        righe.append("   (rung vuoto)")
    testa = f"R{numero}" if numero >= 0 else "R?"
    return testa + " " + ("\n" + " " * len(testa) + " ").join(righe)


def read_section(proj: dict, nome_sezione: str = "", max_rung: int = 0) -> str:
    """Testo leggibile di una sezione (o di tutte, se nome_sezione e' vuoto)."""
    sez = sections(proj)
    if nome_sezione:
        sez = [s for s in sez if s["nome"].lower() == nome_sezione.lower()] or \
              [s for s in sez if nome_sezione.lower() in s["nome"].lower()]
        if not sez:
            raise LookupError(f"Sezione '{nome_sezione}' non trovata in {proj['nome']}.")
    out = []
    for s in sez:
        out.append(f"===== {proj['nome']} / {s['nome']} ({s['rung']} rung) =====")
        for i, riga in enumerate(_righe(s["file"])):
            if max_rung and i >= max_rung:
                out.append(f"... ({s['rung'] - max_rung} rung non mostrati)")
                break
            try:
                out.append(decode_rung(json.loads(riga), i))
            except json.JSONDecodeError:
                out.append(f"R{i} (riga non decodificabile)")
    return "\n".join(out)


def _righe(path: str):
    with open(path, encoding="utf-8-sig", errors="ignore") as fh:
        for r in fh:
            if r.strip():
                yield r


def find_var(proj: dict, variabile: str, solo_scrittura: bool = False) -> str:
    """Dove viene usata una variabile: sezione, numero di rung, ruolo.

    solo_scrittura=True restituisce solo i punti in cui viene SCRITTA
    (bobine, SET/RESET, parametri di uscita): serve per capire chi la comanda.
    """
    v = variabile.lower()
    out = []
    for s in sections(proj):
        for i, riga in enumerate(_righe(s["file"])):
            if v not in riga.lower():
                continue
            try:
                obj = json.loads(riga)
            except json.JSONDecodeError:
                continue
            for c in obj.get("CLs", []):
                if not isinstance(c, dict):
                    continue
                t = c.get("__type")
                usato = (c.get("Var", "") or "").lower() == v or \
                        v in json.dumps(c, ensure_ascii=False).lower()
                if not usato:
                    continue
                if t == "ST":
                    ruolo = "SCRITTA (bobina)"
                elif t == "LD":
                    ruolo = "letta (contatto)"
                elif t in ("FB", "F"):
                    ruolo = f"in {c.get('Name', '?')} {c.get('Var', '')}"
                elif t == "IST":
                    ruolo = "in ST in linea"
                else:
                    ruolo = t or "?"
                if solo_scrittura and "SCRITTA" not in ruolo and t != "IST":
                    continue
                out.append(f"{s['nome']:14} R{i:<4} {ruolo:22} {_cella(c)[:90]}")
    if not out:
        return f"'{variabile}' non trovata in {proj['nome']}."
    return f"'{variabile}' in {proj['nome']}: {len(out)} occorrenze\n" + "\n".join(out)


# --------------------------------------------------------------- CLI

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print(__doc__)
        print("uso: sysmac_project.py list | sections <prog> | read <prog> [sez] | var <prog> <variabile>")
    elif sys.argv[1] == "list":
        for p in list_projects(sys.argv[2] if len(sys.argv) > 2 else ""):
            print(f"{p['modificato']}  {p['nome']}")
    elif sys.argv[1] == "sections":
        pr = find_project(sys.argv[2])
        for s in sections(pr):
            print(f"{s['rung']:5} rung  {s['nome']}")
    elif sys.argv[1] == "read":
        pr = find_project(sys.argv[2])
        print(read_section(pr, sys.argv[3] if len(sys.argv) > 3 else ""))
    elif sys.argv[1] == "var":
        pr = find_project(sys.argv[2])
        print(find_var(pr, sys.argv[3]))
