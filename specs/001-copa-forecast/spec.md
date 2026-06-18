# Feature Specification: Copa 2026 Forecast

**Feature Branch**: `001-copa-forecast`

**Created**: 2026-06-17

**Status**: Draft

**Input**: User description: "Criar um projeto para prever o vencedor da Copa 2026 usando dados oficiais da FIFA como ETL obrigatorio, uma premissa mais honesta que privilegie o momento atual das selecoes, os ultimos 12 a 24 meses, amistosos de preparacao, partidas recentes da propria Copa quando disponiveis e pilares reais de avaliacao esportiva do futebol, seguindo o fluxo Spec Kit do GitHub."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ingest Official FIFA Competition Data (Priority: P1)

As an analyst, I want to ingest official FIFA data for the World Cup 2026 so
that fixtures, teams, groups, match status, venues, kickoff times, results, and
tournament rules come from the authoritative competition source.

**Why this priority**: Forecasts are only credible if the competition state is
official. Every later story depends on correct FIFA fixtures, results, and rules.

**Independent Test**: Provide a FIFA source URL or cached FIFA payload. The
system stores the raw extract, validates required fields, normalizes the
competition state, and reports retrieval metadata.

**Acceptance Scenarios**:

1. **Given** an official FIFA fixture source, **When** the ETL runs, **Then** raw
   FIFA data is stored before any normalization.
2. **Given** a FIFA match has a result or live status by the run date, **When**
   the ETL normalizes competition state, **Then** that official status is used
   in the forecast inputs.
3. **Given** official FIFA data cannot be reached, **When** the user attempts a
   forecast, **Then** the run is labeled as degraded and cannot claim official
   competition state.

---

### User Story 2 - Generate A Recency-First Forecast (Priority: P2)

As an analyst, I want to generate a World Cup 2026 champion forecast from
recent, date-bounded football evidence so that the probability reflects current
team strength rather than all-time reputation.

**Why this priority**: This is the core modeling value once official competition
state exists.

**Independent Test**: Provide valid official FIFA competition state plus recent
match and team evidence with an "as of" date. The system produces match
probabilities, team-level advancement probabilities, and champion probabilities
without using future data.

**Acceptance Scenarios**:

1. **Given** recent match data ending on a selected run date, **When** the user
   requests a forecast, **Then** the output includes champion probabilities for
   all eligible teams and records the run date.
2. **Given** historical records older than the configured window, **When** the
   forecast is generated, **Then** those records are excluded from current-form
   features or reported only as an explicit historical prior.
3. **Given** World Cup matches have already been played by the run date,
   **When** the forecast is generated, **Then** those official FIFA results
   affect future group and knockout probabilities.

---

### User Story 3 - Explain The Football Evidence (Priority: P3)

As an analyst, I want to inspect the evidence pillars behind each team's
probability so that I can understand whether the forecast is driven by form,
opponent strength, squad availability, attacking/defensive trend, or path
difficulty.

**Why this priority**: Probabilities without explanation are easy to mistake for
authority. The project must make its football reasoning auditable.

**Independent Test**: Select any team in a completed forecast run. The system
shows the active evidence pillars, the data freshness for each pillar, and the
main contributors to probability movement compared with a prior run or baseline.

**Acceptance Scenarios**:

1. **Given** a completed forecast run, **When** the user inspects Brazil,
   France, or any other team, **Then** the output shows current-form, opponent,
   attack, defense, squad, and path indicators when available.
2. **Given** a pillar has missing data, **When** the explanation is generated,
   **Then** the pillar is marked as unavailable rather than silently counted as
   poor performance.
3. **Given** two forecast runs with different run dates, **When** the user
   compares a team's probabilities, **Then** the system identifies which
   evidence changed.

---

### User Story 4 - Simulate The Actual Tournament (Priority: P4)

As an analyst, I want to run simulations that follow the official tournament
structure so that champion probability reflects group standings, bracket path,
draws, extra time, penalties, and uncertainty.

**Why this priority**: A team can be strong and still face a difficult path.
Champion probability requires tournament simulation, not a static power ranking.

**Independent Test**: Provide the official FIFA competition state as of the run
date. The system simulates complete tournaments and reports advancement
probability by round.

**Acceptance Scenarios**:

1. **Given** a valid FIFA-derived tournament ruleset, **When** the simulation
   runs, **Then** every simulated tournament produces one champion and valid
   round outcomes.
2. **Given** a group-stage match can end in a draw, **When** group standings are
   simulated, **Then** draw points and tie-break assumptions are handled
   consistently.
3. **Given** a knockout match is simulated, **When** regulation probabilities do
   not produce a winner, **Then** extra-time or penalty assumptions resolve the
   match according to documented rules.

---

### User Story 5 - Validate Forecast Quality Over Time (Priority: P5)

As an analyst, I want to backtest the model using only information available at
each historical date so that I can judge whether the probabilities are
calibrated and better than simple baselines.

**Why this priority**: Forecasting credibility depends on historical evidence of
calibration and leakage control.

**Independent Test**: Run a backtest over prior international windows or
tournaments. The system reports probabilistic metrics, calibration diagnostics,
and baseline comparisons.

**Acceptance Scenarios**:

1. **Given** historical match data through multiple seasons, **When** backtesting
   runs, **Then** each prediction uses only data available before the predicted
   match.
2. **Given** calibrated and uncalibrated model outputs, **When** evaluation
   completes, **Then** the report identifies whether calibration improved
   probability reliability.
3. **Given** a simple baseline such as Elo-style strength, **When** model
   performance is reported, **Then** the project shows whether the advanced
   model added value.

### Edge Cases

- FIFA changes a fixture, kickoff time, venue, or match status after a prior
  forecast run.
- FIFA data is temporarily unavailable or structurally different from the last
  parser version.
- A team has fewer than five recent matches in the active window.
- A team changed name or federation representation across source systems.
- A match is abandoned, cancelled, postponed, or decided by penalties.
- Squad, injury, expected-goals, or odds data is missing for some teams.
- A run date occurs during the tournament, after some matches have been played.
- Two teams tie on all simulated group-stage tie-break information available to
  the project.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST ETL official FIFA data for World Cup 2026 fixtures,
  teams, groups, venues, kickoff times, match status, match results, and
  tournament rules whenever FIFA publishes those fields.
- **FR-002**: The system MUST persist raw FIFA extracts with source URL,
  retrieval timestamp, parser version, and checksum before normalization.
- **FR-003**: The system MUST label any forecast without reachable or cached
  official FIFA competition state as degraded.
- **FR-004**: The system MUST produce champion probabilities for the FIFA World
  Cup 2026 using a declared forecast run date.
- **FR-005**: The system MUST default to a 24-month evidence window with a
  separately reported 12-month current-form window.
- **FR-006**: The system MUST include matches already played by the forecast run
  date and MUST exclude matches or context unavailable at that date.
- **FR-007**: The system MUST prevent all-time historical aggregates from being
  primary predictors of current form.
- **FR-008**: The system MAY use long historical information only as an explicit
  prior, benchmark, or regularizer and MUST report that contribution separately.
- **FR-009**: The system MUST model match outcomes with at least win, draw, and
  loss probabilities for regulation time when group-stage behavior is relevant.
- **FR-010**: The system MUST support football evidence pillars for opponent
  adjustment, attacking trend, defensive trend, match importance, venue context,
  squad availability, and tournament path.
- **FR-011**: The system MUST mark unavailable evidence pillars as missing rather
  than treating missing data as poor team performance.
- **FR-012**: The system MUST simulate the tournament structure that is official
  as of the run date.
- **FR-013**: The system MUST report advancement probabilities by round in
  addition to champion probability.
- **FR-014**: The system MUST store every forecast run with its FIFA source
  extracts, data sources, extraction dates, feature windows, model version,
  calibration status, and simulation settings.
- **FR-015**: The system MUST provide a team-level explanation of probability
  drivers for every forecast run.
- **FR-016**: The system MUST support comparison between forecast runs to show
  how and why probabilities changed.
- **FR-017**: The system MUST backtest predictions with time-respecting
  validation and compare against at least one simple baseline.
- **FR-018**: The system MUST report probability quality using calibration and
  scoring metrics before any forecast is marked credible.

### Key Entities

- **FIFA Extract**: A raw official FIFA payload with source URL, retrieval time,
  parser version, checksum, and storage path.
- **Official Competition State**: Normalized FIFA-derived teams, groups,
  fixtures, venues, kickoff times, match statuses, results, and rules.
- **Forecast Run**: A dated execution containing FIFA extracts, input data
  versions, feature windows, model versions, calibration status, simulation
  settings, and outputs.
- **Team**: A national team with canonical name, aliases, confederation, and
  tournament eligibility status.
- **Match**: A football match with teams, date, competition, venue context,
  score, penalties if applicable, status, and source metadata.
- **Team Snapshot**: A date-bounded representation of a team's current evidence
  pillars at a forecast run date.
- **Evidence Pillar**: A football evaluation category such as recent form,
  attacking trend, defensive trend, squad availability, or path difficulty.
- **Model Evaluation**: A backtest result containing metrics, calibration
  diagnostics, baseline comparisons, and leakage checks.
- **Simulation Result**: Aggregated tournament outcomes across many simulated
  tournament paths.
- **Data Source**: A source record with ownership, refresh cadence, extraction
  date, schema expectations, and reliability notes.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of official competition-state fields used in forecasts are
  traceable to a raw FIFA extract or an explicitly approved manual correction.
- **SC-002**: 100% of forecast runs include an "as of" date, FIFA source list,
  evidence windows, and simulation settings.
- **SC-003**: 100% of tested historical predictions use only information dated
  before the predicted match.
- **SC-004**: A full tournament forecast completes in under 5 minutes for at
  least 10,000 simulated tournaments on a typical analyst laptop.
- **SC-005**: Forecast reports include champion, finalist, semifinal,
  quarterfinal, round-of-16, and group-advancement probabilities for all active
  teams.
- **SC-006**: Calibration reports show probability buckets where predicted
  probability and observed frequency are compared before any model is promoted
  as credible.
- **SC-007**: The model is not promoted unless it beats or clearly diagnoses its
  gap against a simple baseline on at least one proper probabilistic metric.
- **SC-008**: For every team forecast, a user can identify the top evidence
  pillars and missing data pillars in under 2 minutes.

## Assumptions

- The initial project is an analyst-facing local forecasting system, not a
  public betting product.
- Official FIFA data may come from public FIFA pages, FIFA-hosted API payloads,
  downloadable documents, or cached raw extracts when online access is
  unavailable.
- Public data may be incomplete for player availability, expected goals, and
  tactical indicators; the system will degrade transparently when a pillar is
  unavailable.
- Secondary sources can enrich football evidence, but official FIFA competition
  state remains authoritative.
- Betting odds, if used later, are treated as benchmark or market-comparison
  signals unless explicitly approved as model inputs.
- The project starts with reproducible batch forecasts before adding scheduled
  refreshes or a user interface.
