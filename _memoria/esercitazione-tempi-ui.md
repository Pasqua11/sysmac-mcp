# Esercitazione sui tempi: due programmi nuovi, cronometro alla mano

28/08/2026. Due impianti realizzati da zero misurando **ogni singola operazione nella UI**, per
capire dove sia rimasto il tempo dopo le migliorie di oggi.

| | Nastro con conteggio | Gestione pompe |
|---|---|---|
| rung | 16 | 26 |
| variabili | 46 | 41 (+28 dal template) |
| logica + spec + collaudo Python | ~4 min | ~2 min |
| **operazioni nella UI** | **106 s** | **120 s** |
| collaudo su Sysmac | — | 17 s |
| compilazione | 0 errori | 0 errori |
| esito collaudo | PASS 15/15 (Python) | PASS 14/14 in **entrambi** i simulatori |

Per confronto: il semaforo di stamattina (34 rung) aveva richiesto ~9 minuti di sola UI, e la
movimentazione assi di ieri 2 ore.

## Dettaglio delle operazioni UI

| Operazione | Nastro | Pompe |
|---|---|---|
| creazione progetto | **11 s** (nuovo) | 32 s (duplicando il template) |
| variabili (una chiamata offline) | 37 s | 37 s |
| apertura sezione + import | 25 s* | 18 s |
| compilazione | 33 s | 33 s |

\* 16 s persi in un primo import fallito, poi corretto (vedi sotto).

---

## Cosa ho imparato, con i numeri

### 1. Il template di progetto NON conviene
Era la mia proposta di stamattina. Misurata: **duplicare il template costa 32 s, creare un progetto
nuovo ne costa 11**. Il "Salva con nome" richiede aprire il template, salvarlo e riaprirlo; la
creazione da zero è una sola pagina, e con `sysmac_dialogo` si compila in un colpo.

Il template conserva un solo vantaggio — le 28 variabili di impianto standard già pronte — ma
`vars_offline` impiega **37 s sia per 41 variabili sia per 46**: il tempo non dipende da quante
sono. Quindi la forma giusta del template non è un progetto da duplicare, ma un **file di variabili
standard da concatenare** all'elenco della commessa. Costo aggiuntivo: zero.

### 2. `sysmac_dialogo` ha tagliato la creazione progetto da 156 s a 11 s
Stamattina il semaforo: screenshot, click sul campo, digitazione, altro screenshot, click su Crea.
Adesso due chiamate per nome, senza una coordinata.

### 3. Il primo import dopo l'apertura di una sezione può mancare
L'editor si sta ancora disegnando e il click sul rung cade a vuoto. Costo: 16 s e un errore.
**Corretto nel server**: `sysmac_import_ladder_xml` ora ritenta una volta prima di dichiarare
fallito. Nell'esercizio 2 l'import è filato liscio in 18 s.

### 4. Il simulatore Python aveva un difetto grosso: i fronti
Usavo **una sola memoria di fronte per nome di variabile**. Due rung che leggono `^IN_Foto_Ingresso`
si rubavano il fronte a vicenda, e il conteggio scarti risultava rotto quando invece era corretto.
In un PLC ogni istruzione di fronte ha la propria memoria: ora la chiave è **per occorrenza**
(rung + posizione). Verificato che il semaforo continua a dare PASS e la spec rotta FAIL.

### 5. Mancavano i confronti
`>=`, `<=`, `=`, `>` … non erano implementati e venivano trattati come passanti: un rung
"lotto completo" sarebbe risultato **sempre vero**. Aggiunti insieme alle costanti numeriche
(`MOVE In=0`).

### 6. Il tipo TIME ora si scrive dal simulatore
`SET_T_Pressione = "T#2s"` fallisce con "could not convert string to float". In NJ/NX il TIME è un
intero a 64 bit in **nanosecondi**: aggiunta la conversione in `simlink._codifica`. Da qui una
miglioria importante: **`esegui_scenario` applica da solo i tempi dichiarati nello scenario**, così
lo stesso file JSON vale per Python e per Sysmac senza toccare i valori iniziali del progetto.

### 7. Su Sysmac il PLC conserva lo stato, in Python no
Lo scenario pompe dava PASS in Python e FAIL su Sysmac: `V_S_Marcia_Secco`, allarme ritenuto, era
rimasto attivo dal collaudo precedente. **Regola: ogni scenario comincia con un passo di
azzeramento** (impulso di reset + stato iniziale completo). Aggiunto, e ora PASS in entrambi.

### 8. Due difetti logici trovati prima di aprire Sysmac
- **Nastro**: nessuno (la logica era corretta al primo colpo; il FAIL era del simulatore).
- **Pompe**: timer di pressione **unico per le due pompe** — la riserva partiva ereditando il tempo
  già scaduto e andava in guasto immediato. Trovato in 0,4 s, corretto con un timer per pompa,
  rigenerato e ricollaudato in altri 0,4 s.

---

## Dove sta il tempo adesso

Su ~2 minuti di UI per un programma da 26 rung:

| | quota | riducibile? |
|---|---|---|
| compilazione | 33 s | no, è tempo macchina |
| variabili (chiudi + scrivi + riapri) | 37 s | in parte: ~20 s sono le due aperture progetto |
| import | 18 s | poco, comprende due salvataggi di verifica |
| creazione progetto | 11 s | no |

Il margine vero rimasto è **una decina di secondi** sulle aperture/chiusure. Il resto è tempo di
Sysmac. Cioè: **la UI non è più il collo di bottiglia** — lo è diventata la scrittura della
specifica, che però è lavoro di ingegneria, non di battitura.

## Bilancio

| | ieri (movimentazione) | stamattina (semaforo) | adesso (pompe) |
|---|---|---|---|
| rung | 22 | 34 | 26 |
| tempo totale | **120 min** | 33 min | **~4 min** |
| errori logici trovati | in cantiere | dopo 20 min di simulazione | **in 0,4 s** |

## File dell'esercitazione

`genera_nastro.py` + `nastro_scenario.json` — nastro con conteggio, scarto, lotto, inceppamento
`genera_pompe.py` + `pompe_scenario.json` — due pompe con alternanza, riserva, marcia a secco, ore
Progetti Sysmac: `Nastro_Conteggio` (16 rung), `Gestione_Pompe` (26 rung), `SYNTECH_TEMPLATE`

Entrambi i programmi sono impianti veri, riusabili come punto di partenza per commesse simili.
