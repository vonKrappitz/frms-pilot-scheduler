# Copyright 2026 Maciej M. Kasperek ("vonKrappitz")
# SPDX-License-Identifier: Apache-2.0
"""
Testy bloku 1: dobór egzemplarza i rejestr per maszyna.

Mini-stan budowany ręcznie (bez losowych fixtures), żeby reguły — lokalnie
najpierw, separacja serwisowa, pomijanie serwisu, fallback krajowy, brak
podwójnej rezerwacji, ostemplowanie misji — dało się sprawdzić jednoznacznie.
"""

from datetime import date, timedelta

from frms.models import (
    Kategoria, KlasaMaszyny, Maszyna, Pilot, SlotDyzurowy, StatusMaszyny,
    TrybMisji, TypDyzuru, TypeRating,
)
from frms.rdzen import Rdzen
from frms.rejestr import (
    przydziel_maszyny, nalot_maszyny, kto_latal, obciazenie_floty,
)

DZIEN = date(2026, 6, 2)
HEMS = KlasaMaszyny.HEMS_SREDNI


def _pilot(pid: str, kat: Kategoria = Kategoria.B, baza: str = "EPWA"):
    tr = TypeRating(HEMS, DZIEN - timedelta(days=20), DZIEN - timedelta(days=2), DZIEN + timedelta(days=300))
    return Pilot(id=pid, imie="x", nazwisko="y", kategoria=kat, baza_macierzysta=baza, type_ratings=[tr])


def _slot(sid: str, baza: str):
    # HEMS single-pilot 24h: bez historii dyżurów 24h pilot jest gotowy (48h+).
    return SlotDyzurowy(
        id=sid, baza_id=baza, data=DZIEN, typ_dyzuru=TypDyzuru.DYZUR_24H,
        wymagana_klasa=HEMS, wymagana_kategoria_min=Kategoria.B,
        tryb_misji=TrybMisji.SINGLE_PILOT,
    )


def _maszyna(mid: str, hub: str, nalot: float, status=StatusMaszyny.OPERACYJNA):
    return Maszyna(mid, HEMS, status, aktualny_hub=hub, nalot_h=nalot)


def _zbuduj(maszyny, sloty, piloci=None):
    if piloci is None:
        piloci = [_pilot("P1"), _pilot("P2")]
    r = Rdzen(piloci=piloci, flota=list(maszyny), huby=[], sloty=list(sloty))
    r.harmonogram()  # obsadza sloty pilotami i tworzy misje
    return r


def test_lokalna_maszyna_pierwsza():
    # H1 lokalny (EPWA, niżej w cyklu), H2 krajowy (EPKK, wyżej). Wygrywa lokalny.
    r = _zbuduj([_maszyna("H1", "EPWA", 50.0), _maszyna("H2", "EPKK", 90.0)], [_slot("S1", "EPWA")])
    przydziel_maszyny(r)
    slot = r.sloty[0]
    assert slot.maszyna_id == "H1"
    assert slot.maszyna_z_innej_bazy is False


def test_separacja_serwisowa_lokalnie():
    # Dwa lokalne: H2 bliżej progu pobieżnego (90 > 50) — dociążamy H2.
    r = _zbuduj([_maszyna("H1", "EPWA", 50.0), _maszyna("H2", "EPWA", 90.0)], [_slot("S1", "EPWA")])
    przydziel_maszyny(r)
    assert r.sloty[0].maszyna_id == "H2"


def test_pomija_serwis():
    # H1 lokalny ale w serwisie do jutra; bierzemy H3 (też lokalny, dostępny).
    h1 = _maszyna("H1", "EPWA", 90.0)
    h3 = _maszyna("H3", "EPWA", 30.0)
    r = _zbuduj([h1, h3], [_slot("S1", "EPWA")])
    r.ustaw_serwis_maszyny("H1", DZIEN + timedelta(days=1), "EPLB")
    przydziel_maszyny(r)
    assert r.sloty[0].maszyna_id == "H3"


def test_fallback_krajowy_oznaczony():
    # Brak maszyny w bazie EPWA; jedyna jest w EPKK. Sprowadzenie + repozycja huba.
    r = _zbuduj([_maszyna("H2", "EPKK", 70.0)], [_slot("S1", "EPWA")])
    przydziel_maszyny(r)
    slot = r.sloty[0]
    assert slot.maszyna_id == "H2"
    assert slot.maszyna_z_innej_bazy is True
    assert r.maszyna("H2").aktualny_hub == "EPWA"  # przyleciała do bazy slotu


def test_brak_podwojnej_rezerwacji_tego_samego_dnia():
    # Dwa sloty EPWA tego samego dnia, jedna maszyna. Drugi zostaje bez maszyny.
    r = _zbuduj([_maszyna("H1", "EPWA", 40.0)], [_slot("S1", "EPWA"), _slot("S2", "EPWA")])
    wynik = przydziel_maszyny(r)
    przydzielone = [s for s in r.sloty if s.maszyna_id is not None]
    assert len(przydzielone) == 1
    assert wynik["bez_maszyny"]  # drugi slot zaraportowany jako bez maszyny


def test_misja_ostemplowana():
    r = _zbuduj([_maszyna("H1", "EPWA", 40.0)], [_slot("S1", "EPWA")])
    przydziel_maszyny(r)
    pic_id = r.sloty[0].przypisany_pilot_id
    pic = r.pilot(pic_id)
    misje_h1 = [m for m in pic.historia_misji if m.maszyna_id == "H1" and m.data == DZIEN]
    assert len(misje_h1) >= 1


def test_nalot_i_kto_latal():
    r = _zbuduj([_maszyna("H1", "EPWA", 40.0)], [_slot("S1", "EPWA")])
    przydziel_maszyny(r)
    info = nalot_maszyny(r, "H1")
    assert info is not None
    assert info["liczba_dyzurow"] == 1
    assert info["nalot_razem_h"] >= 40.0
    log = kto_latal(r.piloci, "H1")
    assert len(log) == 1
    assert len(log[0]["piloci"]) >= 1
    assert nalot_maszyny(r, "NIE_MA") is None


def test_obciazenie_floty_pokrywa_cala_flote():
    r = _zbuduj([_maszyna("H1", "EPWA", 40.0), _maszyna("H2", "EPKK", 60.0)], [_slot("S1", "EPWA")])
    przydziel_maszyny(r)
    ob = obciazenie_floty(r)
    assert set(ob.keys()) == {"H1", "H2"}
    assert ob["H1"]["liczba_dyzurow"] == 1
    assert ob["H2"]["liczba_dyzurow"] == 0  # nieużyta
