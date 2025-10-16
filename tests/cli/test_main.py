"""Tests for CLI main module"""
import pytest
from click.testing import CliRunner
from kagura.cli.main import cli
from kagura.version import __version__


def test_cli_version_option():
    """Test --version option"""
    runner = CliRunner()
    result = runner.invoke(cli, ['--version'])
    assert result.exit_code == 0
    assert __version__ in result.output


def test_cli_version_command():
    """Test version command"""
    runner = CliRunner()
    result = runner.invoke(cli, ['version'])
    assert result.exit_code == 0
    assert f'Kagura AI v{__version__}' in result.output


def test_cli_help():
    """Test --help option"""
    runner = CliRunner()
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0
    assert 'Kagura AI' in result.output


def test_cli_verbose_flag():
    """Test --verbose flag with version command"""
    runner = CliRunner()
    result = runner.invoke(cli, ['--verbose', 'version'])
    assert result.exit_code == 0
    assert f'Kagura AI v{__version__}' in result.output
    assert 'Python-First AI Agent Framework' in result.output
    assert 'https://github.com/JFK/kagura-ai' in result.output


def test_cli_verbose_short_flag():
    """Test -v short flag with version command"""
    runner = CliRunner()
    result = runner.invoke(cli, ['-v', 'version'])
    assert result.exit_code == 0
    assert f'Kagura AI v{__version__}' in result.output
    assert 'Python-First AI Agent Framework' in result.output


def test_cli_quiet_flag():
    """Test --quiet flag with version command"""
    runner = CliRunner()
    result = runner.invoke(cli, ['--quiet', 'version'])
    assert result.exit_code == 0
    assert result.output == ''  # No output when quiet


def test_cli_quiet_short_flag():
    """Test -q short flag with version command"""
    runner = CliRunner()
    result = runner.invoke(cli, ['-q', 'version'])
    assert result.exit_code == 0
    assert result.output == ''


def test_cli_version_normal_output():
    """Test version command without flags shows normal output"""
    runner = CliRunner()
    result = runner.invoke(cli, ['version'])
    assert result.exit_code == 0
    assert f'Kagura AI v{__version__}' in result.output
    # Should not show verbose info by default
    assert 'Python-First AI Agent Framework' not in result.output
