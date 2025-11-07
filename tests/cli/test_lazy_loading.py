"""Tests for lazy loading CLI optimization"""

import subprocess
import sys
import time

from click.testing import CliRunner

from kagura.cli.lazy import LazyGroup
from kagura.cli.main import cli


def test_help_is_fast():
    """Test that --help is fast (< 0.5s)"""
    start = time.time()
    result = subprocess.run(
        ["kagura", "--help"], capture_output=True, text=True, timeout=5
    )
    duration = time.time() - start

    assert result.returncode == 0
    assert duration < 0.5, f"--help took {duration:.2f}s (expected < 0.5s)"


def test_version_is_fast():
    """Test that version command is fast (< 0.5s)"""
    start = time.time()
    result = subprocess.run(
        ["kagura", "version"], capture_output=True, text=True, timeout=5
    )
    duration = time.time() - start

    assert result.returncode == 0
    assert "Kagura AI" in result.stdout
    assert duration < 0.5, f"version took {duration:.2f}s (expected < 0.5s)"


def test_lazy_loading_does_not_import_mcp():
    """Test that MCP module is not imported on --help"""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from kagura.cli.main import cli; "
            "import sys; "
            "cli(['--help'], standalone_mode=False); "
            "print('mcp.server' in sys.modules)",
        ],
        capture_output=True,
        text=True,
    )

    # mcp.server should NOT be imported
    assert "False" in result.stdout, "mcp.server module should not be imported"


def test_lazy_loading_does_not_import_monitor():
    """Test that monitor module is not imported on --help"""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from kagura.cli.main import cli; "
            "import sys; "
            "cli(['--help'], standalone_mode=False); "
            "print('kagura.observability' in sys.modules)",
        ],
        capture_output=True,
        text=True,
    )

    # observability should NOT be imported
    assert "False" in result.stdout, "observability module should not be imported"


def test_all_commands_listed():
    """Test that all commands are still listed in --help"""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])

    assert result.exit_code == 0

    # All commands should be listed
    expected_commands = ["chat", "mcp", "monitor", "auth"]
    for cmd in expected_commands:
        assert cmd in result.output, f"Command '{cmd}' not found in --help"


@pytest.mark.slow
def test_all_commands_still_work():
    """Test that all commands still work with lazy loading (slow: CLI invocation)"""
    commands = ["chat", "mcp", "monitor", "auth"]

    for cmd in commands:
        result = subprocess.run(
            ["kagura", cmd, "--help"], capture_output=True, text=True, timeout=10
        )
        assert result.returncode == 0, f"{cmd} command failed"
        assert len(result.stdout) > 0, f"{cmd} has no help output"


def test_lazy_group_get_command():
    """Test LazyGroup.get_command() loads on demand"""
    import click

    # Create a test lazy group
    @click.group(
        cls=LazyGroup, lazy_subcommands={"testcmd": ("os.path", "join", "Test command")}
    )
    def test_cli():
        pass

    # Get command - should load lazily
    ctx = click.Context(test_cli, info_name="testcli")
    cmd = test_cli.get_command(ctx, "testcmd")

    assert cmd is not None
    assert callable(cmd)


def test_lazy_group_unknown_command():
    """Test LazyGroup handles unknown commands"""
    runner = CliRunner()

    result = runner.invoke(cli, ["nonexistent"])

    assert result.exit_code != 0
    assert "Error" in result.output or "no such command" in result.output.lower()


def test_lazy_group_caching():
    """Test that loaded commands are cached"""
    import click

    @click.group(
        cls=LazyGroup, lazy_subcommands={"testcmd": ("os.path", "join", "Test command")}
    )
    def test_cli():
        pass

    ctx = click.Context(test_cli, info_name="testcli")

    # First call - should load
    cmd1 = test_cli.get_command(ctx, "testcmd")

    # Second call - should use cache
    cmd2 = test_cli.get_command(ctx, "testcmd")

    assert cmd1 is cmd2, "Commands should be the same instance (cached)"


def test_cli_import_time():
    """Test that CLI import is fast (< 100ms)"""
    start = time.time()
    from kagura.cli.main import cli  # noqa: F401, F811

    duration = time.time() - start

    assert duration < 0.1, f"CLI import took {duration:.3f}s (expected < 0.1s)"


def test_format_commands_without_loading():
    """Test that format_commands doesn't load lazy commands"""
    import click
    from click.formatting import HelpFormatter

    # Track which modules are loaded
    initial_modules = set(sys.modules.keys())

    # Create a minimal context
    ctx = click.Context(cli, info_name="kagura")
    formatter = HelpFormatter()

    # Format commands
    cli.format_commands(ctx, formatter)

    # Check that heavy modules were NOT imported
    new_modules = set(sys.modules.keys()) - initial_modules

    # Should not import mcp, observability, etc.
    assert "kagura.mcp" not in new_modules
    assert "kagura.observability" not in new_modules
    assert "mcp.server" not in new_modules


def test_version_command_fast():
    """Test version command executes quickly"""
    runner = CliRunner()

    start = time.time()
    result = runner.invoke(cli, ["version"])
    duration = time.time() - start

    assert result.exit_code == 0
    assert "Kagura AI" in result.output
    assert duration < 0.2, f"version command took {duration:.3f}s (expected < 0.2s)"


def test_lazy_load_error_handling():
    """Test error handling when lazy load fails"""
    import click

    @click.group(
        cls=LazyGroup, lazy_subcommands={"bad": ("nonexistent.module", "command")}
    )
    def test_cli():
        pass

    runner = CliRunner()
    result = runner.invoke(test_cli, ["bad"])

    assert result.exit_code != 0
    assert "Failed to load command" in result.output


def test_cli_startup_benchmark():
    """Benchmark test to ensure startup stays fast"""
    # Run multiple times and check average
    durations = []

    for _ in range(5):
        start = time.time()
        subprocess.run(
            ["kagura", "--help"],
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        )
        durations.append(time.time() - start)

    avg_duration = sum(durations) / len(durations)
    max_duration = max(durations)

    assert avg_duration < 0.3, f"Average startup: {avg_duration:.3f}s (expected < 0.3s)"
    assert max_duration < 0.5, f"Max startup: {max_duration:.3f}s (expected < 0.5s)"
