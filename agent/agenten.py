"""
Lädt die Agent-Konfigurationen aus dem Ordner agents/.

Ein Agent ist hier einfach eine Python-Datei mit ein paar Variablen:

    NAME = "Lernhelfer"
    BESCHREIBUNG = "Hilft beim Lernen"            (optional)
    SYSTEM_PROMPT = "Du bist ein Lernhelfer ..."
    TOOLS = ["rechner", "uhrzeit"]                 (oder TOOLS = "alle", oder TOOLS = [])

Der Dateiname (ohne .py) ist die Kennung, mit der man den Agent startet:
    python main.py lernhelfer
"""

import importlib.util
from pathlib import Path

from .tool_registry import ALLE_TOOLS

STANDARD_AGENT = "allrounder"


class KonfigFehler(Exception):
    """Fehler in einer Agent-Datei – die Meldung erklärt, was zu tun ist."""


def agent_laden(kennung: str, ordner: str | Path = "agents") -> dict:
    """Liest agents/<kennung>.py und gibt die Konfiguration als Dict zurück."""
    datei = Path(ordner) / f"{kennung}.py"
    if not datei.exists():
        vorhanden = ", ".join(agenten_auflisten(ordner)) or "(keine)"
        raise KonfigFehler(
            f"Den Agent '{kennung}' gibt es nicht (Datei {datei} fehlt).\n"
            f"Vorhandene Agents: {vorhanden}"
        )

    # Datei als Python-Modul einlesen
    spec = importlib.util.spec_from_file_location(f"agents.{kennung}", datei)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)

    if not hasattr(modul, "SYSTEM_PROMPT"):
        raise KonfigFehler(f"In {datei} fehlt die Variable SYSTEM_PROMPT = \"...\".")

    tools = getattr(modul, "TOOLS", [])
    if tools == "alle":
        tools = list(ALLE_TOOLS)

    unbekannt = [t for t in tools if t not in ALLE_TOOLS]
    if unbekannt:
        raise KonfigFehler(
            f"In {datei} stehen Tools, die es nicht gibt: {', '.join(unbekannt)}\n"
            f"Verfügbare Tools: {', '.join(ALLE_TOOLS) or '(keine)'}\n"
            f"Tipp: Der Tool-Name ist der Funktionsname, nicht der Dateiname."
        )

    return {
        "kennung": kennung,
        "name": getattr(modul, "NAME", kennung),
        "beschreibung": getattr(modul, "BESCHREIBUNG", ""),
        "system_prompt": modul.SYSTEM_PROMPT.strip(),
        "tools": list(tools),
    }


def agenten_auflisten(ordner: str | Path = "agents") -> list[str]:
    """Alle Agent-Kennungen (Dateinamen ohne .py), z. B. ["allrounder", "lernhelfer"]."""
    return sorted(
        p.stem for p in Path(ordner).glob("*.py") if not p.name.startswith("_")
    )
