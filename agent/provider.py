"""
Provider: Verbindung zum Sprachmodell (LLM).

Fast alle Anbieter sprechen dasselbe "Protokoll" wie OpenAI. Deshalb reicht EIN Python-Paket
(openai) für alle – es ändern sich nur drei Werte: Adresse (base_url), Schlüssel (api_key), Modell.

Diese Werte stehen in der Datei .env (die du aus .env.example kopierst). So landen
geheime Schlüssel nie im Code.
"""

import os

from dotenv import load_dotenv
from openai import OpenAI

# Bekannte Anbieter: Name -> (Adresse, Standard-Modell, Name der Key-Variable in .env)
ANBIETER = {
    "nvidia": ("https://integrate.api.nvidia.com/v1", "nvidia/nemotron-3.5-lightning-30b-a3b", "NVIDIA_API_KEY"),
    "groq": ("https://api.groq.com/openai/v1", "openai/gpt-oss-120b", "GROQ_API_KEY"),
    "custom": (None, None, "AI_API_KEY"),  # alles selbst in .env eintragen (z. B. Ollama, OpenAI)
}


class ProviderFehler(Exception):
    """Konfigurationsfehler – die Meldung erklärt, was zu tun ist."""


def einstellungen_lesen() -> dict:
    """Liest .env und gibt {"anbieter", "base_url", "modell", "api_key"} zurück."""
    if not os.path.exists(".env"):
        raise ProviderFehler(
            "Keine .env-Datei gefunden.\n"
            "So geht's: Kopiere die Datei .env.example und nenne die Kopie .env.\n"
            "Trage dort deinen API-Key ein (Anleitung steht in der README.md, Schritt 3)."
        )
    load_dotenv(".env", override=True)

    anbieter = os.getenv("AI_PROVIDER", "nvidia").strip().lower()
    if anbieter not in ANBIETER:
        raise ProviderFehler(
            f"Unbekannter AI_PROVIDER '{anbieter}' in .env. Erlaubt sind: {', '.join(ANBIETER)}"
        )

    standard_url, standard_modell, key_name = ANBIETER[anbieter]
    base_url = os.getenv("AI_BASE_URL") or standard_url
    modell = os.getenv("AI_MODEL") or standard_modell
    api_key = (os.getenv(key_name) or "").strip()

    if not api_key or api_key.startswith("hier_"):
        raise ProviderFehler(
            f"Kein API-Key gefunden. Öffne die Datei .env und trage bei {key_name}= deinen Schlüssel ein.\n"
            f"(Wie du an einen kostenlosen Schlüssel kommst, steht in der README.md, Schritt 3.)"
        )
    if not base_url or not modell:
        raise ProviderFehler(
            "Bei AI_PROVIDER=custom musst du in .env auch AI_BASE_URL und AI_MODEL eintragen."
        )

    return {"anbieter": anbieter, "base_url": base_url, "modell": modell, "api_key": api_key}


def client_erstellen() -> tuple[OpenAI, str]:
    """Gibt (client, modellname) zurück."""
    e = einstellungen_lesen()
    client = OpenAI(base_url=e["base_url"], api_key=e["api_key"], timeout=60)
    return client, e["modell"]
