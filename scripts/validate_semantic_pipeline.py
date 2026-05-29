#!/usr/bin/env python3
"""Local checks for the semantic requirements pipeline."""

from __future__ import annotations

import argparse
import csv
import sys
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from semantic_contracts import (  # noqa: E402
    BASELINE_EMBEDDING_DIMENSIONS,
    BASELINE_EMBEDDING_MODEL,
    CLUSTER_ARTIFACT_PATH,
    CLUSTER_K,
    EXPERIMENT_RESULTS_PATH,
    PROJECTION_DIMENSIONS,
    build_payloads,
    load_cluster_artifact,
    load_requirements,
    validate_artifact,
)

TEXT_EXTENSIONS = {".md", ".py", ".txt", ".yml", ".yaml"}
STALE_COMMAND = "load_" + "qdrant.py"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate semantic cluster metadata, docs, and local checks."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=ROOT,
        help="Repository root.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    errors: list[str] = []
    notes: list[str] = []

    requirements = load_requirements(root / "data/earlybird_requirements.json")
    artifact = load_cluster_artifact(root / CLUSTER_ARTIFACT_PATH)
    errors.extend(validate_artifact(artifact, requirements))
    payloads = build_payloads(artifact, artifact.baseline_embedding)

    errors.extend(check_experiment_results(root / EXPERIMENT_RESULTS_PATH))
    errors.extend(check_stale_command_references(root))
    duplicate_notes = find_duplicate_notes(requirements)
    notes.extend(duplicate_notes)

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print("Semantic pipeline validation OK")
    print(f"Requirements: {len(requirements)}")
    print(f"Verified artifact payloads: {len(payloads)}")
    print(f"Clusters: k={CLUSTER_K}")
    print(f"Projection dimensions: {PROJECTION_DIMENSIONS}")
    print(f"Baseline embedding: {BASELINE_EMBEDDING_MODEL}/{BASELINE_EMBEDDING_DIMENSIONS}")
    print("Retrieval precision@k: requires live embeddings and is not run by this local check.")
    if notes:
        for note in notes:
            print(f"NOTE: {note}")
    else:
        print("Duplicate text check: no exact or near-duplicate requirement texts found.")
    return 0


def check_experiment_results(path: Path) -> list[str]:
    if not path.exists():
        return [f"missing experiment results: {path}"]

    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    if not rows:
        return [f"empty experiment results: {path}"]

    top = rows[0]
    errors: list[str] = []
    if top.get("d") != str(PROJECTION_DIMENSIONS):
        errors.append(
            f"top experiment result d={top.get('d')} does not match {PROJECTION_DIMENSIONS}"
        )
    if top.get("k") != str(CLUSTER_K):
        errors.append(f"top experiment result k={top.get('k')} does not match {CLUSTER_K}")
    return errors


def check_stale_command_references(root: Path) -> list[str]:
    offenders: list[str] = []
    this_script = Path(__file__).resolve()
    for path in root.rglob("*"):
        if ".git" in path.parts or not path.is_file():
            continue
        if path.resolve() == this_script:
            continue
        if path.name == "SEMANTIC_MODEL.md":
            continue
        if path.suffix not in TEXT_EXTENSIONS:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if STALE_COMMAND in text:
            offenders.append(str(path.relative_to(root)))
    return [f"stale {STALE_COMMAND} reference in {path}" for path in offenders]


def find_duplicate_notes(requirements: list[object]) -> list[str]:
    notes: list[str] = []
    texts = [(getattr(req, "req_id"), getattr(req, "text")) for req in requirements]
    for idx, (left_id, left_text) in enumerate(texts):
        for right_id, right_text in texts[idx + 1:]:
            if left_text == right_text:
                notes.append(f"exact duplicate text: {left_id} and {right_id}")
                continue
            similarity = SequenceMatcher(None, left_text, right_text).ratio()
            if similarity >= 0.95:
                notes.append(
                    f"near-duplicate text: {left_id} and {right_id} "
                    f"(similarity={similarity:.3f})"
                )
    return notes


if __name__ == "__main__":
    raise SystemExit(main())
