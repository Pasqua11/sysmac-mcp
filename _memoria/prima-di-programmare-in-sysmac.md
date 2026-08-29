# PRIMA di programmare in Sysmac: usa il generatore, non la GUI

Nota scritta il 27/08/2026 dopo un errore costato ~2 ore.

## Cosa è successo
Richiesta: aggiungere i blocchi di movimentazione assi alla commessa `Commessa_Movimentazione`.
Ho disegnato 5 box FB (MC_Power, MC_Home, MC_Reset, MC_MoveAbsolute, MC_Stop) **a mano nella GUI**,
tasto per tasto, con uno screenshot di verifica dopo ogni conferma: ~50 minuti per 5 rung.
Gli altri 17 rung, generati via XML e incollati, sono costati **3 minuti**.

Il punto: `C:\Users\tecni\Claude\sysmac-mcp\` conteneva **già** un generatore completo e collaudato,
e `memory\` conteneva le note che lo spiegano. Non le ho lette prima di iniziare.

## Regola operativa
All'inizio di QUALSIASI attività su Sysmac Studio, prima di toccare la GUI:

1. Leggere `C:\Users\tecni\Claude\CLAUDE.md` e l'indice di `C:\Users\tecni\Claude\memory\`.
2. In particolare:
   - `memory\catena-import-ladder-chiusa.md` — flusso spec JSON → ladder compilato (~4 min per 15 rung)
   - `memory\convertitore-rung-spec.md` — progetto esistente → spec JSON → ladder rigenerato
   - `memory\metodo_programmazione_luca.md` — architettura e convenzioni dei progetti SYNTECH
   - `memory\registrazione-variabili-in-blocco.md` — variabili via TSV + `sysmac_paste_vars`
3. Disegnare a mano nella GUI **solo** un tipo di blocco che non esiste ancora in
   `sysmac-mcp\templates\` e che non è ricavabile da `pins.json`, e subito dopo campionarlo
   con `sysmac_copy_rung_to_file` per non doverlo rifare mai più.

## Flusso corretto (da `catena-import-ladder-chiusa.md`)
1. Scrivere la **spec JSON** (sintassi in testa a `ladder_gen.py`): `chain`, `or`, `out`, `fb`, `p`.
2. `python ladder_gen.py spec.json` → `out\sec_<Sezione>.xml` + `out\vars.txt`
   (la cartella `out_dir` deve già esistere).
3. Variabili in blocco: `sysmac_paste_vars(vars.txt)` — gestisce il dialogo "Risolvi conflitti".
4. Import rung: `sysmac_import_ladder_xml` / `sysmac_paste_file` sul rung selezionato.
5. `sysmac_compile_text` → gli errori residui sono solo assi/gruppi assi non registrati:
   `sysmac_register_from_error` (il default del dialogo, "Variabile esterna", è già quello giusto).
6. `sysmac_save`.

**Validare sempre l'XML prima dell'import**: se non è well-formed Sysmac lo rifiuta in silenzio,
dicendo "incollato" senza incollare nulla (caso storico: `typeName="<"` non escapato).

## Cosa il generatore già conosce
`templates\`: TON, MOVE, =, >, @Inc, Get100msClk, MC_Power, MC_Home, MC_MoveAbsolute,
MC_GroupEnable, MC_GroupDisable, MC_GroupReset, MC_Reset, MC_Stop, MC_MoveJog,
MC_MoveLinearAbsolute/Relative, ST inline, clock movimenti.
`pins.json` / `pin_reali.json`: firme dei pin di **91 tipi** ricavate da 11.766 blocchi reali,
FB custom di Luca inclusi (Contatore, Controllo_EV, Ritardo, INV*_3G3M1, MTCP_Server_NJNX...).

Quindi: per i blocchi motion **non serve disegnare niente a mano**.

## Trappole GUI da ricordare (se la GUI è inevitabile)
- **Controllare il CapsLock**: se è attivo, SendKeys scrive i nomi invertiti (`FB_Power_Trasl`
  diventa `fb_pOWER_tRASL`) e il blocco va rifatto. Per i nomi conviene comunque la clipboard.
- Finestra Sysmac non visibile: `ShowWindow(SW_RESTORE)` sull'hwnd, non basta il focus.
- Tabelle variabili: creare la riga con tasto destro → *Crea nuovo*, poi **ESC**, poi tasto destro
  sul **selettore di riga** → *Incolla*. Con la cella in editing il Ctrl+V finisce dentro la cella.
- Nel rung: per inserire un elemento dopo un contatto, selezionare il contatto e premere `{RIGHT}`
  finché la selezione è sulla cella vuota; i tasti C/D/O/I/F vanno in minuscolo.
- Nome istanza di un FB: click sul box → `{ENTER}` (edita il tipo) → `{ENTER}` (passa all'istanza).

## Cartella ripulita
I 5 template duplicati che avevo campionato il 27/08 (`rung_MC_*.xml`, `rung_MOVE.xml`) sono
stati spostati in `templates\_duplicati_2026-08-27\` per non alterare il caricamento del
generatore: i corrispondenti `mc_*.xml` erano già presenti. Si possono eliminare.
