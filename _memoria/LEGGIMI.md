# Memoria di lavoro Sysmac

Copia della cartella `C:\Users\tecni\Claude\memory\` del PC fisso (esclusi i file non attinenti:
`wordpress_locale.md`, `projects\sacchi-cli.md`, `projects\vault-autodesk.md`).
Snapshot al 29/08/2026.

**Non è codice**: è quello che Claude deve sapere per usare bene l'MCP `sysmac-ladder` —
procedure verificate, errori già risolti, tempi misurati, metodo di programmazione.
Senza, il server funziona lo stesso, ma si ricomincia da capo a sbattere sui problemi già chiusi.

## Come attivarla sul notebook

Due modi, equivalenti.

**A) Copiarla nella posizione standard** (consigliata se replichi anche il resto):

```powershell
Copy-Item "C:\Users\<utente>\Claude\sysmac-mcp\_memoria\*" "C:\Users\<utente>\Claude\memory\" -Recurse
```

**B) Lasciarla nel repo** e aggiungere una riga a `C:\Users\<utente>\.claude\CLAUDE.md`:

```
Prima di lavorare su Sysmac Studio leggi C:\Users\<utente>\Claude\sysmac-mcp\_memoria\
(procedure verificate e metodo di lavoro).
```

Il vantaggio di B: la memoria resta versionata e si aggiorna con `git pull`.

## Cosa leggere per prime

| File | Perché |
|---|---|
| `prima-di-programmare-in-sysmac.md` | i controlli da fare prima di toccare un progetto |
| `metodo_programmazione_luca.md` | come Luca vuole che sia scritto il software |
| `sysmac_automazione.md` | panoramica dell'automazione dell'ambiente |
| `collaudo-post-riavvio.md` | ricalibrazione dopo riavvio o cambio PC/risoluzione |
| `ricetta-tempi-sysmac.md` | tempi di attesa affidabili delle operazioni UI |
| `registrazione-variabili-in-blocco.md` | inserimento variabili in blocco senza errori |

`CLAUDE_memoria_di_lavoro.md` è l'indice generale degli strumenti (contiene anche la parte
prezzi/fornitori, non attinente al PLC: utile solo se sul notebook fai anche quel lavoro).

## Nota

È uno snapshot, non un canale di sincronizzazione: se lavori su entrambi i PC, la memoria
va aggiornata a mano (commit + push da un lato, `git pull` dall'altro) o rischi due versioni
divergenti.
