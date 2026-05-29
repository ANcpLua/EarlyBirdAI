#!/usr/bin/env python3
"""Dynamic God Team discovery for workflow skills."""

from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.manifold import TSNE
from sklearn.metrics import silhouette_score
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.utils import resample

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    PLOTTING_ENABLED = True
except ImportError:
    plt = None  # type: ignore[assignment]
    PLOTTING_ENABLED = False

PLUGIN_NAME = "gods"
SELECTED_COMMAND = "/gods:review"
DEFAULT_SKILL_PATH = Path("examples/thermo-nuclear-code-quality-review.md")
AXES_PATH = Path("data/workflow_axes.json")
GODS_PATH = Path("data/candidate_gods.json")
RESULTS_DIR = Path("results")
VISUALIZATIONS_DIR = Path("visualizations")
GOD_TEAM_PATH = RESULTS_DIR / "god_team.json"
GOD_TEAM_SCORES_PATH = RESULTS_DIR / "god_team_scores.csv"
GOD_TEAM_TSNE_PATH = VISUALIZATIONS_DIR / "god_team_tsne.png"
K_RANGE = range(3, 13)
RANDOM_STATE = 42
SMALLEST_TEAM_MARGIN = 0.025
MIN_COVERAGE_RETENTION = 0.96


@dataclass(frozen=True)
class WorkflowAxis:
    axis_id: str
    label: str
    description: str
    keywords: tuple[str, ...]

    @classmethod
    def from_json(cls, item: dict[str, Any]) -> "WorkflowAxis":
        return cls(
            axis_id=require_str(item, "id"),
            label=require_str(item, "label"),
            description=require_str(item, "description"),
            keywords=tuple(str(keyword).lower() for keyword in item.get("keywords", [])),
        )

    @property
    def embedding_text(self) -> str:
        return " ".join([self.axis_id, self.label, self.description, *self.keywords])


@dataclass(frozen=True)
class CandidateGod:
    name: str
    pantheon: str
    domains: tuple[str, ...]
    workflow_affinity: tuple[str, ...]
    mythic_power: float
    name_usability: float
    role_hint: str
    notes: str

    @classmethod
    def from_json(cls, item: dict[str, Any]) -> "CandidateGod":
        return cls(
            name=require_str(item, "name"),
            pantheon=require_str(item, "pantheon"),
            domains=tuple(str(value) for value in item.get("domains", [])),
            workflow_affinity=tuple(str(value) for value in item.get("workflow_affinity", [])),
            mythic_power=require_score(item, "mythic_power"),
            name_usability=require_score(item, "name_usability"),
            role_hint=require_str(item, "role_hint"),
            notes=require_str(item, "notes"),
        )

    @property
    def embedding_text(self) -> str:
        return " ".join(
            [
                self.name,
                self.pantheon,
                *self.domains,
                *self.workflow_affinity,
                self.role_hint,
                self.notes,
            ]
        )


@dataclass(frozen=True)
class SelectedGod:
    god: CandidateGod
    assigned_axes: tuple[WorkflowAxis, ...]
    semantic_fit_score: float
    coverage_score: float
    non_overlap_score: float
    evidence_score: float
    final_score: float


@dataclass(frozen=True)
class TeamCandidate:
    k: int
    selected: tuple[SelectedGod, ...]
    team_coverage: float
    team_separation: float
    team_power: float
    team_overlap_penalty: float
    team_name_quality: float
    team_complexity_penalty: float
    silhouette: float | None
    bootstrap_stability: float | None
    score: float


def discover_god_team(
    skill_input: str | None,
    axes_path: Path = AXES_PATH,
    gods_path: Path = GODS_PATH,
) -> dict[str, Any]:
    skill_name, skill_text = read_skill_input(skill_input)
    axes = extract_axes(skill_text, load_axes(axes_path))
    gods = load_candidate_gods(gods_path)
    vectorizer, axis_vectors, god_vectors = embed_axes_and_gods(axes, gods)

    candidates = [
        evaluate_team_size(k, axes, gods, axis_vectors, god_vectors)
        for k in K_RANGE
        if k <= len(axes)
    ]
    if not candidates:
        raise ValueError("no candidate team sizes could be evaluated")

    best_score = max(candidate.score for candidate in candidates)
    best_coverage = max(candidate.team_coverage for candidate in candidates)
    acceptable = [
        candidate
        for candidate in candidates
        if candidate.score >= best_score - SMALLEST_TEAM_MARGIN
        and candidate.team_coverage >= best_coverage * MIN_COVERAGE_RETENTION
    ]
    if not acceptable:
        acceptable = [max(candidates, key=lambda candidate: candidate.score)]
    winner = min(acceptable, key=lambda candidate: candidate.k)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    VISUALIZATIONS_DIR.mkdir(parents=True, exist_ok=True)
    write_scores(candidates, GOD_TEAM_SCORES_PATH)
    visualization_note = write_tsne_visualization(
        axes,
        gods,
        axis_vectors,
        god_vectors,
        winner,
        GOD_TEAM_TSNE_PATH,
    )

    output = build_output(skill_name, axes, gods, candidates, winner, visualization_note)
    GOD_TEAM_PATH.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    return output


def read_skill_input(skill_input: str | None) -> tuple[str, str]:
    if skill_input:
        path = Path(skill_input)
        if path.exists() and path.is_file():
            return slug_from_path(path), path.read_text(encoding="utf-8")
        return "inline-skill", skill_input

    return (
        DEFAULT_SKILL_PATH.stem,
        DEFAULT_SKILL_PATH.read_text(encoding="utf-8"),
    )


def load_axes(path: Path) -> list[WorkflowAxis]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError(f"{path} must contain a list")
    return [WorkflowAxis.from_json(item) for item in raw]


def load_candidate_gods(path: Path) -> list[CandidateGod]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError(f"{path} must contain a list")
    gods = [CandidateGod.from_json(item) for item in raw]
    if len(gods) < max(K_RANGE):
        raise ValueError(f"{path} must contain at least {max(K_RANGE)} candidate gods")
    return gods


def extract_axes(skill_text: str, known_axes: list[WorkflowAxis]) -> tuple[WorkflowAxis, ...]:
    normalized = skill_text.lower().replace("_", " ").replace("-", " ")
    scored: list[tuple[int, WorkflowAxis]] = []
    for axis in known_axes:
        score = 0
        for keyword in axis.keywords:
            if keyword.lower() in normalized:
                score += 1
        for token in axis.axis_id.split("_"):
            if token in normalized:
                score += 1
        if axis.label.lower() in normalized:
            score += 2
        scored.append((score, axis))

    selected = [axis for score, axis in scored if score > 0]
    if len(selected) < 3:
        selected = [axis for _, axis in scored]
    return tuple(selected)


def embed_axes_and_gods(
    axes: tuple[WorkflowAxis, ...],
    gods: list[CandidateGod],
) -> tuple[TfidfVectorizer, np.ndarray, np.ndarray]:
    corpus = [axis.embedding_text for axis in axes] + [god.embedding_text for god in gods]
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
    matrix = vectorizer.fit_transform(corpus).astype(np.float64).toarray()
    return vectorizer, matrix[: len(axes)], matrix[len(axes):]


def evaluate_team_size(
    k: int,
    axes: tuple[WorkflowAxis, ...],
    gods: list[CandidateGod],
    axis_vectors: np.ndarray,
    god_vectors: np.ndarray,
) -> TeamCandidate:
    labels = cluster_axes(axis_vectors, k, RANDOM_STATE)
    selected: list[SelectedGod] = []
    used_god_indexes: set[int] = set()
    axis_to_god_similarity = cosine_similarity(axis_vectors, god_vectors)

    for cluster_id in range(k):
        axis_indexes = [index for index, label in enumerate(labels) if label == cluster_id]
        cluster_axis_vectors = axis_vectors[axis_indexes]
        centroid = cluster_axis_vectors.mean(axis=0, keepdims=True)
        god_fit = cosine_similarity(centroid, god_vectors)[0]

        god_index = choose_god(gods, god_vectors, god_fit, used_god_indexes)
        used_god_indexes.add(god_index)
        cluster_axes_for_god = tuple(axes[index] for index in axis_indexes)

        semantic_fit = float(god_fit[god_index])
        coverage = float(axis_to_god_similarity[axis_indexes, god_index].mean())
        non_overlap = estimate_non_overlap(god_index, used_god_indexes, god_vectors)
        evidence_score = evidence_for_axes(gods[god_index], cluster_axes_for_god)
        final_score = score_god(gods[god_index], semantic_fit, coverage, non_overlap, evidence_score)
        selected.append(
            SelectedGod(
                god=gods[god_index],
                assigned_axes=cluster_axes_for_god,
                semantic_fit_score=semantic_fit,
                coverage_score=coverage,
                non_overlap_score=non_overlap,
                evidence_score=evidence_score,
                final_score=final_score,
            )
        )

    selected_tuple = tuple(sorted(selected, key=lambda item: item.final_score, reverse=True))
    selected_indexes = [gods.index(item.god) for item in selected_tuple]
    team_coverage = float(np.max(axis_to_god_similarity[:, selected_indexes], axis=1).mean())
    team_power = float(np.mean([item.god.mythic_power for item in selected_tuple]))
    team_name_quality = float(np.mean([item.god.name_usability for item in selected_tuple]))
    team_overlap_penalty = average_pairwise_similarity(god_vectors[selected_indexes])
    team_separation = 1.0 - team_overlap_penalty
    complexity_penalty = (k - min(K_RANGE)) / (max(K_RANGE) - min(K_RANGE))
    silhouette = compute_silhouette(axis_vectors, labels)
    bootstrap_stability = compute_bootstrap_stability(axis_vectors, k, labels)
    normalized_silhouette = 0.5 if silhouette is None else (silhouette + 1.0) / 2.0
    stability_score = 0.5 if bootstrap_stability is None else bootstrap_stability

    score = (
        0.30 * team_coverage
        + 0.20 * team_separation
        + 0.15 * team_power
        + 0.10 * team_name_quality
        + 0.15 * normalized_silhouette
        + 0.05 * stability_score
        - 0.05 * complexity_penalty
    )

    return TeamCandidate(
        k=k,
        selected=selected_tuple,
        team_coverage=team_coverage,
        team_separation=team_separation,
        team_power=team_power,
        team_overlap_penalty=team_overlap_penalty,
        team_name_quality=team_name_quality,
        team_complexity_penalty=complexity_penalty,
        silhouette=silhouette,
        bootstrap_stability=bootstrap_stability,
        score=score,
    )


def cluster_axes(axis_vectors: np.ndarray, k: int, random_state: int) -> np.ndarray:
    model = KMeans(n_clusters=k, random_state=random_state, n_init=25)
    return model.fit_predict(axis_vectors)


def choose_god(
    gods: list[CandidateGod],
    god_vectors: np.ndarray,
    god_fit: np.ndarray,
    used_indexes: set[int],
) -> int:
    scores: list[tuple[float, int]] = []
    for index, god in enumerate(gods):
        if index in used_indexes:
            continue
        if used_indexes:
            overlap = float(cosine_similarity(god_vectors[index:index + 1], god_vectors[list(used_indexes)]).max())
        else:
            overlap = 0.0
        score = (
            0.55 * float(god_fit[index])
            + 0.20 * god.mythic_power
            + 0.15 * god.name_usability
            + 0.10 * (1.0 - overlap)
        )
        scores.append((score, index))
    return max(scores)[1]


def estimate_non_overlap(
    god_index: int,
    used_indexes: set[int],
    god_vectors: np.ndarray,
) -> float:
    others = [index for index in used_indexes if index != god_index]
    if not others:
        return 1.0
    overlap = float(cosine_similarity(god_vectors[god_index:god_index + 1], god_vectors[others]).max())
    return max(0.0, 1.0 - overlap)


def evidence_for_axes(god: CandidateGod, axes: tuple[WorkflowAxis, ...]) -> float:
    profile_text = god.embedding_text.lower()
    if not axes:
        return 0.0
    matched = 0
    for axis in axes:
        if any(keyword in profile_text for keyword in axis.keywords):
            matched += 1
    return matched / len(axes)


def score_god(
    god: CandidateGod,
    semantic_fit: float,
    coverage: float,
    non_overlap: float,
    evidence_score: float,
) -> float:
    return (
        0.40 * semantic_fit
        + 0.20 * coverage
        + 0.15 * non_overlap
        + 0.15 * god.mythic_power
        + 0.05 * god.name_usability
        + 0.05 * evidence_score
    )


def compute_silhouette(axis_vectors: np.ndarray, labels: np.ndarray) -> float | None:
    if len(set(labels)) < 2 or len(set(labels)) >= len(axis_vectors):
        return None
    return float(silhouette_score(axis_vectors, labels, metric="cosine"))


def compute_bootstrap_stability(
    axis_vectors: np.ndarray,
    k: int,
    reference_labels: np.ndarray,
    iterations: int = 50,
) -> float | None:
    if len(axis_vectors) <= k:
        return None

    scores: list[float] = []
    sample_size = max(k + 1, math.ceil(len(axis_vectors) * 0.8))
    for index in range(iterations):
        sample_indexes = sorted(
            set(
                resample(
                    np.arange(len(axis_vectors)),
                    n_samples=sample_size,
                    random_state=RANDOM_STATE + index,
                    replace=True,
                )
            )
        )
        if len(sample_indexes) <= k:
            continue
        sample_vectors = axis_vectors[sample_indexes]
        labels = cluster_axes(sample_vectors, k, RANDOM_STATE + index)
        reference = reference_labels[sample_indexes]
        scores.append(pair_agreement(reference, labels))
    if not scores:
        return None
    return float(np.mean(scores))


def pair_agreement(left: np.ndarray, right: np.ndarray) -> float:
    total = 0
    matches = 0
    for i in range(len(left)):
        for j in range(i + 1, len(left)):
            total += 1
            if (left[i] == left[j]) == (right[i] == right[j]):
                matches += 1
    return matches / total if total else 0.0


def average_pairwise_similarity(vectors: np.ndarray) -> float:
    if len(vectors) < 2:
        return 0.0
    similarities = cosine_similarity(vectors)
    values = [
        similarities[i, j]
        for i in range(len(vectors))
        for j in range(i + 1, len(vectors))
    ]
    return float(np.mean(values)) if values else 0.0


def write_scores(candidates: list[TeamCandidate], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            lineterminator="\n",
            fieldnames=[
                "k",
                "score",
                "team_coverage",
                "team_separation",
                "team_power",
                "team_overlap_penalty",
                "team_name_quality",
                "team_complexity_penalty",
                "silhouette",
                "bootstrap_stability",
                "selected_gods",
            ],
        )
        writer.writeheader()
        for candidate in sorted(candidates, key=lambda item: item.score, reverse=True):
            writer.writerow(
                {
                    "k": candidate.k,
                    "score": round(candidate.score, 4),
                    "team_coverage": round(candidate.team_coverage, 4),
                    "team_separation": round(candidate.team_separation, 4),
                    "team_power": round(candidate.team_power, 4),
                    "team_overlap_penalty": round(candidate.team_overlap_penalty, 4),
                    "team_name_quality": round(candidate.team_name_quality, 4),
                    "team_complexity_penalty": round(candidate.team_complexity_penalty, 4),
                    "silhouette": format_optional(candidate.silhouette),
                    "bootstrap_stability": format_optional(candidate.bootstrap_stability),
                    "selected_gods": "|".join(item.god.name for item in candidate.selected),
                }
            )


def write_tsne_visualization(
    axes: tuple[WorkflowAxis, ...],
    gods: list[CandidateGod],
    axis_vectors: np.ndarray,
    god_vectors: np.ndarray,
    winner: TeamCandidate,
    path: Path,
) -> str:
    if not PLOTTING_ENABLED:
        return "Matplotlib unavailable; t-SNE visualization was skipped."

    selected_names = {item.god.name for item in winner.selected}
    selected_indexes = [index for index, god in enumerate(gods) if god.name in selected_names]
    vectors = np.vstack([axis_vectors, god_vectors[selected_indexes]])
    labels = [axis.axis_id for axis in axes] + [gods[index].name for index in selected_indexes]
    kinds = ["axis"] * len(axes) + ["god"] * len(selected_indexes)

    perplexity = max(2, min(5, len(vectors) - 1))
    points = TSNE(
        n_components=2,
        random_state=RANDOM_STATE,
        init="random",
        learning_rate="auto",
        perplexity=perplexity,
    ).fit_transform(vectors)

    _, ax = plt.subplots(figsize=(12, 8))
    for kind, marker, color in [("axis", "o", "#3b82f6"), ("god", "^", "#b91c1c")]:
        indexes = [index for index, value in enumerate(kinds) if value == kind]
        ax.scatter(
            points[indexes, 0],
            points[indexes, 1],
            marker=marker,
            color=color,
            label=kind,
            s=90,
            alpha=0.85,
        )

    for index, label in enumerate(labels):
        ax.annotate(label, (points[index, 0], points[index, 1]), fontsize=8)

    ax.set_title("God Team t-SNE visualization")
    ax.set_xlabel("t-SNE 1")
    ax.set_ylabel("t-SNE 2")
    ax.grid(True, alpha=0.25)
    ax.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()
    return f"t-SNE visualization written to {path}."


def build_output(
    skill_name: str,
    axes: tuple[WorkflowAxis, ...],
    gods: list[CandidateGod],
    candidates: list[TeamCandidate],
    winner: TeamCandidate,
    visualization_note: str,
) -> dict[str, Any]:
    selected_names = {item.god.name for item in winner.selected}
    rejected_gods = [
        {
            "god": god.name,
            "reason": "lower marginal coverage or higher overlap for this skill run",
        }
        for god in gods
        if god.name not in selected_names
    ]
    rejected_sizes = [
        {
            "k": candidate.k,
            "score": round(candidate.score, 4),
            "reason": rejected_size_reason(candidate, winner),
        }
        for candidate in sorted(candidates, key=lambda item: item.k)
        if candidate.k != winner.k
    ]
    team = [
        {
            "god": item.god.name,
            "role": item.god.role_hint,
            "semantic_fit_score": round(item.semantic_fit_score, 4),
            "mythic_power_score": round(item.god.mythic_power, 4),
            "coverage_score": round(item.coverage_score, 4),
            "non_overlap_score": round(item.non_overlap_score, 4),
            "name_usability_score": round(item.god.name_usability, 4),
            "evidence_score": round(item.evidence_score, 4),
            "final_score": round(item.final_score, 4),
            "assigned_axes": [axis.axis_id for axis in item.assigned_axes],
            "evidence": [
                item.god.notes,
                "Assigned by embedding similarity between skill axes and candidate god profile.",
            ],
        }
        for item in winner.selected
    ]

    return {
        "plugin": PLUGIN_NAME,
        "skill": skill_name,
        "selected_command": SELECTED_COMMAND,
        "optimal_team_size": winner.k,
        "selection_reason": (
            "Smallest team within "
            f"{SMALLEST_TEAM_MARGIN:.3f} of the best score while balancing coverage, "
            f"retaining at least {MIN_COVERAGE_RETENTION:.0%} of the best coverage, "
            "separation, mythic power, name usability, silhouette, and stability."
        ),
        "team": team,
        "rejected_gods": rejected_gods,
        "rejected_team_sizes": rejected_sizes,
        "axis_coverage": [axis.axis_id for axis in axes],
        "metrics": {
            "team_coverage": round(winner.team_coverage, 4),
            "team_separation": round(winner.team_separation, 4),
            "team_power": round(winner.team_power, 4),
            "team_overlap_penalty": round(winner.team_overlap_penalty, 4),
            "team_name_quality": round(winner.team_name_quality, 4),
            "team_complexity_penalty": round(winner.team_complexity_penalty, 4),
            "silhouette": round(winner.silhouette, 4) if winner.silhouette is not None else None,
            "bootstrap_stability": (
                round(winner.bootstrap_stability, 4)
                if winner.bootstrap_stability is not None
                else None
            ),
        },
        "validation": {
            "tsne_visual_support": (
                "Generated for visual inspection only; inspect the PNG for neighborhood sanity."
            ),
            "silhouette_support": silhouette_support(winner.silhouette),
            "bootstrap_stability_support": stability_support(winner.bootstrap_stability),
            "smaller_than_redundant_team": any(
                candidate.k > winner.k and candidate.score <= winner.score + SMALLEST_TEAM_MARGIN
                for candidate in candidates
            ),
        },
        "outputs": {
            "scores": str(GOD_TEAM_SCORES_PATH),
            "visualization": str(GOD_TEAM_TSNE_PATH),
        },
        "notes": [
            visualization_note,
            "t-SNE is visualization only and was not used as the final ranking metric.",
            "The initial 7-god team in SEMANTIC_MODEL.md is a hypothesis, not a preselected result.",
        ],
    }


def rejected_size_reason(candidate: TeamCandidate, winner: TeamCandidate) -> str:
    if candidate.k < winner.k:
        return "too compressed for the selected coverage/separation target"
    if candidate.score > winner.score:
        return "higher raw score but rejected by smallest-team margin rule"
    return "more roles without enough score improvement"


def silhouette_support(value: float | None) -> str:
    if value is None:
        return "not available for this team size"
    if value < 0:
        return "negative; assignments are likely wrong or overlapping"
    if value < 0.10:
        return "weak positive; roles are separated but still semantically close"
    if value < 0.35:
        return "moderate positive; separation is usable"
    return "strong positive separation"


def stability_support(value: float | None) -> str:
    if value is None:
        return "not available for this team size"
    if value >= 0.90:
        return "strong bootstrap stability"
    if value >= 0.75:
        return "usable bootstrap stability"
    return "weak bootstrap stability"


def slug_from_path(path: Path) -> str:
    return path.stem.lower().replace(" ", "-")


def format_optional(value: float | None) -> str:
    return "" if value is None else f"{value:.4f}"


def require_str(item: dict[str, Any], key: str) -> str:
    value = item.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{key} must be a non-empty string")
    return value


def require_score(item: dict[str, Any], key: str) -> float:
    value = item.get(key)
    if not isinstance(value, (int, float)):
        raise ValueError(f"{key} must be numeric")
    score = float(value)
    if not 0.0 <= score <= 1.0:
        raise ValueError(f"{key} must be between 0 and 1")
    return score
