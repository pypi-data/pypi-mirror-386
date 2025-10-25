"""Test the enhanced argument features (mutual exclusivity and grouping)."""

import pytest
from click.testing import CliRunner

from click_with_aliasing import argument, command


@pytest.fixture
def runner():
    """Fixture for invoking Click commands."""
    return CliRunner()


def test_mutually_exclusive_arguments_valid(runner: CliRunner):
    """Test that mutually exclusive arguments work when only one is provided."""

    @command("test")
    @argument("input_file", required=False, mutually_exclusive=["input_url"])
    @argument("input_url", required=False, mutually_exclusive=["input_file"])
    def cmd(input_file, input_url):
        if input_file:
            return f"file: {input_file}"
        if input_url:
            return f"url: {input_url}"
        return "none"

    # Test with file only
    result = runner.invoke(cmd, ["test.txt"])
    assert result.exit_code == 0

    # Test with url only
    result = runner.invoke(cmd, ["http://example.com"])
    assert result.exit_code == 0

    # Test with neither
    result = runner.invoke(cmd, [])
    assert result.exit_code == 0


def test_mutually_exclusive_arguments_invalid(runner: CliRunner):
    """Test that mutually exclusive arguments fail when both are provided."""

    @command("test")
    @argument("input_file", required=False, mutually_exclusive=["input_url"])
    @argument("input_url", required=False, mutually_exclusive=["input_file"])
    def cmd(input_file, input_url):
        pass

    # Test with both arguments - this is tricky because Click will assign
    # positional args in order, so we need to ensure both get values
    result = runner.invoke(cmd, ["file.txt", "http://example.com"])
    assert result.exit_code != 0
    assert "mutually exclusive" in result.output.lower()


def test_argument_requires(runner: CliRunner):
    """Test that argument requirements work correctly."""

    @command("test")
    @argument("host", required=False, requires=["port"])
    @argument("port", required=False, requires=["host"])
    def cmd(host, port):
        pass

    # Valid: both provided
    result = runner.invoke(cmd, ["localhost", "8080"])
    assert result.exit_code == 0

    # Valid: neither provided
    result = runner.invoke(cmd, [])
    assert result.exit_code == 0

    # Invalid: only one provided
    result = runner.invoke(cmd, ["localhost"])
    assert result.exit_code != 0
    assert "requires" in result.output.lower()


def test_argument_group_mutually_exclusive_valid(runner: CliRunner):
    """Test that group-level mutual exclusivity works for arguments."""

    @command("test")
    @argument(
        "file1",
        required=False,
        group="files",
        group_mutually_exclusive=["urls"],
    )
    @argument(
        "file2",
        required=False,
        group="files",
        group_mutually_exclusive=["urls"],
    )
    @argument(
        "url1", required=False, group="urls", group_mutually_exclusive=["files"]
    )
    @argument(
        "url2", required=False, group="urls", group_mutually_exclusive=["files"]
    )
    def cmd(file1, file2, url1, url2):
        pass

    # Valid: arguments from same group
    result = runner.invoke(cmd, ["file1.txt", "file2.txt"])
    assert result.exit_code == 0

    # Valid: single file argument
    result = runner.invoke(cmd, ["file1.txt"])
    assert result.exit_code == 0


def test_argument_group_mutually_exclusive_invalid(runner: CliRunner):
    """Test that group-level mutual exclusivity fails correctly for arguments."""

    @command("test")
    @argument(
        "file1",
        required=False,
        group="files",
        group_mutually_exclusive=["urls"],
    )
    @argument(
        "url1", required=False, group="urls", group_mutually_exclusive=["files"]
    )
    def cmd(file1, url1):
        pass

    # Invalid: arguments from different mutually exclusive groups
    # This will assign both positional arguments
    result = runner.invoke(cmd, ["file.txt", "http://example.com"])
    assert result.exit_code != 0
    assert "mutually exclusive" in result.output.lower()
