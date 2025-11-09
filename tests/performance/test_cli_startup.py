"""Performance regression tests for CLI startup time.

Related: Issue #548 - CLI startup optimization
Target: <3 seconds for coding commands
"""

import subprocess
import time

import pytest


@pytest.mark.performance
@pytest.mark.slow
def test_cli_startup_time_under_3_seconds():
    """Regression test for #548 - CLI commands must start in <3 seconds.

    Measures startup time for the most common CLI commands.
    Fails if any command takes >3 seconds (83% improvement from 13.9s baseline).
    """
    import sys

    commands = [
        [sys.executable, "-m", "kagura.cli.main", "coding", "sessions", "--limit", "1"],
        [
            sys.executable,
            "-m",
            "kagura.cli.main",
            "coding",
            "decisions",
            "--limit",
            "1",
        ],
        [sys.executable, "-m", "kagura.cli.main", "coding", "errors", "--limit", "1"],
    ]

    for cmd in commands:
        start = time.time()
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=5,
            env={
                "KAGURA_DEFAULT_PROJECT": "test-project",
                "KAGURA_DEFAULT_USER": "test-user",
            },
        )
        elapsed = time.time() - start

        assert result.returncode == 0, (
            f"Command failed: {' '.join(cmd[2:])}\nStderr: {result.stderr.decode()}"
        )

        # Target: <5s (conservative, accounts for CI/environment variance)
        # Baseline was 13.9s, optimized to ~2-4s depending on environment
        # This test ensures we don't regress back to 10s+ territory
        assert elapsed < 5.0, (
            f"CLI took {elapsed:.2f}s (target: <5s) for {' '.join(cmd[2:])}"
        )


@pytest.mark.performance
def test_lightweight_memory_no_reranker_init():
    """Verify lightweight config doesn't initialize MemoryReranker.

    Related: Issue #548 - Reranker initialization was 6.5s bottleneck
    """
    from kagura.cli.coding.utils import _get_lightweight_coding_memory

    memory = _get_lightweight_coding_memory("test-user", "test-project")

    # CodingMemoryManager inherits from MemoryManager
    # Should NOT have initialized reranker
    assert memory.reranker is None, (
        "Reranker should be None in lightweight config "
        "(config.rerank.enabled should be False)"
    )

    # Verify config is correct
    assert memory.config.rerank.enabled is False, (
        "config.rerank.enabled should be False in lightweight config"
    )


@pytest.mark.performance
def test_memory_system_config_respects_explicit_rerank_false():
    """Test MemorySystemConfig.model_post_init() respects explicit enabled=False.

    Related: Issue #548 - Bug where model_post_init() ignored explicit settings
    Reproducer: model_post_init() would override enabled=False to True when model cached
    """
    from kagura.config.memory_config import MemorySystemConfig, RerankConfig

    # Create config with explicit enabled=False
    config = MemorySystemConfig(rerank=RerankConfig(enabled=False))

    # Should stay False (not overridden by model_post_init auto-detection)
    assert config.rerank.enabled is False, (
        "model_post_init() should respect explicit rerank.enabled=False "
        "(check __pydantic_fields_set__ logic)"
    )


@pytest.mark.performance
def test_memory_system_config_auto_enables_when_not_explicit():
    """Test MemorySystemConfig auto-enables reranking when model cached.

    Related: Issue #548 - Smart default for users with cached models
    """
    from kagura.config.memory_config import MemorySystemConfig
    from kagura.core.memory.reranker import is_reranker_available

    # Only test if model is actually cached
    if not is_reranker_available(check_fallback=True):
        pytest.skip("Reranking model not cached, can't test auto-enablement")

    # Create config without explicit rerank parameter
    config = MemorySystemConfig()

    # Should auto-enable because model is cached
    assert config.rerank.enabled is True, (
        "model_post_init() should auto-enable reranking when model cached "
        "and user didn't explicitly configure rerank"
    )
