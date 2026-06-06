# Copyright 2026 Maciej M. Kasperek ("vonKrappitz")
# SPDX-License-Identifier: Apache-2.0
"""Testy prognozy serwisowej (frms.prognoza_serwis)."""

from datetime import date, timedelta

from frms.models import Maszyna, KlasaMaszyny, KonfiguracjaSerwisu, PoziomSerwisu
from frms.prognoza_serwis import (
    godziny_do_progow, najblizszy_przeglad, prognoza_dni, priorytet_wezwania,
    prognoza_maszyny, prognoza_floty, wezwania_priorytetowe,
)

S = KonfiguracjaSerwisu()
DZIEN = date(2026, 6, 3)
H145 = KlasaMaszyny.HEMS_SREDNI


def _maszyna(mid, nalot, hub="EPWA", serwis_do=None):
    return Maszyna(id=mid, klasa=H145, aktualny_hub=hub, nalot_h=nalot, w_serwisie_do=serwis_do)


def test_godziny_do_progow():
    m = _maszyna("H1", 95.0)
    g = godziny_do_progow(m, S)
    assert g[PoziomSerwisu.POBIEZNY] == 5.0      # 100 - 95
    assert g[PoziomSerwisu.POWAZNY] == 505.0     # 600 - 95
    assert g[PoziomSerwisu.REMONT] == 2905.0     # 3000 - 95


def test_najblizszy_i_prognoza_dni():
    m = _maszyna("H1", 95.0)
    poziom, godz = najblizszy_przeglad(m, S)
    assert poziom == PoziomSerwisu.POBIEZNY and godz == 5.0
    assert prognoza_dni(m, S, tempo=3.0) == 2     # ceil(5/3)
    assert prognoza_dni(m, S, tempo=5.0) == 1


def test_priorytet_progi():
    assert priorytet_wezwania(5.0) == "WYSOKI"
    assert priorytet_wezwania(10.0) == "WYSOKI"
    assert priorytet_wezwania(25.0) == "SREDNI"
    assert priorytet_wezwania(100.0) == "NISKI"


def test_prog_przekroczony_wysoki_zero_dni():
    m = _maszyna("H1", 108.0)   # po progu pobieżnym (100)
    poziom, godz = najblizszy_przeglad(m, S)
    assert poziom == PoziomSerwisu.POBIEZNY and godz == -8.0
    assert prognoza_dni(m, S) == 0
    assert prognoza_maszyny(m, S, DZIEN)["priorytet"] == "WYSOKI"


def test_prognoza_floty_i_wezwania():
    pilna = _maszyna("H1", 96.0)                          # 4 h do pobieżnego -> WYSOKI
    srednia = _maszyna("H2", 75.0)                        # 25 h -> SREDNI
    luzna = _maszyna("H3", 10.0)                          # 90 h -> NISKI
    w_serw = _maszyna("H4", 99.0, serwis_do=DZIEN + timedelta(days=2))  # pilna, ale w serwisie
    flota = [luzna, w_serw, srednia, pilna]
    pf = prognoza_floty(flota, S, DZIEN)
    assert pf[0]["maszyna_id"] == "H1"        # najpilniejsza pierwsza
    assert pf[-1]["maszyna_id"] == "H4"       # w serwisie na końcu
    wez = [w["maszyna_id"] for w in wezwania_priorytetowe(flota, S, DZIEN)]
    assert wez == ["H1", "H2"]                # H4 pominięta (w serwisie), H3 za luźna
