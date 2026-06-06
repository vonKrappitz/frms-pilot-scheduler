# Architektura FRMS Pilot Scheduler

## Warstwy aplikacji

```
┌─────────────────────────────────────────────────────────────┐
│                      Interfejs CLI                          │
│            (frms/cli.py — komendy konsoli)                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   Warstwa biznesowa                         │
│   ┌──────────────────────┐  ┌──────────────────────────┐    │
│   │  scheduler.py        │  │  validator.py            │    │
│   │  - dobierz_pilota    │  │  - alerty_type_rating    │    │
│   │  - generuj_harm.     │  │  - alerty_przeciazenia   │    │
│   │  - score_pilota      │  │  - statystyki_systemu    │    │
│   └──────────────────────┘  └──────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   Warstwa modeli                            │
│              (frms/models.py — dataclasses)                 │
│   Pilot, TypeRating, SlotDyzurowy, Baza, Misja              │
│   Enumy: Kategoria, KlasaMaszyny, TypDyzuru, SkalaNACA      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   Warstwa danych                            │
│  (frms/data.py — mock data 30 pilotów + 5 baz + sloty)      │
│  W wersji produkcyjnej: PostgreSQL + SQLAlchemy ORM         │
└─────────────────────────────────────────────────────────────┘
```

## Główne klasy

### Pilot

Reprezentuje pojedynczego Pilota MEDEVAC w Korpusie KPRL.

**Pola:**
- `id`, `imie`, `nazwisko`, `kategoria` (A/B/C/D)
- `baza_macierzysta` — kod ICAO bazy operacyjnej
- `type_ratings` — lista uprawnień EASA Part-FCL na klasy maszyn
- `historia_misji` — lista misji wykonanych w ostatnich 30 dniach

**Metody operacyjne:**
- `ma_type_rating(klasa, dzien)` — czy pilot ma aktualny rating
- `obciazenie_96h(dzien)` — kumulacyjne godziny lotu w 96h
- `godziny_od_ostatniego_dyzuru_24h(dzien)` — sprawdza odpoczynek
- `gotowy_do_dyzuru_24h(dzien)` — EASA AMC1 wymaga 48h
- `przeciazony(dzien)` — czy przekroczył 60h w oknie 7 dni

### SlotDyzurowy

Pojedynczy slot do obsadzenia w bazie.

**Pola:**
- `id`, `baza_id`, `data`, `typ_dyzuru` (24H / 6H / on-call)
- `wymagana_klasa` — klasa maszyny
- `wymagana_kategoria_min` — minimum A/B/C/D
- `przypisany_pilot_id` — uzupełniany przez scheduler

## Algorytm doboru

### Krok 1: Filtrowanie kandydatów

`kandydat_kwalifikujacy_sie(pilot, slot)` zwraca `(bool, powod)`:

```python
1. Czy kategoria pilota >= wymagana_kategoria_min ?
   → NIE: odrzuć z powodem "kategoria niedostateczna"

2. Czy pilot ma aktualny type rating na slot.wymagana_klasa ?
   → NIE: odrzuć z powodem "brak type rating"

3. Czy slot.typ_dyzuru == DYZUR_24H i pilot.gotowy_do_dyzuru_24h ?
   → NIE: odrzuć z powodem "niedostateczny odpoczynek"

4. Czy pilot.przeciazony(slot.data) ?
   → TAK: odrzuć z powodem "przekroczenie 60h/7d"
```

### Krok 2: Ocena kandydatów

`score_pilota(pilot, slot)` zwraca liczbę zmiennoprzecinkową (niższa = lepiej):

```
score = obciazenie_96h
      + 0.5 * hierarchia_kategorii    (kara za "marnowanie" wyższej kategorii)
      - 2.0 * premia_type_rating       (jeśli rating wygasa = priorytet)
```

### Krok 3: Wybór

```python
najlepszy = min(kwalifikujacy, key=score_pilota)
```

## Zgodność z normami EASA

Pełna dokumentacja w `docs/EASA_COMPLIANCE.md`.

Implementacja sprawdza zgodność z:

- **EASA AMC1 ORO.FTL.110** — wymóg minimum 48h odpoczynku po dyżurze 24h
- **EASA Part-FCL** — okno 90-dniowe utrzymania type rating
- **EU 2003/88/WE** — limit 60h pracy w oknie 7 dni
- **GM1 ORO.FTL.120** — wytyczne implementacyjne FRMS

## Rozszerzenia produkcyjne

Lista rozszerzeń wymaganych do wdrożenia produkcyjnego:

### Trwała baza danych

```
SQLite/PostgreSQL + SQLAlchemy ORM
- migracje schematu (Alembic)
- backup + replikacja
- indeksy na: pilot_id, baza_id, data
```

### Integracja zewnętrzna

```
- API dyspozytorni krajowej LPR (real-time stan misji)
- API ULC (rejestr type rating, walidacja uprawnień)
- API Eurocontrol (status statków powietrznych, NOTAM)
- System raportowania EASA SAFA/SACA
```

### Interfejs użytkownika

```
Frontend: React lub Vue.js
- Dashboard dyspozytora (real-time)
- Aplikacja mobilna dla pilotów (status dyżuru, alerty)
- Panel administracyjny ULC (zarządzanie type rating)
```

### Bezpieczeństwo i zgodność RODO

```
- Autoryzacja: OAuth2 / SAML
- Szyfrowanie: AES-256 dla danych wrażliwych
- Audyt log: każda zmiana harmonogramu
- Retencja danych: zgodnie z ustawą o PRM
```
