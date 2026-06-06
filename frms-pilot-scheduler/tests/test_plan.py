# Copyright 2026 Maciej M. Kasperek ("vonKrappitz")
# SPDX-License-Identifier: Apache-2.0
"""Testy warstwy planu operacyjnego (frms.plan)."""

from datetime import date, timedelta

from frms.data import generuj_pilotow
from frms.plan import plan_dni, dzien_planu, nastepny_dzien, poprzedni_dzien, HORYZONT_DNI

START = date(2026, 6, 2)


def test_horyzont_15_dni():
    piloci = generuj_pilotow(START)
    plan = plan_dni(piloci, START, dni=HORYZONT_DNI)
    assert HORYZONT_DNI == 15
    assert len(plan) == 15
    assert plan[0].data == START
    assert plan[-1].data == START + timedelta(days=14)
    # dni rosnąco i bez dziur
    daty = [d.data for d in plan]
    assert daty == sorted(daty)
    assert all((daty[i + 1] - daty[i]).days == 1 for i in range(len(daty) - 1))


def test_kazdy_dzien_ma_sloty():
    piloci = generuj_pilotow(START)
    plan = plan_dni(piloci, START, dni=HORYZONT_DNI)
    assert all(len(d.sloty) > 0 for d in plan)


def test_nawigacja_dzien_po_dniu():
    piloci = generuj_pilotow(START)
    plan = plan_dni(piloci, START, dni=HORYZONT_DNI)
    assert nastepny_dzien(plan, START) == START + timedelta(days=1)
    assert poprzedni_dzien(plan, START) is None
    assert nastepny_dzien(plan, plan[-1].data) is None
    assert poprzedni_dzien(plan, START + timedelta(days=1)) == START
    assert dzien_planu(plan, START + timedelta(days=3)).data == START + timedelta(days=3)
    assert dzien_planu(plan, START + timedelta(days=99)) is None
