# Metodo di programmazione di Luca — appreso da Cappa Ceramiche V2 (26/08/2026)
Fonte: analisi offline completa del progetto (C:\OMRON\Data\Solution, GUID dd9adb0e), 17 sezioni + FB custom, confermata con domande dirette a Luca. NJ/NX + 2 servoassi R88D-1SN EtherCAT (MC_X=_MC_AX[2], MC_Y=_MC_AX[3]).

## Architettura
Un solo Programma0 diviso in SEZIONI per funzione, in ordine di flusso: Marcia_Robot (MC_Power con consensi DrvStatus, jog MC_MoveJog interbloccati /Busy dell altro asse) -> Portelli (sicurezze: lock porte/cassetti) -> Reset_Movimenti (homing sequenziato: MC_Home Y -> chiudi coperchi -> MC_Home X -> MC_MoveAbsolute di riposizionamento) -> Ritardo_Start_Ricette -> Sequenze_Movimentazione (ARBITRAGGIO: decide quale movimento) -> Trasf_Dati (DATI: carica quote del movimento deciso) -> Movimentazione_Robot (ESECUZIONE: come muoversi) -> Memorie_Vasche -> sezioni di processo per vasca -> Serrande -> Allarmi. Separazione decisione/dati/esecuzione.

## Pattern sequenze di movimento (il piu importante)
1. PRENOTAZIONE: rung di arbitraggio = catena consensi (Ready_Movimentazione, /Bit_Macchina_Piena, vasca dest libera /Mem_Vx, OK_Cadenza, Carico_Sicuro) + confronto ricetta [=(Ricetta.Cicli[n].Vasca_Depo, 1/2/3/0)] -> SET coppia Prelievo_* + Deposito_* (bobine SET, ritentive fino a fine movimento) + bobina semplice Look* (impulso che SETta Blocco_Cassetti nei Portelli; Look = lock cassetti, 1A=Car1->V1 ecc.).
2. SLOT TEMPORALI: Clock_Movimenti conta 0..5 su Get100msClk; ogni sorgente ha uno slot ([=(Clock,1)]=V1, 2=V2, 3=V3, 4=Carico1, 5=Carico2): mai due prenotazioni nello stesso scan, vasche prioritarie sui carichi. Reset clock quando Movim_Prenotati.
3. Movim_Prenotati = OR di tutte le prenotazioni; blocca nuove prenotazioni (via /Movim_Prenotati in Ready) e fa partire la catena.
4. ESECUZIONE: catena FISSA MOV1..MOV9 di MC_MoveAbsolute alternando assi (X orizzontale, Y verticale), ogni MOVx_Done abilita il successivo. UNA SOLA catena serve tutte le combinazioni sorgente/destinazione: Trasf_Dati assegna X_PRESA/Y_PRESA/X_DEPOSITO/Y_DEPOSITO/X_AGGANCIO/X_SGANCIO in base a quale Prelievo_*/Deposito_* e attivo; un ST inline calcola Distance1..9. Velocita parametriche da ricetta (SET_Speed_UP_Vx / DOWN / X_Agganciato, retain), trasferite ai Speed_Mov* sul fronte ^Movim_Prenotati.
5. AVVICINAMENTI: doppio blocco con BufferMode=_mcBlendingPrevious: MOV4A lento (ultimi 50mm, Distance4_Acc=Distance2-50) poi MOV4 veloce; MOV6 veloce fino a Y_DEPOSITO-230 poi MOV6A lento a quota finale. Le quote fisse nel codice (1592 soglia X coperchio forno, 1000 riposo dopo homing, offset -50/-230) sono QUOTE MECCANICHE VOLUTAMENTE hard-coded (non cambiano mai) - confermato da Luca.
6. CONSENSI INTERMEDI OK_MOV_2/5/6: la catena aspetta coperchi (comando+doppio finecorsa: OUT_OPEN_Cx AND IN_Cx_OPEN AND /IN_Cx_CLOSE), sgocciolatura (Cnt_Sgocc_Vx) e stabilizzazione (Cnt_Stabi_Vx) via FB Contatore. Timer TON di assestamento T#2s prima del consenso.
7. FINE: MOV9_Done -> End_Movimenti -> RST di tutte le prenotazioni (+ reset da chiave IN_RESET o allarmi assi). Pausa_Mov1_2: contatto N.C. mai scritto, serve per FORZATURA MANUALE in collaudo (fermare la catena tra MOV1 e MOV2).
NOTA: lo ST "CALCOLO QUOTE" esiste in 2 copie (Trasf_Dati R0 con -100, Movimentazione_Robot R0 con -230): Luca dice che sono VOLUTI ENTRAMBI (ragione non ancora spiegata nel dettaglio - chiedere se serve toccarli; in scan vince quello di Movimentazione_Robot).

## Scheduler ricette (FB Ritardo)
FB in ST con FOR: dati ordine vasche e durate della ricetta IN MACCHINA (RM_*) e della ricetta AL CARICO (RC_*), calcola il ritardo minimo di partenza perche non collidano sulla stessa vasca -> T_Min; +60s sicurezza -> Tempo_Ritardo_Car*; Tempo_da_ultimo_Carico (contatore a 1s) > soglia -> OK_Cadenza_Car*. Copia ricetta con UN SOLO MOVE di struttura: MOVE(Ricetta_Memoria[Id])->Ricetta_Macchina sul fronte ^Prelievo_Car*.

## Convenzioni (confermate anche qui)
- IN_/OUT_ = I/O fisici con AT (BuiltInIO/IOBus); V_P_ pulsanti HMI, V_S_ selettori/settaggi HMI, V_L_ lampade HMI; Mem_ stati (spesso SET/RST); PV_/SET_ processo/setpoint (SET_ e quote in RETAIN R=1); Tim_/Cnt_ istanze; P_On/P_Off sempre attivo/mai.
- Allarme_Bit[1..80] ARRAY con commenti per elemento (EC nel db); raccolta spia: ArySearch(Allarme_Bit[1],80,TRUE)->Spia_Allarme; Vasche_Ready = AND di /Allarme_Bit[..] pertinenti; Bit_OK_Processo esclude le vasche usate dalla ricetta se in allarme, bypass con V_S_Escludi_Allarmi.
- SET/RST usati per stati persistenti (96 SET / 80 RST nel progetto), bobine semplici per logica combinatoria. Alternanza carichi: Mem_Enable_Car2 SET/RST su fronti dei sensori presenza cassetto.
- ST inline (48 nel progetto) SOLO per calcoli: quote, min/sec, scheduling con FOR. Ladder per tutta la logica di stato. FB custom minimi: Contatore (decremento a 1s con Get1sClk, End_Conteggio, ricarica quando /ENABLE), Ritardo (scheduler).
- Analogiche: LIMIT -> INT_TO_REAL -> @MovingAverage(buffer 30-100 su Get100msClk) -> ScaleTrans -> + correttivo -> PV_*; sotto soglia forzo 0.
- Coperchi vasche: Mem_Open_Vx SET su fronte del passo di movimento che lo richiede (^MOV5_Done ecc.) o da HMI, RST a fine uso; uscita = Marcia + Mem + porte bloccate + /emergenza.
- Diagnostica assi: sezioni con MC_x.DrvStatus.*, MFaultLvl, codici allarme in WORD, stringhe Errore_X/Y; FB libreria Omron 1S (Brake_Release, Drive_Restart, MC_Restart1S...).
- Strutture dati ricetta: Ricetta_Master{Cicli[1..3]{Vasca_Depo INT; Vasca[1..3]{Dato[0..9] INT; Bit_0..7}}; Nome STRING[21]; Numero; PV_Ciclo}; Ricetta_Memoria ARRAY[1..20] RETAIN; UNION PAROLA (bit[16]/WORD) per scambio HMI/Modbus.

## Come leggere i progetti offline (per analisi future)
Sezione = <guid>.xml nel folder Solution: 1 riga JSON per rung. Tipi: LD contatto (Not/Up/Down), ST bobina (S=Set, RS=Reset!), FB, F funzione, IST = ST inline (codice nel campo TXT), HL linea. CMT commento rung. Tabelle variabili = formato SLWD (++D=tipo N=nome AT=... R=1 retain, EC=commenti elementi array). Il progetto APERTO si riconosce dal file <pid>.applicationlock.
