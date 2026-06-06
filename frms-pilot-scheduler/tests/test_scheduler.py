# Copyright 2026 Maciej M. Kasperek ("vonKrappitz")
# SPDX-License-Identifier: Apache-2.0
"""Podstawowe testy jednostkowe schedulera FRMS."""

from datetime import date

import pytest

from frms.data import generuj_pilotow, generuj_sloty
from frms.models import Kategoria, KlasaMaszyny, TypDyzuru, TypeRating, Pilot
from frms.scheduler import (
    generuj_harmonogram, kandydat_kwalifikujacy_sie,
    kategoria_wystarczajaca
)


DZIEN_TEST = date(2026, 6, 1)


def test_kategoria_hierarchia():
    """Hierarchia kategorii działa zgodnie z A < B < C < D."""
    assert kategoria_wystarczajaca(Kategoria.D, Kategoria.A)
    assert kategoria_wystarczajaca(Kategoria.C, Kategoria.C)
    assert not kategoria_wystarczajaca(Kategoria.A, Kategoria.C)


def test_type_rating_aktualny():
    """Type rating aktualny gdy poniżej 90 dni od ostatniego lotu i ważny."""
    dzien_referencyjny = date(2026, 6, 1)
    tr = TypeRating(
        klasa=KlasaMaszyny.HEMS_SREDNI,
        data_uzyskania=date(2024, 1, 1),
        data_ostatniego_lotu=date(2026, 4, 10),  # 52 dni wstecz - bez alertu
        data_waznosci=date(2027, 4, 10),
    )
    assert tr.jest_aktualny(dzien_referencyjny)
    assert not tr.wymaga_alertu(dzien_referencyjny)


def test_type_rating_wygasly():
    """Type rating nieaktualny po 90 dniach bez lotu."""
    dzien_referencyjny = date(2026, 6, 1)
    tr = TypeRating(
        klasa=KlasaMaszyny.LST_LEKKI,
        data_uzyskania=date(2024, 1, 1),
        data_ostatniego_lotu=date(2026, 1, 1),  # 151 dni wstecz
        data_waznosci=date(2027, 1, 1),
    )
    assert not tr.jest_aktualny(dzien_referencyjny)


def test_generacja_pilotow():
    """Generacja zwraca 30 pilotów LPR: A=10/B=10/C=7/D=3."""
    from frms.models import Organizacja
    piloci = generuj_pilotow(DZIEN_TEST)
    assert len(piloci) == 30
    assert all(p.organizacja == Organizacja.LPR for p in piloci)

    rozklad = {Kategoria.A: 0, Kategoria.B: 0, Kategoria.C: 0, Kategoria.D: 0}
    for p in piloci:
        rozklad[p.kategoria] += 1

    assert rozklad[Kategoria.A] == 10
    assert rozklad[Kategoria.B] == 10
    assert rozklad[Kategoria.C] == 7
    assert rozklad[Kategoria.D] == 3


def test_generacja_slotow():
    """Tydzień: 7 × (3 MEDEVAC + 4 HEMS + 8 LST + 2 LST-EPRZ + 1 STOL + 1 TRENING) = 133."""
    sloty = generuj_sloty(DZIEN_TEST, dni=7)
    assert len(sloty) == 7 * (3 + 4 + 8 + 2 + 1 + 1)


def test_harmonogram_obsadza_wiekszosc_slotow():
    """Realistyczny test: harmonogram powinien obsadzić >75% slotów."""
    piloci = generuj_pilotow(DZIEN_TEST)
    sloty = generuj_sloty(DZIEN_TEST, dni=7)
    obsadzone, nieobsadzone = generuj_harmonogram(sloty, piloci)
    procent = 100 * len(obsadzone) / len(sloty)
    assert procent > 75, f"Tylko {procent:.1f}% slotów obsadzonych"


def test_kategoria_zbyt_niska_odrzuca():
    """Pilot kategorii A nie może być przypisany do slotu MEDEVAC (wymaga C)."""
    piloci = generuj_pilotow(DZIEN_TEST)
    sloty = generuj_sloty(DZIEN_TEST, dni=1)
    slot_medevac = next(s for s in sloty if s.wymagana_kategoria_min == Kategoria.C)
    pilot_a = next(p for p in piloci if p.kategoria == Kategoria.A)
    ok, powod = kandydat_kwalifikujacy_sie(pilot_a, slot_medevac)
    assert not ok
    assert "kategoria" in powod.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


# ============================================================
# TESTY SYMULATORA LAW DĘBLIN (currency.py)
# ============================================================

def test_prog_currency_samolot_dluzszy_niz_heli():
    """Próg dni bez lotu: samolot STOL 45 dni, helikoptery 21 dni."""
    from frms.currency import prog_currency_dni, PROG_DNI_BEZ_LOTU_HELI, PROG_DNI_BEZ_LOTU_SAMOLOT
    assert prog_currency_dni(KlasaMaszyny.MEDEVAC_CIEZKI) == PROG_DNI_BEZ_LOTU_HELI == 21
    assert prog_currency_dni(KlasaMaszyny.HEMS_SREDNI) == 21
    assert prog_currency_dni(KlasaMaszyny.LST_LEKKI) == 21
    assert prog_currency_dni(KlasaMaszyny.STOL_SAMOLOT) == PROG_DNI_BEZ_LOTU_SAMOLOT == 45


def test_dni_od_ostatniego_lotu_per_klasa():
    """Funkcja liczy poprawnie dni od ostatniego lotu operacyjnego."""
    from frms.currency import dni_od_ostatniego_lotu_per_klasa
    from frms.models import Misja, SkalaNACA
    dzien = date(2026, 6, 1)
    pilot = Pilot(
        id="P999", imie="Test", nazwisko="Pilot",
        kategoria=Kategoria.C, baza_macierzysta="EPWA",
        type_ratings=[TypeRating(
            klasa=KlasaMaszyny.HEMS_SREDNI,
            data_uzyskania=date(2024, 1, 1),
            data_ostatniego_lotu=date(2026, 5, 15),
            data_waznosci=date(2027, 1, 1),
        )],
        historia_misji=[
            Misja(date(2026, 5, 15), 3.0, KlasaMaszyny.HEMS_SREDNI, SkalaNACA.NACA_3, TypDyzuru.DYZUR_24H),
        ]
    )
    assert dni_od_ostatniego_lotu_per_klasa(pilot, KlasaMaszyny.HEMS_SREDNI, dzien) == 17


def test_wymaga_currency_recovery_po_22_dniach_helikopter():
    """Pilot bez lotu na H145 przez 22 dni — przekracza próg 21 dni."""
    from frms.currency import wymaga_currency_recovery
    from frms.models import Misja, SkalaNACA
    dzien = date(2026, 6, 1)
    pilot = Pilot(
        id="P999", imie="Test", nazwisko="Pilot",
        kategoria=Kategoria.C, baza_macierzysta="EPWA",
        type_ratings=[TypeRating(
            klasa=KlasaMaszyny.HEMS_SREDNI,
            data_uzyskania=date(2024, 1, 1),
            data_ostatniego_lotu=date(2026, 5, 10),  # 22 dni wstecz
            data_waznosci=date(2027, 1, 1),
        )],
        historia_misji=[
            Misja(date(2026, 5, 10), 3.0, KlasaMaszyny.HEMS_SREDNI, SkalaNACA.NACA_3, TypDyzuru.DYZUR_24H),
        ]
    )
    assert wymaga_currency_recovery(pilot, KlasaMaszyny.HEMS_SREDNI, dzien) is True


def test_samolot_nie_wymaga_recovery_po_22_dniach():
    """Pilot bez lotu na samolocie STOL przez 22 dni — próg 45 dni, więc OK."""
    from frms.currency import wymaga_currency_recovery
    from frms.models import Misja, SkalaNACA
    dzien = date(2026, 6, 1)
    pilot = Pilot(
        id="P999", imie="Test", nazwisko="Pilot",
        kategoria=Kategoria.C, baza_macierzysta="EPKT",
        type_ratings=[TypeRating(
            klasa=KlasaMaszyny.STOL_SAMOLOT,
            data_uzyskania=date(2024, 1, 1),
            data_ostatniego_lotu=date(2026, 5, 10),  # 22 dni wstecz
            data_waznosci=date(2027, 1, 1),
        )],
        historia_misji=[
            Misja(date(2026, 5, 10), 2.5, KlasaMaszyny.STOL_SAMOLOT, SkalaNACA.NACA_2, TypDyzuru.ON_CALL_24H),
        ]
    )
    assert wymaga_currency_recovery(pilot, KlasaMaszyny.STOL_SAMOLOT, dzien) is False


def test_recurrent_resetuje_licznik_dni_bez_lotu():
    """Sesja recurrent kwartalny resetuje licznik dni bez lotu — pilot nie wymaga recovery."""
    from frms.currency import wymaga_currency_recovery
    from frms.models import Misja, SkalaNACA, SesjaSymulatorowa
    dzien = date(2026, 6, 1)
    pilot = Pilot(
        id="P999", imie="Test", nazwisko="Pilot",
        kategoria=Kategoria.C, baza_macierzysta="EPWA",
        type_ratings=[TypeRating(
            klasa=KlasaMaszyny.MEDEVAC_CIEZKI,
            data_uzyskania=date(2024, 1, 1),
            data_ostatniego_lotu=date(2026, 5, 10),  # 22 dni wstecz - zwykle wymaga recovery
            data_waznosci=date(2027, 1, 1),
        )],
        historia_misji=[
            Misja(date(2026, 5, 10), 4.0, KlasaMaszyny.MEDEVAC_CIEZKI, SkalaNACA.NACA_4, TypDyzuru.DYZUR_24H),
        ],
        historia_sesji_symulatorowych=[
            # Recurrent 10 dni temu - resetuje licznik
            SesjaSymulatorowa(
                data=date(2026, 5, 22),
                klasa_maszyny=KlasaMaszyny.MEDEVAC_CIEZKI,
                czas_trwania_h=6.0,
                czy_recurrent=True,
            ),
        ]
    )
    # Mimo 22 dni bez lotu — sym 10 dni temu resetuje, więc NIE wymaga recovery
    assert wymaga_currency_recovery(pilot, KlasaMaszyny.MEDEVAC_CIEZKI, dzien) is False
