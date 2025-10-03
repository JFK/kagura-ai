"""Test version - minimal test for SETUP-001"""
from kagura import __version__


def test_version_exists():
    """Test that version is defined"""
    assert __version__ == "2.0.0-alpha.1"
