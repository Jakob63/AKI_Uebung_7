# VORLAGE FÜR DEINEN EIGENEN AGENT
#
# So geht's:
#   1. Kopiere diese Datei und gib der Kopie einen Namen OHNE Unterstrich vorne,
#      z. B. agents/mensa_agent.py
#   2. Fülle die vier Variablen unten aus.
#   3. Starte deinen Agent:   python main.py mensa_agent
#      (oder in der Web-UI im Auswahlmenü)

# Anzeigename
NAME = "Mein Agent"

# Ein Satz, wofür der Agent da ist (wird in der Web-UI angezeigt)
BESCHREIBUNG = "Beschreibe hier kurz, was dein Agent kann."

# Der System-Prompt: WER ist der Agent und an welche REGELN hält er sich?
# Tipp: Schreib hier auch rein, WANN er welches Tool benutzen soll.
SYSTEM_PROMPT = """
Du bist ...

Regeln:
- Antworte auf Deutsch.
- ...
"""

# Welche Tools darf der Agent benutzen? Das sind die FUNKTIONSNAMEN aus dem Ordner tools/.
# Alle verfügbaren Namen zeigt dir:   python check_tools.py
# TOOLS = "alle"  gibt ihm alle Tools,  TOOLS = []  gar keine.
TOOLS = ["uhrzeit", "rechner"]
