"""Tests for CLI Rich helpers."""

from __future__ import annotations

import pytest
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from kagura.cli.utils.rich_helpers import (
    create_console,
    create_error_panel,
    create_info_panel,
    create_success_panel,
    create_table,
    create_warning_panel,
)


class TestCreateConsole:
    """Tests for create_console()."""

    def test_creates_console_instance(self) -> None:
        """Test that create_console returns a Console instance."""
        console = create_console()
        assert isinstance(console, Console)

    def test_console_is_usable(self) -> None:
        """Test that returned console can be used for printing."""
        console = create_console()
        # Should not raise
        with console.capture() as capture:
            console.print("test")
        assert "test" in capture.get()


class TestCreateTable:
    """Tests for create_table()."""

    def test_creates_table_instance(self) -> None:
        """Test that create_table returns a Table instance."""
        table = create_table()
        assert isinstance(table, Table)

    def test_table_with_title(self) -> None:
        """Test table creation with title."""
        table = create_table(title="Test Table")
        assert table.title == "Test Table"

    def test_table_with_no_header(self) -> None:
        """Test table creation without header."""
        table = create_table(show_header=False)
        assert table.show_header is False

    def test_table_with_lines(self) -> None:
        """Test table creation with row lines."""
        table = create_table(show_lines=True)
        assert table.show_lines is True

    def test_table_can_add_columns_and_rows(self) -> None:
        """Test that table can be used normally."""
        table = create_table()
        table.add_column("Name")
        table.add_column("Status")
        table.add_row("Project A", "Active")
        # Should not raise


class TestCreatePanels:
    """Tests for panel creation functions."""

    def test_success_panel_is_green(self) -> None:
        """Test that success panel has green style."""
        panel = create_success_panel("Success message")
        assert isinstance(panel, Panel)
        assert panel.style == "green"
        assert "Success" in str(panel.title)

    def test_error_panel_is_red(self) -> None:
        """Test that error panel has red style."""
        panel = create_error_panel("Error message")
        assert isinstance(panel, Panel)
        assert panel.style == "red"
        assert "Error" in str(panel.title)

    def test_warning_panel_is_yellow(self) -> None:
        """Test that warning panel has yellow style."""
        panel = create_warning_panel("Warning message")
        assert isinstance(panel, Panel)
        assert panel.style == "yellow"
        assert "Warning" in str(panel.title)

    def test_info_panel_is_blue(self) -> None:
        """Test that info panel has blue style."""
        panel = create_info_panel("Info message")
        assert isinstance(panel, Panel)
        assert panel.style == "blue"
        assert "Info" in str(panel.title)

    def test_panel_with_custom_title(self) -> None:
        """Test panel creation with custom title."""
        panel = create_success_panel("Message", title="Custom Title")
        assert "Custom Title" in str(panel.title)

    def test_panel_with_expand(self) -> None:
        """Test panel creation with expand=True."""
        panel = create_success_panel("Message", expand=True)
        assert panel.expand is True

    def test_panel_supports_rich_markup(self) -> None:
        """Test that panel message supports Rich markup."""
        panel = create_success_panel("[bold]Bold text[/]")
        # Should not raise
        assert isinstance(panel, Panel)
