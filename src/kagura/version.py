"""Version information for Kagura AI

Version is automatically read from pyproject.toml metadata.
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("kagura_ai")
except PackageNotFoundError:
    # Package not installed (e.g., during development)
    __version__ = "0.0.0.dev"
