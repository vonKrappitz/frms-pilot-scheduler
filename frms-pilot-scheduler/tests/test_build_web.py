# Copyright 2026 Maciej M. Kasperek ("vonKrappitz")
# SPDX-License-Identifier: Apache-2.0
"""
Testy generatora interfejsu web (frms.build_web).

Pilnują, że regeneracja produkuje spójny plik: parsowalny JSON, komplet funkcji
renderujących, świeże dane (Grand Caravan, plan 15 dni, symulator EPDE) i brak
pozostałości po starym modelu (KODIAK). Zamyka pułapkę zachłannej podmiany.
"""

import json
import re

from frms.build_web import zbuduj_web

FUNKCJE = [
    "renderDashboard", "renderHarmonogram", "renderPlan", "renderPiloci",
    "renderAlerty", "renderSesje", "renderSymulator", "renderLaw", "renderAwanse", "renderMapa", "renderSerwis", "renderCentrum", "renderAll",
    "showSection", "setLang", "planPrev", "planNext", "lawPrev", "lawNext",
    "lawZaliczRecovery", "lawZaliczRecurrent",
    "seatCell", "planTabela", "swapToggle", "swapPick", "swapRevert",
    "dodatkoweFotele", "trainPick", "trainRevert", "stolToggle", "stolPick",
    "lawSetLadowania", "serwWezwij",
]


def _zbuduj(tmp_path):
    sciezka = tmp_path / "frms-web.html"
    zbuduj_web(str(sciezka))
    return sciezka.read_text(encoding="utf-8")


def test_json_parsowalny_i_klucze(tmp_path):
    s = _zbuduj(tmp_path)
    m = re.search(r"const DANE = (\{.*?\});\s*\nlet currentLang", s, re.DOTALL)
    assert m, "nie znaleziono osadzonego const DANE"
    d = json.loads(m.group(1))
    for k in ("statystyki", "piloci", "sloty", "plan_15dni", "symulator_epde", "law_grafik_15dni", "alerty_kursy", "awanse", "serwis_prognoza", "centrum_live", "siec_reforma", "sesje_symulatorowe", "alerty"):
        assert k in d
    assert "kursy" in d["piloci"][0]
    assert len(d["law_grafik_15dni"]) == 15
    sloty = [x for dz in d["plan_15dni"] for x in dz["sloty"]]
    assert any(x.get("kandydaci_pic") for x in sloty), "brak pul kandydatów w planie"


def test_komplet_funkcji_renderujacych(tmp_path):
    s = _zbuduj(tmp_path)
    for fn in FUNKCJE:
        assert ("function " + fn in s) or (fn + "(" in s), f"brak funkcji {fn}"


def test_swieze_dane_bez_kodiaka(tmp_path):
    s = _zbuduj(tmp_path)
    assert "STOL_KODIAK_100" not in s
    assert "STOL_GRAND_CARAVAN_EX" in s


def test_plan_ma_15_dni(tmp_path):
    s = _zbuduj(tmp_path)
    d = json.loads(re.search(r"const DANE = (\{.*?\});\s*\nlet currentLang", s, re.DOTALL).group(1))
    assert len(d["plan_15dni"]) == 15
