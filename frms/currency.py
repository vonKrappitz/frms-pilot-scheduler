# Copyright 2026 Maciej M. Kasperek ("vonKrappitz")
# SPDX-License-Identifier: Apache-2.0
"""
Moduł śledzenia świeżości operacyjnej (currency) pilotów MEDEVAC.

Zgodny z EASA AMC1 ORO.FTL.110 oraz Part-FCL recency. Polityka Korpusu:

1. RECURRENT KWARTALNY (obowiązkowy trening okresowy):
   - Raz na kwartał kalendarzowy pilot odbywa jedną sesję na symulatorze.
   - 2 kolejne dni × 6h = 12h, trudne scenariusze: autorotacje, awarie silnika,
     lądowania awaryjne, loty w trudnych warunkach.
   - Sesja dotyczy jednej klasy; klasy rotują przez kwartały, więc w ciągu roku
     każda klasa dostaje swoje 12h. Domyślnie kierujemy na klasę własną najdawniej
     ćwiczoną; zakres dozwolony to klasy własne plus jedna kategoria wyżej
     (wybór i powtórzenie klasy są w gestii operatora, blok 7).
   - Żadnego pustego kwartału: dopóki pilot ma aktualne uprawnienia, kwartał musi
     domknąć sesją.

2. CURRENCY RECOVERY (odzyskanie świeżości po przerwie operacyjnej):
   - Wyzwolenie: 21 dni bez lotu dla śmigłowców, 45 dni dla samolotu STOL.
   - Po wyzwoleniu pilot ma 45 dni na wykonanie sesji. Dla samolotu daje to
     twardy limit 45+45=90 dni bez lotu (granica przepisowa). Recovery samolotu
     ma niższy priorytet niż śmigłowców.
   - Sesja: 1 dzień × 6h, ważna dopiero z minimum 5 startami i lądowaniami.

Lokalizacja sesji: EPDE (Lotnicza Akademia Wojskowa Dęblin).
"""

from datetime import date, timedelta
from typing import Optional

from frms.models import Kategoria, KlasaMaszyny, Pilot, SesjaSymulatorowa


# ============================================================
# PROGI I STAŁE POLITYKI CURRENCY
# ============================================================

PROG_DNI_BEZ_LOTU_HELI = 21       # AW101, H145, H135 — wyzwolenie recovery
PROG_DNI_BEZ_LOTU_SAMOLOT = 45    # Cessna Grand Caravan EX (STOL) — wyzwolenie recovery
OKNO_RECOVERY_DNI = 45            # termin wykonania recovery po wyzwoleniu
MAX_DNI_BEZ_LOTU = 90             # granica przepisowa (samolot: 45 wyzwolenie + 45 okno)
MIN_STARTY_LADOWANIA_RECOVERY = 5  # minimum startów ORAZ lądowań do zaliczenia recovery

# Klasy wyłączone z symulatora i szkolenia (obecnie brak).
KLASY_BEZ_SYM_I_SZKOLEN = frozenset()
CZAS_SESJI_SYMULATORA = 6.0       # godziny per dzień szkoleniowy
DNI_RECURRENT = 2                 # recurrent kwartalny: 2 dni × 6h = 12h
DNI_RECOVERY = 1                  # recovery: 1 dzień × 6h


def prog_currency_dni(klasa: KlasaMaszyny) -> int:
    """Próg dni bez lotu wyzwalający recovery: samolot 45, śmigłowce 21.

    Samolot tłokowo-turbinowy wolniej eroduje umiejętności pilota niż reżim
    wirnikowy, stąd łagodniejszy próg wyzwolenia.
    """
    if klasa == KlasaMaszyny.STOL_SAMOLOT:
        return PROG_DNI_BEZ_LOTU_SAMOLOT
    return PROG_DNI_BEZ_LOTU_HELI


def priorytet_recovery(klasa: KlasaMaszyny) -> str:
    """Priorytet recovery: śmigłowce WYSOKI, samolot STOL NISKI."""
    return "NISKI" if klasa == KlasaMaszyny.STOL_SAMOLOT else "WYSOKI"


# ============================================================
# DNI OD OSTATNIEJ AKTYWNOŚCI
# ============================================================

def dni_od_ostatniego_lotu_per_klasa(pilot: Pilot, klasa: KlasaMaszyny, dzien: date) -> int:
    """Dni od ostatniego lotu operacyjnego (bez symulatora) na danej klasie.

    Brak historii lotów → dni od daty ostatniego lotu z type rating. Brak type
    rating → 999.
    """
    loty = [m for m in pilot.historia_misji
            if m.klasa_maszyny == klasa and not m.czy_symulator and m.data <= dzien]
    if loty:
        return (dzien - max(loty, key=lambda m: m.data).data).days
    for tr in pilot.type_ratings:
        if tr.klasa == klasa:
            return (dzien - tr.data_ostatniego_lotu).days
    return 999


def dni_od_ostatniego_treningu_dowolnego(pilot: Pilot, klasa: KlasaMaszyny, dzien: date) -> int:
    """Dni od ostatniej dowolnej sesji symulatorowej na danej klasie (recurrent lub recovery).

    Sesja symulatorowa odświeża świeżość, więc resetuje licznik recovery.
    """
    sesje = [s for s in pilot.historia_sesji_symulatorowych
             if s.klasa_maszyny == klasa and s.data <= dzien]
    if not sesje:
        return 999
    return (dzien - max(sesje, key=lambda s: s.data).data).days


def dni_od_ostatniego_recurrent_per_klasa(pilot: Pilot, klasa: KlasaMaszyny, dzien: date) -> int:
    """Dni od ostatniej sesji recurrent na danej klasie. Brak → 999."""
    rec = [s for s in pilot.historia_sesji_symulatorowych
           if s.klasa_maszyny == klasa and s.czy_recurrent and s.data <= dzien]
    if not rec:
        return 999
    return (dzien - max(rec, key=lambda s: s.data).data).days


def data_ostatniej_aktywnosci(pilot: Pilot, klasa: KlasaMaszyny, dzien: date) -> Optional[date]:
    """Najpóźniejsza z dat: lot operacyjny lub sesja symulatorowa na danej klasie."""
    daty = [m.data for m in pilot.historia_misji
            if m.klasa_maszyny == klasa and not m.czy_symulator and m.data <= dzien]
    daty += [s.data for s in pilot.historia_sesji_symulatorowych
             if s.klasa_maszyny == klasa and s.data <= dzien]
    if daty:
        return max(daty)
    for tr in pilot.type_ratings:
        if tr.klasa == klasa:
            return tr.data_ostatniego_lotu
    return None


# ============================================================
# RECOVERY
# ============================================================

def wymaga_currency_recovery(pilot: Pilot, klasa: KlasaMaszyny, dzien: date) -> bool:
    """Czy pilot wymaga recovery na danej klasie (1 dzień × 6h).

    Wyzwolenie: dni od ostatniego lotu LUB od ostatniej sesji symulatorowej
    (cokolwiek było później) przekracza próg klasy.
    """
    if not pilot.ma_type_rating(klasa, dzien):
        return False
    dni_efektywne = min(
        dni_od_ostatniego_lotu_per_klasa(pilot, klasa, dzien),
        dni_od_ostatniego_treningu_dowolnego(pilot, klasa, dzien),
    )
    return dni_efektywne >= prog_currency_dni(klasa)


def termin_recovery(pilot: Pilot, klasa: KlasaMaszyny, dzien: date) -> Optional[date]:
    """Ostateczny termin wykonania recovery (data ostatniej aktywności + próg + okno).

    None, gdy recovery nie jest wymagane lub brak punktu odniesienia.
    """
    if not wymaga_currency_recovery(pilot, klasa, dzien):
        return None
    baza = data_ostatniej_aktywnosci(pilot, klasa, dzien)
    if baza is None:
        return None
    return baza + timedelta(days=prog_currency_dni(klasa) + OKNO_RECOVERY_DNI)


def dni_do_terminu_recovery(pilot: Pilot, klasa: KlasaMaszyny, dzien: date) -> Optional[int]:
    """Dni do terminu recovery (ujemne = po terminie). None, gdy nie dotyczy."""
    termin = termin_recovery(pilot, klasa, dzien)
    return None if termin is None else (termin - dzien).days


def recovery_wazna(sesja: SesjaSymulatorowa) -> bool:
    """Sesja recovery ważna dopiero z minimum 5 startami ORAZ 5 lądowaniami."""
    if not sesja.czy_currency_recovery:
        return False
    return (sesja.starty >= MIN_STARTY_LADOWANIA_RECOVERY
            and sesja.ladowania >= MIN_STARTY_LADOWANIA_RECOVERY)


# ============================================================
# RECURRENT KWARTALNY
# ============================================================

def kwartal(dzien: date) -> tuple[int, int]:
    """Zwraca (rok, numer kwartału 1–4) dla danego dnia."""
    return (dzien.year, (dzien.month - 1) // 3 + 1)


def _ma_aktualne_ratingi(pilot: Pilot, dzien: date) -> bool:
    return any(tr.jest_aktualny(dzien) for tr in pilot.type_ratings)


def klasy_wlasne_aktualne(pilot: Pilot, dzien: date) -> list[KlasaMaszyny]:
    """Klasy, na które pilot ma aktualny type rating (z zachowaniem kolejności)."""
    out: list[KlasaMaszyny] = []
    for tr in pilot.type_ratings:
        if tr.jest_aktualny(dzien) and tr.klasa not in out:
            out.append(tr.klasa)
    return out


def zakres_szkolenia_symulator(pilot: Pilot, dzien: date) -> set[KlasaMaszyny]:
    """Dozwolony zakres szkolenia na symulatorze: klasy własne plus jedna kategoria wyżej.

    A dochodzi do HEMS (klasa kat B), B do MEDEVAC (klasa kat C). C i D mają już
    cztery klasy LPR.
    """
    zakres = set(klasy_wlasne_aktualne(pilot, dzien))
    if pilot.kategoria == Kategoria.A:
        zakres.add(KlasaMaszyny.HEMS_SREDNI)
    elif pilot.kategoria == Kategoria.B:
        zakres.add(KlasaMaszyny.MEDEVAC_CIEZKI)
    return zakres


def klasa_recurrent_domyslna(pilot: Pilot, dzien: date) -> Optional[KlasaMaszyny]:
    """Domyślna klasa kwartalnego recurrent: własna, najdawniej ćwiczona na symulatorze.

    Operator może nadpisać wybór (także na klasę z zakresu „jedna wyżej"
    lub powtórzyć klasę) w UI; to jest sensowny domyślny rozkład.
    """
    wlasne = klasy_wlasne_aktualne(pilot, dzien)
    if not wlasne:
        return None
    return max(wlasne, key=lambda k: dni_od_ostatniego_recurrent_per_klasa(pilot, k, dzien))


def recurrent_odbyty_w_kwartale(pilot: Pilot, dzien: date) -> bool:
    """Czy pilot odbył jakąkolwiek sesję recurrent w bieżącym kwartale kalendarzowym."""
    biezacy = kwartal(dzien)
    return any(
        s.czy_recurrent and s.data <= dzien and kwartal(s.data) == biezacy
        for s in pilot.historia_sesji_symulatorowych
    )


def wymaga_recurrent_kwartalny(pilot: Pilot, klasa: KlasaMaszyny, dzien: date) -> bool:
    """Czy pilot ma w tym kwartale odbyć recurrent na DANEJ klasie.

    Zwraca True dokładnie dla jednej klasy (domyślnie wybranej), gdy pilot ma
    aktualne uprawnienia i nie domknął jeszcze kwartału. Dzięki temu pętle per
    type rating w CLI i eksporcie wskazują jedną sesję recurrent na kwartał.
    """
    if not _ma_aktualne_ratingi(pilot, dzien):
        return False
    if recurrent_odbyty_w_kwartale(pilot, dzien):
        return False
    return klasa == klasa_recurrent_domyslna(pilot, dzien)


# ============================================================
# GENERATOR SESJI SYMULATOROWYCH DLA PILOTA
# ============================================================

def generuj_sesje_symulatorowe_dla_pilota(pilot: Pilot, dzien_referencyjny: date) -> list[SesjaSymulatorowa]:
    """Sesje symulatorowe pilota: kwartalny recurrent (jedna klasa) plus recovery per klasa.

    Recurrent ma pierwszeństwo na klasie wybranej; ta sama klasa nie generuje
    równolegle recovery (świeżo odświeżona).
    """
    sesje: list[SesjaSymulatorowa] = []

    klasa_rec = klasa_recurrent_domyslna(pilot, dzien_referencyjny)
    if klasa_rec is not None and wymaga_recurrent_kwartalny(pilot, klasa_rec, dzien_referencyjny):
        for d in range(DNI_RECURRENT):
            sesje.append(SesjaSymulatorowa(
                data=dzien_referencyjny + timedelta(days=d),
                klasa_maszyny=klasa_rec,
                czas_trwania_h=CZAS_SESJI_SYMULATORA,
                czy_recurrent=True,
            ))

    for klasa in klasy_wlasne_aktualne(pilot, dzien_referencyjny):
        if klasa == klasa_rec:
            continue  # klasa właśnie odświeżona recurrentem
        if wymaga_currency_recovery(pilot, klasa, dzien_referencyjny):
            sesje.append(SesjaSymulatorowa(
                data=dzien_referencyjny,
                klasa_maszyny=klasa,
                czas_trwania_h=CZAS_SESJI_SYMULATORA,
                czy_currency_recovery=True,
                starty_ladowania=MIN_STARTY_LADOWANIA_RECOVERY,
            ))

    return sesje


def liczba_dni_wylaczenia_z_dyzurow(sesje: list[SesjaSymulatorowa]) -> int:
    """Ile dni pilot będzie wyłączony z dyżurów: recurrent 2 dni, recovery 1 dzień."""
    if not sesje:
        return 0
    return DNI_RECURRENT if any(s.czy_recurrent for s in sesje) else DNI_RECOVERY


def opis_powodu_sesji(pilot: Pilot, klasa: KlasaMaszyny, dzien: date, lang: str = "pl") -> Optional[str]:
    """Tekstowy powód sesji dla pilota i klasy (recurrent lub recovery), albo None.

    `lang='pl'` (domyślnie) lub `'en'`."""
    if wymaga_recurrent_kwartalny(pilot, klasa, dzien):
        rok, kw = kwartal(dzien)
        if lang == "en":
            return f"quarterly recurrent (Q{kw} {rok}) — demanding scenarios: autorotations, engine failures, emergency landings"
        return f"recurrent kwartalny (Q{kw} {rok}) — trudne scenariusze: autorotacje, awarie silnika, lądowania awaryjne"
    if wymaga_currency_recovery(pilot, klasa, dzien):
        dni = dni_od_ostatniego_lotu_per_klasa(pilot, klasa, dzien)
        prog = prog_currency_dni(klasa)
        do_terminu = dni_do_terminu_recovery(pilot, klasa, dzien)
        prio = priorytet_recovery(klasa)
        if lang == "en":
            prio_en = {"WYSOKI": "HIGH", "SREDNI": "MEDIUM", "NISKI": "LOW"}.get(prio, prio)
            return (f"currency recovery — {dni} days without flight (threshold {prog}), "
                    f"due in {do_terminu} days, priority {prio_en}")
        return (f"currency recovery — {dni} dni bez lotu (próg {prog}), "
                f"termin za {do_terminu} dni, priorytet {prio}")
    return None
