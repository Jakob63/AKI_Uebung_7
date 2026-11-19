"""
Web-Oberfläche (Chat im Browser) – benutzt denselben Agent-Loop wie main.py.

Starten:
    python web.py
Dann öffnet sich der Browser (sonst: http://127.0.0.1:7860 aufrufen).

Diese Datei musst du NICHT ändern: Neue Tools und neue Agents erscheinen automatisch.
"""

import json
import logging
import os
import sys
from pathlib import Path

os.chdir(Path(__file__).parent)  # immer im Projektordner arbeiten
sys.stdout.reconfigure(encoding="utf-8")

import gradio as gr  # noqa: E402

from agent.agenten import STANDARD_AGENT, KonfigFehler, agent_laden, agenten_auflisten  # noqa: E402
from agent.loop import AgentFehler, antworten  # noqa: E402
from agent.provider import ProviderFehler  # noqa: E402
from agent.tool_registry import LADEFEHLER, tool_ausfuehren, tools_laden  # noqa: E402

logging.basicConfig(filename="agent.log", level=logging.INFO, encoding="utf-8",
                    format="%(asctime)s %(levelname)s %(name)s: %(message)s")

tools_laden()

# Aktionen, die auf ein "ja" des Nutzers warten (@tool(bestaetigen=True)).
# Einfach eine globale Liste – die Web-UI läuft ja nur lokal für dich.
offene_aktionen: list[dict] = []


def als_text(argumente: dict) -> str:
    return json.dumps(argumente, ensure_ascii=False)


def tool_nachricht(name: str, argumente: dict, ergebnis: str) -> gr.ChatMessage:
    """Ein aufklappbarer Kasten im Chat, der einen Tool-Aufruf zeigt."""
    return gr.ChatMessage(
        role="assistant",
        content=f"**Argumente:** `{als_text(argumente)}`\n\n**Ergebnis:**\n```\n{ergebnis[:1500]}\n```",
        metadata={"title": f"🔧 Tool benutzt: {name}", "status": "done"},
    )


def verlauf_umwandeln(gradio_verlauf: list) -> list[dict]:
    """Gradio speichert den Chat in einem eigenen Format. Wir behalten nur die echten
    Nachrichten (keine Tool-Kästen) und machen daraus {"role": ..., "content": "..."}."""
    verlauf = []
    for n in gradio_verlauf:
        if (n.get("metadata") or {}).get("title"):
            continue  # Tool-Kasten oder Hinweis -> nicht ans LLM schicken
        inhalt = n.get("content")
        if isinstance(inhalt, list):  # neuere Gradio-Versionen: Liste von Textstücken
            inhalt = " ".join(t.get("text", "") for t in inhalt if isinstance(t, dict))
        if isinstance(inhalt, str):
            verlauf.append({"role": n["role"], "content": inhalt})
    return verlauf


def chat(nachricht: str, gradio_verlauf: list, agent_kennung: str):
    """Wird von Gradio bei jeder neuen Nachricht aufgerufen. Gibt die Chat-Blasen zurück."""
    global offene_aktionen
    try:
        agent = agent_laden(agent_kennung)
    except KonfigFehler as fehler:
        return f"❌ {fehler}"

    anzeige = []  # alles, was wir gleich im Chat anzeigen

    # --- Callbacks für den Agent-Loop ------------------------------------------
    neue_aktionen = []

    def tool_anzeigen(name, argumente, ergebnis):
        if {"name": name, "argumente": argumente} in neue_aktionen:
            return  # wartet noch auf "ja" -> dafür zeigen wir unten einen eigenen Hinweis
        anzeige.append(tool_nachricht(name, argumente, ergebnis))

    def bestaetigen(name, argumente):
        # Im Browser können wir nicht mitten im Loop "j/n" fragen. Deshalb merken wir uns die
        # Aktion und sagen erstmal "nein". Antwortet der Nutzer danach mit "ja", führen wir sie aus.
        neue_aktionen.append({"name": name, "argumente": argumente})
        return False

    # --- Hat der Nutzer eine offene Aktion mit "ja" bestätigt? -------------------
    an_llm = nachricht
    if offene_aktionen and nachricht.strip().lower().rstrip("!.") in ("ja", "j", "yes", "ok", "jo"):
        infos = []
        for aktion in offene_aktionen:
            ergebnis = tool_ausfuehren(aktion["name"], aktion["argumente"])
            tool_anzeigen(aktion["name"], aktion["argumente"], ergebnis)
            infos.append(f"{aktion['name']}({als_text(aktion['argumente'])}) -> {ergebnis}")
        # Zusätzliche Infos schicken wir als Teil der user-Nachricht (nicht als zweite system-Nachricht!)
        an_llm = (f"{nachricht}\n\n[Info: Ich habe bestätigt. Folgende Aktionen wurden ausgeführt: "
                  f"{'; '.join(infos)}. Bitte nicht noch einmal ausführen.]")
    offene_aktionen = []

    # --- Agent-Loop starten (derselbe wie im Terminal) ---------------------------
    verlauf = verlauf_umwandeln(gradio_verlauf) + [{"role": "user", "content": an_llm}]
    try:
        antwort = antworten(agent, verlauf, on_tool_call=tool_anzeigen, bestaetigen=bestaetigen)
    except (AgentFehler, ProviderFehler) as fehler:
        return anzeige + [gr.ChatMessage(role="assistant", content=f"❌ {fehler}")]
    except Exception:
        logging.exception("Unerwarteter Fehler in der Web-UI")
        return anzeige + [gr.ChatMessage(role="assistant", content="❌ Unerwarteter Fehler – Details stehen in agent.log.")]

    anzeige.append(gr.ChatMessage(role="assistant", content=antwort))

    if neue_aktionen:
        offene_aktionen = neue_aktionen
        liste = "\n".join(f"- `{a['name']}({als_text(a['argumente'])})`" for a in neue_aktionen)
        anzeige.append(gr.ChatMessage(
            role="assistant",
            content=f"Der Agent möchte Folgendes ausführen:\n{liste}\n\n"
                    f"Antworte mit **ja**, um es auszuführen. Jede andere Antwort bricht ab.",
            metadata={"title": "⚠️ Bestätigung nötig"},
        ))
    return anzeige


def agent_info(kennung: str) -> str:
    """Kurzer Infotext über dem Chat: Was kann der gewählte Agent?"""
    try:
        a = agent_laden(kennung)
    except KonfigFehler as fehler:
        return f"❌ {fehler}"
    tools = ", ".join(f"`{t}`" for t in a["tools"]) or "(keine)"
    return f"**{a['name']}** – {a['beschreibung']}  \nTools: {tools}"


def agent_gewechselt(kennung: str):
    """Beim Agent-Wechsel: Chat leeren und Infotext aktualisieren."""
    global offene_aktionen
    offene_aktionen = []
    return agent_info(kennung), [], []


# ---------------------------------------------------------------------------
# Die Oberfläche zusammenbauen
# ---------------------------------------------------------------------------

with gr.Blocks(title="Agent-Vorlage") as app:
    gr.Markdown("# 🤖 Agent-Vorlage\nWähle einen Agent und chatte los. "
                "Aufklappbare Kästen 🔧 zeigen, welche Tools der Agent benutzt hat.")
    for datei, fehler in LADEFEHLER.items():
        gr.Markdown(f"⚠️ **tools/{datei}** konnte nicht geladen werden: `{fehler}` "
                    f"(Tipp: `python check_tools.py`)")

    kennungen = agenten_auflisten()
    auswahl = gr.Dropdown(
        choices=kennungen,
        value=STANDARD_AGENT if STANDARD_AGENT in kennungen else kennungen[0],
        label="Agent",
    )
    info = gr.Markdown(agent_info(auswahl.value))

    chat_fenster = gr.ChatInterface(
        fn=chat,
        additional_inputs=[auswahl],
        chatbot=gr.Chatbot(height=500, label="Chat"),
        textbox=gr.Textbox(placeholder="Schreib eine Nachricht …", submit_btn=True),
    )
    auswahl.change(agent_gewechselt, inputs=auswahl,
                   outputs=[info, chat_fenster.chatbot, chat_fenster.chatbot_state])


if __name__ == "__main__":
    app.launch(inbrowser=True)
