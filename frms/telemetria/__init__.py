"""
Moduł telemetrii (blok 10): adapter `MockTelemetry`.

Deterministyczna zaślepka portu `TelemetryProvider` (bez RNG): pozycja w okolicy
huba macierzystego, paliwo, czas bieżącej misji. Realne GPS podmienia tylko ten
adapter, bez zmian w rdzeniu ani w innych modułach.
"""

import hashlib
from typing import Optional

from frms.models import Maszyna, Pilot

# Przybliżone współrzędne baz/hubów (lotniska, stopnie dziesiętne).
WSPOLRZEDNE_BAZ = {
    "EPWA": (52.17, 20.97), "EPKK": (50.08, 19.80), "EPWR": (51.10, 16.89),
    "EPLL": (51.72, 19.40), "EPKT": (50.47, 19.08), "EPRZ": (50.11, 22.02),
    "EPZA": (49.30, 19.96), "EPLB": (51.24, 22.71), "EPDE": (51.55, 21.89),
    "EPSY": (53.48, 20.94), "EPGD": (54.38, 18.47), "EPPO": (52.42, 16.83),
    "EPBY": (53.10, 17.98), "EPSC": (53.58, 14.90),
}


def _h(s: str) -> int:
    return int(hashlib.md5(s.encode()).hexdigest(), 16)


class MockTelemetry:
    """Deterministyczny adapter portu TelemetryProvider. Bez RNG, bez stanu."""

    def __init__(self, baza_wspolrzednych: Optional[dict] = None):
        self.coords = baza_wspolrzednych or WSPOLRZEDNE_BAZ

    def _w_locie(self, maszyna: Maszyna) -> bool:
        return _h(maszyna.id) % 3 == 0

    def pozycja(self, maszyna: Maszyna) -> Optional[tuple[float, float]]:
        c = self.coords.get(maszyna.aktualny_hub or "")
        if c is None:
            return None
        if not self._w_locie(maszyna):
            return c
        h = _h(maszyna.id)
        dlat = ((h % 100) / 100 - 0.5) * 0.6
        dlon = (((h // 100) % 100) / 100 - 0.5) * 0.8
        return (round(c[0] + dlat, 4), round(c[1] + dlon, 4))

    def paliwo(self, maszyna: Maszyna) -> Optional[float]:
        return float(20 + _h(maszyna.id + "f") % 81)

    def czas_misji(self, maszyna: Maszyna) -> Optional[int]:
        if not self._w_locie(maszyna):
            return None
        return 20 + _h(maszyna.id + "t") % 161

    def zaloga(self, maszyna: Maszyna) -> list[Pilot]:
        return []
