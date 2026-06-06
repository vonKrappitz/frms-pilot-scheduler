# FRMS — projekt rozbudowy (zamrożenie robocze)

Dokument zbiera wszystkie wymagania ustalone w trakcie pracy i opisuje, jak je
wdrożyć po powrocie do aplikacji. Apka jest zamrożona w stanie działającym
(walidacja: 12/12 testów). Niniejszy plik jest mapą drogową — nic w nim nie jest
jeszcze zaimplementowane poza częścią oznaczoną jako gotowa.

---

## 0. Zasada nadrzędna — architektura modułowa

Całość budujemy wokół **rdzenia** (jedno źródło prawdy o stanie: piloci, maszyny,
sloty, konfiguracja) oraz **modułów podpinanych przez jawne interfejsy**. Moduł
nie sięga do wnętrza innego modułu — czyta i zapisuje stan przez rdzeń, dzięki
czemu można go dołączyć i odłączyć bez przebudowy reszty. To jest sens „łatwo
podpiąć moduł".

Rdzeń (gotowy w v1.1): modele danych oraz logika doboru i harmonogramu.

Moduły, każdy jako osobny pakiet z własnym kontraktem do rdzenia:
- `scheduler` — dobór załóg i maszyn, rotacja, currency (częściowo gotowy),
- `serwis` — śledzenie przeglądów i wezwania techniczne (§12),
- `centralny` — mapa sytuacyjna i podgląd operacyjny (§13),
- `telemetria` — adapter danych z maszyn: GPS, paliwo, czas misji (§13.1).

**Wzorzec: porty i adaptery.** Rdzeń definiuje interfejs (port), moduł go
implementuje (adapter). Telemetria w prototypie to adapter-zaślepka z danymi
symulowanymi; podmiana na realne źródło GPS wymienia wyłącznie adapter, nie
rusza rdzenia ani innych modułów. Każdy moduł deklaruje, co czyta i co zapisuje
— bez ukrytych zależności między modułami.

---

## 1. Stan zamrożony — co już działa (v1.1)

Zaimplementowane, przetestowane, w repozytorium:

- **Flota krajowa, 51 egzemplarzy** w jednej puli, oznaczenia litera klasy + numer:
  HEMS H1–H31, LST L1–L13, MEDEVAC X1–X4, STOL S1–S3. Podział wprost z bilansu
  części II: 44 operacyjne, 5 rezerwa krajowa, 2 żelazna rezerwa (EC135).
- **Status egzemplarza**: operacyjna / rezerwa krajowa / żelazna rezerwa (ta
  ostatnia zakonserwowana, poza obsadą).
- **Siedem hubów (CRL)**: Warszawa, Kraków, Wrocław, Gdańsk, Lublin, Poznań,
  Olsztyn — z domyślnym przydziałem maszyn (round-robin) i sektorami.
- **Konfiguracja** (`Konfiguracja`, `KonfiguracjaSerwisu`): trzy progi serwisu
  (pobieżny 100 h / poważny 600 h / remont 3000 h) oraz wymagany nalot
  miesięczny per klasa — wartości domyślne, w pełni zmienialne.
- **Resurs maszyny** (`nalot_h`) i **status serwisowy** (ile do każdego przeglądu).
- **Misja** ma już pola `maszyna_id` i `drugi_pilot_id` — gotowe pod rejestr.
- **Reguły kadrowe**: MEDEVAC tylko C+C lub B+D; kategoria A lata wyłącznie VFR
  i w dzień (pole `nocny_lub_ifr`); kategoria B lata LST + STOL + HEMS.
- **Symulator**: recovery po 21/45 dniach = 1 dzień × 6 h; recurrent kwartalny
  = 2 dni × 6 h z trudnymi elementami.

---

## 2. Model danych — rozszerzenia do dodania

### 2.1. `Pilot` — nowe pola
| Pole | Typ | Opis |
|---|---|---|
| `hub` | `str` | aktualny przydział do CRL (dziś jest `baza_macierzysta` — ujednolicić) |
| `dni_wolne` | `list[tuple[date, date]]` | twarde bloki wolnego (np. 4 dni pod rząd) |
| `kursy` | `dict[Kurs, bool]` | ukończenie kursów (patrz §7.2) |
| `nalot_logbook_h` | `dict[KlasaMaszyny, float]` | nalot dotychczasowy (z logbooka) per klasa |
| `historia_szkolen` | `list[Szkolenie]` | odbyte loty szkoleniowe i sesje |
| `egzaminy_zdane` | `dict[Kategoria, date]` | zdane egzaminy wewnętrzne na awans |

Nalot całkowity per klasa = `nalot_logbook_h[klasa]` + suma godzin z `historia_misji`
dla tej klasy. Nalot całkowity łączny = suma po wszystkich klasach.

### 2.2. `Maszyna` — nowe pola
| Pole | Typ | Opis |
|---|---|---|
| `w_serwisie_do` | `Optional[date]` | jeśli w przeglądzie — data powrotu |
| `lokalizacja_serwisu` | `Optional[str]` | hub (pobieżny) lub „EPLB" (poważny/remont) |
| `historia_serwisow` | `list[Serwis]` | log przeglądów: typ, data, miejsce |

Nalot maszyny i wykaz „kto na niej latał" liczone z `Misja.maszyna_id` (rejestr).

### 2.3. Nowe modele
- `Kurs(Enum)`: VFR_DZIEN, LOTY_NOCNE, IFR, NVIS, WYCIAGARKA, ECMO, GORSKI_TOPR.
- `Szkolenie(dataclass)`: data, klasa, instruktor_id, czy_zaliczony.
- `WymogiAwansu(dataclass)`: dla każdej pary kategorii (A→B, B→C, C→D) — minimalny
  nalot per klasa, wymagane kursy, wymóg zdanego egzaminu wewnętrznego.
- `Konfiguracja` — dodać: `limit_lotow_szkoleniowych_na_7dni = 2`,
  mapowanie poziom serwisu → miejsce (pobieżny+małe naprawy = hub; poważny+remont = Lublin).

---

## 3. Dobór maszyny i rejestr per egzemplarz

**Przypisanie maszyny do dyżuru** (rozszerzenie `generuj_harmonogram`):
- Po dobraniu pilota(ów) do slotu dobierz egzemplarz danej klasy z huba slotu.
- **Reguła separacji serwisowej**: wybieraj maszynę o **najwyższym** nalocie
  poniżej progu pobieżnego — dociążasz najbliższą przeglądowi, resztę trzymasz
  na rozłożonych poziomach, więc przeglądy nie wpadają razem.
- Maszyna w serwisie (`w_serwisie_do > dzień`) jest pomijana.
- Zapisz `Misja.maszyna_id` oraz `drugi_pilot_id` (dla załóg dwuosobowych).

**Rejestr per maszyna** (nowe funkcje raportujące):
- `nalot_maszyny(m)` — suma godzin z misji + bieżący `nalot_h`.
- `kto_latal(m)` — lista pilotów z datami i współzałogą (z `maszyna_id` + `drugi_pilot_id`).
- `obciazenie_floty()` — nalot i status serwisowy każdego egzemplarza.

---

## 4. Liczniki i raporty

- **Miesięczne** (kalendarzowo), per pilot: nalot łączny, nalot per klasa osobno,
  godziny symulatora. Funkcja `nalot_miesiac(pilot, rok, miesiac)`.
- **Całkowite**, per pilot: nalot łączny (logbook + misje) oraz per klasa.
- **Per maszyna**: nalot bieżący, do każdego przeglądu, log lotów.
- Eksport tych liczników do JSON web demo (rozszerzyć `export_json.py`).

---

## 5. Szkolenia, awanse, egzaminy

### 5.1. Skierowanie na szkolenie na klasie (ręczne)
- Operator zaznacza: „pilot P, szkolenie na klasie K".
- System szuka slotu, w którym P może lecieć jako szkolony z instruktorem D na
  pokładzie (np. A → HEMS z D). Wzorzec: istniejąca `dobierz_pare_treningowa`.
- **Limit twardy: lot szkoleniowy nie częściej niż 2 razy na 7 dni** dla pilota.
  Sprawdzać `historia_szkolen` w oknie 7 dni przed przydziałem.

### 5.2. Awans kategorii (A→B→C→D)
Warunki awansu sprawdzane łącznie (`WymogiAwansu`):
1. nalot per wymagana klasa ≥ próg,
2. komplet wymaganych kursów ukończony,
3. zdany egzamin wewnętrzny (wpis w `egzaminy_zdane`).
Dopiero gdy wszystkie spełnione — okno pozwala **zatwierdzić awans** (podniesienie
`kategoria`). System nie awansuje automatycznie — decyzję podejmuje operator.

### 5.3. Zatwierdzanie szkoleń
Lot/sesja szkoleniowa po wykonaniu czeka na zatwierdzenie (`czy_zaliczony`).
Zatwierdzenie odblokowuje zaliczenie do wymogów awansu.

---

## 6. Model serwisowy — huby kontra Lublin

| Poziom | Gdzie | Postój | Próg (domyślny) |
|---|---|---|---|
| Pobieżny + małe naprawy | każdy hub (CRL) | 1 dzień | co 100 h |
| Poważny | **tylko Lublin (EPLB)** | 3 dni | co 600 h |
| Remont główny | **tylko Lublin (EPLB)** | 30 dni | co 3000 h |

Lublin to krajowy ośrodek ciężkich przeglądów i remontów wszystkich maszyn
(sąsiedztwo Świdnika). Gdy maszyna osiąga próg poważny/remont — leci do EPLB,
`lokalizacja_serwisu = "EPLB"`, wyłączona z obsady do `w_serwisie_do`. Pobieżny
przegląd wykonuje hub macierzysty bez przemieszczania maszyny.

---

## 7. Życzenia i kursy

### 7.1. Życzenia (dni wolne)
Twarde bloki dat (`dni_wolne`). W `kandydat_kwalifikujacy_sie`: jeśli dzień slotu
mieści się w bloku wolnego pilota — odrzuć. Okno pozwala dodać/usunąć blok.

### 7.2. Kursy
Rejestr `kursy: dict[Kurs, bool]`. Wykaz w UI: które kursy pilot ma, których nie.
Powiązanie: kurs LOTY_NOCNE / IFR warunkuje obsadę slotów `nocny_lub_ifr` (dziś
rozstrzyga sama kategoria — docelowo dodatkowo kurs).

---

## 8. Okna interfejsu (web demo)

| Okno | Funkcja |
|---|---|
| Konfiguracja serwisu | edycja 3 progów (pobieżny/poważny/remont), godziny i dni postoju |
| Konfiguracja nalotu | edycja wymaganego nalotu per klasa — podnoszenie i obniżanie |
| Przydział maszyn → huby | przeniesienie egzemplarza do innego huba |
| Przenoszenie pilotów → huby | przeniesienie pilota do innego huba |
| Dodaj / usuń pilota | dodanie; usunięcie po potwierdzeniu z **timeoutem 10 s** |
| Awanse i szkolenia | podgląd spełnienia wymogów, zatwierdzenie szkolenia, awans kategorii |
| Skierowanie na szkolenie | wybór pilota + klasy → system szuka lotu z instruktorem D (limit 2/7 dni) |
| Mapa metra | przegląd sektorów + dyżury dnia (patrz §9) |
| Rejestr maszyn | nalot, status serwisu, lokalizacja, log lotów każdego egzemplarza |
| Liczniki pilota | nalot miesięczny i całkowity, per klasa i symulator, kursy |

Konfiguracja przelicza statusy na żywo w JS z danych eksportowanych przez backend;
pełny re-scheduling pozostaje po stronie Pythona (regeneracja JSON).

---

## 9. Mapa metra sektorów

- Siedem sektorów jako linie (CRL = stacja węzłowa, CT = stacje pośrednie),
  stylizacja schematyczna jak mapa metra.
- Przełącznik sektora.
- Panel „dziś dyżuruje": dla wybranego sektora lista — pilot / baza / maszyna.
- Dane z harmonogramu dnia + przydziału maszyn do hubów.
- Sektory (rev1): Warszawa (Łask, Biała Podlaska), Kraków (Sanok, Gliwice,
  Kielce, Rzeszów), Poznań (Mirosławiec, Toruń, Zielona Góra, Stargard),
  Olsztyn (Białystok, Ełk), Gdańsk (Bytów, Krępa Słupska sez.), Wrocław
  (Lubomierz), Lublin (Zamość).

---

## 10. Reguły szczegółowe (zebrane)

- Lot szkoleniowy: ≤ 2 razy na 7 dni na pilota.
- Usunięcie pilota: potwierdzenie z timeoutem 10 s (zabezpieczenie).
- Separacja serwisowa: dobór maszyny dociąża najbliższą progowi.
- Poważny przegląd i remont: wyłącznie Lublin; pobieżny: hub macierzysty.
- Symulator: 1 egzemplarz na klasę w LAW Dęblin, najwyżej 1 pilot dziennie na
  symulator — kolejkować, gdy kolizja (przesunąć sesję na kolejny wolny dzień).
- Recovery 1 dzień / recurrent 2 dni (już wdrożone).
- MEDEVAC C+C lub B+D; A tylko VFR/dzień (już wdrożone).

---

## 12. Moduł serwisu (panel techniczny)

Osobny moduł dla obsługi technicznej, podpięty do rdzenia przez nalot maszyn
i konfigurację progów.

- **Prognoza przeglądów** — dla każdej maszyny liczy, kiedy osiągnie próg
  (pobieżny / poważny / remont), na podstawie średniego dziennego nalotu.
  Wynik czytelny dla technika: „H5 — pobieżny za ~3 dni", „X2 — poważny za
  ~6 tygodni". Serwis widzi tu, jakie maszyny i kiedy przyjdą na przegląd lub
  remont.
- **Wezwanie priorytetowe** — technik klika „wezwij H5 na przegląd": maszyna
  natychmiast przechodzi w tryb priorytetowy, zostaje wycofana z obsady i
  skierowana na przegląd (pobieżny w hubie, poważny i remont w Lublinie),
  niezależnie od bieżącego resursu. `Maszyna` dostaje flagę
  `wezwanie_serwisowe: bool` — scheduler pomija ją natychmiast.
- **Kolejka serwisu** — maszyny w przeglądzie i oczekujące, z datą powrotu
  (`w_serwisie_do`) oraz miejscem (hub lub Lublin).

Okno: tabela floty z prognozą terminu i statusem, przycisk wezwania, podgląd
kolejki. Lublin oznaczony jako węzeł ciężkich przeglądów całej floty.

---

## 13. Moduł centralny — mapa sytuacyjna i telemetria

Całościowy podgląd operacyjny: mapa wszystkich sektorów z tym, co aktualnie
leci. Rozszerza mapę metra (§9) o warstwę sytuacyjną na żywo.

- **Mapa sytuacyjna** — wszystkie sektory naraz, maszyny w powietrzu oznaczane
  na bieżąco, z wejściem w pojedynczy sektor.
- **Klik na maszynę → panel parametrów**: kto leci (załoga), ile trwa bieżąca
  misja, pozycja oraz stan paliwa — o ile maszyna raportuje te dane.
- **Warstwa GPS** — pozycje maszyn z raportowania pokładowego, jeśli dostępne.

### 13.1. Interfejs telemetrii (klucz modułowości)

Dane z maszyn płyną przez interfejs `TelemetryProvider`:
- `pozycja(maszyna) -> (lat, lon) | None`
- `paliwo(maszyna) -> procent | None`
- `czas_misji(maszyna) -> minuty | None`
- `zaloga(maszyna) -> list[Pilot]`

W prototypie: adapter-zaślepka `MockTelemetry` z danymi symulowanymi (pozycje
w obrębie sektora, paliwo malejące wraz z czasem misji). Produkcyjnie: adapter
podpięty do realnego źródła — transponder, system pokładowy, śledzenie GPS.
Gdy maszyna nie raportuje, pola wracają `None`, panel pokazuje „brak danych",
a reszta modułu działa dalej.

Raportowanie zwrotne z maszyn w czasie rzeczywistym jest **opcjonalne**: moduł
centralny działa i bez telemetrii (pokazuje przydziały i dyżury), a źródło
danych dokłada warstwę live, gdy istnieje. To pozwala wdrożyć moduł teraz,
a telemetrię podpiąć później bez zmian w rdzeniu.

---

## 14. Roadmapa implementacji (kolejność powrotu)

Bloki rdzenia i interfejsu:

1. **Rejestr per egzemplarz** — przypisanie maszyny do dyżuru (separacja
   serwisowa) + funkcje „kto/kiedy/z kim" + nalot maszyny.
2. **Liczniki** — miesięczne i całkowite (pilot, klasa, symulator) + eksport JSON.
3. **Serwis (reguły)** — przeglądy pobieżne w hubie, poważne i remont w Lublinie,
   wyłączanie maszyny na czas postoju.
4. **Pojemność symulatora** — limit 1 pilot/dzień/symulator + kolejkowanie.
5. **Życzenia i kursy** — bloki wolnego + rejestr kursów + powiązanie z obsadą.
6. **Szkolenia i awanse** — skierowanie na szkolenie (limit 2/7), wymogi awansu,
   egzaminy, zatwierdzanie.
7. **Web demo** — okna konfiguracji, przydział maszyn i pilotów do hubów,
   dodaj/usuń pilota (timeout 10 s), awanse, rejestr maszyn, liczniki.
8. **Mapa metra** — sektory, przełącznik, panel dyżurów dnia.

Moduły podpinane (architektura z §0):

9. **Moduł serwisu** — prognoza przeglądów + wezwanie priorytetowe + kolejka.
10. **Moduł centralny** — mapa sytuacyjna + interfejs telemetrii z adapterem
    `MockTelemetry`; realne źródło GPS podpinane później bez zmian w rdzeniu.

Architektura modułowa (§0) jest zasadą przekrojową: bloki 1–6 utrwalają rdzeń,
7–8 to interfejs, 9–10 to moduły dopinane przez porty. Po każdym bloku `pytest`
+ regeneracja web demo.

