# Il generatore ST: la stessa specifica, due linguaggi

29/08/2026. `st_gen.py` traduce in Structured Text la **stessa spec JSON** che già produce il
ladder. Non è un formato nuovo: è la scelta di quale linguaggio far uscire dalla stessa fonte.

## La verifica: i due linguaggi devono comportarsi in modo identico

Questo è il punto. Avendo un interprete per il ladder (`sim_spec`) e uno per l'ST (`sim_st`), la
traduzione si verifica da sola: si esegue lo **stesso scenario di collaudo** sulle due versioni e
si confrontano gli esiti passo per passo. Non serve Sysmac, e non serve fidarsi.

| programma | rung | ST | esito |
|---|---|---|---|
| lavaggio 4 vasche | 44 | 220 righe | **identici** |
| lavaggio 11 vasche | 90 | 460 righe | **identici** |
| gestione pompe | 26 | 126 righe | **identici** |
| nastro con conteggio | 16 | 80 righe | **identici** |
| **wetbench CFE** | **715** | **3285 righe** | **identici** |
| semaforo | 34 | 151 righe | 15 passi su 16 |

Anche le misure di durata coincidono al centesimo di secondo: 6,01 contro 6,01; 2,01 contro 2,01;
3,02 contro 3,02; 3,01 contro 3,01.

## Cosa traduce

| ladder | ST |
|---|---|
| `"A"` / `"/A"` | `A` / `NOT A` |
| `"^A"` | `(A AND NOT _fp_A)` con memoria di fronte |
| `{"or": [x, y]}` | `(x OR y)` |
| `"(X)"` | `X := <condizione>;` |
| `"(S X)"` / `"(R X)"` | `IF <cond> THEN X := TRUE/FALSE; END_IF;` |
| `{"fb": "TON", ...}` | `Tim(In := <cond>, PT := ...);` e poi `Tim.Q` |
| `{"f": "@Inc"}` / `MOVE` | `X := X + 1;` / `X := <valore>;` |
| `{"f": ">="}` | `(a >= b)` |

Le memorie dei fronti (`_fp_<nome>`) sono dichiarate e aggiornate **in fondo al programma**, dopo
tutti gli usi: è l'unico modo di rendere in ST il contatto di fronte del ladder.

## Tre difetti trovati dal confronto (e tutti e tre erano miei)

Il confronto ha lavorato subito, e non sul generatore: sull'**interprete**.

1. **L'ordine dei passi dello scenario.** `sim_spec` e il simulatore di Sysmac eseguono
   `set → attendi → impulso`; io in `sim_st` facevo `set → impulso → attendi`, con impulsi da
   0,15 s invece di 0,3. Lo stesso scenario dava esiti diversi.
2. **Un'attesa di troppo.** Aggiungevo 0,05 s dopo ogni impulso: su un impianto a fasi
   temporizzate come il semaforo, il ritardo si accumula e sposta le fasi.
3. **I passi `durata` non erano implementati**, e quando li ho implementati sbagliavo la
   semantica: bisogna **agganciare il fronte** — aspettare prima lo stato opposto, poi l'inizio
   vero — altrimenti si misura una frazione della durata e, peggio, si consuma meno tempo
   simulato, sfasando tutto quello che viene dopo.

Nessuno dei tre riguardava la traduzione. È il motivo per cui il confronto vale: separa i difetti
del generatore da quelli degli strumenti di misura.

## L'unico caso aperto

Il **lampeggio del giallo notturno** nel semaforo: in ladder oscilla (semiperiodo misurato 0,5 s),
in ST no (misura 0,0, cioè non cambia mai stato).

Il lampeggio è fatto con due temporizzatori incrociati — il primo abilitato dalla negazione
dell'uscita del secondo. È l'unico costrutto della batteria in cui un blocco funzione dipende
dall'uscita di un altro blocco valutato più avanti nello stesso ciclo: lì l'ordine di valutazione
conta, e la mia traduzione non lo riproduce.

**È un caso isolato e circoscritto**, non un difetto generale: 5 programmi su 6 sono identici, e il
più grande è quello da 715 rung. Ma finché non è risolto, il lampeggio va scritto a mano in ST o
lasciato in ladder.

## Come si usa

```
python st_gen.py lavaggio11_spec.json           genera lavaggio11.st
python st_gen.py cfe_spec.json Allarmi          solo quella sezione
python confronta_ladder_st.py                   verifica tutta la batteria
python confronta_ladder_st.py <spec> <scenario> verifica un caso
```

Il generatore restituisce anche l'elenco delle memorie di fronte da dichiarare fra le variabili
interne, pronto per `sysmac_vars_offline`.

## File

`sysmac-mcp\st_gen.py` — il generatore
`sysmac-mcp\confronta_ladder_st.py` — il confronto fra i due linguaggi
`sysmac-mcp\sim_st.py` — l'interprete ST, ora allineato a sim_spec sugli scenari
