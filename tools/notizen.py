"""Notizen in eine Textdatei schreiben, lesen und löschen.

Hier siehst du @tool(bestaetigen=True): Tools, die etwas VERÄNDERN, sollten nicht ohne
Nachfrage laufen. Vor dem Ausführen wird der Nutzer gefragt.
Das reine Lesen ist harmlos und läuft ohne Nachfrage.
"""

from pathlib import Path

from agent import tool

NOTIZ_DATEI = Path("notizen.txt")


@tool
def notizen_lesen() -> list:
    """Liest alle gespeicherten Notizen des Nutzers. Gibt eine Liste zurück (leer, wenn es keine gibt)."""
    if not NOTIZ_DATEI.exists():
        return []
    zeilen = NOTIZ_DATEI.read_text(encoding="utf-8").splitlines()
    return [z for z in zeilen if z.strip()]


@tool(bestaetigen=True)
def notiz_speichern(text: str) -> str:
    """Speichert eine neue Notiz dauerhaft (wird an die Notizdatei angehängt).

    text: Der Inhalt der Notiz, ein kurzer Satz
    """
    with NOTIZ_DATEI.open("a", encoding="utf-8") as datei:
        datei.write(text.replace("\n", " ").strip() + "\n")
    return f"Notiz gespeichert: {text}"


@tool(bestaetigen=True)
def notizen_loeschen() -> str:
    """Löscht ALLE gespeicherten Notizen unwiderruflich."""
    anzahl = len(notizen_lesen())
    NOTIZ_DATEI.unlink(missing_ok=True)
    return f"{anzahl} Notiz(en) gelöscht."
