"""The main application."""

import argparse
import logging
import sys

import lithi.implementation

from . import __version__, commands
from .bizlog.brand import get_logo, get_name
from .bizlog.settings import Settings
from .core.cli import Cli
from .core.config import (
    ConfigManager,
    get_cache_dirpath,
    get_config_dirpath,
    get_config_name,
    set_app_name,
)
from .core.logger import Logger, logger
from .interface.target import TargetFactory


def on_cli_init(_: Cli, args: argparse.Namespace) -> None:
    """Perform custom initialisation for the command line init."""
    if args.verbose:
        logger.setLevel(logging.WARNING)
    else:
        logger.setLevel(logging.ERROR)


def on_cli_no_command(cli: Cli, args: argparse.Namespace) -> None:
    """Handle the default behavior when no command is given."""
    if args.version:
        print(f"{get_name()} {__version__}")
        sys.exit(0)
    else:
        cli.print_help()


def app() -> None:
    """Run the main application."""
    try:
        set_app_name(get_name())
        Logger.get(
            name=get_config_name(),
            level=logging.WARNING,
            directory=get_cache_dirpath(),
        )
        ConfigManager.init(settings_cls=Settings, path=get_config_dirpath())
        TargetFactory.init(targets_package=lithi.implementation)
        cli = Cli(
            name=get_name(),
            description=get_logo(),
            on_init=on_cli_init,
            on_no_command=on_cli_no_command,
        )

        cli.load_commands(commands)
        cli.exec()

    except KeyboardInterrupt:
        print("\nOperation interrupted by user.")
        sys.exit(1)


if __name__ == "__main__":
    app()
