from __future__ import annotations

from sqlmesh.core.config.base import BaseConfig
from sqlmesh.utils.errors import ConfigError
from sqlmesh.utils.pydantic import field_validator


class RunConfig(BaseConfig):
    """A configuration for `sqlmesh run` command.
    `sqlmesh run` コマンドの構成。

    Args:
        environment_check_interval: Interval in seconds between environment checks.
            環境チェックの間隔（秒）。
        environment_check_max_wait: Maximum time in seconds to wait for environment to be ready.
            環境の準備ができるまで待機する最大時間（秒）。
    """

    environment_check_interval: int = 30
    environment_check_max_wait: int = 6 * 60 * 60  # 6 hours by default

    @field_validator("environment_check_interval", "environment_check_max_wait", mode="after")
    @classmethod
    def _validate_positive_int(cls, v: int) -> int:
        if v <= 0:
            raise ConfigError(f"Value must be a positive integer, got {v}")
        return v
