"""Das einfachste Tool: keine Parameter, gibt nur Datum und Uhrzeit zurück.

Sprachmodelle wissen nicht, wie spät es ist – sie haben keine Uhr.
Mit diesem Tool können sie nachschauen.
"""

from datetime import datetime

from agent import tool

WOCHENTAGE = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]


@tool
def uhrzeit() -> dict:
    """Gibt das heutige Datum, den Wochentag und die aktuelle Uhrzeit zurück.
    Benutze dieses Tool immer, wenn es um "heute", "jetzt", "morgen" oder die Uhrzeit geht.
    """
    jetzt = datetime.now()
    return {
        "datum": jetzt.strftime("%d.%m.%Y"),
        "wochentag": WOCHENTAGE[jetzt.weekday()],
        "uhrzeit": jetzt.strftime("%H:%M"),
    }
