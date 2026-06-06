# Copyright 2026 Maciej M. Kasperek ("vonKrappitz")
# SPDX-License-Identifier: Apache-2.0
"""
Dane testowe (mock data) systemu FRMS.

30 pilotów Korpusu KPRL w 5 bazach operacyjnych,
przykładowy tygodniowy zestaw slotów dyżurowych.
"""

from datetime import date, timedelta
import random

from frms.models import (
    Baza, Kategoria, KlasaMaszyny, KonfiguracjaSerwisu, Maszyna,
    Misja, Organizacja, Pilot, SkalaNACA, SlotDyzurowy, StatusMaszyny,
    TrybMisji, TypDyzuru, TypeRating
)


# Ziarno losowe dla powtarzalności wyników testowych
random.seed(42)


# ============================================================
# FLOTA KRAJOWA — pula 51 statków powietrznych (bilans Części II)
# Oznaczenie: litera klasy + numer. Maszyny bez stałej bazy — krążą między
# hubami. Operacyjne 44 + rezerwa krajowa 5 + żelazna rezerwa 2 (EC135).
# ============================================================

FLOTA: list[Maszyna] = (
    # HEMS H145 — 28 operacyjnych + 3 rezerwa krajowa = 31 (H1–H31)
    [Maszyna(f"H{i}", KlasaMaszyny.HEMS_SREDNI, StatusMaszyny.OPERACYJNA) for i in range(1, 29)]
    + [Maszyna(f"H{i}", KlasaMaszyny.HEMS_SREDNI, StatusMaszyny.REZERWA_KRAJOWA) for i in range(29, 32)]
    # LST H135 — 9 operacyjnych + 2 rezerwa krajowa + 2 żelazna (EC135) = 13 (L1–L13)
    + [Maszyna(f"L{i}", KlasaMaszyny.LST_LEKKI, StatusMaszyny.OPERACYJNA) for i in range(1, 10)]
    + [Maszyna(f"L{i}", KlasaMaszyny.LST_LEKKI, StatusMaszyny.REZERWA_KRAJOWA) for i in range(10, 12)]
    + [Maszyna(f"L{i}", KlasaMaszyny.LST_LEKKI, StatusMaszyny.REZERWA_ZELAZNA) for i in range(12, 14)]
    # MEDEVAC AW101 — 4 operacyjne (X1–X4)
    + [Maszyna(f"X{i}", KlasaMaszyny.MEDEVAC_CIEZKI, StatusMaszyny.OPERACYJNA) for i in range(1, 5)]
    # STOL Caravan — 3 operacyjne (S1–S3)
    + [Maszyna(f"S{i}", KlasaMaszyny.STOL_SAMOLOT, StatusMaszyny.OPERACYJNA) for i in range(1, 4)]
)


def maszyny_klasy(klasa: KlasaMaszyny, tylko_operacyjne: bool = True) -> list[Maszyna]:
    """Zwraca egzemplarze danej klasy; domyślnie tylko operacyjne (bez rezerw)."""
    wynik = [m for m in FLOTA if m.klasa == klasa]
    if tylko_operacyjne:
        wynik = [m for m in wynik if m.status == StatusMaszyny.OPERACYJNA]
    return wynik


# ============================================================
# HUBY — siedem Centrów Regionalnych LPR (rev1: pre-seed 7 CRL)
# ============================================================

HUBY = [
    {"id": "EPWA", "miasto": "Warszawa", "sektor": "Mazowsze"},
    {"id": "EPKK", "miasto": "Kraków",   "sektor": "Małopolska i południe"},
    {"id": "EPWR", "miasto": "Wrocław",  "sektor": "Dolny Śląsk"},
    {"id": "EPGD", "miasto": "Gdańsk",   "sektor": "Pomorze"},
    {"id": "EPLB", "miasto": "Lublin",   "sektor": "Lubelszczyzna (ośrodek remontów)"},
    {"id": "EPPO", "miasto": "Poznań",   "sektor": "Wielkopolska"},
    {"id": "EPSY", "miasto": "Olsztyn",  "sektor": "Północny wschód"},
]

# Domyślny przydział operacyjnych maszyn do hubów (round-robin) oraz losowy
# bieżący resurs. Osobny strumień losowy — nie zaburza danych pilotów.
_flota_rng = random.Random(123)
_kody_hubow = [h["id"] for h in HUBY]
_idx_hub = 0
for _m in FLOTA:
    _m.nalot_h = round(_flota_rng.uniform(0, 95), 1)
    if _m.status == StatusMaszyny.OPERACYJNA:
        _m.aktualny_hub = _kody_hubow[_idx_hub % len(_kody_hubow)]
        _idx_hub += 1


def status_serwisowy(m: Maszyna, kfg: KonfiguracjaSerwisu) -> dict:
    """
    Ile godzin nalotu zostało maszynie do najbliższego przeglądu każdego
    poziomu, na podstawie konfigurowalnych progów. Bliski próg = pilny serwis.
    """
    return {
        "do_pobieznego_h": round(kfg.serwis_pobiezny_h - (m.nalot_h % kfg.serwis_pobiezny_h), 1),
        "do_powaznego_h": round(kfg.serwis_powazny_h - (m.nalot_h % kfg.serwis_powazny_h), 1),
        "do_remontu_h": round(kfg.remont_h - (m.nalot_h % kfg.remont_h), 1),
    }


def maszyny_huba(hub_id: str) -> list[Maszyna]:
    """Wykaz maszyn aktualnie przydzielonych do danego huba (CRL)."""
    return [m for m in FLOTA if m.aktualny_hub == hub_id]


# ============================================================
# BAZY OPERACYJNE LPR (w pełnej reformie: 25 baz)
# ============================================================

BAZY = [
    # Bazy LPR
    Baza("EPWA", "Warszawa-Chopina", "HUB",
         [KlasaMaszyny.MEDEVAC_CIEZKI, KlasaMaszyny.HEMS_SREDNI, KlasaMaszyny.LST_LEKKI],
         Organizacja.LPR),
    Baza("EPKK", "Kraków-Balice", "HUB",
         [KlasaMaszyny.MEDEVAC_CIEZKI, KlasaMaszyny.HEMS_SREDNI, KlasaMaszyny.LST_LEKKI],
         Organizacja.LPR),
    Baza("EPWR", "Wrocław-Strachowice", "HUB",
         [KlasaMaszyny.MEDEVAC_CIEZKI, KlasaMaszyny.HEMS_SREDNI, KlasaMaszyny.LST_LEKKI],
         Organizacja.LPR),
    Baza("EPLL", "Łódź-Lublinek", "FOB",
         [KlasaMaszyny.HEMS_SREDNI, KlasaMaszyny.LST_LEKKI],
         Organizacja.LPR),
    Baza("EPKT", "Katowice-Pyrzowice", "FOB",
         [KlasaMaszyny.HEMS_SREDNI, KlasaMaszyny.STOL_SAMOLOT],
         Organizacja.LPR),
    # Rzeszów-Jasionka: specjalny FOB-LST 7-21 (jedyny FOB nie 24/7, bez HEMS)
    Baza("EPRZ", "Rzeszów-Jasionka (FOB-LST 7-21)", "FOB-LST",
         [KlasaMaszyny.LST_LEKKI],
         Organizacja.LPR),
    # LAW Dęblin — państwowe centrum szkoleniowe i symulatorowe Korpusu KPRL
    # Wszystkie 4 klasy symulatorów floty: AW101, H145, H135, Grand Caravan EX
    # Sesje currency recovery (1 dzień × 6h) oraz recurrent kwartalny (2 dni × 6h)
    Baza("EPDE", "Lotnicza Akademia Wojskowa Dęblin (symulatory)", "SZKOLENIOWA",
         [KlasaMaszyny.MEDEVAC_CIEZKI, KlasaMaszyny.HEMS_SREDNI, KlasaMaszyny.LST_LEKKI,
          KlasaMaszyny.STOL_SAMOLOT],
         Organizacja.LPR),
]


# ============================================================
# 30 PILOTÓW (rozkład: A=10, B=10, C=7, D=3)
# ============================================================

IMIONA = [
    ("Adam", "Kowalski"), ("Bartosz", "Nowak"), ("Cezary", "Wiśniewski"),
    ("Dariusz", "Wójcik"), ("Edward", "Kowalczyk"), ("Filip", "Kamiński"),
    ("Grzegorz", "Lewandowski"), ("Henryk", "Zieliński"), ("Igor", "Szymański"),
    ("Jakub", "Dąbrowski"), ("Krzysztof", "Kozłowski"), ("Łukasz", "Jankowski"),
    ("Maciej", "Mazur"), ("Norbert", "Kwiatkowski"), ("Oskar", "Krawczyk"),
    ("Paweł", "Piotrowski"), ("Robert", "Grabowski"), ("Sebastian", "Pawłowski"),
    ("Tomasz", "Michalski"), ("Urban", "Adamczyk"), ("Wojciech", "Dudek"),
    ("Zbigniew", "Zając"), ("Aleksander", "Wieczorek"), ("Błażej", "Jabłoński"),
    ("Czesław", "Król"), ("Damian", "Majewski"), ("Eryk", "Olszewski"),
    ("Feliks", "Jaworski"), ("Gerard", "Wróbel"), ("Hubert", "Malinowski"),
]


def _generuj_type_ratings(kategoria: Kategoria, dzien: date, indeks: int = 0) -> list[TypeRating]:
    """
    Generuje uprawnienia type rating zgodne z zakresem rotacji każdej kategorii.

    Kategoria A: LST + STOL (2 ratingi; tylko VFR i w dzień)
    Kategoria B: LST + STOL + HEMS średni + opcjonalnie MEDEVAC (40 proc. w awansie na C)
    Kategoria C: 4 klasy LPR (MEDEVAC, HEMS, LST, STOL)
    Kategoria D: 4 klasy LPR (multi-rating pełny)
    """
    mapowanie = {
        # A: jeden śmigłowiec plus jeden samolot (dozwolone połączenie wg ORO.FC.240)
        Kategoria.A: [KlasaMaszyny.LST_LEKKI, KlasaMaszyny.STOL_SAMOLOT],
        # B/C/D: tylko śmigłowce (do trzech typów), bez samolotu STOL
        Kategoria.B: [KlasaMaszyny.LST_LEKKI, KlasaMaszyny.HEMS_SREDNI],
        Kategoria.C: [KlasaMaszyny.MEDEVAC_CIEZKI, KlasaMaszyny.HEMS_SREDNI,
                      KlasaMaszyny.LST_LEKKI],
        Kategoria.D: [KlasaMaszyny.MEDEVAC_CIEZKI, KlasaMaszyny.HEMS_SREDNI,
                      KlasaMaszyny.LST_LEKKI],
    }
    klasy = list(mapowanie[kategoria])

    # Specjalna logika kat B: 40 proc. pilotów ma dodatkowo type rating MEDEVAC
    # (są w trakcie awansu na kat C — latają jako FO pod nadzorem PIC kat C/D)
    if kategoria == Kategoria.B and indeks < 4:
        klasy.append(KlasaMaszyny.MEDEVAC_CIEZKI)

    ratings = []
    for klasa in klasy:
        # Każdy type rating ważny 12 miesięcy od ostatniego lotu
        dni_od_ostatniego = random.randint(0, 89)  # do 89 dni - aktualny
        data_lotu = dzien - timedelta(days=dni_od_ostatniego)
        data_uzyskania = dzien - timedelta(days=random.randint(365, 3650))
        data_waznosci = data_lotu + timedelta(days=365)
        ratings.append(TypeRating(
            klasa=klasa,
            data_uzyskania=data_uzyskania,
            data_ostatniego_lotu=data_lotu,
            data_waznosci=data_waznosci,
        ))
    return ratings


def _generuj_historie_misji(pilot_id: str, kategoria: Kategoria, dzien: date) -> list[Misja]:
    """Generuje historię misji pilota z ostatnich 30 dni."""
    historia = []
    liczba_misji = random.randint(8, 18)
    for _ in range(liczba_misji):
        dni_temu = random.randint(0, 30)
        data_misji = dzien - timedelta(days=dni_temu)
        klasa = random.choice(list(KlasaMaszyny))
        typ = random.choice([TypDyzuru.DYZUR_24H, TypDyzuru.ZMIANA_6H, TypDyzuru.ON_CALL_24H])
        if typ == TypDyzuru.DYZUR_24H:
            czas = random.uniform(2.0, 6.0)
        elif typ == TypDyzuru.ZMIANA_6H:
            czas = random.uniform(1.5, 4.5)
        else:
            czas = random.uniform(0.5, 3.0)
        naca = SkalaNACA(random.randint(2, 6))
        historia.append(Misja(
            data=data_misji,
            czas_trwania_h=czas,
            klasa_maszyny=klasa,
            naca=naca,
            typ_dyzuru=typ,
        ))
    return historia


def generuj_pilotow(dzien_referencyjny: date) -> list[Pilot]:
    """
    Generuje pulę testową 30 pilotów LPR.

    Rozkład kategorii: A=10, B=10, C=7, D=3
    """
    rozklad_lpr = (
        [Kategoria.A] * 10 +
        [Kategoria.B] * 10 +
        [Kategoria.C] * 7 +
        [Kategoria.D] * 3
    )
    bazy_lpr = [b.id for b in BAZY if b.organizacja == Organizacja.LPR]
    piloci = []
    indeksy_w_kategorii = {Kategoria.A: 0, Kategoria.B: 0, Kategoria.C: 0, Kategoria.D: 0}

    # Piloci LPR
    for i, kat in enumerate(rozklad_lpr):
        imie, nazwisko = IMIONA[i]
        pid = f"P{i+1:03d}"
        idx = indeksy_w_kategorii[kat]
        pilot = Pilot(
            id=pid,
            imie=imie,
            nazwisko=nazwisko,
            kategoria=kat,
            baza_macierzysta=random.choice(bazy_lpr),
            organizacja=Organizacja.LPR,
            type_ratings=_generuj_type_ratings(kat, dzien_referencyjny, idx),
            historia_misji=_generuj_historie_misji(pid, kat, dzien_referencyjny),
        )
        piloci.append(pilot)
        indeksy_w_kategorii[kat] += 1

    return piloci


def generuj_sloty(dzien_poczatkowy: date, dni: int = 7) -> list[SlotDyzurowy]:
    """
    Generuje tygodniowy zestaw slotów dyżurowych dla 5 baz.

    Każdy dzień:
    - 3 dyżury MEDEVAC 24h (w 3 hubach)
    - 4 dyżury HEMS Primary 24h (w 3 hubach + 1 FOB Łódź)
    - 2 zmiany LST 6h (w 4 bazach × 2 = 8 slotów)
    - 1 dyżur on-call STOL (Katowice)
    - 1 sesja treningowa (rotacyjnie między hubami) — instruktor kat D + pilot kat A/B
    """
    sloty = []
    slot_id = 0
    huby_treningowe = ["EPWA", "EPKK", "EPWR"]
    for dzien_offset in range(dni):
        dzien = dzien_poczatkowy + timedelta(days=dzien_offset)

        # MEDEVAC ciężki AW101 — ZAWSZE załoga dwuosobowa (certyfikacja EASA CS-29)
        # Niezależnie od warunków pogodowych czy rodzaju misji
        for hub_id in ["EPWA", "EPKK", "EPWR"]:
            slot_id += 1
            sloty.append(SlotDyzurowy(
                id=f"S{slot_id:04d}",
                baza_id=hub_id,
                data=dzien,
                typ_dyzuru=TypDyzuru.DYZUR_24H,
                wymagana_klasa=KlasaMaszyny.MEDEVAC_CIEZKI,
                wymagana_kategoria_min=Kategoria.C,
                tryb_misji=TrybMisji.DWA_PILOTY,  # AW101 zawsze 2 pilotów
            ))

        # HEMS Primary H145 24h w 3 hubach + 1 FOB (Łódź)
        # ~30 proc. dyżurów to hi-risk (bad weather, IFR noc, wyciągarka)
        for baza_id in ["EPWA", "EPKK", "EPWR", "EPLL"]:
            slot_id += 1
            tryb = TrybMisji.DWA_PILOTY if random.random() < 0.30 else TrybMisji.SINGLE_PILOT
            sloty.append(SlotDyzurowy(
                id=f"S{slot_id:04d}",
                baza_id=baza_id,
                data=dzien,
                typ_dyzuru=TypDyzuru.DYZUR_24H,
                wymagana_klasa=KlasaMaszyny.HEMS_SREDNI,
                wymagana_kategoria_min=Kategoria.B,
                tryb_misji=tryb,
            ))

        # LST 6h (2 zmiany dziennie) w 4 bazach LPR z HEMS
        for baza_id in ["EPWA", "EPKK", "EPWR", "EPLL"]:
            for _ in range(2):
                slot_id += 1
                sloty.append(SlotDyzurowy(
                    id=f"S{slot_id:04d}",
                    baza_id=baza_id,
                    data=dzien,
                    typ_dyzuru=TypDyzuru.ZMIANA_6H,
                    wymagana_klasa=KlasaMaszyny.LST_LEKKI,
                    wymagana_kategoria_min=Kategoria.A,
                ))

        # Rzeszów-Jasionka (EPRZ): specjalny FOB-LST 7-21 (jedyny FOB nie 24/7)
        # Tylko LST H135, 2 zmiany: poranna (7-15) i popołudniowa (13-21)
        # Bez HEMS Primary, bez MEDEVAC
        for _ in range(2):
            slot_id += 1
            sloty.append(SlotDyzurowy(
                id=f"S{slot_id:04d}",
                baza_id="EPRZ",
                data=dzien,
                typ_dyzuru=TypDyzuru.ZMIANA_6H,
                wymagana_klasa=KlasaMaszyny.LST_LEKKI,
                wymagana_kategoria_min=Kategoria.A,
            ))

        # STOL Grand Caravan EX w Katowicach
        # Zawsze jednoosobowy, kapitan kat A z pełną licencją STOL. W trudnych
        # warunkach dyspozytor włącza mentora/obserwatora (trudny_lot) — dodatkowa,
        # niepilotująca załoga z prywatną biegłością STOL, nie copilot.
        slot_id += 1
        sloty.append(SlotDyzurowy(
            id=f"S{slot_id:04d}",
            baza_id="EPKT",
            data=dzien,
            typ_dyzuru=TypDyzuru.ON_CALL_24H,
            wymagana_klasa=KlasaMaszyny.STOL_SAMOLOT,
            wymagana_kategoria_min=Kategoria.A,
            tryb_misji=TrybMisji.SINGLE_PILOT,
        ))

        # Sesja treningowa: rotacyjnie między hubami i klasami maszyn
        # Parzyste dni: trening HEMS, nieparzyste: trening LST (A+D)
        # Instruktor kat D szkoli pilota niższej kategorii
        hub_treningowy = huby_treningowe[dzien_offset % len(huby_treningowe)]
        klasa_treningu = (KlasaMaszyny.HEMS_SREDNI if dzien_offset % 2 == 0
                          else KlasaMaszyny.LST_LEKKI)
        slot_id += 1
        sloty.append(SlotDyzurowy(
            id=f"S{slot_id:04d}",
            baza_id=hub_treningowy,
            data=dzien,
            typ_dyzuru=TypDyzuru.TRENING,
            wymagana_klasa=klasa_treningu,
            wymagana_kategoria_min=Kategoria.A,  # szkolony może być kat A
        ))

    return sloty
