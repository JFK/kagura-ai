"""Test version - minimal test for SETUP-001"""
import tomllib
from pathlib import Path
from kagura import __version__


def test_version_exists():
    """Test that version is defined and follows semver"""
    assert __version__ is not None
    assert isinstance(__version__, str)
    # Check that it follows semver format (e.g., 2.0.0-beta.1 or 2.0.0)
    parts = __version__.split('-')
    version_nums = parts[0].split('.')
    assert len(version_nums) == 3
    assert all(part.isdigit() for part in version_nums)


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
