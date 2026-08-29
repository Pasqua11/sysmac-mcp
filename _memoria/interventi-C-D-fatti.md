# Interventi C e D — fatti e verificati (28/08/2026)

Con A e B, il piano di ottimizzazione della UI è **completo**.

---

## C — I dialoghi si pilotano per nome

Nuovo tool `sysmac_dialogo(titolo, campi, caselle, tendine, riga, pulsante)`: una sola chiamata al
posto di una decina di click a coordinate.

```python
sysmac_dialogo(titolo="Impostazione libreria",
               campi="Nome=SYNTECH_FB_Cappa; Autore=Luca; Commento=...",
               caselle="Disattiva visualizzazione sorgente=off",
               tendine="Tipo di libreria=Libreria regolare",
               pulsante="OK")
```

**Verificato sul dialogo vero**, quello che era costato ~50 click per le tre librerie:

| Prova | Esito |
|---|---|
| tre campi (Nome, Autore, Commento) in una chiamata | scritti esatti, controllati a video |
| casella "Includere le librerie di riferimento" on/off | commutata (Sysmac ha pure aperto il suo avviso) |
| tendina "Tipo di libreria" | voce selezionata |
| pulsanti OK / Annulla per nome | premuti |

### Le due sorprese
1. **I campi Edit non hanno un nome**: nei dialoghi WPF di Sysmac l'etichetta è un elemento `Text`
   separato. `Find-UiEditByLabel` risolve per geometria — stessa altezza dell'etichetta, subito a
   destra — ed è ciò che fa funzionare tutto il resto.
2. **Le voci delle tendine si chiamano `[Chiave, Etichetta]`**: la voce "Libreria regolare" è
   esposta come `[Standard, Libreria regolare]`. La ricerca esatta falliva; ora c'è il ripiego sulla
   corrispondenza parziale.

**Limite noto:** la griglia del dialogo *Riferimento libreria* non espone le righe via UIA (griglia
WPF virtualizzata), quindi lì `riga=` non funziona. Nella tabella variabili invece le righe ci sono.

Funzioni aggiunte a `sysmac_ui.ps1`: `Find-UiEditByLabel`, `Set-UiValue`, `Set-UiToggle`,
`Select-UiComboItem`, `Select-UiGridRow`.

---

## D — Variabili a progetto aperto

Nuovo tool `sysmac_vars(variabili, tabella, programma)`. Prima serviva:
chiudi progetto → `vars_offline` → riapri, 2-3 minuti a giro (quattro giri nella sola sessione della
batteria) e ogni riapertura poteva lasciare la finestra nascosta.

**Verificato:** `Create 4 variabili in 'globali' (3 -> 7).` — a progetto aperto, una chiamata.

Il menu contestuale si apre con **Shift+F10** (niente click destro a coordinate) e le voci si
scelgono per nome: `Crea nuovo`, `Incolla`, `Elimina`.

### Come ci sono arrivato (due tentativi falliti)
1. `Crea nuovo` + `ESC` lascia il fuoco sulla **cella**: l'Incolla ci finisce dentro e si vede il
   TSV intero scritto nella colonna Nome (`e False Non pubblica...`).
2. **Shift+Spazio**, che nelle griglie standard seleziona la riga, qui non fa nulla.
3. Quello che funziona è cliccare il **selettore di riga** — ma senza coordinate fisse: le righe
   sono esposte come `DataItem` con il loro rettangolo, quindi il punto si calcola
   (`x + 8`, `y + altezza/2`). È `_selettore_ultima_riga()`.

La riga vuota creata come cuscinetto resta al suo posto anche dopo l'incolla (le nuove vanno sotto),
quindi si elimina ricliccando lo stesso punto.

**Trappola trovata collaudando:** se nella tabella c'è già una riga vuota residua, Sysmac non ne crea
un'altra e l'operazione fallisce. Il messaggio d'errore ora lo dice.

Come per l'import, alla fine conta le variabili sul disco prima e dopo: se non aumentano, **fallisce**
invece di dichiarare successo.

---

## Stato complessivo dopo A, B, C, D

| | prima | adesso |
|---|---|---|
| finestra nascosta | azioni fallite in silenzio | ripristinata e massimizzata da sola |
| coordinate note | fuori di 9 px (origine finestra massimizzata) | centrate |
| progetto individuato | primo `.applicationlock` trovato, spesso orfano | quello del PID vivo |
| import rung | "Incollato" sempre | conta i rung, fallisce se non ha incollato |
| testo con CapsLock | maiuscole invertite | esatto, dagli appunti |
| dialoghi | ~10 click a coordinate ciascuno | 1 chiamata per nome |
| variabili | chiudi → scrivi → riapri (2-3 min) | 1 chiamata a progetto aperto |

## File e backup

| File | Backup |
|---|---|
| `sysmac-mcp\server.py` | `.bak_pre_visibile`, `.bak_pre_lockpid`, `.bak_pre_massimizza`, `.bak_pre_offsetclick`, `.bak_pre_capslock`, `.bak_pre_dialoghi`, `.bak_pre_vars`, `.bak_pre_riga_uia` |
| `sysmac_ui.ps1` | `.bak_pre_dialoghi`, `.bak_pre_combo`, `.bak_pre_vars` |

Patch rieseguibili in `sysmac-mcp\`: `patch_A.py`, `patch_A2.py`, `patch_A3.py`, `patch_A4.py`,
`patch_B.py`, `patch_C.py`, `patch_D.py`, `patch_D2.py` (tutte con `--dry`).

**Riavvio dell'app Claude**: ora serve, perché i tool `mcp__sysmac-ladder__*` (compresi i due nuovi,
`sysmac_dialogo` e `sysmac_vars`) sono ancora quelli vecchi in memoria. Il codice è già collaudato:
le prove giravano in un processo separato che rilegge `server.py` a ogni chiamata.

Il progetto `test_import_ladder` è stato riportato allo stato di partenza: 137 rung, 3 variabili
globali.
