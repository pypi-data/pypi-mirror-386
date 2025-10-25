"""Tests for -h help alias functionality."""

import click
import pytest
from click.testing import CliRunner

from click_with_aliasing import command, group, option


@pytest.fixture
def runner():
    """Fixture that returns a Click CliRunner."""
    return CliRunner()


def test_group_h_help_alias(runner: CliRunner):
    """Test that -h works as an alias for --help on groups."""

    @group()
    def cli():
        """Test group."""

    result = runner.invoke(cli, ["-h"])
    assert result.exit_code == 0
    assert "Test group." in result.output
    assert "-h, --help" in result.output


def test_group_help_still_works(runner: CliRunner):
    """Test that --help still works on groups."""

    @group()
    def cli():
        """Test group."""

    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Test group." in result.output
    assert "-h, --help" in result.output


def test_command_h_help_alias(runner: CliRunner):
    """Test that -h works as an alias for --help on commands."""

    @command("test")
    def cmd():
        """Test command."""
        click.echo("Hello")

    result = runner.invoke(cmd, ["-h"])
    assert result.exit_code == 0
    assert "Test command." in result.output
    assert "-h, --help" in result.output


def test_command_help_still_works(runner: CliRunner):
    """Test that --help still works on commands."""

    @command("test")
    def cmd():
        """Test command."""
        click.echo("Hello")

    result = runner.invoke(cmd, ["--help"])
    assert result.exit_code == 0
    assert "Test command." in result.output
    assert "-h, --help" in result.output


def test_command_with_h_option_no_h_help(runner: CliRunner):
    """Test that commands using -h for another purpose don't get -h help."""

    @command("test")
    @option("--host", "-h", help="Hostname")
    def cmd(host):
        """Test command with -h option."""
        click.echo(f"Host: {host}")

    # -h should be used for --host, not help
    result = runner.invoke(cmd, ["-h", "localhost"])
    assert result.exit_code == 0
    assert "Host: localhost" in result.output

    # --help should still work
    result = runner.invoke(cmd, ["--help"])
    assert result.exit_code == 0
    assert "Test command with -h option." in result.output
    assert "-h, --host TEXT" in result.output
    assert "--help" in result.output
    # Should not have "-h, --help" together
    assert "-h, --help" not in result.output


def test_group_with_h_command_no_h_help(runner: CliRunner):
    """Test that groups with commands using -h don't get -h help."""

    @group()
    def cli():
        """Test group."""

    @command("with_h")
    @option("--host", "-h", help="Hostname")
    def with_h_cmd(host):
        """Command with -h."""
        click.echo(f"Host: {host}")

    @command("without_h")
    def without_h_cmd():
        """Command without -h."""
        click.echo("Hello")

    cli.add_command(with_h_cmd)
    cli.add_command(without_h_cmd)

    # Group should not have -h help because one command uses -h
    result = runner.invoke(cli, ["-h"])
    assert result.exit_code != 0
    assert "No such option: -h" in result.output

    # --help should still work on group
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Test group." in result.output

    # Command with -h should use it for --host
    result = runner.invoke(cli, ["with_h", "-h", "localhost"])
    assert result.exit_code == 0
    assert "Host: localhost" in result.output

    # Command without -h should have -h help
    result = runner.invoke(cli, ["without_h", "-h"])
    assert result.exit_code == 0
    assert "Command without -h." in result.output
    assert "-h, --help" in result.output


def test_subcommand_h_help_alias(runner: CliRunner):
    """Test that -h works on subcommands."""

    @group()
    def cli():
        """Main group."""

    @command("sub")
    @option("--verbose", "-v", is_flag=True)
    def subcmd(verbose):
        """Subcommand."""
        if verbose:
            click.echo("Verbose")

    cli.add_command(subcmd)

    # Subcommand should have -h help
    result = runner.invoke(cli, ["sub", "-h"])
    assert result.exit_code == 0
    assert "Subcommand." in result.output
    assert "-h, --help" in result.output


def test_nested_groups_h_help(runner: CliRunner):
    """Test that -h works on nested groups."""

    @group()
    def cli():
        """Main group."""

    @group("subgroup")
    def subgrp():
        """Sub group."""

    @command("cmd")
    def cmd():
        """Command."""
        click.echo("Hello")

    subgrp.add_command(cmd)
    cli.add_command(subgrp)

    # Main group should have -h help
    result = runner.invoke(cli, ["-h"])
    assert result.exit_code == 0
    assert "Main group." in result.output
    assert "-h, --help" in result.output

    # Subgroup should have -h help
    result = runner.invoke(cli, ["subgroup", "-h"])
    assert result.exit_code == 0
    assert "Sub group." in result.output
    assert "-h, --help" in result.output

    # Command should have -h help
    result = runner.invoke(cli, ["subgroup", "cmd", "-h"])
    assert result.exit_code == 0
    assert "Command." in result.output
    assert "-h, --help" in result.output


def test_multiple_commands_with_h_override(runner: CliRunner):
    """Test group with multiple commands that use -h."""

    @group()
    def cli():
        """Main group."""

    @command("cmd1")
    @option("--host", "-h")
    def cmd1(host):
        """Command 1."""
        click.echo(f"Host: {host}")

    @command("cmd2")
    @option("--header", "-h")
    def cmd2(header):
        """Command 2."""
        click.echo(f"Header: {header}")

    cli.add_command(cmd1)
    cli.add_command(cmd2)

    # Group should not have -h help
    result = runner.invoke(cli, ["-h"])
    assert result.exit_code != 0
    assert "No such option: -h" in result.output

    # Both commands should use -h for their options
    result = runner.invoke(cli, ["cmd1", "-h", "localhost"])
    assert result.exit_code == 0
    assert "Host: localhost" in result.output

    result = runner.invoke(cli, ["cmd2", "-h", "X-Custom"])
    assert result.exit_code == 0
    assert "Header: X-Custom" in result.output


def test_group_with_own_h_option(runner: CliRunner):
    """Test that groups using -h for their own option don't get -h help."""

    @group()
    @option("--host", "-h", help="Server host")
    def cli(host):
        """Main group with host option."""
        if host:
            click.echo(f"Host: {host}")

    @command("run")
    def run():
        """Run command."""
        click.echo("Running")

    cli.add_command(run)

    # Group should not have -h help because it uses -h for --host
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "-h, --host" in result.output
    assert "--help" in result.output
    # Should not have "-h, --help" together
    assert result.output.count("-h,") == 1  # Only once for --host

    # -h should be used for --host
    result = runner.invoke(cli, ["-h", "localhost", "run"])
    assert result.exit_code == 0
    assert "Host: localhost" in result.output
    assert "Running" in result.output

    # Subcommand should still have -h help
    result = runner.invoke(cli, ["run", "-h"])
    assert result.exit_code == 0
    assert "Run command." in result.output
    assert "-h, --help" in result.output


def test_group_and_command_both_use_h(runner: CliRunner):
    """Test when both group and command use -h for their own options."""

    @group()
    @option("--host", "-h", help="Server host")
    def cli(host):
        """Main group with host option."""
        if host:
            click.echo(f"Group host: {host}")

    @command("connect")
    @option("--header", "-h", help="HTTP header")
    def connect(header):
        """Connect with custom header."""
        click.echo(f"Header: {header}")

    @command("ping")
    def ping():
        """Ping the server."""
        click.echo("Pinging...")

    cli.add_command(connect)
    cli.add_command(ping)

    # Group should not have -h help
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "-h, --host" in result.output
    assert "--help" in result.output
    assert result.output.count("-h,") == 1  # Only for --host

    # Group -h should work for --host
    result = runner.invoke(cli, ["-h", "example.com", "ping"])
    assert result.exit_code == 0
    assert "Group host: example.com" in result.output
    assert "Pinging..." in result.output

    # Command with -h should use it for --header
    result = runner.invoke(cli, ["connect", "-h", "X-Custom-Header"])
    assert result.exit_code == 0
    assert "Header: X-Custom-Header" in result.output

    # Command with -h should not have -h help
    result = runner.invoke(cli, ["connect", "--help"])
    assert result.exit_code == 0
    assert "-h, --header" in result.output
    assert "--help" in result.output
    assert result.output.count("-h,") == 1  # Only for --header

    # Command without -h should have -h help
    result = runner.invoke(cli, ["ping", "-h"])
    assert result.exit_code == 0
    assert "Ping the server." in result.output
    assert "-h, --help" in result.output
