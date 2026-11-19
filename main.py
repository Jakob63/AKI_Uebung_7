"""
Terminal-Chat mit einem Agent.

Starten:
    python main.py                 -> Standard-Agent (allrounder)
    python main.py lernhelfer      -> ein bestimmter Agent aus dem Ordner agents/
    python main.py --debug         -> zeigt zusätzlich alle Nachrichten, die ans LLM gehen

Im Chat:
    exit   -> beenden
    neu    -> Gespräch von vorne beginnen
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

if sys.version_info < (3, 10):
    sys.exit("❌ Du brauchst Python 3.10 oder neuer. Installiere eine neuere Version von python.org.")

# Immer im Projektordner arbeiten, egal von wo aus das Programm gestartet wurde
os.chdir(Path(__file__).parent)
sys.stdout.reconfigure(encoding="utf-8")  # damit Umlaute unter Windows richtig angezeigt werden

from agent.agenten import STANDARD_AGENT, KonfigFehler, agent_laden  # noqa: E402
from agent.loop import AgentFehler, antworten  # noqa: E402
from agent.provider import ProviderFehler, einstellungen_lesen  # noqa: E402
from agent.tool_registry import LADEFEHLER, tools_laden  # noqa: E402

# Fehler-Details landen in agent.log (für die Fehlersuche)
logging.basicConfig(filename="agent.log", level=logging.INFO, encoding="utf-8",
                    format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def kuerzen(text: str, laenge: int = 300) -> str:
    return text if len(text) <= laenge else text[:laenge] + " …"


# ---------------------------------------------------------------------------
# Die Callbacks: So "spricht" der Agent-Loop mit dem Terminal
# ---------------------------------------------------------------------------

def tool_anzeigen(name: str, argumente: dict, ergebnis: str):
    """Wird nach jedem Tool-Aufruf aufgerufen – damit man SIEHT, was der Agent tut."""
    args_text = ", ".join(f"{k}={v!r}" for k, v in argumente.items())
    print(f"   🔧 Tool: {name}({args_text})")
    print(f"      ↳ Ergebnis: {kuerzen(ergebnis)}")


def nachfragen(name: str, argumente: dict) -> bool:
    """Wird vor 'gefährlichen' Tools aufgerufen (@tool(bestaetigen=True))."""
    args_text = ", ".join(f"{k}={v!r}" for k, v in argumente.items())
    antwort = input(f"   ⚠️  Der Agent möchte {name}({args_text}) ausführen. Ausführen? [j/n] ")
    return antwort.strip().lower() in ("j", "ja", "y", "yes")


def debug_anzeigen(nachrichten: list[dict]):
    """Nur mit --debug: zeigt die komplette Nachrichtenliste, die gleich ans LLM geht."""
    print("\n----- DEBUG: Nachrichten an das LLM -----")
    print(json.dumps(nachrichten, ensure_ascii=False, indent=2))
    print("-----------------------------------------\n")


# ---------------------------------------------------------------------------
# Hauptprogramm
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Chatte im Terminal mit einem Agent.")
    parser.add_argument("agent", nargs="?", default=STANDARD_AGENT, help="Name des Agents (Datei in agents/)")
    parser.add_argument("--debug", action="store_true", help="alle Nachrichten an das LLM anzeigen")
    optionen = parser.parse_args()

    tools_laden()
    for datei, fehler in LADEFEHLER.items():
        print(f"⚠️  Das Tool in tools/{datei} konnte nicht geladen werden: {fehler}")
        print("    (Tipp: python check_tools.py zeigt mehr Details)\n")

    try:
        agent = agent_laden(optionen.agent)
        einstellungen = einstellungen_lesen()
    except (KonfigFehler, ProviderFehler) as fehler:
        print(f"❌ {fehler}")
        sys.exit(1)

    print(f"🤖 Agent: {agent['name']}  (Modell: {einstellungen['modell']})")
    print(f"   Tools: {', '.join(agent['tools']) or '(keine)'}")
    print("   Tippe 'exit' zum Beenden oder 'neu' für ein neues Gespräch.\n")

    verlauf = []  # Das bisherige Gespräch: [{"role": "user", "content": ...}, {"role": "assistant", ...}]
    while True:
        try:
            frage = input("Du: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not frage:
            continue
        if frage.lower() in ("exit", "quit", "q"):
            break
        if frage.lower() == "neu":
            verlauf = []
            print("(Neues Gespräch gestartet)\n")
            continue

        verlauf.append({"role": "user", "content": frage})
        try:
            antwort = antworten(
                agent,
                verlauf,
                on_tool_call=tool_anzeigen,
                bestaetigen=nachfragen,
                on_llm_anfrage=debug_anzeigen if optionen.debug else None,
            )
        except (AgentFehler, ProviderFehler) as fehler:
            print(f"❌ {fehler}\n")
            verlauf.pop()  # die Frage war nicht erfolgreich -> wieder entfernen
            continue
        except Exception:
            logging.exception("Unerwarteter Fehler")
            print("❌ Unerwarteter Fehler – die Details stehen in der Datei agent.log.\n")
            verlauf.pop()
            continue

        verlauf.append({"role": "assistant", "content": antwort})
        print(f"\n{agent['name']}: {antwort}\n")

    print("Tschüss! 👋")


if __name__ == "__main__":
    main()
