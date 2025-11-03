"""Unified health check command for Kagura AI.

Provides comprehensive system diagnostics including:
- System requirements (Python version, disk space)
- API configuration and connectivity
- Memory system (database, RAG, reranking)
- MCP integration
- Coding memory stats
"""

from __future__ import annotations

import asyncio
import shutil
import sys
from pathlib import Path
from typing import Any

import click
from rich.console import Console
from rich.panel import Panel

from kagura.config.env import (
    get_anthropic_api_key,
    get_openai_api_key,
)
from kagura.config.paths import get_data_dir

console = Console()


def _check_python_version() -> tuple[str, str]:
    """Check Python version.

    Returns:
        Tuple of (status, message)
    """
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"

    if version.major < 3 or (version.major == 3 and version.minor < 11):
        return "error", f"Python {version_str} (requires 3.11+)"
    return "ok", f"Python {version_str}"


def _check_disk_space() -> tuple[str, str]:
    """Check available disk space.

    Returns:
        Tuple of (status, message)
    """
    try:
        data_dir = get_data_dir()
        usage = shutil.disk_usage(data_dir)
        free_gb = usage.free / (1024**3)

        if free_gb < 1:
            return "warning", f"{free_gb:.1f} GB available (low)"
        return "ok", f"{free_gb:.1f} GB available"
    except Exception as e:
        return "error", f"Could not check: {e}"


def _check_dependencies() -> list[tuple[str, str, str]]:
    """Check optional dependencies.

    Returns:
        List of (package_name, status, message) tuples
    """
    results = []

    # ChromaDB (required for RAG)
    try:
        import chromadb  # type: ignore

        version = chromadb.__version__
        results.append(("chromadb", "ok", f"v{version}"))
    except ImportError:
        results.append(("chromadb", "warning", "Not installed (RAG disabled)"))

    # Sentence Transformers (required for RAG embeddings)
    try:
        import sentence_transformers  # type: ignore

        version = sentence_transformers.__version__
        results.append(("sentence-transformers", "ok", f"v{version}"))
    except ImportError:
        results.append(
            ("sentence-transformers", "warning", "Not installed (RAG disabled)")
        )

    return results


async def _check_api_configuration() -> list[tuple[str, str, str]]:
    """Check API key configuration and connectivity.

    Returns:
        List of (provider_name, status, message) tuples
    """
    from kagura.config.env import (
        get_anthropic_default_model,
        get_openai_default_model,
    )

    results = []

    # Anthropic
    anthropic_key = get_anthropic_api_key()
    if not anthropic_key:
        results.append(("Anthropic", "warning", "Not configured"))
    else:
        # Test connectivity
        try:
            from litellm import acompletion

            model = get_anthropic_default_model()
            await acompletion(
                model=model,
                messages=[{"role": "user", "content": "test"}],
                api_key=anthropic_key,
                max_tokens=1,
                timeout=10,
            )
            results.append(("Anthropic", "ok", "Configured and reachable"))
        except ImportError:
            results.append(
                ("Anthropic", "warning", "Configured (litellm not installed)")
            )
        except Exception as e:
            error_msg = str(e)
            if "authentication" in error_msg.lower() or "invalid" in error_msg.lower():
                results.append(("Anthropic", "error", "Invalid API key"))
            else:
                results.append(("Anthropic", "error", f"Unreachable: {error_msg[:50]}"))

    # OpenAI
    openai_key = get_openai_api_key()
    if not openai_key:
        results.append(("OpenAI", "info", "Not configured (optional)"))
    else:
        # Test connectivity
        try:
            from litellm import acompletion

            model = get_openai_default_model()
            await acompletion(
                model=model,
                messages=[{"role": "user", "content": "test"}],
                api_key=openai_key,
                max_tokens=1,
                timeout=10,
            )
            results.append(("OpenAI", "ok", "Configured and reachable"))
        except ImportError:
            results.append(("OpenAI", "warning", "Configured (litellm not installed)"))
        except Exception as e:
            error_msg = str(e)
            if "authentication" in error_msg.lower() or "invalid" in error_msg.lower():
                results.append(("OpenAI", "error", "Invalid API key"))
            else:
                results.append(("OpenAI", "error", f"Unreachable: {error_msg[:50]}"))

    return results


def _check_memory_system() -> tuple[dict[str, Any], list[str]]:
    """Check memory system status.

    Returns:
        Tuple of (status_dict, recommendations)
    """
    from kagura.core.memory import MemoryManager

    status = {}
    recommendations = []

    # Check database
    db_path = get_data_dir() / "memory.db"
    if db_path.exists():
        status["database_exists"] = True
        status["database_size_mb"] = db_path.stat().st_size / (1024**2)
    else:
        status["database_exists"] = False
        recommendations.append(
            "Database not initialized (will be created on first use)"
        )

    # Check memory counts
    persistent_count = 0
    try:
        manager = MemoryManager(user_id="system", agent_name="doctor")

        # Count persistent memories
        persistent_count = manager.persistent.count()
        status["persistent_count"] = persistent_count

        # Check RAG
        if manager.persistent_rag is not None:
            try:
                rag_count = manager.persistent_rag.collection.count()
                status["rag_count"] = rag_count
                status["rag_enabled"] = True

                if rag_count == 0 and persistent_count > 0:
                    recommendations.append(
                        "RAG index is empty but memories exist. "
                        "Run 'kagura memory index' to build index"
                    )
            except Exception:  # ChromaDB collection.count() can fail if not initialized
                status["rag_enabled"] = False
                status["rag_count"] = 0
                recommendations.append(
                    "RAG not available. Install: "
                    "pip install chromadb sentence-transformers"
                )
        else:
            status["rag_enabled"] = False
            status["rag_count"] = 0
            recommendations.append(
                "RAG not available. Install: pip install chromadb sentence-transformers"
            )

    except Exception as e:
        status["error"] = str(e)
        status["persistent_count"] = 0
        status["rag_enabled"] = False
        status["rag_count"] = 0
        recommendations.append(f"Memory system error: {e}")
        # Early return to avoid accessing undefined manager
        return status, recommendations

    # Check reranking
    import os

    reranking_enabled = os.getenv("KAGURA_ENABLE_RERANKING", "").lower() == "true"
    status["reranking_enabled"] = reranking_enabled

    if not reranking_enabled:
        # Check if model is installed by trying to import
        try:
            import sentence_transformers  # type: ignore # noqa: F401

            # Try to load the model (this will fail if not downloaded)
            try:
                # Check if model exists in cache
                cache_dir = get_data_dir() / "models"
                model_path = cache_dir / "cross-encoder_ms-marco-MiniLM-L-6-v2"

                if model_path.exists():
                    status["reranking_model_installed"] = True
                    recommendations.append(
                        "Reranking model installed but not enabled. "
                        "Set: export KAGURA_ENABLE_RERANKING=true"
                    )
                else:
                    status["reranking_model_installed"] = False
                    recommendations.append(
                        "Reranking not available. Install: "
                        "kagura memory setup --reranking"
                    )
            except Exception:  # Ignore errors - operation is non-critical
                status["reranking_model_installed"] = False
                recommendations.append(
                    "Reranking not available. Install: kagura memory setup --reranking"
                )
        except ImportError:
            status["reranking_model_installed"] = False
            recommendations.append(
                "sentence-transformers not installed (required for reranking)"
            )
    else:
        status["reranking_model_installed"] = True

    return status, recommendations


def _check_mcp_integration() -> tuple[str, str]:
    """Check MCP integration status.

    Returns:
        Tuple of (status, message)
    """
    # Check Claude Desktop config
    config_paths = [
        Path.home() / ".config" / "claude-code" / "mcp.json",
        Path.home()
        / "Library"
        / "Application Support"
        / "Claude"
        / "claude_desktop_config.json",
    ]

    for path in config_paths:
        if path.exists():
            try:
                import json

                with open(path) as f:
                    config = json.load(f)

                if "mcpServers" in config and "kagura" in config["mcpServers"]:
                    return "ok", f"Configured in {path.name}"
            except Exception:  # Ignore errors - operation is non-critical
                pass

    return "warning", "Not configured (MCP server starts with Claude Desktop)"


def _check_coding_memory() -> dict[str, Any]:
    """Check coding memory status.

    Returns:
        Status dictionary
    """
    from kagura.core.memory import MemoryManager

    try:
        manager = MemoryManager(user_id="system", agent_name="coding-memory")

        # Count sessions - search in persistent storage
        sessions = manager.persistent.search(
            query="%session%",
            user_id="system",
            agent_name="coding-memory",
            limit=1000,
        )

        # Try to identify unique projects
        projects: set[str] = set()
        for session in sessions:
            if "metadata" in session:
                try:
                    import json

                    metadata = json.loads(session.get("metadata", "{}"))
                    if "project_id" in metadata:
                        projects.add(metadata["project_id"])
                except Exception:  # JSON parsing can fail for invalid metadata
                    pass

        return {
            "sessions_count": len(sessions),
            "projects_count": len(projects),
        }
    except Exception:  # Ignore errors - operation is non-critical
        return {
            "sessions_count": 0,
            "projects_count": 0,
        }


def _get_status_icon(status: str) -> str:
    """Get status icon for display."""
    if status == "ok":
        return "[green]✓[/green]"
    elif status == "warning":
        return "[yellow]⚠[/yellow]"
    elif status == "error":
        return "[red]✗[/red]"
    else:
        return "[blue]ℹ[/blue]"


@click.command()
@click.option("--fix", is_flag=True, help="Interactively fix detected issues")
@click.pass_context
def doctor(ctx: click.Context, fix: bool) -> None:
    """Run comprehensive system health check.

    This unified command checks:

    \b
    - System requirements (Python version, disk space)
    - API configuration and connectivity
    - Memory system (database, RAG, reranking)
    - MCP integration
    - Coding memory stats

    Examples:

        kagura doctor           # Run health check

        kagura doctor --fix     # Interactive setup
    """
    console.print("\n")
    console.print(
        Panel(
            "[bold]Kagura System Health Check 🏥[/]\n"
            "Running comprehensive diagnostics...",
            style="blue",
        )
    )
    console.print()

    recommendations: list[str] = []
    overall_status = "ok"

    # 1. System Requirements
    console.print("[bold cyan]1. System Requirements[/]")

    py_status, py_msg = _check_python_version()
    console.print(f"   {_get_status_icon(py_status)} {py_msg}")
    if py_status == "error":
        overall_status = "error"

    disk_status, disk_msg = _check_disk_space()
    console.print(f"   {_get_status_icon(disk_status)} {disk_msg}")
    if disk_status == "warning" and overall_status == "ok":
        overall_status = "warning"

    deps = _check_dependencies()
    for pkg_name, pkg_status, pkg_msg in deps:
        console.print(f"   {_get_status_icon(pkg_status)} {pkg_name}: {pkg_msg}")
        if pkg_status == "warning":
            if "chromadb" in pkg_name.lower():
                recommendations.append(
                    "Install RAG dependencies: pip install chromadb sentence-transformers"
                )
            if overall_status == "ok":
                overall_status = "warning"

    console.print()

    # 2. API Configuration
    console.print("[bold cyan]2. API Configuration[/]")
    with console.status("[cyan]Testing API connections..."):
        api_results = asyncio.run(_check_api_configuration())

    for provider, status, msg in api_results:
        console.print(f"   {_get_status_icon(status)} {provider}: {msg}")
        if status == "error":
            overall_status = "error"
            recommendations.append(f"Check {provider} API key configuration")
        elif status == "warning" and overall_status == "ok":
            overall_status = "warning"

    console.print()

    # 3. Memory System
    console.print("[bold cyan]3. Memory System[/]")
    mem_status, mem_recommendations = _check_memory_system()

    if mem_status.get("database_exists"):
        console.print(
            f"   {_get_status_icon('ok')} Database: "
            f"{mem_status.get('persistent_count', 0)} memories "
            f"({mem_status.get('database_size_mb', 0):.1f} MB)"
        )
    else:
        console.print(f"   {_get_status_icon('info')} Database: Not yet initialized")

    if mem_status.get("rag_enabled"):
        rag_count = mem_status.get("rag_count", 0)
        rag_icon = "ok" if rag_count > 0 else "warning"
        console.print(
            f"   {_get_status_icon(rag_icon)} RAG: {rag_count} vectors indexed"
        )
    else:
        console.print(f"   {_get_status_icon('warning')} RAG: Not available")

    if mem_status.get("reranking_enabled"):
        console.print(f"   {_get_status_icon('ok')} Reranking: Enabled")
    elif mem_status.get("reranking_model_installed"):
        console.print(
            f"   {_get_status_icon('warning')} Reranking: "
            "Model installed but not enabled"
        )
    else:
        console.print(
            f"   {_get_status_icon('info')} Reranking: Not installed (optional)"
        )

    recommendations.extend(mem_recommendations)

    if not mem_status.get("rag_enabled") and overall_status == "ok":
        overall_status = "warning"

    console.print()

    # 4. MCP Integration
    console.print("[bold cyan]4. MCP Integration[/]")
    mcp_status, mcp_msg = _check_mcp_integration()
    console.print(f"   {_get_status_icon(mcp_status)} Claude Desktop: {mcp_msg}")
    console.print()

    # 5. Coding Memory
    console.print("[bold cyan]5. Coding Memory[/]")
    coding_status = _check_coding_memory()
    console.print(
        f"   {_get_status_icon('ok')} Projects: {coding_status['projects_count']} tracked"
    )
    console.print(
        f"   {_get_status_icon('ok')} Sessions: {coding_status['sessions_count']} recorded"
    )
    console.print()

    # Overall Status
    if overall_status == "ok" and not recommendations:
        overall_icon = "[green]✓[/green]"
        overall_msg = "[green]All systems healthy[/green]"
    elif overall_status == "warning" or recommendations:
        overall_icon = "[yellow]⚠[/yellow]"
        overall_msg = "[yellow]Ready (with suggestions)[/yellow]"
    else:
        overall_icon = "[red]✗[/red]"
        overall_msg = "[red]Issues detected[/red]"

    console.print(f"[bold]Overall Status:[/bold] {overall_icon} {overall_msg}\n")

    # Recommendations
    if recommendations:
        console.print("[bold yellow]Recommendations:[/bold yellow]")
        for i, rec in enumerate(recommendations, 1):
            console.print(f"  {i}. {rec}")
        console.print()

        if fix:
            console.print(
                "[blue]💡 Run 'kagura doctor --fix' for interactive setup (coming soon)[/]"
            )
        else:
            console.print(
                "[blue]💡 Run 'kagura doctor --fix' to interactively fix issues[/]"
            )
        console.print()

    # Environment variable suggestions
    import os

    env_suggestions = []

    if not os.getenv("KAGURA_DEFAULT_PROJECT"):
        env_suggestions.append(
            ("KAGURA_DEFAULT_PROJECT", "export KAGURA_DEFAULT_PROJECT=your-project")
        )

    if mem_status.get("reranking_model_installed") and not mem_status.get(
        "reranking_enabled"
    ):
        env_suggestions.append(
            ("KAGURA_ENABLE_RERANKING", "export KAGURA_ENABLE_RERANKING=true")
        )

    if env_suggestions:
        console.print("[bold]Environment Variables (Optional):[/bold]")
        for var_name, command in env_suggestions:
            console.print(f"  • {var_name}")
            console.print(f"    [dim]{command}[/dim]")
        console.print()

    console.print(
        Panel(
            "[bold]Diagnostics Complete[/]\n\n"
            "For more help:\n"
            "  • kagura config doctor - API configuration only\n"
            "  • kagura mcp doctor - MCP integration only\n"
            "  • kagura memory --help - Memory management",
            style="blue",
        )
    )
    console.print()


if __name__ == "__main__":
    doctor()
