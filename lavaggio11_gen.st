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
Seq_Attiva := (Mem_Carico OR Mem_V1 OR Mem_V2 OR Mem_V3 OR Mem_V4 OR Mem_V5 OR Mem_V6 OR Mem_V7 OR Mem_V8 OR Mem_V9 OR Mem_V10 OR Mem_V11 OR Mem_Scarico);

// CARRO SOPRA LA VASCA DA FARE: qui si ferma e cala il cestello
Mem_Target := Mem_Ciclo AND Mem_Pieno AND ((V_S_Usa_V1 AND NOT End_V1 AND IN_Pos_V1) OR (V_S_Usa_V2 AND NOT End_V2 AND IN_Pos_V2) OR (V_S_Usa_V3 AND NOT End_V3 AND IN_Pos_V3) OR (V_S_Usa_V4 AND NOT End_V4 AND IN_Pos_V4) OR (V_S_Usa_V5 AND NOT End_V5 AND IN_Pos_V5) OR (V_S_Usa_V6 AND NOT End_V6 AND IN_Pos_V6) OR (V_S_Usa_V7 AND NOT End_V7 AND IN_Pos_V7) OR (V_S_Usa_V8 AND NOT End_V8 AND IN_Pos_V8) OR (V_S_Usa_V9 AND NOT End_V9 AND IN_Pos_V9) OR (V_S_Usa_V10 AND NOT End_V10 AND IN_Pos_V10) OR (V_S_Usa_V11 AND NOT End_V11 AND IN_Pos_V11));

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
    End_V10 := FALSE;
    End_V11 := FALSE;
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

// INGRESSO VASCA 5
IF Mem_Ciclo AND Mem_Pieno AND V_S_Usa_V5 AND IN_Pos_V5 AND IN_Carro_Basso AND End_V4 AND NOT End_V5 THEN
    Mem_V5 := TRUE;
END_IF;

// PERMANENZA IN VASCA 5
Tim_V5(In := Mem_V5, PT := SET_T_V5);

// USCITA DALLA VASCA 5
IF (Tim_V5.Q OR NOT V_S_Usa_V5) AND (Mem_V5 OR (Mem_Ciclo AND NOT V_S_Usa_V5 AND End_V4)) THEN
    End_V5 := TRUE;
    Mem_V5 := FALSE;
    Mem_Estrai := TRUE;
END_IF;

// RISCALDAMENTO VASCA 5 (solo se in ricetta e livello ok)
OUT_Risc_V5 := V_S_Usa_V5 AND IN_Livello_V5 AND NOT IN_Temp_V5 AND Consensi;

// ALLARME LIVELLO VASCA 5
IF V_S_Usa_V5 AND NOT IN_Livello_V5 AND Mem_Ciclo THEN
    V_S_All_Liv_V5 := TRUE;
END_IF;

// ALLARME TEMPERATURA VASCA 5 (fuori range da troppo tempo)
Tim_Temp_V5(In := V_S_Usa_V5 AND NOT IN_Temp_V5 AND Mem_V5, PT := T#120s);
IF V_S_Usa_V5 AND NOT IN_Temp_V5 AND Mem_V5 AND Tim_Temp_V5.Q THEN
    V_S_All_Temp_V5 := TRUE;
END_IF;

// INGRESSO VASCA 6
IF Mem_Ciclo AND Mem_Pieno AND V_S_Usa_V6 AND IN_Pos_V6 AND IN_Carro_Basso AND End_V5 AND NOT End_V6 THEN
    Mem_V6 := TRUE;
END_IF;

// PERMANENZA IN VASCA 6
Tim_V6(In := Mem_V6, PT := SET_T_V6);

// USCITA DALLA VASCA 6
IF (Tim_V6.Q OR NOT V_S_Usa_V6) AND (Mem_V6 OR (Mem_Ciclo AND NOT V_S_Usa_V6 AND End_V5)) THEN
    End_V6 := TRUE;
    Mem_V6 := FALSE;
    Mem_Estrai := TRUE;
END_IF;

// RISCALDAMENTO VASCA 6 (solo se in ricetta e livello ok)
OUT_Risc_V6 := V_S_Usa_V6 AND IN_Livello_V6 AND NOT IN_Temp_V6 AND Consensi;

// ALLARME LIVELLO VASCA 6
IF V_S_Usa_V6 AND NOT IN_Livello_V6 AND Mem_Ciclo THEN
    V_S_All_Liv_V6 := TRUE;
END_IF;

// ALLARME TEMPERATURA VASCA 6 (fuori range da troppo tempo)
Tim_Temp_V6(In := V_S_Usa_V6 AND NOT IN_Temp_V6 AND Mem_V6, PT := T#120s);
IF V_S_Usa_V6 AND NOT IN_Temp_V6 AND Mem_V6 AND Tim_Temp_V6.Q THEN
    V_S_All_Temp_V6 := TRUE;
END_IF;

// INGRESSO VASCA 7
IF Mem_Ciclo AND Mem_Pieno AND V_S_Usa_V7 AND IN_Pos_V7 AND IN_Carro_Basso AND End_V6 AND NOT End_V7 THEN
    Mem_V7 := TRUE;
END_IF;

// PERMANENZA IN VASCA 7
Tim_V7(In := Mem_V7, PT := SET_T_V7);

// USCITA DALLA VASCA 7
IF (Tim_V7.Q OR NOT V_S_Usa_V7) AND (Mem_V7 OR (Mem_Ciclo AND NOT V_S_Usa_V7 AND End_V6)) THEN
    End_V7 := TRUE;
    Mem_V7 := FALSE;
    Mem_Estrai := TRUE;
END_IF;

// RISCALDAMENTO VASCA 7 (solo se in ricetta e livello ok)
OUT_Risc_V7 := V_S_Usa_V7 AND IN_Livello_V7 AND NOT IN_Temp_V7 AND Consensi;

// ALLARME LIVELLO VASCA 7
IF V_S_Usa_V7 AND NOT IN_Livello_V7 AND Mem_Ciclo THEN
    V_S_All_Liv_V7 := TRUE;
END_IF;

// ALLARME TEMPERATURA VASCA 7 (fuori range da troppo tempo)
Tim_Temp_V7(In := V_S_Usa_V7 AND NOT IN_Temp_V7 AND Mem_V7, PT := T#120s);
IF V_S_Usa_V7 AND NOT IN_Temp_V7 AND Mem_V7 AND Tim_Temp_V7.Q THEN
    V_S_All_Temp_V7 := TRUE;
END_IF;

// INGRESSO VASCA 8
IF Mem_Ciclo AND Mem_Pieno AND V_S_Usa_V8 AND IN_Pos_V8 AND IN_Carro_Basso AND End_V7 AND NOT End_V8 THEN
    Mem_V8 := TRUE;
END_IF;

// PERMANENZA IN VASCA 8
Tim_V8(In := Mem_V8, PT := SET_T_V8);

// USCITA DALLA VASCA 8
IF (Tim_V8.Q OR NOT V_S_Usa_V8) AND (Mem_V8 OR (Mem_Ciclo AND NOT V_S_Usa_V8 AND End_V7)) THEN
    End_V8 := TRUE;
    Mem_V8 := FALSE;
    Mem_Estrai := TRUE;
END_IF;

// RISCALDAMENTO VASCA 8 (solo se in ricetta e livello ok)
OUT_Risc_V8 := V_S_Usa_V8 AND IN_Livello_V8 AND NOT IN_Temp_V8 AND Consensi;

// ALLARME LIVELLO VASCA 8
IF V_S_Usa_V8 AND NOT IN_Livello_V8 AND Mem_Ciclo THEN
    V_S_All_Liv_V8 := TRUE;
END_IF;

// ALLARME TEMPERATURA VASCA 8 (fuori range da troppo tempo)
Tim_Temp_V8(In := V_S_Usa_V8 AND NOT IN_Temp_V8 AND Mem_V8, PT := T#120s);
IF V_S_Usa_V8 AND NOT IN_Temp_V8 AND Mem_V8 AND Tim_Temp_V8.Q THEN
    V_S_All_Temp_V8 := TRUE;
END_IF;

// INGRESSO VASCA 9
IF Mem_Ciclo AND Mem_Pieno AND V_S_Usa_V9 AND IN_Pos_V9 AND IN_Carro_Basso AND End_V8 AND NOT End_V9 THEN
    Mem_V9 := TRUE;
END_IF;

// PERMANENZA IN VASCA 9
Tim_V9(In := Mem_V9, PT := SET_T_V9);

// USCITA DALLA VASCA 9
IF (Tim_V9.Q OR NOT V_S_Usa_V9) AND (Mem_V9 OR (Mem_Ciclo AND NOT V_S_Usa_V9 AND End_V8)) THEN
    End_V9 := TRUE;
    Mem_V9 := FALSE;
    Mem_Estrai := TRUE;
END_IF;

// RISCALDAMENTO VASCA 9 (solo se in ricetta e livello ok)
OUT_Risc_V9 := V_S_Usa_V9 AND IN_Livello_V9 AND NOT IN_Temp_V9 AND Consensi;

// ALLARME LIVELLO VASCA 9
IF V_S_Usa_V9 AND NOT IN_Livello_V9 AND Mem_Ciclo THEN
    V_S_All_Liv_V9 := TRUE;
END_IF;

// ALLARME TEMPERATURA VASCA 9 (fuori range da troppo tempo)
Tim_Temp_V9(In := V_S_Usa_V9 AND NOT IN_Temp_V9 AND Mem_V9, PT := T#120s);
IF V_S_Usa_V9 AND NOT IN_Temp_V9 AND Mem_V9 AND Tim_Temp_V9.Q THEN
    V_S_All_Temp_V9 := TRUE;
END_IF;

// INGRESSO VASCA 10
IF Mem_Ciclo AND Mem_Pieno AND V_S_Usa_V10 AND IN_Pos_V10 AND IN_Carro_Basso AND End_V9 AND NOT End_V10 THEN
    Mem_V10 := TRUE;
END_IF;

// PERMANENZA IN VASCA 10
Tim_V10(In := Mem_V10, PT := SET_T_V10);

// USCITA DALLA VASCA 10
IF (Tim_V10.Q OR NOT V_S_Usa_V10) AND (Mem_V10 OR (Mem_Ciclo AND NOT V_S_Usa_V10 AND End_V9)) THEN
    End_V10 := TRUE;
    Mem_V10 := FALSE;
    Mem_Estrai := TRUE;
END_IF;

// RISCALDAMENTO VASCA 10 (solo se in ricetta e livello ok)
OUT_Risc_V10 := V_S_Usa_V10 AND IN_Livello_V10 AND NOT IN_Temp_V10 AND Consensi;

// ALLARME LIVELLO VASCA 10
IF V_S_Usa_V10 AND NOT IN_Livello_V10 AND Mem_Ciclo THEN
    V_S_All_Liv_V10 := TRUE;
END_IF;

// ALLARME TEMPERATURA VASCA 10 (fuori range da troppo tempo)
Tim_Temp_V10(In := V_S_Usa_V10 AND NOT IN_Temp_V10 AND Mem_V10, PT := T#120s);
IF V_S_Usa_V10 AND NOT IN_Temp_V10 AND Mem_V10 AND Tim_Temp_V10.Q THEN
    V_S_All_Temp_V10 := TRUE;
END_IF;

// INGRESSO VASCA 11
IF Mem_Ciclo AND Mem_Pieno AND V_S_Usa_V11 AND IN_Pos_V11 AND IN_Carro_Basso AND End_V10 AND NOT End_V11 THEN
    Mem_V11 := TRUE;
END_IF;

// PERMANENZA IN VASCA 11
Tim_V11(In := Mem_V11, PT := SET_T_V11);

// USCITA DALLA VASCA 11
IF (Tim_V11.Q OR NOT V_S_Usa_V11) AND (Mem_V11 OR (Mem_Ciclo AND NOT V_S_Usa_V11 AND End_V10)) THEN
    End_V11 := TRUE;
    Mem_V11 := FALSE;
    Mem_Estrai := TRUE;
END_IF;

// RISCALDAMENTO VASCA 11 (solo se in ricetta e livello ok)
OUT_Risc_V11 := V_S_Usa_V11 AND IN_Livello_V11 AND NOT IN_Temp_V11 AND Consensi;

// ALLARME LIVELLO VASCA 11
IF V_S_Usa_V11 AND NOT IN_Livello_V11 AND Mem_Ciclo THEN
    V_S_All_Liv_V11 := TRUE;
END_IF;

// ALLARME TEMPERATURA VASCA 11 (fuori range da troppo tempo)
Tim_Temp_V11(In := V_S_Usa_V11 AND NOT IN_Temp_V11 AND Mem_V11, PT := T#120s);
IF V_S_Usa_V11 AND NOT IN_Temp_V11 AND Mem_V11 AND Tim_Temp_V11.Q THEN
    V_S_All_Temp_V11 := TRUE;
END_IF;

// DEPOSITO ALLO SCARICO
IF Mem_Ciclo AND End_V11 AND IN_Pos_Scarico AND IN_Carro_Basso AND Mem_Pieno THEN
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
OUT_Abbassa := (Mem_Target OR (Mem_Ciclo AND Mem_Pieno AND End_V11 AND IN_Pos_Scarico)) AND NOT IN_Carro_Basso AND NOT Mem_Estrai AND Consensi;

// RESET ALLARMI
IF (V_P_Reset AND NOT _fp_V_P_Reset) THEN
    V_S_All_Liv_V1 := FALSE;
    V_S_All_Liv_V2 := FALSE;
    V_S_All_Liv_V3 := FALSE;
    V_S_All_Liv_V4 := FALSE;
    V_S_All_Liv_V5 := FALSE;
    V_S_All_Liv_V6 := FALSE;
    V_S_All_Liv_V7 := FALSE;
    V_S_All_Liv_V8 := FALSE;
    V_S_All_Liv_V9 := FALSE;
    V_S_All_Liv_V10 := FALSE;
    V_S_All_Liv_V11 := FALSE;
    V_S_All_Temp_V1 := FALSE;
    V_S_All_Temp_V2 := FALSE;
    V_S_All_Temp_V3 := FALSE;
    V_S_All_Temp_V4 := FALSE;
    V_S_All_Temp_V5 := FALSE;
    V_S_All_Temp_V6 := FALSE;
    V_S_All_Temp_V7 := FALSE;
    V_S_All_Temp_V8 := FALSE;
    V_S_All_Temp_V9 := FALSE;
    V_S_All_Temp_V10 := FALSE;
    V_S_All_Temp_V11 := FALSE;
END_IF;

// SPIA ALLARME CUMULATIVO
V_L_Allarme := (V_S_All_Liv_V1 OR V_S_All_Liv_V2 OR V_S_All_Liv_V3 OR V_S_All_Liv_V4 OR V_S_All_Liv_V5 OR V_S_All_Liv_V6 OR V_S_All_Liv_V7 OR V_S_All_Liv_V8 OR V_S_All_Liv_V9 OR V_S_All_Liv_V10 OR V_S_All_Liv_V11 OR V_S_All_Temp_V1 OR V_S_All_Temp_V2 OR V_S_All_Temp_V3 OR V_S_All_Temp_V4 OR V_S_All_Temp_V5 OR V_S_All_Temp_V6 OR V_S_All_Temp_V7 OR V_S_All_Temp_V8 OR V_S_All_Temp_V9 OR V_S_All_Temp_V10 OR V_S_All_Temp_V11 OR NOT Consensi);

// SPIA CICLO
V_L_Ciclo := Mem_Ciclo;

// SPIA FINE CICLO
V_L_Fine_Ciclo := Mem_Fine;

// ALLARME TRASLAZIONE: il carro non arriva entro il tempo
IF Tim_Traslazione.Q THEN
    V_S_All_Traslazione := TRUE;
END_IF;

// RESET ALLARME TRASLAZIONE
IF (V_P_Reset AND NOT _fp_V_P_Reset) THEN
    V_S_All_Traslazione := FALSE;
END_IF;

// RISCALDAMENTO IN CORSO: almeno una resistenza inserita
V_L_Riscaldamento := (OUT_Risc_V1 OR OUT_Risc_V2 OR OUT_Risc_V3 OR OUT_Risc_V4 OR OUT_Risc_V5 OR OUT_Risc_V6 OR OUT_Risc_V7 OR OUT_Risc_V8 OR OUT_Risc_V9 OR OUT_Risc_V10 OR OUT_Risc_V11);

// MACCHINA PRONTA: consensi presenti e nessun allarme
V_L_Pronto := Consensi AND NOT V_L_Allarme AND NOT V_S_All_Traslazione;

//--------------------------------------------------------------------------
// Memorie dei fronti: aggiornate alla FINE, dopo tutti gli usi.
// E' cosi' che il contatto di fronte del ladder si rende in ST.
//--------------------------------------------------------------------------
_fp_V_P_Start := V_P_Start;
_fp_V_P_Stop := V_P_Stop;
_fp_V_P_Reset := V_P_Reset;