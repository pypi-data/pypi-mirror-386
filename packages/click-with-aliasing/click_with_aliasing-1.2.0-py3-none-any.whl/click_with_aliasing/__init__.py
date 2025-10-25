"""This module is the entry point for the package."""

from .argument import argument
from .command import command
from .group import group
from .option import option
from .rule import rule

__all__ = [
    "argument",
    "command",
    "group",
    "option",
    "rule",
]
