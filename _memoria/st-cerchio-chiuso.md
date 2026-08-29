# Structured Text: il cerchio è chiuso

29/08/2026. Lo stesso programma ST, collaudato in Python e sul simulatore di Sysmac, con lo stesso
file di scenario e lo stesso esito.

| | |
|---|---|
| collaudo con `sim_st.py` | **PASS 13/13** in 0,09 s |
| compilazione in Sysmac | **0 errori, 0 avvisi** |
| collaudo sul simulatore Sysmac | **PASS 13/13** in 12 s |

Il programma è un essiccatore a tre fasi: 107 righe, macchina a stati con CASE, riscaldamento con
doppio termostato, allarme di salita, sovratemperatura che toglie le resistenze in qualunque passo.
In ladder sarebbero una quarantina di rung.

## Cosa bloccava, e la regola che ne esce

Ieri il simulatore si rifiutava di partire: *"Il programma potrebbe non essere stato compilato
correttamente"*. Ho inseguito due piste sbagliate prima di trovare quella giusta.

**Prima pista (giusta ma non sufficiente): l'associazione al task.** Un POU aggiunto dopo la
creazione del progetto non è associato a nessun task, e senza associazione il PLC non lo esegue
mai. La compilazione lo dice in un modo che non aiuta: *"Errore di collegamento. Il nome, il tipo
di dati o il namespace utilizzato non corrispondono alla definizione"*.

Aprendo **Configurazioni e impostazioni → Impostazioni task → Impostazioni assegnazione
programma** si vede l'elenco: `PrimaryTask → Programma1`. Ed era **già lì**, scritto da
`task_pou.py`. Quindi l'associazione via file funziona davvero — a patto di usare il valore giusto.

**Il dettaglio che costa ore:** `IniFileTrackingId` non è un GUID qualsiasi, deve essere il
`trackingId` dell'entità del POU nel file `.oem`, senza trattini. Con un valore inventato Sysmac
accetta il file e poi **scarta l'associazione in silenzio**, senza un solo messaggio.

**La causa vera: lo stato accumulato.** Dopo aver modificato i file di progetto dall'esterno, e
dopo la sequenza compila / elimina POU / riassegna / ricompila, Sysmac Studio si porta dietro dati
di configurazione disallineati. Né la ricompilazione completa né *Strumenti → Aggiornare dati di
trasferimento impostazioni e configurazioni* bastano a rimetterlo in riga.

> **Regola: dopo aver modificato i file di un progetto dall'esterno, riavviare Sysmac Studio** —
> non basta chiudere e riaprire il progetto. Con il riavvio, lo stesso progetto che rifiutava di
> partire ha avviato il simulatore in 23 secondi.

## L'import nativo: provato, non praticabile

**Strumenti → Importa programma ST...** esiste e accetta `Formato programma ST (*.xml)`. Ho provato
con il formato che Sysmac usa internamente (`<StructuredTextModel><Text>…</Text></…>`): rifiutato,
*"Impossibile importare alcuni file"*.

Non esiste una voce di esportazione da cui ricavare il formato: `IEC 61131-10 XML` ha **solo**
Importa, e nel menu contestuale del POU non c'è un export. Senza la documentazione Omron del
formato, questa strada è chiusa.

**Non serve.** Creare il POU dal menu contestuale e incollare il codice funziona e costa **3,5
secondi** — quattro volte meno dell'import ladder.

## La procedura che funziona, in ordine

1. scrivere l'ST e collaudarlo con `sim_st.py` (frazioni di secondo, si itera quanto si vuole)
2. creare il progetto, salvarlo come `.smc2`, chiuderlo
3. scrivere le variabili con `sysmac_vars_offline` — **globali senza `programma=`, interne ed
   esterne con `programma="<nome del POU>"`**, altrimenti finiscono nel POU sbagliato
4. riaprire, creare il POU ST e incollare il codice (`sysmac_st_nuovo`)
5. associare il POU al task: `task_pou.py`, oppure dalla UI in Impostazioni task
6. **riavviare Sysmac Studio**, riaprire il progetto
7. ricompilare (completa, non F8), avviare il simulatore, collaudare con lo stesso scenario

## Cosa resta

Il **generatore ST dalla specifica** — che a questo punto è la parte facile: la stessa spec JSON
che produce i rung può produrre testo ST, e il collaudo automatico c'è già.

## File

`sysmac-mcp\sim_st.py` — l'interprete, 35 prove su 35
`sysmac-mcp\st_essiccatore.st` + `st_essiccatore_scenario.json` — l'impianto e il suo collaudo
`sysmac-mcp\task_pou.py` — associazione POU/task sul file di progetto
Progetto: `C:\OMRON\Data\Lib\ST_Essiccatore.smc2`
