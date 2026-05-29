#!/usr/bin/env python3
"""CLI entry point for dynamic God Team discovery."""

from __future__ import annotations

import argparse
import json

from god_team_discovery import GOD_TEAM_PATH, discover_god_team


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Discover the smallest powerful God Team for a skill or workflow."
    )
    parser.add_argument(
        "--skill",
        help=(
            "Skill markdown path or free-form skill/task text. Defaults to the "
            "thermo-nuclear code-quality review example."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the full God Team JSON after writing artifacts.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = discover_god_team(args.skill)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(
            f"Selected {result['optimal_team_size']} gods for {result['skill']} "
            f"using {result['command']}."
        )
        print(f"Wrote {GOD_TEAM_PATH}")
        print("Team:", ", ".join(member["god"] for member in result["team"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
