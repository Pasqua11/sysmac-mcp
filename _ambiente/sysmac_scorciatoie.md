# Sysmac Studio – Mappa completa tasti di scelta rapida

Fonte: finestra **Strumenti > Personalizza tasti di scelta rapida...** (destinazione "Controllore"),
letta direttamente dall'installazione di Luca il 26/08/2026 tramite UI Automation.
351 comandi totali, 129 con scorciatoia assegnata. Le voci senza scorciatoia sono omesse.

Sintassi tra parentesi = stringa SendKeys da usare con `sysmac_send_keys`.

---

## 1. Menu principale

### File
| Comando | Tasto | SendKeys |
|---|---|---|
| Salva | Ctrl+S | `^s` |
| Stampa... | Ctrl+P | `^p` |

### Modifica
| Comando | Tasto | SendKeys |
|---|---|---|
| Annulla | Ctrl+Z | `^z` |
| Ripeti | Ctrl+Y | `^y` |
| Taglia | Ctrl+X | `^x` |
| Copia | Ctrl+C | `^c` |
| Incolla | Ctrl+V | `^v` |
| Elimina | Delete | `{DELETE}` |
| Seleziona tutto | Ctrl+A | `^a` |
| Trova e Sostituisci... | Ctrl+F | `^f` |
| Cerca precedente | Shift+F3 | `+{F3}` |
| Cerca successivo | F3 | `{F3}` |
| Passa a explorer multivista | Alt+Shift+L | `%+l` |

### Visualizza
| Comando | Tasto | SendKeys |
|---|---|---|
| Explorer multivista | Alt+1 | `%1` |
| Visualizzazione scelta rapida progetto | Alt+Shift+1 | `%+1` |
| Casella degli strumenti | Alt+2 | `%2` |
| Scheda Risultati | Alt+3 | `%3` |
| Scheda Monitoraggio | Alt+4 | `%4` |
| Monitoraggio (Tabella) | Alt+Shift+4 | `%+4` |
| Scheda Riferimenti incrociati | Alt+5 | `%5` |
| Scheda Compilazione | Alt+6 | `%6` |
| Scheda Risultati Trova e Sostituisci | Alt+7 | `%7` |
| Pannello Simulazione | Alt+8 | `%8` |
| Monitoraggio differenziale | Alt+9 | `%9` |
| Tabella variabili | Ctrl+Shift+V | `^+v` |
| Ricerca progetto intelligente | Ctrl+Shift+F | `^+f` |
| Ultime finestre chiuse | Ctrl+Shift+H | `^+h` |
| Zoom avanti | Alt+Right | `%{RIGHT}` |
| Zoom indietro | Alt+Left | `%{LEFT}` |
| Adatta alla finestra | Alt+Up | `%{UP}` |
| Ripristino zoom | Alt+Down | `%{DOWN}` |

### Progetto
| Comando | Tasto | SendKeys |
|---|---|---|
| Verifica tutti i programmi | F7 | `{F7}` |
| Verifica programmi selezionati | Shift+F7 | `+{F7}` |
| Compila Controllore | F8 | `{F8}` |
| **Ricompila Controllore** | **Ctrl+Shift+F8** *(nuovo)* | `^+{F8}` |
| Interrompi compilazione | Shift+F8 | `+{F8}` |
| Modifica online – Avvio | Ctrl+E | `^e` |
| Modifica online – Trasferisci | Ctrl+Shift+E | `^+e` |
| Modifica online – Annulla | Ctrl+U | `^u` |
| Vai a Pannello di modifica | Ctrl+Shift+G | `^+g` |

### Controllore
| Comando | Tasto | SendKeys |
|---|---|---|
| Online | Ctrl+W | `^w` |
| Offline | Ctrl+Shift+W | `^+w` |
| Sincronizza... | Ctrl+M | `^m` |
| Trasferisci a controllore... | Ctrl+T | `^t` |
| Trasferisci da controllore... | Ctrl+Shift+T | `^+t` |
| Modalità RUN... | Ctrl+3 | `^3` |
| Modalità PROGRAM... | Ctrl+1 | `^1` |
| Set (istruzione) | Ctrl+Shift+J | `^+j` |
| Reset (istruzione) | Ctrl+Shift+K | `^+k` |
| Aggiornamento forzato TRUE | Ctrl+J | `^j` |
| Aggiornamento forzato FALSE | Ctrl+K | `^k` |
| Aggiornamento forzato Annulla | Ctrl+L | `^l` |

### Simulazione
| Comando | Tasto | SendKeys |
|---|---|---|
| Esegui | F5 | `{F5}` |
| Esegui in modalità PROGRAM | Alt+F5 | `%{F5}` |
| Pausa | Ctrl+Alt+Break | `^%{BREAK}` |
| Arresta | Shift+F5 | `+{F5}` |
| Esecuzione step | F10 | `{F10}` |
| Esegui step | F11 | `{F11}` |
| Esci da step | Shift+F11 | `+{F11}` |
| **Esegui una scansione** | **Ctrl+Alt+5** *(nuovo)* | `^%5` |
| Finestra punto di interruzione | Alt+F9 | `%{F9}` |
| Imposta/Cancella punto di interruzione | F9 | `{F9}` |
| Attiva/disattiva punto di interruzione | Ctrl+F9 | `^{F9}` |
| Cancella tutti i punti di interruzione | Ctrl+Shift+F9 | `^+{F9}` |

### Strumenti
| Comando | Tasto | SendKeys |
|---|---|---|
| **IEC 61131-10 XML > Importa...** | **Ctrl+Alt+X** *(nuovo)* | `^%x` |
| Riproduzione automazione – Avvia | Ctrl+B | `^b` |
| Riproduzione automazione – Esci | Ctrl+Shift+B | `^+b` |

### Finestra
| Comando | Tasto | SendKeys |
|---|---|---|
| Chiudi scheda | Ctrl+F4 | `^{F4}` |
| Apri scheda successiva | Ctrl+F6 | `^{F6}` |
| Apri scheda precedente | Ctrl+Shift+F6 | `^+{F6}` |

---

## 2. Editor ladder (finestra di modifica)

Attenzione: questi tasti valgono **solo con il focus nell'editor ladder**. Alcune lettere
(H, R, O) hanno significato diverso a seconda del sotto-contesto (inserimento vs. visualizzazione).

### Modifica / Inserisci
| Comando | Tasto | SendKeys |
|---|---|---|
| Avvia modifiche | Enter oppure F2 | `{ENTER}` / `{F2}` |
| Elenco dei tasti di scelta rapida | H | `h` |
| Inserisci rung sopra | Shift+R | `+r` |
| Inserisci rung sotto | R | `r` |
| **Inserisci etichetta salto** | **Ctrl+Alt+L** *(nuovo)* | `^%l` |
| Inserisci ingresso (N.O.) | C | `c` |
| Inserisci sopra | Ctrl+Shift+1 | `^+1` |
| Inserisci sotto | Ctrl+Shift+2 | `^+2` |
| Incolla | P | `p` |
| Sposta linea di collegamento | M | `m` |
| Aggiungi linea di collegamento | T | `t` |
| Inserisci ingresso parallelo sopra | Shift+W | `+w` |
| Inserisci ingresso parallelo sotto | W | `w` |
| Inserisci ingresso N.C. / Inverti (NOT) | D oppure / | `d` / `/` |
| Inserisci ingresso N.C. sopra | Shift+X | `+x` |
| Inserisci ingresso N.C. sotto | X | `x` |
| Inserisci uscita / uscita parallela sotto | O | `o` |
| Inserisci uscita parallela sopra | Shift+O | `+o` |
| Inserisci uscita NOT | Q | `q` |
| Inserisci blocco funzione | F | `f` |
| Inserisci funzione | I | `i` |
| Inserisci salto | J | `j` |
| Inserisci ST in linea | S | `s` |
| Diff positiva | Ctrl+Shift+U | `^+u` |
| Diff negativa | Ctrl+Shift+D | `^+d` |
| **Imposta istruzione (Set)** | **Ctrl+Alt+Q** *(nuovo)* | `^%q` |
| **Ripristina istruzione (Reset)** | **Ctrl+Alt+W** *(nuovo)* | `^%w` |
| Al livello superiore | Ctrl+Shift+P | `^+p` |
| Al livello inferiore | Ctrl+Shift+L | `^+l` |
| Modifica commento variabile | Ctrl+Enter | `^{ENTER}` |
| Modifica commento elemento | Alt+Enter | `%{ENTER}` |
| Registra nella tabella delle variabili | Ctrl+Alt+R | `^%r` |
| Vai alla tabella variabili | Ctrl+Alt+J | `^%j` |
| Cerca fattore di uscita | Ctrl+O | `^o` |
| Mostra descrizione comando | Shift+T | `+t` |

### Vai a
| Comando | Tasto | SendKeys |
|---|---|---|
| Vai a variabile successiva | N | `n` |
| Indietro | B | `b` |
| Vai a ingresso successivo | Ctrl+Shift+I | `^+i` |
| Vai a uscita successiva | Ctrl+Shift+O | `^+o` |
| Ripercorri ricerca | Space | `{SPACE}` |
| Vai a rung | G | `g` |
| Mostra/nascondi guida | Ctrl+G | `^g` |
| Visualizza elenco commenti di rung | L oppure Alt+Shift+R | `l` / `%+r` |
| Nascondi elenco commenti di rung | Shift+L | `+l` |

### Modifica linea di collegamento
| Comando | Tasto | SendKeys |
|---|---|---|
| Sposta punto collegamento sopra | Ctrl+Up | `^{UP}` |
| Sposta punto collegamento sotto | Ctrl+Down | `^{DOWN}` |
| Sposta punto collegamento a destra | Ctrl+Right | `^{RIGHT}` |
| Sposta punto collegamento a sinistra | Ctrl+Left | `^{LEFT}` |
| Copia sequenza rung | Ctrl+Shift+V | `^+v` |

### Visualizza / rung
| Comando | Tasto | SendKeys |
|---|---|---|
| Ingrandisci rung | + | `{ADD}` |
| Riduci rung | - | `{SUBTRACT}` |
| Cerca fattore di uscita | Ctrl+O | `^o` |
| Cerca rung di uscita | O | `o` |
| Nascondi rung | H | `h` |
| Mostra rung | R | `r` |
| Passa all'editor | Enter | `{ENTER}` |
| Elimina rung | Delete | `{DELETE}` |
| Espandi rung | Right | `{RIGHT}` |
| Comprimi rung | Left | `{LEFT}` |

---

## 3. Scorciatoie create il 26/08/2026

Assegnate per ridurre la navigazione a menu durante il lavoro automatizzato.
Verificate riaprendo la finestra dopo l'OK; backup in `C:\Users\tecni\Claude\sysmac_shortcuts_backup.json`
(reimportabile con il pulsante **Importa** della stessa finestra).

| Comando | Percorso menu | Nuovo tasto | ID interno |
|---|---|---|---|
| Importa XML PLCopen | Strumenti > IEC 61131-10 XML > Importa... | Ctrl+Alt+X | `NexPlcOpenXml.V3Import` |
| Ricompila Controllore | Progetto > Ricompila Controllore | Ctrl+Shift+F8 | `NexReBuild` |
| Esegui una scansione | Simulazione > Esegui una scansione | Ctrl+Alt+5 | `OneScan Simulator` |
| Inserisci etichetta salto | Editor ladder | Ctrl+Alt+L | `InsertJumpLabel` |
| Imposta istruzione (Set) | Editor ladder | Ctrl+Alt+Q | `Set` |
| Ripristina istruzione (Reset) | Editor ladder | Ctrl+Alt+W | `Reset` |

### Limiti riscontrati (fatti, non ipotesi)
- **Esporta variabili globali** (Strumenti): il pulsante "Assegna" resta disabilitato → comando
  non personalizzabile in questa versione.
- **Ctrl+Alt+S**: il campo "Immetti nuovo tasto di scelta rapida" non registra la combinazione
  (probabile intercettazione a livello di sistema). Per questo "Imposta istruzione" usa Ctrl+Alt+Q.
- Le voci del menu **File** (Salva, Stampa, ecc.) risultano a sola lettura: si vedono ma non
  si riassegnano.
- Il file `%APPDATA%\OMRON\CXAP\UserShortcutKeys.json` non risultava ancora aggiornato subito
  dopo l'OK: Sysmac lo riscrive alla chiusura dell'applicazione. Il backup esportato
  manualmente contiene comunque le 6 assegnazioni.
