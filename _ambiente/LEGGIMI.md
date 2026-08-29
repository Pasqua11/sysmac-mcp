# Ambiente Sysmac Studio da replicare sul notebook

Questi file non sono codice dell'MCP: sono la configurazione dell'**applicazione Sysmac Studio**
e le librerie di progetto. Vanno reinstallati a mano una volta sola sul notebook.

## 1. Scorciatoie da tastiera (obbligatorio)

`SYSMAC_SHORTCUTS_BACKUP.JSON` contiene le scorciatoie personalizzate che il server MCP **preme**.
Senza, i comandi vengono inviati a vuoto e le operazioni falliscono in silenzio.

| Scorciatoia | Comando |
|---|---|
| `Ctrl+Alt+X` | import XML (NexPlcOpenXml.V3Import) |
| `Ctrl+Shift+F8` | rebuild controller (NexReBuild) |
| `Ctrl+Alt+5` | OneScan Simulator |
| `Ctrl+Alt+W` | Reset (editor ladder) |
| `Ctrl+Alt+Q` | Set (editor ladder) |
| `Ctrl+Alt+L` | InsertJumpLabel (editor ladder) |

Import in Sysmac Studio: *Tools → Option → Shortcut Keys → Import*, selezionando il JSON.
Poi verificare che compaiano tutte e sei; il dettaglio e i casi particolari stanno in
`sysmac_scorciatoie.md`.

## 2. Librerie FB SYNTECH

`librerie_slr\*.slr` (Cappa, Etch, Skid, PROVA) vanno copiate in `C:\OMRON\Data\Lib\` sul notebook.
I progetti che le referenziano non compilano se mancano.
Aggancio al progetto: *Project → Library → Show References → Add*.

## 3. Stato del lavoro

`STATO_LAVORO_SYSMAC.md` è il punto di situazione sullo sviluppo del server MCP: cosa è chiuso,
cosa è in sospeso. Utile da leggere prima di riprendere lo sviluppo sul notebook.

## Nota sulla calibrazione

Le funzioni che pilotano la UI leggono gli elementi via UI Automation (per nome, non per pixel),
quindi cambiare risoluzione di norma non le rompe. Restano da verificare i **tempi di attesa**:
la ricetta misurata sul PC fisso è in `_memoria\ricetta-tempi-sysmac.md`, e la procedura di
riverifica in `_memoria\collaudo-post-riavvio.md`.
