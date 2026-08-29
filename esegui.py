"""esegui.py - runner isolato per sysmac_exec.

Gira in un processo separato: cosi' un blocco (tipico del socket del
simulatore quando la simulazione non e' in RUN) o un errore grave non
trascinano giu' il server MCP, e il timeout e' davvero applicabile.

Uso:  python esegui.py <file_codice.py>
Stampa su stdout un JSON: {"uscita": "...", "risultato": "...", "errore": "..."}
"""

import io
import json
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _watchdog(secondi, api_box):
    """Chiude la sessione col simulatore e termina PRIMA che il padre uccida
    il processo: un processo ucciso lascia la connessione appesa lato
    simulatore, e le connessioni appese bloccano quelle successive."""
    import threading

    def _scade():
        try:
            if api_box.get("api") is not None:
                api_box["api"].chiudi()
        except Exception:
            pass
        sys.stderr.write("\n[watchdog] tempo scaduto: chiusura pulita\n")
        sys.stderr.flush()
        os._exit(3)

    t = threading.Timer(secondi, _scade)
    t.daemon = True
    t.start()
    return t


def main():
    codice = open(sys.argv[1], encoding="utf-8-sig").read()
    box = {"api": None}
    if len(sys.argv) > 2:
        try:
            _watchdog(max(2.0, float(sys.argv[2]) - 2.0), box)
        except ValueError:
            pass
    esito = {"uscita": "", "risultato": None, "errore": None}
    buf = io.StringIO()
    vero_stdout = sys.stdout
    api = None
    try:
        import sysmac_api as api
        box["api"] = api
        ns = dict(api.NAMESPACE)
        ns["__name__"] = "sysmac_exec"
        sys.stdout = buf
        try:
            # se l'ultima istruzione e' un'espressione se ne stampa il valore
            albero = compile(codice, "<sysmac_exec>", "exec")
            exec(albero, ns)
        finally:
            sys.stdout = vero_stdout
        ris = ns.get("risultato")
        if ris is not None:
            esito["risultato"] = ris if isinstance(ris, str) else \
                json.dumps(ris, ensure_ascii=False, default=str)
    except BaseException:
        sys.stdout = vero_stdout
        esito["errore"] = traceback.format_exc(limit=8)
    finally:
        try:
            if api is not None:
                api.chiudi()
        except Exception:
            pass
    esito["uscita"] = buf.getvalue()
    vero_stdout.write(json.dumps(esito, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
