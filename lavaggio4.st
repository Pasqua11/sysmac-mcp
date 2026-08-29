//==========================================================================
//  SEZIONE LAVAGGIO
//==========================================================================

// CONSENSI DI SICUREZZA
Consensi := NOT IN_Emergenza AND IN_Protezioni AND IN_Press_Aria;

// START CICLO (azzera anche il fine ciclo precedente)
IF (V_P_Start AND NOT _fp_V_P_Start) AND Consensi AND V_S_Auto AND IN_Presenza_Cesto AND NOT Seq_Attiva THEN
    Mem_Fine := FALSE;
    Mem_Ciclo := TRUE;
END_IF;

// ARRESTO CICLO
IF ((V_P_Stop AND NOT _fp_V_P_Stop) OR NOT Consensi OR Mem_Fine) THEN
    Mem_Ciclo := FALSE;
END_IF;

// SEQUENZA ATTIVA: un passo qualsiasi in corso
Seq_Attiva := (Mem_Carico OR Mem_V1 OR Mem_V2 OR Mem_V3 OR Mem_V4 OR Mem_Scarico);

// CARRO SOPRA LA VASCA DA FARE: qui si ferma e cala il cestello
Mem_Target := Mem_Ciclo AND Mem_Pieno AND ((V_S_Usa_V1 AND NOT End_V1 AND IN_Pos_V1) OR (V_S_Usa_V2 AND NOT End_V2 AND IN_Pos_V2) OR (V_S_Usa_V3 AND NOT End_V3 AND IN_Pos_V3) OR (V_S_Usa_V4 AND NOT End_V4 AND IN_Pos_V4));

// AZZERAMENTO PASSI A INIZIO CICLO
IF (V_P_Start AND NOT _fp_V_P_Start) THEN
    End_V1 := FALSE;
    End_V2 := FALSE;
    End_V3 := FALSE;
    End_V4 := FALSE;
END_IF;

// PRELIEVO AL CARICO
IF Mem_Ciclo AND IN_Pos_Carico AND IN_Presenza_Cesto AND NOT Mem_Pieno THEN
    Mem_Carico := TRUE;
END_IF;

// CESTELLO PRELEVATO
IF Mem_Carico AND IN_Carro_Alto THEN
    Mem_Pieno := TRUE;
    Mem_Carico := FALSE;
END_IF;

// INGRESSO VASCA 1
IF Mem_Ciclo AND Mem_Pieno AND V_S_Usa_V1 AND IN_Pos_V1 AND IN_Carro_Basso AND Mem_Pieno AND NOT End_V1 THEN
    Mem_V1 := TRUE;
END_IF;

// PERMANENZA IN VASCA 1
Tim_V1(In := Mem_V1, PT := SET_T_V1);

// USCITA DALLA VASCA 1
IF (Tim_V1.Q OR NOT V_S_Usa_V1) AND (Mem_V1 OR (Mem_Ciclo AND NOT V_S_Usa_V1 AND Mem_Pieno)) THEN
    End_V1 := TRUE;
    Mem_V1 := FALSE;
    Mem_Estrai := TRUE;
END_IF;

// RISCALDAMENTO VASCA 1 (solo se in ricetta e livello ok)
OUT_Risc_V1 := V_S_Usa_V1 AND IN_Livello_V1 AND NOT IN_Temp_V1 AND Consensi;

// ALLARME LIVELLO VASCA 1
IF V_S_Usa_V1 AND NOT IN_Livello_V1 AND Mem_Ciclo THEN
    V_S_All_Liv_V1 := TRUE;
END_IF;

// ALLARME TEMPERATURA VASCA 1 (fuori range da troppo tempo)
Tim_Temp_V1(In := V_S_Usa_V1 AND NOT IN_Temp_V1 AND Mem_V1, PT := T#120s);
IF V_S_Usa_V1 AND NOT IN_Temp_V1 AND Mem_V1 AND Tim_Temp_V1.Q THEN
    V_S_All_Temp_V1 := TRUE;
END_IF;

// INGRESSO VASCA 2
IF Mem_Ciclo AND Mem_Pieno AND V_S_Usa_V2 AND IN_Pos_V2 AND IN_Carro_Basso AND End_V1 AND NOT End_V2 THEN
    Mem_V2 := TRUE;
END_IF;

// PERMANENZA IN VASCA 2
Tim_V2(In := Mem_V2, PT := SET_T_V2);

// USCITA DALLA VASCA 2
IF (Tim_V2.Q OR NOT V_S_Usa_V2) AND (Mem_V2 OR (Mem_Ciclo AND NOT V_S_Usa_V2 AND End_V1)) THEN
    End_V2 := TRUE;
    Mem_V2 := FALSE;
    Mem_Estrai := TRUE;
END_IF;

// RISCALDAMENTO VASCA 2 (solo se in ricetta e livello ok)
OUT_Risc_V2 := V_S_Usa_V2 AND IN_Livello_V2 AND NOT IN_Temp_V2 AND Consensi;

// ALLARME LIVELLO VASCA 2
IF V_S_Usa_V2 AND NOT IN_Livello_V2 AND Mem_Ciclo THEN
    V_S_All_Liv_V2 := TRUE;
END_IF;

// ALLARME TEMPERATURA VASCA 2 (fuori range da troppo tempo)
Tim_Temp_V2(In := V_S_Usa_V2 AND NOT IN_Temp_V2 AND Mem_V2, PT := T#120s);
IF V_S_Usa_V2 AND NOT IN_Temp_V2 AND Mem_V2 AND Tim_Temp_V2.Q THEN
    V_S_All_Temp_V2 := TRUE;
END_IF;

// INGRESSO VASCA 3
IF Mem_Ciclo AND Mem_Pieno AND V_S_Usa_V3 AND IN_Pos_V3 AND IN_Carro_Basso AND End_V2 AND NOT End_V3 THEN
    Mem_V3 := TRUE;
END_IF;

// PERMANENZA IN VASCA 3
Tim_V3(In := Mem_V3, PT := SET_T_V3);

// USCITA DALLA VASCA 3
IF (Tim_V3.Q OR NOT V_S_Usa_V3) AND (Mem_V3 OR (Mem_Ciclo AND NOT V_S_Usa_V3 AND End_V2)) THEN
    End_V3 := TRUE;
    Mem_V3 := FALSE;
    Mem_Estrai := TRUE;
END_IF;

// RISCALDAMENTO VASCA 3 (solo se in ricetta e livello ok)
OUT_Risc_V3 := V_S_Usa_V3 AND IN_Livello_V3 AND NOT IN_Temp_V3 AND Consensi;

// ALLARME LIVELLO VASCA 3
IF V_S_Usa_V3 AND NOT IN_Livello_V3 AND Mem_Ciclo THEN
    V_S_All_Liv_V3 := TRUE;
END_IF;

// ALLARME TEMPERATURA VASCA 3 (fuori range da troppo tempo)
Tim_Temp_V3(In := V_S_Usa_V3 AND NOT IN_Temp_V3 AND Mem_V3, PT := T#120s);
IF V_S_Usa_V3 AND NOT IN_Temp_V3 AND Mem_V3 AND Tim_Temp_V3.Q THEN
    V_S_All_Temp_V3 := TRUE;
END_IF;

// INGRESSO VASCA 4
IF Mem_Ciclo AND Mem_Pieno AND V_S_Usa_V4 AND IN_Pos_V4 AND IN_Carro_Basso AND End_V3 AND NOT End_V4 THEN
    Mem_V4 := TRUE;
END_IF;

// PERMANENZA IN VASCA 4
Tim_V4(In := Mem_V4, PT := SET_T_V4);

// USCITA DALLA VASCA 4
IF (Tim_V4.Q OR NOT V_S_Usa_V4) AND (Mem_V4 OR (Mem_Ciclo AND NOT V_S_Usa_V4 AND End_V3)) THEN
    End_V4 := TRUE;
    Mem_V4 := FALSE;
    Mem_Estrai := TRUE;
END_IF;

// RISCALDAMENTO VASCA 4 (solo se in ricetta e livello ok)
OUT_Risc_V4 := V_S_Usa_V4 AND IN_Livello_V4 AND NOT IN_Temp_V4 AND Consensi;

// ALLARME LIVELLO VASCA 4
IF V_S_Usa_V4 AND NOT IN_Livello_V4 AND Mem_Ciclo THEN
    V_S_All_Liv_V4 := TRUE;
END_IF;

// ALLARME TEMPERATURA VASCA 4 (fuori range da troppo tempo)
Tim_Temp_V4(In := V_S_Usa_V4 AND NOT IN_Temp_V4 AND Mem_V4, PT := T#120s);
IF V_S_Usa_V4 AND NOT IN_Temp_V4 AND Mem_V4 AND Tim_Temp_V4.Q THEN
    V_S_All_Temp_V4 := TRUE;
END_IF;

// DEPOSITO ALLO SCARICO
IF Mem_Ciclo AND End_V4 AND IN_Pos_Scarico AND IN_Carro_Basso AND Mem_Pieno THEN
    Mem_Scarico := TRUE;
END_IF;

// CESTELLO DEPOSITATO
IF Mem_Scarico AND IN_Carro_Alto THEN
    Mem_Pieno := FALSE;
    Mem_Scarico := FALSE;
    Mem_Fine := TRUE;
    V_S_Cicli_Fatti := V_S_Cicli_Fatti + 1;
END_IF;

// TRASLAZIONE AVANTI: verso la vasca successiva o lo scarico
OUT_Carro_Avanti := Mem_Ciclo AND Mem_Pieno AND IN_Carro_Alto AND NOT Mem_Target AND NOT IN_Pos_Scarico AND Consensi;

// TRASLAZIONE INDIETRO: rientro a vuoto al carico
OUT_Carro_Indietro := Mem_Ciclo AND NOT Mem_Pieno AND IN_Carro_Alto AND NOT IN_Pos_Carico AND Consensi;

// SORVEGLIANZA TEMPO DI TRASLAZIONE
Tim_Traslazione(In := (OUT_Carro_Avanti OR OUT_Carro_Indietro), PT := SET_T_Traslazione);

// FINE ESTRAZIONE DALLA VASCA
IF IN_Carro_Alto THEN
    Mem_Estrai := FALSE;
END_IF;

// SOLLEVAMENTO CESTELLO
OUT_Solleva := (Mem_Carico OR Mem_Scarico OR Mem_Estrai) AND NOT IN_Carro_Alto AND Consensi;

// ABBASSAMENTO CESTELLO (in vasca o sulla stazione di scarico)
OUT_Abbassa := (Mem_Target OR (Mem_Ciclo AND Mem_Pieno AND End_V4 AND IN_Pos_Scarico)) AND NOT IN_Carro_Basso AND NOT Mem_Estrai AND Consensi;

// RESET ALLARMI
IF (V_P_Reset AND NOT _fp_V_P_Reset) THEN
    V_S_All_Liv_V1 := FALSE;
    V_S_All_Liv_V2 := FALSE;
    V_S_All_Liv_V3 := FALSE;
    V_S_All_Liv_V4 := FALSE;
    V_S_All_Temp_V1 := FALSE;
    V_S_All_Temp_V2 := FALSE;
    V_S_All_Temp_V3 := FALSE;
    V_S_All_Temp_V4 := FALSE;
END_IF;

// SPIA ALLARME CUMULATIVO
V_L_Allarme := (V_S_All_Liv_V1 OR V_S_All_Liv_V2 OR V_S_All_Liv_V3 OR V_S_All_Liv_V4 OR V_S_All_Temp_V1 OR V_S_All_Temp_V2 OR V_S_All_Temp_V3 OR V_S_All_Temp_V4 OR NOT Consensi);

// SPIA CICLO
V_L_Ciclo := Mem_Ciclo;

// SPIA FINE CICLO
V_L_Fine_Ciclo := Mem_Fine;

//--------------------------------------------------------------------------
// Memorie dei fronti: aggiornate alla FINE, dopo tutti gli usi.
// E' cosi' che il contatto di fronte del ladder si rende in ST.
//--------------------------------------------------------------------------
_fp_V_P_Start := V_P_Start;
_fp_V_P_Stop := V_P_Stop;
_fp_V_P_Start := V_P_Start;
_fp_V_P_Reset := V_P_Reset;