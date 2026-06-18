# Tasks: Global Iterative Elo Prior

**Input**: `specs/003-global-elo-prior/{spec.md,plan.md}`

- [x] G001 Implement `global_elo_ratings` in `src/copa_forecast/models/prior.py`
- [x] G002 Unit tests in `tests/unit/test_prior.py` (convergence/spread +
      opponent-quality discounting)
- [x] G003 Wire prior into `forecast.py` (rating_priors + pillar label/source)
- [x] G004 Wire prior into `evaluation.py` backtest (deep-history prior anchor +
      SoS ratings; keep `fifa_sum` recency baseline)
- [x] G007 Deep-history window: `feature_windows.prior_months` (120) drives the
      ETL fetch + bound so the prior sees ~10y; recent-form stays at max_months
- [x] G005 Re-run backtest + forecast — validated on 2026-06-18 (3152 matches):
      Côte d'Ivoire #13, Norway #11 (out of top 10); top tier = ARG/FRA/GER/ENG/
      ESP/BEL/BRA. Backtest IMPROVED: accuracy 60.7%, calibrated Brier 0.523,
      log loss 0.910 (vs 0.566 / 0.976 before).
- [x] G006 Full suite (57) + ruff green; quality gate SUCCESS

## Outcome
The deep window was the decisive lever (a 24-month prior is too compressed to
separate pedigree from a hot streak). Decoupling it from the recency window gave
both face validity and a measurable accuracy/calibration gain.

## Dependencies
G001 → G002/G003/G004/G007 → G005 → G006.
