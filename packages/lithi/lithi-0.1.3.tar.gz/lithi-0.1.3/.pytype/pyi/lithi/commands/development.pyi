# (generated with --quick)

import argparse
import dataclasses
import lithi.core.cli
import lithi.core.logger
from typing import Callable, ClassVar, TypeVar, overload

Argument: type[lithi.core.cli.Argument]
Command: type[lithi.core.cli.Command]
logger: lithi.core.logger._GlobalLoggerProxy

_T = TypeVar('_T')

@dataclasses.dataclass
class Development(lithi.core.cli.Command):
    name: ClassVar[str]
    args: ClassVar[list[lithi.core.cli.Argument]]
    __doc__: str
    def __init__(self) -> None: ...
    def exec(self, _: argparse.Namespace) -> None: ...

@overload
def dataclass(cls: None, /) -> Callable[[type[_T]], type[_T]]: ...
@overload
def dataclass(cls: type[_T], /) -> type[_T]: ...
@overload
def dataclass(*, init: bool = ..., repr: bool = ..., eq: bool = ..., order: bool = ..., unsafe_hash: bool = ..., frozen: bool = ..., match_args: bool = ..., kw_only: bool = ..., slots: bool = ...) -> Callable[[type[_T]], type[_T]]: ...
