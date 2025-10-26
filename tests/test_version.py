"""Test version - minimal test for SETUP-001"""

import tomllib
from pathlib import Path

from kagura import __version__


def test_version_exists():
    """Test that version is defined and follows PEP 440"""
    assert __version__ is not None
    assert isinstance(__version__, str)

    # PEP 440 format: X.Y.Z[{a|b|rc}N]
    # Examples: 4.0.0, 4.0.0a0, 4.0.0b1, 4.0.0rc2
    import re

    pep440_pattern = r"^\d+\.\d+\.\d+([ab]\d+|rc\d+)?$"
    assert re.match(pep440_pattern, __version__), (
        f"Version '{__version__}' does not follow PEP 440 format. "
        f"Expected: X.Y.Z or X.Y.Z{{a|b|rc}}N (e.g., 4.0.0a0)"
    )


def test_version_consistency():
    """Test that pyproject.toml and version.py have the same version"""
    # Read version from pyproject.toml
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        pyproject_data = tomllib.load(f)
    pyproject_version = pyproject_data["project"]["version"]

    # Read version from version.py (already imported as __version__)
    version_py_version = __version__

    # Assert they are equal
    assert pyproject_version == version_py_version, (
        f"Version mismatch: pyproject.toml has '{pyproject_version}' "
        f"but version.py has '{version_py_version}'"
    )
