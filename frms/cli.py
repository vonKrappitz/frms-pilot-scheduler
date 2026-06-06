# Copyright 2026 Maciej M. Kasperek ("vonKrappitz")
# SPDX-License-Identifier: Apache-2.0
"""
Interfejs konsoli (CLI) systemu FRMS.

Użycie:
    python -m frms.cli generuj-harmonogram
    python -m frms.cli alerty
    python -m frms.cli statystyki
    python -m frms.cli pilot P001
"""

import sys
from datetime import date
from collections import defaultdict

from frms.data import BAZY, generuj_pilotow, generuj_sloty
from frms.scheduler import generuj_harmonogram
from frms.validator import alerty_type_rating, alerty_przeciazenia, statystyki_systemu


def cmd_generuj_harmonogram():
    """Generuje tygodniowy harmonogram dyżurów dla 5 baz testowych."""
    dzien = date.today()
    piloci = generuj_pilotow(dzien)
    sloty = generuj_sloty(dzien, dni=7)
    obsadzone, nieobsadzone = generuj_harmonogram(sloty, piloci)

    print("=" * 80)
    print(f"HARMONOGRAM DYŻURÓW LPR — tydzień od {dzien}")
    print("=" * 80)
    print(f"Slotów łącznie: {len(sloty)}")
    print(f"Obsadzonych:    {len(obsadzone)} ({100*len(obsadzone)/len(sloty):.1f}%)")
    print(f"Nieobsadzonych: {len(nieobsadzone)}")
    print()

    pilot_dict = {p.id: p for p in piloci}

    # Grupuj po dniu i bazie
    grupy = defaultdict(list)
    for s in obsadzone:
        grupy[(s.data, s.baza_id)].append(s)

    for (data_slot, baza_id), grupa in sorted(grupy.items()):
        baza_nazwa = next((b.nazwa for b in BAZY if b.id == baza_id), baza_id)
        print(f"\n{data_slot} | {baza_id} ({baza_nazwa}):")
        for s in grupa:
            pilot = pilot_dict[s.przypisany_pilot_id]
            if s.typ_dyzuru.value == "TRENING" and s.instruktor_id:
                instruktor = pilot_dict[s.instruktor_id]
                print(f"  {s.typ_dyzuru.value:12s} | {s.wymagana_klasa.value:18s} "
                      f"| INSTRUKTOR: {instruktor.id} ({instruktor.imie} {instruktor.nazwisko}, kat. {instruktor.kategoria.value}) "
                      f"+ SZKOLONY: {pilot.id} ({pilot.imie} {pilot.nazwisko}, kat. {pilot.kategoria.value})")
            elif s.drugi_pilot_id:
                fo = pilot_dict[s.drugi_pilot_id]
                org_tag = f" [{s.organizacja.value}]" if s.organizacja.value != "LPR" else ""
                print(f"  {s.typ_dyzuru.value:12s} | {s.wymagana_klasa.value:18s}{org_tag} | [ZAŁOGA 2-OSOBOWA] "
                      f"PIC: {pilot.id} ({pilot.imie} {pilot.nazwisko}, kat. {pilot.kategoria.value}) "
                      f"+ FO: {fo.id} ({fo.imie} {fo.nazwisko}, kat. {fo.kategoria.value})")
            else:
                org_tag = f" [{s.organizacja.value}]" if s.organizacja.value != "LPR" else ""
                print(f"  {s.typ_dyzuru.value:12s} | {s.wymagana_klasa.value:18s}{org_tag} "
                      f"| Pilot {pilot.id} ({pilot.imie} {pilot.nazwisko}, kat. {pilot.kategoria.value})")

    if nieobsadzone:
        print("\n" + "!" * 80)
        print(f"SLOTY NIEOBSADZONE ({len(nieobsadzone)}):")
        print("!" * 80)
        for s in nieobsadzone:
            print(f"  {s.data} | {s.baza_id} | {s.typ_dyzuru.value} | {s.wymagana_klasa.value}")


def cmd_alerty():
    """Wypisuje wszystkie alerty operacyjne."""
    dzien = date.today()
    piloci = generuj_pilotow(dzien)
    alerty_tr = alerty_type_rating(piloci, dzien)
    alerty_p = alerty_przeciazenia(piloci, dzien)

    print("=" * 80)
    print(f"ALERTY OPERACYJNE — {dzien}")
    print("=" * 80)

    print(f"\n[1] ALERTY TYPE RATING ({len(alerty_tr)})")
    print("-" * 80)
    if not alerty_tr:
        print("  Brak alertów.")
    for a in alerty_tr[:20]:  # max 20 najpilniejszych
        print(f"  [{a['priorytet']:6s}] {a['pilot_id']} {a['imie_nazwisko']:25s} "
              f"kat. {a['kategoria']} | {a['klasa']:18s} | "
              f"wygasa za {a['dni_do_wygasniecia']:3d} dni | "
              f"od lotu {a['dni_od_ostatniego_lotu']:3d} dni")

    print(f"\n[2] ALERTY OBCIĄŻENIA ({len(alerty_p)})")
    print("-" * 80)
    if not alerty_p:
        print("  Brak alertów.")
    for a in alerty_p:
        print(f"  [{a['priorytet']:6s}] {a['pilot_id']} {a['imie_nazwisko']:25s} | "
              f"{a['typ']} | {a.get('wartosc', '')}")


def cmd_statystyki():
    """Wypisuje statystyki agregowane systemu."""
    dzien = date.today()
    piloci = generuj_pilotow(dzien)
    stat = statystyki_systemu(piloci, dzien)

    print("=" * 80)
    print(f"STATYSTYKI SYSTEMU FRMS — {dzien}")
    print("=" * 80)
    print(f"\nLiczba pilotów MEDEVAC: {stat['liczba_pilotow']}")
    print("\nRozkład kategorii kompetencyjnych:")
    for kat, liczba in stat["rozklad_kategorii"].items():
        print(f"  Kategoria {kat}: {liczba:3d} pilotów")
    print(f"\nType rating aktualne: {stat['type_ratings_aktualne_proc']}%")
    print(f"Piloci gotowi do dyżuru 24h: {stat['piloci_gotowi_do_dyzuru_24h']}/{stat['liczba_pilotow']}")
    print(f"Średnie obciążenie 96h: {stat['srednie_obciazenie_96h']}h")


def cmd_pilot(pilot_id: str):
    """Wypisuje szczegółową kartę pilota."""
    dzien = date.today()
    piloci = generuj_pilotow(dzien)
    pilot = next((p for p in piloci if p.id == pilot_id), None)
    if pilot is None:
        print(f"Pilot {pilot_id} nie znaleziony.")
        return

    print("=" * 80)
    print(f"KARTA PILOTA — {pilot.id}")
    print("=" * 80)
    print(f"Imię i nazwisko: {pilot.imie} {pilot.nazwisko}")
    print(f"Kategoria: {pilot.kategoria.value}")
    print(f"Baza macierzysta: {pilot.baza_macierzysta}")
    print(f"Obciążenie 96h: {pilot.obciazenie_96h(dzien):.1f}h")
    print(f"Godziny od ostatniego dyżuru 24h: {pilot.godziny_od_ostatniego_dyzuru_24h(dzien)}h")
    print(f"Gotowy do dyżuru 24h: {'TAK' if pilot.gotowy_do_dyzuru_24h(dzien) else 'NIE'}")

    print(f"\nType ratings ({len(pilot.type_ratings)}):")
    for tr in pilot.type_ratings:
        status = "AKTUALNY" if tr.jest_aktualny(dzien) else "NIEAKTUALNY"
        print(f"  {tr.klasa.value:18s} | {status:11s} | "
              f"wygasa {tr.data_waznosci} (za {tr.dni_do_wygasniecia(dzien)} dni) | "
              f"ostatni lot {tr.data_ostatniego_lotu} ({tr.dni_od_ostatniego_lotu(dzien)} dni temu)")

    print(f"\nHistoria misji ({len(pilot.historia_misji)} w ostatnich 30 dniach):")
    for m in sorted(pilot.historia_misji, key=lambda x: x.data, reverse=True)[:10]:
        print(f"  {m.data} | {m.czas_trwania_h:.1f}h | {m.klasa_maszyny.value:18s} | "
              f"{m.typ_dyzuru.value:12s} | NACA {m.naca.value}")


def cmd_sesje_symulatorowe():
    """
    Wyświetla raport sesji symulatorowych w LAW Dęblin (baza EPDE)
    wymaganych dla aktywnej kadry pilotów.

    Pokazuje:
    - Pilotów wymagających currency recovery (przerwa lotów >21 lub >45 dni)
    - Pilotów wymagających recurrent kwartalnego (>90 dni od ostatniego treningu)
    - Łączną liczbę dni-osobogodzin symulatora wymaganych w tygodniu
    """
    from frms.currency import (
        opis_powodu_sesji,
        wymaga_currency_recovery,
        wymaga_recurrent_kwartalny,
    )
    from frms.scheduler import generuj_sloty_symulatorowe

    dzien = date.today()
    piloci = generuj_pilotow(dzien)
    sloty_sym = generuj_sloty_symulatorowe(piloci, dzien, dni=7)

    print("=" * 80)
    print(f"SESJE SYMULATOROWE LAW DĘBLIN (EPDE) — tydzień od {dzien}")
    print("=" * 80)

    # Reset historii sesji (bo generuj_sloty_symulatorowe je dodaje) -
    # raport pokaże co BY było wymagane gdyby nie dodawał historii
    # Cofamy: piloci_swiezzi musimy odróżnić
    # Najprościej: ponowne wygenerowanie pilotów do analizy
    piloci_raport = generuj_pilotow(dzien)

    wymagajacy_recovery = []
    wymagajacy_recurrent = []

    for pilot in piloci_raport:
        for tr in pilot.type_ratings:
            if not tr.jest_aktualny(dzien):
                continue
            if wymaga_recurrent_kwartalny(pilot, tr.klasa, dzien):
                powod = opis_powodu_sesji(pilot, tr.klasa, dzien)
                wymagajacy_recurrent.append((pilot, tr.klasa, powod))
            elif wymaga_currency_recovery(pilot, tr.klasa, dzien):
                powod = opis_powodu_sesji(pilot, tr.klasa, dzien)
                wymagajacy_recovery.append((pilot, tr.klasa, powod))

    print(f"\nPilotów z type rating aktywnym:  {sum(1 for p in piloci_raport if any(tr.jest_aktualny(dzien) for tr in p.type_ratings))}")
    print(f"Wymagających currency recovery:  {len(wymagajacy_recovery)}")
    print(f"Wymagających recurrent kwart.:   {len(wymagajacy_recurrent)}")
    print(f"Slotów SYMULATOR_LAW łącznie:    {len(sloty_sym)} (recovery liczy 2× dzień)")

    if wymagajacy_recurrent:
        print("\n--- RECURRENT KWARTALNY (2 dni × 6h) ---")
        for pilot, klasa, powod in wymagajacy_recurrent:
            print(f"  {pilot.id} ({pilot.imie} {pilot.nazwisko}, kat. {pilot.kategoria.value}) "
                  f"| {klasa.value:18s} | {powod}")

    if wymagajacy_recovery:
        print("\n--- CURRENCY RECOVERY (1 dzień × 6h + 24h odp.) ---")
        for pilot, klasa, powod in wymagajacy_recovery:
            print(f"  {pilot.id} ({pilot.imie} {pilot.nazwisko}, kat. {pilot.kategoria.value}) "
                  f"| {klasa.value:18s} | {powod}")

    if not wymagajacy_recovery and not wymagajacy_recurrent:
        print("\n  ✓ Wszyscy piloci mają aktualną świeżość operacyjną.")

    # Łączny czas symulatora w tygodniu
    czas_lacznie = sum(6.0 for _ in sloty_sym)
    print(f"\nŁączny czas symulatora w tygodniu: {czas_lacznie:.0f} h "
          f"({czas_lacznie/6:.0f} dni-pilotów)")


def main():
    if len(sys.argv) < 2:
        print("Użycie:")
        print("  python -m frms.cli generuj-harmonogram")
        print("  python -m frms.cli alerty")
        print("  python -m frms.cli statystyki")
        print("  python -m frms.cli sesje-symulatorowe")
        print("  python -m frms.cli pilot <ID>")
        sys.exit(1)

    komenda = sys.argv[1]
    if komenda == "generuj-harmonogram":
        cmd_generuj_harmonogram()
    elif komenda == "alerty":
        cmd_alerty()
    elif komenda == "statystyki":
        cmd_statystyki()
    elif komenda == "sesje-symulatorowe":
        cmd_sesje_symulatorowe()
    elif komenda == "pilot":
        if len(sys.argv) < 3:
            print("Podaj ID pilota, np. P001")
            sys.exit(1)
        cmd_pilot(sys.argv[2])
    else:
        print(f"Nieznana komenda: {komenda}")
        sys.exit(1)


if __name__ == "__main__":
    main()
