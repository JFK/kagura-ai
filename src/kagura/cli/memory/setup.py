"""Memory setup and model installation commands.

Provides commands for downloading embedding and reranking models.
"""

from __future__ import annotations

import os

import click
from rich.console import Console

console = Console()

# Default reranking model (v4.2.0+, BGE-reranker-v2-m3)
DEFAULT_RERANKER_MODEL = "BAAI/bge-reranker-v2-m3"


@click.command(name="setup")
@click.option(
    "--model",
    default=None,
    help="Embedding model (default: auto-detect based on OPENAI_API_KEY)",
)
@click.option(
    "--provider",
    type=click.Choice(["openai", "local"], case_sensitive=False),
    default=None,
    help="Force provider: 'openai' (API) or 'local' (sentence-transformers)",
)
def setup_command(model: str | None, provider: str | None) -> None:
    """Pre-download embeddings model to avoid MCP timeout.

    Downloads and initializes the embedding model used for semantic search.
    Run this once before using MCP memory tools to prevent first-time timeouts.

    Provider auto-detection:
    - If OPENAI_API_KEY is set → OpenAI Embeddings API (text-embedding-3-large)
    - Otherwise → Local model (intfloat/multilingual-e5-large, ~500MB download)

    Examples:

        # Auto-detect based on OPENAI_API_KEY
        kagura memory setup

        # Force OpenAI API (requires OPENAI_API_KEY)
        kagura memory setup --provider openai

        # Force local model
        kagura memory setup --provider local

        # Specific model
        kagura memory setup --model intfloat/multilingual-e5-base
    """
    from kagura.config.memory_config import EmbeddingConfig

    console.print("\n[cyan]Kagura Memory Setup[/cyan]")
    console.print()

    # Auto-detect provider if not specified
    has_openai_key = bool(os.getenv("OPENAI_API_KEY"))

    if provider is None:
        if has_openai_key:
            provider = "openai"
            console.print("[green]✓ OPENAI_API_KEY detected[/green]")
        else:
            provider = "local"
            console.print("[yellow]⚠ OPENAI_API_KEY not set[/yellow]")
        console.print(f"Using provider: [bold]{provider}[/bold]")
        console.print()

    # Set default model based on provider
    if model is None:
        if provider == "openai":
            model = "text-embedding-3-large"
        else:
            model = "intfloat/multilingual-e5-large"

    # Provider-specific setup
    if provider == "openai":
        console.print(f"Using OpenAI Embeddings API: [bold]{model}[/bold]")
        console.print("[dim](API-based, no download required)[/dim]")
        console.print()

        if not has_openai_key:
            console.print("[red]✗ OPENAI_API_KEY not set[/red]")
            console.print("\nSet your API key:")
            console.print("  export OPENAI_API_KEY='sk-...'")
            raise click.Abort()

        try:
            # Test OpenAI API
            from openai import OpenAI

            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

            with console.status("[bold green]Testing OpenAI API..."):
                response = client.embeddings.create(input=["test"], model=model)

            console.print("[green]✓ OpenAI API configured successfully![/green]")
            console.print()
            console.print(f"  Model: {model}")
            console.print(f"  Dimension: {len(response.data[0].embedding)}")
            console.print()
            console.print("[green]MCP memory tools ready (using OpenAI API)![/green]")
            console.print()

        except Exception as e:
            console.print(f"\n[red]✗ OpenAI API test failed: {e}[/red]")
            raise click.Abort()

    else:  # local provider
        console.print(f"Downloading local model: [bold]{model}[/bold]")
        console.print("[dim](~500MB, may take 30-60 seconds)[/dim]")
        console.print()

        try:
            from kagura.core.memory.embeddings import Embedder

            config = EmbeddingConfig(model=model)

            with console.status("[bold green]Downloading model..."):
                embedder = Embedder(config)

            # Test the model
            test_embedding = embedder.encode_queries(["test"])

            console.print("[green]✓ Model downloaded successfully![/green]")
            console.print()
            console.print(f"  Model: {model}")
            console.print(f"  Dimension: {len(test_embedding[0])}")
            console.print()
            console.print("[green]MCP memory tools are now ready to use![/green]")
            console.print()

        except ImportError as e:
            console.print(f"\n[red]✗ Missing dependency: {e}[/red]")
            console.print("\nInstall with: pip install 'kagura-ai[memory]'")
            raise click.Abort()
        except Exception as e:
            console.print(f"\n[red]✗ Setup failed: {e}[/red]")
            raise click.Abort()

    # Download reranking model (v4.2.3+)
    try:
        from sentence_transformers import CrossEncoder

        from kagura.core.memory.reranker import is_reranker_available

        # Check if already downloaded
        if is_reranker_available(DEFAULT_RERANKER_MODEL):
            console.print(
                f"[green]✓ Reranking model already cached: {DEFAULT_RERANKER_MODEL}[/green]"
            )
        else:
            console.print("[cyan]Downloading reranking model...[/cyan]")
            console.print("[dim](BGE-reranker-v2-m3, ~600MB, may take 30-60 seconds)[/dim]")
            console.print()

            with console.status("[bold green]Downloading reranker..."):
                # Download by instantiating (model will be cached)
                _ = CrossEncoder(DEFAULT_RERANKER_MODEL)

            console.print("[green]✓ Reranking model downloaded successfully![/green]")

        console.print()
        console.print("[bold green]🎉 Memory setup complete![/bold green]")
        console.print()

    except ImportError as e:
        console.print(f"\n[yellow]⚠ Reranker download skipped: {e}[/yellow]")
        console.print("[dim](Install with: pip install 'kagura-ai[memory]')[/dim]")
    except Exception as e:
        console.print(f"\n[yellow]⚠ Reranker download failed: {e}[/yellow]")
        console.print("[dim](Non-critical: Memory tools will use fallback reranker)[/dim]")


@click.command(name="install-reranking")
@click.option("--force", is_flag=True, help="Force re-download even if already cached")
def install_reranking(force: bool) -> None:
    """Download reranking model (BGE-reranker-v2-m3).

    Downloads the BGE-reranker-v2-m3 model (~600MB) for improved search ranking.
    This is automatically called by 'kagura memory setup', but can be run separately.

    Examples:

        # Download reranking model
        kagura memory install-reranking

        # Force re-download
        kagura memory install-reranking --force
    """
    from kagura.core.memory.reranker import is_reranker_available

    console.print("\n[cyan]Downloading reranking model...[/cyan]")
    console.print("[dim](BGE-reranker-v2-m3, ~600MB, may take 30-60 seconds)[/dim]")
    console.print()

    try:
        from sentence_transformers import CrossEncoder

        # Check if already downloaded (unless force)
        if not force and is_reranker_available(DEFAULT_RERANKER_MODEL):
            console.print(
                f"[green]✓ Reranking model already cached: {DEFAULT_RERANKER_MODEL}[/green]"
            )
            console.print("[dim](Use --force to re-download)[/dim]")
            return

        with console.status("[bold green]Downloading..."):
            # Download by instantiating (model will be cached)
            _ = CrossEncoder(DEFAULT_RERANKER_MODEL)

        console.print("[green]✓ Reranking model downloaded successfully![/green]")
        console.print()

    except ImportError as e:
        console.print(f"\n[red]✗ Missing dependency: {e}[/red]")
        console.print("\nInstall with: pip install 'kagura-ai[memory]'")
        raise click.Abort()
    except Exception as e:
        console.print(f"\n[red]✗ Download failed: {e}[/red]")
        raise click.Abort()
