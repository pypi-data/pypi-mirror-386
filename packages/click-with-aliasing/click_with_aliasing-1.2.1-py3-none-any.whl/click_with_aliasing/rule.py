"""Rule decorator for group-level validation of options and arguments."""

# pylint: disable=protected-access
# pylint: disable=too-many-locals
# pylint: disable=too-many-branches
# pylint: disable=too-many-statements

from typing import Any, Callable, Literal

import click

from .argument import Argument
from .option import Option


def rule(
    group_name: str,
    mode: (
        Literal["all_or_none", "at_least", "at_most", "exactly"] | None
    ) = None,
    count: int = 1,
    exclusive_from_groups: list[str] | None = None,
    exclusive_from_options: list[str] | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Define validation rules for a group of options or arguments.

    Args:
        group_name (str):
            The name of the group to apply rules to.
        mode (str, optional):
            The validation mode for the group:
            - `all_or_none`: Either all options provided or none
            - `at_least`: Minimum number of options required (set by count)
            - `at_most`: Maximum number of options allowed (set by count)
            - `exactly`: Exact number of options required (set by count)
        count (int):
            Number used with `at_least`, `at_most`, or `exactly` modes.
        exclusive_from_groups (List[str], optional):
            List of group names that are mutually exclusive with this group.
        exclusive_from_options (List[str], optional):
            List of option/argument names that are mutually exclusive with this
            group.

    Returns:
        Callable[[Callable[..., Any]], Callable[..., Any]]:
            A decorator function that takes a command function and returns it
            with validation rules attached.

    Raises:
        ValueError:
            If invalid parameters are provided at definition time.

    Examples:
        @command()
        @option("--username", group="credentials")
        @option("--password", group="credentials")
        @rule(
            "credentials",
            mode="all_or_none",
            exclusive_from_options=["token"]
        )
        @option("--token")
        def cmd(...):
            pass

        @command()
        @option("--json", group="format")
        @option("--xml", group="format")
        @rule("format", mode="exactly")
        def cmd(...):
            pass

        @command()
        @option("--file1", group="files")
        @option("--file2", group="files")
        @option("--file3", group="files")
        @rule("files", mode="at_least", count=2)
        def cmd(...):
            pass
    """
    valid_modes = ["all_or_none", "at_least", "at_most", "exactly"]
    if mode and mode not in valid_modes:
        raise ValueError(
            f"Parameter 'mode' must be one of {valid_modes} (got {mode!r})"
        )

    if count != 1 and mode not in ["at_least", "at_most", "exactly"]:
        raise ValueError(
            "Parameter 'count' can only be used with modes "
            "'at_least', 'at_most', "
            f"or 'exactly' (got mode={mode!r})"
        )

    if count < 1:
        raise ValueError(
            f"Parameter 'count' must be a positive integer (got {count})"
        )

    if (
        mode is None
        and not exclusive_from_groups
        and not exclusive_from_options
    ):
        raise ValueError(
            "Must specify either 'mode', 'exclusive_from_groups', "
            "or 'exclusive_from_options'"
        )

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        if not hasattr(func, "_group_rules"):
            func._group_rules = {}  # type: ignore[attr-defined]

        if group_name in func._group_rules:  # type: ignore[attr-defined]
            raise ValueError(f"Group '{group_name}' already has a rule defined")

        func._group_rules[group_name] = {  # type: ignore[attr-defined]
            "mode": mode,
            "count": count,
            "exclusive_from_groups": exclusive_from_groups or [],
            "exclusive_from_options": exclusive_from_options or [],
        }

        # pylint: disable=line-too-long
        original_callback = func.callback if hasattr(func, "callback") else func  # type: ignore[attr-defined]

        def validation_wrapper(*args: Any, **kwargs: Any) -> Any:
            ctx = click.get_current_context()
            opts = ctx.params

            rules = getattr(func, "_group_rules", {})

            _validate_rules(ctx, rules, opts)

            return original_callback(*args, **kwargs)

        validation_wrapper.__name__ = original_callback.__name__
        validation_wrapper.__doc__ = original_callback.__doc__

        if hasattr(func, "callback"):
            func.callback = validation_wrapper  # type: ignore[attr-defined]
        else:
            rules_to_preserve = func._group_rules  # type: ignore[attr-defined]
            func = validation_wrapper
            func._group_rules = rules_to_preserve  # type: ignore[attr-defined]

        return func

    return decorator


def _normalize_name(name: str) -> str:
    """
    Normalize option/argument name by converting dashes to underscores.

    Args:
        name (str):
            The option or argument name to normalize.

    Returns:
        str:
            The normalized name with underscores instead of dashes.
    """
    return name.replace("-", "_")


def _format_options_list(options: list[str]) -> str:
    """
    Format a list of option names for error messages.

    Args:
        options (list[str]):
            List of option names to format.

    Returns:
        str:
            Formatted string with proper grammar and quotation.
    """
    if len(options) == 1:
        return f"'--{options[0]}'"
    if len(options) == 2:
        return f"'--{options[0]}' and '--{options[1]}'"
    all_but_last = "', '--".join(options[:-1])
    return f"'--{all_but_last}' and '--{options[-1]}'"


def _validate_rules(
    ctx: click.Context, rules: dict[str, Any], opts: dict[str, Any]
) -> None:
    """
    Validate all group rules at runtime.

    Args:
        ctx (click.Context):
            The Click context containing command information.
        rules (dict[str, Any]):
            Dictionary mapping group names to their rule configurations.
        opts (dict[str, Any]):
            Dictionary of parsed option/argument values.

    Raises:
        click.UsageError:
            If any validation rule is violated.
    """

    def is_value_provided(val: Any) -> bool:
        return (
            val is not None
            and type(val).__name__ != "Sentinel"
            and val is not False
        )

    groups: dict[str, list[str]] = {}
    for param in ctx.command.params:
        if (
            isinstance(param, (Option, Argument))
            and hasattr(param, "group")
            and param.group
        ):
            if param.group not in groups:
                groups[param.group] = []
            if param.name:
                groups[param.group].append(param.name)

    for group_name, rule_config in rules.items():
        group_params = groups.get(group_name, [])
        if not group_params:
            continue

        provided_params: list[str] = []
        for param_name in group_params:
            value = opts.get(param_name)
            if is_value_provided(value):
                provided_params.append(param_name)

        for other_group in rule_config["exclusive_from_groups"]:
            other_params = groups.get(other_group, [])
            conflicting: list[str] = []
            for param_name in other_params:
                value = opts.get(param_name)
                if is_value_provided(value):
                    conflicting.append(param_name)

            if conflicting and provided_params:
                raise click.UsageError(
                    f"Group '{group_name}' "
                    f"(option '--{provided_params[0].replace('_', '-')}') "
                    f"is mutually exclusive with group '{other_group}' "
                    f"(option '--{conflicting[0].replace('_', '-')}')"
                )

        for option_name in rule_config["exclusive_from_options"]:
            normalized = _normalize_name(option_name)
            value = opts.get(normalized)
            if is_value_provided(value) and provided_params:
                raise click.UsageError(
                    f"Group '{group_name}' "
                    f"(option '--{provided_params[0].replace('_', '-')}') "
                    "is mutually exclusive with option "
                    f"'--{option_name.replace('_', '-')}'"
                )

        mode = rule_config["mode"]
        count = rule_config["count"]

        if mode == "all_or_none":
            if provided_params and len(provided_params) != len(group_params):
                missing = [
                    param_name.replace("_", "-")
                    for param_name in group_params
                    if param_name not in provided_params
                ]
                raise click.UsageError(
                    f"Group '{group_name}' requires all options "
                    "when any are provided. "
                    f"Missing: {_format_options_list(missing)}"
                )

        elif mode == "at_least":
            if len(provided_params) < count:
                if provided_params:
                    options_list_fmt = _format_options_list(
                        [p.replace("_", "-") for p in provided_params]
                    )
                    provided_str = (
                        f" (got {len(provided_params)}: {options_list_fmt})"
                    )
                else:
                    provided_str = ""
                raise click.UsageError(
                    f"Group '{group_name}' requires at least {count} "
                    f"{'option' if count == 1 else 'options'}{provided_str}"
                )

        elif mode == "at_most":
            if len(provided_params) > count:
                provided_list = [p.replace("_", "-") for p in provided_params]
                options_list_fmt = _format_options_list(provided_list)
                raise click.UsageError(
                    f"Group '{group_name}' allows at most {count} "
                    f"{'option' if count == 1 else 'options'} "
                    f"(got {len(provided_params)}: {options_list_fmt})"
                )

        elif mode == "exactly":
            if len(provided_params) != count:
                if provided_params:
                    provided_list = [
                        p.replace("_", "-") for p in provided_params
                    ]
                    options_list_fmt = _format_options_list(provided_list)
                    provided_str = (
                        f" (got {len(provided_params)}: {options_list_fmt})"
                    )
                else:
                    provided_str = ""
                raise click.UsageError(
                    f"Group '{group_name}' requires exactly {count} "
                    f"{'option' if count == 1 else 'options'}{provided_str}"
                )
