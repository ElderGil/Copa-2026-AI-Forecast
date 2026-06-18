# Research: Copa 2026 Forecast

## Decision: Treat FIFA As Official Competition-State Source

**Rationale**: Fixtures, teams, groups, status, results, venues, kickoff times,
and tournament rules must come from the competition authority when available.
The ETL will store raw FIFA payloads before normalization so every forecast can
be audited against what FIFA published at retrieval time.

**Alternatives considered**:

- Kaggle or community fixture files as source of truth: rejected for official
  state because they can lag, transform, or disagree with FIFA.
- Manual fixture spreadsheet: useful only as a temporary fallback and must be
  labeled as degraded/manual.

## Decision: Use Confederations And Federations As Official Enrichment Sources

**Rationale**: FIFA is authoritative for World Cup competition state, but model
assertiveness depends on recent context that may live with other official
entities. Confederations are official for qualifiers and continental
competitions. National federations are official for call-ups, squad changes,
friendlies, preparation camps, suspensions, and injury announcements.

**Alternatives considered**:

- FIFA-only model: accepted as a minimal MVP, but weaker for current form and
  squad availability.
- Unofficial scraper-first model: rejected because it makes source authority and
  licensing unclear.

## Decision: Support Both Online FIFA Fetch And Cached FIFA Payloads

**Rationale**: Official FIFA pages and feeds can change structure or be
temporarily unreachable. The project must support cached raw payloads so a run
can be reproduced and parser changes can be tested.

**Alternatives considered**:

- Online-only ETL: rejected because reproducibility would be weak.
- Cache-only ETL: rejected because current tournament status must be refreshable.

## Decision: Use Recency Windows With Exponential Decay

**Rationale**: International football has sparse samples, so a hard one-year
cutoff can overreact to too few matches. The project will compute 3-, 6-, 12-,
and 24-month views, with the 12-month and tournament-preparation windows given
strong interpretive weight. Exponential decay keeps older matches available
without letting them dominate.

**Alternatives considered**:

- All-time cumulative features: rejected because they mostly encode reputation
  and federation history rather than current sporting strength.
- One-year-only features: useful as a pillar, but too brittle for teams with few
  fixtures.

## Decision: Model Match Outcomes Before Champion Probability

**Rationale**: Champion probability is an aggregate of match outcomes and
tournament path. The project will estimate regulation-time win/draw/loss
probabilities, derive knockout advancement assumptions, and simulate the
tournament.

**Alternatives considered**:

- Direct champion classifier: rejected because it hides bracket path and offers
  almost no training data.
- Forced binary match winner: rejected because group-stage draws materially
  affect standings.

## Decision: Keep Elo-Style Strength As Baseline And Prior

**Rationale**: Elo-style ratings are transparent, strong baselines for sports,
and useful when recent samples are small. They will be opponent-adjusted and
decayed, but not treated as the entire model.

**Alternatives considered**:

- Pure tree model over team names: rejected because it can memorize identity and
  produce untrustworthy probabilities.
- Pure expert rules: rejected because calibration and backtesting become weak.

## Decision: Use Calibrated Ensemble Outputs

**Rationale**: Tree and ensemble models can rank teams well while producing poor
probability estimates. The project will evaluate log loss, Brier score, and
calibration buckets, then apply calibration when it improves reliability.

**Alternatives considered**:

- Use raw `predict_proba`: rejected as insufficient for probability claims.
- Only report rankings: rejected because the user needs probabilities and
  uncertainty.

## Decision: Use Rolling-Origin Backtesting

**Rationale**: Forecasting is temporal. Each historical prediction must be
trained only with data available before that match or tournament date.

**Alternatives considered**:

- Random train/test split: rejected because it can mix future information into
  evaluation and overstate performance.
- Single holdout tournament: useful as a final check, but too small alone.

## Decision: Treat LLMs As Context Extractors Only

**Rationale**: Generative AI can help summarize injury reports, squad news, and
tactical context when trusted sources are provided. It must not invent facts or
assign numeric probabilities directly.

**Alternatives considered**:

- LLM as predictor: rejected because it is difficult to calibrate and audit.
- No textual context: acceptable for MVP, but weaker once squad news matters.

## Decision: Store Forecast Runs As Reproducible Artifacts

**Rationale**: A forecast must be revisitable. Each run will store config, raw
FIFA extract references, source metadata, feature windows, model versions,
calibration status, simulation settings, and generated outputs.

**Alternatives considered**:

- Overwrite a single ranking file: rejected because it destroys lineage and
  makes probability changes impossible to audit.
