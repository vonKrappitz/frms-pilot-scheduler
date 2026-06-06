# Copyright 2026 Maciej M. Kasperek ("vonKrappitz")
# SPDX-License-Identifier: Apache-2.0
"""
Prognoza serwisowa i wezwania priorytetowe (blok 9).

Dla każdego egzemplarza liczy nalot pozostały do najbliższego progu obsługi
(pobieżny 100 h, poważny 600 h, remont 3000 h) i przelicza go na dni według
założonego tempa nalotu. Egzemplarze blisko progu albo po progu trafiają do
wezwań priorytetowych, z miejscem obsługi z reguł serwisu.

Tempo nalotu jest na razie założeniem (`TEMPO_DOMYSLNE_H_DZIEN`); realne tempo
dostarczy telemetria w bloku 10.
"""

import math
from datetime import date
from typing import Optional

from frms.models import PoziomSerwisu, KonfiguracjaSerwisu
from frms.serwis import prog_poziomu, _nalot_od_ostatniego, miejsce_serwisu, w_serwisie

TEMPO_DOMYSLNE_H_DZIEN = 3.0    # założone tempo nalotu na egzemplarz (do czasu telemetrii)
PROG_WEZWANIA_WYSOKI_H = 10.0   # ≤10 h do progu (lub po progu) → wezwanie wysokie
PROG_WEZWANIA_SREDNI_H = 30.0   # ≤30 h → wezwanie średnie

_POZIOMY = (PoziomSerwisu.POBIEZNY, PoziomSerwisu.POWAZNY, PoziomSerwisu.REMONT)


def godziny_do_progow(maszyna, s: KonfiguracjaSerwisu) -> dict:
    """Nalot pozostały do każdego poziomu obsługi (ujemny = próg przekroczony)."""
    return {p: round(prog_poziomu(p, s) - _nalot_od_ostatniego(maszyna, p), 1) for p in _POZIOMY}


def najblizszy_przeglad(maszyna, s: KonfiguracjaSerwisu):
    """(poziom, godziny_pozostale) najbliższego progu. Godziny ≤ 0 = próg przekroczony."""
    g = godziny_do_progow(maszyna, s)
    poziom = min(g, key=lambda p: g[p])
    return poziom, g[poziom]


def prognoza_dni(maszyna, s: KonfiguracjaSerwisu, tempo: float = TEMPO_DOMYSLNE_H_DZIEN) -> Optional[int]:
    """Dni do najbliższego progu przy danym tempie nalotu. 0 gdy próg już przekroczony."""
    if tempo <= 0:
        return None
    _, godz = najblizszy_przeglad(maszyna, s)
    return max(0, math.ceil(godz / tempo)) if godz > 0 else 0


def priorytet_wezwania(godziny_pozostale: float) -> str:
    if godziny_pozostale <= PROG_WEZWANIA_WYSOKI_H:
        return "WYSOKI"
    if godziny_pozostale <= PROG_WEZWANIA_SREDNI_H:
        return "SREDNI"
    return "NISKI"


def prognoza_maszyny(maszyna, s: KonfiguracjaSerwisu, dzien: date,
                     tempo: float = TEMPO_DOMYSLNE_H_DZIEN) -> dict:
    poziom, godz = najblizszy_przeglad(maszyna, s)
    return {
        "maszyna_id": maszyna.id,
        "klasa": maszyna.klasa.value,
        "hub": maszyna.aktualny_hub,
        "nalot_h": round(maszyna.nalot_h, 1),
        "poziom": poziom.value,
        "godziny_do": godz,
        "dni_do": prognoza_dni(maszyna, s, tempo),
        "priorytet": priorytet_wezwania(godz),
        "miejsce": miejsce_serwisu(poziom, maszyna, s),
        "w_serwisie": w_serwisie(maszyna, dzien),
    }


def prognoza_floty(maszyny: list, s: KonfiguracjaSerwisu, dzien: date,
                   tempo: float = TEMPO_DOMYSLNE_H_DZIEN) -> list:
    """Prognoza dla wszystkich egzemplarzy, najpilniejsze pierwsze (te w serwisie na końcu)."""
    out = [prognoza_maszyny(m, s, dzien, tempo) for m in maszyny]
    out.sort(key=lambda x: (x["w_serwisie"], x["godziny_do"]))
    return out


def wezwania_priorytetowe(maszyny: list, s: KonfiguracjaSerwisu, dzien: date,
                          tempo: float = TEMPO_DOMYSLNE_H_DZIEN) -> list:
    """Egzemplarze do priorytetowego wezwania na obsługę (wysoki lub średni, nie w serwisie)."""
    return [p for p in prognoza_floty(maszyny, s, dzien, tempo)
            if p["priorytet"] in ("WYSOKI", "SREDNI") and not p["w_serwisie"]]
