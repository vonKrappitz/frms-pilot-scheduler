# Copyright 2026 Maciej M. Kasperek ("vonKrappitz")
# SPDX-License-Identifier: Apache-2.0
"""
Pula zamienników pilota dla slotu dyżurowego.

Dyspozytor wskazuje pilota do zwolnienia, a system zwraca listę kandydatów,
którymi można go podmienić bez naruszenia kwalifikacji, świeżości i odpoczynku.

Reguła kategorii jest twarda: slot wymagający kategorii C nie przyjmie pilota A.
Wyjątek szkoleniowy: w slocie dwuosobowym drugi fotel może objąć pilot dokładnie
jedną kategorię poniżej minimum, jeśli pierwszy pilot (PIC) to kategoria D. Taki
lot jest oznaczony jako szkoleniowy, a nadzorujący D zostaje powiadomiony i może
zgłosić sprzeciw. Przykłady: MEDEVAC (min C) z PIC kat D dopuszcza kat B; HEMS
(min B) z PIC kat D dopuszcza kat A.
"""

from dataclasses import dataclass
from typing import Optional

from frms.models import Kategoria, KlasaMaszyny, Pilot, SlotDyzurowy, TypDyzuru
from frms.scheduler import HIERARCHIA, kandydat_kwalifikujacy_sie, score_pilota
from frms.currency import wymaga_currency_recovery, KLASY_BEZ_SYM_I_SZKOLEN
from frms.kursy import spelnia_kursy, dostepny_w_dniu
from frms.stol import stol_biegly_prywatnie
from frms.awanse import moze_przyjac_szkolenie


@dataclass
class Kandydat:
    """Pilot możliwy do wstawienia w zwolniony fotel slotu."""
    pilot: Pilot
    lot_szkoleniowy: bool = False             # ścieżka wyjątku (kategoria o jeden poniżej minimum)
    nadzorujacy_id: Optional[str] = None      # PIC kat D nadzorujący; może zgłosić sprzeciw
    obserwator: bool = False                  # STOL: dodatkowa, niepilotująca załoga (mentor/asystent), nie copilot
    adnotacja: str = ""


def _piloci_zajeci_dnia(sloty: list[SlotDyzurowy], dzien, pomijany_id: Optional[str] = None) -> set[str]:
    """Id pilotów już obsadzonych (PIC, FO, instruktor) w dowolnym slocie tego dnia.

    Zwalniany pilot jest pomijany, bo jego fotel właśnie się otwiera.
    """
    zajeci: set[str] = set()
    for s in sloty:
        if s.data != dzien:
            continue
        for pid in (s.przypisany_pilot_id, s.drugi_pilot_id, s.instruktor_id):
            if pid is not None and pid != pomijany_id:
                zajeci.add(pid)
    return zajeci


def kandydaci_zamiany(
    slot: SlotDyzurowy,
    zwalniany_id: str,
    piloci: list[Pilot],
    sloty: list[SlotDyzurowy],
) -> list[Kandydat]:
    """Lista zamienników dla pilota `zwalniany_id` w danym slocie.

    Najpierw kandydaci normalni (posortowani od najlepszego), potem ewentualni
    kandydaci szkoleniowi z wyjątku.
    """
    by_id = {p.id: p for p in piloci}
    zajeci = _piloci_zajeci_dnia(sloty, slot.data, zwalniany_id)

    fotel_drugi = (slot.drugi_pilot_id == zwalniany_id)
    pic_id = slot.przypisany_pilot_id
    pic = by_id.get(pic_id) if (pic_id and pic_id != zwalniany_id) else None
    pierwszy_to_D = pic is not None and pic.kategoria == Kategoria.D

    prog = HIERARCHIA[slot.wymagana_kategoria_min]
    wynik: list[Kandydat] = []

    for p in piloci:
        if p.id == zwalniany_id or p.id in zajeci:
            continue
        if not dostepny_w_dniu(p, slot.data):
            continue  # urlop obowiązuje na każdej ścieżce

        # Ścieżka normalna: pełna kwalifikacja, brak restrykcji currency, komplet kursów.
        ok, _ = kandydat_kwalifikujacy_sie(p, slot)
        if (ok and not wymaga_currency_recovery(p, slot.wymagana_klasa, slot.data)
                and spelnia_kursy(p, slot.wymagana_klasa)):
            wynik.append(Kandydat(p))
            continue

        # Ścieżka wyjątku szkoleniowego.
        if slot.wymagana_klasa in KLASY_BEZ_SYM_I_SZKOLEN:
            continue  # klasy wyłączone ze szkolenia (obecnie brak)
        if not (fotel_drugi and slot.wymaga_dwoch_pilotow() and pierwszy_to_D):
            continue
        if HIERARCHIA[p.kategoria] != prog - 1:
            continue  # tylko dokładnie jedna kategoria poniżej minimum
        if not moze_przyjac_szkolenie(p, slot.data):
            continue  # uczeń: limit 2 loty szkoleniowe na 7 dni
        if p.organizacja != slot.organizacja and not slot.emergency_pilot_request:
            continue  # separacja organizacji obowiązuje
        if slot.nocny_lub_ifr and p.kategoria == Kategoria.A:
            continue  # kat A nie lata nocą/IFR nawet szkoleniowo
        if slot.typ_dyzuru == TypDyzuru.DYZUR_24H and not p.gotowy_do_dyzuru_24h(slot.data):
            continue  # odpoczynek obowiązuje
        if p.przeciazony(slot.data):
            continue  # limit tygodniowy obowiązuje
        wynik.append(Kandydat(
            pilot=p,
            lot_szkoleniowy=True,
            nadzorujacy_id=pic.id,
            adnotacja=(
                f"lot szkoleniowy: kat {p.kategoria.value} poniżej minimum "
                f"{slot.wymagana_kategoria_min.value}, nadzór kat D ({pic.id}). "
                f"Nadzorujący może zgłosić sprzeciw."
            ),
        ))

    # Normalni najpierw (od najlepszego score), szkoleniowi na końcu.
    wynik.sort(key=lambda k: (k.lot_szkoleniowy, score_pilota(k.pilot, slot)))
    return wynik


def _kwalifikuje_normalnie(p: Pilot, slot: SlotDyzurowy) -> bool:
    """Pełna kwalifikacja operacyjna plus brak restrykcji currency."""
    ok, _ = kandydat_kwalifikujacy_sie(p, slot)
    return ok and not wymaga_currency_recovery(p, slot.wymagana_klasa, slot.data)


def instruktor_slotu(slot: SlotDyzurowy, piloci: list[Pilot]) -> Optional[Pilot]:
    """Zwraca pilota dowodzącego slotem, jeśli jest kategorii D (potencjalny instruktor)."""
    by_id = {p.id: p for p in piloci}
    p = by_id.get(slot.przypisany_pilot_id)
    return p if (p is not None and p.kategoria == Kategoria.D) else None


def kandydaci_szkoleniowi(
    slot: SlotDyzurowy, piloci: list[Pilot], sloty: list[SlotDyzurowy]
) -> list[Kandydat]:
    """Fotel szkoleniowy przy maszynie jednoosobowej obsadzonej przez kat D.

    D może szkolić tylko kandydatów do danej klasy: kategoria nie niżej niż jedna
    poniżej minimum klasy (nie wolno przeskakiwać szczebli). Na MEDEVAC (min C)
    szkoli B, C, D; na HEMS (min B) szkoli A, B, C, D; A na MEDEVAC nie wejdzie,
    bo musi najpierw zrobić B. Bez wymogu type ratingu. Obowiązują wypoczynek,
    dostępność i separacja organizacji. Sloty dwuosobowe operacyjne mają osobny
    fotel (patrz kandydaci_zamiany), więc tu są pomijane.
    """
    instr = instruktor_slotu(slot, piloci)
    if (instr is None or slot.wymaga_dwoch_pilotow()
            or slot.wymagana_klasa in KLASY_BEZ_SYM_I_SZKOLEN
            or slot.wymagana_klasa == KlasaMaszyny.STOL_SAMOLOT):
        return []  # STOL: instruktaż formalny poza korpusem; mentor idzie pulą obserwatora
    prog_min = HIERARCHIA[slot.wymagana_kategoria_min] - 1  # jedna poniżej minimum klasy
    zajeci = _piloci_zajeci_dnia(sloty, slot.data)  # instruktor jest obsadzony, więc wypada
    wynik: list[Kandydat] = []
    for p in piloci:
        if p.id == instr.id or p.id in zajeci:
            continue
        if not dostepny_w_dniu(p, slot.data):
            continue
        if not moze_przyjac_szkolenie(p, slot.data):
            continue  # uczeń: limit 2 loty szkoleniowe na 7 dni
        if HIERARCHIA[p.kategoria] < prog_min:
            continue  # za niska kategoria — nie jest kandydatem do tej klasy
        if p.organizacja != slot.organizacja and not slot.emergency_pilot_request:
            continue
        if slot.nocny_lub_ifr and p.kategoria == Kategoria.A:
            continue
        if slot.typ_dyzuru == TypDyzuru.DYZUR_24H and not p.gotowy_do_dyzuru_24h(slot.data):
            continue
        if p.przeciazony(slot.data):
            continue
        wynik.append(Kandydat(
            pilot=p, lot_szkoleniowy=True, nadzorujacy_id=instr.id,
            adnotacja=(f"lot szkoleniowy pod nadzorem kat D ({instr.id}); "
                       f"nadzorujący może zgłosić sprzeciw"),
        ))
    wynik.sort(key=lambda k: (HIERARCHIA[k.pilot.kategoria], k.pilot.id))
    return wynik


def kandydaci_obserwatora_stol(
    slot: SlotDyzurowy, piloci: list[Pilot], sloty: list[SlotDyzurowy]
) -> list[Kandydat]:
    """Nieformalny mentor lub obserwator dla slotu STOL w trudnych warunkach.

    Kapitanem i jedynym odpowiedzialnym pozostaje pilot kat A z pełną licencją
    STOL (Caravan jest jednopilotowy, więc prawo nie wymaga drugiego pilota).
    Kandydaci to piloci B/C/D z prywatną biegłością STOL: samozgłoszeniem i
    świeżymi godzinami w wewnętrznym rejestrze, bez wymogu formalnego ratingu.
    Wchodzą jako dodatkowa, niepilotująca załoga (radzą, wspierają, nasłuchują),
    nie copilot. D mentoruje nieformalnie; formalny instruktaż na typie samolotu
    leży poza korpusem A–D. Pierwszy pilot i zajęci tego dnia są pomijani.
    """
    if slot.wymagana_klasa != KlasaMaszyny.STOL_SAMOLOT or not slot.trudny_lot:
        return []
    zajeci = _piloci_zajeci_dnia(sloty, slot.data)
    wynik: list[Kandydat] = []
    for p in piloci:
        if p.id == slot.przypisany_pilot_id or p.id in zajeci:
            continue
        if p.kategoria == Kategoria.A:
            continue  # A jest kapitanem STOL, nie obserwatorem
        if not dostepny_w_dniu(p, slot.data):
            continue
        if not stol_biegly_prywatnie(p, slot.data):
            continue
        if p.kategoria == Kategoria.D:
            adn = "mentor nieformalny (instruktaż formalny poza korpusem); kapitanem kat A"
        else:
            adn = "obserwator/asystent, prywatna biegłość STOL; dodatkowa, niepilotująca załoga; kapitanem kat A"
        wynik.append(Kandydat(pilot=p, obserwator=True, adnotacja=adn))
    # mentor (kat D) przed wsparciem operacyjnym, dalej po id
    wynik.sort(key=lambda k: (0 if k.pilot.kategoria == Kategoria.D else 1, k.pilot.id))
    return wynik
