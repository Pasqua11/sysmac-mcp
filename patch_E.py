# -*- coding: utf-8 -*-
"""patch_E.py - le cinque correzioni emerse dal programma da 90 rung (28/08/2026).

E1  Invoke-SysmacMenu prendeva il Text invece del MenuItem: 'File/Chiudi' non
    chiudeva niente. Ora filtra per ControlType MenuItem.
E2  sysmac_menu splittava solo su '/', ma il docstring di sysmac_ui documenta
    'File|Chiudi'. Ora accetta entrambi.
E3  sysmac_save non si accorgeva del dialogo "Salva progetto" che compare sui
    progetti gestiti come file: diceva "salvato" quando non lo era.
E4  sysmac_api.vars_offline rifiutava un percorso .smc2 (solo il tool MCP lo
    accettava). Ora lo riconosce e usa la strada giusta - quella da 0,1 s.
E5  Nuovo tool sysmac_apri_sezione: espande l'albero (i nodi si richiudono a
    ogni riapertura del progetto e il doppio clic non li apre) e apre la
    sezione ladder. Erano 18 s di clic a coordinate a ogni programma.
"""
import os
import re
import shutil

MCP = r"C:\Users\tecni\Claude\sysmac-mcp"
PS1 = r"C:\Users\tecni\Claude\sysmac_ui.ps1"
SRV = os.path.join(MCP, "server.py")
API = os.path.join(MCP, "sysmac_api.py")


def backup(p, tag):
    b = p + ".bak_" + tag
    if not os.path.exists(b):
        shutil.copy2(p, b)
    return b


def sostituisci(testo, vecchio, nuovo, etichetta):
    if vecchio not in testo:
        raise SystemExit("PUNTO DI AGGANCIO NON TROVATO: " + etichetta)
    if testo.count(vecchio) != 1:
        raise SystemExit("aggancio ambiguo (%d occorrenze): %s"
                         % (testo.count(vecchio), etichetta))
    return testo.replace(vecchio, nuovo)


# ---------------------------------------------------------------- E1  ps1
backup(PS1, "pre_menuitem")
ps = open(PS1, encoding="utf-8-sig").read()

ps = sostituisci(
    ps,
    "    $top = Find-UiElement -Root $main -Name $Path[0]\n",
    "    # deve essere il MenuItem: cercando per solo nome si prende il Text\n"
    "    # dell'etichetta ('_Chiudi'), che non ha InvokePattern e non fa nulla\n"
    "    $top = Find-UiElement -Root $main -Name $Path[0] -Type MenuItem\n"
    "    if (-not $top) { $top = Find-UiElement -Root $main -Name $Path[0] }\n",
    "E1 menu radice")

ps = sostituisci(
    ps,
    "        $item = Find-UiElement -Root $top -Name $Path[$i]\n"
    "        if (-not $item) { $item = Find-UiElement -Root $main -Name $Path[$i] }\n",
    "        $item = Find-UiElement -Root $top -Name $Path[$i] -Type MenuItem\n"
    "        if (-not $item) { $item = Find-UiElement -Root $main -Name $Path[$i] -Type MenuItem }\n"
    "        if (-not $item) { $item = Find-UiElement -Root $top -Name $Path[$i] }\n"
    "        if (-not $item) { $item = Find-UiElement -Root $main -Name $Path[$i] }\n",
    "E1 voce di menu")

open(PS1, "w", encoding="utf-8").write(ps)
print("E1 sysmac_ui.ps1: Invoke-SysmacMenu filtra per MenuItem")

# ------------------------------------------------------------ E2/E3/E5 server
backup(SRV, "pre_patchE")
s = open(SRV, encoding="utf-8").read()

s = sostituisci(
    s,
    '    voci = [p.strip() for p in path.split("/") if p.strip()]\n',
    '    # il separatore documentato in sysmac_ui e\' "|", quello storico "/":\n'
    '    # accettarli entrambi evita un fallimento silenzioso\n'
    '    voci = [p.strip() for p in re.split(r"[/|]", path) if p.strip()]\n',
    "E2 separatore menu")

s = sostituisci(
    s,
    '''def sysmac_save() -> str:
    """Salva il progetto (Ctrl+S)."""
    _focus_sysmac()
    _send_keys("^s")
    time.sleep(2)
    return "Salvataggio inviato (Ctrl+S)."''',
    '''def sysmac_save(file: str = "") -> str:
    """Salva il progetto (Ctrl+S).

    Sui progetti gestiti COME FILE (creati con "Gestisci nel file di progetto")
    Ctrl+S apre il dialogo "Salva progetto" invece di salvare, e finora il tool
    rispondeva "salvato" mentre il dialogo restava aperto. Ora il dialogo viene
    riconosciuto: con `file` valorizzato ci si scrive il percorso e si conferma,
    altrimenti si annulla e si segnala che il percorso serve."""
    _focus_sysmac()
    _send_keys("^s")
    time.sleep(2.5)
    albero = sysmac_ui_dump("", 4) or ""
    if "Salva progetto" not in albero:
        return "Salvataggio inviato (Ctrl+S)."
    if not file:
        _send_keys("{ESC}")
        return ("ATTENZIONE: il progetto e' gestito come FILE e Ctrl+S ha aperto "
                "il dialogo 'Salva progetto' (nulla e' stato salvato). "
                "Richiamare sysmac_save(file=r'...\\\\nome.smc2').")
    _uia("$w = Get-SysmacDialog 'Salva progetto'; "
         "$e = Find-UiElement -Root $w -Type Edit; "
         "if ($e) { $vp = $e.GetCurrentPattern("
         "[System.Windows.Automation.ValuePattern]::Pattern); "
         "$vp.SetValue(%s); 'SCRITTO' } else { 'CAMPO NON TROVATO' }"
         % _ps_quote(file))
    time.sleep(0.6)
    _uia("$w = Get-SysmacDialog 'Salva progetto'; "
         "[void](Invoke-UiButton -Root $w -Name 'Salva')")
    for _ in range(30):
        time.sleep(1)
        if "Salva progetto" not in (sysmac_ui_dump("", 3) or ""):
            return "Progetto salvato in %s" % file
    return "FALLITO: il dialogo 'Salva progetto' e' ancora aperto."''',
    "E3 sysmac_save")

# ---- E5: nuovo tool, inserito subito prima di sysmac_save
NUOVO = '''@mcp.tool()
def sysmac_apri_sezione(sezione: str = "", programma: str = "") -> str:
    """Apre una SEZIONE ladder nell'editor, espandendo l'albero da sola.

    Serve perche' alla riapertura di un progetto l'Explorer multivista torna
    tutto chiuso, il doppio clic sul nodo NON lo espande (va premuto il
    triangolino) e i clic a coordinate costavano ~18 s e diversi tentativi a
    vuoto. Qui si usa UI Automation: si cercano i TreeItem per nome, si
    espandono con ExpandCollapsePattern e si apre la sezione con un
    SelectionItem + doppio clic sul suo rettangolo.

    sezione   nome della sezione (vuoto = la prima sezione ladder trovata)
    programma nome del POU, se ce n'e' piu' di uno
    """
    percorso = ["Programmazione", "POUs", "Programmi"]
    if programma:
        percorso.append(programma)
    cmd = ["$w = Get-SysmacMainWindow"]
    for nome in percorso:
        cmd.append(
            "$n = Find-UiElement -Root $w -Name %s -Type TreeItem; "
            "if ($n) { $p = $null; "
            "if ($n.TryGetCurrentPattern([System.Windows.Automation.ExpandCollapsePattern]::Pattern, [ref]$p)) "
            "{ $p.Expand(); Start-Sleep -Milliseconds 400 } }" % _ps_quote(nome))
    cmd.append("'ESPANSO'")
    _uia("; ".join(cmd))
    time.sleep(0.5)

    if sezione:
        filtro = "-Name %s " % _ps_quote(sezione)
    else:
        filtro = ""
    out = _uia(
        "$w = Get-SysmacMainWindow; "
        "$s = Find-UiElement -Root $w %s-Type TreeItem; "
        "if ($s) { $r = $s.Current.BoundingRectangle; "
        "'{0};{1}' -f [int]($r.X + $r.Width/2), [int]($r.Y + $r.Height/2) } "
        "else { 'NONTROVATA' }" % filtro)
    coord = [r for r in (out or "").splitlines() if ";" in r]
    if not coord:
        return ("FALLITO: sezione %r non trovata nell'albero. %s"
                % (sezione or "(prima ladder)", (out or "").strip()[:200]))
    x, y = [int(v) for v in coord[-1].split(";")[:2]]
    _click(x, y, "left", True)
    time.sleep(3)
    return "Sezione %s aperta (doppio clic in %d,%d)." % (sezione or "ladder", x, y)


'''
s = sostituisci(s, "@mcp.tool()\ndef sysmac_save(", NUOVO + "@mcp.tool()\ndef sysmac_save(",
                "E5 nuovo tool sysmac_apri_sezione")

if "\nimport re" not in s and "\nimport re\n" not in s:
    s = s.replace("\nimport os\n", "\nimport os\nimport re\n", 1)

open(SRV, "w", encoding="utf-8").write(s)
print("E2 sysmac_menu accetta '/' e '|'")
print("E3 sysmac_save riconosce il dialogo 'Salva progetto'")
print("E5 nuovo tool sysmac_apri_sezione")

# ---------------------------------------------------------------- E4  api
backup(API, "pre_smc2")
a = open(API, encoding="utf-8").read()

a = sostituisci(
    a,
    '''    """Crea variabili scrivendo i file di progetto. Il progetto deve essere
    CHIUSO in Sysmac. Accetta ("NOME","TIPO") oppure {"nome":..,"tipo":..}."""
    return slwd.crea_variabili(progetto_nome, globali=globali, interne=interne,
                               esterne=esterne, programma=programma)''',
    '''    """Crea variabili scrivendo i file di progetto. Il progetto deve essere
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
                               esterne=esterne, programma=programma)''',
    "E4 vars_offline con .smc2")

open(API, "w", encoding="utf-8").write(a)
print("E4 sysmac_api.vars_offline accetta un percorso .smc2")

# ------------------------------------------------------------------ verifica
import py_compile
for p in (SRV, API):
    py_compile.compile(p, doraise=True)
print("\nsintassi Python OK per server.py e sysmac_api.py")
