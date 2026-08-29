//==========================================================================
//  SEZIONE SERVIZI
//==========================================================================

// SERVIZI DI IMPIANTO: aria, aspirazione, acqua DI, termico
Mem_Impianto_Ok := IN_Press_Aria AND IN_Aspirazione AND IN_DIW_Press AND IN_Termico_Gen;

// FILTRO SUI SERVIZI: devono restare presenti per 2 s
Tim_Debounce(In := Mem_Impianto_Ok, PT := T#2s);

// CONSENSI DI SICUREZZA
Consensi := NOT IN_Emergenza AND IN_Protezioni AND Tim_Debounce.Q;

// PORTELLI CHIUSI: consenso al ciclo automatico
OUT_Blocco_Portelli := IN_Portello_1 AND IN_Portello_2 AND Consensi;

// ANOMALIA BLOCCANTE
Mem_Anomalia := (NOT Consensi OR V_S_All_Robot OR V_S_All_Timeout OR V_S_All_Portello OR V_S_All_Ricetta);

// MACCHINA PRONTA
V_L_Pronto := Consensi AND NOT Mem_Anomalia AND Mem_Ricetta_Ok;

// MANUALE: traslazione avanti in semiautomatico
Man_Avanti := V_S_Semiauto AND NOT Mem_Ciclo AND Consensi AND V_P_Start AND IN_Robot_Alto;

// MANUALE: traslazione indietro in semiautomatico
Man_Indietro := V_S_Semiauto AND NOT Mem_Ciclo AND Consensi AND V_P_Stop AND IN_Robot_Alto;

//==========================================================================
//  SEZIONE RICETTA
//==========================================================================

// RICETTA: acquisizione della selezione da SCADA
IF NOT Mem_Ciclo THEN
    V_S_Ricetta_Att := V_S_Ricetta_Sel;
END_IF;

// RICETTA: la vasca 1 e' usata se ha un passo assegnato
V_S_Usa_V1 := (V_S_Passo_V1 > 0);

// CHECK RICETTA: la vasca 1 usata deve essere pronta
IF V_S_Usa_V1 AND NOT Rdy_V1 AND Mem_Ciclo THEN
    V_S_All_Ricetta := TRUE;
END_IF;

// CHECK RICETTA: la vasca 1 usata deve avere un tempo
IF V_S_Usa_V1 AND (V_S_Passo_V1 = 0) THEN
    V_S_All_Ricetta := TRUE;
END_IF;

// CHECK RICETTA: soluzione vasca 1 esaurita
V_S_Soluzione_Vecchia_V1 := (V_S_Cicli_V1 >= SET_Cicli_Max_V1);

// CHECK RICETTA: vasca 1 con soluzione vecchia non parte
IF V_S_Usa_V1 AND V_S_Soluzione_Vecchia_V1 AND (V_P_Start AND NOT _fp_V_P_Start) THEN
    V_S_All_Ricetta := TRUE;
END_IF;

// RICETTA: la vasca 2 e' usata se ha un passo assegnato
V_S_Usa_V2 := (V_S_Passo_V2 > 0);

// CHECK RICETTA: la vasca 2 usata deve essere pronta
IF V_S_Usa_V2 AND NOT Rdy_V2 AND Mem_Ciclo THEN
    V_S_All_Ricetta := TRUE;
END_IF;

// CHECK RICETTA: la vasca 2 usata deve avere un tempo
IF V_S_Usa_V2 AND (V_S_Passo_V2 = 0) THEN
    V_S_All_Ricetta := TRUE;
END_IF;

// CHECK RICETTA: soluzione vasca 2 esaurita
V_S_Soluzione_Vecchia_V2 := (V_S_Cicli_V2 >= SET_Cicli_Max_V2);

// CHECK RICETTA: vasca 2 con soluzione vecchia non parte
IF V_S_Usa_V2 AND V_S_Soluzione_Vecchia_V2 AND (V_P_Start AND NOT _fp_V_P_Start) THEN
    V_S_All_Ricetta := TRUE;
END_IF;

// RICETTA: la vasca 3 e' usata se ha un passo assegnato
V_S_Usa_V3 := (V_S_Passo_V3 > 0);

// CHECK RICETTA: la vasca 3 usata deve essere pronta
IF V_S_Usa_V3 AND NOT Rdy_V3 AND Mem_Ciclo THEN
    V_S_All_Ricetta := TRUE;
END_IF;

// CHECK RICETTA: la vasca 3 usata deve avere un tempo
IF V_S_Usa_V3 AND (V_S_Passo_V3 = 0) THEN
    V_S_All_Ricetta := TRUE;
END_IF;

// CHECK RICETTA: soluzione vasca 3 esaurita
V_S_Soluzione_Vecchia_V3 := (V_S_Cicli_V3 >= SET_Cicli_Max_V3);

// CHECK RICETTA: vasca 3 con soluzione vecchia non parte
IF V_S_Usa_V3 AND V_S_Soluzione_Vecchia_V3 AND (V_P_Start AND NOT _fp_V_P_Start) THEN
    V_S_All_Ricetta := TRUE;
END_IF;

// RICETTA: la vasca 4 e' usata se ha un passo assegnato
V_S_Usa_V4 := (V_S_Passo_V4 > 0);

// CHECK RICETTA: la vasca 4 usata deve essere pronta
IF V_S_Usa_V4 AND NOT Rdy_V4 AND Mem_Ciclo THEN
    V_S_All_Ricetta := TRUE;
END_IF;

// CHECK RICETTA: la vasca 4 usata deve avere un tempo
IF V_S_Usa_V4 AND (V_S_Passo_V4 = 0) THEN
    V_S_All_Ricetta := TRUE;
END_IF;

// CHECK RICETTA: soluzione vasca 4 esaurita
V_S_Soluzione_Vecchia_V4 := (V_S_Cicli_V4 >= SET_Cicli_Max_V4);

// CHECK RICETTA: vasca 4 con soluzione vecchia non parte
IF V_S_Usa_V4 AND V_S_Soluzione_Vecchia_V4 AND (V_P_Start AND NOT _fp_V_P_Start) THEN
    V_S_All_Ricetta := TRUE;
END_IF;

// RICETTA: la vasca 5 e' usata se ha un passo assegnato
V_S_Usa_V5 := (V_S_Passo_V5 > 0);

// CHECK RICETTA: la vasca 5 usata deve essere pronta
IF V_S_Usa_V5 AND NOT Rdy_V5 AND Mem_Ciclo THEN
    V_S_All_Ricetta := TRUE;
END_IF;

// CHECK RICETTA: la vasca 5 usata deve avere un tempo
IF V_S_Usa_V5 AND (V_S_Passo_V5 = 0) THEN
    V_S_All_Ricetta := TRUE;
END_IF;

// CHECK RICETTA: soluzione vasca 5 esaurita
V_S_Soluzione_Vecchia_V5 := (V_S_Cicli_V5 >= SET_Cicli_Max_V5);

// CHECK RICETTA: vasca 5 con soluzione vecchia non parte
IF V_S_Usa_V5 AND V_S_Soluzione_Vecchia_V5 AND (V_P_Start AND NOT _fp_V_P_Start) THEN
    V_S_All_Ricetta := TRUE;
END_IF;

// RICETTA: la vasca 6 e' usata se ha un passo assegnato
V_S_Usa_V6 := (V_S_Passo_V6 > 0);

// CHECK RICETTA: la vasca 6 usata deve essere pronta
IF V_S_Usa_V6 AND NOT Rdy_V6 AND Mem_Ciclo THEN
    V_S_All_Ricetta := TRUE;
END_IF;

// CHECK RICETTA: la vasca 6 usata deve avere un tempo
IF V_S_Usa_V6 AND (V_S_Passo_V6 = 0) THEN
    V_S_All_Ricetta := TRUE;
END_IF;

// CHECK RICETTA: soluzione vasca 6 esaurita
V_S_Soluzione_Vecchia_V6 := (V_S_Cicli_V6 >= SET_Cicli_Max_V6);

// CHECK RICETTA: vasca 6 con soluzione vecchia non parte
IF V_S_Usa_V6 AND V_S_Soluzione_Vecchia_V6 AND (V_P_Start AND NOT _fp_V_P_Start) THEN
    V_S_All_Ricetta := TRUE;
END_IF;

// RICETTA: la vasca 7 e' usata se ha un passo assegnato
V_S_Usa_V7 := (V_S_Passo_V7 > 0);

// CHECK RICETTA: la vasca 7 usata deve essere pronta
IF V_S_Usa_V7 AND NOT Rdy_V7 AND Mem_Ciclo THEN
    V_S_All_Ricetta := TRUE;
END_IF;

// CHECK RICETTA: la vasca 7 usata deve avere un tempo
IF V_S_Usa_V7 AND (V_S_Passo_V7 = 0) THEN
    V_S_All_Ricetta := TRUE;
END_IF;

// CHECK RICETTA: soluzione vasca 7 esaurita
V_S_Soluzione_Vecchia_V7 := (V_S_Cicli_V7 >= SET_Cicli_Max_V7);

// CHECK RICETTA: vasca 7 con soluzione vecchia non parte
IF V_S_Usa_V7 AND V_S_Soluzione_Vecchia_V7 AND (V_P_Start AND NOT _fp_V_P_Start) THEN
    V_S_All_Ricetta := TRUE;
END_IF;

// RICETTA: la vasca 8 e' usata se ha un passo assegnato
V_S_Usa_V8 := (V_S_Passo_V8 > 0);

// CHECK RICETTA: la vasca 8 usata deve essere pronta
IF V_S_Usa_V8 AND NOT Rdy_V8 AND Mem_Ciclo THEN
    V_S_All_Ricetta := TRUE;
END_IF;

// CHECK RICETTA: la vasca 8 usata deve avere un tempo
IF V_S_Usa_V8 AND (V_S_Passo_V8 = 0) THEN
    V_S_All_Ricetta := TRUE;
END_IF;

// CHECK RICETTA: soluzione vasca 8 esaurita
V_S_Soluzione_Vecchia_V8 := (V_S_Cicli_V8 >= SET_Cicli_Max_V8);

// CHECK RICETTA: vasca 8 con soluzione vecchia non parte
IF V_S_Usa_V8 AND V_S_Soluzione_Vecchia_V8 AND (V_P_Start AND NOT _fp_V_P_Start) THEN
    V_S_All_Ricetta := TRUE;
END_IF;

// RICETTA: la vasca 9 e' usata se ha un passo assegnato
V_S_Usa_V9 := (V_S_Passo_V9 > 0);

// CHECK RICETTA: la vasca 9 usata deve essere pronta
IF V_S_Usa_V9 AND NOT Rdy_V9 AND Mem_Ciclo THEN
    V_S_All_Ricetta := TRUE;
END_IF;

// CHECK RICETTA: la vasca 9 usata deve avere un tempo
IF V_S_Usa_V9 AND (V_S_Passo_V9 = 0) THEN
    V_S_All_Ricetta := TRUE;
END_IF;

// CHECK RICETTA: soluzione vasca 9 esaurita
V_S_Soluzione_Vecchia_V9 := (V_S_Cicli_V9 >= SET_Cicli_Max_V9);

// CHECK RICETTA: vasca 9 con soluzione vecchia non parte
IF V_S_Usa_V9 AND V_S_Soluzione_Vecchia_V9 AND (V_P_Start AND NOT _fp_V_P_Start) THEN
    V_S_All_Ricetta := TRUE;
END_IF;

// RICETTA CONGRUENTE: nessun allarme di congruenza
Mem_Ricetta_Ok := NOT V_S_All_Ricetta AND (V_S_Ricetta_Att > 0);

// RESET ALLARME RICETTA
IF (V_P_Reset AND NOT _fp_V_P_Reset) THEN
    V_S_All_Ricetta := FALSE;
END_IF;

//==========================================================================
//  SEZIONE CICLI
//==========================================================================

// AZZERAMENTO PASSI A INIZIO CICLO
IF (V_P_Start AND NOT _fp_V_P_Start) THEN
    End_V1 := FALSE;
    End_V2 := FALSE;
    End_V3 := FALSE;
    End_V4 := FALSE;
    End_V5 := FALSE;
    End_V6 := FALSE;
    End_V7 := FALSE;
    End_V8 := FALSE;
    End_V9 := FALSE;
    Mem_Fine := FALSE;
    Mem_Rob_Estrai := FALSE;
END_IF;

// START CICLO AUTOMATICO
IF (V_P_Start AND NOT _fp_V_P_Start) AND Consensi AND V_S_Auto AND Mem_Ricetta_Ok AND IN_Cesto_Carico AND NOT Mem_Anomalia AND NOT Mem_Rob_Muove THEN
    Mem_Fine := FALSE;
    Mem_Ciclo := TRUE;
END_IF;

// ARRESTO CICLO
IF ((V_P_Stop AND NOT _fp_V_P_Stop) OR Mem_Anomalia OR Mem_Fine) THEN
    Mem_Ciclo := FALSE;
END_IF;

// PAUSA CICLO
IF (V_P_Pausa AND NOT _fp_V_P_Pausa) AND Mem_Ciclo THEN
    Mem_Pausa := TRUE;
END_IF;

// RIPRESA DALLA PAUSA
IF (V_P_Start AND NOT _fp_V_P_Start) AND Mem_Pausa THEN
    Mem_Pausa := FALSE;
END_IF;

// PASSO DI RICETTA IN CORSO
V_L_Ciclo := (Mem_V1 OR Mem_V2 OR Mem_V3 OR Mem_V4 OR Mem_V5 OR Mem_V6 OR Mem_V7 OR Mem_V8 OR Mem_V9);

// INGRESSO IN VASCA 1
IF Mem_Ciclo AND NOT Mem_Pausa AND Mem_Cesto AND V_S_Usa_V1 AND IN_Robot_Su_V1 AND IN_Robot_Basso AND Mem_Cesto AND NOT End_V1 AND Rdy_V1 THEN
    Mem_V1 := TRUE;
END_IF;

// PERMANENZA IN VASCA 1
Tim_Perm_V1(In := Mem_V1 AND NOT Mem_Pausa, PT := SET_T_Perm_V1);

// USCITA DALLA VASCA 1 (o salto se non in ricetta)
IF (Tim_Perm_V1.Q OR NOT V_S_Usa_V1) AND (Mem_V1 OR (Mem_Ciclo AND NOT V_S_Usa_V1 AND Mem_Cesto)) THEN
    End_V1 := TRUE;
    Mem_V1 := FALSE;
END_IF;

// CONTEGGIO CICLI DELLA SOLUZIONE IN VASCA 1
IF (End_V1 AND NOT _fp_End_V1) AND V_S_Usa_V1 THEN
    V_S_Cicli_V1 := V_S_Cicli_V1 + 1;
END_IF;

// INGRESSO IN VASCA 2
IF Mem_Ciclo AND NOT Mem_Pausa AND Mem_Cesto AND V_S_Usa_V2 AND IN_Robot_Su_V2 AND IN_Robot_Basso AND End_V1 AND NOT End_V2 AND Rdy_V2 THEN
    Mem_V2 := TRUE;
END_IF;

// PERMANENZA IN VASCA 2
Tim_Perm_V2(In := Mem_V2 AND NOT Mem_Pausa, PT := SET_T_Perm_V2);

// USCITA DALLA VASCA 2 (o salto se non in ricetta)
IF (Tim_Perm_V2.Q OR NOT V_S_Usa_V2) AND (Mem_V2 OR (Mem_Ciclo AND NOT V_S_Usa_V2 AND End_V1)) THEN
    End_V2 := TRUE;
    Mem_V2 := FALSE;
END_IF;

// CONTEGGIO CICLI DELLA SOLUZIONE IN VASCA 2
IF (End_V2 AND NOT _fp_End_V2) AND V_S_Usa_V2 THEN
    V_S_Cicli_V2 := V_S_Cicli_V2 + 1;
END_IF;

// INGRESSO IN VASCA 3
IF Mem_Ciclo AND NOT Mem_Pausa AND Mem_Cesto AND V_S_Usa_V3 AND IN_Robot_Su_V3 AND IN_Robot_Basso AND End_V2 AND NOT End_V3 AND Rdy_V3 THEN
    Mem_V3 := TRUE;
END_IF;

// PERMANENZA IN VASCA 3
Tim_Perm_V3(In := Mem_V3 AND NOT Mem_Pausa, PT := SET_T_Perm_V3);

// USCITA DALLA VASCA 3 (o salto se non in ricetta)
IF (Tim_Perm_V3.Q OR NOT V_S_Usa_V3) AND (Mem_V3 OR (Mem_Ciclo AND NOT V_S_Usa_V3 AND End_V2)) THEN
    End_V3 := TRUE;
    Mem_V3 := FALSE;
END_IF;

// CONTEGGIO CICLI DELLA SOLUZIONE IN VASCA 3
IF (End_V3 AND NOT _fp_End_V3) AND V_S_Usa_V3 THEN
    V_S_Cicli_V3 := V_S_Cicli_V3 + 1;
END_IF;

// INGRESSO IN VASCA 4
IF Mem_Ciclo AND NOT Mem_Pausa AND Mem_Cesto AND V_S_Usa_V4 AND IN_Robot_Su_V4 AND IN_Robot_Basso AND End_V3 AND NOT End_V4 AND Rdy_V4 THEN
    Mem_V4 := TRUE;
END_IF;

// PERMANENZA IN VASCA 4
Tim_Perm_V4(In := Mem_V4 AND NOT Mem_Pausa, PT := SET_T_Perm_V4);

// USCITA DALLA VASCA 4 (o salto se non in ricetta)
IF (Tim_Perm_V4.Q OR NOT V_S_Usa_V4) AND (Mem_V4 OR (Mem_Ciclo AND NOT V_S_Usa_V4 AND End_V3)) THEN
    End_V4 := TRUE;
    Mem_V4 := FALSE;
END_IF;

// CONTEGGIO CICLI DELLA SOLUZIONE IN VASCA 4
IF (End_V4 AND NOT _fp_End_V4) AND V_S_Usa_V4 THEN
    V_S_Cicli_V4 := V_S_Cicli_V4 + 1;
END_IF;

// INGRESSO IN VASCA 5
IF Mem_Ciclo AND NOT Mem_Pausa AND Mem_Cesto AND V_S_Usa_V5 AND IN_Robot_Su_V5 AND IN_Robot_Basso AND End_V4 AND NOT End_V5 AND Rdy_V5 THEN
    Mem_V5 := TRUE;
END_IF;

// PERMANENZA IN VASCA 5
Tim_Perm_V5(In := Mem_V5 AND NOT Mem_Pausa, PT := SET_T_Perm_V5);

// USCITA DALLA VASCA 5 (o salto se non in ricetta)
IF (Tim_Perm_V5.Q OR NOT V_S_Usa_V5) AND (Mem_V5 OR (Mem_Ciclo AND NOT V_S_Usa_V5 AND End_V4)) THEN
    End_V5 := TRUE;
    Mem_V5 := FALSE;
END_IF;

// CONTEGGIO CICLI DELLA SOLUZIONE IN VASCA 5
IF (End_V5 AND NOT _fp_End_V5) AND V_S_Usa_V5 THEN
    V_S_Cicli_V5 := V_S_Cicli_V5 + 1;
END_IF;

// INGRESSO IN VASCA 6
IF Mem_Ciclo AND NOT Mem_Pausa AND Mem_Cesto AND V_S_Usa_V6 AND IN_Robot_Su_V6 AND IN_Robot_Basso AND End_V5 AND NOT End_V6 AND Rdy_V6 THEN
    Mem_V6 := TRUE;
END_IF;

// PERMANENZA IN VASCA 6
Tim_Perm_V6(In := Mem_V6 AND NOT Mem_Pausa, PT := SET_T_Perm_V6);

// USCITA DALLA VASCA 6 (o salto se non in ricetta)
IF (Tim_Perm_V6.Q OR NOT V_S_Usa_V6) AND (Mem_V6 OR (Mem_Ciclo AND NOT V_S_Usa_V6 AND End_V5)) THEN
    End_V6 := TRUE;
    Mem_V6 := FALSE;
END_IF;

// CONTEGGIO CICLI DELLA SOLUZIONE IN VASCA 6
IF (End_V6 AND NOT _fp_End_V6) AND V_S_Usa_V6 THEN
    V_S_Cicli_V6 := V_S_Cicli_V6 + 1;
END_IF;

// INGRESSO IN VASCA 7
IF Mem_Ciclo AND NOT Mem_Pausa AND Mem_Cesto AND V_S_Usa_V7 AND IN_Robot_Su_V7 AND IN_Robot_Basso AND End_V6 AND NOT End_V7 AND Rdy_V7 THEN
    Mem_V7 := TRUE;
END_IF;

// PERMANENZA IN VASCA 7
Tim_Perm_V7(In := Mem_V7 AND NOT Mem_Pausa, PT := SET_T_Perm_V7);

// USCITA DALLA VASCA 7 (o salto se non in ricetta)
IF (Tim_Perm_V7.Q OR NOT V_S_Usa_V7) AND (Mem_V7 OR (Mem_Ciclo AND NOT V_S_Usa_V7 AND End_V6)) THEN
    End_V7 := TRUE;
    Mem_V7 := FALSE;
END_IF;

// CONTEGGIO CICLI DELLA SOLUZIONE IN VASCA 7
IF (End_V7 AND NOT _fp_End_V7) AND V_S_Usa_V7 THEN
    V_S_Cicli_V7 := V_S_Cicli_V7 + 1;
END_IF;

// INGRESSO IN VASCA 8
IF Mem_Ciclo AND NOT Mem_Pausa AND Mem_Cesto AND V_S_Usa_V8 AND IN_Robot_Su_V8 AND IN_Robot_Basso AND End_V7 AND NOT End_V8 AND Rdy_V8 THEN
    Mem_V8 := TRUE;
END_IF;

// PERMANENZA IN VASCA 8
Tim_Perm_V8(In := Mem_V8 AND NOT Mem_Pausa, PT := SET_T_Perm_V8);

// USCITA DALLA VASCA 8 (o salto se non in ricetta)
IF (Tim_Perm_V8.Q OR NOT V_S_Usa_V8) AND (Mem_V8 OR (Mem_Ciclo AND NOT V_S_Usa_V8 AND End_V7)) THEN
    End_V8 := TRUE;
    Mem_V8 := FALSE;
END_IF;

// CONTEGGIO CICLI DELLA SOLUZIONE IN VASCA 8
IF (End_V8 AND NOT _fp_End_V8) AND V_S_Usa_V8 THEN
    V_S_Cicli_V8 := V_S_Cicli_V8 + 1;
END_IF;

// INGRESSO IN VASCA 9
IF Mem_Ciclo AND NOT Mem_Pausa AND Mem_Cesto AND V_S_Usa_V9 AND IN_Robot_Su_V9 AND IN_Robot_Basso AND End_V8 AND NOT End_V9 AND Rdy_V9 THEN
    Mem_V9 := TRUE;
END_IF;

// PERMANENZA IN VASCA 9
Tim_Perm_V9(In := Mem_V9 AND NOT Mem_Pausa, PT := SET_T_Perm_V9);

// USCITA DALLA VASCA 9 (o salto se non in ricetta)
IF (Tim_Perm_V9.Q OR NOT V_S_Usa_V9) AND (Mem_V9 OR (Mem_Ciclo AND NOT V_S_Usa_V9 AND End_V8)) THEN
    End_V9 := TRUE;
    Mem_V9 := FALSE;
END_IF;

// CONTEGGIO CICLI DELLA SOLUZIONE IN VASCA 9
IF (End_V9 AND NOT _fp_End_V9) AND V_S_Usa_V9 THEN
    V_S_Cicli_V9 := V_S_Cicli_V9 + 1;
END_IF;

// CICLO COMPLETATO
IF Mem_Ciclo AND End_V9 AND NOT Mem_Cesto THEN
    Mem_Fine := TRUE;
END_IF;

// CONTEGGIO CESTI PROCESSATI
IF (Mem_Fine AND NOT _fp_Mem_Fine) THEN
    V_S_Cesti_Fatti := V_S_Cesti_Fatti + 1;
END_IF;

// SPIA FINE CICLO
V_L_Fine_Ciclo := Mem_Fine;

// SPIA PAUSA
V_L_Pausa := Mem_Pausa;

//==========================================================================
//  SEZIONE VASCHE
//==========================================================================

// VASCA 1 - RICHIESTA DI CARICO SOTTO IL MINIMO
IF NOT IN_Liv_Min_V1 AND Consensi AND NOT V_S_All_Liv_V1 THEN
    Req_Carico_V1 := TRUE;
END_IF;

// VASCA 1 - FINE CARICO AL MASSIMO
IF (IN_Liv_Max_V1 OR NOT Consensi) THEN
    Req_Carico_V1 := FALSE;
END_IF;

// VASCA 1 - ELETTROVALVOLA DI CARICO
OUT_Carico_V1 := Req_Carico_V1 AND IN_DIW_Press AND Consensi AND NOT Mem_V1;

// VASCA 1 - SORVEGLIANZA TEMPO DI CARICO
Tim_Carico_V1(In := OUT_Carico_V1, PT := SET_T_Carico_V1);

// VASCA 1 - ALLARME CARICO NON RIUSCITO
IF Tim_Carico_V1.Q THEN
    V_S_All_Carico_V1 := TRUE;
END_IF;

// VASCA 1 - RICHIESTA DI SCARICO SOLUZIONE ESAURITA
IF V_S_Soluzione_Vecchia_V1 AND NOT Mem_Ciclo AND Consensi THEN
    Req_Scarico_V1 := TRUE;
END_IF;

// VASCA 1 - FINE SCARICO SOTTO IL MINIMO
IF (NOT IN_Liv_Min_V1 OR NOT Consensi) THEN
    Req_Scarico_V1 := FALSE;
END_IF;

// VASCA 1 - ELETTROVALVOLA DI SCARICO
OUT_Scarico_V1 := Req_Scarico_V1 AND Consensi AND NOT OUT_Carico_V1;

// VASCA 1 - AZZERAMENTO CICLI DOPO IL CAMBIO SOLUZIONE
IF (Req_Scarico_V1 AND NOT _fp_Req_Scarico_V1) AND IN_Liv_Max_V1 THEN
    V_S_Cicli_V1 := 0;
END_IF;

// VASCA 1 - POMPA DI RICIRCOLO
OUT_Pompa_V1 := IN_Liv_Min_V1 AND Consensi AND NOT Req_Scarico_V1;

// VASCA 1 - RISCALDAMENTO
OUT_Risc_V1 := IN_Liv_Min_V1 AND NOT IN_Temp_Ok_V1 AND NOT IN_Temp_Alta_V1 AND OUT_Pompa_V1 AND Consensi;

// VASCA 1 - PRONTA AL PROCESSO
Rdy_V1 := IN_Liv_Min_V1 AND IN_Temp_Ok_V1 AND IN_Ricircolo_V1 AND NOT V_S_Soluzione_Vecchia_V1;

// VASCA 1 - SPIA PRONTA
V_L_Vasca_Ready_V1 := Rdy_V1;

// VASCA 2 - RICHIESTA DI CARICO SOTTO IL MINIMO
IF NOT IN_Liv_Min_V2 AND Consensi AND NOT V_S_All_Liv_V2 THEN
    Req_Carico_V2 := TRUE;
END_IF;

// VASCA 2 - FINE CARICO AL MASSIMO
IF (IN_Liv_Max_V2 OR NOT Consensi) THEN
    Req_Carico_V2 := FALSE;
END_IF;

// VASCA 2 - ELETTROVALVOLA DI CARICO
OUT_Carico_V2 := Req_Carico_V2 AND IN_DIW_Press AND Consensi AND NOT Mem_V2;

// VASCA 2 - SORVEGLIANZA TEMPO DI CARICO
Tim_Carico_V2(In := OUT_Carico_V2, PT := SET_T_Carico_V2);

// VASCA 2 - ALLARME CARICO NON RIUSCITO
IF Tim_Carico_V2.Q THEN
    V_S_All_Carico_V2 := TRUE;
END_IF;

// VASCA 2 - RICHIESTA DI SCARICO SOLUZIONE ESAURITA
IF V_S_Soluzione_Vecchia_V2 AND NOT Mem_Ciclo AND Consensi THEN
    Req_Scarico_V2 := TRUE;
END_IF;

// VASCA 2 - FINE SCARICO SOTTO IL MINIMO
IF (NOT IN_Liv_Min_V2 OR NOT Consensi) THEN
    Req_Scarico_V2 := FALSE;
END_IF;

// VASCA 2 - ELETTROVALVOLA DI SCARICO
OUT_Scarico_V2 := Req_Scarico_V2 AND Consensi AND NOT OUT_Carico_V2;

// VASCA 2 - AZZERAMENTO CICLI DOPO IL CAMBIO SOLUZIONE
IF (Req_Scarico_V2 AND NOT _fp_Req_Scarico_V2) AND IN_Liv_Max_V2 THEN
    V_S_Cicli_V2 := 0;
END_IF;

// VASCA 2 - POMPA DI RICIRCOLO
OUT_Pompa_V2 := IN_Liv_Min_V2 AND Consensi AND NOT Req_Scarico_V2;

// VASCA 2 - RISCALDAMENTO
OUT_Risc_V2 := IN_Liv_Min_V2 AND NOT IN_Temp_Ok_V2 AND NOT IN_Temp_Alta_V2 AND OUT_Pompa_V2 AND Consensi;

// VASCA 2 - PRONTA AL PROCESSO
Rdy_V2 := IN_Liv_Min_V2 AND IN_Temp_Ok_V2 AND IN_Ricircolo_V2 AND NOT V_S_Soluzione_Vecchia_V2;

// VASCA 2 - SPIA PRONTA
V_L_Vasca_Ready_V2 := Rdy_V2;

// VASCA 3 - RICHIESTA DI CARICO SOTTO IL MINIMO
IF NOT IN_Liv_Min_V3 AND Consensi AND NOT V_S_All_Liv_V3 THEN
    Req_Carico_V3 := TRUE;
END_IF;

// VASCA 3 - FINE CARICO AL MASSIMO
IF (IN_Liv_Max_V3 OR NOT Consensi) THEN
    Req_Carico_V3 := FALSE;
END_IF;

// VASCA 3 - ELETTROVALVOLA DI CARICO
OUT_Carico_V3 := Req_Carico_V3 AND IN_DIW_Press AND Consensi AND NOT Mem_V3;

// VASCA 3 - SORVEGLIANZA TEMPO DI CARICO
Tim_Carico_V3(In := OUT_Carico_V3, PT := SET_T_Carico_V3);

// VASCA 3 - ALLARME CARICO NON RIUSCITO
IF Tim_Carico_V3.Q THEN
    V_S_All_Carico_V3 := TRUE;
END_IF;

// VASCA 3 - RICHIESTA DI SCARICO SOLUZIONE ESAURITA
IF V_S_Soluzione_Vecchia_V3 AND NOT Mem_Ciclo AND Consensi THEN
    Req_Scarico_V3 := TRUE;
END_IF;

// VASCA 3 - FINE SCARICO SOTTO IL MINIMO
IF (NOT IN_Liv_Min_V3 OR NOT Consensi) THEN
    Req_Scarico_V3 := FALSE;
END_IF;

// VASCA 3 - ELETTROVALVOLA DI SCARICO
OUT_Scarico_V3 := Req_Scarico_V3 AND Consensi AND NOT OUT_Carico_V3;

// VASCA 3 - AZZERAMENTO CICLI DOPO IL CAMBIO SOLUZIONE
IF (Req_Scarico_V3 AND NOT _fp_Req_Scarico_V3) AND IN_Liv_Max_V3 THEN
    V_S_Cicli_V3 := 0;
END_IF;

// VASCA 3 - POMPA DI RICIRCOLO
OUT_Pompa_V3 := IN_Liv_Min_V3 AND Consensi AND NOT Req_Scarico_V3;

// VASCA 3 - RISCALDAMENTO
OUT_Risc_V3 := IN_Liv_Min_V3 AND NOT IN_Temp_Ok_V3 AND NOT IN_Temp_Alta_V3 AND OUT_Pompa_V3 AND Consensi;

// VASCA 3 - PRONTA AL PROCESSO
Rdy_V3 := IN_Liv_Min_V3 AND IN_Temp_Ok_V3 AND IN_Ricircolo_V3 AND NOT V_S_Soluzione_Vecchia_V3;

// VASCA 3 - SPIA PRONTA
V_L_Vasca_Ready_V3 := Rdy_V3;

// VASCA 4 - RICHIESTA DI CARICO SOTTO IL MINIMO
IF NOT IN_Liv_Min_V4 AND Consensi AND NOT V_S_All_Liv_V4 THEN
    Req_Carico_V4 := TRUE;
END_IF;

// VASCA 4 - FINE CARICO AL MASSIMO
IF (IN_Liv_Max_V4 OR NOT Consensi) THEN
    Req_Carico_V4 := FALSE;
END_IF;

// VASCA 4 - ELETTROVALVOLA DI CARICO
OUT_Carico_V4 := Req_Carico_V4 AND IN_DIW_Press AND Consensi AND NOT Mem_V4;

// VASCA 4 - SORVEGLIANZA TEMPO DI CARICO
Tim_Carico_V4(In := OUT_Carico_V4, PT := SET_T_Carico_V4);

// VASCA 4 - ALLARME CARICO NON RIUSCITO
IF Tim_Carico_V4.Q THEN
    V_S_All_Carico_V4 := TRUE;
END_IF;

// VASCA 4 - RICHIESTA DI SCARICO SOLUZIONE ESAURITA
IF V_S_Soluzione_Vecchia_V4 AND NOT Mem_Ciclo AND Consensi THEN
    Req_Scarico_V4 := TRUE;
END_IF;

// VASCA 4 - FINE SCARICO SOTTO IL MINIMO
IF (NOT IN_Liv_Min_V4 OR NOT Consensi) THEN
    Req_Scarico_V4 := FALSE;
END_IF;

// VASCA 4 - ELETTROVALVOLA DI SCARICO
OUT_Scarico_V4 := Req_Scarico_V4 AND Consensi AND NOT OUT_Carico_V4;

// VASCA 4 - AZZERAMENTO CICLI DOPO IL CAMBIO SOLUZIONE
IF (Req_Scarico_V4 AND NOT _fp_Req_Scarico_V4) AND IN_Liv_Max_V4 THEN
    V_S_Cicli_V4 := 0;
END_IF;

// VASCA 4 - POMPA DI RICIRCOLO
OUT_Pompa_V4 := IN_Liv_Min_V4 AND Consensi AND NOT Req_Scarico_V4;

// VASCA 4 - RISCALDAMENTO
OUT_Risc_V4 := IN_Liv_Min_V4 AND NOT IN_Temp_Ok_V4 AND NOT IN_Temp_Alta_V4 AND OUT_Pompa_V4 AND Consensi;

// VASCA 4 - PRONTA AL PROCESSO
Rdy_V4 := IN_Liv_Min_V4 AND IN_Temp_Ok_V4 AND IN_Ricircolo_V4 AND NOT V_S_Soluzione_Vecchia_V4;

// VASCA 4 - SPIA PRONTA
V_L_Vasca_Ready_V4 := Rdy_V4;

// VASCA 5 - RICHIESTA DI CARICO SOTTO IL MINIMO
IF NOT IN_Liv_Min_V5 AND Consensi AND NOT V_S_All_Liv_V5 THEN
    Req_Carico_V5 := TRUE;
END_IF;

// VASCA 5 - FINE CARICO AL MASSIMO
IF (IN_Liv_Max_V5 OR NOT Consensi) THEN
    Req_Carico_V5 := FALSE;
END_IF;

// VASCA 5 - ELETTROVALVOLA DI CARICO
OUT_Carico_V5 := Req_Carico_V5 AND IN_DIW_Press AND Consensi AND NOT Mem_V5;

// VASCA 5 - SORVEGLIANZA TEMPO DI CARICO
Tim_Carico_V5(In := OUT_Carico_V5, PT := SET_T_Carico_V5);

// VASCA 5 - ALLARME CARICO NON RIUSCITO
IF Tim_Carico_V5.Q THEN
    V_S_All_Carico_V5 := TRUE;
END_IF;

// VASCA 5 - RICHIESTA DI SCARICO SOLUZIONE ESAURITA
IF V_S_Soluzione_Vecchia_V5 AND NOT Mem_Ciclo AND Consensi THEN
    Req_Scarico_V5 := TRUE;
END_IF;

// VASCA 5 - FINE SCARICO SOTTO IL MINIMO
IF (NOT IN_Liv_Min_V5 OR NOT Consensi) THEN
    Req_Scarico_V5 := FALSE;
END_IF;

// VASCA 5 - ELETTROVALVOLA DI SCARICO
OUT_Scarico_V5 := Req_Scarico_V5 AND Consensi AND NOT OUT_Carico_V5;

// VASCA 5 - AZZERAMENTO CICLI DOPO IL CAMBIO SOLUZIONE
IF (Req_Scarico_V5 AND NOT _fp_Req_Scarico_V5) AND IN_Liv_Max_V5 THEN
    V_S_Cicli_V5 := 0;
END_IF;

// VASCA 5 - POMPA DI RICIRCOLO
OUT_Pompa_V5 := IN_Liv_Min_V5 AND Consensi AND NOT Req_Scarico_V5;

// VASCA 5 - RISCALDAMENTO
OUT_Risc_V5 := IN_Liv_Min_V5 AND NOT IN_Temp_Ok_V5 AND NOT IN_Temp_Alta_V5 AND OUT_Pompa_V5 AND Consensi;

// VASCA 5 - PRONTA AL PROCESSO
Rdy_V5 := IN_Liv_Min_V5 AND IN_Temp_Ok_V5 AND IN_Ricircolo_V5 AND NOT V_S_Soluzione_Vecchia_V5;

// VASCA 5 - SPIA PRONTA
V_L_Vasca_Ready_V5 := Rdy_V5;

// VASCA 6 - RICHIESTA DI CARICO SOTTO IL MINIMO
IF NOT IN_Liv_Min_V6 AND Consensi AND NOT V_S_All_Liv_V6 THEN
    Req_Carico_V6 := TRUE;
END_IF;

// VASCA 6 - FINE CARICO AL MASSIMO
IF (IN_Liv_Max_V6 OR NOT Consensi) THEN
    Req_Carico_V6 := FALSE;
END_IF;

// VASCA 6 - ELETTROVALVOLA DI CARICO
OUT_Carico_V6 := Req_Carico_V6 AND IN_DIW_Press AND Consensi AND NOT Mem_V6;

// VASCA 6 - SORVEGLIANZA TEMPO DI CARICO
Tim_Carico_V6(In := OUT_Carico_V6, PT := SET_T_Carico_V6);

// VASCA 6 - ALLARME CARICO NON RIUSCITO
IF Tim_Carico_V6.Q THEN
    V_S_All_Carico_V6 := TRUE;
END_IF;

// VASCA 6 - RICHIESTA DI SCARICO SOLUZIONE ESAURITA
IF V_S_Soluzione_Vecchia_V6 AND NOT Mem_Ciclo AND Consensi THEN
    Req_Scarico_V6 := TRUE;
END_IF;

// VASCA 6 - FINE SCARICO SOTTO IL MINIMO
IF (NOT IN_Liv_Min_V6 OR NOT Consensi) THEN
    Req_Scarico_V6 := FALSE;
END_IF;

// VASCA 6 - ELETTROVALVOLA DI SCARICO
OUT_Scarico_V6 := Req_Scarico_V6 AND Consensi AND NOT OUT_Carico_V6;

// VASCA 6 - AZZERAMENTO CICLI DOPO IL CAMBIO SOLUZIONE
IF (Req_Scarico_V6 AND NOT _fp_Req_Scarico_V6) AND IN_Liv_Max_V6 THEN
    V_S_Cicli_V6 := 0;
END_IF;

// VASCA 6 - POMPA DI RICIRCOLO
OUT_Pompa_V6 := IN_Liv_Min_V6 AND Consensi AND NOT Req_Scarico_V6;

// VASCA 6 - RISCALDAMENTO
OUT_Risc_V6 := IN_Liv_Min_V6 AND NOT IN_Temp_Ok_V6 AND NOT IN_Temp_Alta_V6 AND OUT_Pompa_V6 AND Consensi;

// VASCA 6 - PRONTA AL PROCESSO
Rdy_V6 := IN_Liv_Min_V6 AND IN_Temp_Ok_V6 AND IN_Ricircolo_V6 AND NOT V_S_Soluzione_Vecchia_V6;

// VASCA 6 - SPIA PRONTA
V_L_Vasca_Ready_V6 := Rdy_V6;

// VASCA 7 - RICHIESTA DI CARICO SOTTO IL MINIMO
IF NOT IN_Liv_Min_V7 AND Consensi AND NOT V_S_All_Liv_V7 THEN
    Req_Carico_V7 := TRUE;
END_IF;

// VASCA 7 - FINE CARICO AL MASSIMO
IF (IN_Liv_Max_V7 OR NOT Consensi) THEN
    Req_Carico_V7 := FALSE;
END_IF;

// VASCA 7 - ELETTROVALVOLA DI CARICO
OUT_Carico_V7 := Req_Carico_V7 AND IN_DIW_Press AND Consensi AND NOT Mem_V7;

// VASCA 7 - SORVEGLIANZA TEMPO DI CARICO
Tim_Carico_V7(In := OUT_Carico_V7, PT := SET_T_Carico_V7);

// VASCA 7 - ALLARME CARICO NON RIUSCITO
IF Tim_Carico_V7.Q THEN
    V_S_All_Carico_V7 := TRUE;
END_IF;

// VASCA 7 - RICHIESTA DI SCARICO SOLUZIONE ESAURITA
IF V_S_Soluzione_Vecchia_V7 AND NOT Mem_Ciclo AND Consensi THEN
    Req_Scarico_V7 := TRUE;
END_IF;

// VASCA 7 - FINE SCARICO SOTTO IL MINIMO
IF (NOT IN_Liv_Min_V7 OR NOT Consensi) THEN
    Req_Scarico_V7 := FALSE;
END_IF;

// VASCA 7 - ELETTROVALVOLA DI SCARICO
OUT_Scarico_V7 := Req_Scarico_V7 AND Consensi AND NOT OUT_Carico_V7;

// VASCA 7 - AZZERAMENTO CICLI DOPO IL CAMBIO SOLUZIONE
IF (Req_Scarico_V7 AND NOT _fp_Req_Scarico_V7) AND IN_Liv_Max_V7 THEN
    V_S_Cicli_V7 := 0;
END_IF;

// VASCA 7 - POMPA DI RICIRCOLO
OUT_Pompa_V7 := IN_Liv_Min_V7 AND Consensi AND NOT Req_Scarico_V7;

// VASCA 7 - RISCALDAMENTO
OUT_Risc_V7 := IN_Liv_Min_V7 AND NOT IN_Temp_Ok_V7 AND NOT IN_Temp_Alta_V7 AND OUT_Pompa_V7 AND Consensi;

// VASCA 7 - PRONTA AL PROCESSO
Rdy_V7 := IN_Liv_Min_V7 AND IN_Temp_Ok_V7 AND IN_Ricircolo_V7 AND NOT V_S_Soluzione_Vecchia_V7;

// VASCA 7 - SPIA PRONTA
V_L_Vasca_Ready_V7 := Rdy_V7;

// VASCA 8 - RICHIESTA DI CARICO SOTTO IL MINIMO
IF NOT IN_Liv_Min_V8 AND Consensi AND NOT V_S_All_Liv_V8 THEN
    Req_Carico_V8 := TRUE;
END_IF;

// VASCA 8 - FINE CARICO AL MASSIMO
IF (IN_Liv_Max_V8 OR NOT Consensi) THEN
    Req_Carico_V8 := FALSE;
END_IF;

// VASCA 8 - ELETTROVALVOLA DI CARICO
OUT_Carico_V8 := Req_Carico_V8 AND IN_DIW_Press AND Consensi AND NOT Mem_V8;

// VASCA 8 - SORVEGLIANZA TEMPO DI CARICO
Tim_Carico_V8(In := OUT_Carico_V8, PT := SET_T_Carico_V8);

// VASCA 8 - ALLARME CARICO NON RIUSCITO
IF Tim_Carico_V8.Q THEN
    V_S_All_Carico_V8 := TRUE;
END_IF;

// VASCA 8 - RICHIESTA DI SCARICO SOLUZIONE ESAURITA
IF V_S_Soluzione_Vecchia_V8 AND NOT Mem_Ciclo AND Consensi THEN
    Req_Scarico_V8 := TRUE;
END_IF;

// VASCA 8 - FINE SCARICO SOTTO IL MINIMO
IF (NOT IN_Liv_Min_V8 OR NOT Consensi) THEN
    Req_Scarico_V8 := FALSE;
END_IF;

// VASCA 8 - ELETTROVALVOLA DI SCARICO
OUT_Scarico_V8 := Req_Scarico_V8 AND Consensi AND NOT OUT_Carico_V8;

// VASCA 8 - AZZERAMENTO CICLI DOPO IL CAMBIO SOLUZIONE
IF (Req_Scarico_V8 AND NOT _fp_Req_Scarico_V8) AND IN_Liv_Max_V8 THEN
    V_S_Cicli_V8 := 0;
END_IF;

// VASCA 8 - POMPA DI RICIRCOLO
OUT_Pompa_V8 := IN_Liv_Min_V8 AND Consensi AND NOT Req_Scarico_V8;

// VASCA 8 - RISCALDAMENTO
OUT_Risc_V8 := IN_Liv_Min_V8 AND NOT IN_Temp_Ok_V8 AND NOT IN_Temp_Alta_V8 AND OUT_Pompa_V8 AND Consensi;

// VASCA 8 - PRONTA AL PROCESSO
Rdy_V8 := IN_Liv_Min_V8 AND IN_Temp_Ok_V8 AND IN_Ricircolo_V8 AND NOT V_S_Soluzione_Vecchia_V8;

// VASCA 8 - SPIA PRONTA
V_L_Vasca_Ready_V8 := Rdy_V8;

// VASCA 9 - RICHIESTA DI CARICO SOTTO IL MINIMO
IF NOT IN_Liv_Min_V9 AND Consensi AND NOT V_S_All_Liv_V9 THEN
    Req_Carico_V9 := TRUE;
END_IF;

// VASCA 9 - FINE CARICO AL MASSIMO
IF (IN_Liv_Max_V9 OR NOT Consensi) THEN
    Req_Carico_V9 := FALSE;
END_IF;

// VASCA 9 - ELETTROVALVOLA DI CARICO
OUT_Carico_V9 := Req_Carico_V9 AND IN_DIW_Press AND Consensi AND NOT Mem_V9;

// VASCA 9 - SORVEGLIANZA TEMPO DI CARICO
Tim_Carico_V9(In := OUT_Carico_V9, PT := SET_T_Carico_V9);

// VASCA 9 - ALLARME CARICO NON RIUSCITO
IF Tim_Carico_V9.Q THEN
    V_S_All_Carico_V9 := TRUE;
END_IF;

// VASCA 9 - RICHIESTA DI SCARICO SOLUZIONE ESAURITA
IF V_S_Soluzione_Vecchia_V9 AND NOT Mem_Ciclo AND Consensi THEN
    Req_Scarico_V9 := TRUE;
END_IF;

// VASCA 9 - FINE SCARICO SOTTO IL MINIMO
IF (NOT IN_Liv_Min_V9 OR NOT Consensi) THEN
    Req_Scarico_V9 := FALSE;
END_IF;

// VASCA 9 - ELETTROVALVOLA DI SCARICO
OUT_Scarico_V9 := Req_Scarico_V9 AND Consensi AND NOT OUT_Carico_V9;

// VASCA 9 - AZZERAMENTO CICLI DOPO IL CAMBIO SOLUZIONE
IF (Req_Scarico_V9 AND NOT _fp_Req_Scarico_V9) AND IN_Liv_Max_V9 THEN
    V_S_Cicli_V9 := 0;
END_IF;

// VASCA 9 - POMPA DI RICIRCOLO
OUT_Pompa_V9 := IN_Liv_Min_V9 AND Consensi AND NOT Req_Scarico_V9;

// VASCA 9 - RISCALDAMENTO
OUT_Risc_V9 := IN_Liv_Min_V9 AND NOT IN_Temp_Ok_V9 AND NOT IN_Temp_Alta_V9 AND OUT_Pompa_V9 AND Consensi;

// VASCA 9 - PRONTA AL PROCESSO
Rdy_V9 := IN_Liv_Min_V9 AND IN_Temp_Ok_V9 AND IN_Ricircolo_V9 AND NOT V_S_Soluzione_Vecchia_V9;

// VASCA 9 - SPIA PRONTA
V_L_Vasca_Ready_V9 := Rdy_V9;

//==========================================================================
//  SEZIONE CHIMICA
//==========================================================================

// VASCA 1 - ATTESA FRA DUE DOSATE A
Tim_Pausa_A_V1(In := NOT Req_Dos_A_V1, PT := SET_T_Pausa_Dos_V1);

// VASCA 1 - RICHIESTA DOSATA A: conducibilita' bassa
IF IN_Cond_Bassa_V1 AND IN_Liv_Min_V1 AND OUT_Pompa_V1 AND NOT V_S_All_Chim_V1 AND Tim_Pausa_A_V1.Q AND Consensi THEN
    Req_Dos_A_V1 := TRUE;
END_IF;

// VASCA 1 - DOSATA A: comando della pompa dosatrice
OUT_Dos_A_V1 := Req_Dos_A_V1 AND IN_Chim_A_Min_V1 AND NOT IN_Liv_Max_V1;

// VASCA 1 - DOSATA A: durata della dosata
Tim_Dos_A_V1(In := OUT_Dos_A_V1, PT := SET_T_Dos_V1);

// VASCA 1 - DOSATA A: fine dosata e conteggio
IF Tim_Dos_A_V1.Q THEN
    Req_Dos_A_V1 := FALSE;
    V_S_Dosate_V1 := V_S_Dosate_V1 + 1;
END_IF;

// VASCA 1 - ATTESA FRA DUE DOSATE B
Tim_Pausa_B_V1(In := NOT Req_Dos_B_V1, PT := SET_T_Pausa_Dos_V1);

// VASCA 1 - RICHIESTA DOSATA B: pH fuori banda
IF IN_pH_Basso_V1 AND IN_Liv_Min_V1 AND OUT_Pompa_V1 AND Tim_Pausa_B_V1.Q AND Consensi THEN
    Req_Dos_B_V1 := TRUE;
END_IF;

// VASCA 1 - DOSATA B: comando della pompa dosatrice
OUT_Dos_B_V1 := Req_Dos_B_V1 AND IN_Chim_B_Min_V1 AND NOT IN_Liv_Max_V1;

// VASCA 1 - DOSATA B: durata della dosata
Tim_Dos_B_V1(In := OUT_Dos_B_V1, PT := SET_T_Dos_V1);

// VASCA 1 - DOSATA B: fine dosata
IF Tim_Dos_B_V1.Q THEN
    Req_Dos_B_V1 := FALSE;
END_IF;

// VASCA 1 - CHIMICO ESAURITO
IF ((Req_Dos_A_V1 AND NOT IN_Chim_A_Min_V1) OR (Req_Dos_B_V1 AND NOT IN_Chim_B_Min_V1)) THEN
    V_S_All_Chim_V1 := TRUE;
END_IF;

// VASCA 1 - RICHIESTA RABBOCCO per evaporazione
IF NOT IN_Liv_Max_V1 AND IN_Liv_Min_V1 AND IN_Temp_Ok_V1 AND NOT Mem_V1 AND Consensi THEN
    Req_Rabb_V1 := TRUE;
END_IF;

// VASCA 1 - RABBOCCO: elettrovalvola
OUT_Rabbocco_V1 := Req_Rabb_V1 AND IN_DIW_Press AND NOT OUT_Carico_V1;

// VASCA 1 - RABBOCCO: sorveglianza del tempo
Tim_Rabb_V1(In := OUT_Rabbocco_V1, PT := SET_T_Rabbocco_V1);

// VASCA 1 - RABBOCCO: fine al livello massimo
IF (IN_Liv_Max_V1 OR Tim_Rabb_V1.Q) THEN
    Req_Rabb_V1 := FALSE;
END_IF;

// VASCA 1 - ALLARME rabbocco troppo lungo
IF Tim_Rabb_V1.Q AND NOT IN_Liv_Max_V1 THEN
    V_S_All_Rabbocco_V1 := TRUE;
END_IF;

// VASCA 1 - AGITAZIONE ad aria durante il processo
OUT_Agitazione_V1 := Mem_V1 AND IN_Press_Aria AND IN_Liv_Min_V1 AND Consensi;

// VASCA 1 - LAVAGGIO A CASCATA nelle vasche di risciacquo
OUT_Cascata_V1 := Mem_V1 AND IN_DIW_Press AND NOT IN_Liv_Sfioro_V1 AND Consensi;

// VASCA 1 - CONDUCIBILITA' fuori banda da troppo tempo
Tim_Cond_V1(In := (IN_Cond_Alta_V1 OR (IN_Cond_Bassa_V1 AND NOT Req_Dos_A_V1)) AND IN_Liv_Min_V1, PT := T#300s);

// VASCA 1 - ALLARME conducibilita'
IF Tim_Cond_V1.Q THEN
    V_S_All_Cond_V1 := TRUE;
END_IF;

// VASCA 1 - pH fuori banda da troppo tempo
Tim_pH_V1(In := (IN_pH_Alto_V1 OR (IN_pH_Basso_V1 AND NOT Req_Dos_B_V1)) AND IN_Liv_Min_V1, PT := T#300s);

// VASCA 1 - ALLARME pH
IF Tim_pH_V1.Q THEN
    V_S_All_pH_V1 := TRUE;
END_IF;

// VASCA 1 - ALLARME sfioro intervenuto
IF IN_Liv_Sfioro_V1 THEN
    V_S_All_Sfioro_V1 := TRUE;
END_IF;

// VASCA 1 - lo sfioro chiude carico e rabbocco
IF V_S_All_Sfioro_V1 THEN
    Req_Carico_V1 := FALSE;
    Req_Rabb_V1 := FALSE;
END_IF;

// VASCA 1 - ALLARME filtro intasato
IF IN_Filtro_Sporco_V1 AND OUT_Pompa_V1 THEN
    V_S_All_Filtro_V1 := TRUE;
END_IF;

// VASCA 1 - RESET allarmi di chimica
IF (V_P_Reset AND NOT _fp_V_P_Reset) THEN
    V_S_All_Cond_V1 := FALSE;
    V_S_All_pH_V1 := FALSE;
    V_S_All_Sfioro_V1 := FALSE;
    V_S_All_Filtro_V1 := FALSE;
    V_S_All_Chim_V1 := FALSE;
    V_S_All_Rabbocco_V1 := FALSE;
END_IF;

// VASCA 1 - la vasca non e' pronta con allarmi di chimica
IF (V_S_All_Cond_V1 OR V_S_All_pH_V1 OR V_S_All_Sfioro_V1 OR V_S_All_Chim_V1) THEN
    Rdy_V1 := FALSE;
END_IF;

// VASCA 2 - ATTESA FRA DUE DOSATE A
Tim_Pausa_A_V2(In := NOT Req_Dos_A_V2, PT := SET_T_Pausa_Dos_V2);

// VASCA 2 - RICHIESTA DOSATA A: conducibilita' bassa
IF IN_Cond_Bassa_V2 AND IN_Liv_Min_V2 AND OUT_Pompa_V2 AND NOT V_S_All_Chim_V2 AND Tim_Pausa_A_V2.Q AND Consensi THEN
    Req_Dos_A_V2 := TRUE;
END_IF;

// VASCA 2 - DOSATA A: comando della pompa dosatrice
OUT_Dos_A_V2 := Req_Dos_A_V2 AND IN_Chim_A_Min_V2 AND NOT IN_Liv_Max_V2;

// VASCA 2 - DOSATA A: durata della dosata
Tim_Dos_A_V2(In := OUT_Dos_A_V2, PT := SET_T_Dos_V2);

// VASCA 2 - DOSATA A: fine dosata e conteggio
IF Tim_Dos_A_V2.Q THEN
    Req_Dos_A_V2 := FALSE;
    V_S_Dosate_V2 := V_S_Dosate_V2 + 1;
END_IF;

// VASCA 2 - ATTESA FRA DUE DOSATE B
Tim_Pausa_B_V2(In := NOT Req_Dos_B_V2, PT := SET_T_Pausa_Dos_V2);

// VASCA 2 - RICHIESTA DOSATA B: pH fuori banda
IF IN_pH_Basso_V2 AND IN_Liv_Min_V2 AND OUT_Pompa_V2 AND Tim_Pausa_B_V2.Q AND Consensi THEN
    Req_Dos_B_V2 := TRUE;
END_IF;

// VASCA 2 - DOSATA B: comando della pompa dosatrice
OUT_Dos_B_V2 := Req_Dos_B_V2 AND IN_Chim_B_Min_V2 AND NOT IN_Liv_Max_V2;

// VASCA 2 - DOSATA B: durata della dosata
Tim_Dos_B_V2(In := OUT_Dos_B_V2, PT := SET_T_Dos_V2);

// VASCA 2 - DOSATA B: fine dosata
IF Tim_Dos_B_V2.Q THEN
    Req_Dos_B_V2 := FALSE;
END_IF;

// VASCA 2 - CHIMICO ESAURITO
IF ((Req_Dos_A_V2 AND NOT IN_Chim_A_Min_V2) OR (Req_Dos_B_V2 AND NOT IN_Chim_B_Min_V2)) THEN
    V_S_All_Chim_V2 := TRUE;
END_IF;

// VASCA 2 - RICHIESTA RABBOCCO per evaporazione
IF NOT IN_Liv_Max_V2 AND IN_Liv_Min_V2 AND IN_Temp_Ok_V2 AND NOT Mem_V2 AND Consensi THEN
    Req_Rabb_V2 := TRUE;
END_IF;

// VASCA 2 - RABBOCCO: elettrovalvola
OUT_Rabbocco_V2 := Req_Rabb_V2 AND IN_DIW_Press AND NOT OUT_Carico_V2;

// VASCA 2 - RABBOCCO: sorveglianza del tempo
Tim_Rabb_V2(In := OUT_Rabbocco_V2, PT := SET_T_Rabbocco_V2);

// VASCA 2 - RABBOCCO: fine al livello massimo
IF (IN_Liv_Max_V2 OR Tim_Rabb_V2.Q) THEN
    Req_Rabb_V2 := FALSE;
END_IF;

// VASCA 2 - ALLARME rabbocco troppo lungo
IF Tim_Rabb_V2.Q AND NOT IN_Liv_Max_V2 THEN
    V_S_All_Rabbocco_V2 := TRUE;
END_IF;

// VASCA 2 - AGITAZIONE ad aria durante il processo
OUT_Agitazione_V2 := Mem_V2 AND IN_Press_Aria AND IN_Liv_Min_V2 AND Consensi;

// VASCA 2 - LAVAGGIO A CASCATA nelle vasche di risciacquo
OUT_Cascata_V2 := Mem_V2 AND IN_DIW_Press AND NOT IN_Liv_Sfioro_V2 AND Consensi;

// VASCA 2 - CONDUCIBILITA' fuori banda da troppo tempo
Tim_Cond_V2(In := (IN_Cond_Alta_V2 OR (IN_Cond_Bassa_V2 AND NOT Req_Dos_A_V2)) AND IN_Liv_Min_V2, PT := T#300s);

// VASCA 2 - ALLARME conducibilita'
IF Tim_Cond_V2.Q THEN
    V_S_All_Cond_V2 := TRUE;
END_IF;

// VASCA 2 - pH fuori banda da troppo tempo
Tim_pH_V2(In := (IN_pH_Alto_V2 OR (IN_pH_Basso_V2 AND NOT Req_Dos_B_V2)) AND IN_Liv_Min_V2, PT := T#300s);

// VASCA 2 - ALLARME pH
IF Tim_pH_V2.Q THEN
    V_S_All_pH_V2 := TRUE;
END_IF;

// VASCA 2 - ALLARME sfioro intervenuto
IF IN_Liv_Sfioro_V2 THEN
    V_S_All_Sfioro_V2 := TRUE;
END_IF;

// VASCA 2 - lo sfioro chiude carico e rabbocco
IF V_S_All_Sfioro_V2 THEN
    Req_Carico_V2 := FALSE;
    Req_Rabb_V2 := FALSE;
END_IF;

// VASCA 2 - ALLARME filtro intasato
IF IN_Filtro_Sporco_V2 AND OUT_Pompa_V2 THEN
    V_S_All_Filtro_V2 := TRUE;
END_IF;

// VASCA 2 - RESET allarmi di chimica
IF (V_P_Reset AND NOT _fp_V_P_Reset) THEN
    V_S_All_Cond_V2 := FALSE;
    V_S_All_pH_V2 := FALSE;
    V_S_All_Sfioro_V2 := FALSE;
    V_S_All_Filtro_V2 := FALSE;
    V_S_All_Chim_V2 := FALSE;
    V_S_All_Rabbocco_V2 := FALSE;
END_IF;

// VASCA 2 - la vasca non e' pronta con allarmi di chimica
IF (V_S_All_Cond_V2 OR V_S_All_pH_V2 OR V_S_All_Sfioro_V2 OR V_S_All_Chim_V2) THEN
    Rdy_V2 := FALSE;
END_IF;

// VASCA 3 - ATTESA FRA DUE DOSATE A
Tim_Pausa_A_V3(In := NOT Req_Dos_A_V3, PT := SET_T_Pausa_Dos_V3);

// VASCA 3 - RICHIESTA DOSATA A: conducibilita' bassa
IF IN_Cond_Bassa_V3 AND IN_Liv_Min_V3 AND OUT_Pompa_V3 AND NOT V_S_All_Chim_V3 AND Tim_Pausa_A_V3.Q AND Consensi THEN
    Req_Dos_A_V3 := TRUE;
END_IF;

// VASCA 3 - DOSATA A: comando della pompa dosatrice
OUT_Dos_A_V3 := Req_Dos_A_V3 AND IN_Chim_A_Min_V3 AND NOT IN_Liv_Max_V3;

// VASCA 3 - DOSATA A: durata della dosata
Tim_Dos_A_V3(In := OUT_Dos_A_V3, PT := SET_T_Dos_V3);

// VASCA 3 - DOSATA A: fine dosata e conteggio
IF Tim_Dos_A_V3.Q THEN
    Req_Dos_A_V3 := FALSE;
    V_S_Dosate_V3 := V_S_Dosate_V3 + 1;
END_IF;

// VASCA 3 - ATTESA FRA DUE DOSATE B
Tim_Pausa_B_V3(In := NOT Req_Dos_B_V3, PT := SET_T_Pausa_Dos_V3);

// VASCA 3 - RICHIESTA DOSATA B: pH fuori banda
IF IN_pH_Basso_V3 AND IN_Liv_Min_V3 AND OUT_Pompa_V3 AND Tim_Pausa_B_V3.Q AND Consensi THEN
    Req_Dos_B_V3 := TRUE;
END_IF;

// VASCA 3 - DOSATA B: comando della pompa dosatrice
OUT_Dos_B_V3 := Req_Dos_B_V3 AND IN_Chim_B_Min_V3 AND NOT IN_Liv_Max_V3;

// VASCA 3 - DOSATA B: durata della dosata
Tim_Dos_B_V3(In := OUT_Dos_B_V3, PT := SET_T_Dos_V3);

// VASCA 3 - DOSATA B: fine dosata
IF Tim_Dos_B_V3.Q THEN
    Req_Dos_B_V3 := FALSE;
END_IF;

// VASCA 3 - CHIMICO ESAURITO
IF ((Req_Dos_A_V3 AND NOT IN_Chim_A_Min_V3) OR (Req_Dos_B_V3 AND NOT IN_Chim_B_Min_V3)) THEN
    V_S_All_Chim_V3 := TRUE;
END_IF;

// VASCA 3 - RICHIESTA RABBOCCO per evaporazione
IF NOT IN_Liv_Max_V3 AND IN_Liv_Min_V3 AND IN_Temp_Ok_V3 AND NOT Mem_V3 AND Consensi THEN
    Req_Rabb_V3 := TRUE;
END_IF;

// VASCA 3 - RABBOCCO: elettrovalvola
OUT_Rabbocco_V3 := Req_Rabb_V3 AND IN_DIW_Press AND NOT OUT_Carico_V3;

// VASCA 3 - RABBOCCO: sorveglianza del tempo
Tim_Rabb_V3(In := OUT_Rabbocco_V3, PT := SET_T_Rabbocco_V3);

// VASCA 3 - RABBOCCO: fine al livello massimo
IF (IN_Liv_Max_V3 OR Tim_Rabb_V3.Q) THEN
    Req_Rabb_V3 := FALSE;
END_IF;

// VASCA 3 - ALLARME rabbocco troppo lungo
IF Tim_Rabb_V3.Q AND NOT IN_Liv_Max_V3 THEN
    V_S_All_Rabbocco_V3 := TRUE;
END_IF;

// VASCA 3 - AGITAZIONE ad aria durante il processo
OUT_Agitazione_V3 := Mem_V3 AND IN_Press_Aria AND IN_Liv_Min_V3 AND Consensi;

// VASCA 3 - LAVAGGIO A CASCATA nelle vasche di risciacquo
OUT_Cascata_V3 := Mem_V3 AND IN_DIW_Press AND NOT IN_Liv_Sfioro_V3 AND Consensi;

// VASCA 3 - CONDUCIBILITA' fuori banda da troppo tempo
Tim_Cond_V3(In := (IN_Cond_Alta_V3 OR (IN_Cond_Bassa_V3 AND NOT Req_Dos_A_V3)) AND IN_Liv_Min_V3, PT := T#300s);

// VASCA 3 - ALLARME conducibilita'
IF Tim_Cond_V3.Q THEN
    V_S_All_Cond_V3 := TRUE;
END_IF;

// VASCA 3 - pH fuori banda da troppo tempo
Tim_pH_V3(In := (IN_pH_Alto_V3 OR (IN_pH_Basso_V3 AND NOT Req_Dos_B_V3)) AND IN_Liv_Min_V3, PT := T#300s);

// VASCA 3 - ALLARME pH
IF Tim_pH_V3.Q THEN
    V_S_All_pH_V3 := TRUE;
END_IF;

// VASCA 3 - ALLARME sfioro intervenuto
IF IN_Liv_Sfioro_V3 THEN
    V_S_All_Sfioro_V3 := TRUE;
END_IF;

// VASCA 3 - lo sfioro chiude carico e rabbocco
IF V_S_All_Sfioro_V3 THEN
    Req_Carico_V3 := FALSE;
    Req_Rabb_V3 := FALSE;
END_IF;

// VASCA 3 - ALLARME filtro intasato
IF IN_Filtro_Sporco_V3 AND OUT_Pompa_V3 THEN
    V_S_All_Filtro_V3 := TRUE;
END_IF;

// VASCA 3 - RESET allarmi di chimica
IF (V_P_Reset AND NOT _fp_V_P_Reset) THEN
    V_S_All_Cond_V3 := FALSE;
    V_S_All_pH_V3 := FALSE;
    V_S_All_Sfioro_V3 := FALSE;
    V_S_All_Filtro_V3 := FALSE;
    V_S_All_Chim_V3 := FALSE;
    V_S_All_Rabbocco_V3 := FALSE;
END_IF;

// VASCA 3 - la vasca non e' pronta con allarmi di chimica
IF (V_S_All_Cond_V3 OR V_S_All_pH_V3 OR V_S_All_Sfioro_V3 OR V_S_All_Chim_V3) THEN
    Rdy_V3 := FALSE;
END_IF;

// VASCA 4 - ATTESA FRA DUE DOSATE A
Tim_Pausa_A_V4(In := NOT Req_Dos_A_V4, PT := SET_T_Pausa_Dos_V4);

// VASCA 4 - RICHIESTA DOSATA A: conducibilita' bassa
IF IN_Cond_Bassa_V4 AND IN_Liv_Min_V4 AND OUT_Pompa_V4 AND NOT V_S_All_Chim_V4 AND Tim_Pausa_A_V4.Q AND Consensi THEN
    Req_Dos_A_V4 := TRUE;
END_IF;

// VASCA 4 - DOSATA A: comando della pompa dosatrice
OUT_Dos_A_V4 := Req_Dos_A_V4 AND IN_Chim_A_Min_V4 AND NOT IN_Liv_Max_V4;

// VASCA 4 - DOSATA A: durata della dosata
Tim_Dos_A_V4(In := OUT_Dos_A_V4, PT := SET_T_Dos_V4);

// VASCA 4 - DOSATA A: fine dosata e conteggio
IF Tim_Dos_A_V4.Q THEN
    Req_Dos_A_V4 := FALSE;
    V_S_Dosate_V4 := V_S_Dosate_V4 + 1;
END_IF;

// VASCA 4 - ATTESA FRA DUE DOSATE B
Tim_Pausa_B_V4(In := NOT Req_Dos_B_V4, PT := SET_T_Pausa_Dos_V4);

// VASCA 4 - RICHIESTA DOSATA B: pH fuori banda
IF IN_pH_Basso_V4 AND IN_Liv_Min_V4 AND OUT_Pompa_V4 AND Tim_Pausa_B_V4.Q AND Consensi THEN
    Req_Dos_B_V4 := TRUE;
END_IF;

// VASCA 4 - DOSATA B: comando della pompa dosatrice
OUT_Dos_B_V4 := Req_Dos_B_V4 AND IN_Chim_B_Min_V4 AND NOT IN_Liv_Max_V4;

// VASCA 4 - DOSATA B: durata della dosata
Tim_Dos_B_V4(In := OUT_Dos_B_V4, PT := SET_T_Dos_V4);

// VASCA 4 - DOSATA B: fine dosata
IF Tim_Dos_B_V4.Q THEN
    Req_Dos_B_V4 := FALSE;
END_IF;

// VASCA 4 - CHIMICO ESAURITO
IF ((Req_Dos_A_V4 AND NOT IN_Chim_A_Min_V4) OR (Req_Dos_B_V4 AND NOT IN_Chim_B_Min_V4)) THEN
    V_S_All_Chim_V4 := TRUE;
END_IF;

// VASCA 4 - RICHIESTA RABBOCCO per evaporazione
IF NOT IN_Liv_Max_V4 AND IN_Liv_Min_V4 AND IN_Temp_Ok_V4 AND NOT Mem_V4 AND Consensi THEN
    Req_Rabb_V4 := TRUE;
END_IF;

// VASCA 4 - RABBOCCO: elettrovalvola
OUT_Rabbocco_V4 := Req_Rabb_V4 AND IN_DIW_Press AND NOT OUT_Carico_V4;

// VASCA 4 - RABBOCCO: sorveglianza del tempo
Tim_Rabb_V4(In := OUT_Rabbocco_V4, PT := SET_T_Rabbocco_V4);

// VASCA 4 - RABBOCCO: fine al livello massimo
IF (IN_Liv_Max_V4 OR Tim_Rabb_V4.Q) THEN
    Req_Rabb_V4 := FALSE;
END_IF;

// VASCA 4 - ALLARME rabbocco troppo lungo
IF Tim_Rabb_V4.Q AND NOT IN_Liv_Max_V4 THEN
    V_S_All_Rabbocco_V4 := TRUE;
END_IF;

// VASCA 4 - AGITAZIONE ad aria durante il processo
OUT_Agitazione_V4 := Mem_V4 AND IN_Press_Aria AND IN_Liv_Min_V4 AND Consensi;

// VASCA 4 - LAVAGGIO A CASCATA nelle vasche di risciacquo
OUT_Cascata_V4 := Mem_V4 AND IN_DIW_Press AND NOT IN_Liv_Sfioro_V4 AND Consensi;

// VASCA 4 - CONDUCIBILITA' fuori banda da troppo tempo
Tim_Cond_V4(In := (IN_Cond_Alta_V4 OR (IN_Cond_Bassa_V4 AND NOT Req_Dos_A_V4)) AND IN_Liv_Min_V4, PT := T#300s);

// VASCA 4 - ALLARME conducibilita'
IF Tim_Cond_V4.Q THEN
    V_S_All_Cond_V4 := TRUE;
END_IF;

// VASCA 4 - pH fuori banda da troppo tempo
Tim_pH_V4(In := (IN_pH_Alto_V4 OR (IN_pH_Basso_V4 AND NOT Req_Dos_B_V4)) AND IN_Liv_Min_V4, PT := T#300s);

// VASCA 4 - ALLARME pH
IF Tim_pH_V4.Q THEN
    V_S_All_pH_V4 := TRUE;
END_IF;

// VASCA 4 - ALLARME sfioro intervenuto
IF IN_Liv_Sfioro_V4 THEN
    V_S_All_Sfioro_V4 := TRUE;
END_IF;

// VASCA 4 - lo sfioro chiude carico e rabbocco
IF V_S_All_Sfioro_V4 THEN
    Req_Carico_V4 := FALSE;
    Req_Rabb_V4 := FALSE;
END_IF;

// VASCA 4 - ALLARME filtro intasato
IF IN_Filtro_Sporco_V4 AND OUT_Pompa_V4 THEN
    V_S_All_Filtro_V4 := TRUE;
END_IF;

// VASCA 4 - RESET allarmi di chimica
IF (V_P_Reset AND NOT _fp_V_P_Reset) THEN
    V_S_All_Cond_V4 := FALSE;
    V_S_All_pH_V4 := FALSE;
    V_S_All_Sfioro_V4 := FALSE;
    V_S_All_Filtro_V4 := FALSE;
    V_S_All_Chim_V4 := FALSE;
    V_S_All_Rabbocco_V4 := FALSE;
END_IF;

// VASCA 4 - la vasca non e' pronta con allarmi di chimica
IF (V_S_All_Cond_V4 OR V_S_All_pH_V4 OR V_S_All_Sfioro_V4 OR V_S_All_Chim_V4) THEN
    Rdy_V4 := FALSE;
END_IF;

// VASCA 5 - ATTESA FRA DUE DOSATE A
Tim_Pausa_A_V5(In := NOT Req_Dos_A_V5, PT := SET_T_Pausa_Dos_V5);

// VASCA 5 - RICHIESTA DOSATA A: conducibilita' bassa
IF IN_Cond_Bassa_V5 AND IN_Liv_Min_V5 AND OUT_Pompa_V5 AND NOT V_S_All_Chim_V5 AND Tim_Pausa_A_V5.Q AND Consensi THEN
    Req_Dos_A_V5 := TRUE;
END_IF;

// VASCA 5 - DOSATA A: comando della pompa dosatrice
OUT_Dos_A_V5 := Req_Dos_A_V5 AND IN_Chim_A_Min_V5 AND NOT IN_Liv_Max_V5;

// VASCA 5 - DOSATA A: durata della dosata
Tim_Dos_A_V5(In := OUT_Dos_A_V5, PT := SET_T_Dos_V5);

// VASCA 5 - DOSATA A: fine dosata e conteggio
IF Tim_Dos_A_V5.Q THEN
    Req_Dos_A_V5 := FALSE;
    V_S_Dosate_V5 := V_S_Dosate_V5 + 1;
END_IF;

// VASCA 5 - ATTESA FRA DUE DOSATE B
Tim_Pausa_B_V5(In := NOT Req_Dos_B_V5, PT := SET_T_Pausa_Dos_V5);

// VASCA 5 - RICHIESTA DOSATA B: pH fuori banda
IF IN_pH_Basso_V5 AND IN_Liv_Min_V5 AND OUT_Pompa_V5 AND Tim_Pausa_B_V5.Q AND Consensi THEN
    Req_Dos_B_V5 := TRUE;
END_IF;

// VASCA 5 - DOSATA B: comando della pompa dosatrice
OUT_Dos_B_V5 := Req_Dos_B_V5 AND IN_Chim_B_Min_V5 AND NOT IN_Liv_Max_V5;

// VASCA 5 - DOSATA B: durata della dosata
Tim_Dos_B_V5(In := OUT_Dos_B_V5, PT := SET_T_Dos_V5);

// VASCA 5 - DOSATA B: fine dosata
IF Tim_Dos_B_V5.Q THEN
    Req_Dos_B_V5 := FALSE;
END_IF;

// VASCA 5 - CHIMICO ESAURITO
IF ((Req_Dos_A_V5 AND NOT IN_Chim_A_Min_V5) OR (Req_Dos_B_V5 AND NOT IN_Chim_B_Min_V5)) THEN
    V_S_All_Chim_V5 := TRUE;
END_IF;

// VASCA 5 - RICHIESTA RABBOCCO per evaporazione
IF NOT IN_Liv_Max_V5 AND IN_Liv_Min_V5 AND IN_Temp_Ok_V5 AND NOT Mem_V5 AND Consensi THEN
    Req_Rabb_V5 := TRUE;
END_IF;

// VASCA 5 - RABBOCCO: elettrovalvola
OUT_Rabbocco_V5 := Req_Rabb_V5 AND IN_DIW_Press AND NOT OUT_Carico_V5;

// VASCA 5 - RABBOCCO: sorveglianza del tempo
Tim_Rabb_V5(In := OUT_Rabbocco_V5, PT := SET_T_Rabbocco_V5);

// VASCA 5 - RABBOCCO: fine al livello massimo
IF (IN_Liv_Max_V5 OR Tim_Rabb_V5.Q) THEN
    Req_Rabb_V5 := FALSE;
END_IF;

// VASCA 5 - ALLARME rabbocco troppo lungo
IF Tim_Rabb_V5.Q AND NOT IN_Liv_Max_V5 THEN
    V_S_All_Rabbocco_V5 := TRUE;
END_IF;

// VASCA 5 - AGITAZIONE ad aria durante il processo
OUT_Agitazione_V5 := Mem_V5 AND IN_Press_Aria AND IN_Liv_Min_V5 AND Consensi;

// VASCA 5 - LAVAGGIO A CASCATA nelle vasche di risciacquo
OUT_Cascata_V5 := Mem_V5 AND IN_DIW_Press AND NOT IN_Liv_Sfioro_V5 AND Consensi;

// VASCA 5 - CONDUCIBILITA' fuori banda da troppo tempo
Tim_Cond_V5(In := (IN_Cond_Alta_V5 OR (IN_Cond_Bassa_V5 AND NOT Req_Dos_A_V5)) AND IN_Liv_Min_V5, PT := T#300s);

// VASCA 5 - ALLARME conducibilita'
IF Tim_Cond_V5.Q THEN
    V_S_All_Cond_V5 := TRUE;
END_IF;

// VASCA 5 - pH fuori banda da troppo tempo
Tim_pH_V5(In := (IN_pH_Alto_V5 OR (IN_pH_Basso_V5 AND NOT Req_Dos_B_V5)) AND IN_Liv_Min_V5, PT := T#300s);

// VASCA 5 - ALLARME pH
IF Tim_pH_V5.Q THEN
    V_S_All_pH_V5 := TRUE;
END_IF;

// VASCA 5 - ALLARME sfioro intervenuto
IF IN_Liv_Sfioro_V5 THEN
    V_S_All_Sfioro_V5 := TRUE;
END_IF;

// VASCA 5 - lo sfioro chiude carico e rabbocco
IF V_S_All_Sfioro_V5 THEN
    Req_Carico_V5 := FALSE;
    Req_Rabb_V5 := FALSE;
END_IF;

// VASCA 5 - ALLARME filtro intasato
IF IN_Filtro_Sporco_V5 AND OUT_Pompa_V5 THEN
    V_S_All_Filtro_V5 := TRUE;
END_IF;

// VASCA 5 - RESET allarmi di chimica
IF (V_P_Reset AND NOT _fp_V_P_Reset) THEN
    V_S_All_Cond_V5 := FALSE;
    V_S_All_pH_V5 := FALSE;
    V_S_All_Sfioro_V5 := FALSE;
    V_S_All_Filtro_V5 := FALSE;
    V_S_All_Chim_V5 := FALSE;
    V_S_All_Rabbocco_V5 := FALSE;
END_IF;

// VASCA 5 - la vasca non e' pronta con allarmi di chimica
IF (V_S_All_Cond_V5 OR V_S_All_pH_V5 OR V_S_All_Sfioro_V5 OR V_S_All_Chim_V5) THEN
    Rdy_V5 := FALSE;
END_IF;

// VASCA 6 - ATTESA FRA DUE DOSATE A
Tim_Pausa_A_V6(In := NOT Req_Dos_A_V6, PT := SET_T_Pausa_Dos_V6);

// VASCA 6 - RICHIESTA DOSATA A: conducibilita' bassa
IF IN_Cond_Bassa_V6 AND IN_Liv_Min_V6 AND OUT_Pompa_V6 AND NOT V_S_All_Chim_V6 AND Tim_Pausa_A_V6.Q AND Consensi THEN
    Req_Dos_A_V6 := TRUE;
END_IF;

// VASCA 6 - DOSATA A: comando della pompa dosatrice
OUT_Dos_A_V6 := Req_Dos_A_V6 AND IN_Chim_A_Min_V6 AND NOT IN_Liv_Max_V6;

// VASCA 6 - DOSATA A: durata della dosata
Tim_Dos_A_V6(In := OUT_Dos_A_V6, PT := SET_T_Dos_V6);

// VASCA 6 - DOSATA A: fine dosata e conteggio
IF Tim_Dos_A_V6.Q THEN
    Req_Dos_A_V6 := FALSE;
    V_S_Dosate_V6 := V_S_Dosate_V6 + 1;
END_IF;

// VASCA 6 - ATTESA FRA DUE DOSATE B
Tim_Pausa_B_V6(In := NOT Req_Dos_B_V6, PT := SET_T_Pausa_Dos_V6);

// VASCA 6 - RICHIESTA DOSATA B: pH fuori banda
IF IN_pH_Basso_V6 AND IN_Liv_Min_V6 AND OUT_Pompa_V6 AND Tim_Pausa_B_V6.Q AND Consensi THEN
    Req_Dos_B_V6 := TRUE;
END_IF;

// VASCA 6 - DOSATA B: comando della pompa dosatrice
OUT_Dos_B_V6 := Req_Dos_B_V6 AND IN_Chim_B_Min_V6 AND NOT IN_Liv_Max_V6;

// VASCA 6 - DOSATA B: durata della dosata
Tim_Dos_B_V6(In := OUT_Dos_B_V6, PT := SET_T_Dos_V6);

// VASCA 6 - DOSATA B: fine dosata
IF Tim_Dos_B_V6.Q THEN
    Req_Dos_B_V6 := FALSE;
END_IF;

// VASCA 6 - CHIMICO ESAURITO
IF ((Req_Dos_A_V6 AND NOT IN_Chim_A_Min_V6) OR (Req_Dos_B_V6 AND NOT IN_Chim_B_Min_V6)) THEN
    V_S_All_Chim_V6 := TRUE;
END_IF;

// VASCA 6 - RICHIESTA RABBOCCO per evaporazione
IF NOT IN_Liv_Max_V6 AND IN_Liv_Min_V6 AND IN_Temp_Ok_V6 AND NOT Mem_V6 AND Consensi THEN
    Req_Rabb_V6 := TRUE;
END_IF;

// VASCA 6 - RABBOCCO: elettrovalvola
OUT_Rabbocco_V6 := Req_Rabb_V6 AND IN_DIW_Press AND NOT OUT_Carico_V6;

// VASCA 6 - RABBOCCO: sorveglianza del tempo
Tim_Rabb_V6(In := OUT_Rabbocco_V6, PT := SET_T_Rabbocco_V6);

// VASCA 6 - RABBOCCO: fine al livello massimo
IF (IN_Liv_Max_V6 OR Tim_Rabb_V6.Q) THEN
    Req_Rabb_V6 := FALSE;
END_IF;

// VASCA 6 - ALLARME rabbocco troppo lungo
IF Tim_Rabb_V6.Q AND NOT IN_Liv_Max_V6 THEN
    V_S_All_Rabbocco_V6 := TRUE;
END_IF;

// VASCA 6 - AGITAZIONE ad aria durante il processo
OUT_Agitazione_V6 := Mem_V6 AND IN_Press_Aria AND IN_Liv_Min_V6 AND Consensi;

// VASCA 6 - LAVAGGIO A CASCATA nelle vasche di risciacquo
OUT_Cascata_V6 := Mem_V6 AND IN_DIW_Press AND NOT IN_Liv_Sfioro_V6 AND Consensi;

// VASCA 6 - CONDUCIBILITA' fuori banda da troppo tempo
Tim_Cond_V6(In := (IN_Cond_Alta_V6 OR (IN_Cond_Bassa_V6 AND NOT Req_Dos_A_V6)) AND IN_Liv_Min_V6, PT := T#300s);

// VASCA 6 - ALLARME conducibilita'
IF Tim_Cond_V6.Q THEN
    V_S_All_Cond_V6 := TRUE;
END_IF;

// VASCA 6 - pH fuori banda da troppo tempo
Tim_pH_V6(In := (IN_pH_Alto_V6 OR (IN_pH_Basso_V6 AND NOT Req_Dos_B_V6)) AND IN_Liv_Min_V6, PT := T#300s);

// VASCA 6 - ALLARME pH
IF Tim_pH_V6.Q THEN
    V_S_All_pH_V6 := TRUE;
END_IF;

// VASCA 6 - ALLARME sfioro intervenuto
IF IN_Liv_Sfioro_V6 THEN
    V_S_All_Sfioro_V6 := TRUE;
END_IF;

// VASCA 6 - lo sfioro chiude carico e rabbocco
IF V_S_All_Sfioro_V6 THEN
    Req_Carico_V6 := FALSE;
    Req_Rabb_V6 := FALSE;
END_IF;

// VASCA 6 - ALLARME filtro intasato
IF IN_Filtro_Sporco_V6 AND OUT_Pompa_V6 THEN
    V_S_All_Filtro_V6 := TRUE;
END_IF;

// VASCA 6 - RESET allarmi di chimica
IF (V_P_Reset AND NOT _fp_V_P_Reset) THEN
    V_S_All_Cond_V6 := FALSE;
    V_S_All_pH_V6 := FALSE;
    V_S_All_Sfioro_V6 := FALSE;
    V_S_All_Filtro_V6 := FALSE;
    V_S_All_Chim_V6 := FALSE;
    V_S_All_Rabbocco_V6 := FALSE;
END_IF;

// VASCA 6 - la vasca non e' pronta con allarmi di chimica
IF (V_S_All_Cond_V6 OR V_S_All_pH_V6 OR V_S_All_Sfioro_V6 OR V_S_All_Chim_V6) THEN
    Rdy_V6 := FALSE;
END_IF;

// VASCA 7 - ATTESA FRA DUE DOSATE A
Tim_Pausa_A_V7(In := NOT Req_Dos_A_V7, PT := SET_T_Pausa_Dos_V7);

// VASCA 7 - RICHIESTA DOSATA A: conducibilita' bassa
IF IN_Cond_Bassa_V7 AND IN_Liv_Min_V7 AND OUT_Pompa_V7 AND NOT V_S_All_Chim_V7 AND Tim_Pausa_A_V7.Q AND Consensi THEN
    Req_Dos_A_V7 := TRUE;
END_IF;

// VASCA 7 - DOSATA A: comando della pompa dosatrice
OUT_Dos_A_V7 := Req_Dos_A_V7 AND IN_Chim_A_Min_V7 AND NOT IN_Liv_Max_V7;

// VASCA 7 - DOSATA A: durata della dosata
Tim_Dos_A_V7(In := OUT_Dos_A_V7, PT := SET_T_Dos_V7);

// VASCA 7 - DOSATA A: fine dosata e conteggio
IF Tim_Dos_A_V7.Q THEN
    Req_Dos_A_V7 := FALSE;
    V_S_Dosate_V7 := V_S_Dosate_V7 + 1;
END_IF;

// VASCA 7 - ATTESA FRA DUE DOSATE B
Tim_Pausa_B_V7(In := NOT Req_Dos_B_V7, PT := SET_T_Pausa_Dos_V7);

// VASCA 7 - RICHIESTA DOSATA B: pH fuori banda
IF IN_pH_Basso_V7 AND IN_Liv_Min_V7 AND OUT_Pompa_V7 AND Tim_Pausa_B_V7.Q AND Consensi THEN
    Req_Dos_B_V7 := TRUE;
END_IF;

// VASCA 7 - DOSATA B: comando della pompa dosatrice
OUT_Dos_B_V7 := Req_Dos_B_V7 AND IN_Chim_B_Min_V7 AND NOT IN_Liv_Max_V7;

// VASCA 7 - DOSATA B: durata della dosata
Tim_Dos_B_V7(In := OUT_Dos_B_V7, PT := SET_T_Dos_V7);

// VASCA 7 - DOSATA B: fine dosata
IF Tim_Dos_B_V7.Q THEN
    Req_Dos_B_V7 := FALSE;
END_IF;

// VASCA 7 - CHIMICO ESAURITO
IF ((Req_Dos_A_V7 AND NOT IN_Chim_A_Min_V7) OR (Req_Dos_B_V7 AND NOT IN_Chim_B_Min_V7)) THEN
    V_S_All_Chim_V7 := TRUE;
END_IF;

// VASCA 7 - RICHIESTA RABBOCCO per evaporazione
IF NOT IN_Liv_Max_V7 AND IN_Liv_Min_V7 AND IN_Temp_Ok_V7 AND NOT Mem_V7 AND Consensi THEN
    Req_Rabb_V7 := TRUE;
END_IF;

// VASCA 7 - RABBOCCO: elettrovalvola
OUT_Rabbocco_V7 := Req_Rabb_V7 AND IN_DIW_Press AND NOT OUT_Carico_V7;

// VASCA 7 - RABBOCCO: sorveglianza del tempo
Tim_Rabb_V7(In := OUT_Rabbocco_V7, PT := SET_T_Rabbocco_V7);

// VASCA 7 - RABBOCCO: fine al livello massimo
IF (IN_Liv_Max_V7 OR Tim_Rabb_V7.Q) THEN
    Req_Rabb_V7 := FALSE;
END_IF;

// VASCA 7 - ALLARME rabbocco troppo lungo
IF Tim_Rabb_V7.Q AND NOT IN_Liv_Max_V7 THEN
    V_S_All_Rabbocco_V7 := TRUE;
END_IF;

// VASCA 7 - AGITAZIONE ad aria durante il processo
OUT_Agitazione_V7 := Mem_V7 AND IN_Press_Aria AND IN_Liv_Min_V7 AND Consensi;

// VASCA 7 - LAVAGGIO A CASCATA nelle vasche di risciacquo
OUT_Cascata_V7 := Mem_V7 AND IN_DIW_Press AND NOT IN_Liv_Sfioro_V7 AND Consensi;

// VASCA 7 - CONDUCIBILITA' fuori banda da troppo tempo
Tim_Cond_V7(In := (IN_Cond_Alta_V7 OR (IN_Cond_Bassa_V7 AND NOT Req_Dos_A_V7)) AND IN_Liv_Min_V7, PT := T#300s);

// VASCA 7 - ALLARME conducibilita'
IF Tim_Cond_V7.Q THEN
    V_S_All_Cond_V7 := TRUE;
END_IF;

// VASCA 7 - pH fuori banda da troppo tempo
Tim_pH_V7(In := (IN_pH_Alto_V7 OR (IN_pH_Basso_V7 AND NOT Req_Dos_B_V7)) AND IN_Liv_Min_V7, PT := T#300s);

// VASCA 7 - ALLARME pH
IF Tim_pH_V7.Q THEN
    V_S_All_pH_V7 := TRUE;
END_IF;

// VASCA 7 - ALLARME sfioro intervenuto
IF IN_Liv_Sfioro_V7 THEN
    V_S_All_Sfioro_V7 := TRUE;
END_IF;

// VASCA 7 - lo sfioro chiude carico e rabbocco
IF V_S_All_Sfioro_V7 THEN
    Req_Carico_V7 := FALSE;
    Req_Rabb_V7 := FALSE;
END_IF;

// VASCA 7 - ALLARME filtro intasato
IF IN_Filtro_Sporco_V7 AND OUT_Pompa_V7 THEN
    V_S_All_Filtro_V7 := TRUE;
END_IF;

// VASCA 7 - RESET allarmi di chimica
IF (V_P_Reset AND NOT _fp_V_P_Reset) THEN
    V_S_All_Cond_V7 := FALSE;
    V_S_All_pH_V7 := FALSE;
    V_S_All_Sfioro_V7 := FALSE;
    V_S_All_Filtro_V7 := FALSE;
    V_S_All_Chim_V7 := FALSE;
    V_S_All_Rabbocco_V7 := FALSE;
END_IF;

// VASCA 7 - la vasca non e' pronta con allarmi di chimica
IF (V_S_All_Cond_V7 OR V_S_All_pH_V7 OR V_S_All_Sfioro_V7 OR V_S_All_Chim_V7) THEN
    Rdy_V7 := FALSE;
END_IF;

// VASCA 8 - ATTESA FRA DUE DOSATE A
Tim_Pausa_A_V8(In := NOT Req_Dos_A_V8, PT := SET_T_Pausa_Dos_V8);

// VASCA 8 - RICHIESTA DOSATA A: conducibilita' bassa
IF IN_Cond_Bassa_V8 AND IN_Liv_Min_V8 AND OUT_Pompa_V8 AND NOT V_S_All_Chim_V8 AND Tim_Pausa_A_V8.Q AND Consensi THEN
    Req_Dos_A_V8 := TRUE;
END_IF;

// VASCA 8 - DOSATA A: comando della pompa dosatrice
OUT_Dos_A_V8 := Req_Dos_A_V8 AND IN_Chim_A_Min_V8 AND NOT IN_Liv_Max_V8;

// VASCA 8 - DOSATA A: durata della dosata
Tim_Dos_A_V8(In := OUT_Dos_A_V8, PT := SET_T_Dos_V8);

// VASCA 8 - DOSATA A: fine dosata e conteggio
IF Tim_Dos_A_V8.Q THEN
    Req_Dos_A_V8 := FALSE;
    V_S_Dosate_V8 := V_S_Dosate_V8 + 1;
END_IF;

// VASCA 8 - ATTESA FRA DUE DOSATE B
Tim_Pausa_B_V8(In := NOT Req_Dos_B_V8, PT := SET_T_Pausa_Dos_V8);

// VASCA 8 - RICHIESTA DOSATA B: pH fuori banda
IF IN_pH_Basso_V8 AND IN_Liv_Min_V8 AND OUT_Pompa_V8 AND Tim_Pausa_B_V8.Q AND Consensi THEN
    Req_Dos_B_V8 := TRUE;
END_IF;

// VASCA 8 - DOSATA B: comando della pompa dosatrice
OUT_Dos_B_V8 := Req_Dos_B_V8 AND IN_Chim_B_Min_V8 AND NOT IN_Liv_Max_V8;

// VASCA 8 - DOSATA B: durata della dosata
Tim_Dos_B_V8(In := OUT_Dos_B_V8, PT := SET_T_Dos_V8);

// VASCA 8 - DOSATA B: fine dosata
IF Tim_Dos_B_V8.Q THEN
    Req_Dos_B_V8 := FALSE;
END_IF;

// VASCA 8 - CHIMICO ESAURITO
IF ((Req_Dos_A_V8 AND NOT IN_Chim_A_Min_V8) OR (Req_Dos_B_V8 AND NOT IN_Chim_B_Min_V8)) THEN
    V_S_All_Chim_V8 := TRUE;
END_IF;

// VASCA 8 - RICHIESTA RABBOCCO per evaporazione
IF NOT IN_Liv_Max_V8 AND IN_Liv_Min_V8 AND IN_Temp_Ok_V8 AND NOT Mem_V8 AND Consensi THEN
    Req_Rabb_V8 := TRUE;
END_IF;

// VASCA 8 - RABBOCCO: elettrovalvola
OUT_Rabbocco_V8 := Req_Rabb_V8 AND IN_DIW_Press AND NOT OUT_Carico_V8;

// VASCA 8 - RABBOCCO: sorveglianza del tempo
Tim_Rabb_V8(In := OUT_Rabbocco_V8, PT := SET_T_Rabbocco_V8);

// VASCA 8 - RABBOCCO: fine al livello massimo
IF (IN_Liv_Max_V8 OR Tim_Rabb_V8.Q) THEN
    Req_Rabb_V8 := FALSE;
END_IF;

// VASCA 8 - ALLARME rabbocco troppo lungo
IF Tim_Rabb_V8.Q AND NOT IN_Liv_Max_V8 THEN
    V_S_All_Rabbocco_V8 := TRUE;
END_IF;

// VASCA 8 - AGITAZIONE ad aria durante il processo
OUT_Agitazione_V8 := Mem_V8 AND IN_Press_Aria AND IN_Liv_Min_V8 AND Consensi;

// VASCA 8 - LAVAGGIO A CASCATA nelle vasche di risciacquo
OUT_Cascata_V8 := Mem_V8 AND IN_DIW_Press AND NOT IN_Liv_Sfioro_V8 AND Consensi;

// VASCA 8 - CONDUCIBILITA' fuori banda da troppo tempo
Tim_Cond_V8(In := (IN_Cond_Alta_V8 OR (IN_Cond_Bassa_V8 AND NOT Req_Dos_A_V8)) AND IN_Liv_Min_V8, PT := T#300s);

// VASCA 8 - ALLARME conducibilita'
IF Tim_Cond_V8.Q THEN
    V_S_All_Cond_V8 := TRUE;
END_IF;

// VASCA 8 - pH fuori banda da troppo tempo
Tim_pH_V8(In := (IN_pH_Alto_V8 OR (IN_pH_Basso_V8 AND NOT Req_Dos_B_V8)) AND IN_Liv_Min_V8, PT := T#300s);

// VASCA 8 - ALLARME pH
IF Tim_pH_V8.Q THEN
    V_S_All_pH_V8 := TRUE;
END_IF;

// VASCA 8 - ALLARME sfioro intervenuto
IF IN_Liv_Sfioro_V8 THEN
    V_S_All_Sfioro_V8 := TRUE;
END_IF;

// VASCA 8 - lo sfioro chiude carico e rabbocco
IF V_S_All_Sfioro_V8 THEN
    Req_Carico_V8 := FALSE;
    Req_Rabb_V8 := FALSE;
END_IF;

// VASCA 8 - ALLARME filtro intasato
IF IN_Filtro_Sporco_V8 AND OUT_Pompa_V8 THEN
    V_S_All_Filtro_V8 := TRUE;
END_IF;

// VASCA 8 - RESET allarmi di chimica
IF (V_P_Reset AND NOT _fp_V_P_Reset) THEN
    V_S_All_Cond_V8 := FALSE;
    V_S_All_pH_V8 := FALSE;
    V_S_All_Sfioro_V8 := FALSE;
    V_S_All_Filtro_V8 := FALSE;
    V_S_All_Chim_V8 := FALSE;
    V_S_All_Rabbocco_V8 := FALSE;
END_IF;

// VASCA 8 - la vasca non e' pronta con allarmi di chimica
IF (V_S_All_Cond_V8 OR V_S_All_pH_V8 OR V_S_All_Sfioro_V8 OR V_S_All_Chim_V8) THEN
    Rdy_V8 := FALSE;
END_IF;

// VASCA 9 - ATTESA FRA DUE DOSATE A
Tim_Pausa_A_V9(In := NOT Req_Dos_A_V9, PT := SET_T_Pausa_Dos_V9);

// VASCA 9 - RICHIESTA DOSATA A: conducibilita' bassa
IF IN_Cond_Bassa_V9 AND IN_Liv_Min_V9 AND OUT_Pompa_V9 AND NOT V_S_All_Chim_V9 AND Tim_Pausa_A_V9.Q AND Consensi THEN
    Req_Dos_A_V9 := TRUE;
END_IF;

// VASCA 9 - DOSATA A: comando della pompa dosatrice
OUT_Dos_A_V9 := Req_Dos_A_V9 AND IN_Chim_A_Min_V9 AND NOT IN_Liv_Max_V9;

// VASCA 9 - DOSATA A: durata della dosata
Tim_Dos_A_V9(In := OUT_Dos_A_V9, PT := SET_T_Dos_V9);

// VASCA 9 - DOSATA A: fine dosata e conteggio
IF Tim_Dos_A_V9.Q THEN
    Req_Dos_A_V9 := FALSE;
    V_S_Dosate_V9 := V_S_Dosate_V9 + 1;
END_IF;

// VASCA 9 - ATTESA FRA DUE DOSATE B
Tim_Pausa_B_V9(In := NOT Req_Dos_B_V9, PT := SET_T_Pausa_Dos_V9);

// VASCA 9 - RICHIESTA DOSATA B: pH fuori banda
IF IN_pH_Basso_V9 AND IN_Liv_Min_V9 AND OUT_Pompa_V9 AND Tim_Pausa_B_V9.Q AND Consensi THEN
    Req_Dos_B_V9 := TRUE;
END_IF;

// VASCA 9 - DOSATA B: comando della pompa dosatrice
OUT_Dos_B_V9 := Req_Dos_B_V9 AND IN_Chim_B_Min_V9 AND NOT IN_Liv_Max_V9;

// VASCA 9 - DOSATA B: durata della dosata
Tim_Dos_B_V9(In := OUT_Dos_B_V9, PT := SET_T_Dos_V9);

// VASCA 9 - DOSATA B: fine dosata
IF Tim_Dos_B_V9.Q THEN
    Req_Dos_B_V9 := FALSE;
END_IF;

// VASCA 9 - CHIMICO ESAURITO
IF ((Req_Dos_A_V9 AND NOT IN_Chim_A_Min_V9) OR (Req_Dos_B_V9 AND NOT IN_Chim_B_Min_V9)) THEN
    V_S_All_Chim_V9 := TRUE;
END_IF;

// VASCA 9 - RICHIESTA RABBOCCO per evaporazione
IF NOT IN_Liv_Max_V9 AND IN_Liv_Min_V9 AND IN_Temp_Ok_V9 AND NOT Mem_V9 AND Consensi THEN
    Req_Rabb_V9 := TRUE;
END_IF;

// VASCA 9 - RABBOCCO: elettrovalvola
OUT_Rabbocco_V9 := Req_Rabb_V9 AND IN_DIW_Press AND NOT OUT_Carico_V9;

// VASCA 9 - RABBOCCO: sorveglianza del tempo
Tim_Rabb_V9(In := OUT_Rabbocco_V9, PT := SET_T_Rabbocco_V9);

// VASCA 9 - RABBOCCO: fine al livello massimo
IF (IN_Liv_Max_V9 OR Tim_Rabb_V9.Q) THEN
    Req_Rabb_V9 := FALSE;
END_IF;

// VASCA 9 - ALLARME rabbocco troppo lungo
IF Tim_Rabb_V9.Q AND NOT IN_Liv_Max_V9 THEN
    V_S_All_Rabbocco_V9 := TRUE;
END_IF;

// VASCA 9 - AGITAZIONE ad aria durante il processo
OUT_Agitazione_V9 := Mem_V9 AND IN_Press_Aria AND IN_Liv_Min_V9 AND Consensi;

// VASCA 9 - LAVAGGIO A CASCATA nelle vasche di risciacquo
OUT_Cascata_V9 := Mem_V9 AND IN_DIW_Press AND NOT IN_Liv_Sfioro_V9 AND Consensi;

// VASCA 9 - CONDUCIBILITA' fuori banda da troppo tempo
Tim_Cond_V9(In := (IN_Cond_Alta_V9 OR (IN_Cond_Bassa_V9 AND NOT Req_Dos_A_V9)) AND IN_Liv_Min_V9, PT := T#300s);

// VASCA 9 - ALLARME conducibilita'
IF Tim_Cond_V9.Q THEN
    V_S_All_Cond_V9 := TRUE;
END_IF;

// VASCA 9 - pH fuori banda da troppo tempo
Tim_pH_V9(In := (IN_pH_Alto_V9 OR (IN_pH_Basso_V9 AND NOT Req_Dos_B_V9)) AND IN_Liv_Min_V9, PT := T#300s);

// VASCA 9 - ALLARME pH
IF Tim_pH_V9.Q THEN
    V_S_All_pH_V9 := TRUE;
END_IF;

// VASCA 9 - ALLARME sfioro intervenuto
IF IN_Liv_Sfioro_V9 THEN
    V_S_All_Sfioro_V9 := TRUE;
END_IF;

// VASCA 9 - lo sfioro chiude carico e rabbocco
IF V_S_All_Sfioro_V9 THEN
    Req_Carico_V9 := FALSE;
    Req_Rabb_V9 := FALSE;
END_IF;

// VASCA 9 - ALLARME filtro intasato
IF IN_Filtro_Sporco_V9 AND OUT_Pompa_V9 THEN
    V_S_All_Filtro_V9 := TRUE;
END_IF;

// VASCA 9 - RESET allarmi di chimica
IF (V_P_Reset AND NOT _fp_V_P_Reset) THEN
    V_S_All_Cond_V9 := FALSE;
    V_S_All_pH_V9 := FALSE;
    V_S_All_Sfioro_V9 := FALSE;
    V_S_All_Filtro_V9 := FALSE;
    V_S_All_Chim_V9 := FALSE;
    V_S_All_Rabbocco_V9 := FALSE;
END_IF;

// VASCA 9 - la vasca non e' pronta con allarmi di chimica
IF (V_S_All_Cond_V9 OR V_S_All_pH_V9 OR V_S_All_Sfioro_V9 OR V_S_All_Chim_V9) THEN
    Rdy_V9 := FALSE;
END_IF;

//==========================================================================
//  SEZIONE MOVIMENTAZIONE
//==========================================================================

// ROBOT: prelievo del cesto al carico
IF Mem_Ciclo AND NOT Mem_Pausa AND IN_Robot_Carico AND IN_Cesto_Carico AND NOT Mem_Cesto AND IN_Robot_Basso THEN
    Mem_Rob_Carico := TRUE;
END_IF;

// ROBOT: chiusura pinza sul cesto
OUT_Pinza_Chiudi := Mem_Rob_Carico AND NOT IN_Cesto_Presente AND Consensi;

// ROBOT: cesto agganciato
IF Mem_Rob_Carico AND IN_Cesto_Presente AND IN_Robot_Alto THEN
    Mem_Cesto := TRUE;
    Mem_Rob_Carico := FALSE;
END_IF;

// ROBOT: cesto da estrarre dalla vasca appena terminata
IF (((End_V1 AND NOT _fp_End_V1) AND V_S_Usa_V1) OR ((End_V2 AND NOT _fp_End_V2) AND V_S_Usa_V2) OR ((End_V3 AND NOT _fp_End_V3) AND V_S_Usa_V3) OR ((End_V4 AND NOT _fp_End_V4) AND V_S_Usa_V4) OR ((End_V5 AND NOT _fp_End_V5) AND V_S_Usa_V5) OR ((End_V6 AND NOT _fp_End_V6) AND V_S_Usa_V6) OR ((End_V7 AND NOT _fp_End_V7) AND V_S_Usa_V7) OR ((End_V8 AND NOT _fp_End_V8) AND V_S_Usa_V8) OR ((End_V9 AND NOT _fp_End_V9) AND V_S_Usa_V9)) AND Mem_Cesto THEN
    Mem_Rob_Estrai := TRUE;
END_IF;

// ROBOT: fine estrazione dalla vasca
IF IN_Robot_Alto THEN
    Mem_Rob_Estrai := FALSE;
END_IF;

// ROBOT: posizione di destinazione raggiunta
Mem_Rob_Target := Mem_Ciclo AND Mem_Cesto AND ((V_S_Usa_V1 AND NOT End_V1 AND IN_Robot_Su_V1) OR (V_S_Usa_V2 AND NOT End_V2 AND IN_Robot_Su_V2) OR (V_S_Usa_V3 AND NOT End_V3 AND IN_Robot_Su_V3) OR (V_S_Usa_V4 AND NOT End_V4 AND IN_Robot_Su_V4) OR (V_S_Usa_V5 AND NOT End_V5 AND IN_Robot_Su_V5) OR (V_S_Usa_V6 AND NOT End_V6 AND IN_Robot_Su_V6) OR (V_S_Usa_V7 AND NOT End_V7 AND IN_Robot_Su_V7) OR (V_S_Usa_V8 AND NOT End_V8 AND IN_Robot_Su_V8) OR (V_S_Usa_V9 AND NOT End_V9 AND IN_Robot_Su_V9));

// ROBOT: traslazione avanti (automatico o manuale)
OUT_Robot_Avanti := ((Mem_Ciclo AND NOT Mem_Pausa AND Mem_Cesto AND IN_Robot_Alto AND NOT Mem_Rob_Target AND NOT IN_Robot_Scarico) OR Man_Avanti) AND Consensi;

// ROBOT: rientro a vuoto (automatico o manuale)
OUT_Robot_Indietro := ((Mem_Ciclo AND NOT Mem_Cesto AND IN_Robot_Alto AND NOT IN_Robot_Carico) OR Man_Indietro) AND Consensi;

// ROBOT: discesa in vasca o allo scarico
OUT_Robot_Scende := (Mem_Rob_Target OR (Mem_Ciclo AND Mem_Cesto AND End_V9 AND IN_Robot_Scarico)) AND NOT IN_Robot_Basso AND NOT Mem_Rob_Estrai AND NOT Mem_Pausa AND Consensi;

// ROBOT: salita
OUT_Robot_Sale := (Mem_Rob_Carico OR Mem_Rob_Scarico OR Mem_Rob_Estrai) AND NOT IN_Robot_Alto AND NOT Mem_Pausa AND Consensi;

// ROBOT: deposito allo scarico
IF Mem_Ciclo AND End_V9 AND IN_Robot_Scarico AND IN_Robot_Basso AND Mem_Cesto THEN
    Mem_Rob_Scarico := TRUE;
END_IF;

// ROBOT: apertura pinza allo scarico
OUT_Pinza_Apri := Mem_Rob_Scarico AND IN_Robot_Basso AND Consensi;

// ROBOT: cesto rilasciato
IF Mem_Rob_Scarico AND NOT IN_Cesto_Presente THEN
    Mem_Cesto := FALSE;
    Mem_Rob_Scarico := FALSE;
END_IF;

// ROBOT: un movimento e' in corso
Mem_Rob_Muove := (OUT_Robot_Avanti OR OUT_Robot_Indietro OR OUT_Robot_Sale OR OUT_Robot_Scende);

// ROBOT: sorveglianza del tempo di movimento
Tim_Mov(In := Mem_Rob_Muove, PT := SET_T_Mov);

// ROBOT: allarme timeout movimento
IF Tim_Mov.Q THEN
    V_S_All_Timeout := TRUE;
END_IF;

// ROBOT: posizione corrente allo scarico
IF IN_Robot_Scarico THEN
    V_S_Pos_Robot := 99;
END_IF;

// ROBOT: posizione corrente al carico
IF IN_Robot_Carico THEN
    V_S_Pos_Robot := 0;
END_IF;

// ROBOT: posizione corrente sulla vasca 1
IF IN_Robot_Su_V1 THEN
    V_S_Pos_Robot := 1;
END_IF;

// ROBOT: destinazione vasca 1 quando e' la prossima
IF Mem_Ciclo AND Mem_Cesto AND V_S_Usa_V1 AND NOT End_V1 THEN
    V_S_Pos_Target := 1;
END_IF;

// ROBOT: allarme se scende su una vasca non pronta (1)
IF IN_Robot_Su_V1 AND IN_Robot_Basso AND V_S_Usa_V1 AND NOT Rdy_V1 THEN
    V_S_All_Robot := TRUE;
END_IF;

// ROBOT: posizione corrente sulla vasca 2
IF IN_Robot_Su_V2 THEN
    V_S_Pos_Robot := 2;
END_IF;

// ROBOT: destinazione vasca 2 quando e' la prossima
IF Mem_Ciclo AND Mem_Cesto AND V_S_Usa_V2 AND NOT End_V2 AND End_V1 THEN
    V_S_Pos_Target := 2;
END_IF;

// ROBOT: allarme se scende su una vasca non pronta (2)
IF IN_Robot_Su_V2 AND IN_Robot_Basso AND V_S_Usa_V2 AND NOT Rdy_V2 THEN
    V_S_All_Robot := TRUE;
END_IF;

// ROBOT: posizione corrente sulla vasca 3
IF IN_Robot_Su_V3 THEN
    V_S_Pos_Robot := 3;
END_IF;

// ROBOT: destinazione vasca 3 quando e' la prossima
IF Mem_Ciclo AND Mem_Cesto AND V_S_Usa_V3 AND NOT End_V3 AND End_V2 THEN
    V_S_Pos_Target := 3;
END_IF;

// ROBOT: allarme se scende su una vasca non pronta (3)
IF IN_Robot_Su_V3 AND IN_Robot_Basso AND V_S_Usa_V3 AND NOT Rdy_V3 THEN
    V_S_All_Robot := TRUE;
END_IF;

// ROBOT: posizione corrente sulla vasca 4
IF IN_Robot_Su_V4 THEN
    V_S_Pos_Robot := 4;
END_IF;

// ROBOT: destinazione vasca 4 quando e' la prossima
IF Mem_Ciclo AND Mem_Cesto AND V_S_Usa_V4 AND NOT End_V4 AND End_V3 THEN
    V_S_Pos_Target := 4;
END_IF;

// ROBOT: allarme se scende su una vasca non pronta (4)
IF IN_Robot_Su_V4 AND IN_Robot_Basso AND V_S_Usa_V4 AND NOT Rdy_V4 THEN
    V_S_All_Robot := TRUE;
END_IF;

// ROBOT: posizione corrente sulla vasca 5
IF IN_Robot_Su_V5 THEN
    V_S_Pos_Robot := 5;
END_IF;

// ROBOT: destinazione vasca 5 quando e' la prossima
IF Mem_Ciclo AND Mem_Cesto AND V_S_Usa_V5 AND NOT End_V5 AND End_V4 THEN
    V_S_Pos_Target := 5;
END_IF;

// ROBOT: allarme se scende su una vasca non pronta (5)
IF IN_Robot_Su_V5 AND IN_Robot_Basso AND V_S_Usa_V5 AND NOT Rdy_V5 THEN
    V_S_All_Robot := TRUE;
END_IF;

// ROBOT: posizione corrente sulla vasca 6
IF IN_Robot_Su_V6 THEN
    V_S_Pos_Robot := 6;
END_IF;

// ROBOT: destinazione vasca 6 quando e' la prossima
IF Mem_Ciclo AND Mem_Cesto AND V_S_Usa_V6 AND NOT End_V6 AND End_V5 THEN
    V_S_Pos_Target := 6;
END_IF;

// ROBOT: allarme se scende su una vasca non pronta (6)
IF IN_Robot_Su_V6 AND IN_Robot_Basso AND V_S_Usa_V6 AND NOT Rdy_V6 THEN
    V_S_All_Robot := TRUE;
END_IF;

// ROBOT: posizione corrente sulla vasca 7
IF IN_Robot_Su_V7 THEN
    V_S_Pos_Robot := 7;
END_IF;

// ROBOT: destinazione vasca 7 quando e' la prossima
IF Mem_Ciclo AND Mem_Cesto AND V_S_Usa_V7 AND NOT End_V7 AND End_V6 THEN
    V_S_Pos_Target := 7;
END_IF;

// ROBOT: allarme se scende su una vasca non pronta (7)
IF IN_Robot_Su_V7 AND IN_Robot_Basso AND V_S_Usa_V7 AND NOT Rdy_V7 THEN
    V_S_All_Robot := TRUE;
END_IF;

// ROBOT: posizione corrente sulla vasca 8
IF IN_Robot_Su_V8 THEN
    V_S_Pos_Robot := 8;
END_IF;

// ROBOT: destinazione vasca 8 quando e' la prossima
IF Mem_Ciclo AND Mem_Cesto AND V_S_Usa_V8 AND NOT End_V8 AND End_V7 THEN
    V_S_Pos_Target := 8;
END_IF;

// ROBOT: allarme se scende su una vasca non pronta (8)
IF IN_Robot_Su_V8 AND IN_Robot_Basso AND V_S_Usa_V8 AND NOT Rdy_V8 THEN
    V_S_All_Robot := TRUE;
END_IF;

// ROBOT: posizione corrente sulla vasca 9
IF IN_Robot_Su_V9 THEN
    V_S_Pos_Robot := 9;
END_IF;

// ROBOT: destinazione vasca 9 quando e' la prossima
IF Mem_Ciclo AND Mem_Cesto AND V_S_Usa_V9 AND NOT End_V9 AND End_V8 THEN
    V_S_Pos_Target := 9;
END_IF;

// ROBOT: allarme se scende su una vasca non pronta (9)
IF IN_Robot_Su_V9 AND IN_Robot_Basso AND V_S_Usa_V9 AND NOT Rdy_V9 THEN
    V_S_All_Robot := TRUE;
END_IF;

// RESET MOVIMENTI: allarmi di movimentazione azzerati
IF (V_P_Reset AND NOT _fp_V_P_Reset) THEN
    V_S_All_Timeout := FALSE;
    V_S_All_Robot := FALSE;
    Mem_Rob_Carico := FALSE;
    Mem_Rob_Scarico := FALSE;
    Mem_Rob_Estrai := FALSE;
END_IF;

//==========================================================================
//  SEZIONE ALLARMI
//==========================================================================

// ALLARME: emergenza premuta
IF IN_Emergenza THEN
    V_S_All_Emergenza := TRUE;
END_IF;

// RESET allarme emergenza premuta
IF (V_P_Reset AND NOT _fp_V_P_Reset) AND NOT IN_Emergenza THEN
    V_S_All_Emergenza := FALSE;
END_IF;

// ALLARME: protezioni aperte
IF NOT IN_Protezioni THEN
    V_S_All_Protezioni := TRUE;
END_IF;

// RESET allarme protezioni aperte
IF (V_P_Reset AND NOT _fp_V_P_Reset) AND IN_Protezioni THEN
    V_S_All_Protezioni := FALSE;
END_IF;

// ALLARME: mancanza aria compressa
IF NOT IN_Press_Aria THEN
    V_S_All_Aria := TRUE;
END_IF;

// RESET allarme mancanza aria compressa
IF (V_P_Reset AND NOT _fp_V_P_Reset) AND IN_Press_Aria THEN
    V_S_All_Aria := FALSE;
END_IF;

// ALLARME: aspirazione insufficiente
IF NOT IN_Aspirazione THEN
    V_S_All_Aspirazione := TRUE;
END_IF;

// RESET allarme aspirazione insufficiente
IF (V_P_Reset AND NOT _fp_V_P_Reset) AND IN_Aspirazione THEN
    V_S_All_Aspirazione := FALSE;
END_IF;

// ALLARME: mancanza acqua deionizzata
IF NOT IN_DIW_Press THEN
    V_S_All_DIW := TRUE;
END_IF;

// RESET allarme mancanza acqua deionizzata
IF (V_P_Reset AND NOT _fp_V_P_Reset) AND IN_DIW_Press THEN
    V_S_All_DIW := FALSE;
END_IF;

// ALLARME: termico generale intervenuto
IF NOT IN_Termico_Gen THEN
    V_S_All_Termico := TRUE;
END_IF;

// RESET allarme termico generale intervenuto
IF (V_P_Reset AND NOT _fp_V_P_Reset) AND IN_Termico_Gen THEN
    V_S_All_Termico := FALSE;
END_IF;

// ALLARME: portello aperto durante il ciclo
IF Mem_Ciclo AND (NOT IN_Portello_1 OR NOT IN_Portello_2) THEN
    V_S_All_Portello := TRUE;
END_IF;

// RESET allarme portello
IF (V_P_Reset AND NOT _fp_V_P_Reset) AND IN_Portello_1 AND IN_Portello_2 THEN
    V_S_All_Portello := FALSE;
END_IF;

// ALLARME VASCA 1: livello sotto il minimo in processo
IF Mem_V1 AND NOT IN_Liv_Min_V1 THEN
    V_S_All_Liv_V1 := TRUE;
END_IF;

// ALLARME VASCA 1: fuori temperatura da troppo tempo
Tim_Temp_V1(In := V_S_Usa_V1 AND NOT IN_Temp_Ok_V1 AND Mem_V1, PT := T#180s);

// ALLARME VASCA 1: memoria temperatura
IF Tim_Temp_V1.Q THEN
    V_S_All_Temp_V1 := TRUE;
END_IF;

// ALLARME VASCA 1: sovratemperatura (sicurezza)
IF IN_Temp_Alta_V1 THEN
    V_S_All_TempAlta_V1 := TRUE;
END_IF;

// ALLARME VASCA 1: ricircolo assente con pompa in marcia
Tim_Ric_V1(In := OUT_Pompa_V1 AND NOT IN_Ricircolo_V1, PT := T#10s);

// ALLARME VASCA 1: memoria ricircolo
IF Tim_Ric_V1.Q THEN
    V_S_All_Ricircolo_V1 := TRUE;
END_IF;

// RESET allarmi della vasca 1
IF (V_P_Reset AND NOT _fp_V_P_Reset) THEN
    V_S_All_Liv_V1 := FALSE;
    V_S_All_Temp_V1 := FALSE;
    V_S_All_TempAlta_V1 := FALSE;
    V_S_All_Ricircolo_V1 := FALSE;
    V_S_All_Carico_V1 := FALSE;
END_IF;

// VASCA 1: il riscaldamento cade sugli allarmi
IF (V_S_All_TempAlta_V1 OR V_S_All_Liv_V1 OR V_S_All_Ricircolo_V1) THEN
    OUT_Risc_V1 := FALSE;
END_IF;

// ALLARME VASCA 2: livello sotto il minimo in processo
IF Mem_V2 AND NOT IN_Liv_Min_V2 THEN
    V_S_All_Liv_V2 := TRUE;
END_IF;

// ALLARME VASCA 2: fuori temperatura da troppo tempo
Tim_Temp_V2(In := V_S_Usa_V2 AND NOT IN_Temp_Ok_V2 AND Mem_V2, PT := T#180s);

// ALLARME VASCA 2: memoria temperatura
IF Tim_Temp_V2.Q THEN
    V_S_All_Temp_V2 := TRUE;
END_IF;

// ALLARME VASCA 2: sovratemperatura (sicurezza)
IF IN_Temp_Alta_V2 THEN
    V_S_All_TempAlta_V2 := TRUE;
END_IF;

// ALLARME VASCA 2: ricircolo assente con pompa in marcia
Tim_Ric_V2(In := OUT_Pompa_V2 AND NOT IN_Ricircolo_V2, PT := T#10s);

// ALLARME VASCA 2: memoria ricircolo
IF Tim_Ric_V2.Q THEN
    V_S_All_Ricircolo_V2 := TRUE;
END_IF;

// RESET allarmi della vasca 2
IF (V_P_Reset AND NOT _fp_V_P_Reset) THEN
    V_S_All_Liv_V2 := FALSE;
    V_S_All_Temp_V2 := FALSE;
    V_S_All_TempAlta_V2 := FALSE;
    V_S_All_Ricircolo_V2 := FALSE;
    V_S_All_Carico_V2 := FALSE;
END_IF;

// VASCA 2: il riscaldamento cade sugli allarmi
IF (V_S_All_TempAlta_V2 OR V_S_All_Liv_V2 OR V_S_All_Ricircolo_V2) THEN
    OUT_Risc_V2 := FALSE;
END_IF;

// ALLARME VASCA 3: livello sotto il minimo in processo
IF Mem_V3 AND NOT IN_Liv_Min_V3 THEN
    V_S_All_Liv_V3 := TRUE;
END_IF;

// ALLARME VASCA 3: fuori temperatura da troppo tempo
Tim_Temp_V3(In := V_S_Usa_V3 AND NOT IN_Temp_Ok_V3 AND Mem_V3, PT := T#180s);

// ALLARME VASCA 3: memoria temperatura
IF Tim_Temp_V3.Q THEN
    V_S_All_Temp_V3 := TRUE;
END_IF;

// ALLARME VASCA 3: sovratemperatura (sicurezza)
IF IN_Temp_Alta_V3 THEN
    V_S_All_TempAlta_V3 := TRUE;
END_IF;

// ALLARME VASCA 3: ricircolo assente con pompa in marcia
Tim_Ric_V3(In := OUT_Pompa_V3 AND NOT IN_Ricircolo_V3, PT := T#10s);

// ALLARME VASCA 3: memoria ricircolo
IF Tim_Ric_V3.Q THEN
    V_S_All_Ricircolo_V3 := TRUE;
END_IF;

// RESET allarmi della vasca 3
IF (V_P_Reset AND NOT _fp_V_P_Reset) THEN
    V_S_All_Liv_V3 := FALSE;
    V_S_All_Temp_V3 := FALSE;
    V_S_All_TempAlta_V3 := FALSE;
    V_S_All_Ricircolo_V3 := FALSE;
    V_S_All_Carico_V3 := FALSE;
END_IF;

// VASCA 3: il riscaldamento cade sugli allarmi
IF (V_S_All_TempAlta_V3 OR V_S_All_Liv_V3 OR V_S_All_Ricircolo_V3) THEN
    OUT_Risc_V3 := FALSE;
END_IF;

// ALLARME VASCA 4: livello sotto il minimo in processo
IF Mem_V4 AND NOT IN_Liv_Min_V4 THEN
    V_S_All_Liv_V4 := TRUE;
END_IF;

// ALLARME VASCA 4: fuori temperatura da troppo tempo
Tim_Temp_V4(In := V_S_Usa_V4 AND NOT IN_Temp_Ok_V4 AND Mem_V4, PT := T#180s);

// ALLARME VASCA 4: memoria temperatura
IF Tim_Temp_V4.Q THEN
    V_S_All_Temp_V4 := TRUE;
END_IF;

// ALLARME VASCA 4: sovratemperatura (sicurezza)
IF IN_Temp_Alta_V4 THEN
    V_S_All_TempAlta_V4 := TRUE;
END_IF;

// ALLARME VASCA 4: ricircolo assente con pompa in marcia
Tim_Ric_V4(In := OUT_Pompa_V4 AND NOT IN_Ricircolo_V4, PT := T#10s);

// ALLARME VASCA 4: memoria ricircolo
IF Tim_Ric_V4.Q THEN
    V_S_All_Ricircolo_V4 := TRUE;
END_IF;

// RESET allarmi della vasca 4
IF (V_P_Reset AND NOT _fp_V_P_Reset) THEN
    V_S_All_Liv_V4 := FALSE;
    V_S_All_Temp_V4 := FALSE;
    V_S_All_TempAlta_V4 := FALSE;
    V_S_All_Ricircolo_V4 := FALSE;
    V_S_All_Carico_V4 := FALSE;
END_IF;

// VASCA 4: il riscaldamento cade sugli allarmi
IF (V_S_All_TempAlta_V4 OR V_S_All_Liv_V4 OR V_S_All_Ricircolo_V4) THEN
    OUT_Risc_V4 := FALSE;
END_IF;

// ALLARME VASCA 5: livello sotto il minimo in processo
IF Mem_V5 AND NOT IN_Liv_Min_V5 THEN
    V_S_All_Liv_V5 := TRUE;
END_IF;

// ALLARME VASCA 5: fuori temperatura da troppo tempo
Tim_Temp_V5(In := V_S_Usa_V5 AND NOT IN_Temp_Ok_V5 AND Mem_V5, PT := T#180s);

// ALLARME VASCA 5: memoria temperatura
IF Tim_Temp_V5.Q THEN
    V_S_All_Temp_V5 := TRUE;
END_IF;

// ALLARME VASCA 5: sovratemperatura (sicurezza)
IF IN_Temp_Alta_V5 THEN
    V_S_All_TempAlta_V5 := TRUE;
END_IF;

// ALLARME VASCA 5: ricircolo assente con pompa in marcia
Tim_Ric_V5(In := OUT_Pompa_V5 AND NOT IN_Ricircolo_V5, PT := T#10s);

// ALLARME VASCA 5: memoria ricircolo
IF Tim_Ric_V5.Q THEN
    V_S_All_Ricircolo_V5 := TRUE;
END_IF;

// RESET allarmi della vasca 5
IF (V_P_Reset AND NOT _fp_V_P_Reset) THEN
    V_S_All_Liv_V5 := FALSE;
    V_S_All_Temp_V5 := FALSE;
    V_S_All_TempAlta_V5 := FALSE;
    V_S_All_Ricircolo_V5 := FALSE;
    V_S_All_Carico_V5 := FALSE;
END_IF;

// VASCA 5: il riscaldamento cade sugli allarmi
IF (V_S_All_TempAlta_V5 OR V_S_All_Liv_V5 OR V_S_All_Ricircolo_V5) THEN
    OUT_Risc_V5 := FALSE;
END_IF;

// ALLARME VASCA 6: livello sotto il minimo in processo
IF Mem_V6 AND NOT IN_Liv_Min_V6 THEN
    V_S_All_Liv_V6 := TRUE;
END_IF;

// ALLARME VASCA 6: fuori temperatura da troppo tempo
Tim_Temp_V6(In := V_S_Usa_V6 AND NOT IN_Temp_Ok_V6 AND Mem_V6, PT := T#180s);

// ALLARME VASCA 6: memoria temperatura
IF Tim_Temp_V6.Q THEN
    V_S_All_Temp_V6 := TRUE;
END_IF;

// ALLARME VASCA 6: sovratemperatura (sicurezza)
IF IN_Temp_Alta_V6 THEN
    V_S_All_TempAlta_V6 := TRUE;
END_IF;

// ALLARME VASCA 6: ricircolo assente con pompa in marcia
Tim_Ric_V6(In := OUT_Pompa_V6 AND NOT IN_Ricircolo_V6, PT := T#10s);

// ALLARME VASCA 6: memoria ricircolo
IF Tim_Ric_V6.Q THEN
    V_S_All_Ricircolo_V6 := TRUE;
END_IF;

// RESET allarmi della vasca 6
IF (V_P_Reset AND NOT _fp_V_P_Reset) THEN
    V_S_All_Liv_V6 := FALSE;
    V_S_All_Temp_V6 := FALSE;
    V_S_All_TempAlta_V6 := FALSE;
    V_S_All_Ricircolo_V6 := FALSE;
    V_S_All_Carico_V6 := FALSE;
END_IF;

// VASCA 6: il riscaldamento cade sugli allarmi
IF (V_S_All_TempAlta_V6 OR V_S_All_Liv_V6 OR V_S_All_Ricircolo_V6) THEN
    OUT_Risc_V6 := FALSE;
END_IF;

// ALLARME VASCA 7: livello sotto il minimo in processo
IF Mem_V7 AND NOT IN_Liv_Min_V7 THEN
    V_S_All_Liv_V7 := TRUE;
END_IF;

// ALLARME VASCA 7: fuori temperatura da troppo tempo
Tim_Temp_V7(In := V_S_Usa_V7 AND NOT IN_Temp_Ok_V7 AND Mem_V7, PT := T#180s);

// ALLARME VASCA 7: memoria temperatura
IF Tim_Temp_V7.Q THEN
    V_S_All_Temp_V7 := TRUE;
END_IF;

// ALLARME VASCA 7: sovratemperatura (sicurezza)
IF IN_Temp_Alta_V7 THEN
    V_S_All_TempAlta_V7 := TRUE;
END_IF;

// ALLARME VASCA 7: ricircolo assente con pompa in marcia
Tim_Ric_V7(In := OUT_Pompa_V7 AND NOT IN_Ricircolo_V7, PT := T#10s);

// ALLARME VASCA 7: memoria ricircolo
IF Tim_Ric_V7.Q THEN
    V_S_All_Ricircolo_V7 := TRUE;
END_IF;

// RESET allarmi della vasca 7
IF (V_P_Reset AND NOT _fp_V_P_Reset) THEN
    V_S_All_Liv_V7 := FALSE;
    V_S_All_Temp_V7 := FALSE;
    V_S_All_TempAlta_V7 := FALSE;
    V_S_All_Ricircolo_V7 := FALSE;
    V_S_All_Carico_V7 := FALSE;
END_IF;

// VASCA 7: il riscaldamento cade sugli allarmi
IF (V_S_All_TempAlta_V7 OR V_S_All_Liv_V7 OR V_S_All_Ricircolo_V7) THEN
    OUT_Risc_V7 := FALSE;
END_IF;

// ALLARME VASCA 8: livello sotto il minimo in processo
IF Mem_V8 AND NOT IN_Liv_Min_V8 THEN
    V_S_All_Liv_V8 := TRUE;
END_IF;

// ALLARME VASCA 8: fuori temperatura da troppo tempo
Tim_Temp_V8(In := V_S_Usa_V8 AND NOT IN_Temp_Ok_V8 AND Mem_V8, PT := T#180s);

// ALLARME VASCA 8: memoria temperatura
IF Tim_Temp_V8.Q THEN
    V_S_All_Temp_V8 := TRUE;
END_IF;

// ALLARME VASCA 8: sovratemperatura (sicurezza)
IF IN_Temp_Alta_V8 THEN
    V_S_All_TempAlta_V8 := TRUE;
END_IF;

// ALLARME VASCA 8: ricircolo assente con pompa in marcia
Tim_Ric_V8(In := OUT_Pompa_V8 AND NOT IN_Ricircolo_V8, PT := T#10s);

// ALLARME VASCA 8: memoria ricircolo
IF Tim_Ric_V8.Q THEN
    V_S_All_Ricircolo_V8 := TRUE;
END_IF;

// RESET allarmi della vasca 8
IF (V_P_Reset AND NOT _fp_V_P_Reset) THEN
    V_S_All_Liv_V8 := FALSE;
    V_S_All_Temp_V8 := FALSE;
    V_S_All_TempAlta_V8 := FALSE;
    V_S_All_Ricircolo_V8 := FALSE;
    V_S_All_Carico_V8 := FALSE;
END_IF;

// VASCA 8: il riscaldamento cade sugli allarmi
IF (V_S_All_TempAlta_V8 OR V_S_All_Liv_V8 OR V_S_All_Ricircolo_V8) THEN
    OUT_Risc_V8 := FALSE;
END_IF;

// ALLARME VASCA 9: livello sotto il minimo in processo
IF Mem_V9 AND NOT IN_Liv_Min_V9 THEN
    V_S_All_Liv_V9 := TRUE;
END_IF;

// ALLARME VASCA 9: fuori temperatura da troppo tempo
Tim_Temp_V9(In := V_S_Usa_V9 AND NOT IN_Temp_Ok_V9 AND Mem_V9, PT := T#180s);

// ALLARME VASCA 9: memoria temperatura
IF Tim_Temp_V9.Q THEN
    V_S_All_Temp_V9 := TRUE;
END_IF;

// ALLARME VASCA 9: sovratemperatura (sicurezza)
IF IN_Temp_Alta_V9 THEN
    V_S_All_TempAlta_V9 := TRUE;
END_IF;

// ALLARME VASCA 9: ricircolo assente con pompa in marcia
Tim_Ric_V9(In := OUT_Pompa_V9 AND NOT IN_Ricircolo_V9, PT := T#10s);

// ALLARME VASCA 9: memoria ricircolo
IF Tim_Ric_V9.Q THEN
    V_S_All_Ricircolo_V9 := TRUE;
END_IF;

// RESET allarmi della vasca 9
IF (V_P_Reset AND NOT _fp_V_P_Reset) THEN
    V_S_All_Liv_V9 := FALSE;
    V_S_All_Temp_V9 := FALSE;
    V_S_All_TempAlta_V9 := FALSE;
    V_S_All_Ricircolo_V9 := FALSE;
    V_S_All_Carico_V9 := FALSE;
END_IF;

// VASCA 9: il riscaldamento cade sugli allarmi
IF (V_S_All_TempAlta_V9 OR V_S_All_Liv_V9 OR V_S_All_Ricircolo_V9) THEN
    OUT_Risc_V9 := FALSE;
END_IF;

// SPIA ALLARME CUMULATIVO
V_L_Allarme := (V_S_All_Emergenza OR V_S_All_Protezioni OR V_S_All_Aria OR V_S_All_Aspirazione OR V_S_All_DIW OR V_S_All_Termico OR V_S_All_Ricetta OR V_S_All_Robot OR V_S_All_Timeout OR V_S_All_Portello OR V_S_All_Liv_V1 OR V_S_All_Liv_V2 OR V_S_All_Liv_V3 OR V_S_All_Liv_V4 OR V_S_All_Liv_V5 OR V_S_All_Liv_V6 OR V_S_All_Liv_V7 OR V_S_All_Liv_V8 OR V_S_All_Liv_V9 OR V_S_All_Temp_V1 OR V_S_All_Temp_V2 OR V_S_All_Temp_V3 OR V_S_All_Temp_V4 OR V_S_All_Temp_V5 OR V_S_All_Temp_V6 OR V_S_All_Temp_V7 OR V_S_All_Temp_V8 OR V_S_All_Temp_V9 OR V_S_All_TempAlta_V1 OR V_S_All_TempAlta_V2 OR V_S_All_TempAlta_V3 OR V_S_All_TempAlta_V4 OR V_S_All_TempAlta_V5 OR V_S_All_TempAlta_V6 OR V_S_All_TempAlta_V7 OR V_S_All_TempAlta_V8 OR V_S_All_TempAlta_V9 OR V_S_All_Ricircolo_V1 OR V_S_All_Ricircolo_V2 OR V_S_All_Ricircolo_V3 OR V_S_All_Ricircolo_V4 OR V_S_All_Ricircolo_V5 OR V_S_All_Ricircolo_V6 OR V_S_All_Ricircolo_V7 OR V_S_All_Ricircolo_V8 OR V_S_All_Ricircolo_V9 OR V_S_All_Carico_V1 OR V_S_All_Carico_V2 OR V_S_All_Carico_V3 OR V_S_All_Carico_V4 OR V_S_All_Carico_V5 OR V_S_All_Carico_V6 OR V_S_All_Carico_V7 OR V_S_All_Carico_V8 OR V_S_All_Carico_V9 OR V_S_All_Cond_V1 OR V_S_All_Cond_V2 OR V_S_All_Cond_V3 OR V_S_All_Cond_V4 OR V_S_All_Cond_V5 OR V_S_All_Cond_V6 OR V_S_All_Cond_V7 OR V_S_All_Cond_V8 OR V_S_All_Cond_V9 OR V_S_All_pH_V1 OR V_S_All_pH_V2 OR V_S_All_pH_V3 OR V_S_All_pH_V4 OR V_S_All_pH_V5 OR V_S_All_pH_V6 OR V_S_All_pH_V7 OR V_S_All_pH_V8 OR V_S_All_pH_V9 OR V_S_All_Sfioro_V1 OR V_S_All_Sfioro_V2 OR V_S_All_Sfioro_V3 OR V_S_All_Sfioro_V4 OR V_S_All_Sfioro_V5 OR V_S_All_Sfioro_V6 OR V_S_All_Sfioro_V7 OR V_S_All_Sfioro_V8 OR V_S_All_Sfioro_V9 OR V_S_All_Filtro_V1 OR V_S_All_Filtro_V2 OR V_S_All_Filtro_V3 OR V_S_All_Filtro_V4 OR V_S_All_Filtro_V5 OR V_S_All_Filtro_V6 OR V_S_All_Filtro_V7 OR V_S_All_Filtro_V8 OR V_S_All_Filtro_V9 OR V_S_All_Chim_V1 OR V_S_All_Chim_V2 OR V_S_All_Chim_V3 OR V_S_All_Chim_V4 OR V_S_All_Chim_V5 OR V_S_All_Chim_V6 OR V_S_All_Chim_V7 OR V_S_All_Chim_V8 OR V_S_All_Chim_V9 OR V_S_All_Rabbocco_V1 OR V_S_All_Rabbocco_V2 OR V_S_All_Rabbocco_V3 OR V_S_All_Rabbocco_V4 OR V_S_All_Rabbocco_V5 OR V_S_All_Rabbocco_V6 OR V_S_All_Rabbocco_V7 OR V_S_All_Rabbocco_V8 OR V_S_All_Rabbocco_V9);

// CONTEGGIO ALLARMI ATTIVI: azzeramento a ogni scansione
V_S_Allarmi_Att := 0;

// CONTEGGIO ALLARMI: V_S_All_Emergenza
IF V_S_All_Emergenza THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Protezioni
IF V_S_All_Protezioni THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Aria
IF V_S_All_Aria THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Aspirazione
IF V_S_All_Aspirazione THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_DIW
IF V_S_All_DIW THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Termico
IF V_S_All_Termico THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Ricetta
IF V_S_All_Ricetta THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Robot
IF V_S_All_Robot THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Timeout
IF V_S_All_Timeout THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Portello
IF V_S_All_Portello THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Liv_V1
IF V_S_All_Liv_V1 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Liv_V2
IF V_S_All_Liv_V2 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Liv_V3
IF V_S_All_Liv_V3 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Liv_V4
IF V_S_All_Liv_V4 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Liv_V5
IF V_S_All_Liv_V5 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Liv_V6
IF V_S_All_Liv_V6 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Liv_V7
IF V_S_All_Liv_V7 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Liv_V8
IF V_S_All_Liv_V8 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Liv_V9
IF V_S_All_Liv_V9 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Temp_V1
IF V_S_All_Temp_V1 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Temp_V2
IF V_S_All_Temp_V2 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Temp_V3
IF V_S_All_Temp_V3 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Temp_V4
IF V_S_All_Temp_V4 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Temp_V5
IF V_S_All_Temp_V5 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Temp_V6
IF V_S_All_Temp_V6 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Temp_V7
IF V_S_All_Temp_V7 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Temp_V8
IF V_S_All_Temp_V8 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Temp_V9
IF V_S_All_Temp_V9 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_TempAlta_V1
IF V_S_All_TempAlta_V1 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_TempAlta_V2
IF V_S_All_TempAlta_V2 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_TempAlta_V3
IF V_S_All_TempAlta_V3 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_TempAlta_V4
IF V_S_All_TempAlta_V4 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_TempAlta_V5
IF V_S_All_TempAlta_V5 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_TempAlta_V6
IF V_S_All_TempAlta_V6 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_TempAlta_V7
IF V_S_All_TempAlta_V7 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_TempAlta_V8
IF V_S_All_TempAlta_V8 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_TempAlta_V9
IF V_S_All_TempAlta_V9 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Ricircolo_V1
IF V_S_All_Ricircolo_V1 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Ricircolo_V2
IF V_S_All_Ricircolo_V2 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Ricircolo_V3
IF V_S_All_Ricircolo_V3 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Ricircolo_V4
IF V_S_All_Ricircolo_V4 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Ricircolo_V5
IF V_S_All_Ricircolo_V5 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Ricircolo_V6
IF V_S_All_Ricircolo_V6 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Ricircolo_V7
IF V_S_All_Ricircolo_V7 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Ricircolo_V8
IF V_S_All_Ricircolo_V8 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Ricircolo_V9
IF V_S_All_Ricircolo_V9 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Carico_V1
IF V_S_All_Carico_V1 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Carico_V2
IF V_S_All_Carico_V2 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Carico_V3
IF V_S_All_Carico_V3 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Carico_V4
IF V_S_All_Carico_V4 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Carico_V5
IF V_S_All_Carico_V5 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Carico_V6
IF V_S_All_Carico_V6 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Carico_V7
IF V_S_All_Carico_V7 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Carico_V8
IF V_S_All_Carico_V8 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Carico_V9
IF V_S_All_Carico_V9 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Cond_V1
IF V_S_All_Cond_V1 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Cond_V2
IF V_S_All_Cond_V2 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Cond_V3
IF V_S_All_Cond_V3 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Cond_V4
IF V_S_All_Cond_V4 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Cond_V5
IF V_S_All_Cond_V5 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Cond_V6
IF V_S_All_Cond_V6 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Cond_V7
IF V_S_All_Cond_V7 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Cond_V8
IF V_S_All_Cond_V8 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Cond_V9
IF V_S_All_Cond_V9 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_pH_V1
IF V_S_All_pH_V1 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_pH_V2
IF V_S_All_pH_V2 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_pH_V3
IF V_S_All_pH_V3 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_pH_V4
IF V_S_All_pH_V4 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_pH_V5
IF V_S_All_pH_V5 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_pH_V6
IF V_S_All_pH_V6 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_pH_V7
IF V_S_All_pH_V7 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_pH_V8
IF V_S_All_pH_V8 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_pH_V9
IF V_S_All_pH_V9 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Sfioro_V1
IF V_S_All_Sfioro_V1 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Sfioro_V2
IF V_S_All_Sfioro_V2 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Sfioro_V3
IF V_S_All_Sfioro_V3 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Sfioro_V4
IF V_S_All_Sfioro_V4 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Sfioro_V5
IF V_S_All_Sfioro_V5 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Sfioro_V6
IF V_S_All_Sfioro_V6 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Sfioro_V7
IF V_S_All_Sfioro_V7 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Sfioro_V8
IF V_S_All_Sfioro_V8 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Sfioro_V9
IF V_S_All_Sfioro_V9 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Filtro_V1
IF V_S_All_Filtro_V1 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Filtro_V2
IF V_S_All_Filtro_V2 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Filtro_V3
IF V_S_All_Filtro_V3 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Filtro_V4
IF V_S_All_Filtro_V4 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Filtro_V5
IF V_S_All_Filtro_V5 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Filtro_V6
IF V_S_All_Filtro_V6 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Filtro_V7
IF V_S_All_Filtro_V7 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Filtro_V8
IF V_S_All_Filtro_V8 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Filtro_V9
IF V_S_All_Filtro_V9 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Chim_V1
IF V_S_All_Chim_V1 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Chim_V2
IF V_S_All_Chim_V2 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Chim_V3
IF V_S_All_Chim_V3 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Chim_V4
IF V_S_All_Chim_V4 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Chim_V5
IF V_S_All_Chim_V5 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Chim_V6
IF V_S_All_Chim_V6 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Chim_V7
IF V_S_All_Chim_V7 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Chim_V8
IF V_S_All_Chim_V8 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Chim_V9
IF V_S_All_Chim_V9 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Rabbocco_V1
IF V_S_All_Rabbocco_V1 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Rabbocco_V2
IF V_S_All_Rabbocco_V2 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Rabbocco_V3
IF V_S_All_Rabbocco_V3 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Rabbocco_V4
IF V_S_All_Rabbocco_V4 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Rabbocco_V5
IF V_S_All_Rabbocco_V5 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Rabbocco_V6
IF V_S_All_Rabbocco_V6 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Rabbocco_V7
IF V_S_All_Rabbocco_V7 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Rabbocco_V8
IF V_S_All_Rabbocco_V8 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

// CONTEGGIO ALLARMI: V_S_All_Rabbocco_V9
IF V_S_All_Rabbocco_V9 THEN
    V_S_Allarmi_Att := V_S_Allarmi_Att + 1;
END_IF;

//==========================================================================
//  SEZIONE AUSILIARI
//==========================================================================

// BASE TEMPI DEL LOG: un impulso al secondo
Tim_Log(In := Mem_Ciclo AND NOT Tim_Log.Q, PT := T#1s);

// LOG: passo di ricetta in corso verso lo SCADA
IF (Tim_Log.Q AND NOT _fp_Tim_Log_Q) THEN
    V_S_Passo := V_S_Pos_Robot;
END_IF;

// SEMIAUTOMATICO: carico manuale della vasca 1
IF V_S_Semiauto AND NOT Mem_Ciclo AND Consensi AND NOT IN_Liv_Max_V1 AND IN_DIW_Press THEN
    Req_Carico_V1 := TRUE;
END_IF;

// SEMIAUTOMATICO: carico manuale della vasca 2
IF V_S_Semiauto AND NOT Mem_Ciclo AND Consensi AND NOT IN_Liv_Max_V2 AND IN_DIW_Press THEN
    Req_Carico_V2 := TRUE;
END_IF;

// SEMIAUTOMATICO: carico manuale della vasca 3
IF V_S_Semiauto AND NOT Mem_Ciclo AND Consensi AND NOT IN_Liv_Max_V3 AND IN_DIW_Press THEN
    Req_Carico_V3 := TRUE;
END_IF;

// SEMIAUTOMATICO: carico manuale della vasca 4
IF V_S_Semiauto AND NOT Mem_Ciclo AND Consensi AND NOT IN_Liv_Max_V4 AND IN_DIW_Press THEN
    Req_Carico_V4 := TRUE;
END_IF;

// SEMIAUTOMATICO: carico manuale della vasca 5
IF V_S_Semiauto AND NOT Mem_Ciclo AND Consensi AND NOT IN_Liv_Max_V5 AND IN_DIW_Press THEN
    Req_Carico_V5 := TRUE;
END_IF;

// SEMIAUTOMATICO: carico manuale della vasca 6
IF V_S_Semiauto AND NOT Mem_Ciclo AND Consensi AND NOT IN_Liv_Max_V6 AND IN_DIW_Press THEN
    Req_Carico_V6 := TRUE;
END_IF;

// SEMIAUTOMATICO: carico manuale della vasca 7
IF V_S_Semiauto AND NOT Mem_Ciclo AND Consensi AND NOT IN_Liv_Max_V7 AND IN_DIW_Press THEN
    Req_Carico_V7 := TRUE;
END_IF;

// SEMIAUTOMATICO: carico manuale della vasca 8
IF V_S_Semiauto AND NOT Mem_Ciclo AND Consensi AND NOT IN_Liv_Max_V8 AND IN_DIW_Press THEN
    Req_Carico_V8 := TRUE;
END_IF;

// SEMIAUTOMATICO: carico manuale della vasca 9
IF V_S_Semiauto AND NOT Mem_Ciclo AND Consensi AND NOT IN_Liv_Max_V9 AND IN_DIW_Press THEN
    Req_Carico_V9 := TRUE;
END_IF;

//--------------------------------------------------------------------------
// Memorie dei fronti: aggiornate alla FINE, dopo tutti gli usi.
// E' cosi' che il contatto di fronte del ladder si rende in ST.
//--------------------------------------------------------------------------
_fp_V_P_Start := V_P_Start;
_fp_V_P_Reset := V_P_Reset;
_fp_V_P_Stop := V_P_Stop;
_fp_V_P_Pausa := V_P_Pausa;
_fp_End_V1 := End_V1;
_fp_End_V2 := End_V2;
_fp_End_V3 := End_V3;
_fp_End_V4 := End_V4;
_fp_End_V5 := End_V5;
_fp_End_V6 := End_V6;
_fp_End_V7 := End_V7;
_fp_End_V8 := End_V8;
_fp_End_V9 := End_V9;
_fp_Mem_Fine := Mem_Fine;
_fp_Req_Scarico_V1 := Req_Scarico_V1;
_fp_Req_Scarico_V2 := Req_Scarico_V2;
_fp_Req_Scarico_V3 := Req_Scarico_V3;
_fp_Req_Scarico_V4 := Req_Scarico_V4;
_fp_Req_Scarico_V5 := Req_Scarico_V5;
_fp_Req_Scarico_V6 := Req_Scarico_V6;
_fp_Req_Scarico_V7 := Req_Scarico_V7;
_fp_Req_Scarico_V8 := Req_Scarico_V8;
_fp_Req_Scarico_V9 := Req_Scarico_V9;
_fp_Tim_Log_Q := Tim_Log.Q;