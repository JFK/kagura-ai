"""
Visualization for Broadlistening Analysis

Creates interactive visualizations using Plotly for cluster analysis results.

Example:
    >>> from visualization import create_visualization
    >>> create_visualization(result, output_path="outputs/viz.html")
"""

from pathlib import Path
from typing import Any

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def create_visualization(
    result: dict[str, Any], output_path: str | Path = "outputs/visualization.html"
) -> None:
    """Create interactive HTML visualization of clustering results

    Generates:
    - Cluster scatter plot (2D UMAP embeddings)
    - Property distribution bar charts

    Args:
        result: Pipeline result dictionary with keys:
            - clusters: List of Cluster objects
            - embeddings: 2D UMAP embeddings (np.ndarray or list)
            - labels: Cluster labels (np.ndarray or list)
            - property_stats: Property distributions
        output_path: Path to save HTML file

    Example:
        >>> result = await broadlistening_pipeline(df)
        >>> create_visualization(result, "outputs/viz.html")
    """
    clusters = result["clusters"]
    embeddings = np.array(result["embeddings"])
    labels = np.array(result["labels"])
    property_stats = result.get("property_stats", {})

    # Count property charts
    n_properties = len(property_stats)
    n_rows = 1 + (n_properties + 1) // 2  # Scatter + property charts in 2 columns

    # Create subplot titles
    subplot_titles = ["Cluster Scatter Plot"]
    for prop in property_stats.keys():
        subplot_titles.append(f"{prop} Distribution")

    # Create figure with subplots
    specs = [[{"type": "scatter", "colspan": 2}] + [None]]  # Scatter plot spans 2 columns
    for i in range(n_properties // 2 + n_properties % 2):
        specs.append([{"type": "bar"}, {"type": "bar"}])

    fig = make_subplots(
        rows=n_rows,
        cols=2,
        subplot_titles=subplot_titles,
        vertical_spacing=0.12,
        horizontal_spacing=0.1,
        specs=specs,
    )

    # ============================================
    # 1. Cluster Scatter Plot
    # ============================================
    for cluster in clusters:
        # Get indices of opinions in this cluster
        cluster_opinion_ids = {op.id for op in cluster.opinions}
        cluster_indices = [
            i
            for i, op in enumerate(result["opinions"])
            if op.id in cluster_opinion_ids
        ]

        if len(cluster_indices) == 0:
            continue

        cluster_embeddings = embeddings[cluster_indices]
        cluster_texts = [result["opinions"][i].text for i in cluster_indices]

        # Truncate text for hover
        hover_texts = [text[:100] + "..." if len(text) > 100 else text for text in cluster_texts]

        fig.add_trace(
            go.Scatter(
                x=cluster_embeddings[:, 0],
                y=cluster_embeddings[:, 1],
                mode="markers",
                name=cluster.label,
                text=hover_texts,
                hovertemplate="<b>%{text}</b><br>" + f"Cluster: {cluster.label}<extra></extra>",
                marker=dict(size=8, line=dict(width=0.5, color="white")),
            ),
            row=1,
            col=1,
        )

    # ============================================
    # 2. Property Distribution Charts
    # ============================================
    prop_list = list(property_stats.items())
    for i, (prop_name, distribution) in enumerate(prop_list):
        row = 2 + i // 2
        col = 1 + i % 2

        # Sort by count (descending)
        sorted_items = sorted(distribution.items(), key=lambda x: x[1], reverse=True)
        x_values = [item[0] for item in sorted_items]
        y_values = [item[1] for item in sorted_items]

        fig.add_trace(
            go.Bar(x=x_values, y=y_values, name=prop_name, showlegend=False), row=row, col=col
        )

        # Update axes
        fig.update_xaxes(title_text=prop_name, row=row, col=col)
        fig.update_yaxes(title_text="Count", row=row, col=col)

    # ============================================
    # Layout
    # ============================================
    fig.update_layout(
        title={
            "text": "Broadlistening Analysis - Interactive Visualization",
            "x": 0.5,
            "xanchor": "center",
        },
        showlegend=True,
        height=300 + 300 * n_rows,
        legend=dict(orientation="v", yanchor="top", y=0.99, xanchor="left", x=1.02),
    )

    # Update scatter plot axes
    fig.update_xaxes(title_text="UMAP Dimension 1", row=1, col=1)
    fig.update_yaxes(title_text="UMAP Dimension 2", row=1, col=1)

    # Save
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(output_path)
    print(f"✅ Visualization saved to {output_path}")


def create_simple_scatter(
    embeddings: np.ndarray, labels: np.ndarray, output_path: str | Path = "outputs/scatter.html"
) -> None:
    """Create simple scatter plot of clusters

    Args:
        embeddings: 2D embeddings (N x 2)
        labels: Cluster labels (N,)
        output_path: Path to save HTML file

    Example:
        >>> create_simple_scatter(umap_embeds, cluster_labels)
    """
    fig = go.Figure()

    for cluster_id in np.unique(labels):
        cluster_points = embeddings[labels == cluster_id]
        fig.add_trace(
            go.Scatter(
                x=cluster_points[:, 0],
                y=cluster_points[:, 1],
                mode="markers",
                name=f"Cluster {cluster_id}",
                marker=dict(size=8),
            )
        )

    fig.update_layout(
        title="Cluster Scatter Plot",
        xaxis_title="UMAP Dimension 1",
        yaxis_title="UMAP Dimension 2",
        height=600,
    )

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(output_path)
    print(f"✅ Scatter plot saved to {output_path}")
