"""
Moduł serwisu (blok 3): reguły kierowania egzemplarzy na obsługę techniczną.

Reguła miejsca: przegląd pobieżny w hubie macierzystym (1 dzień), poważny i
remont wyłącznie w ośrodku remontowym przy CRL Lublin (EPLB, 3 i 30 dni).
Skierowanie ustawia `w_serwisie_do` oraz wpis do historii. Maszyna w serwisie
sama wypada z obsady, bo `przydziel_maszyny` (blok 1) pomija egzemplarze z
ustawionym `w_serwisie_do`.

Detekcja należnego przeglądu liczy nalot od ostatniej obsługi danego poziomu
(zapisany w historii), więc po obsłudze próg się zeruje. Prognoza wyprzedzająca
to blok 9; tutaj jest sama reguła.

Zależności: tylko `frms.models` i `frms.rdzen`.
"""

from datetime import date, timedelta
from typing import Optional

from frms.models import KonfiguracjaSerwisu, PoziomSerwisu, Serwis, StatusMaszyny
from frms.rdzen import Rdzen


def czas_serwisu_dni(poziom: PoziomSerwisu, s: KonfiguracjaSerwisu) -> int:
    """Ile dni trwa obsługa danego poziomu."""
    return {
        PoziomSerwisu.POBIEZNY: s.dni_serwis_pobiezny,
        PoziomSerwisu.POWAZNY: s.dni_serwis_powazny,
        PoziomSerwisu.REMONT: s.dni_remont,
    }[poziom]


def prog_poziomu(poziom: PoziomSerwisu, s: KonfiguracjaSerwisu) -> float:
    """Próg nalotu (godziny) wyzwalający dany poziom obsługi."""
    return {
        PoziomSerwisu.POBIEZNY: s.serwis_pobiezny_h,
        PoziomSerwisu.POWAZNY: s.serwis_powazny_h,
        PoziomSerwisu.REMONT: s.remont_h,
    }[poziom]


def miejsce_serwisu(poziom: PoziomSerwisu, maszyna, s: KonfiguracjaSerwisu) -> str:
    """Gdzie kierujemy: pobieżny do huba macierzystego, poważny i remont do EPLB."""
    if poziom == PoziomSerwisu.POBIEZNY:
        return maszyna.aktualny_hub or s.osrodek_powazny_remont  # brak huba → ośrodek (bezpieczny default)
    return s.osrodek_powazny_remont


def w_serwisie(maszyna, dzien: date) -> bool:
    """Czy egzemplarz jest w serwisie w danym dniu (wyłączony z obsady)."""
    return maszyna.w_serwisie_do is not None and dzien <= maszyna.w_serwisie_do


def _nalot_od_ostatniego(maszyna, poziom: PoziomSerwisu) -> float:
    """Nalot narosły od ostatniej obsługi danego poziomu (lub od zera, gdy brak)."""
    baza = 0.0
    for w in maszyna.historia_serwisow:
        if w.poziom == poziom and w.nalot_w_chwili > baza:
            baza = w.nalot_w_chwili
    return maszyna.nalot_h - baza


def poziom_naleznego_przegladu(maszyna, s: KonfiguracjaSerwisu) -> Optional[PoziomSerwisu]:
    """Najcięższy poziom, którego próg maszyna przekroczyła od ostatniej takiej obsługi."""
    for poziom in (PoziomSerwisu.REMONT, PoziomSerwisu.POWAZNY, PoziomSerwisu.POBIEZNY):
        if _nalot_od_ostatniego(maszyna, poziom) >= prog_poziomu(poziom, s):
            return poziom
    return None


def skieruj(rdzen: Rdzen, maszyna_id: str, poziom: PoziomSerwisu, dzien: date) -> Optional[Serwis]:
    """Kieruje egzemplarz na obsługę: ustawia powrót, miejsce i wpis do historii.

    Zwraca utworzony wpis Serwis albo None, gdy brak takiej maszyny.
    """
    m = rdzen.maszyna(maszyna_id)
    if m is None:
        return None
    s = rdzen.konfiguracja.serwis
    do_dnia = dzien + timedelta(days=czas_serwisu_dni(poziom, s))
    miejsce = miejsce_serwisu(poziom, m, s)
    wpis = Serwis(poziom=poziom, od=dzien, do_dnia=do_dnia, miejsce=miejsce, nalot_w_chwili=m.nalot_h)
    m.w_serwisie_do = do_dnia
    m.lokalizacja_serwisu = miejsce
    m.historia_serwisow.append(wpis)
    return wpis


def przegladaj_flote(rdzen: Rdzen, dzien: date) -> list:
    """Auto-kieruje wszystkie operacyjne maszyny, którym należy się przegląd.

    Pomija te już w serwisie. Zwraca listę utworzonych wpisów Serwis.
    """
    s = rdzen.konfiguracja.serwis
    skierowane = []
    for m in rdzen.flota:
        if m.status != StatusMaszyny.OPERACYJNA or w_serwisie(m, dzien):
            continue
        poziom = poziom_naleznego_przegladu(m, s)
        if poziom is not None:
            wpis = skieruj(rdzen, m.id, poziom, dzien)
            if wpis is not None:
                skierowane.append(wpis)
    return skierowane


def zwolnij_po_terminie(rdzen: Rdzen, dzien: date) -> int:
    """Zwalnia z serwisu maszyny, których termin powrotu minął. Zwraca liczbę zwolnionych."""
    n = 0
    for m in rdzen.flota:
        if m.w_serwisie_do is not None and m.w_serwisie_do < dzien:
            m.w_serwisie_do = None
            m.lokalizacja_serwisu = None
            n += 1
    return n
