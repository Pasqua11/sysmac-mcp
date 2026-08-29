# Librerie Sysmac `.slr` dei FB SYNTECH — fatte e verificate

Realizzate il 28/08/2026. **Tre librerie, quattro FB, tutte e tre agganciabili insieme allo stesso progetto.**

---

## 1. Le librerie prodotte

Cartella: `C:\OMRON\Data\Lib\` (percorso predefinito di Sysmac)

| File | Versione | FB pubblicati | Origine |
|---|---|---|---|
| `SYNTECH_FB_Cappa.slr` | 1.0.0 | `Ritardo` | Cappa Ceramiche V2 |
| `SYNTECH_FB_Etch.slr` | 1.0.0 | `Contatore_Full` | CAPPA_ETCH_RELASE2 |
| `SYNTECH_FB_Skid.slr` | 1.0.0 | `Controllo_EV`, `Cnt_Min_Sec` | SKID_BAWA_Test |

Tutte con Società = SYNTECH e sorgente visibile (così il FB si può ispezionare e modificare
dal progetto che lo usa).

**Verifica finale superata**: agganciate tutte e tre a `test_import_ladder`, i quattro FB compaiono
nella Casella degli strumenti come categorie separate e sono utilizzabili nel ladder.

## Cosa NON è entrato, e perché

- **`Contatore`** — ha già una libreria Sysmac dal 14/11/2019, agganciata a 81 progetti.
  Pubblicarne una seconda con lo stesso nome creerebbe due librerie omonime con ID diversi.
- **`Drive_Error_Warning`** — non è un FB SYNTECH: arriva dalla libreria Omron `Servizio_1S`,
  insieme a `Brake_Release`, `Drive_Restart`, `Drive_In_STO`.
- **`MTCP_Server_NJNX`** e i cinque **`INV*_3G3M1_*`** — librerie Omron (Modbus TCP, inverter 3G3M1).

---

## 2. Procedura (versione definitiva, con le due trappole)

1. Aprire il progetto d'origine → **File → Salva con nome**: dare il nome della copia **e** impostare
   subito **Tipo = *Progetto libreria*** nello stesso dialogo (Sysmac avvisa che le informazioni sui
   gruppi di variabili vengono eliminate: è irreversibile, per questo si lavora su una copia).
   *Senza il tipo "Progetto libreria", la voce **Crea libreria** resta disabilitata.*
2. Aprire la copia → **Progetto → Libreria → Impostazione libreria**:
   - `Nome`, `Versione`, `Autore`, `Società`, `Commento`;
   - togliere **"Disattiva visualizzazione sorgente"** per mantenere il sorgente ispezionabile;
   - in **Selezione elemento** deselezionare `Programma0` e spuntare solo i FB da pubblicare.
3. **Ripulire il progetto libreria** (vedi trappola sotto).
4. **Progetto → Libreria → Crea libreria** → salvare in `C:\OMRON\Data\Lib\`.
5. Nel progetto di destinazione: **Progetto → Libreria → Mostra riferimenti** → **+** → scegliere il `.slr`.

### Trappola 1 — la libreria si porta dietro TUTTI i tipi dati del progetto
Non solo quelli usati dai FB pubblicati. Due librerie ricavate da progetti diversi che definiscono lo
stesso tipo non possono convivere:

> *Errore riferimento libreria — I seguenti nomi sono duplicati. Non è possibile fare riferimento alla
> libreria. File di libreria: SYNTECH_FB_Etch.slr — Nome: **PAROLA***

`PAROLA` (la UNION bit/WORD) era in Cappa **e** in Etch. Rimedio applicato: nella copia usa-e-getta
di Etch sono stati **eliminati i tipi dati utente** (`PAROLA` e `Recipe`, nessuno dei due usato da
`Contatore_Full`) e la libreria è stata ricreata: 11.856 byte invece di 12.843, e nessun conflitto.

Per riferimento, i tipi dati definiti in ciascun progetto: Cappa 272, Etch 106, **Skid 1** — ed è il
motivo per cui Skid non ha mai dato problemi.

### Trappola 2 — "Crea libreria" pretende un progetto che compila
> *Errore creazione libreria — Si è verificato un errore di compilazione. Correggere il programma,
> quindi creare nuovamente la libreria.*

Eliminando i tipi dati si rompono i programmi che li usavano. Nella copia va quindi eliminato anche
il resto: `Programma0` (click destro → Elimina) e le variabili globali che usavano quei tipi
(`Ricetta_Edit`, `Ricetta_Memoria`, rimosse offline con `slwd` a progetto chiuso; backup in
`*.bak_prelib`). Dopo la pulizia: **0 errori / 0 avvisi**, e la libreria si crea.

**In sintesi: il progetto libreria va ridotto ai soli FB da pubblicare.**

---

## 3. Da fare quando vuoi

**Pulizia** (non elimino file di mia iniziativa):
- progetti copia: `SYNTECH_LIB_PROVA`, `SYNTECH_LIB_Etch`, `SYNTECH_LIB_Skid` — servivano solo a
  produrre i `.slr`, si possono eliminare dalla pagina iniziale di Sysmac. Da tenere se pensi di
  dover riemettere una libreria con una versione nuova: rifare la copia costa qualche minuto.
- `C:\OMRON\Data\Lib\SYNTECH_FB_PROVA.slr` — libreria di prova, superata da `SYNTECH_FB_Cappa.slr`.
- `test_import_ladder` ha adesso le tre librerie referenziate: se elimini i `.slr` togli prima i
  riferimenti da *Mostra riferimenti*.

**Aperto:**
- se una commessa nuova deve usare `Contatore`, va agganciata la libreria del 2019 (che però non
  esiste come file `.slr` sul PC: sta solo incorporata nei progetti che la usano).
- versione: tutte a 1.0.0. Quando modificherai un FB, ricordati di alzare la versione nel dialogo
  *Impostazione libreria* prima di ricreare il `.slr`.
