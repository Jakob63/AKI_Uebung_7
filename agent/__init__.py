"""
Der "Motor" der Vorlage.

Diesen Ordner musst du NICHT ändern, um eigene Tools oder Agents zu bauen.
Du darfst ihn aber gerne lesen – jede Datei ist kommentiert:

    tool_registry.py  ->  @tool-Decorator, macht aus einer Python-Funktion ein Tool
    agenten.py        ->  lädt die Agent-Konfigurationen aus dem Ordner agents/
    provider.py       ->  liest die .env-Datei und baut die Verbindung zum LLM
    loop.py           ->  der eigentliche Agent-Loop (LLM fragen -> Tool ausführen -> wiederholen)
"""

from .tool_registry import tool

__all__ = ["tool"]
