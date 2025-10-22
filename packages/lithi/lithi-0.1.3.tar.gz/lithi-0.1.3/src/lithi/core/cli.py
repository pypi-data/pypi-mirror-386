"""Module for command line argument operations."""

from __future__ import annotations

import argparse
import importlib
import inspect
import pkgutil
import types
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any, ClassVar

from .logger import logger


class ArgumentType(str, Enum):
    """Supported argument types."""

    BOOL = "bool"
    INT = "int"
    FLOAT = "float"
    STRING = "string"
    CHOICE = "choice"


@dataclass(frozen=True, kw_only=True)
class Argument:
    """A CLI argument definition with automatic type inference."""

    name: str
    short: str | None = None
    help: str | None = None
    default: Any = None
    required: bool = False
    choices: list[Any] | None = None
    metavar: str | None = None

    def __post_init__(self) -> None:
        """Validate argument configuration."""
        if self.required and self.default is not None:
            raise ValueError(
                f"Argument '{self.name}' cannot be both"
                " required and have a default"
            )

    @property
    def dest(self) -> str:
        """Get the destination variable name."""
        return self.name.replace("-", "_")

    @property
    def arg_type(self) -> ArgumentType:
        """Infer the argument type from the default value."""
        if self.choices:
            return ArgumentType.CHOICE

        if self.default is None:
            return ArgumentType.STRING

        if isinstance(self.default, bool):
            return ArgumentType.BOOL
        if isinstance(self.default, int):
            return ArgumentType.INT
        if isinstance(self.default, float):
            return ArgumentType.FLOAT

        return ArgumentType.STRING

    def register(self, parser: argparse.ArgumentParser) -> None:
        """Register this argument with an ArgumentParser."""
        names = self._build_argument_names()
        kwargs = self._build_argument_kwargs()
        parser.add_argument(*names, **kwargs)

    def _build_argument_names(self) -> list[str]:
        """Build the argument name list (e.g., ['-v', '--verbose'])."""
        names = [f"--{self.name}"]
        if self.short:
            names.insert(0, f"-{self.short}")
        return names

    def _build_argument_kwargs(self) -> dict[str, Any]:
        """Build kwargs dict for argparse.add_argument()."""
        kwargs: dict[str, Any] = {
            "dest": self.dest,
            "help": self._build_help_text(),
        }

        # Add type-specific configuration
        match self.arg_type:
            case ArgumentType.BOOL:
                kwargs["action"] = (
                    "store_false" if self.default else "store_true"
                )
                kwargs["default"] = self.default

            case ArgumentType.INT:
                kwargs["type"] = int
                self._add_default_and_required(kwargs)

            case ArgumentType.FLOAT:
                kwargs["type"] = float
                self._add_default_and_required(kwargs)

            case ArgumentType.CHOICE:
                kwargs["choices"] = self.choices
                self._add_default_and_required(kwargs)

            case ArgumentType.STRING:
                kwargs["type"] = str
                self._add_default_and_required(kwargs)

        if self.metavar:
            kwargs["metavar"] = self.metavar

        return kwargs

    def _add_default_and_required(self, kwargs: dict[str, Any]) -> None:
        """Add default and required to kwargs (helper for non-bool types)."""
        kwargs["default"] = self.default
        if self.required:
            kwargs["required"] = True

    def _build_help_text(self) -> str:
        """Build help text with default value."""
        if not self.help:
            return ""

        help_text = self.help

        if self.arg_type != ArgumentType.BOOL and self.default is not None:
            help_text += f" (default: {self.default})"

        return help_text


class Command(ABC):
    """Base class for CLI commands with automatic registration."""

    name: ClassVar[str]
    args: ClassVar[list[Argument]] = []

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Validate and auto-configure subclass."""
        super().__init_subclass__(**kwargs)

        # Auto-generate name from class name if not provided
        if not hasattr(cls, "name") or not cls.name:
            cls.name = cls.__name__.lower().replace("command", "")

        # Initialize args if not defined
        if not hasattr(cls, "args"):
            cls.args = []

    @abstractmethod
    def exec(self, args: argparse.Namespace) -> None:
        """Execute the command with parsed arguments."""
        raise NotImplementedError


class Cli:
    """Command line argument manager with automatic discovery."""

    def __init__(
        self,
        name: str = "app",
        description: str | None = None,
        on_init: Callable[[Cli, argparse.Namespace], None] | None = None,
        on_no_command: Callable[[Cli, argparse.Namespace], None] | None = None,
    ) -> None:
        """Initialize the CLI manager."""
        self.name = name
        self.on_init = on_init
        self.on_no_command = on_no_command
        self.commands: dict[str, Command] = {}

        self.parser = argparse.ArgumentParser(
            prog=name,
            description=description,
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

    def register(self, command: Command) -> None:
        """Register a command."""
        logger.info("Registered command: %s", command.name)
        self.commands[command.name] = command

    def load_commands(self, package: types.ModuleType) -> None:
        """Recursively register all Command subclasses from a package."""
        for module_info in pkgutil.walk_packages(
            path=package.__path__,
            prefix=f"{package.__name__}.",
        ):
            module_name = module_info.name

            try:
                module = importlib.import_module(module_name)

                # Scan for Command subclasses
                for _, cls in inspect.getmembers(module, inspect.isclass):
                    if issubclass(cls, Command) and cls is not Command:
                        # Only register if defined in this module
                        if cls.__module__ == module_name:
                            self.register(cls())

            except ImportError as e:
                logger.warning("Failed to import %s: %s", module_name, e)

    def exec(self) -> None:
        """Parse arguments and execute the appropriate command."""
        # Add global arguments
        self.parser.add_argument(
            "--version", action="store_true", help="Get version."
        )

        self.parser.add_argument(
            "-v",
            "--verbose",
            action="store_true",
            help="Enable verbose output",
        )

        # Add subcommands
        if self.commands:
            subparsers = self.parser.add_subparsers(
                dest="command",
                title="commands",
                description="Available commands",
            )

            for cmd in self.commands.values():
                doc_string = (cmd.__doc__ or "").strip()
                cmd_parser = subparsers.add_parser(
                    cmd.name,
                    help=doc_string,
                    formatter_class=argparse.RawDescriptionHelpFormatter,
                )

                for arg in cmd.args:
                    arg.register(cmd_parser)

        # Parse arguments
        args = self.parser.parse_args()

        # Run init callback
        if self.on_init:
            self.on_init(self, args)

        # Execute command or show help
        if args.command:
            cmd = self.commands[args.command]
            cmd.exec(args)
        else:
            if self.on_no_command:
                self.on_no_command(self, args)
            else:
                self.print_help()

    def print_help(self) -> None:
        """Print the help message."""
        self.parser.print_help()
