# Il buco più grosso: metà del tuo codice è in Structured Text

29/08/2026. Restando dentro Sysmac Studio, ho contato che cosa usano davvero i 119 progetti
della libreria. Il risultato cambia le priorità.

| tipo di POU | quanti |
|---|---|
| Ladder | 2948 |
| **Structured Text** | **2709** |
| blocchi funzione in ladder | 464 |

**Quasi metà del codice dei tuoi progetti è in ST, e io sapevo generare solo ladder.** L'86% dei
progetti contiene almeno un POU in ST, il 78% ha blocchi funzione propri.

## La buona notizia: l'ST è più facile del ladder

Il ladder in un progetto Sysmac è XML con celle, coordinate e topologie — è il motivo per cui
`ladder_gen` è il pezzo più complicato di tutto il lavoro. L'ST invece è **testo puro** dentro un
tag:

```xml
<StructuredTextModel ...><Text>IF TCP_Socket.Handle > 0 THEN ...</Text></StructuredTextModel>
```

Niente celle, niente coordinate, nessuna topologia da rispettare.

## Prova fatta, non teoria

Ho creato il progetto `PROVA_ST`, aggiunto un POU in ST (tasto destro su Programmi → Aggiungi →
**ST**), scritto le variabili, incollato il codice e compilato.

```pascal
// Gestione pompa di travaso - scritto in Structured Text
Consensi := NOT IN_Emergenza AND IN_Protezioni;

IF V_P_Start AND Consensi AND NOT IN_Liv_Max THEN
    Mem_Ciclo := TRUE;
END_IF;

IF V_P_Stop OR NOT Consensi OR IN_Liv_Max THEN
    Mem_Ciclo := FALSE;
END_IF;

OUT_Pompa := Mem_Ciclo AND IN_Liv_Min AND Consensi;

IF IN_Liv_Max AND Mem_Ciclo THEN
    V_S_Cicli := V_S_Cicli + 1;
END_IF;

V_L_Allarme := NOT Consensi;
```

**Compilazione: 0 errori, 0 avvisi.**

| fase | ST | ladder (confronto) |
|---|---|---|
| creazione del POU | pochi secondi, dal menu contestuale | — |
| variabili | 0,06 s | 0,05 s |
| **inserimento del codice** | **3,5 s** | 13,7 s (import XML) |
| compilazione | 42 s | 17,5 s |

L'inserimento è **quattro volte più veloce**: si incolla testo invece di un XML da megabyte.

## Cosa serve per usarlo davvero

1. **Un generatore ST dalla specifica**, come `ladder_gen` ma molto più semplice: la stessa spec
   JSON che oggi produce rung può produrre testo ST.
2. **Il simulatore che capisce l'ST**, per non perdere il collaudo automatico — che è la cosa di
   maggior valore che abbiamo costruito. È il pezzo di lavoro vero: serve un interprete di IF /
   CASE / FOR / WHILE e delle espressioni.
3. **La creazione di POU e blocchi funzione da zero**, non solo dentro `Programma0/Sezione0`:
   il menu contestuale su Programmi, Funzioni e Blocchi funzione si pilota già.

## Perché conviene

Ci sono cose che in ladder sono impraticabili e in ST vengono naturali: cicli su array, gestione
di stringhe e comunicazioni (nel tuo CFE300 c'è un intero server Modbus TCP scritto in ST),
calcoli, macchine a stati con CASE. E il codice ST è più corto: le 8 righe qui sopra sarebbero
otto rung.

## Le altre funzionalità di Sysmac non ancora coperte

Meno urgenti ma dentro lo stesso ambito:

- **strutture dati e enumerazioni**: una struttura `Vasca` invece di 40 variabili con suffisso
  `_V1`, `_V2`… — nei tuoi wetbench farebbe una differenza enorme
- **task e assegnazione dei programmi ai task** (97% dei progetti li configura)
- **Data Trace**: registrare le variabili durante la simulazione, per un collaudo con grafici
- **confronto offline** fra due versioni di progetto
- **eventi e allarmi utente** (47% dei progetti)
