# Copyright 2026 Maciej M. Kasperek ("vonKrappitz")
# SPDX-License-Identifier: Apache-2.0
"""Test twardej reguły: jeden pilot = jedna maszyna w danym dniu.

Żaden pilot nie może wystąpić dwukrotnie w tym samym dniu w roli PIC, drugiego
pilota ani instruktora, na wielu datach startowych i w 15-dniowym oknie.
"""
from datetime import date, timedelta

import pytest

from frms.data import generuj_pilotow, generuj_sloty
from frms.scheduler import generuj_harmonogram


@pytest.mark.parametrize("offset", [0, 6, 12, 18, 24])
def test_brak_podwojnej_obsady_w_dniu(offset):
    d = date(2026, 6, 1) + timedelta(days=offset)
    piloci = generuj_pilotow(d)
    sloty = generuj_sloty(d, dni=15)
    obsadzone, _ = generuj_harmonogram(sloty, piloci)

    licznik: dict[tuple, int] = {}
    for s in obsadzone:
        for pid in (s.przypisany_pilot_id, s.drugi_pilot_id, s.instruktor_id):
            if pid:
                klucz = (pid, s.data)
                licznik[klucz] = licznik.get(klucz, 0) + 1

    kolizje = {k: v for k, v in licznik.items() if v > 1}
    assert not kolizje, f"pilot obsadzony wielokrotnie w dniu: {list(kolizje)[:5]}"
