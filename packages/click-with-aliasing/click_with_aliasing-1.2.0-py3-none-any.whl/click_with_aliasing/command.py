"""The command decorator with alias support."""

import asyncio
import functools
from typing import Any, Callable

import click


class Command(click.Command):
    """A Click command that supports aliasing."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize a new Command instance.

        Args:
            *args (Any):
                Positional arguments for the base click.Command class.
            **kwargs (Any):
                Keyword arguments for the base click.Command class.
        """
        self.aliases: list[str] = kwargs.pop("aliases", [])
        super().__init__(*args, **kwargs)


def command(
    name: str,
    *args: Any,
    aliases: list[str] | None = None,
    **kwargs: Any,
) -> Callable[[Callable[..., Any]], Command]:
    """
    Create a command decorator with aliasing support.

    Args:
        name (str):
            The name of the command.
        aliases (List[str], optional):
            List of alternative names for the command.
        *args (Any):
            Additional positional arguments passed to click.command.
        **kwargs (Any):
            Additional keyword arguments passed to click.command.

    Returns:
        Callable[[Callable[..., Any]], Command]:
            A decorator function that takes a command function and returns a
            Command instance with the specified configuration.

    Examples:
        @command(name="my_command")
        def cmd():
            pass

        @command(name="my_command", aliases=["mc", "mycmd"])
        def cmd():
            pass
    """

    def decorator(fn: Callable[..., Any]) -> Command:
        original_fn = fn

        if asyncio.iscoroutinefunction(fn):

            @functools.wraps(fn)
            def sync_wrapper(*wrapper_args: Any, **wrapper_kwargs: Any) -> Any:
                return asyncio.run(original_fn(*wrapper_args, **wrapper_kwargs))

            fn = sync_wrapper

        command_decorator = click.command(name=name, cls=Command, **kwargs)
        cmd = command_decorator(fn)
        cmd.aliases = aliases or []
        return cmd

    return decorator
