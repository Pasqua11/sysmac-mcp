# /// script
# requires-python = ">=3.11"
# dependencies = ["mcp"]
# ///
"""
sysmac-ladder MCP server
Importa programmi ladder in Omron Sysmac Studio in pochi secondi, via clipboard
XML (formato proprietario "ladderSnippetXML") + automazione input (SendInput).

REQUISITO CRITICO: Sysmac Studio si auto-eleva ad amministratore, quindi il
processo che ospita questo server (l'app Claude desktop) DEVE girare anch'esso
come amministratore, altrimenti Windows scarta l'input iniettato.

Uso da riga di comando (test senza MCP):
  python server.py selftest
  python server.py import <file.xml>
"""
import base64
import ctypes
import os
import re
import subprocess
import sys
import tempfile
import time

from mcp.server.fastmcp import FastMCP, Image

mcp = FastMCP("sysmac-ladder")

user32 = ctypes.windll.user32

# ---------------------------------------------------------------- utilita

def _ps(script: str, sta: bool = False, timeout: int = 90) -> str:
    args = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass"]
    if sta:
        args.append("-STA")
    args += ["-Command", script]
    r = subprocess.run(args, capture_output=True, text=True,
                       timeout=timeout, errors="replace")
    if r.returncode != 0 and r.stderr:
        raise RuntimeError(f"PowerShell: {r.stderr.strip()[:400]}")
    return (r.stdout or "").strip()

def _ps_quote(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"

class _MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long), ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong), ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong), ("dwExtraInfo", ctypes.c_void_p)]

class _INPUT(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong), ("mi", _MOUSEINPUT)]

def _screen_wh():
    return user32.GetSystemMetrics(0) - 1, user32.GetSystemMetrics(1) - 1

def _mouse(dx: int, dy: int, flags: int) -> None:
    inp = _INPUT()
    inp.type = 0
    inp.mi = _MOUSEINPUT(dx, dy, 0, flags, 0, None)
    user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(_INPUT))

def _move(x: int, y: int) -> None:
    w, h = _screen_wh()
    _mouse(int(x * 65535 / w), int(y * 65535 / h), 0x8001)

def _click(x: int, y: int, button: str = "left", double: bool = False) -> None:
    down, up = (0x0002, 0x0004) if button == "left" else (0x0008, 0x0010)
    _move(x, y)
    time.sleep(0.12)
    for _ in range(2 if double else 1):
        _mouse(0, 0, down); time.sleep(0.05)
        _mouse(0, 0, up);   time.sleep(0.06)

def _sysmac_hwnd() -> int:
    out = _ps("(Get-Process SysmacStudio -ErrorAction SilentlyContinue | "
              "Where-Object { $_.MainWindowHandle -ne 0 } | "
              "Select-Object -First 1).MainWindowHandle")
    if not out or out.strip() in ("", "0"):
        # finestra nascosta: MainWindowHandle vale 0, ma la finestra esiste
        h = _hwnd_per_titolo("Sysmac Studio")
        if h:
            return h
        raise RuntimeError("Sysmac Studio non in esecuzione (o senza finestra). Avvialo e apri un progetto.")
    return int(out)

def _fg_same_process(h: int) -> bool:
    """True se la finestra in primo piano appartiene al processo di h
    (menu contestuali e dialoghi di Sysmac sono finestre separate)."""
    fg = user32.GetForegroundWindow()
    if fg == h:
        return True
    pid_h = ctypes.c_ulong(0)
    pid_fg = ctypes.c_ulong(0)
    user32.GetWindowThreadProcessId(h, ctypes.byref(pid_h))
    user32.GetWindowThreadProcessId(fg, ctypes.byref(pid_fg))
    return pid_h.value != 0 and pid_h.value == pid_fg.value

def _focus_sysmac() -> int:
    """Porta Sysmac Studio in primo piano e ne restituisce la finestra.

    Windows nega SetForegroundWindow ai processi che non hanno gia' il primo
    piano (con l'app Claude in evidenza fallisce sempre): si provano in
    cascata tre tecniche, dalla piu' educata alla piu' brutale."""
    h = _sysmac_hwnd()
    if not h:
        raise RuntimeError("Sysmac Studio non in esecuzione (o senza finestra). "
                           "Avvialo e apri un progetto.")
    SW_MINIMIZE, SW_RESTORE, SW_SHOW = 6, 9, 5
    if not _assicura_visibile(h):
        raise RuntimeError(
            "la finestra di Sysmac Studio e' nascosta e non torna a video. "
            "Riportarla in primo piano a mano (o riavviare Sysmac) e riprovare.")
    if user32.IsIconic(h):
        user32.ShowWindow(h, SW_RESTORE)
        time.sleep(0.4)

    def in_primo_piano():
        return user32.GetForegroundWindow() == h

    # 1) tentativo diretto
    user32.ShowWindow(h, SW_SHOW)
    user32.SetForegroundWindow(h)
    time.sleep(0.25)
    if in_primo_piano():
        return h

    # 2) aggancio alla coda di input di chi ha il primo piano
    try:
        avanti = user32.GetForegroundWindow()
        t_avanti = user32.GetWindowThreadProcessId(avanti, None)
        t_mio = ctypes.windll.kernel32.GetCurrentThreadId()
        t_suo = user32.GetWindowThreadProcessId(h, None)
        for t in {t_avanti, t_suo}:
            if t and t != t_mio:
                user32.AttachThreadInput(t_mio, t, True)
        user32.BringWindowToTop(h)
        user32.SetForegroundWindow(h)
        user32.SetActiveWindow(h)
        time.sleep(0.25)
        for t in {t_avanti, t_suo}:
            if t and t != t_mio:
                user32.AttachThreadInput(t_mio, t, False)
    except Exception:
        pass
    if in_primo_piano():
        return h

    # 3) riduci a icona e ripristina
    user32.ShowWindow(h, SW_MINIMIZE)
    time.sleep(0.35)
    user32.ShowWindow(h, SW_RESTORE)
    time.sleep(0.6)
    user32.SetForegroundWindow(h)
    time.sleep(0.25)
    if in_primo_piano():
        return h

    raise RuntimeError(
        "impossibile portare Sysmac in primo piano. Di solito c'e' una "
        "finestra che ruba il fuoco (notifica di Norton, dialogo di un'altra "
        "applicazione): chiuderla e riprovare.")


# ---------------------------------------------------------- finestra nascosta
# 28/08/2026: una finestra NASCOSTA (non minimizzata) faceva fallire in silenzio
# ogni azione: MainWindowHandle vale 0, il focus "riesce" su una finestra
# invisibile e i tasti finiscono nell'applicazione sbagliata. Sono stati persi
# 79 rung con l'import che rispondeva comunque "Incollato".

def _hwnd_per_titolo(parte: str, solo_visibili: bool = False) -> int:
    """hwnd della prima finestra il cui titolo contiene `parte`.

    A differenza di _find_window (che torna il rettangolo e salta le finestre
    non visibili) qui si considerano ANCHE le finestre nascoste: serve proprio
    a ritrovarle per rimetterle a video."""
    from ctypes import wintypes
    trovato = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    def _cb(hwnd, _):
        if trovato:
            return True
        n = user32.GetWindowTextLengthW(hwnd)
        if n:
            buf = ctypes.create_unicode_buffer(n + 1)
            user32.GetWindowTextW(hwnd, buf, n + 1)
            if parte.lower() in buf.value.lower():
                if not solo_visibili or user32.IsWindowVisible(hwnd):
                    trovato.append(hwnd)
        return True

    user32.EnumWindows(_cb, 0)
    return int(trovato[0]) if trovato else 0


def _assicura_visibile(h: int) -> bool:
    """Se la finestra e' nascosta la rimette a video. True se ora e' visibile."""
    if not h:
        return False
    if user32.IsWindowVisible(h):
        return True
    SW_RESTORE, SW_SHOW = 9, 5
    user32.ShowWindow(h, SW_RESTORE)
    time.sleep(0.5)
    user32.ShowWindow(h, SW_SHOW)
    time.sleep(0.5)
    return bool(user32.IsWindowVisible(h))


def _pid_sysmac() -> int:
    """PID del processo che possiede la finestra di Sysmac (niente PowerShell)."""
    try:
        h = _sysmac_hwnd()
    except Exception:
        return 0
    pid = ctypes.c_ulong(0)
    user32.GetWindowThreadProcessId(h, ctypes.byref(pid))
    return int(pid.value)


def _cartella_progetto_aperto() -> str:
    """Cartella di lavoro del progetto APERTO, riconosciuta dal file
    <pid>.applicationlock. Copre sia l'archivio (Solution) sia i progetti
    aperti da file .smc2 (ProjFileTmp).

    ATTENZIONE: restano lock ORFANI di sessioni chiuse male (28/08/2026: 9 su
    10, il piu' vecchio di febbraio 2025). Si accetta quindi SOLO il lock il cui
    nome corrisponde al PID del Sysmac attualmente in esecuzione."""
    pid = _pid_sysmac()
    if not pid:
        return ""
    atteso = "%d.applicationlock" % pid
    for radice in (r"C:\OMRON\Data\Solution", r"C:\OMRON\Data\ProjFileTmp"):
        if not os.path.isdir(radice):
            continue
        try:
            sotto = os.listdir(radice)
        except OSError:
            continue
        for d in sotto:
            p = os.path.join(radice, d)
            if not os.path.isdir(p):
                continue
            try:
                if atteso in os.listdir(p):
                    return p
            except OSError:
                continue
    return ""


def _conta_rung_progetto() -> int:
    """Somma dei rung di tutte le sezioni ladder del progetto aperto, letta dal
    DISCO. Le sezioni sono file con una riga JSON per rung (campo "CLs")."""
    cart = _cartella_progetto_aperto()
    if not cart:
        return -1
    tot = 0
    for f in os.listdir(cart):
        if not f.endswith(".xml"):
            continue
        p = os.path.join(cart, f)
        try:
            with open(p, encoding="utf-8-sig", errors="ignore") as fh:
                testa = fh.read(400)
                if '"CLs"' not in testa and '"CMT"' not in testa:
                    continue
                fh.seek(0)
                tot += sum(1 for r in fh if r.strip())
        except OSError:
            continue
    return tot



# ------------------------------------------------------------------ CapsLock
# 27/08/2026: col CapsLock acceso SendKeys ha scritto "fb_pOWER_tRASL" al posto
# di "FB_Power_Trasl" (manda tasti fisici, quindi il maiuscolo si inverte) e il
# blocco funzione e' stato creato col nome sbagliato. Ora si controlla prima.

_VK_CAPITAL = 0x14


def _capslock_attivo() -> bool:
    """True se il CapsLock e' inserito. Lettura via GetKeyState: istantanea,
    senza PowerShell, e concorde con [Windows.Forms.Control]::IsKeyLocked."""
    return bool(user32.GetKeyState(_VK_CAPITAL) & 1)


def _capslock_off() -> bool:
    """Spegne il CapsLock se acceso. True se ha dovuto agire."""
    if not _capslock_attivo():
        return False
    user32.keybd_event(_VK_CAPITAL, 0, 0, 0)   # KEYEVENTF_KEYDOWN
    user32.keybd_event(_VK_CAPITAL, 0, 2, 0)   # KEYEVENTF_KEYUP
    time.sleep(0.15)
    return not _capslock_attivo()


# caratteri che danno un significato speciale alla stringa in SendKeys:
# se ci sono, il testo e' una SEQUENZA DI COMANDO e va inviato come tale.
_SENDKEYS_SPECIALI = "{}^%+~()[]"


def _e_comando_sendkeys(testo: str) -> bool:
    """True se `testo` va inviato con SendKeys invece che dagli appunti.

    Sono comandi: le sequenze con caratteri speciali ("^s", "{ENTER}") e le
    scorciatoie di UNA lettera dell'editor ladder (c, d, o, f, r, t, i, w),
    che incollate non farebbero nulla."""
    if len(testo) <= 1:
        return True
    return any(c in _SENDKEYS_SPECIALI for c in testo)


def _send_keys(keys: str) -> None:
    # con il CapsLock acceso SendKeys inverte le maiuscole: si spegne prima,
    # ma solo quando la sequenza contiene davvero delle lettere
    if any(c.isalpha() for c in keys):
        _capslock_off()
    _ps("Add-Type -AssemblyName System.Windows.Forms; "
        f"[System.Windows.Forms.SendKeys]::SendWait({_ps_quote(keys)})")

# ------------------------------------------------------- UI Automation (UIA)
# I click a coordinate si rompono se la finestra si sposta, cambia zoom o
# risoluzione. Sysmac Studio e' WPF ed espone TUTTA la UI via UI Automation:
# leggere e pilotare per NOME e' molto piu' affidabile. La logica UIA sta nella
# libreria PowerShell sysmac_ui.ps1, riusabile anche fuori dall'MCP.

# Risoluzione portabile: prima accanto a questo file (repo), poi il percorso
# storico del PC fisso, infine la variabile d'ambiente SYSMAC_UI_PS1.
_UI_PS1 = os.environ.get("SYSMAC_UI_PS1") or ""
if not _UI_PS1 or not os.path.exists(_UI_PS1):
    _cand = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sysmac_ui.ps1")
    _UI_PS1 = _cand if os.path.exists(_cand) else r"C:\Users\tecni\Claude\sysmac_ui.ps1"

def _uia(script: str, timeout: int = 120) -> str:
    """Esegue uno snippet PowerShell con sysmac_ui.ps1 gia' caricato.

    Prima assicura che la finestra di Sysmac sia VISIBILE: la libreria
    PowerShell la cerca via MainWindowHandle, che per una finestra nascosta
    vale 0, e tutte le funzioni UIA (compilazione, errori, dialoghi, menu)
    risponderebbero "Sysmac in avvio: nessuna finestra"."""
    if not os.path.exists(_UI_PS1):
        raise RuntimeError(f"Libreria UIA mancante: {_UI_PS1}")
    try:
        _assicura_visibile(_sysmac_hwnd())
    except Exception:
        pass
    return _ps(". " + _ps_quote(_UI_PS1) + "; " + script, timeout=timeout)

def _set_ladder_clipboard(xml: str) -> None:
    tmp = os.path.join(tempfile.gettempdir(), "ladder_snippet.xml")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(xml)
    _ps("Add-Type -AssemblyName System.Windows.Forms; "
        f"$x = Get-Content -Path {_ps_quote(tmp)} -Raw; "
        "$d = New-Object System.Windows.Forms.DataObject; "
        "$d.SetData('ladderSnippetXML', $x); "
        "[System.Windows.Forms.Clipboard]::SetDataObject($d, $true)", sta=True)

def _get_ladder_clipboard() -> str:
    tmp = os.path.join(tempfile.gettempdir(), "ladder_out.xml")
    if os.path.exists(tmp):
        os.remove(tmp)
    _ps("Add-Type -AssemblyName System.Windows.Forms; "
        "$d = [System.Windows.Forms.Clipboard]::GetDataObject(); "
        "if ($d -and $d.GetDataPresent('ladderSnippetXML')) { "
        f"$d.GetData('ladderSnippetXML') | Set-Content -Path {_ps_quote(tmp)} -Encoding UTF8 }}",
        sta=True)
    if not os.path.exists(tmp):
        return ""
    with open(tmp, "r", encoding="utf-8-sig") as f:
        return f.read()

def _capture(x: int, y: int, w: int, h: int) -> bytes:
    tmp = os.path.join(tempfile.gettempdir(), "sysmac_cap.png")
    _ps("Add-Type -AssemblyName System.Drawing; "
        f"$b = New-Object System.Drawing.Bitmap {w}, {h}; "
        "$g = [System.Drawing.Graphics]::FromImage($b); "
        f"$g.CopyFromScreen({x}, {y}, 0, 0, (New-Object System.Drawing.Size {w}, {h})); "
        f"$b.Save({_ps_quote(tmp)}, [System.Drawing.Imaging.ImageFormat]::Png)")
    with open(tmp, "rb") as f:
        return f.read()

# ---------------------------------------------------------------- tool MCP

def _rect_sysmac():
    """(sinistra, alto, destra, basso) della finestra di Sysmac Studio."""
    from ctypes import wintypes
    h = _sysmac_hwnd()
    r = wintypes.RECT()
    user32.GetWindowRect(h, ctypes.byref(r))
    return r.left, r.top, r.right, r.bottom


class _WINDOWPLACEMENT(ctypes.Structure):
    _fields_ = [("length", ctypes.c_uint), ("flags", ctypes.c_uint),
                ("showCmd", ctypes.c_uint),
                ("ptMinX", ctypes.c_long), ("ptMinY", ctypes.c_long),
                ("ptMaxX", ctypes.c_long), ("ptMaxY", ctypes.c_long),
                ("rcLeft", ctypes.c_long), ("rcTop", ctypes.c_long),
                ("rcRight", ctypes.c_long), ("rcBottom", ctypes.c_long)]


def _stato_finestra(h: int) -> int:
    """showCmd della finestra: 1 = normale, 2 = minimizzata, 3 = massimizzata."""
    wp = _WINDOWPLACEMENT()
    wp.length = ctypes.sizeof(_WINDOWPLACEMENT)
    if not user32.GetWindowPlacement(h, ctypes.byref(wp)):
        return 0
    return int(wp.showCmd)


def _massimizza():
    """Porta Sysmac a schermo intero: e' la condizione in cui sono state
    misurate tutte le coordinate note. Ritorna True se ha dovuto agire.

    Lo stato si legge da GetWindowPlacement, non dalle dimensioni: dopo un
    ciclo nascondi/ripristina la finestra puo' essere in stato NORMALE ma piu'
    grande dello schermo (0, 90, 1938, 1128), e il vecchio test sulle misure la
    dava per massimizzata lasciando tutte le coordinate sfalsate di 90 px."""
    SW_MAXIMIZE = 3
    h = _sysmac_hwnd()
    if _stato_finestra(h) == SW_MAXIMIZE:
        return False
    user32.ShowWindow(h, SW_MAXIMIZE)
    time.sleep(0.8)
    return True


def _incolla(testo: str) -> None:
    """Immette un testo tramite gli APPUNTI invece che con SendKeys.

    SendKeys non e' affidabile su stringhe lunghe con maiuscole e backslash:
    il 27/08/2026 un percorso e' stato digitato con tutte le maiuscole
    invertite e l'inizio troncato ("...cOMMESSA_mOVIMENTAZIONE.SMC2").
    Con gli appunti il testo arriva esatto."""
    _ps("Set-Clipboard -Value " + _ps_quote(testo), sta=True)
    _send_keys("^v")
    time.sleep(0.3)


def _clickf(x: int, y: int, button: str = "left", double: bool = False,
            massimizza: bool = True):
    """Click in coordinate RELATIVE alla finestra di Sysmac.

    Da usare per tutte le coordinate note: sono valide a finestra massimizzata,
    quindi per difetto la finestra viene prima massimizzata; l'offset viene
    comunque sommato, cosi' funziona anche se la massimizzazione non riesce.
    """
    _focus_sysmac()
    if massimizza and _massimizza():
        # la finestra e' appena passata a schermo intero: Sysmac ridisegna il
        # layout interno con un attimo di ritardo e un click troppo pronto cade
        # sulla riga sbagliata (28/08/2026: "Crea nuovo" non disponibile)
        time.sleep(1.2)
    l, t, _r, _b = _rect_sysmac()
    # A finestra massimizzata l'origine e' (-9, -9) (bordi invisibili di
    # Windows 11) e le coordinate note, misurate sullo schermo, vanno usate
    # tali e quali: sommare un offset negativo sposta il click di 9 px e su un
    # numero di rung basta a mancarlo (il Ctrl+V poi non incolla nulla).
    _click(x + max(l, 0), y + max(t, 0), button, double)


@mcp.tool(annotations={"readOnlyHint": True})
def sysmac_status() -> str:
    """Stato complessivo: processo Sysmac Studio, progetto aperto, e se il
    SIMULATORE e' acceso e in RUN. Da chiamare per primo quando non si sa in
    che stato e' la macchina."""
    import json
    out = _ps("Get-Process SysmacStudio -ErrorAction SilentlyContinue | "
              "ForEach-Object { \"pid=$($_.Id) title='$($_.MainWindowTitle)'\" }")
    riga = (out or "").strip() or "Sysmac Studio NON in esecuzione"
    info = {"sysmac": riga, "progetto": _progetto_aperto()}
    try:
        d = os.path.dirname(os.path.abspath(__file__))
        if d not in sys.path:
            sys.path.insert(0, d)
        import simlink
        if not simlink.porta_aperta():
            info["simulatore"] = "spento (nessun socket su 127.0.0.1:7000)"
        else:
            c = simlink.Sim().connect()
            try:
                info["simulatore"] = "acceso, CPU in %s" % c.modo().get("modo", "?")
            finally:
                c.close()
    except Exception as e:
        info["simulatore"] = "non determinabile: %s" % e
    return json.dumps(info, ensure_ascii=False)

@mcp.tool()
def sysmac_import_ladder_xml(xml: str, rung_row_y: int = 210,
                             verifica: bool = True) -> str:
    """Importa uno o piu rung ladder in Sysmac Studio: mette l'XML (formato
    ladderSnippetXML, radice <Rungs>) negli appunti, porta Sysmac in primo
    piano, seleziona il rung alla riga video rung_row_y (default 210 = rung 0)
    e incolla con Ctrl+V. Il rung incollato viene inserito SOTTO quello
    selezionato. Richiede editor ladder aperto e simulazione FERMA.

    Con verifica=True (predefinito) SALVA e conta i rung del progetto prima e
    dopo: se non sono aumentati solleva un errore invece di dire "Incollato".
    Serve perche' un Ctrl+V su una finestra nascosta o senza rung selezionato
    non incolla nulla e prima passava inosservato."""
    if "<Rungs>" not in xml:
        raise ValueError("XML non valido: atteso formato ladderSnippetXML con radice <Rungs>.")
    attesi = xml.count("<RungXML")
    prima = -1
    if verifica:
        _focus_sysmac()
        _send_keys("^s")
        time.sleep(1.5)
        prima = _conta_rung_progetto()

    _set_ladder_clipboard(xml)
    _clickf(317, rung_row_y)
    time.sleep(0.4)
    _send_keys("^v")
    time.sleep(1.5)

    # se l'editor era ancora in disegno il primo Ctrl+V non prende: si ritenta
    # una volta prima di dichiarare fallito (28/08/2026: 16 s persi cosi')
    if verifica and prima >= 0:
        _send_keys("^s")
        time.sleep(1.5)
        if _conta_rung_progetto() <= prima:
            time.sleep(1.5)
            _clickf(317, rung_row_y)
            time.sleep(0.6)
            _send_keys("^v")
            time.sleep(1.8)

    if not verifica or prima < 0:
        return ("Incollato (senza verifica). Registrare le eventuali variabili "
                "nuove e compilare con sysmac_compile_text.")
    _send_keys("^s")
    time.sleep(2.0)
    dopo = _conta_rung_progetto()
    delta = dopo - prima
    if delta <= 0:
        raise RuntimeError(
            "IMPORT NON RIUSCITO: i rung del progetto non sono aumentati "
            "(%d prima, %d dopo, attesi +%d). Cause tipiche: nessun rung "
            "selezionato alla riga %d, editor ladder non aperto, simulazione in "
            "RUN, oppure il Ctrl+V e' finito in un'altra applicazione."
            % (prima, dopo, attesi, rung_row_y))
    return ("Incollati %d rung (attesi %d; totale progetto %d -> %d). "
            "Ora registrare le eventuali variabili nuove e compilare."
            % (delta, attesi, prima, dopo))
@mcp.tool()
def sysmac_apri_sezione(sezione: str = "", programma: str = "") -> str:
    """Apre una SEZIONE ladder nell'editor senza clic a coordinate fisse.

    L'Explorer multivista non e' un albero WPF ma un TreeView Win32 dentro un
    WindowsFormsHost: UI Automation non ne pubblica i nodi e cercarli come
    TreeItem non trova niente. Si pilota da tastiera sfruttando il fatto che
    la FRECCIA DESTRA apre il nodo chiuso e, se e' gia' aperto, scende al
    primo figlio: ripetendola si arriva alla prima foglia del ramo, cioe'
    Programmazione > POUs > Programmi > <primo programma> > <prima sezione>.

    L'unica coordinata e' il centro del pannello, letto da UIA: segue il
    pannello se viene spostato o ridimensionato.

    sezione   nome atteso della sezione; vuoto = apre la prima e basta.
              Se il nome non corrisponde, scende di una riga e riprova.
    programma nome del POU, usato solo nel messaggio finale.
    """
    _focus_sysmac()
    out = _uia(
        "$w = Get-SysmacMainWindow; "
        "$c = New-Object System.Windows.Automation.PropertyCondition("
        "[System.Windows.Automation.AutomationElement]::ClassNameProperty, "
        "'WindowsFormsHost'); "
        "$h = $w.FindFirst([System.Windows.Automation.TreeScope]::Descendants, $c); "
        "if ($h) { $r = $h.Current.BoundingRectangle; "
        "'{0};{1};{2};{3}' -f [int]$r.X, [int]$r.Y, [int]$r.Width, [int]$r.Height } "
        "else { 'NOHOST' }")
    riga = [r for r in (out or "").splitlines() if r.count(";") == 3]
    if not riga:
        return ("FALLITO: pannello Explorer multivista non trovato - il "
                "progetto e' aperto? %s" % (out or "").strip()[:150])
    x, y, w, h = [int(v) for v in riga[-1].split(";")]

    def _schede():
        alb = sysmac_ui_dump("", 400) or ""
        return [r.split("|")[-1].strip() for r in alb.splitlines()
                if "Pane" in r and " - " in r]

    prima = set(_schede())
    # fuoco sull'albero, poi: in cima, chiudi il primo ramo, scendi su
    # Programmazione e vai giu' fino alla prima foglia. Tutto in una sola
    # sequenza: ogni chiamata separata costerebbe un avvio di PowerShell.
    _click(x + min(w // 2, 120), y + 14)
    time.sleep(0.5)
    _send_keys("{HOME}{LEFT}{DOWN}")
    time.sleep(0.9)
    # A gruppi di tre: mandati tutti insieme, il TreeView ne perde qualcuno
    # mentre sta espandendo i nodi e la selezione finisce altrove.
    for _ in range(4):
        _send_keys("{RIGHT 3}")
        time.sleep(0.6)
    time.sleep(1.2)
    _send_keys("{ENTER}")

    for tentativo in range(12):
        for _ in range(6):
            time.sleep(0.8)
            nuove = [t for t in _schede() if t not in prima]
            if nuove:
                break
        else:
            nuove = []
        if nuove:
            aperta = nuove[-1]
            if not sezione or sezione.lower() in aperta.lower():
                return "Sezione aperta: %s" % aperta
            prima.add(aperta)
        # nome diverso da quello chiesto: scendo di una riga e riprovo.
        # A meta' dei tentativi si riparte dalla cima dell'albero: se la
        # discesa si era persa, insistere con DOWN non porta da nessuna parte.
        if tentativo == 5:
            _send_keys("{HOME}{LEFT}{DOWN}")
            time.sleep(0.9)
            for _ in range(4):
                _send_keys("{RIGHT 3}")
                time.sleep(0.6)
            _send_keys("{ENTER}")
        else:
            _send_keys("{DOWN}{ENTER}")

    return ("FALLITO: non ho aperto una scheda di nome %r. Verificare il nome "
            "esatto della sezione nell'Explorer." % sezione)


def _scrivi_appunti(testo: str) -> None:
    """Mette il testo negli appunti e lo incolla con Ctrl+V.

    Per il codice ST e' l'unica strada sensata: SendKeys interpreta le
    parentesi, il piu' e le graffe come comandi, e un programma di cento
    righe battuto tasto per tasto ci metterebbe minuti."""
    _ps("Add-Type -AssemblyName System.Windows.Forms; "
        "[System.Windows.Forms.Clipboard]::SetText(%s)" % _ps_quote(testo))
    time.sleep(0.4)
    _send_keys("^v")



@mcp.tool()
def sysmac_st_nuovo(codice: str = "", nome: str = "") -> str:
    """Crea un POU in STRUCTURED TEXT sotto Programmi e ci scrive il codice.

    Meta' del codice dei progetti SYNTECH e' in ST, e l'ST e' molto piu'
    semplice del ladder da produrre: e' testo, non XML con celle e coordinate.
    Incollarlo costa 3-4 secondi contro i 14 dell'import ladder.

    codice  il testo ST da scrivere (vuoto = crea il POU e basta)
    nome    nome da dare al POU; vuoto = lascia quello proposto da Sysmac

    Richiede il progetto aperto. Il POU viene creato in coda a Programmi.
    """
    _focus_sysmac()
    time.sleep(0.4)

    # l'albero va espanso fino a "Programmi": i nodi sono di un TreeView Win32
    # che UIA non espone, quindi si usano i triangolini a coordinate note
    for cx, cy in ((19, 233), (54, 259), (84, 285)):
        _clickf(cx, cy)
        time.sleep(0.9)
    _clickf(140, 285)                 # seleziona "Programmi"
    time.sleep(0.7)
    _clickf(140, 285, "right")        # menu contestuale
    time.sleep(1.8)
    # da qui in poi solo tastiera: il popup e' una finestra a se' e un clic
    # che porti Sysmac in primo piano lo farebbe sparire
    _send_keys("{DOWN}")              # "Aggiungi"
    time.sleep(0.6)
    _send_keys("{RIGHT}")             # apre il sottomenu Ladder / ST
    time.sleep(1.2)
    _send_keys("{DOWN}")              # da Ladder a ST
    time.sleep(0.5)
    _send_keys("{ENTER}")
    time.sleep(3.5)

    if nome:
        _send_keys("{F2}")
        time.sleep(0.8)
        _send_keys("^a")
        _scrivi_appunti(nome)
        time.sleep(0.5)
        _send_keys("{ENTER}")
        time.sleep(1.5)

    # apre il POU appena creato: e' l'ultima riga sotto Programmi
    albero_prima = sysmac_ui_dump("", 400) or ""
    for y in (337, 363, 389, 415):
        _clickf(178, y, "left", True)
        time.sleep(2.5)
        dump = sysmac_ui_dump("", 400) or ""
        aperte = [r for r in dump.splitlines()
                  if "Pane" in r and "Programma" in r and "Sezione" not in r]
        if aperte and dump != albero_prima:
            break
    else:
        return "FALLITO: POU creato ma non sono riuscito ad aprirlo."

    if codice:
        return sysmac_st_scrivi(codice)
    return "POU in ST creato e aperto."


@mcp.tool()
def sysmac_st_scrivi(codice: str) -> str:
    """Scrive il codice nel POU in Structured Text gia' aperto nell'editor.

    Sostituisce tutto il contenuto (Ctrl+A) e incolla dagli appunti. Verifica
    poi che il testo sia davvero finito nell'editor confrontando la prima riga
    non vuota."""
    _focus_sysmac()
    time.sleep(0.3)
    _clickf(700, 300)                 # cursore dentro l'area di testo
    time.sleep(0.6)
    _send_keys("^a")
    time.sleep(0.3)
    _scrivi_appunti(codice)
    time.sleep(1.5)
    prima = ""
    for riga in codice.splitlines():
        if riga.strip():
            prima = riga.strip()[:30]
            break
    dump = sysmac_ui_dump("", 600) or ""
    if prima and prima not in dump:
        return ("Codice incollato (%d righe), ma non ho potuto verificarlo "
                "nell'albero: controllare l'editor." % len(codice.splitlines()))
    return "Codice ST scritto: %d righe." % len(codice.splitlines())


@mcp.tool()
def sysmac_save(file: str = "") -> str:
    """Salva il progetto (Ctrl+S).

    Sui progetti gestiti COME FILE (creati con "Gestisci nel file di progetto")
    Ctrl+S apre il dialogo "Salva progetto" invece di salvare, e finora il tool
    rispondeva "salvato" mentre il dialogo restava aperto. Ora il dialogo viene
    riconosciuto: con `file` valorizzato ci si scrive il percorso e si conferma,
    altrimenti si annulla e si segnala che il percorso serve."""
    _focus_sysmac()
    _send_keys("^s")
    # Il dialogo puo' metterci qualche secondo ad aprirsi: su un progetto da
    # 700 rung ne ha impiegati 4-5. Con l'attesa fissa di 2,5 s il tool
    # rispondeva "salvato" mentre non aveva salvato niente.
    albero = ""
    for _ in range(12):
        time.sleep(1)
        albero = sysmac_ui_dump("", 4) or ""
        if "Salva progetto" in albero:
            break
    if "Salva progetto" not in albero:
        return "Salvataggio inviato (Ctrl+S)."
    if not file:
        _send_keys("{ESC}")
        return ("ATTENZIONE: il progetto e' gestito come FILE e Ctrl+S ha aperto "
                "il dialogo 'Salva progetto' (nulla e' stato salvato). "
                "Richiamare sysmac_save(file=r'...\\nome.smc2').")
    # Il campo "Nome file" e' un Pane con ClassName 'Edit' e AutomationId
    # '1001', senza ValuePattern: si trova solo cosi'. Di lui prendo il
    # rettangolo (niente coordinate fisse) e ci scrivo dentro da tastiera.
    out = _uia(
        "$w = Get-SysmacDialog 'Salva progetto'; "
        "$c1 = New-Object System.Windows.Automation.PropertyCondition("
        "[System.Windows.Automation.AutomationElement]::AutomationIdProperty, '1001'); "
        "$c2 = New-Object System.Windows.Automation.PropertyCondition("
        "[System.Windows.Automation.AutomationElement]::ClassNameProperty, 'Edit'); "
        "$and = New-Object System.Windows.Automation.AndCondition($c1, $c2); "
        "$e = $w.FindFirst([System.Windows.Automation.TreeScope]::Descendants, $and); "
        "if ($e) { $r = $e.Current.BoundingRectangle; "
        "'{0};{1};{2};{3}' -f [int]$r.X, [int]$r.Y, [int]$r.Width, [int]$r.Height } "
        "else { 'NOCAMPO' }")
    riga = [r for r in (out or "").splitlines() if r.count(";") == 3]
    if not riga:
        _send_keys("{ESC}")
        return ("FALLITO: campo 'Nome file' non trovato nel dialogo. %s"
                % (out or "").strip()[:150])
    cx, cy, cw, ch = [int(v) for v in riga[-1].split(";")]
    _click(cx + cw // 2, cy + ch // 2)
    time.sleep(0.5)
    _send_keys("^a")
    time.sleep(0.3)
    _send_keys(file)
    time.sleep(0.8)
    _send_keys("{ENTER}")
    for _ in range(40):
        time.sleep(1)
        if "Salva progetto" not in (sysmac_ui_dump("", 3) or ""):
            if os.path.exists(file):
                return "Progetto salvato in %s" % file
            return ("Dialogo chiuso ma il file %s non risulta creato: "
                    "controllare il percorso." % file)
    return "FALLITO: il dialogo 'Salva progetto' e' ancora aperto."

@mcp.tool()
def sysmac_sim(action: str) -> str:
    """Simulatore integrato: action='start' (F5, esegue) o 'stop' (Shift+F5,
    arresta). Con la simulazione attiva l'editor ladder e in sola lettura."""
    _focus_sysmac()
    if action == "start":
        _send_keys("{F5}")
    elif action == "stop":
        _send_keys("+{F5}")
    else:
        raise ValueError("action deve essere 'start' o 'stop'")
    time.sleep(5)
    return f"Simulazione: {action} inviato."

def sysmac_click(x: int, y: int, button: str = "left", double: bool = False,
                 assoluto: bool = False) -> str:
    """Clic in Sysmac Studio. Per difetto le coordinate sono RELATIVE alla
    finestra di Sysmac (e la finestra viene massimizzata prima): e' cosi' che
    sono state misurate tutte le coordinate note di menu, dialoghi ed editor.
    Con assoluto=True si usano invece le coordinate dello schermo."""
    if assoluto:
        _focus_sysmac()
        _click(x, y, button, double)
        return "Click %s a (%d,%d) [schermo]." % (button, x, y)
    _clickf(x, y, button, double)
    l, t, _r, _b = _rect_sysmac()
    return "Click %s a (%d,%d) della finestra = (%d,%d) sullo schermo." % (
        button, x, y, x + l, y + t)


@mcp.tool()
def sysmac_register_from_error(error_row_y: int = 815) -> str:
    """Registra la PRIMA variabile non registrata segnalata nel pannello
    'Compila': doppio click sulla riga di errore (salta e seleziona l'elemento),
    poi Ctrl+Alt+R + Invio (variabile interna). Piu affidabile dei click a
    coordinate. Flusso consigliato dopo un import: sysmac_compile -> se ci sono
    errori 'variabile non registrata', chiamare questo tool una volta per
    errore, ricompilando in mezzo."""
    _focus_sysmac()
    _click(462, error_row_y, double=True)
    time.sleep(1.2)
    _send_keys("^%r")
    time.sleep(1.0)
    _send_keys("{ENTER}")
    time.sleep(0.7)
    return "Registrazione inviata per l'elemento del primo errore. Ricompilare con sysmac_compile."
# -------------------------------------------------- tool MCP basati su UIA
# Questi tool NON usano coordinate: trovano gli elementi per nome tramite UI
# Automation. Preferirli sempre a sysmac_click quando esiste l'equivalente.

def sysmac_focus() -> str:
    """Porta Sysmac Studio in primo piano e conferma che ha ricevuto il focus.
    Da chiamare quando un invio tasti non ha avuto effetto: spesso il motivo e'
    che la finestra attiva era un'altra (app Claude, notifica, altro dialogo)."""
    h = _focus_sysmac()
    titolo = _ps("(Get-Process SysmacStudio -ErrorAction SilentlyContinue | "
                 "Where-Object { $_.MainWindowHandle -ne 0 } | "
                 "Select-Object -First 1).MainWindowTitle")
    return f"Sysmac in primo piano (hwnd={h}) - {titolo or 'senza titolo'}"

def sysmac_menu(path: str) -> str:
    """Apre una voce di menu per NOME invece che a coordinate.
    path = percorso separato da '/', es:
      'Strumenti/Personalizza tasti di scelta rapida...'
      'Progetto/Ricompila Controllore'
      'Simulazione/Esegui'
    Usa ExpandCollapsePattern + InvokePattern: non dipende da dove si trova la
    finestra ne' dal tema. Se la voce non esiste restituisce FALLITO: verificare
    il nome esatto con sysmac_ui_dump."""
    # il separatore documentato in sysmac_ui e' "|", quello storico "/":
    # accettarli entrambi evita un fallimento silenzioso
    voci = [p.strip() for p in re.split(r"[/|]", path) if p.strip()]
    if not voci:
        raise ValueError("path vuoto")
    lista = ",".join(_ps_quote(v) for v in voci)
    out = _uia(f"if (Invoke-SysmacMenu -Path {lista}) {{ 'OK' }} else {{ 'FALLITO' }}")
    if "OK" in out:
        return f"Menu aperto: {path}"
    return f"FALLITO: voce di menu non trovata o non attivabile ({path}). {out}".strip()

def sysmac_button(name: str, dialog: str = "") -> str:
    """Preme un pulsante per NOME (OK, Annulla, Applica, Assegna, Esporta...).
    dialog = titolo esatto della finestra di dialogo; vuoto = finestra principale.
    NB: filtra per ControlType Button. E' importante, perche' in alcune finestre
    esistono righe di griglia con lo stesso nome del pulsante (es. 'Annulla'):
    cercare solo per nome preme la riga sbagliata e non succede nulla."""
    root = f"Get-SysmacDialog {_ps_quote(dialog)}" if dialog else "Get-SysmacMainWindow"
    out = _uia(f"$r = {root}; "
               f"if (-not $r) {{ 'FINESTRA_NON_TROVATA' }} "
               f"elseif (Invoke-UiButton -Root $r -Name {_ps_quote(name)}) {{ 'PREMUTO' }} "
               f"else {{ 'NON_PREMUTO' }}")
    if "PREMUTO" in out and "NON_PREMUTO" not in out:
        return f"Premuto il pulsante '{name}'."
    if "FINESTRA_NON_TROVATA" in out:
        raise RuntimeError(f"Finestra '{dialog or 'principale'}' non trovata.")
    return f"Pulsante '{name}' non premuto (assente o disabilitato). {out}".strip()


@mcp.tool()
def sysmac_dialogo(titolo: str = "", campi: str = "", caselle: str = "",
                   tendine: str = "", pulsante: str = "",
                   riga: str = "") -> str:
    """Compila un dialogo di Sysmac per NOME, senza coordinate.

    titolo   titolo esatto del dialogo; vuoto = finestra principale
    campi    "Etichetta=valore" separati da ';'  (campi di testo)
    caselle  "Etichetta=on|off" separati da ';'  (caselle di spunta)
    tendine  "Etichetta=voce" separati da ';'    (menu a tendina)
    riga     testo della riga di tabella/lista da selezionare
    pulsante nome del pulsante da premere alla fine (OK, Salva, Annulla...)

    Esempio (Impostazione libreria, che prima costava una decina di click):
      sysmac_dialogo(titolo="Impostazione libreria",
                     campi="Nome=SYNTECH_FB_Cappa; Societa=SYNTECH",
                     caselle="Disattiva visualizzazione sorgente=off",
                     pulsante="OK")

    I campi di testo si trovano per ETICHETTA: nei dialoghi WPF di Sysmac
    l'Edit non ha un nome proprio, quindi si prende quello alla stessa altezza
    dell'etichetta e subito a destra."""

    def _coppie(t):
        fuori = []
        for pezzo in (t or "").split(";"):
            pezzo = pezzo.strip()
            if not pezzo:
                continue
            if "=" not in pezzo:
                raise ValueError("atteso 'Etichetta=valore', trovato: %r" % pezzo)
            k, v = pezzo.split("=", 1)
            fuori.append((k.strip(), v.strip()))
        return fuori

    root = f"Get-SysmacDialog {_ps_quote(titolo)}" if titolo else "Get-SysmacMainWindow"
    righe = [f"$r = {root}",
             "if (-not $r) { 'FINESTRA_NON_TROVATA'; exit }"]
    esiti = []
    # NB: negli esiti si usa un INDICE, non il nome: un apostrofo nell'etichetta
    # (es. "Notificare se l'ID libreria...") romperebbe la stringa PowerShell.
    n = 0
    for k, v in _coppie(campi):
        n += 1
        righe.append(f"if (Set-UiValue -Root $r -Name {_ps_quote(k)} -Value {_ps_quote(v)}) "
                     f"{{ 'OK {n}' }} else {{ 'KO {n}' }}")
        esiti.append((n, "campo " + k))
    for k, v in _coppie(caselle):
        n += 1
        on = "$true" if v.lower() in ("on", "si", "true", "1", "x") else "$false"
        righe.append(f"if (Set-UiToggle -Root $r -Name {_ps_quote(k)} -On {on}) "
                     f"{{ 'OK {n}' }} else {{ 'KO {n}' }}")
        esiti.append((n, "casella " + k))
    for k, v in _coppie(tendine):
        n += 1
        righe.append(f"if (Select-UiComboItem -Root $r -Name {_ps_quote(k)} -Item {_ps_quote(v)}) "
                     f"{{ 'OK {n}' }} else {{ 'KO {n}' }}")
        esiti.append((n, "tendina " + k))
    if riga:
        n += 1
        righe.append(f"if (Select-UiGridRow -Root $r -Text {_ps_quote(riga)}) "
                     f"{{ 'OK {n}' }} else {{ 'KO {n}' }}")
        esiti.append((n, "riga " + riga))
    if pulsante:
        n += 1
        righe.append(f"if (Invoke-UiButton -Root $r -Name {_ps_quote(pulsante)}) "
                     f"{{ 'OK {n}' }} else {{ 'KO {n}' }}")
        esiti.append((n, "pulsante " + pulsante))

    if len(righe) == 2:
        raise ValueError("niente da fare: indicare almeno campi, caselle, tendine, riga o pulsante.")

    out = _uia("; ".join(righe))
    if "FINESTRA_NON_TROVATA" in out:
        raise RuntimeError("dialogo %r non trovato." % (titolo or "finestra principale"))
    mappa = dict(esiti)
    ko = []
    for r in out.splitlines():
        r = r.strip()
        if r.startswith("KO"):
            try:
                ko.append(mappa[int(r.split()[1])])
            except Exception:
                ko.append(r)
    if ko:
        raise RuntimeError("dialogo %r, non riuscito: %s. Esito completo: %s"
                           % (titolo or "principale", "; ".join(ko), out.strip()))
    return ("dialogo %r: %s -> tutto riuscito."
            % (titolo or "principale", ", ".join(d for _i, d in esiti)))

def sysmac_ui_dump(title: str = "", max_items: int = 300) -> str:
    """Esplora una finestra di Sysmac elencando 'tipo | nome' dei suoi elementi.
    title = titolo del dialogo da ispezionare; vuoto = finestra principale.
    Serve per scoprire i nomi esatti da passare a sysmac_menu / sysmac_button
    prima di automatizzare una finestra mai vista."""
    root = f"Get-SysmacDialog {_ps_quote(title)}" if title else "Get-SysmacMainWindow"
    out = _uia(f"$r = {root}; if (-not $r) {{ 'FINESTRA_NON_TROVATA' }} "
               f"else {{ Get-UiDump -Root $r -Max {int(max_items)} }}")
    return out or "(nessun elemento)"

@mcp.tool(annotations={"readOnlyHint": True})
def sysmac_errors(max_rows: int = 30) -> str:
    """Legge il pannello 'Compila' come TESTO invece che come screenshot.
    Restituisce 'ERRORI=n AVVISI=m' e una riga per ciascun messaggio nel formato
    numero | descrizione (con il nome della variabile) | programma e sezione | riga.
    Scorre da solo la griglia, che e' virtualizzata: senza scorrimento UIA vedrebbe
    solo le prime righe disegnate (con 60 avvisi se ne leggevano 9).
    Se il pannello e' chiuso lo segnala: riaprirlo con Alt+6.
    Alzare max_rows per liste lunghe (default 30)."""
    return _uia(f"Get-SysmacBuildErrors -Max {int(max_rows)}") or "(nessun output)"

@mcp.tool()
def sysmac_compile_text(wait_seconds: int = 12) -> str:
    """Come sysmac_compile ma restituisce gli errori come TESTO invece che come
    immagine: compila con F8, attende, poi legge il pannello 'Compila'.
    Piu' economico e piu' preciso dello screenshot."""
    _focus_sysmac()
    _send_keys("{F8}")
    time.sleep(max(3, wait_seconds))
    return _uia(f"Get-SysmacBuildErrors -Max 30") or "(nessun output)"

# ------------------------------------- tool MCP di LETTURA DIRETTA da disco
# Sysmac tiene i progetti in C:\Omron\Data\Solution\<guid>\ come file di
# testo: le sezioni ladder sono JSON, un rung per riga. Leggerli e' immediato
# e non richiede ne' Sysmac aperto ne' screenshot: e' la via piu' veloce per
# capire cosa fa un programma. Dettagli in sysmac_project.py.

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sysmac_project as _prj

def sysmac_projects(filtro: str = "") -> str:
    """Elenca i progetti Sysmac presenti sul disco (piu' recenti prima), anche
    senza aprire Sysmac Studio. filtro = pezzo del nome."""
    righe = [f"{p['modificato']}  {p['nome']}" for p in _prj.list_projects(filtro)]
    return "\n".join(righe) if righe else "Nessun progetto trovato."

def sysmac_sections(progetto: str) -> str:
    """Sezioni ladder di un progetto e quanti rung contengono.
    progetto = nome (anche parziale) o GUID."""
    p = _prj.find_project(progetto)
    s = _prj.sections(p)
    if not s:
        return f"{p['nome']}: nessuna sezione ladder."
    return f"{p['nome']}:\n" + "\n".join(f"{x['rung']:5} rung  {x['nome']}" for x in s)

def sysmac_read(progetto: str, sezione: str = "", max_rung: int = 0) -> str:
    """Legge il ladder come TESTO leggibile direttamente dai file di progetto:
    un rung per blocco, con commento, contatti (LD/LDN), bobine (OUT/SET/RESET),
    blocchi funzione con i parametri e lo ST in linea.
    Non serve che il progetto sia aperto. max_rung=0 significa tutti."""
    p = _prj.find_project(progetto)
    return _prj.read_section(p, sezione, max_rung)

def sysmac_find_var(progetto: str, variabile: str, solo_scrittura: bool = False) -> str:
    """Dove viene usata una variabile: sezione, rung e ruolo (letta da un
    contatto, scritta da una bobina, passata a un blocco funzione, usata in ST).
    solo_scrittura=True mostra solo dove viene SCRITTA: e' il modo piu' rapido
    per capire chi comanda un bit durante il debug."""
    p = _prj.find_project(progetto)
    return _prj.find_var(p, variabile, solo_scrittura)

# ---------------------------------------------------------------- CLI test


def sysmac_paste_vars(path: str, row_x: int = 353, row_y: int = 304,
                      wait: float = 1.2) -> str:
    """Registra in BLOCCO le variabili di un file TSV nella tabella variabili
    del programma (scheda 'Interne'), gestendo il dialogo 'Risolvi conflitti
    operazione Incolla' che Sysmac apre quando la tabella non e' vuota.

    TSV atteso (una riga per variabile, colonne separate da TAB):
        Nome <TAB> Tipo <TAB> ValoreIniziale <TAB> AT <TAB> Ritentivo <TAB>
        Costante <TAB> Commento
    (lo produce ladder_gen.py insieme alla sezione: out\\vars.txt)

    PRIMA di chiamarlo: aprire l'editor della sezione ladder e la tabella
    variabili (click sulla barra 'Variabili'), poi scorrere in fondo alla
    tabella. row_x/row_y = punto su cui cliccare per selezionare una RIGA
    (la colonna del selettore, a sinistra del nome).

    Sequenza: seleziona riga -> Ctrl+V -> se compare il dialogo, lo gestisce
    con risolvi_conflitti.ps1 (UI Automation, InvokePattern):
    'Copia tutto da destra a sinistra' -> attende che 'Applica' si abiliti ->
    'Applica' -> 'Chiudi'.
    NB: i click del mouse sui pulsanti del dialogo NON funzionano in modo
    affidabile (il layout interno si sposta col contenuto e il dialogo si apre
    a cascata in posizioni diverse); l'Invoke di UI Automation si'.
    """
    with open(path, encoding="utf-8") as fh:
        rows = [l.rstrip("\r\n") for l in fh.read().splitlines() if l.strip()]
    if not rows:
        return "Nessuna variabile nel file."
    tsv = "\r\n".join(rows)
    _ps("Add-Type -AssemblyName System.Windows.Forms; "
        "[System.Windows.Forms.Clipboard]::SetText(" + _ps_quote(tsv) + ")", sta=True)

    _focus_sysmac()
    _click(row_x, row_y)
    time.sleep(0.3)
    _send_keys("^v")
    time.sleep(wait)

    dlg = _find_window("Risolvi conflitti")
    if dlg is None:
        return f"{len(rows)} variabili incollate (nessun dialogo di conflitti)."

    # Il dialogo va gestito via UI Automation: i click del mouse sui suoi
    # pulsanti non sono affidabili (il layout interno si sposta col contenuto
    # e "Applica" si abilita con ritardo). Lo script fa:
    #   "Copia tutto da destra a sinistra" -> attesa -> "Applica" -> "Chiudi"
    ps1 = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "risolvi_conflitti.ps1")
    out = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps1],
        capture_output=True, text=True, timeout=90,
        errors="replace").stdout.strip()
    esito = {
        "APPLICATO_E_CHIUSO": "applicate",
        "APPLICATO_DIALOGO_ANCORA_APERTO": "applicate (dialogo ancora aperto)",
        "NESSUN_DIALOGO": "nessun dialogo",
        "APPLICA_NON_ABILITATO": "NON applicate: 'Applica' non si e' abilitato",
        "PULSANTE_COPIA_NON_TROVATO": "NON applicate: pulsante 'Copia tutto' non trovato",
    }.get(out, "esito incerto: " + out)
    return f"{len(rows)} variabili: {esito}. Verificare con sysmac_compile."



# ==================================================================== SIMULATORE
# Collaudo HEADLESS: legge e scrive le variabili globali mentre la simulazione
# gira, via NexSocket.dll. ~0,2 ms per operazione, contro i ~3 s di uno
# screenshot + click destro Set/Reset. Vincolo: solo variabili GLOBALI.

def _progetto_aperto() -> str:
    """Nome del progetto dal titolo finestra: '<Progetto> - <controller> - ...'."""
    out = _ps("Get-Process SysmacStudio -ErrorAction SilentlyContinue | "
              "ForEach-Object { $_.MainWindowTitle }")
    t = (out or "").strip().splitlines()
    t = t[0] if t else ""
    return t.split(" - ")[0].strip() if " - " in t else ""


def _sim(progetto: str = ""):
    d = os.path.dirname(os.path.abspath(__file__))
    if d not in sys.path:
        sys.path.insert(0, d)
    import simlink
    p = progetto or _progetto_aperto()
    try:
        return simlink.Sim(progetto=p or None).connect()
    except Exception:
        # progetto non trovato su disco (mai salvato): si prosegue senza tipi
        return simlink.Sim().connect()


def _lista(s: str):
    return [x.strip() for x in re.split(r"[,;\n]+", s or "") if x.strip()]


def sysmac_sim_stato(progetto: str = "") -> str:
    """Verifica se il SIMULATORE e' raggiungibile e quante variabili globali
    espone il progetto aperto. Da chiamare prima di leggere/scrivere."""
    import json
    p = progetto or _progetto_aperto()
    info = {"progetto": p}
    try:
        d = os.path.dirname(os.path.abspath(__file__))
        if d not in sys.path:
            sys.path.insert(0, d)
        import simvars
        info["variabili_globali"] = len(simvars.variabili_globali(p)) if p else 0
    except Exception as e:
        info["variabili_globali"] = "non leggibili: %s" % e
    try:
        s = _sim(progetto)
        try:
            s.read("_CurrentTime")
            info["simulatore"] = "RAGGIUNGIBILE"
        finally:
            s.close()
    except Exception as e:
        info["simulatore"] = "NON raggiungibile (%s). Avviare la simulazione (F5)." % e
    return json.dumps(info, ensure_ascii=False)


@mcp.tool(annotations={"readOnlyHint": True})
def sysmac_sim_vars(progetto: str = "", filtro: str = "", max_righe: int = 200) -> str:
    """Elenco delle VARIABILI GLOBALI del progetto con il tipo esatto, letto
    dai file su disco (nessuna GUI, istantaneo). Solo queste variabili sono
    leggibili/scrivibili dal simulatore."""
    import json
    d = os.path.dirname(os.path.abspath(__file__))
    if d not in sys.path:
        sys.path.insert(0, d)
    import simvars
    p = progetto or _progetto_aperto()
    t = simvars.variabili_globali(p)
    if filtro:
        f = filtro.lower()
        t = {k: v for k, v in t.items() if f in k.lower()}
    voci = sorted(t.items())
    testo = "\n".join("%s\t%s" % kv for kv in voci[:max_righe])
    if len(voci) > max_righe:
        testo += "\n... (%d di %d mostrate)" % (max_righe, len(voci))
    return "progetto=%s  globali=%d\n%s" % (p, len(voci), testo)


@mcp.tool(annotations={"readOnlyHint": True})
def sysmac_sim_read(variabili: str, progetto: str = "") -> str:
    """Legge una o piu' variabili GLOBALI dal simulatore in RUN.
    variabili: nomi separati da virgola, es. 'IN_MARCIA,PV_Ph,Allarme_Bit[3]'.
    Sostituisce screenshot e finestre di watch: ~0,2 ms per variabile."""
    import json
    s = _sim(progetto)
    try:
        return json.dumps(s.read_many(_lista(variabili)), ensure_ascii=False)
    finally:
        s.close()


@mcp.tool()
def sysmac_sim_write(assegnazioni: str, progetto: str = "") -> str:
    """Scrive variabili GLOBALI nel simulatore in RUN (equivale a forzare gli
    ingressi). assegnazioni: 'IN_MARCIA=1,SET_PH=7.2,Nome=testo'."""
    import json
    coppie = {}
    for a in _lista(assegnazioni):
        if "=" not in a:
            return "formato errato: '%s' (atteso NOME=VALORE)" % a
        n, v = a.split("=", 1)
        coppie[n.strip()] = v.strip()
    s = _sim(progetto)
    try:
        s.write_many(coppie)
        return json.dumps({"scritte": coppie,
                           "rilette": s.read_many(list(coppie))}, ensure_ascii=False)
    finally:
        s.close()


@mcp.tool(annotations={"readOnlyHint": True})
def sysmac_sim_watch(variabili: str, secondi: float = 5.0,
                     intervallo: float = 0.2, progetto: str = "") -> str:
    """Registra l'andamento nel tempo di alcune variabili (timeline compatta:
    salva un campione solo quando qualcosa cambia). Serve a verificare
    sequenze, timer e passi di ciclo senza guardare lo schermo."""
    import json
    s = _sim(progetto)
    try:
        c = s.watch(_lista(variabili), float(secondi), float(intervallo))
        return json.dumps(c, ensure_ascii=False)
    finally:
        s.close()


@mcp.tool()
def sysmac_sim_test(scenario: str, progetto: str = "") -> str:
    """Esegue un COLLAUDO AUTOMATICO sul simulatore e ritorna PASS/FAIL.

    scenario = JSON (testo o percorso di un file .json):
    {"nome":"ciclo semaforo",
     "passi":[{"set":{"IN_MARCIA":1}},
              {"attendi":1},
              {"verifica":{"Sem1_Verde":true,"Sem2_Rosso":true},
               "descrizione":"fase 1"},
              {"attendi":10},
              {"verifica":{"Sem1_Giallo":true}},
              {"watch":["Sem1_Verde","Sem1_Rosso"],"secondi":6}]}
    """
    import json
    sc = scenario.strip()
    if not sc.startswith("{"):
        with open(sc, "r", encoding="utf-8-sig") as f:
            sc = f.read()
    dati = json.loads(sc)
    s = _sim(progetto)
    try:
        return json.dumps(s.esegui_scenario(dati), ensure_ascii=False, indent=1)
    finally:
        s.close()


def _selettore_ultima_riga():
    """(x, y) del selettore dell'ULTIMA riga della griglia a fuoco, in
    coordinate schermo, ricavato dal rettangolo della riga via UI Automation.

    Serve perche' l'Incolla del menu contestuale si applica alla CELLA se non
    e' selezionata la riga intera: il TSV finirebbe scritto dentro la cella."""
    ps = ("$w = Get-SysmacMainWindow; $best = $null; "
          "foreach ($r in @(Find-UiElements -Root $w -Type DataItem)) { "
          "  $b = $r.Current.BoundingRectangle; "
          "  if ($b.Width -gt 100) { if (-not $best -or $b.Y -gt $best.Y) { $best = $b } } }; "
          "if ($best) { '' + [int]$best.X + ';' + [int]$best.Y + ';' + [int]$best.Height } "
          "else { 'NIENTE' }")
    out = _uia(ps).strip().splitlines()
    ultima = out[-1].strip() if out else ""
    if ";" not in ultima:
        raise RuntimeError("nessuna riga di griglia trovata: la tabella variabili "
                           "e' aperta e ha almeno una riga?")
    x, y, h = [int(v) for v in ultima.split(";")]
    return x + 8, y + h // 2

def _tsv_variabili(variabili: str, tab: str) -> str:
    """Righe 'NOME TIPO [commento]' -> TSV con le colonne della tabella scelta.
    Stessi formati di sysmac_vars_crea, verificati su Sysmac Studio 1.66."""
    righe = []
    for r in (variabili or "").splitlines():
        r = r.strip()
        if not r:
            continue
        if "\t" in r:
            p = r.split("\t")
        elif ":" in r and " " not in r.split(":")[0]:
            p = r.split(":", 1)
        else:
            p = r.split(None, 1)
        nome = p[0].strip()
        tipo = p[1].strip() if len(p) > 1 else ""
        com = p[2].strip() if len(p) > 2 else ""
        if tab != "esterne" and not tipo:
            raise ValueError("riga senza tipo: %r (atteso NOME TIPO)" % r)
        if tab == "globali":
            righe.append("\t".join([nome, tipo, "", "", "False", "False",
                                    "Non pubblicare", com]))
        elif tab == "interne":
            righe.append("\t".join([nome, tipo, "", "", "False", "False", com]))
        else:
            righe.append("\t".join([nome, "False", com]))
    if not righe:
        raise ValueError("nessuna variabile indicata")
    return "\r\n".join(righe)


def _conta_variabili(tab: str, programma: str = "") -> int:
    """Quante variabili ci sono nella tabella indicata, lette dal DISCO."""
    cart = _cartella_progetto_aperto()
    if not cart:
        return -1
    d = os.path.dirname(os.path.abspath(__file__))
    if d not in sys.path:
        sys.path.insert(0, d)
    import slwd
    try:
        f = slwd.file_globali(cart) if tab == "globali" else slwd.file_locali(cart, programma)
        _testa, gruppi = slwd.leggi(f)
    except Exception:
        return -1
    sigla = {"globali": "VAR", "interne": "VAR", "esterne": "VAR_EXTERNAL"}[tab]
    tot = 0
    for intest, righe in gruppi:
        if ("GN=%s" % sigla) in intest:
            tot += len(righe)
    return tot


@mcp.tool()
def sysmac_vars_crea(variabili: str, tabella: str = "globali",
                     tabella_vuota: bool = False,
                     riga_x: int = 290, riga_y: int = 232) -> str:
    """Crea VARIABILI in blocco incollandole nella tabella gia' aperta in
    Sysmac (una sola Ctrl+V per centinaia di righe).

    tabella:
      "globali" -> Variabili globali        (8 colonne TSV)
      "interne" -> Variabili interne del POU (7 colonne, qui vanno le istanze
                   di FB: TON, CTU, blocchi funzione: NON sono ammesse fra le
                   globali)
      "esterne" -> Variabili esterne del POU (solo il NOME: il tipo lo eredita
                   dalla globale). SERVE una riga esterna per OGNI variabile
                   globale usata dal programma, altrimenti la compilazione da'
                   "Per utilizzare una variabile globale e' necessario
                   registrare una variabile esterna corrispondente".

    variabili: una per riga, "NOME TIPO" / "NOME:TIPO" / "NOME<TAB>TIPO".
    Per la tabella "esterne" basta il nome.
    tabella_vuota=True se la tabella non ha ancora righe: la prima variabile
    viene digitata (l'incolla su tabella vuota non funziona), le altre incollate.

    Formati verificati sperimentalmente il 27/08/2026 su Sysmac Studio 1.66.
    """
    tab = (tabella or "globali").strip().lower()
    if tab not in ("globali", "interne", "esterne"):
        return "tabella deve essere 'globali', 'interne' o 'esterne'"

    righe = []
    for r in (variabili or "").splitlines():
        r = r.strip()
        if not r:
            continue
        if "\t" in r:
            p = r.split("\t")
        elif ":" in r and " " not in r.split(":")[0]:
            p = r.split(":", 1)
        else:
            p = r.split(None, 1)
        nome = p[0].strip()
        tipo = p[1].strip() if len(p) > 1 else ""
        com = p[2].strip() if len(p) > 2 else ""
        if tab != "esterne" and not tipo:
            return "riga senza tipo: %r (atteso NOME TIPO)" % r
        righe.append((nome, tipo, com))
    if not righe:
        return "nessuna variabile indicata"

    def tsv(v):
        if tab == "globali":     # Nome Tipo Iniziale AT Ritentivo Costante Pubbl. Commento
            return "\t".join([v[0], v[1], "", "", "False", "False",
                               "Non pubblicare", v[2]])
        if tab == "interne":     # Nome Tipo Iniziale AT Ritentivo Costante Commento
            return "\t".join([v[0], v[1], "", "", "False", "False", v[2]])
        return "\t".join([v[0], "False", v[2]])        # esterne: Nome Costante Commento

    _focus_sysmac()
    inizio = 0
    if tabella_vuota:
        n, t, _c = righe[0]
        _click(riga_x + 210, riga_y, double=True)
        time.sleep(0.35)
        _send_keys(n + ("{TAB}" + t if tab != "esterne" else "") + "{ENTER}")
        time.sleep(0.6)
        _click(riga_x + 1000, riga_y + 60)      # esce dalla cella e conferma
        time.sleep(0.4)
        inizio = 1
        if len(righe) == 1:
            return "creata 1 variabile (%s): %s" % (tab, n)

    testo = "\r\n".join(tsv(v) for v in righe[inizio:]) + "\r\n"
    _ps("Set-Clipboard -Value " + _ps_quote(testo), sta=True)
    _focus_sysmac()
    _click(riga_x, riga_y)            # seleziona la riga (colonna maniglia)
    time.sleep(0.3)
    _send_keys("^v")
    time.sleep(1.0)
    return ("tabella '%s': incollate %d variabili%s. Verificare con "
            "sysmac_compile_text, poi sysmac_save."
            % (tab, len(righe) - inizio,
               " (+1 digitata)" if inizio else ""))


@mcp.tool()
def sysmac_vars(variabili: str, tabella: str = "globali", programma: str = "",
                riga_x: int = 385, riga_y: int = 225) -> str:
    """Crea VARIABILI in blocco a progetto APERTO, senza chiuderlo e senza
    click a coordinate sui menu.

    variabili: una per riga, "NOME TIPO" (o "NOME:TIPO", o TSV completo).
               Per la tabella "esterne" basta il nome.
    tabella:   "globali" | "interne" | "esterne"
    programma: nome del POU per interne/esterne (serve solo alla verifica)

    PRIMA di chiamarlo: aprire la tabella giusta in Sysmac (Variabili globali
    dall'albero, oppure la barra "Variabili" sopra l'editor della sezione per
    interne/esterne). riga_x/riga_y servono solo al primo click, che da' il
    fuoco alla griglia: tutto il resto (ultima riga, menu contestuale, crea
    riga, incolla, elimina la riga vuota) va da se'.

    Sostituisce il giro chiudi progetto -> vars_offline -> riapri, che costava
    2-3 minuti e rischiava di lasciare la finestra nascosta."""
    tab = (tabella or "globali").strip().lower()
    if tab not in ("globali", "interne", "esterne"):
        raise ValueError("tabella deve essere 'globali', 'interne' o 'esterne'")
    tsv = _tsv_variabili(variabili, tab)
    attese = tsv.count("\r\n") + 1

    prima = _conta_variabili(tab, programma)

    _ps("Add-Type -AssemblyName System.Windows.Forms; "
        "[System.Windows.Forms.Clipboard]::SetText(" + _ps_quote(tsv) + ")", sta=True)

    _clickf(riga_x, riga_y)          # unico click "cieco": fuoco alla griglia
    time.sleep(0.4)
    _send_keys("^{END}")             # ultima riga
    time.sleep(0.8)

    # riga nuova in fondo (fa da cuscinetto: incollare su una riga esistente la
    # sovrascriverebbe), dal menu contestuale aperto da tastiera
    _send_keys("+{F10}"); time.sleep(1.0)
    if "OK" not in _uia("if (Invoke-UiMenuItem -Name 'Crea nuovo') { 'OK' } else { 'KO' }"):
        _send_keys("{ESC}")
        raise RuntimeError(
            "non sono riuscito a creare la riga nuova in fondo. Causa tipica: "
            "nella tabella c'e' gia' una RIGA VUOTA residua (nome mancante) e "
            "Sysmac non ne crea una seconda: eliminarla e riprovare.")
    time.sleep(0.8)
    _send_keys("{ESC}")              # esce dall'editing della cella
    time.sleep(0.5)

    # seleziona la RIGA intera cliccandone il selettore, calcolato via UIA
    sel_x, sel_y = _selettore_ultima_riga()
    _click(sel_x, sel_y)
    time.sleep(0.5)

    _send_keys("+{F10}"); time.sleep(1.0)
    if "OK" not in _uia("if (Invoke-UiMenuItem -Name 'Incolla') { 'OK' } else { 'KO' }"):
        _send_keys("{ESC}")
        raise RuntimeError("Incolla non disponibile nel menu contestuale.")
    time.sleep(1.8)

    # eventuale dialogo "Risolvi conflitti operazione Incolla"
    conflitti = ""
    if _find_window("Risolvi conflitti"):
        ps1 = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "risolvi_conflitti.ps1")
        if os.path.exists(ps1):
            r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                                "-File", ps1], capture_output=True, text=True,
                               timeout=90, errors="replace").stdout.strip()
            conflitti = " (dialogo conflitti: %s)" % r
        time.sleep(1.0)

    # la riga vuota resta dov'era (le nuove vanno sotto): stesso punto, Elimina
    _click(sel_x, sel_y)
    time.sleep(0.4)
    _send_keys("+{F10}"); time.sleep(1.0)
    _uia("Invoke-UiMenuItem -Name 'Elimina' | Out-Null")
    time.sleep(0.8)

    _send_keys("^s"); time.sleep(2.2)
    dopo = _conta_variabili(tab, programma)
    if prima >= 0 and dopo >= 0:
        delta = dopo - prima
        if delta <= 0:
            raise RuntimeError(
                "VARIABILI NON CREATE: la tabella %s aveva %d righe e ne ha %d "
                "(attese +%d). Controllare che sia aperta la tabella giusta e "
                "che il primo click (%d,%d) cada su una sua cella."
                % (tab, prima, dopo, attese, riga_x, riga_y))
        avviso = "" if delta == attese else " ATTENZIONE: attese %d, create %d." % (attese, delta)
        return ("Create %d variabili in '%s' (%d -> %d).%s%s"
                % (delta, tab, prima, dopo, conflitti, avviso))
    return ("Incollate %d variabili in '%s' (verifica su disco non disponibile).%s"
            % (attese, tab, conflitti))

@mcp.tool()
def sysmac_vars_offline(progetto: str, globali: str = "", interne: str = "",
                        esterne: str = "", programma: str = "") -> str:
    """Crea VARIABILI scrivendo direttamente i file di progetto, a progetto
    CHIUSO: nessuna GUI, nessun clipboard, nessuna coordinata. Istantaneo
    anche per centinaia di variabili. E' la via piu' veloce e piu' affidabile.

    Richiede che il progetto NON sia aperto in Sysmac Studio (altrimenti il
    salvataggio di Sysmac sovrascrive le modifiche): il tool lo verifica e si
    rifiuta di scrivere.

    globali / interne: una variabile per riga, "NOME TIPO" oppure "NOME:TIPO",
      con eventuale terzo campo (separato da TAB) come commento.
      Le ISTANZE DI BLOCCO FUNZIONE (TON, CTU, FB custom) vanno in `interne`:
      non sono ammesse fra le globali.
    esterne: solo i NOMI delle variabili globali usate dal programma (il tipo
      viene ereditato). Ne serve una per OGNI globale usata, altrimenti la
      compilazione fallisce.
    programma: nome del POU (necessario solo se il progetto ha piu' POU).

    `progetto` puo' essere il NOME di un progetto dell'archivio (che deve essere
    chiuso in Sysmac) oppure il PERCORSO di un file .smc2: in quel caso il file
    viene estratto, modificato e ricompresso, e non serve nessun archivio.

    Dopo: riaprire il progetto, F8 (sysmac_compile_text), Ctrl+S.
    """
    import json
    d = os.path.dirname(os.path.abspath(__file__))
    if d not in sys.path:
        sys.path.insert(0, d)
    import slwd

    def parse(testo, con_tipo=True):
        out = []
        for r in (testo or "").splitlines():
            r = r.strip()
            if not r:
                continue
            if "\t" in r:
                p = r.split("\t")
            elif ":" in r and " " not in r.split(":")[0]:
                p = r.split(":", 1)
            else:
                p = r.split(None, 1)
            v = {"nome": p[0].strip()}
            if con_tipo:
                if len(p) < 2:
                    raise ValueError("riga senza tipo: %r" % r)
                v["tipo"] = p[1].strip()
            if len(p) > 2:
                v["commento"] = p[2].strip()
            out.append(v)
        return out

    import smc2
    try:
        if smc2.e_file(progetto):
            # progetto che sta in un file: si estrae, si scrive, si ricomprime
            with smc2.progetto(progetto) as p:
                res = slwd.crea_variabili(
                    p.cartella,
                    globali=parse(globali),
                    interne=parse(interne),
                    esterne=parse(esterne, con_tipo=False),
                    programma=programma, forza=True)
                p.tocca()
            res["file"] = progetto
        else:
            res = slwd.crea_variabili(
                progetto,
                globali=parse(globali),
                interne=parse(interne),
                esterne=parse(esterne, con_tipo=False),
                programma=programma)
    except Exception as e:
        return "ERRORE: %s" % e
    return json.dumps(res, ensure_ascii=False, indent=1)


def sysmac_vars_offline_stato(progetto: str) -> str:
    """Dice se il progetto e' aperto in Sysmac (e quindi non scrivibile
    offline) e quante variabili contiene gia' ciascuna tabella."""
    import json
    d = os.path.dirname(os.path.abspath(__file__))
    if d not in sys.path:
        sys.path.insert(0, d)
    import slwd
    cart = slwd.trova_progetto(progetto)
    info = {"cartella": cart, "aperto_in_sysmac": slwd.aperto_in_sysmac(cart)}
    _t, g = slwd.leggi(slwd.file_globali(cart))
    info["globali"] = sum(len(r) for _i, r in g)
    try:
        _t, l = slwd.leggi(slwd.file_locali(cart))
        info["gruppi_locali"] = {i.split("\t")[0].replace("+GN=", ""): len(r)
                                 for i, r in l}
    except ValueError as e:
        info["gruppi_locali"] = str(e)
    return json.dumps(info, ensure_ascii=False)


def _python():
    """Interprete da usare per i processi figli. sys.executable non e'
    affidabile quando il server e' avviato da un contenitore che lo rimpiazza:
    si ricade sull'interprete configurato per il server MCP."""
    p = sys.executable or ""
    if p.lower().endswith("python.exe") and os.path.exists(p):
        return p
    for c in (r"C:\Program Files\Python313\python.exe",
              r"C:\Program Files\Python312\python.exe"):
        if os.path.exists(c):
            return c
    return p or "python"


def _ambiente():
    """Ambiente minimo e pulito per i processi figli: l'ambiente ereditato dal
    contenitore puo' contenere variabili (PYTHONPATH, PYTHONSTARTUP, proxy...)
    che rallentano o alterano l'avvio dell'interprete."""
    tieni = ("SystemRoot", "windir", "PATH", "PATHEXT", "TEMP", "TMP",
             "USERPROFILE", "APPDATA", "LOCALAPPDATA", "PROGRAMFILES",
             "COMSPEC", "NUMBER_OF_PROCESSORS", "OS")
    e = {k: v for k, v in os.environ.items() if k.upper() in
         {t.upper() for t in tieni}}
    e["PYTHONIOENCODING"] = "utf-8"
    e["PYTHONDONTWRITEBYTECODE"] = "1"
    return e


def _exec_diagnostica(d):
    """Perche' i processi figli non partono? Risponde con i tempi misurati."""
    import json
    import time as _t
    import tempfile
    info = {"interprete": _python(), "sys.executable": sys.executable,
            "cartella": d, "variabili_ambiente_ereditate": len(os.environ)}
    prova = os.path.join(tempfile.gettempdir(), "_sysmac_prova.py")
    try:
        with open(prova, "w", encoding="utf-8") as fh:
            fh.write("print('ok')\n")
        for etichetta, kw in (("figlio_semplice", {}),
                              ("figlio_ambiente_pulito", {"env": _ambiente()})):
            t = _t.time()
            try:
                r = subprocess.run([_python(), prova], capture_output=True,
                                   text=True, timeout=25,
                                   stdin=subprocess.DEVNULL, **kw)
                info[etichetta] = "%.1f s -> %r" % (_t.time() - t,
                                                    (r.stdout or "").strip())
            except subprocess.TimeoutExpired:
                info[etichetta] = "TIMEOUT dopo %.0f s" % (_t.time() - t)
            except Exception as ex:
                info[etichetta] = "errore: %s" % ex
        t = _t.time()
        try:
            subprocess.run(["cmd", "/c", "echo ok"], capture_output=True,
                           text=True, timeout=25, stdin=subprocess.DEVNULL)
            info["figlio_cmd"] = "%.1f s" % (_t.time() - t)
        except Exception as ex:
            info["figlio_cmd"] = "errore: %s" % ex
    finally:
        try:
            os.unlink(prova)
        except OSError:
            pass
    return json.dumps(info, ensure_ascii=False, indent=1)


@mcp.tool()
async def sysmac_exec(codice: str, timeout: int = 50, max_caratteri: int = 6000) -> str:
    """Esegue uno SCRIPT PYTHON con Sysmac Studio e il suo simulatore gia'
    collegati. E' il modo piu' efficiente di lavorare: una sequenza che
    richiederebbe 8-10 chiamate separate si scrive in un solo script, con
    cicli, condizioni e ritentativi, e costa un solo giro.

    USALO PER: sequenze di piu' passi, collaudi, cicli di attesa, elaborazioni
    sui dati letti, generazione di variabili, tutto cio' che va ripetuto.
    NON SERVE per una singola lettura o scrittura: per quelle bastano
    sysmac_sim_read / sysmac_sim_write.

    FUNZIONI GIA' DISPONIBILI nello script (non importare nulla):
      progetto()                      nome del progetto aperto
      leggi("A","B")                  variabili globali dal simulatore in RUN
      scrivi(A=1, PV_Ph=7.2)          forza gli ingressi e rilegge
      watch("A","B", secondi=10)      timeline (salva solo i cambiamenti)
      collauda(scenario)              scenario dict/JSON -> esito PASS/FAIL
      sim()                           oggetto Sim completo (read, write, info)
      sim_pronto()                    True se il simulatore risponde
      sim_avvia(attesa=60)            F5 e ATTENDE che risponda davvero
      sim_ferma()                     Shift+F5
      compila()  errori()  salva()    F8 / elenco errori / Ctrl+S
      importa(xml_o_file)             incolla rung (simulazione ferma)
      vars_globali(filtro="")         {nome: tipo} dal disco, senza GUI
      vars_offline(prog, globali=[], interne=[], esterne=[])
                                      crea variabili nei file (progetto CHIUSO)
      simlink, simvars, slwd, S       moduli completi (S = tutti i tool)
      json, time, re, os

    COSA TORNA: tutto quello che stampi con print(). Se assegni una variabile
    chiamata `risultato`, viene restituita anche quella (serializzata in JSON).

    VINCOLI: il simulatore espone SOLO le variabili GLOBALI; deve essere in RUN
    (l'avvio richiede ~40-60 s); vars_offline richiede il progetto CHIUSO.
    Il codice gira in un processo separato con timeout: se si blocca viene
    terminato senza danneggiare il server. Il timeout predefinito e' 50 s
    perche' il client MCP smette di aspettare prima: per operazioni piu' lunghe
    (avvio del simulatore, collaudi di minuti) alzarlo E sapere che la risposta
    potrebbe non tornare -- l'uscita completa resta comunque in
    out\\ultimo_exec.txt. Passando `codice="__diagnostica__"` il tool misura
    perche' i processi figli non partono.

    ESEMPIO
        sim_avvia()
        scrivi(IN_MARCIA=1)
        t = watch("Sem1_Verde","Sem1_Rosso", secondi=30)
        print("transizioni:", len(t))
        risultato = collauda({"nome":"ciclo","passi":[
            {"attendi":2},
            {"verifica":{"Sem1_Verde":True}}]})
    """
    import asyncio
    d = os.path.dirname(os.path.abspath(__file__))
    if codice.strip() == "__diagnostica__":
        return await asyncio.to_thread(_exec_diagnostica, d)
    return await asyncio.to_thread(_esegui_codice, codice, timeout,
                                   max_caratteri)


def _esegui_codice(codice: str, timeout: int, max_caratteri: int) -> str:
    import json
    import tempfile
    import time as _t
    d = os.path.dirname(os.path.abspath(__file__))

    f = tempfile.NamedTemporaryFile("w", suffix=".py", delete=False,
                                    encoding="utf-8")
    try:
        f.write(codice)
        f.close()
        avvio = _t.time()
        try:
            r = subprocess.run(
                [_python(), os.path.join(d, "esegui.py"), f.name,
                 str(timeout)],
                capture_output=True, text=True, timeout=timeout, cwd=d,
                encoding="utf-8", errors="replace",
                stdin=subprocess.DEVNULL, env=_ambiente(),
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        except subprocess.TimeoutExpired as e:
            parziale = (e.stdout or "")[-800:] if e.stdout else ""
            errp = (e.stderr or "")[-800:] if e.stderr else ""
            return ("TIMEOUT dopo %d s (interprete %s). Lo script e' stato "
                    "interrotto.\nCause possibili, in ordine: (1) il codice "
                    "attende qualcosa che non arriva -- l'avvio del simulatore "
                    "richiede 40-60 s, usare sim_avvia() che verifica; (2) una "
                    "finestra di dialogo aperta in Sysmac blocca l'operazione "
                    "-- controllarla con sysmac_ui(azione='albero'); (3) una "
                    "connessione al simulatore rimasta appesa da un'esecuzione "
                    "precedente.\nuscita parziale: %r\nerrori: %r"
                    % (timeout, _python(), parziale, errp))
        try:
            e = json.loads((r.stdout or "").strip() or "{}")
        except ValueError:
            return "USCITA NON INTERPRETABILE:\n%s\n%s" % (r.stdout[-2000:],
                                                            r.stderr[-1000:])
        parti = []
        if e.get("uscita"):
            parti.append(e["uscita"].rstrip())
        if e.get("risultato") is not None:
            parti.append("risultato = " + str(e["risultato"]))
        if e.get("errore"):
            parti.append("ERRORE:\n" + e["errore"].rstrip())
        if r.stderr and r.stderr.strip() and not e.get("errore"):
            parti.append("stderr: " + r.stderr.strip()[:500])
        testo = "\n".join(parti) if parti else "(nessuna uscita)"
        try:
            reg = os.path.join(d, "out")
            os.makedirs(reg, exist_ok=True)
            with open(os.path.join(reg, "ultimo_exec.txt"), "w",
                      encoding="utf-8") as fh:
                fh.write("durata %.1f s\n\n%s" % (_t.time() - avvio, testo))
        except OSError:
            pass
        if len(testo) > max_caratteri:
            testo = (testo[:max_caratteri]
                     + "\n... [uscita troncata a %d caratteri: l'uscita "
                       "completa e' in out\\ultimo_exec.txt]" % max_caratteri)
        return testo
    finally:
        try:
            os.unlink(f.name)
        except OSError:
            pass


@mcp.tool()
def sysmac_ui(azione: str, x: int = 0, y: int = 0, testo: str = "",
              doppio: bool = False, pulsante: str = "left",
              titolo: str = "", max_voci: int = 300) -> str:
    """Comandi diretti sull'interfaccia di Sysmac Studio: un solo tool al posto
    delle sei primitive separate di prima.

    azione:
      "focus"     porta Sysmac in primo piano
      "click"     clic in (x, y); doppio=True per il doppio clic;
                  pulsante="right" per il tasto destro
      "tasti"     invia `testo`: le sequenze di comando ("^v", "{ESC}") e le
                  scorciatoie di una lettera (c, d, o, f, r) partono come
                  tasti, il testo semplice viene immesso dagli APPUNTI
      "scrivi"    scrive `testo` sempre dagli appunti (anche un carattere)
      "capslock"  spegne il CapsLock se acceso
      "menu"      apre la voce di menu in `testo`, es. "File|Chiudi"
      "pulsante"  preme il pulsante di nome `testo` (`titolo` = finestra)
      "albero"    elenca gli elementi dell'interfaccia: serve a capire quale
                  dialogo e' aperto o dove cliccare
      "massimizza" porta la finestra a schermo intero (le coordinate note
                  valgono in quella condizione)
      "riavvia"   chiude e rilancia Sysmac Studio: rimedio quando la pagina
                  iniziale si incastra e i clic non aprono piu' nulla.
                  Rifiuta se c'e' un progetto aperto

    Per una SEQUENZA di operazioni conviene sysmac_exec, dove le stesse
    funzioni sono disponibili come S.sysmac_click(...), S.sysmac_send_keys(...).
    """
    a = (azione or "").strip().lower()
    if a == "focus":
        return sysmac_focus()
    if a == "click":
        return sysmac_click(x, y, pulsante, doppio)
    if a in ("massimizza", "schermo"):
        agito = _massimizza()
        l, t, r, b = _rect_sysmac()
        return ("finestra %s: %d,%d - %d,%d"
                % ("massimizzata ora" if agito else "gia' a schermo intero",
                   l, t, r, b))
    if a in ("tasti", "keys"):
        return sysmac_send_keys(testo)
    if a in ("scrivi", "testo"):
        # scrive SEMPRE dagli appunti, anche un solo carattere
        _focus_sysmac()
        _incolla(testo)
        return "Scritto dagli appunti: %s" % testo
    if a in ("capslock",):
        return ("CapsLock era acceso: spento." if _capslock_off()
                else "CapsLock gia' spento.")
    if a == "menu":
        return sysmac_menu(testo)
    if a in ("pulsante", "button"):
        return sysmac_button(testo, titolo)
    if a in ("albero", "dump"):
        return sysmac_ui_dump(titolo, max_voci)
    if a in ("riavvia", "restart"):
        d = os.path.dirname(os.path.abspath(__file__))
        if d not in sys.path:
            sys.path.insert(0, d)
        import sysmac_api
        try:
            return "Sysmac riavviato in %.0f s" % sysmac_api.riavvia_sysmac()
        except Exception as e:
            return "riavvio non riuscito: %s" % e
    return ("azione sconosciuta: %r. Ammesse: focus, click, tasti, menu, "
            "pulsante, albero." % azione)


@mcp.tool(annotations={"readOnlyHint": True})
def sysmac_progetto(azione: str = "elenco", progetto: str = "",
                    sezione: str = "", variabile: str = "",
                    filtro: str = "", max_rung: int = 0,
                    solo_scrittura: bool = False) -> str:
    """Legge i progetti Sysmac DAL DISCO, senza aprire Sysmac Studio e senza
    toccare la GUI: istantaneo, funziona anche su progetti chiusi.

    azione:
      "elenco"   progetti disponibili (`filtro` per restringere)
      "sezioni"  sezioni/POU di `progetto`
      "leggi"    ladder di `sezione` in forma testuale. Usare `max_rung`:
                 senza limite un progetto grosso produce migliaia di righe
      "cerca"    dove viene usata `variabile` (solo_scrittura=True per le sole
                 scritture)
      "offline"  se il progetto e' aperto in Sysmac e quante variabili ha gia'
                 ciascuna tabella: da controllare PRIMA di sysmac_vars_offline
      "file"     riepilogo di un progetto che sta in un FILE .smc2 (nome,
                 variabili globali, sezioni con il numero di rung), senza
                 aprire Sysmac e senza passare dall'archivio. In `progetto` va
                 il percorso del file.
    """
    a = (azione or "elenco").strip().lower()
    if a == "file":
        import json
        import smc2
        if not progetto:
            return "indicare in `progetto` il percorso del file .smc2"
        try:
            return json.dumps(smc2.informazioni(progetto), ensure_ascii=False,
                              indent=1)
        except Exception as e:
            return "ERRORE: %s" % e
    if a == "elenco":
        return sysmac_projects(filtro)
    if not progetto:
        return "indicare `progetto` per l'azione '%s'" % a
    if a == "sezioni":
        return sysmac_sections(progetto)
    if a == "leggi":
        return sysmac_read(progetto, sezione, max_rung)
    if a == "cerca":
        if not variabile:
            return "indicare `variabile` da cercare"
        return sysmac_find_var(progetto, variabile, solo_scrittura)
    if a == "offline":
        return sysmac_vars_offline_stato(progetto)
    return ("azione sconosciuta: %r. Ammesse: elenco, sezioni, leggi, cerca, "
            "offline." % azione)


@mcp.tool()
def sysmac_sim_reset() -> str:
    """Rimette in sesto il collegamento al simulatore quando si blocca.

    Sintomo tipico: le letture vanno in timeout anche se la simulazione e'
    avviata. Causa: connessioni rimaste aperte da processi terminati male; il
    simulatore non ne accetta di nuove e la DLL si blocca invece di dare
    errore. Questo tool fotografa la situazione e, se serve, ferma e riavvia la
    simulazione (Shift+F5, F5) che e' l'unico modo per liberarle davvero."""
    import json
    d = os.path.dirname(os.path.abspath(__file__))
    if d not in sys.path:
        sys.path.insert(0, d)
    import simlink
    info = {"porta_in_ascolto": simlink.porta_aperta(),
            "connessioni_orfane": simlink.connessioni_orfane()}
    if not info["porta_in_ascolto"]:
        info["azione"] = ("simulatore spento: non c'e' nulla da ripristinare, "
                          "avviarlo con la simulazione (F5)")
        return json.dumps(info, ensure_ascii=False)
    try:
        c = simlink.Sim().connect(attesa=6)
        try:
            info["modo"] = c.modo().get("modo")
        finally:
            c.close()
        info["azione"] = "collegamento sano, nessun intervento necessario"
        return json.dumps(info, ensure_ascii=False)
    except Exception as e:
        info["diagnosi"] = str(e)
    sysmac_sim("stop")
    time.sleep(6)
    sysmac_sim("start")
    info["azione"] = ("simulazione fermata e riavviata: attendere 40-60 s, poi "
                      "verificare con sysmac_status")
    return json.dumps(info, ensure_ascii=False)


def sysmac_send_keys(keys: str) -> str:
    """Invia tasti a Sysmac con sintassi SendKeys (es. '{F8}', '^s', '+{F5}',
    '^%r', 'Motore{ENTER}').

    Il TESTO semplice (nomi di variabili, tipi, commenti) viene immesso dagli
    APPUNTI invece che con SendKeys: e' l'unico modo affidabile: con il
    CapsLock acceso SendKeys inverte le maiuscole e ogni tanto perde i primi
    caratteri ("Ritardo" -> "tardo").
    Restano inviate come tasti le sequenze di comando ('^s', '{ENTER}') e le
    scorciatoie di una lettera dell'editor ladder (c, d, o, f, r)."""
    _focus_sysmac()
    if _e_comando_sendkeys(keys):
        _send_keys(keys)
        return f"Inviato: {keys}"
    _incolla(keys)
    return f"Scritto dagli appunti: {keys}"

@mcp.tool(annotations={"readOnlyHint": True})
def sysmac_screenshot(x: int = 0, y: int = 0, width: int = 1920, height: int = 1080) -> Image:
    """Screenshot dello schermo (o di una regione) per verificare lo stato di
    Sysmac: editor, dialoghi, pannello errori, stato simulatore."""
    return Image(data=_capture(x, y, width, height), format="png")


@mcp.tool(annotations={"readOnlyHint": True})
def sysmac_istruzioni(azione: str = "cerca", nome: str = "",
                      max_risultati: int = 25) -> str:
    """Il LINGUAGGIO di Sysmac Studio: catalogo delle istruzioni NJ/NX preso
    dai manuali ufficiali installati con Sysmac (Help\\en-US\\*.chm).

    Serve per proporre soluzioni che non siano la sola ricombinazione di quello
    che c'e' gia' nei progetti in azienda: il catalogo copre ~510 istruzioni,
    contro le 92 effettivamente usate finora.

    azione:
      "cerca"     cerca in `nome` per nome o nella descrizione
                  (es. "timer", "string", "array", "shift", "PID")
      "dettaglio" scheda di un'istruzione: tipo FB/FUN, espressione ST,
                  parametri con verso e TIPI AMMESSI, funzionamento
      "completo"  la pagina intera del manuale, quando serve il dettaglio fine
                  (limiti, precauzioni, esempi)
      "riepilogo" quante istruzioni ci sono e come sono distribuite

    I tipi dei parametri vengono dalla matrice del manuale, non dalla memoria:
    se un'istruzione accetta solo INT, qui si vede.
    """
    import json
    d = os.path.dirname(os.path.abspath(__file__))
    if d not in sys.path:
        sys.path.insert(0, d)
    try:
        import istruzioni
    except Exception as e:
        return "catalogo non disponibile: %s" % e
    a = (azione or "cerca").strip().lower()
    try:
        if a == "riepilogo":
            return json.dumps(istruzioni.riepilogo(), ensure_ascii=False)
        if not nome:
            return "indicare `nome` (istruzione o parola da cercare)"
        if a == "cerca":
            return istruzioni.cerca(nome, max_risultati)
        if a == "dettaglio":
            return istruzioni.dettaglio(nome)
        if a == "completo":
            return istruzioni.testo_completo(nome)
    except Exception as e:
        return "ERRORE: %s" % e
    return ("azione sconosciuta: %r. Ammesse: cerca, dettaglio, completo, "
            "riepilogo." % azione)


def _find_window(title_part: str):
    """rettangolo (l, t, r, b) della prima finestra il cui titolo contiene
    title_part, oppure None."""
    from ctypes import wintypes
    found = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    def _cb(hwnd, _):
        n = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        if n:
            buf = ctypes.create_unicode_buffer(n + 1)
            ctypes.windll.user32.GetWindowTextW(hwnd, buf, n + 1)
            if title_part.lower() in buf.value.lower() and \
               ctypes.windll.user32.IsWindowVisible(hwnd):
                r = wintypes.RECT()
                ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(r))
                found.append((r.left, r.top, r.right, r.bottom))
        return True

    ctypes.windll.user32.EnumWindows(_cb, 0)
    return found[0] if found else None


def _selftest() -> None:
    print("status:", _ps("Get-Process SysmacStudio -ErrorAction SilentlyContinue | "
                          "ForEach-Object { \"pid=$($_.Id) title='$($_.MainWindowTitle)'\" }") or "NON attivo")
    h = _sysmac_hwnd()
    print("hwnd:", h)
    print("selftest OK")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "selftest":
        _selftest()
    elif len(sys.argv) > 2 and sys.argv[1] == "import":
        with open(sys.argv[2], "r", encoding="utf-8-sig") as f:
            xml_in = f.read()
        _set_ladder_clipboard(xml_in)
        _focus_sysmac()
        _click(317, 210)
        time.sleep(0.4)
        _send_keys("^v")
        time.sleep(1.5)
        print("import inviato: verificare in Sysmac")
    else:
        mcp.run()

