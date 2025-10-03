"""Test version - minimal test for SETUP-001"""
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
