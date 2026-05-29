#!/usr/bin/env python3
"""Local validation for the dynamic gods plugin pipeline."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from god_team_discovery import (  # noqa: E402
    AXES_PATH,
    GODS_PATH,
    GOD_TEAM_PATH,
    GOD_TEAM_SCORES_PATH,
    GOD_TEAM_TSNE_PATH,
    K_RANGE,
    discover_god_team,
)

REQUIRED_AXES = {
    "structural_simplification",
    "code_judo_deletion",
    "spaghetti_detection",
    "file_size_boundary",
    "abstraction_quality",
    "type_boundary_cleanliness",
    "canonical_layer_ownership",
    "orchestration_atomicity",
    "output_prioritization",
    "tone_enforcement",
    "approval_bar",
}
REQUIRED_GODS = {
    "Athena",
    "Shiva",
    "Hephaestus",
    "Ma'at",
    "Themis",
    "Tyr",
    "Odin",
    "Hermes",
    "Janus",
    "Apollo",
    "Thoth",
    "Hades",
    "Anubis",
    "Ptah",
    "Vishvakarma",
    "Saraswati",
    "Kali",
    "Heimdall",
    "Prometheus",
    "Ganesh",
    "Loki",
    "Ra",
    "Amaterasu",
    "Minerva",
    "Vulcan",
    "Forseti",
    "Ares",
}
PROFILE_FIELDS = {
    "name",
    "pantheon",
    "domains",
    "workflow_affinity",
    "mythic_power_score",
    "name_usability_score",
    "role_hint",
    "evidence_notes",
}


def main() -> int:
    args = parse_args()
    errors: list[str] = []
    discover_god_team(args.skill)

    errors.extend(check_plugin_shape())
    errors.extend(check_source_data())
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
    print(f"Command: {result['command']}")
    print(f"Optimal team size: {result['optimal_team_size']}")
    print("Selected gods:", ", ".join(member["god"] for member in result["team"]))
    print(f"Scores: {GOD_TEAM_SCORES_PATH}")
    print(f"Visualization: {GOD_TEAM_TSNE_PATH}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate the gods discovery pipeline.")
    parser.add_argument(
        "--skill",
        help="Optional skill markdown path or inline task to validate instead of the default example.",
    )
    return parser.parse_args()


def check_plugin_shape() -> list[str]:
    errors: list[str] = []
    manifest_path = ROOT / ".claude-plugin/plugin.json"
    if not manifest_path.exists():
        return ["missing .claude-plugin/plugin.json"]

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("name") != "gods":
        errors.append("plugin manifest name must be gods")
    for skill_name in ["review", "nihil", "forge", "evolve", "rank"]:
        path = ROOT / "skills" / skill_name / "SKILL.md"
        if not path.exists():
            errors.append(f"missing /gods:{skill_name} skill")
    return errors


def check_source_data() -> list[str]:
    errors: list[str] = []
    axes = json.loads((ROOT / AXES_PATH).read_text(encoding="utf-8"))
    axis_ids = {axis.get("id") for axis in axes}
    missing_axes = REQUIRED_AXES - axis_ids
    if missing_axes:
        errors.append(f"workflow axes missing required IDs: {sorted(missing_axes)}")
    if len(axes) < max(K_RANGE):
        errors.append(f"workflow axes must support k={max(K_RANGE)}")

    gods = json.loads((ROOT / GODS_PATH).read_text(encoding="utf-8"))
    god_names = {god.get("name") for god in gods}
    missing_gods = REQUIRED_GODS - god_names
    if missing_gods:
        errors.append(f"candidate corpus missing required gods: {sorted(missing_gods)}")
    for god in gods:
        missing_fields = PROFILE_FIELDS - set(god)
        if missing_fields:
            errors.append(f"{god.get('name', '<unknown>')} missing profile fields: {sorted(missing_fields)}")
        for field in ["mythic_power_score", "name_usability_score"]:
            value = god.get(field)
            if not isinstance(value, (int, float)) or not 0.0 <= float(value) <= 1.0:
                errors.append(f"{god.get('name', '<unknown>')} {field} must be a 0..1 score")
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
        "skill_name",
        "command",
        "selected_gods",
        "optimal_team_size",
        "selection_reason",
        "team",
        "rejected_gods",
        "rejected_team_sizes",
        "role_assignments",
        "score_breakdowns",
        "axis_coverage",
        "metrics",
        "validation",
        "blocked_validations",
        "notes",
    }
    missing = required - set(result)
    if missing:
        errors.append(f"god_team.json missing keys: {sorted(missing)}")
    if result.get("plugin") != "gods":
        errors.append("god_team.json plugin must be gods")
    if result.get("command") != "/gods:review":
        errors.append("god_team.json command must be /gods:review")

    team = result.get("team", [])
    k = result.get("optimal_team_size")
    if k not in K_RANGE:
        errors.append(f"optimal_team_size must be in {min(K_RANGE)}..{max(K_RANGE)}")
    if isinstance(k, int) and len(team) != k:
        errors.append("team length must match optimal_team_size")
    if isinstance(result.get("selected_gods"), list) and len(result["selected_gods"]) != len(team):
        errors.append("selected_gods length must match team length")

    for member in team:
        for key in [
            "god",
            "role",
            "semantic_fit_score",
            "workflow_coverage_score",
            "non_overlap_score",
            "mythic_power_score",
            "name_usability_score",
            "evidence_score",
            "final_score",
            "assigned_axes",
            "evidence_notes",
        ]:
            if key not in member:
                errors.append(f"team member missing {key}")
        if not member.get("assigned_axes"):
            errors.append(f"{member.get('god', '<unknown>')} has no assigned axes")
    if not result.get("role_assignments"):
        errors.append("role_assignments must not be empty")
    if not result.get("score_breakdowns"):
        errors.append("score_breakdowns must not be empty")
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
