"""VORLAGE FÜR DEIN EIGENES TOOL

So geht's:
    1. Kopiere diese Datei und gib der Kopie einen eigenen Namen OHNE Unterstrich vorne,
       z. B. tools/wuerfel.py   (Dateien mit "_" am Anfang werden ignoriert)
    2. Ändere den Funktionsnamen, die Parameter, den Docstring und den Code.
    3. Prüfe dein Tool:     python check_tools.py
    4. Probier es aus:      python main.py
"""

from agent import tool  # <- diese Zeile brauchst du immer


@tool  # <- macht aus der Funktion ein Tool. Mit @tool(bestaetigen=True) wird vorher nachgefragt.
def mein_tool(text: str, anzahl: int = 1) -> dict:
    """HIER STEHT, WAS DAS TOOL MACHT UND WANN DAS LLM ES BENUTZEN SOLL.
    Das ist der wichtigste Teil: Das LLM liest nur diesen Text, nicht deinen Code!

    text: Was bedeutet dieser Parameter? Am besten mit Beispiel, z. B. "Hallo"
    anzahl: Was bedeutet dieser Parameter? (hat einen Standardwert, ist also optional)
    """
    # Hier kommt dein Code hin. Erlaubte Parameter-Typen: str, int, float, bool, list, dict
    ergebnis = text * anzahl

    # Gib am besten ein dict zurück – das LLM bekommt es als JSON zu sehen.
    return {"ergebnis": ergebnis}
