# Copyright 2026 Maciej M. Kasperek ("vonKrappitz")
# SPDX-License-Identifier: Apache-2.0
"""Testy sieci reformy do mapy sektorów (frms.siec)."""

from frms.siec import siec_json, SEKTORY, LICZBA_LOKALIZACJI_SIEC


def test_siedem_sektorow():
    assert len(SEKTORY) == 7
    assert set(SEKTORY) == {"Warszawa", "Kraków", "Wrocław", "Gdańsk", "Lublin", "Poznań", "Olsztyn"}


def test_dwadziescia_osiem_lokalizacji():
    d = siec_json()
    assert d["liczba_nazwane"] == 24          # 7 CRL + 15 CT + CSI + CT-S
    assert d["liczba_bw_nielokalizowane"] == 4
    assert d["liczba_lokalizacji"] == 28
    assert LICZBA_LOKALIZACJI_SIEC == 28


def test_struktura_typow_i_sektorow():
    d = siec_json()
    b = d["bazy"]
    from collections import Counter
    typy = Counter(x["typ"] for x in b)
    assert typy["CRL"] == 7 and typy["CT"] == 15
    # każda baza sektorowa wskazuje istniejący sektor (poza CSI-LRM, który jest poza siatką)
    for x in b:
        if x["typ"] != "CSI-LRM":
            assert x["sektor"] in SEKTORY
    # każdy sektor ma dokładnie jedną głowę CRL
    crl = [x for x in b if x["typ"] == "CRL"]
    assert {x["sektor"] for x in crl} == set(SEKTORY)
