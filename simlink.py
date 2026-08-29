"""simlink.py - collegamento diretto al SIMULATORE di Sysmac Studio.

Parla con il simulatore NJ/NX tramite NexSocket.dll (fornita con Sysmac Studio,
cartella MATLAB\\Win64). Permette di LEGGERE e SCRIVERE le variabili per nome
mentre la simulazione gira, senza toccare la GUI: niente screenshot, niente
click destro -> Set/Reset.

Protocollo (testo, su socket 127.0.0.1:7000 gestito dalla DLL):
    GetVarAddrText   <rev> 1 VAR://<nome>          -> revisione + indirizzo,bit
    AsyncReadMemText <rev> 1 <indirizzo>,2         -> byte del valore
    AsyncWriteMemText<rev> 1 <indirizzo>,2,<hex>   -> scrive

Uso da riga di comando:
    python simlink.py ping
    python simlink.py read IN_MARCIA Sem1_Verde PV_Ph:REAL
    python simlink.py write IN_MARCIA=1 SET_PH:REAL=7.2
    python simlink.py watch 10 0.2 Sem1_Verde Sem1_Giallo Sem1_Rosso
    python simlink.py test scenario.json
"""

import ctypes
import json
import os
import re
import socket
import struct
import threading
import sys
import time

DLL_CANDIDATI = [
    r"C:\Program Files (x86)\OMRON\Sysmac Studio\MATLAB\Win64\NexSocket.dll",
    r"C:\Program Files\OMRON\Sysmac Studio\MATLAB\Win64\NexSocket.dll",
]


class SimError(RuntimeError):
    pass


# formati struct per tipo IEC
_FMT = {
    "SINT": "<b", "INT": "<h", "DINT": "<l", "LINT": "<q",
    "USINT": "<B", "UINT": "<H", "UDINT": "<L", "ULINT": "<Q",
    "BYTE": "<B", "WORD": "<H", "DWORD": "<L", "LWORD": "<Q",
    "REAL": "<f", "LREAL": "<d",
    "TIME": "<q", "LTIME": "<q", "DATE_AND_TIME": "<q", "DT": "<q",
}
# tipo di ripiego quando non e' dichiarato: dedotto dalla dimensione in bit
_PER_BIT = {1: "BOOL", 8: "SINT", 16: "INT", 32: "DINT", 64: "LINT"}


def connessioni_orfane(porta=7000):
    """Quante connessioni verso il simulatore appartengono a processi che non
    esistono piu'. Sono quelle che poi fanno bloccare le connessioni nuove."""
    import subprocess
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "$p=@{}; Get-Process -ErrorAction SilentlyContinue | "
             "ForEach-Object { $p[$_.Id]=1 }; "
             "(Get-NetTCPConnection -RemotePort %d -ErrorAction SilentlyContinue "
             "| Where-Object { -not $p.ContainsKey($_.OwningProcess) } "
             "| Measure-Object).Count" % porta],
            capture_output=True, text=True, timeout=25,
            stdin=subprocess.DEVNULL)
        return int((r.stdout or "0").strip() or 0)
    except Exception:
        return 0


def porta_aperta(ip="127.0.0.1", porta=7000, timeout=1.0):
    """True se il simulatore ha il socket in ascolto.

    Serve come PRE-CONTROLLO obbligatorio: se il simulatore non e' avviato,
    NexSockClient_connect NON ritorna un errore ma si BLOCCA, e con lui tutto
    il processo chiamante. Verificato piu' volte il 27/08/2026."""
    try:
        with socket.create_connection((ip, porta), timeout):
            return True
    except OSError:
        return False


def _trova_dll(path=None):
    if path:
        return path
    for p in DLL_CANDIDATI:
        if os.path.exists(p):
            return p
    raise SimError(
        "NexSocket.dll non trovata. Cercata in:\n  " + "\n  ".join(DLL_CANDIDATI)
    )


def split_tipo(nome):
    """'PV_Ph:REAL' -> ('PV_Ph', 'REAL');  'IN_MARCIA' -> ('IN_MARCIA', None)."""
    if ":" in nome:
        n, t = nome.rsplit(":", 1)
        return n.strip(), t.strip().upper()
    return nome.strip(), None


class Sim:
    """Sessione col simulatore. Usare come context manager."""

    def __init__(self, ip="127.0.0.1", port=7000, dll=None, progetto=None):
        self.ip = ip
        self.port = port
        self.dll_path = _trova_dll(dll)
        self.dll = None
        self.handle = ctypes.c_short()
        self.cache = {}          # nome -> dict(rev, addr, bit, tipo)
        self.tipi = {}           # nome -> tipo dichiarato dall'utente/tabella
        if progetto:
            self.carica_tipi_progetto(progetto)

    # ------------------------------------------------------------ sessione
    def connect(self, verifica_porta=True, attesa=10.0):
        """Apre la sessione col simulatore.

        Due protezioni, entrambe imparate sul campo:
        1) se la porta non e' in ascolto non si chiama nemmeno la DLL, perche'
           senza simulatore `NexSockClient_connect` si blocca per sempre;
        2) la chiamata alla DLL gira comunque in un thread con scadenza,
           perche' si blocca anche quando il simulatore c'e' ma ha connessioni
           orfane rimaste aperte da processi uccisi.
        """
        if verifica_porta and not porta_aperta(self.ip, self.port):
            raise SimError(
                "il simulatore non e' in ascolto su %s:%d. Avviare la "
                "simulazione in Sysmac Studio (Simulazione > Esegui, F5) e "
                "attendere ~40-60 s. NON si tenta la connessione: senza "
                "simulatore la DLL si blocca." % (self.ip, self.port))
        self.dll = ctypes.WinDLL(self.dll_path)
        esito = {}

        def _apri():
            try:
                self.dll.NexSock_initialize()
                esito["rc"] = self.dll.NexSockClient_connect(
                    ctypes.byref(self.handle),
                    self.ip.encode("utf-8"),
                    ctypes.c_int16(self.port))
            except BaseException as e:      # pragma: no cover
                esito["errore"] = e

        t = threading.Thread(target=_apri, daemon=True)
        t.start()
        t.join(attesa)
        if t.is_alive():
            self.dll = None
            orfane = connessioni_orfane(self.port)
            raise SimError(
                "la connessione al simulatore non risponde entro %.0f s. "
                "Di solito significa che restano connessioni aperte da "
                "processi terminati male%s. Rimedio: fermare e riavviare la "
                "simulazione in Sysmac (Shift+F5, poi F5)."
                % (attesa, " (%d orfane rilevate)" % orfane if orfane else ""))
        if "errore" in esito:
            self.dll = None
            raise SimError("errore aprendo la connessione: %s" % esito["errore"])
        if self.handle.value == 0 and esito.get("rc") != 0:
            raise SimError(
                "connessione al simulatore fallita (rc=%s). La simulazione e' "
                "avviata? (Sysmac: Simulazione > Esegui / F5)" % esito.get("rc"))
        return self

    def close(self):
        if self.dll is not None:
            try:
                self.dll.NexSock_close(self.handle.value)
                self.dll.NexSock_terminate()
            except Exception:
                pass
            self.dll = None

    def __enter__(self):
        return self.connect()

    def __exit__(self, *a):
        self.close()

    # ------------------------------------------------------------ protocollo
    def _cmd(self, comando, buf_size=4096):
        if self.dll is None:
            raise SimError("non connesso: chiamare connect()")
        risposte = []
        errori = []
        b = comando.encode("utf-8")
        self.dll.NexSock_send(self.handle, b, len(b))
        # ATTENZIONE: il messaggio finisce SOLO quando receive ritorna 0.
        # Un valore negativo e' un frame di errore DENTRO il messaggio: va
        # letto e poi si DEVE continuare a leggere, altrimenti il flusso si
        # desincronizza e le risposte arrivano sfasate di un comando.
        while True:
            buf = ctypes.create_string_buffer(buf_size)
            n = self.dll.NexSock_receive(self.handle, buf, buf_size)
            if n == 0:
                break
            if n < 0:
                errori.append(buf.value.decode("utf-8", "replace").strip())
                continue
            risposte.append(buf.raw[:n])
        if errori:
            raise SimError("simulatore: %s (comando: %s)"
                           % ("; ".join(errori), comando))
        return risposte

    def ping(self):
        """True se il simulatore risponde."""
        try:
            self._cmd("GetVarAddrText 1 VAR://P_On")
            return True
        except SimError:
            return False

    # ------------------------------------------------------------ modo CPU
    def modo(self):
        """Stato della CPU simulata, letto col comando GetMode.
        -> {"errore": "NoError", "modo": "RUN"|"PROGRAM", "stato": "Run"...}
        ATTENZIONE: il socket risponde anche a simulazione FERMA. Per sapere
        se il programma sta girando davvero bisogna guardare `modo`, non la
        semplice raggiungibilita' del socket."""
        r = self._cmd("GetMode")
        t = r[0].decode("utf-8", "replace") if r else ""
        out = {"grezzo": t.strip()}
        for k, chiave in (("ErrorState", "errore"), ("WorkMode", "modo"),
                          ("WorkState", "stato")):
            m = re.search(k + r":\s*([A-Za-z_]+)", t)
            if m:
                out[chiave] = m.group(1)
        return out

    def in_run(self):
        return self.modo().get("modo") == "RUN"

    def run(self):
        """Mette la CPU simulata in RUN (equivale a F5, ma immediato e senza
        GUI). Il comando accettato e' `Run`, che il simulatore converte
        internamente in `Mode mode=run`."""
        self._cmd("Run")
        return self.modo()

    def stop(self):
        """Riporta la CPU in PROGRAM (l'editor ladder torna modificabile)."""
        self._cmd("Stop")
        return self.modo()

    # ------------------------------------------------------------ variabili
    def info(self, nome):
        """Indirizzo/revisione/dimensione della variabile (con cache)."""
        nome, tipo = split_tipo(nome)
        if tipo:
            self.tipi[nome] = tipo
        if nome in self.cache:
            i = dict(self.cache[nome])
            i["tipo"] = self.tipi.get(nome, i["tipo"])
            return i
        r = self._cmd("GetVarAddrText 1 VAR://%s" % nome)
        if len(r) < 3:
            raise SimError(
                "variabile '%s' non trovata nel simulatore "
                "(dev'essere una variabile GLOBALE e la simulazione in RUN)" % nome
            )
        rev = r[0].decode("utf-8", "replace").strip()
        addr = r[2].decode("utf-8", "replace").strip()
        if addr.endswith("\x00") or addr.endswith(";"):
            addr = addr[:-1]
        try:
            bit = int(addr.split(",")[-1])
        except ValueError:
            raise SimError("indirizzo non interpretabile per '%s': %r" % (nome, addr))
        i = {
            "nome": nome,
            "rev": rev,
            "addr": addr,
            "bit": bit,
            "byte": max(1, bit // 8),
            "tipo": self.tipi.get(nome) or _PER_BIT.get(bit) or "BYTES",
        }
        self.cache[nome] = i
        return i

    def carica_tipi_progetto(self, nome_progetto):
        """Tipi esatti letti dalla tabella variabili globali del progetto su
        disco (nessuna GUI). Indispensabile perche' dal simulatore arriva solo
        la dimensione in bit: REAL e DINT sono entrambi 32 bit."""
        import simvars
        t = simvars.variabili_globali(nome_progetto)
        self.tipi.update({k: v.replace("ARRAY OF ", "") for k, v in t.items()})
        return len(t)

    def carica_tipi(self, path):
        """Legge la lista variabili esportata da Sysmac (Strumenti > Esporta
        variabili globali > CX-Designer, poi incollata in un file di testo):
        colonne separate da TAB/spazi: NOME  TIPO  ...  Salta l'intestazione."""
        n = 0
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for riga in f:
                t = riga.rstrip("\n").split("\t")
                if len(t) < 2:
                    t = riga.split()
                if len(t) < 2 or not t[0] or t[0].lower() in ("name", "nome"):
                    continue
                tipo = t[1].strip().upper()
                base = tipo.split("[")[0]
                if "[" in tipo:      # array: espande gli indici NOME[i]
                    try:
                        rng = tipo[tipo.index("[") + 1:tipo.index("]")]
                        rng = rng.replace("{", "").replace("}", "")
                        a, b = rng.split("..")
                        for k in range(int(a), int(b) + 1):
                            self.tipi["%s[%d]" % (t[0].strip(), k)] = base
                            n += 1
                        continue
                    except Exception:
                        pass
                self.tipi[t[0].strip()] = base
                n += 1
        return n

    # ------------------------------------------------------------ lettura
    def _decodifica(self, dati, tipo):
        if tipo == "BOOL":
            return bool(dati and dati[0])
        if tipo.startswith("STRING"):
            return dati.decode("utf-8", "replace").rstrip("\x00")
        fmt = _FMT.get(tipo)
        if fmt is None:
            return dati.hex()
        n = struct.calcsize(fmt)
        if len(dati) < n:
            dati = dati + b"\x00" * (n - len(dati))
        return struct.unpack(fmt, dati[:n])[0]

    @staticmethod
    def _durata_ns(v):
        """'T#2s' / 'T#1500ms' / 2.5 -> nanosecondi (il TIME di NJ/NX e' un
        intero a 64 bit in ns). Serve per scrivere i tempi di fase dal
        simulatore, senza chiudere il progetto per cambiare i valori iniziali."""
        if isinstance(v, (int, float)):
            return int(float(v) * 1e9)
        s = str(v).strip().upper().replace("T#", "")
        tot = 0.0
        for num, unita in re.findall(r"([\d.]+)\s*([A-Z]*)", s):
            if not num:
                continue
            val = float(num)
            u = unita or "S"
            if u.startswith("MS"):
                tot += val / 1000.0
            elif u.startswith("S"):
                tot += val
            elif u.startswith("M"):
                tot += val * 60
            elif u.startswith("H"):
                tot += val * 3600
            elif u.startswith("D"):
                tot += val * 86400
        return int(tot * 1e9)

    def _codifica(self, valore, tipo, nbyte):
        # il simulatore espone le variabili TIME come LINT a 64 bit: senza
        # questo, scrivere "T#20s" falliva con "could not convert string to
        # float" e i tempi restavano a zero (28/08/2026)
        if isinstance(valore, str) and valore.upper().startswith("T#"):
            return struct.pack("<q", self._durata_ns(valore))
        if tipo == "TIME":
            return struct.pack("<q", self._durata_ns(valore))
        if tipo == "BOOL":
            vero = valore if isinstance(valore, bool) else str(valore).strip().lower() \
                not in ("0", "false", "off", "no", "")
            return b"\x01" if vero else b"\x00"
        if tipo.startswith("STRING"):
            b = str(valore).encode("utf-8")
            return b + b"\x00" * max(0, nbyte - len(b))
        fmt = _FMT.get(tipo)
        if fmt is None:
            raise SimError("tipo '%s' non gestito in scrittura" % tipo)
        if fmt in ("<f", "<d"):
            return struct.pack(fmt, float(valore))
        return struct.pack(fmt, int(float(valore)))

    def read(self, nome):
        i = self.info(nome)
        r = self._cmd("AsyncReadMemText %s 1 %s,2" % (i["rev"], i["addr"]))
        if not r:
            raise SimError("nessuna risposta leggendo '%s'" % i["nome"])
        return self._decodifica(r[0], i["tipo"])

    def read_many(self, nomi):
        out = {}
        for n in nomi:
            base = split_tipo(n)[0]
            try:
                out[base] = self.read(n)
            except SimError as e:
                out[base] = "ERRORE: %s" % e
        return out

    def write(self, nome, valore):
        i = self.info(nome)
        dati = self._codifica(valore, i["tipo"], i["byte"])
        self._cmd("AsyncWriteMemText %s 1 %s,2,%s" % (i["rev"], i["addr"], dati.hex()))
        return True

    def write_many(self, assegnazioni):
        for n, v in assegnazioni.items():
            self.write(n, v)
        return True

    # ------------------------------------------------------------ debug
    def watch(self, nomi, secondi=5.0, intervallo=0.2, solo_cambi=True):
        """Campiona le variabili nel tempo. Ritorna la lista dei campioni
        [{'t': 0.42, 'valori': {...}}, ...]; con solo_cambi salva un campione
        solo quando qualcosa cambia (timeline compatta, pochi token)."""
        for n in nomi:
            self.info(n)
        campioni = []
        t0 = time.time()
        prec = None
        while True:
            t = time.time() - t0
            if t > secondi:
                break
            v = self.read_many(nomi)
            if (not solo_cambi) or v != prec:
                campioni.append({"t": round(t, 3), "valori": v})
                prec = v
            time.sleep(intervallo)
        v = self.read_many(nomi)
        if not campioni or campioni[-1]["valori"] != v:
            campioni.append({"t": round(time.time() - t0, 3), "valori": v})
        return campioni

    def esegui_scenario(self, scenario):
        """Esegue una sequenza di collaudo e ritorna un esito PASS/FAIL.

        scenario = {
          "nome": "...",
          "tipi": {"PV_Ph": "REAL"},              # opzionale
          "passi": [
            {"set": {"IN_MARCIA": 1}},
            {"attendi": 1.5},
            {"verifica": {"Sem1_Verde": true, "Sem1_Rosso": false},
             "tolleranza": 0.01,                  # opzionale, per REAL
             "descrizione": "fase 1"},
            {"watch": ["Sem1_Verde"], "secondi": 5, "intervallo": 0.2}
          ]
        }
        """
        self.tipi.update({k: str(v).upper() for k, v in scenario.get("tipi", {}).items()})
        esito = {"nome": scenario.get("nome", "scenario"), "passi": [],
                 "ok": True, "falliti": 0}
        # i tempi dichiarati nello scenario si applicano subito al PLC: cosi' lo
        # stesso file vale per il simulatore Python e per Sysmac. Senza questo,
        # un SET_T_ a zero manda in guasto tutto (28/08/2026, collaudo pompe).
        if scenario.get("tempi"):
            try:
                self.write_many(scenario["tempi"])
                esito["tempi_applicati"] = scenario["tempi"]
            except Exception as e:
                esito["tempi_applicati"] = "ERRORE: %s" % e
        t0 = time.time()
        for k, passo in enumerate(scenario.get("passi", []), 1):
            voce = {"n": k, "t": round(time.time() - t0, 3)}
            if "descrizione" in passo:
                voce["descrizione"] = passo["descrizione"]
            try:
                if "set" in passo:
                    self.write_many(passo["set"])
                    voce["set"] = passo["set"]
                if "attendi" in passo:
                    time.sleep(float(passo["attendi"]))
                    voce["attendi"] = passo["attendi"]
                if "impulso" in passo:
                    # pulsante: ON breve, poi OFF (chiamate pedonali, start...)
                    self.write_many({n: 1 for n in passo["impulso"]})
                    time.sleep(float(passo.get("durata_impulso", 0.4)))
                    self.write_many({n: 0 for n in passo["impulso"]})
                    voce["impulso"] = passo["impulso"]
                if "durata" in passo:
                    # misura quanto una variabile resta a un valore, agganciando
                    # il FRONTE: prima lo stato opposto, poi l'inizio. Misurare
                    # da uno stato gia' attivo da' risultati falsi (28/08/2026).
                    d = passo["durata"]
                    var = d["variabile"]
                    atteso = bool(d.get("valore", True))
                    tmax = float(d.get("tmax", 120))
                    t_in = time.time()
                    if not d.get("da_ora"):
                        while bool(self.read_many([var])[var]) == atteso and time.time() - t_in < tmax:
                            time.sleep(0.05)
                        while bool(self.read_many([var])[var]) != atteso and time.time() - t_in < tmax:
                            time.sleep(0.05)
                    t_start = time.time()
                    while bool(self.read_many([var])[var]) == atteso and time.time() - t_in < tmax:
                        time.sleep(0.05)
                    mis = round(time.time() - t_start, 3)
                    voce["misurata"] = mis
                    lo, hi = float(d.get("min", 0)), float(d.get("max", 1e9))
                    if not (lo <= mis <= hi):
                        voce["ESITO"] = "FAIL (attesa fra %s e %s)" % (lo, hi)
                        esito["ok"] = False
                        esito["falliti"] += 1
                    else:
                        voce["ESITO"] = "ok"
                if "watch" in passo:
                    voce["timeline"] = self.watch(
                        passo["watch"],
                        float(passo.get("secondi", 5)),
                        float(passo.get("intervallo", 0.2)),
                    )
                if "verifica" in passo:
                    toll = float(passo.get("tolleranza", 0))
                    letti = self.read_many(list(passo["verifica"].keys()))
                    diff = {}
                    for nome, atteso in passo["verifica"].items():
                        ott = letti.get(nome)
                        if isinstance(atteso, (int, float)) and \
                           isinstance(ott, float) and toll:
                            ok = abs(ott - float(atteso)) <= toll
                        elif isinstance(atteso, bool) or isinstance(ott, bool):
                            ok = bool(ott) == bool(atteso)
                        else:
                            ok = ott == atteso
                        if not ok:
                            diff[nome] = {"atteso": atteso, "ottenuto": ott}
                    voce["letti"] = letti
                    if diff:
                        voce["ESITO"] = "FAIL"
                        voce["differenze"] = diff
                        esito["ok"] = False
                        esito["falliti"] += 1
                    else:
                        voce["ESITO"] = "PASS"
            except Exception as e:
                voce["ESITO"] = "ERRORE"
                voce["errore"] = str(e)
                esito["ok"] = False
                esito["falliti"] += 1
            esito["passi"].append(voce)
        esito["durata_s"] = round(time.time() - t0, 2)
        return esito


# ---------------------------------------------------------------------- CLI
def _main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 1
    cmd = argv[1].lower()
    with Sim() as s:
        if cmd == "ping":
            ok = s.ping()
            print("simulatore RAGGIUNGIBILE" if ok else "simulatore NON raggiungibile")
            return 0 if ok else 2
        if cmd == "info":
            for n in argv[2:]:
                print(json.dumps(s.info(n), ensure_ascii=False))
            return 0
        if cmd == "read":
            print(json.dumps(s.read_many(argv[2:]), ensure_ascii=False, indent=1))
            return 0
        if cmd == "write":
            for a in argv[2:]:
                n, v = a.split("=", 1)
                s.write(n, v)
                print("%s <- %s" % (n, v))
            return 0
        if cmd == "watch":
            sec = float(argv[2]); iv = float(argv[3])
            for c in s.watch(argv[4:], sec, iv):
                print("%7.3f  %s" % (c["t"], json.dumps(c["valori"], ensure_ascii=False)))
            return 0
        if cmd == "test":
            with open(argv[2], "r", encoding="utf-8") as f:
                sc = json.load(f)
            r = s.esegui_scenario(sc)
            print(json.dumps(r, ensure_ascii=False, indent=1))
            return 0 if r["ok"] else 3
    print("comando sconosciuto: %s" % cmd)
    return 1


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
