# Spec: Model Credibility & Engineering Remediation

**Feature ID**: 002-credibility-remediation
**Status**: Complete (entregue no commit `36190f1`; validação registrada em `docs/validation.md`)
**Owner**: Elder Gil (human tech lead) + Builder/Reviewer agents
**Depends on**: `001-copa-forecast`
**Constitution**: `.specify/memory/constitution.md` (v1.1.0)

## Context

A thorough data-engineering review of the shipped `001-copa-forecast` pipeline
found that several outputs violate the project constitution and that the
published validation statistics do not validate the model that actually
generates champion probabilities. This feature remediates those gaps without
changing the Spec-Driven workflow.

## Problem statements (findings)

Each finding cites the constitution principle it breaks.

### P1 — Critical (modeling & validity)

- **F1 — The 1X2 model can never predict a draw.** `three_way_baseline` uses a
  fixed `draw_probability=0.26`; verified that the draw is the argmax in
  `0 / 200000` random matchups, so every real draw is scored as a miss.
  Violates **Principle IV** (calibrated, interpretable probabilities) and
  contradicts the README claim that draws are modeled.
- **F2 — No probability calibration is applied.** Published payload reports
  `calibration_status="not_calibrated_mvp_baseline"`; `calibration.py` only
  *measures* ECE/MCE. Violates **Principle IV**.
- **F3 — The production strength formula is not the formula the backtest
  validates.** `features/recent.py` divides decay-weighted numerators by a
  non-decayed `weighted_importance`, while `models/evaluation.py` divides by
  `weight*importance`. A two-win team computes 1.50 pts/match instead of 3.00.
  Violates **Principle V** (validation must reflect the released model).
- **F4 — Champion ranking lacks face validity.** Published run ranks Norway #4
  and Morocco #3 above France (#9), Spain (#10), Brazil (#25). Emergent from
  F1/F3 plus a cold-started local prior. Violates **Principle IV/VI**.
- **F5 — Mandated evidence pillars are not in the model.** No home-advantage
  term; `venue_context` and `squad_context` never affect strength. Violates
  **Principle III**.

### P2 — Engineering & data

- **F6 — Baseline mislabeled** as official "FIFA/Coca-Cola SUM" when it is a
  cold-started local Elo. Violates **Principle VII** (honest lineage).
- **F7 — Fragile crawler**: no User-Agent, retries, or HTTP error handling for a
  daily 48-request job. Violates "failure behavior" quality gate.
- **F8 — Scheduled run uses an unsupported `timezone:` key**; GitHub cron is
  UTC-only, so the job runs at 01:17 BRT, not the documented 04:17.
- **F9 — Team-name normalization exists but is not applied** in the join.
  Violates "team-name normalization MUST be deterministic and versioned".
- **F10 — `_merge_official_states` concatenates fixtures without dedupe.**
- **F11 — `load_recent_matches` breaks on schema drift** (`**item`).
- **F12 — `verify_implementation.py` gives false assurance**: the leakage
  "check" is a keyword grep; the CSV-BOM check passes when no CSV exists.
- **F13 — Ruff is configured but not installed nor run in CI.**
- **F14 — Backtest does not break down performance by date / competition type**
  as required by **Principle V**.
- **F15 — Crawler accepts arbitrary `file://`/local paths (SSRF/local read).**

### P3 — Cleanup & docs

- **F16 — Dead code**: `simulate_champion_distribution`/`simulate_champion_once`,
  `BaselineMatchModel`/`MatchProbability`, `evaluate_binary_probabilities`/
  `EvaluationReport`, `build_missing_pillar_report`.
- **F17 — Leakage helpers tested but not wired** into the pipeline.
- **F18 — Duplicated date/importance/status utilities** across modules.
- **F19 — Misc**: missing head-to-head group tiebreak; ad-hoc goal model;
  mismatched default strength scale (100 vs 1500); orphan asset.
- **F20–F22 — Documentation**: README overstates calibration/schedule/rules;
  `docs/validation.md` enshrines a pytest-less env; no LICENSE.

## Goals / acceptance criteria

1. The 1X2 model can output a draw as the most likely outcome for near-even
   matchups, and draw probability shrinks with rating gap (F1).
2. A calibrator (temperature scaling) is fit on the rolling-origin backtest,
   reported, and the calibrated metrics are persisted; `calibration_status`
   reflects the real method (F2).
3. `features/recent.py` and `models/evaluation.py` compute the same weighted
   average; a two-win team yields 3.0 pts/match (F3).
4. A home-advantage term derived from `venue_context` enters the match model
   (F5); face validity of the champion ranking improves (F4).
5. Crawler is hardened; cron is UTC; normalization is applied; fixtures are
   deduped; loaders tolerate schema drift; verifier checks are real; ruff runs
   in CI (F6–F15).
6. Dead code removed; leakage helpers wired; utilities de-duplicated; docs and
   LICENSE corrected (F16–F22).
7. **All existing tests keep passing**, and new tests cover F1–F3 and F9.

## Non-goals

- Replacing the local prior with a full historical global Elo (tracked as future
  work; current dataset is match-level for the 2026 field).
- A bivariate-Poisson scoreline model (group GD tiebreak stays approximate).
