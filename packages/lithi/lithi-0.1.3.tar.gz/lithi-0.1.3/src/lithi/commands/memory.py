"""Memory command."""

import argparse
import time
from dataclasses import dataclass
from typing import ClassVar

from lithi.bizlog.settings import Settings
from lithi.core.cli import Argument, Command
from lithi.core.config import ConfigManager
from lithi.interface.target import MemoryArea, TargetFactory


@dataclass
class MemoryCommand(Command):
    """Read memory given the address and the size."""

    name: ClassVar[str] = "mem"

    args: ClassVar[list[Argument]] = [
        Argument(
            name="address", short="a", help="Address in hex", default="0"
        ),
        Argument(
            name="size",
            short="s",
            help="How many bytes to read",
            default=4,
        ),
        Argument(
            name="loop",
            short="l",
            help="Run in a loop",
            default=False,
        ),
    ]

    def exec(self, args: argparse.Namespace) -> None:
        """Execute the command."""
        # Load the default target
        settings: Settings = ConfigManager.load()

        if settings.default.session_name is None:
            raise ValueError("No default session name configured")

        session = settings.sessions[settings.default.session_name]
        target = TargetFactory.create(session.target, session.config)

        # Use the target
        target.connect()
        memory = MemoryArea(address=int(args.address, 0), size=args.size)
        repeat_measurement = True
        while repeat_measurement:
            # Read memory
            if target.is_connected():
                value = target.read(memory)
                print(f"[{session.target}] {memory} = {memory.format(value)}")
            if args.loop:
                time.sleep(0.1)
            repeat_measurement = args.loop
