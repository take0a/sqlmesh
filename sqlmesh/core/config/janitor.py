from __future__ import annotations


from sqlmesh.core.config.base import BaseConfig


class JanitorConfig(BaseConfig):
    """The configuration for the janitor.
    管理人のための設定。

    Args:
        warn_on_delete_failure: Whether to warn instead of erroring if the janitor fails to delete the expired environment schema / views.
            管理人が期限切れの環境スキーマ/ビューの削除に失敗した場合、エラーではなく警告を出すかどうか。
    """

    warn_on_delete_failure: bool = False
