# Source Policy

## Official FIFA Sources

Official FIFA data is authoritative for World Cup 2026 competition state:

- Fixtures.
- Teams and groups.
- Venues and kickoff times.
- Match status and results.
- Tournament regulations and advancement rules.
- FIFA rankings when used as an official ranking input.
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

## Current Pipeline Coverage

The current implemented pipeline uses official FIFA endpoints for:

- World Cup 2026 fixtures, teams, groups, venues, status, and results.
- Per-team senior men's match history in the configured 12-24 month evidence
  window.

The model does not yet ingest federation squad reports, injuries, suspensions,
or licensed xG/event feeds. Those remain candidate enrichment sources and must
meet the same coverage rule before becoming active model pillars.
