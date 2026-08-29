"""smc2.py - lavorare su un progetto Sysmac che sta in un FILE .smc2.

Uno .smc2 e' uno ZIP che contiene la cartella GUID del progetto: dentro ci sono
esattamente i file che slwd.py e spec2rung.py sanno gia' leggere e scrivere.
Questo modulo fa da strato sopra: estrae, ti da' la cartella, ricomprime.

    import smc2, slwd, spec2rung
    with smc2.progetto(r"D:\\Commesse\\Skid.smc2") as p:
        slwd.crea_variabili(p.cartella, globali=[("IN_MARCIA", "BOOL")])
        spec2rung.scrivi_sezione(p.sezione("Movimentazione"), rungs)
    # ricompresso in automatico all'uscita del blocco

Vantaggi rispetto all'archivio interno di Sysmac (C:\\OMRON\\Data\\Solution):
  - non serve che il progetto sia chiuso: un file e' solo un file
  - CREARE un progetto = copiare un file modello
  - RINOMINARE un progetto = rinominare il file (il nome del progetto segue
    quello del file: verificato il 27/08/2026)
  - backup e rollback = copia del file
  - Sysmac lo apre in ~4 s dalla pagina "File di progetto" (serve la spunta
    "Gestisci nel file di progetto") e NON crea voci nell'archivio

La stessa API accetta anche un progetto dell'archivio, indicato per nome: in
quel caso non c'e' nulla da estrarre e da ricomprimere.
"""

import os
import re
import shutil
import tempfile
import zipfile

ESTENSIONI = (".smc2", ".smc", ".csm2")


class ErroreProgetto(RuntimeError):
    pass


def e_file(x):
    return isinstance(x, str) and x.lower().endswith(ESTENSIONI)


def bloccato(path):
    """True se un altro programma tiene il file aperto in scrittura
    (tipicamente Sysmac con il progetto caricato)."""
    try:
        with open(path, "r+b"):
            return False
    except OSError:
        return True


# ------------------------------------------------------------------ sezioni
def sezioni(cartella):
    """[(nome, percorso_file)] delle sezioni, nell'ordine dell'albero."""
    oem = [f for f in os.listdir(cartella) if f.endswith(".oem")]
    if not oem:
        raise ErroreProgetto("nessun .oem in %s" % cartella)
    with open(os.path.join(cartella, oem[0]), encoding="utf-8",
              errors="replace") as fh:
        t = fh.read()
    out = []
    for m in re.finditer(r'<Entity type="PouBody"[^>]*>', t):
        tag = m.group(0)
        i = re.search(r'id="([0-9a-fA-F-]+)"', tag)
        n = re.search(r'name="([^"]*)"', tag)
        if i and n:
            out.append((n.group(1), os.path.join(cartella, i.group(1) + ".xml")))
    return out


def nome_progetto(cartella):
    for f in os.listdir(cartella):
        if f.endswith(".manifest"):
            with open(os.path.join(cartella, f), encoding="utf-8",
                      errors="replace") as fh:
                m = re.search(r'solutionName="([^"]*)"', fh.read())
            if m:
                return m.group(1)
    return ""


# ------------------------------------------------------------------ apertura
class Progetto(object):
    """Contesto di lavoro su un progetto. Usare con `with`."""

    def __init__(self, origine, sola_lettura=False, backup=True):
        self.origine = origine
        self.sola_lettura = sola_lettura
        self.backup = backup
        self.cartella = None
        self.modificato = False
        self._tmp = None
        self._e_file = e_file(origine)

    # ---- ciclo di vita
    def __enter__(self):
        if not self._e_file:
            import slwd
            self.cartella = (origine if os.path.isdir(origine := self.origine)
                             else slwd.trova_progetto(self.origine))
            return self
        if not os.path.exists(self.origine):
            raise ErroreProgetto("file non trovato: %s" % self.origine)
        if not self.sola_lettura and bloccato(self.origine):
            raise ErroreProgetto(
                "il file %s e' bloccato da un altro programma: probabilmente e' "
                "aperto in Sysmac Studio. Chiuderlo prima di scriverci."
                % os.path.basename(self.origine))
        self._tmp = tempfile.mkdtemp(prefix="smc2_")
        with zipfile.ZipFile(self.origine) as z:
            z.extractall(self._tmp)
        cartelle = [d for d in os.listdir(self._tmp)
                    if os.path.isdir(os.path.join(self._tmp, d))]
        if len(cartelle) != 1:
            self._pulisci()
            raise ErroreProgetto(
                "atteso un solo progetto nello zip, trovati %s" % cartelle)
        self.cartella = os.path.join(self._tmp, cartelle[0])
        self.modificato = False
        return self

    def __exit__(self, tipo, val, tb):
        try:
            if self._e_file and tipo is None and self.modificato:
                self.salva()
        finally:
            self._pulisci()
        return False

    def _pulisci(self):
        if self._tmp:
            shutil.rmtree(self._tmp, ignore_errors=True)
            self._tmp = None

    # ---- comodita'
    def sezioni(self):
        return sezioni(self.cartella)

    def sezione(self, nome):
        for n, f in sezioni(self.cartella):
            if n.lower() == nome.lower():
                return f
        raise ErroreProgetto("sezione '%s' non trovata: presenti %s"
                             % (nome, [n for n, _ in sezioni(self.cartella)]))

    def nome(self):
        return nome_progetto(self.cartella)

    def tocca(self):
        """Segnala che il contenuto e' cambiato (fa ricomprimere all'uscita)."""
        self.modificato = True
        return self

    def salva(self):
        """Ricomprime la cartella nel file di partenza, in modo atomico."""
        if not self._e_file:
            return False
        if self.sola_lettura:
            raise ErroreProgetto("aperto in sola lettura")
        if self.backup:
            b = self.origine + ".bak"
            if os.path.exists(self.origine):
                shutil.copyfile(self.origine, b)
        base = os.path.dirname(self.cartella)
        tmpzip = self.origine + ".nuovo"
        with zipfile.ZipFile(tmpzip, "w", zipfile.ZIP_DEFLATED) as z:
            for cur, _dirs, files in os.walk(self.cartella):
                rel = os.path.relpath(cur, base).replace("\\", "/")
                z.writestr(rel + "/", "")
                for f in files:
                    p = os.path.join(cur, f)
                    z.write(p, os.path.relpath(p, base).replace("\\", "/"))
        os.replace(tmpzip, self.origine)
        self.modificato = False
        return True


def progetto(origine, sola_lettura=False, backup=True):
    """Apre un progetto: `origine` puo' essere un file .smc2, una cartella, o
    il nome di un progetto dell'archivio di Sysmac."""
    return Progetto(origine, sola_lettura, backup)


# ------------------------------------------------------- creare e rinominare
def crea(modello, destinazione, sovrascrivi=False):
    """Crea un progetto nuovo copiando un file modello.

    Il nome del progetto segue il nome del FILE, quindi creare e rinominare
    sono semplici operazioni su file. Ritorna il percorso creato."""
    if not e_file(modello) or not e_file(destinazione):
        raise ErroreProgetto("servono due file .smc2")
    if os.path.exists(destinazione) and not sovrascrivi:
        raise ErroreProgetto("esiste gia': %s" % destinazione)
    d = os.path.dirname(os.path.abspath(destinazione))
    if d and not os.path.isdir(d):
        os.makedirs(d)
    shutil.copyfile(modello, destinazione)
    return destinazione


def rinomina(percorso, nuovo_nome):
    """Rinomina il file (e quindi il progetto). `nuovo_nome` senza estensione."""
    d = os.path.dirname(os.path.abspath(percorso))
    est = os.path.splitext(percorso)[1]
    nuovo = os.path.join(d, nuovo_nome + est)
    os.replace(percorso, nuovo)
    return nuovo


# ------------------------------------------------------------------ lettura
def variabili_globali(origine):
    """{nome: tipo} delle variabili globali, da file .smc2 o da archivio."""
    import simvars
    import slwd
    with progetto(origine, sola_lettura=True) as p:
        tipi = {}
        for _intest, righe in slwd.leggi(slwd.file_globali(p.cartella))[1]:
            for r in righe:
                n, d = slwd.campo(r, "N"), slwd.campo(r, "D")
                if n and d:
                    t, rng = simvars.normalizza_tipo(d)
                    if rng:
                        tipi[n] = "ARRAY OF " + t
                        for k in range(rng[0], rng[1] + 1):
                            tipi["%s[%d]" % (n, k)] = t
                    else:
                        tipi[n] = t
        return tipi


def informazioni(origine):
    """Riepilogo di un progetto senza aprirlo in Sysmac."""
    with progetto(origine, sola_lettura=True) as p:
        sez = p.sezioni()
        rung = {}
        for n, f in sez:
            try:
                with open(f, encoding="utf-8-sig", errors="replace") as fh:
                    rung[n] = sum(1 for r in fh if r.strip().startswith("{"))
            except OSError:
                rung[n] = "?"
        return {"nome": p.nome(), "origine": origine,
                "in_file": e_file(origine),
                "globali": len(variabili_globali_da_cartella(p.cartella)),
                "sezioni": rung}


def variabili_globali_da_cartella(cartella):
    import slwd
    out = {}
    for _i, righe in slwd.leggi(slwd.file_globali(cartella))[1]:
        for r in righe:
            n = slwd.campo(r, "N")
            if n:
                out[n] = slwd.campo(r, "D")
    return out


if __name__ == "__main__":
    import json
    import sys
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    print(json.dumps(informazioni(sys.argv[1]), ensure_ascii=False, indent=1))
