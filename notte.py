# -*- coding: utf-8 -*-
"""
notte.py - esercitazione autonoma su Sysmac Studio.

Compone impianti sempre diversi pescando dal catalogo di moduli funzionali,
li collauda con il simulatore Python, poi fa il giro completo in Sysmac
Studio (crea progetto, scrive le variabili, importa il ladder, compila e -
ogni tanto - collauda sul simulatore vero) cronometrando ogni fase.

Serve a migliorare due cose insieme: la QUALITA' della logica, perche' ogni
impianto viene collaudato e i difetti finiscono nel diario, e la VELOCITA'
in interfaccia, perche' i tempi di ogni fase vengono misurati e confrontati.

Uso:
    python notte.py [ore] [--senza-gui]

Si ferma da solo dopo `ore` (default 8), oppure creando il file FERMATI.txt
nella cartella di lavoro. Scrive il diario in diario_notte.md.

ATTENZIONE: pilota mouse e tastiera reali. Mentre gira il PC non va usato.
"""
import datetime
import json
import os
import random
import shutil
import sys
import time
import traceback

BASE = r"C:\Users\tecni\Claude\sysmac-mcp"
LAVORO = r"C:\Users\tecni\Claude\esercizi_notte"
PROG = r"C:\OMRON\Data\Lib"
sys.path.insert(0, BASE)

import moduli                      # noqa: E402
import ladder_gen                  # noqa: E402
from sim_spec import SimSpec       # noqa: E402
import server as S                 # noqa: E402

DIARIO = os.path.join(LAVORO, "diario_notte.md")
MISURE = os.path.join(LAVORO, "misure.json")
STOP = os.path.join(LAVORO, "FERMATI.txt")


# --------------------------------------------------------------------- diario
def nota(testo=""):
    riga = testo if testo.startswith(("#", "|", "-", " ")) or not testo else testo
    with open(DIARIO, "a", encoding="utf-8") as f:
        f.write(riga + "\n")
    print(riga, flush=True)


def ora():
    return datetime.datetime.now().strftime("%H:%M:%S")


# ---------------------------------------------------------------- composizione
def componi(n_moduli, seme):
    """Sceglie n moduli a caso e li monta in un impianto con ossatura comune."""
    rnd = random.Random(seme)
    scelte = []
    for k in range(n_moduli):
        f = rnd.choice(moduli.CATALOGO)
        if f is moduli.sequenza:
            scelte.append(f(k + 1, rnd.choice([3, 4, 5, 6])))
        else:
            scelte.append(f(k + 1))

    G = [
        ("IN_Emergenza", "BOOL", "fungo di emergenza"),
        ("IN_Protezioni", "BOOL", "protezioni chiuse"),
        ("V_P_Reset", "BOOL", "reset allarmi"),
        ("V_L_Allarme", "BOOL", "spia allarme cumulativo"),
        ("V_L_Pronto", "BOOL", "spia macchina pronta"),
    ]
    I = [("Consensi", "BOOL", "consensi di sicurezza presenti")]
    sezioni = {"Sicurezze": [
        {"cmt": "CONSENSI DI SICUREZZA",
         "chain": ["/IN_Emergenza", "IN_Protezioni", "(Consensi)"]},
    ]}
    iniziale = {"IN_Emergenza": False, "IN_Protezioni": True}
    tempi = {}
    passi = []
    allarmi = []

    for m in scelte:
        G += m["globali"]
        I += m["interne"]
        sezioni[m["nome"].replace(" ", "_").replace("(", "").replace(")", "")] = m["rung"]
        iniziale.update(m.get("iniziale", {}))
        tempi.update(m.get("tempi", {}))
        passi += m["passi"]
        allarmi += m["allarmi"]

    finali = [
        {"cmt": "SPIA ALLARME CUMULATIVO",
         "chain": [{"or": (allarmi or ["/Consensi"]) + ["/Consensi"]},
                   "(V_L_Allarme)"]},
        {"cmt": "MACCHINA PRONTA",
         "chain": ["Consensi", "/V_L_Allarme", "(V_L_Pronto)"]},
    ]
    sezioni["Allarmi"] = finali

    # collaudo: stato iniziale, poi i passi dei moduli, poi l'emergenza
    scenario = {
        "nome": "esercizio con %d moduli" % n_moduli,
        "tempi": tempi,
        "passi": ([{"descrizione": "stato iniziale e reset",
                    "set": iniziale, "impulso": ["V_P_Reset"], "attendi": 0.6,
                    "verifica": {"V_L_Pronto": True, "V_L_Allarme": False}}] +
                  passi +
                  [{"descrizione": "EMERGENZA: la macchina non e' piu' pronta",
                    "set": {"IN_Emergenza": True}, "attendi": 0.5,
                    "verifica": {"V_L_Pronto": False, "V_L_Allarme": True}}]),
    }
    return G, I, sezioni, scenario, [m["nome"] for m in scelte]


# ------------------------------------------------------------------- collaudi
def collaudo_python(spec_path, scenario):
    s = SimSpec(spec_path, tempi=scenario.get("tempi", {}))
    return s.scenario(scenario)


def solo_globali(scenario, globali):
    """Copia dello scenario con le sole variabili che il simulatore espone."""
    nomi = set(g[0] for g in globali)
    sc = json.loads(json.dumps(scenario))
    for p in sc["passi"]:
        if "verifica" in p:
            p["verifica"] = {k: v for k, v in p["verifica"].items() if k in nomi}
    return sc


# ------------------------------------------------------------ fasi su Sysmac
def attendi(cond, secondi, passo=1.0):
    fine = time.time() + secondi
    while time.time() < fine:
        time.sleep(passo)
        try:
            if cond():
                return True
        except Exception:
            pass
    return False


def rispondi_salvataggio():
    """Se Sysmac chiede "Salvare il progetto prima di chiudere?" risponde No.

    E' il dialogo che manda in stallo qualunque automazione: compare come
    finestra figlia intitolata col NOME DEL PROGETTO, non "Sysmac Studio",
    quindi non lo si trova cercando per titolo fisso. Qui lo si riconosce dal
    testo e si preme No: il progetto e' gia' stato salvato prima, e un "Si'"
    aprirebbe il dialogo file su un progetto gestito come file.
    """
    try:
        albero = S.sysmac_ui_dump("", 12) or ""
    except Exception:
        return False
    if "prima di chiudere" not in albero:
        return False
    S._uia(
        "$r = [System.Windows.Automation.AutomationElement]::RootElement; "
        "$c = New-Object System.Windows.Automation.PropertyCondition("
        "[System.Windows.Automation.AutomationElement]::NameProperty, 'No'); "
        "$b = $r.FindFirst([System.Windows.Automation.TreeScope]::Descendants, $c); "
        "if ($b) { [void](Invoke-UiElement -Element $b); 'PREMUTO' } "
        "else { 'NON TROVATO' }")
    time.sleep(2)
    return True


def chiudi_progetto():
    try:
        S.sysmac_sim("stop")
    except Exception:
        pass
    time.sleep(4)
    # salvare PRIMA evita che la chiusura chieda conferma: su un progetto
    # gia' associato al suo file Ctrl+S salva senza aprire dialoghi
    try:
        S.sysmac_ui(azione="tasti", testo="^s")
        time.sleep(4)
    except Exception:
        pass
    try:
        S.sysmac_menu("File|Chiudi")
    except Exception:
        pass
    for _ in range(4):
        if attendi(lambda: not json.loads(S.sysmac_status())["progetto"], 12):
            return True
        if not rispondi_salvataggio():
            # nessun dialogo di salvataggio: forse il menu non e' partito
            try:
                S.sysmac_ui(azione="click", x=23, y=47)
                time.sleep(1.2)
                S.sysmac_ui(azione="click", x=48, y=78)
            except Exception:
                pass
    return not json.loads(S.sysmac_status())["progetto"]


def crea_progetto(nome, secondo_tentativo=False):
    """Crea un progetto nuovo. Se la pagina iniziale si e' incastrata - capita
    dopo un recupero - riavvia Sysmac e riprova una volta sola."""
    S.sysmac_ui(azione="focus")
    S.sysmac_ui(azione="massimizza")
    time.sleep(1)
    S.sysmac_ui(azione="click", x=127, y=151)
    riuscito = False
    for _ in range(15):
        time.sleep(1)
        try:
            S.sysmac_dialogo(campi="Nome progetto=%s; Autore=SYNTECH" % nome)
            riuscito = True
            break
        except Exception:
            pass
    if not riuscito:
        if secondo_tentativo:
            return False
        nota("      ... pagina iniziale bloccata: riavvio Sysmac")
        try:
            S.sysmac_ui(azione="riavvia")
        except Exception:
            pass
        time.sleep(15)
        return crea_progetto(nome, True)
    S.sysmac_ui(azione="pulsante", testo="Crea")
    return attendi(lambda: nome in S.sysmac_status(), 60)


def riapri_progetto(nome):
    """Riapre il progetto cercandolo PER NOME nell'elenco dei file recenti.

    La coordinata fissa sulla prima riga non va bene: l'ordine dell'elenco
    cambia a ogni apertura e si finiva per riaprire il progetto sbagliato o
    per non aprire niente.
    """
    S.sysmac_ui(azione="focus")
    S.sysmac_ui(azione="massimizza")
    time.sleep(1)
    S.sysmac_ui(azione="click", x=127, y=186)   # "Apri progetto"
    time.sleep(3)
    out = S._uia(
        "$w = Get-SysmacMainWindow; "
        "$c = New-Object System.Windows.Automation.PropertyCondition("
        "[System.Windows.Automation.AutomationElement]::NameProperty, %s); "
        "$e = $w.FindFirst([System.Windows.Automation.TreeScope]::Descendants, $c); "
        "if ($e) { $r = $e.Current.BoundingRectangle; "
        "'{0};{1}' -f [int]($r.X + $r.Width/2), [int]($r.Y + $r.Height/2) } "
        "else { 'NONTROVATO' }" % S._ps_quote(nome + ".smc2"))
    riga = [r for r in (out or "").splitlines() if r.count(";") == 1]
    if riga:
        x, y = [int(v) for v in riga[-1].split(";")]
        S._click(x, y, "left", True)
    else:
        S.sysmac_ui(azione="click", x=900, y=310, doppio=True)
    return attendi(lambda: json.loads(S.sysmac_status())["progetto"], 60)


def chiudi_dialoghi(giri=6):
    """Chiude i dialoghi aperti premendone i pulsanti.

    L'ESC da solo non basta: i messaggi di Sysmac ("Selezionare un file
    quando si utilizza Gestione in File di progetto") hanno il solo OK, e
    restano li' a bloccare tutto. Si premono, nell'ordine, No / OK / Annulla,
    ripetendo perche' i dialoghi sono impilati e si richiamano a vicenda:
    Annulla sul dialogo file -> "selezionare un file" -> OK -> "salvare prima
    di chiudere?" -> No -> chiuso.

    NON si preme mai "Salva": se il campo del nome e' rimasto vuoto quel
    pulsante non chiude niente e si gira a vuoto.
    """
    chiusi = 0
    for _ in range(giri):
        # Caso speciale: il dialogo di salvataggio su file. Annullarlo fa
        # ricomparire "selezionare un file" e si gira a vuoto; qui si scrive
        # un nome valido e si salva, che e' anche la cosa giusta da fare.
        try:
            if "Salva progetto" in (S.sysmac_ui_dump("", 3) or ""):
                dove = os.path.join(PROG, "SCARTO_%d.smc2" % int(time.time()))
                r = S.sysmac_save(file=dove)
                if "salvato" in r.lower():
                    chiusi += 1
                    time.sleep(1.5)
                    continue
        except Exception:
            pass
        premuto = S._uia(
            "$r = [System.Windows.Automation.AutomationElement]::RootElement; "
            "foreach ($n in @('No','OK','Annulla')) { "
            "$c = New-Object System.Windows.Automation.PropertyCondition("
            "[System.Windows.Automation.AutomationElement]::NameProperty, $n); "
            "$b = $r.FindFirst("
            "[System.Windows.Automation.TreeScope]::Descendants, $c); "
            "if ($b) { [void](Invoke-UiElement -Element $b); $n; break } }")
        if not (premuto or "").strip():
            break
        chiusi += 1
        time.sleep(1.5)
    return chiusi


def recupera():
    """Rimette Sysmac in uno stato noto: niente dialoghi, nessun progetto."""
    nota("      ... recupero: chiudo dialoghi e progetto")
    n = chiudi_dialoghi()
    if n:
        nota("      ... chiusi %d dialoghi" % n)
    try:
        S.sysmac_ui(azione="tasti", testo="{ESC}")
    except Exception:
        pass
    time.sleep(1)
    if not chiudi_progetto():
        try:
            S.sysmac_ui(azione="riavvia")
            time.sleep(12)
        except Exception:
            pass


# ------------------------------------------------------------------- esercizio
def esercizio(n, seme, con_simulatore):
    t = {}
    nome = "ES%03d" % n
    n_mod = random.Random(seme).choice([3, 4, 5, 6, 7, 8])
    t0 = time.time()
    G, I, sezioni, scenario, elenco = componi(n_mod, seme)
    n_rung = sum(len(v) for v in sezioni.values())
    t["genera"] = round(time.time() - t0, 2)

    spec = {"out_dir": os.path.join(BASE, "out"),
            "variables": [{"name": a, "type": b, "comment": c} for a, b, c in I],
            "sections": sezioni}
    sp = os.path.join(LAVORO, "%s_spec.json" % nome)
    json.dump(spec, open(sp, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    json.dump(scenario, open(os.path.join(LAVORO, "%s_scenario.json" % nome),
                             "w", encoding="utf-8"), indent=1, ensure_ascii=False)

    nota("")
    nota("### %s - %s - %d rung, %d globali, %d interne"
         % (nome, ora(), n_rung, len(G), len(I)))
    nota("moduli: " + ", ".join(elenco))

    # --- collaudo logico
    t0 = time.time()
    try:
        esito = collaudo_python(sp, scenario)
    except Exception as e:
        nota("- **il simulatore Python e' andato in errore**: `%s`" % str(e)[:200])
        return {"nome": nome, "rung": n_rung, "errore_sim": str(e)[:200]}
    t["collaudo_py"] = round(time.time() - t0, 2)
    falliti = [p for p in esito["passi"] if p.get("ESITO") == "FAIL"]
    t["py_passi"] = len(esito["passi"])
    t["py_falliti"] = len(falliti)
    if falliti:
        nota("- collaudo Python: **FAIL %d/%d** in %.2f s"
             % (len(falliti), len(esito["passi"]), t["collaudo_py"]))
        for p in falliti[:6]:
            nota("  - %s -> `%s`" % (p.get("descrizione", "")[:70],
                                     str(p.get("differenze"))[:110]))
    else:
        nota("- collaudo Python: PASS %d/%d in %.2f s"
             % (len(esito["passi"]), len(esito["passi"]), t["collaudo_py"]))

    # --- ladder
    t0 = time.time()
    unica = dict(spec)
    tutti = []
    for v in sezioni.values():
        tutti += v
    unica["sections"] = {"Prog": tutti}
    up = os.path.join(LAVORO, "%s_unica.json" % nome)
    json.dump(unica, open(up, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    ladder_gen.build_spec(up)
    xml = open(os.path.join(BASE, "out", "sec_Prog.xml"), encoding="utf-8").read()
    t["xml"] = round(time.time() - t0, 2)
    t["xml_kb"] = round(len(xml) / 1024)

    # --- Sysmac
    fase = "creazione"
    try:
        chiudi_dialoghi(3)          # si parte da uno schermo pulito
        t0 = time.time()
        if not crea_progetto(nome):
            raise RuntimeError("progetto non creato")
        t["crea"] = round(time.time() - t0, 1)

        fase = "salvataggio"
        t0 = time.time()
        smc = os.path.join(PROG, nome + ".smc2")
        if os.path.exists(smc):
            os.remove(smc)
        r = S.sysmac_save(file=smc)
        if "salvato" not in r.lower():
            raise RuntimeError("salvataggio: " + r[:120])
        t["salva"] = round(time.time() - t0, 1)

        fase = "chiusura"
        t0 = time.time()
        chiudi_progetto()
        t["chiudi"] = round(time.time() - t0, 1)

        fase = "variabili"
        t0 = time.time()
        S.sysmac_vars_offline(
            progetto=smc,
            globali="\n".join("%s\t%s\t%s" % g for g in G),
            interne="\n".join("%s\t%s\t%s" % g for g in I),
            esterne="\n".join(g[0] for g in G))
        t["variabili"] = round(time.time() - t0, 2)

        fase = "riapertura"
        t0 = time.time()
        if not riapri_progetto(nome):
            raise RuntimeError("progetto non riaperto")
        t["riapri"] = round(time.time() - t0, 1)

        fase = "apertura sezione"
        t0 = time.time()
        r = S.sysmac_apri_sezione()
        if "aperta" not in r.lower():
            # riserva: i clic a coordinate sui triangolini dell'albero.
            # Meno elegante della navigazione da tastiera, ma e' il metodo
            # gia' collaudato su decine di progetti e qui conta arrivare in
            # fondo senza sorveglianza.
            nota("      ... sezione: passo ai clic a coordinate")
            S.sysmac_ui(azione="focus")
            time.sleep(0.3)
            for (cx, cy) in [(19, 233), (54, 259), (84, 285), (97, 311)]:
                S.sysmac_ui(azione="click", x=cx, y=cy)
                time.sleep(0.9)
            S.sysmac_ui(azione="click", x=178, y=337, doppio=True)
            time.sleep(5)
            albero = S.sysmac_ui_dump("", 400) or ""
            if not [l for l in albero.splitlines()
                    if "Pane" in l and " - " in l and "Programma" in l]:
                raise RuntimeError("sezione non aperta: " + r[:100])
        t["sezione"] = round(time.time() - t0, 1)

        fase = "import"
        t0 = time.time()
        try:
            S.sysmac_import_ladder_xml(xml=xml, verifica=False)
        except Exception:
            pass
        S.sysmac_ui(azione="tasti", testo="^s")
        ok = attendi(lambda: S._conta_rung_progetto() > n_rung - 2, 240, 4)
        t["import"] = round(time.time() - t0, 1)
        if not ok:
            raise RuntimeError("i rung non sono comparsi nel progetto")

        fase = "compilazione"
        t0 = time.time()
        S.sysmac_ui(azione="tasti", testo="{F8}")
        time.sleep(8)
        attendi(lambda: "ERRORI=" in S.sysmac_errors(), 240, 6)
        err = S.sysmac_errors()
        t["compila"] = round(time.time() - t0, 1)
        t["errori"] = err.splitlines()[0] if err else "?"
        nota("- Sysmac: crea %.1f | salva %.1f | vars %.2f | riapri %.1f | "
             "sezione %.1f | import %.1f | compila %.1f  ->  **%s**"
             % (t["crea"], t["salva"], t["variabili"], t["riapri"],
                t["sezione"], t["import"], t["compila"], t["errori"]))
        t["ui_totale"] = round(sum(t[k] for k in
                                   ("crea", "salva", "chiudi", "variabili",
                                    "riapri", "sezione", "import", "compila")), 1)

        if "ERRORI=0" not in t["errori"]:
            nota("  - **la compilazione ha dato errori**: %s" % err[:300])

        # --- collaudo sul simulatore vero, ogni tanto
        if con_simulatore:
            fase = "collaudo simulatore"
            t0 = time.time()
            S.sysmac_ui(azione="tasti", testo="^s")
            time.sleep(3)
            import sysmac_api as api
            api.sim_avvia(attesa=180)
            sc = solo_globali(scenario, G)
            e2 = api.collauda(sc)
            t["sysmac_collaudo"] = round(time.time() - t0, 1)
            t["sysmac_falliti"] = e2["falliti"]
            if e2["ok"]:
                nota("- collaudo su Sysmac: **PASS %d/%d** in %.0f s"
                     % (len(e2["passi"]), len(e2["passi"]), t["sysmac_collaudo"]))
            else:
                nota("- collaudo su Sysmac: **FAIL %d/%d**"
                     % (e2["falliti"], len(e2["passi"])))
                for p in e2["passi"]:
                    if p.get("ESITO") == "FAIL":
                        nota("  - %s -> `%s`" % (p.get("descrizione", "")[:66],
                                                 str(p.get("differenze"))[:110]))
                        break
            api.sim_ferma()
            time.sleep(4)

        chiudi_progetto()
    except Exception as e:
        nota("- **interrotto durante %s**: `%s`" % (fase, str(e)[:180]))
        t["interrotto"] = fase
        recupera()

    t["nome"] = nome
    t["rung"] = n_rung
    t["moduli"] = elenco
    return t


# ----------------------------------------------------------------------- main
def main():
    ore = 8.0
    con_gui = True
    for a in sys.argv[1:]:
        if a == "--senza-gui":
            con_gui = False
        else:
            try:
                ore = float(a)
            except ValueError:
                pass

    os.makedirs(LAVORO, exist_ok=True)
    if os.path.exists(STOP):
        os.remove(STOP)

    # Un solo esercitatore per volta: due processi che pilotano insieme la
    # stessa finestra di Sysmac si rubano i clic a vicenda e non se ne
    # accorge nessuno. Il lock contiene il PID e viene ignorato se il
    # processo che l'ha scritto non esiste piu'.
    lock = os.path.join(LAVORO, "in_corso.pid")
    if os.path.exists(lock):
        try:
            vecchio = int(open(lock).read().strip())
            import subprocess
            vivo = subprocess.run(
                ["tasklist", "/FI", "PID eq %d" % vecchio],
                capture_output=True, text=True).stdout
            if str(vecchio) in vivo:
                print("Un'altra esercitazione e' gia' in corso (PID %d): esco."
                      % vecchio)
                return
        except Exception:
            pass
    with open(lock, "w") as f:
        f.write(str(os.getpid()))

    nota("")
    nota("# Esercitazione notturna - %s"
         % datetime.datetime.now().strftime("%d/%m/%Y %H:%M"))
    nota("")
    nota("Durata prevista: %.1f ore. Per fermarla basta creare il file "
         "`FERMATI.txt` in `%s`." % (ore, LAVORO))

    misure = []
    if os.path.exists(MISURE):
        try:
            misure = json.load(open(MISURE, encoding="utf-8"))
        except Exception:
            misure = []

    fine = time.time() + ore * 3600
    n = len(misure)
    ko_di_fila = 0
    while time.time() < fine and not os.path.exists(STOP):
        n += 1
        seme = int(time.time()) + n
        # il collaudo sul simulatore vero costa un paio di minuti: uno su tre
        con_sim = con_gui and (n % 3 == 0)
        try:
            t = esercizio(n, seme, con_sim) if con_gui else _solo_logica(n, seme)
        except Exception:
            nota("- **errore grave**: ```%s```" % traceback.format_exc(limit=4)[:600])
            recupera()
            t = {"nome": "ES%03d" % n, "errore": "grave"}

        # Se Sysmac si pianta e non si riprende, insistere per ore non serve:
        # meglio passare alla sola logica, che continua a produrre impianti
        # collaudati e a trovare difetti. Lo si scrive nel diario.
        if con_gui:
            if t.get("ui_totale"):
                ko_di_fila = 0
            else:
                ko_di_fila += 1
                if ko_di_fila >= 4:
                    nota("")
                    nota("> **Sysmac non risponde piu' da 4 esercizi: proseguo "
                         "con la sola parte logica.** Al mattino basta chiudere "
                         "e riaprire Sysmac Studio per rimetterlo in sesto.")
                    con_gui = False
        misure.append(t)
        json.dump(misure, open(MISURE, "w", encoding="utf-8"),
                  indent=1, ensure_ascii=False)
        _riepilogo(misure)

    try:
        os.remove(lock)
    except Exception:
        pass
    nota("")
    nota("## Fine: %d esercizi. %s" % (len(misure), ora()))
    _finale(misure)


def _finale(misure):
    """Riepilogo di fine notte: quanto si e' andati veloci e cosa e' fallito."""
    fatti = [m for m in misure if m.get("ui_totale")]
    nota("")
    nota("| | |")
    nota("|---|---|")
    nota("| esercizi tentati | %d |" % len(misure))
    nota("| arrivati in fondo | %d |" % len(fatti))
    if fatti:
        nota("| rung totali prodotti | %d |" % sum(m["rung"] for m in fatti))
        nota("| tempo medio di UI | %.0f s |"
             % (sum(m["ui_totale"] for m in fatti) / len(fatti)))
        nota("| rung medi per esercizio | %.0f |"
             % (sum(m["rung"] for m in fatti) / len(fatti)))
        primi = fatti[:max(1, len(fatti) // 3)]
        ultimi = fatti[-max(1, len(fatti) // 3):]
        nota("| media UI primo terzo | %.0f s |"
             % (sum(m["ui_totale"] for m in primi) / len(primi)))
        nota("| media UI ultimo terzo | %.0f s |"
             % (sum(m["ui_totale"] for m in ultimi) / len(ultimi)))
    ko = [m for m in misure if m.get("interrotto")]
    if ko:
        nota("")
        nota("### Fasi che si sono interrotte")
        conta = {}
        for m in ko:
            conta[m["interrotto"]] = conta.get(m["interrotto"], 0) + 1
        for f, n in sorted(conta.items(), key=lambda x: -x[1]):
            nota("- %s: %d volte" % (f, n))
    logici = [m for m in misure if m.get("py_falliti")]
    if logici:
        nota("")
        nota("### Esercizi con difetti logici trovati dal collaudo")
        for m in logici:
            nota("- %s (%d passi falliti): %s"
                 % (m["nome"], m["py_falliti"], ", ".join(m.get("moduli", []))))


def _solo_logica(n, seme):
    nome = "ES%03d" % n
    G, I, sezioni, scenario, elenco = componi(
        random.Random(seme).choice([3, 4, 5, 6, 7, 8]), seme)
    spec = {"out_dir": os.path.join(BASE, "out"),
            "variables": [{"name": a, "type": b, "comment": c} for a, b, c in I],
            "sections": sezioni}
    sp = os.path.join(LAVORO, "%s_spec.json" % nome)
    json.dump(spec, open(sp, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    t0 = time.time()
    esito = collaudo_python(sp, scenario)
    n_rung = sum(len(v) for v in sezioni.values())
    nota("### %s - %d rung - collaudo %s (%d/%d) in %.2f s"
         % (nome, n_rung, "PASS" if esito["ok"] else "FAIL",
            esito["falliti"], len(esito["passi"]), time.time() - t0))
    return {"nome": nome, "rung": n_rung, "py_falliti": esito["falliti"],
            "moduli": elenco}


def _riepilogo(misure):
    fatti = [m for m in misure if m.get("ui_totale")]
    if len(fatti) < 2:
        return
    ultimi = fatti[-5:]
    med = sum(m["ui_totale"] for m in ultimi) / len(ultimi)
    rung = sum(m["rung"] for m in ultimi) / len(ultimi)
    nota("  _(ultimi %d: %.0f s di UI per %.0f rung in media)_"
         % (len(ultimi), med, rung))


if __name__ == "__main__":
    main()
