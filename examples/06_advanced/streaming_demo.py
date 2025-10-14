"""Streaming Demo - Real-time response streaming

This example demonstrates:
- Streaming LLM responses token-by-token
- Improved perceived latency
- Better user experience
- Progressive output display
"""

import asyncio
import sys
from kagura import LLMConfig
from kagura.core.streaming import call_llm_stream, stream_to_string


config = LLMConfig(
    model="gpt-4o-mini",
    temperature=0.7
)


async def demo_basic_streaming():
    """Basic streaming demonstration"""
    print("=== Demo 1: Basic Streaming ===")
    print("Prompt: Write a short story about a robot\n")
    print("Response (streaming):")
    print("-" * 60)

    prompt = "Write a short story (3 paragraphs) about a friendly robot."

    # Stream response token by token
    async for chunk in call_llm_stream(prompt, config):
        print(chunk, end="", flush=True)

    print("\n" + "-" * 60)


async def demo_streaming_vs_non_streaming():
    """Compare streaming vs non-streaming experience"""
    print("\n\n=== Demo 2: Streaming vs Non-Streaming ===")

    prompt = "Explain quantum computing in simple terms."

    # Non-streaming (appears all at once after delay)
    print("\nNon-streaming (all at once):")
    print("Waiting...", end="", flush=True)
    stream = call_llm_stream(prompt, config)
    full_response = await stream_to_string(stream)
    print("\r" + " " * 20 + "\r", end="")  # Clear "Waiting..."
    print(full_response)

    # Streaming (progressive display)
    print("\n\nStreaming (progressive):")
    print("-" * 60)
    async for chunk in call_llm_stream(prompt, config):
        print(chunk, end="", flush=True)
    print("\n" + "-" * 60)


async def demo_streaming_with_spinner():
    """Streaming with a processing indicator"""
    print("\n\n=== Demo 3: Streaming with Status ===")

    prompt = "List 5 tips for learning Python programming."

    print("\nGenerating response... (streaming)\n")
    print("=" * 60)

    chunks_received = 0
    async for chunk in call_llm_stream(prompt, config):
        print(chunk, end="", flush=True)
        chunks_received += 1

    print("\n" + "=" * 60)
    print(f"Received {chunks_received} chunks")


async def demo_multiple_streaming():
    """Multiple streaming responses in sequence"""
    print("\n\n=== Demo 4: Multiple Streaming Responses ===")

    questions = [
        "What is Python?",
        "What is JavaScript?",
        "What is Rust?"
    ]

    for i, question in enumerate(questions, 1):
        print(f"\n{i}. {question}")
        print("-" * 60)

        async for chunk in call_llm_stream(
            f"Answer in 1-2 sentences: {question}",
            config
        ):
            print(chunk, end="", flush=True)

        print()  # New line after each response


async def demo_streaming_code_generation():
    """Stream code generation (useful for long outputs)"""
    print("\n\n=== Demo 5: Streaming Code Generation ===")

    prompt = """
    Write a Python function that implements a binary search algorithm.
    Include docstring and comments.
    """

    print("Generating code... (streaming)\n")
    print("```python")

    async for chunk in call_llm_stream(prompt, config):
        print(chunk, end="", flush=True)

    print("```")


async def demo_collect_streamed_response():
    """Show how to collect streamed response into string"""
    print("\n\n=== Demo 6: Collecting Streamed Response ===")

    prompt = "Explain the benefits of async programming."

    print("Streaming response...")

    # Collect chunks while displaying
    chunks = []
    async for chunk in call_llm_stream(prompt, config):
        print(chunk, end="", flush=True)
        chunks.append(chunk)

    full_response = "".join(chunks)

    print("\n\n" + "-" * 60)
    print(f"Total response length: {len(full_response)} characters")
    print(f"Number of chunks: {len(chunks)}")


async def main():
    print("Streaming Demo (RFC-025)")
    print("=" * 60)
    print("Streaming provides better UX with progressive output")
    print("First token arrives in <500ms (vs 2-5s for full response)")
    print("=" * 60)

    await demo_basic_streaming()
    await demo_streaming_vs_non_streaming()
    await demo_streaming_with_spinner()
    await demo_multiple_streaming()
    await demo_streaming_code_generation()
    await demo_collect_streamed_response()

    print("\n" + "=" * 60)
    print("Summary: Streaming significantly improves perceived latency!")


if __name__ == "__main__":
    asyncio.run(main())
