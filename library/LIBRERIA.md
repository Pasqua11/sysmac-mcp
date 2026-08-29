# LIBRERIA CIRCUITI LADDER SYNTECH
Estratta il 25/08/2026 analizzando 102 progetti reali (18.860 rung) da C:\OMRON\Data\Solution.
File dati: catalog.json (tutti i rung riassunti), esemplari.json (rung completi), stats.txt (frequenze).
Notazione: LD(x)=contatto NO, LD(/x)=NC, LD(^x)=fronte salita, ST(x)=bobina, FB:Nome[istanza](param), F:funzione.

## Frequenze d'uso (stile SYNTECH)
TON 3735 | Contatore(FB custom) 986 | EC_CoESDOWrite 262 | MC_MoveAbsolute 204 | TOF 95 | PIDAT 43
MOVE 3251 | confronti =,>,<,>= ~3800 | Get1sClk 575 | ScaleTrans 430 | @Inc 406 | @MovingAverage 67

## 1. CLOCK DI SISTEMA (in testa alla sezione Pompe/principale)
  F:Get1minClk() -> ST(Clock_1Min)      'CLOCK 1 MINUTO'
  F:Get1sClk()   -> ST(Clock_1Sec)      'CLOCK 1 SECONDO'

## 2. COMANDO POMPA CON INVERTER 3G3M1 (EtherCAT)
'COMANDO POMPA1' [Scrubber Ammoniaca/Pompe]
  LD(/Enable_Pompa2) FB:TON[Tim_30](PT=T#15s)          <- alternanza pompe
  LD(IN_MARCIA) LD(Enable_Pompa) LD(LIV_POMPA) LD(Power_Inverter1)
  FB:TON[Tim_1](PT=T#5s)                                <- ritardo avvio 5s
  FB:INV003_3G3M1_ECT[COMMAND_PUMP_1](ForwardRun=Fwd_Pump1, CmdFrequencyReference=Frequenza_Pump1,
     CmdAcceleration/Decel=Accellerazione/Decellerazione_Pump1, FaultReset=FaultReset_Pump1,
     out: DriveStatus>PUMP1_DriveStatus, ActOutputFrequencyMonitor>PV_PUMP1_ActOutFreqMonitor)
  ST(PUMP1_Active)
Variante semplice senza inverter (Scrubber FL530): catena abilitazioni + /IN_TERMICO_P1 -> TON 5s -> ST(PUMP1_Active) ST(OUT_PUMP_1)

## 3. CONTAORE DI FUNZIONAMENTO (pattern standard, 1 rung per utenza)
'CONTEGGIO ORE POMPA n'
  LD(IN_MARCIA) LD(PUMPn_Active) LD(^Clock_1Min) F:@Inc(InOut=PV_Minuti_PUMPn)

## 4. DOSAGGIO ON/OFF CICLICO con FB "Contatore" (pH, conducibilita)
'SOLUZIONE: VERIFICA PH' [Scrubber Ammoniaca/Elettrovalvole]
  LD(PUMP1_Active) LD(PUMP2_Active) FB:TON[Tim_Pump_Attiva](PT=T#10S)
  LD(Enable_Dosaggio) LD(/Allarme_Bit[27]) LD(IN_LIV_SIC_TANK) F:>(In1=PV_Ph,In2=SET_PH)
  LD(/Cnt_1.End_Conteggio) -> ST(Dosaggio_Auto)
  LD(/Cnt_2.End_Conteggio) FB:Contatore[Cnt_1](SET_VALUE=SET_PH_Time_Pompa_ON,VALUE=PV_Cnt_1)
  LD(Cnt_1.End_Conteggio)  FB:Contatore[Cnt_2](SET_VALUE=SET_PH_Time_Pompa_OFF,VALUE=PV_Cnt_2)
FB custom "Contatore": conteggio con SET_VALUE/VALUE e uscita .End_Conteggio (in quasi tutti i progetti; anche Contatore_Full, Cnt_Min_Sec).

## 5. SCALATURA INGRESSO ANALOGICO (pattern standard NX1P2, 0-8000 grezzi)
'SCALO INGRESSO ANALOGICO n'
  LD(P_On) F:LIMIT(MN=int#0,In=ANALOG_IN_n,MX=int#8000 > ANALOG_IN_n_Limit)
  F:INT_TO_REAL(> PV_Analogn_Real)
  F:ScaleTrans(SclIn=PV_Analogn_Real, X0=real#0,Y0=real#0, X1=real#8000, Y1=real#<fondoscala> > PV_<grandezza>)
Esempi fondoscala: pH 14.00, conducibilita 2000, pressione Dwyer 1000 Pa.

## 6. ANALOGICA CON MEDIA MOBILE (aspirazioni, pressioni rumorose)
  LD(P_On) F:INT_TO_REAL F:Get100msClk + F:@MovingAverage(Buf=Buffer[0],BufSize=uint#100 > Average)
  F:>(soglia 400) F:ScaleTrans(Average, 400..2000 -> 0..1000 > PV) ; sotto soglia: F:MOVE(0 > PV)

## 7. RITARDO ALLA DISECCITAZIONE (TOF)
'BIT MACCHINA PIENA': OR di presenze -> FB:TOF[TIM32](PT=TIME#20S) -> ST(Bit_Macchina_Piena)
'EV CARICO H2O': LD(/IN_EMERGENZA) LD(Mem_DI_V1) LD(Tim_Refill.Q) FB:TOF[Toff_Refill](PT=t#2s) -> ST(OUT_DI_TANK)

## 8. REGOLAZIONE PID (PIDAT) + USCITA PROPORZIONALE NEL TEMPO
  LD(Marcia_ON) LD(abilitazioni...) FB:PIDAT[PID_x](PV=Real_PV_x, SP=Real_SET_x, ManCtl/StartAT/OprSetParams/InitSetParams,
     PBand/ITime/DTime in&out (persistenza autotuning), MV>PID_MV) ST(AT_Done)
  FB:TimeProportionalOut[TimeProp_x](AIn=PID_MV, CtlPrd=time#1s..2s, MinPlsWidth=1) -> ST(Out_Riscaldamento)

## 9. MODBUS TCP SERVER (supervisione/SCADA)
  LD(_EIP_EtnOnlineSta) FB:MTCP_Server_NJNX[ModbusTCP_Server](Registers=Modbus_Registers, Coils=Modbus_Coils,
     Local_TcpPort=UINT#502, ConnectionTimeout=T#60s | TCP_Status>Server_Status, IP_Client>...) -> ST(Client_Connected)
Nota NX102 porta 2: usare _EIP2_EtnOnlineSta.

## 10. ABILITAZIONE SERVO (motion)
  LD(Tim_Marcia.Q) LD(/Allarme_Bit[7]) LD(MC_X.DrvStatus.Ready) LD(MC_Y.DrvStatus.Ready) LD(MC_X.DrvStatus.MainPower) LD(MC_Y.DrvStatus.MainPower)
  FB:MC_Power[Power_x](Axis=MC_X) FB:MC_Power[Power_y](Axis=MC_Y)

## Convenzioni di denominazione SYNTECH (ricorrenti in tutti i progetti)
IN_* ingressi fisici (IN_MARCIA, IN_EMERGENZA, IN_LIV_*, IN_TERMICO_*) | OUT_* uscite (OUT_PUMP_1, OUT_DI_TANK)
PV_* valori di processo | SET_* setpoint | Mem_* memorie | Tim_* istanze TON/TOF | Cnt_* istanze Contatore
Enable_* consensi | *_Active stati | Allarme_Bit[n] array allarmi | P_On sempre attivo | Clock_1Min/1Sec

## Sezioni tipiche di un progetto SYNTECH
Pompe, Elettrovalvole, Analogiche, Allarmi, Memorie_Vasche, Ricette, Server/Modbus, Marcia_Robot (se motion)

## Come usare la libreria con il server MCP sysmac-ladder
1. Per IMPORTARE un circuito: serve il template in formato ladderSnippetXML -> aprire un progetto che lo contiene,
   selezionare il rung e usare sysmac_copy_rung() per salvarne l XML in sysmac-mcp\templates\<nome>.xml (da fare una volta per pattern).
2. In alternativa (futuro): convertitore JSON rung -> ladderSnippetXML (il JSON e gia tutto in catalog.json).
3. La logica esatta di OGNI rung dei 102 progetti e consultabile in catalog.json (progetto -> sezione -> rung -> contatti/bobine/FB).

## Aggiornamento 26/08/2026
- Il miner ora estrae anche i blocchi **ST inline** dei rung (__type=IST, campo TXT) nel campo `st`: 1.229 rung su 18.929 li contengono. Senza questi si perdono i calcoli (quote di movimentazione, trasferimenti dati, scalature).
- Nuovo pattern documentato: **movimentazione interpolata a gruppo assi** (MC_GroupEnable + catena MC_MoveLinearAbsolute/Relative in blending), estratto da Hydra_Sonic_40_2g_V1. Scheda completa in `C:\Users\tecni\Claude\memory\movimentazione-interpolata-gruppo-assi.md`.

