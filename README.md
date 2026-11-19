# 🤖 Agent-Vorlage: Baue deinen eigenen KI-Agent mit Tools

Ein Sprachmodell (LLM) wie ChatGPT kann eigentlich nur eines: **Text schreiben**.
Es weiß nicht, wie spät es ist, kann nicht zuverlässig rechnen und kennt das Wetter von morgen nicht.

Ein **Agent** ist ein Programm, das dem Sprachmodell **Werkzeuge (Tools)** gibt.
Das Modell entscheidet selbst, wann es welches Werkzeug braucht – und unser Programm führt es aus.

In dieser Vorlage ist das ganze "Drumherum" schon fertig. **Du schreibst nur noch:**

- 🔧 **Tools** – kleine Python-Funktionen (ein Tool = eine Funktion), und
- 🧑‍🏫 **Agents** – eine Datei mit einer Rollenbeschreibung und einer Liste erlaubter Tools.

> **Keine Programmiererfahrung?** Kein Problem. Folge einfach den Schritten der Reihe nach.
> Alles, was du eintippen musst, steht in grauen Kästen. Am Ende gibt es einen
> [Mini-Spickzettel zu Python](#-mini-spickzettel-python).

---

## Inhalt

1. [Einmalig einrichten](#1-einmalig-einrichten) (ca. 15 Minuten)
2. [Den Agent starten](#2-den-agent-starten)
3. [Dein erstes eigenes Tool](#3-dein-erstes-eigenes-tool)
4. [Dein eigener Agent](#4-dein-eigener-agent)
5. [Experimente für den Kurs](#5-experimente-für-den-kurs)
6. [Wie funktioniert das eigentlich?](#6-wie-funktioniert-das-eigentlich)
7. [Hilfe, es geht nicht!](#7-hilfe-es-geht-nicht)

---

## 1. Einmalig einrichten

### Schritt 1: Python installieren

Prüfe zuerst, ob Python schon da ist. Öffne ein **Terminal**:

- **Windows:** Startmenü → „PowerShell“ eintippen → öffnen
- **Mac:** Programme → Dienstprogramme → „Terminal“

Tippe ein und drücke Enter:

```
python --version
```

Steht da `Python 3.10` oder eine höhere Zahl (auch die allerneueste Version ist in Ordnung)? Super, weiter mit Schritt 2.
Sonst: Python von [python.org/downloads](https://www.python.org/downloads/) installieren.
**Windows: Beim Installieren unbedingt den Haken bei „Add python.exe to PATH“ setzen!**
Danach das Terminal schließen und neu öffnen.

> Auf dem Mac heißt der Befehl manchmal `python3` statt `python` (und `pip3` statt `pip`).

### Schritt 2: Projekt herunterladen, in den Ordner wechseln und Pakete installieren

Projekt herunterladen (im Terminal, in dem Ordner, in dem das Projekt landen soll):

```
git clone https://github.com/Jakob63/AKI_Uebung_7.git
cd AKI_Uebung_7
```

> Kein `git` installiert? Dann auf der [GitHub-Seite](https://github.com/Jakob63/AKI_Uebung_7)
> auf den grünen Knopf **Code → Download ZIP** klicken und die ZIP-Datei entpacken.
> Danach im Terminal in den entpackten Ordner wechseln: `cd ` tippen (mit Leerzeichen!),
> den Ordner aus dem Explorer/Finder ins Terminal **ziehen** und Enter drücken.

> 💡 In VS Code oder PyCharm geht's noch einfacher: Ordner öffnen, unten das Terminal benutzen –
> das ist automatisch im richtigen Ordner.

Jetzt eine eigene „Spielwiese“ für die Python-Pakete anlegen (eine *virtuelle Umgebung*)
und die Pakete installieren:

**Windows (PowerShell):**
```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

**Mac / Linux:**
```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Wenn vorne im Terminal jetzt `(.venv)` steht, hat es geklappt. Die Installation dauert meist unter einer Minute.

> ⚠️ **Windows-Fehler „Ausführung von Skripts ist auf diesem System deaktiviert“?**
> Das ist ein Windows-Schutz für PowerShell. So geht's trotzdem:
>
> 1. Diese Zeile eingeben, mit `J` (oder `Y`) bestätigen und danach die `activate`-Zeile nochmal ausführen:
>    ```
>    Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
>    ```
>    Das musst du nur **einmal** machen, es gilt dauerhaft für deinen Windows-Benutzer.
> 2. Klappt das nicht (z. B. Meldung über *Gruppenrichtlinien* auf Hochschul- oder Firmenrechnern),
>    erlaube es nur für das aktuelle Terminal (muss in jedem neuen Terminal wiederholt werden):
>    ```
>    Set-ExecutionPolicy -Scope Process Bypass
>    .venv\Scripts\activate
>    ```
> 3. Oder benutze die **Eingabeaufforderung** statt PowerShell – dort gibt es die Sperre nicht.
>    In VS Code: im Terminal oben rechts auf den kleinen Pfeil neben dem **+** klicken →
>    **„Command Prompt“** wählen, dann:
>    ```
>    .venv\Scripts\activate.bat
>    ```
>
> ⚠️ **Wichtig:** Jedes Mal, wenn du ein neues Terminal öffnest, musst du die Umgebung wieder
> aktivieren (`.venv\Scripts\activate` bzw. `source .venv/bin/activate`).

### Schritt 3: Einen kostenlosen Schlüssel (API-Key) besorgen

Das Sprachmodell läuft nicht auf deinem Rechner, sondern bei einem Anbieter im Internet.
Dafür brauchst du einen Schlüssel. Wir nehmen **NVIDIA** – kostenlos mit einem NVIDIA-Account.

1. Öffne [build.nvidia.com](https://build.nvidia.com) und klicke oben rechts auf **Login**.
   Falls du noch keinen Account hast: kostenlos registrieren (E-Mail genügt).
2. Nach dem Anmelden: Klicke auf **Get API Key** (oben rechts oder auf der Seite eines Modells)
   und dann auf **Generate Key**.
3. Den Schlüssel (fängt mit `nvapi-` an) **kopieren**. Du siehst ihn nur einmal!

### Schritt 4: Den Schlüssel eintragen

1. Kopiere die Datei `.env.example` im Projektordner und nenne die Kopie **`.env`**
   (genau so: Punkt am Anfang, keine Endung).
   Im Terminal geht das so: Windows `copy .env.example .env` · Mac `cp .env.example .env`
2. Öffne `.env` mit einem Texteditor (VS Code, Notepad …) und ersetze `hier_deinen_key_einfuegen`
   durch deinen Schlüssel:
   ```
   NVIDIA_API_KEY=nvapi-AbC123...
   ```
3. Speichern.

> 🔒 Die `.env` ist **geheim**. Nicht weitergeben, nicht hochladen, nicht in Screenshots zeigen.

### Schritt 5: Testen, ob alles da ist

```
python check_tools.py
```

Das zeigt alle Tools, alle Agents und ob dein Schlüssel eingetragen ist.

Jetzt noch testen, ob die Verbindung zum Sprachmodell klappt:

```
python check_tools.py --llm
```

Steht unten „✅ Das Sprachmodell hat das Tool benutzt“, bist du startklar! 🎉

---

## 2. Den Agent starten

### Variante A: Im Terminal

```
python main.py
```

Jetzt kannst du chatten. Probier z. B.:

- `Wie spät ist es?`
- `Was ist 17,5 % von 2389?`
- `Wie wird das Wetter morgen in Konstanz?`
- `Merk dir: Am Freitag ist Mathe-Übung`

Du siehst bei jeder Antwort, **welche Tools der Agent benutzt** hat (🔧) und was dabei herauskam.
Bei manchen Tools (z. B. Notiz speichern) **fragt** das Programm vorher nach: `[j/n]`.

Einen bestimmten Agent startest du so:

```
python main.py lernhelfer
python main.py reiseplaner
python main.py ohne_tools
```

| Eingabe im Chat | Was passiert |
|---|---|
| `exit` | Beenden |
| `neu` | Gespräch vergessen und neu anfangen |

Neugierig, was **genau** ans Sprachmodell geschickt wird? Starte mit `--debug`:

```
python main.py --debug
```

### Variante B: Im Browser

```
python web.py
```

Der Browser öffnet sich automatisch (sonst die Adresse aufrufen, die im Terminal steht, meist [http://127.0.0.1:7860](http://127.0.0.1:7860)).
Oben wählst du den Agent aus. Die aufklappbaren Kästen „🔧 Tool benutzt“ zeigen, was der Agent getan hat.
Wenn der Agent etwas Wichtiges tun will (z. B. eine Notiz speichern), fragt er nach – klicke dann auf **Ja, ausführen** oder antworte mit **ja**.

Beenden: im Terminal **Strg + C** drücken.

> Beide Varianten benutzen **genau denselben** Agent. Neue Tools und Agents tauchen automatisch in beiden auf.

---

## 3. Dein erstes eigenes Tool

Wir bauen ein **Würfel-Tool**. Sprachmodelle können nämlich nicht wirklich zufällig würfeln.

### Schritt 1: Neue Datei anlegen

Lege im Ordner `tools/` eine neue Datei **`wuerfel.py`** an
(oder kopiere `tools/_vorlage.py` und benenne sie um).

### Schritt 2: Diesen Code hineinschreiben

```python
import random

from agent import tool


@tool
def wuerfeln(seiten: int = 6, anzahl: int = 1) -> dict:
    """Würfelt mit einem oder mehreren Würfeln. Benutze dieses Tool immer,
    wenn der Nutzer würfeln möchte oder eine Zufallszahl braucht.

    seiten: Wie viele Seiten hat der Würfel? Normal sind 6
    anzahl: Wie viele Würfel sollen geworfen werden?
    """
    wuerfe = []
    for i in range(anzahl):
        wuerfe.append(random.randint(1, seiten))
    return {"wuerfe": wuerfe, "summe": sum(wuerfe)}
```

### Schritt 3: Prüfen

```
python check_tools.py wuerfeln
```

Du siehst jetzt **genau das, was das Sprachmodell über dein Tool erfährt**.
Es sieht deinen Code nicht – nur den Namen, den Beschreibungstext und die Parameter!

### Schritt 4: Ausprobieren

```
python main.py
```

Frag: `Würfel mal mit zwei zwanzigseitigen Würfeln!` – und schau, ob 🔧 `wuerfeln` aufgerufen wird.

### Was bedeuten die Teile?

```python
@tool                                   # ← macht aus der Funktion ein Tool (Pflicht!)
def wuerfeln(seiten: int = 6, ...):     # ← Name des Tools + Parameter mit Typ
    """Würfelt mit ...                  # ← BESCHREIBUNG: Das liest das Sprachmodell!
                                        #   Hier steht WAS das Tool tut und WANN es benutzt wird.
    seiten: Wie viele Seiten ...        # ← Beschreibung eines Parameters ("name: text")
    """
    ...                                 # ← dein Code
    return {"summe": ...}               # ← Ergebnis, am besten ein dict
```

**Die Regeln für ein Tool:**

| Regel | Warum? |
|---|---|
| `@tool` direkt über `def` | Sonst wird die Funktion nicht als Tool erkannt. |
| `from agent import tool` oben in der Datei | Sonst kennt Python `@tool` nicht. |
| Jeder Parameter hat einen Typ: `str` (Text), `int` (ganze Zahl), `float` (Kommazahl), `bool` (ja/nein), `list`, `dict` | Das Sprachmodell muss wissen, was es übergeben soll. |
| Parameter mit `= Wert` sind **optional** | Ohne Standardwert muss das Modell den Parameter immer angeben. |
| Docstring (`"""..."""`) mit guter Beschreibung | **Das Wichtigste!** Je besser die Beschreibung, desto besser benutzt das Modell dein Tool. |
| Pro Parameter eine Zeile `name: Beschreibung` im Docstring | Am besten mit Beispiel, z. B. `stadt: Name der Stadt, z. B. "Konstanz"` |
| `return` gibt ein `dict`, eine `list` oder einen Text zurück | Das wird dem Modell als Ergebnis gezeigt. |
| Funktionsnamen nur mit Kleinbuchstaben, Zahlen und `_`, keine Umlaute | Manche Anbieter lehnen andere Zeichen ab. |
| Tool soll etwas verändern/löschen? → `@tool(bestaetigen=True)` | Dann wird vorher nachgefragt. |

> 💡 **Fehler sind erlaubt!** Wenn in deinem Tool etwas schiefgeht (z. B. `raise ValueError("Stadt nicht gefunden")`),
> stürzt nicht alles ab. Das Sprachmodell bekommt die Fehlermeldung und kann darauf reagieren.

### Ideen für weitere Tools

| Idee | Tipp |
|---|---|
| Passwort-Generator | `random.choice("abc...")` in einer Schleife |
| Einheiten-Umrechner (km ↔ Meilen, °C ↔ °F) | einfache Rechnung |
| Countdown bis zu den Semesterferien | `from datetime import date`, `(date(2027, 2, 1) - date.today()).days` |
| Wikipedia-Zusammenfassung | `httpx.get(f"https://de.wikipedia.org/api/rest_v1/page/summary/{begriff}", timeout=10).json()["extract"]` – schau dir `tools/wetter.py` als Beispiel an |
| Witze-Sammlung | Liste mit Witzen + `random.choice(...)` |
| To-do-Liste | wie `tools/notizen.py`, aber mit „erledigt“-Funktion |

---

## 4. Dein eigener Agent

Ein Agent besteht nur aus **einer Rollenbeschreibung** (System-Prompt) und einer **Liste von Tools**.
Mit denselben Tools kannst du also ganz verschiedene Agents bauen.

### Schritt 1: Datei anlegen

Kopiere `agents/_vorlage.py` und nenne die Kopie z. B. **`agents/spielleiter.py`**.

### Schritt 2: Ausfüllen

```python
NAME = "Spielleiter"

BESCHREIBUNG = "Leitet ein kleines Würfelspiel."

SYSTEM_PROMPT = """
Du bist ein lustiger Spielleiter für ein Würfelspiel.
Regeln:
- Antworte auf Deutsch und mit viel Begeisterung.
- Würfle IMMER mit dem Tool "wuerfeln", erfinde niemals selbst Zahlen.
- Wer die höhere Summe hat, gewinnt die Runde. Zähle die Punkte mit.
"""

TOOLS = ["wuerfeln", "uhrzeit"]
```

- **`SYSTEM_PROMPT`**: Wer ist der Agent? Wie soll er sich verhalten? **Wann soll er welches Tool benutzen?**
- **`TOOLS`**: die **Funktionsnamen** der Tools (nicht die Dateinamen!).
  `python check_tools.py` zeigt dir alle Namen. `TOOLS = "alle"` erlaubt alle, `TOOLS = []` keines.

### Schritt 3: Starten

```
python main.py spielleiter
```

oder `python web.py` und im Auswahlmenü „spielleiter“ wählen.

---

## 5. Experimente für den Kurs

1. **Ohne Tools:** `python main.py ohne_tools` → frag „Wie spät ist es?“ und „Wie wird das Wetter morgen?“.
   Was macht das Modell? Erfindet es etwas (*halluziniert* es)? Dann dasselbe mit `python main.py`.
2. **Das Modell wählt selbst:** Frag den Allrounder Verschiedenes. Wann nimmt er welches Tool? Wann keins?
3. **Schlechte Beschreibung:** Ändere in `tools/rechner.py` den Docstring in `"""Macht was."""`.
   Rechnet das Modell jetzt noch mit dem Tool? (Danach wieder zurückändern!)
4. **Parameter & Internet:** Frag nach dem Wetter für 3 Tage in zwei Städten. Wie oft wird `wetter` aufgerufen?
5. **Fehlerfall:** Frag nach dem Wetter in „Xyzabc“. Das Tool meldet einen Fehler – wie reagiert der Agent?
6. **Eigener Agent:** Baue einen spezialisierten Agent (z. B. Mensa-Agent, Lern-Agent, Spielleiter).
7. **Diskussion:** Welche Tools sollten nur nach Bestätigung laufen (`bestaetigen=True`)?
   Was sollte ein Agent niemals ohne Nachfrage tun dürfen?
8. **Blick unter die Haube:** `python main.py --debug` – wie sieht das Gespräch aus, das wirklich ans Modell geht?
   Findest du die Tool-Ergebnisse (`"role": "tool"`)?

---

## 6. Wie funktioniert das eigentlich?

```
 Du ──► Agent-Loop ──► Sprachmodell: "Hier ist das Gespräch + diese Tools kannst du benutzen"
            ▲                  │
            │                  ▼
            │          Antwort A: normaler Text  ──► fertig, wird dir angezeigt
            │          Antwort B: "Bitte ruf Tool X mit {…} auf"
            │                  │
            │                  ▼
            └──── unser Programm führt Tool X aus, hängt das Ergebnis ans Gespräch an
                  und fragt das Sprachmodell nochmal  (höchstens 8 Runden)
```

**Wichtig:** Das Sprachmodell führt **nie selbst** Code aus. Es *bittet* nur darum, ein Tool aufzurufen.
Ausgeführt wird es von unserem Programm – deshalb können wir auch vorher nachfragen.

### Was liegt wo?

```
├── README.md            ← diese Anleitung
├── .env.example         ← Vorlage für deinen geheimen Schlüssel (→ kopieren nach .env)
├── requirements.txt     ← welche Python-Pakete gebraucht werden
├── main.py              ← Chat im Terminal:  python main.py [agent]
├── web.py               ← Chat im Browser:   python web.py
├── check_tools.py       ← prüft Tools & Agents: python check_tools.py
│
├── tools/               ← ✏️ HIER kommen deine Tools rein
│   ├── _vorlage.py      ←    zum Kopieren
│   ├── uhrzeit.py       ←    einfachstes Beispiel (keine Parameter)
│   ├── rechner.py       ←    Taschenrechner
│   ├── notizen.py       ←    Notizen speichern/lesen (mit Nachfrage!)
│   └── wetter.py        ←    echte Internet-API (Open-Meteo, ohne Key)
│
├── agents/              ← ✏️ HIER konfigurierst du deine Agents
│   ├── _vorlage.py      ←    zum Kopieren
│   ├── allrounder.py    ←    darf alle Tools (Standard)
│   ├── ohne_tools.py    ←    zum Vergleich: gar keine Tools
│   ├── lernhelfer.py    ←    Beispiel: spezialisierter Agent
│   └── reiseplaner.py   ←    Beispiel: kombiniert Uhrzeit + Wetter + Notizen
│
└── agent/               ← ⚙️ der "Motor" – musst du nicht ändern (darfst aber reinschauen)
    ├── tool_registry.py ←    @tool: macht aus einer Funktion ein Tool (Beschreibung fürs Modell)
    ├── agenten.py       ←    liest die Dateien in agents/
    ├── provider.py      ←    Verbindung zum Sprachmodell (liest .env)
    ├── loop.py          ←    der Agent-Loop aus dem Bild oben
    └── webseite.html    ←    die Chat-Seite, die web.py im Browser anzeigt
```

Dateien, deren Name mit `_` beginnt, werden ignoriert – deshalb sind die Vorlagen keine echten Tools/Agents.

### Andere Sprachmodelle

In der `.env` kannst du den Anbieter wechseln (Details stehen als Kommentar in `.env.example`):

| `AI_PROVIDER=` | Was | Schlüssel |
|---|---|---|
| `nvidia` (Standard) | [NVIDIA](https://build.nvidia.com), Standard-Modell `nvidia/nemotron-3.5-lightning-30b-a3b` | `NVIDIA_API_KEY` |
| `groq` | [Groq](https://console.groq.com/keys), Standard-Modell `openai/gpt-oss-120b` | `GROQ_API_KEY` |
| `custom` | alles, was „OpenAI-kompatibel“ ist, z. B. [Ollama](https://ollama.com) auf dem eigenen Rechner | `AI_API_KEY`, `AI_BASE_URL`, `AI_MODEL` |

Mit `AI_MODEL=...` kannst du ein anderes Modell wählen (bei NVIDIA findest du alle Modelle auf
[build.nvidia.com/models](https://build.nvidia.com/models)). Nicht jedes Modell kann gut mit Tools umgehen –
wenn der Agent Tools ignoriert oder komische Antworten gibt, wechsle zurück zum Standard.
Mit `python check_tools.py --llm` kannst du ein Modell schnell testen.

> Anbieter schalten ältere Modelle regelmäßig ab. Kommt die Meldung „Das Modell … wurde vom Anbieter
> abgeschaltet“, trage bei `AI_MODEL=` ein aktuelles Modell ein.

---

## 7. Hilfe, es geht nicht!

| Meldung / Problem | Lösung |
|---|---|
| `python` wird nicht gefunden | Python installieren (Schritt 1). Mac: `python3` benutzen. Windows: Bei der Installation „Add to PATH“ anhaken. |
| `ModuleNotFoundError: No module named 'openai'` (oder `dotenv`, `httpx`) | Umgebung nicht aktiv: `.venv\Scripts\activate` (Win) bzw. `source .venv/bin/activate` (Mac), ggf. nochmal `pip install -r requirements.txt` |
| „Ausführung von Skripts ist deaktiviert“ | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` – geht das nicht: `Set-ExecutionPolicy -Scope Process Bypass` oder die Eingabeaufforderung mit `.venv\Scripts\activate.bat` benutzen (Details in Schritt 2) |
| „Keine .env-Datei gefunden“ | `.env.example` kopieren und Kopie `.env` nennen (Schritt 4). Achtung: Windows versteckt manchmal Dateiendungen – die Datei darf nicht `.env.txt` heißen. |
| „Kein API-Key gefunden“ | In `.env` steht noch `hier_deinen_key_einfuegen` – echten Schlüssel eintragen und speichern. |
| „Der API-Key wurde abgelehnt“ / „Zugriff verweigert“ | Schlüssel falsch oder unvollständig kopiert → neuen Schlüssel erstellen (Schritt 3). |
| „Das Modell … wurde vom Anbieter abgeschaltet“ | In `.env` bei `AI_MODEL=` ein aktuelles Modell eintragen (siehe [Andere Sprachmodelle](#andere-sprachmodelle)). |
| „Zu viele Anfragen (Rate-Limit)“ | Das kostenlose Kontingent ist kurz aufgebraucht – ein paar Minuten warten. |
| Mein Tool taucht nicht auf | `python check_tools.py` ausführen. Häufige Ursachen: `@tool` vergessen, Datei liegt nicht in `tools/`, Dateiname beginnt mit `_`, Tippfehler (die Meldung sagt dir die Zeile). |
| „Tools, die es nicht gibt“ beim Agent | In `TOOLS = [...]` muss der **Funktionsname** stehen, nicht der Dateiname. |
| Das Modell benutzt mein Tool nicht | Docstring verbessern: **was** macht das Tool und **wann** soll es benutzt werden? Im `SYSTEM_PROMPT` des Agents erwähnen. |
| Irgendein anderer Fehler | Die Datei `agent.log` enthält Details. Oder mit `python main.py --debug` starten. |

---

## 🐍 Mini-Spickzettel Python

```python
# Kommentar – wird von Python ignoriert

name = "Konstanz"          # str   = Text (immer in Anführungszeichen)
anzahl = 3                 # int   = ganze Zahl
preis = 2.50               # float = Kommazahl (mit PUNKT!)
fertig = True              # bool  = True oder False
staedte = ["Ulm", "Lindau"]                 # list  = Liste
person = {"name": "Kim", "alter": 19}       # dict  = "Steckbrief" aus Schlüssel: Wert

def begruessen(name: str) -> str:   # Funktion mit Parameter "name" vom Typ Text
    return "Hallo " + name          # return = das Ergebnis der Funktion

if anzahl > 2:             # Bedingung (Doppelpunkt + Einrückung beachten!)
    print("viele")

for stadt in staedte:      # Schleife: einmal für jedes Element
    print(stadt)
```

**Einrückung ist wichtig!** Alles, was zu einer Funktion, einem `if` oder einer Schleife gehört,
ist um 4 Leerzeichen eingerückt.

Viel Spaß beim Bauen! 🚀
