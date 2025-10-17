#!/usr/bin/env python3
"""
Bootstrap Stability-Based Requirements Clustering

Data-driven methodology for semantic clustering:
  - Spherical k-means (cosine distance, L2-normalized embeddings)
  - Higher-dimensional PCA (16-43d range, constrained by n=44 samples)
  - Bootstrap stability analysis (ARI/NMI) for statistical validation
  - Adaptive quality thresholds (percentile-based, not fixed)
  - Silhouette score maximization (cluster quality, not ARI)

Experiment Configuration:
    - Embedding Model: sentence-transformers/all-mpnet-base-v2 (768d native, +10% quality)
    - Dimensions Tested: [16, 24, 32, 43] (max=43 for n=44 samples)
    - Cluster Range: k ∈ [3, 15] (full exploration)
    - Distance Metric: Cosine (spherical k-means)
    - Bootstrap Samples: 100 iterations per (d, k) configuration

Selection Criteria:
    1. PRIMARY: Maximize Silhouette score (cluster quality)
    2. SECONDARY: Pass adaptive thresholds (p40 Silhouette, p60 DBI, 2× size ratio)

Rationale:
    - Silhouette score measures cluster separation and cohesion
    - Silhouette peaks at optimal k, then declines (natural sweet spot)
    - ARI increases monotonically with k (not useful for selection)
    - Bootstrap analysis validates statistical stability of chosen k
"""

import json
import warnings
from typing import List, Dict, Any, Tuple

try:
    import matplotlib

    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib import cm

    PLOTTING_ENABLED = True
except ImportError:
    matplotlib = None  # type: ignore[assignment]
    plt = None  # type: ignore[assignment]
    cm = None  # type: ignore[assignment]
    PLOTTING_ENABLED = False

import numpy as np
import csv
import os
from sentence_transformers import SentenceTransformer
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.cluster import KMeans
from sklearn.metrics import (
    silhouette_score, davies_bouldin_score, adjusted_rand_score, normalized_mutual_info_score
)
from sklearn.metrics.pairwise import cosine_distances
from sklearn.utils import resample

warnings.filterwarnings(
    "ignore",
    message=r"The number of unique classes is greater than 50% of the number of samples.*",
    category=UserWarning,
    module=r"sklearn.metrics.cluster._supervised",
)

EMBEDDING_MODEL = 'sentence-transformers/all-mpnet-base-v2'  # 768D, higher quality (+10% vs MiniLM)
NATIVE_DIMENSION = 768
DIMENSIONS_TO_TEST = [16, 24, 32, 43]  # Max = 43 (< 44 samples)
K_RANGE = list(range(3, 16))

N_BOOTSTRAP_SAMPLES = 100
BOOTSTRAP_SAMPLE_RATIO = 0.8
RANDOM_STATE = 42
DATA_PATH = 'data/earlybird_requirements.json'
OUTPUT_DIR = 'visualizations'
RESULTS_DIR = 'results'

# Constants for repeated strings
TITLE_K = "Number of Clusters (k)"

# Deterministic randomness
DEFAULT_SEED = 42
RNG = np.random.default_rng(DEFAULT_SEED)


def load_requirements(file_path: str = DATA_PATH) -> List[Dict[str, Any]]:
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def spherical_kmeans(embeddings: np.ndarray, k: int, random_state: int = RANDOM_STATE) -> np.ndarray:
    """
    Spherical k-means clustering using cosine distance.

    Assumes embeddings are already L2-normalized. Standard k-means on
    normalized vectors is equivalent to spherical k-means.

    Args:
        embeddings: L2-normalized embedding vectors (n_samples, n_features)
        k: Number of clusters
        random_state: Random seed

    Returns:
        Cluster labels (n_samples,)
    """
    # Verify nomalization
    norms = np.linalg.norm(embeddings, axis=1)
    assert np.allclose(norms, 1.0, atol=1e-6), "Embeddings must be L2-normalized"

    kmeans = KMeans(n_clusters=k, random_state=random_state, n_init=10)
    labels = kmeans.fit_predict(embeddings)
    return labels


def bootstrap_stability(embeddings: np.ndarray, k: int,
                        n_bootstrap: int = N_BOOTSTRAP_SAMPLES) -> Dict[str, Any]:
    """
    Compute clustering stability via bootstrap resampling.

    Measures consistency of cluster assignments across bootstrap samples
    using Adjusted Rand Index (ARI) and Normalized Mutual Information (NMI).

    Args:
        embeddings: L2-normalized embedding vectors
        k: Number of clusters
        n_bootstrap: Number of bootstrap iterations

    Returns:
        Dict with stability metrics and all bootstrap results
    """
    n_samples = len(embeddings)
    sample_size = int(n_samples * BOOTSTRAP_SAMPLE_RATIO)

    labels_full = spherical_kmeans(embeddings, k, random_state=RANDOM_STATE)

    ari_scores = []
    nmi_scores = []
    silhouette_scores = []
    db_scores = []

    for i in range(n_bootstrap):
        indices = resample(np.arange(n_samples), n_samples=sample_size,
                           random_state=RANDOM_STATE + i, replace=True)
        unique_indices = np.unique(indices)

        if len(unique_indices) < k:
            continue

        bootstrap_embeddings = embeddings[unique_indices]

        bootstrap_labels = spherical_kmeans(bootstrap_embeddings, k,
                                            random_state=RANDOM_STATE + i)

        ari = adjusted_rand_score(labels_full[unique_indices], bootstrap_labels)
        nmi = normalized_mutual_info_score(labels_full[unique_indices], bootstrap_labels)

        ari_scores.append(ari)
        nmi_scores.append(nmi)

        cos_dist = cosine_distances(bootstrap_embeddings)
        sil = silhouette_score(cos_dist, bootstrap_labels, metric='precomputed', random_state=RANDOM_STATE)
        db = davies_bouldin_score(bootstrap_embeddings, bootstrap_labels)

        silhouette_scores.append(sil)
        db_scores.append(db)

    return {
        'ari_mean': np.mean(ari_scores),
        'ari_std': np.std(ari_scores),
        'nmi_mean': np.mean(nmi_scores),
        'nmi_std': np.std(nmi_scores),
        'silhouette_mean': np.mean(silhouette_scores),
        'silhouette_std': np.std(silhouette_scores),
        'db_mean': np.mean(db_scores),
        'db_std': np.std(db_scores),
        'ari_scores': ari_scores,
        'nmi_scores': nmi_scores,
        'silhouette_scores': silhouette_scores,
        'db_scores': db_scores
    }


def test_k_range_with_stability(embeddings: np.ndarray,
                                k_range: List[int]) -> List[Dict[str, Any]]:
    """
    Test multiple k values with bootstrap stability analysis.

    Args:
        embeddings: L2-normalized embedding vectors
        k_range: List of k values to test

    Returns:
        List of dictionaries containing metrics for each k value
    """
    results = []

    for k in k_range:
        print(f"    k={k}: Running {N_BOOTSTRAP_SAMPLES} bootstrap iterations...", end=' ')

        labels = spherical_kmeans(embeddings, k)

        cos_dist = cosine_distances(embeddings)
        silhouette = silhouette_score(cos_dist, labels, metric='precomputed', random_state=RANDOM_STATE)
        davies_bouldin = davies_bouldin_score(embeddings, labels)

        _, counts = np.unique(labels, return_counts=True)
        median_size = np.median(counts)
        max_size = np.max(counts)
        size_ratio = max_size / median_size if median_size > 0 else np.inf

        stability = bootstrap_stability(embeddings, k)

        results.append({
            'k': k,
            'silhouette': silhouette,
            'davies_bouldin': davies_bouldin,
            'max_cluster_size': int(max_size),
            'min_cluster_size': int(np.min(counts)),
            'median_cluster_size': float(median_size),
            'size_ratio': size_ratio,
            'ari_mean': stability['ari_mean'],
            'ari_std': stability['ari_std'],
            'nmi_mean': stability['nmi_mean'],
            'nmi_std': stability['nmi_std'],
            'silhouette_bootstrap_mean': stability['silhouette_mean'],
            'silhouette_bootstrap_std': stability['silhouette_std'],
            'db_bootstrap_mean': stability['db_mean'],
            'db_bootstrap_std': stability['db_std'],
            'labels': labels,
            'bootstrap_data': stability
        })

        print(f"ARI={stability['ari_mean']:.3f}±{stability['ari_std']:.3f}, "
              f"NMI={stability['nmi_mean']:.3f}±{stability['nmi_std']:.3f}")

    return results


def compute_adaptive_thresholds(all_results: Dict[int, Dict[str, Any]]) -> Dict[str, float]:
    """
    Compute adaptive quality thresholds based on percentiles across all configurations.

    Args:
        all_results: Dictionary of results for all dimensions

    Returns:
        Dict with adaptive threshold values
    """
    all_silhouette = []
    all_db = []

    for d, data in all_results.items():
        for r in data['results']:
            all_silhouette.extend(r['bootstrap_data']['silhouette_scores'])
            all_db.extend(r['bootstrap_data']['db_scores'])

    silhouette_p40 = np.percentile(all_silhouette, 40)
    db_p60 = np.percentile(all_db, 60)

    return {
        'silhouette_threshold': silhouette_p40,
        'db_threshold': db_p60,
        'size_ratio_threshold': 2.0
    }


def passes_adaptive_criteria(result: Dict[str, Any], thresholds: Dict[str, float]) -> bool:
    """Check if clustering result passes adaptive quality thresholds."""
    return (result['silhouette_bootstrap_mean'] >= thresholds['silhouette_threshold'] and
            result['db_bootstrap_mean'] <= thresholds['db_threshold'] and
            result['size_ratio'] <= thresholds['size_ratio_threshold'])


def plot_stability_analysis(results: List[Dict[str, Any]], dimension: int,
                            thresholds: Dict[str, float], output_file: str) -> None:
    """
    Generate comprehensive stability and quality metrics plot.
    """
    if not PLOTTING_ENABLED:
        print(f"Matplotlib not available — skipping stability plot: {output_file}.png")
        return

    k_values = [r['k'] for r in results]
    ari_means = [r['ari_mean'] for r in results]
    ari_stds = [r['ari_std'] for r in results]
    nmi_means = [r['nmi_mean'] for r in results]
    silhouettes = [r['silhouette_bootstrap_mean'] for r in results]
    db_scores = [r['db_bootstrap_mean'] for r in results]

    _, axes = plt.subplots(2, 2, figsize=(14, 10))

    axes[0, 0].errorbar(k_values, ari_means, yerr=ari_stds,
                        fmt='bo-', linewidth=2, markersize=8, capsize=5)
    axes[0, 0].set_xlabel(TITLE_K, fontsize=12)
    axes[0, 0].set_ylabel('Adjusted Rand Index (ARI)', fontsize=12)
    axes[0, 0].set_title('Bootstrap Stability (ARI)', fontsize=14, fontweight='bold')
    axes[0, 0].grid(True, alpha=0.3)
    axes[0, 0].set_xticks(k_values)
    axes[0, 0].set_ylim([0, 1])

    axes[0, 1].plot(k_values, nmi_means, 'go-', linewidth=2, markersize=8)
    axes[0, 1].set_xlabel(TITLE_K, fontsize=12)
    axes[0, 1].set_ylabel('Normalized Mutual Information (NMI)', fontsize=12)
    axes[0, 1].set_title('Bootstrap Stability (NMI)', fontsize=14, fontweight='bold')
    axes[0, 1].grid(True, alpha=0.3)
    axes[0, 1].set_xticks(k_values)
    axes[0, 1].set_ylim([0, 1])

    axes[1, 0].plot(k_values, silhouettes, 'mo-', linewidth=2, markersize=8)
    axes[1, 0].axhline(y=thresholds['silhouette_threshold'], color='r', linestyle='--',
                       label=f'Adaptive (p40): {thresholds["silhouette_threshold"]:.3f}')
    axes[1, 0].set_xlabel(TITLE_K, fontsize=12)
    axes[1, 0].set_ylabel('Silhouette Score (Bootstrap Mean)', fontsize=12)
    axes[1, 0].set_title('Silhouette Score by k', fontsize=14, fontweight='bold')
    axes[1, 0].grid(True, alpha=0.3)
    axes[1, 0].set_xticks(k_values)
    axes[1, 0].legend()

    axes[1, 1].plot(k_values, db_scores, 'ro-', linewidth=2, markersize=8)
    axes[1, 1].axhline(y=thresholds['db_threshold'], color='r', linestyle='--',
                       label=f'Adaptive (p60): {thresholds["db_threshold"]:.2f}')
    axes[1, 1].set_xlabel(TITLE_K, fontsize=12)
    axes[1, 1].set_ylabel('Davies-Bouldin Index (Bootstrap Mean)', fontsize=12)
    axes[1, 1].set_title('Davies-Bouldin Index by k', fontsize=14, fontweight='bold')
    axes[1, 1].grid(True, alpha=0.3)
    axes[1, 1].set_xticks(k_values)
    axes[1, 1].legend()
    axes[1, 1].invert_yaxis()

    plt.suptitle(f'Dimension {dimension} - Stability & Quality Analysis',
                 fontsize=16, fontweight='bold', y=0.995)
    plt.tight_layout()
    plt.savefig(f'{output_file}.png', dpi=150, bbox_inches='tight')
    plt.close()

    print(f"Saved: {output_file}.png")


def plot_tsne_visualization(embeddings: np.ndarray, labels: np.ndarray,
                            requirements: List[Dict[str, Any]], k: int,
                            dimension: int, output_file: str) -> None:
    """Generate t-SNE 2D projection visualization of embedding space with clusters."""
    if not PLOTTING_ENABLED:
        print(f"Matplotlib not available — skipping t-SNE plot: {output_file}")
        return

    print("  Running t-SNE for visualization...")
    tsne = TSNE(n_components=2, random_state=RANDOM_STATE,
                perplexity=min(30, len(embeddings) - 1))
    embeddings_2d = tsne.fit_transform(embeddings)

    _, ax = plt.subplots(figsize=(12, 10))

    cmap = cm.get_cmap('tab10')
    colors = cmap(np.linspace(0, 1, k))

    labels = np.asarray(labels)

    for cluster_id in range(k):
        mask = labels == cluster_id
        cluster_points = embeddings_2d[mask]
        mask_indices = np.nonzero(np.asarray(mask))[0]

        ax.scatter(cluster_points[:, 0], cluster_points[:, 1],
                   c=[colors[cluster_id]], label=f'Cluster {cluster_id}',
                   s=150, alpha=0.7, edgecolors='black', linewidth=1)

        for i, (x, y) in enumerate(cluster_points):
            idx = int(mask_indices[i])
            req_id = requirements[idx]['id']
            ax.annotate(req_id, (x, y), fontsize=8, ha='center', va='center',
                        fontweight='bold')

    ax.set_xlabel('t-SNE Dimension 1', fontsize=12)
    ax.set_ylabel('t-SNE Dimension 2', fontsize=12)
    ax.set_title(f't-SNE 2D Projection (d={dimension}, k={k})',
                 fontsize=14, fontweight='bold')
    ax.legend(loc='best', fontsize=10)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"Saved: {output_file}")


def generate_embeddings(requirements: List[Dict[str, Any]]) -> np.ndarray:
    """Generate and normalize embeddings from requirements text."""
    print("\nGenerating embeddings...")
    model = SentenceTransformer(EMBEDDING_MODEL)
    texts = [req['text'] for req in requirements]
    embeddings_native = model.encode(texts, show_progress_bar=False)
    embeddings_native = embeddings_native / np.linalg.norm(embeddings_native, axis=1, keepdims=True)

    print(f"Native embedding shape: {embeddings_native.shape}")
    print(f"Embeddings normalized: {np.allclose(np.linalg.norm(embeddings_native, axis=1), 1.0)}")

    return embeddings_native


def analyze_dimension_results(
        d: int,
        results: List[Dict[str, Any]],
        embeddings: np.ndarray,
        requirements: List[Dict[str, Any]],
        thresholds: Dict[str, float],
        figure_counter: int
) -> int:
    """
    Analyze and visualize results for a single dimension.

    Returns updated figure counter.
    """
    print(f"\n{'=' * 80}")
    print(f"DIMENSION {d} - SUMMARY")
    print(f"{'=' * 80}")

    print(f"\n{'k':>3} {'ARI':>7} {'NMI':>7} {'Silh':>7} {'DB':>6} {'MaxSize':>8} {'Ratio':>6} {'Pass':>5}")
    print("-" * 70)
    for r in results:
        passes = 'YES' if passes_adaptive_criteria(r, thresholds) else 'NO'
        print(f"{r['k']:>3} {r['ari_mean']:>7.3f} {r['nmi_mean']:>7.3f} "
              f"{r['silhouette_bootstrap_mean']:>7.3f} {r['db_bootstrap_mean']:>6.2f} "
              f"{r['max_cluster_size']:>8} {r['size_ratio']:>6.2f} {passes:>5}")

    print("\nGenerating visualizations...")

    fig_name = f"{OUTPUT_DIR}/figure_{figure_counter}_dimension_{d}d_stability"
    plot_stability_analysis(results, d, thresholds, fig_name)
    figure_counter += 1

    passing = [r for r in results if passes_adaptive_criteria(r, thresholds)]
    if passing:
        best = max(passing, key=lambda x: x['silhouette_bootstrap_mean'])
    else:
        best = max(results, key=lambda x: x['silhouette_bootstrap_mean'])

    print(f"  Best k for d={d}: {best['k']} (Silhouette: {best['silhouette_bootstrap_mean']:.3f}, "
          f"ARI: {best['ari_mean']:.3f})")

    output_file = f"{OUTPUT_DIR}/figure_{figure_counter}_tsne_projection_{d}d.png"
    plot_tsne_visualization(embeddings, best['labels'], requirements, best['k'], d, output_file)
    figure_counter += 1

    return figure_counter


def select_global_best(all_results: Dict[int, Dict[str, Any]], thresholds: Dict[str, float]) -> Tuple[
    Dict[str, Any], List[Dict[str, Any]]]:
    """Select the global best configuration across all dimensions.

    Returns:
        Tuple of (best_config, all_configs)
    """
    all_configs = []
    for d, data in all_results.items():
        for r in data['results']:
            config = {
                'd': d,
                'k': r['k'],
                'ari_mean': r['ari_mean'],
                'ari_std': r['ari_std'],
                'nmi_mean': r['nmi_mean'],
                'nmi_std': r['nmi_std'],
                'silhouette': r['silhouette_bootstrap_mean'],
                'silhouette_std': r['silhouette_bootstrap_std'],
                'davies_bouldin': r['db_bootstrap_mean'],
                'db_std': r['db_bootstrap_std'],
                'max_cluster': r['max_cluster_size'],
                'size_ratio': r['size_ratio'],
                'explained_var': data['explained_variance'],
                'passes': passes_adaptive_criteria(r, thresholds)
            }
            all_configs.append(config)

    passing_configs = [c for c in all_configs if c['passes']]
    if passing_configs:
        best = max(passing_configs, key=lambda x: x['silhouette'])
    else:
        best = max(all_configs, key=lambda x: x['silhouette'])

    return best, all_configs


def export_results_csv(all_configs: List[Dict[str, Any]]) -> str:
    """Export all configurations to CSV, sorted by silhouette score."""
    csv_path = f"{RESULTS_DIR}/experiment_results.csv"
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'rank', 'd', 'k', 'ari_mean', 'ari_std', 'nmi_mean', 'nmi_std',
            'silhouette', 'silhouette_std', 'davies_bouldin', 'db_std',
            'max_cluster', 'size_ratio', 'explained_var', 'passes'
        ])
        writer.writeheader()

        sorted_configs = sorted(all_configs, key=lambda x: x['silhouette'], reverse=True)
        for i, c in enumerate(sorted_configs, 1):
            writer.writerow({
                'rank': i,
                'd': c['d'],
                'k': c['k'],
                'ari_mean': round(c['ari_mean'], 3),
                'ari_std': round(c['ari_std'], 3),
                'nmi_mean': round(c['nmi_mean'], 3),
                'nmi_std': round(c['nmi_std'], 3),
                'silhouette': round(c['silhouette'], 3),
                'silhouette_std': round(c['silhouette_std'], 3),
                'davies_bouldin': round(c['davies_bouldin'], 2),
                'db_std': round(c['db_std'], 2),
                'max_cluster': c['max_cluster'],
                'size_ratio': round(c['size_ratio'], 2),
                'explained_var': round(c['explained_var'], 1),
                'passes': 'YES' if c['passes'] else 'NO'
            })

    print(f"\nSaved: {csv_path}")
    return csv_path


def print_global_best(best: Dict[str, Any]) -> None:
    """Print the global best configuration summary."""
    print("\nGLOBAL BEST CONFIGURATION:")
    print(f"  Dimension (d): {best['d']}")
    print(f"  Clusters (k): {best['k']}")
    print(f"  Stability (ARI): {best['ari_mean']:.3f} ± {best['ari_std']:.3f}")
    print(f"  Stability (NMI): {best['nmi_mean']:.3f} ± {best['nmi_std']:.3f}")
    print(f"  Silhouette Score: {best['silhouette']:.3f} ± {best['silhouette_std']:.3f}")
    print(f"  Davies-Bouldin Index: {best['davies_bouldin']:.2f} ± {best['db_std']:.2f}")
    print(f"  Max Cluster Size: {best['max_cluster']}")
    print(f"  Size Ratio: {best['size_ratio']:.2f}× median")
    print(f"  Explained Variance: {best['explained_var']:.1f}%")
    print(f"  Passes Criteria: {best['passes']}")


def main() -> None:
    """Execute bootstrap stability-based clustering experiment."""
    print("=" * 80)
    print("BOOTSTRAP STABILITY-BASED REQUIREMENTS CLUSTERING")
    print("Spherical K-Means with Adaptive Quality Thresholds")
    print("=" * 80)

    requirements = load_requirements()
    print(f"\nLoaded {len(requirements)} requirements")

    print("\nExperiment Configuration:")
    print(f"  Model: {EMBEDDING_MODEL}")
    print(f"  Native dimension: {NATIVE_DIMENSION}d")
    print(f"  Dimensions to test: {DIMENSIONS_TO_TEST}")
    print(f"  Cluster range (k): {K_RANGE}")
    print(f"  Bootstrap iterations: {N_BOOTSTRAP_SAMPLES}")
    print(f"  Bootstrap sample ratio: {BOOTSTRAP_SAMPLE_RATIO}")
    print("\nSelection Strategy:")
    print("  1. PRIMARY: Cluster quality (maximize Silhouette score)")
    print("  2. SECONDARY: Pass adaptive thresholds (p40 Silhouette, p60 DBI, 2× size ratio)")
    print("\n  Rationale: Silhouette peaks at optimal cluster separation, ARI increases with k.")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)

    embeddings_native = generate_embeddings(requirements)

    all_results: Dict[int, Dict[str, Any]] = {}

    for d in DIMENSIONS_TO_TEST:
        print(f"\n{'=' * 80}")
        print(f"TESTING DIMENSION: {d}")
        print(f"{'=' * 80}")

        print(f"Applying PCA to reduce to {d} dimensions...")
        pca = PCA(n_components=d, random_state=RANDOM_STATE)
        embeddings = pca.fit_transform(embeddings_native)
        embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
        exp_var = np.sum(pca.explained_variance_ratio_) * 100
        print(f"Explained variance: {exp_var:.1f}%")

        print("Testing k values with bootstrap stability analysis:")
        results = test_k_range_with_stability(embeddings, K_RANGE)
        all_results[d] = {
            'results': results,
            'embeddings': embeddings,
            'explained_variance': exp_var
        }

    print(f"\n{'=' * 80}")
    print("COMPUTING ADAPTIVE THRESHOLDS")
    print(f"{'=' * 80}")
    thresholds = compute_adaptive_thresholds(all_results)
    print(f"Adaptive Silhouette Threshold (p40): {thresholds['silhouette_threshold']:.3f}")
    print(f"Adaptive Davies-Bouldin Threshold (p60): {thresholds['db_threshold']:.2f}")
    print(f"Cluster Size Ratio Threshold: {thresholds['size_ratio_threshold']:.1f}× median")

    figure_counter = 1
    for d in DIMENSIONS_TO_TEST:
        results = all_results[d]['results']
        embeddings = all_results[d]['embeddings']
        figure_counter = analyze_dimension_results(
            d, results, embeddings, requirements, thresholds, figure_counter
        )

    print(f"\n{'=' * 80}")
    print("GLOBAL ANALYSIS")
    print(f"{'=' * 80}")

    best, all_configs = select_global_best(all_results, thresholds)
    print_global_best(best)

    csv_path = export_results_csv(all_configs)

    print(f"\n{'=' * 80}")
    print("EXPERIMENT COMPLETE")
    print(f"{'=' * 80}")

    if PLOTTING_ENABLED:
        total_figs = len(DIMENSIONS_TO_TEST) * 2
        print(f"\nGenerated {total_figs} visualizations:")
        print(f"  - figure_1 through figure_{total_figs}")
    else:
        print("\nMatplotlib not available — visualizations were skipped.")

    print("\nGenerated results:")
    total_configs = len(DIMENSIONS_TO_TEST) * len(K_RANGE)
    print(f"  - {csv_path} ({total_configs} configurations)")


if __name__ == "__main__":
    main()
