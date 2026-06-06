# FRMS Pilot Scheduler

**Language:** English | [Polski](README.pl.md)

A Python proof-of-concept of a **fatigue risk management system (FRMS)** for rostering helicopter emergency medical service (HEMS) / medical-evacuation (MEDEVAC) pilots across a multi-tier fleet. The tool assigns pilots to duty slots while keeping each pilot's type-rating currency valid, respecting a cumulative-duty-load limit, and rotating the pool so that no rating lapses.

Licensed under the Apache License, Version 2.0.

---

## What it does

The fleet is multi-type, and a single pilot may hold ratings on more than one aircraft class. Coordinating such a roster by hand is error-prone once the workforce grows. This tool demonstrates that the task can be steered computationally.

For every pilot it tracks three variables continuously:

1. **Type-rating validity** on each aircraft class, with an alert before the 90-day recency window expires.
2. **Cumulative duty load** over the last 96 hours (counting missions, flight length and severity).
3. **Position in the rotation cycle**.

On that basis it assigns pilots to duty slots so as to fill every shift within the available categories, while preventing both the overload of any one pilot and a prolonged break on any one type. The fatigue indicator enters as a **hard rule**: a pilot above the cumulative-duty-load threshold is not placed in a slot, even with a valid rating.

Pilots are organised into a four-tier categorisation (**A–D**) defined against European flight-crew licensing and recency rules. The categories are built so that no pilot exceeds the legal limit on type combinations.

## Status

This is a **proof of concept, not a production system**. It exists to show the feasibility of computational oversight of a multi-type pilot roster of realistic size. It is released for transparency and reproducibility alongside the associated research (see *Associated work* below).

## Associated work

This repository is the reference implementation of the FRMS described in a study on **crew resources and fatigue management in air rescue (HEMS)**, currently under peer review. The full citation will be added here once the study is published.

## Repository layout

```
frms/                FRMS package (scheduling logic and validator)
tests/               unit tests confirming the assignment rules
examples/            small runnable examples
docs/                documentation
scale_test.py        scalability benchmark (see "Reproducing the results")
requirements.txt     Python dependencies
CHANGELOG.md         change history
LICENSE / NOTICE     Apache-2.0 licence and notices
```

The two public entry points referenced in the paper are `generuj_harmonogram` (schedule generation) and the schedule validator. `scale_test.py` reuses both unchanged.

## Requirements

- Python 3.10 or newer
- Dependencies listed in `requirements.txt`

## Installation

```bash
git clone https://github.com/vonKrappitz/frms-pilot-scheduler.git
cd frms-pilot-scheduler
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

Run the bundled example:

```bash
python -m examples.demo          # or: python examples/demo.py
```

Run the unit tests:

```bash
python -m pytest                 # or: python -m unittest
```

## Reproducing the results reported in the associated paper

The scalability claim is reproduced with a single command:

```bash
python scale_test.py
```

`scale_test.py` reuses `generuj_harmonogram` and the validator without modifying them, and scales the synthetic workforce. Expected behaviour:

- At **182 pilots and 772 weekly slots**, a schedule is produced in **under one second**.
- About **92 per cent** of slots are filled; overload alerts are **near zero**.
- Staffing holds at **92–94 per cent** regardless of scale (about 95.7 per cent at 33 pilots, about 93.3 per cent at 182).
- Runtime grows roughly with the square of the workforce size (about O(n²)).

Exact figures may vary slightly with the random seed and the host machine, but the orders of magnitude above should hold.

## How to cite

**Software:**

> M. Kasperek, *FRMS Pilot Scheduler* (Python software), Apache-2.0. GitHub: https://github.com/vonKrappitz/frms-pilot-scheduler. Zenodo DOI: *(to be added after the first release is archived)*.

The citation for the associated study will be added once it is published.

## License

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).

## Author

Maciej Kasperek — GitHub [@vonKrappitz](https://github.com/vonKrappitz) · ORCID [0009-0008-7419-0851](https://orcid.org/0009-0008-7419-0851)
