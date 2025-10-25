"""Argument that extends the Click Argument with more functionality."""

# pylint: disable=redefined-builtin
# pylint: disable=too-many-locals
# pylint: disable=too-many-arguments
# pylint: disable=too-many-branches

from typing import Any, Callable, Mapping, TypeVar

import click

F = TypeVar("F", bound=Callable[..., Any])


class Argument(click.Argument):
    """Argument that extends the Click Argument with more functionality."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize a new `Argument` instance.

        Args:
            *args:
                Positional arguments for the base `click.Argument` class.
            **kwargs:
                Keyword arguments for the base `click.Argument` class.
        """
        self.mutually_exclusive: list[str] = kwargs.pop(
            "mutually_exclusive", []
        )
        self.requires: list[str] = kwargs.pop("requires", [])
        self.group: str | None = kwargs.pop("group", None)
        self.group_mutually_exclusive: list[str] = kwargs.pop(
            "group_mutually_exclusive", []
        )
        super().__init__(*args, **kwargs)

    def handle_parse_result(
        self, ctx: click.Context, opts: Mapping[str, Any], args: list[str]
    ) -> tuple[Any, list[str]]:
        """Handle parsing and validate mutual exclusivity and requirements."""
        if self.name is None:
            return super().handle_parse_result(ctx, opts, args)

        current_value = opts.get(self.name)

        def is_value_provided(val: Any) -> bool:
            return val is not None and type(val).__name__ != "Sentinel"

        if is_value_provided(current_value):
            if self.mutually_exclusive:
                for mutex_arg in self.mutually_exclusive:
                    mutex_val = opts.get(mutex_arg)
                    if is_value_provided(mutex_val):
                        raise click.UsageError(
                            f"Argument '{self.name}' is mutually "
                            f"exclusive with '{mutex_arg}'."
                        )

            if self.group and self.group_mutually_exclusive:
                self._validate_group_exclusivity(ctx, opts)

        if self.requires and is_value_provided(current_value):
            missing = []
            for required_arg in self.requires:
                if not is_value_provided(opts.get(required_arg)):
                    missing.append(required_arg)

            if missing:
                raise click.UsageError(
                    f"Argument '{self.name}' requires "
                    f"{', '.join(f'{arg}' for arg in missing)}."
                )

        return super().handle_parse_result(ctx, opts, args)

    def _validate_group_exclusivity(
        self, ctx: click.Context, opts: Mapping[str, Any]
    ) -> None:
        """Validate that mutually exclusive groups are not used together."""

        def is_value_provided(val: Any) -> bool:
            return val is not None and type(val).__name__ != "Sentinel"

        groups: dict[str, list[str]] = {}
        for param in ctx.command.params:
            if (
                isinstance(param, Argument)
                and hasattr(param, "group")
                and param.group
            ):
                if param.group not in groups:
                    groups[param.group] = []
                if param.name:
                    groups[param.group].append(param.name)

        if self.group not in groups:
            return

        for other_group in self.group_mutually_exclusive:
            if other_group not in groups:
                continue

            other_group_args = groups[other_group]
            for other_arg in other_group_args:
                if is_value_provided(opts.get(other_arg)):
                    raise click.UsageError(
                        f"Argument '{self.name}' (group '{self.group}') "
                        f"is mutually exclusive with '{other_arg}' "
                        f"(group '{other_group}')."
                    )


def argument(
    *param_decls: str,
    mutually_exclusive: list[str] | None = None,
    requires: list[str] | None = None,
    group: str | None = None,
    group_mutually_exclusive: list[str] | None = None,
    required: bool = True,
    type: Any | None = None,
    default: Any | None = None,
    callback: Callable[..., Any] | None = None,
    metavar: str | None = None,
    expose_value: bool = True,
    is_eager: bool = False,
    envvar: str | None = None,
    shell_complete: Callable[..., Any] | None = None,
    autocompletion: Callable[..., Any] | None = None,
    nargs: int = 1,
    **kwargs: Any,
) -> Callable[[F], F]:
    """
    Create an argument decorator with extended functionality over the base
    `click.Argument` class.

    Args:
        *param_decls:
            Parameter declarations (e.g., 'name').
        mutually_exclusive (List[str], optional):
            List of argument names that are mutually exclusive with this
            argument.
        requires (List[str], optional):
            List of argument names that must be specified together with this
            argument.
        group (str, optional):
            Group name for this argument. Arguments in the same group are
            logically related.
        group_mutually_exclusive (List[str], optional):
            List of group names that are mutually exclusive with this
            argument's group.
        required (bool):
            Whether the argument is required (default: True).
        type (optional):
            The type to convert the value to (e.g., click.INT, click.Path()).
        default (optional):
            Default value for the argument.
        callback (Callable, optional):
            Callback function to transform the value.
        metavar (str, optional):
            How the value is shown in help text.
        expose_value (bool):
            Whether to pass value to the command function.
        is_eager (bool):
            Process this argument before others.
        envvar (str, optional):
            Environment variable name to read from.
        shell_complete (Callable, optional):
            Shell completion function.
        autocompletion (Callable, optional):
            Deprecated. Use shell_complete instead.
        nargs (int):
            Number of arguments to consume (default: 1, use -1 for
            unlimited).
        **kwargs:
            Additional Click argument parameters.

    Returns:
        Callable[[F], F]:
            A decorator function that takes a command function and returns it
            with the argument attached.

    Examples:
        # Simple mutual exclusivity
        @command()
        @argument("file", required=False, mutually_exclusive=["url"])
        @argument("url", required=False, mutually_exclusive=["file"])
        def cmd(file: str, url: str):
            pass

        # Group-level mutual exclusivity
        @command()
        @argument("file1", group="files", group_mutually_exclusive=["urls"])
        @argument("file2", group="files", group_mutually_exclusive=["urls"])
        @argument("url1", group="urls", group_mutually_exclusive=["files"])
        @argument("url2", group="urls", group_mutually_exclusive=["files"])
        def cmd(file1: str, file2: str, url1: str, url2: str):
            pass
    """
    kwargs["cls"] = Argument

    # Add custom parameters
    if mutually_exclusive:
        kwargs["mutually_exclusive"] = mutually_exclusive
    if requires:
        kwargs["requires"] = requires
    if group:
        kwargs["group"] = group
    if group_mutually_exclusive:
        kwargs["group_mutually_exclusive"] = group_mutually_exclusive

    # Add standard Click parameters (only if not None/default)
    if not required:
        kwargs["required"] = required
    if type is not None:
        kwargs["type"] = type
    if default is not None:
        kwargs["default"] = default
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
    if nargs != 1:
        kwargs["nargs"] = nargs

    return click.argument(*param_decls, **kwargs)
