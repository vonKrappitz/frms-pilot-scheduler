# Copyright 2026 Maciej M. Kasperek ("vonKrappitz")
# SPDX-License-Identifier: Apache-2.0
"""
Algorytm doboru pilota do slotu dyżurowego.

Implementuje trzy zmienne kontrolne zgodne z EASA AMC1 ORO.FTL.110:
1. Aktualność type rating na wymaganą klasę maszyny (okno 90-dniowe Part-FCL)
2. Kumulacyjne obciążenie operacyjne z poprzednich 96 godzin
3. Pozycja pilota w 10-dniowym cyklu rotacyjnym anty-rutynowym
"""

from datetime import date
from typing import Optional

from frms.models import Kategoria, Pilot, SlotDyzurowy, TypDyzuru


# Hierarchia kategorii: A < B < C < D
HIERARCHIA = {Kategoria.A: 1, Kategoria.B: 2, Kategoria.C: 3, Kategoria.D: 4}


def kategoria_wystarczajaca(pilota: Kategoria, wymagana_min: Kategoria) -> bool:
    """Czy kategoria pilota spełnia minimum wymagane na slocie."""
    return HIERARCHIA[pilota] >= HIERARCHIA[wymagana_min]


def kandydat_kwalifikujacy_sie(pilot: Pilot, slot: SlotDyzurowy) -> tuple[bool, str]:
    """
    Sprawdza czy pilot może być przypisany do slotu.

    Zwraca (czy_kwalifikuje_sie, powod_odrzucenia_lub_pusty_string).
    """
    # 0. Separacja organizacji: pilot pracuje tylko w swojej organizacji
    #    Wyjątek: emergency_pilot_request — slot pozwala na cross-organization
    if pilot.organizacja != slot.organizacja and not slot.emergency_pilot_request:
        return False, f"pilot {pilot.organizacja.value} nie obsługuje slotu {slot.organizacja.value}"

    # 1. Kategoria pilota
    if not kategoria_wystarczajaca(pilot.kategoria, slot.wymagana_kategoria_min):
        return False, f"kategoria {pilot.kategoria.value} < wymagana {slot.wymagana_kategoria_min.value}"

    # 1b. Loty IFR/nocne: kategoria A lata wyłącznie VFR i w dzień (heli i STOL).
    #     Loty w warunkach IFR lub po zmroku wymagają minimum kategorii B.
    if slot.nocny_lub_ifr and pilot.kategoria == Kategoria.A:
        return False, "kat A lata tylko VFR i w dzień — slot nocny/IFR wymaga min. kat B"

    # 2. Aktualność type rating
    if not pilot.ma_type_rating(slot.wymagana_klasa, slot.data):
        return False, f"brak aktualnego type rating na {slot.wymagana_klasa.value}"

    # 3. EASA AMC1 ORO.FTL.110: dyżur 24h wymaga 48h odpoczynku po poprzednim
    if slot.typ_dyzuru == TypDyzuru.DYZUR_24H:
        if not pilot.gotowy_do_dyzuru_24h(slot.data):
            godziny = pilot.godziny_od_ostatniego_dyzuru_24h(slot.data)
            return False, f"odpoczynek {godziny}h < 48h od ostatniego dyżuru 24h"

    # 4. Przeciążenie tygodniowe (max 60h/7 dni)
    if pilot.przeciazony(slot.data):
        return False, "przekroczenie 60h w oknie 7 dni"

    return True, ""


def score_pilota(pilot: Pilot, slot: SlotDyzurowy) -> float:
    """
    Funkcja oceny pilota dla slotu — niższy wynik = lepszy kandydat.

    Składowe:
    - Obciążenie 96h (niskie = lepiej)
    - Hierarchia kategorii (niższa = lepiej, by nie marnować D na proste sloty)
    - Premia za bliski koniec ważności type rating (negative score = wyżej w rankingu)
    """
    obciazenie = pilot.obciazenie_96h(slot.data)
    hierarchia_kara = HIERARCHIA[pilot.kategoria] * 0.5

    # Premia za pilnowanie type rating: -2.0 jeśli rating wygasa w 30 dniach
    premia_rating = 0.0
    for tr in pilot.type_ratings:
        if tr.klasa == slot.wymagana_klasa:
            if tr.dni_od_ostatniego_lotu(slot.data) >= 60:
                premia_rating = -2.0  # potrzebuje aktywności na tym typie
            break

    return obciazenie + hierarchia_kara + premia_rating


def dobierz_pare_medevac(
    slot: SlotDyzurowy,
    piloci: list[Pilot],
) -> Optional[tuple[Pilot, Pilot]]:
    """
    Dobór załogi dwuosobowej dla misji wymagających dwóch pilotów.

    Reguły zależą od klasy maszyny:

    AW101 (MEDEVAC ciężki cywilny) — zawsze załoga 2-osobowa, zgodnie z
    certyfikacją EASA CS-29. Dozwolone konfiguracje (Tabela 1 manuskryptu):
      operacyjne (dwóch samodzielnych MEDEVAC): C+C, C+D, D+D
      szkoleniowa/nadzorowana: B+D — instruktor D (PIC) nadzoruje szkolonego B (FO)

    Reguła nadrzędna: pilota bez samodzielnych uprawnień MEDEVAC (kat B) może
    wziąć na pokład wyłącznie instruktor kat D, więc B lata MEDEVAC tylko z D.
    Preferencja oszczędza deficytową kadrę D; B+D jest ostatecznością na slocie
    operacyjnym. Niedozwolone: C+B, B+B (kat C nie jest instruktorem) oraz A w
    dowolnej roli MEDEVAC.

    H145 (HEMS), Grand Caravan EX (STOL) w trybie DWA_PILOTY:
      PIC kat C+ z aktualnym type rating + FO dowolnej kategorii (A/B/C/D)
      z aktualnym type rating. Niższe kategorie FO preferowane (oszczędność D).

    Każdy z dwóch pilotów musi mieć aktualny type rating EASA Part-FCL na klasę.
    Filtrowanie organizacyjne: piloci tylko dla slotów własnej organizacji.

    Zwraca (PIC, FO) lub None jeśli brak dostępnej pary.
    """
    from frms.models import Kategoria, KlasaMaszyny

    def pilot_dostepny(p: Pilot) -> bool:
        """Sprawdza dostępność pilota: organizacja + type rating + odpoczynek."""
        if p.organizacja != slot.organizacja and not slot.emergency_pilot_request:
            return False
        if not p.ma_type_rating(slot.wymagana_klasa, slot.data):
            return False
        if slot.typ_dyzuru == TypDyzuru.DYZUR_24H and not p.gotowy_do_dyzuru_24h(slot.data):
            return False
        if p.przeciazony(slot.data):
            return False
        return True

    dostepni = [p for p in piloci if pilot_dostepny(p)]
    if len(dostepni) < 2:
        return None

    # AW101: specjalna logika 6 konfiguracji preferowanych
    if slot.wymagana_klasa == KlasaMaszyny.MEDEVAC_CIEZKI:
        po_kategorii = {Kategoria.B: [], Kategoria.C: [], Kategoria.D: []}
        for p in dostepni:
            if p.kategoria in po_kategorii:
                po_kategorii[p.kategoria].append(p)
        for kat in po_kategorii:
            po_kategorii[kat].sort(key=lambda p: p.obciazenie_96h(slot.data))

        # Konfiguracje wg Tabeli 1 manuskryptu. Preferencja: najpierw dwa
        # samodzielne MEDEVAC, oszczędzając deficytową kadrę D; B+D na końcu,
        # bo na slocie operacyjnym B nie jest samodzielny. PIC = wyższa kategoria.
        C, D, B = po_kategorii[Kategoria.C], po_kategorii[Kategoria.D], po_kategorii[Kategoria.B]
        if len(C) >= 2:
            return (C[0], C[1])            # C+C — standard operacyjny
        if C and D:
            return (D[0], C[0])            # C+D — PIC = D
        if len(D) >= 2:
            return (D[0], D[1])            # D+D
        if D and B:
            return (D[0], B[0])            # B+D — PIC = D nadzoruje szkolonego B (FO)
        return None

    # H145, Grand Caravan EX w trybie 2-osobowym: PIC kat C+ + FO dowolny
    kandydaci_pic = [
        p for p in dostepni
        if HIERARCHIA[p.kategoria] >= HIERARCHIA[Kategoria.C]
    ]
    if not kandydaci_pic:
        return None
    pic = min(kandydaci_pic, key=lambda p: (
        HIERARCHIA[p.kategoria],
        p.obciazenie_96h(slot.data),
    ))

    kandydaci_fo = [p for p in dostepni if p.id != pic.id]
    if not kandydaci_fo:
        return None
    fo = min(kandydaci_fo, key=lambda p: (
        HIERARCHIA[p.kategoria],
        p.obciazenie_96h(slot.data),
    ))

    return (pic, fo)


def dobierz_pilota(slot: SlotDyzurowy, piloci: list[Pilot]) -> Optional[Pilot]:
    """
    Główny algorytm: znajdź najlepszego kandydata dla slotu.

    Zwraca Pilot lub None jeśli nie ma kwalifikującego się.
    """
    kandydaci = []
    for p in piloci:
        ok, _powod = kandydat_kwalifikujacy_sie(p, slot)
        if ok:
            kandydaci.append((score_pilota(p, slot), p))

    if not kandydaci:
        return None

    # Sortuj rosnąco po wyniku — pierwszy = najlepszy
    kandydaci.sort(key=lambda x: x[0])
    return kandydaci[0][1]


def dobierz_pare_treningowa(
    slot: SlotDyzurowy,
    piloci: list[Pilot],
) -> Optional[tuple[Pilot, Pilot]]:
    """
    Specjalna logika dla slotów TRENING.

    Znajduje parę: instruktor kategorii D + pilot szkolony niższej kategorii.
    Priorytet dla szkolonego: pilot który NIE MA jeszcze type rating na wymaganą
    klasę (rozszerzenie kompetencji) lub którego rating wymaga odświeżenia.

    Zwraca (instruktor, szkolony) lub None.
    """
    from frms.models import Kategoria

    # 1. Znajdź instruktorów: kat D z aktualnym type rating na wymaganą klasę
    instruktorzy = [
        p for p in piloci
        if p.kategoria == Kategoria.D
        and p.ma_type_rating(slot.wymagana_klasa, slot.data)
        and not p.przeciazony(slot.data)
    ]
    if not instruktorzy:
        return None

    # Wybierz instruktora z najniższym obciążeniem 96h
    instruktor = min(instruktorzy, key=lambda p: p.obciazenie_96h(slot.data))

    # 2. Znajdź szkolonego: pilot kategorii A/B/C który:
    #    - NIE ma aktualnego type rating na wymaganą klasę (rozszerzenie), LUB
    #    - ma rating ale wymaga alertu (recurrent training)
    kandydaci_szkoleni = []
    for p in piloci:
        if p.kategoria == Kategoria.D:
            continue  # instruktorzy nie szkolą instruktorów
        if p.id == instruktor.id:
            continue
        if p.przeciazony(slot.data):
            continue

        # Priorytet 1: pilot bez type rating na klasę (chce się nauczyć)
        ma_rating = any(tr.klasa == slot.wymagana_klasa for tr in p.type_ratings)
        if not ma_rating:
            kandydaci_szkoleni.append((1, p))
            continue

        # Priorytet 2: pilot z type rating wymagającym alertu (recurrent)
        for tr in p.type_ratings:
            if tr.klasa == slot.wymagana_klasa and tr.wymaga_alertu(slot.data):
                kandydaci_szkoleni.append((2, p))
                break

    if not kandydaci_szkoleni:
        return None

    # Sortuj: najpierw priorytet 1 (rozszerzenia), potem priorytet 2 (recurrent)
    # W ramach grupy: najniższe obciążenie 96h
    kandydaci_szkoleni.sort(key=lambda x: (x[0], x[1].obciazenie_96h(slot.data)))
    szkolony = kandydaci_szkoleni[0][1]

    return (instruktor, szkolony)


def generuj_harmonogram(
    sloty: list[SlotDyzurowy],
    piloci: list[Pilot],
) -> tuple[list[SlotDyzurowy], list[SlotDyzurowy]]:
    """
    Generuje harmonogram: przypisuje pilotów do slotów.

    Obsługuje dwa tryby:
    - Sloty operacyjne (DYZUR_24H, ZMIANA_6H, ON_CALL_24H) — jeden pilot
    - Sloty TRENING — para (instruktor kat D + pilot szkolony)

    Po przypisaniu pilota do slotu dodaje wirtualną misję do jego historii.
    Dla treningu obciążenie liczone osobno dla obu pilotów.

    Twarda reguła: jeden pilot może być obsadzony tylko na jednej maszynie w danym
    dniu (jako PIC, drugi pilot lub instruktor); na pozostałe sloty tego dnia jest
    niedostępny.
    """
    from frms.models import Misja, SkalaNACA

    obsadzone = []
    nieobsadzone = []
    sloty_posortowane = sorted(sloty, key=lambda s: s.data)
    # Twarda wyłączność: jeden pilot = jedna maszyna w danym dniu. Pilot przypisany
    # do slotu (jako PIC, drugi pilot lub instruktor) jest niedostępny dla pozostałych
    # slotów tego samego dnia.
    zajeci_w_dniu: dict[date, set[str]] = {}

    for slot in sloty_posortowane:
        zajeci = zajeci_w_dniu.setdefault(slot.data, set())
        dostepni = [p for p in piloci if p.id not in zajeci]
        if slot.typ_dyzuru == TypDyzuru.TRENING:
            # Specjalna logika: para instruktor + szkolony
            para = dobierz_pare_treningowa(slot, dostepni)
            if para is not None:
                instruktor, szkolony = para
                slot.instruktor_id = instruktor.id
                slot.przypisany_pilot_id = szkolony.id
                zajeci.update({instruktor.id, szkolony.id})
                obsadzone.append(slot)

                # Trening trwa ~4h (briefing teoretyczny + lot + debriefing)
                czas_treningu = 4.0
                for p in (instruktor, szkolony):
                    p.historia_misji.append(Misja(
                        data=slot.data,
                        czas_trwania_h=czas_treningu,
                        klasa_maszyny=slot.wymagana_klasa,
                        naca=SkalaNACA.NACA_0,  # trening = brak pacjenta
                        typ_dyzuru=TypDyzuru.TRENING,
                    ))
            else:
                nieobsadzone.append(slot)
        elif slot.wymaga_dwoch_pilotow():
            # MEDEVAC ciężki: załoga dwuosobowa (PIC + FO)
            para = dobierz_pare_medevac(slot, dostepni)
            if para is not None:
                pic, fo = para
                slot.przypisany_pilot_id = pic.id
                slot.drugi_pilot_id = fo.id
                zajeci.update({pic.id, fo.id})
                obsadzone.append(slot)

                # Obaj piloci obciążeni dyżurem 24h
                szacowany_czas = 4.0
                for p in (pic, fo):
                    p.historia_misji.append(Misja(
                        data=slot.data,
                        czas_trwania_h=szacowany_czas,
                        klasa_maszyny=slot.wymagana_klasa,
                        naca=SkalaNACA.NACA_4,
                        typ_dyzuru=slot.typ_dyzuru,
                    ))
            else:
                nieobsadzone.append(slot)
        else:
            # Standardowy slot operacyjny — jeden pilot
            pilot = dobierz_pilota(slot, dostepni)
            if pilot is not None:
                slot.przypisany_pilot_id = pilot.id
                zajeci.add(pilot.id)
                obsadzone.append(slot)

                if slot.typ_dyzuru == TypDyzuru.DYZUR_24H:
                    szacowany_czas = 4.0
                elif slot.typ_dyzuru == TypDyzuru.ZMIANA_6H:
                    szacowany_czas = 3.5
                else:
                    szacowany_czas = 1.5

                pilot.historia_misji.append(Misja(
                    data=slot.data,
                    czas_trwania_h=szacowany_czas,
                    klasa_maszyny=slot.wymagana_klasa,
                    naca=SkalaNACA.NACA_3,
                    typ_dyzuru=slot.typ_dyzuru,
                ))
            else:
                nieobsadzone.append(slot)

    return obsadzone, nieobsadzone


# ============================================================
# SLOTY SYMULATOROWE LAW DĘBLIN
# ============================================================

def generuj_sloty_symulatorowe(
    piloci: list[Pilot],
    dzien_start: date,
    dni: int = 7,
) -> list[SlotDyzurowy]:
    """
    Generuje sloty SYMULATOR_LAW dla pilotów wymagających sesji currency recovery
    lub recurrent kwartalnego w bazie EPDE (Lotnicza Akademia Wojskowa Dęblin).

    Sprawdza każdego pilota dla każdego type rating; jeśli pilot wymaga sesji
    w tym tygodniu — generuje odpowiednie sloty (1 dzień dla recurrent lub
    2 dni dla currency recovery).

    Sloty generowane są od dnia start. Każdy slot ma:
    - baza_id = "EPDE"
    - typ_dyzuru = TypDyzuru.SYMULATOR_LAW
    - wymagana_klasa = klasa symulatora (AW101, H145, H135, Grand Caravan EX)
    - przypisany_pilot_id = pilot, który ma odbyć sesję
    """
    from frms.currency import generuj_sesje_symulatorowe_dla_pilota

    sloty: list[SlotDyzurowy] = []
    slot_counter = 0

    for pilot in piloci:
        sesje = generuj_sesje_symulatorowe_dla_pilota(pilot, dzien_start)
        for sesja in sesje:
            # Sesja musi mieścić się w oknie tygodnia
            if (sesja.data - dzien_start).days >= dni:
                continue
            slot_counter += 1
            slot = SlotDyzurowy(
                id=f"SYM-{slot_counter:04d}",
                baza_id="EPDE",
                data=sesja.data,
                typ_dyzuru=TypDyzuru.SYMULATOR_LAW,
                wymagana_klasa=sesja.klasa_maszyny,
                wymagana_kategoria_min=pilot.kategoria,
                organizacja=pilot.organizacja,
                przypisany_pilot_id=pilot.id,
            )
            sloty.append(slot)

            # Dodaj sesję do historii pilota (do śledzenia currency w kolejnych iteracjach)
            pilot.historia_sesji_symulatorowych.append(sesja)

    return sloty


def piloci_wylaczeni_w_dniu(
    piloci: list[Pilot],
    sloty_symulatorowe: list[SlotDyzurowy],
    dzien: date,
) -> set[str]:
    """
    Zwraca zbiór ID pilotów wyłączonych z puli operacyjnej w danym dniu
    z powodu sesji symulatorowej w LAW Dęblin.

    Wyłączenie obejmuje:
    - dzień sesji symulatorowej (sym = pilot fizycznie w Dęblinie)
    - dzień następujący po 2-dniowej recovery (24h odpoczynku)
    """
    wylaczeni: set[str] = set()
    for slot in sloty_symulatorowe:
        if slot.data == dzien:
            wylaczeni.add(slot.przypisany_pilot_id)
    return wylaczeni
