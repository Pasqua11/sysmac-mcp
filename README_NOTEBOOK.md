# Replica dell'ambiente sul notebook — MCP `sysmac-ladder`

Stato di riferimento: PC fisso `victus-tecnico`, 29/08/2026.
Questo repository contiene **solo il server MCP sysmac-ladder** (server, generatori ST/ladder,
simulatore, libreria blocchi, indice istruzioni NJ/NX). Cosa *non* c'è: vedi l'ultima sezione.

---

## 1. Prerequisiti sul notebook

| Requisito | Versione sul PC fisso | Note |
|---|---|---|
| Python | 3.13.12 (`C:\Program Files\Python313\python.exe`) | Va bene qualsiasi 3.11+; annota il percorso reale, serve al punto 3 |
| Pacchetto Python | `mcp` 1.29.1 | **unica dipendenza esterna**: tutto il resto è libreria standard |
| Git | 2.53 | per il clone |
| Sysmac Studio | installato | necessario solo per le funzioni che pilotano la UI |
| Claude Cowork | installato | stesso account `trentalucas74@gmail.com` |

Installazione della dipendenza:

```powershell
& "C:\Program Files\Python313\python.exe" -m pip install mcp
```

Verifica rapida (deve stampare la versione senza errori):

```powershell
& "C:\Program Files\Python313\python.exe" -c "import mcp, sys; print(sys.version)"
```

## 2. Clone del repository

```powershell
git clone <URL-DEL-REPO> "C:\Users\<utente>\Claude\sysmac-mcp"
```

Consiglio: mantenere lo **stesso percorso** del PC fisso (`...\Claude\sysmac-mcp`) per non
dover adattare nulla. Il codice non contiene percorsi assoluti hard-coded: risolve tutto
rispetto alla propria cartella.

## 3. Registrare l'MCP in Claude

File da modificare sul notebook:
`C:\Users\<utente>\AppData\Roaming\Claude\claude_desktop_config.json`

Aggiungere dentro `"mcpServers"`:

```json
"sysmac-ladder": {
  "command": "C:\\Program Files\\Python313\\python.exe",
  "args": ["C:\\Users\\<utente>\\Claude\\sysmac-mcp\\server.py"]
}
```

Se serve anche il controllo del desktop Windows (usato da diverse skill), aggiungere:

```json
"windows-mcp": {
  "command": "C:\\Program Files\\Python313\\Scripts\\uvx.exe",
  "args": ["--native-tls", "windows-mcp", "serve"],
  "env": { "ANONYMIZED_TELEMETRY": "false" }
}
```

`uvx` si ottiene con `pip install uv`.

Poi **chiudere e riaprire Claude** (non basta chiudere la finestra: uscire dalla tray icon).

## 4. Verifica

In una sessione Cowork, chiedere a Claude di eseguire `sysmac_status`.
Risposta attesa: stato del server e se Sysmac Studio è aperto/agganciato.
Test offline (senza Sysmac aperto): generazione ST e simulazione, es. `sysmac_sim_test`.

## 5. Differenze note tra i due PC

- **Risoluzione/scala schermo diversa** → le funzioni che cliccano la UI di Sysmac possono
  richiedere una ricalibrazione. La procedura sta in `C:\Users\tecni\Claude\memory\collaudo-post-riavvio.md`
  e in `sysmac_scorciatoie.md` (non inclusi qui, vedi sotto).
- La cartella `out/` (file XML/ST generati) non è versionata: viene ricreata all'uso.
- I file `*.bak_*` non sono versionati: la cronologia ora è nei commit Git.

## 6. Cosa NON è in questo repository

| Elemento | Dove sta sul PC fisso | Come portarlo |
|---|---|---|
| Skill personali (price-research, leggi-email-outlook, vault-carica-commessa, layout-piastra-quadro, bilancio-aziendale, wordpress-avada-syntech, genera-documenti, converti-documenti-anydoc, manual-style-analyzer) | sincronizzate dall'account Claude | **automatiche**: entrando con lo stesso account compaiono sul notebook. Verificare con `/skills` |
| Plugin installati | account Claude / `.claude\plugins` | automatici con l'account |
| Memoria di lavoro Sysmac | `memory\` (parte attinente) | **inclusa nel repo**: cartella `_memoria\`, istruzioni in `_memoria\LEGGIMI.md` |
| Istruzioni globali | `C:\Users\tecni\.claude\CLAUDE.md` | da copiare a parte: percorsi server e regola prezzi, serve solo se sul notebook fai anche preventivi/offerte |
| Script prezzi/ricerca/email | `sacchi_cli.py`, `sacchi_to_db.py`, `rs_to_db.py`, `aggiorna_prezzi_2026.py`, `qc_prezzi.py`, `cerca_server.ps1`, `cerca_contenuto.ps1`, `leggi_email.ps1`, `sysmac_ui.ps1` | da copiare a parte |
| DB prezzi | `prezzi_fornitori.db` | **tenerne una copia sola** (server o PC fisso): due copie divergono e lo storico si sporca |
| Cookie/sessioni (`sacchi_cookies.json`, `chrome_sacchi_profile`) | locali | non trasferire: rigenerarli con un login sul notebook |
