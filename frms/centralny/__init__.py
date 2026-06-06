"""
Moduł centralny (blok 10): mapa sytuacyjna floty.

Składa stan floty z `Rdzen` z warstwą telemetrii (port `TelemetryProvider`) w
snapshot live: status, pozycja, paliwo, czas misji per egzemplarz. Status łączy
telemetrię z regułami serwisu: maszyna w obsłudze jest SERWIS, w locie (telemetria
raportuje czas misji) LOT, w pozostałych przypadkach ZIEMIA.
"""

from collections import Counter
from datetime import date

from frms.models import Maszyna, StatusMaszyny
from frms.porty import TelemetryProvider
from frms.serwis import w_serwisie


def status_maszyny(maszyna: Maszyna, telemetry: TelemetryProvider, dzien: date) -> str:
    if maszyna.status != StatusMaszyny.OPERACYJNA:
        return "NIEOPERACYJNA"
    if w_serwisie(maszyna, dzien):
        return "SERWIS"
    return "LOT" if telemetry.czas_misji(maszyna) is not None else "ZIEMIA"


def snapshot_maszyny(maszyna: Maszyna, telemetry: TelemetryProvider, dzien: date) -> dict:
    poz = telemetry.pozycja(maszyna)
    return {
        "maszyna_id": maszyna.id,
        "klasa": maszyna.klasa.value,
        "hub": maszyna.aktualny_hub,
        "status": status_maszyny(maszyna, telemetry, dzien),
        "lat": poz[0] if poz else None,
        "lon": poz[1] if poz else None,
        "paliwo": telemetry.paliwo(maszyna),
        "czas_misji_min": telemetry.czas_misji(maszyna),
    }


def snapshot_floty(maszyny: list, telemetry: TelemetryProvider, dzien: date) -> dict:
    masz = [snapshot_maszyny(m, telemetry, dzien) for m in maszyny]
    porzadek = {"LOT": 0, "ZIEMIA": 1, "SERWIS": 2, "NIEOPERACYJNA": 3}
    masz.sort(key=lambda x: (porzadek.get(x["status"], 9), x["maszyna_id"]))
    return {"maszyny": masz, "podsumowanie": dict(Counter(m["status"] for m in masz))}
