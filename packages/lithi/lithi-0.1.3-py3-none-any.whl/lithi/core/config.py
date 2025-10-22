"""Support for configuration operations."""

import json
from pathlib import Path
from typing import Any, Generic, TypeVar, cast

from pydantic_settings import BaseSettings
from xdg_base_dirs import xdg_cache_home, xdg_config_home

from .logger import logger

_app_name: str | None = None


def set_app_name(name: str) -> None:
    """Set the configuration name."""
    global _app_name
    _app_name = name


def get_config_name() -> str:
    """
    Get the configuration name.

    Returns:
        str: The configuration name.
    """
    if not _app_name:
        raise RuntimeError("Config name is not set")
    return _app_name


def get_config_dirpath() -> Path:
    """
    Get the configuration directory path.

    This path is based on the XDG configuration home.

    Returns:
        Path: The absolute path to the configuration directory.
    """
    return Path(xdg_config_home()) / get_config_name()


def get_cache_dirpath() -> Path:
    """
    Get the cache directory path.

    This path is based on the XDG cache home.

    Returns:
        Path: The absolute path to the cache directory.
    """
    return Path(xdg_cache_home()) / get_config_name()


def _save_config_file(file: Path, data: dict[str, Any]) -> None:
    """Save configuration data to file."""
    if file.suffix == ".json":
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(
            json.dumps(data, indent=4, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    else:
        raise ValueError(f"Unsupported config format: {file.suffix}")


class ConfigSettings(BaseSettings):
    """Base configuration settings with file and environment support."""

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


_T = TypeVar("_T", bound=BaseSettings)


class ConfigManager(Generic[_T]):
    """Config manager with reload and save support (singleton pattern)."""

    _settings: _T | None = None
    _path: Path | None = None
    _settings_cls: type[_T] | None = None
    _SETTINGS_FILE: str = "settings.json"

    @classmethod
    def init(cls, settings_cls: type[_T], path: Path | str) -> None:
        """Initialize the config manager with settings class and path."""
        cls._settings_cls = settings_cls
        cls._path = Path(path) if isinstance(path, str) else path
        cls._settings = None
        logger.info(f"Initialized config manager at {cls._path}")

    @classmethod
    def load(cls, reload: bool = False) -> _T:
        """Load configuration from file and environment."""
        if cls._settings_cls is None or cls._path is None:
            raise RuntimeError("Config not initialized. Call init() first.")

        # Type narrowing for pytype
        # after the check above, these can't be None
        settings_cls = cast(type[_T], cls._settings_cls)  # type: ignore[redundant-cast]
        path = cast(Path, cls._path)  # type: ignore[redundant-cast]

        if reload or cls._settings is None:
            filepath: Path = path / cls._SETTINGS_FILE
            logger.info("Loading config from %s", filepath)

            if filepath.exists():
                data = json.loads(filepath.read_text(encoding="utf-8"))
                cls._settings = settings_cls.model_validate(data)
            else:
                # Let BaseSettings handle environment variables only
                cls._settings = settings_cls()
                logger.info(
                    "No config file found,"
                    " using defaults and environment variables."
                )

        return cls._settings

    @classmethod
    def save(cls) -> None:
        """Save current configuration to file."""
        if cls._settings_cls is None or cls._path is None:
            raise RuntimeError("Config not initialized. Call init() first.")

        if cls._settings is None:
            raise RuntimeError("Config not loaded yet. Call load() first.")

        # Type narrowing for pytype
        # after the checks above, these can't be None
        settings = cast(_T, cls._settings)  # type: ignore[redundant-cast]
        path = cast(Path, cls._path)  # type: ignore[redundant-cast]

        data = settings.model_dump(exclude_none=True)
        filepath: Path = path / cls._SETTINGS_FILE
        _save_config_file(filepath, data)
        logger.info(f"Saved config to {filepath}")
