"""
Tests for the command-line interface.
"""

import pytest
from click.testing import CliRunner
from cybersecurity_log_generator.cli import main


def test_cli_help():
    """Test CLI help output."""
    runner = CliRunner()
    result = runner.invoke(main, ['--help'])
    assert result.exit_code == 0
    assert "Cybersecurity Log Generator" in result.output


def test_cli_list_types():
    """Test CLI list types command."""
    runner = CliRunner()
    result = runner.invoke(main, ['list-types'])
    assert result.exit_code == 0
    assert "Supported Log Types" in result.output


def test_cli_generate_logs():
    """Test CLI generate logs command."""
    runner = CliRunner()
    result = runner.invoke(main, ['generate', '--type', 'ids', '--count', '5'])
    assert result.exit_code == 0
    # The output should contain JSON logs
    assert "timestamp" in result.output or "event_type" in result.output


def test_cli_generate_pillar_logs():
    """Test CLI generate pillar logs command."""
    runner = CliRunner()
    result = runner.invoke(main, ['pillar', '--pillar', 'authentication', '--count', '5'])
    assert result.exit_code == 0
    # The output should contain JSON logs
    assert "timestamp" in result.output or "event_type" in result.output


def test_cli_generate_logs_with_output():
    """Test CLI generate logs with output file."""
    runner = CliRunner()
    result = runner.invoke(main, ['generate', '--type', 'ids', '--count', '3', '--output', 'test_output.json'])
    assert result.exit_code == 0
    assert "Generated 3 logs and saved to test_output.json" in result.output
    
    # Clean up
    import os
    if os.path.exists("test_output.json"):
        os.remove("test_output.json")


def test_cli_invalid_type():
    """Test CLI with invalid log type."""
    runner = CliRunner()
    result = runner.invoke(main, ['generate', '--type', 'invalid_type', '--count', '5'])
    assert result.exit_code == 1
    assert "Error generating logs" in result.output


def test_cli_invalid_pillar():
    """Test CLI with invalid pillar."""
    runner = CliRunner()
    result = runner.invoke(main, ['pillar', '--pillar', 'invalid_pillar', '--count', '5'])
    assert result.exit_code == 1
    assert "Error generating pillar logs" in result.output
