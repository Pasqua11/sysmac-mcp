"""sysmac_api.py - ambiente in cui gira il codice passato a `sysmac_exec`.

Espone con nomi brevi tutto quello che serve per pilotare Sysmac Studio e il
suo simulatore, cosi' una sequenza che richiederebbe 8-10 chiamate MCP separate
si scrive come un unico script.

Disponibili automaticamente nello script:

  ---- simulatore (solo variabili GLOBALI, simulazione in RUN) ----
  leggi("A","B")                -> {"A":..., "B":...}
  scrivi(A=1, PV_Ph=7.2)        -> scrive e rilegge
  watch("A","B", secondi=10)    -> timeline (campiona solo i cambiamenti)
  collauda(scenario)            -> esito PASS/FAIL dello scenario
  sim()                         -> l'oggetto Sim completo (read/write/info...)

  ---- progetto ----
  progetto()                    -> nome del progetto aperto
  usa_file("...smc2")           -> se il progetto sta in un file
  dialogo_aperto()              -> testo del dialogo modale, "" se non c'e'
  chiudi_dialogo("OK")          -> preme un pulsante del dialogo
  chiudi_progetto()             -> chiude il progetto (serve per l'offline)
  riavvia_sysmac()              -> se la pagina iniziale si incastra
  apri_progetto("Nome")         -> riapre un progetto cercandolo per nome
  vars_globali(filtro="")       -> {nome: tipo} dal disco, senza GUI
  vars_offline(progetto, globali=[...], interne=[...], esterne=[...])
                                -> crea variabili scrivendo i file (progetto CHIUSO)

  ---- GUI / ciclo di lavoro ----
  compila()                     -> "ERRORI=n AVVISI=m" + righe di errore
  salva()                       -> Ctrl+S
  sim_avvia(attesa=50)          -> F5 e attende che il socket sia pronto
  sim_ferma()                   -> Shift+F5
  importa(xml_o_percorso)       -> incolla rung in ladder (simulazione ferma)

  ---- moduli completi ----
  simlink, simvars, slwd, S (= server.py, tutti i tool come funzioni)
  json, time, re, os

Convenzioni: tutto quello che stampi con print() torna a Claude. L'ultima
espressione dello script, se c'e', viene stampata da sola. La connessione al
simulatore viene aperta una volta sola e chiusa in automatico alla fine.
"""

import json
import os
import re
import sys
import time

_D = os.path.dirname(os.path.abspath(__file__))
if _D not in sys.path:
    sys.path.insert(0, _D)

import simlink            # noqa: E402
import smc2               # noqa: E402
import istruzioni         # noqa: E402
import simvars            # noqa: E402
import slwd               # noqa: E402
import server as S        # noqa: E402  (tutti i tool MCP come normali funzioni)

_sessione = {"sim": None, "file": ""}


def _flat(args):
    out = []
    for a in args:
        if isinstance(a, (list, tuple, set)):
            out.extend(str(x) for x in a)
        elif isinstance(a, str) and ("," in a or ";" in a):
            out.extend(x.strip() for x in re.split(r"[,;]", a) if x.strip())
        else:
            out.append(str(a))
    return out


# ------------------------------------------------------------- simulatore
def usa_file(percorso_smc2):
    """Indica che il progetto aperto in Sysmac sta in un FILE .smc2.

    Serve perche' un progetto gestito nel file NON compare nell'archivio, e
    senza i tipi presi dal progetto il simulatore restituisce solo la
    dimensione in bit (REAL e DINT indistinguibili)."""
    _sessione["file"] = percorso_smc2
    chiudi()
    return percorso_smc2


def sim(progetto_nome=""):
    """Connessione al simulatore, aperta una volta e riusata."""
    if _sessione["sim"] is None:
        _sessione["sim"] = S._sim(progetto_nome or _sessione.get("file", ""))
    return _sessione["sim"]


def leggi(*nomi):
    return sim().read_many(_flat(nomi))


def scrivi(**valori):
    s = sim()
    s.write_many(valori)
    return s.read_many(list(valori))


def watch(*nomi, secondi=5.0, intervallo=0.2, solo_cambi=True):
    return sim().watch(_flat(nomi), float(secondi), float(intervallo), solo_cambi)


def collauda(scenario):
    """scenario: dict, testo JSON o percorso di un file .json."""
    if isinstance(scenario, str):
        sc = scenario.strip()
        if not sc.startswith("{"):
            sc = open(sc, encoding="utf-8-sig").read()
        scenario = json.loads(sc)
    return sim().esegui_scenario(scenario)


def sim_pronto():
    """True se il programma sta GIRANDO davvero (CPU simulata in RUN).
    Nota: il socket risponde anche a simulazione ferma, quindi non basta
    riuscire a connettersi: si controlla WorkMode con GetMode."""
    try:
        return sim().in_run()
    except Exception:
        return False


def modo():
    """Stato della CPU simulata: {"modo": "RUN"|"PROGRAM", ...}."""
    return sim().modo()


# ATTENZIONE - i comandi Run/Stop sul socket ESISTONO e cambiano davvero il
# modo della CPU simulata, ma NON vanno usati per pilotare la simulazione:
#  1) dopo un `Run` da socket la logica viene valutata ma i TIMER NON
#     AVANZANO (il ciclo del semaforo resta bloccato in fase 1 all'infinito);
#  2) Sysmac non si accorge del cambio di modo e il successivo avvio da GUI
#     fallisce con "Si e' verificato un errore o un timeout" (verificato
#     27/08/2026, il simulatore va poi riavviato).
# Restano raggiungibili come diagnostica via sim().run() / sim().stop(),
# ma NON sono esposti nel namespace di sysmac_exec.


# ---------------------------------------------------------------- progetto
def progetto():
    return S._progetto_aperto()


def vars_globali(filtro="", progetto_nome=""):
    t = simvars.variabili_globali(progetto_nome or progetto())
    if filtro:
        f = filtro.lower()
        t = {k: v for k, v in t.items() if f in k.lower()}
    return t


def vars_offline(progetto_nome, globali=(), interne=(), esterne=(), programma=""):
    """Crea variabili scrivendo i file di progetto. Il progetto deve essere
    CHIUSO in Sysmac. Accetta ("NOME","TIPO") oppure {"nome":..,"tipo":..}.

    `progetto_nome` puo' essere il nome di un progetto dell'archivio OPPURE il
    percorso di un file .smc2. Quest'ultima e' la strada veloce: sul progetto
    da 90 rung le 166 variabili sono entrate in 0,1 s contro i 37 s
    dell'archivio (misurato il 28/08/2026)."""
    if str(progetto_nome).lower().endswith(".smc2"):
        return S.sysmac_vars_offline(progetto=progetto_nome, globali=globali,
                                     interne=interne, esterne=esterne,
                                     programma=programma)
    return slwd.crea_variabili(progetto_nome, globali=globali, interne=interne,
                               esterne=esterne, programma=programma)


def dialogo_aperto():
    """Testo della finestra di dialogo eventualmente aperta in Sysmac, oppure
    "" se non ce n'e'. Le finestre modali bloccano qualunque automazione: va
    controllato PRIMA di aspettare a lungo qualcosa."""
    try:
        albero = S.sysmac_ui_dump("", 12) or ""
    except Exception:
        return ""
    righe = [r for r in albero.splitlines() if r.startswith("Pane")]
    for r in righe:
        testo = r.split("|", 1)[1].strip() if "|" in r else ""
        if len(testo) > 12:
            return testo
    return ""


def chiudi_dialogo(pulsante="OK"):
    """Preme un pulsante della finestra di dialogo aperta."""
    return S.sysmac_button(pulsante)


def chiudi_progetto(salva_prima=False, tentativi=3):
    """Chiude il progetto aperto (serve prima di ogni scrittura offline).
    Gestisce la domanda "Salvare il progetto prima di chiudere?"."""
    for _ in range(tentativi):
        # un dialogo modale rimasto aperto blocca qualsiasi cosa: si scaccia
        # prima di provare a chiudere il progetto
        for _k in range(3):
            if not dialogo_aperto():
                break
            chiudi_dialogo("OK")
            time.sleep(1.5)
        t = S._progetto_aperto()
        if not t:
            return "nessun progetto aperto"
        S._clickf(23, 47)          # menu File
        time.sleep(0.9)
        S._clickf(45, 78)          # prima voce: Chiudi
        time.sleep(4)
        d = dialogo_aperto()
        if "alva" in d:            # "Salvare il progetto prima di chiudere?"
            chiudi_dialogo("S\u00ec" if salva_prima else "No")
            time.sleep(6)
        time.sleep(4)
        if not S._progetto_aperto():
            return "progetto chiuso"
    return "NON sono riuscito a chiudere il progetto (dialogo: %r)" % dialogo_aperto()


def riavvia_sysmac(attesa=90):
    """Chiude e rilancia Sysmac Studio.

    Serve perche' la pagina iniziale puo' entrare in uno stato in cui i clic
    non aprono piu' nulla: finestre di scelta file rimaste aperte, elenco
    "File di progetto recenti" che non risponde. Riavviare la ripulisce
    (verificato il 27/08/2026: subito dopo, l'apertura ha impiegato 4 s).

    RIFIUTA se c'e' un progetto aperto: non si rischia di perdere modifiche
    non salvate."""
    aperto = S._progetto_aperto()
    if aperto:
        raise RuntimeError(
            "c'e' il progetto '%s' aperto: chiuderlo (chiudi_progetto()) prima "
            "di riavviare, altrimenti si rischia di perdere modifiche" % aperto)
    chiudi()
    S._ps("Stop-Process -Name SysmacStudio -Force -ErrorAction SilentlyContinue")
    time.sleep(6)
    S._ps('Start-Process "C:\\Program Files (x86)\\OMRON\\Sysmac Studio\\'
          'SysmacStudio.exe"')
    t0 = time.time()
    while time.time() - t0 < attesa:
        time.sleep(4)
        try:
            if S._sysmac_hwnd():
                time.sleep(4)
                return round(time.time() - t0, 1)
        except Exception:
            pass
    raise RuntimeError("Sysmac non e' ripartito entro %d s" % attesa)


def apri_progetto(nome, attesa=35, riavvio=True):
    """Apre un progetto dalla pagina iniziale, cercandolo per NOME nella
    casella di ricerca invece di fidarsi dell'ordinamento della lista.

    Se non ci riesce e `riavvio` e' attivo, riavvia Sysmac (la pagina iniziale
    si incastra) e ritenta una volta sola."""
    if S._progetto_aperto():
        return "c'e' gia' un progetto aperto: %s" % S._progetto_aperto()
    S._clickf(116, 186)                 # "Apri progetto"
    time.sleep(3)
    S._clickf(1120, 168)                # casella "Ricerca nome progetto"
    time.sleep(0.5)
    S._send_keys("^a")
    S._incolla(nome)
    time.sleep(2.5)
    S._clickf(497, 218, double=True)    # prima riga del risultato
    t0 = time.time()
    while time.time() - t0 < attesa:
        time.sleep(3)
        if S._progetto_aperto():
            return S._progetto_aperto()
        d = dialogo_aperto()
        if d:
            return "bloccato da un dialogo: %r" % d
    if riavvio:
        # pagina iniziale incastrata: riavviare Sysmac la ripulisce
        try:
            secondi = riavvia_sysmac()
        except Exception as e:
            return "non aperto entro %d s e riavvio non riuscito: %s" % (attesa, e)
        return "%s (dopo riavvio di Sysmac in %.0f s)" % (
            apri_progetto(nome, attesa, riavvio=False), secondi)
    return "progetto non aperto entro %d s" % attesa


# ------------------------------------------------------------ ciclo lavoro
def compila(attesa=15):
    return S.sysmac_compile_text(attesa)


def errori(max_righe=30):
    return S.sysmac_errors(max_righe)


def salva():
    return S.sysmac_save()


def sim_ferma():
    """Ferma la simulazione (Shift+F5) e libera l'editor ladder."""
    chiudi()
    r = S.sysmac_sim("stop")
    time.sleep(3)
    return r


def sim_avvia(attesa=120, passo=4, auto=True, assestamento=3.0):
    """Avvia la simulazione (F5) e ATTENDE che la CPU sia davvero in RUN.
    Ritorna i secondi impiegati; 0.0 se era gia' in RUN. Dopo il passaggio in
    RUN aspetta `assestamento` secondi: i primissimi cicli non sono regolari e
    un collaudo lanciato subito puo' fallire su un programma corretto.

    Mentre aspetta CONTROLLA LE FINESTRE DI DIALOGO: una modale blocca l'avvio
    e prima si restava fermi fino alla scadenza senza capire perche'. Con
    auto=True il caso noto "La compilazione non e' stata ancora completata"
    (tipico dopo una scrittura offline) viene risolto da solo: OK, F8, ritenta.

    Serve F5: il comando `Run` sul socket mette in RUN ma lascia i timer fermi,
    quindi non e' una scorciatoia valida (v. nota sopra)."""
    t0 = time.time()
    if sim_pronto():
        return 0.0
    chiudi()
    S.sysmac_sim("start")
    gia_ricompilato = False
    while time.time() - t0 < attesa:
        time.sleep(passo)
        try:
            if sim().in_run():
                # subito dopo il passaggio in RUN i primi cicli non sono
                # ancora regolari: un collaudo lanciato all'istante puo' dare
                # FAIL su un programma corretto (osservato il 27/08/2026).
                time.sleep(assestamento)
                return round(time.time() - t0, 1)
        except Exception:
            chiudi()
        d = dialogo_aperto()
        if not d:
            continue
        if auto and "ompila" in d and not gia_ricompilato:
            chiudi_dialogo("OK")
            time.sleep(1)
            compila(25)
            gia_ricompilato = True
            S.sysmac_sim("start")
            continue
        raise RuntimeError(
            "l'avvio della simulazione e' bloccato da una finestra di dialogo: "
            "%r. Rispondere con chiudi_dialogo('OK') e riprovare." % d)
    raise RuntimeError(
        "il simulatore non e' andato in RUN entro %d s (nessun dialogo "
        "aperto). Provare: compila() e poi di nuovo sim_avvia()." % attesa)


def importa(xml_o_percorso, riga_y=210):
    """Incolla rung in ladder (serve editor aperto e simulazione ferma)."""
    x = xml_o_percorso
    if not x.lstrip().startswith("<"):
        x = open(x, encoding="utf-8-sig").read()
    return S.sysmac_import_ladder_xml(x, riga_y)


def chiudi():
    if _sessione["sim"] is not None:
        try:
            _sessione["sim"].close()
        except Exception:
            pass
        _sessione["sim"] = None


NAMESPACE = {
    "leggi": leggi, "scrivi": scrivi, "watch": watch, "collauda": collauda,
    "sim": sim, "sim_pronto": sim_pronto, "sim_avvia": sim_avvia,
    "modo": modo, "chiudi": chiudi, "usa_file": usa_file,
    "riavvia_sysmac": riavvia_sysmac, "dialogo_aperto": dialogo_aperto,
    "chiudi_dialogo": chiudi_dialogo, "chiudi_progetto": chiudi_progetto,
    "apri_progetto": apri_progetto,
    "sim_ferma": sim_ferma, "progetto": progetto, "vars_globali": vars_globali,
    "vars_offline": vars_offline, "compila": compila, "errori": errori,
    "salva": salva, "importa": importa,
    "simlink": simlink, "simvars": simvars, "slwd": slwd, "S": S,
    "smc2": smc2, "istruzioni": istruzioni,
    "json": json, "time": time, "re": re, "os": os,
}


