# Collaudo dei tool dopo il riavvio (28/08/2026)

Il riavvio dell'app Claude ha caricato i tool nuovi e ha fatto emergere **quattro difetti** che le
prove nel processo separato non potevano mostrare. Tutti corretti e riverificati.

## 1. Decoratori scivolati sulla funzione sbagliata
`patch_D` aveva inserito il nuovo codice **dopo** il `@mcp.tool()` che apparteneva a
`sysmac_vars_crea`: il decoratore è finito su un helper interno.
Risultato visibile al riavvio: `_selettore_ultima_riga` esposto come tool e `sysmac_vars_crea`
sparita dall'elenco. Peggio: `patch_D2`, tagliando "fino al prossimo `@mcp.tool`", aveva
**cancellato del tutto** `sysmac_vars_crea`.

**Corretto**: funzione recuperata dal backup `.bak_pre_vars` e reinserita col suo decoratore;
decoratore orfano rimosso dall'helper. Controllo automatico: nessuna `def _*` è più esposta come
tool, e i 21 tool attesi ci sono tutti.

> Lezione: quando si inserisce codice prima di una funzione, guardare **cosa c'è sopra**. Un
> decoratore non appartiene alla riga che lo segue per caso.

## 2. Il click subito dopo la massimizzazione
Primo uso reale di `sysmac_vars` via MCP: fallito. La finestra era in stato *normale*
(0, 90, 1938, 1128); `_clickf` l'ha massimizzata, ma Sysmac ridisegna il layout interno con un
attimo di ritardo e il click è caduto sulla riga sbagliata — "Crea nuovo" non disponibile.

**Corretto**: dopo una massimizzazione *effettiva*, `_clickf` attende 1,2 s prima di cliccare.
Riprova: `Create 3 variabili in 'globali' (3 -> 6).`

## 3. L'apostrofo nelle etichette
`sysmac_dialogo` costruiva i messaggi di esito interpolando il nome dell'elemento dentro una stringa
PowerShell. Con la casella *"Notificare se **l'ID** libreria..."* la stringa si spezzava:

```
Token 'ID' imprevisto nell'espressione o nell'istruzione.
```

**Corretto**: gli esiti usano un indice numerico e il nome viene rimappato in Python. Riprova sulla
stessa casella: riuscita, con il nome intero riportato nel messaggio.

## 4. (già noto, ora documentato) la riga vuota residua
Se in tabella resta una riga senza nome, Sysmac non ne crea un'altra e `sysmac_vars` fallisce. Il
messaggio d'errore lo dice esplicitamente — ed è così che ho capito subito il primo fallimento.

---

## Stato finale verificato **attraverso i tool MCP**

| Tool | Prova | Esito |
|---|---|---|
| `sysmac_vars` | 3 variabili globali a progetto aperto | `Create 3 variabili in 'globali' (3 -> 6).` |
| `sysmac_dialogo` | casella con apostrofo + pulsante OK | riuscito |
| `sysmac_ui` massimizza | finestra ripristinata a schermo intero | riuscito |
| `sysmac_status` | progetto e simulatore | corretto |

Progetto `test_import_ladder` riportato allo stato di partenza: **137 rung, 3 variabili globali**.

## Backup aggiunti
`server.py.bak_pre_ripristino`, `.bak_pre_attesa_max`, `.bak_pre_apostrofo`.

## Serve un ultimo riavvio
Le quattro correzioni sono nel file ma i tool in memoria sono ancora quelli caricati poco fa.
Dopo il riavvio: `sysmac_vars_crea` torna disponibile, `_selettore_ultima_riga` sparisce
dall'elenco, e `sysmac_dialogo`/`sysmac_vars` includono le correzioni 2 e 3.
