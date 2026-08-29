# Piano di copertura dei blocchi Sysmac — niente più attese

Redatto e in parte eseguito il 27/08/2026. Obiettivo: qualunque blocco usato nei programmi SYNTECH
deve poter essere generato e importato senza disegnare nulla nella GUI.

---

## 1. Punto di partenza (misurato, non stimato)

| Dato | Valore |
|---|---|
| Tipi di blocco usati nei 73 progetti | **91** |
| Istanze totali di blocchi | **11.766** |
| Tipi con template XML campionato da Sysmac | 17 |
| Tipi con sola firma ricostruita da `pins.json` | 74 |
| FB scritti da Luca | 12 |
| Istruzioni del catalogo manuali mai usate | ~420 (su ~510) |

I primi 20 tipi coprono l'85% degli usi, i primi 56 il 98%.

---

## 2. Fase 1 — Collaudo dei blocchi standard  ✅ ESEGUITA

**Metodo.** Generata una batteria automatica: un rung minimo per ogni tipo, con ogni pin collegato
a una variabile del tipo giusto, presa dalla firma in `pins.json`. Tutto importato nel progetto
`test_import_ladder` (NX1P2 + 2 assi virtuali + gruppo assi) e compilato.

**Risultato: 76 tipi su 78 compilano a 0 errori / 0 avvisi.**
Copertura sugli usi reali: **92,9%** (10.930 istanze su 11.766; il resto sono i FB custom, fase 2).

Quattro giri di correzione, tutti su errori miei nel generatore della batteria, non del generatore ladder:

| Problema trovato | Correzione |
|---|---|
| Variabili chiamate `v_INT`, `v_BOOL`... | in `ladder_gen` il prefisso **`v`** significa "contatto con fronte di discesa": `v_EN` diventava un fronte su `_EN`. Rinominate `t_*` |
| Istanze dei FB non dichiarate | ogni `{"fb": X, "inst": I}` richiede una variabile `I` di tipo `X` nella tabella |
| Pin di tipo `ANY_NUM[]`, `ANY_ELEMENTARY[]` | si passa il **primo elemento** (`arr[0]`), non l'array |
| Pin di tipo `ARRAY[0..3] OF LREAL` (MC_MoveLinear*) | si passa invece l'**array intero** |

**Non passati, con causa accertata:**

| Tipo | Usi | Causa | Rimedio |
|---|---|---|---|
| `AryMax` | 4 | firma da database incompleta: Sysmac non riconosce il box | campionare il rung da un progetto che lo usa |
| `AryMin` | 1 | idem | idem |
| `\\OMR_1S\MC_Restart1S` | 6 | FB della libreria Omron 1S, non presente nel progetto di test | agganciare la libreria 1S al progetto |

**File prodotti** (in `C:\Users\tecni\Claude\sysmac-mcp\`):

- `genera_batteria.py` — rigenera la batteria da `pins.json` in un comando
- `batteria_spec.json` — spec delle 11 famiglie (78 rung, 122 variabili)
- `out\sec_Batt_*.xml`, `out\batt_gruppo_[ABC].xml` — ladder pronto da incollare

---

## 3. Fase 2 — I 12 FB scritti da te → libreria Sysmac unica  ⏳ DA FARE

Oggi ognuno di questi vive dentro il progetto che lo usa: un progetto nuovo non li ha, e il ladder
generato non compila.

| FB | Usi | FB | Usi |
|---|---|---|---|
| `Contatore` | 652 | `Drive_Error_Warning` | 31 |
| `MTCP_Server_NJNX` | 43 | `Cnt_Min_Sec` | 24 |
| `Controllo_EV` | 36 | `Contatore_Full` | 12 |
| `INV000_3G3M1_Alarm` | 10 | `INV003_3G3M1_ECT` | 10 |
| `Ritardo` | 4 | `INV001/002/011_3G3M1_*` | 1 ciascuno |

**Come procedere:** prendere la versione più recente di ciascun FB, raccoglierla in un progetto
"libreria SYNTECH", esportarla come `.slr` e agganciarla alle commesse nuove.
Attenzione a `MTCP_Server_NJNX`: nei progetti esistono **due firme diverse** (due versioni di libreria);
va deciso quale diventa quella ufficiale.

Stima: 1-2 ore, da fare in una sessione dedicata perché richiede scelte tue su quale versione tenere.

---

## 4. Fase 3 — Da descrizione a parole a ladder importato  ⏳ DA FARE

Il flusso che useremo alla prossima commessa:

1. **Tu descrivi** la sequenza come la diresti a un collega
   ("carro con 6 vasche, prelievo al carico, tempo per vasca, deposito allo scarico, allarmi").
2. **Io scrivo la spec JSON** e **te la mostro** prima di importare: è testo leggibile, una riga per rung.
3. `ladder_gen.py` genera XML + tabella variabili.
4. `vars_offline` crea le variabili a progetto chiuso, import dei rung, `F8`, `Ctrl+S`.

Tempo atteso per una sezione da 30 rung: **5-10 minuti**, contro le 2 ore di stasera.

Acceleratore già disponibile: 73 progetti sono già convertiti in spec JSON (`sysmac-mcp\specs\`),
quindi una sezione collaudata si riusa cambiando i nomi invece di riscriverla.

---

## 5. Regole operative ricavate stasera (già in `memory\`)

1. **Prima di ogni import verificare che la finestra di Sysmac sia VISIBILE.**
   Il tool risponde "Incollato" anche quando il Ctrl+V finisce nel vuoto perché la finestra è nascosta:
   è così che ho perso il primo giro di 79 rung. Controllo: `IsWindowVisible` sull'hwnd, e se serve
   `ShowWindow(SW_RESTORE)`.
2. **Validare l'XML prima di incollare** (`[xml]$file` in PowerShell): se non è well-formed Sysmac
   lo rifiuta in silenzio.
3. **Variabili sempre offline** (`vars_offline`, progetto chiuso): una chiamata, zero GUI, zero
   dialoghi "Risolvi conflitti".
4. **Il prefisso `v` nei nomi è riservato** dalla sintassi della spec (fronte di discesa). Da evitare
   nei nomi generati automaticamente.
5. **Controllare il CapsLock** prima di qualunque `SendKeys`.

---

## 6. Cosa resta e quanto costa

| Attività | Tempo stimato | Serve una tua decisione? |
|---|---|---|
| Campionare `AryMax` e `AryMin` da un progetto reale | 10 min | no |
| Agganciare la libreria Omron 1S per `MC_Restart1S` | 15 min | no |
| Libreria `.slr` dei 12 FB custom | 1-2 h | sì: quale versione di `MTCP_Server_NJNX` |
| Estendere il catalogo alle istruzioni mai usate | su richiesta | no: la firma si ricava dal manuale |
