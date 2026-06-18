# Quickstart: Copa 2026 Forecast

This quickstart describes the expected analyst workflow for the first
implementation increment.

## 1. Prepare Forecast Config

Create a forecast config file with:

- `run_id`
- `as_of_date`
- official FIFA source URLs or cached raw FIFA payload paths
- raw FIFA output directory
- feature windows
- simulation settings
- model profile

Validate that every input source has a retrieval date and license note.

## 2. Fetch Or Load Official FIFA Data

Run the FIFA ETL workflow.

Expected result:

- Raw FIFA payloads are stored before parsing.
- Retrieval timestamp, source URL, checksum, and parser version are recorded.
- Fixtures, teams, groups, venues, kickoff times, match statuses, results, and
  rules are normalized into official competition state.
- If FIFA data is unavailable, the run is labeled degraded.

## 3. Validate Data Contracts

Run the data validation workflow.

Expected result:

- Team names are mapped or reported as unmapped.
- Matches after `as_of_date` are rejected for feature generation.
- Missing evidence pillars are listed.
- Cancelled or postponed matches are excluded from played-match features.
- Official FIFA competition state is available before a credible forecast run.

## 4. Build Temporal Features

Generate team snapshots for the configured run date.

Expected result:

- 12-month and 24-month windows are present.
- Feature timestamps do not exceed the run date.
- Long-history priors, if enabled, are stored separately from current-form
  features.

## 5. Train Or Load Model Profile

Run the selected model profile.

Expected result:

- Baseline probabilities are available.
- Advanced model probabilities are available when configured.
- Calibration status is recorded.
- Evaluation artifacts exist before the model is marked credible.

## 6. Simulate Tournament

Run the tournament simulation using official FIFA competition state available at
the run date.

Expected result:

- Every simulation produces exactly one champion.
- Group standings follow documented point and tie-break rules.
- Knockout ties are resolved by documented extra-time or penalty assumptions.

## 7. Inspect Outputs

Review:

- Champion probabilities.
- Advancement probabilities by round.
- Team explanations.
- Missing evidence pillars.
- FIFA extract lineage.
- Calibration and baseline comparison report.

## 8. Compare Runs

Run the same workflow with a later `as_of_date`.

Expected result:

- Probability movement is attributed to changed FIFA competition state, changed
  matches, squad context, path changes, or missing/new data sources.
