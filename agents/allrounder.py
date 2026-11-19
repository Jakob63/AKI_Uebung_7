# Ein Agent, der ALLE Tools aus dem Ordner tools/ benutzen darf.
# Das ist der Standard-Agent, wenn du einfach "python main.py" startest.
# Neue Tools sind hier also automatisch dabei.

NAME = "Allrounder"

BESCHREIBUNG = "Darf alle Tools benutzen – gut zum Ausprobieren neuer Tools."

SYSTEM_PROMPT = """
Du bist ein hilfsbereiter Assistent für Studierende der HTWG Konstanz.
Antworte immer auf Deutsch, kurz und freundlich.
Wenn ein Tool dir bei einer Frage helfen kann, benutze es, statt zu raten.
"""

TOOLS = "alle"
