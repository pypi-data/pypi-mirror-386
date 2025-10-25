"""Option that extends the Click Option with more functionality."""

# pylint: disable=redefined-builtin
# pylint: disable=too-many-locals
# pylint: disable=too-many-arguments
# pylint: disable=too-many-branches
# pylint: disable=too-many-statements

from typing import Any, Callable, Mapping, TypeVar

import click

F = TypeVar("F", bound=Callable[..., Any])


class Option(click.Option):
    """Option that extends the Click Option with more functionality."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize a new `Option` instance."""
        self.mutually_exclusive: list[str] = kwargs.pop(
            "mutually_exclusive", []
        )
        self.requires: list[str] = kwargs.pop("requires", [])
        self.group: str | None = kwargs.pop("group", None)
        self.group_mutually_exclusive: list[str] = kwargs.pop(
            "group_mutually_exclusive", []
        )
        super().__init__(*args, **kwargs)

    def _find_option_value(
        self, opts: Mapping[str, Any], option_name: str
    ) -> Any:
        """Find option value, trying both dash and underscore variants."""
        return opts.get(option_name.replace("-", "_"))

    def handle_parse_result(
        self, ctx: click.Context, opts: Mapping[str, Any], args: list[str]
    ) -> tuple[Any, list[str]]:
        """Handle parsing and validate mutual exclusivity and requirements."""
        if self.name is None:
            return super().handle_parse_result(ctx, opts, args)

        current_value = opts.get(self.name)

        if current_value is not None:
            if self.mutually_exclusive:
                conflicting = []
                for mutex_opt in self.mutually_exclusive:
                    if self._find_option_value(opts, mutex_opt) is not None:
                        conflicting.append(mutex_opt.replace("_", "-"))

                if conflicting:
                    if len(conflicting) == 1:
                        conflicts_str = f"'--{conflicting[0]}'"
                    elif len(conflicting) == 2:
                        conflicts_str = (
                            f"'--{conflicting[0]}' and '--{conflicting[1]}'"
                        )
                    else:
                        all_but_last = "', '--".join(conflicting[:-1])
                        conflicts_str = (
                            f"'--{all_but_last}' and '--{conflicting[-1]}'"
                        )

                    raise click.UsageError(
                        f"Option '--{self.name.replace('_', '-')}' "
                        "is mutually exclusive with "
                        f"{conflicts_str}."
                    )

            if self.group and self.group_mutually_exclusive:
                self._validate_group_exclusivity(ctx, opts)

        if self.requires and current_value is not None:
            missing = []
            for required_opt in self.requires:
                if self._find_option_value(opts, required_opt) is None:
                    missing.append(required_opt.replace("_", "-"))

            if missing:
                if len(missing) == 1:
                    missing_str = f"'--{missing[0]}'"
                elif len(missing) == 2:
                    missing_str = f"'--{missing[0]}' and '--{missing[1]}'"
                else:
                    all_but_last = "', '--".join(missing[:-1])
                    missing_str = f"'--{all_but_last}' and '--{missing[-1]}'"

                raise click.UsageError(
                    f"Option '--{self.name.replace('_', '-')}' requires "
                    f"{missing_str}."
                )

        return super().handle_parse_result(ctx, opts, args)

    def _validate_group_exclusivity(
        self, ctx: click.Context, opts: Mapping[str, Any]
    ) -> None:
        """Validate that mutually exclusive groups are not used together."""
        groups: dict[str, list[str]] = {}
        for param in ctx.command.params:
            if (
                isinstance(param, Option)
                and hasattr(param, "group")
                and param.group
            ):
                if param.group not in groups:
                    groups[param.group] = []
                if param.name:
                    groups[param.name] = []
                    groups[param.group].append(param.name)

        if self.group not in groups:
            return

        for other_group in self.group_mutually_exclusive:
            if other_group not in groups:
                continue

            other_group_opts = groups[other_group]
            for other_opt in other_group_opts:
                if opts.get(other_opt) is not None:
                    _name = (self.name or "<unknown>").replace("_", "-")
                    _other_opt = (other_opt or "<unknown>").replace("_", "-")
                    raise click.UsageError(
                        f"Option '--{_name}' (group '{self.group}') "
                        f"is mutually exclusive with '--{_other_opt}' "
                        f"(group '{other_group}')."
                    )


def option(
    *param_decls: str,
    mutually_exclusive: list[str] | None = None,
    requires: list[str] | None = None,
    group: str | None = None,
    group_mutually_exclusive: list[str] | None = None,
    default: Any | None = None,
    required: bool = False,
    type: Any | None = None,
    help: str | None = None,
    hidden: bool = False,
    show_default: bool = False,
    prompt: bool = False,
    confirmation_prompt: bool = False,
    hide_input: bool = False,
    is_flag: bool | None = None,
    flag_value: Any | None = None,
    multiple: bool = False,
    count: bool = False,
    allow_from_autoenv: bool = True,
    show_choices: bool = True,
    show_envvar: bool = False,
    callback: Callable[..., Any] | None = None,
    metavar: str | None = None,
    expose_value: bool = True,
    is_eager: bool = False,
    envvar: str | None = None,
    shell_complete: Callable[..., Any] | None = None,
    autocompletion: Callable[..., Any] | None = None,
    **kwargs: Any,
) -> Callable[[F], F]:
    """
    Create an option decorator with mutual exclusivity and grouping support.

    Args:
        *param_decls:
            Parameter declarations (e.g., "--name", "-n").
        mutually_exclusive (List[str], optional):
            List of option names that are mutually exclusive with this option.
        requires (List[str], optional):
            List of option names that must be specified together with this
            option.
        group (str, optional):
            Group name for this option. Options in the same group are
            logically related.
        group_mutually_exclusive (List[str], optional):
            List of group names that are mutually exclusive with this option's
            group.
        default (optional):
            Default value for the option.
        required (bool):
            Whether the option is required.
        type (optional):
            The type to convert the value to (e.g., click.INT, click.Path()).
        help (str, optional):
            Help text for the option.
        hidden (bool):
            Hide this option from help output.
        show_default (bool):
            Show the default value in help text.
        prompt (bool):
            Prompt the user for input if not provided.
        confirmation_prompt (bool):
            Prompt twice for confirmation (for passwords).
        hide_input (bool):
            Hide user input (for passwords).
        is_flag (bool, optional):
            Whether this is a boolean flag.
        flag_value (optional):
            Value to use when flag is set.
        multiple (bool):
            Allow the option to be specified multiple times.
        count (bool):
            Count the number of times the option is specified.
        allow_from_autoenv (bool):
            Allow value from environment variable.
        show_choices (bool):
            Show valid choices in help text.
        show_envvar (bool):
            Show environment variable name in help text.
        callback (Callable, optional):
            Callback function to transform the value.
        metavar (str, optional):
            How the value is shown in help text.
        expose_value (bool):
            Whether to pass value to the command function.
        is_eager (bool):
            Process this option before others.
        envvar (str, optional):
            Environment variable name to read from.
        shell_complete (Callable, optional):
            Shell completion function.
        autocompletion (Callable, optional):
            Deprecated. Use shell_complete instead.
        **kwargs:
            Additional Click option parameters.

    Returns:
        Callable[[F], F]:
            A decorator function that takes a command function and returns it
            with the option attached.

    Examples:
        # Simple mutual exclusivity
        @command()
        @option("--json", is_flag=True, mutually_exclusive=["xml", "yaml"])
        @option("--xml", is_flag=True, mutually_exclusive=["json", "yaml"])
        @option("--yaml", is_flag=True, mutually_exclusive=["json", "xml"])
        def cmd(json, xml, yaml):
            pass

        # Options that require each other
        @command()
        @option("--username", requires=["password"])
        @option("--password", requires=["username"])
        def cmd(username, password):
            pass

        # Group-level mutual exclusivity
        @command()
        @option("--json", group="format", group_mutually_exclusive=["output"])
        @option("--xml", group="format", group_mutually_exclusive=["output"])
        @option("--stdout", group="output", group_mutually_exclusive=["format"])
        @option("--file", group="output", group_mutually_exclusive=["format"])
        def cmd(json, xml, stdout, file):
            pass
    """
    kwargs["cls"] = Option

    if mutually_exclusive:
        kwargs["mutually_exclusive"] = mutually_exclusive
    if requires:
        kwargs["requires"] = requires
    if group:
        kwargs["group"] = group
    if group_mutually_exclusive:
        kwargs["group_mutually_exclusive"] = group_mutually_exclusive
    if default is not None:
        kwargs["default"] = default
    if required:
        kwargs["required"] = required
    if type is not None:
        kwargs["type"] = type
    if help is not None:
        kwargs["help"] = help
    if hidden:
        kwargs["hidden"] = hidden
    if show_default:
        kwargs["show_default"] = show_default
    if prompt:
        kwargs["prompt"] = prompt
    if confirmation_prompt:
        kwargs["confirmation_prompt"] = confirmation_prompt
    if hide_input:
        kwargs["hide_input"] = hide_input
    if is_flag is not None:
        kwargs["is_flag"] = is_flag
    if flag_value is not None:
        kwargs["flag_value"] = flag_value
    if multiple:
        kwargs["multiple"] = multiple
    if count:
        kwargs["count"] = count
    if not allow_from_autoenv:
        kwargs["allow_from_autoenv"] = allow_from_autoenv
    if not show_choices:
        kwargs["show_choices"] = show_choices
    if show_envvar:
        kwargs["show_envvar"] = show_envvar
    if callback is not None:
        kwargs["callback"] = callback
    if metavar is not None:
        kwargs["metavar"] = metavar
    if not expose_value:
        kwargs["expose_value"] = expose_value
    if is_eager:
        kwargs["is_eager"] = is_eager
    if envvar is not None:
        kwargs["envvar"] = envvar
    if shell_complete is not None:
        kwargs["shell_complete"] = shell_complete
    if autocompletion is not None:
        kwargs["autocompletion"] = autocompletion

    return click.option(*param_decls, **kwargs)
