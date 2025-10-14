"""DataAnalystPreset - Data analysis and insights

This example demonstrates:
- Using DataAnalystPreset for data analysis
- Statistical insights
- Data interpretation
- Visualization recommendations
"""

import asyncio
from kagura.presets import DataAnalystPreset


async def main():
    print("DataAnalystPreset Demo")
    print("-" * 50)

    # Create data analyst
    analyst = (
        DataAnalystPreset("data_analyst")
        .with_model("gpt-4o-mini")
        .build()
    )

    # Sample datasets to analyze
    datasets = [
        {
            "name": "Sales Data",
            "data": "Monthly sales: Jan=100, Feb=120, Mar=150, Apr=130, May=180, Jun=200",
            "question": "What trends do you see and what should we focus on?"
        },
        {
            "name": "User Metrics",
            "data": "Daily active users: Mon=1000, Tue=1200, Wed=1100, Thu=1300, Fri=1500, Sat=800, Sun=700",
            "question": "Analyze the weekly pattern and suggest improvements"
        },
        {
            "name": "Survey Results",
            "data": "Customer satisfaction: Very Satisfied=45%, Satisfied=30%, Neutral=15%, Dissatisfied=7%, Very Dissatisfied=3%",
            "question": "What insights can you derive from this?"
        }
    ]

    for dataset in datasets:
        print(f"\n{'=' * 50}")
        print(f"Dataset: {dataset['name']}")
        print(f"Data: {dataset['data']}")
        print(f"Question: {dataset['question']}")
        print(f"{'=' * 50}")

        analysis = await analyst(
            f"Analyze this data: {dataset['data']}\n"
            f"Question: {dataset['question']}"
        )

        print(f"\nAnalysis:")
        print(analysis)

    print("\n" + "=" * 50)
    print("DataAnalystPreset Features:")
    print("- Statistical analysis")
    print("- Trend identification")
    print("- Actionable insights")
    print("- Visualization suggestions")


if __name__ == "__main__":
    asyncio.run(main())
