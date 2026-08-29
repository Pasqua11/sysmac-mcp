# -*- coding: utf-8 -*-
"""autodiagnosi.py - un comando solo che dice se il server e' sano.

Da lanciare dopo OGNI modifica a server.py o ai moduli. Nasce da un problema
vero: il 27/08/2026 due modifiche fatte sostituendo testo "fino alla prossima
riga vuota" hanno CANCELLATO funzioni (undici la prima volta, due la seconda).
Entrambe le volte se ne e' accorto un controllo, non un collaudo: senza,
sarebbe finito in produzione.

    python autodiagnosi.py            tutto
    python autodiagnosi.py --veloce   salta i round-trip sul catalogo

Codice di uscita 0 se tutto passa.
"""
import ast
import io
import os
import shutil
import subprocess
import sys
import tempfile
import time

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)

MODULI = ["server.py", "simlink.py", "simvars.py", "slwd.py", "smc2.py",
          "sysmac_api.py", "esegui.py", "spec2rung.py", "json2spec.py",
          "rung2spec.py", "ladder_gen.py", "sysmac_project.py",
          "estrai_pin_reali.py", "movimentazione.py"]

# I tool che DEVONO esserci: se una modifica ne fa sparire uno, si vede subito.
TOOL_ATTESI = {
    "sysmac_status", "sysmac_exec", "sysmac_ui", "sysmac_progetto",
    "sysmac_screenshot", "sysmac_import_ladder_xml", "sysmac_compile_text",
    "sysmac_errors", "sysmac_save", "sysmac_sim",
    "sysmac_sim_reset", "sysmac_sim_vars", "sysmac_sim_read",
    "sysmac_sim_write", "sysmac_sim_watch", "sysmac_sim_test",
    "sysmac_vars_crea", "sysmac_vars_offline", "sysmac_register_from_error",
    "sysmac_istruzioni",
}
# Funzioni interne indispensabili, anche se non sono tool.
INTERNE_ATTESE = {"_ps", "_click", "_clickf", "_incolla", "_send_keys",
                  # accorpate in sysmac_ui: restano funzioni, non tool
                  "sysmac_send_keys", "sysmac_click", "sysmac_focus",
                  "sysmac_menu", "sysmac_button", "sysmac_ui_dump",
                  "sysmac_projects", "sysmac_sections", "sysmac_read",
                  "sysmac_find_var", "sysmac_vars_offline_stato",
                  "_focus_sysmac", "_massimizza", "_rect_sysmac", "_sim",
                  "_progetto_aperto", "_python", "_esegui_codice"}

esiti = []


def prova(nome, funzione, critica=True):
    t = time.time()
    try:
        msg = funzione()
        ok = True
    except Exception as e:
        msg = "%s: %s" % (type(e).__name__, e)
        ok = False
    esiti.append((nome, ok, critica))
    print("  %-34s %-4s %-52s (%.1fs)"
          % (nome, "OK" if ok else ("ERR" if critica else "!"),
             str(msg)[:52], time.time() - t))
    return ok


# ------------------------------------------------------------------ prove
def _sintassi():
    for m in MODULI:
        p = os.path.join(D, m)
        if not os.path.exists(p):
            raise AssertionError("modulo mancante: %s" % m)
        ast.parse(io.open(p, encoding="utf-8").read())
    return "%d moduli" % len(MODULI)


def _funzioni_server():
    s = io.open(os.path.join(D, "server.py"), encoding="utf-8").read()
    a = ast.parse(s)
    nomi = {n.name for n in a.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    mancanti = (TOOL_ATTESI | INTERNE_ATTESE) - nomi
    if mancanti:
        raise AssertionError("funzioni sparite: %s" % sorted(mancanti))
    import re
    esposti = set(re.findall(
        r"^@mcp\.tool\([^\n]*\)\n(?:async )?def (sysmac_\w+)", s, re.M))
    persi = TOOL_ATTESI - esposti
    if persi:
        raise AssertionError("tool non piu' esposti: %s" % sorted(persi))
    return "%d tool esposti, %d funzioni" % (len(esposti), len(nomi))


def _import():
    import sysmac_api
    n = len(sysmac_api.NAMESPACE)
    if n < 25:
        raise AssertionError("namespace di sysmac_exec troppo piccolo: %d" % n)
    return "namespace sysmac_exec: %d voci" % n


def _spec2rung_base():
    import spec2rung
    casi = [
        {"cmt": "serie", "chain": ["A", "/B", "(C)"]},
        {"cmt": "or", "chain": [{"or": ["A", "B"]}, "/C", "(D)"]},
        {"cmt": "set", "chain": ["A", "(S M)"]},
        {"cmt": "fork", "chain": ["A"], "out": ["(X)", "(Y)"]},
        {"cmt": "ton", "chain": ["A", {"fb": "TON", "inst": "T1",
                                       "p": {"PT": "T#5s"}}, "(Q)"]},
    ]
    for c in casi:
        ok, ottenuto = spec2rung.verifica_roundtrip(c)
        if not ok and c["cmt"] != "ton":     # il TON aggiunge i pin non connessi
            raise AssertionError("round-trip fallito su '%s': %s"
                                 % (c["cmt"], ottenuto))
    return "%d topologie" % len(casi)


def _catalogo_istruzioni():
    import istruzioni
    r = istruzioni.riepilogo()
    if r["istruzioni"] < 400:
        raise AssertionError("catalogo troppo piccolo: %s" % r)
    d = istruzioni.dettaglio("TON")
    if "In" not in d or "BOOL" not in d:
        raise AssertionError("scheda TON incompleta")
    return "%d istruzioni, %d con ST" % (r["istruzioni"], r["con_espressione_ST"])


def _pin_reali():
    import json
    p = os.path.join(D, "pin_reali.json")
    d = json.load(io.open(p, encoding="utf-8"))
    if "TON" not in d or not d["TON"]["in"]:
        raise AssertionError("firma di TON mancante")
    return "%d blocchi noti" % len(d)


def _slwd_su_copia():
    import slwd
    import simvars
    prog = [n for n, _p in slwd.elenco_progetti()]
    if not prog:
        raise AssertionError("nessun progetto nell'archivio")
    cart = slwd.trova_progetto(prog[0])
    tmp = tempfile.mkdtemp(prefix="diag_")
    try:
        f = os.path.join(tmp, "g.xml")
        shutil.copyfile(slwd.file_globali(cart), f)
        a, _s = slwd.aggiungi(f, "globali",
                              [("DIAG_X", "REAL")], backup=False)
        if a != ["DIAG_X"]:
            raise AssertionError("scrittura variabile non riuscita")
        simvars.normalizza_tipo("ARRAY[1..4] OF BOOL")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return "%d progetti in archivio" % len(prog)


def _smc2_ciclo():
    import smc2
    import slwd
    modello = os.path.join(D, "modelli", "modello_NJ501.smc2")
    if not os.path.exists(modello):
        raise AssertionError("manca il modello %s" % modello)
    tmp = tempfile.mkdtemp(prefix="diag_")
    try:
        f = os.path.join(tmp, "Diagnosi.smc2")
        smc2.crea(modello, f)
        with smc2.progetto(f) as p:
            slwd.crea_variabili(p.cartella, globali=[("DIAG_SMC2", "INT")],
                                forza=True)
            p.tocca()
        if "DIAG_SMC2" not in smc2.variabili_globali(f):
            raise AssertionError("la variabile non e' finita nel file")
        return "crea + scrivi + rileggi"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _roundtrip(script):
    def f():
        r = subprocess.run([sys.executable, script], capture_output=True,
                           text=True, errors="replace", cwd=D, timeout=180)
        for riga in (r.stdout or "").splitlines():
            if "IDENTICI" in riga or "ESATTO" in riga:
                esito = riga.strip()
            if "DIVERGENTI" in riga or riga.strip().startswith("diversi"):
                n = riga.split()[-1]
                if n not in ("0",):
                    raise AssertionError(riga.strip())
        return esito
    return f


def _simulatore():
    import simlink
    if not simlink.porta_aperta():
        return "spento (informativo)"
    c = simlink.Sim().connect(attesa=6)
    try:
        return "acceso, CPU in %s" % c.modo().get("modo")
    finally:
        c.close()


def main():
    veloce = "--veloce" in sys.argv
    t0 = time.time()
    print("AUTODIAGNOSI  %s" % time.strftime("%d/%m/%Y %H:%M"))
    print("-" * 104)
    print(" STRUTTURA")
    prova("sintassi dei moduli", _sintassi)
    prova("tool e funzioni di server.py", _funzioni_server)
    prova("ambiente di sysmac_exec", _import)
    print(" GENERAZIONE")
    prova("spec2rung: topologie base", _spec2rung_base)
    prova("firme dei blocchi funzione", _pin_reali)
    prova("catalogo istruzioni (manuale)", _catalogo_istruzioni)
    if not veloce:
        prova("round-trip sulla spec (17.500 rung)",
              _roundtrip("roundtrip_catalogo.py"))
        prova("round-trip severo JSON (17.500 rung)",
              _roundtrip("roundtrip_json.py"))
    print(" SCRITTURA")
    prova("slwd: variabili su copia", _slwd_su_copia)
    prova("smc2: progetto in un file", _smc2_ciclo)
    print(" AMBIENTE (informativo)")
    prova("simulatore", _simulatore, critica=False)
    print("-" * 104)
    ko = [n for n, ok, crit in esiti if not ok and crit]
    print("%d prove, %d fallite%s  -  %.1f s"
          % (len(esiti), len(ko), (": " + ", ".join(ko)) if ko else "",
             time.time() - t0))
    print("ESITO:", "TUTTO A POSTO" if not ko else "CI SONO PROBLEMI")
    return 0 if not ko else 1


if __name__ == "__main__":
    sys.exit(main())
