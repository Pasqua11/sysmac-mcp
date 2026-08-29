//==========================================================================
//  SEZIONE POMPE
//==========================================================================

// CONSENSI DI SICUREZZA
Consensi := NOT IN_Emergenza AND IN_Protezioni;

// RICHIESTA DI POMPAGGIO: parte al livello minimo
IF NOT IN_Livello_Min AND Consensi AND V_S_Auto THEN
    Mem_Richiesta := TRUE;
END_IF;

// FINE POMPAGGIO: livello massimo raggiunto o consensi caduti
IF (IN_Livello_Max OR NOT Consensi OR NOT V_S_Auto) THEN
    Mem_Richiesta := FALSE;
END_IF;

// ALTERNANZA: alla richiesta tocca alla pompa con meno minuti
IF (Mem_Richiesta AND NOT _fp_Mem_Richiesta) AND (V_S_Ore_P1 <= V_S_Ore_P2) AND NOT V_S_Guasto_P1 AND IN_Termico_P1 THEN
    Mem_P1_Sel := TRUE;
    Mem_P2_Sel := FALSE;
END_IF;

// ALTERNANZA: altrimenti tocca alla pompa 2
IF (Mem_Richiesta AND NOT _fp_Mem_Richiesta) AND (V_S_Ore_P1 > V_S_Ore_P2) AND NOT V_S_Guasto_P2 AND IN_Termico_P2 THEN
    Mem_P2_Sel := TRUE;
    Mem_P1_Sel := FALSE;
END_IF;

// SELEZIONE MANUALE POMPA 1 DA SCADA
IF (V_S_Pompa_Manuale = 1) THEN
    Mem_P1_Sel := TRUE;
    Mem_P2_Sel := FALSE;
END_IF;

// SELEZIONE MANUALE POMPA 2 DA SCADA
IF (V_S_Pompa_Manuale = 2) THEN
    Mem_P2_Sel := TRUE;
    Mem_P1_Sel := FALSE;
END_IF;

// COMANDO POMPA 1
OUT_Pompa_1 := Mem_Richiesta AND Mem_P1_Sel AND Consensi AND IN_Termico_P1 AND NOT V_S_Guasto_P1 AND NOT V_S_Marcia_Secco;

// COMANDO POMPA 2
OUT_Pompa_2 := Mem_Richiesta AND Mem_P2_Sel AND Consensi AND IN_Termico_P2 AND NOT V_S_Guasto_P2 AND NOT V_S_Marcia_Secco;

// SORVEGLIANZA PRESSIONE, POMPA 1 (un timer per pompa: quello unico lasciava alla riserva il tempo gia' scaduto)
Tim_Press_P1(In := OUT_Pompa_1 AND NOT IN_Press_Mandata, PT := SET_T_Pressione);

// SORVEGLIANZA PRESSIONE, POMPA 2
Tim_Press_P2(In := OUT_Pompa_2 AND NOT IN_Press_Mandata, PT := SET_T_Pressione);

// GUASTO POMPA 1: niente pressione o termico intervenuto
IF (Tim_Press_P1.Q OR NOT IN_Termico_P1) THEN
    V_S_Guasto_P1 := TRUE;
END_IF;

// GUASTO POMPA 2: niente pressione o termico intervenuto
IF (Tim_Press_P2.Q OR NOT IN_Termico_P2) THEN
    V_S_Guasto_P2 := TRUE;
END_IF;

// PASSAGGIO ALLA RISERVA: se P1 e' guasta tocca a P2
IF V_S_Guasto_P1 AND Mem_Richiesta AND NOT V_S_Guasto_P2 AND IN_Termico_P2 THEN
    Mem_P2_Sel := TRUE;
    Mem_P1_Sel := FALSE;
END_IF;

// PASSAGGIO ALLA RISERVA: se P2 e' guasta tocca a P1
IF V_S_Guasto_P2 AND Mem_Richiesta AND NOT V_S_Guasto_P1 AND IN_Termico_P1 THEN
    Mem_P1_Sel := TRUE;
    Mem_P2_Sel := FALSE;
END_IF;

// MARCIA A SECCO: livello sotto il minimo con pompa in marcia
Tim_Secco(In := (OUT_Pompa_1 OR OUT_Pompa_2) AND NOT IN_Livello_Min, PT := SET_T_Secco);

// ALLARME MARCIA A SECCO
IF Tim_Secco.Q THEN
    V_S_Marcia_Secco := TRUE;
END_IF;

// BASE TEMPI PER LE ORE DI MARCIA (impulso al minuto)
Tim_Minuto(In := (OUT_Pompa_1 OR OUT_Pompa_2) AND NOT Tim_Minuto.Q, PT := T#60s);

// CONTA MINUTI POMPA 1
IF (Tim_Minuto.Q AND NOT _fp_Tim_Minuto_Q) AND OUT_Pompa_1 THEN
    V_S_Ore_P1 := V_S_Ore_P1 + 1;
END_IF;

// CONTA MINUTI POMPA 2
IF (Tim_Minuto.Q AND NOT _fp_Tim_Minuto_Q) AND OUT_Pompa_2 THEN
    V_S_Ore_P2 := V_S_Ore_P2 + 1;
END_IF;

// RESET ALLARMI DA SCADA O DA BORDO MACCHINA
IF ((V_P_Reset AND NOT _fp_V_P_Reset) OR (IN_Reset AND NOT _fp_IN_Reset)) THEN
    V_S_Guasto_P1 := FALSE;
    V_S_Guasto_P2 := FALSE;
    V_S_Marcia_Secco := FALSE;
END_IF;

// SPIE DI MARCIA
V_L_P1_Marcia := OUT_Pompa_1;

// SPIA MARCIA POMPA 2
V_L_P2_Marcia := OUT_Pompa_2;

// SPIA CICLO
V_L_Ciclo := Mem_Richiesta;

// SPIA ALLARME CUMULATIVO
V_L_Allarme := (V_S_Guasto_P1 OR V_S_Guasto_P2 OR V_S_Marcia_Secco OR NOT Consensi);

// MACCHINA PRONTA
V_L_Pronto := Consensi AND NOT V_S_Marcia_Secco;

//--------------------------------------------------------------------------
// Memorie dei fronti: aggiornate alla FINE, dopo tutti gli usi.
// E' cosi' che il contatto di fronte del ladder si rende in ST.
//--------------------------------------------------------------------------
_fp_Mem_Richiesta := Mem_Richiesta;
_fp_Tim_Minuto_Q := Tim_Minuto.Q;
_fp_V_P_Reset := V_P_Reset;
_fp_IN_Reset := IN_Reset;