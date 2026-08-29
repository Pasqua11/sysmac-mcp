# Convertitore rung → spec: il software esistente diventa ricetta rigenerabile

Fatto il 26/08/2026. Chiude il cerchio: **progetto Sysmac esistente → spec JSON → ladder rigenerato → import in Sysmac**.

## Risultati misurati

| Passo | Risultato |
|---|---|
| Progetti analizzati (deduplicati per versione) | **73** su 111 |
| Rung convertiti in spec | **12.356 / 12.356 = 100%** |
| Rung rigenerati da spec con `ladder_gen` | **12.356 / 12.356 = 100%** |
| Import in Sysmac + disegno corretto | verificato su rung reali, compreso il set difficile |

Nessun rung è risultato non-serie-parallelo: la topologia ladder dei progetti SYNTECH è sempre riducibile.

## Come funziona (`rung2spec.py`)

Nel JSON di ogni rung Sysmac la topologia c'è tutta:
- ogni elemento ha **`X`** (colonna) e **`Y`** (riga) e collega il nodo `(X,Y)` al nodo `(X+1,Y)`;
- **`VLs`** sono i montanti verticali: `{X, Y}` unisce il nodo `(X,Y)` a `(X,Y+1)`;
- **`HL`** è un filo orizzontale (arco senza logica), `LRI`/`RRI` le barre.

L'algoritmo: griglia → **union-find** sui montanti (nodi elettricamente uniti) → grafo di archi → **riduzione serie-parallelo** → albero → spec `chain` / `{"or": …}` / `out`. I rami paralleli vengono ordinati per riga originale e i paralleli annidati appiattiti, così la spec somiglia al rung disegnato.

Esempio reale (Hydra, `MOVIMENTAZIONE PRENOTATA`):
```json
{"cmt": "MOVIMENTAZIONE PRENOTATA",
 "chain": [{"or": ["Car_V1","Car_V3","V1_V2", … ,"F2_Scar"]}, "(Movim_Prenotati)"]}
```
e `MANUALE ASSE X`, che ha tre rami di uscita:
```json
{"chain": ["MC_X.DrvStatus.ServoOn","/MC_X.DrvStatus.DrvAlarm","/Manu_Y.Busy"],
 "out": [["X_Jog_SX", {"fb":"MC_MoveJog","inst":"Manu_X","p":{…}}],
         ["V_P_Sx","(X_Jog_SX)"], ["V_P_Dx","(X_Jog_DX)"]]}
```

### Selezione dei progetti
Per ogni nome base si tiene la **versione `V` più alta**; a parità di versione, la cartella modificata più di recente. 111 progetti → 73.

### Variabili incluse
Ogni sezione della spec porta con sé le **variabili realmente usate**, con tipo, ritentivo e commento presi dalla tabella del progetto d'origine: una sezione convertita è importabile senza inventare i tipi.

## Il pezzo che ha tolto il collo di bottiglia: `pins_from_db.py`

Il generatore conosceva i blocchi solo dai template campionati a mano (copia rung da Sysmac). Con 17 tipi la rigenerazione si fermava al **73,7%**: mancavano `Contatore` (510 usi), i confronti, `Get1sClk`, `ScaleTrans`, `ArySearch`, `PIDAT`…

La firma dei pin però è già nel database: nel JSON dei rung ogni blocco elenca `In`/`Out` con `Arg` (nome), `Type` (tipo), `__type` = `PF` (pin di potenza) o `PRM` (dato), `IO` (InOut). Da lì si ricostruisce il `<PinViewModel …/>` del formato clipboard.

Risultato: **91 tipi** raccolti da 11.766 blocchi, di cui 12 FB scritti da Luca (`Contatore`, `Controllo_EV`, `Cnt_Min_Sec`, `Ritardo`, `Drive_Error_Warning`, `MTCP_Server_NJNX`, la famiglia `INV*_3G3M1`…), riconosciuti come tali e marcati `IsUserDefinedType="true"`. Un solo tipo ha firme diverse fra progetti (`MTCP_Server_NJNX`, due versioni di libreria): si usa la più frequente.
I template campionati restano prioritari, perché sono XML reali di Sysmac.

Con questo la rigenerazione è passata da 73,7% a **100%**.

## Il bug che ha fatto perdere più tempo (e come si manifestava)

Un blocco di 8 rung veniva **rifiutato da Sysmac senza alcun messaggio**: il paste rispondeva "incollati", e non compariva nulla.

Prima ipotesi (sbagliata): i pin ricavati dal database non vanno bene. Falsificata: `TOF` e `@Inc`, entrambi con pin dal database, entravano perfettamente.

Causa vera: **XML non well-formed**. Le funzioni di confronto `<`, `<=`, `<>` finivano non escapate dentro un attributo — `typeName="<"` — e il parser XML si fermava. Il controllo `[xml]$file` in PowerShell lo ha trovato in un secondo: *"'<', valore esadecimale 0x3C, è un carattere di attributo non valido, riga 356"*.
Corretto con l'escaping di `typeName`, `variableName`, `baseVariableName` (patch 6). **Lezione: prima di ogni import, validare l'XML — Sysmac non dice niente se è rotto.**

## Verifica in Sysmac (progetto `test_import_ladder`)

Entrati e disegnati correttamente, con pin presi dal database e mai campionati:
`TOF`, `@Inc`, `@Dec`, `@MOVE`, `>`, `Get1sClk`, `ScaleTrans`, `ArySearch`, `EC_CoESDOWrite`, `ResetECError`, `ResetMCError`, più rung reali presi da `ADDITIONAL_HOOD` e la sezione `Portelli` di Hydra.

**Quello che non ho portato a 0 errori**: la compilazione finale della sezione `Portelli` resta con errori di *variabile non registrata*. Non è un problema del ladder — ogni `sysmac_register_from_error` toglie esattamente un errore (26 → 25 → …). La causa è la procedura GUI: quando la tabella variabili contiene già dei nomi, Ctrl+V apre il dialogo **"Risolvi conflitti operazione Incolla"**, e va premuto *Copia tutto da destra a sinistra* → *Applica* → *Chiudi*. Se l'Applica non va a segno, le variabili non entrano e il ladder resta senza registrazioni. È il prossimo pezzo da automatizzare (`sysmac_paste_vars`).

## File

| File | Cosa fa |
|---|---|
| `sysmac-mcp\rung2spec.py` | converte i progetti in spec (`--tutti`, `--progetto <guid>`, `--report`) |
| `sysmac-mcp\specs\*.json` | 73 progetti convertiti, con variabili per sezione |
| `sysmac-mcp\pins_from_db.py` → `pins.json` | firme dei pin di 91 tipi, ricavate dai rung |
| `sysmac-mcp\estrai_sezione.py` | estrae una sezione + variabili e prepara la spec per l'import |
| `sysmac-mcp\verifica_roundtrip.py` | misura quanti rung tornano indietro e perché no |
| `ladder_gen.py.bak_pre_escape` (e precedenti) | backup progressivi prima di ogni patch |

## Cosa si può fare adesso che prima no

- **Replicare una sezione cambiando i nomi**: `Vasca1_Acido` → quarta vasca con i suffissi `_V1`→`_V4` è una sostituzione sulla spec, non 31 rung da ridisegnare.
- **Comporre una macchina nuova** pescando sezioni collaudate da 73 progetti.
- **Diffare due revisioni** a livello di logica invece che di byte.
- **Riportare in vita un progetto**: la spec è testo leggibile e versionabile.
