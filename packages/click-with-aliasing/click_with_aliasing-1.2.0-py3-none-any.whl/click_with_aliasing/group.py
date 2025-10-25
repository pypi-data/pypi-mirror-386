"""The group decorator with alias support."""

import asyncio
import functools
from typing import Any, Callable

import click


class Group(click.Group):
    """A Click group that supports aliasing."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize a new Group instance.

        Args:
            *args (Any):
                Positional arguments for the base click.Group class.
            **kwargs (Any):
                Keyword arguments for the base click.Group class.
        """
        self.aliases: list[str] = kwargs.pop("aliases", [])
        super().__init__(*args, **kwargs)

    def add_command(self, cmd: click.Command, name: str | None = None) -> None:
        """
        Add a command to the group, including its aliases.

        Args:
            cmd (click.Command):
                The command to add to the group.
            name (str, optional):
                The name to use for the command. If not provided, uses the
                command's default name.

        Raises:
            ValueError:
                If the command name is already taken.
        """
        aliases = getattr(cmd, "aliases", None)
        if aliases is None:
            aliases = []
        elif not isinstance(aliases, (list, tuple)):
            aliases = [aliases] if isinstance(aliases, str) else []

        super().add_command(cmd, name)
        for alias in aliases:
            if isinstance(alias, str) and alias.strip():
                super().add_command(cmd, alias)

    def format_commands(
        self, ctx: click.Context, formatter: click.HelpFormatter
    ) -> None:
        """
        Format the command list for display in help text.

        Args:
            ctx (click.Context):
                The Click context containing command information.
            formatter (click.HelpFormatter):
                The formatter to write command information to.
        """
        commands = {}
        for name, cmd in self.commands.items():
            if name == cmd.name:
                aliases = getattr(cmd, "aliases", None)
                if aliases is None:
                    aliases = []
                elif not isinstance(aliases, (list, tuple)):
                    aliases = [aliases] if isinstance(aliases, str) else []

                valid_aliases = [
                    a for a in aliases if isinstance(a, str) and a.strip()
                ]

                if valid_aliases:
                    name = f"{name} ({', '.join(valid_aliases)})"
                commands[name] = cmd

        rows = [
            (name, cmd.get_short_help_str()) for name, cmd in commands.items()
        ]

        if rows:
            with formatter.section("Commands"):
                formatter.write_dl(rows)


def group(
    name: str | None = None,
    *,
    aliases: list[str] | None = None,
    **kwargs: Any,
) -> Callable[[Callable[..., Any]], Group]:
    """
    Create a group decorator with aliasing support.

    Args:
        name (str, optional):
            The name of the group. If not provided, uses the function name.
        aliases (List[str], optional):
            List of alternative names for the group.
        **kwargs (Any):
            Additional keyword arguments passed to click.group.

    Returns:
        Callable[[Callable[..., Any]], Group]:
            A decorator function that takes a group function and returns a
            Group instance with the specified configuration.

    Examples:
        @group(name="my_group")
        def grp():
            pass

        @group(name="my_group", aliases=["mg", "mygrp"])
        def grp():
            pass

        @group()
        def mygroup():
            pass
    """

    def decorator(func: Callable[..., Any]) -> Group:
        inferred_name = name or func.__name__

        original_func = func

        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            def sync_wrapper(*wrapper_args: Any, **wrapper_kwargs: Any) -> Any:
                return asyncio.run(
                    original_func(*wrapper_args, **wrapper_kwargs)
                )

            func = sync_wrapper

        group_decorator = click.group(
            name=inferred_name,
            cls=Group,
            aliases=aliases,
            **kwargs,
        )
        cmd = group_decorator(func)
        return cmd

    return decorator
