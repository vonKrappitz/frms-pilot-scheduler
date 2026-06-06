# Changelog

Wszystkie istotne zmiany w projekcie FRMS (pilot scheduler KPRL/LPR).
Format: odwrotnie chronologiczny, najnowsze na górze. Daty ISO (RRRR-MM-DD).

## [usunięcie TOPR z apki i demo] 2026-06-04

### Usunięte (TOPR/AW189 jakby nigdy nie istniał)
- `models.py`: usunięty członek `Organizacja.TOPR` oraz `KlasaMaszyny.TOPR_GORSKI` (AW189). Flota to teraz cztery klasy (AW101, H145, H135, Caravan). Metody (`wymaga_dwoch_pilotow`, `wymagany_nalot`) i docstringi oczyszczone z AW189/TOPR.
- `data.py`: usunięta baza EPZA Zakopane (TOPR), trzej piloci TOPR (demo to 30 pilotów LPR), slot AW189 w `generuj_sloty`, gałąź TOPR w `_generuj_type_ratings`, klasa AW189 z puli symulatora EPDE, nazwiska TOPR z `IMIONA`.
- `scheduler.py`, `currency.py`, `kursy.py`, `symulator.py`, `zamiana.py`, `export_json.py`, `build_web.py`: wszystkie odwołania do TOPR/AW189 usunięte lub przeredagowane. `KLASY_BEZ_SYM_I_SZKOLEN` jest teraz pustym zbiorem. Karta „Piloci" na dashboardzie bez rozbicia LPR/TOPR.
- Testy: `test_generacja_pilotow` (30 LPR), `test_generacja_slotow` (133/tydz.), usunięte asercje i test dot. TOPR. W całym `frms-web.html` brak ciągów TOPR/AW189/EPZA.

### Wpływ na liczby (demo bez TOPR)
- Jednostka bazowa 30 pilotów LPR / 133 sloty: 122/133 = 91,7%; dashboard (data raportu) 92,5%. Sieć docelowa 182/772 = 709 (91,8%).

### Walidacja
- 125 testów, headless 51/0, skan EN czysty, brak TOPR/AW189/EPZA w wygenerowanym HTML.



### Zmienione (rdzeń schedulera)
- `generuj_harmonogram` pilnuje teraz, że pilot przypisany do slotu (PIC, drugi pilot lub instruktor) jest niedostępny dla pozostałych slotów tego samego dnia. Śledzenie zajętych per dzień (`zajeci_w_dniu`), funkcje doboru dostają tylko pilotów wolnych w danym dniu. Koniec z dawną własnością prototypu dopuszczającą podwójną obsadę.
- Dodano `tests/test_wylacznosc_dnia.py` (5 dat, okno 15 dni): zero kolizji potwierdzone.

### Wpływ na liczby
- Po wyłączności: baza 128/140 = 91,4%, sieć docelowa 690/772 = 89,4% (scale_test). Poprzednio z dopuszczoną podwójną obsadą i parami z Tabeli 1: 130/140 = 92,9% i 704/772 = 91,2%.

### Walidacja
- 126 testów (121 + 5), headless 51/0, skan EN czysty, 0 podwójnych obsad w 5 przebiegach.



### Naprawione (błąd krytyczny, sprzeczność kod ↔ manuskrypt)
- `dobierz_pare_medevac` dla AW101 dopuszczał wyłącznie C+C i B+D, a docstring i komentarz jawnie zakazywały C+D i D+D („instruktor D pojawia się w MEDEVAC tylko jako nadzór nad B"). Sprzeczne z Tabelą 1 manuskryptu (C+C, C+D, D+D + B+D) i z briefem. Teraz dopuszczone wszystkie cztery: operacyjne C+C → C+D → D+D, a B+D jako ostateczność na slocie operacyjnym (PIC = D). PIC zawsze wyższej kategorii; B nigdy nie jest PIC.
- Dodano `tests/test_pary_medevac.py`: bezpośredni test osiągalności każdej dozwolonej pary i odrzucenia zakazanych (C+B, B+B, pojedynczy pilot). Wcześniejszy inwariant sprawdzał tylko brak par zakazanych, więc nie wykrywał, że C+D i D+D są w ogóle nieosiągalne.

### Wpływ na liczby (DO DECYZJI — dotyka cytowanych figur)
- Stary (błędny) kod: baza 133/140 = 95,0%, skala 720/772 = 93,3% — to liczby w manuskrypcie.
- Poprawiony kod (C+C, C+D, D+D, B+D): baza 130/140 = 92,9%, skala 704/772 = 91,2%.
- Dopuszczenie C+D/D+D obniża obsadę netto, bo pary C+D zużywają deficytowych C obsadzających inne sloty. Cytowane 95,0%/93,3% powstały pod regułą sprzeczną z Tabelą 1.

### Walidacja
- 121 testów (113 + 8), headless 51/0, skan EN czysty.



### Dodane
- Plik `NOTICE` w korzeniu: „Copyright 2026 Maciej M. Kasperek (\"vonKrappitz\")", odsyła do LICENSE.
- Nagłówek `# Copyright 2026 Maciej M. Kasperek (\"vonKrappitz\")` + `SPDX-License-Identifier: Apache-2.0` we wszystkich plikach źródłowych (frms/*.py, tests/*.py, scale_test.py, qa_headless.js, qa_en_leak.js) — łącznie 43 pliki.
- Generowany `frms-web.html`: komentarz copyright po doctype oraz dyskretna stopka „© 2026 Maciej M. Kasperek (\"vonKrappitz\") · Apache-2.0" (wstrzyknięte w SZABLON build_web.py).
- README: sekcja Licencja z copyright i odesłaniem do NOTICE; sekcja Autor uzupełniona o pełne imię, pseudonim, ORCID i GitHub.
- LICENSE pozostaje wierną treścią Apache 2.0 (właściciel praw deklarowany w NOTICE i nagłówkach, nie w treści licencji).

### Walidacja
- 113 testów, headless 51/0, skan EN czysty, importy pakietu OK. Copyright obecny w wygenerowanym HTML.



### Zmienione
- Sesje LAW: kolumna „powód" była po polsku także w EN. `frms/currency.py`: `opis_powodu_sesji` dostała parametr `lang` (pl/en). `frms/export_json.py`: eksport dokłada `powod_en`. `frms/build_web.py` renderSesje: definiuje `pl` i wybiera powód wg języka.
- Serwis: poziom obsługi (POBIEZNY/POWAZNY/REMONT) i priorytet (WYSOKI/SREDNI/NISKI) były surowymi polskimi enumami. renderSerwis tłumaczy etykiety (routine/major/overhaul, HIGH/MEDIUM/LOW), kolor odznaki dalej liczony z surowej wartości, więc logika bez zmian.
- Dodano `qa_en_leak.js`: renderuje wszystkie 12 sekcji po EN i skanuje pod kątem polskich słów UI. Po poprawkach przebieg czysty.

### Walidacja
- 113 testów, headless 51/0, skan przecieków EN czysty we wszystkich sekcjach i kartach dashboardu.



### Zmienione
- Serwis: obok „Wezwij na serwis" doszło „Anuluj wezwanie". Obie akcje są dwustopniowe: pierwszy klik uzbraja przycisk „Potwierdź ... (5)" z odliczaniem, drugi klik w oknie 5 s zatwierdza, a po upływie 5 s albo po „porzuć" stan wraca. Stan w pamięci (`serwStan`, `serwPend`, `serwTimer`); handlery `serwArm`/`serwPotwierdz`/`serwPorzuc`, `serwWezwij` zachowane jako alias uzbrojenia.
- Plan 15 dni: zmiana pilota dostała jawny, czytelny przycisk „✎ zmień" przy każdym obsadzonym fotelu (PIC i drugi pilot), widoczny zawsze; rozwija listę kandydatów albo informuje o ich braku. Wcześniej zmianę uruchamiała tylko podkreślona nazwa pilota, co było mało widoczne.
- Stress test (`qa_headless.js`) złapał i naprawiono błąd: znacznik prywatnego STOL w „Pilotach" używał `pl` bez lokalnej definicji, co wywalało `renderAll()` na starcie. Dodano `const pl` w `renderPiloci`.

### Walidacja
- Headless 51 kroków bez błędu (wszystkie okna PL i EN, pełne sekwencje handlerów). Inwarianty silnika OK (STOL tylko A jako PIC, pary MEDEVAC, kategorie, ratingi, kursy, awanse). Per-pilot 33/33. 113 testów. scale_test 95,0% / 93,3%.
- Uwaga: rdzeń `generuj_harmonogram` dopuszcza obsadę tego samego pilota na dwóch slotach w dniu (własność prototypu, nie regresja; spójna z opisem „dowód wykonalności, nie system produkcyjny").



### Zmienione (rdzeń odmrożony)
- Uprawnienia kategorii wyrównane do manuskryptów i ORO.FC.240 (potwierdzone u źródła: pilot łączący śmigłowiec i samolot ma po jednym typie każdego; wyjątek tylko dla tłokowych jednopilotowych VFR dzień, więc turbinowego Caravana nie obejmuje). `_generuj_type_ratings`: A = H135 plus STOL; B = H135 plus H145; C, D = H135, H145, AW101. STOL znika z B/C/D.
- Slot STOL (`generuj_sloty`): zawsze jednoosobowy, kapitan kat A; w trudnych warunkach mentor/obserwator włączany flagą `trudny_lot`.
- Nowy model prywatnego STOL. `frms/models.py`: `Pilot.stol_prywatnie`, `Pilot.stol_rejestr`; `Kandydat.obserwator`. `frms/stol.py`: rejestr godzin, kryterium biegłości (samozgłoszenie plus świeże godziny), enricher. B/C/D oficjalnie bez kwalifikacji komercyjnej STOL, ale z prawem do prywatnego latania; biegli prywatnie mogą być nieformalnym mentorem (kat D) lub wsparciem (B/C) kapitana A, jako dodatkowa niepilotująca załoga, nie copilot. Rejestr wewnętrzny, bez mocy regulacyjnej.
- `frms/zamiana.py`: `kandydaci_drugiego_pilota_stol` → `kandydaci_obserwatora_stol` (pula z prywatnej biegłości, bez wymogu formalnego ratingu, oznaczeni jako obserwator). STOL wyłączony z formalnego fotela szkoleniowego (instruktaż samolotowy poza korpusem A–D).
- `frms/export_json.py`: enricher prywatnego STOL, rola w puli (mentor/wsparcie), znaczniki `stol_prywatnie`/`stol_biegly` u pilota. `frms/build_web.py`: Plan 15 dni z etykietą „trudne warunki (mentor/obserwator)" i rolą, znacznik STOL w „Pilotach". Poprawka martwego warunku klasy w kolumnie kursów.
- `scale_test.py` odtworzony w katalogu głównym (replikacja jednostki bazowej; reprodukowalność cz. III [22]).

### Walidacja
- 113 testów zielonych. Obsada bazowa 133/140 = 95,0% — bez zmian po przebudowie. scale_test odtworzony reprodukuje liczby manuskryptu: 95,0% przy 33/140 oraz 93,3% (720/772) w sieci docelowej 182/772, czas ~n². Manuskrypt nie wymaga zmiany.

## [poprawki po przeglądzie i przeniesienie kursów] 2026-06-03

### Zmienione
- Kursy wciągarki i FIKI przeniesione pod MEDEVAC (AW101). Za manuskryptem cz. II: H145 ma tylko podstawowe odladzanie i nie nosi wciągarki, pełne FIKI i wciągarkę ma wyłącznie AW101. `frms/kursy.py`: `KURSY_HEMS = {lot nocny, gogle nocne}`, `KURSY_MEDEVAC` dokłada wciągarkę i FIKI; enricher nadaje zestaw zależny od ratingu (MEDEVAC 4, sam HEMS 2). `frms/awanse.py`: bramka kursowa po szczeblach — na B kursy HEMS, na C kursy MEDEVAC (wciągarka i FIKI jako brama na AW101), na D bez nowych. `frms/build_web.py` renderPiloci: kursy liczone per pilot (MEDEVAC 4, HEMS 2) plus poprawka martwego warunku klasy (wartości enuma `MEDEVAC_AW101`/`HEMS_H145`, nie nazwy członków). Testy zaktualizowane (`test_kursy`, `test_awanse`, `test_zamiana`). Poza zamrożonym rdzeniem: scale_test bez zmian.
- TOPR wyciszony w symulatorze i szkoleniu. `frms/currency.py`: `KLASY_BEZ_SYM_I_SZKOLEN = {TOPR_GORSKI}`. `frms/symulator.py`: zapotrzebowanie symulatorowe pomija TOPR (recurrent i recovery). `frms/zamiana.py`: fotel szkoleniowy i wyjątek szkoleniowy nie dotyczą slotów TOPR. Test `test_topr_wylaczony_z_symulatora`.
- Recovery LAW: osobno starty i lądowania, minimum 5 + 5. `frms/models.py`: pola `SesjaSymulatorowa.starty` i `.ladowania`. `frms/currency.py`: `recovery_wazna` wymaga startów ≥ 5 ORAZ lądowań ≥ 5. `frms/law.py`: `zarejestruj_recovery(pilot, klasa, dzien, starty, ladowania)`. Web: dwa pola (starty, lądow.), zaliczenie od 5 + 5. Testy zaktualizowane.
- Web, sekcja Serwis: przycisk „Wezwij na przegląd" per egzemplarz (stan w pamięci demo, znacznik „wezwana"); egzemplarze w serwisie bez przycisku.
- Web, mapa live (Centrum): powiększona (viewBox 720×780, większe kropki i etykiety, mocniejszy jitter), bo była nieczytelna.
- Mapa sektorów na pełnej sieci reformy. `frms/siec.py`: sieć z cyklu SFT (Część I architektura, Część II Załącznik 1 Tabela 1) — 7 Centrów Regionalnych jako głowy sektorów, 15 Centrów Transferowych z przypisaniem do sektorów, CSI-LRM Drawsko Pomorskie, CT-S Krępa Słupska; 24 nazwane lokalizacje, plus 4 Bazy Wsparcia bez nazw i lokalizacji w artykułach (razem 28). `frms/export_json.py`: klucz `siec_reforma`. Web: `renderMapa` rysuje 7 sektorów (szprychy CRL→CT w kolorze sektora, węzły CRL/CT/CT-S/CSI-LRM), legenda z licznikiem 24/28. `tests/test_siec.py` (3). Dane zweryfikowane względem artykułów.

### Założenie
- Cztery Bazy Wsparcia są policzone do 28, lecz nierysowane: artykuły ich nie nazywają ani nie lokalizują. Po podaniu nazw i współrzędnych wejdą na mapę.

## [blok 10] 2026-06-03 — moduł centralny: mapa live z telemetrią (roadmapa §14 kompletna)

### Dodane
- `frms/telemetria/__init__.py`: adapter `MockTelemetry` implementujący port `TelemetryProvider` (pozycja, paliwo, czas misji, załoga). Deterministyczny, bez RNG i bez stanu; pozycja w okolicy huba (`WSPOLRZEDNE_BAZ`), w locie z odchyłką. Realne GPS podmienia tylko adapter.
- `frms/centralny/__init__.py`: snapshot live floty (`snapshot_floty`, `snapshot_maszyny`, `status_maszyny`). Status łączy telemetrię z regułami serwisu: SERWIS, LOT (telemetria raportuje czas misji), ZIEMIA, NIEOPERACYJNA.
- `frms/export_json.py`: klucz `centrum_live` (maszyny ze statusem, pozycją, paliwem, czasem misji; podsumowanie; współrzędne baz). Smoke: 51 maszyn, 17 LOT / 27 ZIEMIA / 7 NIEOPERACYJNA.
- `frms-web.html` (generator): zakładka „Centrum (live)" z mapą geograficzną (bazy i maszyny rzutowane z lat/lon, status kolorem) oraz tabelą floty z paliwem i czasem misji.
- `tests/test_centralny.py` (6), guard generatora rozszerzony.

### Stan projektu
- Roadmapa rozbudowy (§14, bloki 0–10) kompletna. 109 testów zielonych. Funkcje rdzenia (`generuj_pilotow`, `generuj_sloty`, `generuj_harmonogram`) nietknięte przez cały cykl, więc scale_test cytowany w artykule pozostaje reprodukowalny.

## [blok 9] 2026-06-03 — moduł serwisu: prognoza zużycia i wezwania priorytetowe

### Dodane
- `frms/prognoza_serwis.py`: nalot pozostały do każdego progu obsługi (`godziny_do_progow`), najbliższy próg (`najblizszy_przeglad`), dni do progu wg tempa (`prognoza_dni`, tempo założone `TEMPO_DOMYSLNE_H_DZIEN=3.0` do czasu telemetrii), priorytet wezwania (`priorytet_wezwania`: WYSOKI ≤10 h lub po progu, SREDNI ≤30 h, NISKI dalej), prognoza i wezwania floty (`prognoza_floty`, `wezwania_priorytetowe`). Reużywa reguł serwisu (`prog_poziomu`, `_nalot_od_ostatniego`, `miejsce_serwisu`). `tests/test_prognoza_serwis.py` (5).
- `frms/export_json.py`: klucze `serwis_prognoza` (cała flota, najpilniejsze pierwsze) i `serwis_wezwania` (priorytetowe). Smoke: 51 maszyn, 13 wezwań.
- `frms-web.html` (generator): zakładka „Serwis" z banerem liczby wezwań i tabelą prognozy (nalot, próg, godziny i dni do obsługi, priorytet, miejsce). Egzemplarze w serwisie oznaczone.

### Założenie
- Tempo nalotu jest stałym założeniem; realne tempo per egzemplarz dostarczy telemetria (blok 10).

## [blok 8] 2026-06-03 — mapa metra sektorów sieci

### Dodane
- `frms-web.html` (generator): zakładka „Sieć / Sektory" ze schematyczną mapą metra (SVG). Bazy jako stacje, CRL (HUB) jako węzły przesiadkowe (podwójny pierścień), baza szkoleniowa jako kwadrat. Sektory geograficzne wokół CRL: Centralny (Warszawa, Łódź, Dęblin), Południowy (Kraków, Katowice, Rzeszów, Zakopane TOPR), Zachodni (Wrocław), każdy własną kolorową linią. Legenda sektorów i typów węzłów. Stacje rysowane z `DANE.bazy`, układ schematyczny stały.
- `tests/test_build_web.py`: guard rozszerzony o `renderMapa`.

### Założenie
- Podział na sektory jest geograficzny (wokół CRL), bo dane baz nie niosą przypisania do sektora ani współrzędnych. Do zmiany, jeśli reforma definiuje sektory inaczej.

## [blok 6 — część 2] 2026-06-03 — awanse: eligibility, limit ucznia, widok (blok 6 kompletny)

### Dodane
- `frms/models.py`: pole `Misja.czy_szkoleniowy` (additive) — lot szkoleniowy liczy do limitu ucznia.
- `frms/awanse.py`: eligibility do awansu. Progi nalotu (ROBOCZE: B 500 h, C 1000 h, D 2000 h), `nalot_calkowity` (logbook plus misje bez symulatora). Kursy wchodzą na szczeblu A→B (komplet czterech), dalej już są (`spelnia_kursy_do_awansu`). Limit ucznia: maksymalnie 2 loty szkoleniowe na 7 dni (`liczba_szkolen_ucznia_w_oknie`, `moze_przyjac_szkolenie`); sesje symulatorowe nie liczą się. Instruktor bez limitu, z prawem weta (sprzeciw już w wymianie). `kwalifikuje_sie_do_awansu` łączy nalot, kursy i minimum 3 zatwierdzających. `tests/test_awanse.py` (8).
- `frms/zamiana.py`: limit ucznia egzekwowany w obu ścieżkach szkoleniowych.
- `frms/export_json.py`: klucz `awanse` (kandydaci z kryteriami i liczbą zatwierdzających), liczony na kopii populacji z deterministycznym kontekstem demo (`przypisz_wspolne_loty_demo`: wspólne loty z trzema D plus roboczy nalot życiowy per kategoria), kanoniczna populacja nietknięta. Smoke: 18/28 kwalifikuje się (B→C i C→D), A→B blokuje brak kursów.
- `frms-web.html` (generator): zakładka „Awanse" z kryteriami per kandydat (nalot vs próg, kursy, zatwierdzający n/3, kwalifikuje).

## [blok 6 — część 1] 2026-06-03 — awanse: zatwierdzanie przez instruktorów (w toku)

### Dodane
- `frms/awanse.py`: awans wymaga zatwierdzenia przez minimum 3 pilotów kategorii D (`MIN_ZATWIERDZAJACYCH_D`), a każdy zatwierdzający musi mieć wspólną historię lotów z uczniem (`latal_z`, powiązanie przez `drugi_pilot_id`). `instruktorzy_zatwierdzajacy`, `liczba_zatwierdzajacych`, `ma_dosc_zatwierdzajacych`, `nastepna_kategoria` (A→B→C→D). Brak automatycznego awansu. `tests/test_awanse.py` (4).

### Do zrobienia (blok 6)
- Eligibility do awansu: progi nalotu i komplet kursów na każdy szczebel (A→B, B→C, C→D), limit szkoleń 2 na 7 dni. Czeka na wartości progów.
- Eksport i web: lista kandydatów do awansu z liczbą uprawnionych zatwierdzających i spełnieniem progów.

## [blok 5] 2026-06-03 — kursy specjalistyczne i dni wolne

### Dodane
- `frms/models.py`: enum `Kurs` (LOT_NOCNY, ZAWIS_WCIAGARKA, GOGLE_NOCNE, FIKI); pola `Pilot.kursy` i `Pilot.dni_wolne` (additive).
- `frms/kursy.py`: HEMS i MEDEVAC wymagają kompletu czterech kursów (LST/STOL/TOPR żadnego). `brakujace_kursy`, `spelnia_kursy`, `na_urlopie`, `dostepny_w_dniu`. Enrichery deterministyczne (bez RNG, by nie ruszać scale_test): `przypisz_kursy_domyslne` (każdy pilot z ratingiem HEMS/MEDEVAC dostaje komplet, co jedenastemu odejmuje jeden kurs dla demonstracji bramki), `przypisz_dni_wolne`. `tests/test_kursy.py` (6).
- `frms/zamiana.py`: bramkowanie w doborze i wymianie. Urlop wyklucza na każdej ścieżce; komplet kursów wymagany na ścieżce normalnej dla HEMS/MEDEVAC. Ścieżka szkoleniowa nie jest bramkowana kursami. Rdzeń harmonogramu nietknięty. `tests/test_zamiana.py` rozszerzone (15).
- `frms/export_json.py`: populacje wzbogacone o kursy i dni wolne (po harmonogramie). Pola `kursy` i `liczba_dni_wolnych` w pilotach. Klucz `alerty_kursy`: obsadzony pilot na HEMS/MEDEVAC bez kompletu kursów (analogicznie do alertów type ratingu). Smoke: 20 pilotów z kursami, 2 z niepełnym kompletem, 5 z dniami wolnymi, 9 alertów kursów.
- `frms-web.html` (generator): w zakładce Piloci kolumny „Kursy" (4/4 zielone, niepełne czerwone) i „Wolne"; w zakładce Alerty podtabela braków kursów u obsadzonych pilotów.

## [blok 7 — część 5] 2026-06-03 — web: fotel szkoleniowy i trudny lot STOL (blok 7 web kompletny)

### Dodane
- `frms/export_json.py`: per slot planu pule `fotel_szkoleniowy` (maszyna jednoosobowa z PIC kat D, kandydaci z `kandydaci_szkoleniowi`) i `kandydaci_stol_trudny` (STOL, drugi pilot operacyjny z `kandydaci_drugiego_pilota_stol`, liczone z tymczasowo włączonym `trudny_lot`).
- `frms-web.html` (generator): pod obsadą slotu w planie link „+ fotel szkoleniowy" (rozwija pulę, wybór dodaje pilota szkolonego z nadzorem D, cofnij przywraca) oraz checkbox „trudny lot (2. pilot)" dla STOL (po włączeniu picker drugiego pilota operacyjnego). Stan w pamięci demo.
- `tests/test_build_web.py`: guard rozszerzony o funkcje foteli dodatkowych.

### Stan bloku 7
- Web kompletny: nawigacja dzień po dniu (15 dni), wymiana pilota, fotel szkoleniowy, trudny lot STOL, grafik LAW z rejestracją, obłożenie symulatora EPDE z przepełnieniem, przełącznik PL/EN. Generator z bezpiecznym wstrzykiwaniem danych.

## [blok 7 — część 4] 2026-06-03 — web: interaktywna wymiana pilota w planie

### Dodane
- `frms/export_json.py`: każdy slot w `plan_15dni` niesie pule kandydatów do zamiany (`kandydaci_pic`, `kandydaci_fo`), liczone silnikiem `kandydaci_zamiany` na populacji planu, kompaktowo `{id, szk, nadz}` (czołówka 20). Kandydaci szkoleniowi (jedna kategoria poniżej minimum przy PIC kat D) oznaczeni `szk` z nadzorującym.
- `frms-web.html` (generator): w zakładce „Plan 15 dni" kliknięcie pilota w slocie rozwija pulę kandydatów; „Wybierz" podmienia obsadę (stan w pamięci), „cofnij" przywraca. Kandydat szkoleniowy ma znacznik i nadzorującego. Silnik jest jedynym źródłem reguł, JS tylko pokazuje gotową pulę.
- `tests/test_build_web.py`: guard rozszerzony o funkcje wymiany i obecność pul w planie.

### Do zrobienia (blok 7, dalej)
- Otwieranie fotela szkoleniowego przy maszynie jednoosobowej z D oraz przełącznik „trudny lot" STOL w interfejsie (silnik gotowy: `kandydaci_szkoleniowi`, `kandydaci_drugiego_pilota_stol`).

## [blok 7 — część 3] 2026-06-03 — moduł LAW: grafik treningów i rejestracja wyniku

### Dodane
- `frms/law.py`: grafik treningów EPDE na dziś i kolejne 14 dni (`grafik_law`), z typem sesji (recurrent/recovery), maszyną i całkowitym nalotem pilota na tym modelu (`nalot_na_klasie`, suma godzin lotu operacyjnego, bez symulatora). Rejestracja wyniku: `zarejestruj_recovery` (zalicza dopiero od 5 startów i lądowań, inaczej nic nie zapisuje), `zarejestruj_recurrent` (zalicza kwartał jednym wywołaniem). `tests/test_law.py` (5).
- `frms/export_json.py`: klucz `law_grafik_15dni` (15 dni, sesje z pilotem, klasą, typem, nalotem na modelu, wymaganymi startami i terminem recovery), liczony na czystej kopii pilotów przed mutacją historii.
- `frms-web.html` (generator): zakładka „Grafik LAW" z nawigacją dzień po dniu. Każda sesja pokazuje maszynę, pilota, typ, nalot na modelu i termin recovery. Rejestracja po stronie demo (stan w pamięci): recovery ma pole startów i lądowań plus przycisk zaliczenia aktywny od 5, recurrent jeden przycisk. Jeden dzień obsługuje wielu pilotów na różnych maszynach, mix recovery i recurrent.
- `tests/test_build_web.py`: guard rozszerzony o funkcje i klucz LAW.

## [blok 7 — część 2] 2026-06-03 — web: odbudowa generatorem, plan 15 dni, bezpieczne wstrzykiwanie danych

### Naprawione
- Pułapka zachłannej podmiany `const DANE = {.*};` (regex, DOTALL) zjadała funkcje renderujące po danych i przy regeneracji uszkadzała `frms-web.html`. Metoda wycofana. `frms-web.html` jest teraz produkowany przez generator `frms/build_web.py`, który wstrzykuje dane przez unikalny znacznik `__DANE__` zwykłym `str.replace(count=1)`. Nigdy więcej regexu na osadzonym JSON.

### Dodane
- `frms/build_web.py`: generator całego interfejsu (komplet widoków: Dashboard, Harmonogram, Plan 15 dni, Piloci, Alerty, Sesje LAW, Symulator EPDE; przełącznik PL/EN). `python3 -m frms.build_web` regeneruje plik.
- `frms/export_json.py`: klucz `plan_15dni` (operacyjny plan dzień po dniu na 15 dni), liczony na osobnej, zasianej populacji (te same 33 osoby) dla determinizmu, niezależnie od mutacji tygodniowych.
- Web: zakładka „Plan 15 dni" z nawigacją dzień po dniu (poprzedni/następny, licznik 1/15, obsadzenie dnia) oraz zakładka „Symulator EPDE" z banerem przepełnienia i tabelą nieobsadzonych.
- `tests/test_build_web.py` (4): JSON parsowalny, komplet funkcji renderujących, świeże dane bez KODIAK, plan 15 dni. Pilnują, że regeneracja nie uszkodzi pliku.

### Wycofane
- Checkpoint `FRMS_checkpoint_2026-06-03_blok7cz1.zip` zawiera uszkodzony `frms-web.html` (stara metoda). Odrzucić na rzecz nowego checkpointu.

## [blok 7 — część 1] 2026-06-03 — web: panel obłożenia symulatora EPDE

### Dodane
- `frms/export_json.py`: klucz `symulator_epde` (obłożenie per dzień, przepełnienie). Liczony z `zaplanuj_symulator` na kopii pilotów przed dopisaniem sesji do historii, żeby reguła „raz na kwartał" nie wyzerowała zapotrzebowania.
- `frms-web.html`: zakładka „Symulator EPDE", panel obłożenia per dzień z banerem przepełnienia (zielony gdy wszystko się mieści, czerwony z liczbą nieobsadzonych) i tabelą nieobsadzonych z oknami. Smoke przy dacie 2026-06-03 (koniec kwartału): 56 slotów, 8 nieobsadzonych — realny sygnał przepełnienia przy wąskim oknie recurrent.

### Do zrobienia (blok 7, dalej)
- Nawigacja dzień po dniu po 15-dniowym planie operacyjnym.
- Wymiana pilota: klik pilota w slocie, pula kandydatów (norma plus szkoleniowi), fotel szkoleniowy przy maszynie jednoosobowej z D, przełącznik „trudny lot" STOL.

## [blok 4] 2026-06-03 — dobór, wymiana pilota, horyzont 15 dni, pojemność symulatora (silnik gotowy; web w bloku 7)

### Dodane
- `frms/zamiana.py`: pula zamienników dla slotu (`kandydaci_zamiany`). Ścieżka normalna reużywa `kandydat_kwalifikujacy_sie` i dodatkowo wyklucza pilotów wymagających currency recovery oraz zajętych tego dnia. Wyjątek szkoleniowy: w slocie dwuosobowym drugi fotel może objąć pilot dokładnie jedną kategorię poniżej minimum, jeśli PIC to kat D; lot oznaczony jako szkoleniowy, nadzorujący D może zgłosić sprzeciw. Próg kategorii poza tym twardy.
- `frms/zamiana.py`: fotel szkoleniowy przy maszynie jednoosobowej (STOL/H135/H145 single) obsadzonej przez kat D (`kandydaci_szkoleniowi`, `instruktor_slotu`). D szkoli tylko kandydatów do klasy, kategoria nie niżej niż jedna poniżej minimum klasy (MEDEVAC: B/C/D, HEMS: A/B/C/D; A na MEDEVAC nie wejdzie, bo musi najpierw zrobić B), bez wymogu type ratingu, z flagą szkoleniową i nadzorem D. Drugi pilot operacyjny dla STOL z `trudny_lot` (`kandydaci_drugiego_pilota_stol`): pełna kwalifikacja, bez flagi szkoleniowej.
- `SlotDyzurowy.trudny_lot` (additive): dyspozytor włącza drugiego pilota na STOL (ciężkie warunki / długi / powrotny).
- `tests/test_zamiana.py` (12).
- `frms/plan.py`: warstwa planu operacyjnego, horyzont `HORYZONT_DNI = 15` (dziś i kolejne 14 dni), sloty pogrupowane per dzień, nawigacja `nastepny_dzien`/`poprzedni_dzien`/`dzien_planu`. Woła `generuj_sloty(dzien, dni)` i `generuj_harmonogram` bez zmiany ich sygnatur. `tests/test_plan.py` (3).
- `frms/symulator.py`: pojemność EPDE, jeden pilot na klasę na dzień. `zbierz_zapotrzebowanie` czyta reguły currency i wyznacza okna (recurrent w kwartale, recovery w 45 dniach). `zaplanuj_z_zapotrzebowania` pakuje greedy: priorytet (recovery WYSOKI, recovery NISKI, recurrent), potem najwcześniejszy termin; kolizje rozwiązuje przesunięciem na pierwszy wolny dzień w oknie; bez podwójnej rezerwacji symulatora klasy i bez pilota w dwóch symulatorach tego samego dnia. `zaplanuj_symulator` emituje sloty SYMULATOR_LAW i zwraca nieobsadzone jako sygnał przepełnienia. Smoke: 33 recurrent + 2 recovery = 68 slotów, zero przepełnienia, rozłożone na 40 dni. `tests/test_symulator.py` (6).

### Do zrobienia (blok 7, web)
- Wiring w `frms-web.html`: nawigacja dzień po dniu po 15-dniowym planie, wymiana pilota z pulą kandydatów, fotel szkoleniowy i przełącznik „trudny lot" STOL, widok obłożenia symulatora EPDE z sygnałem przepełnienia.

## [blok 3.5] 2026-06-03 — przebudowa modelu sesji symulatorowych

### Zmienione
- Samolot STOL: Daher Kodiak 100 zastąpiony przez Cessna Grand Caravan EX. Rename czysty, bez aliasu i długu: wartość enuma `KlasaMaszyny.STOL_SAMOLOT` = `"STOL_GRAND_CARAVAN_EX"`, stała `PROG_DNI_BEZ_LOTU_KODIAK` przemianowana na `PROG_DNI_BEZ_LOTU_SAMOLOT`. Komentarze i etykiety w data/scheduler/models/web zaktualizowane.
- Recurrent: model kwartalny (kwartał kalendarzowy) zamiast kroczącego 90 dni. Jedna sesja na pilota na kwartał, 2 dni × 6h = 12h, trudne scenariusze (autorotacje, awarie silnika, lądowania awaryjne). Bez pustego kwartału. Domyślna klasa: własna najdawniej ćwiczona. Zakres dozwolony: klasy własne plus jedna kategoria wyżej (A→HEMS, B→MEDEVAC), do ręcznego wyboru w UI (blok 7).
- Recovery: okno 45 dni na wykonanie po wyzwoleniu. Wyzwolenie 21 dni (helikoptery) / 45 dni (samolot). Samolot: twardy limit 45+45 = 90 dni bez lotu (granica przepisowa). Priorytet NISKI dla samolotu, WYSOKI dla helikopterów. Sesja ważna od minimum 5 startów i lądowań.
- Eksport sesji: poprawione liczby (recurrent 2 dni / 12h, recovery 1 dzień / 6h; wcześniej odwrócone), dodane pola `priorytet` i `dni_do_terminu` przy recovery.

### Dodane
- `SesjaSymulatorowa.starty_ladowania` (pole, domyślnie 0; recovery ważne od 5).
- `frms/currency.py`: `priorytet_recovery`, `termin_recovery`, `dni_do_terminu_recovery`, `recovery_wazna`, `data_ostatniej_aktywnosci`, `kwartal`, `klasy_wlasne_aktualne`, `zakres_szkolenia_symulator`, `klasa_recurrent_domyslna`, `recurrent_odbyty_w_kwartale`.
- `tests/test_currency.py`: testy modelu kwartalnego, zakresu, recovery (okno/priorytet/ważność), generatora.

### Walidacja
- pytest 52/52. Web demo (`frms-web.html`) zregenerowane: 39 sesji, godziny_sym 432, zero wystąpień Kodiaka, JSON parsuje się.

## [blok 3] 2026-06-02 — reguły serwisu maszyn

### Dodane
- `frms/serwis/`: poziomy serwisu (POBIEZNY/POWAZNY/REMONT), detekcja należnego przeglądu po nalocie, kierowanie (pobieżny: hub macierzysty 1 dzień; poważny/remont: EPLB 3/30 dni), zwalnianie po terminie, przegląd floty.
- Modele (additive): enum `PoziomSerwisu`, dataclass `Serwis`, pola `Maszyna.w_serwisie_do/lokalizacja_serwisu/historia_serwisow`, `KonfiguracjaSerwisu.osrodek_powazny_remont`.
- Stan serwisowy w `obciazenie_floty`.
- `tests/test_serwis.py` (7).

## [blok 2] 2026-06-02 — liczniki nalotu i godzin

### Dodane
- `frms/liczniki.py`: nalot miesięczny / per klasa / całkowity, godziny symulatora, liczniki pilota i maszyny, log lotów.
- `Pilot.nalot_logbook_h` (additive).
- `tests/test_liczniki.py` (6), `tests/test_export.py` (5).

### Zmienione
- `frms/export_json.py`: jedno źródło prawdy (jeden `Rdzen.domyslny` po harmonogramie i przydziale maszyn). Stały `SEED_EKSPORTU=2026` (powtarzalność). Helper `_bezpiecznie()` izoluje błędy per rekord. Dodane klucze `liczniki_pilotow`, `liczniki_maszyn`, `obciazenie_floty`; sloty niosą `maszyna_id`.

## [blok 1] 2026-06-02 — rejestr maszyn per egzemplarz

### Dodane
- `frms/rejestr.py`: dobór maszyn (lokalnie najpierw, potem krajowo), separacja serwisowa, brak podwójnej rezerwacji egzemplarza na dzień; `nalot_maszyny`, `kto_latal`, `obciazenie_floty`.
- `SlotDyzurowy.maszyna_id`, `SlotDyzurowy.maszyna_z_innej_bazy` (additive).
- `tests/test_rejestr.py` (8).

## [blok 0] 2026-06-02 — szkielet architektury

### Dodane
- `frms/rdzen.py`: kontener stanu `Rdzen` (źródło prawdy) z akcesorami odczytu i zapisu, fabryka `Rdzen.domyslny(dzien)`.
- `frms/porty.py`: protokół `TelemetryProvider` (granica IO).
- Puste pakiety `frms/serwis/`, `frms/centralny/`, `frms/telemetria/`.
- `tests/test_rdzen.py`.

### Zasady
- Architektura: stan jako cienki kontener (wariant A), płaski pakiet `frms/` (wariant S). Reguła zależności: moduły i IO zależą tylko od rdzenia; rdzeń od nikogo.
- Sygnatury publiczne `generuj_pilotow`, `generuj_sloty`, `generuj_harmonogram` nietknięte (reprodukowalność wyniku scale_test cytowanego w artykule).
