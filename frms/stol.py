# Copyright 2026 Maciej M. Kasperek ("vonKrappitz")
# SPDX-License-Identifier: Apache-2.0
"""
Prywatna biegłość STOL i wewnętrzny rejestr godzin.

Komercyjnie samolot STOL (Cessna Grand Caravan EX) lata wyłącznie kategoria A,
z pełną licencją na ten typ oraz na lekki śmigłowiec H135 (dozwolone połączenie
jeden samolot plus jeden śmigłowiec wg ORO.FC.240). Piloci B, C i D nie mają
kwalifikacji komercyjnej na STOL, ale ci, którzy latają go prywatnie (PPL, własny
koszt), mogą w trudnych warunkach siedzieć obok kapitana A jako nieformalny
mentor lub asystent: dodatkowa, niepilotująca załoga, nie copilot.

Operator prowadzi wewnętrzny rejestr: pilot co miesiąc sam zgłasza, czy latał
STOL prywatnie i ile godzin. Rejestr nie ma mocy regulacyjnej (nie zastępuje
kwalifikacji komercyjnej, którą ma tylko A); służy do wskazania, kto utrzymuje
prywatną biegłość i nadaje się na obserwatora. Dane są wyłącznie wewnętrzne.
"""

from datetime import date, timedelta

from frms.models import Kategoria, Pilot

MIN_GODZIN_STOL_PRYWATNE = 2.0   # minimum godzin w oknie, by uznać prywatną biegłość
OKNO_STOL_DNI = 62               # okno biegłości: ostatnie dwa miesiące


def godziny_stol_w_oknie(pilot: Pilot, dzien: date, okno_dni: int = OKNO_STOL_DNI) -> float:
    """Suma prywatnych godzin STOL zgłoszonych w oknie kończącym się w `dzien`."""
    prog = dzien - timedelta(days=okno_dni)
    return sum(godz for data_zgl, godz in pilot.stol_rejestr if prog <= data_zgl <= dzien)


def stol_biegly_prywatnie(pilot: Pilot, dzien: date) -> bool:
    """Czy pilot utrzymuje prywatną biegłość STOL: zgłosił status i ma świeże
    godziny w rejestrze. Tylko taki pilot może być mentorem/obserwatorem."""
    if not pilot.stol_prywatnie:
        return False
    return godziny_stol_w_oknie(pilot, dzien) >= MIN_GODZIN_STOL_PRYWATNE


# ---- enricher danych (deterministyczny, bez RNG, by nie ruszać scale_test) ----

def przypisz_stol_prywatny(piloci: list[Pilot], dzien: date) -> None:
    """Nadaje status prywatnego pilota STOL i comiesięczne zgłoszenie godzin.

    Deterministycznie: co trzeci pilot kategorii B, C lub D deklaruje prywatne
    latanie STOL; większość ma świeże zgłoszenie (biegli), a co dziewiąty
    zadeklarował, lecz nie zgłosił świeżych godzin (niebiegły), by pokazać, że to
    rejestr, a nie sama deklaracja, rozstrzyga o dopuszczeniu na obserwatora.
    """
    for i, p in enumerate(piloci):
        if p.kategoria in (Kategoria.B, Kategoria.C, Kategoria.D) and i % 3 == 0:
            p.stol_prywatnie = True
            if i % 9 == 0:
                p.stol_rejestr = []                       # zadeklarował, brak świeżych godzin
            else:
                p.stol_rejestr = [(dzien - timedelta(days=20), 4.0)]  # 4 h w ostatnim miesiącu
        else:
            p.stol_prywatnie = False
            p.stol_rejestr = []
