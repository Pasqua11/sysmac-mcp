# Automazione Sysmac Studio via Claude (windows-mcp) — procedure testate

Aggiornato: 25/08/2026 — sessione "Sysmac Studio motor start-stop program" (progetto Claude "Sysmac Studio con Claude").

## Prerequisiti CRITICI (senza questi i click "spariscono")
1. **Sysmac Studio si auto-elevata ad amministratore** (l'exe si rilancia elevato, verificato: processo figlio elevato anche da parent non elevato). Windows/UIPI scarta l'input sintetico verso finestre elevate.
   → **L'app Claude desktop DEVE essere avviata "Esegui come amministratore"**, altrimenti nessun click/tasto arriva a Sysmac.
2. **Notifiche Norton** (toaster in alto a destra) rubano il focus e mangiano i click: chiuderle subito (finestra proc NortonUI, WM_CLOSE) o silenziarle.
3. Con **Chrome Remote Desktop attivo**, i movimenti del mouse dell'utente sovrascrivono quelli iniettati: chiedere di non toccare mouse/tastiera e ridurre a icona la finestra Claude sul PC.
4. `SetCursorPos` di windows-mcp è inaffidabile in questo scenario: usare **SendInput** (P/Invoke, coordinate assolute 0..65535 scalate su 1919x1079) per click/move; `SendKeys` per tastiera. Focus con `SetForegroundWindow(hwnd)` via P/Invoke sul MainWindowHandle del processo.
5. Screenshot: windows-mcp Screenshot funziona sempre; i tool computer_* del bridge Claude possono andare in timeout (se accade: riavviare l'app Claude sul PC).

## Nuovo progetto (Sysmac 1.66 ITA)
- Pagina iniziale → "Nuovo progetto" (click ~127,150) → campo Nome (~1219,167) → periferica default NJ501-1500 v1.70 va bene per simulazione.
- Bottone **"Crea"** è piccolo (rect ~1381,919 40x24): click SendInput a ~1401,931. Trovabile anche via UIAutomation (nome "Crea") ma Invoke() UIA NON preme il bottone WPF — serve il click reale.
- Progetto aperto quando il titolo diventa "<nome> - new_Controller_0 - Sysmac Studio (32bit)".

## Editing ladder (editor Sezione0, tasti rapidi)
- Doppio click su Sezione0 nell'Explorer (in Programmazione → POUs → Programmi → Programma0).
- Selezionare cella sul rung, poi: **C** = contatto N.O., **D** = contatto N.C., **O** = bobina/uscita, **T** = linea collegamento.
- Ramo parallelo (auto-ritenuta): selezionare il contatto → menu **Inserisci → Componenti circuito → "OR con ingresso N.O."** (aggiunge il contatto in parallelo già cablato). In alternativa tasto **W** (parallelo sotto) / Shift+W (sopra).
- Dopo l'inserimento si apre subito il campo nome variabile: digitare il nome → **Enter** → dialogo "Seleziona il tipo di variabile" → "Variabile interna" o "Variabile globale".
- **NON premere ESC** dopo la conferma: annulla il nome e lascia la cella "Immetti variabile" → errore di compilazione "Non è stato immesso un parametro". Per chiudere il tooltip commento cliccare su un'area vuota dell'editor.
- Errore cella vuota nel parallelo: Ctrl+Z ripetuto fino a tornare alla serie pulita, poi rifare il ramo con "OR con ingresso N.O." in un colpo solo.

## Compilazione e simulazione
- **F8** = Compila controllore (Progetto → Compila Controllore). Pannello Compila: 0 errori/0 avvisi.
- **Simulazione → Esegui (F5)**: avvia il simulatore integrato, pannello "Stato del controllore" = ONLINE / Modalità RUN, ladder in monitor (verde = alimentato).
- Forzare ingressi: **tasto destro sul contatto → Set/Reset → Set** (TRUE) o **Reset** (FALSE). Le voci grigie indicano lo stato già attivo.
- Test start/stop eseguito con successo: Start=Set → motore ON; Start=Reset → resta ON (auto-ritenuta); Stop=Set → OFF; Stop=Reset → resta OFF.

## Schema start/stop usato
Rung 0: [PB_Start N.O. || Motore N.O. (ritenuta)] --- PB_Stop N.C. --- (Motore)
Variabili: PB_Start, PB_Stop, Motore — BOOL, interne. Progetto: StartStop_Motore.

## Idee per velocizzare (v. anche doc nel progetto Claude)
- Sequenze tastiera batch senza screenshot intermedi (C→nome→Enter→click tipo var→D→nome→Enter→...): 1 rung in ~10 s.
- Copia/incolla rung via clipboard (formato proprietario Sysmac — vedi esperimento in progetto).
- Per logica complessa: POU in **ST** (testo puro, si digita con SendKeys in un colpo) e richiamo dal ladder, o inline ST.

## METODO VELOCE (SCOPERTA 25/08/2026): generazione rung via clipboard XML
Sysmac Studio copia/incolla i rung ladder negli appunti nel formato **"ladderSnippetXML"** — XML puro, leggibile e GENERABILE.
**Ricetta testata end-to-end (rung con parallelo incollato e compilato 0 errori):**
1. Generare l XML del rung (template: memory/ladder_snippet_rung0.xml = start/stop con auto-ritenuta; basta sostituire i variableName).
   Struttura: <Rungs><RungXML><LadderElement ladderElementType="Contact|Coil|Edge|Connection" .../></RungXML></Rungs>.
   - Contact: variableName, inverted="true" per N.C., ConnectionPoint input/output con Edge.
   - Coil: variableName, set/reset per bobine SET/RESET.
   - Edge: sourceID/targetID collegano i ConnectionPoint (instanceID esadecimali qualsiasi, purche coerenti).
   - Connection IsLeftPowerRail/IsRightPowerRail = barre di alimentazione; Connection intermedi = nodi dei paralleli.
2. Metterlo negli appunti: script **C:\Users\tecni\Claude\ladder_paste.ps1** (SetData "ladderSnippetXML").
3. In Sysmac: selezionare un rung (click sul numero di riga) e **Ctrl+V** → il rung compare completo, rami paralleli inclusi.
4. Variabili nuove: risultano "non registrate" → click sull elemento → **Ctrl+Alt+R** → dialogo "Variabile interna/globale" → scegliere. (In alternativa registrarle prima nella tabella variabili.)
5. **F8** per compilare.
Nota: per incollare serve simulazione FERMA (Shift+F5 arresta). Copiare un rung esistente (selezione + Ctrl+C) e leggere gli appunti e il modo per ottenere altri template (timer, contatori, FB...).

## SERVER MCP "sysmac-ladder" (creato 25/08/2026)
Percorso: **C:\Users\tecni\Claude\sysmac-mcp\server.py** (Python 3.13 + SDK mcp, stdio).
Registrato in %APPDATA%\Claude\claude_desktop_config.json (backup .bak_20260825). Dopo modifiche alla config: riavviare l'app Claude **come amministratore** (obbligatorio: Sysmac e elevato).
Nelle sessioni Cowork i tool appaiono come mcp__remote-devices__sysmac-ladder__*.

### Tool disponibili
- sysmac_status() — processo/titolo (= progetto aperto)
- sysmac_import_ladder_xml(xml, rung_row_y=210) — clipboard ladderSnippetXML + focus + selezione rung + Ctrl+V (il rung entra SOTTO quello selezionato). Richiede editor ladder aperto e simulazione ferma.
- sysmac_copy_rung(rung_row_y) — copia il rung selezionato e RESTITUISCE il suo XML (per creare template da circuiti disegnati a mano)
- sysmac_register_variable(x, y, scope) — click elemento + Ctrl+Alt+R + Invio(interna)/Tab+Invio(globale)
- sysmac_register_from_error(error_row_y=815) — PIU AFFIDABILE: doppio click sulla prima riga errore del pannello Compila (salta all elemento) + Ctrl+Alt+R + Invio
- sysmac_compile(wait_seconds=12) — F8 + screenshot barra "N Errori / M Avvisi"
- sysmac_save() / sysmac_sim("start"|"stop") — Ctrl+S / F5, Shift+F5
- sysmac_click / sysmac_send_keys / sysmac_screenshot — primitive generiche di fallback

### Flusso "programma completo in pochi secondi" (testato: rung Luce importato e compilato 0 errori)
1. Claude genera l XML dei rung (template in memory/ladder_snippet_rung0.xml)
2. sysmac_import_ladder_xml(xml) — un rung o piu rung per volta
3. sysmac_compile() → per ogni errore "variabile non registrata": sysmac_register_from_error() → ricompilare
4. sysmac_save(), eventuale sysmac_sim("start") per il collaudo
Test CLI senza MCP: python server.py selftest | python server.py import file.xml
Lezione appresa: la registrazione variabili con click a coordinate fisse puo mancare l elemento; la via robusta e partire dagli errori di compilazione (doppio click sulla riga = salto all elemento gia selezionato).

## LIBRERIA CIRCUITI (25/08/2026)
Analizzati 102 progetti reali (18.860 rung) direttamente da C:\OMRON\Data\Solution (il ladder e' leggibile OFFLINE: file <guid>.xml con un JSON per rung; nomi sezioni nel file .oem, nome progetto nel .manifest).
Libreria circuiti standard SYNTECH: **C:\Users\tecni\Claude\sysmac-mcp\library\LIBRERIA.md** (+ catalog.json completo, esemplari.json, stats.txt). Copia nel progetto Claude: claude/libreria-circuiti-syntech.md.

## Scoperte 26/08/2026 — pipeline veloce (test Ascensore_3Piani: 5 min 10 s editing totale)
- **Pre-registrazione variabili via paste TSV nella tabella variabili locali: FUNZIONA.** Formato riga (TSV, righe separate da CRLF): `Nome<TAB>Tipo<TAB>ValoreIniziale<TAB>AT<TAB>False<TAB>False<TAB>Commento`. Mettere il testo negli appunti (SetText normale), aprire il pannello "Variabili" nell editor ladder, selezionare la riga con il grip a sinistra e Ctrl+V: tutte le righe entrano in un colpo, commenti inclusi. Se il click sull area vuota crea una riga vuota in edit: ESC, selezionarla dal grip, tasto destro > Elimina. Elimina il ciclo register_from_error: compilazione 0 errori al primo colpo.
- **Set/Reset rapidi in simulazione**: selezionare il contatto (click) poi Ctrl+Shift+J = Set, Ctrl+Shift+K = Reset. Molto piu veloce del menu contestuale.
- **Pausa simulatore**: Ctrl+Alt+Break mette in pausa (congela i TON), F5 riprende. Indispensabile per fotografare stati brevi (finestre di pochi secondi). Il pulsante pausa del pannello Simulazione a coordinate fisse e inaffidabile.
- **Generatore XML rung**: script che genera ladderSnippetXML da 2 topologie (serie N contatti + coil; parallelo 2 rami + serie NC + coil) partendo dal template start/stop. Coprono memorie con auto-ritenuta, consensi, interblocchi. 12 rung in un solo paste. Nota: ogni contatto/coil/nodo ha 2-3 ConnectionPoint; gli Edge collegano CP a CP; id esadecimali univoci.
- Tempi ascensore 3 piani (12 rung, 18 var): progetto nuovo 1 min, paste variabili ~1 min, paste 12 rung ~30 s, F8 0 errori + salva ~1 min. Confronto: semafori (10 rung, 12 var, con register_from_error) = 19 min. Guadagno ~4x.

## Scoperte 26/08/2026 sera — generazione FB/motion via XML (test Movimentazione_2Assi, riuscito)
- **Generatore ladderSnippetXML esteso a FB/Funzioni/ST inline: FUNZIONA.** Struttura FB: 1 ConnectionPoint per pin visibile (ordine = PinViewModel, input poi output; PowerPin=true su Execute/In e Done/Q); ogni pin non-power si collega via Edge a un elemento `Variable` (nome vuoto se pin non usato; il pin InOut Axis ha Variable sia in ingresso che in uscita). Funzioni: ladderElementType="Function", IsPolynomial=true per confronti. ST inline: ladderElementType="InlineStructuredTextServices.InsertInlineST" con text= XML-escaped e textEntityID=GUID nuovo. Template campionati in sysmac-mcp\templates\ (ton, mc_power, mc_home, mc_moveabs, clock_movimenti, confronto_eq, ist_inline).
- **LIMITE: niente rami multipli in USCITA senza nodo** — piu edge dallo stesso ConnectionPoint per bobine/FB paralleli generano "Dati del rung N danneggiati" all'import. Workaround collaudato: un rung per uscita (duplicando i consensi). Il parallelo in INGRESSO (2 contatti + nodo merge) funziona.
- **Variabili globali nel programma**: le variabili globali (es. assi MC_X/MC_Y) vanno registrate come ESTERNE nel programma; il paste TSV nella tabella Esterne NON funziona e nemmeno la digitazione diretta — usare la registrazione dall errore di compilazione (doppio click errore + Ctrl+Alt+R + Invio), che le inserisce corrette con Costante spuntata. Una registrazione risolve tutti gli usi della stessa variabile.
- **Assi VIRTUALI in simulazione**: Tipo asse default = "Asse servoazionamento virtuale" (nessun drive EtherCAT necessario); metodo homing default "Posizione zero preimpostata" OK. ATTENZIONE: DrvStatus.* (ServoOn, MainPower...) NON si attiva sugli assi virtuali (non esiste il drive) — per consensi e ready usare **MC_x.Status.Ready** (stato MC dell asse) come fa Cappa Ceramiche in Sequenze R0. DrvStatus.Ready invece risulta TRUE e puo stare nell Enable di MC_Power.
- Homing e movimenti sugli assi virtuali sono rapidi/istantanei: il collaudo delle catene MOV va letto dagli effetti (Mem_*, End_*, posizioni) piu che inseguito a screenshot.
- Creazione progetto con assi: aggiungi assi (right-click Impostazione asse > Aggiungi > Asse controllo assi), rinomina (right-click > Rinomina, digitare con windows-mcp Type). Sezioni: right-click sezione > Inserisci sopra > Sezione (NON su Programma0: crea un programma intero); riordino con Sposta su/giu. I click sui menu contestuali di Sysmac vanno fatti con windows-mcp Click (il focus-check del server sysmac-ladder fallisce quando il menu e in primo piano).
- Test completo Movimentazione_2Assi: 4 sezioni (Marcia, Sequenze, Trasf_Dati, Movimentazione), 45 rung, 74 variabili, 2 assi virtuali, catena MOV1..MOV7 con pinza, blending MOV5/5A, arbitraggio a slot, scheduler-free. 2 cicli completi (A->V1, B->V2) collaudati in simulazione con memorie vasca corrette. Editing ~44 min inclusi 2 fix; a regime stimato ~15 min.

## FLUSSO RAPIDO DEFINITIVO (dal 26/08/2026 sera) — strumenti permanenti
Per generare un programma nuovo, usare SEMPRE questa pipeline (niente piu codice ad-hoc):
1. **Scrivere la spec JSON** (sintassi documentata in testa a `C:\Users\tecni\Claude\sysmac-mcp\ladder_gen.py`; esempio funzionante: `spec_esempio.json`). Contatti "X" "/X" "^X", bobine "(X)" "(S X)" "(R X)", FB `{"fb":"TON","inst":"Tim_1","p":{"PT":"T#3s"}}`, funzioni `{"f":"=","p":{...}}`, ST inline `{"ist":"..."}`, parallelo di 2 contatti in testa con "par". UNA uscita per rung. Sezione "variables" -> genera il TSV.
2. `python C:\Users\tecni\Claude\sysmac-mcp\ladder_gen.py spec.json` -> genera `sec_<Sezione>.xml` VALIDATI + `vars.txt`. `--tipi` elenca i blocchi noti; `--autotest` verifica l'installazione. I tipi FB/F si imparano AUTOMATICAMENTE dai template in `sysmac-mcp\templates\` (9 gia presenti: TON, MC_Power, MC_Home, MC_MoveAbsolute, =, >, MOVE, @Inc, Get100msClk). Blocco nuovo? `sysmac_copy_rung_to_file` su un rung che lo contiene, salvando nei templates.
3. Variabili: `powershell -STA -File C:\Users\tecni\Claude\text_clip.ps1 vars.txt` -> tabella variabili -> paste (interne). Globali/assi: registrare dagli errori F8 (Ctrl+Alt+R).
4. Import: tool MCP **sysmac_paste_file(path)** (nuovo, prende il file direttamente) o `ladder_paste.ps1` + Ctrl+V. Eliminare il rung 0 vuoto.
5. F8 -> 0 errori -> Ctrl+S -> simulazione.
NOVITA in server.py (attive al riavvio dell app Claude, backup in server.py.bak_20260826): `sysmac_paste_file`, `sysmac_copy_rung_to_file`, `sysmac_copy_rung` con colonna X parametrica, `_focus_sysmac` che ora TOLLERA menu contestuali e dialoghi di Sysmac in primo piano (prima falliva col menu aperto).
Tempo atteso per un progetto tipo Movimentazione_2Assi con questa pipeline: ~12-15 min editing.
