# Copyright 2026 Maciej M. Kasperek ("vonKrappitz")
# SPDX-License-Identifier: Apache-2.0
"""Bezpośrednie testy doboru pary MEDEVAC (reguły obsady AW101).

Weryfikują nie tylko brak par zakazanych, ale przede wszystkim OSIĄGALNOŚĆ
każdej dozwolonej konfiguracji: C+C, C+D, D+D (operacyjne) oraz B+D
(nadzorowana, D jako PIC). Zakazane: C+B, B+B, sam jeden pilot, A w roli MEDEVAC.
"""
from datetime import date


from frms.models import (
    Pilot, TypeRating, SlotDyzurowy, Kategoria, KlasaMaszyny,
    TypDyzuru, Organizacja, TrybMisji,
)
from frms.scheduler import dobierz_pare_medevac

MED = KlasaMaszyny.MEDEVAC_CIEZKI
DZIEN = date(2026, 6, 1)


def _pilot(pid: str, kat: Kategoria) -> Pilot:
    return Pilot(
        id=pid, imie="X", nazwisko="Y", kategoria=kat,
        baza_macierzysta="EPWA", organizacja=Organizacja.LPR,
        type_ratings=[TypeRating(
            klasa=MED, data_uzyskania=date(2023, 1, 1),
            data_ostatniego_lotu=date(2026, 5, 20), data_waznosci=date(2028, 1, 1),
        )],
    )


def _slot() -> SlotDyzurowy:
    return SlotDyzurowy(
        id="M1", baza_id="EPWA", data=DZIEN, typ_dyzuru=TypDyzuru.ON_CALL_24H,
        wymagana_klasa=MED, wymagana_kategoria_min=Kategoria.C,
        tryb_misji=TrybMisji.DWA_PILOTY, organizacja=Organizacja.LPR,
    )


def _kat(res):
    return None if res is None else tuple(sorted([res[0].kategoria, res[1].kategoria], key=lambda k: k.name))


# --- konfiguracje dozwolone: każda musi być osiągalna ---

def test_para_cc():
    r = dobierz_pare_medevac(_slot(), [_pilot("c1", Kategoria.C), _pilot("c2", Kategoria.C)])
    assert r is not None and _kat(r) == (Kategoria.C, Kategoria.C)


def test_para_cd_osiagalna():
    r = dobierz_pare_medevac(_slot(), [_pilot("c1", Kategoria.C), _pilot("d1", Kategoria.D)])
    assert r is not None and _kat(r) == (Kategoria.C, Kategoria.D)
    assert r[0].kategoria == Kategoria.D  # PIC = D (wyższa kategoria)


def test_para_dd_osiagalna():
    r = dobierz_pare_medevac(_slot(), [_pilot("d1", Kategoria.D), _pilot("d2", Kategoria.D)])
    assert r is not None and _kat(r) == (Kategoria.D, Kategoria.D)


def test_para_bd_d_jest_pic():
    r = dobierz_pare_medevac(_slot(), [_pilot("b1", Kategoria.B), _pilot("d1", Kategoria.D)])
    assert r is not None and _kat(r) == (Kategoria.B, Kategoria.D)
    assert r[0].kategoria == Kategoria.D   # PIC = instruktor D
    assert r[1].kategoria == Kategoria.B   # FO = szkolony B; B nigdy nie jest PIC


# --- konfiguracje zakazane: muszą zwrócić None ---

def test_para_cb_zakazana():
    assert dobierz_pare_medevac(_slot(), [_pilot("c1", Kategoria.C), _pilot("b1", Kategoria.B)]) is None


def test_para_bb_zakazana():
    assert dobierz_pare_medevac(_slot(), [_pilot("b1", Kategoria.B), _pilot("b2", Kategoria.B)]) is None


def test_jeden_pilot_to_za_malo():
    assert dobierz_pare_medevac(_slot(), [_pilot("c1", Kategoria.C)]) is None


def test_b_nigdy_nie_jest_pic_medevac():
    """Niezależnie od dostępnej kadry B nie może być PIC na MEDEVAC."""
    pula = [_pilot("b1", Kategoria.B), _pilot("b2", Kategoria.B),
            _pilot("d1", Kategoria.D), _pilot("c1", Kategoria.C), _pilot("c2", Kategoria.C)]
    r = dobierz_pare_medevac(_slot(), pula)
    assert r is not None
    assert r[0].kategoria != Kategoria.B
