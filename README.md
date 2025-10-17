# EarlyBird Requirements Clustering

Semantic clustering of [44 EarlyBird breakfast delivery system requirements](data/earlybird_requirements.json) using embeddings and vector database.

---

## Task

Feed embeddings of [functional requirements](data/earlybird_requirements.json) into a vector database ([Qdrant](https://qdrant.tech/)), cluster them, and derive an architecture proposal where each component implements one cluster of requirements.

---

## Approach

1. **Embeddings:** [all-mpnet-base-v2](https://huggingface.co/sentence-transformers/all-mpnet-base-v2) (768D → [PCA](https://en.wikipedia.org/wiki/Principal_component_analysis) to 16D)
2. **Vector Database:** [Qdrant](https://qdrant.tech/) ([HNSW](https://en.wikipedia.org/wiki/Hierarchical_navigable_small_world), [cosine distance](https://en.wikipedia.org/wiki/Cosine_similarity))
3. **Clustering:** [Spherical k-means](https://en.wikipedia.org/wiki/K-means_clustering#Spherical_k-means_clustering)
4. **Selection:** Maximize [Silhouette score](https://en.wikipedia.org/wiki/Silhouette_(clustering)) (peaks at k=11)

---

## Result

**11 clusters** (Cluster 0-10) for [44 requirements](data/earlybird_requirements.json) (~4 per cluster)

- **[Silhouette Score](https://en.wikipedia.org/wiki/Silhouette_(clustering)):** 0.306 (peak at k=11)
- **[PCA](https://en.wikipedia.org/wiki/Principal_component_analysis) Dimensions:** 16D (76.1% variance retained)
- **Distance Metric:** [Cosine](https://en.wikipedia.org/wiki/Cosine_similarity)

See [full bootstrap analysis results](results/experiment_results.csv) for all 52 configurations tested.

---

## Architecture

See [**ARCHITECTURE.md**](docs/ARCHITECTURE.md) for component descriptions:

- Cluster 0: Order Assembly
- Cluster 1: SMS Ordering
- Cluster 2: Repeat Orders
- Cluster 3: Order Cancellation
- Cluster 4: Product Catalog
- Cluster 5: Route Planning
- Cluster 6: System Integrations
- Cluster 7: Invoicing
- Cluster 8: User Access
- Cluster 9: Product Search
- Cluster 10: Customer Service

---

## Files

### Input Data
- **data/earlybird_requirements.json** - 44 initial requirements

### Results
- **results/experiment_results.csv** - Full bootstrap analysis (52 configurations ranked)
- **results/qdrant_clusters.json** - Requirements grouped by cluster (k=11, d=16)

### Documentation
- **docs/ARCHITECTURE.md** - Component architecture proposal
- **docs/earlybird_clustering.png** - Comprehensive visualization

### Tools
- **main.py** - Bootstrap stability-based clustering experiment
- **load_qdrant.py** - Load clustered data into Qdrant vector database

---

## Usage

### 1. Run Clustering Experiment

```bash
# Bootstrap stability analysis (generates CSV results)
python3 main.py
```

**Output:**
- `results/experiment_results.csv` - All 52 configurations ranked by silhouette score
- `visualizations/` - Stability plots and t-SNE projections

### 2. Load into Qdrant

```bash
# Load clustered requirements into Qdrant vector database
python3 load_qdrant.py
```

**Input:** [results/qdrant_clusters.json](results/qdrant_clusters.json) - Requirements grouped by cluster (k=11, d=16)

**Qdrant payload structure:**
```json
{
  "req_id": "R1",
  "text": "We guarantee breakfast delivery...",
  "cluster_id": 4,
  "label": "Product Catalog"
}
```
