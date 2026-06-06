# Copyright 2026 Maciej M. Kasperek ("vonKrappitz")
# SPDX-License-Identifier: Apache-2.0
"""Testy modułu LAW (frms.law)."""

from datetime import date, timedelta

from frms.models import (
    Kategoria, KlasaMaszyny, Organizacja, Pilot, TypeRating, Misja, SkalaNACA, TypDyzuru,
)
from frms.data import generuj_pilotow
from frms.law import (
    grafik_law, nalot_na_klasie, zarejestruj_recovery, zarejestruj_recurrent,
    HORYZONT_LAW_DNI,
)
from frms.currency import recurrent_odbyty_w_kwartale

HEMS = KlasaMaszyny.HEMS_SREDNI
START = date(2026, 6, 3)


def test_grafik_w_oknie_i_typy():
    piloci = generuj_pilotow(START)
    g = grafik_law(piloci, START, HORYZONT_LAW_DNI)
    assert g, "grafik nie powinien być pusty"
    koniec = START + timedelta(days=HORYZONT_LAW_DNI - 1)
    for w in g:
        assert START <= w.data <= koniec
        assert w.typ in ("RECURRENT", "RECOVERY")
        if w.typ == "RECOVERY":
            assert w.starty_wymagane == 5 and w.termin is not None
        else:
            assert w.starty_wymagane == 0 and w.termin is None


def test_dzien_moze_miec_wielu_pilotow_rozne_maszyny():
    piloci = generuj_pilotow(START)
    g = grafik_law(piloci, START, HORYZONT_LAW_DNI)
    # pierwszy dzień z sesjami: różne klasy, różni piloci
    pierwszy = min(w.data for w in g)
    tego_dnia = [w for w in g if w.data == pierwszy]
    assert len({w.pilot_id for w in tego_dnia}) == len(tego_dnia)  # różni piloci
    assert len({w.klasa for w in tego_dnia}) >= 1


def test_nalot_na_klasie_sumuje_godziny_lotu():
    p = Pilot(id="X", imie="x", nazwisko="x", kategoria=Kategoria.B,
              baza_macierzysta="EPWA", organizacja=Organizacja.LPR,
              type_ratings=[TypeRating(HEMS, START - timedelta(days=400),
                                       START - timedelta(days=5), START + timedelta(days=300))],
              historia_misji=[
                  Misja(START - timedelta(days=10), 2.0, HEMS, SkalaNACA.NACA_3, TypDyzuru.DYZUR_24H),
                  Misja(START - timedelta(days=20), 3.5, HEMS, SkalaNACA.NACA_2, TypDyzuru.DYZUR_24H),
                  Misja(START - timedelta(days=30), 5.0, HEMS, SkalaNACA.NACA_2, TypDyzuru.DYZUR_24H, czy_symulator=True),
              ])
    assert nalot_na_klasie(p, HEMS) == 5.5  # 2.0 + 3.5; sesja symulatorowa pominięta


def test_rejestracja_recovery_prog_startow():
    p = generuj_pilotow(START)[0]
    przed = len(p.historia_sesji_symulatorowych)
    assert zarejestruj_recovery(p, HEMS, START, 4, 6) is False  # za mało startów
    assert zarejestruj_recovery(p, HEMS, START, 6, 4) is False  # za mało lądowań
    assert len(p.historia_sesji_symulatorowych) == przed  # nic nie zapisano
    assert zarejestruj_recovery(p, HEMS, START, 5, 5) is True
    assert len(p.historia_sesji_symulatorowych) == przed + 1


def test_rejestracja_recurrent_zalicza_kwartal():
    p = generuj_pilotow(START)[0]
    klasa = p.type_ratings[0].klasa
    assert zarejestruj_recurrent(p, klasa, START) is True
    assert recurrent_odbyty_w_kwartale(p, START) is True
