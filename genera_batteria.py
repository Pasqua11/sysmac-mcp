# -*- coding: utf-8 -*-
"""
genera_batteria.py - crea la spec JSON di collaudo: un rung minimo per ogni tipo
di blocco usato nei progetti SYNTECH (pins.json), con i pin collegati a variabili
del tipo corretto. Serve a certificare che ogni tipo entri in Sysmac e compili.

Uso:  python genera_batteria.py [lotto]     (lotto = nome famiglia, opzionale)
Esce: batteria_spec.json  (+ elenco tipi per lotto su stdout)
"""
import json, os, sys, collections

D = os.path.dirname(os.path.abspath(__file__))
PINS = json.load(open(os.path.join(D, "pins.json"), encoding="utf-8"))

# ---- mappa datatype del manuale -> variabile campione da dichiarare -------
TIPO_VAR = {
    "BOOL": ("t_BOOL", "BOOL"),
    "INT": ("t_INT", "INT"),
    "int": ("t_INT", "INT"),
    "UINT": ("t_UINT", "UINT"),
    "DINT": ("t_DINT", "DINT"),
    "UDINT": ("t_UDINT", "UDINT"),
    "USINT": ("t_USINT", "USINT"),
    "REAL": ("t_REAL", "REAL"),
    "LREAL": ("t_LREAL", "LREAL"),
    "WORD": ("t_WORD", "WORD"),
    "DWORD": ("t_DWORD", "DWORD"),
    "BYTE": ("t_BYTE", "BYTE"),
    "TIME": ("t_TIME", "TIME"),
    # famiglie generiche -> scelta concreta
    "ANY": ("t_INT", "INT"),
    "ANY_NUM": ("t_INT", "INT"),
    "ANY_INT": ("t_INT", "INT"),
    "ANY_REAL": ("t_REAL", "REAL"),
    "ANY_BIT": ("t_WORD", "WORD"),
    "ANY_BIT(except BOOL)": ("t_WORD", "WORD"),
    "ANY_NUM, STRING": ("t_INT", "INT"),
    "ANY_ELEMENTARY(except BOOL)": ("t_INT", "INT"),
    "ANY_ELEMENTARY(except ANY_BIT)": ("t_INT", "INT"),
    "ANY_ELEMENTARY, ENUM": ("t_INT", "INT"),
    # array
    "ANY_NUM[]": ("arr_INT", "ARRAY[0..9] OF INT"),
    "ANY_ELEMENTARY[](except ANY_BIT[])": ("arr_INT", "ARRAY[0..9] OF INT"),
    "ANY_ELEMENTARY[], ENUM[]": ("arr_INT", "ARRAY[0..9] OF INT"),
    "array[1..3] of int": ("arr3_INT", "ARRAY[1..3] OF INT"),
    "ARRAY[0..1023] OF WORD": ("arr_W1024", "ARRAY[0..1023] OF WORD"),
    "ARRAY[0..1023] OF BOOL": ("arr_B1024", "ARRAY[0..1023] OF BOOL"),
    "ARRAY[0..3] OF LREAL": ("arr4_LREAL", "ARRAY[0..3] OF LREAL"),
    # stringhe
    "STRING": ("t_STR", "STRING[256]"),
    "STRING[20]": ("t_STR20", "STRING[20]"),
    "STRING[24]": ("t_STR24", "STRING[24]"),
    "STRING[256]": ("t_STR", "STRING[256]"),
    # strutture ed enum di sistema
    "_sAXIS_REF": ("mc_x", None),            # gia' nel progetto di test
    "_sGROUP_REF": ("MC_Group000", None),    # gia' nel progetto di test
    "_sSDO_ACCESS": ("t_SDO", "_sSDO_ACCESS"),
    "_sTimer": ("t_sTimer", "_sTimer"),
    "_sOPR_SET_PARAMS": ("t_OPR", "_sOPR_SET_PARAMS"),
    "_sINIT_SET_PARAMS": ("t_INIT", "_sINIT_SET_PARAMS"),
    "_sNXUNIT_ID": ("t_NXID", "_sNXUNIT_ID"),
    "_eMC_BUFFER_MODE": ("t_eBUF", "_eMC_BUFFER_MODE"),
    "_eMC_COORD_SYSTEM": ("t_eCOORD", "_eMC_COORD_SYSTEM"),
    "_eMC_TRANSITION_MODE": ("t_eTRANS", "_eMC_TRANSITION_MODE"),
    "_eMC_DIRECTION": ("t_eDIR", "_eMC_DIRECTION"),
    "_eCONNECTION_STATE": ("t_eCONN", "_eCONNECTION_STATE"),
}

# famiglie, per importare a lotti e capire subito dove si rompe
FAMIGLIE = {
    "matematica": ["+", "-", "*", "/", "@+", "@-", "@*", "@/", "@ADD", "ADD", "SUB", "MUL", "DIV",
                    "Inc", "Dec", "@Inc", "@Dec", "ABS", "SQRT", "MOD"],
    "confronti": ["=", "<>", "<", ">", "<=", ">=", "EQ", "LT", "GT", "LE", "GE", "NE"],
    "logica": ["AND", "OR", "XOR", "NOT", "TestABit", "TestABitN", "SetABit", "ResetABit",
                "Up", "Down", "UpQ", "DownQ"],
    "timer_contatori": ["TON", "TOF", "TP", "Timer", "CTD", "CTU", "CTUD"],
    "clock": ["Get1sClk", "Get100msClk", "Get10msClk", "Get1minClk", "Get1msClk", "GetTime"],
    "conversioni": ["INT_TO_REAL", "REAL_TO_INT", "REAL_TO_WORD", "WORD_TO_REAL", "UINT_TO_WORD",
                     "WORD_TO_UINT", "INT_TO_WORD", "WORD_TO_INT", "REAL_TO_LREAL", "LREAL_TO_REAL",
                     "DINT_TO_INT", "INT_TO_DINT", "TO_INT", "TO_REAL"],
    "dati_array": ["MOVE", "@MOVE", "ArySearch", "AryMove", "Clear", "LIMIT", "ScaleTrans",
                    "@MovingAverage", "SEL", "MUX"],
    "motion": [t for t in PINS if t.startswith("MC_")],
    "diagnostica": ["ResetECError", "ResetMCError", "GetMCError", "GetECError", "GetNXBError",
                     "GetPLCError", "ResetPLCError", "EC_CoESDOWrite", "EC_CoESDORead", "NX_ChangeWriteMode"],
    "processo": ["PIDAT", "PID", "TimeProportionalOut"],
}

def famiglia_di(tipo):
    for fam, elenco in FAMIGLIE.items():
        if tipo in elenco:
            return fam
    return "altro"

def main():
    solo_lotto = sys.argv[1] if len(sys.argv) > 1 else None

    tipi = {k: v for k, v in PINS.items() if not v.get("user") and "\\" not in k}   # i FB custom vanno in libreria
    if solo_lotto:
        tipi = {k: v for k, v in tipi.items() if famiglia_di(k) == solo_lotto}

    variabili = {}          # nome -> tipo (solo quelle da dichiarare)
    sezioni = collections.defaultdict(list)
    n_out = 0
    saltati = []

    for tipo in sorted(tipi, key=lambda t: -PINS[t].get("usi", 0)):
        info = PINS[tipo]
        p = {}
        ok = True
        for pin in info["pins"]:
            nome = pin["name"]
            if not nome or pin.get("power"):        # EN/ENO e pin di potenza: li fa il rung
                continue
            dt = pin["datatype"]
            if dt not in TIPO_VAR:
                ok = False
                saltati.append((tipo, dt))
                break
            var, decl = TIPO_VAR[dt]
            rif = var
            # pin generico di tipo array (ANY_NUM[], ANY_ELEMENTARY[]...) -> primo elemento;
            # pin dichiarato come ARRAY concreto -> si passa l'array intero
            if "[]" in dt and decl and "ARRAY" in decl.upper():
                rif = var + ("[1]" if "[1.." in decl else "[0]")
            if pin["is_input"] or pin.get("inout"):
                if decl:
                    variabili[var] = decl
                p[nome if pin["is_input"] else "OUT:" + nome] = rif
                if pin.get("inout") and not pin["is_input"]:
                    p["OUT:" + nome] = rif
            else:
                n_out += 1
                ovar = "o%03d_%s" % (n_out, var.replace("t_", "").replace("arr", "A"))
                if decl:
                    variabili[ovar] = decl
                    p["OUT:" + nome] = ovar
        if not ok:
            continue

        fam = famiglia_di(tipo)
        elem = {("fb" if info["kind"] == "FB" else "f"): tipo, "p": p}
        if info["kind"] == "FB":
            inst = "I_" + tipo.replace("@", "at_").replace(".", "_").replace("\\", "_")
            elem["inst"] = inst
            variabili[inst] = tipo
        sezioni["Batt_" + fam].append({"cmt": "COLLAUDO %s (usi %d)" % (tipo, info.get("usi", 0)),
                                        "chain": ["t_EN", elem]})

    variabili["t_EN"] = "BOOL"
    spec = {
        "out_dir": os.path.join(D, "out"),
        "variables": [{"name": n, "type": t} for n, t in sorted(variabili.items())],
        "sections": dict(sezioni),
    }
    dest = os.path.join(D, "batteria_spec.json")
    json.dump(spec, open(dest, "w", encoding="utf-8"), indent=1, ensure_ascii=False)

    print("spec:", dest)
    for s, rung in sorted(sezioni.items()):
        print("  %-24s %d rung" % (s, len(rung)))
    print("variabili da dichiarare:", len(variabili))
    if saltati:
        print("SALTATI (datatype non mappato):")
        for t, dt in saltati:
            print("   %-24s %s" % (t, dt))

if __name__ == "__main__":
    main()


