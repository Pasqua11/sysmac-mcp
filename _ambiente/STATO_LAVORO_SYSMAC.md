# Stato lavoro — server MCP Sysmac veloce (avviato 26/08/2026 notte)

Obiettivo di Luca: rendere il server MCP il piu' veloce possibile a **scrivere
codice ladder** e a **debuggare col simulatore**.

File di riferimento: `C:\Users\tecni\Claude\sysmac-mcp\` (server.py, ladder_gen.py,
rung2spec.py, sysmac_project.py) e `C:\Users\tecni\Claude\sysmac_ui.ps1`.

---

## FATTO

1. **Layer UI Automation** nel server MCP (`_uia()` + `sysmac_ui.ps1`):
   `sysmac_focus`, `sysmac_menu`, `sysmac_button`, `sysmac_ui_dump`,
   `sysmac_errors`, `sysmac_compile_text`. Tutti verificati dal vivo.
   - `sysmac_errors` legge il pannello Compila come testo (pannello trovato per
     AutomationId `buildWindowsViewWindow`), contatori + tutte le righe,
     scorrendo la griglia virtualizzata. Verificato su 2 errori veri e 60 avvisi.
   - `sysmac_focus` corretto con 3 tentativi progressivi (foreground lock di
     Windows): diretto, SW_RESTORE, AttachThreadInput.

2. **Lettura diretta dei progetti dal disco** — la scoperta piu' importante.
   Sysmac tiene i progetti in `C:\Omron\Data\Solution\<guid>\`:
   - `<guid>.oem` = albero entita' XML (Program / PouBody Ladder / Variables...)
   - `<id-sezione>.xml` = **JSON, un rung per riga** (BOM UTF-8 in testa)
   - tipi di cella osservati su 1475 sezioni di 112 progetti:
     `LD` contatto (Not/Up/Dwn), `ST` bobina (S=SET, RS=RESET, Not=NOT),
     `FB` blocco funzione (Name/Var/In/Out), `F` funzione, `IST` ST in linea,
     `PRM` parametro (Arg/Type/Var/IO), `PF` pin power flow, `HL` link.
   - `sysmac_project.py` decodifica tutto questo in testo leggibile.
   - Nuovi tool: `sysmac_projects`, `sysmac_sections`, `sysmac_read`,
     `sysmac_find_var`. Nessuno richiede Sysmac aperto ne' screenshot.

3. Ricerca su GitHub / web: non esiste una libreria pronta per il ladder Omron.
   Il PLCopen XML (IEC 61131-10) e' gia' sbloccato su questa installazione
   (Strumenti > IEC 61131-10 XML, scorciatoia Ctrl+Alt+X assegnata stanotte).
   `ladder_gen.py` (gia' esistente) genera il formato clipboard proprietario da
   una spec JSON compatta: resta la via di scrittura piu' veloce e sicura.

---

## DA FARE (in ordine)

4. **Debug col simulatore** — il pezzo mancante. Serve calibrare sulla finestra
   reale (Sysmac deve essere aperto con un progetto):
   - struttura UIA della scheda Monitoraggio (Alt+4) e della tabella variabili
   - `Get-SysmacWatchRows` (lettura valori live come testo)
   - `Set-SysmacWatchValue` (forzatura valore) e `Add-SysmacWatchVar`
   - tool MCP: `sysmac_watch`, `sysmac_watch_set`, `sysmac_watch_add`
   - ciclo di debug: avvia sim -> forza ingressi -> leggi valori -> confronta
     con la logica letta da disco (`sysmac_read`) -> concludi

5. **Scrittura diretta su disco** (potenziale grande accelerazione, DA VERIFICARE
   con prudenza): generare il JSON dei rung e scriverlo nel file di sezione a
   progetto CHIUSO. Prima di provarlo servono: copia di sicurezza della cartella
   progetto, prova su un progetto scratch, verifica che Sysmac non invalidi
   manifest/hash. Se non regge, resta il percorso clipboard (gia' funzionante).

6. Eventuale `spec` <-> `JSON di disco`: convertitore diretto, per evitare del
   tutto il passaggio dal ladderSnippetXML (che e' 5-6 volte piu' voluminoso).

---

## REGOLE DI SICUREZZA SEGUITE

- Niente scritture dentro `C:\Omron` (per ora sola lettura).
- Backup prima di ogni modifica ai file di Luca (`.bak_*`).
- Il progetto aperto non e' mai stato salvato da me.
