#!/usr/bin/env python3
"""Shared contracts for the semantic requirements pipeline."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

REQUIREMENTS_PATH = Path("data/earlybird_requirements.json")
CLUSTER_ARTIFACT_PATH = Path("results/qdrant_clusters.json")
EXPERIMENT_RESULTS_PATH = Path("results/experiment_results.csv")

COLLECTION_NAME = "requirements_v1"
VECTOR_NAME = "semantic_text"
DISTANCE = "cosine"

BASELINE_EMBEDDING_MODEL = "text-embedding-3-small"
BASELINE_EMBEDDING_DIMENSIONS = 1536
OPTIONAL_EMBEDDING_CONFIGS = {
    ("text-embedding-3-large", 1024),
    ("text-embedding-3-large", 3072),
}

SEMANTIC_VERSION = "amaterasu-v1"
CLUSTER_MODEL = "bootstrap-kmeans-v1"
CLUSTER_K = 11
PROJECTION_DIMENSIONS = 16
AGENT_OWNER = "Amaterasu"
VERIFIER = "Ma'at"
ALLOWED_STATUS = {"candidate", "verified", "rejected", "deprecated"}


@dataclass(frozen=True)
class Requirement:
    req_id: str
    text: str


@dataclass(frozen=True)
class EmbeddingConfig:
    model: str = BASELINE_EMBEDDING_MODEL
    dimensions: int = BASELINE_EMBEDDING_DIMENSIONS


@dataclass(frozen=True)
class ClusterAssignment:
    req_id: str
    text: str
    source: str
    cluster_id: int
    cluster_label: str
    semantic_version: str
    cluster_model: str
    cluster_k: int
    projection_dimensions: int
    agent_owner: str
    verified_by: str
    status: str
    confidence: float
    evidence: tuple[str, ...]

    @classmethod
    def from_json(cls, item: dict[str, Any], defaults: dict[str, Any]) -> "ClusterAssignment":
        evidence = item.get("evidence", defaults.get("evidence", ()))
        if not isinstance(evidence, list):
            raise ValueError(f"{item.get('req_id', '<unknown>')} evidence must be a list")

        return cls(
            req_id=_require_str(item, "req_id"),
            text=_require_str(item, "text"),
            source=_str_value(item, "source", defaults["source"]),
            cluster_id=_require_int(item, "cluster_id"),
            cluster_label=_require_str(item, "cluster_label"),
            semantic_version=_str_value(item, "semantic_version", defaults["semantic_version"]),
            cluster_model=_str_value(item, "cluster_model", defaults["cluster_model"]),
            cluster_k=_int_value(item, "cluster_k", defaults["cluster_k"]),
            projection_dimensions=_int_value(
                item,
                "projection_dimensions",
                defaults["projection_dimensions"],
            ),
            agent_owner=_str_value(item, "agent_owner", defaults["agent_owner"]),
            verified_by=_str_value(item, "verified_by", defaults["verified_by"]),
            status=_str_value(item, "status", defaults["status"]),
            confidence=_float_value(item, "confidence", defaults["confidence"]),
            evidence=tuple(str(entry) for entry in evidence),
        )

    def to_payload(self, embedding: EmbeddingConfig) -> dict[str, Any]:
        return {
            "req_id": self.req_id,
            "text": self.text,
            "source": self.source,
            "cluster_id": self.cluster_id,
            "cluster_label": self.cluster_label,
            "semantic_version": self.semantic_version,
            "embedding_model": embedding.model,
            "embedding_dimensions": embedding.dimensions,
            "cluster_model": self.cluster_model,
            "cluster_k": self.cluster_k,
            "projection_dimensions": self.projection_dimensions,
            "agent_owner": self.agent_owner,
            "verified_by": self.verified_by,
            "verifier": self.verified_by,
            "status": self.status,
            "confidence": self.confidence,
            "evidence": list(self.evidence),
        }


@dataclass(frozen=True)
class ClusterArtifact:
    schema_version: int
    semantic_version: str
    source: str
    collection_name: str
    vector_name: str
    distance: str
    baseline_embedding: EmbeddingConfig
    cluster_model: str
    cluster_k: int
    projection_dimensions: int
    agent_owner: str
    verifier: str
    status: str
    confidence: float
    evidence: tuple[str, ...]
    assignments: tuple[ClusterAssignment, ...]


def load_requirements(path: Path = REQUIREMENTS_PATH) -> list[Requirement]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError(f"{path} must contain a JSON list")

    return [
        Requirement(req_id=_require_str(item, "id"), text=_require_str(item, "text"))
        for item in raw
    ]


def load_cluster_artifact(path: Path = CLUSTER_ARTIFACT_PATH) -> ClusterArtifact:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"{path} must contain a JSON object")

    qdrant = _require_dict(raw, "qdrant")
    embedding = _require_dict(raw, "embedding")
    clustering = _require_dict(raw, "clustering")
    review = _require_dict(raw, "agent_review")
    assignments_raw = raw.get("requirements")
    if not isinstance(assignments_raw, list):
        raise ValueError(f"{path} must contain a requirements list")

    defaults = {
        "source": _str_value(raw, "source", str(REQUIREMENTS_PATH)),
        "semantic_version": _str_value(raw, "semantic_version", SEMANTIC_VERSION),
        "cluster_model": _str_value(clustering, "cluster_model", CLUSTER_MODEL),
        "cluster_k": _int_value(clustering, "cluster_k", CLUSTER_K),
        "projection_dimensions": _int_value(
            clustering,
            "projection_dimensions",
            PROJECTION_DIMENSIONS,
        ),
        "agent_owner": _str_value(review, "semantic_discovery", AGENT_OWNER),
        "verified_by": _str_value(review, "verifier", VERIFIER),
        "status": _str_value(review, "status", "candidate"),
        "confidence": _float_value(review, "confidence", 0.0),
        "evidence": review.get("evidence", []),
    }

    baseline = EmbeddingConfig(
        model=_str_value(embedding, "baseline_model", BASELINE_EMBEDDING_MODEL),
        dimensions=_int_value(
            embedding,
            "baseline_dimensions",
            BASELINE_EMBEDDING_DIMENSIONS,
        ),
    )

    return ClusterArtifact(
        schema_version=_int_value(raw, "schema_version", 1),
        semantic_version=defaults["semantic_version"],
        source=defaults["source"],
        collection_name=_str_value(qdrant, "collection", COLLECTION_NAME),
        vector_name=_str_value(qdrant, "vector_name", VECTOR_NAME),
        distance=_str_value(qdrant, "distance", DISTANCE),
        baseline_embedding=baseline,
        cluster_model=defaults["cluster_model"],
        cluster_k=defaults["cluster_k"],
        projection_dimensions=defaults["projection_dimensions"],
        agent_owner=defaults["agent_owner"],
        verifier=defaults["verified_by"],
        status=defaults["status"],
        confidence=defaults["confidence"],
        evidence=tuple(str(entry) for entry in defaults["evidence"]),
        assignments=tuple(
            ClusterAssignment.from_json(item, defaults)
            for item in assignments_raw
        ),
    )


def validate_embedding_config(config: EmbeddingConfig) -> list[str]:
    if (
        config.model == BASELINE_EMBEDDING_MODEL
        and config.dimensions == BASELINE_EMBEDDING_DIMENSIONS
    ):
        return []
    if (config.model, config.dimensions) in OPTIONAL_EMBEDDING_CONFIGS:
        return []
    return [
        "embedding config must be text-embedding-3-small/1536 or optional "
        "text-embedding-3-large at 1024 or 3072 dimensions"
    ]


def validate_artifact(
    artifact: ClusterArtifact,
    requirements: Iterable[Requirement],
) -> list[str]:
    errors: list[str] = []
    by_id = {req.req_id: req for req in requirements}
    seen_ids: set[str] = set()

    _expect(errors, artifact.schema_version == 1, "schema_version must be 1")
    _expect(errors, artifact.semantic_version == SEMANTIC_VERSION, "semantic_version mismatch")
    _expect(errors, artifact.source == str(REQUIREMENTS_PATH), "source path mismatch")
    _expect(errors, artifact.collection_name == COLLECTION_NAME, "Qdrant collection mismatch")
    _expect(errors, artifact.vector_name == VECTOR_NAME, "Qdrant vector name mismatch")
    _expect(errors, artifact.distance == DISTANCE, "Qdrant distance mismatch")
    _expect(errors, artifact.cluster_model == CLUSTER_MODEL, "cluster model mismatch")
    _expect(errors, artifact.cluster_k == CLUSTER_K, "cluster_k mismatch")
    _expect(
        errors,
        artifact.projection_dimensions == PROJECTION_DIMENSIONS,
        "projection dimensions mismatch",
    )
    _expect(errors, artifact.agent_owner == AGENT_OWNER, "agent owner mismatch")
    _expect(errors, artifact.verifier == VERIFIER, "verifier mismatch")
    errors.extend(validate_embedding_config(artifact.baseline_embedding))

    cluster_ids = {assignment.cluster_id for assignment in artifact.assignments}
    _expect(
        errors,
        len(artifact.assignments) == len(by_id),
        "artifact requirement count does not match raw requirements",
    )
    _expect(
        errors,
        cluster_ids == set(range(artifact.cluster_k)),
        f"cluster ids must cover 0..{artifact.cluster_k - 1}",
    )

    for assignment in artifact.assignments:
        if assignment.req_id in seen_ids:
            errors.append(f"duplicate requirement in artifact: {assignment.req_id}")
        seen_ids.add(assignment.req_id)

        source = by_id.get(assignment.req_id)
        if source is None:
            errors.append(f"artifact references unknown requirement: {assignment.req_id}")
            continue
        if assignment.text != source.text:
            errors.append(f"text mismatch for {assignment.req_id}")
        if assignment.source != artifact.source:
            errors.append(f"source mismatch for {assignment.req_id}")
        if assignment.semantic_version != artifact.semantic_version:
            errors.append(f"semantic version mismatch for {assignment.req_id}")
        if assignment.cluster_model != artifact.cluster_model:
            errors.append(f"cluster model mismatch for {assignment.req_id}")
        if assignment.cluster_k != artifact.cluster_k:
            errors.append(f"cluster_k mismatch for {assignment.req_id}")
        if assignment.projection_dimensions != artifact.projection_dimensions:
            errors.append(f"projection dimensions mismatch for {assignment.req_id}")
        if assignment.agent_owner != artifact.agent_owner:
            errors.append(f"agent owner mismatch for {assignment.req_id}")
        if assignment.verified_by != artifact.verifier:
            errors.append(f"verifier mismatch for {assignment.req_id}")
        if assignment.status not in ALLOWED_STATUS:
            errors.append(f"invalid status for {assignment.req_id}: {assignment.status}")
        if not 0.0 <= assignment.confidence <= 1.0:
            errors.append(f"confidence outside [0, 1] for {assignment.req_id}")
        if not assignment.cluster_label:
            errors.append(f"empty cluster label for {assignment.req_id}")

    missing_ids = set(by_id) - seen_ids
    for req_id in sorted(missing_ids, key=stable_req_sort_key):
        errors.append(f"artifact is missing requirement: {req_id}")

    return errors


def build_payloads(
    artifact: ClusterArtifact,
    embedding: EmbeddingConfig,
) -> list[dict[str, Any]]:
    return [assignment.to_payload(embedding) for assignment in artifact.assignments]


def stable_point_id(req_id: str) -> int:
    if len(req_id) < 2 or not req_id[1:].isdigit():
        raise ValueError(f"Requirement id {req_id!r} cannot be converted to a Qdrant integer id")
    return int(req_id[1:])


def stable_req_sort_key(req_id: str) -> tuple[int, str]:
    if len(req_id) >= 2 and req_id[1:].isdigit():
        return int(req_id[1:]), req_id
    return 999_999, req_id


def _require_dict(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"{key} must be an object")
    return value


def _require_str(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{key} must be a non-empty string")
    return value


def _require_int(data: dict[str, Any], key: str) -> int:
    value = data.get(key)
    if not isinstance(value, int):
        raise ValueError(f"{key} must be an integer")
    return value


def _str_value(data: dict[str, Any], key: str, default: str) -> str:
    value = data.get(key, default)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{key} must be a non-empty string")
    return value


def _int_value(data: dict[str, Any], key: str, default: int) -> int:
    value = data.get(key, default)
    if not isinstance(value, int):
        raise ValueError(f"{key} must be an integer")
    return value


def _float_value(data: dict[str, Any], key: str, default: float) -> float:
    value = data.get(key, default)
    if isinstance(value, int):
        return float(value)
    if not isinstance(value, float):
        raise ValueError(f"{key} must be numeric")
    return value


def _expect(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)
