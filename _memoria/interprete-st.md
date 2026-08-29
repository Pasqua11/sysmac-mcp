# L'interprete Structured Text: fatto e funzionante

29/08/2026. Primo passo della copertura ST: l'interprete che permette di collaudare il codice
prima di aprire Sysmac. È la parte di maggior valore, ed è finita.

## `sim_st.py` — 35 prove su 35

Esegue il codice ST come lo eseguirebbe il PLC, una scansione dopo l'altra. Copre quello che si usa
davvero negli impianti:

| | |
|---|---|
| espressioni | AND, OR, XOR, NOT, confronti, aritmetica, MOD, esadecimali, reali |
| istruzioni | IF/ELSIF/ELSE, CASE con etichette multiple, FOR con BY ed EXIT, WHILE, REPEAT |
| blocchi | TON, TOF, TP, CTU, CTD, con parametri nominali e accesso ai membri (`Tim.Q`, `Tim.ET`) |
| funzioni | ABS, MIN, MAX, SQRT, LIMIT, SEL, MUX, conversioni |
| altro | commenti `//` e `(* *)`, durate composte `T#1s500ms`, tempi da variabile |

Usa **lo stesso formato di scenario** del ladder: un solo file JSON collauda ST, ladder e il
simulatore vero di Sysmac.

## Ha già trovato un difetto vero

Ho scritto un essiccatore a tre fasi (107 righe, macchina a stati con CASE — in ladder sarebbero
una quarantina di rung). Al collaudo, **passo 10, il secondo ciclo**:

```
FAIL  {"V_S_Passo": [1, 9], "OUT_Resistenze": [true, false]}
```

Il temporizzatore di salita era chiamato **dentro il ramo `1:` del CASE**. Uscendo da quel passo
non veniva più aggiornato, restava con `Q` alto, e al ciclo successivo la macchina andava in
allarme dopo pochi millisecondi.

È un difetto classico dell'ST, e il PLC si comporta esattamente così. La regola:

> **In ST i blocchi funzione con stato vanno chiamati a OGNI scansione, mai dentro un ramo
> condizionale.** La condizione si passa come ingresso: `Tim(In := V_S_Passo = 1, PT := ...)`.

Corretto così: **PASS 13/13 in 0,09 s**.

E si conferma la regola dei due cicli: senza il passo "SECONDO CICLO" il collaudo sarebbe passato.

## Dentro Sysmac: creato e compilato

`sysmac_st_nuovo` crea il POU dal menu contestuale (Programmi → Aggiungi → **ST**) e ci incolla il
codice. Il POU si compila con **0 errori, 0 avvisi**.

Inserire il codice costa **3,5 s** contro i 13,7 s dell'import ladder: l'ST è testo, non XML.

## Dove mi sono fermato

Il collaudo dell'ST **sul simulatore di Sysmac** non l'ho ancora chiuso. L'ostacolo:

**Un POU aggiunto dopo la creazione del progetto non è associato a nessun task**, e senza
associazione il PLC non lo esegue mai. La compilazione dà un messaggio che non aiuta:
*"Errore di collegamento. Il nome, il tipo di dati o il namespace utilizzato non corrispondono
alla definizione"*.

Ho scritto `task_pou.py` per fare l'associazione modificando il file di progetto, e ho scoperto che
`IniFileTrackingId` **non è un GUID qualsiasi**: deve essere il `trackingId` dell'entità del POU nel
file `.oem`, senza trattini. Con un valore inventato Sysmac accetta il file e poi scarta
l'associazione in silenzio, senza errori.

Con il trackingId giusto l'associazione regge alla riapertura e la compilazione dà 0 errori — ma
l'avvio del simulatore si blocca su *"Il programma potrebbe non essere stato compilato
correttamente"*, e il comando **Strumenti → Aggiornare dati di trasferimento impostazioni e
configurazioni** non basta a sbloccarlo.

**Conclusione onesta: l'associazione al task va fatta dalla UI** (Configurazioni e impostazioni →
Impostazioni task), non scrivendo il file. Il resto del giro funziona.

## Una scoperta che semplifica tutto

Nel menu Strumenti c'è **"Importa programma ST..."**: Sysmac ha un import nativo per l'ST. È quasi
certamente la strada giusta — più pulita del creare il POU a mano e incollare nell'editor, e
probabilmente porta con sé anche la dichiarazione delle variabili.

## Prossimi passi

1. Provare **Strumenti → Importa programma ST**: se importa anche le variabili, sostituisce metà
   del lavoro fatto oggi.
2. Fare l'associazione al task dalla UI e chiudere il collaudo incrociato.
3. Il generatore ST dalla spec, che a quel punto è la parte facile.

## File

`sysmac-mcp\sim_st.py` — l'interprete (500 righe)
`sysmac-mcp\prova_st.py` — le 35 prove
`sysmac-mcp\st_essiccatore.st` + `st_essiccatore_scenario.json` — l'impianto di prova
`sysmac-mcp\task_pou.py` — associazione POU/task (funziona sul file, non basta per il simulatore)
`patch_H.py` — `sysmac_st_nuovo` e `sysmac_st_scrivi` nel server
