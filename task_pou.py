# -*- coding: utf-8 -*-
"""
task_pou.py - assegna un POU a un task del controllore, a progetto chiuso.

In Sysmac un POU di tipo Programma non basta crearlo: va anche ASSOCIATO a un
task, altrimenti la compilazione risponde "Errore di collegamento. Il nome, il
tipo di dati o il namespace utilizzato non corrispondono alla definizione" -
un messaggio che non dice affatto qual e' il problema, e che ci ha fatto
perdere un giro intero il 29/08/2026.

Programma0 viene associato da Sysmac alla creazione del progetto; ogni POU
aggiunto dopo, no.

L'associazione sta in un piccolo file XML dei task:

    <Programs>
      <AssociatedProgramData ProgramName="Programma0" InstanceName="Programma0"
        IniFileTrackingId="93b2e587..." StartupSetting="TRUE"
        SequenceNumber="1" IsDebugProgram="false" />
    </Programs>

Aggiungerne una riga costa millesimi di secondo, contro il giro completo nella
finestra "Impostazioni task".
"""
import glob
import os
import re
import sys
import uuid

sys.path.insert(0, r"C:\Users\tecni\Claude\sysmac-mcp")
import slwd
import smc2


def file_task(cartella):
    """Il file XML che contiene le associazioni programma-task."""
    for f in glob.glob(os.path.join(cartella, "*.xml")):
        try:
            with open(f, encoding="utf-8-sig", errors="ignore") as fh:
                testo = fh.read(4000)
        except OSError:
            continue
        if "AssociatedProgramData" in testo or "<Programs />" in testo:
            return f
    return None


def _cartella(progetto):
    """Funziona sia con un nome d'archivio sia con un percorso .smc2: nel
    secondo caso il file va estratto e poi ricompresso, come fa
    sysmac_vars_offline."""
    if str(progetto).lower().endswith(".smc2"):
        return None
    return slwd.trova_progetto(progetto)


def elenco(progetto):
    """I programmi gia' associati al task."""
    cart = _cartella(progetto)
    if cart is None:
        with smc2.progetto(progetto, sola_lettura=True) as p:
            return _leggi(p.cartella)
    return _leggi(cart)


def _leggi(cart):
    f = file_task(cart)
    if not f:
        return []
    return re.findall(r'ProgramName="([^"]+)"',
                      open(f, encoding="utf-8-sig").read())


def id_pou(cart, nome):
    """Il `trackingId` del POU, senza trattini: e' quello che va in
    IniFileTrackingId.

    NON e' un numero qualsiasi. Con un GUID inventato Sysmac accetta il file,
    ma alla riapertura scarta l'associazione in silenzio: il programma non
    viene mai eseguito e la compilazione non segnala niente. Due ore per
    scoprirlo, il 29/08/2026.

    L'entita' nel .oem si presenta cosi':
      <Entity type="Program" subtype="StructuredText" id="775eecfc-..."
              name="Programma1" ... trackingId="8386f1e6-258f-..." />
    """
    for oem in glob.glob(os.path.join(cart, "*.oem")):
        testo = open(oem, encoding="utf-8-sig", errors="ignore").read()
        for m in re.finditer(r"<Entity[^>]*>", testo):
            e = m.group(0)
            if 'name="%s"' % nome in e and 'type="Program"' in e:
                i = re.search(r'trackingId="([^"]+)"', e)
                if i:
                    return i.group(1).replace("-", "")
    return None


def _aggiungi(cart, programma):
    f = file_task(cart)
    if not f:
        raise RuntimeError("file dei task non trovato in %s" % cart)
    testo = open(f, encoding="utf-8-sig").read()
    gia = re.findall(r'ProgramName="([^"]+)"', testo)
    if programma in gia:
        return "%s era gia' associato al task (%s)" % (programma, ", ".join(gia))

    ident = id_pou(cart, programma)
    if not ident:
        raise RuntimeError("POU %r non trovato nel progetto: senza il suo "
                           "identificativo l'associazione verrebbe scartata"
                           % programma)

    riga = ('    <AssociatedProgramData ProgramName="{n}" InstanceName="{n}" '
            'IniFileTrackingId="{i}" StartupSetting="TRUE" '
            'SequenceNumber="{s}" IsDebugProgram="false" />\n'
            .format(n=programma, i=ident, s=len(gia) + 1))

    if "<Programs />" in testo:
        nuovo = testo.replace("<Programs />", "<Programs>\n%s  </Programs>" % riga)
    elif "</Programs>" in testo:
        nuovo = testo.replace("  </Programs>", riga + "  </Programs>")
    else:
        raise RuntimeError("sezione <Programs> non trovata nel file dei task")

    with open(f, "w", encoding="utf-8") as fh:
        fh.write(nuovo)
    return "%s associato al task (ora: %s)" % (programma,
                                               ", ".join(gia + [programma]))


def assegna(progetto, programma, forza=False):
    """Associa `programma` al task. Restituisce un messaggio."""
    cart = _cartella(progetto)
    if cart is None:
        with smc2.progetto(progetto) as p:
            msg = _aggiungi(p.cartella, programma)
            p.modificato = True      # senza questo il .smc2 non viene riscritto
            return msg
    if not forza and slwd.aperto_in_sysmac(cart):
        raise RuntimeError("il progetto e' APERTO in Sysmac: chiuderlo prima, "
                           "altrimenti il salvataggio sovrascrive la modifica")
    return _aggiungi(cart, programma)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
    elif len(sys.argv) == 2:
        print("programmi associati:", ", ".join(elenco(sys.argv[1])) or "(nessuno)")
    else:
        print(assegna(sys.argv[1], sys.argv[2]))
