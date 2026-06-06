# Copyright 2026 Maciej M. Kasperek ("vonKrappitz")
# SPDX-License-Identifier: Apache-2.0
"""
Rejestr per egzemplarz (blok 1).

Po wygenerowaniu harmonogramu `przydziel_maszyny(rdzen)` dobiera do każdego
obsadzonego dyżuru operacyjnego konkretny egzemplarz wymaganej klasy i stempluje
nim slot oraz misje załogi. Dobór: najpierw z bazy slotu, dopiero potem z puli
krajowej (sprowadzenie spoza bazy, oznaczane flagą — egzemplarz repozycjonuje,
nie jest dostępny od ręki). Separacja serwisowa dociąża egzemplarz najbliższy
przeglądowi pobieżnemu, resztę trzyma rozłożoną.

Funkcje raportujące (`nalot_maszyny`, `kto_latal`, `obciazenie_floty`)
wyprowadzają stan floty z historii misji przez pole `Misja.maszyna_id`.

Zależności: tylko `frms.models` i `frms.rdzen`. Czas przebazowania (ferry) nie
jest tu modelowany — to ewentualne późniejsze dostrojenie.
"""

from datetime import date
from typing import Optional

from frms.models import StatusMaszyny, TypDyzuru
from frms.rdzen import Rdzen


def _dostepna(m, dzien: date) -> bool:
    """Egzemplarz dostępny: operacyjny i nie w serwisie tego dnia.

    Pola serwisowe Maszyny dochodzą w bloku 3; do tego czasu czytamy je
    ostrożnie przez getattr, więc reguła już działa, a blok 3 tylko je wypełni.
    """
    if m.status != StatusMaszyny.OPERACYJNA:
        return False
    w_serwisie_do = getattr(m, "w_serwisie_do", None)
    if w_serwisie_do is not None and dzien <= w_serwisie_do:
        return False
    return True


def _pozycja_w_cyklu(m, prog_h: float) -> float:
    """Pozycja egzemplarza w cyklu przeglądu pobieżnego (0..prog). Wyżej = bliżej przeglądu."""
    if prog_h <= 0:
        return 0.0
    return m.nalot_h % prog_h


def _ostempluj_misje(pilot, slot, maszyna_id: str) -> bool:
    """Wpisuje maszynę do zaplanowanej misji pilota dla tego slotu.

    Idzie od końca historii: scheduler dokleja zaplanowane misje na koniec, więc
    pierwsze trafienie od tyłu to właśnie ta misja, a nie wpis historyczny z tego
    samego dnia (kolizja możliwa tylko w dniu zerowym).
    """
    for mi in reversed(pilot.historia_misji):
        if (mi.maszyna_id is None
                and mi.data == slot.data
                and mi.klasa_maszyny == slot.wymagana_klasa
                and mi.typ_dyzuru == slot.typ_dyzuru):
            mi.maszyna_id = maszyna_id
            return True
    return False


def przydziel_maszyny(rdzen: Rdzen) -> dict:
    """Dobiera egzemplarze do obsadzonych dyżurów. Odpalać PO harmonogramie.

    Zwraca podsumowanie: ile przydzielono, ile sprowadzono spoza bazy, które
    sloty zostały bez maszyny.
    """
    prog = rdzen.konfiguracja.serwis.serwis_pobiezny_h
    zajete_w_dniu: dict[date, set] = {}
    przydzielone = 0
    sprowadzone = 0
    bez_maszyny: list[str] = []

    for slot in sorted(rdzen.sloty, key=lambda s: s.data):
        # Symulator nie zużywa statku powietrznego; nieobsadzonych nie ruszamy.
        if slot.typ_dyzuru == TypDyzuru.SYMULATOR_LAW:
            continue
        if not slot.jest_obsadzony():
            continue

        zajete = zajete_w_dniu.setdefault(slot.data, set())
        kandydaci = [
            m for m in rdzen.flota
            if m.klasa == slot.wymagana_klasa
            and _dostepna(m, slot.data)
            and m.id not in zajete
        ]
        if not kandydaci:
            bez_maszyny.append(slot.id)
            continue

        lokalni = [m for m in kandydaci if m.aktualny_hub == slot.baza_id]
        if lokalni:
            wybor = max(lokalni, key=lambda m: _pozycja_w_cyklu(m, prog))
            z_innej = False
        else:
            wybor = max(kandydaci, key=lambda m: _pozycja_w_cyklu(m, prog))
            z_innej = True

        slot.maszyna_id = wybor.id
        slot.maszyna_z_innej_bazy = z_innej
        zajete.add(wybor.id)
        wybor.aktualny_hub = slot.baza_id  # egzemplarz przyleciał do bazy slotu
        przydzielone += 1
        if z_innej:
            sprowadzone += 1

        for pid in (slot.przypisany_pilot_id, slot.drugi_pilot_id, slot.instruktor_id):
            if pid is None:
                continue
            p = rdzen.pilot(pid)
            if p is not None:
                _ostempluj_misje(p, slot, wybor.id)

    return {
        "przydzielone": przydzielone,
        "sprowadzone": sprowadzone,
        "bez_maszyny": bez_maszyny,
    }


def nalot_maszyny(rdzen: Rdzen, maszyna_id: str) -> Optional[dict]:
    """Nalot egzemplarza i odległość do progów. None, gdy brak takiej maszyny.

    Misje dwuosobowe tworzą dwa wpisy (PIC i FO) z tym samym `maszyna_id`. Jedna
    maszyna ma najwyżej jeden dyżur dziennie, więc godziny statku liczymy raz na
    dzień, nie sumując obu wpisów załogi.
    """
    m = rdzen.maszyna(maszyna_id)
    if m is None:
        return None

    po_dacie: dict[date, float] = {}
    for p in rdzen.piloci:
        for mi in p.historia_misji:
            if mi.maszyna_id == maszyna_id:
                po_dacie.setdefault(mi.data, mi.czas_trwania_h)

    z_misji = round(sum(po_dacie.values()), 1)
    razem = round(m.nalot_h + z_misji, 1)
    s = rdzen.konfiguracja.serwis
    return {
        "id": maszyna_id,
        "klasa": m.klasa.value,
        "hub": m.aktualny_hub,
        "nalot_bazowy_h": round(m.nalot_h, 1),
        "nalot_z_misji_h": z_misji,
        "nalot_razem_h": razem,
        "do_pobieznego_h": round(s.serwis_pobiezny_h - (razem % s.serwis_pobiezny_h), 1),
        "do_powaznego_h": round(s.serwis_powazny_h - (razem % s.serwis_powazny_h), 1),
        "do_remontu_h": round(s.remont_h - (razem % s.remont_h), 1),
        "liczba_dyzurow": len(po_dacie),
    }


def kto_latal(piloci, maszyna_id: str) -> list[dict]:
    """Wykaz dyżurów na danym egzemplarzu: data, typ, kto (1 lub 2 pilotów)."""
    rekordy: dict[date, dict] = {}
    for p in piloci:
        for mi in p.historia_misji:
            if mi.maszyna_id != maszyna_id:
                continue
            r = rekordy.setdefault(mi.data, {
                "data": mi.data,
                "typ_dyzuru": mi.typ_dyzuru.value,
                "piloci": [],
            })
            r["piloci"].append(p.id)
    return [rekordy[d] for d in sorted(rekordy)]


def obciazenie_floty(rdzen: Rdzen) -> dict:
    """Obciążenie każdego egzemplarza: liczba dyżurów i godziny z misji.

    Egzemplarze z `liczba_dyzurow == 0` to maszyny nieużyte w tym harmonogramie.
    """
    wynik: dict[str, dict] = {}
    for m in rdzen.flota:
        info = nalot_maszyny(rdzen, m.id)
        wynik[m.id] = {
            "klasa": m.klasa.value,
            "status": m.status.value,
            "hub": m.aktualny_hub,
            "liczba_dyzurow": info["liczba_dyzurow"],
            "godziny_z_misji_h": info["nalot_z_misji_h"],
            "w_serwisie_do": m.w_serwisie_do.isoformat() if m.w_serwisie_do else None,
            "lokalizacja_serwisu": m.lokalizacja_serwisu,
        }
    return wynik
