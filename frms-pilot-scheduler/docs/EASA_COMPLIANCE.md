# Zgodność z normami EASA

System FRMS Pilot Scheduler implementuje wymogi następujących aktów prawnych Unii Europejskiej oraz wytycznych Europejskiej Agencji Bezpieczeństwa Lotniczego (EASA):

## Acceptable Means of Compliance — AMC1 ORO.FTL.110

**Tytuł:** Operator responsibilities — Fatigue Risk Management System

**Wymóg:** Operator lotniczy musi wdrożyć system zarządzania ryzykiem zmęczenia załogi (Fatigue Risk Management System, FRMS) jako część Safety Management System.

**Implementacja w aplikacji:**

| Wymóg AMC1 ORO.FTL.110 | Implementacja FRMS Pilot Scheduler |
|---|---|
| Minimum 12 godz. odpoczynku po dyżurze podstawowym | `gotowy_do_dyzuru_24h()` |
| Minimum 48 godz. po dyżurze 24-godzinnym | `godziny_od_ostatniego_dyzuru_24h() >= 48` |
| Maksimum 60 godz. pracy w oknie 7 dni | `przeciazony()` |
| Monitorowanie obciążenia rolling 96h | `obciazenie_96h()` |
| Rejestracja typu dyżuru | `Misja.typ_dyzuru` |

## Guidance Material — GM1 ORO.FTL.120

**Tytuł:** Fatigue Risk Management — Implementation Guidance

**Wymagane elementy systemu informatycznego:**

1. Rejestracja czasu pracy każdej załogi (✅ `historia_misji`)
2. Monitoring obciążenia w trybie ciągłym (✅ `obciazenie_96h`)
3. Alerty progowe (✅ `alerty_przeciazenia`)
4. Możliwość audytu wstecznego (⚠️ wymaga trwałej bazy danych w wersji produkcyjnej)
5. Raporty zgodności okresowe (⚠️ wymaga modułu raportowania)

## EASA Part-FCL (Flight Crew Licensing)

**Regulacja:** Rozporządzenie Komisji (UE) nr 1178/2011 załącznik I.

**Wymóg utrzymania type rating:**
- 12 miesięcy ważności od ostatniego kursu odnawiającego (recurrent training)
- Minimum aktywność operacyjna w oknie 90-dniowym dla pełnej aktualności
- Po 90 dniach bez lotu: wymagany check ride / kurs odnawiający

**Implementacja:**

```python
def jest_aktualny(self, dzien_referencyjny: date) -> bool:
    return (
        self.dni_do_wygasniecia(dzien_referencyjny) > 0
        and self.dni_od_ostatniego_lotu(dzien_referencyjny) <= 90
    )
```

Algorytm doboru pilota odrzuca kandydatów których type rating nie jest aktualny, co zapobiega:

- Wygaśnięciu uprawnień w trakcie służby
- Konieczności płatnego recurrent training (50–80 tys. zł/rok per rating)
- Pełnego type rating renewal (150–250 tys. zł)

## Dyrektywa 2003/88/WE Parlamentu Europejskiego

**Tytuł:** Niektóre aspekty organizacji czasu pracy.

**Wymogi:**
- Maksymalny tygodniowy wymiar czasu pracy 48 godz. (z możliwością derogacji do 60 godz. dla wybranych grup)
- Minimum 11 godz. nieprzerwanego odpoczynku w cyklu 24-godzinnym
- Tygodniowy odpoczynek nieprzerwany minimum 35 godz.

**Implementacja:** Walidator `przeciazony()` weryfikuje próg 60 godz./7 dni.

## Rozporządzenie wykonawcze Komisji (UE) 2023/1020

**Tytuł:** Wspólne standardy operacyjne dla śmigłowcowych usług ratownictwa medycznego (HEMS).

**Termin wdrożenia:** 25 maja 2028 r.

**Relacja z FRMS:** Standard SPA.HEMS.110(e) wymaga rejestrowania czasu lotu w trybie operacyjnym z możliwością audytu przez nadzór państwa członkowskiego (w Polsce: Urząd Lotnictwa Cywilnego). System FRMS jest narzędziem dostarczającym te dane.

## Polskie akty prawne

- **Ustawa z dnia 26 czerwca 1974 r. — Kodeks pracy** (Dz.U. 1974 nr 24 poz. 141 z późn. zm.), art. 129, 132–133. **Wymaga nowelizacji** dla wprowadzenia cyklu dyżurów 24 godz. + 48 godz. odpoczynku.
- **Ustawa z dnia 8 września 2006 r. o Państwowym Ratownictwie Medycznym** (Dz.U. 2006 nr 191 poz. 1410 z późn. zm.). **Wymaga nowelizacji** w zakresie statusu zawodowego Pilota MEDEVAC.
- **Ustawa z dnia 3 lipca 2002 r. — Prawo lotnicze** (Dz.U. 2002 nr 130 poz. 1112 z późn. zm.). **Wymaga nowelizacji** w zakresie regulowanego zawodu państwowego.

## Wzorce zagraniczne

System FRMS Pilot Scheduler jest inspirowany rozwiązaniami stosowanymi operacyjnie przez:

- **Szwajcarska Rega** — system Polaris (wewnętrzny)
- **Norweska Norsk Luftambulanse** — system FleetMonitor
- **Niemiecka ADAC Luftrettung** — system Crew Resource Management

Wszystkie trzy systemy implementują podobne mechanizmy walidacji EASA AMC1 ORO.FTL.110, EASA Part-FCL oraz krajowych przepisów czasu pracy załóg lotniczych.
