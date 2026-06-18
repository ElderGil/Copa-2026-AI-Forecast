# Data Directory

This directory stores local, versioned data artifacts for forecast runs.

- `raw/`: source extracts exactly as retrieved.
- `raw/fifa/`: official FIFA extracts exactly as retrieved.
- `raw/fifa_recent_matches/`: official FIFA Calendar team-match extracts.
- `interim/`: normalized intermediate files.
- `processed/`: feature tables, forecast inputs, and model-ready datasets.
- `processed/recent_matches/`: deduped recent-match JSON/CSV and coverage
  reports used by the forecast.

Every usable source must include source metadata: owner or origin, retrieval
date, schema version, license note, and known coverage gaps.

Official FIFA extracts must be stored raw before any parser or normalization
step runs.
