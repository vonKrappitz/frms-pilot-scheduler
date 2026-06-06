# Copyright 2026 Maciej M. Kasperek ("vonKrappitz")
# SPDX-License-Identifier: Apache-2.0
"""
Testy eksportu (M2): jedno źródło prawdy, komplet kluczy, serializowalność,
odporność na powtórzenie. Liczniki maszyn muszą być niepuste (blok 1 + 2 działają
w pełnym przebiegu).
"""

import json

from frms.export_json import eksport_do_json

STARE_KLUCZE = {"statystyki", "bazy", "piloci", "sloty", "alerty", "sesje_symulatorowe"}
NOWE_KLUCZE = {"liczniki_pilotow", "liczniki_maszyn", "obciazenie_floty"}


def test_eksport_ma_wszystkie_klucze():
    dane = eksport_do_json()
    assert STARE_KLUCZE.issubset(dane.keys())
    assert NOWE_KLUCZE.issubset(dane.keys())


def test_eksport_jest_serializowalny():
    dane = eksport_do_json()
    s = json.dumps(dane, ensure_ascii=False)
    assert len(s) > 0
    # round-trip
    assert json.loads(s)["statystyki"]["liczba_pilotow"] == dane["statystyki"]["liczba_pilotow"]


def test_sloty_maja_pole_maszyny():
    dane = eksport_do_json()
    assert dane["sloty"], "powinny być jakieś sloty"
    for s in dane["sloty"]:
        assert "maszyna_id" in s
        assert "maszyna_z_innej_bazy" in s


def test_liczniki_niepuste_w_pelnym_przebiegu():
    dane = eksport_do_json()
    assert len(dane["liczniki_pilotow"]) > 0
    # przynajmniej jedna maszyna realnie latała → liczniki maszyn niepuste
    assert len(dane["liczniki_maszyn"]) > 0
    # każdy licznik maszyny ma log lotów
    for m in dane["liczniki_maszyn"]:
        assert "log_lotow" in m


def test_eksport_powtarzalny():
    # Stały seed: dwa przebiegi dają tę samą liczbę pilotów i slotów.
    a = eksport_do_json()["statystyki"]
    b = eksport_do_json()["statystyki"]
    assert a["liczba_pilotow"] == b["liczba_pilotow"]
    assert a["liczba_slotow_operacyjnych"] == b["liczba_slotow_operacyjnych"]
    assert a["procent_obsadzenia"] == b["procent_obsadzenia"]
