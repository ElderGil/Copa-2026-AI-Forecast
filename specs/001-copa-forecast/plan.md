# Implementation Plan: Copa 2026 Forecast

**Branch**: `001-copa-forecast` | **Date**: 2026-06-17 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-copa-forecast/spec.md`

## Summary

Build a reproducible forecasting project for the FIFA World Cup 2026. Official
FIFA data is the source of truth for competition state. The forecasting layer
prioritizes recent football evidence, calibrated match probabilities, faithful
tournament simulation, and a static public one-page for daily prediction
updates. The implementation starts as a modular Python pipeline with official
FIFA ETL, versioned data files, explicit contracts, temporal feature generation,
baseline and ensemble models, calibration reports, Monte Carlo tournament
simulation, and GitHub Pages-ready static output.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: MVP uses the Python standard library for deterministic
ETL, rules, simulation primitives, and static-page generation. Planned analysis
dependencies for full modeling: pandas, numpy, scikit-learn, duckdb, pyarrow,
pydantic, typer, pyyaml, httpx, matplotlib, pytest, ruff.

**Storage**: Local versioned files: raw FIFA JSON/HTML/PDF-derived extracts as
retrieved, raw secondary CSV/JSON, processed Parquet, DuckDB views for
analytical queries, and JSON/YAML metadata for forecast runs

**Testing**: pytest with unit, integration, contract, ETL fixture, leakage, and
backtest tests

**Target Platform**: Local macOS/Linux analyst environment; later deployable as
a scheduled batch job

**Project Type**: Modular Python pipeline plus static HTML site output

**Performance Goals**: Generate a complete tournament forecast with at least
10,000 Monte Carlo simulations in under 5 minutes on a typical analyst laptop

**Constraints**: Official FIFA competition state required for credible runs; no
future data leakage; no all-time aggregate as primary current-form signal; every
forecast run records FIFA source dates, feature windows, calibration status, and
simulation settings; every implementation phase must pass
`python3 scripts/verify_implementation.py`.

**Scale/Scope**: FIFA World Cup 2026 qualified/active teams, official FIFA
fixtures/results/statuses/rules, international matches in rolling 24-month
windows, historical backtests across prior windows, and local reproducible
outputs

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Official FIFA ETL Is Source Of Truth**: PASS. FIFA ETL is the first user
  story and blocks credible forecast runs.
- **Recency Before Historical Reputation**: PASS. The plan uses 24-month and
  12-month windows as primary features; long history is limited to explicit
  priors or baselines.
- **Football-Specific Evidence Pillars**: PASS. The design includes current
  form, opponent adjustment, attack, defense, importance, venue, squad context,
  and tournament path.
- **Calibrated Probabilities**: PASS. The model layer requires calibration
  reports and proper probability metrics before promotion.
- **Temporal Validation**: PASS. Evaluation uses rolling-origin/tournament-cycle
  backtests, not random splits.
- **Tournament Simulation**: PASS. Simulation follows official FIFA competition
  state as of the run date and distinguishes diagnostic rankings from title
  probability.
- **Data Lineage And Explainability**: PASS. Forecast runs persist raw FIFA
  extract references, source freshness, feature windows, model versions, and
  explanation summaries.
- **Reviewer Gate**: PASS. `docs/architecture_analysis.md` is the technical
  reviewer guide and `scripts/verify_implementation.py` is the mandatory final
  validation command.

## Project Structure

### Documentation (this feature)

```text
specs/001-copa-forecast/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── forecast-config.schema.yaml
├── checklists/
│   └── requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
src/copa_forecast/
├── __init__.py
├── cli.py
├── config.py
├── data/
│   ├── contracts.py
│   ├── ingest.py
│   ├── normalize.py
│   ├── validate.py
│   └── sources/
│       ├── __init__.py
│       └── fifa.py
├── features/
│   ├── windows.py
│   ├── pillars.py
│   └── leakage.py
├── models/
│   ├── baselines.py
│   ├── match_model.py
│   ├── calibration.py
│   └── evaluation.py
├── simulation/
│   ├── rules.py
│   ├── monte_carlo.py
│   └── standings.py
├── reporting/
│   ├── explanations.py
│   └── artifacts.py
└── site/
    └── static_page.py

configs/
├── example.forecast.json
└── source_registry.yaml

data/
├── raw/
│   └── fifa/
├── interim/
└── processed/

tests/
├── contract/
├── fixtures/
├── integration/
└── unit/
```

**Structure Decision**: Use one Python package with separate modules rather than
separate services in the MVP. The pipeline is modular enough to split later, but
GitHub Pages publication does not need a backend service.

## Complexity Tracking

No constitution violations require justification.
