# Piano: ridurre i tempi di scrittura nella UI di Sysmac

Scritto il 28/08/2026 dopo aver riletto `server.py` (60 KB, 64 funzioni), `sysmac_api.py` e
`sysmac_ui.ps1` (24 funzioni UIA). **Nessuna modifica ancora fatta.**

Il generatore ladder non è più il collo di bottiglia: 17 rung generati in 3 minuti contro i 50
minuti di 5 rung disegnati a mano. Il tempo se ne va ora nel **pilotaggio della GUI**.

---

## Intervento A — Finestra sempre visibile e import che verifica l'esito
**Costo attuale:** 79 rung incollati nel vuoto, ~15 minuti di diagnosi, poi 6 ripristini manuali
via PowerShell nel corso della sessione.

**Causa individuata nel codice:**

- `_sysmac_hwnd()` prende l'handle da `Get-Process | Where MainWindowHandle -ne 0`. Quando la
  finestra è **nascosta** (non minimizzata) quel valore può essere 0: l'handle si perde.
- `_focus_sysmac()` gestisce solo `IsIconic` (minimizzata). Il caso `IsWindowVisible == false` non
  è previsto, quindi il focus "riesce" su una finestra invisibile e i tasti vanno altrove.
- `sysmac_import_ladder_xml()` restituisce sempre la stringa "Incollato", senza controllare nulla.

**Modifiche**

| File | Punto | Cosa cambia |
|---|---|---|
| `server.py` | `_sysmac_hwnd()` | se `MainWindowHandle` è 0, fallback su `_find_window("Sysmac Studio")` (funzione già presente) |
| `server.py` | `_focus_sysmac()` | nuova `_assicura_visibile(h)`: se `IsWindowVisible(h)` è falso → `ShowWindow(SW_RESTORE)` + `ShowWindow(SW_SHOW)`; chiamata prima del giro di tentativi di primo piano |
| `server.py` | `sysmac_import_ladder_xml()` | nuovo parametro `verifica=True`: salva (Ctrl+S), rilegge dal disco il file della sezione e conta i rung prima/dopo; se non sono aumentati **solleva un errore** invece di dire "Incollato" |

**Come lo verifico:** nascondo la finestra con `ShowWindow(SW_HIDE)` e lancio un import; deve
riportare la finestra a video e incollare, oppure fallire con un messaggio chiaro — mai rispondere
"Incollato" a vuoto.

*Tempo stimato: 30 min + 15 di verifica.*

---

## Intervento B — Testo sempre dagli appunti, e guardia sul CapsLock
**Costo attuale:** CapsLock attivo → `FB_Power_Trasl` digitato come `fb_pOWER_tRASL`, blocco da
cancellare e rifare (~10 min). In un altro caso il primo carattere è andato perso: `Ritardo` → `tardo`.

**Nel codice c'è già la soluzione, ma è usata in un solo punto:** `_incolla()` (clipboard + Ctrl+V)
viene chiamata solo da `apri_progetto`. Tutto il resto passa da `_send_keys` → SendKeys.

**Modifiche**

| File | Punto | Cosa cambia |
|---|---|---|
| `server.py` | nuova `_capslock_off()` | legge `[Windows.Forms.Control]::IsKeyLocked('CapsLock')`; se attivo invia `{CAPSLOCK}`. Chiamata all'inizio di `_send_keys` (con cache: una sola verifica ogni N secondi, per non pagare un PowerShell a ogni tasto) |
| `server.py` | `sysmac_send_keys()` e `sysmac_ui(azione="tasti")` | se il testo **non** contiene caratteri di controllo SendKeys (`{ } ^ % + ~`), usa `_incolla()` invece di SendKeys |
| `server.py` | nuova azione `sysmac_ui(azione="scrivi")` | scrive sempre via appunti, per i casi in cui serve il testo letterale |

**Come lo verifico:** attivo il CapsLock a mano, scrivo `FB_Power_Trasl` in un campo del ladder e
controllo che arrivi esatto.

*Tempo stimato: 20 min + 10 di verifica.*

---

## Intervento C — Dialoghi pilotati per nome, non a coordinate
**Costo attuale:** le tre librerie sono costate ~50 chiamate, quasi tutte click a pixel con uno
screenshot di verifica dopo ognuno. Ogni dialogo nuovo richiede una tornata di prove per trovare
le coordinate, e le coordinate valgono solo a finestra massimizzata.

**Cosa c'è già in `sysmac_ui.ps1`:** `Find-UiElement`, `Invoke-UiButton`, `Invoke-UiElement`,
`Get-UiGridRows`, `Select-UiTreeRow`, `Expand-UiTree`, `Get-SysmacDialog`.
**Cosa manca:** scrivere in un campo, spuntare una casella, scegliere da una tendina, selezionare
una riga di tabella per contenuto.

**Modifiche**

| File | Aggiunta | Pattern UIA |
|---|---|---|
| `sysmac_ui.ps1` | `Set-UiValue -Root -Name -Value` | `ValuePattern.SetValue` — campi di testo |
| `sysmac_ui.ps1` | `Set-UiToggle -Root -Name -On` | `TogglePattern` — caselle di spunta |
| `sysmac_ui.ps1` | `Select-UiComboItem -Root -Name -Item` | `ExpandCollapsePattern` + `SelectionItemPattern` — tendine (es. *Tipo = Progetto libreria*) |
| `sysmac_ui.ps1` | `Select-UiGridRow -Root -Text` | selezione riga per contenuto — tabelle variabili, riferimenti libreria |
| `server.py` | nuovo tool `sysmac_dialogo(...)` | una sola chiamata: `titolo`, `campi="Nome=SYNTECH_FB_Cappa; Società=SYNTECH"`, `caselle="Disattiva visualizzazione sorgente=off"`, `tendine="Tipo=Progetto libreria"`, `pulsante="OK"` |

**Effetto atteso:** *Impostazione libreria* passa da ~10 chiamate con coordinate a **1**; lo stesso
vale per *Proprietà progetto* e *Riferimento libreria*.

**Come lo verifico:** rifaccio l'impostazione di una libreria su una copia con una sola chiamata e
confronto il `.slr` prodotto con quello di oggi.

*Tempo stimato: 2 h + 30 min di verifica.* È il più lungo, ed è quello che rende ripetibile tutto
il lavoro sui dialoghi.

---

## Intervento D — Variabili senza il giro chiudi → scrivi → riapri
**Costo attuale:** 4 cicli da 2-3 minuti l'uno nella sola sessione della batteria (~10 min), più il
rischio che ogni riapertura lasci la finestra nascosta (vedi A).

**Situazione:** `sysmac_paste_vars` esiste già e gestisce il dialogo "Risolvi conflitti", ma
pretende che la tabella sia **già aperta e scorrita in fondo**, e vuole le coordinate della riga
(`row_x=353, row_y=304`). Per questo ho preferito `vars_offline`, che però impone di chiudere il
progetto.

**Modifiche**

| File | Punto | Cosa cambia |
|---|---|---|
| `server.py` | nuovo tool `sysmac_vars(tabella, tsv)` | fa il giro completo senza coordinate: apre la tabella dall'albero (`Select-UiTreeRow`), sceglie la scheda *Interne/Esterne*, va in fondo (Ctrl+End), crea la riga (menu contestuale → *Crea nuovo*, via UIA), incolla, elimina la riga vuota residua |
| `server.py` | `sysmac_paste_vars` | resta come primitiva di basso livello |

Dipende da C per le funzioni UIA di griglia.

**Come lo verifico:** creo 20 variabili globali in un progetto aperto e le rileggo con
`vars_globali()`; devono esserci tutte, senza chiudere il progetto.

*Tempo stimato: 45 min + 15 di verifica.*

---

## Ordine, tempi, avvertenze

| Ordine | Intervento | Tempo | Perché in questa posizione |
|---|---|---|---|
| 1 | **A** finestra + esito import | 45 min | è il guasto che ha fatto perdere più tempo, ed è indipendente |
| 2 | **B** appunti + CapsLock | 30 min | rapido, elimina un'intera classe di errori silenziosi |
| 3 | **C** helper UIA dialoghi | 2 h 30 | il più lungo, ma abilita D e tutto il lavoro futuro sui dialoghi |
| 4 | **D** variabili a progetto aperto | 1 h | usa le funzioni introdotte in C |

**Totale ≈ 5 ore**, verifiche incluse.

**Due avvertenze operative:**

1. **Dopo ogni modifica a `server.py` va riavviata l'app Claude**: il server MCP viene caricato
   all'avvio. Conviene quindi raggruppare le modifiche e riavviare una volta per intervento, non
   per singola patch.
2. **Backup progressivi** come già fai: `server.py.bak_pre_visibile`, `.bak_pre_clipboard`,
   `.bak_pre_dialoghi`, `.bak_pre_vars`. Idem per `sysmac_ui.ps1`.

## Fuori perimetro ma sempre aperto
`AryMax` e `AryMin` restano da campionare da un progetto che li usa (10 minuti), e
`MC_Restart1S` richiede la libreria Omron 1S agganciata al progetto.
