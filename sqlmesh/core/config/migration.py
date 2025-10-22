from __future__ import annotations

from sqlmesh.core.config.base import BaseConfig


class MigrationConfig(BaseConfig):
    """Configuration for the SQLMesh state migration.
    SQLMesh 状態移行の構成。

    Args:
        promoted_snapshots_only: If True, only snapshots that are part of at least one environment will be migrated.
            Otherwise, all snapshots will be migrated.
            True の場合、少なくとも 1 つの環境の一部であるスナップショットのみが移行されます。
            それ以外の場合は、すべてのスナップショットが移行されます。
    """

    promoted_snapshots_only: bool = True
