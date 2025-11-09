# ruff: noqa: I001, E402
"""CLI-specific utility functions.

.. deprecated:: 4.3.0
    This module has been moved to ``kagura.utils.cli``.
    Import from ``kagura.utils.cli`` instead.
    This compatibility shim will be removed in v4.5.0.

This package contains utilities specific to CLI commands,
particularly Rich console formatting and progress indicators.
"""

import warnings

# Deprecation warning
warnings.warn(
    "kagura.cli.utils is deprecated and will be removed in v4.5.0. "
    "Use kagura.utils.cli instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export from new location for backward compatibility
from kagura.utils.cli.progress import create_progress_bar, create_spinner_progress
from kagura.utils.cli.rich_helpers import (
    create_console,
    create_error_panel,
    create_info_panel,
    create_success_panel,
    create_table,
    create_warning_panel,
)
from kagura.utils.cli.time_formatters import (  # noqa: E402
    format_duration,
    format_relative_time,
    format_timestamp,
)

__all__ = [
    # Rich helpers
    "create_console",
    "create_table",
    "create_success_panel",
    "create_error_panel",
    "create_warning_panel",
    "create_info_panel",
    # Progress helpers
    "create_spinner_progress",
    "create_progress_bar",
    # Time formatters
    "format_relative_time",
    "format_duration",
    "format_timestamp",
]
