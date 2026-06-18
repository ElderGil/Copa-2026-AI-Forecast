# Copa 2026 AI Forecast

Spec-driven project for forecasting the FIFA World Cup 2026 champion with
official FIFA ETL and a recency-first football model.

The project starts from two premises:

1. Official FIFA data is the source of truth for World Cup fixtures, teams,
   groups, match status, venues, kickoff times, results, and rules.
2. All-time historical aggregates are not enough for national-team football.
   Forecasts must prioritize current team form, recent opponents, attacking and
   defensive trend, squad availability, preparation matches, matches already
   played in the tournament, and the actual tournament path.

## Spec Kit Artifacts

- Constitution: `.specify/memory/constitution.md`
- Feature spec: `specs/001-copa-forecast/spec.md`
- Plan: `specs/001-copa-forecast/plan.md`
- Research: `specs/001-copa-forecast/research.md`
- Data model: `specs/001-copa-forecast/data-model.md`
- Contract: `specs/001-copa-forecast/contracts/forecast-config.schema.yaml`
- Tasks: `specs/001-copa-forecast/tasks.md`

## Forecasting Stance

- ETL official FIFA data before any credible forecast run.
- Store raw FIFA payloads before normalization.
- Use 12- and 24-month windows as primary sporting evidence.
- Treat long history only as explicit prior, benchmark, or regularizer.
- Predict match probabilities before tournament probabilities.
- Evaluate with temporal backtests and calibration, not random splits.
- Simulate the official tournament path instead of ranking all teams in a
  synthetic round robin.
