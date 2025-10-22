from __future__ import annotations

from sqlmesh.core.config.base import BaseConfig


class UIConfig(BaseConfig):
    """The UI configuration for SQLMesh.
    SQLMesh の UI 構成。

    Args:
        format_on_save: Whether to format the SQL code on save or not.
            保存時に SQL コードをフォーマットするかどうか。
    """

    format_on_save: bool = True
