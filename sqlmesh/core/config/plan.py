from __future__ import annotations

import typing as t

from sqlmesh.core.config.base import BaseConfig
from sqlmesh.core.config.categorizer import CategorizerConfig


class PlanConfig(BaseConfig):
    """Configuration for a plan.
    プランの構成。

    Args:
        forward_only: Whether the plan should be forward-only.
            プランを前向きのみにするかどうか。
        auto_categorize_changes: Whether SQLMesh should attempt to automatically categorize model changes (breaking / non-breaking)
            during plan creation.
            SQLMesh がプラン作成中にモデルの変更 (破壊的 / 非破壊的) を自動的に分類するかどうか。
        include_unmodified: Whether to include unmodified models in the target development environment.
            変更されていないモデルをターゲット開発環境に含めるかどうか。
        enable_preview: Whether to enable preview for forward-only models in development environments.
            開発環境でフォワード専用モデルのプレビューを有効にするかどうか。
        no_diff: Hide text differences for changed models.
            変更されたモデルのテキストの差異を非表示にします。
        no_prompts: Whether to disable interactive prompts for the backfill time range.
            バックフィル時間範囲の対話型プロンプトを無効にするかどうか。
        auto_apply: Whether to automatically apply the new plan after creation.
            作成後に新しいプランを自動的に適用するかどうか。
        use_finalized_state: Whether to compare against the latest finalized environment state, or to use
            whatever state the target environment is currently in.
            最新の確定された環境状態と比較するか、またはターゲット環境の現在の状態を使用するかを指定します。
        always_recreate_environment: Whether to always recreate the target environment from the `create_from` environment.
            `create_from` 環境から常にターゲット環境を再作成するかどうか。
    """

    forward_only: bool = False
    auto_categorize_changes: CategorizerConfig = CategorizerConfig()
    include_unmodified: bool = False
    enable_preview: t.Optional[bool] = None
    no_diff: bool = False
    no_prompts: bool = True
    auto_apply: bool = False
    use_finalized_state: bool = False
    always_recreate_environment: bool = False
