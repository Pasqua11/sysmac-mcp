# Memory

## Me
Luca (trentalucas74@gmail.com), tecnico elettrico/automazione. Lavoro con materiale elettrico, schemi SPAC, preventivi fornitori.

## Strumenti Attivi
| Strumento | Cosa fa | Come usarlo |
|-----------|---------|-------------|
| **sacchi-cli** | Ordina/cerca su Sacchi.it senza browser | `python sacchi_cli.py <comando>` |
| **prezzi_fornitori.db** | DB SQLite prezzi fornitori | Query Python o skill price-research |
| **aggiorna_prezzi_2026.py** | Importa prezzi da fatture PDF + conferme ordine nel DB. v4.6 (19/06/2026): filtro anti-spazzatura, parser dedicato fatture AI Automazione/Industriale, normalizzazione codici Omron | Task pianificato sabato ~22:00; log in %TEMP%\aggiorna_prezzi_log.txt |
| **qc_prezzi.py** | Controllo qualità DB prezzi (sola lettura): segnala codici sospetti e variazioni prezzo anomale. Stato in _qc_last_id.txt | Task pianificato domenica ~08:00; report in qc_prezzi_report.txt |
| **prompt_sacchi_prezzi_v2.md** | Procedura scraping prezzi netti da Sacchi.it (Chrome) | Validata 10/06/2026 |
| **sacchi_to_db.py** | Importa nel DB i prezzi scrapati da Sacchi.it | Sostituire lista PREZZI e DATA, eseguire con Python Windows |
| **prompt_rs_prezzi_v1.md** | Procedura scraping prezzi da RS Online (fetch same-origin, ~0,8 s/codice) | Validata 10/06/2026 |
| **rs_to_db.py** | Importa nel DB i prezzi scrapati da RS (fornitore RS id 46) | Come sacchi_to_db.py |

## Regole Operative
- **Ricerca prezzi — ordine obbligatorio**:
  1. **DB** `prezzi_fornitori.db`: se il codice ha un prezzo con data_rilevazione ≤ 6 mesi, usarlo (indicando fonte e data). Più vecchio o assente → online.
  2. **Sacchi.it** (scraping web, prompt_sacchi_prezzi_v2.md) per i codici mancanti.
  3. **RS Online** (rsonline.it) per i codici non trovati su Sacchi.
  I non trovati da nessuna fonte → "da quotare a parte", mai inventare prezzi.
- **Dopo ogni run di scraping prezzi Sacchi.it**: inserire SEMPRE i prezzi trovati in `prezzi_fornitori.db` via `sacchi_to_db.py` (fornitore SACCHI id 47, fonte "sacchi.it (scraping web)", append con data_rilevazione — mai sovrascrivere lo storico). Stesso principio per prezzi trovati su RS (fonte "rsonline.it (scraping web)").

## Manutenzione DB prezzi (aggiornato 19/06/2026)
- **Filtro anti-spazzatura** in ingestione (`is_codice_garbage` in aggiorna_prezzi_2026.py): scarta codici troncati (es. `OMR-`), tutti-zeri/segnaposto (`000000000000`), con spazi, troppo corti, e parole-testo di fattura (`Scontr.`, `Esigib.`, `VALVOLA`…). I record con codice NULL legittimi (es. pacchetti KEYENCE) NON vengono toccati.
- **Parser fatture AI Automazione / AI Industriale** (`extract_items_ai_fattura`): il fornitore usa codici `PREFIX-CODICE` (OMR-, SIE-, SNR-, LEG-, WEK-…); estrae il vero codice produttore, o codice=NULL+descrizione quando assente (così non perde la riga).
- **Normalizzazione codici Omron** (`normalizza_codice`): trattino canonico serie NX (`NXID5442`→`NX-ID5442`), `NX1P2…`, `NX1W…`, `G9SE…`. Schneider e Siemens NON normalizzati (già coerenti tra le fonti — non aggiungere regole lì).
- **Task pianificato QC**: `qc-prezzi-domenica` (domenica ~08:00) segnala anomalie, NON cancella. Le pulizie del DB si fanno una-tantum con anteprima + conferma esplicita, mai in automatico.
- **Backup DB** prima di ogni operazione distruttiva (file `prezzi_fornitori_*BACKUP*/PRECLEAN/PRENORM/PREBACKFILL*.db` nella cartella Claude).

## Terms / Shorthand
| Termine | Significato |
|---------|-------------|
| **sacchi** | Sacchi.it (distributore materiale elettrico) |
| **sacchi-cli** | CLI Python per ordinare da Sacchi.it |
| **cart** / **carrello** | Carrello Sacchi.it |
| **productId** | Codice interno Sacchi (18 cifre, es. 000000000001406383) |
| **mfr code** | Codice produttore (es. 3RT20161BB41) |

## Progetti / Script Attivi
| Nome | Cosa | File |
|------|------|------|
| **sacchi-cli** | CLI per Sacchi.it: search, price, stock, cart | `C:\Users\tecni\Claude\sacchi_cli.py` |

→ Dettagli: memory/projects/sacchi-cli.md
→ Glossario completo: memory/glossary.md

## Percorsi importanti
| Cosa | Percorso |
|------|----------|
| **Offerte commerciali ufficiali ai clienti** | `\\192.168.1.56\Documenti\OFFERTE SYNTECH` |


## Manuali macchina — stili di impaginazione
Quando creo un **nuovo manuale macchina**, cercare e applicare gli stili/template di impaginazione salvati nella cartella `C:\Users\tecni\Claude\Documenti\`:
- `Syntech_standard formattazione manuali - guida.md` + `Syntech_standard formattazione manuali - checklist.md` → standard cappe / wet bench (riferimento Com.1000); include la struttura dei manuali HMI / Terminale Operatore (descrizioni a punti, una schermata HMI per pagina).
- `CONVECO_formatting_guide.md` + `CONVECO_style_checklist.md` → standard Scrubber FBK / CONVECO.

Scegliere il template in base alla famiglia di macchina, applicarlo e verificare la conformità con la skill `manual-style-analyzer`.


## Cartella ufficiale (nota del 30/07/2026)
- **Questa cartella (`C:\Users\tecni\Claude`) è la cartella di lavoro UFFICIALE**: DB prezzi, script, backup, fatture, template manuali, memory/.
- `leggi_email.ps1` (lettura email Outlook) e' QUI: `C:\Users\tecni\Claude\leggi_email.ps1`. La cartella `Documents\Claude` e' stata ELIMINATA il 30/07/2026: non usarla e non ricrearla.
- Ricerca file per nome sul server: `C:\Users\tecni\Claude\cerca_server.ps1` — dentro i documenti: `C:\Users\tecni\Claude\cerca_contenuto.ps1`.
- Memoria WordPress/sito syntech.it: memory/wordpress_locale.md — progetto in `Projects\Sito Syntech Wordpress`.

## Sysmac Studio — automazione via Claude (nota del 25/08/2026)
Per pilotare Sysmac Studio (nuovo progetto, ladder, simulatore) con Claude/windows-mcp: procedure testate e prerequisiti (app Claude come ADMIN, Norton, SendInput) in **memory/sysmac_automazione.md**. Progetto Claude di riferimento: "Sysmac Studio con Claude".
- **Tasti di scelta rapida**: mappa completa (351 comandi, 129 assegnati) letta dalla finestra "Personalizza tasti di scelta rapida" il 26/08/2026 -> `C:\Users\tecni\Claude\sysmac_scorciatoie.md`. Per ogni comando c'e' anche la stringa SendKeys pronta per `sysmac_send_keys`. Usarla PRIMA di navigare i menu a click.
- Scorciatoie aggiunte il 26/08/2026 per velocizzare l'automazione: Ctrl+Alt+X = Strumenti>IEC 61131-10 XML>Importa (import ladder XML), Ctrl+Shift+F8 = Ricompila Controllore, Ctrl+Alt+5 = Simulazione>Esegui una scansione, Ctrl+Alt+L = Inserisci etichetta salto (ladder), Ctrl+Alt+Q = Imposta istruzione/Set (ladder), Ctrl+Alt+W = Ripristina istruzione/Reset (ladder). Backup reimportabile: `C:\Users\tecni\Claude\sysmac_shortcuts_backup.json`. Nota: Ctrl+Alt+S non e' assegnabile (non viene registrato dal campo) e "Esporta variabili globali" non e' personalizzabile.
- **Layer UI Automation nell'MCP (26/08/2026)**: `server.py` ora ha il ponte `_uia()` verso la libreria `C:\Users\tecni\Claude\sysmac_ui.ps1` e 6 tool che NON usano coordinate: `sysmac_focus`, `sysmac_menu` (voce di menu per nome, es. "Progetto/Ricompila Controllore"), `sysmac_button` (pulsante per nome in un dialogo), `sysmac_ui_dump` (esplora una finestra sconosciuta), `sysmac_errors` e `sysmac_compile_text` (errori di compilazione come TESTO invece che screenshot). Preferirli SEMPRE a `sysmac_click`. Backup del server precedente: `server.py.bak_pre_uia2`. `sysmac_errors` CALIBRATO e verificato il 26/08/2026 su errori veri: pannello identificato per AutomationId `buildWindowsViewWindow`, contatori Errori/Avvisi + righe complete (scorre da solo la griglia virtualizzata). Se il pannello e' chiuso: Alt+6.

### REGOLA (27/08/2026): in Sysmac NON si disegna a mano
Prima di qualsiasi lavoro di programmazione su Sysmac, leggere **memory/prima-di-programmare-in-sysmac.md**.
Il ladder si GENERA: spec JSON -> `python sysmac-mcp\ladder_gen.py spec.json` -> import XML + `sysmac_paste_vars`.
Il generatore conosce gia' 91 tipi di blocchi (`pins.json`) e i template in `sysmac-mcp\templates\` (MC_Power, MC_Home,
MC_MoveAbsolute, MC_Stop, MC_Reset, MC_MoveJog, MC_MoveLinear*, MC_Group*, TON, MOVE, confronti, ST inline).
Disegnare un box FB nella GUI e' l'ultima risorsa, solo per un tipo mai campionato: costa ~10 minuti a blocco
contro ~10 secondi via XML. Controllare sempre il CapsLock prima di usare SendKeys.

Copertura blocchi Sysmac: stato e piano in **memory/piano-copertura-blocchi-sysmac.md** (27/08/2026). 76 tipi su 78 certificati (import + compilazione 0 errori) = 92,9% degli usi reali; restano AryMax/AryMin da campionare, MC_Restart1S (libreria 1S) e i 12 FB custom da raccogliere in una libreria .slr. Rigenerare la batteria con `python sysmac-mcp\genera_batteria.py` + `ladder_gen.py batteria_spec.json`.

Librerie FB SYNTECH (28/08/2026): tre file .slr in C:\OMRON\Data\Lib -- SYNTECH_FB_Cappa (Ritardo), SYNTECH_FB_Etch (Contatore_Full), SYNTECH_FB_Skid (Controllo_EV, Cnt_Min_Sec), verificate insieme sullo stesso progetto. Procedura e trappole (tipi dati duplicati tra librerie, progetto libreria che deve compilare) in **memory/libreria-slr-procedura.md**. Contatore ha gia' una sua libreria dal 2019; Drive_Error_Warning e MTCP/INV*_3G3M1 sono librerie Omron, non FB SYNTECH.

MCP sysmac-ladder, intervento A (28/08/2026): corretti 4 difetti in server.py -- finestra nascosta ora ripristinata (_assicura_visibile), lock .applicationlock orfani filtrati per PID, _massimizza usa GetWindowPlacement invece delle dimensioni, e soprattutto _clickf NON somma piu' l'origine negativa (-9,-9) della finestra massimizzata: tutte le coordinate note erano fuori di 9 px. sysmac_import_ladder_xml ora conta i rung prima/dopo e FALLISCE se non ha incollato. Dettagli in **memory/intervento-A-fatto.md**, backup server.py.bak_pre_*.

MCP sysmac-ladder, intervento B (28/08/2026): il TESTO si scrive dagli appunti, non con SendKeys. sysmac_send_keys instrada da solo: lunghezza 1 o caratteri {}^%+~ = tasti (scorciatoie ladder c/d/o/f/r/t/i e sequenze ^s), tutto il resto = appunti. Aggiunte _capslock_attivo/_capslock_off (guardia automatica prima di ogni SendKeys con lettere) e le azioni sysmac_ui 'scrivi' e 'capslock'. Verificato con CapsLock acceso: Test_CapsLock_OK scritto esatto. Dettagli in **memory/intervento-B-fatto.md**, backup server.py.bak_pre_capslock.

MCP sysmac-ladder, interventi C e D (28/08/2026): due tool nuovi. sysmac_dialogo(titolo, campi, caselle, tendine, riga, pulsante) compila un dialogo per NOME in una chiamata (i campi Edit si trovano per etichetta con Find-UiEditByLabel, geometria; le voci delle tendine sono esposte come [Chiave, Etichetta] quindi match parziale). sysmac_vars(variabili, tabella) crea variabili a progetto APERTO: menu contestuale con Shift+F10, voci per nome, riga selezionata cliccando il selettore calcolato via UIA (_selettore_ultima_riga). Entrambi verificano l'esito sul disco e falliscono se non hanno fatto nulla. Dettagli in **memory/interventi-C-D-fatti.md**.

MCP sysmac-ladder, collaudo post-riavvio (28/08/2026): corretti 4 difetti emersi solo caricando i tool -- decoratore @mcp.tool scivolato su un helper (e sysmac_vars_crea cancellata, poi recuperata dal backup), click troppo pronto dopo la massimizzazione (ora 1,2 s di attesa in _clickf), apostrofo nelle etichette che rompeva la stringa PowerShell in sysmac_dialogo (ora esiti per indice). Regola: quando si inserisce codice prima di una funzione, controllare il decoratore che sta sopra. Dettagli in **memory/collaudo-post-riavvio.md**.

Semaforo incrocio (28/08/2026): progetto **Semaforo_Incrocio_V2**, 34 rung, 77 variabili, 0 errori, collaudato in simulazione (giallo 3,03 s / tutto-rosso 2,02 s / verde 26,1 s / con chiamata pedonale 8,3 s / notte lampeggiante / emergenza tutto rosso). Realizzato in 33 minuti contro le 2 ore della movimentazione assi. La logica sta in `sysmac-mcp\genera_semaforo.py`: si modifica li' e si rigenera (3 s XML + 10 s import), non si tocca il ladder. Tempi di fase = variabili TIME ritentive da SCADA. Lezioni sui tempi in **memory/semaforo-incrocio-report.md**.

RICETTA TEMPI Sysmac (28/08/2026): un programma nuovo si fa in ~30 min seguendo **memory/ricetta-tempi-sysmac.md** -- logica come spec Python, XML validato, variabili in blocco, import verificato, compilazione subito, poi SIMULAZIONE (e' li' che si trovano gli errori di logica). Tabella delle trappole misurate (finestra nascosta, offset 9 px, CapsLock, Ctrl+A che non svuota, riga vuota, watch >30 s, misure senza fronte, pulsanti con acceleratore).

COLLAUDO SENZA SYSMAC (28/08/2026): prima di aprire Sysmac si prova la logica con `python sysmac-mcp\sim_spec.py <spec.json> <scenario.json>` -> PASS/FAIL in meno di 1 s (interprete ladder della spec: contatti, fronti, SET/RESET, OR, TON, clock, MOVE, @Inc). Lo STESSO scenario JSON gira anche sul simulatore Sysmac con collauda(): simlink.esegui_scenario ora supporta 'impulso' e 'durata' (che aggancia il FRONTE, altrimenti la misura e' falsa). tempi_progetto.py applica tempi di PROVA (ciclo 20 s) o REALI (55 s) scrivendo i valori iniziali a progetto chiuso. Verifica incrociata sul semaforo: Python e Sysmac concordano entro 0,3 s. Dettagli in **memory/collaudo-senza-sysmac.md**.

ESERCITAZIONE TEMPI UI (28/08/2026): due programmi nuovi (Nastro_Conteggio 16 rung, Gestione_Pompe 26 rung) realizzati in ~4 min l'uno, 106-120 s di sole operazioni UI. Scoperte: il TEMPLATE DI PROGETTO NON CONVIENE (duplicare 32 s contro 11 s per crearne uno nuovo; e vars_offline impiega 37 s sia per 41 sia per 46 variabili) -- il template giusto e' un FILE DI VARIABILI STANDARD da concatenare. Corretti: fronti per occorrenza e confronti in sim_spec, TIME scrivibile dal simulatore ('T#2s' -> nanosecondi), esegui_scenario applica da solo i tempi dello scenario, import con ritentativo. REGOLA: ogni scenario su Sysmac deve iniziare con un passo di azzeramento (il PLC conserva gli allarmi ritenuti, il simulatore Python no). Dettagli in **memory/esercitazione-tempi-ui.md**.
28/08/2026 - Linea di lavaggio 11 vasche, 90 rung, 166 variabili: compilata 0 errori, PASS 54/54 sia in Python sia su Sysmac. UI 101 s in tutto, cioe' QUANTO un programma da 26 rung: il tempo non scala coi rung, conviene importare tutto in un colpo solo. Scoperta chiave: scrivendo le variabili nel FILE .smc2 (progetto creato con 'Gestisci nel file di progetto') ci vogliono 0,1 s invece dei 37 s dell'archivio. Vedi memory/lavaggio-90-rung-tempi.md e sysmac-mcp/genera_lavaggio.py (parametrico 4-20 vasche).
28/08/2026 - Programma piu' lungo della libreria: CFE300_V4, 711 rung in 29 sezioni (censimento di 119 progetti in 1,1 s con sysmac-mcp/censimento.py). Ne ho scritto l'equivalente, CFE_Wetbench_V2: 716 rung, 653 variabili, 0 errori, PASS 38/38 in Python e su Sysmac, in 4 min 40 s totali (200 s di UI). Otto volte i rung del programma precedente costano solo il doppio del tempo. REGOLA NUOVA: ogni scenario di collaudo deve fare almeno DUE cicli completi - i difetti di azzeramento dei passi si vedono solo dal secondo. Corretti anche sim_spec (simulava solo la prima sezione!) e simlink (TIME esposte come LINT). Vedi memory/cfe-716-rung-tempi.md.
28/08/2026 - Rifiniture server Sysmac: sysmac_apri_sezione ora funziona (10,5 s invece di 19 a coordinate) e sysmac_save(file=...) salva davvero (15,9 s). SCOPERTA CHIAVE: Sysmac non e' tutta WPF. L'Explorer multivista e' un TreeView Win32 dentro WindowsFormsHost e UIA NON ne espone i nodi: si pilota con {HOME}{LEFT}{DOWN} poi {RIGHT 12} (la freccia destra apre il nodo chiuso e scende al primo figlio se e' aperto). Nel dialogo Salva progetto il campo Nome file e' un Pane con ClassName=Edit e AutomationId=1001, senza ValuePattern, e i pulsanti sono Pane con ClassName=Button: si cercano per ClassName+AutomationId e si usa il loro rettangolo. REGOLA: se un elemento non si trova, non cercarlo per tipo - guarda ClassName e AutomationId. Inoltre ogni _send_keys avvia un processo PowerShell: accorpare SEMPRE i tasti in una sola sequenza (12 tasti separati = 12 s, insieme = 1 s). Vedi memory/rifiniture-server-sysmac.md.
28/08/2026 notte - Motore di esercitazione autonoma: sysmac-mcp/moduli.py (catalogo di 8 moduli di automazione veri, ognuno con i propri rung E i propri passi di collaudo) + sysmac-mcp/notte.py (compone impianti casuali, collauda in Python, fa il giro completo in Sysmac, cronometra, si autoripara). Avviato per la notte del 28/08. Risultati in C:\Users\tecni\Claude\esercizi_notte (diario_notte.md, misure.json). Per fermarlo: creare FERMATI.txt in quella cartella. LEZIONI: un solo processo per volta sulla GUI (lock PID); il dialogo 'Salvare prima di chiudere?' si intitola col NOME DEL PROGETTO e va evitato salvando prima; i dialoghi si richiamano a vicenda, premerli nell'ordine No/OK/Annulla e mai Salva a campo vuoto; i tasti mandati tutti insieme si perdono, mandarli a gruppi di 3. Vedi memory/esercitazione-notturna.md.
29/08/2026 - ESITO NOTTE: 153 esercizi su 153 completati, 6618 rung, tutte le compilazioni a 0 errori, zero interruzioni. MA il tempo NON e' migliorato (primo terzo 99 s, ultimo terzo 111 s): le fasi sono costanti al decimo di secondo perche' sono tempi macchina di Sysmac, non di abilita'. CONCLUSIONE: esercitarsi ancora sulla UI e' tempo sprecato; il collo di bottiglia e' ora la scrittura della specifica. Creato sysmac-mcp/linter.py: controlla doppie bobine, SET senza reset, variabili mai lette/mai scritte, senza aprire Sysmac. Passato su 119 progetti: la libreria e' sana, solo la famiglia CFE300 ha 2 doppie bobine (V_L_DI_Parz_V4 e _V6, comandate in due rung diversi). Cosa manca davvero, in ordine: 1) ponte schema SPAC -> variabili + mappa I/O (il pezzo piu' grosso), 2) linter completo da lanciare prima di ogni consegna, 3) documentazione generata dal progetto, 4) scenari di collaudo come verbale PDF, 5) AryMax/AryMin e movimentazione con quote a 0. Vedi memory/bilancio-e-prossimi-passi.md.
29/08/2026 - SCOPERTA IMPORTANTE (ricognizione.py sui 119 progetti): 2709 POU in Structured Text contro 2948 in Ladder. Meta' del codice SYNTECH e' in ST e finora generavo solo ladder. L'ST e' memorizzato come TESTO PURO dentro <StructuredTextModel><Text>...</Text>: molto piu' semplice del ladder XML. PROVA RIUSCITA: progetto PROVA_ST, POU aggiunto da menu contestuale su Programmi > Aggiungi > ST, codice incollato in 3,5 s (contro 13,7 s dell'import ladder), compilazione 0 errori 0 avvisi. Prossimo passo naturale: generatore ST dalla spec + interprete ST nel simulatore per non perdere il collaudo automatico. Vedi memory/structured-text.md.
29/08/2026 - INTERPRETE ST FATTO: sysmac-mcp/sim_st.py esegue Structured Text come il PLC (IF/CASE/FOR/WHILE/REPEAT, TON/TOF/TP/CTU/CTD, funzioni standard), 35 prove su 35, stesso formato di scenario del ladder. Ha gia' trovato un difetto vero: un TON chiamato DENTRO un ramo del CASE non si azzera mai e al secondo ciclo la macchina va in allarme subito - REGOLA: in ST i blocchi con stato vanno chiamati a OGNI scansione, la condizione si passa come ingresso. Nel server: sysmac_st_nuovo/sysmac_st_scrivi (POU ST creato da menu contestuale Programmi>Aggiungi>ST, codice incollato in 3,5 s contro 13,7 s del ladder, compila 0 errori). NON CHIUSO: il collaudo sul simulatore, perche' un POU aggiunto dopo la creazione del progetto NON e' associato a nessun task e il PLC non lo esegue (errore fuorviante: 'Errore di collegamento'). task_pou.py associa il POU scrivendo il file - attenzione, IniFileTrackingId deve essere il trackingId dell'entita' nel .oem senza trattini, non un GUID inventato - ma non basta a far partire il simulatore: l'associazione va fatta dalla UI. DA PROVARE: Strumenti > Importa programma ST, l'import nativo di Sysmac. Vedi memory/interprete-st.md.
29/08/2026 - ST: CERCHIO CHIUSO. Essiccatore a 3 fasi in Structured Text (107 righe, macchina a stati con CASE): PASS 13/13 con sim_st.py in 0,09 s, 0 errori di compilazione, PASS 13/13 sul simulatore Sysmac in 12 s, stesso file di scenario. REGOLA CHIAVE trovata: dopo aver modificato i file di un progetto DALL'ESTERNO bisogna RIAVVIARE Sysmac Studio, non basta chiudere e riaprire il progetto - lo stesso progetto che rifiutava di avviare il simulatore e' partito in 23 s dopo il riavvio. L'associazione POU-task si vede in Configurazioni e impostazioni > Impostazioni task > Impostazioni assegnazione programma, e task_pou.py la scrive correttamente. Le variabili: globali senza programma=, interne ed esterne CON programma='<nome POU>'. Import nativo (Strumenti > Importa programma ST) provato: vuole un XML in formato Omron non documentato, non esiste export da cui ricavarlo, strada chiusa e inutile visto che incollare il codice costa 3,5 s. Manca solo il generatore ST dalla spec. Vedi memory/st-cerchio-chiuso.md.
29/08/2026 - GENERATORE ST FATTO: sysmac-mcp/st_gen.py traduce in Structured Text la STESSA spec JSON che produce il ladder. Verificato con confronta_ladder_st.py, che esegue lo stesso scenario sui due linguaggi e confronta passo per passo: 5 programmi su 6 si comportano in modo IDENTICO, compreso il wetbench CFE (715 rung -> 3285 righe di ST), e le misure di durata coincidono al centesimo. UNICO CASO APERTO: il lampeggio del semaforo, fatto con due TON incrociati (uno abilitato dalla negazione dell'uscita dell'altro): in ladder oscilla, in ST no. Costrutto isolato, per ora da scrivere a mano o lasciare in ladder. Il confronto ha trovato tre difetti dell'INTERPRETE, non del generatore: lo scenario va eseguito nell'ordine set-attendi-impulso con impulsi da 0,3 s (come sim_spec e come il simulatore Sysmac), niente attese aggiuntive dopo l'impulso, e i passi 'durata' devono agganciare il FRONTE (aspettare prima lo stato opposto). Vedi memory/generatore-st.md.
