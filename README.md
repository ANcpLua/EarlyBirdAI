# EarlyBird Semantic Requirements Pipeline

Evidence-checked semantic clustering and Qdrant ingestion for the 44 EarlyBird breakfast delivery requirements.

`SEMANTIC_MODEL.md` is the source of truth. The pipeline deliberately separates exploratory clustering vectors from
production retrieval embeddings:

```text
raw requirements
  -> bootstrap clustering experiment
  -> verified cluster artifact
  -> production retrieval embeddings
  -> Qdrant ingestion
```

## Policy

- Experiment layer: `main.py` may use `sentence-transformers/all-mpnet-base-v2` with PCA projections such as 16D for
  stability analysis and visualization.
- Retrieval layer: `qdrant_ingest.py` must use real OpenAI retrieval embeddings for live Qdrant writes.
- Baseline retrieval embedding: `text-embedding-3-small` at 1536 dimensions.
- Optional benchmark ceiling: `text-embedding-3-large` at 1024 or 3072 dimensions.
- Compressed experiment vectors are never written to Qdrant as production retrieval vectors.

## Files

- `data/earlybird_requirements.json` - raw requirements, R1 through R44.
- `main.py` - bootstrap clustering experiment; writes experiment rankings and visualizations.
- `results/experiment_results.csv` - ranked clustering candidates.
- `results/qdrant_clusters.json` - verified cluster artifact consumed by ingestion.
- `semantic_contracts.py` - shared schema, constants, and payload builder.
- `qdrant_ingest.py` - dry-run or live Qdrant ingestion with `semantic_text` named vectors.
- `scripts/validate_semantic_pipeline.py` - local audit check for schema, docs, experiment output, and duplicates.
- `docs/ARCHITECTURE.md` - candidate architecture labels derived from the clusters.
- `docs/earlybird_clustering.png` and `visualizations/` - generated experiment visuals.

## Usage

Install dependencies when the local Python environment does not already provide them:

```bash
python3 -m pip install -r requirements.txt
```

Run the clustering experiment:

```bash
python3 main.py
```

Validate the checked-in artifact and documentation locally:

```bash
python3 scripts/validate_semantic_pipeline.py
```

Preview Qdrant ingestion without external services:

```bash
python3 qdrant_ingest.py --dry-run
```

Run live ingestion:

```bash
docker run -p 6333:6333 qdrant/qdrant
OPENAI_API_KEY=... python3 qdrant_ingest.py
```

If Qdrant or `OPENAI_API_KEY` is unavailable, `qdrant_ingest.py` falls back to the same dry-run report unless
`--require-live` is set.

## Qdrant Model

- Collection: `requirements_v1`
- Named vector: `semantic_text`
- Distance: cosine
- Baseline vector size: 1536

Each point stores payload metadata for auditability:

```json
{
  "req_id": "R1",
  "text": "We guarantee breakfast delivery...",
  "source": "data/earlybird_requirements.json",
  "cluster_id": 4,
  "cluster_label": "Product Catalog",
  "semantic_version": "amaterasu-v1",
  "embedding_model": "text-embedding-3-small",
  "embedding_dimensions": 1536,
  "cluster_model": "bootstrap-kmeans-v1",
  "cluster_k": 11,
  "projection_dimensions": 16,
  "agent_owner": "Amaterasu",
  "verified_by": "Ma'at",
  "verifier": "Ma'at",
  "status": "candidate",
  "confidence": 0.0,
  "evidence": []
}
```

## Agent Roles

- Amaterasu owns semantic discovery.
- Ma'at verifies labels, evidence, and confidence.
- Odin is reserved for unresolved external or domain claims.
- Athena owns taxonomy and schema normalization.
- Hephaestus implements approved changes.
- Shiva removes obsolete names, artifacts, and docs.

Current labels remain `candidate` because the repository has clustering evidence and source references, but no live
retrieval precision@k run or separate human semantic-quality review.
