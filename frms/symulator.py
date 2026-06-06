# Copyright 2026 Maciej M. Kasperek ("vonKrappitz")
# SPDX-License-Identifier: Apache-2.0
"""
Pojemność symulatora w EPDE (Lotnicza Akademia Wojskowa Dęblin).

Jeden egzemplarz symulatora na klasę, jeden pilot na dzień na symulator. Sesje
wymagane przez reguły currency są pakowane na konkretne dni: recurrent (2 kolejne
dni) w obrębie kwartału kalendarzowego, recovery (1 dzień) w swoim oknie 45 dni.
Kolizje rozwiązuje przesunięcie sesji na pierwszy wolny termin w oknie. Recovery
helikopterów (priorytet WYSOKI) idzie przed recovery samolotu (NISKI), recurrent
na końcu. Zapotrzebowanie, którego nie da się zmieścić w oknie, wraca jako
nieobsadzone: to sygnał przepełnienia, nie cicha porażka.
"""

from calendar import monthrange
from dataclasses import dataclass
from datetime import date, timedelta

from frms.models import Pilot, SlotDyzurowy, TypDyzuru, KlasaMaszyny
from frms.currency import (
    kwartal, klasy_wlasne_aktualne, klasa_recurrent_domyslna,
    wymaga_recurrent_kwartalny, wymaga_currency_recovery,
    termin_recovery, priorytet_recovery, DNI_RECURRENT, DNI_RECOVERY,
    KLASY_BEZ_SYM_I_SZKOLEN,
)

EPDE = "EPDE"
POJEMNOSC_NA_KLASE_DZIEN = 1  # jeden pilot na dzień na symulator danej klasy

# Priorytety kolejkowania (mniejsza liczba = wcześniej).
_PRIO_RECOVERY = {"WYSOKI": 0, "NISKI": 1}
_PRIO_RECURRENT = 2


@dataclass
class ZapotrzebowanieSym:
    pilot_id: str
    klasa: KlasaMaszyny
    typ: str                 # "RECURRENT" lub "RECOVERY"
    dni: int                 # 2 dla recurrent, 1 dla recovery
    okno_od: date
    okno_do: date            # ostatni dopuszczalny dzień rozpoczęcia mieszczący całą sesję
    priorytet: int
    opis: str = ""


def _granice_kwartalu(dzien: date) -> tuple[date, date]:
    rok, kw = kwartal(dzien)
    m_pierwszy = (kw - 1) * 3 + 1
    m_ostatni = kw * 3
    start = date(rok, m_pierwszy, 1)
    koniec = date(rok, m_ostatni, monthrange(rok, m_ostatni)[1])
    return start, koniec


def _dni(od: date, do: date):
    d = od
    while d <= do:
        yield d
        d += timedelta(days=1)


def zbierz_zapotrzebowanie(piloci: list[Pilot], dzien_start: date) -> list[ZapotrzebowanieSym]:
    """Buduje listę sesji wymaganych przez reguły currency, z oknami umieszczenia."""
    q_start, q_koniec = _granice_kwartalu(dzien_start)
    okno_rec_od = max(dzien_start, q_start)
    zapotrzebowanie: list[ZapotrzebowanieSym] = []

    for p in piloci:
        klasa_rec = klasa_recurrent_domyslna(p, dzien_start)
        if (klasa_rec is not None and klasa_rec not in KLASY_BEZ_SYM_I_SZKOLEN
                and wymaga_recurrent_kwartalny(p, klasa_rec, dzien_start)):
            zapotrzebowanie.append(ZapotrzebowanieSym(
                pilot_id=p.id, klasa=klasa_rec, typ="RECURRENT", dni=DNI_RECURRENT,
                okno_od=okno_rec_od, okno_do=q_koniec, priorytet=_PRIO_RECURRENT,
                opis="recurrent kwartalny",
            ))
        for klasa in klasy_wlasne_aktualne(p, dzien_start):
            if klasa == klasa_rec or klasa in KLASY_BEZ_SYM_I_SZKOLEN:
                continue  # recurrent tej klasy albo klasa wyłączona z symulatora
            if not wymaga_currency_recovery(p, klasa, dzien_start):
                continue
            termin = termin_recovery(p, klasa, dzien_start)
            okno_do = termin if (termin and termin >= dzien_start) else dzien_start
            prio = priorytet_recovery(klasa)
            zapotrzebowanie.append(ZapotrzebowanieSym(
                pilot_id=p.id, klasa=klasa, typ="RECOVERY", dni=DNI_RECOVERY,
                okno_od=dzien_start, okno_do=okno_do, priorytet=_PRIO_RECOVERY[prio],
                opis=f"recovery {prio.lower()}",
            ))
    return zapotrzebowanie


def zaplanuj_z_zapotrzebowania(
    zapotrzebowanie: list[ZapotrzebowanieSym],
) -> tuple[list[tuple[ZapotrzebowanieSym, list[date]]], list[ZapotrzebowanieSym]]:
    """Pakuje zapotrzebowanie przy pojemności jeden pilot na klasę na dzień.

    Zwraca (przydziały, nieobsadzone). Przydział to (zapotrzebowanie, lista dni).
    Kolejność: priorytet, potem najwcześniejszy termin (okno_do), potem pilot.
    """
    kolejka = sorted(zapotrzebowanie, key=lambda z: (z.priorytet, z.okno_do, z.pilot_id, z.klasa.value))
    zajete_klasa_dzien: set[tuple[KlasaMaszyny, date]] = set()
    zajety_pilot_dzien: set[tuple[str, date]] = set()
    przydzialy: list[tuple[ZapotrzebowanieSym, list[date]]] = []
    nieobsadzone: list[ZapotrzebowanieSym] = []

    for z in kolejka:
        umieszczono = False
        ostatni_start = z.okno_do - timedelta(days=z.dni - 1)
        for start in _dni(z.okno_od, ostatni_start):
            dni_sesji = [start + timedelta(days=i) for i in range(z.dni)]
            if any((z.klasa, d) in zajete_klasa_dzien for d in dni_sesji):
                continue
            if any((z.pilot_id, d) in zajety_pilot_dzien for d in dni_sesji):
                continue
            for d in dni_sesji:
                zajete_klasa_dzien.add((z.klasa, d))
                zajety_pilot_dzien.add((z.pilot_id, d))
            przydzialy.append((z, dni_sesji))
            umieszczono = True
            break
        if not umieszczono:
            nieobsadzone.append(z)

    return przydzialy, nieobsadzone


def zaplanuj_symulator(
    piloci: list[Pilot], dzien_start: date,
) -> tuple[list[SlotDyzurowy], list[ZapotrzebowanieSym]]:
    """Pełne planowanie EPDE: zbiera zapotrzebowanie, pakuje, emituje sloty SYMULATOR_LAW.

    Zwraca (sloty, nieobsadzone). Nieobsadzone to przepełnienie pojemności symulatora.
    """
    by_id = {p.id: p for p in piloci}
    zapotrzebowanie = zbierz_zapotrzebowanie(piloci, dzien_start)
    przydzialy, nieobsadzone = zaplanuj_z_zapotrzebowania(zapotrzebowanie)

    sloty: list[SlotDyzurowy] = []
    licznik = 0
    for z, dni_sesji in sorted(przydzialy, key=lambda x: (x[1][0], x[0].pilot_id)):
        p = by_id[z.pilot_id]
        for d in dni_sesji:
            licznik += 1
            sloty.append(SlotDyzurowy(
                id=f"SYM-{licznik:04d}",
                baza_id=EPDE,
                data=d,
                typ_dyzuru=TypDyzuru.SYMULATOR_LAW,
                wymagana_klasa=z.klasa,
                wymagana_kategoria_min=p.kategoria,
                organizacja=p.organizacja,
                przypisany_pilot_id=p.id,
            ))
    return sloty, nieobsadzone
