# (generated with --quick)

import argparse
import dataclasses
import lithi.bizlog.settings
import lithi.core.cli
import lithi.core.config
import lithi.interface.target
import time
from typing import Callable, ClassVar, TypeVar, overload

Argument: type[lithi.core.cli.Argument]
Command: type[lithi.core.cli.Command]
ConfigManager: type[lithi.core.config.ConfigManager]
MemoryArea: type[lithi.interface.target.MemoryArea]
Settings: type[lithi.bizlog.settings.Settings]
TargetFactory: type[lithi.interface.target.TargetFactory]

_T = TypeVar('_T')

@dataclasses.dataclass
class MemoryCommand(lithi.core.cli.Command):
    name: ClassVar[str]
    args: ClassVar[list[lithi.core.cli.Argument]]
    __doc__: str
    def __init__(self) -> None: ...
    def exec(self, args: argparse.Namespace) -> None: ...

@overload
def dataclass(cls: None, /) -> Callable[[type[_T]], type[_T]]: ...
@overload
def dataclass(cls: type[_T], /) -> type[_T]: ...
@overload
def dataclass(*, init: bool = ..., repr: bool = ..., eq: bool = ..., order: bool = ..., unsafe_hash: bool = ..., frozen: bool = ..., match_args: bool = ..., kw_only: bool = ..., slots: bool = ...) -> Callable[[type[_T]], type[_T]]: ...
