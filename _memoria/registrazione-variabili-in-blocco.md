# Variabili non registrate: soluzione definitiva (26/08/2026)

Risolto l'ultimo collo di bottiglia dell'import ladder. Prova finale: sezione `Portelli` (7 rung, 23 variabili) convertita da progetto → spec → rigenerata → importata → **0 errori / 0 avvisi**.

## Il problema
Dopo un import, ogni variabile non presente nella tabella genera un errore *"Esiste una variabile non registrata"*. Registrarle una a una (`Ctrl+Alt+R` o `sysmac_register_from_error`) costa una chiamata per variabile: su una sezione vera sono decine.

L'incolla del TSV in blocco funziona **solo se la tabella variabili è vuota**. Se contiene già dei nomi, `Ctrl+V` apre il dialogo **"Risolvi conflitti operazione Incolla (Programma0)"** e senza gestirlo le variabili non entrano — silenziosamente.

## La procedura corretta

1. Aprire l'editor della sezione e la **tabella variabili** (click sulla barra `Variabili`), scheda *Interne*.
2. Scorrere **in fondo** alla tabella e cliccare il **selettore di riga** (la colonna grigia a sinistra del nome) dell'ultima variabile: serve una riga selezionata, non una cella in edit.
3. `Ctrl+V`.
4. Se compare il dialogo:
   - **"Copia tutto da destra a sinistra"** → le righe passano dalla lista di origine a quella di destinazione;
   - attendere che **"Applica"** si abiliti (all'inizio è grigio: un click troppo rapido non fa nulla) e premerlo — quando ha funzionato, "Applica" torna disabilitato;
   - **chiudere il dialogo**.
5. `sysmac_compile` per verificare.

### I click del mouse sui pulsanti NON funzionano: usare UI Automation
Ho perso tempo cercando coordinate stabili. Non esistono, per due motivi:
1. il dialogo si apre **a cascata**: prima a `(128,128)`, poi a `(224,224)`… stesse dimensioni (1440×740) ma posizione diversa ogni volta;
2. anche a parità di rettangolo, **il layout interno si sposta col contenuto** (colonne più larghe per i tipi lunghi): con 17 variabili "Chiudi" stava a `R-74, B-60`, con 59 a `R-42, B-28`.

La soluzione è **UI Automation con `InvokePattern`**, che preme il pulsante per nome senza toccare il mouse — e funziona anche da PowerShell non elevato:

```powershell
Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes
# finestra il cui Name inizia con "Risolvi conflitti"
# -> pulsante -> $b.GetCurrentPattern([InvokePattern]::Pattern).Invoke()
```

Dettagli che servono:
- **"Applica" e "Chiudi"** hanno un `Name` e si trovano per nome. `IsEnabled` dice quando "Applica" è pronto: va atteso in un ciclo, altrimenti l'Invoke non fa nulla.
- **"Copia tutto da destra a sinistra" NON ha `Name`** (icona + testo in un ContentPresenter): lo si riconosce come il pulsante largo **200–300 px** più a destra fra quelli senza nome (gli altri della barra misurano 329, 143 e 115 px).

Script pronto: `sysmac-mcp\risolvi_conflitti.ps1` — esce con `APPLICATO_E_CHIUSO` (0), `APPLICA_NON_ABILITATO` / `PULSANTE_COPIA_NON_TROVATO` (2), `NESSUN_DIALOGO` (1).

Nota: un **click** inviato da uno script Python normale non ha effetto (Sysmac gira elevato, UIPI scarta l'input sintetico) — l'**Invoke** di UIA invece passa.

## Il tool: `sysmac_paste_vars`
Aggiunto a `sysmac-mcp\server.py` (riga ~324, backup `server.py.bak_pre_pastevars`):

```
sysmac_paste_vars(path, row_x=353, row_y=304, wait=1.2)
```
Mette il TSV negli appunti, seleziona la riga, incolla, e se il dialogo compare esegue "Copia tutto" → "Applica" (fino a 3 tentativi, perché si abilita con ritardo) → chiusura con Alt+F4. Il TSV è quello che `ladder_gen.py` produce già insieme alla sezione (`out\vars.txt`).

**Serve riavviare l'app Claude** perché il nuovo tool venga caricato.

## Bug collaterale trovato e corretto: il fronte di discesa
Il rung `DOPO UNA CHIUSURA PORTELLI RESETTO GLI ALLARMI` conteneva un contatto a **fronte di discesa** su `Mem_Portelle_Open`. Il convertitore lo esporta come `vMem_Portelle_Open`, ma il generatore non riconosceva il prefisso `v` e creava una variabile inesistente con quel nome — da cui errori di "variabile non registrata" che nessuna registrazione avrebbe potuto risolvere.

Corretto in `ladder_gen.py` (patch v3, backup `.bak_pre_down3`), insieme alla **bobina negata** `(/Var)`:
- `vVar` → contatto con `diffDown="true"`
- `(/Var)` → bobina con `inverted="true"`

Verifica del parser:
```
_parse_item('vMem_Portelle_Open') -> ('C', 'Mem_Portelle_Open', False, False, True)
_parse_item('(/Spia)')            -> ('O', 'Spia', 'N')
```

### Lezione sul metodo (costata tempo)
La patch che introduceva il fronte di discesa era **fallita silenziosamente** settimane… anzi, poche ore prima: l'`assert` sull'ancora non trovata era finito in un output di PowerShell che avevo troncato con `Select-Object -First 2`. Da allora tutte le patch:
1. stampano l'esito e **non** vanno troncate;
2. verificano la sintassi con `py_compile` e in caso di errore **ripristinano il backup**;
3. usano ancore lette dal file corrente, non copiate da versioni precedenti (le patch successive cambiano le righe).

## Secondo bug: le variabili dentro l'ST inline
`rung2spec` raccoglieva i nomi da contatti, bobine, istanze FB e parametri, ma **non dal testo dei blocchi ST inline**. Su `Movimentazione_Robot` mancavano così `X_PRESA`, `Y_PRESA`, `X_DEPOSITO`, `Y_DEPOSITO` — usate solo nel calcolo quote — e restavano 10 errori.
Aggiunta `ist_names()`: estrae gli identificatori dal testo ST (togliendo commenti `(*…*)` e `//…` e le parole chiave IEC) e li incrocia con la tabella variabili, così i nomi inventati vengono scartati da soli. Da 59 a 63 variabili, e compare il tipo `REAL` con il flag ritentivo giusto.

## Variabili di sistema da NON esportare
`estrai_sezione.py` ora esclude dal TSV le variabili di tipo **`_sAXIS_REF` e `_sGROUP_REF`** (`MC_Group000`, `MC_X`, `MC_Y`…): esistono già, create dalla configurazione controllo assi, e vanno registrate come **variabili esterne** (una sola volta, con `sysmac_register_from_error`). Ricrearle come interne genererebbe duplicati scollegati dall'asse reale.

## Risultato misurato

**Prova 1 — `Portelli`** (7 rung, 23 variabili):

| Passo | Errori |
|---|---|
| Dopo l'import | 26 |
| Dopo il merge variabili in blocco | 3 |
| Dopo il fix del fronte di discesa, in sezione pulita | **0** |

**Prova 2 — `Movimentazione_Robot`** (8 rung, 63 variabili: la catena MOV1→MOV8 su gruppo assi con ST inline):

| Passo | Errori |
|---|---|
| Dopo l'import, senza variabili | 116 |
| Dopo il merge via UI Automation | 10 |
| Dopo l'aggiunta delle variabili dell'ST inline | **0** |

## Flusso completo, oggi
```
rung2spec.py --tutti                          progetti -> specs\*.json (con variabili)
estrai_sezione.py <spec> <sezione>            spec + TSV della sola sezione
ladder_gen.py out\spec_<sezione>.json         XML dei rung + out\vars.txt
[xml]$file                                    validare SEMPRE l'XML prima di incollare
sysmac_paste_vars(out\vars.txt)               variabili in blocco (UIA)
sysmac_paste_file(out\sec_<sezione>.xml)      rung
sysmac_register_from_error  x N               solo assi/gruppi -> "Variabile esterna"
sysmac_compile                                atteso: 0 errori
```

## Nota sulla copertura
Rilanciando `rung2spec --tutti` dopo queste prove compaiono **6 rung non convertiti** ("ramo parallelo vuoto", "rung vuoto"): sono tutti nel progetto `test_import_ladder`, cioè scarti dei miei esperimenti. **Sui 73 progetti reali la conversione resta 100%.**
