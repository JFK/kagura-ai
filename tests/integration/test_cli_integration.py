"""Integration tests for CLI"""
import pytest
from click.testing import CliRunner

from kagura.cli.main import cli


def test_cli_version():
    """Test CLI version command"""
    runner = CliRunner()
    result = runner.invoke(cli, ['version'])

    assert result.exit_code == 0
    assert "Kagura AI" in result.output


def test_cli_help():
    """Test CLI help output"""
    runner = CliRunner()
    result = runner.invoke(cli, ['--help'])

    assert result.exit_code == 0
    assert "Kagura AI" in result.output
    assert "version" in result.output


@pytest.mark.skip(reason="REPL uses prompt_toolkit which requires real terminal, incompatible with CliRunner")
def test_cli_repl_help():
    """Test REPL help command"""
    runner = CliRunner()
    result = runner.invoke(cli, ['repl'], input='/help\n/exit\n')

    assert result.exit_code == 0
    assert "Available Commands" in result.output or "help" in result.output.lower()


def test_cli_invalid_command():
    """Test CLI with invalid command"""
    runner = CliRunner()
    result = runner.invoke(cli, ['invalid-command'])

    assert result.exit_code != 0
