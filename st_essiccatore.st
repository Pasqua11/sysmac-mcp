//==============================================================================
//  ESSICCATORE A TRE FASI - scritto in Structured Text
//  Riscaldamento, mantenimento, raffreddamento. La sequenza e' una macchina a
//  stati con CASE: in ladder servirebbero una quarantina di rung.
//==============================================================================

// ----------------------------------------------------------------- sicurezze
Consensi := NOT IN_Emergenza AND IN_Protezioni AND IN_Termico;

IF NOT Consensi THEN
    V_S_All_Sicurezza := TRUE;
END_IF;
IF V_P_Reset AND Consensi THEN
    V_S_All_Sicurezza := FALSE;
END_IF;

// ------------------------------------------------------------ avvio e arresto
IF V_P_Start AND Consensi AND V_S_Passo = 0 AND NOT V_L_Allarme THEN
    V_S_Passo := 1;
    V_S_Cicli := V_S_Cicli + 1;
END_IF;

IF V_P_Stop OR NOT Consensi THEN
    V_S_Passo := 0;
END_IF;

// ---------------------------------------------------------- temporizzatori
// I blocchi con stato vanno chiamati a OGNI scansione, mai dentro un ramo del
// CASE: se si chiamano solo nel passo in cui servono, quando si esce da quel
// passo non vengono piu' aggiornati e restano con Q alto. Al ciclo successivo
// l'allarme scatterebbe subito. La condizione va passata come ingresso.
Tim_Salita(In := V_S_Passo = 1, PT := SET_T_Salita);
Tim_Mantieni(In := V_S_Passo = 2, PT := SET_T_Mantieni);

// -------------------------------------------------- sequenza a macchina stati
CASE V_S_Passo OF

    0:  // fermo
        OUT_Resistenze := FALSE;
        OUT_Ventola := FALSE;
        V_L_Ciclo := FALSE;

    1:  // riscaldamento fino alla temperatura di lavoro
        V_L_Ciclo := TRUE;
        OUT_Resistenze := NOT IN_Temp_Raggiunta;
        OUT_Ventola := TRUE;
        IF IN_Temp_Raggiunta THEN
            V_S_Passo := 2;
        ELSIF Tim_Salita.Q THEN
            V_S_All_Salita := TRUE;      // non arriva in temperatura
            V_S_Passo := 9;
        END_IF;

    2:  // mantenimento per il tempo di ricetta
        V_L_Ciclo := TRUE;
        OUT_Resistenze := NOT IN_Temp_Alta;
        OUT_Ventola := TRUE;
        IF Tim_Mantieni.Q THEN
            V_S_Passo := 3;
        END_IF;

    3:  // raffreddamento: resistenze spente, ventola avanti
        V_L_Ciclo := TRUE;
        OUT_Resistenze := FALSE;
        OUT_Ventola := TRUE;
        IF NOT IN_Temp_Raggiunta THEN
            V_S_Passo := 4;
        END_IF;

    4:  // ciclo completato
        V_L_Ciclo := FALSE;
        OUT_Ventola := FALSE;
        V_L_Fine := TRUE;
        IF V_P_Reset THEN
            V_L_Fine := FALSE;
            V_S_Passo := 0;
        END_IF;

    9:  // blocco per anomalia
        OUT_Resistenze := FALSE;
        OUT_Ventola := TRUE;          // si continua a ventilare per sicurezza
        V_L_Ciclo := FALSE;
        IF V_P_Reset THEN
            V_S_All_Salita := FALSE;
            V_S_Passo := 0;
        END_IF;

END_CASE;

// ------------------------------------------------------- sicurezza di massima
// la sovratemperatura toglie le resistenze in qualunque passo
IF IN_Temp_Alta THEN
    OUT_Resistenze := FALSE;
    V_S_All_Sovratemp := TRUE;
END_IF;
IF V_P_Reset AND NOT IN_Temp_Alta THEN
    V_S_All_Sovratemp := FALSE;
END_IF;

// senza consensi non si comanda niente
IF NOT Consensi THEN
    OUT_Resistenze := FALSE;
    OUT_Ventola := FALSE;
END_IF;

V_L_Allarme := V_S_All_Sicurezza OR V_S_All_Salita OR V_S_All_Sovratemp;
V_L_Pronto := Consensi AND NOT V_L_Allarme;
