# 90 rung cronometrati: linea di lavaggio a 11 vasche

28/08/2026. Programma vero, non un riempitivo: carro traslante, 11 vasche con permanenza,
riscaldamento con termostato, sorveglianza livello, salto delle vasche fuori ricetta, allarmi,
conteggio cicli. **90 rung, 112 variabili globali, 54 interne.**

Progetto: `Lavaggio_11_Vasche` (`C:\OMRON\Data\Lib\Lavaggio_11_Vasche.smc2`)
Generatore: `sysmac-mcp\genera_lavaggio.py` — parametrico, da 4 a 20 vasche.

## Esito

| | |
|---|---|
| compilazione Sysmac | **0 errori, 0 avvisi** |
| collaudo logico Python (`sim_spec`) | **PASS 54/54** in 1,4 s |
| collaudo sul simulatore Sysmac | **PASS 54/54** in 27,9 s |

## Tempi misurati

### Fuori da Sysmac — 1,6 s in tutto

| fase | tempo |
|---|---|
| generazione spec + variabili + scenari | 0,08 s |
| collaudo logico su 54 passi | 1,41 s |
| generazione XML dei 90 rung (596 KB) | 0,10 s |

### Dentro Sysmac — 101 s di operazioni utili

| fase | tempo |
|---|---|
| compilazione del dialogo Nuovo progetto | 7,0 s |
| creazione progetto | 6,5 s |
| salvataggio iniziale su file `.smc2` | 4,3 s |
| chiusura progetto | 7,4 s |
| **166 variabili scritte nel file** | **0,1 s** |
| riapertura progetto | 4,5 s |
| espansione albero + apertura sezione | 18,3 s |
| **import dei 90 rung** | **17,4 s** |
| compilazione | 27,4 s |
| salvataggio finale | 7,7 s |

Collaudo a parte: avvio simulatore 26,4 s + esecuzione scenario 27,9 s.

## Il risultato che conta: la UI non scala con i rung

| | Nastro | Pompe | **Lavaggio** |
|---|---|---|---|
| rung | 16 | 26 | **90** |
| variabili | 46 | 69 | **166** |
| import | 25 s | 18 s | **17,4 s** |
| compilazione | 33 s | 33 s | **27,4 s** |
| **totale UI** | 106 s | 120 s | **101 s** |

**90 rung costano quanto 26.** L'import è un unico Ctrl+V: che l'XML sia da 130 KB o da 600 KB
cambia poco. La compilazione dipende dal progetto, non dalla sua lunghezza. Il tempo se ne va tutto
in apri/chiudi/salva, che sono costi fissi.

Corollario pratico: **conviene fare programmi grandi in un colpo solo**, non a pezzi. Tre import da
30 rung costano il triplo di uno da 90.

## Scoperta grossa: le variabili nel file `.smc2`

Finora scrivevo le variabili passando dall'archivio progetti: **37 s**, indipendentemente da quante
fossero. Scrivendo invece direttamente il file `.smc2` (che `sysmac_vars_offline` accetta come
percorso) **166 variabili sono entrate in 0,1 s**. Trecentosettanta volte più veloce.

Il progetto va quindi creato con **"Gestisci nel file di progetto"** — che è anche ciò che Sysmac
propone da solo — e salvato come `.smc2` prima di scriverci dentro.

## Difetti trovati, e da chi

### 1. Ciclo che non riparte (trovato dal collaudo Python, passo 24)
`Mem_Fine` veniva azzerato in un rung più in basso di quello di arresto: al secondo START il ciclo
partiva e veniva fermato **nello stesso scan**. Un difetto che in cantiere si scopre al collaudo
con il cliente davanti. Il simulatore Python l'ha segnalato in 0,35 s; correzione e riverifica in
meno di un minuto.

### 2. Carro che non poteva scendere (trovato scrivendo lo scenario)
La prima stesura comandava l'abbassamento solo quando il cestello era *già* in vasca — condizione
impossibile. Risolto introducendo `Mem_Target` (carro fermo sopra la vasca da fare) e `Mem_Estrai`.
Averlo scoperto scrivendo il collaudo, prima di aprire Sysmac, è esattamente il punto del metodo.

### 3. Il simulatore Sysmac vede solo le variabili globali
Le verifiche su `End_Vk` (interne) tornano `ERROR=0105 Invalid parameter`, 11 falsi FAIL.
Il generatore ora produce **due scenari**: quello completo per Python e uno ripulito
(`*_scenario_sysmac.json`) con le sole globali.

### 4. Il collaudo su Sysmac va fatto a simulatore appena avviato
Secondo giro consecutivo: 36 FAIL su 54, nessuno reale. Le memorie erano rimaste alte dal giro
precedente e `/Seq_Attiva` bloccava lo START. **Regola: `sim_ferma()` + `sim_avvia()` prima di ogni
collaudo**, non solo il reset degli allarmi.

## Tempo perso in inciampi della UI (~3 minuti)

- **Pagina iniziale incastrata** dopo la chiusura di un progetto: le voci restano grigie e i click
  non fanno nulla. Rimedio: `sysmac_ui(azione="riavvia")`. ~40 s.
- **Ctrl+S su progetto nuovo apre "Salva progetto"** e serve scegliere un file. ~90 s persi
  prima di capirlo. Ora è documentato sopra.
- **`sysmac_ui(azione="menu")` apre il menu ma non seleziona la voce**, e gli acceleratori non
  arrivano ai popup: File|Chiudi non funziona. Funziona il click a coordinate (23,47) poi (48,78).
- **`vars_offline` di `sysmac_api` non accetta un percorso `.smc2`**, solo il nome d'archivio; il
  tool MCP `sysmac_vars_offline` sì.
- **L'albero si richiude alla riapertura del progetto** e il doppio clic sul nodo non lo espande:
  va cliccato il triangolino.

Sono cinque correzioni da fare al server, tutte piccole: varrebbero un'altra ventina di secondi a
programma e, soprattutto, niente più tentativi a vuoto.

## File

`sysmac-mcp\genera_lavaggio.py` — generatore parametrico (rung ≈ 6·vasche + 24)
`lavaggio11_spec.json`, `lavaggio11_scenario.json`, `lavaggio11_scenario_sysmac.json`
`lavaggio11_globali.txt` / `_interne.txt` / `_esterne.txt`
