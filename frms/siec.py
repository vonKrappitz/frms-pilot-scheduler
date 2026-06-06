# Copyright 2026 Maciej M. Kasperek ("vonKrappitz")
# SPDX-License-Identifier: Apache-2.0
"""
Sieć ratownictwa lotniczego po reformie 2028 (do mapy sektorów).

Dane z cyklu artykułów SFT, Część I (architektura sieci) oraz Część II
(przypisanie baz HEMS Primary do sektorów, Załącznik 1 Tabela 1). Struktura
sektorowa: siedem Centrów Regionalnych (CRL) jako głowy sektorów oraz przypisane
im Centra Transferowe (CT), uzupełnione o Centrum Szkoleniowo-Integracyjne
(CSI-LRM) i bazę sezonową (CT-S).

Cztery Bazy Wsparcia (BW) wymienia Część I bez nazw ani lokalizacji, więc tu ich
nie ma: sieć liczy 28 lokalizacji, z czego 24 nazwane (7 CRL + 15 CT + CSI-LRM +
CT-S). Współrzędne są przybliżone, na potrzeby schematu.

Dane wyłącznie do warstwy mapowej; rdzeń grafikowania ich nie używa.
"""

# (id, nazwa, typ, sektor, lat, lon) — sektor = głowa (CRL) sektora; dla CRL własna nazwa.
SIEC_REFORMA = [
    # Centra Regionalne (CRL) — głowy siedmiu sektorów, całodobowe
    ("Warszawa", "Warszawa", "CRL", "Warszawa", 52.23, 21.00),
    ("Kraków", "Kraków", "CRL", "Kraków", 50.06, 19.94),
    ("Wrocław", "Wrocław", "CRL", "Wrocław", 51.11, 17.03),
    ("Gdańsk", "Gdańsk", "CRL", "Gdańsk", 54.35, 18.65),
    ("Lublin", "Lublin", "CRL", "Lublin", 51.25, 22.57),
    ("Poznań", "Poznań", "CRL", "Poznań", 52.41, 16.93),
    ("Olsztyn", "Olsztyn", "CRL", "Olsztyn", 53.78, 20.49),
    # Sektor krakowski
    ("Gliwice-Trynek", "Gliwice-Trynek", "CT", "Kraków", 50.28, 18.67),
    ("Kielce-Masłów", "Kielce-Masłów (hybrydowa)", "CT", "Kraków", 50.91, 20.73),
    ("Sanok-Trepcza", "Sanok-Trepcza", "CT", "Kraków", 49.55, 22.20),
    ("Rzeszów-Jasionka", "Rzeszów-Jasionka (LST)", "CT", "Kraków", 50.11, 22.02),
    # Sektor warszawski
    ("Łask", "Łask", "CT", "Warszawa", 51.55, 19.18),
    ("Biała Podlaska", "Biała Podlaska (dwufunkcyjna)", "CT", "Warszawa", 52.03, 23.13),
    # Sektor wrocławski
    ("Lubomierz", "Lubomierz", "CT", "Wrocław", 51.00, 15.55),
    # Sektor gdański
    ("Bytów", "Bytów", "CT", "Gdańsk", 54.17, 17.49),
    # Sektor lubelski
    ("Zamość-Mokre", "Zamość-Mokre", "CT", "Lublin", 50.72, 23.20),
    # Sektor poznański
    ("Toruń-Bielany", "Toruń-Bielany", "CT", "Poznań", 53.04, 18.55),
    ("Stargard", "Stargard", "CT", "Poznań", 53.34, 15.05),
    ("Zielona Góra-Babimost", "Zielona Góra-Babimost", "CT", "Poznań", 52.14, 15.83),
    ("Mirosławiec", "Mirosławiec", "CT", "Poznań", 53.35, 16.09),
    # Sektor olsztyński
    ("Białystok-Krywlany", "Białystok-Krywlany", "CT", "Olsztyn", 53.10, 23.10),
    ("Ełk-Makosieje", "Ełk-Makosieje", "CT", "Olsztyn", 53.83, 22.36),
    # Ośrodki o funkcjach szczególnych (poza siatką sektorową)
    ("Drawsko Pomorskie", "Drawsko Pomorskie (CSI-LRM)", "CSI-LRM", None, 53.52, 15.81),
    ("Krępa Słupska", "Krępa Słupska (sezonowa)", "CT-S", "Gdańsk", 54.45, 17.02),
]

SEKTORY = ["Warszawa", "Kraków", "Wrocław", "Gdańsk", "Lublin", "Poznań", "Olsztyn"]

# Cztery Bazy Wsparcia (BW) bez nazw i lokalizacji w artykułach.
LICZBA_BW_NIELOKALIZOWANE = 4
LICZBA_LOKALIZACJI_SIEC = len(SIEC_REFORMA) + LICZBA_BW_NIELOKALIZOWANE  # 28


def siec_json() -> dict:
    bazy = [{"id": b[0], "nazwa": b[1], "typ": b[2], "sektor": b[3],
             "lat": b[4], "lon": b[5]} for b in SIEC_REFORMA]
    return {
        "bazy": bazy,
        "sektory": SEKTORY,
        "liczba_nazwane": len(bazy),
        "liczba_bw_nielokalizowane": LICZBA_BW_NIELOKALIZOWANE,
        "liczba_lokalizacji": LICZBA_LOKALIZACJI_SIEC,
    }
