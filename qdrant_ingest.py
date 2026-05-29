#!/usr/bin/env python3
"""Ingest verified requirement clusters into Qdrant with retrieval embeddings."""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from semantic_contracts import (
    BASELINE_EMBEDDING_DIMENSIONS,
    BASELINE_EMBEDDING_MODEL,
    CLUSTER_ARTIFACT_PATH,
    COLLECTION_NAME,
    DISTANCE,
    EmbeddingConfig,
    VECTOR_NAME,
    build_payloads,
    load_cluster_artifact,
    load_requirements,
    stable_point_id,
    validate_artifact,
    validate_embedding_config,
)

QDRANT_URL = "http://localhost:6333"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate the verified semantic cluster artifact, create real retrieval "
            "embeddings, and ingest requirement points into Qdrant."
        )
    )
    parser.add_argument(
        "--cluster-artifact",
        type=Path,
        default=CLUSTER_ARTIFACT_PATH,
        help="Verified cluster artifact to ingest.",
    )
    parser.add_argument(
        "--qdrant-url",
        default=QDRANT_URL,
        help="Qdrant URL for live ingestion.",
    )
    parser.add_argument(
        "--collection",
        default=COLLECTION_NAME,
        help="Qdrant collection name.",
    )
    parser.add_argument(
        "--embedding-model",
        default=BASELINE_EMBEDDING_MODEL,
        help="OpenAI embedding model.",
    )
    parser.add_argument(
        "--embedding-dimensions",
        type=int,
        default=BASELINE_EMBEDDING_DIMENSIONS,
        help="OpenAI embedding dimensions.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate payloads and report planned ingestion without external calls.",
    )
    parser.add_argument(
        "--require-live",
        action="store_true",
        help="Fail instead of falling back to dry-run when OpenAI or Qdrant is unavailable.",
    )
    parser.add_argument(
        "--no-recreate",
        action="store_true",
        help="Do not delete and recreate the Qdrant collection before upsert.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    embedding = EmbeddingConfig(
        model=args.embedding_model,
        dimensions=args.embedding_dimensions,
    )

    config_errors = validate_embedding_config(embedding)
    if config_errors:
        return fail(config_errors)

    requirements = load_requirements()
    artifact = load_cluster_artifact(args.cluster_artifact)
    artifact_errors = validate_artifact(artifact, requirements)
    if artifact_errors:
        return fail(artifact_errors)

    payloads = build_payloads(artifact, embedding)
    if args.collection != artifact.collection_name:
        return fail([f"--collection must match artifact collection {artifact.collection_name!r}"])
    if artifact.vector_name != VECTOR_NAME:
        return fail([f"artifact vector name must be {VECTOR_NAME!r}"])
    if artifact.distance != DISTANCE:
        return fail([f"artifact distance must be {DISTANCE!r}"])

    if args.dry_run:
        print_dry_run(payloads, embedding, args, reason="--dry-run requested")
        return 0

    client, qdrant_error = try_qdrant_client(args)
    if client is None:
        print_dry_run(payloads, embedding, args, reason=f"Qdrant is unavailable: {qdrant_error}")
        return 1 if args.require_live else 0

    vectors, embedding_error = try_openai_embeddings(
        [payload["text"] for payload in payloads],
        embedding,
    )
    if vectors is None:
        print_dry_run(
            payloads,
            embedding,
            args,
            reason=f"OpenAI embeddings are unavailable: {embedding_error}",
        )
        return 1 if args.require_live else 0

    ingest_points(
        client=client,
        collection_name=args.collection,
        vector_name=artifact.vector_name,
        embedding=embedding,
        payloads=payloads,
        vectors=vectors,
        recreate=not args.no_recreate,
    )

    print(
        f"Ingested {len(payloads)} requirements into {args.collection} "
        f"using {embedding.model}/{embedding.dimensions}."
    )
    return 0


def try_qdrant_client(args: argparse.Namespace) -> tuple[Any | None, str | None]:
    try:
        from qdrant_client import QdrantClient
    except ImportError as exc:
        return None, f"qdrant-client import failed: {exc}"

    try:
        client = QdrantClient(url=args.qdrant_url)
        client.get_collections()
        return client, None
    except Exception as exc:  # pragma: no cover - depends on external service
        return None, f"connection failed at {args.qdrant_url}: {exc}"


def try_openai_embeddings(
    texts: Sequence[str],
    embedding: EmbeddingConfig,
) -> tuple[list[list[float]] | None, str | None]:
    if not os.environ.get("OPENAI_API_KEY"):
        return None, "OPENAI_API_KEY is not set"

    try:
        from openai import OpenAI
    except ImportError as exc:
        return None, f"openai import failed: {exc}"

    try:
        client = OpenAI()
        response = client.embeddings.create(
            model=embedding.model,
            input=list(texts),
            dimensions=embedding.dimensions,
            encoding_format="float",
        )
    except Exception as exc:  # pragma: no cover - depends on external service
        return None, f"embedding request failed: {exc}"

    vectors = [
        list(item.embedding)
        for item in sorted(response.data, key=lambda item: item.index)
    ]
    wrong_sizes = [len(vector) for vector in vectors if len(vector) != embedding.dimensions]
    if wrong_sizes:
        raise ValueError(
            "OpenAI returned embedding dimensions that do not match "
            f"{embedding.dimensions}: {wrong_sizes}"
        )
    return vectors, None


def ingest_points(
    client: Any,
    collection_name: str,
    vector_name: str,
    embedding: EmbeddingConfig,
    payloads: Sequence[dict[str, Any]],
    vectors: Sequence[Sequence[float]],
    recreate: bool,
) -> None:
    from qdrant_client.http import models as qmodels

    if recreate and client.collection_exists(collection_name):
        client.delete_collection(collection_name)

    if not client.collection_exists(collection_name):
        client.create_collection(
            collection_name=collection_name,
            vectors_config={
                vector_name: qmodels.VectorParams(
                    size=embedding.dimensions,
                    distance=qmodels.Distance.COSINE,
                )
            },
        )
        create_payload_indexes(client, collection_name, qmodels)

    points = [
        qmodels.PointStruct(
            id=stable_point_id(payload["req_id"]),
            vector={vector_name: list(vector)},
            payload=payload,
        )
        for payload, vector in zip(payloads, vectors, strict=True)
    ]
    client.upsert(collection_name=collection_name, points=points)


def create_payload_indexes(client: Any, collection_name: str, qmodels: Any) -> None:
    indexes = {
        "req_id": qmodels.PayloadSchemaType.KEYWORD,
        "source": qmodels.PayloadSchemaType.KEYWORD,
        "cluster_id": qmodels.PayloadSchemaType.INTEGER,
        "cluster_label": qmodels.PayloadSchemaType.KEYWORD,
        "semantic_version": qmodels.PayloadSchemaType.KEYWORD,
        "embedding_model": qmodels.PayloadSchemaType.KEYWORD,
        "embedding_dimensions": qmodels.PayloadSchemaType.INTEGER,
        "cluster_model": qmodels.PayloadSchemaType.KEYWORD,
        "cluster_k": qmodels.PayloadSchemaType.INTEGER,
        "projection_dimensions": qmodels.PayloadSchemaType.INTEGER,
        "agent_owner": qmodels.PayloadSchemaType.KEYWORD,
        "verified_by": qmodels.PayloadSchemaType.KEYWORD,
        "verifier": qmodels.PayloadSchemaType.KEYWORD,
        "status": qmodels.PayloadSchemaType.KEYWORD,
    }
    for field_name, schema in indexes.items():
        client.create_payload_index(
            collection_name=collection_name,
            field_name=field_name,
            field_schema=schema,
        )


def print_dry_run(
    payloads: Sequence[dict[str, Any]],
    embedding: EmbeddingConfig,
    args: argparse.Namespace,
    reason: str,
) -> None:
    cluster_ids = sorted({payload["cluster_id"] for payload in payloads})
    print("DRY RUN:", reason)
    print(f"Validated payloads: {len(payloads)}")
    print(f"Collection: {args.collection}")
    print(f"Named vector: {VECTOR_NAME}")
    print(f"Distance: {DISTANCE}")
    print(f"Embedding: {embedding.model}/{embedding.dimensions}")
    print(f"Clusters: {cluster_ids[0]}..{cluster_ids[-1]} ({len(cluster_ids)} total)")
    print("No embeddings were requested and no Qdrant writes were performed.")


def fail(errors: Sequence[str]) -> int:
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
