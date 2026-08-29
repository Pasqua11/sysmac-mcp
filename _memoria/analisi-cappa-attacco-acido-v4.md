# Cappa Attacco Acido_V4 C924 — analisi del software

Estratta il 26/08/2026 dal database Sysmac offline (`C:\OMRON\Data\Solution\a63c2245-…`), ultima modifica del progetto **09/03/2026**. CPU **NX1P2-9024DT1 ver. 1.47**. "C924" è verosimilmente la commessa 924 (deduzione dal nome, non verificata sui documenti).

## 1. Che macchina è
Cappa di attacco acido per wafer: un **robot cartesiano a 2 assi** (`MC_X` traslazione, `MC_Y` sollevamento, servo 1S su EtherCAT, 2 nodi) sposta il cestello lungo una linea di 5 stazioni:

**Carico → Vasca 1 (acido + ultrasuoni) → Vasca 2 (rinse) → Vasca 3 (rinse) → Forno (asciugatura) → Scarico**

Formati gestiti: **wafer 8" e 12"** (`SET_Ciclo`), con quote di immersione diverse. Interfaccia HMI + **Modbus TCP server** (`MTCP_Server_NJNX`) e comandi remoti OPC.

Differenza sostanziale con `Hydra_Sonic_40_2g` (l'altra macchina a vasche analizzata): **qui non c'è gruppo assi né interpolazione**. Nessun `MC_Group*`, nessun `MC_MoveLinear*`: sono 15 `MC_MoveAbsolute` su asse singolo, alternando X e Y. I movimenti sono a "L", non diagonali.

## 2. Sezioni del Programma0
`Marcia_Robot` (9) → `Portelli` (9) → `Reset_Movimenti` (4) → `Trasf_Dati` (9) → `Movimentazione_Robot` (51) → `Ausiliari` (8) → `Vasche_Ready` (4) → `Vasca1_Acido` (31) → `Vasca2_Rinse` (14) → `Vasca3_Rinse` (28) → `Forno` (12) → `Serranda` (4) → `Ric_Remoto` (11) → `Allarmi` (51). In tutto ~235 rung.

## 3. Abilitazione e reset assi
Identico nello scheletro a Hydra ma **senza gruppo**: `/IN_MARCIA → Marcia_ON`, TON 200 ms, poi `MC_Power` su X e Y con i consensi `DrvStatus.Ready · MainPower`. Jog manuale con interblocco incrociato (`/Manu_Y.Busy` su X e viceversa), X a 40 mm/s e Y a 10.

**Homing a tre passi** (`Reset_Movimenti`): `MC_Home` su Y → 1 s → `MC_Home` su X → 1 s → **`MC_MoveAbsolute` su Y a quota 130** (posizione di riposo bassa). `End_Reset_Robot` richiede tutti e tre i `.Done`. È una differenza da Hydra, dove il reset finisce con gli assi a zero.

## 4. Il ciclo: 15 movimenti in cascata
`Start_Ciclo` nasce da una catena di consensi lunga: `Ready_Movimentazione · Mem_Puls_Start_Ciclo · /IN_PORTA_APERTA_CARICO · Carico_Ready · Vasca1_Ready · Vasca2_Ready · Vasca3_Ready · Ricetta_Rinse · V_S_Marcia`, con l'alternativa del comando remoto (`Mem_OK_Call_Ric`). Si resetta su `End_Ciclo`.

| Mov | Asse | Quota | Descrizione | Consenso di avanzamento |
|---|---|---|---|---|
| MOV0 | Y | 0 | salita verticale | `Movim_Prenotati` + TON 400 ms |
| MOV1 | X | 1621 | traslazione a Vasca 1 | `MOV0.Done` + TON 1 s, `/Ricetta_Rinse` |
| MOV2 | Y | `Mov2_Position` | discesa in Vasca 1 | `MOV1.Done` + TON 1 s + `Cnt_Stabi_V1` |
| MOV3 | Y | 0 | risalita da Vasca 1 | `MOV2.Done` + **`Cnt_V1.End_Conteggio`** (tempo processo) |
| MOV4 | X | 1214 | traslazione a Vasca 2 | `MOV3.Done` + `Cnt_Sgocc_V1.End_Conteggio` (sgocciolatura) |
| MOV5 | Y | `Mov5_Position` | discesa in Vasca 2 | `MOV4.Done` + TON 1 s + `Cnt_Stabi_V2` |
| MOV6 | Y | 0 | risalita da Vasca 2 | `Cnt_V2.End_Conteggio` |
| MOV7 | X | 834 | traslazione a Vasca 3 | `Cnt_Sgocc_V2.End_Conteggio` **oppure** direttamente da `MOV0.Done` se `Ricetta_Rinse` |
| MOV8 | Y | `Mov8_Position` | discesa in Vasca 3 | `MOV7.Done` + TON 1 s + `Cnt_Stabi_V3` |
| MOV9 | Y | 0 | risalita da Vasca 3 | `Cnt_V3.End_Conteggio` |
| MOV10 | X | 419 | traslazione al Forno | `Cnt_Sgocc_V3.End_Conteggio` |
| MOV11 | Y | `Mov11_Position` | discesa in Forno | `MOV10.Done` + TON 1 s + `Cnt_Stabi_Forno` |
| MOV12 | Y | 0 | risalita dal Forno | `Cnt_V4.End_Conteggio` |
| MOV13 | X | 0 | traslazione a Scarico | `MOV12.Done` + TON 1 s |
| MOV14 | Y | 130 | discesa finale di riposo | `MOV13.Done` + TON 1 s |

`MOV14.Done` → contatore `Cnt_End_Movimenti` → `End_Movimenti` → `End_Ciclo` → `Fine_Ciclo`.

**Tre schemi ricorrenti, ripetuti identici per ogni stazione:**
1. **stabilizzazione** (`Cnt_Stabi_*`) sulla discesa,
2. **tempo di processo** (`Cnt_V*` con `SET_Timer_V*` da ricetta) che sblocca la risalita,
3. **sgocciolatura** (`Cnt_Sgocc_*`) che sblocca la traslazione successiva, con spia lampeggiante `V_L_Sgoccio_V*` mentre è in corso.

Tutti realizzati con il FB custom `Contatore` (`SET_VALUE` / `VALUE` / `.End_Conteggio`), non con TON: così i tempi sono impostabili da HMI in secondi interi e visualizzabili come conto alla rovescia.

### Quote parametriche per formato wafer
```
/SET_Ciclo (8")  → Mov2_Position=520, Mov5_Position=520, Mov11_Position=420
 SET_Ciclo (12") → Mov2_Position=420, Mov5_Position=420, Mov11_Position=420
/SET_Livello_V3  → Mov8_Position=520      SET_Livello_V3 → Mov8_Position=420
```
Le quote X sono invece **costanti cablate nel ladder** (1621 / 1214 / 834 / 419 / 0): scelta diversa da Hydra, dove tutte le posizioni passano da variabili `X_*` trasferite in `Trasf_Dati`.

### Ricetta "solo rinse"
`Ricetta_Id_Menu = 10 o 11` → `Ricetta_Rinse`: i movimenti verso V1 e V2 sono esclusi (`/Ricetta_Rinse` in serie su MOV1…MOV6) e MOV7 parte direttamente da `MOV0.Done`. Il cestello va dritto in Vasca 3.

## 5. Gestione delle vasche (Vasca1_Acido, 31 rung — modello per le altre)
- **Livelli**: `IN_LIV_MAX / IN_LIV_12 / IN_LIV_8 / IN_LIV_MIN`, ciascuno filtrato da un TON (100 ms i livelli di processo, 1 s il minimo).
- **Carico acqua DI** e **carico soluzione**, separati per formato 8"/12": memoria set/reset comandata da pulsante HMI (`V_P_*`), interrotta da `V_P_Annulla`, dal livello raggiunto o da `Allarme_Azoto`.
- **Scarico**: `Mem_Scarico_V1` con contatore di svuotamento 20 s dopo il livello minimo; blocco se l'exhaust è pieno o assente.
- **Fusto soluzione vuoto**: se la pompa gira 10 s con `/IN_LIV_VUOTO_FUSTO` → `Mem_Vuoto_Fusto_V1` disabilita la pompa (`V_S_Pump_Soluz_V1`).
- **Spillaggio** a tempo (`@Dec` su `PV_Timer_Spilla_V1` con `Get100msClk`), vincolato a portellino chiuso e termico pompa OK.
- **Ricircolo** e **ultrasuoni**: attivi solo con vasca sopra il livello minimo, in marcia, e — in automatico — solo durante la permanenza del cestello (`Mem_Ciclo_V1`).
- **Vita soluzione**: `Get1minClk → @Inc(PV_Minuti_Soluz_V1)` finché la vasca è piena, più `PV_Run_Soluz_V1` (numero di cicli); entrambi azzerati allo scarico. È il dato che finisce nel log.

## 6. Forno: PID con autotuning
`PIDAT` con PV/SP in REAL (temperatura interi decimi → `/10.0`), parametri `PID_OprSetParams` / `PID_InitSetParams` inizializzati da rung ST inline abilitati da `SET_Param_Pid`, uscita `MV` → `TimeProportionalOut` (periodo 1 s) → due uscite SCR **alta** e **bassa**. La resistenza bassa viene esclusa dopo `MOV9.Done` nel ciclo 12". Presenti spray 1 e 2 comandati durante la discesa/risalita in forno. Un rung di **simulazione** del riscaldamento (`P_Off`, quindi disattivo) resta nel progetto per le prove.
Nel commento del rung sono annotati i tempi reali: *riscaldamento con sole resistenze alte 1 °C/min, con tutte le resistenze 1 °C/20 s*.

## 7. Sicurezze, allarmi, remoto
- **Allarmi**: array `Allarme_Bit[1..50]`, spia riassuntiva via `ArySearch`. Le condizioni di zona (`Carico_Ready`, `Vasca1_Ready`, `Vasca2_Ready`, `Vasca3_Ready`) sono catene di negati dei bit di allarme pertinenti — e sono consensi diretti a `Start_Ciclo`. Il carico da solo pesa 17 allarmi.
- **Porte**: quattro attuatori (carico, SX/DX, 1-2 down, 3 down) con blocco/sblocco legato a marcia, ciclo e reset; l'apertura si "prenota" e avviene solo a ciclo fermo.
- **Serranda aspirazione**: apertura totale con `V_S_Enable_Aspirazione`, chiusura fino a mezza apertura altrimenti.
- **Comando remoto** (`Ric_Remoto`): con `V_S_Ric_Remoto` attivo, l'host scrive `Ricetta_Remoto` (accettata se `0 < x < 12`) e `Rem_Ok_Ric`; handshake con timeout 10 s → `Mem_OK_Call_Ric` abilita `Start_Ciclo`. Sono replicati da remoto anche start ciclo e i comandi acqua/scarico/annulla della Vasca 3.
- **Log**: sui fronti di `Start_Ciclo` e `Fine_Ciclo` scrive `Log_Stringa` ("INIZIO CICLO" / "FINE CICLO") con vita soluzione e numero run, e alza `Log_Enable` per l'HMI.

## 8. Osservazioni tecniche
1. **Nessuna diagnostica di sequenza**: manca il rung di coerenza dei `MOV*_Done` che in Hydra incrementa `Errori_Movimento`. Qui un salto di passo non verrebbe rilevato.
2. **Quote X cablate**: cambiare la geometria della macchina richiede di editare i rung, non una tabella di ricetta. Su Hydra la scelta opposta ha reso il codice riutilizzabile.
3. **`Fine_Ciclo` anche su `IN_PORTA_APERTA_CARICO`** (rung 47): l'apertura porta di carico chiude il ciclo. Da tenere presente se si toccano le logiche porte.
4. **Rung di simulazione lasciati in campo** (riscaldamento forno su `P_Off`): innocui ma da ripulire in una eventuale V5.
5. Il progetto contiene ancora i FB di libreria 1S (`MC_Restart1S`, `MC_MotorReplacement1S`, `MC_BrakeRelease1S`, `Get1sInfo`) e i FB custom `Brake_Release`, `Drive_Restart`, `Drive_In_STO`, `Drive_Error_Warning`, `Contatore`, `MTCP_Server_NJNX`: stessa base di Hydra.

## 9. Dati per il generatore ladder
Tipi FB/funzioni usati qui e **non ancora nei template** di `sysmac-mcp\templates\`: `Contatore`, `PIDAT`, `TimeProportionalOut`, `ArySearch`, `@Dec`, `<=`, `<`, `Get1minClk`, `Get1sClk`, `INT_TO_REAL`. Campionandoli si copre praticamente tutto il vocabolario di questa macchina.
