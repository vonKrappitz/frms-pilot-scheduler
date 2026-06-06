# Copyright 2026 Maciej M. Kasperek ("vonKrappitz")
# SPDX-License-Identifier: Apache-2.0
"""
Walidator zgodności z normami EASA i generator alertów operacyjnych.

Wzorzec: szwajcarska Rega, norweska Norsk Luftambulanse, niemiecka ADAC Luftrettung.
"""

from datetime import date
from frms.models import Kategoria, Pilot


def alerty_type_rating(piloci: list[Pilot], dzien: date) -> list[dict]:
    """Generuje alerty o type ratingach wymagających uwagi."""
    alerty = []
    for p in piloci:
        for tr in p.type_ratings:
            if tr.wymaga_alertu(dzien):
                priorytet = "WYSOKI" if tr.dni_do_wygasniecia(dzien) <= 14 else "ŚREDNI"
                alerty.append({
                    "priorytet": priorytet,
                    "pilot_id": p.id,
                    "imie_nazwisko": f"{p.imie} {p.nazwisko}",
                    "kategoria": p.kategoria.value,
                    "klasa": tr.klasa.value,
                    "dni_do_wygasniecia": tr.dni_do_wygasniecia(dzien),
                    "dni_od_ostatniego_lotu": tr.dni_od_ostatniego_lotu(dzien),
                    "typ": "type_rating_wygasa" if tr.dni_do_wygasniecia(dzien) <= 30
                           else "nieaktywnosc_na_typie",
                })
    return sorted(alerty, key=lambda a: (a["priorytet"] != "WYSOKI", a["dni_do_wygasniecia"]))


def alerty_przeciazenia(piloci: list[Pilot], dzien: date) -> list[dict]:
    """Alerty o przekroczeniu limitów obciążenia EASA AMC1 ORO.FTL.110."""
    alerty = []
    for p in piloci:
        if p.przeciazony(dzien):
            alerty.append({
                "priorytet": "WYSOKI",
                "pilot_id": p.id,
                "imie_nazwisko": f"{p.imie} {p.nazwisko}",
                "typ": "przekroczenie_60h_7dni",
                "wartosc": "ponad 60h w oknie 7 dni",
            })
        obc96 = p.obciazenie_96h(dzien)
        if obc96 > 20.0:
            alerty.append({
                "priorytet": "ŚREDNI",
                "pilot_id": p.id,
                "imie_nazwisko": f"{p.imie} {p.nazwisko}",
                "typ": "wysokie_obciazenie_96h",
                "wartosc": f"{obc96:.1f}h w oknie 96h",
            })
    return alerty


def statystyki_systemu(piloci: list[Pilot], dzien: date) -> dict:
    """Zwraca statystyki agregowane systemu."""
    rozklad_kategorii = {k: 0 for k in Kategoria}
    type_ratings_aktualne = 0
    type_ratings_lacznie = 0
    piloci_gotowi_24h = 0

    for p in piloci:
        rozklad_kategorii[p.kategoria] += 1
        for tr in p.type_ratings:
            type_ratings_lacznie += 1
            if tr.jest_aktualny(dzien):
                type_ratings_aktualne += 1
        if p.gotowy_do_dyzuru_24h(dzien):
            piloci_gotowi_24h += 1

    return {
        "liczba_pilotow": len(piloci),
        "rozklad_kategorii": {k.value: v for k, v in rozklad_kategorii.items()},
        "type_ratings_aktualne_proc": round(
            100 * type_ratings_aktualne / type_ratings_lacznie, 1
        ) if type_ratings_lacznie else 0,
        "piloci_gotowi_do_dyzuru_24h": piloci_gotowi_24h,
        "srednie_obciazenie_96h": round(
            sum(p.obciazenie_96h(dzien) for p in piloci) / len(piloci), 1
        ) if piloci else 0,
    }
