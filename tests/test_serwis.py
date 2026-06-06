# Copyright 2026 Maciej M. Kasperek ("vonKrappitz")
# SPDX-License-Identifier: Apache-2.0
"""
Testy bloku 3: reguły serwisu.

Sprawdzane: kierowanie poważnego/remontu do EPLB, pobieżnego do huba
macierzystego, czasy obsługi, wyłączenie z obsady na czas serwisu, powrót po
terminie, detekcja należnego przeglądu z zerowaniem progu po obsłudze.
"""

from datetime import date, timedelta

from frms.models import (
    Kategoria, KlasaMaszyny, Maszyna, PoziomSerwisu, Pilot, SlotDyzurowy,
    StatusMaszyny, TrybMisji, TypDyzuru, TypeRating,
)
from frms.rdzen import Rdzen
from frms.rejestr import przydziel_maszyny
from frms.serwis import (
    skieruj, w_serwisie, zwolnij_po_terminie, poziom_naleznego_przegladu,
    przegladaj_flote,
)

HEMS = KlasaMaszyny.HEMS_SREDNI
DZIEN = date(2026, 6, 2)


def _rdzen(maszyny, sloty=None, piloci=None):
    return Rdzen(piloci=piloci or [], flota=list(maszyny), huby=[], sloty=sloty or [])


def test_powazny_do_eplb_trzy_dni():
    r = _rdzen([Maszyna("H1", HEMS, StatusMaszyny.OPERACYJNA, aktualny_hub="EPWA", nalot_h=620.0)])
    wpis = skieruj(r, "H1", PoziomSerwisu.POWAZNY, DZIEN)
    assert wpis.miejsce == "EPLB"
    assert wpis.do_dnia == DZIEN + timedelta(days=3)
    m = r.maszyna("H1")
    assert m.w_serwisie_do == DZIEN + timedelta(days=3)
    assert len(m.historia_serwisow) == 1


def test_pobiezny_do_huba_macierzystego():
    r = _rdzen([Maszyna("H1", HEMS, StatusMaszyny.OPERACYJNA, aktualny_hub="EPKK", nalot_h=120.0)])
    wpis = skieruj(r, "H1", PoziomSerwisu.POBIEZNY, DZIEN)
    assert wpis.miejsce == "EPKK"  # hub macierzysty
    assert wpis.do_dnia == DZIEN + timedelta(days=1)


def test_remont_trzydziesci_dni_do_eplb():
    r = _rdzen([Maszyna("H1", HEMS, StatusMaszyny.OPERACYJNA, aktualny_hub="EPWA", nalot_h=3100.0)])
    wpis = skieruj(r, "H1", PoziomSerwisu.REMONT, DZIEN)
    assert wpis.miejsce == "EPLB"
    assert wpis.do_dnia == DZIEN + timedelta(days=30)


def test_maszyna_w_serwisie_wypada_z_obsady():
    # Jedyny egzemplarz HEMS w bazie, ale w serwisie → slot zostaje bez maszyny.
    tr = TypeRating(HEMS, DZIEN - timedelta(days=20), DZIEN - timedelta(days=2), DZIEN + timedelta(days=300))
    piloci = [Pilot(id=f"P{i}", imie="x", nazwisko="y", kategoria=Kategoria.B,
                    baza_macierzysta="EPWA", type_ratings=[tr]) for i in (1, 2)]
    slot = SlotDyzurowy(id="S1", baza_id="EPWA", data=DZIEN, typ_dyzuru=TypDyzuru.DYZUR_24H,
                        wymagana_klasa=HEMS, wymagana_kategoria_min=Kategoria.B,
                        tryb_misji=TrybMisji.SINGLE_PILOT)
    r = Rdzen(piloci=piloci, flota=[Maszyna("H1", HEMS, StatusMaszyny.OPERACYJNA, aktualny_hub="EPWA", nalot_h=620.0)],
              huby=[], sloty=[slot])
    skieruj(r, "H1", PoziomSerwisu.POWAZNY, DZIEN)
    r.harmonogram()
    wynik = przydziel_maszyny(r)
    assert slot.maszyna_id is None
    assert "S1" in wynik["bez_maszyny"]


def test_powrot_po_terminie():
    m = Maszyna("H1", HEMS, StatusMaszyny.OPERACYJNA, aktualny_hub="EPWA", nalot_h=620.0)
    r = _rdzen([m])
    skieruj(r, "H1", PoziomSerwisu.POWAZNY, DZIEN)  # do DZIEN+3
    assert w_serwisie(m, DZIEN) is True
    assert w_serwisie(m, DZIEN + timedelta(days=3)) is True   # ostatni dzień włącznie
    # następnego dnia po terminie zwalniamy
    zwolnione = zwolnij_po_terminie(r, DZIEN + timedelta(days=4))
    assert zwolnione == 1
    assert m.w_serwisie_do is None
    assert w_serwisie(m, DZIEN + timedelta(days=4)) is False


def test_detektor_progu_i_zerowanie_po_obsludze():
    s = __import__("frms.models", fromlist=["KonfiguracjaSerwisu"]).KonfiguracjaSerwisu()
    # nalot 650 > próg poważnego 600, < remontu 3000 → należny POWAZNY
    m = Maszyna("H1", HEMS, StatusMaszyny.OPERACYJNA, aktualny_hub="EPWA", nalot_h=650.0)
    assert poziom_naleznego_przegladu(m, s) == PoziomSerwisu.POWAZNY
    # po obsłudze poważnego próg się zeruje — poważny już nie należny
    r = _rdzen([m])
    skieruj(r, "H1", PoziomSerwisu.POWAZNY, DZIEN)
    # narósł od ostatniego poważnego = 0 < 600; ale pobieżny (próg 100) wciąż przekroczony
    assert poziom_naleznego_przegladu(m, s) == PoziomSerwisu.POBIEZNY
    # maszyna o niskim nalocie nie potrzebuje nic
    m2 = Maszyna("H2", HEMS, StatusMaszyny.OPERACYJNA, aktualny_hub="EPWA", nalot_h=50.0)
    assert poziom_naleznego_przegladu(m2, s) is None


def test_przegladaj_flote_pomija_juz_w_serwisie():
    m1 = Maszyna("H1", HEMS, StatusMaszyny.OPERACYJNA, aktualny_hub="EPWA", nalot_h=650.0)
    m2 = Maszyna("H2", HEMS, StatusMaszyny.OPERACYJNA, aktualny_hub="EPWA", nalot_h=50.0)
    r = _rdzen([m1, m2])
    skierowane = przegladaj_flote(r, DZIEN)
    assert len(skierowane) == 1  # tylko H1 (H2 świeża)
    # druga przebieg: H1 już w serwisie, nic nowego
    assert przegladaj_flote(r, DZIEN) == []
