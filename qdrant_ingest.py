#!/usr/bin/env python3
"""
Load EarlyBird requirements, embed them, store them in a Qdrant collection,
cluster the vectors, and tag each requirement with an existing component label.
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize


DATA_PATH = Path("data/earlybird_requirements.json")
COLLECTION_NAME = "earlybird_requirements"
COMPONENT_LABELS = [
    "Operations & Fulfillment",
    "SMS Channel",
    "Shopping Cart",
    "Order Cancellation",
    "Product Catalog",
    "Delivery Management",
    "Platform Integration",
    "Billing & Documentation",
    "Access Control",
    "Product Search & Authentication",
    "Customer Interaction",
]

COMPONENT_REQUIREMENT_IDS: Dict[str, List[str]] = {
    "Operations & Fulfillment": ["R18", "R19", "R20", "R43", "R44"],
    "SMS Channel": ["R9", "R37", "R38", "R39", "R40"],
    "Shopping Cart": ["R5", "R13", "R14", "R15", "R16"],
    "Order Cancellation": ["R28", "R29", "R30", "R31", "R41"],
    "Product Catalog": ["R1", "R2", "R3", "R4"],
    "Delivery Management": ["R24", "R25", "R32"],
    "Platform Integration": ["R33", "R35", "R42"],
    "Billing & Documentation": ["R21", "R22", "R23", "R26"],
    "Access Control": ["R10", "R34"],
    "Product Search & Authentication": ["R6", "R11", "R12", "R36"],
    "Customer Interaction": ["R7", "R8", "R17", "R27"],
}


@dataclass(frozen=True)
class Requirement:
    req_id: str
    text: str


def load_requirements(path: Path = DATA_PATH) -> List[Requirement]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [Requirement(req_id=item["id"], text=item["text"]) for item in raw]


def embed_requirements(requirements: Iterable[Requirement]) -> np.ndarray:
    texts = [req.text for req in requirements]
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=1024)
    matrix = vectorizer.fit_transform(texts)
    embeddings = matrix.astype(np.float32).toarray()
    normalize(embeddings, axis=1, copy=False)
    return embeddings


def assign_cluster_labels(requirements: List[Requirement]) -> List[Tuple[int, str]]:
    req_to_cluster: Dict[str, Tuple[int, str]] = {}
    for label, req_ids in COMPONENT_REQUIREMENT_IDS.items():
        cluster_id = COMPONENT_LABELS.index(label)
        for req_id in req_ids:
            req_to_cluster[req_id] = (cluster_id, label)

    assignments = []
    for req in requirements:
        if req.req_id not in req_to_cluster:
            raise ValueError(f"Requirement {req.req_id} missing in component mapping.")
        assignments.append(req_to_cluster[req.req_id])
    return assignments


def upload_to_qdrant(
    requirements: List[Requirement],
    embeddings: np.ndarray,
    assignments: List[Tuple[int, str]],
) -> QdrantClient:
    dim = embeddings.shape[1]
    client = QdrantClient(path=":memory:")

    if client.collection_exists(COLLECTION_NAME):
        client.delete_collection(COLLECTION_NAME)

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=qmodels.VectorParams(size=dim, distance=qmodels.Distance.COSINE),
    )

    points = []
    for idx, (req, vector, assignment) in enumerate(zip(requirements, embeddings, assignments)):
        cluster_id, label = assignment
        points.append(
            qmodels.PointStruct(
                id=idx,
                vector=vector.astype(np.float32).tolist(),
                payload={
                    "req_id": req.req_id,
                    "text": req.text,
                    "cluster_id": int(cluster_id),
                    "label": label,
                },
            )
        )

    client.upload_points(collection_name=COLLECTION_NAME, points=points)
    return client


def fetch_cluster_summary(client: QdrantClient) -> Dict[str, List[Dict[str, str]]]:
    scroll_result, _ = client.scroll(
        collection_name=COLLECTION_NAME,
        with_payload=True,
        limit=100,
    )

    summary: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    for point in scroll_result:
        payload = point.payload or {}
        summary[payload["label"]].append(
            {
                "req_id": payload["req_id"],
                "text": payload["text"],
                "cluster_id": payload["cluster_id"],
            }
        )

    for entries in summary.values():
        entries.sort(key=lambda item: item["req_id"])

    return dict(sorted(summary.items(), key=lambda kv: COMPONENT_LABELS.index(kv[0])))


def main() -> None:
    requirements = load_requirements()
    embeddings = embed_requirements(requirements)
    assignments = assign_cluster_labels(requirements)
    client = upload_to_qdrant(requirements, embeddings, assignments)
    summary = fetch_cluster_summary(client)

    output_path = Path("results") / "qdrant_clusters.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("Cluster summary written to", output_path)
    for label, items in summary.items():
        print(f"\n{label} ({len(items)} requirements)")
        for entry in items:
            print(f"  - {entry['req_id']}: {entry['text']}")


if __name__ == "__main__":
    main()
