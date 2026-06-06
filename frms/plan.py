# Copyright 2026 Maciej M. Kasperek ("vonKrappitz")
# SPDX-License-Identifier: Apache-2.0
"""
Warstwa planu operacyjnego: horyzont dziś plus kolejne dni (domyślnie 15 dni),
sloty pogrupowane per dzień, do nawigacji dzień po dniu w interfejsie.

Nie modyfikuje funkcji bazowych: woła `generuj_sloty(dzien, dni)` i
`generuj_harmonogram(sloty, piloci)` bez zmiany ich sygnatur, więc wynik
scale_test cytowany w artykule pozostaje reprodukowalny.
"""

from dataclasses import dataclass, field
from datetime import date

from frms.models import Pilot, SlotDyzurowy
from frms.data import generuj_sloty
from frms.scheduler import generuj_harmonogram

HORYZONT_DNI = 15  # dziś i kolejne 14 dni


@dataclass
class DzienPlanu:
    data: date
    sloty: list[SlotDyzurowy] = field(default_factory=list)


def plan_dni(piloci: list[Pilot], dzien_start: date, dni: int = HORYZONT_DNI) -> list[DzienPlanu]:
    """Plan operacyjny: obsadzone sloty pogrupowane per dzień, w kolejności rosnącej.

    Pilotów dostarcza wołający (np. z zasianego rdzenia), aby plan był
    deterministyczny i spójny z eksportem.
    """
    sloty = generuj_sloty(dzien_start, dni=dni)
    generuj_harmonogram(sloty, piloci)

    wg_dnia: dict[date, DzienPlanu] = {}
    for s in sloty:
        wg_dnia.setdefault(s.data, DzienPlanu(data=s.data)).sloty.append(s)
    return [wg_dnia[d] for d in sorted(wg_dnia)]


def dzien_planu(plan: list[DzienPlanu], dzien: date) -> DzienPlanu | None:
    """Zwraca plan konkretnego dnia albo None."""
    for d in plan:
        if d.data == dzien:
            return d
    return None


def nastepny_dzien(plan: list[DzienPlanu], biezacy: date) -> date | None:
    """Data następnego dnia w planie po `biezacy` (nawigacja „następny dzień"). None na końcu."""
    daty = [d.data for d in plan]
    for i, d in enumerate(daty):
        if d == biezacy and i + 1 < len(daty):
            return daty[i + 1]
    return None


def poprzedni_dzien(plan: list[DzienPlanu], biezacy: date) -> date | None:
    """Data poprzedniego dnia w planie przed `biezacy`. None na początku."""
    daty = [d.data for d in plan]
    for i, d in enumerate(daty):
        if d == biezacy and i > 0:
            return daty[i - 1]
    return None
