# (generated with --quick)

import lithi.core.config
from typing import Any, Optional

BaseModel: Any
ConfigSettings: type[lithi.core.config.ConfigSettings]
Field: Any

class DefaultConfig(Any):
    __doc__: str
    session_name: Optional[str]

class SessionConfig(Any):
    __doc__: str
    config: Any
    target: str

class Settings(lithi.core.config.ConfigSettings):
    __doc__: str
    default: DefaultConfig
    sessions: dict[str, SessionConfig]
