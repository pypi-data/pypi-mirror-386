"""
Test basic CLI functionality.
"""

import pytest
from click.testing import CliRunner
from bapao.cli import cli


def test_cli_banner():
    """Test that the banner command works."""
    runner = CliRunner()
    result = runner.invoke(cli, ['banner'])
    assert result.exit_code == 0
    assert 'BAPAO' in result.output


def test_cli_help():
    """Test that CLI help displays correctly."""
    runner = CliRunner()
    result = runner.invoke(cli, ['--help'])
    
    assert result.exit_code == 0
    assert 'BAPAO' in result.output
    assert 'Make your entire development environment portable' in result.output


def test_init_help():
    """Test that init command help works."""
    runner = CliRunner()
    result = runner.invoke(cli, ['init', '--help'])
    assert result.exit_code == 0
    assert 'Initialize a new BAPAO profile' in result.output