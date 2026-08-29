# Catena di import ladder CHIUSA end-to-end (26/08/2026)

Prova riuscita: da una specifica JSON a una sezione ladder di **15 rung con 23 variabili, compilata a 0 errori / 0 avvisi**, senza disegnare nulla a mano. Progetto di prova: `test_import_ladder` (NX1P2-1040DT ver 1.70, 2 assi virtuali `mc_x`/`mc_y` + gruppo `MC_Group000` a 2 assi).

## Il flusso completo, nell'ordine

1. **Spec JSON** con sezioni e variabili (sintassi in testa a `ladder_gen.py`).
2. `python ladder_gen.py spec.json` → `out\sec_<Sezione>.xml` (ladderSnippetXML) + `out\vars.txt` (TSV variabili).
   **La cartella `out_dir` deve esistere**: `ladder_gen.py` non la crea e muore con `FileNotFoundError`.
3. **Variabili in blocco** (novità: prima si registravano una a una):
   - aprire la sezione ladder → cliccare la barra **Variabili** in alto per aprire la tabella (scheda *Interne*);
   - cliccare una volta nell'area vuota ("Per aggiungere un elemento fare clic qui") → nasce una riga vuota;
   - **ESC**, poi cliccare il **selettore di riga** (la cella grigia a sinistra della colonna Nome) per selezionare la riga intera;
   - **Ctrl+V** → tutte le righe TSV entrano in un colpo;
   - eliminare la riga vuota residua (selettore di riga + Canc).
   - Il TSV va ripulito dalle righe vuote prima di metterlo negli appunti: `vars.txt` esce con `\r\r\n` e senza pulizia si ottengono 45 righe invece di 23. Ordine colonne: `Nome, Tipo, Valore iniziale, AT, Ritentivo, Costante, Commento`.
4. `sysmac_paste_file(path, rung_col_x, rung_row_y)` sul rung selezionato → i rung entrano **sotto**; eliminare il rung 0 vuoto.
5. `sysmac_compile()` → gli errori residui sono solo "variabile non registrata" sugli **assi e sui gruppi assi**.
6. Per ciascuno: `sysmac_register_from_error()` → ricompilare. Bastano **3 registrazioni** (una per `mc_x`, una per `mc_y`, una per `MC_Group000`): registrando l'asse la prima volta si risolvono in blocco tutti i suoi riferimenti (`.DrvStatus.Ready`, `.MFaultLvl.Active`, i pin `Axis`, ecc.).
7. `sysmac_save()`.

Tempo effettivo della prova: ~4 minuti dalla generazione alla compilazione pulita.

## Lezione chiave: assi e gruppi = variabile ESTERNA
Il dialogo di Ctrl+Alt+R ("Seleziona il tipo di variabile") propone *Variabile interna* / *Variabile esterna*. Per assi e gruppi assi la scelta corretta è **Variabile esterna** (sono variabili globali create dalla configurazione controllo assi): registrarli come interni creerebbe un duplicato locale scollegato dall'asse reale.
**Il pulsante predefinito del dialogo è già "Variabile esterna"**, quindi `sysmac_register_from_error` (che manda Invio) fa la cosa giusta su assi e gruppi. Attenzione al caso opposto: per una normale variabile interna non registrata quel default sarebbe sbagliato — meglio pre-registrare sempre tutto via TSV, così gli unici errori residui sono assi e gruppi.

## Template disponibili (`sysmac-mcp\templates\`)
Campionati da progetti reali con `sysmac_copy_rung_to_file`. Dopo la sessione del 26/08 il generatore conosce **17 tipi**:

`TON`, `MOVE`, `=`, `>`, `@Inc`, `Get100msClk`, `MC_Power`, `MC_Home`, `MC_MoveAbsolute` (preesistenti) +
**`MC_GroupEnable`, `MC_GroupDisable`, `MC_GroupReset`, `MC_Reset`, `MC_Stop`, `MC_MoveJog`, `MC_MoveLinearAbsolute`, `MC_MoveLinearRelative`** (campionati da Hydra_Sonic_40_2g_V1).

Per insegnarne altri (TOF, `Contatore`, `ScaleTrans`, `PIDAT`, `MTCP_Server_NJNX`…): aprire un progetto che li contiene, `sysmac_copy_rung_to_file` sul rung, salvare in `templates\`. Nessun'altra modifica al codice.

## Uscite multiple e OR a N rami (fatto il 26/08/2026, secondo giro)

I due limiti storici sono caduti. Sintassi nuova nella spec:

```json
{"cmt": "ABILITAZIONE SERVO X E Y",
 "chain": ["Tim_Marcia.Q", "mc_x.DrvStatus.Ready", "mc_y.DrvStatus.Ready"],
 "out": [ [{"fb":"MC_Power","inst":"Power_x","p":{"Axis":"mc_x","OUT:Axis":"mc_x"}}],
          [{"fb":"MC_Power","inst":"Power_y","p":{"Axis":"mc_y","OUT:Axis":"mc_y"}}] ]}
```

- `"out": [ramo, ramo, ...]` → più rami di uscita in parallelo (bobine o FB). Un ramo è una lista di elementi in serie, oppure un elemento singolo (`"(Blocco_Portellino)"`).
- `{"or": [ramo, ramo, ...]}` → parallelo verticale a **N rami in qualunque punto della catena**; ogni ramo può contenere elementi in serie (es. `["Reset_Auto_All_Robot", {"f":"Get100msClk","p":{}}]`).
- `"par"` resta valido ed è ora un OR in testa senza il limite di 2 contatti.

Provati e compilati a 0 errori nel progetto di test: OR a **12 rami** (`Movim_Prenotati`), OR con ramo in serie + **3 FB in uscita** (reset assi come Hydra), OR in mezzo alla catena + 2 bobine, marcia/arresto con ritenuta, 2 `MC_Power` nello stesso rung.

### La regola che conta: MAI due `Connection` in cascata
Prima versione: un nodo per unire l'OR (N→1) e un secondo nodo per diramare le uscite (1→M). Compilava a 0 errori **ma Sysmac disegnava i blocchi sovrapposti**, illeggibili.
Nei rung reali c'è **una sola `Connection`** che fa entrambe le cose: N ConnectionPoint di ingresso e M di uscita (in `mc_reset_groupreset.xml`: 2 in / 3 out). Fondendo i due nodi il layout diventa identico all'originale.
Modello di riferimento: **un ConnectionPoint porta un solo Edge**; per diramare si aggiungono ConnectionPoint all'elemento `Connection` (la barra sinistra ha N CP output, la destra N CP input).

### Ipotesi scartata: l'altezza del rung
Avevo attribuito la sovrapposizione all'attributo `Height` del `RungXML` (i rung reali con 3 FB stanno a ~574, il generato dichiarava 270). **Falso**: rigenerato con `Height=865` il disegno era identico. Sysmac ricalcola il layout per conto suo. La formula di altezza in `ladder_gen.py` è comunque stata allineata alle misure reali (FB ≈ 190 px, riga di contatti ≈ 45, ST inline ≈ 80 + 22/riga), ma non è lei a risolvere il problema.

## Limiti residui
- I rami non si annidano oltre un livello con `par` (usare `or`, che invece si annida).
- I pin non collegati restano vuoti: Sysmac li accetta.

## Backup progressivi di `ladder_gen.py`
`\.bak_pre_multiout` (prima di out/or) → `\.bak_pre_altezza` → `\.bak_pre_nodounico`.

## Nota sull'input da tastiera
`sysmac_send_keys` ha prodotto testo **tutto minuscolo** in due casi (nome progetto e rinomina asse: `MC_X` → `mc_x`). Non è confermato se sia SendKeys che perde lo shift o Sysmac che normalizza; non ho verificato la causa. Conseguenza pratica: gli identificatori IEC sono case-insensitive, quindi il ladder compila comunque, ma per avere i nomi con le maiuscole conviene passare dalla clipboard (`Clipboard set` + Ctrl+V) invece di digitarli.

## Prossimi passi utili
1. Automatizzare la pre-registrazione TSV in un tool MCP (`sysmac_paste_vars`), oggi fatta a mano con click sul selettore di riga + Ctrl+V.
2. Collaudo in simulazione (F5 + forzature Set/Reset) come passo finale del flusso.
3. Ampliare i template: `TOF`, `Contatore`, `ScaleTrans`, `PIDAT`, `MTCP_Server_NJNX`, `@MovingAverage`.
4. Generare una sezione intera partendo dal catalogo (`catalog.json`) invece che da una spec scritta a mano: i dati per farlo ci sono già tutti.

## Aggiornamento 26/08/2026 - registrazione variabili in blocco
Nuovo tool `sysmac_paste_vars(path)`: incolla il TSV delle variabili e gestisce il dialogo 'Risolvi conflitti operazione Incolla' (Copia tutto da destra a sinistra -> Applica -> Alt+F4). Richiede riavvio dell'app Claude. Procedura e coordinate in `C:\Users\tecni\Claude\memory\registrazione-variabili-in-blocco.md`.

