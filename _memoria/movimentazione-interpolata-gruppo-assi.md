# Movimentazione interpolata a gruppo assi (pattern Hydra_Sonic)

Estratto il 26/08/2026 dal progetto **Hydra_Sonic_40_2g_V1** (`C:\OMRON\Data\Solution\b00abc66-83f4-4930-a005-6b9e89509878`), letto offline dai file `.oem` / `<sezione>.xml` come per la libreria circuiti SYNTECH.
Novità rispetto alla libreria esistente: qui gli assi **non** si muovono singolarmente con `MC_MoveAbsolute`, ma in **interpolazione lineare su gruppo assi** con `MC_MoveLinearAbsolute` / `MC_MoveLinearRelative` concatenati in blending.

## 1. Macchina
Impianto di trattamento a vasche (linea galvanica / ultrasuoni "Hydra Sonic 40"): carico → V1…V7 → forno F1/F2 → scarico. Il trasporto dei cesti è un **robot cartesiano a 2 assi**:
- **MC_X** = traslazione orizzontale (max vel. 1000 mm/s, jog 300, homing 30)
- **MC_Y** = sollevamento (max vel. 750 mm/s, jog 300, homing 15)
- **MC_Group000** = gruppo `NexAxisGroup2Axes`, X=MC_X, Y=MC_Y, unità mm/s, stop mode *Promptly Stop*
- `MC_Axis000` / `MC_Axis001` sono presenti ma **non usati nel ladder: assi predisposti per espansione futura** (non sono residui da cancellare).
Servo su EtherCAT (2 × NexECAT, serie 1S: presenti FB `MC_BrakeRelease1S`, `MC_Restart1S`, `MC_MotorReplacement1S`). Altri organi: Lift, agitazione, nastrini carico/scarico, forni, vasche, HMI (pagine + Modbus TCP server `MTCP_Server_NJNX`).

## 2. Sezioni del Programma0 (ladder, ordine di scansione)
`Marcia_Robot` → `Portelli` → `Reset_Movimenti` → `Trasf_Dati` → `Movimentazione_Robot` → `Sequenze_Movimentazione` → `Memorie_Vasche` → `Agitazione` → `Lift` → `Nastrini` → `Vasche` → `Forni` → `Ausiliari` → `Allarmi`.

## 3. Abilitazione assi + gruppo (sezione Marcia_Robot)
```
/IN_MARCIA                      -> Marcia_ON
Marcia_ON  -> TON 3 s (Tim_Marcia)
Tim_Marcia.Q · MC_X.DrvStatus.Ready · MC_Y.DrvStatus.Ready
             · MC_X.DrvStatus.MainPower · MC_Y.DrvStatus.MainPower
             -> MC_Power(Power_x, Axis:=MC_X) , MC_Power(Power_y, Axis:=MC_Y)
End_Reset_Robot -> TON 2 s -> GruppoEnable
GruppoEnable    -> MC_GroupEnable (Group1,  AxesGroup:=MC_Group000)
/GruppoEnable   -> MC_GroupDisable(Group1_OFF, AxesGroup:=MC_Group000)
```
**Regola appresa:** il gruppo si abilita solo DOPO l'homing completato (`End_Reset_Robot`) e con 2 s di ritardo; si disabilita sul negato della stessa memoria.

Manuale/JOG: `MC_MoveJog` per asse, con interblocco incrociato `/Manu_Y.Busy` su X e `/Manu_X.Busy` su Y (mai i due jog insieme), consensi `ServoOn · /DrvAlarm`. X: Vel 40, Acc 15; Y: Vel 15, Acc 30; Dec 100000 (arresto immediato al rilascio).

Reset errori: `IN_RESET + Reset_Auto_All_Robot + Get100msClk` → `MC_Reset` X, `MC_Reset` Y, **`MC_GroupReset`** sul gruppo. Prima del reset, `^IN_RESET · /End_Reset_Robot` → `MC_Stop` su entrambi gli assi (Dec 200).

`Robot_Ready` = ServoOn X·Y · /DrvAlarm · /DrvWarning · /MFaultLvl.Active (entrambi gli assi).

## 4. Homing (Reset_Movimenti)
```
Start_Reset_Robot -> MC_Home(Home_Y, Axis:=MC_Y) ; TON 1 s ; MC_Home(Home_X, Axis:=MC_X)
Home_Y.Done · Home_X.Done -> End_Reset_Robot (memoria set/reset con P_On)
```
**Sequenza obbligata: prima Y (sale), poi 1 s dopo X.** Mai azzerare X con il cesto in basso.

## 5. Ciclo di movimentazione a 10 passi (Movimentazione_Robot)
Le quote sono `ARRAY[0..3] OF LREAL` (indice 0 = X, 1 = Y; il gruppo è a 2 assi ma l'array è dimensionato a 4).
Le posizioni sorgente/destinazione arrivano dal blocco `Trasf_Dati`, che a ogni tipo di movimento copia le costanti di impianto nelle 6 variabili REAL di lavoro:
```
X_PRESA, Y_PRESA, X_AGGANCIO      (da: X_CARICO / X_V1 … X_F2 / X_*_Svincolo)
X_DEPOSITO, Y_DEPOSITO, X_SGANCIO
```
Calcolo quote (ST inline, rung 1 di Movimentazione_Robot):
```
Distance1[0]:=X_PRESA + X_AGGANCIO;   Distance1[1]:=0;          (* MOV1: X sopra la presa, Y alto *)
Distance2[0]:=Distance1[0];           Distance2[1]:=Y_PRESA;    (* MOV2: discesa Y *)
Distance3[0]:=X_PRESA;                Distance3[1]:=Distance2[1];(* MOV3: X di aggancio *)
Distance4_Acc[0]:=0;                  Distance4_Acc[1]:=-50;    (* MOV4A: relativo, 50 mm lenti *)
Distance4[0]:=Distance3[0];           Distance4[1]:=0;          (* MOV4: salita con cesto *)
Distance5[0]:=X_DEPOSITO;             Distance5[1]:=Distance4[1];(* MOV5: traslazione con cesto *)
Distance6[0]:=Distance5[0];           Distance6[1]:=Y_DEPOSITO-50;(* MOV6: discesa veloce fino a -50 *)
Distance6_Dec[0]:=Distance5[0];       Distance6_Dec[1]:=Y_DEPOSITO;(* MOV6A: ultimi 50 mm lenti *)
Distance7[0]:=X_DEPOSITO + X_SGANCIO; Distance7[1]:=Distance6_Dec[1];(* MOV7: svincolo X *)
Distance8[0]:=Distance7[0];           Distance8[1]:=0;          (* MOV8: risalita, fine ciclo *)
```
Catena FB (tutti su `AxesGroup:=MC_Group000`, ciascuno abilitato dal `.Done` del precedente):

| Passo | FB | Quota | Vel | Acc/Dec | Buffer / Transition | Consenso extra |
|---|---|---|---|---|---|---|
| MOV1 | MC_MoveLinearAbsolute | Distance1 | 300 | 500/500 | — (Execute diretto) | `Movim_Prenotati · End_Reset_Robot` + TON 400 ms |
| MOV2 | MC_MoveLinearAbsolute | Distance2 | 250 | 100/100 | BlendingNext + CornerSuperimposed | `/Pausa_Mov1_2` |
| MOV3 | MC_MoveLinearAbsolute | Distance3 | 50 | 100/100 | — | `OK_Aggancio` |
| MOV4A | **MC_MoveLinearRelative** | Distance4_Acc (−50 mm Y) | 50 | 100/100 | — | dopo MOV3 |
| MOV4 | MC_MoveLinearAbsolute | Distance4 | 200 | 500/500 | BlendingNext + CornerSuperimposed | dopo MOV3 |
| MOV5 | MC_MoveLinearAbsolute | Distance5 | 250 | 100/500 | BlendingNext + CornerSuperimposed | `MOV4A_Done · OK_Lift_Down` |
| MOV6 | MC_MoveLinearAbsolute | Distance6 | 100 | 100/100 | BlendingNext + CornerSuperimposed | — |
| MOV6A | MC_MoveLinearAbsolute | Distance6_Dec | 30 | 100/100 | BlendingNext + CornerSuperimposed | — |
| MOV7 | MC_MoveLinearAbsolute | Distance7 | 50 | 100/100 | — | `OK_Sgancio` |
| MOV8 | MC_MoveLinearAbsolute | Distance8 | 250 | 500/500 | BlendingNext + CornerSuperimposed | dopo MOV7 |

`MOV8_Done → End_Movimenti`.

**Regole di stile apprese:**
- Il passo *lento in avvicinamento* si fa spezzando la tratta in due: tratto veloce fino a `quota−50`, poi ultimi 50 mm a velocità ridotta (MOV6/MOV6A).
- **MOV4A = aggancio del cesto a velocità bassa** (confermato da Luca): movimento *relativo* di −50 mm sull'asse Y a velocità 50, eseguito prima della risalita rapida MOV4. È il modo standard per "prendere in carico" il cesto senza strappi; MOV4A e MOV4 partono entrambi da `MOV3_Done` ed è voluto (MOV4 è in blending e prende il testimone quando MOV4A ha finito la tratta lenta).
- Dove il movimento deve essere **fluido** si usa `BufferMode := _mcBlendingNext` + `TransitionMode := _mcTMCornerSuperimposed`; dove serve **fermarsi davvero** (aggancio, sgancio, presa) si lascia BufferMode di default e si vincola l'Execute a un consenso fisico.
- Consenso `OK_Aggancio` / `OK_Sgancio`: uno degli OR dei 12 tipi di movimento · `/Enable_Agitazione · /OUT_AGITAZIONE · IN_AGITAZ_UP` (agitazione ferma e in alto).
- `OK_Lift_Down`: `/Alt_Lift_Down · MOV3_Done · /OUT_LIFT_ENABLE · /IN_LIFT_SU · IN_LIFT_EXTRACORSA · IN_LIFT_GIU` + TON 2 s.
- Diagnostica: rung finale che verifica la **coerenza della sequenza** (ogni combinazione "passo N+1 fatto senza il passo N") e incrementa `Errori_Movimento` con `@Inc`.

## 6. Scelta del movimento (Sequenze_Movimentazione)
- `Macchina_OK` = `Robot_Ready · MC_Group000.Status.Ready · End_Reset_Robot · End_Reset_Agita · End_Reset_Lift`
- `Ready_Movimentazione` = `/Call_Prenoto_Porte · /Movim_Prenotati · Macchina_OK`
- **Scheduler round-robin**: `Get100msClk → @Inc(Clock_Movimenti)`, azzerato a >13 quando c'è una movimentazione in corso. Ogni tipo di trasferimento ha uno slot fisso confrontato con `=(Clock_Movimenti, n)`: V3→V4 =1, V1→V2 =2, V4→V5 =3, V2→V3 =4, F2→Scar =5, F1→Scar =6, V7→F2 =7, V7→F1 =8, V6→V7 =9, V5→V6 =10, Car→V1 =11, Car→V3 =12. **Criterio di assegnazione degli slot (confermato da Luca): svuotare prima il fondo linea.** Gli slot bassi vanno ai trasferimenti più avanti nel processo (V3→V4, V1→V2, V4→V5…), gli slot alti al carico (Car→V1 = 11, Car→V3 = 12): così un cesto nuovo entra solo quando la linea a valle si è già liberata, evitando ingorghi e attese in vasca oltre il tempo di ricetta. Non è un'assegnazione empirica: è la regola da replicare su macchine analoghe.
- Ogni movimento è una memoria set/reset (`OUT` su `P_On`, reset su `IN_RESET · End_Movimenti`), condizionata da: contatore vasca finito (`Cnt_Vn.End_Conteggio`), destinazione libera (`/Mem_Vn`), ricetta attiva, `Temper_OK`, e per il carico `Carico_Sicuro`.
- `Movim_Prenotati` = OR dei 12 movimenti. Rung di sicurezza: somma dei movimenti attivi (`@ADD`), se `>= 2` incrementa `Errore_Movimenti`.
- Ricette: `Mem_Ricetta1` (Car→V1, percorso completo) / `Mem_Ricetta2` (Car→V3, salta V1-V2); la 2 si prenota e diventa attiva solo a vasche V1/V2/V3 libere.

## 7. Dati verso HMI (Trasf_Dati, ST inline)
```
Posizione_Asse_X := MC_X.Act.Pos;   X_Coppia := MC_X.Act.Trq;
X_Origin := MC_X.DrvStatus.HomeSw;  X_Cw := MC_X.DrvStatus.P_OT;  X_Ccw := MC_X.DrvStatus.N_OT;
X_Allarm_Code := MC_X.MFaultLvl.Code;   (* idem per Y *)
```
+ `ScaleTrans` per la grafica: X da −40…4450 mm → 0…770 px, Y da 0…414 mm → 0…100 px.

## 8. FB custom presenti nel progetto
`Contatore` (già in libreria), `Brake_Release`, `Drive_Restart`, `Drive_In_STO`, `Drive_Error_Warning`, `MTCP_Server_NJNX`, e i FB Omron 1S: `MC_BrakeRelease1S`, `MC_Restart1S`, `MC_MotorReplacement1S`, `Get1sInfo`.

## 9. Nota tecnica per l'estrazione offline
Nel JSON dei rung, oltre a `LD`/`ST`/`FB`/`F`, esiste il tipo **`IST` = ST inline** con il codice nel campo `TXT` (con `\r\n` escapati). Senza gestirlo si perdono tutti i calcoli di quota.

**`mine.py` è stato aggiornato il 26/08/2026** (backup: `mine.py.bak_pre_ist`): ora `summarize_rung` restituisce anche il campo `st` con i blocchi inline, e `stats.txt` conta la voce `<ST inline>`. Ri-eseguito sull'intero database: **105 progetti / 18.929 rung, di cui 1.229 rung contengono ST inline** che prima erano invisibili nel catalogo.

Script d'estrazione usati in questa sessione: `dump_hydra.py` (struttura + rung) e `dump2.py` (IST + variabili).
