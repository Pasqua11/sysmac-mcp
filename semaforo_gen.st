//==========================================================================
//  SEZIONE SEMAFORO
//==========================================================================

// CLOCK 1 SECONDO (lampeggio giallo notturno)
Clock_1s := P_On;
IF P_On THEN
    // DA COMPLETARE: Get1sClk();
END_IF;

// EMERGENZA: fungo premuto o lampada rossa guasta
Mem_Emergenza := (IN_Emergenza OR IN_Guasto_Rosso_NS OR IN_Guasto_Rosso_EO);

// CONSENSO AL CICLO AUTOMATICO
Mem_Ciclo := IN_Marcia AND V_S_Auto AND NOT V_S_Notte AND NOT Mem_Emergenza;

// PARTENZA CICLO DALLA FASE 1
IF Mem_Ciclo AND NOT Mem_F1 AND NOT Mem_F2 AND NOT Mem_F3 AND NOT Mem_F4 AND NOT Mem_F5 AND NOT Mem_F6 THEN
    Mem_F1 := TRUE;
END_IF;

// ARRESTO CICLO: azzera tutte le fasi
IF NOT Mem_Ciclo THEN
    Mem_F1 := FALSE;
    Mem_F2 := FALSE;
    Mem_F3 := FALSE;
    Mem_F4 := FALSE;
    Mem_F5 := FALSE;
    Mem_F6 := FALSE;
END_IF;

// FASE 1 - VERDE NORD-SUD: durata e verde minimo
Tim_F1(In := Mem_F1, PT := SET_T_Verde_NS);
Tim_F1min(In := Mem_F1, PT := SET_T_Verde_Min);

// FINE FASE 1 -> FASE 2 (anticipata dalla chiamata pedonale NS)
IF Mem_F1 AND (Tim_F1.Q OR (Mem_Ped_NS AND Tim_F1min.Q)) THEN
    Mem_F1 := FALSE;
    Mem_F2 := TRUE;
    Mem_Ped_NS := FALSE;
END_IF;

// FASE 2 - GIALLO NORD-SUD
Tim_F2(In := Mem_F2, PT := SET_T_Giallo);

// FINE FASE 2 -> FASE 3
IF Mem_F2 AND Tim_F2.Q THEN
    Mem_F2 := FALSE;
    Mem_F3 := TRUE;
END_IF;

// FASE 3 - TUTTO ROSSO DI SICUREZZA
Tim_F3(In := Mem_F3, PT := SET_T_TuttoRosso);

// FINE FASE 3 -> FASE 4
IF Mem_F3 AND Tim_F3.Q THEN
    Mem_F3 := FALSE;
    Mem_F4 := TRUE;
END_IF;

// FASE 4 - VERDE EST-OVEST: durata e verde minimo
Tim_F4(In := Mem_F4, PT := SET_T_Verde_EO);
Tim_F4min(In := Mem_F4, PT := SET_T_Verde_Min);

// FINE FASE 4 -> FASE 5 (anticipata dalla chiamata pedonale EO)
IF Mem_F4 AND (Tim_F4.Q OR (Mem_Ped_EO AND Tim_F4min.Q)) THEN
    Mem_F4 := FALSE;
    Mem_F5 := TRUE;
    Mem_Ped_EO := FALSE;
END_IF;

// FASE 5 - GIALLO EST-OVEST
Tim_F5(In := Mem_F5, PT := SET_T_Giallo);

// FINE FASE 5 -> FASE 6
IF Mem_F5 AND Tim_F5.Q THEN
    Mem_F5 := FALSE;
    Mem_F6 := TRUE;
END_IF;

// FASE 6 - TUTTO ROSSO DI SICUREZZA
Tim_F6(In := Mem_F6, PT := SET_T_TuttoRosso);

// FINE FASE 6 -> FASE 1: ciclo completato
IF Mem_F6 AND Tim_F6.Q THEN
    Mem_F6 := FALSE;
    Mem_F1 := TRUE;
    V_S_Cicli_Completati := V_S_Cicli_Completati + 1;
END_IF;

// CHIAMATA PEDONALE NORD-SUD
IF (V_P_Chiam_Ped_NS AND NOT _fp_V_P_Chiam_Ped_NS) THEN
    Mem_Ped_NS := TRUE;
END_IF;

// CHIAMATA PEDONALE EST-OVEST
IF (V_P_Chiam_Ped_EO AND NOT _fp_V_P_Chiam_Ped_EO) THEN
    Mem_Ped_EO := TRUE;
END_IF;

// SPIE DI PRENOTAZIONE PEDONALE
V_L_Ped_NS_Prenotato := Mem_Ped_NS;

// SPIA PRENOTAZIONE PEDONALE EST-OVEST
V_L_Ped_EO_Prenotato := Mem_Ped_EO;

// VERDE NORD-SUD
OUT_NS_Verde := Mem_F1;

// GIALLO NORD-SUD (anche lampeggiante di notte)
OUT_NS_Giallo := (Mem_F2 OR (V_S_Notte AND Clock_1s));

// ROSSO NORD-SUD (tutte le fasi in cui NS e' fermo, ed emergenza)
OUT_NS_Rosso := (Mem_F3 OR Mem_F4 OR Mem_F5 OR Mem_F6 OR Mem_Emergenza) AND NOT V_S_Notte;

// VERDE EST-OVEST
OUT_EO_Verde := Mem_F4;

// GIALLO EST-OVEST (anche lampeggiante di notte)
OUT_EO_Giallo := (Mem_F5 OR (V_S_Notte AND Clock_1s));

// ROSSO EST-OVEST (tutte le fasi in cui EO e' fermo, ed emergenza)
OUT_EO_Rosso := (Mem_F1 OR Mem_F2 OR Mem_F3 OR Mem_F6 OR Mem_Emergenza) AND NOT V_S_Notte;

// PEDONALE NORD-SUD VERDE (si attraversa NS mentre i veicoli EO vanno)
OUT_Ped_NS_Verde := Mem_F4 AND NOT Mem_Emergenza;

// PEDONALE NORD-SUD ROSSO
OUT_Ped_NS_Rosso := NOT Mem_F4;

// PEDONALE EST-OVEST VERDE (si attraversa EO mentre i veicoli NS vanno)
OUT_Ped_EO_Verde := Mem_F1 AND NOT Mem_Emergenza;

// PEDONALE EST-OVEST ROSSO
OUT_Ped_EO_Rosso := NOT Mem_F1;

// SPIA CICLO ATTIVO
V_L_Ciclo_Attivo := Mem_Ciclo;

// SPIA MODALITA NOTTE
V_L_Notte := V_S_Notte;

// SPIA EMERGENZA
V_L_Emergenza := Mem_Emergenza;

//--------------------------------------------------------------------------
// Memorie dei fronti: aggiornate alla FINE, dopo tutti gli usi.
// E' cosi' che il contatto di fronte del ladder si rende in ST.
//--------------------------------------------------------------------------
_fp_V_P_Chiam_Ped_NS := V_P_Chiam_Ped_NS;
_fp_V_P_Chiam_Ped_EO := V_P_Chiam_Ped_EO;