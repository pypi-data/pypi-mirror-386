"""Tests for the group decorator."""

import asyncio

import click
import pytest
from click.testing import CliRunner

from click_with_aliasing import command, group


@command(name="async_cmd", aliases=["ac"])
async def async_command():
    """An async command for testing."""
    await asyncio.sleep(0.1)
    click.echo("Async command ran")


@group(name="async_grp", aliases=["ag"])
async def async_group():
    """An async group for testing."""
    await asyncio.sleep(0.1)


async_group.add_command(async_command)


@pytest.fixture
def runner():
    """Fixture for invoking Click commands."""
    return CliRunner()


class TestAsyncCommand:
    """Test class for async command functionality."""

    def test_async_command_wrapping(self):
        """Test that async commands are properly wrapped."""
        assert not asyncio.iscoroutinefunction(async_command.callback)

    def test_async_command_execution(self, runner: CliRunner):
        """Test async command execution."""
        result = runner.invoke(async_group, ["async_cmd"])
        assert result.exit_code == 0
        assert "Async command ran" in result.output

    def test_async_command_alias_execution(self, runner: CliRunner):
        """Test async command execution via alias."""
        result = runner.invoke(async_group, ["ac"])
        assert result.exit_code == 0
        assert "Async command ran" in result.output


class TestAsyncGroup:
    """Test class for async group functionality."""

    def test_async_group_wrapping(self):
        """Test that async groups are properly wrapped."""
        assert not asyncio.iscoroutinefunction(async_group.callback)

    def test_async_group_help(self, runner: CliRunner):
        """Test async group help functionality."""
        result = runner.invoke(async_group, ["--help"])
        assert result.exit_code == 0
        assert "async_cmd" in result.output


def test_add_regular_click_command_to_aliased_group():
    """Test that regular Click commands can be added to AliasedGroup."""

    @group(name="test_group")
    def test_grp():
        pass

    @click.command()
    def regular_cmd():
        """A regular Click command."""

    test_grp.add_command(regular_cmd)
