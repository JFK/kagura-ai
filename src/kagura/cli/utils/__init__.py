"""CLI-specific utility functions.

This package contains utilities specific to CLI commands,
particularly Rich console formatting and progress indicators.
"""

from kagura.cli.utils.progress import create_progress_bar, create_spinner_progress
from kagura.cli.utils.rich_helpers import (
    create_console,
    create_error_panel,
    create_info_panel,
    create_success_panel,
    create_table,
    create_warning_panel,
)
from kagura.cli.utils.time_formatters import (
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
