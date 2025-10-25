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

    def get_help_option(self, ctx: click.Context) -> click.Option | None:
        """
        Get the help option with -h alias support.

        This method adds -h as an alias for --help unless the command
        uses -h for another purpose.

        Args:
            ctx (click.Context):
                The Click context.

        Returns:
            click.Option | None:
                The help option with -h alias, or None if help is disabled.
        """
        help_option_names = self.get_help_option_names(ctx)
        if not help_option_names:
            return None

        # Check if this command uses -h for another purpose
        has_h_conflict = False
        for param in self.params:
            if hasattr(param, "opts") and "-h" in param.opts:
                has_h_conflict = True
                break

        # Add -h to help option names if no conflict
        if not has_h_conflict and "-h" not in help_option_names:
            help_option_names = ["-h"] + list(help_option_names)

        return click.Option(
            help_option_names,
            is_flag=True,
            is_eager=True,
            expose_value=False,
            callback=self._show_help_callback,
            help="Show this message and exit.",
        )

    @staticmethod
    def _show_help_callback(
        ctx: click.Context, param: click.Parameter, value: bool
    ) -> None:
        """
        Callback to show help message.

        Args:
            ctx (click.Context):
                The Click context.
            param (click.Parameter):
                The parameter that triggered the callback.
            value (bool):
                The value of the parameter.
        """
        if value and not ctx.resilient_parsing:
            click.echo(ctx.get_help(), color=ctx.color)
            ctx.exit()


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
