# Plan: Model Credibility & Engineering Remediation

**Input**: `specs/002-credibility-remediation/spec.md`
**Constitution gate**: re-checked at plan, before implementation, before any
result is presented as credible (Governance section).

## Constitution compliance check

| Principle | Before | After this feature |
|---|---|---|
| III — Football pillars | No home/venue; squad always missing | Home-advantage term from `venue_context`; venue pillar feeds the match model; squad still declared-missing transparently |
| IV — Calibrated probabilities | `not_calibrated`; draw never argmax | Dynamic draw + temperature scaling fit on backtest |
| V — Temporal validation | Validates a different formula; no slices | Unified formula; breakdown by competition type and date window |
| VII — Lineage/explainability | Baseline mislabeled | Honest baseline name + calibration recorded in metadata |

No new constitution exceptions are required; all changes move the system toward
compliance.

## Technical approach

1. **Match model (`models/baselines.py`)** — `three_way_baseline` gains
   `home_advantage` and a Gaussian-decaying draw term:
   `draw = draw_max * exp(-(eff_diff / draw_scale)**2)`, `eff_diff = Δrating +
   home_advantage`. Tuned so a level matchup yields draw ≈ 0.40 (argmax-capable)
   while a 200-pt gap decays toward ≈ 0.26. Win/loss split the remainder by the
   existing Elo expectation. Signature stays backward compatible (new
   keyword-only args, sensible defaults).
2. **Feature parity (`features/recent.py`)** — accumulate
   `weighted_importance += weight * importance` so the live denominator equals
   the backtest's. Join teams by `normalize_name` to absorb localization drift.
3. **Calibration (`models/calibration.py`, `models/evaluation.py`)** — add
   `fit_temperature` / `apply_temperature` (1-D search minimizing multiclass log
   loss). Backtest fits T on model predictions, reports raw + calibrated metrics
   and per-competition / per-window slices, and passes `home_advantage` from each
   target's `venue_context`.
4. **Simulation (`simulation/monte_carlo.py`)** — share `COMPLETED_STATUSES`,
   fix the missing-strength default to the 1500 scale, add an optional
   head-to-head tiebreak hook, drop dead champion-sampling helpers.
5. **Ingestion robustness (`data/sources/fifa.py`, `cli.py`, `recent_matches.py`)**
   — User-Agent + retry/backoff + HTTP error handling + scheme allow-list;
   dedupe merged fixtures; tolerant `load_recent_matches`.
6. **Shared utilities (`copa_forecast/timeutils.py`)** — single `add_months` /
   `days_in_month`; callers import it.
7. **Quality gate / CI** — real leakage assertion + stricter CSV check in
   `verify_implementation.py`; UTC cron; `ruff` in dev deps and a CI lint+test
   step.
8. **Docs** — README, `docs/validation.md`, add `LICENSE`.

## Risk & test strategy

- Numeric unit tests assert structure, not magic probabilities, so the draw /
  home-advantage change is safe; new tests pin F1 (draw can be argmax), F3
  (3.0 pts/match), F9 (normalized join).
- Run `pytest` after each batch; never leave the suite red.
