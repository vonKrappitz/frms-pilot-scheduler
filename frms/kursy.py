# Copyright 2026 Maciej M. Kasperek ("vonKrappitz")
# SPDX-License-Identifier: Apache-2.0
"""
Kursy specjalistyczne i dni wolne.

HEMS (H145) wymaga dwóch kursów: lot nocny i gogle nocne. MEDEVAC (AW101) dokłada
do nich zawis z wciągarką oraz FIKI, bo tylko ciężka maszyna ma wciągarkę i pełne
odladzanie (H145 ma odladzanie podstawowe i nie nosi wciągarki). LST i STOL
nie wymagają żadnego kursu. Pilot bez kompletu wymaganego na danej klasie nie
wchodzi na jej slot; pilot na urlopie jest niedostępny w tym dniu.

Egzekwowanie jest w warstwie doboru i wymiany. Rdzenia harmonogramu nie dotyka,
więc reprodukowalność scale_test pozostaje nienaruszona; brak kursu u już
obsadzonego pilota zgłaszany jest jako alert, analogicznie do type ratingu.
"""

from datetime import date

from frms.models import Kurs, KlasaMaszyny, Pilot

# Kursy HEMS: noc i noktowizja (H145 lata nocą oraz IFR).
KURSY_HEMS = frozenset({Kurs.LOT_NOCNY, Kurs.GOGLE_NOCNE})
# Kursy MEDEVAC: HEMS plus wciągarka i FIKI (zdolności wyłącznie AW101).
KURSY_MEDEVAC = frozenset({
    Kurs.LOT_NOCNY, Kurs.GOGLE_NOCNE, Kurs.ZAWIS_WCIAGARKA, Kurs.FIKI,
})
# Komplet wszystkich czterech kursów (= zestaw MEDEVAC).
WSZYSTKIE_KURSY = KURSY_MEDEVAC

# Wymagania kursowe per klasa maszyny.
KURSY_WYMAGANE: dict[KlasaMaszyny, frozenset] = {
    KlasaMaszyny.HEMS_SREDNI: KURSY_HEMS,
    KlasaMaszyny.MEDEVAC_CIEZKI: KURSY_MEDEVAC,
}


def kursy_wymagane(klasa: KlasaMaszyny) -> frozenset:
    return KURSY_WYMAGANE.get(klasa, frozenset())


def brakujace_kursy(pilot: Pilot, klasa: KlasaMaszyny) -> list[Kurs]:
    """Kursy wymagane na danej klasie, których pilot nie ma. Kolejność stała."""
    posiadane = set(pilot.kursy)
    wymagane = kursy_wymagane(klasa)
    return [k for k in Kurs if k in wymagane and k not in posiadane]


def spelnia_kursy(pilot: Pilot, klasa: KlasaMaszyny) -> bool:
    """Czy pilot ma komplet kursów wymaganych na danej klasie."""
    return not brakujace_kursy(pilot, klasa)


def na_urlopie(pilot: Pilot, dzien: date) -> bool:
    return dzien in pilot.dni_wolne


def dostepny_w_dniu(pilot: Pilot, dzien: date) -> bool:
    return not na_urlopie(pilot, dzien)


# ---- enrichery danych (deterministyczne, bez RNG, by nie ruszać scale_test) ----

def przypisz_kursy_domyslne(piloci: list[Pilot]) -> None:
    """Nadaje kursy zależnie od ratingu: pilot z MEDEVAC dostaje cztery kursy,
    pilot z samym HEMS dwa (lot nocny, gogle nocne), reszta żadnego.

    Deterministycznie wybranym pilotom (co jedenasty po indeksie) odbiera ostatni
    kurs z ich zestawu, aby zademonstrować bramkowanie i alerty. Bez RNG.
    """
    for i, p in enumerate(piloci):
        klasy = {tr.klasa for tr in p.type_ratings}
        if KlasaMaszyny.MEDEVAC_CIEZKI in klasy:
            wymagane = KURSY_MEDEVAC
        elif KlasaMaszyny.HEMS_SREDNI in klasy:
            wymagane = KURSY_HEMS
        else:
            p.kursy = []
            continue
        komplet = [k for k in Kurs if k in wymagane]  # stała kolejność
        if i % 11 == 0 and komplet:
            komplet = komplet[:-1]  # deterministyczny brak ostatniego kursu z zestawu
        p.kursy = komplet


def przypisz_dni_wolne(piloci: list[Pilot], dzien_start: date, dni: int = 15) -> None:
    """Nadaje dni wolne deterministycznie: co siódmy pilot ma wolne w jednym dniu okna."""
    from datetime import timedelta
    for i, p in enumerate(piloci):
        if i % 7 == 3:
            offset = (i // 7) % dni
            p.dni_wolne = [dzien_start + timedelta(days=offset)]
        else:
            p.dni_wolne = []
