//==========================================================================
//  SEZIONE NASTRO
//==========================================================================

// CONSENSI DI SICUREZZA (emergenza, protezioni, aria)
Consensi := NOT IN_Emergenza AND IN_Protezioni AND IN_Press_Aria;

// START CICLO
IF (V_P_Start AND NOT _fp_V_P_Start) AND Consensi AND NOT Mem_Lotto_Pieno THEN
    Mem_Ciclo := TRUE;
END_IF;

// ARRESTO CICLO: stop, mancanza consensi, lotto completo o inceppamento
IF ((V_P_Stop AND NOT _fp_V_P_Stop) OR NOT Consensi OR Mem_Lotto_Pieno OR V_S_Allarme_Inceppo) THEN
    Mem_Ciclo := FALSE;
END_IF;

// COMANDO MARCIA NASTRO
OUT_Nastro_Marcia := Mem_Ciclo AND Consensi;

// CONTEGGIO PEZZI IN TRANSITO (fronte della fotocellula)
IF (IN_Foto_Ingresso AND NOT _fp_IN_Foto_Ingresso) AND Mem_Ciclo THEN
    V_S_Pezzi_Contati := V_S_Pezzi_Contati + 1;
END_IF;

// PEZZO DA SCARTARE: memorizza al passaggio in fotocellula
IF (IN_Foto_Ingresso AND NOT _fp_IN_Foto_Ingresso) AND IN_Qualita_KO AND Mem_Ciclo THEN
    Mem_Scarto := TRUE;
    V_S_Pezzi_Scartati := V_S_Pezzi_Scartati + 1;
END_IF;

// TEMPO DI DEVIAZIONE ALLO SCARTO
Tim_Deviatore(In := Mem_Scarto, PT := SET_T_Deviatore);

// COMANDO DEVIATORE
OUT_Deviatore := Mem_Scarto;

// FINE DEVIAZIONE
IF Tim_Deviatore.Q THEN
    Mem_Scarto := FALSE;
END_IF;

// LOTTO COMPLETATO: pezzi contati >= pezzi impostati
IF (V_S_Pezzi_Contati >= SET_Pezzi_Lotto) AND Mem_Ciclo THEN
    Mem_Lotto_Pieno := TRUE;
END_IF;

// SORVEGLIANZA INCEPPAMENTO IN USCITA
Tim_Inceppo(In := IN_Pres_Uscita AND Mem_Ciclo, PT := SET_T_Inceppo);

// ALLARME INCEPPAMENTO
IF Tim_Inceppo.Q THEN
    V_S_Allarme_Inceppo := TRUE;
END_IF;

// RESET CONTEGGI E ALLARMI DA SCADA
IF (V_P_Reset_Conteggi AND NOT _fp_V_P_Reset_Conteggi) THEN
    Mem_Lotto_Pieno := FALSE;
    V_S_Allarme_Inceppo := FALSE;
    V_S_Pezzi_Contati := 0;
    V_S_Pezzi_Scartati := 0;
END_IF;

// SPIA CICLO
V_L_Ciclo := Mem_Ciclo;

// SPIA LOTTO COMPLETO
V_L_Lotto_Completo := Mem_Lotto_Pieno;

// SPIA ALLARME CUMULATIVO
V_L_Allarme := (V_S_Allarme_Inceppo OR NOT Consensi);

//--------------------------------------------------------------------------
// Memorie dei fronti: aggiornate alla FINE, dopo tutti gli usi.
// E' cosi' che il contatto di fronte del ladder si rende in ST.
//--------------------------------------------------------------------------
_fp_V_P_Start := V_P_Start;
_fp_V_P_Stop := V_P_Stop;
_fp_IN_Foto_Ingresso := IN_Foto_Ingresso;
_fp_V_P_Reset_Conteggi := V_P_Reset_Conteggi;