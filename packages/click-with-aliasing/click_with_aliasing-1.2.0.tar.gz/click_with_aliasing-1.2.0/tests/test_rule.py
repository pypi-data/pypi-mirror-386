"""Tests for the rule decorator functionality."""

import click
import pytest
from click.testing import CliRunner

from click_with_aliasing import command, option, rule


def test_rule_all_or_none_valid_all_provided():
    """Test all_or_none mode when all options are provided."""

    @command("test")
    @option("--username", group="creds")
    @option("--password", group="creds")
    @option("--email", group="creds")
    @rule("creds", mode="all_or_none")
    def cmd(username, password, email):
        click.echo(f"{username}:{password}:{email}")

    runner = CliRunner()
    result = runner.invoke(
        cmd,
        [
            "--username",
            "john",
            "--password",
            "secret",
            "--email",
            "john@example.com",
        ],
    )
    assert result.exit_code == 0
    assert "john:secret:john@example.com" in result.output


def test_rule_all_or_none_valid_none_provided():
    """Test all_or_none mode when no options are provided."""

    @command("test")
    @option("--username", group="creds")
    @option("--password", group="creds")
    @option("--email", group="creds")
    @rule("creds", mode="all_or_none")
    def cmd(username, password, email):
        click.echo("None provided")

    runner = CliRunner()
    result = runner.invoke(cmd, [])
    assert result.exit_code == 0
    assert "None provided" in result.output


def test_rule_all_or_none_invalid_partial():
    """Test all_or_none mode when only some options are provided."""

    @command("test")
    @option("--username", group="creds")
    @option("--password", group="creds")
    @option("--email", group="creds")
    @rule("creds", mode="all_or_none")
    def cmd(username, password, email):
        click.echo("Success")

    runner = CliRunner()
    result = runner.invoke(cmd, ["--username", "john"])
    assert result.exit_code != 0
    assert (
        "Group 'creds' requires all options when any are provided"
        in result.output
    )
    assert "'--password' and '--email'" in result.output


def test_rule_at_least_valid():
    """Test at_least mode when requirement is satisfied."""

    @command("test")
    @option("--option1", group="opts")
    @option("--option2", group="opts")
    @option("--option3", group="opts")
    @rule("opts", mode="at_least", count=2)
    def cmd(option1, option2, option3):
        click.echo("Success")

    runner = CliRunner()
    result = runner.invoke(cmd, ["--option1", "val1", "--option2", "val2"])
    assert result.exit_code == 0
    assert "Success" in result.output


def test_rule_at_least_invalid():
    """Test at_least mode when requirement is not met."""

    @command("test")
    @option("--option1", group="opts")
    @option("--option2", group="opts")
    @option("--option3", group="opts")
    @rule("opts", mode="at_least", count=2)
    def cmd(option1, option2, option3):
        click.echo("Success")

    runner = CliRunner()
    result = runner.invoke(cmd, ["--option1", "val1"])
    assert result.exit_code != 0
    assert "Group 'opts' requires at least 2 options" in result.output


def test_rule_at_most_valid():
    """Test at_most mode when requirement is satisfied."""

    @command("test")
    @option("--option1", group="opts")
    @option("--option2", group="opts")
    @option("--option3", group="opts")
    @rule("opts", mode="at_most", count=2)
    def cmd(option1, option2, option3):
        click.echo("Success")

    runner = CliRunner()
    result = runner.invoke(cmd, ["--option1", "val1", "--option2", "val2"])
    assert result.exit_code == 0
    assert "Success" in result.output


def test_rule_at_most_invalid():
    """Test at_most mode when too many options are provided."""

    @command("test")
    @option("--option1", group="opts")
    @option("--option2", group="opts")
    @option("--option3", group="opts")
    @rule("opts", mode="at_most", count=2)
    def cmd(option1, option2, option3):
        click.echo("Success")

    runner = CliRunner()
    result = runner.invoke(
        cmd, ["--option1", "val1", "--option2", "val2", "--option3", "val3"]
    )
    assert result.exit_code != 0
    assert "Group 'opts' allows at most 2 options" in result.output
    assert "(got 3:" in result.output


def test_rule_exactly_valid():
    """Test exactly mode when requirement is satisfied."""

    @command("test")
    @option("--option1", group="opts")
    @option("--option2", group="opts")
    @option("--option3", group="opts")
    @rule("opts", mode="exactly", count=2)
    def cmd(option1, option2, option3):
        click.echo("Success")

    runner = CliRunner()
    result = runner.invoke(cmd, ["--option1", "val1", "--option2", "val2"])
    assert result.exit_code == 0
    assert "Success" in result.output


def test_rule_exactly_invalid_too_few():
    """Test exactly mode when too few options are provided."""

    @command("test")
    @option("--option1", group="opts")
    @option("--option2", group="opts")
    @option("--option3", group="opts")
    @rule("opts", mode="exactly", count=2)
    def cmd(option1, option2, option3):
        click.echo("Success")

    runner = CliRunner()
    result = runner.invoke(cmd, ["--option1", "val1"])
    assert result.exit_code != 0
    assert "Group 'opts' requires exactly 2 options" in result.output


def test_rule_exactly_invalid_too_many():
    """Test exactly mode when too many options are provided."""

    @command("test")
    @option("--option1", group="opts")
    @option("--option2", group="opts")
    @option("--option3", group="opts")
    @rule("opts", mode="exactly", count=2)
    def cmd(option1, option2, option3):
        click.echo("Success")

    runner = CliRunner()
    result = runner.invoke(
        cmd, ["--option1", "val1", "--option2", "val2", "--option3", "val3"]
    )
    assert result.exit_code != 0
    assert "Group 'opts' requires exactly 2 options" in result.output


def test_rule_exclusive_from_options_valid():
    """Test exclusive_from_options when no conflict exists."""

    @command("test")
    @option("--username", group="creds")
    @option("--password", group="creds")
    @option("--token")
    @rule("creds", mode="all_or_none", exclusive_from_options=["token"])
    def cmd(username, password, token):
        if token:
            click.echo(f"Token: {token}")
        else:
            click.echo(f"Creds: {username}:{password}")

    runner = CliRunner()

    # Test with credentials only
    result = runner.invoke(cmd, ["--username", "john", "--password", "secret"])
    assert result.exit_code == 0
    assert "Creds: john:secret" in result.output

    # Test with token only
    result = runner.invoke(cmd, ["--token", "abc123"])
    assert result.exit_code == 0
    assert "Token: abc123" in result.output


def test_rule_exclusive_from_options_invalid():
    """Test exclusive_from_options when conflict exists."""

    @command("test")
    @option("--username", group="creds")
    @option("--password", group="creds")
    @option("--token")
    @rule("creds", mode="all_or_none", exclusive_from_options=["token"])
    def cmd(username, password, token):
        click.echo("Success")

    runner = CliRunner()
    result = runner.invoke(cmd, ["--username", "john", "--token", "abc123"])
    assert result.exit_code != 0
    assert (
        "Group 'creds' (option '--username') is mutually exclusive with option '--token'"
        in result.output
    )


def test_rule_exclusive_from_groups_valid():
    """Test exclusive_from_groups when no conflict exists."""

    @command("test")
    @option("--username", group="creds")
    @option("--password", group="creds")
    @option("--api-key", group="api")
    @option("--api-secret", group="api")
    @rule("creds", mode="all_or_none", exclusive_from_groups=["api"])
    @rule("api", mode="all_or_none")
    def cmd(username, password, api_key, api_secret):
        if username:
            click.echo(f"Creds: {username}:{password}")
        else:
            click.echo(f"API: {api_key}:{api_secret}")

    runner = CliRunner()

    # Test with credentials only
    result = runner.invoke(cmd, ["--username", "john", "--password", "secret"])
    assert result.exit_code == 0
    assert "Creds: john:secret" in result.output

    # Test with API keys only
    result = runner.invoke(
        cmd, ["--api-key", "key123", "--api-secret", "secret456"]
    )
    assert result.exit_code == 0
    assert "API: key123:secret456" in result.output


def test_rule_exclusive_from_groups_invalid():
    """Test exclusive_from_groups when conflict exists."""

    @command("test")
    @option("--username", group="creds")
    @option("--password", group="creds")
    @option("--api-key", group="api")
    @option("--api-secret", group="api")
    @rule("creds", mode="all_or_none", exclusive_from_groups=["api"])
    @rule("api", mode="all_or_none")
    def cmd(username, password, api_key, api_secret):
        click.echo("Success")

    runner = CliRunner()

    # Test with both groups complete but mutually exclusive
    result = runner.invoke(
        cmd,
        [
            "--username",
            "john",
            "--password",
            "secret",
            "--api-key",
            "key123",
            "--api-secret",
            "secret456",
        ],
    )
    assert result.exit_code != 0
    assert "is mutually exclusive with group" in result.output


def test_rule_with_dashes_and_underscores():
    """Test that rule works with both dashes and underscores in option names."""

    @command("test")
    @option("--user-name", group="creds")
    @option("--pass-word", group="creds")
    @rule("creds", mode="all_or_none")
    def cmd(user_name, pass_word):
        click.echo(f"{user_name}:{pass_word}")

    runner = CliRunner()
    result = runner.invoke(
        cmd, ["--user-name", "john", "--pass-word", "secret"]
    )
    assert result.exit_code == 0
    assert "john:secret" in result.output


def test_rule_multiple_groups():
    """Test multiple rule decorators on the same command."""

    @command("test")
    @option("--username", group="creds")
    @option("--password", group="creds")
    @option("--host", group="connection")
    @option("--port", group="connection")
    @rule("creds", mode="all_or_none")
    @rule("connection", mode="all_or_none")
    def cmd(username, password, host, port):
        click.echo(f"{username}@{host}:{port}")

    runner = CliRunner()

    # Valid: both groups complete
    result = runner.invoke(
        cmd,
        [
            "--username",
            "john",
            "--password",
            "secret",
            "--host",
            "localhost",
            "--port",
            "8080",
        ],
    )
    assert result.exit_code == 0
    assert "john@localhost:8080" in result.output

    # Invalid: partial credentials
    result = runner.invoke(
        cmd, ["--username", "john", "--host", "localhost", "--port", "8080"]
    )
    assert result.exit_code != 0
    assert "Group 'creds' requires all options" in result.output

    # Invalid: partial connection
    result = runner.invoke(
        cmd,
        ["--username", "john", "--password", "secret", "--host", "localhost"],
    )
    assert result.exit_code != 0
    assert "Group 'connection' requires all options" in result.output


def test_rule_definition_time_error_invalid_mode():
    """Test that invalid mode raises ValueError at definition time."""

    with pytest.raises(ValueError, match="Parameter 'mode' must be one of"):

        @command("test")
        @option("--opt1", group="grp")
        @rule("grp", mode="invalid_mode")  # type: ignore
        def cmd(opt1):
            pass


def test_rule_definition_time_error_invalid_count():
    """Test that invalid count raises ValueError at definition time."""

    with pytest.raises(
        ValueError, match="Parameter 'count' must be a positive integer"
    ):

        @command("test")
        @option("--opt1", group="grp")
        @rule("grp", mode="at_least", count=0)
        def cmd(opt1):
            pass


def test_rule_with_at_least_count_one():
    """Test at_least mode with count=1 (at least one required)."""

    @command("test")
    @option("--option1", group="opts")
    @option("--option2", group="opts")
    @option("--option3", group="opts")
    @rule("opts", mode="at_least", count=1)
    def cmd(option1, option2, option3):
        click.echo("Success")

    runner = CliRunner()

    # Valid: one option
    result = runner.invoke(cmd, ["--option1", "val1"])
    assert result.exit_code == 0

    # Invalid: no options
    result = runner.invoke(cmd, [])
    assert result.exit_code != 0
    assert "Group 'opts' requires at least 1 option" in result.output


def test_rule_error_message_formatting():
    """Test that error messages are properly formatted with option lists."""

    @command("test")
    @option("--opt1", group="grp")
    @option("--opt2", group="grp")
    @option("--opt3", group="grp")
    @rule("grp", mode="all_or_none")
    def cmd(opt1, opt2, opt3):
        click.echo("Success")

    runner = CliRunner()

    # Missing two options
    result = runner.invoke(cmd, ["--opt1", "val1"])
    assert result.exit_code != 0
    assert "'--opt2' and '--opt3'" in result.output

    # Missing one option
    result = runner.invoke(cmd, ["--opt1", "val1", "--opt2", "val2"])
    assert result.exit_code != 0
    assert "'--opt3'" in result.output
