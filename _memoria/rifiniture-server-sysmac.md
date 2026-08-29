# Le due rifiniture: cosa nascondeva l'interfaccia di Sysmac

28/08/2026. Chiusi i due punti rimasti aperti. Entrambi erano lo stesso problema di fondo:
**Sysmac Studio non è tutta WPF**, e i pezzi che non lo sono UI Automation li descrive in modo
ingannevole. Trovarlo ha richiesto di guardare davvero l'albero degli elementi invece di fidarsi
dei nomi.

| | prima | dopo |
|---|---|---|
| `sysmac_apri_sezione` | non trovava i nodi, si usavano clic a coordinate: **19,1 s** | **10,5 s**, nessuna coordinata dei nodi |
| `sysmac_save(file=...)` | annullava il dialogo e non salvava | **15,9 s**, file creato |

## L'Explorer multivista non è un albero WPF

È un **TreeView Win32** (`WindowsForms10.SysTreeView32`) dentro un `WindowsFormsHost`. UIA non ne
pubblica i nodi: cercare `Programmazione` fra i discendenti restituisce **zero elementi**, ed è per
questo che la prima versione falliva sempre.

Tre tentativi prima di trovare la strada:

1. **Ricerca incrementale** (digitare il nome del nodo): non risponde.
2. **Tasto `*` del tastierino**, che nei TreeView Win32 espande ricorsivamente: qui apre **un solo
   livello**.
3. **Freccia destra ripetuta**: funziona. Il tasto fa due cose a seconda dello stato — se il nodo è
   chiuso lo apre, se è già aperto **scende al primo figlio**. Ripeterlo porta quindi sempre alla
   prima foglia del ramo, che sotto Programmazione è `POUs > Programmi > Programma0 > Sezione0`.
   Arrivati alla foglia i tasti in più non fanno danno.

La sequenza è `{HOME}{LEFT}{DOWN}` per posizionarsi su Programmazione, poi `{RIGHT 12}` e `{ENTER}`.
Se il nome della scheda aperta non è quello richiesto, il tool scende di una riga e riprova.

**Una scoperta collaterale che vale per tutto il server:** mandare i 12 tasti con dodici chiamate
separate costava **12 secondi**, perché ogni `_send_keys` avvia un processo PowerShell. In un'unica
sequenza costa un decimo. Da qui gran parte del guadagno.

L'unica coordinata rimasta è il centro del pannello, letto da UIA: segue il pannello se viene
spostato o ridimensionato.

## Il dialogo "Salva progetto" mente sui tipi

È il common dialog di Windows, e UIA lo espone così:

- il campo **"Nome file" non è un `Edit`**: è un **`Pane`** con `ClassName='Edit'` e
  `AutomationId='1001'`. Cercare `-Type Edit` prendeva invece la **colonna "Nome" della lista dei
  file** — un elemento che accetta la scrittura senza che si veda alcun effetto. Da qui il
  "sembra fatto ma non è successo niente".
- quel Pane **non espone ValuePattern**, quindi `SetValue` non è utilizzabile.
- anche i pulsanti **Salva e Annulla sono `Pane`** con `ClassName='Button'`, per cui
  `Invoke-UiButton`, che filtra per ControlType Button, non li trova.

La strada che funziona: identificare il campo per `AutomationId` **e** `ClassName` insieme,
leggerne il **rettangolo** da UIA, cliccarci dentro, `Ctrl+A`, digitare il percorso e `INVIO`.
Nessuna coordinata fissa, e la verifica finale è che il file esista davvero sul disco.

In più l'attesa del dialogo passa da 2,5 s fissi a un'attesa fino a 12 s: su un progetto da 700
rung il dialogo compariva dopo 4-5 secondi, e il tool nel frattempo rispondeva "salvato".

## Una misura da correggere nel report precedente

Gli **80 s** attribuiti alla ricompilazione completa del progetto da 716 rung **non sono
attendibili**: era rimasto aperto un dialogo di conferma ("tutti i programmi vengono ricompilati,
continuare?") che ho scoperto solo dopo. Il dato solido resta la **prima compilazione con F8, che
era conclusa entro 57 s** con 0 errori — coerente con i 27 s del progetto da 90 rung.

## Regola generale che ne esce

Quando un elemento della UI non si trova, **non cercarlo per tipo**: leggere l'albero degli
elementi e guardare `ClassName` e `AutomationId`. In Sysmac i controlli Win32 ospitati dentro WPF
si presentano tutti come `Pane`, qualunque cosa siano davvero.

## Da fare quando vuoi

Sono rimasti sul disco tre progetti di prova che non elimino di mia iniziativa:
`PROVA_SALVA_F1.smc2`, `PROVA_F3.smc2` e `CFE_Wetbench_9V.smc2` (la prima versione, quella con i
difetti) in `C:\OMRON\Data\Lib`.

## File

`patch_F.py` — attesa del dialogo e primo tentativo su `sysmac_apri_sezione`
`patch_F2.py` — `sysmac_apri_sezione` con la freccia destra ripetuta
`patch_F3.py` — `sysmac_save` con il campo trovato per AutomationId + ClassName
Backup: `server.py.bak_pre_patchF`, `.bak_pre_patchF2`, `.bak_pre_patchF3`
