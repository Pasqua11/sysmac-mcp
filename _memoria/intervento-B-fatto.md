# Intervento B — fatto e verificato (28/08/2026)

Obiettivo: il testo scritto nella GUI deve arrivare **esatto**, sempre.

## Il test

CapsLock acceso di proposito prima di partire, poi la sequenza tipica dell'editor ladder:

```
CapsLock ON: True
Inviato: r                              <- scorciatoia "nuovo rung": tasti
Inviato: c                              <- scorciatoia "contatto": tasti
Scritto dagli appunti: Test_CapsLock_OK <- testo: appunti
```

A video il contatto si chiama **`Test_CapsLock_OK`**, con le maiuscole al posto giusto.
Il 27/08, nelle stesse condizioni, `FB_Power_Trasl` era diventato `fb_pOWER_tRASL` e il blocco
funzione andò rifatto.

## Cosa è cambiato

| Aggiunta | Cosa fa |
|---|---|
| `_capslock_attivo()` | legge `GetKeyState(VK_CAPITAL)` — istantaneo, senza PowerShell, concorde con `IsKeyLocked` |
| `_capslock_off()` | spegne il CapsLock con `keybd_event`; restituisce True se ha dovuto agire |
| `_send_keys()` | spegne il CapsLock prima di inviare, ma solo se la sequenza contiene lettere |
| `sysmac_send_keys()` | **testo semplice → appunti**, sequenze di comando → SendKeys |
| `sysmac_ui(azione="scrivi")` | scrive sempre dagli appunti, anche un solo carattere |
| `sysmac_ui(azione="capslock")` | spegne il CapsLock su richiesta |

### La regola di instradamento, e perché è così
Nell'editor ladder le scorciatoie sono **lettere singole**: `c` contatto, `d` contatto N.C.,
`o` bobina, `f` blocco funzione, `r` nuovo rung, `t` linea, `i` funzione.
Incollarle dagli appunti non produrrebbe nulla. Quindi:

- lunghezza 1 → **tasti** (scorciatoie)
- contiene `{ } ^ % + ~ ( ) [ ]` → **tasti** (sequenze come `^s`, `{ENTER}`, `+{F5}`)
- tutto il resto → **appunti**

Questo copre i due guasti osservati: maiuscole invertite dal CapsLock e primi caratteri persi
(`Ritardo` → `tardo`).

## File

`sysmac-mcp\server.py`, backup `server.py.bak_pre_capslock`.
Patch rieseguibile: `sysmac-mcp\patch_B.py` (con `--dry` per simulare).

Il progetto `test_import_ladder` è tornato ai suoi 137 rung, CapsLock spento.

---

## Stato dopo A e B

| | prima | adesso |
|---|---|---|
| finestra nascosta | azioni fallite in silenzio | ripristinata e massimizzata da sola |
| click a coordinate note | fuori di 9 px (offset finestra massimizzata) | centrati |
| progetto individuato | primo lock trovato, spesso orfano | lock del PID vivo |
| import | "Incollato" sempre | conta i rung e fallisce se non ha incollato |
| testo con CapsLock | maiuscole invertite | esatto, dagli appunti |

**Serve un riavvio dell'app Claude** perché i tool `mcp__sysmac-ladder__*` usino il nuovo codice:
le verifiche giravano in un processo separato che rilegge `server.py` a ogni chiamata.

Restano gli interventi **C** (helper UIA per i dialoghi, ~2h30) e **D** (variabili senza
chiudi/riapri, ~1h), che dipende da C.
