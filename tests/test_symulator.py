# Copyright 2026 Maciej M. Kasperek ("vonKrappitz")
# SPDX-License-Identifier: Apache-2.0
"""Testy pojemności symulatora EPDE (frms.symulator)."""

from datetime import date, timedelta

from frms.models import KlasaMaszyny
from frms.data import generuj_pilotow
from frms.symulator import (
    ZapotrzebowanieSym, zaplanuj_z_zapotrzebowania, zaplanuj_symulator,
    _PRIO_RECURRENT, _PRIO_RECOVERY,
)

MEDEVAC = KlasaMaszyny.MEDEVAC_CIEZKI
HEMS = KlasaMaszyny.HEMS_SREDNI
LST = KlasaMaszyny.LST_LEKKI
D0 = date(2026, 4, 1)  # początek Q2


def _rec(pid, klasa, od, do):
    return ZapotrzebowanieSym(pid, klasa, "RECURRENT", 2, od, do, _PRIO_RECURRENT, "rec")


def _rcv(pid, klasa, od, do, prio="WYSOKI"):
    return ZapotrzebowanieSym(pid, klasa, "RECOVERY", 1, od, do, _PRIO_RECOVERY[prio], "rcv")


def _bez_kolizji_klasa_dzien(przydzialy):
    widziane = set()
    for z, dni in przydzialy:
        for d in dni:
            klucz = (z.klasa, d)
            if klucz in widziane:
                return False
            widziane.add(klucz)
    return True


def _bez_kolizji_pilot_dzien(przydzialy):
    widziane = set()
    for z, dni in przydzialy:
        for d in dni:
            klucz = (z.pilot_id, d)
            if klucz in widziane:
                return False
            widziane.add(klucz)
    return True


def test_pojemnosc_jeden_na_klase_dzien():
    okno_do = D0 + timedelta(days=89)
    z = [_rec("P1", MEDEVAC, D0, okno_do), _rec("P2", MEDEVAC, D0, okno_do)]
    przydzialy, nieob = zaplanuj_z_zapotrzebowania(z)
    assert nieob == []
    assert len(przydzialy) == 2
    assert _bez_kolizji_klasa_dzien(przydzialy)
    # każdy recurrent to 2 kolejne dni
    for _, dni in przydzialy:
        assert len(dni) == 2 and (dni[1] - dni[0]).days == 1


def test_recovery_w_oknie():
    przydzialy, nieob = zaplanuj_z_zapotrzebowania([_rcv("P1", HEMS, D0, D0 + timedelta(days=5))])
    assert nieob == []
    (_, dni), = przydzialy
    assert D0 <= dni[0] <= D0 + timedelta(days=5)


def test_pilot_nie_w_dwoch_symulatorach_naraz():
    # ten sam pilot, dwie recovery różnych klas, to samo okno jednodniowe-ish
    okno = D0 + timedelta(days=3)
    z = [_rcv("P1", HEMS, D0, okno), _rcv("P1", LST, D0, okno)]
    przydzialy, nieob = zaplanuj_z_zapotrzebowania(z)
    assert nieob == []
    assert _bez_kolizji_pilot_dzien(przydzialy)
    dni_all = [d for _, dd in przydzialy for d in dd]
    assert len(set(dni_all)) == 2  # dwa różne dni dla tego samego pilota


def test_przepelnienie_zwraca_nieobsadzone():
    # jedna klasa, okno jednego dnia, dwie recovery różnych pilotów -> jedna nie wejdzie
    z = [_rcv("P1", HEMS, D0, D0), _rcv("P2", HEMS, D0, D0)]
    przydzialy, nieob = zaplanuj_z_zapotrzebowania(z)
    assert len(przydzialy) == 1 and len(nieob) == 1
    assert _bez_kolizji_klasa_dzien(przydzialy)


def test_recovery_przed_recurrentem_o_ten_sam_dzien_pilota():
    # ten sam pilot ma recovery (priorytet wyższy) i recurrent; recovery bierze dzień pierwszy
    okno_do = D0 + timedelta(days=89)
    z = [_rec("P1", MEDEVAC, D0, okno_do), _rcv("P1", HEMS, D0, D0 + timedelta(days=2))]
    przydzialy, nieob = zaplanuj_z_zapotrzebowania(z)
    assert nieob == []
    po_typie = {zz.typ: dni for zz, dni in przydzialy}
    # recovery umieszczone najwcześniej (D0), recurrent nie nachodzi na ten dzień pilota
    assert po_typie["RECOVERY"][0] == D0
    assert D0 not in po_typie["RECURRENT"]


def test_integracja_realni_piloci_niezmienniki():
    start = date(2026, 4, 1)
    piloci = generuj_pilotow(start)
    sloty, nieob = zaplanuj_symulator(piloci, start)
    # brak podwójnej rezerwacji symulatora klasy w dniu
    klasa_dzien = [(s.wymagana_klasa, s.data) for s in sloty]
    assert len(klasa_dzien) == len(set(klasa_dzien))
    # żaden pilot nie jest w dwóch symulatorach tego samego dnia
    pilot_dzien = [(s.przypisany_pilot_id, s.data) for s in sloty]
    assert len(pilot_dzien) == len(set(pilot_dzien))
    # wszystkie sloty w EPDE
    assert all(s.baza_id == "EPDE" for s in sloty)


