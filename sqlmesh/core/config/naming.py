from __future__ import annotations

from sqlmesh.core.config.base import BaseConfig


class NameInferenceConfig(BaseConfig):
    """Configuration for name inference of models from directory structure.
    ディレクトリ構造からモデルの名前を推論するための構成。

    Args:
        infer_names: A flag indicating whether name inference is enabled.
            名前の推論が有効かどうかを示すフラグ。

    """

    infer_names: bool = False
