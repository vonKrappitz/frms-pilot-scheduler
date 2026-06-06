# Copyright 2026 Maciej M. Kasperek ("vonKrappitz")
# SPDX-License-Identifier: Apache-2.0
"""
Testy szkieletu (blok 0): Rdzen jako jedno źródło prawdy + port telemetrii.

Nie dotykają istniejących testów ani plików rdzenia — sprawdzają tylko, że
nowy kontener buduje się z fixtures, akcesory działają, a opakowanie
schedulera daje ten sam wynik co wywołanie czystej funkcji wprost.
"""

from datetime import date

from frms.rdzen import Rdzen
from frms.porty import TelemetryProvider
from frms.models import KlasaMaszyny, StatusMaszyny
from frms.scheduler import generuj_harmonogram

DZIEN = date(2026, 6, 2)


def test_rdzen_buduje_sie_z_danych():
    r = Rdzen.domyslny(DZIEN)
    assert len(r.flota) == 51
    assert len(r.piloci) > 0
    assert len(r.huby) > 0
    assert len(r.sloty) > 0


def test_akcesory_odczytu():
    r = Rdzen.domyslny(DZIEN)
    # maszyna po ID
    assert r.maszyna("H1") is not None
    assert r.maszyna("NIE_MA") is None
    # tylko operacyjne vs wszystkie
    op = r.maszyny_klasy(KlasaMaszyny.LST_LEKKI, tylko_operacyjne=True)
    wszystkie = r.maszyny_klasy(KlasaMaszyny.LST_LEKKI, tylko_operacyjne=False)
    assert all(m.status == StatusMaszyny.OPERACYJNA for m in op)
    assert len(wszystkie) >= len(op)
    # pilot po ID
    pierwszy = r.piloci[0]
    assert r.pilot(pierwszy.id) is pierwszy


def test_akcesory_zapisu():
    r = Rdzen.domyslny(DZIEN)
    m = r.maszyny_klasy(KlasaMaszyny.HEMS_SREDNI)[0]
    assert r.przydziel_maszyne_do_huba(m.id, "EPKK") is True
    assert r.maszyna(m.id).aktualny_hub == "EPKK"
    assert m in r.maszyny_huba("EPKK")
    # usuwanie pilota
    pid = r.piloci[0].id
    assert r.usun_pilota(pid) is True
    assert r.pilot(pid) is None
    assert r.usun_pilota("NIE_MA") is False


def test_harmonogram_parity():
    # Opakowanie Rdzen.harmonogram() musi wołać generuj_harmonogram(sloty, piloci)
    # w tej kolejności. generuj_pilotow czerpie z globalnego RNG, więc dwa osobne
    # przebiegi dają różne populacje — porównujemy oba wywołania na deepcopy JEDNEGO
    # stanu, żeby wejście było identyczne.
    import copy
    r = Rdzen.domyslny(DZIEN)
    r_a = Rdzen(
        piloci=copy.deepcopy(r.piloci), sloty=copy.deepcopy(r.sloty),
        flota=r.flota, huby=r.huby, konfiguracja=r.konfiguracja,
    )
    sloty_b, piloci_b = copy.deepcopy(r.sloty), copy.deepcopy(r.piloci)

    obs1, nieobs1 = r_a.harmonogram()
    obs2, nieobs2 = generuj_harmonogram(sloty_b, piloci_b)
    assert len(obs1) == len(obs2)
    assert len(nieobs1) == len(nieobs2)


def test_port_jest_protokolem():
    # Klasa implementująca wszystkie metody spełnia kontrakt (runtime_checkable).
    class PustaTelemetria:
        def pozycja(self, maszyna): return None
        def paliwo(self, maszyna): return None
        def czas_misji(self, maszyna): return None
        def zaloga(self, maszyna): return []

    assert isinstance(PustaTelemetria(), TelemetryProvider)
