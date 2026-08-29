# Intervento A — fatto e verificato (28/08/2026)

Obiettivo: la finestra di Sysmac non deve più far fallire le azioni in silenzio, e l'import deve
dire la verità sul proprio esito.

**Esito del test finale**, con la finestra volutamente nascosta prima di partire:

```
prima -> visibile: False
ESITO: Incollati 2 rung (attesi 2; totale progetto 138 -> 140).
dopo  -> visibile: True  stato: 3 (massimizzata)
```

Prima di oggi, nella stessa condizione, la risposta era `"Incollato."` e i rung non entravano.

---

## I quattro difetti trovati (tre non erano nel piano)

### A1 — finestra nascosta ignorata  *(previsto)*
`_focus_sysmac()` gestiva solo `IsIconic` (minimizzata). Una finestra **nascosta** (`SW_HIDE`)
restava tale: il focus "riusciva" e i tasti finivano nell'applicazione sbagliata.
In più `_sysmac_hwnd()` prendeva l'handle da `MainWindowHandle`, che per una finestra nascosta
vale 0, e sollevava "Sysmac non in esecuzione".

**Fatto:** `_hwnd_per_titolo()` (enumera anche le finestre nascoste) come fallback, e
`_assicura_visibile()` chiamata all'inizio di `_focus_sysmac()`.

### A2 — nove lock orfani  *(scoperto strada facendo)*
`_conta_rung_progetto()` individua il progetto aperto dal file `<pid>.applicationlock`.
In `C:\OMRON\Data\Solution` ce n'erano **10, di cui 9 orfani** di sessioni chiuse male — il più
vecchio del 3 febbraio 2025. La prima cartella con un lock era quella sbagliata.

**Fatto:** si accetta solo il lock il cui nome corrisponde al PID del Sysmac in esecuzione
(`GetWindowThreadProcessId`, senza PowerShell).

### A3 — `_massimizza()` si fidava delle dimensioni  *(scoperto strada facendo)*
Il test era `larghezza >= schermo-20 and altezza >= schermo-80`. Dopo un ciclo
nascondi/ripristina la finestra risultava in stato **normale** ma di 1938×1038 px: test superato,
nessuna massimizzazione, e tutte le coordinate note sfalsate di 90 px in verticale.

**Fatto:** lo stato si legge da `GetWindowPlacement().showCmd` (3 = massimizzata).

### A4 — l'offset negativo della finestra massimizzata  *(la causa vera dei click a vuoto)*
Le coordinate note del progetto (317,187 = numero del rung 0, e tutte le altre) sono state misurate
**sullo schermo** con Sysmac massimizzato. `_clickf()` le trattava come relative alla finestra e ci
sommava l'origine, che a finestra massimizzata è **(-9, -9)**: ogni click cadeva 9 px più in alto.
Su un numero di rung tanto basta a finire nella banda gialla del commento — il rung *sembra*
selezionato, ma il Ctrl+V non incolla niente.

Misurato:

| Chiamata | Rung nel progetto |
|---|---|
| `_clickf(317, 187)` + Ctrl+V | 137 → 137 (niente) |
| `_click(318, 188)` + Ctrl+V | 137 → **138** |

**Fatto:** l'origine si somma solo se positiva (`max(l,0)`, `max(t,0)`). A finestra ridotta l'offset
continua a servire e viene applicato come prima.

> Questo difetto era presente da sempre e spiega i click "che a volte non prendono": ogni coordinata
> nota era fuori di 9 px, e passava inosservata finché il bersaglio era abbastanza grande.

### A5 — import che non verifica  *(previsto)*
`sysmac_import_ladder_xml()` rispondeva sempre `"Incollato."`.

**Fatto:** nuovo parametro `verifica=True`: salva, conta i rung del progetto prima e dopo leggendoli
dal disco, e **solleva un errore** se non sono aumentati, indicando le cause tipiche. In caso di
riuscita riporta quanti rung sono entrati rispetto a quanti attesi.

---

## File toccati

| File | Backup |
|---|---|
| `sysmac-mcp\server.py` | `.bak_pre_visibile`, `.bak_pre_lockpid`, `.bak_pre_massimizza`, `.bak_pre_offsetclick` |

Le patch sono script rieseguibili in `sysmac-mcp\`: `patch_A.py`, `patch_A2.py`, `patch_A3.py`,
`patch_A4.py` (ognuno con `--dry` per la sola simulazione).

**Da fare:** riavviare l'app Claude perché il server MCP carichi il nuovo codice. Le verifiche di
oggi giravano in un processo separato che rilegge `server.py` a ogni chiamata, quindi il codice è
già collaudato; i tool `mcp__sysmac-ladder__*` useranno il vecchio codice fino al riavvio.

Il progetto `test_import_ladder` è stato riportato ai suoi 137 rung (i rung di prova annullati).
