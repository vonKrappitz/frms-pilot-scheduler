# STAN — FRMS (zamrożenie rdzenia zdjęte 2026-06-03)

Do 2026-06-03 rdzeń (`generuj_pilotow`, `generuj_sloty`, `generuj_harmonogram`)
był zamrożony dla reprodukowalności scale_test cytowanego w cz. III [22]. Na
polecenie autora zamrożenie zdjęto, by wyrównać uprawnienia do manuskryptów
(STOL formalnie tylko kat A wg ORO.FC.240; B/C/D bez samolotu). Po tej zmianie
obsada bazowa pozostaje 133/140 = 95,0% (bez zmian), a scale_test odtworzono
jako `scale_test.py` w katalogu głównym.

Walidacja: `pytest tests/` (113 testów).

## Reguły kadrowe (aktualne)
- A: H135 plus STOL (jeden śmigłowiec, jeden samolot), VFR dzień.
- B: H135 plus H145. C, D: H135, H145, AW101. Bez samolotu STOL.
- STOL komercyjnie lata wyłącznie kat A; w trudnych warunkach kapitanowi A
  towarzyszy nieformalny mentor/obserwator z prywatną biegłością STOL (B/C/D,
  samozgłoszenie plus rejestr godzin), jako dodatkowa niepilotująca załoga.
- Kursy: HEMS dwa (lot nocny, gogle), MEDEVAC cztery (plus wciągarka, FIKI).
- MEDEVAC C+C/C+D/D+D; B+D szkoleniowo. Symulator recovery 5+5, recurrent 2 dni.

## Dalszy ciąg
Pełny plan: **PROJEKT_rozbudowy.md**. Historia zmian: **CHANGELOG.md**.

## Wznowienie
1. `cd frms-pilot-scheduler`
2. `python3 -m pytest tests/ -q`
3. `python3 scale_test.py`  (skalowalność obsady)
