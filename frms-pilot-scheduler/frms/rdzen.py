# Copyright 2026 Maciej M. Kasperek ("vonKrappitz")
# SPDX-License-Identifier: Apache-2.0
"""
Rdzeń FRMS — jedno źródło prawdy o stanie systemu.

Cienki kontener trzymający piloci, flotę, huby, konfigurację i sloty. Moduły
(serwis, centralny, telemetria) oraz warstwa io czytają i zapisują stan
wyłącznie przez akcesory tego obiektu, nigdy nie sięgając do wnętrza innego
modułu. Scheduler pozostaje czystą funkcją: `Rdzen` jedynie ją opakowuje, więc
sygnatura `generuj_harmonogram(sloty, piloci)` zostaje nietknięta.

Zależności: wyłącznie `frms.models`. Fabryka `Rdzen.domyslny` sięga leniwie po
`frms.data` (fixtures), żeby sam dataclass pozostał czysty.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from frms.models import (
    Baza, KlasaMaszyny, Konfiguracja, Maszyna, Pilot, SlotDyzurowy,
    StatusMaszyny,
)


@dataclass
class Rdzen:
    """Stan systemu w jednym miejscu. Akcesory są jedyną drogą modułów do niego."""

    piloci: list[Pilot] = field(default_factory=list)
    flota: list[Maszyna] = field(default_factory=list)
    huby: list[Baza] = field(default_factory=list)
    konfiguracja: Konfiguracja = field(default_factory=Konfiguracja)
    sloty: list[SlotDyzurowy] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Akcesory odczytu — moduły czytają stan TYLKO tędy
    # ------------------------------------------------------------------
    def pilot(self, pilot_id: str) -> Optional[Pilot]:
        """Pilot po ID albo None."""
        return next((p for p in self.piloci if p.id == pilot_id), None)

    def maszyna(self, maszyna_id: str) -> Optional[Maszyna]:
        """Egzemplarz maszyny po kodzie (np. „H1") albo None."""
        return next((m for m in self.flota if m.id == maszyna_id), None)

    def hub(self, hub_id: str) -> Optional[Baza]:
        """Hub (CRL) po kodzie ICAO albo None."""
        return next((b for b in self.huby if b.id == hub_id), None)

    def maszyny_klasy(self, klasa: KlasaMaszyny, tylko_operacyjne: bool = True) -> list[Maszyna]:
        """Egzemplarze danej klasy; domyślnie tylko operacyjne (bez rezerw)."""
        wynik = [m for m in self.flota if m.klasa == klasa]
        if tylko_operacyjne:
            wynik = [m for m in wynik if m.status == StatusMaszyny.OPERACYJNA]
        return wynik

    def maszyny_huba(self, hub_id: str) -> list[Maszyna]:
        """Maszyny aktualnie przydzielone do danego huba."""
        return [m for m in self.flota if m.aktualny_hub == hub_id]

    def piloci_huba(self, hub_id: str) -> list[Pilot]:
        """Piloci przypisani do danego huba (baza macierzysta)."""
        return [p for p in self.piloci if p.baza_macierzysta == hub_id]

    # ------------------------------------------------------------------
    # Akcesory zapisu — moduły mutują stan TYLKO tędy
    # ------------------------------------------------------------------
    def przydziel_maszyne_do_huba(self, maszyna_id: str, hub_id: str) -> bool:
        """Przenosi egzemplarz do innego huba. Zwraca False, gdy brak maszyny."""
        m = self.maszyna(maszyna_id)
        if m is None:
            return False
        m.aktualny_hub = hub_id
        return True

    def przydziel_pilota_do_huba(self, pilot_id: str, hub_id: str) -> bool:
        """Przenosi pilota do innego huba. Zwraca False, gdy brak pilota."""
        p = self.pilot(pilot_id)
        if p is None:
            return False
        p.baza_macierzysta = hub_id
        return True

    def ustaw_serwis_maszyny(self, maszyna_id: str, do_dnia: Optional[date], miejsce: Optional[str]) -> bool:
        """Wyłącza maszynę na czas serwisu.

        Pełne pola serwisowe Maszyny (`w_serwisie_do`, `lokalizacja_serwisu`)
        dochodzą w bloku 3. Na razie akcesor istnieje jako kontrakt, na którym
        moduł serwisu może się oprzeć już teraz, a blok 3 wymieni tylko jego
        wnętrze, nie sygnaturę.
        """
        m = self.maszyna(maszyna_id)
        if m is None:
            return False
        setattr(m, "w_serwisie_do", do_dnia)
        setattr(m, "lokalizacja_serwisu", miejsce)
        return True

    def dodaj_slot(self, slot: SlotDyzurowy) -> None:
        """Dokłada slot do stanu."""
        self.sloty.append(slot)

    def dodaj_pilota(self, p: Pilot) -> None:
        """Dokłada pilota do stanu."""
        self.piloci.append(p)

    def usun_pilota(self, pilot_id: str) -> bool:
        """Usuwa pilota po ID. Zwraca False, gdy brak takiego pilota."""
        p = self.pilot(pilot_id)
        if p is None:
            return False
        self.piloci.remove(p)
        return True

    # ------------------------------------------------------------------
    # Wygoda — opakowanie czystej logiki schedulera
    # ------------------------------------------------------------------
    def harmonogram(self) -> tuple[list[SlotDyzurowy], list[SlotDyzurowy]]:
        """Generuje harmonogram dla bieżących slotów i pilotów (obsadzone, nieobsadzone)."""
        from frms.scheduler import generuj_harmonogram
        return generuj_harmonogram(self.sloty, self.piloci)

    @classmethod
    def domyslny(cls, dzien_ref: date) -> "Rdzen":
        """Buduje rdzeń z domyślnych fixtures (`frms.data`).

        Import leniwy, żeby sam dataclass nie zależał od fixtures na poziomie
        modułu. Sygnatury `generuj_pilotow` i `generuj_sloty` bez zmian.
        """
        from frms import data
        return cls(
            piloci=data.generuj_pilotow(dzien_ref),
            flota=list(data.FLOTA),
            huby=list(data.BAZY),
            konfiguracja=Konfiguracja(),
            sloty=data.generuj_sloty(dzien_ref),
        )
