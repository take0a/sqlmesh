from __future__ import annotations

from enum import Enum

from sqlmesh.core.config.base import BaseConfig


class AutoCategorizationMode(Enum):
    FULL = "full"
    """Full-auto mode in which the categorizer falls back to the most conservative choice (breaking).
    分類器が最も保守的な選択 (ブレーク) に戻るフルオート モード。"""

    SEMI = "semi"
    """Semi-auto mode in which a user is promted to provide a category in case when the categorizer
    failed to determine it automatically.
    分類器が自動的に分類を決定できなかった場合に、ユーザーにカテゴリを指定するよう求める半自動モード。
    """

    OFF = "off"
    """Disables automatic categorization.
    自動分類を無効にします。"""


class CategorizerConfig(BaseConfig):
    """Configuration for the automatic categorizer of snapshot changes.
    スナップショットの変更の自動分類機能の構成。

    Args:
        external: the auto categorization mode for External models.
            外部モデルの自動分類モード。
        python: the auto categorization mode for Python models.
            Python モデルの自動分類モード。
        sql: the auto categorization mode for SQL models.
            SQL モデルの自動分類モード。
        seed: the auto categorization mode for Seed models.
            シード モデルの自動分類モード。
    """

    external: AutoCategorizationMode = AutoCategorizationMode.FULL
    python: AutoCategorizationMode = AutoCategorizationMode.FULL
    sql: AutoCategorizationMode = AutoCategorizationMode.FULL
    seed: AutoCategorizationMode = AutoCategorizationMode.FULL

    @classmethod
    def all_off(cls) -> CategorizerConfig:
        return cls(
            external=AutoCategorizationMode.OFF,
            python=AutoCategorizationMode.OFF,
            sql=AutoCategorizationMode.OFF,
            seed=AutoCategorizationMode.OFF,
        )

    @classmethod
    def all_semi(cls) -> CategorizerConfig:
        return cls(
            external=AutoCategorizationMode.SEMI,
            python=AutoCategorizationMode.SEMI,
            sql=AutoCategorizationMode.SEMI,
            seed=AutoCategorizationMode.SEMI,
        )

    @classmethod
    def all_full(cls) -> CategorizerConfig:
        return cls(
            external=AutoCategorizationMode.FULL,
            python=AutoCategorizationMode.FULL,
            sql=AutoCategorizationMode.FULL,
            seed=AutoCategorizationMode.FULL,
        )
