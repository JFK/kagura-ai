# SDK Integration Examples

Real-world examples showing how to integrate Kagura AI into your Python applications.

## 📋 Overview

These examples demonstrate production-ready integration patterns for:
- **Web APIs** (FastAPI)
- **Data Pipelines** (ETL/enrichment)
- **Automation** (Email processing)
- **Dashboards** (Streamlit)

All examples use the `@agent` decorator with type-safe outputs and built-in error handling.

---

## 📦 Installation

```bash
# Install SDK integration dependencies
pip install -e "examples/[sdk]"

# Or install all example dependencies
pip install -e "examples/[all]"
```

**Dependencies installed:**
- `fastapi>=0.104.0` - Web framework
- `uvicorn>=0.24.0` - ASGI server
- `streamlit>=1.28.0` - Dashboard framework
- `pandas>=2.0.0` - Data manipulation
- `httpx>=0.25.0` - HTTP client

---

## 🚀 Examples

### 1. FastAPI REST API (`fastapi_endpoint.py`)

Build AI-powered REST APIs with FastAPI integration.

**Use Case**: Customer support API with sentiment analysis

**Features**:
- Type-safe request/response models (Pydantic)
- Async AI agent endpoints
- Auto-generated OpenAPI docs
- Error handling

**Run**:
```bash
uvicorn examples.09_sdk_integration.fastapi_endpoint:app --reload
```

**Test**:
```bash
# Open browser
open http://localhost:8000/docs

# Or use curl
curl -X POST http://localhost:8000/api/support \
     -H "Content-Type: application/json" \
     -d '{"question": "How do I reset my password?"}'
```

**Key Code**:
```python
from fastapi import FastAPI
from kagura import agent

app = FastAPI()

@agent(model="gpt-4o-mini")
async def support_agent(question: str) -> SupportResponse:
    '''Answer customer support question: {{ question }}'''

@app.post("/api/support")
async def handle_support(request: SupportRequest):
    return await support_agent(question=request.question)
```

---

### 2. Data Pipeline (`data_pipeline.py`)

AI-powered ETL for data enrichment and cleaning.

**Use Cases**:
- Company data enrichment (web search + extraction)
- Email classification and routing
- Data cleaning and standardization

**Features**:
- Batch processing with asyncio
- Structured outputs (Pydantic models)
- Web search integration
- Parallel execution

**Run**:
```bash
python examples/09_sdk_integration/data_pipeline.py
```

**Key Code**:
```python
from kagura import agent

@agent(model="gpt-4o-mini", tools=["web_search"])
async def company_enricher(company_name: str) -> CompanyProfile:
    '''Enrich company data for: {{ company_name }}

    Use web_search(query) to find current information.
    Return structured JSON with industry, size, location, etc.
    '''

# Process in parallel
companies = ["Anthropic", "OpenAI", "Google DeepMind"]
tasks = [company_enricher(name) for name in companies]
profiles = await asyncio.gather(*tasks)

# Convert to DataFrame
df = pd.DataFrame([p.model_dump() for p in profiles])
```

---

### 3. Email Automation (`email_automation.py`)

Intelligent email processing and response generation.

**Use Cases**:
- Email classification (support/sales/billing/spam)
- Auto-response generation
- Priority detection
- Daily digest creation

**Features**:
- No external dependencies (standard library only)
- Batch processing
- Confidence scoring
- Human-in-the-loop decision making

**Run**:
```bash
python examples/09_sdk_integration/email_automation.py
```

**Key Code**:
```python
from kagura import agent

@agent(model="gpt-4o-mini")
async def email_analyzer(subject: str, body: str) -> EmailAnalysis:
    '''Analyze incoming email and categorize'''

@agent(model="gpt-4o-mini")
async def response_generator(original_body: str) -> AutoResponse:
    '''Generate professional email response'''

# Process email
analysis = await email_analyzer(subject, body, sender)
if analysis.category != EmailCategory.SPAM:
    response = await response_generator(original_body=body)
    if response.send_now and response.confidence > 0.8:
        send_email(response.body)
```

---

### 4. Streamlit Dashboard (`streamlit_dashboard.py`)

Interactive AI analytics dashboard.

**Use Cases**:
- Data exploration with natural language
- Automated insight generation
- Trend analysis and forecasting
- Business intelligence

**Features**:
- Real-time AI insights
- Natural language queries
- Interactive visualizations
- Automated recommendations

**Run**:
```bash
streamlit run examples/09_sdk_integration/streamlit_dashboard.py
```

**Key Code**:
```python
import streamlit as st
from kagura import agent

@agent(model="gpt-4o-mini")
async def data_analyzer(data_summary: str, question: str) -> str:
    '''Analyze data and answer question'''

@agent(model="gpt-4o-mini")
async def insight_generator(data_summary: str) -> list[DataInsight]:
    '''Generate 3-5 key insights from data'''

# In Streamlit app
st.title("📊 AI Analytics Dashboard")
question = st.text_input("Ask about your data:")
if st.button("Ask"):
    answer = await data_analyzer(data_summary, question)
    st.write(answer)
```

---

## 🎯 Common Patterns

### Pattern 1: Type-Safe Outputs

Use Pydantic models for structured, validated outputs:

```python
from pydantic import BaseModel
from kagura import agent

class Analysis(BaseModel):
    sentiment: str
    confidence: float
    keywords: list[str]

@agent
async def analyzer(text: str) -> Analysis:
    '''Analyze: {{ text }}'''

result = await analyzer("Great product!")
print(result.sentiment)  # IDE autocomplete works!
```

### Pattern 2: Error Handling

Handle AI failures gracefully:

```python
from fastapi import HTTPException

@app.post("/api/analyze")
async def analyze(text: str):
    try:
        result = await analyzer(text)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"AI processing failed: {str(e)}"
        )
```

### Pattern 3: Batch Processing

Process multiple items efficiently:

```python
import asyncio

# Sequential (slow)
results = []
for item in items:
    result = await process(item)
    results.append(result)

# Parallel (fast)
tasks = [process(item) for item in items]
results = await asyncio.gather(*tasks)
```

### Pattern 4: Web Search Integration

Enable agents to search the web:

```python
@agent(tools=["web_search"])
async def researcher(topic: str) -> str:
    '''Research {{ topic }} using web_search(query)'''

result = await researcher("Latest AI trends")
```

---

## 🧪 Testing

All examples include error handling and can be tested:

```bash
# Test FastAPI endpoint
pytest examples/09_sdk_integration/test_fastapi.py

# Test data pipeline
pytest examples/09_sdk_integration/test_pipeline.py

# Manual testing
python examples/09_sdk_integration/email_automation.py
```

---

## 📚 Learn More

- [Kagura AI SDK Guide](../../docs/sdk-guide.md)
- [API Reference](../../docs/api/)
- [@agent Decorator](../../docs/en/api/agent.md)
- [Built-in Tools](../../docs/en/api/tools.md)

---

## 💡 Tips

**Production Checklist**:
- ✅ Add retry logic for LLM calls
- ✅ Implement rate limiting
- ✅ Log agent inputs/outputs
- ✅ Monitor costs with `kagura monitor`
- ✅ Use environment variables for API keys
- ✅ Add human review for low-confidence results

**Performance**:
- Use `asyncio.gather()` for parallel processing
- Cache repeated queries
- Use `gpt-4o-mini` for speed, `gpt-4o` for accuracy
- Enable streaming for better UX

**Cost Control**:
```bash
# Track costs
kagura monitor cost

# View by agent
kagura monitor stats --agent support_agent
```

---

**Built with ❤️ for production AI**
