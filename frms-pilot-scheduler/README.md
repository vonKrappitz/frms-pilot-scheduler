# FRMS Pilot Scheduler

**Fatigue Risk Management System** dla **Korpusu Pilotów Ratownictwa Lotniczego (KPRL)** — prototyp systemu informatycznego do harmonogramowania dyżurów Pilotów MEDEVAC w polskim Lotniczym Pogotowiu Ratunkowym po reformie.

## Kontekst

Repozytorium stanowi proof-of-concept systemu opisanego w artykule naukowym:

> Kasperek M., *Strukturalne deficyty polskiego ratownictwa lotniczego. Propozycja reformy*, „Wiedza Obronna" 2026.

Praca proponuje reformę polskiego LPR opartą na czteroklasowej flocie (MEDEVAC ciężki + HEMS średni + LST lekki + STOL samolot) z 151–182 Pilotami MEDEVAC zorganizowanymi w Korpus KPRL pod nadzorem Urzędu Lotnictwa Cywilnego. Cykl dyżurów 24 godz. + 48 godz. odpoczynku w połączeniu z rotacją między czterema klasami maszyn dla utrzymania type rating EASA Part-FCL wymaga **systemu informatycznego klasy FRMS** zgodnego z normami **EASA AMC1 ORO.FTL.110** oraz **GM1 ORO.FTL.120**.

Niniejsza implementacja demonstruje architekturę takiego systemu z trzema zmiennymi kontrolnymi:

1. **Aktualność type rating** na każdej klasie maszyny (okno 90-dniowe EASA Part-FCL)
2. **Kumulacyjne obciążenie operacyjne** z poprzednich 96 godzin (liczba misji, długość lotów, NACA)
3. **Pozycja w 10-dniowym cyklu rotacyjnym** anty-rutynowym (MEDEVAC → odpoczynek → LST → HEMS → odpoczynek → STOL → odpoczynek → LST)

## Wzorzec implementacyjny

Systemy zarządzania zasobami kadrowymi tej klasy są dziś wykorzystywane operacyjnie przez:

- **Szwajcarska Rega** (Schweizerische Rettungsflugwacht)
- **Norweska Norsk Luftambulanse** (NLA)
- **Niemiecka ADAC Luftrettung**

## Instalacja

Wymaga Python 3.10 lub nowszego.

```bash
git clone https://github.com/vonKrappitz/frms-pilot-scheduler.git
cd frms-pilot-scheduler
pip install -r requirements.txt
```

## Użycie

### 1. Generowanie tygodniowego harmonogramu

```bash
python -m frms.cli generuj-harmonogram
```

Wynik: lista 84 slotów dyżurowych (7 dni × 12 slotów dziennie) z przypisanymi pilotami.

### 2. Alerty operacyjne

```bash
python -m frms.cli alerty
```

Wyświetla:
- Type rating wygasające w 30 dniach (priorytet WYSOKI)
- Type rating po 60 dniach bez lotu (priorytet ŚREDNI)
- Pilotów przekraczających 60 godzin pracy w oknie 7 dni

### 3. Statystyki systemu

```bash
python -m frms.cli statystyki
```

### 4. Karta pilota

```bash
python -m frms.cli pilot P001
```

## Struktura projektu

```
frms-pilot-scheduler/
├── frms/
│   ├── models.py      # Pilot, TypeRating, SlotDyzurowy, Baza, Misja
│   ├── data.py        # 30 testowych pilotów + 5 baz + sloty
│   ├── scheduler.py   # Algorytm doboru pilota do slotu
│   ├── validator.py   # Walidator EASA + generator alertów
│   └── cli.py         # Interfejs konsoli
├── tests/
│   └── test_scheduler.py
├── docs/
│   ├── ARCHITECTURE.md
│   └── EASA_COMPLIANCE.md
├── examples/
│   └── (przykładowe wyniki)
├── requirements.txt
└── README.md
```

## Algorytm doboru pilota

Dla każdego slotu dyżurowego algorytm:

1. **Filtruje kandydatów** — odrzuca pilotów którzy:
   - nie mają wymaganej kategorii kompetencyjnej (A–D)
   - nie mają aktualnego type rating na wymaganą klasę maszyny
   - nie odpoczywali 48 godz. po poprzednim dyżurze 24-godzinnym (EASA AMC1)
   - przekroczyli 60 godzin pracy w oknie 7 dni
2. **Ocenia pozostałych** według funkcji wieloskładnikowej:
   - niskie obciążenie 96-godzinne = lepiej
   - niższa kategoria = lepiej (oszczędność kat. D na sloty wymagające)
   - bliski koniec ważności type rating = priorytet (potrzeba aktywności)
3. **Wybiera najlepszego** kandydata.

## Testy

```bash
pytest tests/ -v
```

## Status projektu

Prototyp ma charakter **proof-of-concept** ilustrujący architekturę informatyczną wymaganą do operacjonalizacji reformy LPR. **Produkcyjne wdrożenie** w Korpusie KPRL wymagałoby:

- Migracji do trwałej bazy danych (PostgreSQL/SQLite z SQLAlchemy)
- Integracji z systemem dyspozytorni krajowej LPR
- Integracji z bazą danych Urzędu Lotnictwa Cywilnego (rejestr type rating)
- Interfejsu webowego (React/Vue) dla dyspozytorów oraz pilotów
- Modułu raportowania zgodnego ze standardami EASA SAFA/SACA
- Zabezpieczeń RODO oraz audyt log

## Licencja

Copyright 2026 Maciej M. Kasperek ("vonKrappitz").
Licencja Apache 2.0 — patrz pliki `LICENSE` (pełna treść) i `NOTICE` (nota autorska). Pliki źródłowe noszą nagłówek `SPDX-License-Identifier: Apache-2.0`.

## Autor

**Maciej M. Kasperek** ("vonKrappitz"), niezależny analityk, Opole.
ORCID: 0009-0008-7419-0851 · GitHub: [vonKrappitz](https://github.com/vonKrappitz)

## Cytowanie

Przy wykorzystaniu kodu prosimy o cytowanie pracy źródłowej:

```
Kasperek M., Strukturalne deficyty polskiego ratownictwa lotniczego.
Propozycja reformy, "Wiedza Obronna" 2026.
```
