"""Test the command decorator and the AliasedCommand class."""

import asyncio

import click
import pytest
from click.testing import CliRunner

from click_with_aliasing import command, group


@command(name="async_test_command", aliases=["atc"])
async def async_cmd():
    """An async test command."""
    await asyncio.sleep(0.1)
    click.echo("Async test command executed")


@group(name="async_test_group", aliases=["atg"])
async def async_grp():
    """An async test group."""
    await asyncio.sleep(0.1)


async_grp.add_command(async_cmd)


@command(name="test_command", aliases=["tc", "tcmd"])
def cmd():
    """A simple test command."""
    click.echo("Test command executed")


@group()
def cli():
    """A simple Click group."""


cli.add_command(cmd)


@pytest.fixture
def runner():
    """Fixture for invoking Click commands."""
    return CliRunner()


def test_command_name():
    """Test that the command name is correctly assigned."""
    assert cmd.name == "test_command"


def test_command_aliases():
    """Test that aliases are correctly assigned."""
    assert hasattr(cmd, "aliases")
    assert cmd.aliases == ["tc", "tcmd"]


def test_command_execution(runner: CliRunner):
    """Test that the command runs successfully."""
    result = runner.invoke(cli, ["test_command"])
    assert result.exit_code == 0
    assert "Test command executed" in result.output


def test_command_alias_execution(runner: CliRunner):
    """Test that the command executes via its alias."""
    for alias in ["tc", "tcmd"]:
        result = runner.invoke(cli, [alias])
        assert result.exit_code == 0
        assert "Test command executed" in result.output


def test_async_group_name():
    """Test that the async group name is correctly assigned."""
    assert async_grp.name == "async_test_group"


def test_async_group_aliases():
    """Test that aliases are correctly assigned to the async group."""
    assert hasattr(async_grp, "aliases")
    assert async_grp.aliases == ["atg"]


def test_async_group_command_execution(runner: CliRunner):
    """Test that the async command within the async group runs successfully."""
    result = runner.invoke(async_grp, ["async_test_command"])
    assert result.exit_code == 0
    assert "Async test command executed" in result.output


def test_async_group_command_alias_execution(runner: CliRunner):
    """Test that the async command executes via its alias in async group."""
    result = runner.invoke(async_grp, ["atc"])
    assert result.exit_code == 0
    assert "Async test command executed" in result.output


def test_async_group_is_sync_wrapped():
    """Test that async group functions are properly wrapped as sync."""
    assert not asyncio.iscoroutinefunction(async_grp.callback)


def test_async_group_help(runner: CliRunner):
    """Test that async group help works correctly."""
    result = runner.invoke(async_grp, ["--help"])
    assert result.exit_code == 0
    assert "async_test_command" in result.output
    assert "atc" in result.output
