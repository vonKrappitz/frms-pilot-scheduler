# Copyright 2026 Maciej M. Kasperek ("vonKrappitz")
# SPDX-License-Identifier: Apache-2.0
"""
Moduł LAW (EPDE Dęblin): grafik treningów symulatorowych na dziś i kolejne dni
oraz rejestracja wyniku sesji.

Grafik pokazuje, którzy piloci mają tego dnia sesję, na jakiej maszynie (klasie),
czy to recurrent czy recovery, oraz całkowity nalot pilota na tym modelu. Jeden
dzień może mieć kilku pilotów na różnych maszynach, część w recovery, część w
recurrent.

Rejestracja: recovery zalicza się dopiero od MIN_STARTY_LADOWANIA_RECOVERY startów
i lądowań; recurrent kwartalny zalicza się bez tego warunku (jeden trening).
"""

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

from frms.models import KlasaMaszyny, Pilot, SesjaSymulatorowa
from frms.symulator import zbierz_zapotrzebowanie, zaplanuj_z_zapotrzebowania
from frms.currency import (
    MIN_STARTY_LADOWANIA_RECOVERY, CZAS_SESJI_SYMULATORA, recovery_wazna,
)

HORYZONT_LAW_DNI = 15  # dziś i kolejne 14 dni


@dataclass
class WpisGrafikuLAW:
    data: date
    pilot_id: str
    klasa: KlasaMaszyny
    typ: str                      # "RECURRENT" lub "RECOVERY"
    nalot_na_modelu_h: float      # całkowity nalot pilota na tej klasie (z historii misji)
    starty_wymagane: int          # MIN_STARTY... dla recovery, 0 dla recurrent
    termin: Optional[date]        # deadline recovery (okno_do); None dla recurrent


def nalot_na_klasie(pilot: Pilot, klasa: KlasaMaszyny) -> float:
    """Suma godzin lotu operacyjnego pilota na danej klasie (bez godzin symulatora)."""
    return round(sum(
        m.czas_trwania_h for m in pilot.historia_misji
        if m.klasa_maszyny == klasa and not m.czy_symulator
    ), 1)


def grafik_law(piloci: list[Pilot], dzien_start: date, dni: int = HORYZONT_LAW_DNI) -> list[WpisGrafikuLAW]:
    """Grafik treningów EPDE na dziś i kolejne dni (sesje zaplanowane w oknie)."""
    by_id = {p.id: p for p in piloci}
    zap = zbierz_zapotrzebowanie(piloci, dzien_start)
    przydzialy, _ = zaplanuj_z_zapotrzebowania(zap)
    koniec = dzien_start + timedelta(days=dni - 1)

    wpisy: list[WpisGrafikuLAW] = []
    for z, dni_sesji in przydzialy:
        for d in dni_sesji:
            if not (dzien_start <= d <= koniec):
                continue
            p = by_id.get(z.pilot_id)
            wpisy.append(WpisGrafikuLAW(
                data=d, pilot_id=z.pilot_id, klasa=z.klasa, typ=z.typ,
                nalot_na_modelu_h=nalot_na_klasie(p, z.klasa) if p else 0.0,
                starty_wymagane=MIN_STARTY_LADOWANIA_RECOVERY if z.typ == "RECOVERY" else 0,
                termin=z.okno_do if z.typ == "RECOVERY" else None,
            ))
    wpisy.sort(key=lambda w: (w.data, w.klasa.value, w.pilot_id))
    return wpisy


def zarejestruj_recovery(pilot: Pilot, klasa: KlasaMaszyny, dzien: date,
                         starty: int, ladowania: int) -> bool:
    """Zapisuje sesję recovery do historii pilota. Zalicza dopiero od 5 startów
    ORAZ 5 lądowań; przy mniejszej liczbie zwraca False i nic nie zapisuje."""
    sesja = SesjaSymulatorowa(
        data=dzien, klasa_maszyny=klasa, czas_trwania_h=CZAS_SESJI_SYMULATORA,
        czy_currency_recovery=True, starty=starty, ladowania=ladowania,
        starty_ladowania=starty + ladowania,
    )
    if not recovery_wazna(sesja):
        return False
    pilot.historia_sesji_symulatorowych.append(sesja)
    return True


def zarejestruj_recurrent(pilot: Pilot, klasa: KlasaMaszyny, dzien: date) -> bool:
    """Zapisuje zaliczony recurrent kwartalny (jeden przycisk, bez progu startów)."""
    sesja = SesjaSymulatorowa(
        data=dzien, klasa_maszyny=klasa, czas_trwania_h=CZAS_SESJI_SYMULATORA,
        czy_recurrent=True,
    )
    pilot.historia_sesji_symulatorowych.append(sesja)
    return True
