"""Tests for CLI main module"""
import pytest
from click.testing import CliRunner
from kagura.cli.main import cli


def test_cli_version_option():
    """Test --version option"""
    runner = CliRunner()
    result = runner.invoke(cli, ['--version'])
    assert result.exit_code == 0
    assert '2.0.0-alpha.1' in result.output


def test_cli_version_command():
    """Test version command"""
    runner = CliRunner()
    result = runner.invoke(cli, ['version'])
    assert result.exit_code == 0
    assert 'Kagura AI v2.0.0-alpha.1' in result.output


def test_cli_help():
    """Test --help option"""
    runner = CliRunner()
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0
    assert 'Kagura AI' in result.output
