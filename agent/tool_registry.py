"""
Tool-Registry: Hier wird aus einer normalen Python-Funktion ein "Tool", das das LLM benutzen kann.

Das LLM kann keinen Python-Code lesen. Es braucht eine Beschreibung im JSON-Format
("JSON-Schema"): Wie heißt das Tool, was macht es, welche Parameter hat es?
Diese Beschreibung bauen wir hier AUTOMATISCH aus

    - dem Funktionsnamen          ->  Name des Tools
    - dem Docstring (erste Zeilen) ->  Beschreibung des Tools
    - den Type-Hints (str, int …) ->  Typen der Parameter
    - den Zeilen "name: text"     ->  Beschreibung der Parameter

Beispiel:

    @tool
    def wetter(stadt: str, tage: int = 1) -> dict:
        '''Gibt die Wettervorhersage für eine Stadt zurück.

        stadt: Name der Stadt, z. B. "Konstanz"
        tage: Anzahl Tage der Vorhersage (1-7)
        '''
"""

import importlib
import inspect
import json
import logging
import sys
import traceback
import typing
from pathlib import Path

logger = logging.getLogger(__name__)

# Alle registrierten Tools: Name -> Infos (Funktion, Schema, bestaetigen)
ALLE_TOOLS: dict[str, dict] = {}

# Fehler, die beim Laden der Dateien in tools/ aufgetreten sind (Dateiname -> Fehlermeldung)
LADEFEHLER: dict[str, str] = {}

# Ergebnisse, die länger sind, werden gekürzt (spart Tokens und verwirrt das LLM weniger)
MAX_ERGEBNIS_LAENGE = 4000

# Welcher Python-Typ wird zu welchem JSON-Typ?
TYP_UEBERSETZUNG = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    list: "array",
    dict: "object",
}


# ---------------------------------------------------------------------------
# 1) Der Decorator @tool
# ---------------------------------------------------------------------------

def tool(funktion=None, *, bestaetigen: bool = False):
    """Markiert eine Funktion als Tool.

    Zwei Schreibweisen sind erlaubt:
        @tool                      -> normales Tool, wird sofort ausgeführt
        @tool(bestaetigen=True)    -> vor dem Ausführen wird der Nutzer gefragt
    """

    def registrieren(f):
        name = f.__name__
        if name in ALLE_TOOLS:
            alte_datei = ALLE_TOOLS[name]["datei"]
            raise ValueError(
                f"Es gibt schon ein Tool mit dem Namen '{name}' (in {alte_datei}). "
                f"Bitte benenne eine der beiden Funktionen um."
            )
        ALLE_TOOLS[name] = {
            "funktion": f,
            "schema": schema_erzeugen(f),
            "bestaetigen": bestaetigen,
            "datei": inspect.getsourcefile(f),
        }
        return f  # Die Funktion bleibt eine ganz normale Funktion

    # "@tool" ohne Klammern: Python übergibt die Funktion direkt
    if funktion is not None:
        return registrieren(funktion)
    # "@tool(bestaetigen=True)": Python ruft erst tool(...) auf und dann das Ergebnis mit der Funktion
    return registrieren


# ---------------------------------------------------------------------------
# 2) Schema aus Funktion erzeugen
# ---------------------------------------------------------------------------

def docstring_zerlegen(f) -> tuple[str, dict[str, str]]:
    """Teilt den Docstring in (Tool-Beschreibung, {parameter: beschreibung})."""
    docstring = inspect.getdoc(f) or ""
    parameter_namen = set(inspect.signature(f).parameters)

    beschreibung_zeilen = []
    parameter_texte = {}
    for zeile in docstring.splitlines():
        if ":" in zeile:
            vorne, hinten = zeile.split(":", 1)
            if vorne.strip() in parameter_namen:
                parameter_texte[vorne.strip()] = hinten.strip()
                continue
        beschreibung_zeilen.append(zeile)

    beschreibung = "\n".join(beschreibung_zeilen).strip()
    return beschreibung, parameter_texte


def typ_zu_json(typ) -> dict:
    """Übersetzt einen Python-Type-Hint in ein (kleines) JSON-Schema."""
    # Literal["a", "b"]  ->  feste Auswahl ("enum")
    if typing.get_origin(typ) is typing.Literal:
        werte = list(typing.get_args(typ))
        return {"type": TYP_UEBERSETZUNG.get(type(werte[0]), "string"), "enum": werte}
    # list[str] -> Liste von Strings
    if typing.get_origin(typ) is list:
        argumente = typing.get_args(typ)
        schema = {"type": "array"}
        if argumente:
            schema["items"] = typ_zu_json(argumente[0])
        return schema
    if typing.get_origin(typ) is dict:
        return {"type": "object"}
    if typ in TYP_UEBERSETZUNG:
        return {"type": TYP_UEBERSETZUNG[typ]}
    # Unbekannter oder fehlender Type-Hint -> wir nehmen "string" (check_tools.py warnt davor)
    return {"type": "string"}


def schema_erzeugen(f) -> dict:
    """Baut die Tool-Beschreibung im OpenAI-Format, die das LLM zu sehen bekommt."""
    beschreibung, parameter_texte = docstring_zerlegen(f)
    signatur = inspect.signature(f)
    typen = typing.get_type_hints(f)

    eigenschaften = {}
    pflicht = []
    for name, parameter in signatur.parameters.items():
        eigenschaft = typ_zu_json(typen.get(name))
        text = parameter_texte.get(name, "")
        if parameter.default is inspect.Parameter.empty:
            pflicht.append(name)  # kein Standardwert -> Pflichtparameter
        else:
            text = f"{text} (optional, Standard: {parameter.default!r})".strip()
        if text:
            eigenschaft["description"] = text
        eigenschaften[name] = eigenschaft

    return {
        "type": "function",
        "function": {
            "name": f.__name__,
            "description": beschreibung or f"Tool {f.__name__} (keine Beschreibung)",
            "parameters": {
                "type": "object",
                "properties": eigenschaften,
                "required": pflicht,
            },
        },
    }


# ---------------------------------------------------------------------------
# 3) Alle Dateien im Ordner tools/ automatisch laden
# ---------------------------------------------------------------------------

def tools_laden(ordner: str | Path = "tools") -> dict[str, dict]:
    """Importiert jede .py-Datei in tools/. Dabei laufen die @tool-Decorators und registrieren sich.

    Dateien, die mit "_" anfangen (z. B. _vorlage.py), werden übersprungen.
    """
    ordner = Path(ordner).resolve()
    projekt_ordner = str(ordner.parent)
    if projekt_ordner not in sys.path:
        sys.path.insert(0, projekt_ordner)

    for datei in sorted(ordner.glob("*.py")):
        if datei.name.startswith("_"):
            continue
        modulname = f"{ordner.name}.{datei.stem}"
        if modulname in sys.modules:
            continue  # schon geladen
        try:
            importlib.import_module(modulname)
        except ModuleNotFoundError as fehler:
            # Ein Paket fehlt (z. B. httpx) -> meist ist die Umgebung nicht aktiv oder nicht installiert
            LADEFEHLER[datei.name] = (
                f"Das Python-Paket '{fehler.name}' fehlt. Ist die Umgebung aktiv (.venv)? "
                f"Dann einmal 'pip install -r requirements.txt' ausführen. "
                f"(Für ein eigenes Paket: 'pip install {fehler.name}')"
            )
            logger.error("Fehler beim Laden von %s\n%s", datei, traceback.format_exc())
        except Exception as fehler:
            # Ein kaputtes Tool soll nicht die ganze Vorlage lahmlegen -> merken und weitermachen
            LADEFEHLER[datei.name] = f"{type(fehler).__name__}: {fehler}"
            logger.error("Fehler beim Laden von %s\n%s", datei, traceback.format_exc())
    return ALLE_TOOLS


# ---------------------------------------------------------------------------
# 4) Ein Tool ausführen (wird vom Agent-Loop aufgerufen)
# ---------------------------------------------------------------------------

def argumente_anpassen(f, argumente: dict) -> dict:
    """LLMs schicken manchmal "42" statt 42 oder erfinden Parameter. Das bügeln wir hier aus."""
    signatur = inspect.signature(f)
    typen = typing.get_type_hints(f)
    ergebnis = {}
    for name, wert in argumente.items():
        if name not in signatur.parameters:
            continue  # Parameter, den es gar nicht gibt -> ignorieren
        typ = typen.get(name)
        try:
            if typ is int and not isinstance(wert, int):
                wert = int(float(wert))
            elif typ is float and not isinstance(wert, (int, float)):
                wert = float(wert)
            elif typ is bool and isinstance(wert, str):
                wert = wert.strip().lower() in ("true", "ja", "1", "yes")
            elif typ is str and not isinstance(wert, str):
                wert = str(wert)
        except (ValueError, TypeError):
            pass  # dann eben unverändert lassen – die Funktion meldet ggf. selbst einen Fehler
        ergebnis[name] = wert

    fehlende = [
        name for name, p in signatur.parameters.items()
        if p.default is inspect.Parameter.empty and name not in ergebnis
    ]
    if fehlende:
        raise ValueError(f"Es fehlen Pflicht-Parameter: {', '.join(fehlende)}")
    return ergebnis


def ergebnis_als_text(ergebnis) -> str:
    """Das LLM bekommt nur Text. Dicts/Listen werden zu JSON, alles andere zu einem String."""
    if isinstance(ergebnis, str):
        text = ergebnis
    else:
        try:
            text = json.dumps(ergebnis, ensure_ascii=False)
        except (TypeError, ValueError):
            text = str(ergebnis)  # z. B. ein set oder ein eigenes Objekt
    if len(text) > MAX_ERGEBNIS_LAENGE:
        text = text[:MAX_ERGEBNIS_LAENGE] + " … [Ergebnis gekürzt]"
    return text


def tool_ausfuehren(name: str, argumente: dict) -> str:
    """Führt ein Tool aus und gibt IMMER einen String zurück – auch bei Fehlern.

    Wichtig: Fehler werden nicht "geworfen", sondern als {"error": ...} zurückgegeben.
    So kann das LLM reagieren ("Die Stadt gibt es nicht, meintest du …?"),
    statt dass der ganze Agent abstürzt.
    """
    if name not in ALLE_TOOLS:
        return json.dumps({"error": f"Ein Tool namens '{name}' gibt es nicht."}, ensure_ascii=False)

    f = ALLE_TOOLS[name]["funktion"]
    try:
        ergebnis = f(**argumente_anpassen(f, argumente))
        return ergebnis_als_text(ergebnis)
    except Exception as fehler:
        logger.exception("Tool %s ist mit Argumenten %s abgestürzt", name, argumente)
        return json.dumps(
            {"error": f"{type(fehler).__name__}: {fehler}"}, ensure_ascii=False
        )
