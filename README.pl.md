# FRMS Pilot Scheduler

**Język:** [English](README.md) | Polski

Prototyp (proof of concept) systemu zarządzania zmęczeniem załóg (FRMS) do układania dyżurów pilotów ratownictwa lotniczego HEMS i transportu medycznego MEDEVAC dla floty wieloklasowej. Narzędzie przydziela pilotów do slotów dyżurowych, pilnując ważności uprawnień na typ, limitu skumulowanego obciążenia i rotacji puli tak, aby żadne uprawnienie nie wygasło.

Licencja: Apache License, wersja 2.0.

---

## Co robi

Flota jest wieloklasowa, a jeden pilot może mieć uprawnienia na więcej niż jedną klasę statku powietrznego. Ręczne ułożenie takiego grafiku jest podatne na błędy, gdy załoga rośnie. To narzędzie pokazuje, że zadanie da się prowadzić obliczeniowo.

Dla każdego pilota śledzi w sposób ciągły trzy zmienne:

1. **Ważność uprawnień na typ** na każdej klasie, z alertem przed wygaśnięciem okna 90 dni.
2. **Skumulowane obciążenie** z ostatnich 96 godzin (misje, długość lotu, ciężkość).
3. **Pozycję w cyklu rotacji**.

Na tej podstawie przydziela pilotów do slotów tak, aby obsadzić każdą zmianę w ramach dostępnych kategorii, zapobiegając zarazem przeciążeniu pojedynczego pilota i zbyt długiej przerwie na danym typie. Wskaźnik zmęczenia wchodzi jako **twarda reguła**: pilot powyżej progu skumulowanego obciążenia nie wchodzi do slotu, nawet z ważnym uprawnieniem.

Piloci są ujęci w czteroklasową kategoryzację (**A–D**) zdefiniowaną względem europejskich reguł licencjonowania i bieżącości. Kategorie są zbudowane tak, aby żaden pilot nie przekroczył prawnego limitu łączenia typów.

## Status

To jest **prototyp, nie system produkcyjny**. Powstał, aby pokazać wykonalność obliczeniowego nadzoru nad wieloklasowym grafikiem pilotów o realnej skali. Udostępniony dla przejrzystości i powtarzalności wraz z powiązaną pracą naukową (patrz *Powiązana praca*).

## Powiązana praca

To repozytorium jest implementacją referencyjną systemu FRMS opisanego w pracy o zasobach załogowych i zarządzaniu zmęczeniem w ratownictwie lotniczym (HEMS). Praca jest obecnie w recenzji. Pełny cytat zostanie dodany po publikacji.

## Układ repozytorium

```
frms/                pakiet FRMS (logika przydziału i walidator)
tests/               testy jednostkowe potwierdzające reguły przydziału
examples/            małe uruchamialne przykłady
docs/                dokumentacja
scale_test.py        test skalowalności (patrz "Odtworzenie wyników")
requirements.txt     zależności Pythona
LICENSE / NOTICE     licencja Apache-2.0 i noty
```

Dwa publiczne punkty wejścia przywoływane w artykule to `generuj_harmonogram` (generowanie grafiku) i walidator grafiku. `scale_test.py` używa obu bez zmian.

## Wymagania

- Python 3.10 lub nowszy
- Zależności wypisane w `requirements.txt`

## Instalacja

```bash
git clone https://github.com/vonKrappitz/frms-pilot-scheduler.git
cd frms-pilot-scheduler
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Użycie

Uruchom dołączony przykład:

```bash
python -m examples.demo          # lub: python examples/demo.py
```

Uruchom testy jednostkowe:

```bash
python -m pytest                 # lub: python -m unittest
```

## Odtworzenie wyników z powiązanego artykułu

Tezę o skalowalności odtwarza jedno polecenie:

```bash
python scale_test.py
```

`scale_test.py` używa `generuj_harmonogram` i walidatora bez ich modyfikacji, skalując syntetyczną załogę. Oczekiwane zachowanie:

- Jednostka bazowa to **30 pilotów i 133 sloty tygodniowe**, z których aplikacja obsadza **122 (około 92 procent)**.
- Przy **182 pilotach i 772 slotach tygodniowych** grafik powstaje w **mniej niż sekundę** (około 280 ms), obsadzając **709 slotów (około 92 procent)**.
- Obsada utrzymuje się płasko ze skalą: **około 92 procent** od jednostki bazowej 30 pilotów (91,7 procent) po 182 pilotów (91,8 procent). Alerty przeładowania pozostają pojedyncze.
- Czas rośnie mniej więcej z kwadratem liczby pilotów (około O(n²)).

Dokładne liczby mogą się nieznacznie różnić w zależności od ziarna losowego i maszyny, ale rzędy wielkości powyżej powinny się utrzymać.

## Jak cytować

**Oprogramowanie:**

> M. Kasperek, *FRMS Pilot Scheduler* (oprogramowanie w Pythonie), Apache-2.0. GitHub: https://github.com/vonKrappitz/frms-pilot-scheduler. Zenodo DOI: *10.5281/zenodo.20574880*.

Cytat powiązanej pracy zostanie dodany po jej publikacji.

## Licencja

Na licencji Apache License, wersja 2.0. Patrz [LICENSE](LICENSE) i [NOTICE](NOTICE).

## Autor

Maciej Kasperek — GitHub [@vonKrappitz](https://github.com/vonKrappitz) · ORCID [0009-0008-7419-0851](https://orcid.org/0009-0008-7419-0851)
