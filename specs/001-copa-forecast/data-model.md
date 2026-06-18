# Data Model: Copa 2026 Forecast

## FIFA Extract

- `extract_id`: Stable identifier for a raw FIFA retrieval.
- `source_url`: Official FIFA URL or feed location.
- `retrieved_at`: Retrieval timestamp.
- `payload_path`: Local path to the raw stored payload.
- `payload_format`: JSON, HTML, PDF-derived text, CSV, or other supported type.
- `checksum`: Content checksum for reproducibility.
- `parser_version`: Parser version used for normalization.
- `status`: Retrieved, cached, failed, or manually supplied.

**Validation rules**:

- Raw payloads are stored before normalization.
- Every official competition-state field points back to a FIFA extract or an
  approved manual correction.

## Official Competition State

- `state_id`: Stable identifier for normalized official state.
- `as_of_date`: Date boundary for the normalized state.
- `fifa_extract_ids`: Extracts used to build the state.
- `teams`: Official teams active in the tournament state.
- `groups`: Group assignments and group metadata.
- `fixtures`: Official fixture list.
- `match_statuses`: Scheduled, live, completed, postponed, cancelled, or other
  official statuses.
- `results`: Official results available by the run date.
- `ruleset_version`: Tournament ruleset identifier.

**Validation rules**:

- State cannot claim official status without at least one FIFA extract.
- Forecasts using non-FIFA competition state are labeled degraded.

## Team

- `team_id`: Stable canonical identifier.
- `canonical_name`: Display name used in reports.
- `fifa_name`: Official FIFA display name when available.
- `aliases`: Known source-specific names.
- `confederation`: Football confederation when known.
- `is_active_2026`: Whether the team is active in the forecast universe.

**Validation rules**:

- Every source team name must resolve to exactly one canonical team or be
  reported as an unmapped name.
- Alias mappings are versioned.

## Match

- `match_id`: Stable identifier derived from FIFA or deterministic fields.
- `fifa_match_id`: Official FIFA match identifier when available.
- `match_date`: Date the match was played or scheduled.
- `home_team_id`: Home or listed team.
- `away_team_id`: Away or opponent team.
- `competition`: Competition or tournament name.
- `match_importance`: Normalized category such as friendly, qualifier,
  continental, World Cup group, or World Cup knockout.
- `venue_context`: Home, away, or neutral context.
- `venue`: Stadium/city when available.
- `status`: Scheduled, live, completed, postponed, cancelled, or abandoned.
- `home_score`, `away_score`: Regulation/full-time score fields as source
  permits.
- `went_to_penalties`: Whether the match required penalties.
- `source_id`: Data source reference.

**Validation rules**:

- A match used for training features must have `match_date` before the forecast
  run date.
- Cancelled or postponed matches must not be treated as played results.

## Data Source

- `source_id`: Stable source identifier.
- `name`: Human-readable source name.
- `retrieved_at`: Extraction timestamp.
- `license_note`: Ownership or usage note.
- `schema_version`: Expected schema contract version.
- `reliability_note`: Known caveats or coverage gaps.
- `authority_level`: Official, enrichment, benchmark, or manual fallback.

**Validation rules**:

- Every raw record used in a forecast must be traceable to a source.
- FIFA competition-state sources have `authority_level = official`.

## Forecast Config

- `run_id`: Human-readable unique run identifier.
- `as_of_date`: Date boundary for the forecast.
- `official_fifa_sources`: Official FIFA source definitions.
- `current_window_months`: Primary current-form window, default 12.
- `max_window_months`: Maximum feature window, default 24.
- `simulation_count`: Number of tournament simulations.
- `data_sources`: Secondary data sources enabled for the run.
- `model_profile`: Modeling profile such as baseline, ensemble, or diagnostic.

**Validation rules**:

- `as_of_date` is required.
- At least one official FIFA source or cached FIFA extract is required for a
  credible run.
- `current_window_months` is less than or equal to `max_window_months`.

## Team Snapshot

- `run_id`: Forecast run reference.
- `team_id`: Team reference.
- `recent_form_features`: Opponent-adjusted recent result indicators.
- `attack_features`: Recent attacking indicators.
- `defense_features`: Recent defensive indicators.
- `squad_features`: Availability and continuity indicators when available.
- `path_features`: Group and bracket path indicators from official FIFA state.
- `missing_pillars`: Evidence pillars unavailable for this team.

**Validation rules**:

- Missing evidence is explicit and separate from zero-valued evidence.
- Feature timestamps must not exceed `as_of_date`.

## Match Probability

- `run_id`: Forecast run reference.
- `match_id`: Match reference or simulated fixture identifier.
- `team_a_id`, `team_b_id`: Teams being evaluated.
- `prob_team_a_win`: Regulation-time or match-state win probability.
- `prob_draw`: Draw probability when applicable.
- `prob_team_b_win`: Regulation-time or match-state win probability.
- `calibration_profile`: Calibration method and date.

**Validation rules**:

- Outcome probabilities must sum to 1 within tolerance.
- Draw probability is required for group-stage regulation-time matches.

## Simulation Result

- `run_id`: Forecast run reference.
- `team_id`: Team reference.
- `prob_group_advance`: Probability of advancing from group stage.
- `prob_round_16`: Probability of reaching round of 16.
- `prob_quarterfinal`: Probability of reaching quarterfinal.
- `prob_semifinal`: Probability of reaching semifinal.
- `prob_final`: Probability of reaching final.
- `prob_champion`: Probability of winning the tournament.

**Validation rules**:

- Round probabilities must be monotonic: champion cannot exceed final, final
  cannot exceed semifinal, and so on.

## Model Evaluation

- `evaluation_id`: Stable evaluation identifier.
- `run_id`: Forecast or model run reference.
- `period`: Historical period evaluated.
- `baseline_name`: Baseline used for comparison.
- `log_loss`: Proper probabilistic score.
- `brier_score`: Proper probabilistic score.
- `calibration_summary`: Bucketed predicted versus observed frequencies.
- `leakage_checks`: Results of temporal leakage tests.

**Validation rules**:

- Evaluation records must state the training cutoff used for every prediction
  block.
