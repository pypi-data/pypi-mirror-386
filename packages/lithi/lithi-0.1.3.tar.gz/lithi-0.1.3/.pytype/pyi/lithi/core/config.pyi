# (generated with --quick)

import json
import lithi.core.logger
import pathlib
from typing import Any, Generic, Optional, TypeVar, Union

BaseSettings: Any
Path: type[pathlib.Path]
_app_name: Optional[str]
logger: lithi.core.logger._GlobalLoggerProxy
xdg_cache_home: Any
xdg_config_home: Any

_T = TypeVar('_T', bound=Any)

class ConfigManager(Generic[_T]):
    _SETTINGS_FILE: str
    __doc__: str
    _path: Optional[pathlib.Path]
    _settings: Optional[_T]
    _settings_cls: Optional[type[_T]]
    @classmethod
    def init(cls, settings_cls: type[_T], path: Union[str, pathlib.Path]) -> None: ...
    @classmethod
    def load(cls, reload: bool = ...) -> _T: ...
    @classmethod
    def save(cls) -> None: ...

class ConfigSettings(Any):
    __doc__: str
    model_config: dict[str, str]

def _save_config_file(file: pathlib.Path, data: dict[str, Any]) -> None: ...
def get_cache_dirpath() -> pathlib.Path: ...
def get_config_dirpath() -> pathlib.Path: ...
def get_config_name() -> str: ...
def set_app_name(name: str) -> None: ...
