"""
Broadlistening Analysis Pipeline

A comprehensive text analysis pipeline demonstrating Kagura AI's workflow capabilities.
Combines LLM-based text processing with traditional ML (UMAP + KMeans clustering).

Features:
- Opinion extraction from comments
- Hierarchical clustering
- AI-powered cluster labeling
- Property-based filtering (gender, region, age_group)
- Overview generation

Based on: Talk to the City (AI Objectives Institute)
Reference: sample_repos/kouchou-ai/server/broadlistening/

Usage:
    python pipeline.py sample_data.csv --n-clusters 5

Example with property filtering:
    >>> result = await broadlistening_pipeline(df, n_clusters=5)
    >>> # Filter by gender
    >>> female_opinions = result['filter'].filter(gender="女性")
    >>> # Filter by multiple regions
    >>> tokyo_osaka = result['filter'].filter(region=["東京都", "大阪府"])
"""

import asyncio
import json
from pathlib import Path
from typing import Any

import pandas as pd
from kagura import agent
from pydantic import BaseModel, Field

# ============================================
# Data Models
# ============================================


class Comment(BaseModel):
    """Comment with demographic properties"""

    comment_id: str
    comment_body: str
    # Properties for filtering
    gender: str | None = None  # "男性", "女性", "その他", "未回答"
    region: str | None = None  # "東京都", "大阪府", etc.
    age_group: str | None = None  # "10代", "20代", "30代", etc.
    custom_props: dict[str, str] = Field(default_factory=dict)


class Opinion(BaseModel):
    """Extracted opinion with properties inherited from comment"""

    id: str
    text: str
    comment_id: str
    # Properties inherited from parent comment
    properties: dict[str, str] = Field(default_factory=dict)


class ClusterLabel(BaseModel):
    """Label and description for a cluster"""

    label: str
    description: str


class Cluster(BaseModel):
    """Cluster of opinions with AI-generated labels"""

    id: str
    label: str
    description: str
    opinions: list[Opinion]
    # Property distribution in this cluster
    # Example: {"gender": {"男性": 10, "女性": 15}, "region": {"東京": 8, "大阪": 17}}
    property_stats: dict[str, dict[str, int]] = Field(default_factory=dict)


# ============================================
# Kagura Agents
# ============================================


@agent(model="gpt-4o-mini")
async def opinion_extractor(comment: str) -> list[str]:
    """Extract opinions from a single comment

    You are an expert at analyzing public comments and extracting distinct opinions.

    Instructions:
    1. Read the comment carefully
    2. Identify all distinct opinions, concerns, or suggestions
    3. Extract each as a separate, self-contained statement
    4. Return as a JSON array of strings

    Comment: {{ comment }}

    Return ONLY a JSON array like: ["意見1", "意見2", "意見3"]
    """
    pass


@agent(model="gpt-4o-mini")
async def cluster_labeler(sample_opinions: list[str]) -> ClusterLabel:
    """Generate label and description for a cluster of opinions

    You are an expert at analyzing and categorizing public opinions.

    Instructions:
    1. Read the sample opinions below
    2. Identify the common theme or topic
    3. Create a short, descriptive label (3-8 words)
    4. Write a brief description (1-2 sentences) explaining what this cluster represents

    Sample opinions from this cluster:
    {% for opinion in sample_opinions %}
    - {{ opinion }}
    {% endfor %}

    Return JSON with format:
    {
        "label": "短いラベル (3-8語)",
        "description": "このクラスタの簡潔な説明 (1-2文)"
    }
    """
    pass


@agent(model="gpt-4o")
async def overview_generator(clusters: list[dict[str, Any]]) -> str:
    """Generate comprehensive overview of all clusters

    You are an expert at synthesizing insights from clustered public opinions.

    Instructions:
    1. Analyze all clusters below
    2. Identify major themes and patterns
    3. Generate a comprehensive overview report in Japanese

    Clusters:
    {% for cluster in clusters %}
    ## {{ cluster.label }}
    {{ cluster.description }}
    意見数: {{ cluster.opinion_count }}
    {% endfor %}

    Generate a report with:
    - エグゼクティブサマリー (2-3文)
    - 主要テーマ (3-5個)
    - 属性別の傾向（性別・地域など、データがある場合）
    - 結論と提言
    """
    pass


# ============================================
# Pipeline Workflow
# ============================================


async def broadlistening_pipeline(
    comments_df: pd.DataFrame,
    n_clusters: int = 10,
    property_columns: list[str] | None = None,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    """Complete broadlistening analysis pipeline with property tracking

    This workflow demonstrates:
    1. LLM-based opinion extraction
    2. Traditional ML clustering (UMAP + KMeans)
    3. AI-powered cluster labeling
    4. Property-based filtering
    5. Comprehensive overview generation

    Args:
        comments_df: DataFrame with columns:
            - comment-id (required)
            - comment-body (required)
            - gender, region, age_group, etc. (optional)
        n_clusters: Number of clusters to create
        property_columns: List of property columns to track
                         If None, auto-detect from dataframe
        output_dir: Directory to save outputs (default: ./outputs)

    Returns:
        {
            "clusters": List of Cluster objects,
            "opinions": List of all Opinion objects,
            "overview": Comprehensive overview text,
            "property_stats": Property distributions across all opinions,
            "filter": PropertyFilter instance for filtering,
            "embeddings": 2D UMAP embeddings for visualization,
            "labels": Cluster labels for each opinion
        }

    Example:
        >>> df = pd.read_csv("sample_data.csv")
        >>> result = await broadlistening_pipeline(df, n_clusters=5)
        >>> # Filter by gender
        >>> female_opinions = result['filter'].filter(gender="女性")
        >>> print(f"Female opinions: {len(female_opinions)}")
    """
    # Import here to avoid dependency issues when module is imported
    from clustering import cluster_opinions
    from filtering import PropertyFilter

    if output_dir is None:
        output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    # Auto-detect property columns
    if property_columns is None:
        property_columns = [
            col
            for col in comments_df.columns
            if col not in ["comment-id", "comment-body"]
        ]

    print("🔍 Starting broadlistening pipeline...")
    print(f"   Comments: {len(comments_df)}")
    print(f"   Clusters: {n_clusters}")
    print(f"   Properties: {property_columns}")

    # ============================================
    # Step 1: Extract opinions from comments
    # ============================================
    print("\n📝 Step 1: Extracting opinions from comments...")
    opinions: list[Opinion] = []

    for idx, row in comments_df.iterrows():
        comment_id = row["comment-id"]
        comment_body = row["comment-body"]

        # Extract opinions using LLM
        try:
            extracted_texts = await opinion_extractor(comment_body)
        except Exception as e:
            print(f"   ⚠️  Error extracting from {comment_id}: {e}")
            continue

        # Build property dict from row
        props = {
            col: str(row[col]) if pd.notna(row[col]) else "未回答"
            for col in property_columns
        }

        # Create Opinion objects with properties
        for i, text in enumerate(extracted_texts):
            opinion = Opinion(
                id=f"A{comment_id}_{i}",
                text=text,
                comment_id=comment_id,
                properties=props,
            )
            opinions.append(opinion)

    print(f"   ✅ Extracted {len(opinions)} opinions from {len(comments_df)} comments")

    if len(opinions) == 0:
        raise ValueError("No opinions extracted. Check your data and LLM responses.")

    # ============================================
    # Step 2: Cluster opinions using UMAP + KMeans
    # ============================================
    print("\n🔬 Step 2: Clustering opinions...")
    cluster_result = await cluster_opinions(
        opinions=[op.text for op in opinions], n_clusters=n_clusters
    )

    embeddings = cluster_result["embeddings"]
    cluster_labels = cluster_result["labels"]

    print(f"   ✅ Created {n_clusters} clusters")

    # ============================================
    # Step 3: Label clusters using LLM
    # ============================================
    print("\n🏷️  Step 3: Labeling clusters...")
    clusters: list[Cluster] = []

    for cluster_id in range(n_clusters):
        # Get opinions in this cluster
        cluster_opinion_objects = [
            opinions[i] for i, label in enumerate(cluster_labels) if label == cluster_id
        ]

        if len(cluster_opinion_objects) == 0:
            print(f"   ⚠️  Cluster {cluster_id} is empty, skipping")
            continue

        # Sample opinions for labeling (max 5)
        sample_texts = [op.text for op in cluster_opinion_objects[:5]]

        # Generate label using LLM
        try:
            label_data = await cluster_labeler(sample_texts)
        except Exception as e:
            print(f"   ⚠️  Error labeling cluster {cluster_id}: {e}")
            label_data = ClusterLabel(
                label=f"クラスタ {cluster_id}",
                description="ラベル生成エラー",
            )

        # Create Cluster object
        cluster = Cluster(
            id=f"C{cluster_id}",
            label=label_data.label,
            description=label_data.description,
            opinions=cluster_opinion_objects,
        )
        clusters.append(cluster)

        print(f"   Cluster {cluster_id}: {label_data.label} ({len(cluster_opinion_objects)} opinions)")

    # ============================================
    # Step 4: Calculate property statistics per cluster
    # ============================================
    print("\n📊 Step 4: Calculating property distributions...")
    for cluster in clusters:
        cluster.property_stats = {}
        for prop in property_columns:
            prop_filter = PropertyFilter(cluster.opinions)
            cluster.property_stats[prop] = prop_filter.get_property_distribution(prop)

    # ============================================
    # Step 5: Generate overview
    # ============================================
    print("\n📝 Step 5: Generating overview...")
    cluster_summaries = [
        {
            "label": c.label,
            "description": c.description,
            "opinion_count": len(c.opinions),
            "property_stats": c.property_stats,
        }
        for c in clusters
    ]

    try:
        overview = await overview_generator(cluster_summaries)
        overview_str = str(overview)  # Convert LLMResponse to string
    except Exception as e:
        print(f"   ⚠️  Error generating overview: {e}")
        overview_str = "概要生成エラー"

    print(f"   ✅ Generated overview ({len(overview_str)} chars)")

    # ============================================
    # Step 6: Create filter instance
    # ============================================
    filter_instance = PropertyFilter(opinions)
    overall_property_stats = {
        prop: filter_instance.get_property_distribution(prop)
        for prop in property_columns
    }

    # ============================================
    # Step 7: Save results
    # ============================================
    print("\n💾 Step 7: Saving results...")

    result = {
        "clusters": [c.model_dump() for c in clusters],
        "opinions": [op.model_dump() for op in opinions],
        "overview": overview_str,
        "property_stats": overall_property_stats,
        "embeddings": embeddings.tolist(),
        "labels": cluster_labels.tolist(),
    }

    # Save JSON
    json_path = output_dir / "result.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"   ✅ Saved results to {json_path}")

    # Save overview as text
    overview_path = output_dir / "overview.txt"
    with open(overview_path, "w", encoding="utf-8") as f:
        f.write(overview_str)
    print(f"   ✅ Saved overview to {overview_path}")

    # Return result with live objects (not serialized)
    return {
        "clusters": clusters,
        "opinions": opinions,
        "overview": overview_str,
        "property_stats": overall_property_stats,
        "filter": filter_instance,
        "embeddings": embeddings,
        "labels": cluster_labels,
    }


# ============================================
# CLI Entry Point
# ============================================


async def main():
    """Command-line interface for running the pipeline"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Broadlistening Analysis Pipeline - Public Comment Analysis with Kagura AI"
    )
    parser.add_argument(
        "input_csv",
        type=str,
        help="Path to input CSV file (must have comment-id and comment-body columns)",
    )
    parser.add_argument(
        "--n-clusters",
        type=int,
        default=5,
        help="Number of clusters to create (default: 5)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="outputs",
        help="Output directory (default: outputs)",
    )
    parser.add_argument(
        "--properties",
        type=str,
        nargs="+",
        help="Property columns to track (default: auto-detect)",
    )

    args = parser.parse_args()

    # Load data
    print(f"📂 Loading data from {args.input_csv}...")
    df = pd.read_csv(args.input_csv)
    print(f"   ✅ Loaded {len(df)} comments")

    # Run pipeline
    result = await broadlistening_pipeline(
        comments_df=df,
        n_clusters=args.n_clusters,
        property_columns=args.properties,
        output_dir=Path(args.output_dir),
    )

    # Print summary
    print("\n" + "=" * 60)
    print("✅ Pipeline Complete!")
    print("=" * 60)
    print(f"   Comments: {len(df)}")
    print(f"   Opinions: {len(result['opinions'])}")
    print(f"   Clusters: {len(result['clusters'])}")
    print(f"   Output: {args.output_dir}/")
    print("\nTop clusters:")
    for i, cluster in enumerate(result["clusters"][:5], 1):
        print(f"   {i}. {cluster.label} ({len(cluster.opinions)} opinions)")

    print("\nProperty distributions:")
    for prop, dist in result["property_stats"].items():
        print(f"   {prop}: {dict(list(dist.items())[:3])}...")

    print("\n💡 Next steps:")
    print(f"   - View results: cat {args.output_dir}/overview.txt")
    print("   - Filter by property: Use PropertyFilter in Python")
    print("   - Visualize: Run visualization.py (coming soon)")


if __name__ == "__main__":
    asyncio.run(main())
