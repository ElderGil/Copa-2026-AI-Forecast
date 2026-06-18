# Plan: Global Iterative Elo Prior

**Input**: `specs/003-global-elo-prior/spec.md`

## Approach

1. **`src/copa_forecast/models/prior.py` — `global_elo_ratings(matches)`**
   - Iterate multiple epochs over all played matches (chronological), updating
     both teams each match with `K = base_k/(1+epoch*decay)` scaled by match
     importance and a capped margin-of-victory multiplier.
   - Decaying K converges the ratings to a stable spread (≈ Bradley-Terry MLE),
     which propagates opponent quality: beating a weak (low-rated) team yields a
     high expected score and therefore little gain. Stop when the largest update
     in an epoch falls below a threshold (cap at `max_epochs`).
   - Venue-neutral (pedigree prior); recency is handled separately by the recent-
     form features, so no decay weighting here.

2. **`forecast.py`** — compute `rating_priors = global_elo_ratings(played)`
   instead of `fifa_sum_ratings`. The prior already flows into
   `build_team_strengths` (wider spread now dominates raw ppg) and into the SoS
   opponent-context pillar. Update the prior pillar's human label/source to say
   "Elo global" (payload keys unchanged to keep the UI stable).

3. **`evaluation.py` (backtest)** — compute `prior_elo = global_elo_ratings(prior)`
   per target and use it as the model's rating anchor and SoS opponent ratings,
   so the backtest validates the deployed prior. Keep `fifa_sum_ratings(prior)`
   only for the `fifa_sum_style` baseline three-way comparison.

## Constitution check

- II (recency before reputation): the prior is still a 24-month window; it is an
  explicit prior/regularizer reported separately from recent-form drivers. ✓
- IV (calibrated): temperature scaling from 002 unchanged; verify no regression. ✓
- V (validation reflects release): backtest uses the same prior. ✓
- VII (lineage): computed locally from FIFA records; no external table. ✓

## Risk & tests

- Performance: `global_elo_ratings` runs once per backtest target (~407×); the
  convergence stop keeps it to a few seconds. If too slow, lower `max_epochs`.
- New unit tests (`tests/unit/test_prior.py`): (a) spread widens / converges,
  (b) beating only weak opponents yields a lower rating than beating strong ones.
- Re-run backtest to confirm calibrated metrics hold; eyeball the ranking.
