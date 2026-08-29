# Ricetta: un programma Sysmac nuovo in mezz'ora

Ricavata misurando tre lavori reali (27-28/08/2026). Da leggere prima di iniziare, insieme a
`prima-di-programmare-in-sysmac.md`.

## I numeri da cui parte tutto

| Lavoro | Rung | Metodo | Tempo |
|---|---|---|---|
| Movimentazione assi | 22 | 5 blocchi disegnati a mano nella GUI | **2 ore** |
| Batteria di collaudo | 78 | generata da `pins.json` | 25 min (4 giri di correzione) |
| Semaforo incrocio | 34 | generata da spec Python | **33 min**, collaudo compreso |

Un blocco funzione disegnato a mano costa ~10 minuti. Lo stesso blocco generato ne costa 10 di
secondi. **Tutto il resto della ricetta discende da qui.**

## L'ordine che funziona

1. **Scrivere la logica come specifica** (`genera_*.py`), non come ladder. Testo leggibile,
   correggibile con una riga, rigenerabile in 3 secondi.
2. **Validare l'XML** (`[xml]$file` in PowerShell) prima di ogni import: Sysmac rifiuta in silenzio
   l'XML rotto.
3. **Variabili in blocco**: `vars_offline` a progetto chiuso (77 variabili in 55 s), oppure
   `sysmac_vars` a progetto aperto se la tabella ha già righe.
4. **Import verificato**: deve rispondere "Incollati N rung (attesi N)". Se non lo dice, non è
   successo niente.
5. **Compilare subito** (`sysmac_compile_text`), prima di aggiungere altro.
6. **Simulare**: è l'unico modo per trovare gli errori di logica. Nel semaforo ha scovato due
   chiamate pedonali invertite che nessuna rilettura del ladder avrebbe mostrato.

## Trappole che costano minuti (misurate)

| Trappola | Sintomo | Rimedio |
|---|---|---|
| Finestra Sysmac nascosta | ogni azione fallisce in silenzio, l'import dice "Incollato" a vuoto | risolto nel server: `_uia` e `_focus_sysmac` la ripristinano |
| Coordinate note e finestra massimizzata | i click cadono 9 px più in alto | risolto: `_clickf` non somma l'origine negativa |
| Click subito dopo la massimizzazione | il click prende la riga sbagliata | risolto: 1,2 s di attesa |
| CapsLock acceso | `FB_Power_Trasl` diventa `fb_pOWER_tRASL` | risolto: testo dagli appunti, guardia sul CapsLock |
| `Ctrl+A` + `Canc` per svuotare una sezione | non seleziona i rung, chiude l'editor | creare una sezione nuova, importarci, eliminare la vecchia |
| Eliminare l'unica sezione di un programma | voce *Elimina* disabilitata | crearne prima un'altra |
| Riga vuota residua in tabella variabili | "Crea nuovo" non fa nulla | eliminarla prima |
| `watch` oltre ~30 s | timeout del client | finestre da 20-28 s |
| Misurare una durata da uno stato già attivo | risultato assurdo (0,4 s invece di 8) | aspettare il **fronte**: prima OFF, poi ON |
| Pulsanti con acceleratore (`_Crea`) | "pulsante non trovato" | risolto: `Invoke-UiButton` tollera underscore e parziali |
| Decoratore `@mcp.tool` sopra il punto di inserimento | un helper diventa tool, una funzione sparisce | guardare sempre la riga **sopra** prima di inserire codice |

## Dove sta il tempo, oggi

Su 33 minuti di semaforo: **12 fino alla compilazione pulita**, 21 di collaudo e correzione. Cioè il
tempo si è spostato dalla scrittura alla verifica — che è esattamente dove deve stare.

Il margine rimasto è quasi tutto nei **giri di apertura/chiusura progetto** (~1 minuto l'uno,
inevitabili quando servono le variabili offline) e nell'attesa del **simulatore** (40-60 s per
partire). Entrambi si ammortizzano lavorando a lotti: tutte le variabili in una volta, tutti i rung
in una volta, tutti gli scenari di collaudo in una sessione di simulazione sola.
