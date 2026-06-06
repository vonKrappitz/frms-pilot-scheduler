# Copyright 2026 Maciej M. Kasperek ("vonKrappitz")
# SPDX-License-Identifier: Apache-2.0
"""Testy kursów i dni wolnych (frms.kursy)."""

from datetime import date, timedelta

from frms.models import Kurs, KlasaMaszyny, Kategoria, Organizacja, Pilot, TypeRating
from frms.kursy import (
    KURSY_HEMS, KURSY_MEDEVAC, WSZYSTKIE_KURSY, kursy_wymagane, brakujace_kursy, spelnia_kursy,
    na_urlopie, dostepny_w_dniu, przypisz_kursy_domyslne, przypisz_dni_wolne,
)
from frms.data import generuj_pilotow

HEMS = KlasaMaszyny.HEMS_SREDNI
MEDEVAC = KlasaMaszyny.MEDEVAC_CIEZKI
LST = KlasaMaszyny.LST_LEKKI
DZIEN = date(2026, 6, 3)


def _tr(klasa):
    return TypeRating(klasa, DZIEN - timedelta(days=400), DZIEN - timedelta(days=5),
                      DZIEN + timedelta(days=360))


def test_wymagania_per_klasa():
    assert kursy_wymagane(HEMS) == KURSY_HEMS               # noc + gogle
    assert kursy_wymagane(MEDEVAC) == KURSY_MEDEVAC         # + wciągarka + FIKI
    assert KURSY_HEMS == {Kurs.LOT_NOCNY, Kurs.GOGLE_NOCNE}
    assert KURSY_MEDEVAC - KURSY_HEMS == {Kurs.ZAWIS_WCIAGARKA, Kurs.FIKI}
    assert kursy_wymagane(LST) == frozenset()


def test_komplet_i_brak():
    p = Pilot(id="P", imie="x", nazwisko="x", kategoria=Kategoria.C, baza_macierzysta="EPWA",
              organizacja=Organizacja.LPR, kursy=list(WSZYSTKIE_KURSY))
    assert spelnia_kursy(p, MEDEVAC) is True
    assert brakujace_kursy(p, MEDEVAC) == []
    assert spelnia_kursy(p, LST) is True  # LST nic nie wymaga
    # sam HEMS to tylko noc i gogle; bez nich brak
    p.kursy = [Kurs.ZAWIS_WCIAGARKA, Kurs.FIKI]
    assert spelnia_kursy(p, HEMS) is False
    assert set(brakujace_kursy(p, HEMS)) == {Kurs.LOT_NOCNY, Kurs.GOGLE_NOCNE}
    # a MEDEVAC bez wciągarki/FIKI też nie spełnia
    p.kursy = [Kurs.LOT_NOCNY, Kurs.GOGLE_NOCNE]
    assert spelnia_kursy(p, HEMS) is True
    assert spelnia_kursy(p, MEDEVAC) is False
    assert set(brakujace_kursy(p, MEDEVAC)) == {Kurs.ZAWIS_WCIAGARKA, Kurs.FIKI}


def test_urlop():
    p = Pilot(id="P", imie="x", nazwisko="x", kategoria=Kategoria.B, baza_macierzysta="EPWA",
              organizacja=Organizacja.LPR, dni_wolne=[DZIEN])
    assert na_urlopie(p, DZIEN) is True
    assert dostepny_w_dniu(p, DZIEN) is False
    assert dostepny_w_dniu(p, DZIEN + timedelta(days=1)) is True


def test_enricher_kursy_dla_hems_medevac():
    piloci = generuj_pilotow(DZIEN)
    przypisz_kursy_domyslne(piloci)
    for p in piloci:
        klasy = {tr.klasa for tr in p.type_ratings}
        if MEDEVAC in klasy:
            assert len(p.kursy) in (3, 4)          # komplet 4 lub brak jednego
            assert set(p.kursy) <= KURSY_MEDEVAC
        elif HEMS in klasy:
            assert len(p.kursy) in (1, 2)          # noc+gogle lub brak jednego
            assert set(p.kursy) <= KURSY_HEMS
        else:
            assert p.kursy == []
    # przynajmniej jeden pilot ma zademonstrowany brak kursu
    assert any(set(p.kursy) and set(p.kursy) < kursy_wymagane_pilota(p) for p in piloci)


def test_enricher_dni_wolne_deterministyczny():
    piloci = generuj_pilotow(DZIEN)
    przypisz_dni_wolne(piloci, DZIEN, 15)
    a = [list(p.dni_wolne) for p in piloci]
    przypisz_dni_wolne(piloci, DZIEN, 15)
    b = [list(p.dni_wolne) for p in piloci]
    assert a == b  # deterministyczny
    assert any(p.dni_wolne for p in piloci)


def kursy_wymagane_pilota(p):
    klasy = {tr.klasa for tr in p.type_ratings}
    if MEDEVAC in klasy: return KURSY_MEDEVAC
    if HEMS in klasy: return KURSY_HEMS
    return frozenset()
