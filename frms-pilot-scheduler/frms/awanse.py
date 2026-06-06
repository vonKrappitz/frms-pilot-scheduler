# Copyright 2026 Maciej M. Kasperek ("vonKrappitz")
# SPDX-License-Identifier: Apache-2.0
"""
Awanse pilotów: zatwierdzanie przez instruktorów.

Awans z kategorii na następną wymaga zatwierdzenia przez minimum trzech pilotów
kategorii D, a każdy zatwierdzający musi mieć w historii wspólne loty z danym
uczniem (powiązanie przez `drugi_pilot_id` w misjach, „kto z kim latał").

Brak automatycznego awansu: moduł liczy uprawnionych zatwierdzających i mówi, czy
jest ich dość. Decyzję podejmuje człowiek.

Druga część (progi nalotu i komplet kursów na każdy szczebel A→B, B→C, C→D oraz
limit szkoleń) dochodzi po ustaleniu wartości.
"""

from typing import Optional

from frms.models import Kategoria, KlasaMaszyny, Pilot
from frms.kursy import KURSY_WYMAGANE

MIN_ZATWIERDZAJACYCH_D = 3

# Progi nalotu całkowitego (godziny) na każdy szczebel. ROBOCZE — do ustalenia.
PROG_NALOTU_NA_KATEGORIE = {
    Kategoria.B: 500.0,
    Kategoria.C: 1000.0,
    Kategoria.D: 2000.0,
}

LIMIT_SZKOLEN_UCZEN_7DNI = 2  # uczeń: maksymalnie 2 loty szkoleniowe na 7 dni

_KOLEJNOSC = [Kategoria.A, Kategoria.B, Kategoria.C, Kategoria.D]


def nastepna_kategoria(kat: Kategoria) -> Optional[Kategoria]:
    """Następny szczebel ścieżki A→B→C→D, albo None dla D."""
    i = _KOLEJNOSC.index(kat)
    return _KOLEJNOSC[i + 1] if i + 1 < len(_KOLEJNOSC) else None


def latal_z(a: Pilot, b: Pilot) -> bool:
    """Czy w historii istnieje wspólny lot a i b (dowolny kierunek powiązania)."""
    if any(m.drugi_pilot_id == b.id for m in a.historia_misji):
        return True
    if any(m.drugi_pilot_id == a.id for m in b.historia_misji):
        return True
    return False


def instruktorzy_zatwierdzajacy(kandydat: Pilot, piloci: list[Pilot]) -> list[Pilot]:
    """Piloci kategorii D uprawnieni do zatwierdzenia awansu ucznia:
    kat D, nie sam kandydat, ze wspólną historią lotów z kandydatem."""
    return [
        d for d in piloci
        if d.kategoria == Kategoria.D and d.id != kandydat.id and latal_z(kandydat, d)
    ]


def liczba_zatwierdzajacych(kandydat: Pilot, piloci: list[Pilot]) -> int:
    return len(instruktorzy_zatwierdzajacy(kandydat, piloci))


def ma_dosc_zatwierdzajacych(kandydat: Pilot, piloci: list[Pilot]) -> bool:
    """Czy jest co najmniej MIN_ZATWIERDZAJACYCH_D uprawnionych instruktorów D."""
    return liczba_zatwierdzajacych(kandydat, piloci) >= MIN_ZATWIERDZAJACYCH_D


from datetime import date, timedelta


def nalot_calkowity(pilot: Pilot) -> float:
    """Całkowity nalot operacyjny: logbook historyczny plus godziny misji (bez symulatora)."""
    misje = sum(m.czas_trwania_h for m in pilot.historia_misji if not m.czy_symulator)
    return round(pilot.nalot_logbook_h + misje, 1)


def spelnia_nalot(pilot: Pilot, cel: Kategoria) -> bool:
    prog = PROG_NALOTU_NA_KATEGORIE.get(cel)
    return prog is None or nalot_calkowity(pilot) >= prog


_KLASA_KURSOW_AWANSU = {
    Kategoria.B: KlasaMaszyny.HEMS_SREDNI,      # na B kursy HEMS (lot nocny, gogle)
    Kategoria.C: KlasaMaszyny.MEDEVAC_CIEZKI,   # na C dochodzą wciągarka i FIKI
}


def spelnia_kursy_do_awansu(pilot: Pilot, cel: Kategoria) -> bool:
    """Kursy wchodzą szczeblami: na B komplet HEMS, na C komplet MEDEVAC (dokłada
    wciągarkę i FIKI, bramę na AW101). Na D bez nowych kursów."""
    klasa = _KLASA_KURSOW_AWANSU.get(cel)
    if klasa is None:
        return True
    return set(KURSY_WYMAGANE[klasa]).issubset(set(pilot.kursy))


def liczba_szkolen_ucznia_w_oknie(pilot: Pilot, dzien: date, dni: int = 7) -> int:
    """Loty szkoleniowe ucznia w ostatnich `dni` dniach. Sesje symulatorowe nie liczą się."""
    od = dzien - timedelta(days=dni - 1)
    return sum(1 for m in pilot.historia_misji
               if m.czy_szkoleniowy and not m.czy_symulator and od <= m.data <= dzien)


def moze_przyjac_szkolenie(pilot: Pilot, dzien: date) -> bool:
    """Czy uczeń nie przekroczył limitu 2 lotów szkoleniowych na 7 dni."""
    return liczba_szkolen_ucznia_w_oknie(pilot, dzien) < LIMIT_SZKOLEN_UCZEN_7DNI


def kwalifikuje_sie_do_awansu(pilot: Pilot, piloci: list[Pilot], dzien: date) -> dict:
    """Pełna ocena gotowości do awansu na następny szczebel.

    Zwraca słownik z cel, spełnieniem kryteriów i decyzją łączną. Brak
    automatycznego awansu: to jest rekomendacja dla człowieka.
    """
    cel = nastepna_kategoria(pilot.kategoria)
    if cel is None:
        return {"cel": None, "kwalifikuje": False}
    nalot_ok = spelnia_nalot(pilot, cel)
    kursy_ok = spelnia_kursy_do_awansu(pilot, cel)
    zatw = liczba_zatwierdzajacych(pilot, piloci)
    zatw_ok = zatw >= MIN_ZATWIERDZAJACYCH_D
    return {
        "cel": cel.value,
        "nalot_calkowity": nalot_calkowity(pilot),
        "prog_nalotu": PROG_NALOTU_NA_KATEGORIE.get(cel),
        "nalot_ok": nalot_ok,
        "kursy_ok": kursy_ok,
        "zatwierdzajacy": zatw,
        "zatwierdzajacy_ok": zatw_ok,
        "kwalifikuje": bool(nalot_ok and kursy_ok and zatw_ok),
    }


def przypisz_wspolne_loty_demo(piloci: list[Pilot], dzien: date) -> None:
    """Demo: ustawia kontekst awansowy na KOPII populacji — wspólną historię lotów
    kandydatów (kat A, B, C) z trzema pierwszymi instruktorami D oraz roboczy nalot
    życiowy per kategoria, aby zademonstrować wszystkie bramki awansu. Deterministyczne,
    bez RNG. Modyfikuje historia_misji i nalot_logbook_h, więc stosować na kopii.

    Dobór nalotu: A→600 h (przejdzie próg nalotu do B, ale brak kursów zablokuje),
    B→1200 h (przejdzie do C), C→2200 h (przejdzie do D)."""
    from frms.models import Misja, SkalaNACA, TypDyzuru, KlasaMaszyny as _KM
    d_ids = [p.id for p in piloci if p.kategoria == Kategoria.D][:3]
    nalot_demo = {Kategoria.A: 600.0, Kategoria.B: 1200.0, Kategoria.C: 2200.0}
    for p in piloci:
        if p.kategoria in (Kategoria.A, Kategoria.B, Kategoria.C):
            for i, did in enumerate(d_ids):
                p.historia_misji.append(Misja(
                    dzien - timedelta(days=10 + i), 1.0, _KM.MEDEVAC_CIEZKI,
                    SkalaNACA.NACA_3, TypDyzuru.DYZUR_24H, drugi_pilot_id=did))
            p.nalot_logbook_h = max(p.nalot_logbook_h, nalot_demo[p.kategoria])
