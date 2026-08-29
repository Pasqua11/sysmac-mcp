# Collaudare la logica prima di aprire Sysmac

Fatto il 28/08/2026. Tre strumenti nuovi, tutti verificati sul semaforo.

---

## 1. `sim_spec.py` — la spec si esegue in Python

Interpreta la stessa spec che alimenta `ladder_gen` e la fa girare come un PLC: scansione ciclica,
contatti (NA, NC, fronti), bobine (normale, SET, RESET), paralleli, rami di uscita, TON con tempo
simulato, `Get*Clk`, `MOVE`, `@Inc`.

**La prova che conta.** Ho reintrodotto l'errore trovato stamattina in Sysmac — le due chiamate
pedonali invertite — e rilanciato:

```
   7  la chiamata NS accorcia il verde NS al minimo   FAIL (attesa fra 2.6 e 4.0)
  10  verde EO accorciato dalla chiamata EO           FAIL (attesa fra 2.6 e 4.0)

Semaforo incrocio - collaudo completo: FAIL (16 passi, 2 falliti)
--- 0,68 s ---
```

Individua **esattamente** i due passi difettosi, in meno di un secondo. Stamattina lo stesso errore
è emerso dopo ~20 minuti di simulazione in Sysmac ed è costato altri 6 minuti di correzione.

Con la spec corretta: `PASS (16 passi, 0 falliti)` in 0,66 s.

## 2. `semaforo_scenario.json` — un file, due mondi

Lo stesso scenario gira nel simulatore Python **e** sul simulatore Sysmac (`collauda()`), perché ho
esteso `simlink.esegui_scenario` con i due passi che mancavano:

- `impulso`: pulsante ON breve poi OFF (chiamate pedonali, start)
- `durata`: misura quanto una variabile resta a un valore **agganciando il fronte** — prima aspetta
  lo stato opposto, poi misura. È l'errore di misura di stamattina (0,4 s invece di 8) reso
  impossibile.

**Verifica incrociata:**

| Misura | Python | Sysmac | scarto |
|---|---|---|---|
| verde NS (6 s di prova) | 6,01 s | 6,23 s | +0,22 |
| giallo (2 s) | 2,01 s | 2,08 s | +0,07 |
| verde NS accorciato dalla chiamata | 3,02 s | 3,14 s | +0,12 |
| verde EO accorciato dalla chiamata | 3,01 s | 3,34 s | +0,33 |
| lampeggio notturno | 0,50 s | 0,51 s | +0,01 |

`Python: PASS | Sysmac: PASS` — il modello è fedele entro tre decimi di secondo, e gli scarti sono
il polling del simulatore reale.

## 3. `tempi_progetto.py` — tempi di prova e tempi reali

I tempi sono variabili `TIME` ritentive: si cambiano nei valori iniziali, senza toccare il ladder.

```
python tempi_progetto.py Semaforo_Incrocio_V2 prova    # ciclo 20 s
python tempi_progetto.py Semaforo_Incrocio_V2 reali    # ciclo 55 s
python tempi_progetto.py Semaforo_Incrocio_V2 mostra
```

Con i tempi di prova il ciclo passa da 55 a 20 secondi: osservare due cicli costa 40 secondi invece
di due minuti. Il progetto è stato riportato ai tempi di esercizio a fine collaudo (verificato).

---

## Il flusso, adesso

1. Scrivere/modificare la logica in `genera_*.py`
2. **`python sim_spec.py spec.json scenario.json`** → PASS o FAIL in meno di un secondo
3. Solo quando è PASS: generare l'XML, importare, compilare
4. Applicare i **tempi di prova**, lanciare lo **stesso scenario** su Sysmac con `collauda()`
5. Rimettere i tempi reali

I primi due punti costano secondi e intercettano gli errori di logica; Sysmac serve a confermare che
il ladder generato si comporta come il modello — e finora lo fa entro tre decimi.

## Quanto vale

| | stamattina | adesso |
|---|---|---|
| errore logico individuato in | ~20 min (simulazione Sysmac) | **0,7 s** (Python) |
| correzione + riverifica | 6 min | 3 s + rigenerazione |
| collaudo completo | 20 min a mano, 15 chiamate | **1 chiamata**, ~90 s su Sysmac |
| ciclo semaforico da osservare | 55 s | 20 s (tempi di prova) |

Stima per il prossimo programma da 30 rung: **10-12 minuti** contro i 33 del semaforo.

## File

| File | Cosa fa |
|---|---|
| `sysmac-mcp\sim_spec.py` | esegue la spec senza Sysmac; da riga di comando dà PASS/FAIL |
| `sysmac-mcp\semaforo_scenario.json` | 16 passi di collaudo, validi per entrambi i simulatori |
| `sysmac-mcp\tempi_progetto.py` | applica i tempi di prova o quelli reali |
| `sysmac-mcp\simlink.py` | esteso con `impulso` e `durata` (backup `.bak_pre_scenario2`) |
| `sysmac-mcp\semaforo_spec_ROTTA.json` | la spec con l'errore reintrodotto: serve a verificare che il simulatore lo trovi ancora |

Il file `semaforo_spec_ROTTA.json` è il collaudo del collaudo: se un domani `sim_spec.py` gli dà
PASS, vuol dire che si è rotto qualcosa nel simulatore.
