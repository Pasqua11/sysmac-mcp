# -*- coding: utf-8 -*-
"""
patch_A.py - Intervento A sul server MCP sysmac-ladder (28/08/2026)

1. _hwnd_per_titolo()   : trova l'hwnd di Sysmac ANCHE se la finestra e' nascosta
2. _sysmac_hwnd()       : fallback su _hwnd_per_titolo quando MainWindowHandle e' 0
3. _assicura_visibile() : ripristina una finestra nascosta (IsWindowVisible == false)
4. _focus_sysmac()      : la chiama prima di tentare il primo piano
5. _conta_rung_progetto(): somma i rung di tutte le sezioni ladder del progetto aperto
6. sysmac_import_ladder_xml(verifica=True): conta i rung prima/dopo e FALLISCE se
   non sono aumentati, invece di rispondere "Incollato" a vuoto.

Uso:  python patch_A.py            (applica)
      python patch_A.py --dry      (mostra solo cosa farebbe)
"""
import os, re, shutil, sys

SRV = r"C:\Users\tecni\Claude\sysmac-mcp\server.py"
BAK = SRV + ".bak_pre_visibile"

NUOVE_FUNZIONI = '''

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


def _cartella_progetto_aperto() -> str:
    """Cartella di lavoro del progetto APERTO, riconosciuta dal file
    <pid>.applicationlock. Copre sia l'archivio (Solution) sia i progetti
    aperti da file .smc2 (ProjFileTmp)."""
    for radice in (r"C:\\OMRON\\Data\\Solution", r"C:\\OMRON\\Data\\ProjFileTmp"):
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
                if any(f.endswith(".applicationlock") for f in os.listdir(p)):
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
'''

IMPORT_NUOVO = '''def sysmac_import_ladder_xml(xml: str, rung_row_y: int = 210,
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
'''


def main():
    dry = "--dry" in sys.argv
    s = open(SRV, encoding="utf-8").read()
    orig = s

    # --- 1) _sysmac_hwnd: fallback quando MainWindowHandle e' 0 --------------
    vecchio_hwnd = '''    if not out:
        raise RuntimeError("Sysmac Studio non in esecuzione (o senza finestra). Avvialo e apri un progetto.")
    return int(out)'''
    nuovo_hwnd = '''    if not out or out.strip() in ("", "0"):
        # finestra nascosta: MainWindowHandle vale 0, ma la finestra esiste
        h = _hwnd_per_titolo("Sysmac Studio")
        if h:
            return h
        raise RuntimeError("Sysmac Studio non in esecuzione (o senza finestra). Avvialo e apri un progetto.")
    return int(out)'''
    assert vecchio_hwnd in s, "patch 1: blocco _sysmac_hwnd non trovato"
    s = s.replace(vecchio_hwnd, nuovo_hwnd, 1)

    # --- 2) _focus_sysmac: rimettere a video una finestra nascosta -----------
    vecchio_focus = '''    SW_MINIMIZE, SW_RESTORE, SW_SHOW = 6, 9, 5
    if user32.IsIconic(h):'''
    nuovo_focus = '''    SW_MINIMIZE, SW_RESTORE, SW_SHOW = 6, 9, 5
    if not _assicura_visibile(h):
        raise RuntimeError(
            "la finestra di Sysmac Studio e' nascosta e non torna a video. "
            "Riportarla in primo piano a mano (o riavviare Sysmac) e riprovare.")
    if user32.IsIconic(h):'''
    assert vecchio_focus in s, "patch 2: blocco _focus_sysmac non trovato"
    s = s.replace(vecchio_focus, nuovo_focus, 1)

    # --- 3) nuove funzioni, inserite prima di _send_keys --------------------
    ancora = "\ndef _send_keys(keys: str) -> None:"
    assert ancora in s, "patch 3: ancora _send_keys non trovata"
    s = s.replace(ancora, NUOVE_FUNZIONI + ancora, 1)

    # --- 4) import con verifica dell'esito -----------------------------------
    i = s.find("def sysmac_import_ladder_xml(")
    assert i > 0, "patch 4: sysmac_import_ladder_xml non trovata"
    j = s.find("\n@mcp.tool", i)
    if j < 0:
        j = s.find("\ndef ", i + 10)
    assert j > i, "patch 4: fine funzione non trovata"
    s = s[:i] + IMPORT_NUOVO + s[j + 1:]

    print("modifiche: %d -> %d caratteri (%+d)" % (len(orig), len(s), len(s) - len(orig)))
    if dry:
        print("(dry run: nessuna scrittura)")
        return
    if not os.path.exists(BAK):
        shutil.copyfile(SRV, BAK)
        print("backup:", BAK)
    open(SRV, "w", encoding="utf-8").write(s)
    print("scritto:", SRV)


if __name__ == "__main__":
    main()
