# Copyright 2026 Maciej M. Kasperek ("vonKrappitz")
# SPDX-License-Identifier: Apache-2.0
"""
Porty rdzenia FRMS — kontrakty, które implementują adaptery modułów.

Wzorzec porty i adaptery: rdzeń definiuje interfejs (port), moduł go
implementuje (adapter). Port deklaruje się wyłącznie tam, gdzie podmienia się
realne źródło zewnętrzne. Na start jest jeden: telemetria. Adapter-zaślepka
`MockTelemetry` mieszka w module `telemetria` (blok 10); realne źródło GPS
podmienia tylko adapter, bez zmian w rdzeniu ani w innych modułach.

Moduły wewnętrzne (serwis, centralny) nie dostają osobnych portów: kontraktują
się o publiczne akcesory `Rdzen`. Port robi się tylko na granicy wejścia/wyjścia.
"""

from typing import Optional, Protocol, runtime_checkable

from frms.models import Maszyna, Pilot


@runtime_checkable
class TelemetryProvider(Protocol):
    """Źródło danych telemetrycznych maszyny (§13.1 projektu rozbudowy).

    Każda wartość może wrócić None, gdy maszyna jej nie raportuje — panel
    pokazuje wtedy „brak danych", a reszta modułu centralnego działa dalej.
    Raportowanie zwrotne jest opcjonalne.
    """

    def pozycja(self, maszyna: Maszyna) -> Optional[tuple[float, float]]:
        """Pozycja (lat, lon) albo None."""
        ...

    def paliwo(self, maszyna: Maszyna) -> Optional[float]:
        """Stan paliwa w procentach (0–100) albo None."""
        ...

    def czas_misji(self, maszyna: Maszyna) -> Optional[int]:
        """Czas trwania bieżącej misji w minutach albo None."""
        ...

    def zaloga(self, maszyna: Maszyna) -> list[Pilot]:
        """Załoga aktualnie na pokładzie (lista może być pusta)."""
        ...
