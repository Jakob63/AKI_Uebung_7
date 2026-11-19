"""
Web-Oberfläche (Chat im Browser) – benutzt denselben Agent-Loop wie main.py.

Starten:
    python web.py
Dann öffnet sich der Browser (sonst die Adresse aufrufen, die im Terminal steht).
Beenden: im Terminal Strg + C drücken.

Diese Datei musst du NICHT ändern: Neue Tools und neue Agents erscheinen automatisch.

Wie funktioniert das? Python bringt einen kleinen Webserver mit (http.server).
Der liefert die Seite agent/webseite.html aus. Wenn du im Browser eine Nachricht
abschickst, ruft die Seite /api/chat auf – und hier läuft dann der Agent-Loop.
"""

import json
import logging
import os
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

if sys.version_info < (3, 10):
    sys.exit("❌ Du brauchst Python 3.10 oder neuer. Installiere eine neuere Version von python.org.")

os.chdir(Path(__file__).parent)  # immer im Projektordner arbeiten
sys.stdout.reconfigure(encoding="utf-8")

from agent.agenten import STANDARD_AGENT, KonfigFehler, agent_laden, agenten_auflisten  # noqa: E402
from agent.loop import AgentFehler, antworten  # noqa: E402
from agent.provider import ProviderFehler  # noqa: E402
from agent.tool_registry import ALLE_TOOLS, LADEFEHLER, tool_ausfuehren, tools_laden  # noqa: E402

logging.basicConfig(filename="agent.log", level=logging.INFO, encoding="utf-8",
                    format="%(asctime)s %(levelname)s %(name)s: %(message)s")

WEBSEITE = Path("agent/webseite.html")
JA_ANTWORTEN = ("ja", "j", "yes", "y", "ok", "jo", "ja bitte", "mach")


# ---------------------------------------------------------------------------
# Was der Server kann
# ---------------------------------------------------------------------------

def agenten_infos() -> dict:
    """Alle Agents für das Auswahlmenü + Warnungen über kaputte Tools."""
    agenten = []
    for kennung in agenten_auflisten():
        try:
            a = agent_laden(kennung)
            agenten.append({"kennung": kennung, "name": a["name"],
                            "beschreibung": a["beschreibung"], "tools": a["tools"]})
        except Exception as fehler:
            agenten.append({"kennung": kennung, "name": kennung, "fehler": str(fehler), "tools": []})
    return {
        "agenten": agenten,
        "standard": STANDARD_AGENT,
        "warnungen": [f"tools/{d} konnte nicht geladen werden: {f}" for d, f in LADEFEHLER.items()],
    }


def chat(anfrage: dict, senden):
    """Beantwortet eine Chat-Nachricht. Jedes Ereignis (Tool-Aufruf, Antwort …) wird sofort
    mit senden({...}) an den Browser geschickt – so sieht man live, was der Agent tut."""
    try:
        agent = agent_laden(anfrage.get("agent") or STANDARD_AGENT)
    except Exception as fehler:
        senden({"typ": "fehler", "text": str(fehler)})
        return

    nachricht = (anfrage.get("nachricht") or "").strip()
    verlauf = [n for n in anfrage.get("verlauf", []) if isinstance(n, dict)]
    offene = anfrage.get("offene_aktionen") or []

    # --- Hat der Nutzer eine offene Aktion bestätigt? ------------------------------
    an_llm = nachricht
    if offene and nachricht.lower().rstrip("!.") in JA_ANTWORTEN:
        infos = []
        for aktion in offene:
            name, argumente = aktion.get("name"), aktion.get("argumente") or {}
            # Nur Tools ausführen, die dieser Agent hat und die eine Bestätigung brauchen
            if name not in agent["tools"] or not ALLE_TOOLS[name]["bestaetigen"]:
                continue
            ergebnis = tool_ausfuehren(name, argumente)
            senden({"typ": "tool", "name": name, "argumente": argumente, "ergebnis": ergebnis})
            infos.append(f"{name}({json.dumps(argumente, ensure_ascii=False)}) -> {ergebnis}")
        if infos:
            # Zusatzinfo als Teil der user-Nachricht (nicht als zweite system-Nachricht!)
            an_llm = (f"{nachricht}\n\n[Info: Ich habe bestätigt. Folgende Aktionen wurden ausgeführt: "
                      f"{'; '.join(infos)}. Bitte nicht noch einmal ausführen.]")

    # --- Callbacks für den Agent-Loop ----------------------------------------------
    neue_aktionen = []

    def bestaetigen(name, argumente):
        # Im Browser können wir nicht mitten im Loop "j/n" fragen. Deshalb merken wir uns die
        # Aktion und sagen erstmal "nein". Antwortet der Nutzer danach mit "ja", führen wir sie aus.
        neue_aktionen.append({"name": name, "argumente": argumente})
        return False

    def tool_anzeigen(name, argumente, ergebnis):
        if {"name": name, "argumente": argumente} in neue_aktionen:
            return  # wartet noch auf "ja" -> dafür gibt es unten einen eigenen Hinweis
        senden({"typ": "tool", "name": name, "argumente": argumente, "ergebnis": ergebnis})

    # --- Agent-Loop starten (derselbe wie im Terminal) -------------------------------
    try:
        antwort = antworten(agent, verlauf + [{"role": "user", "content": an_llm}],
                            on_tool_call=tool_anzeigen, bestaetigen=bestaetigen)
    except (AgentFehler, ProviderFehler) as fehler:
        senden({"typ": "fehler", "text": str(fehler)})
        return
    except Exception:
        logging.exception("Unerwarteter Fehler in der Web-UI")
        senden({"typ": "fehler", "text": "Unerwarteter Fehler – Details stehen in agent.log."})
        return

    senden({"typ": "antwort", "text": antwort})
    if neue_aktionen:
        senden({"typ": "bestaetigung", "aktionen": neue_aktionen})


# ---------------------------------------------------------------------------
# Der Webserver (Technik – hier musst du nichts verstehen)
# ---------------------------------------------------------------------------

class Anfragen(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self.antwort_senden(200, WEBSEITE.read_bytes(), "text/html; charset=utf-8")
        elif self.path == "/api/agenten":
            self.antwort_senden(200, json.dumps(agenten_infos(), ensure_ascii=False).encode(),
                                "application/json; charset=utf-8")
        else:
            self.antwort_senden(404, b"Nicht gefunden", "text/plain")

    def do_POST(self):
        if self.path != "/api/chat":
            self.antwort_senden(404, b"Nicht gefunden", "text/plain")
            return
        laenge = int(self.headers.get("Content-Length", 0))
        anfrage = json.loads(self.rfile.read(laenge) or b"{}")

        # Antwort Stück für Stück schicken: eine JSON-Zeile pro Ereignis
        self.send_response(200)
        self.send_header("Content-Type", "application/x-ndjson; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()

        def senden(ereignis: dict):
            try:
                self.wfile.write((json.dumps(ereignis, ensure_ascii=False) + "\n").encode())
                self.wfile.flush()
            except OSError:
                pass  # Browser-Tab wurde geschlossen – egal

        chat(anfrage, senden)
        self.close_connection = True

    def antwort_senden(self, status: int, inhalt: bytes, typ: str):
        self.send_response(status)
        self.send_header("Content-Type", typ)
        self.send_header("Content-Length", str(len(inhalt)))
        self.end_headers()
        self.wfile.write(inhalt)

    def log_message(self, *args):
        pass  # keine Zeile pro Anfrage im Terminal anzeigen


class Server(ThreadingHTTPServer):
    # Unter Windows würde "reuse" erlauben, dass zwei Server denselben Port belegen
    allow_reuse_address = os.name != "nt"
    daemon_threads = True


def server_starten(port: int = 7860, browser_oeffnen: bool = True) -> ThreadingHTTPServer:
    tools_laden()
    for versuch in range(20):  # ist der Port belegt, nehmen wir den nächsten
        try:
            server = Server(("127.0.0.1", port + versuch), Anfragen)
            break
        except OSError:
            continue
    else:
        sys.exit("❌ Konnte keinen freien Port finden. Läuft web.py vielleicht schon?")

    adresse = f"http://127.0.0.1:{server.server_address[1]}"
    print(f"🌐 Web-UI läuft auf {adresse}")
    print("   (Beenden mit Strg + C)")
    for warnung in agenten_infos()["warnungen"]:
        print(f"⚠️  {warnung}")
    if browser_oeffnen:
        threading.Timer(0.5, webbrowser.open, args=[adresse]).start()
    return server


if __name__ == "__main__":
    server = server_starten()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nTschüss! 👋")
