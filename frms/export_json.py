# Copyright 2026 Maciej M. Kasperek ("vonKrappitz")
# SPDX-License-Identifier: Apache-2.0
"""
Generator danych do interfejsu webowego FRMS.

Eksportuje aktualny stan aplikacji (piloci, bazy, sloty z przydzielonymi
egzemplarzami, alerty, sesje symulatorowe, liczniki nalotu) do struktury JSON
gotowej do osadzenia w pliku index.html.

Model M2: jedno źródło prawdy. Cały eksport liczy się z pojedynczego Rdzen po
harmonogramie i przydziale maszyn — piloci, sloty, statystyki i liczniki dotyczą
tej samej populacji, więc nic się nie rozjeżdża.

Hardening: stały seed daje powtarzalne wyjście; każde liczenie per rekord jest
w osłonie, żeby jeden felerny pilot lub egzemplarz nie wywrócił całego eksportu.
"""

import json
import random
import copy
from datetime import date, timedelta

from frms.rdzen import Rdzen
from frms.scheduler import generuj_sloty_symulatorowe
from frms.symulator import zaplanuj_symulator
from frms.law import grafik_law, HORYZONT_LAW_DNI
from frms.zamiana import kandydaci_zamiany, kandydaci_szkoleniowi, kandydaci_obserwatora_stol
from frms.models import KlasaMaszyny
from frms.kursy import przypisz_kursy_domyslne, przypisz_dni_wolne, brakujace_kursy
from frms.stol import przypisz_stol_prywatny, stol_biegly_prywatnie
from frms.awanse import kwalifikuje_sie_do_awansu, przypisz_wspolne_loty_demo
from frms.prognoza_serwis import prognoza_floty
from frms.telemetria import MockTelemetry, WSPOLRZEDNE_BAZ
from frms.centralny import snapshot_floty
from frms.siec import siec_json
from frms.plan import plan_dni
from frms.data import BAZY, generuj_pilotow
from frms.rejestr import przydziel_maszyny, obciazenie_floty
from frms.liczniki import liczniki_pilota, liczniki_maszyny
from frms.validator import alerty_type_rating, alerty_przeciazenia
from frms.currency import (
    wymaga_currency_recovery, wymaga_recurrent_kwartalny, opis_powodu_sesji,
    priorytet_recovery, dni_do_terminu_recovery,
)
from frms.models import Organizacja, Kategoria


SEED_EKSPORTU = 2026  # stały seed: powtarzalne wyjście demo (hardening: deterministyczne dane)


def _bezpiecznie(fn, default):
    """Wywołuje fn(); przy dowolnym wyjątku zwraca default i nie wywraca eksportu."""
    try:
        return fn()
    except Exception:
        return default


def eksport_do_json():
    """Eksportuje pełen stan aplikacji do struktury JSON (jedno źródło prawdy)."""
    dzien = date.today()
    random.seed(SEED_EKSPORTU)

    # Jedno źródło prawdy: jeden rdzeń, jeden harmonogram, jeden przydział maszyn.
    rdzen = Rdzen.domyslny(dzien)
    obsadzone, nieobsadzone = _bezpiecznie(lambda: rdzen.harmonogram(), ([], []))
    wynik_maszyn = _bezpiecznie(lambda: przydziel_maszyny(rdzen),
                                {"przydzielone": 0, "sprowadzone": 0, "bez_maszyny": []})
    piloci = rdzen.piloci
    sloty_op = rdzen.sloty
    pilot_dict = {p.id: p for p in piloci}
    # Blok 5: kursy i dni wolne (po harmonogramie — rdzeń ich nie używa).
    _bezpiecznie(lambda: przypisz_kursy_domyslne(piloci), None)
    _bezpiecznie(lambda: przypisz_stol_prywatny(piloci, dzien), None)
    _bezpiecznie(lambda: przypisz_dni_wolne(piloci, dzien), None)

    # Sesje symulatorowe wyznaczamy z currency PRZED dopisaniem sesji do historii
    # (inaczej recurrent zresetowałby własny licznik). Potem dopisujemy je do
    # historii, żeby licznik godzin symulatora miał z czego liczyć.
    sesje_sym_json = []
    for p in piloci:
        for tr in p.type_ratings:
            if not _bezpiecznie(lambda tr=tr: tr.jest_aktualny(dzien), False):
                continue
            klasa = tr.klasa
            if _bezpiecznie(lambda: wymaga_recurrent_kwartalny(p, klasa, dzien), False):
                sesje_sym_json.append({
                    "pilot_id": p.id, "pilot_imie": p.imie, "pilot_nazwisko": p.nazwisko,
                    "pilot_kategoria": p.kategoria.value, "klasa": klasa.value,
                    "typ_sesji": "RECURRENT", "dni_trwania": 2, "godziny": 12,
                    "powod": _bezpiecznie(lambda: opis_powodu_sesji(p, klasa, dzien), ""),
                    "powod_en": _bezpiecznie(lambda: opis_powodu_sesji(p, klasa, dzien, "en"), ""),
                })
            elif _bezpiecznie(lambda: wymaga_currency_recovery(p, klasa, dzien), False):
                sesje_sym_json.append({
                    "pilot_id": p.id, "pilot_imie": p.imie, "pilot_nazwisko": p.nazwisko,
                    "pilot_kategoria": p.kategoria.value, "klasa": klasa.value,
                    "typ_sesji": "RECOVERY", "dni_trwania": 1, "godziny": 6,
                    "priorytet": _bezpiecznie(lambda kl=klasa: priorytet_recovery(kl), "WYSOKI"),
                    "dni_do_terminu": _bezpiecznie(lambda kl=klasa: dni_do_terminu_recovery(p, kl, dzien), None),
                    "powod": _bezpiecznie(lambda: opis_powodu_sesji(p, klasa, dzien), ""),
                    "powod_en": _bezpiecznie(lambda: opis_powodu_sesji(p, klasa, dzien, "en"), ""),
                })

    # Pojemność symulatora EPDE (blok 4): liczona na kopii pilotów PRZED dopisaniem
    # sesji do historii, inaczej reguła „raz na kwartał" wyzerowałaby zapotrzebowanie.
    piloci_sym = copy.deepcopy(piloci)
    sloty_sym, nieob_sym = _bezpiecznie(lambda: zaplanuj_symulator(piloci_sym, dzien), ([], []))

    # Dopisanie sesji symulatorowych do historii pilotów (zasila licznik godzin).
    _bezpiecznie(lambda: generuj_sloty_symulatorowe(piloci, dzien, dni=7), [])

    # Alerty z tej samej populacji.
    alerty_tr = _bezpiecznie(lambda: alerty_type_rating(piloci, dzien), [])
    alerty_prz = _bezpiecznie(lambda: alerty_przeciazenia(piloci, dzien), [])

    # ============================================================
    # BAZY
    # ============================================================
    bazy_json = [{
        "id": b.id, "nazwa": b.nazwa, "typ": b.typ,
        "klasy_maszyn": [k.value for k in b.klasy_maszyn],
        "organizacja": b.organizacja.value,
    } for b in BAZY]

    # ============================================================
    # PILOCI (ta sama populacja, po harmonogramie)
    # ============================================================
    piloci_json = []
    for p in piloci:
        type_ratings_lista = []
        for tr in p.type_ratings:
            type_ratings_lista.append({
                "klasa": tr.klasa.value,
                "data_uzyskania": tr.data_uzyskania.isoformat(),
                "data_ostatniego_lotu": tr.data_ostatniego_lotu.isoformat(),
                "data_waznosci": tr.data_waznosci.isoformat(),
                "dni_od_ostatniego_lotu": _bezpiecznie(lambda tr=tr: tr.dni_od_ostatniego_lotu(dzien), None),
                "dni_do_wygasniecia": _bezpiecznie(lambda tr=tr: tr.dni_do_wygasniecia(dzien), None),
                "jest_aktualny": _bezpiecznie(lambda tr=tr: tr.jest_aktualny(dzien), False),
                "wymaga_alertu": _bezpiecznie(lambda tr=tr: tr.wymaga_alertu(dzien), False),
            })
        piloci_json.append({
            "id": p.id, "imie": p.imie, "nazwisko": p.nazwisko,
            "kategoria": p.kategoria.value, "baza_macierzysta": p.baza_macierzysta,
            "organizacja": p.organizacja.value, "type_ratings": type_ratings_lista,
            "obciazenie_96h": _bezpiecznie(lambda: p.obciazenie_96h(dzien), 0.0),
            "godziny_od_dyzuru_24h": _bezpiecznie(lambda: p.godziny_od_ostatniego_dyzuru_24h(dzien), None),
            "gotowy_do_dyzuru": _bezpiecznie(lambda: p.gotowy_do_dyzuru_24h(dzien), True),
            "przeciazony": _bezpiecznie(lambda: p.przeciazony(dzien), False),
            "liczba_misji_w_historii": len(p.historia_misji),
            "kursy": [k.value for k in p.kursy],
            "liczba_dni_wolnych": len(p.dni_wolne),
            "stol_prywatnie": p.stol_prywatnie,
            "stol_biegly": _bezpiecznie(lambda: stol_biegly_prywatnie(p, dzien), False),
        })

    # ============================================================
    # HARMONOGRAM (sloty + przydzielony egzemplarz z bloku 1)
    # ============================================================
    sloty_json = []
    for s in obsadzone + nieobsadzone:
        pic = pilot_dict.get(s.przypisany_pilot_id) if s.przypisany_pilot_id else None
        fo = pilot_dict.get(s.drugi_pilot_id) if s.drugi_pilot_id else None
        instruktor = pilot_dict.get(s.instruktor_id) if s.instruktor_id else None
        sloty_json.append({
            "id": s.id, "baza_id": s.baza_id, "data": s.data.isoformat(),
            "dzien_tygodnia": s.data.strftime("%A"), "typ_dyzuru": s.typ_dyzuru.value,
            "wymagana_klasa": s.wymagana_klasa.value,
            "wymagana_kategoria_min": s.wymagana_kategoria_min.value,
            "tryb_misji": s.tryb_misji.value,
            "obsadzony": _bezpiecznie(lambda: s.jest_obsadzony(), False),
            "maszyna_id": s.maszyna_id,
            "maszyna_z_innej_bazy": s.maszyna_z_innej_bazy,
            "pic": {"id": pic.id, "imie": pic.imie, "nazwisko": pic.nazwisko, "kategoria": pic.kategoria.value} if pic else None,
            "fo": {"id": fo.id, "imie": fo.imie, "nazwisko": fo.nazwisko, "kategoria": fo.kategoria.value} if fo else None,
            "instruktor": {"id": instruktor.id, "imie": instruktor.imie, "nazwisko": instruktor.nazwisko, "kategoria": instruktor.kategoria.value} if instruktor else None,
        })

    # ============================================================
    # ALERTY
    # ============================================================
    alerty_json = []
    for alert in alerty_tr:
        alerty_json.append({
            "typ": "type_rating", "priorytet": alert.get("priorytet", "ŚREDNI"),
            "pilot_id": alert.get("pilot_id"), "imie_nazwisko": alert.get("imie_nazwisko"),
            "pilot_kategoria": alert.get("kategoria"), "klasa": alert.get("klasa"),
            "powod": alert.get("powod", ""),
        })
    for alert in alerty_prz:
        alerty_json.append({
            "typ": "przeciazenie", "priorytet": alert.get("priorytet", "WYSOKI"),
            "pilot_id": alert.get("pilot_id"), "imie_nazwisko": alert.get("imie_nazwisko"),
            "wartosc": alert.get("wartosc", ""),
        })

    # ============================================================
    # LICZNIKI (blok 2) — z tego samego rdzenia
    # ============================================================
    liczniki_pilotow = []
    for p in piloci:
        L = _bezpiecznie(lambda p=p: liczniki_pilota(p, dzien), None)
        if L is not None:
            liczniki_pilotow.append(L)

    ob_floty = _bezpiecznie(lambda: obciazenie_floty(rdzen), {})
    liczniki_maszyn = []
    for m in rdzen.flota:
        info = _bezpiecznie(lambda m=m: liczniki_maszyny(rdzen, m.id), None)
        if info and info.get("liczba_dyzurow", 0) > 0:
            liczniki_maszyn.append(info)

    # ============================================================
    # STATYSTYKI
    # ============================================================
    liczba_recurrent = sum(1 for s in sesje_sym_json if s["typ_sesji"] == "RECURRENT")
    liczba_recovery = sum(1 for s in sesje_sym_json if s["typ_sesji"] == "RECOVERY")
    godziny_sym = sum(s["godziny"] for s in sesje_sym_json)
    maszyn_uzytych = sum(1 for v in ob_floty.values() if v.get("liczba_dyzurow", 0) > 0)

    statystyki_json = {
        "data_raportu": dzien.isoformat(),
        "tydzien_od": dzien.isoformat(),
        "tydzien_do": (dzien + timedelta(days=6)).isoformat(),
        "liczba_pilotow": len(piloci),
        "rozklad_kategorii": {
            "A": sum(1 for p in piloci if p.kategoria == Kategoria.A),
            "B": sum(1 for p in piloci if p.kategoria == Kategoria.B),
            "C": sum(1 for p in piloci if p.kategoria == Kategoria.C),
            "D": sum(1 for p in piloci if p.kategoria == Kategoria.D),
        },
        "liczba_baz": len(BAZY),
        "liczba_baz_lpr_operacyjnych": sum(1 for b in BAZY if b.organizacja == Organizacja.LPR and b.typ != "SZKOLENIOWA"),
        "liczba_slotow_operacyjnych": len(sloty_op),
        "liczba_slotow_obsadzonych": len(obsadzone),
        "liczba_slotow_nieobsadzonych": len(nieobsadzone),
        "procent_obsadzenia": round(100 * len(obsadzone) / len(sloty_op), 1) if sloty_op else 0,
        "liczba_alertow_tr": len(alerty_tr),
        "liczba_alertow_przeciazen": len(alerty_prz),
        "liczba_sesji_sym": len(sesje_sym_json),
        "liczba_recurrent": liczba_recurrent,
        "liczba_recovery": liczba_recovery,
        "godziny_sym_tygodniowo": godziny_sym,
        "liczba_maszyn": len(rdzen.flota),
        "liczba_maszyn_uzytych": maszyn_uzytych,
        "liczba_maszyn_przydzielonych": wynik_maszyn.get("przydzielone", 0),
        "liczba_maszyn_sprowadzonych": wynik_maszyn.get("sprowadzone", 0),
        "liczba_slotow_bez_maszyny": len(wynik_maszyn.get("bez_maszyny", [])),
    }

    # ============================================================
    # SYMULATOR EPDE (blok 4): obłożenie per dzień + przepełnienie
    # ============================================================
    sym_wg_dnia = {}
    for s in sloty_sym:
        p = pilot_dict.get(s.przypisany_pilot_id)
        etykieta = f"{p.imie} {p.nazwisko}".strip() if p else s.przypisany_pilot_id
        wpis = {
            "klasa": s.wymagana_klasa.value,
            "pilot_id": s.przypisany_pilot_id,
            "pilot": etykieta,
            "kategoria": s.wymagana_kategoria_min.value,
        }
        sym_wg_dnia.setdefault(s.data.isoformat(), []).append(wpis)
    oblozenie_sym = [{"data": d, "wpisy": sym_wg_dnia[d]} for d in sorted(sym_wg_dnia)]

    nieobsadzone_sym = [{
        "pilot_id": z.pilot_id, "klasa": z.klasa.value, "typ": z.typ,
        "okno_od": z.okno_od.isoformat(), "okno_do": z.okno_do.isoformat(),
        "opis": z.opis,
    } for z in nieob_sym]

    symulator_epde_json = {
        "oblozenie": oblozenie_sym,
        "nieobsadzone": nieobsadzone_sym,
        "liczba_slotow": len(sloty_sym),
        "liczba_dni": len(oblozenie_sym),
        "liczba_nieobsadzonych": len(nieob_sym),
        "pojemnosc_na_klase_dzien": 1,
    }

    # ============================================================
    # GRAFIK LAW (moduł EPDE): treningi na dziś i kolejne 14 dni
    # ============================================================
    grafik = _bezpiecznie(lambda: grafik_law(piloci_sym, dzien, HORYZONT_LAW_DNI), [])
    law_wg_dnia = {}
    for w in grafik:
        p = pilot_dict.get(w.pilot_id)
        etykieta = f"{p.imie} {p.nazwisko}".strip() if p else w.pilot_id
        law_wg_dnia.setdefault(w.data.isoformat(), []).append({
            "pilot_id": w.pilot_id,
            "pilot": etykieta,
            "kategoria": p.kategoria.value if p else "",
            "klasa": w.klasa.value,
            "typ": w.typ,
            "nalot_na_modelu_h": w.nalot_na_modelu_h,
            "starty_wymagane": w.starty_wymagane,
            "termin": w.termin.isoformat() if w.termin else None,
        })
    law_grafik_json = []
    for i in range(HORYZONT_LAW_DNI):
        d = dzien + timedelta(days=i)
        klucz = d.isoformat()
        law_grafik_json.append({
            "data": klucz,
            "dzien_tygodnia": d.strftime("%A"),
            "sesje": law_wg_dnia.get(klucz, []),
        })

    # ============================================================
    # PLAN 15 DNI (blok 4/7): osobna, zasiana populacja → determinizm,
    # niezależnie od tygodniowych mutacji harmonogramu.
    # ============================================================
    random.seed(SEED_EKSPORTU)
    piloci_plan = generuj_pilotow(dzien)
    plan = _bezpiecznie(lambda: plan_dni(piloci_plan, dzien, dni=15), [])
    # kursy i dni wolne dla populacji planu (po przydziale) — by pule bramkowały
    _bezpiecznie(lambda: przypisz_kursy_domyslne(piloci_plan), None)
    _bezpiecznie(lambda: przypisz_stol_prywatny(piloci_plan, dzien), None)
    _bezpiecznie(lambda: przypisz_dni_wolne(piloci_plan, dzien), None)
    pdict = {p.id: p for p in piloci_plan}

    def _osoba(pid):
        q = pdict.get(pid) if pid else None
        return ({"id": q.id, "imie": q.imie, "nazwisko": q.nazwisko,
                 "kategoria": q.kategoria.value} if q else None)

    plan_json = []
    LIMIT_KAND = 20  # czołówka kandydatów na fotel (picker)

    def _pula(slot, zwalniany_id, sloty_dnia):
        if not zwalniany_id:
            return []
        kand = _bezpiecznie(lambda: kandydaci_zamiany(slot, zwalniany_id, piloci_plan, sloty_dnia), [])
        return [{"id": k.pilot.id, "szk": k.lot_szkoleniowy, "nadz": k.nadzorujacy_id}
                for k in kand[:LIMIT_KAND]]

    def _pula_szkoleniowa(slot, sloty_dnia):
        kand = _bezpiecznie(lambda: kandydaci_szkoleniowi(slot, piloci_plan, sloty_dnia), [])
        return [{"id": k.pilot.id, "nadz": k.nadzorujacy_id} for k in kand[:LIMIT_KAND]]

    def _pula_stol_trudny(slot, sloty_dnia):
        if slot.wymagana_klasa != KlasaMaszyny.STOL_SAMOLOT:
            return []
        orig = slot.trudny_lot
        slot.trudny_lot = True
        try:
            kand = _bezpiecznie(lambda: kandydaci_obserwatora_stol(slot, piloci_plan, sloty_dnia), [])
        finally:
            slot.trudny_lot = orig
        return [{"id": k.pilot.id,
                 "rola": ("mentor" if k.pilot.kategoria == Kategoria.D else "wsparcie")}
                for k in kand[:LIMIT_KAND]]

    for dp in plan:
        sl = []
        for s in dp.sloty:
            sl.append({
                "id": s.id, "baza_id": s.baza_id, "typ_dyzuru": s.typ_dyzuru.value,
                "wymagana_klasa": s.wymagana_klasa.value,
                "wymagana_kategoria_min": s.wymagana_kategoria_min.value,
                "tryb_misji": s.tryb_misji.value,
                "obsadzony": _bezpiecznie(lambda s=s: s.jest_obsadzony(), False),
                "pic": _osoba(s.przypisany_pilot_id),
                "fo": _osoba(s.drugi_pilot_id),
                "instruktor": _osoba(s.instruktor_id),
                "kandydaci_pic": _pula(s, s.przypisany_pilot_id, dp.sloty),
                "kandydaci_fo": _pula(s, s.drugi_pilot_id, dp.sloty),
                "fotel_szkoleniowy": _pula_szkoleniowa(s, dp.sloty),
                "kandydaci_stol_trudny": _pula_stol_trudny(s, dp.sloty),
            })
        plan_json.append({
            "data": dp.data.isoformat(),
            "dzien_tygodnia": dp.data.strftime("%A"),
            "sloty": sl,
            "liczba_slotow": len(sl),
            "liczba_obsadzonych": sum(1 for x in sl if x["obsadzony"]),
        })

    # ============================================================
    # ALERTY KURSÓW (blok 5): obsadzony pilot na HEMS/MEDEVAC bez kompletu kursów
    # ============================================================
    alerty_kursy_json = []
    for s in sloty_op:
        klasa = s.wymagana_klasa
        if klasa not in (KlasaMaszyny.HEMS_SREDNI, KlasaMaszyny.MEDEVAC_CIEZKI):
            continue
        for pid in (s.przypisany_pilot_id, s.drugi_pilot_id):
            p = pilot_dict.get(pid) if pid else None
            if p is None:
                continue
            brak = _bezpiecznie(lambda p=p, klasa=klasa: brakujace_kursy(p, klasa), [])
            if brak:
                alerty_kursy_json.append({
                    "slot_id": s.id, "baza_id": s.baza_id, "klasa": klasa.value,
                    "pilot_id": p.id, "imie_nazwisko": f"{p.imie} {p.nazwisko}".strip(),
                    "brakujace": [k.value for k in brak],
                })

    # ============================================================
    # AWANSE (blok 6): kandydaci z kryteriami i liczbą zatwierdzających
    # ============================================================
    piloci_awanse = copy.deepcopy(piloci)
    _bezpiecznie(lambda: przypisz_wspolne_loty_demo(piloci_awanse, dzien), None)
    awanse_json = []
    for p in piloci_awanse:
        w = _bezpiecznie(lambda p=p: kwalifikuje_sie_do_awansu(p, piloci_awanse, dzien), {"cel": None})
        if not w.get("cel"):
            continue
        w_out = {
            "pilot_id": p.id, "imie_nazwisko": f"{p.imie} {p.nazwisko}".strip(),
            "kategoria": p.kategoria.value,
        }
        w_out.update(w)
        awanse_json.append(w_out)
    awanse_json.sort(key=lambda x: (not x["kwalifikuje"], x["pilot_id"]))

    # ============================================================
    # PROGNOZA SERWISOWA (blok 9): nalot do progu, dni, wezwania priorytetowe
    # ============================================================
    serwis_prognoza_json = _bezpiecznie(
        lambda: prognoza_floty(rdzen.flota, rdzen.konfiguracja.serwis, dzien), [])
    serwis_wezwania_json = [p for p in serwis_prognoza_json
                            if p["priorytet"] in ("WYSOKI", "SREDNI") and not p["w_serwisie"]]

    # ============================================================
    # CENTRUM LIVE (blok 10): snapshot floty z telemetrii (MockTelemetry)
    # ============================================================
    def _centrum():
        tele = MockTelemetry()
        snap = snapshot_floty(rdzen.flota, tele, dzien)
        huby = sorted({m.aktualny_hub for m in rdzen.flota if m.aktualny_hub})
        snap["bazy"] = [{"id": hk, "lat": WSPOLRZEDNE_BAZ[hk][0], "lon": WSPOLRZEDNE_BAZ[hk][1]}
                        for hk in huby if hk in WSPOLRZEDNE_BAZ]
        return snap
    centrum_live_json = _bezpiecznie(_centrum, {"maszyny": [], "podsumowanie": {}, "bazy": []})

    return {
        "statystyki": statystyki_json,
        "bazy": bazy_json,
        "piloci": piloci_json,
        "sloty": sloty_json,
        "plan_15dni": plan_json,
        "alerty": alerty_json,
        "alerty_kursy": alerty_kursy_json,
        "awanse": awanse_json,
        "serwis_prognoza": serwis_prognoza_json,
        "serwis_wezwania": serwis_wezwania_json,
        "centrum_live": centrum_live_json,
        "siec_reforma": _bezpiecznie(siec_json, {"bazy": [], "sektory": []}),
        "sesje_symulatorowe": sesje_sym_json,
        "symulator_epde": symulator_epde_json,
        "law_grafik_15dni": law_grafik_json,
        "liczniki_pilotow": liczniki_pilotow,
        "liczniki_maszyn": liczniki_maszyn,
        "obciazenie_floty": ob_floty,
    }


if __name__ == "__main__":
    dane = eksport_do_json()
    print(json.dumps(dane, ensure_ascii=False, indent=2))
