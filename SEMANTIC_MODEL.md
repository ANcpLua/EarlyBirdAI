# Semantic Requirements Model

## Purpose

Build an evidence-checked semantic requirements pipeline for EarlyBirdAI.

The pipeline separates exploratory clustering/projection from production retrieval. Compressed experiment vectors may be
used for stability analysis and visualization, but Qdrant ingestion must use real retrieval embeddings with explicit
payload metadata.

This file is the source of truth for the semantic model, agent roles, embedding policy, Qdrant payload schema,
validation expectations, and implementation boundaries.

## Source Status

| Claim Type                                              | Status                         |
|---------------------------------------------------------|--------------------------------|
| OpenAI embedding dimensions                             | Publicly documented            |
| Qdrant points, payloads, collections, and named vectors | Publicly documented            |
| scikit-learn silhouette score behavior                  | Publicly documented            |
| Existing repo structure                                 | Inferred from local repository |
| Agent naming model                                      | Project design decision        |
| k=11 and d=16 experiment setup                          | Project design decision        |
| Qdrant payload fields                                   | Project schema decision        |

## Current Repository Shape

Expected root structure:

```text
EarlyBirdAI/
├── data/
├── docs/
├── results/
├── visualizations/
├── main.py
├── qdrant_ingest.py
├── README.md
└── SEMANTIC_MODEL.md
```

The repository must not contain stale documentation that refers to `load_qdrant.py` if the actual ingestion entry point
is `qdrant_ingest.py`.

## Core Decision

Do not default to 4k embeddings.

Use this baseline:

```text
embedding_model: text-embedding-3-small
embedding_dimensions: 1536
projection_dimensions: 16
cluster_k: 11
distance: cosine
qdrant_collection: requirements_v1
agent_owner: Amaterasu
verifier: Ma'at
```

Use `text-embedding-3-large` only as a benchmark or quality ceiling:

```text
text-embedding-3-large @ 1024 dimensions -> quality/cost test
text-embedding-3-large @ 3072 dimensions -> quality ceiling
```

The final choice must be based on retrieval quality, cluster stability, label quality, and validation evidence, not on
larger dimension count alone.

## Non-Goals

Do not:

* Treat 4k embeddings as a default.
* Use compressed `d=16` projection vectors for production semantic retrieval.
* Merge clustering, verification, and ingestion into one opaque script.
* Invent unsupported semantic labels.
* Preserve stale file names or stale README usage.
* Stage, stash, or create extra worktrees.
* Change behavior outside this semantic pipeline unless required by this file.

## Agent Model

The agent names are semantic roles, not implementation classes unless the codebase explicitly needs them.

| Agent      | Responsibility                       | Must Do                                                                    | Must Not Do                            |
|------------|--------------------------------------|----------------------------------------------------------------------------|----------------------------------------|
| Amaterasu  | Illuminate hidden semantic structure | Discover clusters, contradictions, ambiguity, and routing needs            | Implement code changes                 |
| Ma'at      | Verify truth and evidence            | Validate labels, cluster assignments, evidence, and confidence             | Accept unsupported labels              |
| Odin       | Deep research                        | Resolve unclear external/domain meaning with cited evidence                | Research already-resolved local facts  |
| Athena     | Refactor taxonomy and schema         | Merge, split, rename, and normalize semantic structures                    | Destroy validated behavior             |
| Hephaestus | Implement approved changes           | Update scripts, schemas, payloads, docs, and validation paths              | Invent architecture beyond scope       |
| Shiva      | Delete obsolete structure            | Remove stale docs, dead names, obsolete artifacts, and harmful duplication | Delete required source data            |
| Hermes     | Route work                           | Select the next agent/tool based on task intent                            | Perform domain-specific work directly  |
| Janus      | Boundary review                      | Review compatibility, migrations, API/schema transitions                   | Rewrite implementation unnecessarily   |
| Saraswati  | Documentation and naming             | Produce clear README/docs/examples                                         | Hide uncertainty or unsupported claims |

## Minimum Execution Pipeline

Use the compact pipeline unless the repository requires the full role set:

```text
Amaterasu -> Ma'at -> Athena -> Hephaestus -> Shiva
```

Meaning:

```text
Discover -> Verify -> Refactor taxonomy -> Implement -> Delete obsolete artifacts
```

## Required Pipeline Shape

The repository should express this flow clearly:

```text
raw requirements
  -> bootstrap clustering experiment
  -> cluster stability and visualization outputs
  -> verified cluster artifact
  -> production retrieval embeddings
  -> Qdrant collection ingestion
  -> dry-run/local validation path
```

The pipeline must keep these concerns separate:

| Concern                      | Allowed Location                          |
|------------------------------|-------------------------------------------|
| Bootstrap clustering         | `main.py` or a cohesive clustering module |
| Experiment rankings          | `results/experiment_results.csv`          |
| Visualizations               | `visualizations/`                         |
| Accepted cluster assignments | `results/qdrant_clusters.json`            |
| Qdrant ingestion             | `qdrant_ingest.py`                        |
| Semantic model documentation | `SEMANTIC_MODEL.md`                       |
| User-facing usage docs       | `README.md` or `docs/`                    |

## Entry Points

Preferred command surface:

```bash
python3 main.py
docker run -p 6333:6333 qdrant/qdrant
python3 qdrant_ingest.py
```

Do not document `python3 load_qdrant.py` unless that file exists intentionally as a compatibility shim. Prefer one
ingestion entry point: `qdrant_ingest.py`.

## Embedding Policy

### Experiment Layer

The current bootstrap experiment may use low-dimensional projections such as `d=16` for stability analysis, clustering
comparison, and visualization.

This is acceptable only for experiment/projection use.

### Retrieval Layer

Production Qdrant retrieval must use real retrieval embeddings.

Baseline:

```text
model: text-embedding-3-small
dimensions: 1536
```

Optional benchmark:

```text
model: text-embedding-3-large
dimensions: 1024
```

Optional ceiling:

```text
model: text-embedding-3-large
dimensions: 3072
```

### Selection Criteria

Pick the embedding configuration using:

* retrieval precision@k
* cluster stability across bootstrap runs
* human label quality
* duplicate and near-duplicate detection quality
* cost and storage impact
* reproducibility of results

Do not pick by vector dimensionality alone.

## Qdrant Model

Use one collection for requirement points unless the payload schemas diverge enough to justify separate collections.

Preferred collection:

```text
requirements_v1
```

Preferred distance:

```text
cosine
```

Use named vectors when multiple retrieval views are needed:

```text
semantic_text        -> required dense retrieval vector
semantic_summary     -> optional later
semantic_title       -> optional later
lexical_sparse       -> optional later
```

Do not create multiple vector spaces prematurely. Add named vectors only when the code validates a real use case.

## Required Qdrant Payload

Each requirement point should include enough metadata to audit where the semantic label came from and how it was
produced.

Minimum payload:

```json
{
  "req_id": "R1",
  "text": "We guarantee breakfast delivery...",
  "cluster_id": 4,
  "cluster_label": "Product Catalog",
  "source": "requirements.md",
  "semantic_version": "amaterasu-v1",
  "embedding_model": "text-embedding-3-small",
  "embedding_dimensions": 1536,
  "cluster_model": "bootstrap-kmeans-v1",
  "cluster_k": 11,
  "projection_dimensions": 16,
  "agent_owner": "Amaterasu",
  "verified_by": "Ma'at",
  "status": "candidate",
  "confidence": 0.0,
  "evidence": []
}
```

Allowed status values:

```text
candidate
verified
rejected
deprecated
```

Recommended confidence range:

```text
0.0 <= confidence <= 1.0
```

## Validation Rules

Silhouette score is useful but insufficient.

Use it to measure geometric separation, not semantic truth. A high score does not prove that labels are correct. A low
or near-zero score may indicate overlapping clusters, weak feature representation, or an unsuitable cluster count.

Validation must include:

* silhouette score
* bootstrap stability
* cluster label review
* source evidence review
* retrieval precision@k
* duplicate and near-duplicate checks
* dry-run ingestion validation
* README command validation

## Expected Artifacts

The pipeline may produce:

```text
results/experiment_results.csv
results/qdrant_clusters.json
visualizations/
```

`results/experiment_results.csv` should rank clustering candidates by relevant metrics.

`results/qdrant_clusters.json` should contain the accepted cluster assignments and labels that are safe for ingestion.

Qdrant should store requirement points with named vectors and payload metadata.

## Implementation Constraints

Implementation must prefer:

* small cohesive files
* explicit schemas
* typed data contracts where reasonable
* deterministic outputs
* readable CLI commands
* minimal global state
* dry-run support
* clear failure messages
* auditable metadata

Implementation must avoid:

* hidden side effects
* stale script names
* magic constants without documentation
* unverified labels
* overfitted cluster assumptions
* unnecessary abstractions
* mixing experiment vectors with production retrieval vectors

## Required Agent Behavior

### Amaterasu

Inputs:

```text
raw requirements
embedding/projection outputs
cluster results
existing labels
```

Outputs:

```text
candidate clusters
ambiguity map
contradiction list
routing recommendation
```

### Ma'at

Inputs:

```text
candidate clusters
source requirements
cluster labels
evidence fields
```

Outputs:

```text
accepted labels
rejected labels
confidence values
evidence notes
```

### Athena

Inputs:

```text
verified clusters
schema gaps
naming inconsistencies
```

Outputs:

```text
cleaner taxonomy
merged/split clusters
normalized payload schema
```

### Hephaestus

Inputs:

```text
approved schema
approved entry points
approved docs
```

Outputs:

```text
updated scripts
updated Qdrant collection logic
updated payload indexes
updated README usage
```

### Shiva

Inputs:

```text
deprecated files
stale names
obsolete docs
dead artifacts
```

Outputs:

```text
deleted stale references
removed obsolete files
clean repo state
```

## Acceptance Criteria

The work is complete only when:

1. `SEMANTIC_MODEL.md` exists in the repository root.
2. README/docs point to the correct commands.
3. There is no stale `load_qdrant.py` usage unless intentionally supported.
4. Clustering/projection remains separate from production retrieval embeddings.
5. Qdrant ingestion records explicit payload metadata.
6. The baseline embedding config is `text-embedding-3-small` at 1536 dimensions.
7. `text-embedding-3-large` is optional and benchmark-driven.
8. The pipeline can run locally as far as possible without external API keys.
9. If Qdrant or API keys are unavailable, a dry-run path reports what would happen.
10. Validation evidence is summarized.
11. No staged files, stashes, or extra worktrees are left behind.

## Public References

These references justify public technical claims in this file:

* OpenAI embeddings guide: https://developers.openai.com/api/docs/guides/embeddings
* Qdrant vectors documentation: https://qdrant.tech/documentation/manage-data/vectors/
* Qdrant collections documentation: https://qdrant.tech/documentation/manage-data/collections/
* scikit-learn silhouette score
  documentation: https://scikit-learn.org/stable/modules/generated/sklearn.metrics.silhouette_score.html
