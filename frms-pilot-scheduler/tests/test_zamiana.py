# Copyright 2026 Maciej M. Kasperek ("vonKrappitz")
# SPDX-License-Identifier: Apache-2.0
"""
Testy puli zamienników (frms.zamiana).

Reguła kategorii twarda, wyjątek szkoleniowy: drugi fotel, PIC kat D, kandydat
dokładnie jedną kategorię poniżej minimum, oznaczony jako lot szkoleniowy.
"""

from datetime import date, timedelta

from frms.models import (
    Kategoria, KlasaMaszyny, Organizacja, Pilot, SlotDyzurowy, TrybMisji,
    TypDyzuru, TypeRating, Misja, SkalaNACA,
)
from frms.zamiana import kandydaci_zamiany

MEDEVAC = KlasaMaszyny.MEDEVAC_CIEZKI
HEMS = KlasaMaszyny.HEMS_SREDNI
DZIEN = date(2026, 6, 2)


def _tr(klasa):
    return TypeRating(klasa, DZIEN - timedelta(days=400), DZIEN - timedelta(days=5),
                      DZIEN + timedelta(days=360))


def _pilot(pid, kat, klasy):
    from frms.kursy import WSZYSTKIE_KURSY
    return Pilot(id=pid, imie=pid, nazwisko="X", kategoria=kat, baza_macierzysta="EPWA",
                 organizacja=Organizacja.LPR, type_ratings=[_tr(k) for k in klasy],
                 kursy=list(WSZYSTKIE_KURSY))


def _slot_medevac(pic_id, fo_id):
    # MEDEVAC zawsze dwuosobowy; ZMIANA_6H aby pominąć bramkę odpoczynku 24h w teście
    return SlotDyzurowy(id="S1", baza_id="EPWA", data=DZIEN, typ_dyzuru=TypDyzuru.ZMIANA_6H,
                        wymagana_klasa=MEDEVAC, wymagana_kategoria_min=Kategoria.C,
                        tryb_misji=TrybMisji.DWA_PILOTY,
                        przypisany_pilot_id=pic_id, drugi_pilot_id=fo_id)


def test_normalny_kandydat_spelnia_minimum():
    pic_D = _pilot("D1", Kategoria.D, [MEDEVAC])
    fo_stary = _pilot("C_old", Kategoria.C, [MEDEVAC])
    kand_C = _pilot("C_new", Kategoria.C, [MEDEVAC])
    slot = _slot_medevac("D1", "C_old")
    pula = kandydaci_zamiany(slot, "C_old", [pic_D, fo_stary, kand_C], [slot])
    ids = {k.pilot.id for k in pula}
    assert "C_new" in ids
    assert all(not k.lot_szkoleniowy for k in pula if k.pilot.id == "C_new")
    assert "D1" not in ids  # PIC już obsadzony


def test_wyjatek_szkoleniowy_B_przy_PIC_D():
    pic_D = _pilot("D1", Kategoria.D, [MEDEVAC])
    fo_stary = _pilot("C_old", Kategoria.C, [MEDEVAC])
    b = _pilot("B1", Kategoria.B, [HEMS])  # B bez ratingu MEDEVAC — ścieżka szkoleniowa
    a = _pilot("A1", Kategoria.A, [])       # A dwie kategorie poniżej C — nigdy
    slot = _slot_medevac("D1", "C_old")
    pula = kandydaci_zamiany(slot, "C_old", [pic_D, fo_stary, b, a], [slot])
    szk = {k.pilot.id: k for k in pula if k.lot_szkoleniowy}
    assert "B1" in szk
    assert szk["B1"].nadzorujacy_id == "D1"
    assert "lot szkoleniowy" in szk["B1"].adnotacja
    assert "A1" not in {k.pilot.id for k in pula}  # dwie poniżej minimum


def test_brak_wyjatku_gdy_PIC_nie_D():
    pic_C = _pilot("C_pic", Kategoria.C, [MEDEVAC])
    b = _pilot("B1", Kategoria.B, [HEMS])
    slot = _slot_medevac("C_pic", "C_old")
    pula = kandydaci_zamiany(slot, "C_old", [pic_C, b], [slot])
    assert "B1" not in {k.pilot.id for k in pula}  # PIC nie jest D


def test_brak_wyjatku_na_pierwszym_fotelu():
    # Zwalniamy PIC: kandydat poniżej minimum nigdy nie wchodzi na pierwszy fotel
    pic_old = _pilot("C_pic", Kategoria.C, [MEDEVAC])
    fo_D = _pilot("D1", Kategoria.D, [MEDEVAC])
    b = _pilot("B1", Kategoria.B, [HEMS])
    slot = SlotDyzurowy(id="S1", baza_id="EPWA", data=DZIEN, typ_dyzuru=TypDyzuru.ZMIANA_6H,
                        wymagana_klasa=MEDEVAC, wymagana_kategoria_min=Kategoria.C,
                        tryb_misji=TrybMisji.DWA_PILOTY,
                        przypisany_pilot_id="C_pic", drugi_pilot_id="D1")
    pula = kandydaci_zamiany(slot, "C_pic", [pic_old, fo_D, b], [slot])
    assert "B1" not in {k.pilot.id for k in pula}


def test_hems_analog_A_przy_PIC_D():
    # HEMS min B, PIC kat D, drugi fotel: A (jedna poniżej) jako szkoleniowy
    slot = SlotDyzurowy(id="H1", baza_id="EPWA", data=DZIEN, typ_dyzuru=TypDyzuru.ZMIANA_6H,
                        wymagana_klasa=HEMS, wymagana_kategoria_min=Kategoria.B,
                        tryb_misji=TrybMisji.DWA_PILOTY,
                        przypisany_pilot_id="D1", drugi_pilot_id="B_old")
    pic_D = _pilot("D1", Kategoria.D, [HEMS])
    b_old = _pilot("B_old", Kategoria.B, [HEMS])
    a = _pilot("A1", Kategoria.A, [])
    pula = kandydaci_zamiany(slot, "B_old", [pic_D, b_old, a], [slot])
    szk = {k.pilot.id: k for k in pula if k.lot_szkoleniowy}
    assert "A1" in szk and szk["A1"].nadzorujacy_id == "D1"


def test_wyklucza_zajetych_tego_dnia():
    pic_D = _pilot("D1", Kategoria.D, [MEDEVAC])
    fo_stary = _pilot("C_old", Kategoria.C, [MEDEVAC])
    zajety = _pilot("C_busy", Kategoria.C, [MEDEVAC])
    slot = _slot_medevac("D1", "C_old")
    inny = SlotDyzurowy(id="S2", baza_id="EPKK", data=DZIEN, typ_dyzuru=TypDyzuru.ZMIANA_6H,
                        wymagana_klasa=MEDEVAC, wymagana_kategoria_min=Kategoria.C,
                        tryb_misji=TrybMisji.DWA_PILOTY, przypisany_pilot_id="C_busy")
    pula = kandydaci_zamiany(slot, "C_old", [pic_D, fo_stary, zajety], [slot, inny])
    assert "C_busy" not in {k.pilot.id for k in pula}


def test_wyklucza_wymagajacych_recovery():
    # C z ratingiem, ale 60 dni bez lotu na MEDEVAC -> wymaga recovery -> poza pulą normalną
    pic_D = _pilot("D1", Kategoria.D, [MEDEVAC])
    fo_stary = _pilot("C_old", Kategoria.C, [MEDEVAC])
    stary_lot = DZIEN - timedelta(days=60)
    c_recovery = Pilot(id="C_rec", imie="x", nazwisko="x", kategoria=Kategoria.C,
                       baza_macierzysta="EPWA", organizacja=Organizacja.LPR,
                       type_ratings=[TypeRating(MEDEVAC, DZIEN - timedelta(days=400),
                                                stary_lot, DZIEN + timedelta(days=360))],
                       historia_misji=[Misja(stary_lot, 3.0, MEDEVAC, SkalaNACA.NACA_3,
                                             TypDyzuru.ZMIANA_6H)])
    slot = _slot_medevac("D1", "C_old")
    pula = kandydaci_zamiany(slot, "C_old", [pic_D, fo_stary, c_recovery], [slot])
    assert "C_rec" not in {k.pilot.id for k in pula}


# ---- fotel szkoleniowy przy maszynie jednoosobowej z kat D ----
STOL = KlasaMaszyny.STOL_SAMOLOT


LST = KlasaMaszyny.LST_LEKKI


def _slot_lst_single(pic_id):
    return SlotDyzurowy(id="L1", baza_id="EPKK", data=DZIEN, typ_dyzuru=TypDyzuru.ON_CALL_24H,
                        wymagana_klasa=LST, wymagana_kategoria_min=Kategoria.A,
                        tryb_misji=TrybMisji.SINGLE_PILOT, przypisany_pilot_id=pic_id)


def _slot_stol_single(pic_id, trudny=False):
    return SlotDyzurowy(id="ST1", baza_id="EPKT", data=DZIEN, typ_dyzuru=TypDyzuru.ON_CALL_24H,
                        wymagana_klasa=STOL, wymagana_kategoria_min=Kategoria.A,
                        tryb_misji=TrybMisji.SINGLE_PILOT,
                        przypisany_pilot_id=pic_id, trudny_lot=trudny)


def test_fotel_szkoleniowy_single_z_D():
    from frms.zamiana import kandydaci_szkoleniowi
    instr = _pilot("D1", Kategoria.D, [LST])
    c = _pilot("C1", Kategoria.C, [])      # bez ratingu — szkolenie nie wymaga
    d2 = _pilot("D2", Kategoria.D, [LST]) # D może szkolić innego D
    a = _pilot("A1", Kategoria.A, [LST])
    slot = _slot_lst_single("D1")
    pula = kandydaci_szkoleniowi(slot, [instr, c, d2, a], [slot])
    ids = {k.pilot.id for k in pula}
    assert {"C1", "D2", "A1"} <= ids
    assert "D1" not in ids                       # instruktor wypada
    assert all(k.lot_szkoleniowy for k in pula)
    assert all(k.nadzorujacy_id == "D1" for k in pula)


def test_fotel_szkoleniowy_pusty_gdy_PIC_nie_D():
    from frms.zamiana import kandydaci_szkoleniowi
    pic_c = _pilot("C_pic", Kategoria.C, [LST])
    a = _pilot("A1", Kategoria.A, [LST])
    slot = _slot_lst_single("C_pic")
    assert kandydaci_szkoleniowi(slot, [pic_c, a], [slot]) == []


def test_fotel_szkoleniowy_pomija_dwuosobowe():
    from frms.zamiana import kandydaci_szkoleniowi
    pic_D = _pilot("D1", Kategoria.D, [MEDEVAC])
    c = _pilot("C1", Kategoria.C, [MEDEVAC])
    slot = _slot_medevac("D1", None)   # MEDEVAC = dwuosobowy operacyjnie
    assert kandydaci_szkoleniowi(slot, [pic_D, c], [slot]) == []


# ---- trudny lot STOL: drugi pilot operacyjny ----
def test_trudny_lot_stol_obserwator():
    from frms.zamiana import kandydaci_obserwatora_stol
    from datetime import timedelta
    pic = _pilot("A_pic", Kategoria.A, [STOL])         # kapitan STOL
    # B/C/D z prywatną biegłością STOL (samozgłoszenie + świeże godziny)
    mentor = _pilot("D_men", Kategoria.D, [MEDEVAC]); mentor.stol_prywatnie = True; mentor.stol_rejestr = [(DZIEN - timedelta(days=15), 4.0)]
    wsparcie = _pilot("C_ws", Kategoria.C, [MEDEVAC]); wsparcie.stol_prywatnie = True; wsparcie.stol_rejestr = [(DZIEN - timedelta(days=15), 3.0)]
    stale = _pilot("B_stale", Kategoria.B, [HEMS]); stale.stol_prywatnie = True; stale.stol_rejestr = []  # zadeklarował, brak świeżych godzin
    niezgl = _pilot("C_no", Kategoria.C, [MEDEVAC])     # nie zgłosił prywatnego STOL
    inny_A = _pilot("A_other", Kategoria.A, [STOL])     # A jest kapitanem, nie obserwatorem
    slot = _slot_stol_single("A_pic", trudny=True)
    pula = kandydaci_obserwatora_stol(slot, [pic, mentor, wsparcie, stale, niezgl, inny_A], [slot])
    ids = [k.pilot.id for k in pula]
    assert set(ids) == {"D_men", "C_ws"}               # tylko biegli prywatnie B/C/D
    assert "B_stale" not in ids and "C_no" not in ids and "A_other" not in ids and "A_pic" not in ids
    assert all(k.obserwator and not k.lot_szkoleniowy for k in pula)
    assert ids[0] == "D_men"                            # mentor (kat D) przed wsparciem


def test_trudny_lot_wylaczony_pusto():
    from frms.zamiana import kandydaci_obserwatora_stol
    pic = _pilot("A_pic", Kategoria.A, [STOL])
    m = _pilot("D_men", Kategoria.D, [MEDEVAC]); m.stol_prywatnie = True
    slot = _slot_stol_single("A_pic", trudny=False)
    assert kandydaci_obserwatora_stol(slot, [pic, m], [slot]) == []


def test_fotel_szkoleniowy_prog_kandydata():
    # Syntetyczny slot jednoosobowy z minimum C: D szkoli B/C/D, ale nie A
    # (A musi najpierw zrobić B). Sprawdza próg "jedna poniżej minimum klasy".
    from frms.zamiana import kandydaci_szkoleniowi
    slot = SlotDyzurowy(id="X1", baza_id="EPKT", data=DZIEN, typ_dyzuru=TypDyzuru.ON_CALL_24H,
                        wymagana_klasa=HEMS, wymagana_kategoria_min=Kategoria.C,
                        tryb_misji=TrybMisji.SINGLE_PILOT, przypisany_pilot_id="D1")
    instr = _pilot("D1", Kategoria.D, [HEMS])
    a = _pilot("A1", Kategoria.A, [HEMS])
    b = _pilot("B1", Kategoria.B, [])
    c = _pilot("C1", Kategoria.C, [])
    pula = {k.pilot.id for k in kandydaci_szkoleniowi(slot, [instr, a, b, c], [slot])}
    assert "A1" not in pula           # dwie poniżej minimum C
    assert {"B1", "C1"} <= pula       # B jedna poniżej, C na poziomie


# ---- bramkowanie kursów i urlopu (blok 5) ----
def test_wyklucza_brak_kursu_na_medevac():
    from frms.kursy import WSZYSTKIE_KURSY
    from frms.models import Kurs
    pic_D = _pilot("D1", Kategoria.D, [MEDEVAC])
    fo_stary = _pilot("C_old", Kategoria.C, [MEDEVAC])
    bez_fiki = _pilot("C_x", Kategoria.C, [MEDEVAC])
    bez_fiki.kursy = [k for k in WSZYSTKIE_KURSY if k != Kurs.FIKI]  # brak jednego kursu
    slot = _slot_medevac("D1", "C_old")
    pula = kandydaci_zamiany(slot, "C_old", [pic_D, fo_stary, bez_fiki], [slot])
    assert "C_x" not in {k.pilot.id for k in pula}


def test_wyklucza_pilota_na_urlopie():
    pic_D = _pilot("D1", Kategoria.D, [MEDEVAC])
    fo_stary = _pilot("C_old", Kategoria.C, [MEDEVAC])
    urlop = _pilot("C_u", Kategoria.C, [MEDEVAC])
    urlop.dni_wolne = [DZIEN]
    slot = _slot_medevac("D1", "C_old")
    pula = kandydaci_zamiany(slot, "C_old", [pic_D, fo_stary, urlop], [slot])
    assert "C_u" not in {k.pilot.id for k in pula}
