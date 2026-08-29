# Semaforo incrocio: programma, collaudo e tempi

Progetto **`Semaforo_Incrocio_V2`** (NJ501-1500 v1.70) — 34 rung, 77 variabili, **0 errori / 0 avvisi**,
collaudato in simulazione. Realizzato il 28/08/2026 in **33 minuti**.

---

## 1. Cosa fa il programma

Incrocio a due direzioni, **NS** (Nord-Sud) ed **EO** (Est-Ovest), con attraversamenti pedonali.

**Ciclo automatico a 6 fasi** — i due "tutto rosso" sono di sicurezza:

| Fase | Veicoli | Pedoni | Tempo |
|---|---|---|---|
| F1 | verde NS, rosso EO | verde pedonale EO | `SET_T_Verde_NS` 25 s |
| F2 | giallo NS, rosso EO | — | `SET_T_Giallo` 3 s |
| F3 | tutto rosso | — | `SET_T_TuttoRosso` 2 s |
| F4 | rosso NS, verde EO | verde pedonale NS | `SET_T_Verde_EO` 20 s |
| F5 | rosso NS, giallo EO | — | `SET_T_Giallo` 3 s |
| F6 | tutto rosso | — | `SET_T_TuttoRosso` 2 s |

Ciclo completo **55 s**, contato in `V_S_Cicli_Completati`.

**Chiamata pedonale.** Il pulsante prenota l'attraversamento, accende la spia e **anticipa la fine
del verde in corso** una volta trascorso il verde minimo (`SET_T_Verde_Min`, 8 s). Il pedone NS
attraversa durante il verde EO, quindi la sua chiamata accorcia la F1; e viceversa.

**Modalità notte** (`V_S_Notte`): giallo lampeggiante in tutte le direzioni, rossi spenti.

**Emergenza** (`IN_Emergenza` o guasto di una lampada rossa): tutto rosso, pedonali spenti.

Tutti i tempi sono variabili `TIME` ritentive, modificabili da SCADA senza toccare il programma.

---

## 2. Collaudo in simulazione: i tempi misurati

| Prova | Atteso | Misurato | Esito |
|---|---|---|---|
| Giallo | 3 s | **3,03 s** | ok |
| Tutto rosso di sicurezza | 2 s | **2,02 s** | ok |
| Verde NS senza chiamata | 25 s | **26,1 s** | ok (+1,1 s di polling) |
| Verde NS con chiamata pedonale | 8 s (minimo) | **8,3 s** | ok |
| Lampeggio notturno | ~1 Hz | 0,4 s on / 0,6 s off | ok |
| Emergenza | tutto rosso | rossi accesi, resto spento | ok |
| Ripresa dopo emergenza | ciclo da F1 | verde NS, contatore a 3 | ok |
| Pedonali | opposti ai veicoli | verde ped. EO durante verde NS | ok |

### L'errore che il collaudo ha trovato
Le due chiamate pedonali erano **invertite**: la chiamata NS accorciava la fase sbagliata. In
simulazione si è visto subito (il verde non si accorciava mai dal lato giusto). Correzione:
scambio delle due memorie nella spec, rigenerazione, reimport. **Costo della correzione: 6 minuti**,
compresa la ricompilazione e il ricollaudo — sarebbe stato un difetto trovato in cantiere.

---

## 3. Tempi di realizzazione

| Fase | Durata | Totale |
|---|---|---|
| Progetto della logica + spec + generazione XML | 3,1 min | 3,1 |
| Creazione del progetto Sysmac | 2,6 min | 5,7 |
| 77 variabili (29 globali + 19 interne + 29 esterne) | 0,9 min | 6,6 |
| Import 34 rung + compilazione + tempi di fase | 5,9 min | 12,5 |
| Collaudo in simulazione (4 scenari) + correzione errore | 20,6 min | **33,1** |

**Confronto con ieri:** la movimentazione assi — 22 rung, meno logica — è costata **2 ore**, di cui
50 minuti per 5 blocchi disegnati a mano. Qui: 34 rung, 6 fasi, 3 modalità, in 12 minuti fino alla
compilazione pulita, più 20 di collaudo vero.

Numeri che contano:

- **34 rung importati e verificati in 9,5 s**, due volte (prima e dopo la correzione)
- **77 variabili in 55 secondi**, in una sola chiamata offline
- **0 errori al primo tentativo di compilazione**, senza un solo rung disegnato a mano

---

## 4. Cosa ha fatto la differenza (e cosa rallenta ancora)

**Ha funzionato**

1. **Generare invece di disegnare.** La spec Python è leggibile e correggibile: lo scambio delle due
   chiamate pedonali è stato una riga, non due rung da ridisegnare.
2. **Verificare l'esito di ogni azione.** L'import dice "Incollati 34 rung (attesi 34)": nessun
   dubbio da sciogliere con screenshot.
3. **Variabili offline a progetto chiuso.** 77 variabili con commenti in un colpo.
4. **Simulare.** L'errore logico non sarebbe emerso da nessuna rilettura del ladder.

**Ha rallentato, e come si risolve**

| Rallentamento | Costo | Rimedio |
|---|---|---|
| Chiudi/riapri progetto per scrivere le variabili offline | ~1 min a giro | usare `sysmac_vars` (progetto aperto) quando la tabella ha già righe |
| `Ctrl+A` + `Canc` per svuotare una sezione non funziona | ~4 min persi | creare una **sezione nuova**, importarci il ladder e poi eliminare la vecchia (Sysmac non elimina l'unica sezione) |
| `watch` oltre ~30 s supera il timeout del client | 2 tentativi persi | finestre da 20-28 s, o polling con `leggi` |
| Misura di durata agganciata a uno stato già attivo | 1 misura sbagliata (0,4 s) | aspettare sempre il **fronte**: prima lo stato OFF, poi ON |
| Finestra Sysmac nascosta dopo ogni riapertura | ~10 s a giro | già risolto: `_uia` e `_focus_sysmac` la ripristinano da soli |

**Migliorie fatte oggi mentre lavoravo** (nel server MCP):

- `_uia()` garantisce la finestra visibile: prima ogni funzione UIA falliva con "Sysmac in avvio"
- `Invoke-UiButton` tollera l'acceleratore nel nome: il pulsante **Crea** si chiama `_Crea`
- `_clickf` attende 1,2 s dopo una massimizzazione effettiva

---

## 5. File

| File | Contenuto |
|---|---|
| `sysmac-mcp\genera_semaforo.py` | la specifica: logica, tempi, variabili. Rigenera tutto in 3 s |
| `sysmac-mcp\semaforo_spec.json` | spec per `ladder_gen` |
| `sysmac-mcp\out\sec_Semaforo.xml` | i 34 rung pronti da incollare |
| `sysmac-mcp\semaforo_globali.txt` / `_interne.txt` / `_esterne.txt` | elenchi variabili |

Per cambiare i tempi non serve toccare il ladder: sono variabili ritentive da SCADA. Per cambiare la
**logica** si modifica `genera_semaforo.py` e si rigenera: 3 secondi per l'XML, 10 per l'import.
