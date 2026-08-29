# -*- coding: utf-8 -*-
"""
patch_B.py - Intervento B: testo dagli appunti e guardia sul CapsLock (28/08/2026)

Due guasti osservati il 27-28/08/2026 scrivendo nella GUI:

1. CapsLock acceso -> SendKeys manda i caratteri come TASTI FISICI e il
   maiuscolo si inverte: "FB_Power_Trasl" e' diventato "fb_pOWER_tRASL", il
   blocco funzione e' stato creato col nome sbagliato e si e' dovuto rifare.
2. SendKeys perde caratteri all'inizio: "Ritardo" e' arrivato come "tardo".

Rimedio: gli appunti (gia' disponibili in _incolla) diventano la via normale
per il TESTO, mentre SendKeys resta per le sequenze di comando.

ATTENZIONE alle scorciatoie di una lettera: nell'editor ladder "c" = contatto,
"d" = contatto N.C., "o" = bobina, "f" = blocco funzione, "r" = nuovo rung.
Vanno DIGITATE, non incollate: la regola tiene fuori i testi di un carattere.
"""
import os, shutil, sys

SRV = r"C:\Users\tecni\Claude\sysmac-mcp\server.py"
BAK = SRV + ".bak_pre_capslock"

CAPS = '''

# ------------------------------------------------------------------ CapsLock
# 27/08/2026: col CapsLock acceso SendKeys ha scritto "fb_pOWER_tRASL" al posto
# di "FB_Power_Trasl" (manda tasti fisici, quindi il maiuscolo si inverte) e il
# blocco funzione e' stato creato col nome sbagliato. Ora si controlla prima.

_VK_CAPITAL = 0x14


def _capslock_attivo() -> bool:
    """True se il CapsLock e' inserito. Lettura via GetKeyState: istantanea,
    senza PowerShell, e concorde con [Windows.Forms.Control]::IsKeyLocked."""
    return bool(user32.GetKeyState(_VK_CAPITAL) & 1)


def _capslock_off() -> bool:
    """Spegne il CapsLock se acceso. True se ha dovuto agire."""
    if not _capslock_attivo():
        return False
    user32.keybd_event(_VK_CAPITAL, 0, 0, 0)   # KEYEVENTF_KEYDOWN
    user32.keybd_event(_VK_CAPITAL, 0, 2, 0)   # KEYEVENTF_KEYUP
    time.sleep(0.15)
    return not _capslock_attivo()


# caratteri che danno un significato speciale alla stringa in SendKeys:
# se ci sono, il testo e' una SEQUENZA DI COMANDO e va inviato come tale.
_SENDKEYS_SPECIALI = "{}^%+~()[]"


def _e_comando_sendkeys(testo: str) -> bool:
    """True se `testo` va inviato con SendKeys invece che dagli appunti.

    Sono comandi: le sequenze con caratteri speciali ("^s", "{ENTER}") e le
    scorciatoie di UNA lettera dell'editor ladder (c, d, o, f, r, t, i, w),
    che incollate non farebbero nulla."""
    if len(testo) <= 1:
        return True
    return any(c in _SENDKEYS_SPECIALI for c in testo)
'''

VECCHIO_SEND = '''def _send_keys(keys: str) -> None:
    _ps("Add-Type -AssemblyName System.Windows.Forms; "
        f"[System.Windows.Forms.SendKeys]::SendWait({_ps_quote(keys)})")'''

NUOVO_SEND = '''def _send_keys(keys: str) -> None:
    # con il CapsLock acceso SendKeys inverte le maiuscole: si spegne prima,
    # ma solo quando la sequenza contiene davvero delle lettere
    if any(c.isalpha() for c in keys):
        _capslock_off()
    _ps("Add-Type -AssemblyName System.Windows.Forms; "
        f"[System.Windows.Forms.SendKeys]::SendWait({_ps_quote(keys)})")'''

VECCHIO_TOOL = '''def sysmac_send_keys(keys: str) -> str:
    """Invia tasti a Sysmac con sintassi SendKeys (es. '{F8}', '^s', '+{F5}',
    '^%r', 'Motore{ENTER}')."""
    _focus_sysmac()
    _send_keys(keys)
    return f"Inviato: {keys}"'''

NUOVO_TOOL = '''def sysmac_send_keys(keys: str) -> str:
    """Invia tasti a Sysmac con sintassi SendKeys (es. '{F8}', '^s', '+{F5}',
    '^%r', 'Motore{ENTER}').

    Il TESTO semplice (nomi di variabili, tipi, commenti) viene immesso dagli
    APPUNTI invece che con SendKeys: e' l'unico modo affidabile: con il
    CapsLock acceso SendKeys inverte le maiuscole e ogni tanto perde i primi
    caratteri ("Ritardo" -> "tardo").
    Restano inviate come tasti le sequenze di comando ('^s', '{ENTER}') e le
    scorciatoie di una lettera dell'editor ladder (c, d, o, f, r)."""
    _focus_sysmac()
    if _e_comando_sendkeys(keys):
        _send_keys(keys)
        return f"Inviato: {keys}"
    _incolla(keys)
    return f"Scritto dagli appunti: {keys}"'''

VECCHIO_UI = '''    if a in ("tasti", "keys"):
        return sysmac_send_keys(testo)'''

NUOVO_UI = '''    if a in ("tasti", "keys"):
        return sysmac_send_keys(testo)
    if a in ("scrivi", "testo"):
        # scrive SEMPRE dagli appunti, anche un solo carattere
        _focus_sysmac()
        _incolla(testo)
        return "Scritto dagli appunti: %s" % testo
    if a in ("capslock",):
        return ("CapsLock era acceso: spento." if _capslock_off()
                else "CapsLock gia' spento.")'''

DOC_UI = '''      "tasti"     invia `testo` come sequenza SendKeys: "^v", "{ESC}",
                  "Tim_1{TAB}TON{ENTER}"'''
DOC_UI_NUOVO = '''      "tasti"     invia `testo`: le sequenze di comando ("^v", "{ESC}") e le
                  scorciatoie di una lettera (c, d, o, f, r) partono come
                  tasti, il testo semplice viene immesso dagli APPUNTI
      "scrivi"    scrive `testo` sempre dagli appunti (anche un carattere)
      "capslock"  spegne il CapsLock se acceso'''


def main():
    dry = "--dry" in sys.argv
    s = open(SRV, encoding="utf-8").read()
    orig = s

    assert VECCHIO_SEND in s, "patch B1: _send_keys non trovata"
    s = s.replace(VECCHIO_SEND, CAPS.rstrip() + "\n\n\n" + NUOVO_SEND, 1)

    assert VECCHIO_TOOL in s, "patch B2: sysmac_send_keys non trovata"
    s = s.replace(VECCHIO_TOOL, NUOVO_TOOL, 1)

    assert VECCHIO_UI in s, "patch B3: ramo 'tasti' di sysmac_ui non trovato"
    s = s.replace(VECCHIO_UI, NUOVO_UI, 1)

    assert DOC_UI in s, "patch B4: docstring di sysmac_ui non trovata"
    s = s.replace(DOC_UI, DOC_UI_NUOVO, 1)

    print("modifiche: %d -> %d caratteri (%+d)" % (len(orig), len(s), len(s) - len(orig)))
    if dry:
        print("(dry run)")
        return
    if not os.path.exists(BAK):
        shutil.copyfile(SRV, BAK)
        print("backup:", BAK)
    open(SRV, "w", encoding="utf-8").write(s)
    print("scritto:", SRV)


if __name__ == "__main__":
    main()
