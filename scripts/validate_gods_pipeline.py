#!/usr/bin/env python3
"""Local validation for the dynamic gods plugin pipeline."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from god_team_discovery import (  # noqa: E402
    GOD_TEAM_PATH,
    GOD_TEAM_SCORES_PATH,
    GOD_TEAM_TSNE_PATH,
    K_RANGE,
    discover_god_team,
)


def main() -> int:
    errors: list[str] = []
    discover_god_team(None)

    errors.extend(check_plugin_shape())
    errors.extend(check_god_team_json())
    errors.extend(check_scores_csv())
    errors.extend(check_no_stale_fixed_pipeline())

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    result = json.loads((ROOT / GOD_TEAM_PATH).read_text(encoding="utf-8"))
    print("God Team pipeline validation OK")
    print(f"Plugin: {result['plugin']}")
    print(f"Command: {result['selected_command']}")
    print(f"Optimal team size: {result['optimal_team_size']}")
    print("Selected gods:", ", ".join(member["god"] for member in result["team"]))
    print(f"Scores: {GOD_TEAM_SCORES_PATH}")
    print(f"Visualization: {GOD_TEAM_TSNE_PATH}")
    return 0


def check_plugin_shape() -> list[str]:
    errors: list[str] = []
    manifest_path = ROOT / ".claude-plugin/plugin.json"
    if not manifest_path.exists():
        return ["missing .claude-plugin/plugin.json"]

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("name") != "gods":
        errors.append("plugin manifest name must be gods")
    for skill_name in ["review", "forge", "evolve", "rank"]:
        path = ROOT / "skills" / skill_name / "SKILL.md"
        if not path.exists():
            errors.append(f"missing /gods:{skill_name} skill")
    return errors


def check_god_team_json() -> list[str]:
    path = ROOT / GOD_TEAM_PATH
    if not path.exists():
        return [f"missing {GOD_TEAM_PATH}"]

    result = json.loads(path.read_text(encoding="utf-8"))
    errors: list[str] = []
    required = {
        "plugin",
        "skill",
        "selected_command",
        "optimal_team_size",
        "selection_reason",
        "team",
        "rejected_gods",
        "rejected_team_sizes",
        "axis_coverage",
        "metrics",
        "validation",
        "notes",
    }
    missing = required - set(result)
    if missing:
        errors.append(f"god_team.json missing keys: {sorted(missing)}")
    if result.get("plugin") != "gods":
        errors.append("god_team.json plugin must be gods")
    if result.get("selected_command") != "/gods:review":
        errors.append("god_team.json selected_command must be /gods:review")

    team = result.get("team", [])
    k = result.get("optimal_team_size")
    if k not in K_RANGE:
        errors.append(f"optimal_team_size must be in {min(K_RANGE)}..{max(K_RANGE)}")
    if isinstance(k, int) and len(team) != k:
        errors.append("team length must match optimal_team_size")

    for member in team:
        for key in [
            "god",
            "role",
            "semantic_fit_score",
            "mythic_power_score",
            "coverage_score",
            "non_overlap_score",
            "name_usability_score",
            "final_score",
            "assigned_axes",
            "evidence",
        ]:
            if key not in member:
                errors.append(f"team member missing {key}")
        if not member.get("assigned_axes"):
            errors.append(f"{member.get('god', '<unknown>')} has no assigned axes")
    return errors


def check_scores_csv() -> list[str]:
    path = ROOT / GOD_TEAM_SCORES_PATH
    if not path.exists():
        return [f"missing {GOD_TEAM_SCORES_PATH}"]

    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        return [f"{GOD_TEAM_SCORES_PATH} is empty"]
    found = {int(row["k"]) for row in rows}
    expected = set(K_RANGE)
    if found != expected:
        return [f"score CSV must contain k={min(K_RANGE)}..{max(K_RANGE)}"]
    return []


def check_no_stale_fixed_pipeline() -> list[str]:
    stale_terms = [
        "qdrant",
        "requirements_v1",
        "qdrant_ingest",
        "semantic_text",
        "earlybird_requirements",
    ]
    allowed = {
        ".git",
        "scripts/validate_gods_pipeline.py",
    }
    errors: list[str] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        relative = str(path.relative_to(ROOT))
        if relative.split("/")[0] in allowed or relative in allowed:
            continue
        if path.suffix.lower() not in {".md", ".py", ".json", ".txt", ".csv"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        for term in stale_terms:
            if term in text:
                errors.append(f"stale fixed-pipeline term {term!r} in {relative}")
    return errors


if __name__ == "__main__":
    raise SystemExit(main())
