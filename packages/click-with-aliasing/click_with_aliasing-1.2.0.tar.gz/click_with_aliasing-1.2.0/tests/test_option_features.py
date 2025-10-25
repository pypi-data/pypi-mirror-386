"""Test the enhanced option features (mutual exclusivity and grouping)."""

import pytest
from click.testing import CliRunner

from click_with_aliasing import command, option


@pytest.fixture
def runner():
    """Fixture for invoking Click commands."""
    return CliRunner()


def test_mutually_exclusive_options_valid(runner: CliRunner):
    """Test that mutually exclusive options work when only one is provided."""

    @command("test")
    @option("--json", is_flag=True, mutually_exclusive=["xml"])
    @option("--xml", is_flag=True, mutually_exclusive=["json"])
    def cmd(json, xml):
        if json:
            return "json"
        if xml:
            return "xml"
        return "none"

    # Test with --json only
    result = runner.invoke(cmd, ["--json"])
    assert result.exit_code == 0

    # Test with --xml only
    result = runner.invoke(cmd, ["--xml"])
    assert result.exit_code == 0

    # Test with neither
    result = runner.invoke(cmd, [])
    assert result.exit_code == 0


def test_mutually_exclusive_options_invalid(runner: CliRunner):
    """Test that mutually exclusive options fail when both are provided."""

    @command("test")
    @option("--json", is_flag=True, mutually_exclusive=["xml"])
    @option("--xml", is_flag=True, mutually_exclusive=["json"])
    def cmd(json, xml):
        pass

    # Test with both --json and --xml
    result = runner.invoke(cmd, ["--json", "--xml"])
    assert result.exit_code != 0
    assert "mutually exclusive" in result.output.lower()


def test_multiple_mutually_exclusive_options(runner: CliRunner):
    """Test mutual exclusivity with more than two options."""

    @command("test")
    @option("--json", is_flag=True, mutually_exclusive=["xml", "yaml"])
    @option("--xml", is_flag=True, mutually_exclusive=["json", "yaml"])
    @option("--yaml", is_flag=True, mutually_exclusive=["json", "xml"])
    def cmd(json, xml, yaml):
        pass

    # Valid: only one option
    result = runner.invoke(cmd, ["--json"])
    assert result.exit_code == 0

    result = runner.invoke(cmd, ["--xml"])
    assert result.exit_code == 0

    result = runner.invoke(cmd, ["--yaml"])
    assert result.exit_code == 0

    # Invalid: two options
    result = runner.invoke(cmd, ["--json", "--xml"])
    assert result.exit_code != 0

    result = runner.invoke(cmd, ["--json", "--yaml"])
    assert result.exit_code != 0

    result = runner.invoke(cmd, ["--xml", "--yaml"])
    assert result.exit_code != 0


def test_requires_options_valid(runner: CliRunner):
    """Test that required options work when all are provided."""

    @command("test")
    @option("--username", requires=["password"])
    @option("--password", requires=["username"])
    def cmd(username, password):
        pass

    # Valid: both provided
    result = runner.invoke(cmd, ["--username", "user", "--password", "pass"])
    assert result.exit_code == 0

    # Valid: neither provided
    result = runner.invoke(cmd, [])
    assert result.exit_code == 0


def test_requires_options_invalid(runner: CliRunner):
    """Test that required options fail when only some are provided."""

    @command("test")
    @option("--username", requires=["password"])
    @option("--password", requires=["username"])
    def cmd(username, password):
        pass

    # Invalid: only username
    result = runner.invoke(cmd, ["--username", "user"])
    assert result.exit_code != 0
    assert "requires" in result.output.lower()

    # Invalid: only password
    result = runner.invoke(cmd, ["--password", "pass"])
    assert result.exit_code != 0
    assert "requires" in result.output.lower()


def test_group_mutually_exclusive_valid(runner: CliRunner):
    """Test that group-level mutual exclusivity works correctly."""

    @command("test")
    @option(
        "--json",
        is_flag=True,
        group="format",
        group_mutually_exclusive=["output"],
    )
    @option(
        "--xml",
        is_flag=True,
        group="format",
        group_mutually_exclusive=["output"],
    )
    @option(
        "--stdout",
        is_flag=True,
        group="output",
        group_mutually_exclusive=["format"],
    )
    @option("--file", group="output", group_mutually_exclusive=["format"])
    def cmd(json, xml, stdout, file):
        pass

    # Valid: options from same group
    result = runner.invoke(cmd, ["--json", "--xml"])
    assert result.exit_code == 0

    result = runner.invoke(cmd, ["--stdout", "--file", "test.txt"])
    assert result.exit_code == 0

    # Valid: options from format group only
    result = runner.invoke(cmd, ["--json"])
    assert result.exit_code == 0


def test_group_mutually_exclusive_invalid(runner: CliRunner):
    """Test that group-level mutual exclusivity fails correctly."""

    @command("test")
    @option(
        "--json",
        is_flag=True,
        group="format",
        group_mutually_exclusive=["output"],
    )
    @option(
        "--xml",
        is_flag=True,
        group="format",
        group_mutually_exclusive=["output"],
    )
    @option(
        "--stdout",
        is_flag=True,
        group="output",
        group_mutually_exclusive=["format"],
    )
    @option("--file", group="output", group_mutually_exclusive=["format"])
    def cmd(json, xml, stdout, file):
        pass

    # Invalid: options from different mutually exclusive groups
    result = runner.invoke(cmd, ["--json", "--stdout"])
    assert result.exit_code != 0
    assert "mutually exclusive" in result.output.lower()

    result = runner.invoke(cmd, ["--xml", "--file", "test.txt"])
    assert result.exit_code != 0
    assert "mutually exclusive" in result.output.lower()


def test_combined_features(runner: CliRunner):
    """Test combining mutual exclusivity and requirements."""

    @command("test")
    @option("--verbose", "-v", is_flag=True, mutually_exclusive=["quiet"])
    @option("--quiet", "-q", is_flag=True, mutually_exclusive=["verbose"])
    @option("--log-file", requires=["log-level"])
    @option("--log-level", requires=["log-file"])
    def cmd(verbose, quiet, log_file, log_level):
        pass

    # Valid: verbose only
    result = runner.invoke(cmd, ["--verbose"])
    assert result.exit_code == 0

    # Valid: quiet only
    result = runner.invoke(cmd, ["--quiet"])
    assert result.exit_code == 0

    # Valid: log options together
    result = runner.invoke(
        cmd, ["--log-file", "test.log", "--log-level", "INFO"]
    )
    assert result.exit_code == 0

    # Invalid: verbose and quiet together
    result = runner.invoke(cmd, ["--verbose", "--quiet"])
    assert result.exit_code != 0

    # Invalid: log-file without log-level
    result = runner.invoke(cmd, ["--log-file", "test.log"])
    assert result.exit_code != 0

    # Invalid: log-level without log-file
    result = runner.invoke(cmd, ["--log-level", "INFO"])
    assert result.exit_code != 0
