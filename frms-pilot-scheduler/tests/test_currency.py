# Copyright 2026 Maciej M. Kasperek ("vonKrappitz")
# SPDX-License-Identifier: Apache-2.0
"""
Testy nowego modelu sesji symulatorowych:
- recurrent kwartalny (jedna sesja na kwartał, domyślna klasa rotuje),
- zakres szkolenia „własne plus jedna wyżej",
- recovery: okno 45 dni, twardy limit 90 dla samolotu, priorytet, ważność od 5 startów.
"""

from datetime import date, timedelta

from frms.models import (
    Kategoria, KlasaMaszyny, Organizacja, Pilot, SesjaSymulatorowa, TypeRating,
)
from frms.currency import (
    kwartal, prog_currency_dni, priorytet_recovery, wymaga_currency_recovery,
    termin_recovery, dni_do_terminu_recovery, recovery_wazna,
    wymaga_recurrent_kwartalny, recurrent_odbyty_w_kwartale, zakres_szkolenia_symulator,
    klasa_recurrent_domyslna, generuj_sesje_symulatorowe_dla_pilota,
    PROG_DNI_BEZ_LOTU_HELI, PROG_DNI_BEZ_LOTU_SAMOLOT, OKNO_RECOVERY_DNI,
    MIN_STARTY_LADOWANIA_RECOVERY,
)

MEDEVAC = KlasaMaszyny.MEDEVAC_CIEZKI
HEMS = KlasaMaszyny.HEMS_SREDNI
LST = KlasaMaszyny.LST_LEKKI
STOL = KlasaMaszyny.STOL_SAMOLOT
DZIEN = date(2026, 6, 2)  # Q2 2026


def _tr(klasa, dni_od_lotu=10):
    lot = DZIEN - timedelta(days=dni_od_lotu)
    return TypeRating(klasa, lot - timedelta(days=400), lot, lot + timedelta(days=365))


def _pilot(kat, klasy, org=Organizacja.LPR, dni_od_lotu=10):
    return Pilot(id="P1", imie="x", nazwisko="y", kategoria=kat, baza_macierzysta="EPWA",
                 organizacja=org, type_ratings=[_tr(k, dni_od_lotu) for k in klasy])


# ---------------- recurrent kwartalny ----------------
def test_kwartal():
    assert kwartal(date(2026, 1, 15)) == (2026, 1)
    assert kwartal(date(2026, 6, 2)) == (2026, 2)
    assert kwartal(date(2026, 7, 1)) == (2026, 3)
    assert kwartal(date(2026, 12, 31)) == (2026, 4)


def test_recurrent_raz_na_kwartal():
    p = _pilot(Kategoria.C, [MEDEVAC, HEMS, LST, STOL])
    domyslna = klasa_recurrent_domyslna(p, DZIEN)
    assert domyslna is not None
    # świeży pilot: wymaga recurrent na klasie domyślnej, nie na innych
    assert wymaga_recurrent_kwartalny(p, domyslna, DZIEN) is True
    inne = [k for k in (MEDEVAC, HEMS, LST, STOL) if k != domyslna][0]
    assert wymaga_recurrent_kwartalny(p, inne, DZIEN) is False
    # po odbyciu recurrent w tym kwartale — już nie wymaga
    p.historia_sesji_symulatorowych.append(
        SesjaSymulatorowa(DZIEN, domyslna, 6.0, czy_recurrent=True))
    assert recurrent_odbyty_w_kwartale(p, DZIEN) is True
    assert wymaga_recurrent_kwartalny(p, domyslna, DZIEN) is False


def test_klasa_domyslna_rotuje():
    # MEDEVAC ćwiczony w zeszłym kwartale, reszta nigdy → domyślna to nie MEDEVAC
    p = _pilot(Kategoria.C, [MEDEVAC, HEMS, LST, STOL])
    p.historia_sesji_symulatorowych.append(
        SesjaSymulatorowa(date(2026, 3, 1), MEDEVAC, 6.0, czy_recurrent=True))
    assert klasa_recurrent_domyslna(p, DZIEN) != MEDEVAC


def test_zakres_jedna_wyzej():
    assert zakres_szkolenia_symulator(_pilot(Kategoria.A, [LST, STOL]), DZIEN) == {LST, STOL, HEMS}
    assert zakres_szkolenia_symulator(_pilot(Kategoria.B, [LST, STOL, HEMS]), DZIEN) == {LST, STOL, HEMS, MEDEVAC}
    assert zakres_szkolenia_symulator(_pilot(Kategoria.C, [MEDEVAC, HEMS, LST, STOL]), DZIEN) == {MEDEVAC, HEMS, LST, STOL}


# ---------------- recovery ----------------
def test_progi_recovery():
    assert prog_currency_dni(HEMS) == PROG_DNI_BEZ_LOTU_HELI == 21
    assert prog_currency_dni(STOL) == PROG_DNI_BEZ_LOTU_SAMOLOT == 45
    assert priorytet_recovery(HEMS) == "WYSOKI"
    assert priorytet_recovery(STOL) == "NISKI"


def test_recovery_heli_okno_i_priorytet():
    p = _pilot(Kategoria.C, [HEMS], dni_od_lotu=30)  # 30 > 21 → recovery
    assert wymaga_currency_recovery(p, HEMS, DZIEN) is True
    # termin = ostatnia aktywność + 21 + 45; ostatnia 30 dni temu → do terminu 21+45-30 = 36
    assert dni_do_terminu_recovery(p, HEMS, DZIEN) == PROG_DNI_BEZ_LOTU_HELI + OKNO_RECOVERY_DNI - 30
    assert priorytet_recovery(HEMS) == "WYSOKI"


def test_recovery_samolot_limit_90_i_niski_priorytet():
    p50 = _pilot(Kategoria.C, [STOL], dni_od_lotu=50)  # 50 > 45 → recovery
    assert wymaga_currency_recovery(p50, STOL, DZIEN) is True
    # twardy limit: 45 + 45 = 90 dni od ostatniej aktywności
    assert dni_do_terminu_recovery(p50, STOL, DZIEN) == 90 - 50
    # 30 dni < 45 → brak recovery dla samolotu
    p30 = _pilot(Kategoria.C, [STOL], dni_od_lotu=30)
    assert wymaga_currency_recovery(p30, STOL, DZIEN) is False
    assert termin_recovery(p30, STOL, DZIEN) is None


def test_recovery_wazna_od_pieciu_startow():
    zla = SesjaSymulatorowa(DZIEN, HEMS, 6.0, czy_currency_recovery=True, starty=4, ladowania=6)
    dobra = SesjaSymulatorowa(DZIEN, HEMS, 6.0, czy_currency_recovery=True,
                              starty=MIN_STARTY_LADOWANIA_RECOVERY, ladowania=MIN_STARTY_LADOWANIA_RECOVERY)
    assert recovery_wazna(zla) is False
    assert recovery_wazna(dobra) is True


# ---------------- generator ----------------
def test_generator_recurrent_plus_recovery():
    # C z czterema klasami; jedna klasa (nie domyślna) ma starą historię → recovery.
    p = _pilot(Kategoria.C, [MEDEVAC, HEMS, LST, STOL], dni_od_lotu=5)
    dom = klasa_recurrent_domyslna(p, DZIEN)
    # zestarz lot na jednej z NIE-domyślnych klas o 40 dni → recovery na niej
    inna = [k for k in (MEDEVAC, HEMS, LST, STOL) if k != dom][0]
    for tr in p.type_ratings:
        if tr.klasa == inna:
            tr.data_ostatniego_lotu = DZIEN - timedelta(days=40)
            tr.data_waznosci = DZIEN + timedelta(days=300)
    sesje = generuj_sesje_symulatorowe_dla_pilota(p, DZIEN)
    recurrent = [s for s in sesje if s.czy_recurrent]
    recovery = [s for s in sesje if s.czy_currency_recovery]
    assert len(recurrent) == 2  # 2 dni recurrent na klasie domyślnej
    assert all(s.klasa_maszyny == dom for s in recurrent)
    assert any(s.klasa_maszyny == inna for s in recovery)  # recovery na zestarzonej klasie
    # klasa domyślna nie generuje równolegle recovery
    assert all(s.klasa_maszyny != dom for s in recovery)
    # sesje recovery zaliczone z 5 startami
    assert all(s.czy_currency_recovery for s in recovery)
