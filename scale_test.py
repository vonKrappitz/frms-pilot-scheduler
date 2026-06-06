# Copyright 2026 Maciej M. Kasperek ("vonKrappitz")
# SPDX-License-Identifier: Apache-2.0
"""
Test skalowalności grafikowania FRMS (reprodukowalność wyników z powiązanej pracy).

Replikuje jednostkę bazową (30 pilotów, 133 sloty tygodniowe) całkowitym
mnożnikiem k, nadając unikatowe identyfikatory, i mierzy odsetek obsadzonych
slotów oraz czas generowania harmonogramu w skali docelowej. Mnożnik k ≈ 5,5
odwzorowuje sieć docelową (około 182 pilotów i 772 sloty tygodniowe).

Mierzy wyłącznie rdzeń doboru (generuj_harmonogram); kursy, prywatny STOL i
warstwa wymiany nie wchodzą do tego pomiaru.

Uruchomienie:  python3 scale_test.py
"""

import copy
import time
from datetime import date

from frms.data import generuj_pilotow, generuj_sloty
from frms.scheduler import generuj_harmonogram

DZIEN_BAZOWY = date(2026, 6, 1)
MNOZNIKI = [1, 2, 3, 4, 5, 6]  # 6× jednostki bazowej (~180 pilotów, ~798 slotów)


def _replikuj_pilotow(baza, k):
    out = []
    for i in range(k):
        for p in baza:
            q = copy.deepcopy(p)
            q.id = f"{p.id}_{i}"
            out.append(q)
    return out


def _replikuj_sloty(baza, k):
    out = []
    for i in range(k):
        for s in baza:
            t = copy.deepcopy(s)
            t.id = f"{s.id}_{i}"
            t.przypisany_pilot_id = None
            t.drugi_pilot_id = None
            t.instruktor_id = None
            out.append(t)
    return out


def _buduj_do(baza_pilotow, baza_slotow, n_pilotow, n_slotow):
    """Buduje dokładnie n_pilotow i n_slotow przez cykliczne powielanie jednostki
    bazowej z unikatowymi identyfikatorami (do odwzorowania sieci docelowej)."""
    piloci = []
    for i in range(n_pilotow):
        q = copy.deepcopy(baza_pilotow[i % len(baza_pilotow)])
        q.id = f"{q.id}#{i}"
        piloci.append(q)
    sloty = []
    for i in range(n_slotow):
        t = copy.deepcopy(baza_slotow[i % len(baza_slotow)])
        t.id = f"{t.id}#{i}"
        t.przypisany_pilot_id = None
        t.drugi_pilot_id = None
        t.instruktor_id = None
        sloty.append(t)
    return piloci, sloty


def main():
    piloci_baza = generuj_pilotow(DZIEN_BAZOWY)
    sloty_baza = generuj_sloty(DZIEN_BAZOWY, dni=7)
    print(f"Jednostka bazowa: {len(piloci_baza)} pilotów, {len(sloty_baza)} slotów tygodniowych\n")
    print(f"{'k':>2} {'piloci':>7} {'sloty':>6} {'obsadzone':>10} {'obsada':>8} {'czas [ms]':>10}")
    for k in MNOZNIKI:
        piloci = _replikuj_pilotow(piloci_baza, k)
        sloty = _replikuj_sloty(sloty_baza, k)
        t0 = time.perf_counter()
        obsadzone, nieobsadzone = generuj_harmonogram(sloty, piloci)
        dt_ms = (time.perf_counter() - t0) * 1000
        obsada = len(obsadzone) / len(sloty) * 100
        print(f"{k:>2} {len(piloci):>7} {len(sloty):>6} {len(obsadzone):>10} {obsada:>7.1f}% {dt_ms:>10.1f}")

    # Punkt docelowy sieci: 182 pilotów, 772 sloty tygodniowe
    piloci, sloty = _buduj_do(piloci_baza, sloty_baza, 182, 772)
    t0 = time.perf_counter()
    obsadzone, _ = generuj_harmonogram(sloty, piloci)
    dt_ms = (time.perf_counter() - t0) * 1000
    obsada = len(obsadzone) / len(sloty) * 100
    print(f"\nSieć docelowa: {len(piloci)} pilotów, {len(sloty)} slotów tygodniowych — "
          f"obsadzone {len(obsadzone)} ({obsada:.1f}%), czas {dt_ms:.0f} ms")


if __name__ == "__main__":
    main()
