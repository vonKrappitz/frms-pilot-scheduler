# Copyright 2026 Maciej M. Kasperek ("vonKrappitz")
# SPDX-License-Identifier: Apache-2.0
"""Testy modułu centralnego i adaptera telemetrii (blok 10)."""

from datetime import date, timedelta

from frms.models import Maszyna, KlasaMaszyny, StatusMaszyny
from frms.porty import TelemetryProvider
from frms.telemetria import MockTelemetry, WSPOLRZEDNE_BAZ
from frms.centralny import status_maszyny, snapshot_floty

H145 = KlasaMaszyny.HEMS_SREDNI
DZIEN = date(2026, 6, 3)


def _maszyna(mid, hub="EPWA", status=StatusMaszyny.OPERACYJNA, serwis_do=None):
    return Maszyna(id=mid, klasa=H145, aktualny_hub=hub, status=status, w_serwisie_do=serwis_do)


def test_mock_implementuje_port():
    assert isinstance(MockTelemetry(), TelemetryProvider)


def test_deterministyczny_bez_rng():
    t = MockTelemetry()
    m = _maszyna("H1")
    assert t.pozycja(m) == t.pozycja(m)
    assert t.paliwo(m) == t.paliwo(m)
    assert t.czas_misji(m) == t.czas_misji(m)


def test_pozycja_w_okolicy_huba():
    t = MockTelemetry()
    m = _maszyna("H7", hub="EPKK")
    lat, lon = t.pozycja(m)
    bl, bn = WSPOLRZEDNE_BAZ["EPKK"]
    assert abs(lat - bl) <= 0.31 and abs(lon - bn) <= 0.41


def test_pozycja_brak_huba():
    assert MockTelemetry().pozycja(_maszyna("H1", hub="XXXX")) is None


def test_status_serwis_lot_ziemia():
    t = MockTelemetry()
    # w serwisie -> SERWIS niezależnie od telemetrii
    m_serw = _maszyna("H1", serwis_do=DZIEN + timedelta(days=2))
    assert status_maszyny(m_serw, t, DZIEN) == "SERWIS"
    # operacyjna: LOT gdy telemetria raportuje czas misji, inaczej ZIEMIA
    for mid in ["H1", "H2", "H3", "H4", "H5"]:
        m = _maszyna(mid)
        st = status_maszyny(m, t, DZIEN)
        assert st == ("LOT" if t.czas_misji(m) is not None else "ZIEMIA")


def test_snapshot_floty_podsumowanie():
    t = MockTelemetry()
    flota = [_maszyna(f"H{i}") for i in range(1, 8)]
    snap = snapshot_floty(flota, t, DZIEN)
    assert len(snap["maszyny"]) == 7
    assert sum(snap["podsumowanie"].values()) == 7
    assert snap["maszyny"][0]["status"] == "LOT" or all(m["status"] != "LOT" for m in snap["maszyny"])
