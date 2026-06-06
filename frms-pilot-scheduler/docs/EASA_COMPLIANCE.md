# EASA compliance

This document maps the checks implemented by FRMS Pilot Scheduler to the
relevant European rules and EU working-time law. Code identifiers are kept in
Polish to match the names referenced in the associated study.

## AMC1 ORO.FTL.110 — Fatigue Risk Management System

**Requirement:** an air operator must run a Fatigue Risk Management System
(FRMS) as part of its Safety Management System.

| Requirement (AMC1 ORO.FTL.110) | Implementation |
|---|---|
| Minimum 12 h rest after a standard duty | `gotowy_do_dyzuru_24h()` |
| Minimum 48 h after a 24-hour duty | `godziny_od_ostatniego_dyzuru_24h() >= 48` |
| Maximum 60 h of work over 7 days | `przeciazony()` |
| Continuous monitoring of the rolling 96-hour load | `obciazenie_96h()` |
| Recording of the duty type | `Misja.typ_dyzuru` |

## GM1 ORO.FTL.120 — implementation guidance

Required elements of the supporting information system:

1. Recording of each crew member's working time — `historia_misji`
2. Continuous load monitoring — `obciazenie_96h`
3. Threshold alerts — `alerty_przeciazenia`
4. Retrospective audit — requires persistent storage in production
5. Periodic compliance reports — requires a reporting module in production

## Part-FCL (Regulation (EU) No 1178/2011, Annex I)

**Type-rating recency:**
- validity from the last recurrent training,
- a 90-day operational-recency window for full currency,
- after 90 days without a flight, a check ride or refresher is required.

```python
def jest_aktualny(self, dzien_referencyjny: date) -> bool:
    return (
        self.dni_do_wygasniecia(dzien_referencyjny) > 0
        and self.dni_od_ostatniego_lotu(dzien_referencyjny) <= 90
    )
```

The selection algorithm rejects candidates whose type rating is not current.
This prevents a rating from lapsing during duty and avoids the cost of a
recurrent course or a full type-rating renewal.

## Directive 2003/88/EC — organisation of working time

- maximum weekly working time of 48 h, with a derogation to 60 h for certain
  groups,
- minimum 11 h of uninterrupted rest in each 24-hour period,
- minimum 35 h of uninterrupted weekly rest.

**Implementation:** the validator `przeciazony()` enforces the 60 h / 7 days
ceiling.

## Common HEMS operating standards

EU common operating standards for helicopter emergency medical service (HEMS)
require operational flight-time records that the competent national authority
can audit. The FRMS is the tool that supplies those records.

---

These mappings show which regulatory requirement each function addresses.
A full production deployment additionally needs persistent storage, an audit
trail and periodic reporting. See `ARCHITECTURE.md`.
