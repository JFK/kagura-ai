"""
Clustering Utilities for Broadlistening Analysis

Provides UMAP + KMeans based clustering for text embeddings.

Based on: Talk to the City hierarchical clustering approach
Reference: sample_repos/kouchou-ai/server/broadlistening/pipeline/steps/hierarchical_clustering.py
"""

from typing import Any

import numpy as np
from litellm import embedding
from sklearn.cluster import KMeans


async def get_embeddings(texts: list[str], model: str = "text-embedding-3-small") -> np.ndarray:
    """Generate embeddings for texts using LiteLLM

    Args:
        texts: List of text strings to embed
        model: Embedding model to use (default: text-embedding-3-small)

    Returns:
        numpy array of shape (len(texts), embedding_dim)
    """
    print(f"   Generating embeddings for {len(texts)} texts...")

    # Use LiteLLM's embedding function
    response = embedding(model=model, input=texts)

    # Extract embeddings from response
    embeddings = [item["embedding"] for item in response.data]

    embeddings_array = np.array(embeddings)
    print(f"   ✅ Generated embeddings: {embeddings_array.shape}")

    return embeddings_array


def cluster_embeddings_umap_kmeans(
    embeddings: np.ndarray, n_clusters: int = 10
) -> tuple[np.ndarray, np.ndarray]:
    """Cluster embeddings using UMAP + KMeans

    Process:
    1. Dimensionality reduction with UMAP (high-dim → 2D)
    2. Clustering with KMeans on 2D space

    Args:
        embeddings: High-dimensional embeddings (N x D)
        n_clusters: Number of clusters

    Returns:
        - umap_embeddings: 2D UMAP embeddings (N x 2) for visualization
        - labels: Cluster labels for each embedding (N,)
    """
    try:
        from umap import UMAP
    except ImportError:
        raise ImportError(
            "UMAP is required for clustering. Install with: pip install umap-learn"
        )

    n_samples = embeddings.shape[0]

    # Adjust n_neighbors for small datasets
    default_n_neighbors = 15
    if n_samples <= default_n_neighbors:
        n_neighbors = max(2, n_samples - 1)
        print(f"   ⚠️  Small dataset detected. Using n_neighbors={n_neighbors}")
    else:
        n_neighbors = default_n_neighbors

    # Step 1: UMAP dimensionality reduction
    print(f"   Running UMAP (n_neighbors={n_neighbors})...")
    umap_model = UMAP(random_state=42, n_components=2, n_neighbors=n_neighbors)
    umap_embeddings = umap_model.fit_transform(embeddings)
    print(f"   ✅ UMAP complete: {umap_embeddings.shape}")

    # Step 2: KMeans clustering on 2D UMAP space
    print(f"   Running KMeans (n_clusters={n_clusters})...")
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(umap_embeddings)
    print(f"   ✅ KMeans complete: {n_clusters} clusters")

    # Print cluster distribution
    unique, counts = np.unique(labels, return_counts=True)
    print("   Cluster distribution:")
    for cluster_id, count in zip(unique, counts):
        print(f"      Cluster {cluster_id}: {count} items")

    return umap_embeddings, labels


async def cluster_opinions(
    opinions: list[str], n_clusters: int = 10
) -> dict[str, Any]:
    """Complete clustering pipeline: embed + UMAP + KMeans

    This is the main entry point for clustering text opinions.

    Args:
        opinions: List of opinion texts
        n_clusters: Number of clusters to create

    Returns:
        {
            "embeddings": 2D UMAP embeddings (np.ndarray),
            "labels": Cluster labels (np.ndarray),
            "n_clusters": Number of clusters created
        }

    Example:
        >>> opinions = ["意見1", "意見2", "意見3"]
        >>> result = await cluster_opinions(opinions, n_clusters=2)
        >>> print(result["labels"])  # [0, 1, 0]
    """
    if len(opinions) < n_clusters:
        print(
            f"   ⚠️  Warning: Only {len(opinions)} opinions but {n_clusters} clusters requested"
        )
        n_clusters = max(1, len(opinions) // 2)
        print(f"   Adjusting to {n_clusters} clusters")

    # Step 1: Generate embeddings
    embeddings = await get_embeddings(opinions)

    # Step 2: Cluster with UMAP + KMeans
    umap_embeddings, labels = cluster_embeddings_umap_kmeans(embeddings, n_clusters)

    return {
        "embeddings": umap_embeddings,
        "labels": labels,
        "n_clusters": n_clusters,
    }


# ============================================
# Utility Functions
# ============================================


def get_cluster_centers(
    embeddings: np.ndarray, labels: np.ndarray
) -> dict[int, np.ndarray]:
    """Calculate cluster centers (centroids) in embedding space

    Args:
        embeddings: 2D embeddings (N x 2)
        labels: Cluster labels (N,)

    Returns:
        Dictionary mapping cluster_id to centroid coordinates
    """
    centers = {}
    for cluster_id in np.unique(labels):
        cluster_points = embeddings[labels == cluster_id]
        centers[cluster_id] = np.mean(cluster_points, axis=0)
    return centers


def get_cluster_stats(labels: np.ndarray) -> dict[str, Any]:
    """Calculate statistics about clusters

    Args:
        labels: Cluster labels (N,)

    Returns:
        {
            "n_clusters": int,
            "sizes": dict[int, int],  # cluster_id -> size
            "largest_cluster": int,
            "smallest_cluster": int,
            "avg_size": float
        }
    """
    unique, counts = np.unique(labels, return_counts=True)
    sizes = dict(zip(unique.tolist(), counts.tolist()))

    return {
        "n_clusters": len(unique),
        "sizes": sizes,
        "largest_cluster": int(np.max(counts)),
        "smallest_cluster": int(np.min(counts)),
        "avg_size": float(np.mean(counts)),
    }
