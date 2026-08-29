# -*- coding: utf-8 -*-
"""indicizza_manuale.py - costruisce l'indice delle ISTRUZIONI Sysmac partendo
dai manuali di riferimento installati con Sysmac Studio.

I .chm in Help\\en-US contengono la guida ufficiale alle istruzioni della
versione installata: e' la fonte di verita' (non la memoria di Claude) per
sapere quali istruzioni esistono, con che parametri e che tipi.

Le pagine hanno nomi generati (hub1484547388727.html), quindi si indicizza per
<title>. Uscita: manuale\\indice_istruzioni.json
"""
import html as _html
import io
import json
import os
import re
import subprocess
import sys

D = os.path.dirname(os.path.abspath(__file__))
HELP = r"C:\Program Files (x86)\OMRON\Sysmac Studio\Help\en-US"
SETTE = r"C:\Program Files\7-Zip\7z.exe"

MANUALI = {
    "istruzioni": "CommandRef_Help.chm",     # istruzioni standard
    "nj": "CommandRef_NJ.chm",               # NX/CNC/robotica/SECS
    "motion": "CommandRef_Motion_Help.chm",  # MC_*
}


def estrai(nome_chm, destinazione):
    src = os.path.join(HELP, nome_chm)
    if not os.path.exists(src):
        return "manuale assente: %s" % nome_chm
    if os.path.isdir(destinazione) and os.listdir(destinazione):
        return "gia' estratto"
    os.makedirs(destinazione, exist_ok=True)
    tmp = os.path.join(D, "_tmp.chm")
    import shutil
    shutil.copyfile(src, tmp)          # 7z fatica sui percorsi con spazi
    try:
        r = subprocess.run([SETTE, "x", tmp, "-o" + destinazione, "-y"],
                           capture_output=True, text=True, errors="replace",
                           timeout=240)
        if r.returncode:
            return "7z ha risposto %d" % r.returncode
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass
    return "estratto"


def testo(percorso, limite=200000):
    t = io.open(percorso, encoding="utf-8", errors="replace").read(limite)
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", t)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", _html.unescape(t)).strip()


def titolo(percorso):
    t = io.open(percorso, encoding="utf-8", errors="replace").read(4000)
    m = re.search(r"(?is)<title>(.*?)</title>", t)
    return re.sub(r"\s+", " ", _html.unescape(m.group(1))).strip() if m else ""


def indicizza(radice, origine):
    voci = []
    for cur, _d, files in os.walk(radice):
        for f in files:
            if not f.lower().endswith((".htm", ".html")):
                continue
            p = os.path.join(cur, f)
            t = titolo(p)
            if not t or len(t) > 120:
                continue
            voci.append({"titolo": t, "file": os.path.relpath(p, D),
                         "origine": origine,
                         "cartella": os.path.basename(cur),
                         "byte": os.path.getsize(p)})
    return voci


def main():
    tutte = []
    for chiave, chm in MANUALI.items():
        dest = os.path.join(D, "manuale", chiave)
        print("%-11s %-28s %s" % (chiave, chm, estrai(chm, dest)))
        v = indicizza(dest, chiave)
        print("            pagine indicizzate: %d" % len(v))
        tutte.extend(v)

    # una pagina e' "un'istruzione" se il titolo e' un identificatore valido
    ist = {}
    for v in tutte:
        t = v["titolo"]
        nome = t.split()[0].strip()
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{1,40}", nome) and v["byte"] > 3000:
            prec = ist.get(nome)
            if prec is None or v["byte"] > prec["byte"]:
                ist[nome] = v

    out = os.path.join(D, "manuale", "indice_istruzioni.json")
    with io.open(out, "w", encoding="utf-8") as fh:
        json.dump(ist, fh, ensure_ascii=False, indent=1, sort_keys=True)
    print("\nISTRUZIONI INDICIZZATE: %d  ->  %s" % (len(ist), os.path.relpath(out, D)))

    per_origine = {}
    for v in ist.values():
        per_origine[v["origine"]] = per_origine.get(v["origine"], 0) + 1
    print("per manuale:", per_origine)
    noti = [n for n in ("TON", "TOF", "CTU", "CTD", "MOVE", "SetBit", "AryMove",
                        "PIDAT", "TimeProportionalOut", "ScaleTrans", "MC_MoveAbsolute",
                        "MC_Power", "Get1sClk", "SR", "RS", "UpperCase", "Sel", "MAX")
            if n in ist]
    print("controllo a campione (%d/18 trovate):" % len(noti), noti)
    return 0


if __name__ == "__main__":
    sys.exit(main())
