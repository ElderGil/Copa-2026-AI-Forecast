# Spec: Global Iterative Elo Prior

**Feature ID**: 003-global-elo-prior
**Status**: Complete (prior `global_elo_ratings` integrado em `forecast.py`/`evaluation.py`, commit `ed321d6`; todas as tasks concluídas). Resíduo conhecido de validade de face documentado abaixo.
**Depends on**: `001-copa-forecast`, `002-credibility-remediation`
**Constitution**: `.specify/memory/constitution.md` (Principles II, IV, VII)

## Context

Feature 002 fixed the match model (dynamic draw, calibration, consistent
formula, SoS pillar) but left a face-validity gap flagged in review: mid-tier
teams with strong recent records against weak opponents (e.g. Côte d'Ivoire,
Austria, Norway) rank near or above traditional powers (France, Spain, Brazil).

## Diagnosis (measured on the 2026-06-18 snapshot)

The strength prior (`fifa_sum_ratings`, a single chronological Elo pass that
cold-starts every team at 1500) is **far too compressed**: across 48 teams the
prior spans only ~260 points (1433–1693). Because `build_team_strengths` blends
this flat prior with raw points-per-match, the ranking collapses toward
"recent points-per-game", so a flat-track winner (Côte d'Ivoire: 2.38 ppg over
19 matches, prior 1631) lands beside France (prior 1625). A single Elo pass does
not propagate opponent quality: beating weak teams is not discounted because the
opponents are still near 1500 when the match is scored.

## Goals / acceptance criteria

1. A new opponent-quality-aware prior that **iterates to convergence**, so the
   rating spread reflects the win/loss network (target spread ≳ 600 points on
   the current data) and beating weak opponents is discounted.
2. After wiring the prior into the forecast, **Côte d'Ivoire, Austria and Norway
   rank below the established top tier** (France / England / Germany / Spain /
   Argentina) on the 2026-06-18 data.
3. The backtest is updated to validate the **same** prior the forecast uses
   (Principle V), while the published `fifa_sum_style` baseline stays unchanged
   for a fair, comparable benchmark.
4. The match-model metrics (calibrated Brier / log loss) do **not regress**
   versus the 002 baseline.
5. All existing tests stay green; new tests cover the convergence/spread and
   opponent-quality discounting properties.

## Non-goals

- Fetching a multi-year FIFA match history. The prior is still computed from the
  24-month official window already ingested; a longer backfill (which would let
  the prior also reward sustained historical pedigree, e.g. lift Brazil) is a
  separate data task. Persisting/carrying the Elo across daily runs is deferred.
- No external ranking table or odds are introduced (Principle I / VII): the
  prior is computed locally from official FIFA match records.
