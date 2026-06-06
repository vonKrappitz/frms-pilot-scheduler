# Copyright 2026 Maciej M. Kasperek ("vonKrappitz")
# SPDX-License-Identifier: Apache-2.0
"""
Testy bloku 2: liczniki nalotu pilota i log lotów maszyny.

Stan budowany ręcznie: pilot z dwiema misjami w czerwcu, jedną w maju, jedną
sesją symulatorową i logbookiem 1000 h. Pozwala policzyć każdy licznik na pałę.
"""

from datetime import date, timedelta

from frms.models import (
    Kategoria, KlasaMaszyny, Maszyna, Misja, Pilot, SesjaSymulatorowa,
    SkalaNACA, SlotDyzurowy, StatusMaszyny, TrybMisji, TypDyzuru, TypeRating,
)
from frms.rdzen import Rdzen
from frms.rejestr import przydziel_maszyny
from frms.liczniki import (
    nalot_miesiac, nalot_misji, nalot_per_klasa, nalot_calkowity,
    godziny_symulatora, liczniki_pilota, log_lotow_maszyny, liczniki_maszyny,
)

HEMS = KlasaMaszyny.HEMS_SREDNI
LST = KlasaMaszyny.LST_LEKKI
DZIEN = date(2026, 6, 2)


def _pilot_z_historia():
    p = Pilot(id="P1", imie="x", nazwisko="y", kategoria=Kategoria.C, baza_macierzysta="EPWA")
    p.nalot_logbook_h = 1000.0
    p.historia_misji = [
        Misja(date(2026, 6, 1), 4.0, HEMS, SkalaNACA.NACA_3, TypDyzuru.DYZUR_24H),
        Misja(date(2026, 6, 2), 3.0, HEMS, SkalaNACA.NACA_3, TypDyzuru.ZMIANA_6H),
        Misja(date(2026, 5, 20), 2.0, LST, SkalaNACA.NACA_2, TypDyzuru.ZMIANA_6H),
        # wpis symulatorowy w historii misji nie liczy się do nalotu operacyjnego
        Misja(date(2026, 6, 3), 6.0, HEMS, SkalaNACA.NACA_0, TypDyzuru.SYMULATOR_LAW, czy_symulator=True),
    ]
    p.historia_sesji_symulatorowych = [
        SesjaSymulatorowa(date(2026, 6, 3), HEMS, 6.0),
        SesjaSymulatorowa(date(2026, 5, 1), HEMS, 6.0),
    ]
    return p


def test_nalot_miesiac():
    p = _pilot_z_historia()
    # czerwiec: 4.0 + 3.0 (symulatorowy wpis pominięty) = 7.0
    assert nalot_miesiac(p, 2026, 6) == 7.0
    # maj: 2.0
    assert nalot_miesiac(p, 2026, 5) == 2.0
    # lipiec: brak
    assert nalot_miesiac(p, 2026, 7) == 0.0


def test_nalot_misji_i_calkowity():
    p = _pilot_z_historia()
    # misje operacyjne: 4 + 3 + 2 = 9 (symulatorowy pominięty)
    assert nalot_misji(p) == 9.0
    # całkowity: logbook 1000 + 9
    assert nalot_calkowity(p) == 1009.0


def test_nalot_per_klasa():
    p = _pilot_z_historia()
    pk = nalot_per_klasa(p)
    assert pk[HEMS] == 7.0   # 4 + 3
    assert pk[LST] == 2.0
    assert HEMS in pk and len(pk) == 2  # symulator nie tworzy wpisu klasy


def test_godziny_symulatora():
    p = _pilot_z_historia()
    assert godziny_symulatora(p) == 12.0  # 6 + 6


def test_liczniki_pilota_komplet():
    p = _pilot_z_historia()
    L = liczniki_pilota(p, DZIEN)
    assert L["id"] == "P1"
    assert L["nalot_calkowity_h"] == 1009.0
    assert L["nalot_miesiac_h"] == 7.0
    assert L["godziny_symulatora_h"] == 12.0
    assert L["nalot_per_klasa_h"][HEMS.value] == 7.0


def test_log_lotow_maszyny():
    # Mini-stan: slot HEMS obsadzony, jedna maszyna lokalna; po przydziale log ma 1 lot.
    tr = TypeRating(HEMS, DZIEN - timedelta(days=20), DZIEN - timedelta(days=2), DZIEN + timedelta(days=300))
    piloci = [Pilot(id=f"P{i}", imie="x", nazwisko="y", kategoria=Kategoria.B,
                    baza_macierzysta="EPWA", type_ratings=[tr]) for i in (1, 2)]
    flota = [Maszyna("H1", HEMS, StatusMaszyny.OPERACYJNA, aktualny_hub="EPWA", nalot_h=40.0)]
    slot = SlotDyzurowy(id="S1", baza_id="EPWA", data=DZIEN, typ_dyzuru=TypDyzuru.DYZUR_24H,
                        wymagana_klasa=HEMS, wymagana_kategoria_min=Kategoria.B,
                        tryb_misji=TrybMisji.SINGLE_PILOT)
    r = Rdzen(piloci=piloci, flota=flota, huby=[], sloty=[slot])
    r.harmonogram()
    przydziel_maszyny(r)

    log = log_lotow_maszyny(r, "H1")
    assert len(log) == 1
    assert log[0]["godziny_h"] > 0
    assert len(log[0]["piloci"]) >= 1

    info = liczniki_maszyny(r, "H1")
    assert info is not None
    assert info["liczba_dyzurow"] == 1
    assert "log_lotow" in info
    assert liczniki_maszyny(r, "NIE_MA") is None
