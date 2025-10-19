"""Streamlit Dashboard Example - AI-Powered Analytics Dashboard

This example demonstrates how to build an interactive AI dashboard using
Streamlit and Kagura AI agents for data analysis and insights.

Usage:
    # Install dependencies
    pip install -e "examples/[sdk]"

    # Run dashboard
    streamlit run examples/09_sdk_integration/streamlit_dashboard.py
"""

import asyncio
from datetime import datetime

import pandas as pd
import streamlit as st
from kagura import agent
from pydantic import BaseModel

# ============================================
# Page Configuration
# ============================================

st.set_page_config(
    page_title="AI Analytics Dashboard",
    page_icon="📊",
    layout="wide",
)

# ============================================
# Data Models
# ============================================


class DataInsight(BaseModel):
    """Data analysis insight"""

    title: str
    finding: str
    recommendation: str
    confidence: str  # high/medium/low
    impact: str  # high/medium/low


class TrendAnalysis(BaseModel):
    """Trend analysis result"""

    trend_direction: str  # up/down/stable
    percentage_change: float
    key_drivers: list[str]
    forecast: str
    anomalies: list[str]


# ============================================
# AI Agents
# ============================================


@agent(model="gpt-4o-mini")
async def data_analyzer(data_summary: str, question: str) -> str:
    """Analyze data and answer question

    Data Summary:
    {{ data_summary }}

    Question: {{ question }}

    Provide a clear, insightful answer based on the data.
    Include specific numbers and actionable recommendations.
    """
    pass


@agent(model="gpt-4o-mini")
async def insight_generator(data_summary: str, context: str) -> list[DataInsight]:
    """Generate insights from data

    Data Summary:
    {{ data_summary }}

    Context: {{ context }}

    Identify 3-5 key insights:
    - What's notable in the data?
    - What patterns or anomalies exist?
    - What actions should be taken?

    Return as JSON array of DataInsight objects.
    """
    pass


@agent(model="gpt-4o-mini")
async def trend_analyzer(
    data_points: list[float], labels: list[str]
) -> TrendAnalysis:
    """Analyze trend from time series data

    Data points: {{ data_points }}
    Labels: {{ labels }}

    Analyze:
    - Overall trend direction
    - Percentage change
    - Key drivers of change
    - Forecast for next period
    - Any anomalies or outliers

    Return as JSON matching TrendAnalysis model.
    """
    pass


# ============================================
# Sample Data Generation
# ============================================


def generate_sample_data() -> pd.DataFrame:
    """Generate sample sales data for demo"""
    dates = pd.date_range(end=datetime.now(), periods=30, freq="D")
    data = {
        "date": dates,
        "revenue": [1000 + i * 50 + (i % 7) * 100 for i in range(30)],
        "customers": [20 + i * 2 + (i % 5) * 3 for i in range(30)],
        "conversion_rate": [0.15 + (i % 10) * 0.01 for i in range(30)],
    }
    return pd.DataFrame(data)


def summarize_dataframe(df: pd.DataFrame) -> str:
    """Create text summary of DataFrame"""
    summary = f"""
    Dataset: {len(df)} rows, {len(df.columns)} columns
    Columns: {', '.join(df.columns)}

    Statistics:
    {df.describe().to_string()}

    Recent data (last 5 rows):
    {df.tail().to_string()}
    """
    return summary


# ============================================
# Dashboard UI
# ============================================


def main():
    """Main dashboard application"""

    # Header
    st.title("📊 AI Analytics Dashboard")
    st.markdown("Powered by Kagura AI v3.0")

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        analysis_depth = st.selectbox(
            "Analysis Depth",
            ["Quick", "Standard", "Deep"],
            index=1,
        )
        st.divider()
        st.header("📖 About")
        st.markdown(
            """
        This dashboard demonstrates:
        - **AI-powered insights**
        - **Natural language queries**
        - **Automated trend analysis**
        - **Real-time recommendations**
        """
        )

    # Load sample data
    df = generate_sample_data()

    # Tabs
    tab1, tab2, tab3 = st.tabs(["📈 Overview", "🤖 AI Insights", "💬 Ask AI"])

    # ----------------------------------------
    # Tab 1: Overview
    # ----------------------------------------
    with tab1:
        st.header("Data Overview")

        # Metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            total_revenue = df["revenue"].sum()
            st.metric("Total Revenue", f"${total_revenue:,.0f}")
        with col2:
            total_customers = df["customers"].sum()
            st.metric("Total Customers", f"{total_customers:,}")
        with col3:
            avg_conversion = df["conversion_rate"].mean()
            st.metric("Avg Conversion", f"{avg_conversion:.1%}")

        # Chart
        st.subheader("Revenue Trend")
        st.line_chart(df.set_index("date")["revenue"])

        # Data table
        st.subheader("Recent Data")
        st.dataframe(df.tail(10), use_container_width=True)

    # ----------------------------------------
    # Tab 2: AI Insights
    # ----------------------------------------
    with tab2:
        st.header("AI-Generated Insights")

        if st.button("🔍 Generate Insights", type="primary"):
            with st.spinner("Analyzing data with AI..."):
                # Prepare data summary
                data_summary = summarize_dataframe(df)
                context = "E-commerce sales data for the last 30 days"

                # Generate insights
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                insights = loop.run_until_complete(
                    insight_generator(data_summary, context)
                )
                loop.close()

                # Display insights
                for i, insight in enumerate(insights, 1):
                    with st.expander(f"💡 Insight {i}: {insight.title}", expanded=True):
                        st.markdown(f"**Finding:** {insight.finding}")
                        st.markdown(f"**Recommendation:** {insight.recommendation}")

                        col1, col2 = st.columns(2)
                        with col1:
                            st.badge(f"Confidence: {insight.confidence}")
                        with col2:
                            st.badge(f"Impact: {insight.impact}")

        # Trend Analysis
        st.divider()
        st.subheader("📈 Trend Analysis")

        if st.button("Analyze Revenue Trend"):
            with st.spinner("Analyzing trend..."):
                data_points = df["revenue"].tail(14).tolist()
                labels = df["date"].tail(14).dt.strftime("%m/%d").tolist()

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                trend = loop.run_until_complete(
                    trend_analyzer(data_points, labels)
                )
                loop.close()

                col1, col2 = st.columns(2)
                with col1:
                    st.metric(
                        "Trend Direction",
                        trend.trend_direction.upper(),
                        f"{trend.percentage_change:+.1f}%",
                    )
                with col2:
                    st.markdown("**Key Drivers:**")
                    for driver in trend.key_drivers:
                        st.markdown(f"- {driver}")

                st.markdown(f"**Forecast:** {trend.forecast}")

                if trend.anomalies:
                    st.warning("**Anomalies Detected:**")
                    for anomaly in trend.anomalies:
                        st.markdown(f"- {anomaly}")

    # ----------------------------------------
    # Tab 3: Ask AI
    # ----------------------------------------
    with tab3:
        st.header("💬 Ask AI About Your Data")
        st.markdown("Ask natural language questions about the data.")

        question = st.text_input(
            "Your Question:",
            placeholder="What's the average daily revenue?",
        )

        if st.button("Ask", type="primary") and question:
            with st.spinner("Thinking..."):
                data_summary = summarize_dataframe(df)

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                answer = loop.run_until_complete(
                    data_analyzer(data_summary, question)
                )
                loop.close()

                st.success("**AI Answer:**")
                st.markdown(answer)

        # Example questions
        st.divider()
        st.subheader("💡 Example Questions")
        examples = [
            "What's the revenue trend over the last week?",
            "Which days had the highest conversion rate?",
            "Are there any concerning patterns in the data?",
            "What actions should we take to improve revenue?",
        ]
        for example in examples:
            if st.button(example, key=f"example_{example}"):
                st.text_input("Your Question:", value=example, key="filled_question")


# ============================================
# Badge Helper (Streamlit doesn't have native badge)
# ============================================


def st_badge(label: str):
    """Display a badge (workaround)"""
    st.markdown(
        f'<span style="background-color: #e0e0e0; padding: 2px 8px; '
        f'border-radius: 12px; font-size: 12px;">{label}</span>',
        unsafe_allow_html=True,
    )


# Monkey-patch st with badge
st.badge = st_badge


# ============================================
# Run App
# ============================================

if __name__ == "__main__":
    main()
