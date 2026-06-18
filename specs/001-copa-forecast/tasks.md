# Tasks: Copa 2026 Forecast

**Input**: Design documents from `specs/001-copa-forecast/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Required for official FIFA ETL, data contracts, leakage prevention,
calibration, and tournament simulation rules per project constitution.

**Organization**: Tasks are grouped by user story to enable independent
implementation and testing.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create Python package skeleton in `src/copa_forecast/__init__.py`
- [x] T002 Create project metadata and dependency config in `pyproject.toml`
- [x] T003 [P] Configure linting defaults in `pyproject.toml`
- [x] T004 [P] Create example forecast config in `configs/example.forecast.json`
- [x] T005 [P] Create data directory documentation in `data/README.md`
- [x] T006 [P] Create source policy documentation in `docs/sources.md`
- [x] T007 [P] Create official source registry seed in `configs/source_registry.yaml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before user stories

- [x] T008 Implement typed forecast config loading in `src/copa_forecast/config.py`
- [x] T009 Implement data contract entities in `src/copa_forecast/data/contracts.py`
- [x] T010 [P] Add config contract tests in `tests/contract/test_forecast_config.py`
- [x] T011 [P] Add team-name normalization tests in `tests/unit/test_normalize.py`
- [x] T012 Implement canonical team normalization in `src/copa_forecast/data/normalize.py`
- [x] T013 Implement source metadata validation in `src/copa_forecast/data/validate.py`
- [x] T014 Implement CLI command structure in `src/copa_forecast/cli.py`
- [x] T015 Add structured artifact writer in `src/copa_forecast/reporting/artifacts.py`

**Checkpoint**: Foundation ready - user story implementation can begin.

---

## Phase 3: User Story 1 - Ingest Official FIFA Competition Data (Priority: P1) MVP

**Goal**: Fetch or load official FIFA data, store raw payloads, and normalize
competition state.

**Independent Test**: With a cached FIFA fixture payload, run the FIFA ETL and
verify raw storage, metadata, normalized fixtures, teams, statuses, and degraded
mode behavior.

### Tests for User Story 1

- [x] T016 [P] [US1] Add FIFA config contract tests in `tests/contract/test_forecast_config.py`
- [x] T017 [P] [US1] Add raw FIFA payload storage tests in `tests/unit/test_fifa_raw_store.py`
- [x] T018 [P] [US1] Add FIFA parser fixture tests in `tests/unit/test_fifa_parser.py`
- [x] T019 [P] [US1] Add FIFA ETL integration test in `tests/integration/test_fifa_etl.py`

### Implementation for User Story 1

- [x] T020 [US1] Implement FIFA source client in `src/copa_forecast/data/sources/fifa.py`
- [x] T021 [US1] Implement raw FIFA payload persistence in `src/copa_forecast/data/ingest.py`
- [x] T022 [US1] Implement FIFA fixture/team/status parser in `src/copa_forecast/data/sources/fifa.py`
- [x] T023 [US1] Implement official competition state builder in `src/copa_forecast/data/ingest.py`
- [x] T024 [US1] Add degraded-mode validation in `src/copa_forecast/data/validate.py`
- [x] T025 [US1] Add CLI command for FIFA ETL in `src/copa_forecast/cli.py`

**Checkpoint**: Official FIFA competition state is available for credible runs.

---

## Phase 4: User Story 2 - Generate A Recency-First Forecast (Priority: P2)

**Goal**: Generate a dated forecast using official FIFA state, recent evidence,
and no future data.

**Independent Test**: With sample FIFA competition state, recent matches, and
fixtures, run a forecast and verify champion probabilities plus run metadata are
produced.

### Tests for User Story 2

- [x] T026 [P] [US2] Add leakage guard tests in `tests/unit/test_leakage.py`
- [x] T027 [P] [US2] Add temporal window tests in `tests/unit/test_windows.py`
- [x] T028 [P] [US2] Add MVP forecast integration test in `tests/integration/test_forecast_run.py`

### Implementation for User Story 2

- [x] T029 [US2] Implement date-bounded match filtering in `src/copa_forecast/features/leakage.py`
- [x] T030 [US2] Implement rolling 3/6/12/24-month windows in `src/copa_forecast/features/windows.py`
- [x] T031 [US2] Implement football evidence pillars in `src/copa_forecast/features/pillars.py`
- [x] T032 [US2] Implement baseline strength model in `src/copa_forecast/models/baselines.py`
- [x] T033 [US2] Implement match probability model interface in `src/copa_forecast/models/match_model.py`
- [x] T034 [US2] Integrate forecast command in `src/copa_forecast/cli.py`
- [x] T035 [US2] Persist forecast run metadata in `src/copa_forecast/reporting/artifacts.py`

**Checkpoint**: MVP forecast produces dated probabilities without future data.

---

## Phase 4.5: Real Official Recent Match ETL (Priority: P2)

**Goal**: Fetch official FIFA Calendar match history for each qualified team in
the 12-24 month evidence window, persist lineage, and feed the model/site.

**Independent Test**: With local FIFA Calendar-shaped fixtures, run recent-match
ETL, verify deduped processed JSON/CSV with Excel-safe BOM, then verify forecast
uses the recent pillars when team coverage is sufficient.

### Tests for Real Recent ETL

- [x] T063 [P] Add FIFA Calendar parser tests in `tests/unit/test_fifa_parser.py`
- [x] T064 [P] Add recent feature engineering tests in `tests/unit/test_recent_features.py`
- [x] T065 [P] Add recent ETL integration tests in `tests/integration/test_fifa_etl.py`
- [x] T066 [P] Add forecast-with-recent-data integration test in `tests/integration/test_forecast_run.py`

### Implementation for Real Recent ETL

- [x] T067 Implement recent-match source config in `src/copa_forecast/config.py`
- [x] T068 Implement FIFA Calendar match parser in `src/copa_forecast/data/sources/fifa.py`
- [x] T069 Implement recent match ETL artifacts in `src/copa_forecast/data/recent_matches.py`
- [x] T070 Implement recency/importance/venue features in `src/copa_forecast/features/recent.py`
- [x] T071 Integrate recent pillars into forecast strengths in `src/copa_forecast/forecast.py`
- [x] T072 Add CLI command `etl-recent-matches` in `src/copa_forecast/cli.py`
- [x] T073 Add real FIFA config in `configs/fifa.real.forecast.json`

**Checkpoint**: Forecast can run from official FIFA tournament state plus
official FIFA per-team match history instead of sample-only evidence.

---

## Phase 5: User Story 3 - Explain The Football Evidence (Priority: P3)

**Goal**: Explain team probabilities through evidence pillars and missing data.

**Independent Test**: Select any team from a forecast run and verify the output
shows active pillars, missing pillars, and top drivers.

### Tests for User Story 3

- [x] T036 [P] [US3] Add explanation tests in `tests/unit/test_explanations.py`
- [x] T037 [P] [US3] Add run comparison tests in `tests/unit/test_run_comparison.py`

### Implementation for User Story 3

- [x] T038 [US3] Implement team explanation summaries in `src/copa_forecast/reporting/explanations.py`
- [x] T039 [US3] Implement missing-pillar reporting in `src/copa_forecast/features/pillars.py`
- [x] T040 [US3] Implement run-to-run comparison in `src/copa_forecast/reporting/explanations.py`
- [x] T041 [US3] Add CLI explanation command in `src/copa_forecast/cli.py`

**Checkpoint**: Team-level forecast reasoning is inspectable.

---

## Phase 6: User Story 4 - Simulate The Actual Tournament (Priority: P4)

**Goal**: Simulate the official tournament structure and report advancement by
round.

**Independent Test**: Run a tournament simulation with FIFA-derived competition
state and verify every simulated path produces valid standings, knockout
results, and one champion.

### Tests for User Story 4

- [x] T042 [P] [US4] Add group standings tests in `tests/unit/test_standings.py`
- [x] T043 [P] [US4] Add tournament rules tests in `tests/unit/test_rules.py`
- [x] T044 [P] [US4] Add simulation integration test in `tests/integration/test_simulation.py`

### Implementation for User Story 4

- [x] T045 [US4] Implement FIFA-derived tournament rules model in `src/copa_forecast/simulation/rules.py`
- [x] T046 [US4] Implement group standings calculation in `src/copa_forecast/simulation/standings.py`
- [x] T047 [US4] Implement Monte Carlo simulation in `src/copa_forecast/simulation/monte_carlo.py`
- [x] T048 [US4] Add advancement probability reporting in `src/copa_forecast/reporting/artifacts.py`
- [x] T049 [US4] Add CLI simulation command in `src/copa_forecast/cli.py`

**Checkpoint**: Tournament probabilities are based on simulated official paths.

---

## Phase 7: User Story 5 - Validate Forecast Quality Over Time (Priority: P5)

**Goal**: Backtest probabilities with temporal validation and calibration.

**Independent Test**: Run a historical backtest and verify leakage checks,
baseline comparison, and calibration diagnostics are present.

### Tests for User Story 5

- [ ] T050 [P] [US5] Add calibration metric tests in `tests/unit/test_calibration.py`
- [ ] T051 [P] [US5] Add evaluation tests in `tests/unit/test_evaluation.py`
- [ ] T052 [P] [US5] Add backtest integration test in `tests/integration/test_backtest.py`

### Implementation for User Story 5

- [ ] T053 [US5] Implement probability calibration utilities in `src/copa_forecast/models/calibration.py`
- [ ] T054 [US5] Implement rolling-origin evaluation in `src/copa_forecast/models/evaluation.py`
- [ ] T055 [US5] Implement baseline comparison report in `src/copa_forecast/models/evaluation.py`
- [ ] T056 [US5] Add CLI backtest command in `src/copa_forecast/cli.py`
- [ ] T057 [US5] Persist calibration artifacts in `src/copa_forecast/reporting/artifacts.py`

**Checkpoint**: Forecast quality is measurable before promotion.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T058 [P] Update project README in `README.md`
- [ ] T059 [P] Add architecture decision records in `docs/adr/`
- [ ] T060 Add sample data fixtures in `tests/fixtures/`
- [ ] T061 Run all tests and document validation output in `docs/validation.md`
- [ ] T062 Review all outputs for constitution compliance in `specs/001-copa-forecast/plan.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on setup and blocks all user stories.
- **US1 FIFA ETL (Phase 3)**: Starts after foundational and is the MVP gate.
- **US2 Forecast (Phase 4)**: Depends on official FIFA competition state from
  US1 for credible runs.
- **US3 Explanations (Phase 5)**: Starts after foundational; richer when US2
  artifacts exist.
- **US4 Simulation (Phase 6)**: Depends on official FIFA state from US1 and
  match probabilities from US2 or baseline stubs.
- **US5 Validation (Phase 7)**: Depends on model interfaces from US2.
- **Polish (Phase 8)**: Depends on desired stories being complete.

### Parallel Opportunities

- T003, T004, T005, and T006 can run in parallel.
- T009 and T010 can run in parallel.
- Test tasks within each user story can run in parallel.
- US3 explanation work and US4 simulation work can proceed in parallel after
  US1 exposes stable official competition-state artifacts.

## Parallel Example: User Story 1

```bash
Task: "Add FIFA config contract tests in tests/contract/test_fifa_config.py"
Task: "Add raw FIFA payload storage tests in tests/unit/test_fifa_raw_store.py"
Task: "Add FIFA parser fixture tests in tests/unit/test_fifa_parser.py"
Task: "Add FIFA ETL integration test in tests/integration/test_fifa_etl.py"
```

## Implementation Strategy

### MVP First

1. Complete Phase 1 setup.
2. Complete Phase 2 foundation.
3. Complete Phase 3 User Story 1.
4. Stop and validate official FIFA ETL with cached fixtures/results payloads.

### Incremental Delivery

1. Add recency-first forecast from User Story 2.
2. Add explanations from User Story 3.
3. Add tournament simulation from User Story 4.
4. Add backtesting and calibration from User Story 5.
5. Promote a forecast only after FIFA lineage and validation reports pass.
