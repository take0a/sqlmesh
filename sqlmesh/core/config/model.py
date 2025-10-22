from __future__ import annotations

import typing as t

from sqlglot import exp
from sqlmesh.core.dialect import parse_one, extract_func_call
from sqlmesh.core.config.base import BaseConfig
from sqlmesh.core.model.kind import (
    ModelKind,
    OnDestructiveChange,
    model_kind_validator,
    on_destructive_change_validator,
    on_additive_change_validator,
    OnAdditiveChange,
)
from sqlmesh.core.model.meta import FunctionCall
from sqlmesh.core.node import IntervalUnit
from sqlmesh.utils.date import TimeLike
from sqlmesh.utils.pydantic import field_validator


class ModelDefaultsConfig(BaseConfig):
    """A config object for default values applied to model definitions.
    モデル定義に適用されるデフォルト値の構成オブジェクト。

    Args:
        kind: The model kind.
        dialect: The SQL dialect that the model's query is written in.
            モデルのクエリが記述されている SQL 方言。
        cron: A cron string specifying how often the model should be refreshed, leveraging the
            [croniter](https://github.com/kiorky/croniter) library.
            モデルを更新する頻度を指定する cron 文字列。
        owner: The owner of the model.
        start: The earliest date that the model will be backfilled for. If this is None,
            then the date is inferred by taking the most recent start date of its ancestors.
            The start date can be a static datetime or a relative datetime like "1 year ago"
            モデルがバックフィルされる最も古い日付。None の場合、その祖先の最新の開始日に基づいて日付が推測されます。
            開始日は、静的な日時、または「1年前」のような相対的な日時で指定できます。
        table_format: The table format used to manage the physical table files defined by `storage_format`, only applicable in certain engines.
            `storage_format` で定義された物理テーブルファイルを管理するために使用されるテーブル形式。特定のエンジンにのみ適用されます。
            (eg, 'iceberg', 'delta', 'hudi')
        storage_format: The storage format used to store the physical table, only applicable in certain engines.
            物理テーブルを保存するために使用されるストレージ形式。特定のエンジンにのみ適用されます。
            (eg. 'parquet', 'orc')
        on_destructive_change: What should happen when a forward-only model requires a destructive schema change.
            前方のみのモデルで破壊的なスキーマ変更が必要な場合、何が起こるか。
        on_additive_change: What should happen when a forward-only model requires an additive schema change.
            フォワードのみのモデルで追加のスキーマ変更が必要になったときに何が起こるか。
        physical_properties: A key-value mapping of arbitrary properties that are applied to the model table / view in the physical layer.
            物理層のモデル テーブル/ビューに適用される任意のプロパティのキーと値のマッピング。
        virtual_properties: A key-value mapping of arbitrary properties that are applied to the model view in the virtual layer.
            仮想レイヤーのモデル ビューに適用される任意のプロパティのキーと値のマッピング。
        session_properties: A key-value mapping of properties specific to the target engine that are applied to the engine session.
            エンジン セッションに適用される、ターゲット エンジン固有のプロパティのキーと値のマッピング。
        audits: The audits to be applied globally to all models in the project.
            プロジェクト内のすべてのモデルにグローバルに適用される監査。
        optimize_query: Whether the SQL models should be optimized.
            SQL モデルを最適化する必要があるかどうか。
        allow_partials: Whether the models can process partial (incomplete) data intervals.
            モデルが部分的な（不完全な）データ間隔を処理できるかどうか。
        enabled: Whether the models are enabled.
            モデルが有効かどうか。
        interval_unit: The temporal granularity of the models data intervals. By default computed from cron.
            モデルデータ間隔の時間粒度。デフォルトではcronから計算されます。
        batch_concurrency: The maximum number of batches that can run concurrently for an incremental model.
            増分モデルで同時に実行できるバッチの最大数。
        pre_statements: The list of SQL statements that get executed before a model runs.
            モデルが実行される前に実行される SQL ステートメントのリスト。
        post_statements: The list of SQL statements that get executed before a model runs.
            モデルが実行される前に実行される SQL ステートメントのリスト。
        on_virtual_update: The list of SQL statements to be executed after the virtual update.
            仮想更新後に実行される SQL ステートメントのリスト。

    """

    kind: t.Optional[ModelKind] = None
    dialect: t.Optional[str] = None
    cron: t.Optional[str] = None
    owner: t.Optional[str] = None
    start: t.Optional[TimeLike] = None
    table_format: t.Optional[str] = None
    storage_format: t.Optional[str] = None
    on_destructive_change: t.Optional[OnDestructiveChange] = None
    on_additive_change: t.Optional[OnAdditiveChange] = None
    physical_properties: t.Optional[t.Dict[str, t.Any]] = None
    virtual_properties: t.Optional[t.Dict[str, t.Any]] = None
    session_properties: t.Optional[t.Dict[str, t.Any]] = None
    audits: t.Optional[t.List[FunctionCall]] = None
    optimize_query: t.Optional[t.Union[str, bool]] = None
    allow_partials: t.Optional[t.Union[str, bool]] = None
    interval_unit: t.Optional[t.Union[str, IntervalUnit]] = None
    enabled: t.Optional[t.Union[str, bool]] = None
    formatting: t.Optional[t.Union[str, bool]] = None
    batch_concurrency: t.Optional[int] = None
    pre_statements: t.Optional[t.List[t.Union[str, exp.Expression]]] = None
    post_statements: t.Optional[t.List[t.Union[str, exp.Expression]]] = None
    on_virtual_update: t.Optional[t.List[t.Union[str, exp.Expression]]] = None

    _model_kind_validator = model_kind_validator
    _on_destructive_change_validator = on_destructive_change_validator
    _on_additive_change_validator = on_additive_change_validator

    @field_validator("audits", mode="before")
    def _audits_validator(cls, v: t.Any) -> t.Any:
        if isinstance(v, list):
            return [extract_func_call(parse_one(audit)) for audit in v]

        return v
