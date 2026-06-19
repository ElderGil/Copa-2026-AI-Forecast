# Source Policy

## Official FIFA Sources

Official FIFA data is authoritative for World Cup 2026 competition state:

- Fixtures.
- Teams and groups.
- Venues and kickoff times.
- Match status and results.
- Tournament regulations and advancement rules.
- FIFA rankings when used as an official ranking input.
- FIFA Power Rankings by Aramco as an official FIFA editorial/ranking surface
  for benchmark and explainability candidates, once a structured, reproducible
  extraction path is available.
- FIFA Calendar API match records for team-level 12-24 month form, including
  official qualifiers, continental tournaments, Nations League, and friendlies
  represented in FIFA match records.

Raw FIFA payloads must be stored before normalization. Each extract must record
source URL, retrieval timestamp, checksum, payload format, and parser version.

## Secondary Sources

Secondary sources may enrich football evidence, including expected goals,
injuries, player minutes, odds, tactical context, and historical match records.
They cannot override official FIFA competition state unless a manual correction
is explicitly approved and labeled.

## Other Official Sources

Official does not only mean FIFA. The source hierarchy is:

1. **FIFA**: World Cup 2026 competition state, match center, regulations,
   rankings, official match reports, lineups, disciplinary data, and match
   events when available.
2. **Continental confederations**: official qualifiers, Nations League,
   continental tournaments, match reports, standings, disciplinary records, and
   lineups from UEFA, CONMEBOL, CONCACAF, AFC, CAF, and OFC.
3. **National federations**: official call-ups, squad changes, injuries,
   suspensions, coaching changes, friendlies, and preparation-camp information.
4. **Clubs or leagues**: official player availability and minutes when national
   federation data does not cover club context.
5. **Licensed sports-data providers**: event, expected-goals, tracking, or odds
   data can enrich the model if licensing allows it. These are not governing
   bodies, so they do not override FIFA competition state.

## Source Priority By Data Type

| Data type | Primary source | Enrichment source |
|-----------|----------------|-------------------|
| World Cup fixtures/results/status | FIFA | None unless degraded/manual |
| World Cup rules/tie-breaks | FIFA regulations | None unless degraded/manual |
| FIFA ranking | FIFA ranking page/procedure | None |
| FIFA Power Rankings | FIFA Power Rankings page | Benchmark/explainability only until structured ETL is stable |
| Recent senior men's national-team matches | FIFA Calendar API by team | Confederation official sites for reconciliation |
| Qualifiers and continental matches | FIFA Calendar API when available | Confederation official sites for missing reports |
| Squads and call-ups | National federations | FIFA match reports, confederations |
| Injuries/suspensions | National federations and official disciplinary reports | Club/league official reports |
| xG/event data | Licensed provider if available | Public provider only if license permits |
| Market odds benchmark | Licensed odds provider | Public odds snapshots if terms permit |

## Degraded Mode

If official FIFA data is unreachable and no cached FIFA payload is available,
the project may run only in degraded mode. Degraded runs cannot be presented as
official competition-state forecasts.

## Source Trust Boundary

The FIFA source reader (`src/copa_forecast/data/sources/fifa.py`) accepts three
kinds of locations: `https://`/`http://` URLs, `file://` URLs, and bare local
paths. Local paths are intentional and load-bearing: they back the cached-payload
flow (`data/raw/...`, enabled by `allow_cached_payloads`) for reproducible and
offline/CI runs, plus the test fixtures used by `configs/example.forecast.json`.

Because local-path reads are a feature, configs are treated as **trusted input**:

- Production configs MUST point their official source URLs to FIFA HTTPS
  endpoints; local paths in production configs are limited to the pipeline's own
  `data/raw/` cache.
- Never feed an untrusted, third-party config into the reader, since a malicious
  `file://`/local path could read arbitrary files. The reader is not a sandbox.
- If this project is ever exposed as a service accepting user-supplied configs,
  add an allow-list (e.g. restrict local reads to `data/raw/` and
  `tests/fixtures/`) before doing so.

## Current Pipeline Coverage

The current implemented pipeline uses official FIFA endpoints for:

- World Cup 2026 fixtures, teams, groups, venues, status, and results.
- Per-team senior men's match history in the configured 12-24 month evidence
  window.

The model does not yet ingest federation squad reports, injuries, suspensions,
or licensed xG/event feeds. Those remain candidate enrichment sources and must
meet the same coverage rule before becoming active model pillars.

## FIFA Power Rankings Assessment

The FIFA Power Rankings page for the 2026 tournament is an official FIFA
surface, so it is valuable as a benchmark and as a narrative validation layer
for the public one-page output. It should not become an automatic model feature
until the project can extract rank data through a stable, structured endpoint
with the same raw-payload storage, checksum, timestamp, and coverage rules used
for the rest of the FIFA ETL.

Current decision:

- Keep `fifa_power_rankings_aramco` as `official_candidate_pending_structured_etl`.
- Use the locally computed FIFA SUM-style prior as the active official-strength
  benchmark because it is reproducible from the same FIFA match records already
  stored by the pipeline.
- Revisit ingestion when the Power Rankings data can be retrieved without
  brittle JavaScript scraping and with coverage for all qualified teams.
