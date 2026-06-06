# Copyright 2026 Maciej M. Kasperek ("vonKrappitz")
# SPDX-License-Identifier: Apache-2.0
"""
Liczniki nalotu (blok 2).

Pilot: nalot miesięczny, nalot z misji, nalot całkowity (logbook + misje), nalot
per klasa, godziny symulatora. Maszyna: liczniki progowe (z bloku 1) plus
chronologiczny log lotów.

Logbook (`Pilot.nalot_logbook_h`) to lump historyczny bez przypisania do klasy,
więc wchodzi tylko do nalotu całkowitego, nie do rozbicia per klasa. Sesje
symulatorowe nie liczą się jako nalot operacyjny (osobny licznik).

Zależności: `frms.models`, `frms.rdzen`, oraz `frms.rejestr` (reużycie
`nalot_maszyny`, bez powielania logiki progów).
"""

from datetime import date

from frms.models import KlasaMaszyny, Pilot
from frms.rdzen import Rdzen


# ----------------------------------------------------------------------
# Liczniki pilota
# ----------------------------------------------------------------------
def nalot_miesiac(pilot: Pilot, rok: int, miesiac: int) -> float:
    """Godziny misji operacyjnych w danym miesiącu kalendarzowym (bez symulatora)."""
    return round(sum(
        m.czas_trwania_h for m in pilot.historia_misji
        if not m.czy_symulator and m.data.year == rok and m.data.month == miesiac
    ), 1)


def nalot_misji(pilot: Pilot) -> float:
    """Suma godzin wszystkich misji operacyjnych w historii (bez symulatora)."""
    return round(sum(m.czas_trwania_h for m in pilot.historia_misji if not m.czy_symulator), 1)


def nalot_per_klasa(pilot: Pilot) -> dict[KlasaMaszyny, float]:
    """Godziny misji operacyjnych w rozbiciu na klasy maszyn (logbook nie wchodzi)."""
    out: dict[KlasaMaszyny, float] = {}
    for m in pilot.historia_misji:
        if m.czy_symulator:
            continue
        out[m.klasa_maszyny] = round(out.get(m.klasa_maszyny, 0.0) + m.czas_trwania_h, 1)
    return out


def nalot_calkowity(pilot: Pilot) -> float:
    """Nalot całkowity: logbook historyczny plus nalot z misji operacyjnych."""
    return round(pilot.nalot_logbook_h + nalot_misji(pilot), 1)


def godziny_symulatora(pilot: Pilot) -> float:
    """Suma godzin sesji symulatorowych (nie liczy się do nalotu operacyjnego)."""
    return round(sum(s.czas_trwania_h for s in pilot.historia_sesji_symulatorowych), 1)


def liczniki_pilota(pilot: Pilot, dzien: date) -> dict:
    """Komplet liczników pilota gotowy do eksportu (miesiąc bieżący = miesiąc dnia)."""
    return {
        "id": pilot.id,
        "nalot_logbook_h": round(pilot.nalot_logbook_h, 1),
        "nalot_misji_h": nalot_misji(pilot),
        "nalot_calkowity_h": nalot_calkowity(pilot),
        "nalot_miesiac_h": nalot_miesiac(pilot, dzien.year, dzien.month),
        "nalot_per_klasa_h": {k.value: v for k, v in nalot_per_klasa(pilot).items()},
        "godziny_symulatora_h": godziny_symulatora(pilot),
    }


# ----------------------------------------------------------------------
# Liczniki maszyny (domknięcie loga lotów nad blokiem 1)
# ----------------------------------------------------------------------
def log_lotow_maszyny(rdzen: Rdzen, maszyna_id: str) -> list[dict]:
    """Chronologiczny log lotów egzemplarza: data, typ, godziny, kto (1 lub 2 pilotów).

    Misja dwuosobowa to dwa wpisy z tym samym `maszyna_id`; jedna maszyna ma
    najwyżej jeden dyżur dziennie, więc grupujemy po dacie i godziny bierzemy raz.
    """
    po_dacie: dict[date, dict] = {}
    for p in rdzen.piloci:
        for mi in p.historia_misji:
            if mi.maszyna_id != maszyna_id:
                continue
            r = po_dacie.setdefault(mi.data, {
                "data": mi.data.isoformat(),
                "typ_dyzuru": mi.typ_dyzuru.value,
                "godziny_h": mi.czas_trwania_h,
                "piloci": [],
            })
            r["piloci"].append(p.id)
    return [po_dacie[d] for d in sorted(po_dacie)]


def liczniki_maszyny(rdzen: Rdzen, maszyna_id: str):
    """Liczniki progowe maszyny (z bloku 1) plus log lotów. None, gdy brak maszyny."""
    from frms.rejestr import nalot_maszyny
    info = nalot_maszyny(rdzen, maszyna_id)
    if info is None:
        return None
    info = dict(info)
    info["log_lotow"] = log_lotow_maszyny(rdzen, maszyna_id)
    return info
