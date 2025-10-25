"""Test improved error messages."""

from click.testing import CliRunner

from click_with_aliasing import command, option


def test_error_message_single_conflict():
    """Test error message with one conflict."""

    @command("test")
    @option("--opt1", mutually_exclusive=["opt2"])
    @option("--opt2")
    def cmd(opt1, opt2):
        pass

    runner = CliRunner()
    result = runner.invoke(cmd, ["--opt1", "val1", "--opt2", "val2"])
    assert result.exit_code != 0
    assert (
        "Option '--opt1' is mutually exclusive with '--opt2'." in result.output
    )


def test_error_message_two_conflicts():
    """Test error message with two conflicts."""

    @command("test")
    @option("--opt1", mutually_exclusive=["opt2", "opt3"])
    @option("--opt2")
    @option("--opt3")
    def cmd(opt1, opt2, opt3):
        pass

    runner = CliRunner()
    result = runner.invoke(
        cmd, ["--opt1", "val1", "--opt2", "val2", "--opt3", "val3"]
    )
    assert result.exit_code != 0
    assert (
        "Option '--opt1' is mutually exclusive with '--opt2' and '--opt3'."
        in result.output
    )


def test_error_message_three_or_more_conflicts():
    """Test error message with three or more conflicts."""

    @command("test")
    @option("--opt1", mutually_exclusive=["opt2", "opt3", "opt4"])
    @option("--opt2")
    @option("--opt3")
    @option("--opt4")
    def cmd(opt1, opt2, opt3, opt4):
        pass

    runner = CliRunner()
    result = runner.invoke(
        cmd,
        [
            "--opt1",
            "val1",
            "--opt2",
            "val2",
            "--opt3",
            "val3",
            "--opt4",
            "val4",
        ],
    )
    assert result.exit_code != 0
    assert (
        "Option '--opt1' is mutually exclusive with '--opt2', '--opt3' and '--opt4'."
        in result.output
    )


def test_error_message_requires_single():
    """Test requires error message with one missing option."""

    @command("test")
    @option("--opt1", requires=["opt2"])
    @option("--opt2")
    def cmd(opt1, opt2):
        pass

    runner = CliRunner()
    result = runner.invoke(cmd, ["--opt1", "val1"])
    assert result.exit_code != 0
    assert "Option '--opt1' requires '--opt2'." in result.output


def test_error_message_requires_two():
    """Test requires error message with two missing options."""

    @command("test")
    @option("--opt1", requires=["opt2", "opt3"])
    @option("--opt2")
    @option("--opt3")
    def cmd(opt1, opt2, opt3):
        pass

    runner = CliRunner()
    result = runner.invoke(cmd, ["--opt1", "val1"])
    assert result.exit_code != 0
    assert "Option '--opt1' requires '--opt2' and '--opt3'." in result.output


def test_error_message_requires_three_or_more():
    """Test requires error message with three or more missing options."""

    @command("test")
    @option("--opt1", requires=["opt2", "opt3", "opt4"])
    @option("--opt2")
    @option("--opt3")
    @option("--opt4")
    def cmd(opt1, opt2, opt3, opt4):
        pass

    runner = CliRunner()
    result = runner.invoke(cmd, ["--opt1", "val1"])
    assert result.exit_code != 0
    assert (
        "Option '--opt1' requires '--opt2', '--opt3' and '--opt4'."
        in result.output
    )


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
