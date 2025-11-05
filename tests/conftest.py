"""Pytest configuration"""

import os
import tempfile
from pathlib import Path
from typing import Iterator

import pytest


@pytest.fixture(scope="session", autouse=True)
def isolate_test_database():
    """Isolate test database from production.

    CRITICAL: Prevents tests from polluting production database.
    Sets KAGURA_DATA_DIR to temp directory so tests use separate DB.

    Related: Session data loss issue - tests were writing to production DB
    """
    # Create temp directory for test data
    test_data_dir = Path(tempfile.mkdtemp(prefix="kagura_test_data_"))

    # Override data directory for all tests
    os.environ["KAGURA_DATA_DIR"] = str(test_data_dir)

    yield test_data_dir

    # Cleanup after all tests
    try:
        import shutil

        shutil.rmtree(test_data_dir, ignore_errors=True)
    except Exception:
        pass

    # Restore original env (if any)
    os.environ.pop("KAGURA_DATA_DIR", None)


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
