<!--
Sync Impact Report
Version change: 1.0.0 -> 1.1.0
Modified principles:
- Added "Official FIFA ETL Is Source Of Truth"
- Expanded data lineage rules to require raw FIFA payload retention
Added sections:
- None
Removed sections:
- None
Templates reviewed:
- .specify/templates/plan-template.md - reviewed, no change required
- .specify/templates/spec-template.md - reviewed, no change required
- .specify/templates/tasks-template.md - reviewed, no change required
Follow-up TODOs:
- None
-->

# Copa 2026 AI Forecast Constitution

## Core Principles

### I. Official FIFA ETL Is Source Of Truth
Official FIFA data MUST be the source of truth for World Cup fixtures, teams,
groups, match status, match results, venues, kickoff times, and tournament rules
whenever FIFA publishes those fields. The ETL MUST retain raw FIFA payloads,
retrieval timestamps, source URLs, parser versions, and normalized outputs.
Secondary sources MAY enrich missing analytical pillars, but they MUST NOT
override official FIFA competition state unless a documented manual correction
is approved and clearly labeled.

### II. Recency Before Historical Reputation
Forecasts MUST prioritize the current sporting cycle over all-time history. The
default evidence window is the last 24 months before the forecast run, with a
stronger current-form view over the last 12 months and a preparation-form view
for friendlies, qualifiers, continental tournaments, and World Cup matches that
occur during the run period. Long historical records MAY be used only as an
explicit prior, benchmark, or regularizer, and their contribution MUST be
reported separately from current-form signals.

### III. Football-Specific Evidence Pillars
Every forecast MUST be grounded in football evaluation pillars, not only generic
win counts. At minimum, the system MUST support opponent-adjusted results,
recent attacking strength, recent defensive strength, match importance,
home/neutral context, squad availability, and tournament simulation context.
When richer data such as expected goals, player minutes, injuries, odds, or
tactical indicators is unavailable, the forecast MUST state the missing pillar
and degrade transparently.

### IV. Calibrated Probabilities, Not Rankings Disguised As Odds
The project MUST produce interpretable probabilities for match outcomes and
tournament results. Reported probabilities MUST be evaluated with proper
probabilistic metrics such as log loss, Brier score, and calibration curves.
Any ranking output MUST be derived from calibrated scenario probabilities, not
from forced binary winners or uncalibrated classifier scores.

### V. Temporal Validation Is Non-Negotiable
Model validation MUST respect time. Random train/test splits are not acceptable
for primary evaluation because they can mix future context into historical
assessment. Backtests MUST use rolling-origin or tournament-cycle validation,
must compare against simple baselines, and must document performance by date,
competition type, and probability bucket.

### VI. Simulation Must Match The Tournament
Tournament forecasts MUST simulate the official competition structure as of the
forecast run date. Group-stage draws, knockout advancement, extra time,
penalties, rest effects, and bracket path uncertainty MUST be represented when
they affect champion probability. A round-robin power ranking MAY be offered as
diagnostics, but it MUST NOT be presented as title probability.

### VII. Data Lineage And Explainability
Every forecast run MUST record the data sources, extraction dates, schema
version, feature windows, model version, calibration status, and simulation
settings. Users MUST be able to inspect why a team's probability changed across
runs, including which evidence pillars contributed to the change.

## Sports Forecasting Constraints

- Data freshness MUST be explicit: every run has an "as of" date and must avoid
  using matches, squads, injuries, or odds unavailable at that date.
- Official FIFA extracts MUST be stored raw before normalization.
- If official FIFA data is unreachable, a run MAY proceed only in degraded mode
  and MUST be labeled "non-official competition state".
- Team-name normalization MUST be deterministic and versioned.
- Missing data MUST be represented as missing evidence, not silently converted
  into sporting weakness unless the rule is justified in the data dictionary.
- LLM or generative AI components MAY extract structured context from trusted
  text sources, but they MUST NOT invent facts or directly assign numeric win
  probabilities.
- Official tournament rules and fixtures MUST be referenced by source and date
  when used by a simulation run.

## Development Workflow and Quality Gates

- Work proceeds through Spec Kit phases: constitution, specification, plan,
  tasks, implementation, validation.
- Tests for FIFA ETL contracts, data contracts, temporal leakage, probability
  calibration, and tournament simulation rules MUST exist before a forecast can
  be trusted.
- Each user story MUST remain independently testable.
- Any model release MUST include a baseline comparison, a calibration report,
  and a reproducibility note.
- Any new data source MUST include ownership/licensing notes, refresh cadence,
  schema expectations, and failure behavior.

## Governance

This constitution supersedes informal project preferences. Any plan, task, or
implementation that violates a principle MUST either be changed or document a
specific, time-bounded exception in the feature plan's Complexity Tracking
section.

Amendments require an update to this file, a Sync Impact Report, and a semantic
version change:

- MAJOR for redefining or removing a core principle.
- MINOR for adding a principle or materially expanding governance.
- PATCH for clarifications that do not change behavior.

Compliance is reviewed at plan creation, before implementation, and before any
forecast result is presented as credible.

**Version**: 1.1.0 | **Ratified**: 2026-06-17 | **Last Amended**: 2026-06-17
