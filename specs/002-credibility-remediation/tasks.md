# Tasks: Model Credibility & Engineering Remediation

**Input**: `specs/002-credibility-remediation/{spec.md,plan.md}`
**Tests**: New tests required for F1 (draw argmax), F3 (weighted-average parity),
F9 (normalized join). All existing tests MUST stay green.

Legend: `[ ]` pending · `[x]` done · `[~]` partial/deferred-with-note.

## Phase R1: Shared foundations

- [x] R001 Add `src/copa_forecast/timeutils.py` with `add_months`/`days_in_month`
- [x] R002 Add `COMPLETED_STATUSES` to `data/contracts.py` and reuse it
- [x] R003 [P] Add `LICENSE` (MIT)

## Phase R2: Critical modeling (P1)

- [x] R010 [F1][F5] Dynamic draw + `home_advantage` in `models/baselines.py`
- [x] R011 [F1] Unit test: draw is argmax for level matchup (`test_model_baselines.py`)
- [x] R012 [F3] Fix weighted-average denominator in `features/recent.py`
- [x] R013 [F3] Unit test: two wins → 3.0 pts/match (`test_recent_features.py`)
- [x] R014 [F9] Normalize team-name join in `features/recent.py`
- [x] R015 [F9] Unit test: localized name variant still joins
- [x] R016 [F2] `fit_temperature`/`apply_temperature` in `models/calibration.py`
- [x] R017 [F2][F5][F14] Backtest: home-advantage from `venue_context`,
      temperature fit + calibrated metrics, per-competition/per-window slices
- [x] R018 [F2][F4] Forecast: consume fitted temperature (stable
      `data/processed/calibration/temperature.json`), honest `calibration_status`

## Phase R3: Engineering & data (P2)

- [x] R030 [F7][F15] Harden crawler (UA, retries, HTTP errors, scheme allow-list)
- [x] R031 [F10] Dedupe fixtures in `_merge_official_states`
- [x] R032 [F11] Tolerant `load_recent_matches`
- [x] R033 [F12] Functional leakage probe + fixed stub check in `verify_implementation.py`
- [x] R034 [F8] UTC cron in `daily-forecast.yml`
- [x] R035 [F13] Add `ruff` to dev deps + CI lint/test step + `ignore=["E501"]`
- [x] R036 [F6] Honest baseline naming in README validation block

## Phase R4: Cleanup & docs (P3)

- [x] R040 [F16] Remove dead code (champion sampling, evaluate_binary_probabilities,
      build_missing_pillar_report); `BaselineMatchModel` kept + refreshed as the
      public match interface (listed as required module by the quality gate)
- [x] R041 [F17] Wire `assert_no_future_records` into the recent-match ETL output
- [x] R042 [F18] Route date helpers through `timeutils`
- [~] R043 [F19] Default strength scale fixed (→1500); orphan asset removed;
      head-to-head comparator implemented + unit-tested and applied to group-table
      ranking. Deferred: propagation through the fixed-bracket builder in
      `rules.py` (it re-ranks on overall criteria; fair-play / drawing of lots
      remain unmodeled). Goal scoreline model stays approximate per non-goals.
- [x] R044 [F20][F21][F22] Correct README + `docs/validation.md`; LICENSE added
- [x] R045 Run full suite + record validation output (53 pass, ruff clean,
      quality gate SUCCESS)

## Dependencies

- R001/R002 precede R042/R043.
- R010 precedes R011; R012 precedes R013; R014 precedes R015; R016 precedes R017
  precedes R018.
- R045 is last.
