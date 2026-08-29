# Un wetbench da 716 rung, scritto e collaudato in poco più di quattro minuti

28/08/2026. Quattro cose in fila: correggere gli inciampi della UI, trovare il programma più
lungo della libreria SYNTECH, scriverne uno della stessa scala, cronometrare tutto.

---

## 1. Le correzioni al server

| | cosa non andava | esito |
|---|---|---|
| **E1** | `Invoke-SysmacMenu` prendeva il `Text` dell'etichetta (`_Chiudi`) invece del `MenuItem`: l'Invoke non faceva nulla | corretta, filtra per MenuItem — **`File\|Chiudi` ora chiude in 5 s** |
| **E2** | `sysmac_menu` splittava il percorso solo su `/`, ma il docstring documentava `\|` | accetta entrambi |
| **E3** | `sysmac_save` non si accorgeva del dialogo "Salva progetto" e rispondeva "salvato" | riconosce il dialogo — ma **controlla troppo presto**: su progetti grandi il dialogo compare dopo 4-5 s. Da allungare l'attesa |
| **E4** | `vars_offline` rifiutava un percorso `.smc2` | accetta il file — **1117 variabili in 0,07 s** |
| **E5** | nuovo `sysmac_apri_sezione` per espandere l'albero da solo | **non funziona**: nell'Explorer di Sysmac i nodi non sono `TreeItem` e UIA non li vede. Resta il clic a coordinate (19 s) |

Tre su cinque risolte, una da rifinire, una da rifare con un altro approccio.

Corretti anche due difetti degli strumenti, entrambi emersi solo a questa scala:

- **`sim_spec` simulava solo la prima sezione.** Su un programma a 8 sezioni girava il 12% del
  codice senza che nulla lo segnalasse. Ora esegue tutte le sezioni nell'ordine dichiarato.
- **Le variabili TIME il simulatore le espone come `LINT`**, quindi `scrivi(SET_T_Mov="T#20s")`
  falliva. Ora `T#...` viene riconosciuto dal valore, non dal tipo.

---

## 2. Il programma più lungo della libreria

Censiti **119 progetti in 1,1 secondi**:

| rung | progetto | sezioni |
|---|---|---|
| 1467 | Cappa_MTD_R2707_V3 | 735 — *artefatto: le stesse sezioni ripetute nel file* |
| **711** | **CFE300_TEST_Solving / CFE300_V4** | **29** |
| 697 | CFE300_V3 | 29 |
| 396 | Cappa Ceramiche V2 | 25 |
| 342 | CAPPA_ETCH_RELASE2 | 21 |

Il più lungo vero è **CFE300_V4: 711 rung in 29 sezioni** — wetbench a 6 vasche con `Allarmi`
(104 rung), `Vasca1..6`, `Cicli` (58), `Ceck_Ricetta` (46), `Ricetta` (32), `Macro_Movimentazione`.

## 3. Il programma equivalente

`CFE_Wetbench_V2`: **716 rung in 8 sezioni, 464 variabili globali e 189 interne**. Impianto vero,
non riempitivo: 9 vasche con livelli, termostati, ricircolo, carico e scarico; dosaggio chimico A/B
con conducibilità e pH e attesa di omogeneizzazione; rabbocco, sfioro, filtri, agitazione, cascata;
robot di movimentazione cesti con pinza e sorveglianza dei tempi; ricetta con controllo di
congruenza e conteggio dei cicli per soluzione; 197 rung di allarmi con reset selettivo.

| | |
|---|---|
| compilazione Sysmac | **0 errori, 0 avvisi** |
| collaudo Python (38 passi, 2 cicli completi) | **PASS 38/38** |
| collaudo sul simulatore Sysmac | **PASS 38/38** |

## 4. I tempi

### Fuori da Sysmac — 9 secondi

| fase | tempo |
|---|---|
| generazione spec, variabili e scenari | 0,08 s |
| collaudo logico su 38 passi | 8,4 s |
| generazione XML (716 rung, 3,25 MB) | 0,33 s |

### Dentro Sysmac — 3 minuti e 20

| fase | tempo |
|---|---|
| dialogo Nuovo progetto | 7,0 s |
| creazione progetto | 6,7 s |
| salvataggio iniziale su `.smc2` | 12,9 s |
| chiusura | 4,9 s |
| **1117 variabili scritte nel file** | **0,07 s** |
| riapertura | 10,9 s |
| espansione albero + apertura sezione | 19,1 s |
| **import dei 716 rung (3,25 MB)** | **54 s** |
| **compilazione completa** | **~80 s** |
| salvataggio | 5 s |

Collaudo a parte: avvio simulatore 37 s + scenario 38 s.

**Dalla specifica al programma collaudato: 4 minuti e 40 secondi.**

### Come scala

| | Nastro | Pompe | Lavaggio | **CFE** |
|---|---|---|---|---|
| rung | 16 | 26 | 90 | **716** |
| variabili | 46 | 69 | 166 | **653** |
| import | 25 s | 18 s | 17 s | **54 s** |
| compilazione | 33 s | 33 s | 27 s | **80 s** |
| **totale UI** | 106 s | 120 s | 101 s | **200 s** |

**Otto volte i rung costano due volte il tempo.** Import e compilazione crescono, ma molto meno
che proporzionalmente; tutto il resto è costo fisso. Il metodo regge alla scala dei programmi veri
della libreria.

---

## 5. I quattro difetti logici, e chi li ha trovati

### Trovati dal simulatore Python
**Doppia bobina fra sezioni.** Il semiautomatico comandava `OUT_Robot_Avanti` in una sezione
diversa dall'automatico. Comanda l'ultima bobina eseguita nella scansione: con il selettore in
automatico il rung manuale scriveva `FALSE` e **azzerava tutti i comandi del robot**. È il difetto
più insidioso del ladder a più sezioni. Risolto con una memoria per i manuali e un solo punto di
comando per ciascuna uscita.

**Pompa dosatrice che non si fermava.** La richiesta di dosata si riarmava a ogni scansione perché
la sonda leggeva ancora basso. Risolto con l'attesa di omogeneizzazione fra due dosate — che è poi
come funziona davvero un impianto.

### Trovati solo su Sysmac
**Azzeramento dei passi che non azzerava niente.** Il rung aveva `^V_P_Start` **e** `/Mem_Ciclo`,
ma nella stessa scansione il rung di avvio aveva già messo `Mem_Ciclo` a 1: condizione sempre
falsa. Conseguenza: **dal secondo cesto in poi la macchina non ripartiva**.

**Memoria di estrazione lasciata alta dalle vasche saltate.** Le vasche fuori ricetta vengono
completate d'ufficio e armavano anch'esse `Mem_Rob_Estrai`, che restava alta a fine ciclo, teneva
su `Mem_Rob_Muove` e bloccava lo start successivo.

**La lezione che vale più di tutte:** in Python passava perché ogni collaudo partiva da uno stato
vergine e **faceva un solo ciclo**. Su Sysmac il PLC conserva lo stato. Da oggi **ogni scenario
deve eseguire almeno due cicli completi** — è la prova che i passi vengano davvero azzerati.
Aggiunto al collaudo: ora il difetto lo vede anche Python, in 8 secondi.

---

## File

`sysmac-mcp\genera_cfe.py` — generatore parametrico (rung ≈ 74·vasche + 50)
`cfe_spec.json`, `cfe_spec_unica.json`, `cfe_scenario.json`, `cfe_scenario_sysmac.json`
`cfe_globali.txt` / `cfe_interne.txt` / `cfe_esterne.txt`
`censimento.py` + `censimento_libreria.json` — la libreria classificata per numero di rung
`patch_E.py` — le cinque correzioni al server
Progetto: `C:\OMRON\Data\Lib\CFE_Wetbench_V2.smc2`
