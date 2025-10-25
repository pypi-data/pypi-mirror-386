"""Test flexible naming with dashes and underscores."""

from click.testing import CliRunner

from click_with_aliasing import command, option


def test_flexible_naming_underscores():
    """Test that we can use underscores in mutually_exclusive/requires lists."""

    @command("test")
    @option("--my-option", mutually_exclusive=["other_option"])
    @option("--other-option", mutually_exclusive=["my_option"])
    def cmd(my_option, other_option):
        pass

    runner = CliRunner()

    # Both should work
    result = runner.invoke(
        cmd, ["--my-option", "val1", "--other-option", "val2"]
    )
    assert result.exit_code != 0
    assert "mutually exclusive" in result.output.lower()


def test_flexible_naming_dashes():
    """Test that we can use dashes in mutually_exclusive/requires lists."""

    @command("test")
    @option("--my-option", mutually_exclusive=["other-option"])
    @option("--other-option", mutually_exclusive=["my-option"])
    def cmd(my_option, other_option):
        pass

    runner = CliRunner()

    result = runner.invoke(
        cmd, ["--my-option", "val1", "--other-option", "val2"]
    )
    assert result.exit_code != 0
    assert "mutually exclusive" in result.output.lower()


def test_flexible_naming_requires_underscores():
    """Test that requires works with underscores."""

    @command("test")
    @option("--log-file", requires=["log_level"])
    @option("--log-level", requires=["log_file"])
    def cmd(log_file, log_level):
        pass

    runner = CliRunner()

    # Only one provided should fail
    result = runner.invoke(cmd, ["--log-file", "test.log"])
    assert result.exit_code != 0
    assert "requires" in result.output.lower()

    # Both provided should work
    result = runner.invoke(
        cmd, ["--log-file", "test.log", "--log-level", "INFO"]
    )
    assert result.exit_code == 0


def test_flexible_naming_requires_dashes():
    """Test that requires works with dashes."""

    @command("test")
    @option("--log-file", requires=["log-level"])
    @option("--log-level", requires=["log-file"])
    def cmd(log_file, log_level):
        pass

    runner = CliRunner()

    # Only one provided should fail
    result = runner.invoke(cmd, ["--log-file", "test.log"])
    assert result.exit_code != 0
    assert "requires" in result.output.lower()

    # Both provided should work
    result = runner.invoke(
        cmd, ["--log-file", "test.log", "--log-level", "INFO"]
    )
    assert result.exit_code == 0


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
