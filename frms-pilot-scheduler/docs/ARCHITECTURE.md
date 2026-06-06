# Architecture — FRMS Pilot Scheduler

Identifiers (class, function and field names) are kept in Polish to match the
names referenced in the associated study. The prose is in English.

## Application layers

```
┌─────────────────────────────────────────────────────────────┐
│                        CLI interface                        │
│              (frms/cli.py — console commands)               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                       Business layer                        │
│   ┌──────────────────────┐  ┌──────────────────────────┐    │
│   │  scheduler.py        │  │  validator.py            │    │
│   │  - dobierz_pilota    │  │  - alerty_type_rating    │    │
│   │  - generuj_harm.     │  │  - alerty_przeciazenia   │    │
│   │  - score_pilota      │  │  - statystyki_systemu    │    │
│   └──────────────────────┘  └──────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                        Model layer                          │
│              (frms/models.py — dataclasses)                 │
│   Pilot, TypeRating, SlotDyzurowy, Baza, Misja              │
│   Enums: Kategoria, KlasaMaszyny, TypDyzuru, SkalaNACA       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                         Data layer                          │
│   (frms/data.py — mock data: 30 pilots, 5 bases, slots)     │
│   Production target: PostgreSQL + SQLAlchemy ORM            │
└─────────────────────────────────────────────────────────────┘
```

## Main classes

### Pilot

Represents a single MEDEVAC pilot.

**Fields:**
- `id`, `imie`, `nazwisko`, `kategoria` (A/B/C/D)
- `baza_macierzysta` — ICAO code of the home operating base
- `type_ratings` — list of EASA Part-FCL ratings per aircraft class
- `historia_misji` — missions flown in the last 30 days

**Operational methods:**
- `ma_type_rating(klasa, dzien)` — whether the pilot holds a current rating
- `obciazenie_96h(dzien)` — cumulative flight hours over the last 96 hours
- `godziny_od_ostatniego_dyzuru_24h(dzien)` — rest since the last 24-hour duty
- `gotowy_do_dyzuru_24h(dzien)` — readiness check (48-hour rule)
- `przeciazony(dzien)` — whether the 60-hour limit over 7 days is exceeded

### SlotDyzurowy

A single duty slot to be filled at a base.

**Fields:**
- `id`, `baza_id`, `data`, `typ_dyzuru` (24H / 6H / on-call)
- `wymagana_klasa` — required aircraft class
- `wymagana_kategoria_min` — minimum category A/B/C/D
- `przypisany_pilot_id` — set by the scheduler

## Selection algorithm

### Step 1: candidate filtering

`kandydat_kwalifikujacy_sie(pilot, slot)` returns `(bool, reason)`:

```
1. Is the pilot's category >= wymagana_kategoria_min ?
   → NO: reject, reason "category below minimum"

2. Does the pilot hold a current type rating for slot.wymagana_klasa ?
   → NO: reject, reason "no type rating"

3. If slot.typ_dyzuru == DYZUR_24H, is gotowy_do_dyzuru_24h true ?
   → NO: reject, reason "insufficient rest"

4. Is pilot.przeciazony(slot.data) true ?
   → YES: reject, reason "exceeds 60h / 7 days"
```

### Step 2: candidate scoring

`score_pilota(pilot, slot)` returns a float (lower is better):

```
score = obciazenie_96h
      + 0.5 * hierarchia_kategorii    (penalty for "wasting" a higher category)
      - 2.0 * premia_type_rating      (priority if a rating is about to expire)
```

### Step 3: choice

```python
najlepszy = min(kwalifikujacy, key=score_pilota)
```

## EASA alignment

Full mapping in `docs/EASA_COMPLIANCE.md`. The implementation checks against:

- **EASA AMC1 ORO.FTL.110** — minimum rest after a 24-hour duty
- **EASA Part-FCL** — 90-day type-rating recency window
- **Directive 2003/88/EC** — 60-hour working-time ceiling over 7 days
- **GM1 ORO.FTL.120** — FRMS implementation guidance

## Production extensions

Items required for a production deployment, none of which are part of this
proof of concept:

### Persistent storage

```
SQLite / PostgreSQL + SQLAlchemy ORM
- schema migrations (Alembic)
- backup + replication
- indexes on: pilot_id, baza_id, data
```

### External integration

```
- national air-rescue dispatch API (real-time mission state)
- national civil aviation authority API (type-rating registry, validation)
- Eurocontrol API (aircraft status, NOTAM)
- EASA SAFA / SACA reporting
```

### User interface

```
Frontend: React or Vue.js
- dispatcher dashboard (real-time)
- pilot mobile app (duty status, alerts)
- authority panel (type-rating management)
```

### Security and data protection

```
- authorisation: OAuth2 / SAML
- encryption: AES-256 for sensitive data
- audit log: every schedule change
- data retention: per applicable EMS legislation and GDPR
```
