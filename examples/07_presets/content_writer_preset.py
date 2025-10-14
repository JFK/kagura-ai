"""ContentWriterPreset - Content creation assistant

This example demonstrates:
- Using ContentWriterPreset for writing
- Blog posts, articles, marketing copy
- SEO optimization suggestions
- Multiple content formats
"""

import asyncio
from kagura.presets import ContentWriterPreset


async def main():
    print("ContentWriterPreset Demo")
    print("-" * 50)

    # Create content writer
    writer = (
        ContentWriterPreset("content_writer")
        .with_model("gpt-4o-mini")
        .with_context(
            tone="professional yet engaging",
            style="clear and concise"
        )
        .build()
    )

    # Content creation requests
    requests = [
        {
            "type": "Blog Post Intro",
            "prompt": "Write an introduction for a blog post about 'The Benefits of Python for Data Science'"
        },
        {
            "type": "Social Media",
            "prompt": "Create 3 engaging tweets about AI agent frameworks"
        },
        {
            "type": "Product Description",
            "prompt": "Write a compelling product description for a productivity app"
        },
        {
            "type": "Email Subject Lines",
            "prompt": "Generate 5 catchy email subject lines for a new feature announcement"
        }
    ]

    for request in requests:
        print(f"\n{'=' * 50}")
        print(f"Content Type: {request['type']}")
        print(f"Request: {request['prompt']}")
        print(f"{'=' * 50}")

        content = await writer(request['prompt'])
        print(f"\nGenerated Content:")
        print(content)

    print("\n" + "=" * 50)
    print("ContentWriterPreset Features:")
    print("- Multiple content formats")
    print("- SEO awareness")
    print("- Tone and style control")
    print("- Engaging copy")


if __name__ == "__main__":
    asyncio.run(main())
