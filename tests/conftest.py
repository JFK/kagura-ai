"""Pytest configuration"""

import tempfile
from pathlib import Path
from typing import Iterator

import pytest


@pytest.fixture
def sample_agent():
    """Sample agent for testing"""
    from kagura import agent

    @agent
    async def hello(name: str) -> str:
        """Say hello to {{ name }}"""
        return f"Hello, {name}!"

    return hello


@pytest.fixture(scope="session")
def worker_id(request: pytest.FixtureRequest) -> str:
    """Get pytest-xdist worker ID.

    Returns:
        Worker ID string (e.g., "gw0", "gw1", or "master" for sequential)
    """
    if hasattr(request.config, "workerinput"):
        return request.config.workerinput["workerid"]
    return "master"


@pytest.fixture(scope="session")
def worker_tmp_dir(worker_id: str) -> Iterator[Path]:
    """Create worker-specific temporary directory.

    Args:
        worker_id: Worker ID from pytest-xdist

    Yields:
        Path to worker-specific temp directory
    """
    base_tmp = Path(tempfile.gettempdir()) / "kagura_test"
    worker_tmp = base_tmp / worker_id
    worker_tmp.mkdir(parents=True, exist_ok=True)

    yield worker_tmp

    # Cleanup after session
    try:
        import shutil

        shutil.rmtree(worker_tmp, ignore_errors=True)
    except Exception:
        pass
