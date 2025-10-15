# RFC-025: Broadlistening Analysis Example

**Status**: Draft
**Created**: 2025-10-15
**Author**: Claude Code
**Related Issues**: TBD

---

## 📋 Overview

### Problem Statement

Kagura AI lacks real-world examples demonstrating complex data analysis workflows that combine:
- LLM-based text processing (extraction, labeling)
- Traditional ML (clustering, dimensionality reduction)
- Multi-step pipeline orchestration
- **Attribute-based filtering** (gender, region, age, etc.)
- Production-ready error handling

The `broadlistening` system from kouchou-ai provides an excellent use case: analyzing public comments through hierarchical clustering and AI-powered labeling.

### Proposed Solution

Add a comprehensive real-world example (`08_real_world/broadlistening_analysis/`) that:
1. Demonstrates Kagura's workflow capabilities for data analysis
2. Integrates scikit-learn/UMAP with Kagura agents
3. **Supports property-based filtering** (gender, region, age group, etc.)
4. Provides standalone dependency management (`examples/pyproject.toml`)
5. Serves as a reference for building production data pipelines

### Success Criteria

- ✅ Complete working pipeline (extraction → clustering → labeling → visualization)
- ✅ **Property filtering system** (filter by gender, region, or custom attributes)
- ✅ Examples use kagura-ai library only (no internal imports)
- ✅ Isolated dependencies (examples/pyproject.toml)
- ✅ Comprehensive documentation and tests
- ✅ Sample data with demographic properties
- ✅ Interactive filtering in visualization
- ✅ Can identify and fix kagura-ai bugs during development

---

## 🎯 Goals

### Primary Goals

1. **Real-World Showcase**: Demonstrate Kagura's capability for production data analysis
2. **Dependency Isolation**: Separate example-specific dependencies from core library
3. **Flexible Filtering**: Enable analysis by demographic segments
4. **Educational Value**: Teach users how to build complex AI pipelines
5. **Quality Assurance**: Discover and fix kagura-ai bugs through real-world usage

### Non-Goals

- ❌ Integrating broadlistening into kagura-ai core
- ❌ Creating a preset for text clustering (future work)
- ❌ Full FastAPI server implementation (example focuses on pipeline)
- ❌ Production deployment guides (separate documentation)

---

## 📐 Design

### Architecture

```
examples/
├── pyproject.toml                    # NEW: Example-specific dependencies
├── README.md                         # Update: Mention dependency management
└── 08_real_world/
    └── broadlistening_analysis/      # NEW
        ├── README.md                 # Usage guide
        ├── pipeline.py               # Main pipeline (Kagura + scikit-learn)
        ├── clustering.py             # UMAP + KMeans utilities
        ├── filtering.py              # NEW: Property-based filtering
        ├── visualization.py          # Results visualization (with filters)
        ├── demo.ipynb               # Jupyter notebook demo
        ├── sample_data.csv          # Test data (with properties)
        ├── test_pipeline.py         # pytest tests
        └── outputs/                 # Pipeline results
            └── .gitkeep
```

### Property-Based Filtering Design

#### Data Model

```python
# pipeline.py
from pydantic import BaseModel

class Comment(BaseModel):
    comment_id: str
    comment_body: str
    # Properties for filtering
    gender: str | None = None        # "男性", "女性", "その他", "未回答"
    region: str | None = None        # "東京都", "大阪府", etc.
    age_group: str | None = None     # "10代", "20代", "30代", etc.
    custom_props: dict[str, str] = {}  # Extensible custom properties

class Opinion(BaseModel):
    id: str
    text: str
    comment_id: str
    # Inherited properties from comment
    properties: dict[str, str] = {}

class Cluster(BaseModel):
    id: str
    label: str
    description: str
    opinions: list[Opinion]
    # Property distribution in this cluster
    property_stats: dict[str, dict[str, int]] = {}
    # Example: {"gender": {"男性": 10, "女性": 15}, "region": {"東京": 8, "大阪": 17}}
```

#### Filtering API

```python
# filtering.py
from typing import Callable

class PropertyFilter:
    """Filter opinions/clusters by properties"""

    def __init__(self, opinions: list[Opinion]):
        self.opinions = opinions

    def filter(
        self,
        gender: str | list[str] | None = None,
        region: str | list[str] | None = None,
        age_group: str | list[str] | None = None,
        custom: dict[str, str | list[str]] | None = None
    ) -> list[Opinion]:
        """Filter opinions by properties

        Examples:
            # Single value
            filter(gender="女性")

            # Multiple values (OR)
            filter(region=["東京都", "神奈川県"])

            # Multiple filters (AND)
            filter(gender="女性", region="東京都")

            # Custom properties
            filter(custom={"occupation": "会社員"})
        """
        filtered = self.opinions

        if gender:
            filtered = self._filter_by_property(filtered, "gender", gender)
        if region:
            filtered = self._filter_by_property(filtered, "region", region)
        if age_group:
            filtered = self._filter_by_property(filtered, "age_group", age_group)
        if custom:
            for key, value in custom.items():
                filtered = self._filter_by_property(filtered, key, value)

        return filtered

    def _filter_by_property(
        self,
        opinions: list[Opinion],
        property_name: str,
        value: str | list[str]
    ) -> list[Opinion]:
        """Filter by a single property"""
        values = [value] if isinstance(value, str) else value
        return [
            op for op in opinions
            if op.properties.get(property_name) in values
        ]

    def get_property_distribution(
        self,
        property_name: str,
        opinions: list[Opinion] | None = None
    ) -> dict[str, int]:
        """Get distribution of property values"""
        opinions = opinions or self.opinions
        distribution: dict[str, int] = {}

        for op in opinions:
            value = op.properties.get(property_name, "未回答")
            distribution[value] = distribution.get(value, 0) + 1

        return distribution
```

#### Pipeline Integration

```python
# pipeline.py
@workflow.stateful
async def broadlistening_pipeline(
    comments_df: pd.DataFrame,  # Must have property columns
    n_clusters: int = 10,
    property_columns: list[str] | None = None
) -> dict:
    """Complete analysis pipeline with property tracking

    Args:
        comments_df: DataFrame with columns:
            - comment-id (required)
            - comment-body (required)
            - gender, region, age_group, etc. (optional)
        n_clusters: Number of clusters
        property_columns: List of property columns to track
                         If None, auto-detect from dataframe

    Returns:
        {
            "clusters": [...],
            "opinions": [...],
            "overview": "...",
            "property_stats": {...},
            "filter": PropertyFilter instance
        }
    """
    # Auto-detect property columns
    if property_columns is None:
        property_columns = [
            col for col in comments_df.columns
            if col not in ["comment-id", "comment-body"]
        ]

    state = {"opinions": [], "clusters": [], "properties": property_columns}

    # Step 1: Extract opinions (with properties)
    print("🔍 Extracting opinions...")
    for _, row in comments_df.iterrows():
        extracted = await opinion_extractor(row["comment-body"])

        # Build property dict
        props = {
            col: str(row[col]) if pd.notna(row[col]) else "未回答"
            for col in property_columns
        }

        for i, text in enumerate(extracted):
            state["opinions"].append(Opinion(
                id=f"A{row['comment-id']}_{i}",
                text=text,
                comment_id=row["comment-id"],
                properties=props  # Attach properties
            ))

    # Steps 2-4: Embeddings, Clustering, Labeling (unchanged)
    # ...

    # Step 5: Calculate property statistics per cluster
    print("📊 Calculating property distributions...")
    for cluster in state["clusters"]:
        cluster.property_stats = {}
        for prop in property_columns:
            cluster.property_stats[prop] = PropertyFilter(
                cluster.opinions
            ).get_property_distribution(prop)

    # Step 6: Create filter instance
    filter_instance = PropertyFilter(state["opinions"])

    return {
        "clusters": state["clusters"],
        "opinions": state["opinions"],
        "overview": overview,
        "property_stats": {
            prop: filter_instance.get_property_distribution(prop)
            for prop in property_columns
        },
        "filter": filter_instance,
        "embeddings": umap_embeds.tolist(),
        "labels": labels.tolist()
    }
```

### Visualization with Filtering

```python
# visualization.py
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def create_interactive_visualization(
    result: dict,
    output_path: str = "outputs/visualization.html"
):
    """Create interactive HTML visualization with property filters

    Features:
    - Scatter plot of clusters (colored by cluster)
    - Dropdown filters for gender, region, age_group
    - Property distribution charts
    - Update plots dynamically based on filters
    """
    opinions = result["opinions"]
    clusters = result["clusters"]
    embeddings = result["embeddings"]
    property_stats = result["property_stats"]

    # Create figure with subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "Cluster Scatter Plot",
            "Gender Distribution",
            "Region Distribution",
            "Age Group Distribution"
        ),
        specs=[
            [{"type": "scatter"}, {"type": "bar"}],
            [{"type": "bar"}, {"type": "bar"}]
        ]
    )

    # 1. Scatter plot (clusters)
    for cluster in clusters:
        cluster_opinions = [op for op in opinions if any(
            co.id == op.id for co in cluster.opinions
        )]
        cluster_embeddings = [
            embeddings[i] for i, op in enumerate(opinions)
            if op in cluster_opinions
        ]

        fig.add_trace(
            go.Scatter(
                x=[e[0] for e in cluster_embeddings],
                y=[e[1] for e in cluster_embeddings],
                mode="markers",
                name=cluster.label,
                text=[op.text[:50] + "..." for op in cluster_opinions],
                hovertemplate="<b>%{text}</b><br>" +
                             "Cluster: " + cluster.label + "<extra></extra>"
            ),
            row=1, col=1
        )

    # 2. Property distribution charts
    if "gender" in property_stats:
        fig.add_trace(
            go.Bar(
                x=list(property_stats["gender"].keys()),
                y=list(property_stats["gender"].values()),
                name="Gender"
            ),
            row=1, col=2
        )

    if "region" in property_stats:
        fig.add_trace(
            go.Bar(
                x=list(property_stats["region"].keys()),
                y=list(property_stats["region"].values()),
                name="Region"
            ),
            row=2, col=1
        )

    if "age_group" in property_stats:
        fig.add_trace(
            go.Bar(
                x=list(property_stats["age_group"].keys()),
                y=list(property_stats["age_group"].values()),
                name="Age Group"
            ),
            row=2, col=2
        )

    # Add dropdown filters
    fig.update_layout(
        title="Broadlistening Analysis - Interactive Visualization",
        showlegend=True,
        height=800,
        updatemenus=[
            {
                "buttons": [
                    {
                        "label": "All",
                        "method": "update",
                        "args": [{"visible": [True] * len(fig.data)}]
                    },
                    # Add filter buttons dynamically
                ],
                "direction": "down",
                "showactive": True,
                "x": 0.1,
                "y": 1.15
            }
        ]
    )

    fig.write_html(output_path)
    print(f"✅ Visualization saved to {output_path}")
```

### Sample Data Format

```csv
# sample_data.csv
comment-id,comment-body,gender,region,age_group
C001,公園の遊具を増やしてほしい。子どもが遊べる場所が少ない。,女性,東京都,30代
C002,道路の舗装が悪い。危ないので改善を希望します。,男性,大阪府,40代
C003,図書館の開館時間を延長してください。仕事帰りに利用したい。,女性,神奈川県,20代
C004,保育園の待機児童問題を解決してほしい。,女性,東京都,30代
C005,公共施設のバリアフリー化を進めてください。,男性,東京都,60代
C006,夜間の街灯を増やして防犯対策を強化してほしい。,その他,大阪府,50代
C007,公園の清掃をもっと頻繁にしてほしい。,未回答,神奈川県,未回答
...
```

### Dependency Strategy

#### examples/pyproject.toml (Recommended ✅)

```toml
# examples/pyproject.toml
[project]
name = "kagura-ai-examples"
version = "2.5.0"
description = "Real-world examples for Kagura AI"
requires-python = ">=3.11"
dependencies = [
    "kagura-ai>=2.5.0",  # Main library
]

[project.optional-dependencies]
broadlistening = [
    "umap-learn>=0.5.5",
    "scikit-learn>=1.3.0",
    "pandas>=2.0.0",
    "plotly>=5.18.0",
    "jupyter>=1.0.0",
]
all = [
    "kagura-ai-examples[broadlistening]",
]

[build-system]
requires = ["setuptools>=42.0.0", "wheel"]
build-backend = "setuptools.build_meta"
```

---

## 🔄 Implementation Plan

### Phase 1: Infrastructure Setup (Day 1)

**Tasks**:
1. Create `examples/pyproject.toml`
2. Update `examples/README.md` with dependency instructions
3. Add `examples/08_real_world/broadlistening_analysis/` directory structure
4. Configure CI to install example dependencies
5. Create `sample_data.csv` with property columns

**Deliverables**:
- examples/pyproject.toml
- Updated examples/README.md
- Directory structure
- CI workflow update
- Sample data with demographics

**Testing**:
```bash
# Install examples
cd examples && pip install -e ".[broadlistening]"

# Verify imports
python -c "import umap; import sklearn; import plotly; print('OK')"
```

### Phase 2: Core Pipeline Implementation (Day 2-3)

**Tasks**:
1. Implement `pipeline.py` with Kagura agents:
   - `opinion_extractor` agent
   - `cluster_labeler` agent
   - `overview_generator` agent
   - `broadlistening_pipeline` workflow (with property tracking)
2. Implement `clustering.py` utilities:
   - UMAP dimensionality reduction
   - KMeans clustering
   - Hierarchical merging
3. **Implement `filtering.py`**:
   - PropertyFilter class
   - Multi-property filtering
   - Distribution calculation

**Deliverables**:
- pipeline.py (250-350 lines)
- clustering.py (100-150 lines)
- **filtering.py (150-200 lines)** ← NEW
- sample_data.csv (30 comments with properties)

**Testing**:
```bash
python examples/08_real_world/broadlistening_analysis/pipeline.py

# Test filtering
python -c "
from pipeline import broadlistening_pipeline
from filtering import PropertyFilter
import pandas as pd

df = pd.read_csv('sample_data.csv')
result = await broadlistening_pipeline(df)

# Filter by gender
filtered = result['filter'].filter(gender='女性')
print(f'Female opinions: {len(filtered)}')

# Filter by region
filtered = result['filter'].filter(region=['東京都', '大阪府'])
print(f'Tokyo/Osaka opinions: {len(filtered)}')
"
```

### Phase 3: Visualization & Notebook (Day 4)

**Tasks**:
1. Implement `visualization.py`:
   - **Interactive cluster scatter plot with property filters**
   - **Property distribution charts**
   - HTML report generation
2. Create `demo.ipynb`:
   - Step-by-step walkthrough
   - **Filtering examples**
   - Inline visualizations
   - Explanation cells
3. Add comprehensive README.md

**Deliverables**:
- visualization.py (with filtering UI)
- demo.ipynb
- README.md with filtering guide

**Testing**:
```bash
# Run notebook
jupyter notebook examples/08_real_world/broadlistening_analysis/demo.ipynb

# Generate HTML report
python -m visualization outputs/
```

### Phase 4: Tests & Documentation (Day 5)

**Tasks**:
1. Write `test_pipeline.py`:
   - Test opinion extraction
   - Test clustering with mock data
   - Test labeling
   - **Test property filtering**
   - Integration test (full pipeline)
2. Update examples/README.md
3. Add docstrings and type hints
4. Bug fixes discovered during testing

**Deliverables**:
- test_pipeline.py (pytest tests with filtering tests)
- Updated documentation
- Bug reports for kagura-ai (if found)

**Testing**:
```bash
pytest examples/08_real_world/broadlistening_analysis/test_pipeline.py -v

# Test filtering specifically
pytest -k "filter" -v

# Coverage
pytest --cov=examples/08_real_world/broadlistening_analysis
```

---

## 🧪 Testing Strategy

### Unit Tests (Filtering)

```python
# test_pipeline.py
import pytest
from filtering import PropertyFilter
from pipeline import Opinion

def test_property_filter_single_value():
    """Test filtering by single property value"""
    opinions = [
        Opinion(id="A1", text="意見1", comment_id="C1", properties={"gender": "女性"}),
        Opinion(id="A2", text="意見2", comment_id="C2", properties={"gender": "男性"}),
        Opinion(id="A3", text="意見3", comment_id="C3", properties={"gender": "女性"}),
    ]

    filter = PropertyFilter(opinions)
    result = filter.filter(gender="女性")

    assert len(result) == 2
    assert all(op.properties["gender"] == "女性" for op in result)

def test_property_filter_multiple_values():
    """Test filtering by multiple property values (OR)"""
    opinions = [
        Opinion(id="A1", text="意見1", comment_id="C1", properties={"region": "東京都"}),
        Opinion(id="A2", text="意見2", comment_id="C2", properties={"region": "大阪府"}),
        Opinion(id="A3", text="意見3", comment_id="C3", properties={"region": "神奈川県"}),
    ]

    filter = PropertyFilter(opinions)
    result = filter.filter(region=["東京都", "大阪府"])

    assert len(result) == 2

def test_property_filter_multiple_properties():
    """Test filtering by multiple properties (AND)"""
    opinions = [
        Opinion(id="A1", text="意見1", comment_id="C1",
                properties={"gender": "女性", "region": "東京都"}),
        Opinion(id="A2", text="意見2", comment_id="C2",
                properties={"gender": "男性", "region": "東京都"}),
        Opinion(id="A3", text="意見3", comment_id="C3",
                properties={"gender": "女性", "region": "大阪府"}),
    ]

    filter = PropertyFilter(opinions)
    result = filter.filter(gender="女性", region="東京都")

    assert len(result) == 1
    assert result[0].id == "A1"

def test_property_distribution():
    """Test property distribution calculation"""
    opinions = [
        Opinion(id="A1", text="意見1", comment_id="C1", properties={"gender": "女性"}),
        Opinion(id="A2", text="意見2", comment_id="C2", properties={"gender": "男性"}),
        Opinion(id="A3", text="意見3", comment_id="C3", properties={"gender": "女性"}),
    ]

    filter = PropertyFilter(opinions)
    dist = filter.get_property_distribution("gender")

    assert dist == {"女性": 2, "男性": 1}
```

### Integration Tests

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_pipeline_with_properties():
    """Test complete pipeline with property tracking"""
    df = pd.DataFrame({
        "comment-id": ["C1", "C2", "C3"],
        "comment-body": ["コメント1", "コメント2", "コメント3"],
        "gender": ["女性", "男性", "女性"],
        "region": ["東京都", "大阪府", "東京都"]
    })

    result = await broadlistening_pipeline(df, n_clusters=2)

    # Check property stats exist
    assert "property_stats" in result
    assert "gender" in result["property_stats"]
    assert "region" in result["property_stats"]

    # Check filtering works
    filtered = result["filter"].filter(gender="女性")
    assert len(filtered) > 0
```

---

## 📊 Metrics & Success Indicators

### Code Quality
- ✅ pyright --strict passes
- ✅ ruff check passes
- ✅ Test coverage > 80% (including filtering module)
- ✅ All docstrings present

### Functionality
- ✅ Pipeline runs end-to-end without errors
- ✅ Produces meaningful clusters (tested with sample data)
- ✅ **Property filtering works correctly**
- ✅ **Property distributions calculated accurately**
- ✅ Generates readable HTML report with filters
- ✅ Jupyter notebook executes fully

### Documentation
- ✅ README explains installation, usage, and filtering
- ✅ All functions have docstrings
- ✅ Notebook has explanatory markdown cells (including filtering examples)
- ✅ examples/README.md updated

### Performance
- ✅ Pipeline processes 30 comments in < 60 seconds (with mock LLM)
- ✅ Pipeline processes 30 comments in < 5 minutes (with real LLM)
- ✅ Filtering operations < 100ms for 1000 opinions
- ✅ Memory usage < 500MB

---

## 🚀 Rollout Plan

### Stage 1: Development (Week 1)
- Implement phases 1-4
- Internal testing
- Bug fixes

### Stage 2: Review (Week 1-2)
- Create GitHub Issue
- Create Draft PR from Issue branch
- Address review feedback

### Stage 3: Documentation (Week 2)
- Finalize README
- Add to examples/README.md
- Update main README.md (if needed)

### Stage 4: Release (Week 2)
- Merge PR
- Announce in release notes (v2.6.0 or later)
- Share in community channels

---

## 🔒 Risks & Mitigations

### Risk 1: Dependency Conflicts
**Impact**: Medium
**Probability**: Low
**Mitigation**: Use examples/pyproject.toml for isolation; test in clean venv

### Risk 2: LLM Cost for Real Testing
**Impact**: Low
**Probability**: High
**Mitigation**: Use LLMMock for unit tests; small sample data for integration tests

### Risk 3: UMAP Installation Issues
**Impact**: Medium
**Probability**: Medium
**Mitigation**: Document troubleshooting; provide fallback to PCA if UMAP fails

### Risk 4: Property Filter Performance
**Impact**: Low
**Probability**: Low
**Mitigation**: Optimize filtering with list comprehensions; benchmark with 10k opinions

### Risk 5: Example Becomes Outdated
**Impact**: Medium
**Probability**: High (over time)
**Mitigation**: Include in CI test suite; document maintenance schedule

---

## 📚 References

### Inspiration
- **Talk to the City**: https://github.com/AIObjectives/talk-to-the-city-reports
- **kouchou-ai**: sample_repos/kouchou-ai/server/broadlistening/

### Related Documentation
- Kagura Workflow API: docs/en/api/workflow.md
- Agent Testing: docs/en/tutorials/14-testing.md
- Real-world Examples: examples/08_real_world/README.md

### Dependencies
- UMAP: https://umap-learn.readthedocs.io/
- scikit-learn: https://scikit-learn.org/
- Plotly: https://plotly.com/python/

---

## 🤔 Open Questions

1. **Should we use HDBSCAN instead of KMeans?**
   - **Decision**: Start with KMeans (simpler), document HDBSCAN as alternative

2. **Should examples/pyproject.toml be a separate package?**
   - **Decision**: Yes, installable via `pip install -e examples/`

3. **How to handle large datasets in example?**
   - **Decision**: Sample data (30 comments), document scaling strategies

4. **Should we include FastAPI server example?**
   - **Decision**: No, focus on pipeline. Server example is separate RFC.

5. **How many property columns to support?**
   - **Decision**: Support arbitrary properties via custom_props dict, provide examples for common ones (gender, region, age_group)

---

## ✅ Acceptance Criteria

**Definition of Done**:
- [ ] examples/pyproject.toml created and tested
- [ ] broadlistening_analysis/ directory with all files
- [ ] **PropertyFilter class implemented and tested**
- [ ] **Sample data includes property columns**
- [ ] Pipeline runs successfully with sample data and tracks properties
- [ ] **Filtering by properties works correctly**
- [ ] All tests pass (unit + integration + filtering)
- [ ] Jupyter notebook executes fully with filtering examples
- [ ] **Visualization includes property distribution charts**
- [ ] Documentation complete (README + docstrings + filtering guide)
- [ ] CI passes (pyright, ruff, pytest)
- [ ] Draft PR created and reviewed
- [ ] No regressions in kagura-ai core tests

**Review Checklist**:
- [ ] Code follows CLAUDE.md guidelines
- [ ] Type hints present on all functions
- [ ] Error handling implemented
- [ ] LLM calls use proper mocking in tests
- [ ] examples/README.md updated
- [ ] No hardcoded API keys or secrets
- [ ] **Property filtering is extensible (supports custom properties)**

---

## 📝 Future Work

After RFC-025 completion:

1. **RFC-026**: Broadlistening FastAPI Server Example (with API endpoints for filtering)
2. **RFC-027**: Text Clustering Preset (`kagura.presets.ClusteringPreset`)
3. **RFC-028**: Advanced Filtering Features:
   - Numeric range filters (age: 20-30)
   - Date range filters
   - Regex pattern matching
   - Fuzzy matching for text properties
4. **RFC-029**: More Real-World Examples:
   - Sentiment Analysis Dashboard (with filtering)
   - Document Classification Pipeline
   - Time-Series Forecasting with LLM Context
5. **RFC-030**: Example Testing Framework
   - Automated example validation
   - Performance benchmarking
   - Cost estimation

---

## 🎓 Learning Objectives

Users completing this example will learn:

1. **Workflow Design**: Multi-step AI + ML pipelines
2. **Agent Integration**: Combining Kagura agents with traditional ML
3. **Data Processing**: Pandas + scikit-learn + LLM
4. **Property Management**: Tracking and filtering by demographics/attributes
5. **Interactive Visualization**: Plotly with dynamic filters
6. **Testing Strategies**: Mocking LLM calls, integration tests
7. **Production Patterns**: Error handling, logging, reproducibility

---

**This RFC provides a complete blueprint for adding a production-quality real-world example with property-based filtering to Kagura AI.**
