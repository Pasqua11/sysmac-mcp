# Bilancio: cosa è finito, cosa no

29/08/2026, mattino. La notte ha prodotto **153 esercizi su 153 arrivati in fondo, 6618 rung,
153 compilazioni con zero errori, zero interruzioni**. Il motore si è dimostrato affidabile.

Ma il dato più utile è un altro, ed è un risultato negativo.

## La strada della velocità in Sysmac è esaurita

| | |
|---|---|
| media UI, primo terzo della notte | 99 s |
| media UI, ultimo terzo | 111 s |

**Non sono migliorato ripetendo: sono peggiorato del 12%.** E guardando le singole fasi si capisce
perché — sono identiche al decimo di secondo, esercizio dopo esercizio:

| fase | tempo (sempre) |
|---|---|
| creazione progetto | 13,5 s |
| salvataggio su file | 15,8 s |
| variabili | 0,05 s |
| riapertura | 13,8 s |
| apertura sezione | 12,9 s |
| import ladder | 13,7 s |
| compilazione | 17,5 s |

Sono **tempi macchina di Sysmac**, non tempi di abilità. Non c'è più niente da spremere: l'unica
voce che dipendeva da me — le variabili — è già a 0,05 secondi. Il lieve peggioramento finale è
probabilmente accumulo (153 progetti nell'elenco dei recenti, cartella più piena).

Continuare a esercitarsi sulla UI sarebbe tempo sprecato. **Il collo di bottiglia si è spostato
sulla scrittura della specifica**, che è lavoro di ingegneria — il tuo mestiere, non battitura.

## Un controllo automatico sui tuoi progetti veri

Ho scritto un primo `linter.py` e l'ho passato su tutti i 119 progetti della libreria, cercando i
difetti che **la compilazione non segnala**.

Risultato onesto: **la tua libreria è sana.** Solo la famiglia CFE300 ha doppie bobine, due per
versione, ereditate di versione in versione:

```
V_L_DI_Parz_V4   comandata in Vasca4/R26 e Vasca4/R28
V_L_DI_Parz_V6   comandata in Vasca6/R26 e Vasca6/R28
```

Sono spie di "DI parziale", quindi impatto basso — ma è esattamente il meccanismo che nel wetbench
generato ieri **azzerava tutti i comandi del robot**: la stessa uscita scritta in due punti, e a
decidere è solo l'ordine di esecuzione. Un controllo che gira in due secondi lo trova sempre.

Il linter segnala anche altro, che va però triato a mano prima di crederci: 107 variabili messe a 1
con SET e mai resettate nel CFE300, 247 scritte e mai lette, 99 lette e mai scritte. Una parte
saranno legittime (reset da SCADA, ingressi mappati sull'I/O), ma è il tipo di lista che vale la
pena guardare una volta.

## Cosa considero finito

- generazione del ladder da specifica, con 76 tipi di blocco certificati
- collaudo logico in Python, con la regola dei **due cicli** che ha già evitato un difetto grave
- collaudo incrociato sul simulatore Sysmac con lo stesso file di scenario
- il giro completo in interfaccia, misurato e ripetibile su 153 casi
- tre librerie `.slr` funzionanti

## Cosa manca davvero, in ordine di valore

**1. Il ponte con lo schema elettrico e la mappa I/O.** Oggi tutti i programmi che generiamo usano
variabili che non sono legate a nessun morsetto. In una commessa vera servono la configurazione
del rack o di EtherCAT e l'assegnazione delle variabili agli ingressi e alle uscite fisiche — e
quella lista nasce dallo schema SPAC, che già esiste. È il pezzo che oggi fai a mano ed è il più
grosso rimasto.

**2. Il linter fatto sul serio**, e da far girare prima di ogni consegna: doppie bobine, allarmi
senza reset, variabili mai lette o mai scritte, uscite comandate da sezioni diverse, rung
irraggiungibili. Oggi è un abbozzo di 100 righe che già trova qualcosa.

**3. La documentazione generata dal progetto**: lista I/O, descrizione funzionale, manuale
operatore. Sono cose che scrivi dopo, a mano, e che si possono ricavare dal progetto stesso.

**4. Il collaudo come documento di consegna.** Gli scenari JSON che scriviamo per verificare sono
già, di fatto, un verbale di collaudo: manca solo stamparli in un PDF con esito e data.

**5. Le lacune note**, piccole: due tipi non certificati (`AryMax`/`AryMin` da campionare su un
progetto vero, `MC_Restart1S` che richiede la libreria Omron 1S), e la movimentazione assi con
otto quote ancora a zero e velocità in impulsi invece che in millimetri.

## In una riga

Il progetto **non è completo**, ma la parte su cui stavamo lavorando sì. Quello che manca non è
più "scrivere ladder più in fretta": è collegare il ladder al resto del lavoro — schema elettrico
prima, documentazione e collaudo dopo.
