"""
Prüft deine Tools und Agents – OHNE das Sprachmodell zu fragen (braucht also keinen API-Key).

Starten:
    python check_tools.py           -> alle Tools prüfen und ihre Beschreibung fürs LLM anzeigen
    python check_tools.py wetter    -> nur ein bestimmtes Tool anzeigen

Zeigt für jedes Tool das automatisch erzeugte JSON-Schema – also genau das, was das LLM
über dein Tool erfährt. Und es warnt vor typischen Fehlern.
"""

import inspect
import json
import logging
import os
import sys
import typing
from pathlib import Path

if sys.version_info < (3, 10):
    sys.exit("❌ Du brauchst Python 3.10 oder neuer. Installiere eine neuere Version von python.org.")

os.chdir(Path(__file__).parent)
sys.stdout.reconfigure(encoding="utf-8")
logging.basicConfig(filename="agent.log", level=logging.INFO, encoding="utf-8")  # Details ins Log

from agent.agenten import KonfigFehler, agent_laden, agenten_auflisten  # noqa: E402
from agent.tool_registry import (  # noqa: E402
    ALLE_TOOLS, LADEFEHLER, TYP_UEBERSETZUNG, docstring_zerlegen, tools_laden,
)

ERLAUBTE_RUECKGABE = (str, int, float, bool, dict, list, type(None))


def tool_pruefen(name: str, info: dict) -> list[str]:
    """Gibt eine Liste von Warnungen für ein Tool zurück (leer = alles gut)."""
    f = info["funktion"]
    warnungen = []
    typen = typing.get_type_hints(f)
    beschreibung, parameter_texte = docstring_zerlegen(f)

    if not inspect.getdoc(f):
        warnungen.append("Kein Docstring! Das LLM weiß nicht, wofür das Tool da ist. "
                         'Schreib direkt unter "def ...:" einen Text in """dreifachen Anführungszeichen""".')
    elif len(beschreibung) < 20:
        warnungen.append("Die Beschreibung ist sehr kurz. Erkläre, WAS das Tool macht und WANN es benutzt werden soll.")

    for p in inspect.signature(f).parameters:
        typ = typen.get(p)
        if typ is None:
            warnungen.append(f"Parameter '{p}' hat keinen Type-Hint. Schreib z. B. '{p}: str' oder '{p}: int'.")
        elif typ not in TYP_UEBERSETZUNG and typing.get_origin(typ) not in (list, dict, typing.Literal):
            warnungen.append(f"Parameter '{p}' hat den Typ {typ}, der wird nicht unterstützt "
                             f"(erlaubt: str, int, float, bool, list, dict). Er wird als Text behandelt.")
        if p not in parameter_texte:
            warnungen.append(f"Parameter '{p}' ist im Docstring nicht beschrieben. "
                             f"Füge eine Zeile '{p}: Beschreibung' hinzu.")

    rueckgabe = typen.get("return", inspect.Signature.empty)
    if rueckgabe is inspect.Signature.empty:
        warnungen.append("Kein Rückgabetyp angegeben (z. B. '-> dict'). Empfohlen: dict, list oder str.")
    elif (typing.get_origin(rueckgabe) or rueckgabe) not in ERLAUBTE_RUECKGABE:
        warnungen.append(f"Rückgabetyp {rueckgabe} kann nicht als JSON verschickt werden. "
                         f"Gib lieber ein dict, eine list oder einen str zurück.")
    return warnungen


def main():
    nur = sys.argv[1] if len(sys.argv) > 1 else None
    tools_laden()
    probleme = 0

    print("=" * 70)
    print(" TOOLS")
    print("=" * 70)

    for datei, fehler in LADEFEHLER.items():
        probleme += 1
        print(f"\n❌ tools/{datei} konnte nicht geladen werden:\n   {fehler}")
        print("   Tipp: Steht 'from agent import tool' oben in der Datei? Tippfehler? Einrückung?")

    for name, info in ALLE_TOOLS.items():
        if nur and name != nur:
            continue
        datei = Path(info["datei"]).name
        extra = "  (fragt vor Ausführung nach)" if info["bestaetigen"] else ""
        print(f"\n🔧 {name}   [tools/{datei}]{extra}")
        print("   So sieht das LLM dieses Tool:")
        schema_text = json.dumps(info["schema"]["function"], ensure_ascii=False, indent=2)
        print("   " + schema_text.replace("\n", "\n   "))
        warnungen = tool_pruefen(name, info)
        for w in warnungen:
            print(f"   ⚠️  {w}")
        if not warnungen:
            print("   ✅ Alles in Ordnung")
        probleme += len(warnungen)

    if nur and nur not in ALLE_TOOLS:
        print(f"\n❌ Ein Tool namens '{nur}' gibt es nicht. Vorhanden: {', '.join(ALLE_TOOLS)}")
        probleme += 1

    print("\n" + "=" * 70)
    print(" AGENTS")
    print("=" * 70)
    for kennung in agenten_auflisten():
        try:
            a = agent_laden(kennung)
            print(f"✅ {kennung:15} {a['name']}  ->  Tools: {', '.join(a['tools']) or '(keine)'}")
        except KonfigFehler as fehler:
            probleme += 1
            print(f"❌ {kennung:15} {fehler}")
        except Exception as fehler:
            probleme += 1
            print(f"❌ {kennung:15} Datei kann nicht gelesen werden: {type(fehler).__name__}: {fehler}")

    print("\n" + "=" * 70)
    print(" API-KEY")
    print("=" * 70)
    if not Path(".env").exists():
        print("⚠️  Noch keine .env-Datei. Kopiere .env.example nach .env und trage deinen Key ein.")
    else:
        from agent.provider import ProviderFehler, einstellungen_lesen
        try:
            e = einstellungen_lesen()
            print(f"✅ .env gefunden: Anbieter={e['anbieter']}, Modell={e['modell']} "
                  f"(ob der Key wirklich funktioniert, merkst du erst beim Chatten)")
        except ProviderFehler as fehler:
            print(f"⚠️  {fehler}")

    print()
    if probleme:
        print(f"Fertig – {probleme} Hinweis(e) gefunden (siehe ⚠️/❌ oben).")
    else:
        print("Fertig – alles in Ordnung! 🎉")


if __name__ == "__main__":
    main()
