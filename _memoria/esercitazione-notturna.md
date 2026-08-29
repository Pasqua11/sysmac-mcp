# Il motore di esercitazione notturna

28/08/2026, 23:52. Avviato un ciclo che si esercita da solo su Sysmac Studio fino alle 6:20 del
mattino. Non sono io a restare sveglio — la mia esecuzione finisce con la sessione — ma un
programma che ho scritto e collaudato, che gira come processo indipendente sul PC.

## Come funziona

`moduli.py` è un **catalogo di pezzi di automazione veri**: motore con termico, pompa con
pressostato, valvola con finecorsa, riscaldamento con termostato di sicurezza, vasca con livelli,
conteggio pezzi con lotto, sequenza a passi, lampeggio. Ogni modulo dichiara le proprie variabili,
i propri rung **e i propri passi di collaudo**.

`notte.py` ne pesca da tre a otto a caso, li monta in un impianto con ossatura comune (consensi,
allarme cumulativo, macchina pronta) e fa il giro completo:

1. genera spec e scenario di collaudo
2. collauda la logica con il simulatore Python (frazioni di secondo)
3. crea il progetto in Sysmac, lo salva su file, scrive le variabili, riapre, apre la sezione,
   importa il ladder, compila
4. ogni tre esercizi collauda anche sul simulatore vero di Sysmac
5. cronometra ogni fase e scrive tutto nel diario

Ogni impianto è diverso: non è la stessa cosa ripetuta, è esercizio vero.

## Primo esercizio completato

**ES001** — 38 rung, 51 variabili globali, 9 interne, otto moduli (conteggio, due pompe, livello,
valvola, riscaldamento, motore, conteggio).

| fase | tempo |
|---|---|
| collaudo logico (41 passi) | 0,36 s — PASS |
| creazione progetto | 13,5 s |
| salvataggio su file | 15,6 s |
| **60 variabili** | **0,05 s** |
| riapertura | 11,2 s |
| apertura sezione | 12,9 s |
| import ladder | 9,4 s |
| compilazione | 17,5 s |
| **compilazione Sysmac** | **0 errori, 0 avvisi** |

Circa **80 secondi di interfaccia** per un impianto completo e collaudato.

## Difetti trovati mentre costruivo il motore

Il collaudo automatico ha fatto il suo lavoro subito, sul catalogo stesso:

- **Un allarme che non toglieva il comando.** Nel modulo vasca, l'allarme di carico troppo lungo
  accendeva la spia ma lasciava la valvola aperta — cioè proprio nel caso in cui va chiusa.
  Corretto togliendo il comando e azzerando la richiesta.
- **Deriva nei tempi di collaudo.** Verificavo i passi di una sequenza attendendo 1,2 s su timer da
  1 s: dopo cinque passi la deriva vale un passo intero e si controlla quello sbagliato. Ora si
  verificano il primo cambio di passo e il completamento totale.

Dopo le correzioni: **8 moduli su 8 e 30 combinazioni casuali su 30 passano**.

## Cosa ho imparato sull'automazione di Sysmac

- **Un solo esercitatore per volta.** Due processi che pilotano la stessa finestra si rubano i clic
  e nessuno se ne accorge: il diario mostrava esercizi con numeri saltati. Aggiunto un lock con il
  PID.
- **"Salvare il progetto prima di chiudere?"** è il dialogo che blocca qualunque automazione, e
  compare come finestra intitolata **col nome del progetto**, non "Sysmac Studio": cercarlo per
  titolo fisso non lo trova. Ora si risponde No, e soprattutto si salva *prima* di chiudere, così
  non lo si incontra proprio.
- **I dialoghi si richiamano a vicenda.** Annullare il dialogo file fa comparire "selezionare un
  file", che riporta a "salvare?", che riporta al dialogo file. Bisogna premerli nell'ordine giusto
  (No, OK, Annulla) e mai "Salva" con il campo vuoto.
- **I tasti mandati troppo in fretta si perdono.** `{RIGHT 12}` in un colpo solo faceva finire la
  selezione sul nodo sbagliato: il TreeView, mentre espande, non sta dietro. A gruppi di tre con
  una pausa funziona.

## Protezioni

- se la creazione fallisce perché la pagina iniziale si è incastrata, **riavvia Sysmac** e riprova
- se un esercizio si interrompe, chiude dialoghi e progetto e passa al successivo
- se **quattro esercizi di fila** falliscono sulla GUI, passa alla **sola parte logica** per il
  resto della notte, così continua comunque a produrre impianti collaudati invece di sbattere
  contro un muro per ore

## Al mattino

- `C:\Users\tecni\Claude\esercizi_notte\diario_notte.md` — il diario, con un riepilogo finale:
  esercizi tentati e completati, rung prodotti, tempo medio di UI nel primo e nell'ultimo terzo
  della notte (è lì che si vede se sono migliorato), fasi che si sono interrotte, difetti logici
  trovati
- `misure.json` — tutti i tempi, esercizio per esercizio
- i progetti `ES***.smc2` in `C:\OMRON\Data\Lib` e le spec in `esercizi_notte`

**Per fermarlo**: creare un file vuoto `FERMATI.txt` in `C:\Users\tecni\Claude\esercizi_notte`,
oppure chiudere il processo python. Finché gira, **il PC non va usato**: il ciclo muove mouse e
tastiera e i tasti finirebbero nelle finestre sbagliate.
