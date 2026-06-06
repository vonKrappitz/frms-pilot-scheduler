# Copyright 2026 Maciej M. Kasperek ("vonKrappitz")
# SPDX-License-Identifier: Apache-2.0
"""
Modele danych Fatigue Risk Management System (FRMS) dla pilotów MEDEVAC.

Zgodne z EASA AMC1 ORO.FTL.110 oraz GM1 ORO.FTL.120.
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum
from typing import Optional


class Organizacja(Enum):
    """
    Organizacja operacyjna pilota lub bazy.

    LPR: Lotnicze Pogotowie Ratunkowe (cywilny operator państwowy)
    """
    LPR = "LPR"


class Kategoria(Enum):
    """Czterostopniowa hierarchia kompetencyjna Pilotów MEDEVAC."""
    A = "A"  # Pilot podstawowy: LST + STOL (H135 + Caravan), tylko VFR i w dzień
    B = "B"  # Pilot standardowy: LST + HEMS (H135 + H145); od B w górę loty IFR i nocne
    C = "C"  # Pilot zaawansowany: trzy typy śmigłowca (H135 + H145 + AW101), kapitan MEDEVAC
    D = "D"  # Pilot specjalistyczny: instruktor i kapitan floty; trzy typy (H135 + H145 + AW101)


class Kurs(Enum):
    """Kursy specjalistyczne wymagane do lotów HEMS i MEDEVAC."""
    LOT_NOCNY = "LOT_NOCNY"               # lot w warunkach nocnych
    ZAWIS_WCIAGARKA = "ZAWIS_WCIAGARKA"   # zawis z pracującą wciągarką
    GOGLE_NOCNE = "GOGLE_NOCNE"           # lot w goglach nocnych (NVG)
    FIKI = "FIKI"                         # lot w znanych warunkach oblodzenia (Flight Into Known Icing)


class KlasaMaszyny(Enum):
    """
    Cztery klasy operacyjne floty po reformie.

    Zasady eksploatacji załogowej różnią się między klasami:
    - AW101: zawsze załoga dwuosobowa, bez wyjątku (certyfikacja EASA CS-29)
    - H145: single/dual w zależności od trudności misji
    - H135: zawsze single pilot operacyjnie, NIE lata w trudnych warunkach;
            2 pilotów dozwoleni tylko w trybie TRENING (instruktor D + szkolony A)
    - Grand Caravan EX: zawsze single pilot
    """
    MEDEVAC_CIEZKI = "MEDEVAC_AW101"   # cywilny LPR ciężki AW101 — ZAWSZE 2 pilotów
    HEMS_SREDNI = "HEMS_H145"           # cywilny HEMS H145 — single/dual
    LST_LEKKI = "LST_H135"              # LST H135 — single (lub trening A+D)
    STOL_SAMOLOT = "STOL_GRAND_CARAVAN_EX"  # STOL Cessna Grand Caravan EX — zawsze single


class StatusMaszyny(Enum):
    """Status egzemplarza maszyny w puli krajowej."""
    OPERACYJNA = "OPERACYJNA"              # czynna służba, dostępna do obsady
    REZERWA_KRAJOWA = "REZERWA_KRAJOWA"    # rezerwa — wchodzi, gdy operacyjna stoi w serwisie
    REZERWA_ZELAZNA = "REZERWA_ZELAZNA"    # zakonserwowana, na wypadek kryzysu — nie obsadzana


class PoziomSerwisu(Enum):
    """Trzy poziomy obsługi technicznej egzemplarza (progi w KonfiguracjaSerwisu)."""
    POBIEZNY = "POBIEZNY"   # przegląd liniowy/okresowy lekki — w hubie macierzystym, 1 dzień
    POWAZNY = "POWAZNY"     # przegląd okresowy ciężki — ośrodek remontowy (EPLB), 3 dni
    REMONT = "REMONT"       # remont główny — ośrodek remontowy (EPLB), 30 dni


class TypDyzuru(Enum):
    """Typy dyżurów w cyklu rotacyjnym 10-dniowym."""
    DYZUR_24H = "DYZUR_24H"            # MEDEVAC, HEMS Primary (24h ciągły)
    ZMIANA_6H = "ZMIANA_6H"            # LST (zmiana poranna 8-14 lub popołudniowa 14-20)
    ON_CALL_24H = "ON_CALL_24H"        # STOL (dyżur domowy z gotowością startu 60 min)
    TRENING = "TRENING"                # Sesja szkoleniowa: instruktor (kat D) + pilot szkolony
    SYMULATOR_LAW = "SYMULATOR_LAW"    # Sesja symulatorowa w LAW Dęblin (6h, EPDE)
    ODPOCZYNEK = "ODPOCZYNEK"          # 48-godzinny odpoczynek po dyżurze 24h


class TrybMisji(Enum):
    """
    Tryb operacyjny misji MEDEVAC ciężkiej (AW101).

    SINGLE_PILOT: typowy transport międzyszpitalny w dobrej pogodzie.
    Wystarcza jeden pilot kat C+ z aktualnym type rating MEDEVAC.

    DWA_PILOTY: misje hi-risk wymagające załogi dwuosobowej:
    - bad weather / IMC (Instrument Meteorological Conditions)
    - operacje z wyciągarką ratowniczą
    - misje nocne w trudnym terenie (morze, góry)
    - ECMO / transport pacjenta w stanie krytycznym
    Konfiguracje załogi MEDEVAC (AW101): C+C (standard) lub B+D (B szkolony
    pod instruktorem D). Niedozwolone: C+B, B+B.
    """
    SINGLE_PILOT = "SINGLE_PILOT"
    DWA_PILOTY = "DWA_PILOTY"


class SkalaNACA(Enum):
    """Skala stopnia ciężkości misji medycznej (National Advisory Committee for Aeronautics)."""
    NACA_0 = 0  # brak urazu lub choroby
    NACA_1 = 1  # niegroźne obrażenia/dolegliwości
    NACA_2 = 2  # umiarkowane obrażenia
    NACA_3 = 3  # poważne obrażenia
    NACA_4 = 4  # potencjalnie zagrożone życie
    NACA_5 = 5  # bezpośrednio zagrożone życie
    NACA_6 = 6  # natychmiastowa reanimacja
    NACA_7 = 7  # zgon


@dataclass
class TypeRating:
    """Pojedyncze uprawnienie type rating EASA Part-FCL na konkretną klasę maszyny."""
    klasa: KlasaMaszyny
    data_uzyskania: date
    data_ostatniego_lotu: date
    data_waznosci: date  # 12 miesięcy od ostatniego lotu / kursu odnawiającego

    def dni_do_wygasniecia(self, dzien_referencyjny: date) -> int:
        """Liczba dni do wygaśnięcia type rating."""
        return (self.data_waznosci - dzien_referencyjny).days

    def dni_od_ostatniego_lotu(self, dzien_referencyjny: date) -> int:
        """Liczba dni od ostatniego lotu na tym typie maszyny."""
        return (dzien_referencyjny - self.data_ostatniego_lotu).days

    def jest_aktualny(self, dzien_referencyjny: date) -> bool:
        """Czy type rating jest aktualny (EASA Part-FCL: maks. 90 dni bez lotu)."""
        return (
            self.dni_do_wygasniecia(dzien_referencyjny) > 0
            and self.dni_od_ostatniego_lotu(dzien_referencyjny) <= 90
        )

    def wymaga_alertu(self, dzien_referencyjny: date) -> bool:
        """Alert: type rating wygasa w ciągu 30 dni LUB nieaktywny powyżej 60 dni."""
        return (
            self.dni_do_wygasniecia(dzien_referencyjny) <= 30
            or self.dni_od_ostatniego_lotu(dzien_referencyjny) >= 60
        )


@dataclass
class Misja:
    """Pojedyncza wykonana misja operacyjna pilota."""
    data: date
    czas_trwania_h: float
    klasa_maszyny: KlasaMaszyny
    naca: SkalaNACA
    typ_dyzuru: TypDyzuru
    czy_symulator: bool = False  # True jeśli sesja symulatorowa w LAW Dęblin (nie liczy jako lot operacyjny do currency)
    maszyna_id: Optional[str] = None      # egzemplarz maszyny w puli krajowej (np. "H1", "L12", "X3", "S2")
    drugi_pilot_id: Optional[str] = None  # załoga dwuosobowa: ID drugiego pilota (kto z kim latał)
    czy_szkoleniowy: bool = False         # lot szkoleniowy pod nadzorem kat D (liczy do limitu ucznia)


@dataclass
class SesjaSymulatorowa:
    """
    Pojedyncza sesja symulatorowa w LAW Dęblin (kod ICAO EPDE).

    Dwa typy zgodnie z polityką currency Korpusu:
    - currency_recovery: po przekroczeniu progu dni bez lotu operacyjnego
      (21 dni dla helikopterów, 45 dla samolotu STOL Grand Caravan EX).
      Format: 1 dzień × 6h.
    - recurrent_kwartalny: obowiązkowy trening okresowy co 90 dni
      niezależnie od historii lotów, z trudnymi elementami (awarie, sytuacje
      graniczne). Format: 2 kolejne dni × 6h. Recurrent resetuje licznik dni
      bez lotu.
    """
    data: date
    klasa_maszyny: KlasaMaszyny
    czas_trwania_h: float = 6.0
    czy_recurrent: bool = False      # True: recurrent kwartalny (2 dni)
    czy_currency_recovery: bool = False  # True: odzyskiwanie świeżości (1 dzień)
    starty_ladowania: int = 0   # (zaszłość) łączna liczba; nowe pola poniżej rozdzielają starty i lądowania
    starty: int = 0             # liczba startów w sesji recovery
    ladowania: int = 0          # liczba lądowań w sesji recovery  # zaliczone starty i lądowania w sesji; recovery ważne dopiero od 5


@dataclass
class Pilot:
    """Pilot MEDEVAC."""
    id: str
    imie: str
    nazwisko: str
    kategoria: Kategoria
    baza_macierzysta: str
    organizacja: Organizacja = Organizacja.LPR
    type_ratings: list[TypeRating] = field(default_factory=list)
    historia_misji: list[Misja] = field(default_factory=list)
    historia_sesji_symulatorowych: list[SesjaSymulatorowa] = field(default_factory=list)
    nalot_logbook_h: float = 0.0  # nalot historyczny spoza okna historia_misji (suma z logbooka)
    kursy: list["Kurs"] = field(default_factory=list)   # ukończone kursy specjalistyczne
    dni_wolne: list[date] = field(default_factory=list) # dni wolne / życzenia urlopowe
    stol_prywatnie: bool = False                        # samozgłoszenie: lata STOL prywatnie (PPL, własny koszt)
    stol_rejestr: list[tuple[date, float]] = field(default_factory=list)  # wewn. rejestr: (data zgłoszenia, godziny STOL w miesiącu)

    def ma_type_rating(self, klasa: KlasaMaszyny, dzien: date) -> bool:
        """Czy pilot ma aktualny type rating na daną klasę maszyny."""
        for tr in self.type_ratings:
            if tr.klasa == klasa and tr.jest_aktualny(dzien):
                return True
        return False

    def obciazenie_96h(self, dzien_referencyjny: date) -> float:
        """Kumulacyjna liczba godzin lotu w ostatnich 96 godzinach (4 dni)."""
        granica = dzien_referencyjny - timedelta(days=4)
        return sum(
            m.czas_trwania_h
            for m in self.historia_misji
            if granica <= m.data <= dzien_referencyjny
        )

    def godziny_od_ostatniego_dyzuru_24h(self, dzien_referencyjny: date) -> int:
        """Liczba godzin od zakończenia ostatniego dyżuru 24-godzinnego."""
        ostatni = None
        for m in sorted(self.historia_misji, key=lambda x: x.data, reverse=True):
            if m.typ_dyzuru == TypDyzuru.DYZUR_24H:
                ostatni = m.data
                break
        if ostatni is None:
            return 999  # brak historii = pełna gotowość
        return (dzien_referencyjny - ostatni).days * 24

    def gotowy_do_dyzuru_24h(self, dzien_referencyjny: date) -> bool:
        """EASA AMC1 ORO.FTL.110: minimum 48h odpoczynku po dyżurze 24h."""
        return self.godziny_od_ostatniego_dyzuru_24h(dzien_referencyjny) >= 48

    def przeciazony(self, dzien_referencyjny: date) -> bool:
        """Przekroczenie 60h pracy w oknie 7 dni — limit EASA."""
        granica = dzien_referencyjny - timedelta(days=7)
        suma_7d = sum(
            m.czas_trwania_h
            for m in self.historia_misji
            if granica <= m.data <= dzien_referencyjny
        )
        return suma_7d > 60.0


@dataclass
class Baza:
    """Baza operacyjna LPR (hub, FOB lub baza wsparcia)."""
    id: str
    nazwa: str
    typ: str  # "HUB", "FOB", "WSPARCIE", "SEZONOWA"
    klasy_maszyn: list[KlasaMaszyny] = field(default_factory=list)
    organizacja: Organizacja = Organizacja.LPR


@dataclass
class Maszyna:
    """
    Egzemplarz statku powietrznego w puli krajowej.

    Maszyny nie mają stałej bazy — krążą między hubami zgodnie z dyslokacją
    operacyjną. Oznaczenie kodowe: litera klasy + numer (Hx HEMS, Lx LST,
    Xx MEDEVAC, Sx STOL). Nalot egzemplarza oraz wykaz pilotów, którzy na nim
    latali i z kim, wyprowadza się z historii misji przez pole maszyna_id.
    """
    id: str  # oznaczenie kodowe, np. "H1", "L12", "X3", "S2"
    klasa: KlasaMaszyny
    status: StatusMaszyny = StatusMaszyny.OPERACYJNA
    aktualny_hub: Optional[str] = None  # kod CRL, do którego maszyna jest teraz przydzielona
    nalot_h: float = 0.0                # bieżący nalot od ostatniego remontu — podstawa resursu i terminów przeglądów
    w_serwisie_do: Optional[date] = None       # data powrotu z serwisu; do tego dnia maszyna wyłączona z obsady
    lokalizacja_serwisu: Optional[str] = None  # gdzie stoi w serwisie (hub macierzysty lub ośrodek remontowy)
    historia_serwisow: list = field(default_factory=list)  # lista obiektów Serwis (kolejne obsługi)


@dataclass
class KonfiguracjaSerwisu:
    """
    Konfigurowalne progi przeglądów (godziny nalotu między obsługami).
    Edytowalne w oknie konfiguracji — model serwisowy można dostroić.
    """
    serwis_pobiezny_h: float = 100.0   # przegląd liniowy / okresowy lekki
    serwis_powazny_h: float = 600.0    # przegląd okresowy ciężki
    remont_h: float = 3000.0           # remont główny (generalny), ośrodek przy CRL Lublin
    dni_serwis_pobiezny: int = 1
    dni_serwis_powazny: int = 3
    dni_remont: int = 30
    osrodek_powazny_remont: str = "EPLB"  # poważny i remont wyłącznie w ośrodku przy CRL Lublin


@dataclass
class Serwis:
    """Pojedyncza obsługa techniczna egzemplarza (wpis w historii serwisowej)."""
    poziom: "PoziomSerwisu"
    od: date
    do_dnia: date
    miejsce: str
    nalot_w_chwili: float = 0.0  # nalot egzemplarza w chwili skierowania (podstawa detekcji kolejnego progu)


@dataclass
class Konfiguracja:
    """
    Konfiguracja systemu FRMS — parametry zmienialne przez użytkownika.

    Wszystkie wartości mają sensowne domyślne, ale są edytowalne: model
    serwisowy (trzy progi) oraz wymagania nalotu utrzymujące biegłość na
    każdej klasie (można je podnieść lub obniżyć).
    """
    serwis: KonfiguracjaSerwisu = field(default_factory=KonfiguracjaSerwisu)
    # minimalny nalot miesięczny utrzymujący biegłość, per klasa (godziny)
    wymagany_nalot_miesiac_h: dict = field(default_factory=lambda: {
        KlasaMaszyny.MEDEVAC_CIEZKI: 12.0,
        KlasaMaszyny.HEMS_SREDNI: 10.0,
        KlasaMaszyny.LST_LEKKI: 8.0,
        KlasaMaszyny.STOL_SAMOLOT: 6.0,
    })


@dataclass
class SlotDyzurowy:
    """Pojedynczy slot dyżurowy do obsadzenia w bazie."""
    id: str
    baza_id: str
    data: date
    typ_dyzuru: TypDyzuru
    wymagana_klasa: KlasaMaszyny
    wymagana_kategoria_min: Kategoria  # minimum kategoria pilota głównego (PIC)
    organizacja: Organizacja = Organizacja.LPR
    # AW101: SINGLE_PILOT dla prostych misji, DWA_PILOTY dla hi-risk
    # (bad weather, wyciągarka, IFR noc) zgodnie z EASA Part-CAT.OP.MPA.135
    tryb_misji: TrybMisji = TrybMisji.SINGLE_PILOT
    emergency_pilot_request: bool = False  # pozwala na pilota z innej organizacji
    przypisany_pilot_id: Optional[str] = None  # PIC (kapitan, Pilot In Command)
    drugi_pilot_id: Optional[str] = None       # FO (drugi pilot, First Officer)
    instruktor_id: Optional[str] = None        # dla TRENING: kat D jako instruktor
    nocny_lub_ifr: bool = False  # slot nocny lub w warunkach IFR — wymaga min. kat B (kat A lata tylko VFR/dzień)
    maszyna_id: Optional[str] = None       # egzemplarz przydzielony do dyżuru (rejestr per maszyna, blok 1)
    maszyna_z_innej_bazy: bool = False     # True: brak egzemplarza w bazie, sprowadzony z puli krajowej (repozycja)
    trudny_lot: bool = False               # STOL: dyspozytor włącza drugiego pilota (ciężkie warunki / długi / powrotny)

    def wymaga_dwoch_pilotow(self) -> bool:
        """
        Reguły załogowe per klasa maszyny:
        - AW101 (MEDEVAC ciężki): ZAWSZE 2 pilotów, niezależnie od trybu
        - H145 HEMS: 2 pilotów tylko w trybie hi-risk (DWA_PILOTY)
        - H135 LST + Grand Caravan EX STOL: zawsze single (chyba że TRENING - obsługa osobno)
        """
        # AW101 — zawsze załoga dwuosobowa (certyfikacja EASA CS-29)
        if self.wymagana_klasa == KlasaMaszyny.MEDEVAC_CIEZKI:
            return True
        # H145 (HEMS) — dwa piloty tylko w hi-risk
        if self.wymagana_klasa == KlasaMaszyny.HEMS_SREDNI:
            return self.tryb_misji == TrybMisji.DWA_PILOTY
        # H135 i Grand Caravan EX — zawsze single (LST trening obsługiwany osobno przez TypDyzuru.TRENING)
        return False

    def jest_obsadzony(self) -> bool:
        if self.typ_dyzuru == TypDyzuru.TRENING:
            return self.przypisany_pilot_id is not None and self.instruktor_id is not None
        if self.wymaga_dwoch_pilotow():
            return self.przypisany_pilot_id is not None and self.drugi_pilot_id is not None
        return self.przypisany_pilot_id is not None
