"""TranslatorPreset - Multi-language translation agent

This example demonstrates:
- Using TranslatorPreset for translations
- Low temperature for consistency
- Multiple language support
- Caching for repeated translations
"""

import asyncio
from kagura.presets import TranslatorPreset


async def main():
    print("TranslatorPreset Demo")
    print("-" * 50)

    # Create translator
    translator = (
        TranslatorPreset("translator")
        .with_model("gpt-4o-mini")
        .build()
    )

    # Translation requests
    translations = [
        ("Hello, how are you?", "Spanish"),
        ("Good morning", "Japanese"),
        ("Thank you very much", "French"),
        ("Where is the library?", "German"),
        ("I love programming", "Italian")
    ]

    for text, target_lang in translations:
        prompt = f"Translate '{text}' to {target_lang}"
        result = await translator(prompt)

        print(f"\nOriginal ({target_lang}): {text}")
        print(f"Translation: {result}")

    # Demonstrate consistency with caching
    print("\n" + "=" * 50)
    print("Testing consistency (same request twice):")

    text = "Hello, world!"
    target = "Spanish"
    prompt = f"Translate '{text}' to {target}"

    result1 = await translator(prompt)
    result2 = await translator(prompt)  # Should be cached

    print(f"\nFirst: {result1}")
    print(f"Second: {result2}")
    print(f"Consistent: {result1 == result2}")

    print("\n" + "=" * 50)
    print("TranslatorPreset Features:")
    print("- Low temperature (0.3) for consistency")
    print("- Multi-language support")
    print("- Caching enabled by default")
    print("- Accurate translations")


if __name__ == "__main__":
    asyncio.run(main())
