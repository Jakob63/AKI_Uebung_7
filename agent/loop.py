"""
Der Agent-Loop – das Herzstück.

Ablauf:
    1. Wir schicken dem LLM das Gespräch + die Liste der Tools, die es benutzen darf.
    2. Das LLM antwortet entweder
         a) mit normalem Text           -> fertig, Antwort an den Nutzer
         b) mit "Bitte ruf Tool X auf"  -> WIR führen Tool X aus (nicht das LLM!),
                                           hängen das Ergebnis ans Gespräch an
                                           und fragen das LLM erneut (zurück zu 1.)
    3. Nach höchstens MAX_RUNDEN Runden brechen wir ab (Schutz vor Endlosschleifen).

Dieser Code gibt selbst NICHTS aus (kein print, kein input). Stattdessen bekommt er
"Callbacks" übergeben – Funktionen, die das Terminal (main.py) bzw. die Web-UI (web.py)
jeweils auf ihre Art umsetzen. So nutzen beide Oberflächen denselben Loop.
"""

import json
import logging

import openai

from .provider import client_erstellen
from .tool_registry import ALLE_TOOLS, tool_ausfuehren

logger = logging.getLogger(__name__)

MAX_RUNDEN = 8


class AgentFehler(Exception):
    """Fehler bei der Kommunikation mit dem LLM – die Meldung erklärt, was zu tun ist."""


def nachrichten_aufbauen(agent: dict, verlauf: list[dict]) -> list[dict]:
    """Baut die Nachrichtenliste: GENAU EINE system-Nachricht ganz vorne, dann der Chatverlauf.

    Leere Nachrichten werden weggelassen – manche Modelle (z. B. Mistral) lehnen sie mit
    "400 Invalid request" ab.
    """
    nachrichten = [{"role": "system", "content": agent["system_prompt"]}]
    for n in verlauf:
        if n.get("role") not in ("user", "assistant") or not (n.get("content") or "").strip():
            continue
        if nachrichten[-1]["role"] == n["role"]:
            # Zwei Nachrichten derselben Rolle hintereinander -> zusammenfassen (mögen manche Modelle nicht)
            nachrichten[-1]["content"] += "\n\n" + n["content"]
        else:
            nachrichten.append({"role": n["role"], "content": n["content"]})
    return nachrichten


def antworten(
    agent: dict,
    verlauf: list[dict],
    on_tool_call=None,
    bestaetigen=None,
    on_llm_anfrage=None,
) -> str:
    """Lässt den Agent auf den Chatverlauf antworten und gibt die Antwort als Text zurück.

    agent:          Konfiguration aus agents/ (siehe agenten.py)
    verlauf:        Liste von {"role": "user"/"assistant", "content": "..."}
    on_tool_call:   wird nach jedem Tool-Aufruf aufgerufen: on_tool_call(name, argumente, ergebnis)
    bestaetigen:    wird VOR "gefährlichen" Tools aufgerufen: bestaetigen(name, argumente) -> True/False
    on_llm_anfrage: (zum Debuggen) bekommt vor jeder LLM-Anfrage die komplette Nachrichtenliste
    """
    client, modell = client_erstellen()
    nachrichten = nachrichten_aufbauen(agent, verlauf)
    tool_schemas = [ALLE_TOOLS[name]["schema"] for name in agent["tools"]]

    for _runde in range(MAX_RUNDEN):
        if on_llm_anfrage:
            on_llm_anfrage(nachrichten)

        # --- 1. LLM fragen -------------------------------------------------------------
        anfrage = {"model": modell, "messages": nachrichten}
        if tool_schemas:  # ohne Tools den Parameter ganz weglassen (sonst meckern manche APIs)
            anfrage["tools"] = tool_schemas
            anfrage["tool_choice"] = "auto"
        antwort = llm_fragen(client, anfrage, nachrichten)
        nachricht = antwort.choices[0].message

        # --- 2a. Keine Tool-Aufrufe -> fertige Antwort ---------------------------------
        if not nachricht.tool_calls:
            return nachricht.content or "(Das Modell hat eine leere Antwort geschickt.)"

        # --- 2b. Tool-Aufrufe ----------------------------------------------------------
        # Zuerst die Anfrage des Modells selbst ins Gespräch übernehmen. Jede spätere
        # tool-Nachricht muss sich mit ihrer tool_call_id auf genau diese Anfrage beziehen.
        nachrichten.append({
            "role": "assistant",
            "content": nachricht.content or "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                }
                for tc in nachricht.tool_calls
            ],
        })

        for tc in nachricht.tool_calls:
            name = tc.function.name
            ergebnis, argumente = tool_aufruf_bearbeiten(name, tc.function.arguments, agent, bestaetigen)
            if on_tool_call:
                on_tool_call(name, argumente, ergebnis)
            nachrichten.append({"role": "tool", "tool_call_id": tc.id, "content": ergebnis})
        # ... und dann wieder nach oben: LLM mit den Ergebnissen erneut fragen

    return (
        f"Ich habe nach {MAX_RUNDEN} Runden mit Tool-Aufrufen abgebrochen, ohne fertig zu werden. "
        f"Versuch es mit einer einfacheren oder genaueren Frage."
    )


def tool_aufruf_bearbeiten(name: str, argumente_json: str, agent: dict, bestaetigen) -> tuple[str, dict]:
    """Prüft einen einzelnen Tool-Aufruf, fragt ggf. nach und führt ihn aus.

    Gibt (ergebnis_als_text, argumente) zurück.
    """
    # LLMs liefern manchmal kaputtes JSON -> nicht abstürzen, sondern dem Modell Bescheid sagen
    try:
        argumente = json.loads(argumente_json or "{}")
        if not isinstance(argumente, dict):
            raise ValueError("Argumente sind kein JSON-Objekt")
    except ValueError as fehler:
        text = f"Die Argumente waren kein gültiges JSON ({fehler}). Bitte noch einmal korrekt aufrufen."
        return json.dumps({"error": text}, ensure_ascii=False), {"_roh": argumente_json}

    # Das Modell darf nur Tools benutzen, die dieser Agent auch hat
    if name not in agent["tools"]:
        return json.dumps({"error": f"Das Tool '{name}' steht dir nicht zur Verfügung."}, ensure_ascii=False), argumente

    # "Gefährliche" Tools erst nach Bestätigung ausführen
    if ALLE_TOOLS[name]["bestaetigen"]:
        erlaubt = bestaetigen(name, argumente) if bestaetigen else False
        if not erlaubt:
            return json.dumps({
                "status": "nicht ausgeführt",
                "grund": "Der Nutzer hat diese Aktion (noch) nicht bestätigt. "
                         "Beschreibe dem Nutzer kurz, was du tun möchtest, und frage, "
                         "ob du es tun sollst.",
            }, ensure_ascii=False), argumente

    return tool_ausfuehren(name, argumente), argumente


def llm_fragen(client, anfrage: dict, nachrichten: list[dict]):
    """Schickt die Anfrage ans LLM und übersetzt typische Fehler in verständliche Meldungen."""
    try:
        antwort = client.chat.completions.create(**anfrage)
    except openai.AuthenticationError as e:
        raise AgentFehler("Der API-Key wurde abgelehnt. Prüfe den Schlüssel in der Datei .env.") from e
    except openai.PermissionDeniedError as e:
        raise AgentFehler(
            "Zugriff verweigert. Prüfe den API-Key in .env – ist er vollständig kopiert und noch gültig?"
        ) from e
    except openai.NotFoundError as e:
        raise AgentFehler(
            f"Modell oder Adresse nicht gefunden ({anfrage['model']}). Prüfe AI_MODEL/AI_BASE_URL in .env."
        ) from e
    except openai.RateLimitError as e:
        raise AgentFehler(
            "Zu viele Anfragen (Rate-Limit). Warte kurz und versuch es nochmal – "
            "kostenlose Kontingente sind begrenzt."
        ) from e
    except openai.APIConnectionError as e:
        raise AgentFehler("Keine Verbindung zum LLM-Anbieter. Bist du online?") from e
    except openai.BadRequestError as e:
        # Für die Fehlersuche: die Reihenfolge der Rollen loggen (ohne Inhalte)
        rollen = " -> ".join(n["role"] for n in nachrichten)
        logger.exception("LLM hat die Anfrage abgelehnt. Rollenfolge: %s", rollen)
        raise AgentFehler(
            f"Das LLM hat die Anfrage abgelehnt: {e.message}\n"
            f"(Details stehen in agent.log. Rollenfolge: {rollen})"
        ) from e
    except openai.APIStatusError as e:
        if e.status_code == 410:
            raise AgentFehler(
                f"Das Modell '{anfrage['model']}' wurde vom Anbieter abgeschaltet. "
                f"Trage in .env bei AI_MODEL= ein anderes Modell ein (siehe README, 'Andere Sprachmodelle')."
            ) from e
        logger.exception("Unerwarteter API-Fehler")
        raise AgentFehler(f"Fehler vom LLM-Anbieter: {e}") from e
    except openai.APIError as e:
        logger.exception("Unerwarteter API-Fehler")
        raise AgentFehler(f"Fehler vom LLM-Anbieter: {e}") from e

    # Schickt der Anbieter kein JSON zurück, gibt die openai-Bibliothek einfach den rohen Text
    # zurück statt einen Fehler zu melden. Das fangen wir hier ab.
    if isinstance(antwort, str) or not getattr(antwort, "choices", None):
        roh = str(antwort)
        logger.error("Unerwartete Antwort vom LLM-Anbieter (Modell %s):\n%s", anfrage["model"], roh[:3000])
        anfang = " ".join(roh.split())[:200]
        raise AgentFehler(
            "Der LLM-Anbieter hat eine Antwort in einem unerwarteten Format geschickt.\n"
            "Mögliche Ursachen: Ein WLAN mit Anmeldeseite (erst im Browser anmelden), eine falsche "
            "AI_BASE_URL in .env oder ein Problem beim Anbieter.\n"
            f"Anfang der Antwort: {anfang or '(leer)'}\n"
            "(Die komplette Antwort steht in agent.log.)"
        )
    return antwort
