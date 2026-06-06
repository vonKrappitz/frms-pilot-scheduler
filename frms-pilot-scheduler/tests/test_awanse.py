# Copyright 2026 Maciej M. Kasperek ("vonKrappitz")
# SPDX-License-Identifier: Apache-2.0
"""Testy zatwierdzania awansów (frms.awanse)."""

from datetime import date

from frms.models import Kategoria, KlasaMaszyny, Organizacja, Pilot, Misja, SkalaNACA, TypDyzuru
from frms.awanse import (
    nastepna_kategoria, latal_z, instruktorzy_zatwierdzajacy,
    liczba_zatwierdzajacych, ma_dosc_zatwierdzajacych, MIN_ZATWIERDZAJACYCH_D,
)

MEDEVAC = KlasaMaszyny.MEDEVAC_CIEZKI
DZIEN = date(2026, 6, 1)


def _pilot(pid, kat, misje=None):
    return Pilot(id=pid, imie=pid, nazwisko="X", kategoria=kat, baza_macierzysta="EPWA",
                 organizacja=Organizacja.LPR, historia_misji=misje or [])


def _misja_z(drugi_id):
    return Misja(DZIEN, 3.0, MEDEVAC, SkalaNACA.NACA_3, TypDyzuru.DYZUR_24H, drugi_pilot_id=drugi_id)


def test_nastepna_kategoria():
    assert nastepna_kategoria(Kategoria.A) == Kategoria.B
    assert nastepna_kategoria(Kategoria.C) == Kategoria.D
    assert nastepna_kategoria(Kategoria.D) is None


def test_latal_z_oba_kierunki():
    a = _pilot("A", Kategoria.C, [_misja_z("B")])
    b = _pilot("B", Kategoria.D)
    assert latal_z(a, b) is True   # powiązanie po stronie a
    c = _pilot("C", Kategoria.C)
    d = _pilot("D", Kategoria.D, [_misja_z("C")])
    assert latal_z(c, d) is True   # powiązanie po stronie d
    e = _pilot("E", Kategoria.C)
    f = _pilot("F", Kategoria.D)
    assert latal_z(e, f) is False  # brak wspólnego lotu


def test_zatwierdzajacy_tylko_D_ze_wspolna_historia():
    kand = _pilot("K", Kategoria.C, [_misja_z("D1"), _misja_z("D2"), _misja_z("D3")])
    d1 = _pilot("D1", Kategoria.D)
    d2 = _pilot("D2", Kategoria.D)
    d3 = _pilot("D3", Kategoria.D)
    d_obcy = _pilot("D9", Kategoria.D)            # D, ale brak wspólnego lotu
    c_inny = _pilot("C2", Kategoria.C, [_misja_z("K")])  # latał z K, ale nie jest D
    pula = [kand, d1, d2, d3, d_obcy, c_inny]
    zatw = {p.id for p in instruktorzy_zatwierdzajacy(kand, pula)}
    assert zatw == {"D1", "D2", "D3"}
    assert ma_dosc_zatwierdzajacych(kand, pula) is True
    assert MIN_ZATWIERDZAJACYCH_D == 3


def test_za_malo_zatwierdzajacych():
    kand = _pilot("K", Kategoria.C, [_misja_z("D1"), _misja_z("D2")])
    pula = [kand, _pilot("D1", Kategoria.D), _pilot("D2", Kategoria.D)]
    assert liczba_zatwierdzajacych(kand, pula) == 2
    assert ma_dosc_zatwierdzajacych(kand, pula) is False


# ---- eligibility do awansu i limit ucznia (blok 6 cz. 2) ----
from frms.models import Kurs
from frms.kursy import KURSY_HEMS, KURSY_MEDEVAC
from frms.awanse import (
    nalot_calkowity, spelnia_kursy_do_awansu, kwalifikuje_sie_do_awansu,
    liczba_szkolen_ucznia_w_oknie, moze_przyjac_szkolenie,
)
from datetime import timedelta


def _misja(dni_temu, godz, szkoleniowy=False, sym=False, drugi=None):
    return Misja(DZIEN - timedelta(days=dni_temu), godz, MEDEVAC, SkalaNACA.NACA_3,
                 TypDyzuru.DYZUR_24H, czy_symulator=sym, czy_szkoleniowy=szkoleniowy, drugi_pilot_id=drugi)


def test_nalot_calkowity_bez_symulatora():
    p = _pilot("P", Kategoria.C, [_misja(2, 3.0), _misja(5, 4.0), _misja(8, 6.0, sym=True)])
    p.nalot_logbook_h = 1000.0
    assert nalot_calkowity(p) == 1007.0  # 1000 + 3 + 4; sesja sym pominięta


def test_kursy_wchodza_szczeblami():
    # A→B: wystarczą kursy HEMS (noc + gogle)
    a = _pilot("A", Kategoria.A)
    assert spelnia_kursy_do_awansu(a, Kategoria.B) is False  # brak kursów
    a.kursy = list(KURSY_HEMS)
    assert spelnia_kursy_do_awansu(a, Kategoria.B) is True
    # B→C: dochodzą wciągarka i FIKI — sam HEMS nie wystarcza
    b = _pilot("B", Kategoria.B); b.kursy = list(KURSY_HEMS)
    assert spelnia_kursy_do_awansu(b, Kategoria.C) is False  # brak wciągarki i FIKI
    b.kursy = list(KURSY_MEDEVAC)
    assert spelnia_kursy_do_awansu(b, Kategoria.C) is True
    # brak choćby jednego z dwóch nowych kursów dalej blokuje C
    b.kursy = [k for k in KURSY_MEDEVAC if k != Kurs.FIKI]
    assert spelnia_kursy_do_awansu(b, Kategoria.C) is False
    # C→D: bez nowych kursów
    assert spelnia_kursy_do_awansu(_pilot("X", Kategoria.C), Kategoria.D) is True


def test_kwalifikacja_pelna_C_na_D():
    kand = _pilot("K", Kategoria.C, [_misja(1, 1.0, drugi="D1"), _misja(2, 1.0, drugi="D2"), _misja(3, 1.0, drugi="D3")])
    kand.nalot_logbook_h = 2100.0
    pula = [kand, _pilot("D1", Kategoria.D), _pilot("D2", Kategoria.D), _pilot("D3", Kategoria.D)]
    wynik = kwalifikuje_sie_do_awansu(kand, pula, DZIEN)
    assert wynik["cel"] == "D" and wynik["kwalifikuje"] is True
    # za mało nalotu
    kand.nalot_logbook_h = 100.0
    assert kwalifikuje_sie_do_awansu(kand, pula, DZIEN)["kwalifikuje"] is False


def test_limit_szkolen_ucznia():
    p = _pilot("U", Kategoria.B, [_misja(1, 2.0, szkoleniowy=True), _misja(3, 2.0, szkoleniowy=True)])
    assert liczba_szkolen_ucznia_w_oknie(p, DZIEN) == 2
    assert moze_przyjac_szkolenie(p, DZIEN) is False
    # sesje sym i stare loty nie liczą
    p2 = _pilot("U2", Kategoria.B, [_misja(1, 2.0, szkoleniowy=True, sym=True), _misja(20, 2.0, szkoleniowy=True)])
    assert liczba_szkolen_ucznia_w_oknie(p2, DZIEN) == 0
    assert moze_przyjac_szkolenie(p2, DZIEN) is True
