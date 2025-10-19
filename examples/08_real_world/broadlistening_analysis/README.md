# Broadlistening Analysis - Public Comment Analysis Pipeline

A comprehensive real-world example demonstrating Kagura AI v3.0's workflow capabilities for text analysis, combining LLM-based processing with traditional machine learning.

**Features**:
- 🔍 LLM-powered opinion extraction (`@agent` decorator)
- 🔬 Hierarchical clustering (UMAP + KMeans)
- 🏷️ AI-generated cluster labels
- 📊 Property-based filtering (gender, region, age group)
- 📈 Interactive visualization (Plotly)
- 🎯 Type-safe outputs (Pydantic v2)

**Based on**: [Talk to the City](https://github.com/AIObjectives/talk-to-the-city-reports) by AI Objectives Institute

**New in v3.0**: Fully rewritten with `@agent` decorator for cleaner, type-safe code.

---

## 📋 Overview

This example showcases how to build a production-quality data analysis pipeline that:
1. Extracts opinions from public comments using LLMs
2. Clusters similar opinions using UMAP dimensionality reduction and KMeans
3. Generates descriptive labels for each cluster using AI
4. Enables filtering by demographic properties (gender, region, etc.)
5. Produces interactive visualizations and comprehensive reports

**Use Cases**:
- Government public comment analysis (広聴業務)
- Customer feedback categorization
- Survey response analysis
- Social media sentiment clustering

---

## 🚀 Quick Start

### Prerequisites

```bash
# Install broadlistening dependencies
pip install -e "examples/[broadlistening]"
```

**Required API Key**:
```bash
export OPENAI_API_KEY="your-key-here"
```

### Run the Pipeline

```bash
cd examples/08_real_world/broadlistening_analysis

# Run with sample data
python pipeline.py sample_data.csv --n-clusters 5

# Specify output directory
python pipeline.py sample_data.csv --n-clusters 5 --output-dir my_outputs
```

**Output**:
- `outputs/result.json` - Complete analysis results
- `outputs/overview.txt` - Human-readable overview report

---

## 📐 Architecture

### Pipeline Flow

```
1. Opinion Extraction (LLM)
   ↓
2. Embedding Generation (OpenAI)
   ↓
3. Dimensionality Reduction (UMAP)
   ↓
4. Clustering (KMeans)
   ↓
5. Cluster Labeling (LLM)
   ↓
6. Property Analysis & Filtering
   ↓
7. Visualization & Report Generation
```

### File Structure

```
broadlistening_analysis/
├── pipeline.py           # Main pipeline (Kagura workflow)
├── clustering.py         # UMAP + KMeans utilities
├── filtering.py          # Property-based filtering
├── visualization.py      # Plotly visualization
├── sample_data.csv       # Test data (30 comments)
├── test_pipeline.py      # pytest tests
└── outputs/              # Results directory
```

---

## 💻 Usage

### Basic Pipeline

```python
import asyncio
import pandas as pd
from pipeline import broadlistening_pipeline

# Load data
df = pd.read_csv("sample_data.csv")

# Run pipeline
result = asyncio.run(broadlistening_pipeline(
    comments_df=df,
    n_clusters=5
))

print(f"Found {len(result['clusters'])} clusters")
print(f"Extracted {len(result['opinions'])} opinions")
```

### Property-Based Filtering

```python
from filtering import PropertyFilter

# Create filter
filter = PropertyFilter(result['opinions'])

# Filter by gender
female_opinions = filter.filter(gender="女性")
print(f"Female opinions: {len(female_opinions)}")

# Filter by multiple regions (OR)
tokyo_osaka = filter.filter(region=["東京都", "大阪府"])
print(f"Tokyo/Osaka opinions: {len(tokyo_osaka)}")

# Filter by multiple properties (AND)
tokyo_females_30s = filter.filter(
    gender="女性",
    region="東京都",
    age_group="30代"
)
print(f"Tokyo females in 30s: {len(tokyo_females_30s)}")

# Get property distribution
gender_dist = filter.get_property_distribution("gender")
# {"女性": 15, "男性": 10, "その他": 3, "未回答": 2}

# Get summary statistics
summary = filter.summary()
print(summary["completeness"])  # % answered for each property
```

### Visualization

```python
from visualization import create_visualization

# Create interactive HTML visualization
create_visualization(result, output_path="outputs/viz.html")

# Open in browser: outputs/viz.html
```

---

## 📊 Data Format

### Input CSV Format

Your CSV must include:
- **comment-id** (required): Unique identifier
- **comment-body** (required): Comment text
- **property columns** (optional): gender, region, age_group, etc.

**Example**:
```csv
comment-id,comment-body,gender,region,age_group
C001,公園の遊具を増やしてほしい,女性,東京都,30代
C002,道路の舗装が悪い,男性,大阪府,40代
C003,図書館の開館時間を延長してほしい,女性,神奈川県,20代
```

**Supported Property Values**:
- **gender**: 男性, 女性, その他, 未回答
- **region**: 東京都, 大阪府, etc. (any string)
- **age_group**: 10代, 20代, 30代, etc.
- **custom**: Add any custom property columns

---

## 🧪 Testing

```bash
# Run all tests
pytest test_pipeline.py -v

# Run specific tests
pytest test_pipeline.py::test_property_filter -v

# With coverage
pytest test_pipeline.py --cov=. --cov-report=html
```

---

## 🎓 Key Concepts

### 1. Kagura Agents for Text Processing

```python
from kagura import agent

@agent(model="gpt-4o-mini")
async def opinion_extractor(comment: str) -> list[str]:
    """Extract opinions from comment as JSON array"""
    pass
```

**Kagura automatically handles**:
- LLM API calls (via LiteLLM)
- JSON parsing and validation
- Type conversion (Pydantic)
- Error handling and retries

### 2. Combining LLM + Traditional ML

```python
# Step 1: Extract opinions (LLM)
opinions = await opinion_extractor(comment)

# Step 2: Cluster opinions (scikit-learn)
from clustering import cluster_opinions
result = await cluster_opinions(opinions, n_clusters=5)

# Step 3: Label clusters (LLM)
labels = await cluster_labeler(sample_opinions)
```

**Benefits**:
- LLMs for unstructured → structured conversion
- Traditional ML for efficient numerical operations
- Best of both worlds!

### 3. Property-Based Analysis

Track and filter by demographics:

```python
# Attach properties to opinions
opinion = Opinion(
    id="A1",
    text="公園の遊具を増やしてほしい",
    comment_id="C1",
    properties={
        "gender": "女性",
        "region": "東京都",
        "age_group": "30代"
    }
)

# Filter and analyze by segment
filter = PropertyFilter(opinions)
tokyo_30s = filter.filter(region="東京都", age_group="30代")
```

---

## 📚 Learning Objectives

After completing this example, you'll understand:

1. **Workflow Design**: Multi-step AI + ML pipelines with Kagura
2. **LLM Integration**: Using `@agent` decorator for text processing
3. **Traditional ML**: UMAP, KMeans, and scikit-learn integration
4. **Property Management**: Tracking and filtering by attributes
5. **Data Modeling**: Pydantic models for type-safe data
6. **Visualization**: Interactive charts with Plotly
7. **Testing**: Mocking LLM calls, integration tests

---

## 🔧 Configuration

### Clustering Parameters

```python
result = await broadlistening_pipeline(
    comments_df=df,
    n_clusters=10,              # Number of clusters
    property_columns=["gender", "region"],  # Properties to track
    output_dir=Path("outputs")  # Output directory
)
```

### LLM Models

Change models in `pipeline.py`:

```python
@agent(model="gpt-4o")  # More accurate, more expensive
async def opinion_extractor(comment: str) -> list[str]:
    pass

@agent(model="gpt-4o-mini")  # Faster, cheaper
async def cluster_labeler(opinions: list[str]) -> dict:
    pass
```

---

## 🚨 Troubleshooting

### UMAP Installation Issues

If UMAP fails to install:

```bash
# macOS
brew install llvm libomp
pip install umap-learn

# Linux
sudo apt-get install build-essential
pip install umap-learn

# Windows
# Use pre-built wheels from: https://www.lfd.uci.edu/~gohlke/pythonlibs/
```

### Small Dataset Warning

For datasets < 30 comments:
- UMAP may struggle with dimensionality reduction
- Reduce `n_clusters` to 2-3
- Consider using PCA instead (fallback in `clustering.py`)

### LLM API Errors

```python
# Retry configuration
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential())
async def resilient_extraction(comment):
    return await opinion_extractor(comment)
```

---

## 📖 References

### Inspiration
- **Talk to the City**: https://github.com/AIObjectives/talk-to-the-city-reports
- **Kouchou-AI**: sample_repos/kouchou-ai/server/broadlistening/

### Documentation
- [Kagura Workflow API](../../../docs/en/api/workflow.md)
- [Agent Testing](../../../docs/en/tutorials/14-testing.md)
- [Real-world Examples](../../README.md)

### Dependencies
- [UMAP](https://umap-learn.readthedocs.io/) - Dimensionality reduction
- [scikit-learn](https://scikit-learn.org/) - Clustering
- [Plotly](https://plotly.com/python/) - Visualization
- [Kagura AI](https://github.com/JFK/kagura-ai) - Agent framework

---

## 🤝 Contributing

Found a bug? Have an improvement idea?

1. Check existing issues: https://github.com/JFK/kagura-ai/issues
2. Create a new issue with RFC tag
3. Follow CLAUDE.md guidelines for implementation

---

## 📝 License

Apache License 2.0 - see [LICENSE](../../../LICENSE)

---

## 🎉 Next Steps

1. **Run the example**: `python pipeline.py sample_data.csv`
2. **Try your own data**: Prepare CSV with comment-id and comment-body
3. **Experiment with filters**: Filter by different properties
4. **Visualize results**: Open `outputs/viz.html` in browser
5. **Extend the pipeline**: Add custom processing steps

**Happy analyzing with Kagura AI! 📊**

---

Built with ❤️ by the Kagura AI community
