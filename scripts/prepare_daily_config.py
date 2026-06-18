#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a dated forecast config for scheduled daily runs."
    )
    parser.add_argument("--config", required=True, help="Base forecast config JSON.")
    parser.add_argument("--output", required=True, help="Generated config output path.")
    parser.add_argument(
        "--as-of-date",
        required=True,
        help="Forecast cutoff date in YYYY-MM-DD format.",
    )
    parser.add_argument(
        "--run-id",
        help="Optional forecast run id. Defaults to fifa-real-YYYY-MM-DD.",
    )
    parser.add_argument(
        "--github-url",
        help="Optional repository URL to store in public forecast metadata.",
    )
    args = parser.parse_args()

    payload = prepare_daily_config(
        config_path=Path(args.config),
        output_path=Path(args.output),
        as_of_date=args.as_of_date,
        run_id=args.run_id,
        github_url=args.github_url,
    )
    print(
        json.dumps(
            {
                "as_of_date": payload["as_of_date"],
                "run_id": payload["run_id"],
                "output": args.output,
            },
            sort_keys=True,
        )
    )
    return 0


def prepare_daily_config(
    *,
    config_path: Path,
    output_path: Path,
    as_of_date: str,
    run_id: str | None = None,
    github_url: str | None = None,
) -> dict[str, Any]:
    run_date = date.fromisoformat(as_of_date)
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    payload["as_of_date"] = run_date.isoformat()
    payload["run_id"] = run_id or f"fifa-real-{run_date.isoformat()}"
    if github_url:
        payload["project_github_url"] = github_url

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )
    return payload


if __name__ == "__main__":
    raise SystemExit(main())
