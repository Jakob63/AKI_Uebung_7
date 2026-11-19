"""Wetter-Tool mit einer echten, kostenlosen Internet-API (Open-Meteo, braucht keinen Key).

Das Tool macht zwei Anfragen:
    1. "Wo liegt Konstanz?"           -> Koordinaten (Geocoding)
    2. "Wie wird das Wetter dort?"    -> Vorhersage

Wenn die Stadt nicht gefunden wird, werfen wir einen Fehler (raise). Die Vorlage fängt ihn ab
und meldet ihn dem LLM als {"error": "..."} – probier mal "Wie ist das Wetter in Xyzabc?".
"""

import httpx

from agent import tool

# Open-Meteo liefert das Wetter als Zahlencode. Hier die Übersetzung (vereinfacht).
WETTERCODES = {
    0: "klar", 1: "überwiegend klar", 2: "teilweise bewölkt", 3: "bedeckt",
    45: "Nebel", 48: "Nebel mit Reif",
    51: "leichter Nieselregen", 53: "Nieselregen", 55: "starker Nieselregen",
    61: "leichter Regen", 63: "Regen", 65: "starker Regen",
    71: "leichter Schneefall", 73: "Schneefall", 75: "starker Schneefall",
    80: "leichte Regenschauer", 81: "Regenschauer", 82: "heftige Regenschauer",
    95: "Gewitter", 96: "Gewitter mit Hagel", 99: "schweres Gewitter mit Hagel",
}


@tool
def wetter(stadt: str, tage: int = 1) -> dict:
    """Gibt das aktuelle Wetter und die Wettervorhersage für eine Stadt zurück
    (Temperatur in °C, Niederschlag in mm).

    stadt: Name der Stadt, z. B. "Konstanz"
    tage: Anzahl Tage der Vorhersage (1-7)
    """
    tage = max(1, min(tage, 7))  # nur 1 bis 7 Tage erlauben

    # 1. Koordinaten der Stadt suchen
    orte = httpx.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": stadt, "count": 5, "language": "de"},
        timeout=10,  # nie ewig warten
    ).json().get("results")
    if not orte:
        raise ValueError(f"Die Stadt '{stadt}' wurde nicht gefunden.")
    # Ort mit genau passendem Namen bevorzugen (sonst wird aus "Konstanz" schnell "Konstanza")
    passende = [o for o in orte if o["name"].lower() == stadt.strip().lower()]
    ort = (passende or orte)[0]

    # 2. Vorhersage holen
    daten = httpx.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": ort["latitude"],
            "longitude": ort["longitude"],
            "current": "temperature_2m,weather_code",
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code",
            "timezone": "auto",
            "forecast_days": tage,
        },
        timeout=10,
    ).json()

    # 3. Nur das Wichtigste zurückgeben (spart Tokens)
    taeglich = daten["daily"]
    return {
        "ort": f"{ort['name']}, {ort.get('country', '')}",
        "jetzt": {
            "temperatur": daten["current"]["temperature_2m"],
            "wetter": WETTERCODES.get(daten["current"]["weather_code"], "unbekannt"),
        },
        "vorhersage": [
            {
                "datum": taeglich["time"][i],
                "min": taeglich["temperature_2m_min"][i],
                "max": taeglich["temperature_2m_max"][i],
                "niederschlag_mm": taeglich["precipitation_sum"][i],
                "wetter": WETTERCODES.get(taeglich["weather_code"][i], "unbekannt"),
            }
            for i in range(len(taeglich["time"]))
        ],
    }
