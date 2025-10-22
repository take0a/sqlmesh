from __future__ import annotations

import pickle
import re
import typing as t
import zlib

from pydantic import Field
from pydantic.functional_validators import BeforeValidator
from sqlglot import exp
from sqlglot.helper import first
from sqlglot.optimizer.normalize_identifiers import normalize_identifiers

from sqlmesh.cicd.config import CICDBotConfig
from sqlmesh.core import constants as c
from sqlmesh.core.console import get_console
from sqlmesh.core.config.common import (
    EnvironmentSuffixTarget,
    TableNamingConvention,
    VirtualEnvironmentMode,
)
from sqlmesh.core.config.base import BaseConfig, UpdateStrategy
from sqlmesh.core.config.common import variables_validator, compile_regex_mapping
from sqlmesh.core.config.connection import (
    ConnectionConfig,
    DuckDBConnectionConfig,
    SerializableConnectionConfig,
    connection_config_validator,
)
from sqlmesh.core.config.format import FormatConfig
from sqlmesh.core.config.gateway import GatewayConfig
from sqlmesh.core.config.janitor import JanitorConfig
from sqlmesh.core.config.migration import MigrationConfig
from sqlmesh.core.config.model import ModelDefaultsConfig
from sqlmesh.core.config.naming import NameInferenceConfig as NameInferenceConfig
from sqlmesh.core.config.linter import LinterConfig as LinterConfig
from sqlmesh.core.config.plan import PlanConfig
from sqlmesh.core.config.run import RunConfig
from sqlmesh.core.config.dbt import DbtConfig
from sqlmesh.core.config.scheduler import (
    BuiltInSchedulerConfig,
    SchedulerConfig,
    scheduler_config_validator,
)
from sqlmesh.core.config.ui import UIConfig
from sqlmesh.core.loader import Loader, SqlMeshLoader
from sqlmesh.core.notification_target import NotificationTarget
from sqlmesh.core.user import User
from sqlmesh.utils.date import to_timestamp, now
from sqlmesh.utils.errors import ConfigError
from sqlmesh.utils.pydantic import model_validator


def validate_no_past_ttl(v: str) -> str:
    current_time = now()
    if to_timestamp(v, relative_base=current_time) < to_timestamp(current_time):
        raise ValueError(
            f"TTL '{v}' is in the past. Please specify a relative time in the future. Ex: `in 1 week` instead of `1 week`."
        )
    return v


def gateways_ensure_dict(value: t.Dict[str, t.Any]) -> t.Dict[str, t.Any]:
    try:
        if not isinstance(value, GatewayConfig):
            GatewayConfig.parse_obj(value)
        return {"": value}
    except Exception:
        # Normalize all gateway keys to lowercase for case-insensitive matching
        if isinstance(value, dict):
            return {k.lower(): v for k, v in value.items()}
        return value


def validate_regex_key_dict(value: t.Dict[str | re.Pattern, t.Any]) -> t.Dict[re.Pattern, t.Any]:
    return compile_regex_mapping(value)


if t.TYPE_CHECKING:
    from sqlmesh.core._typing import Self

    NoPastTTLString = str
    GatewayDict = t.Dict[str, GatewayConfig]
    RegexKeyDict = t.Dict[re.Pattern, str]
else:
    NoPastTTLString = t.Annotated[str, BeforeValidator(validate_no_past_ttl)]
    GatewayDict = t.Annotated[t.Dict[str, GatewayConfig], BeforeValidator(gateways_ensure_dict)]
    RegexKeyDict = t.Annotated[t.Dict[re.Pattern, str], BeforeValidator(validate_regex_key_dict)]


class Config(BaseConfig):
    """An object used by a Context to configure your SQLMesh project.
    SQLMesh プロジェクトを構成するためにコンテキストによって使用されるオブジェクト。

    Args:
        gateways: Supported gateways and their configurations. Key represents a unique name of a gateway.
            サポートされているゲートウェイとその構成。キーはゲートウェイの一意の名前を表します。
        default_connection: The default connection to use if one is not specified in a gateway.
            ゲートウェイで指定されていない場合に使用するデフォルトの接続。
        default_test_connection: The default connection to use for tests if one is not specified in a gateway.
            ゲートウェイで指定されていない場合にテストに使用するデフォルトの接続。
        default_scheduler: The default scheduler configuration to use if one is not specified in a gateway.
            ゲートウェイで指定されていない場合に使用するデフォルトのスケジューラ構成。
        default_gateway: The default gateway.
            デフォルトゲートウェイ。
        notification_targets: The notification targets to use.
            使用する通知ターゲット。
        project: The project name of this config. Used for multi-repo setups.
            この設定のプロジェクト名。マルチリポジトリ設定に使用されます。
        snapshot_ttl: The period of time that a model snapshot that is not a part of any environment should exist before being deleted.
            どの環境にも属さないモデル スナップショットが削除されるまでに存在する期間。
        environment_ttl: The period of time that a development environment should exist before being deleted.
            開発環境が削除されるまでに存在する期間。
        ignore_patterns: Files that match glob patterns specified in this list are ignored when scanning the project folder.
            このリストで指定された glob パターンに一致するファイルは、プロジェクト フォルダーをスキャンするときに無視されます。
        time_column_format: The default format to use for all model time columns. Defaults to %Y-%m-%d.
            This time format uses python format codes. https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes.
            すべてのモデル時間列に使用するデフォルトの形式です。デフォルトは %Y-%m-%d です。
            この時間形式では Python のフォーマットコードが使用されます。
        users: A list of users that can be used for approvals/notifications.
            承認/通知に使用できるユーザーのリスト。
        username: Name of a single user who should receive approvals/notification, instead of all users in the `users` list.
            `users` リスト内のすべてのユーザーではなく、承認/通知を受け取る単一のユーザーの名前。
        pinned_environments: A list of development environment names that should not be deleted by the janitor task.
            janitor タスクによって削除されない開発環境名のリスト。
        loader: Loader class used for loading project files.
            プロジェクト ファイルを読み込むために使用される Loader クラス。
        loader_kwargs: Key-value arguments to pass to the loader instance.
            ローダー インスタンスに渡すキー値引数。
        env_vars: A dictionary of environmental variable names and values.
            環境変数の名前と値の辞書。
        model_defaults: Default values for model definitions.
            モデル定義のデフォルト値。
        physical_schema_mapping: A mapping from regular expressions to names of schemas in which physical tables for corresponding models will be placed.
            正規表現から、対応するモデルの物理テーブルが配置されるスキーマの名前へのマッピング。
        environment_suffix_target: Indicates whether to append the environment name to the schema or table name.
            スキーマ名またはテーブル名に環境名を追加するかどうかを示します。
        physical_table_naming_convention: Indicates how tables should be named at the physical layer
            物理層でテーブルに名前を付ける方法を示します
        virtual_environment_mode: Indicates how environments should be handled.
            環境をどのように処理するかを示します。
        gateway_managed_virtual_layer: Whether the models' views in the virtual layer are created by the model-specific gateway rather than the default gateway.
            仮想レイヤー内のモデルのビューが、デフォルト ゲートウェイではなくモデル固有のゲートウェイによって作成されるかどうか。
        infer_python_dependencies: Whether to statically analyze Python code to automatically infer Python package requirements.
            Python コードを静的に分析して、Python パッケージの要件を自動的に推測するかどうか。
        environment_catalog_mapping: A mapping from regular expressions to catalog names. The catalog name is used to determine the target catalog for a given environment.
            正規表現からカタログ名へのマッピング。カタログ名は、特定の環境におけるターゲットカタログを決定するために使用されます。
        default_target_environment: The name of the environment that will be the default target for the `sqlmesh plan` and `sqlmesh run` commands.
            `sqlmesh plan` コマンドと `sqlmesh run` コマンドのデフォルトのターゲットとなる環境の名前。
        log_limit: The default number of logs to keep.
            保存するログのデフォルトの数。
        format: The formatting options for SQL code.
            SQL コードの書式設定オプション。
        ui: The UI configuration for SQLMesh.
            SQLMesh の UI 構成。
        plan: The plan configuration.
            プランの構成。
        migration: The migration configuration.
            移行構成。
        variables: A dictionary of variables that can be used in models / macros.
            モデル/マクロで使用できる変数の辞書。
        disable_anonymized_analytics: Whether to disable the anonymized analytics collection.
            匿名化された分析収集を無効にするかどうか。
        before_all: SQL statements or macros to be executed at the start of the `sqlmesh plan` and `sqlmesh run` commands.
            `sqlmesh plan` および `sqlmesh run` コマンドの開始時に実行される SQL ステートメントまたはマクロ。
        after_all: SQL statements or macros to be executed at the end of the `sqlmesh plan` and `sqlmesh run` commands.
            `sqlmesh plan` コマンドと `sqlmesh run` コマンドの最後に実行される SQL ステートメントまたはマクロ。
        cache_dir: The directory to store the SQLMesh cache. Defaults to .cache in the project folder.
            SQLMesh キャッシュを保存するディレクトリ。デフォルトはプロジェクト フォルダ内の .cache です。
    """

    gateways: GatewayDict = {"": GatewayConfig()}
    default_connection: t.Optional[SerializableConnectionConfig] = None
    default_test_connection_: t.Optional[SerializableConnectionConfig] = Field(
        default=None, alias="default_test_connection"
    )
    default_scheduler: SchedulerConfig = BuiltInSchedulerConfig()
    default_gateway: str = ""
    notification_targets: t.List[NotificationTarget] = []
    project: str = ""
    snapshot_ttl: NoPastTTLString = c.DEFAULT_SNAPSHOT_TTL
    environment_ttl: t.Optional[NoPastTTLString] = c.DEFAULT_ENVIRONMENT_TTL
    ignore_patterns: t.List[str] = c.IGNORE_PATTERNS
    time_column_format: str = c.DEFAULT_TIME_COLUMN_FORMAT
    users: t.List[User] = []
    model_defaults: ModelDefaultsConfig = ModelDefaultsConfig()
    pinned_environments: t.Set[str] = set()
    loader: t.Type[Loader] = SqlMeshLoader
    loader_kwargs: t.Dict[str, t.Any] = {}
    env_vars: t.Dict[str, str] = {}
    username: str = ""
    physical_schema_mapping: RegexKeyDict = {}
    environment_suffix_target: EnvironmentSuffixTarget = EnvironmentSuffixTarget.default
    physical_table_naming_convention: TableNamingConvention = TableNamingConvention.default
    virtual_environment_mode: VirtualEnvironmentMode = VirtualEnvironmentMode.default
    gateway_managed_virtual_layer: bool = False
    infer_python_dependencies: bool = True
    environment_catalog_mapping: RegexKeyDict = {}
    default_target_environment: str = c.PROD
    log_limit: int = c.DEFAULT_LOG_LIMIT
    cicd_bot: t.Optional[CICDBotConfig] = None
    run: RunConfig = RunConfig()
    format: FormatConfig = FormatConfig()
    ui: UIConfig = UIConfig()
    plan: PlanConfig = PlanConfig()
    migration: MigrationConfig = MigrationConfig()
    model_naming: NameInferenceConfig = NameInferenceConfig()
    variables: t.Dict[str, t.Any] = {}
    disable_anonymized_analytics: bool = False
    before_all: t.Optional[t.List[str]] = None
    after_all: t.Optional[t.List[str]] = None
    linter: LinterConfig = LinterConfig()
    janitor: JanitorConfig = JanitorConfig()
    cache_dir: t.Optional[str] = None
    dbt: t.Optional[DbtConfig] = None

    _FIELD_UPDATE_STRATEGY: t.ClassVar[t.Dict[str, UpdateStrategy]] = {
        "gateways": UpdateStrategy.NESTED_UPDATE,
        "notification_targets": UpdateStrategy.EXTEND,
        "ignore_patterns": UpdateStrategy.EXTEND,
        "users": UpdateStrategy.EXTEND,
        "model_defaults": UpdateStrategy.NESTED_UPDATE,
        "auto_categorize_changes": UpdateStrategy.NESTED_UPDATE,
        "pinned_environments": UpdateStrategy.EXTEND,
        "physical_schema_override": UpdateStrategy.KEY_UPDATE,
        "run": UpdateStrategy.NESTED_UPDATE,
        "format": UpdateStrategy.NESTED_UPDATE,
        "ui": UpdateStrategy.NESTED_UPDATE,
        "loader_kwargs": UpdateStrategy.KEY_UPDATE,
        "plan": UpdateStrategy.NESTED_UPDATE,
        "before_all": UpdateStrategy.EXTEND,
        "after_all": UpdateStrategy.EXTEND,
        "linter": UpdateStrategy.NESTED_UPDATE,
        "dbt": UpdateStrategy.NESTED_UPDATE,
    }

    _connection_config_validator = connection_config_validator
    _scheduler_config_validator = scheduler_config_validator  # type: ignore
    _variables_validator = variables_validator

    @model_validator(mode="before")
    def _normalize_and_validate_fields(cls, data: t.Any) -> t.Any:
        if not isinstance(data, dict):
            return data

        if "gateways" not in data and "gateway" in data:
            data["gateways"] = data.pop("gateway")

        for plan_deprecated in ("auto_categorize_changes", "include_unmodified"):
            if plan_deprecated in data:
                raise ConfigError(
                    f"The `{plan_deprecated}` config is deprecated. Please use the `plan.{plan_deprecated}` config instead."
                )

        if "physical_schema_override" in data:
            get_console().log_warning(
                "`physical_schema_override` is deprecated. Please use `physical_schema_mapping` instead."
            )

            if "physical_schema_mapping" in data:
                raise ConfigError(
                    "Only one of `physical_schema_override` and `physical_schema_mapping` can be specified."
                )

            physical_schema_override: t.Dict[str, str] = data.pop("physical_schema_override")
            # translate physical_schema_override to physical_schema_mapping
            # physical_schema_override を physical_schema_mapping に変換する
            data["physical_schema_mapping"] = {
                f"^{k}$": v for k, v in physical_schema_override.items()
            }

        return data

    @model_validator(mode="after")
    def _normalize_fields_after(self) -> Self:
        dialect = self.model_defaults.dialect

        def _normalize_identifiers(key: str) -> None:
            setattr(
                self,
                key,
                {
                    k: normalize_identifiers(v, dialect=dialect).name
                    for k, v in getattr(self, key, {}).items()
                },
            )

        if (
            self.environment_suffix_target == EnvironmentSuffixTarget.CATALOG
            and self.environment_catalog_mapping
        ):
            raise ConfigError(
                f"'environment_suffix_target: catalog' is mutually exclusive with 'environment_catalog_mapping'.\n"
                "Please specify one or the other"
            )

        if self.plan.use_finalized_state and not self.virtual_environment_mode.is_full:
            raise ConfigError(
                "Using the finalized state is only supported when `virtual_environment_mode` is set to `full`."
            )

        if self.environment_catalog_mapping:
            _normalize_identifiers("environment_catalog_mapping")
        if self.physical_schema_mapping:
            _normalize_identifiers("physical_schema_mapping")

        return self

    @model_validator(mode="after")
    def _inherit_project_config_in_cicd_bot(self) -> Self:
        if self.cicd_bot:
            # inherit the project-level settings into the CICD bot if they have not been explicitly overridden
            # 明示的に上書きされていない場合は、プロジェクトレベルの設定を CICD ボットに継承します。
            if self.cicd_bot.auto_categorize_changes_ is None:
                self.cicd_bot.auto_categorize_changes_ = self.plan.auto_categorize_changes

            if self.cicd_bot.pr_include_unmodified_ is None:
                self.cicd_bot.pr_include_unmodified_ = self.plan.include_unmodified

        return self

    def get_default_test_connection(
        self,
        default_catalog: t.Optional[str] = None,
        default_catalog_dialect: t.Optional[str] = None,
    ) -> ConnectionConfig:
        return self.default_test_connection_ or DuckDBConnectionConfig(
            catalogs=(
                None
                if default_catalog is None
                else {
                    # transpile catalog name from main connection dialect to DuckDB
                    # メイン接続方言からDuckDBにカタログ名をトランスパイルする
                    exp.parse_identifier(default_catalog, dialect=default_catalog_dialect).sql(
                        dialect="duckdb"
                    ): ":memory:"
                }
            )
        )

    def get_gateway(self, name: t.Optional[str] = None) -> GatewayConfig:
        if isinstance(self.gateways, dict):
            if name is None:
                if self.default_gateway:
                    # Normalize default_gateway name to lowercase for lookup
                    # 検索のために default_gateway 名を小文字に正規化する
                    default_key = self.default_gateway.lower()
                    if default_key not in self.gateways:
                        raise ConfigError(f"Missing gateway with name '{self.default_gateway}'")
                    return self.gateways[default_key]

                if "" in self.gateways:
                    return self.gateways[""]

                return first(self.gateways.values())

            # Normalize lookup name to lowercase since gateway keys are already lowercase
            # ゲートウェイキーがすでに小文字なので、ルックアップ名を小文字に正規化します
            lookup_key = name.lower()
            if lookup_key not in self.gateways:
                raise ConfigError(f"Missing gateway with name '{name}'.")

            return self.gateways[lookup_key]
        if name is not None:
            raise ConfigError("Gateway name is not supported when only one gateway is configured.")
        return self.gateways

    def get_connection(self, gateway_name: t.Optional[str] = None) -> ConnectionConfig:
        connection = self.get_gateway(gateway_name).connection or self.default_connection
        if connection is None:
            msg = f" for gateway '{gateway_name}'" if gateway_name else ""
            raise ConfigError(f"No connection configured{msg}.")
        return connection

    def get_state_connection(
        self, gateway_name: t.Optional[str] = None
    ) -> t.Optional[ConnectionConfig]:
        return self.get_gateway(gateway_name).state_connection

    def get_test_connection(
        self,
        gateway_name: t.Optional[str] = None,
        default_catalog: t.Optional[str] = None,
        default_catalog_dialect: t.Optional[str] = None,
    ) -> ConnectionConfig:
        return self.get_gateway(gateway_name).test_connection or self.get_default_test_connection(
            default_catalog=default_catalog, default_catalog_dialect=default_catalog_dialect
        )

    def get_scheduler(self, gateway_name: t.Optional[str] = None) -> SchedulerConfig:
        return self.get_gateway(gateway_name).scheduler or self.default_scheduler

    def get_state_schema(self, gateway_name: t.Optional[str] = None) -> t.Optional[str]:
        return self.get_gateway(gateway_name).state_schema

    @property
    def default_gateway_name(self) -> str:
        if self.default_gateway:
            return self.default_gateway
        if "" in self.gateways:
            return ""
        return first(self.gateways)

    @property
    def dialect(self) -> t.Optional[str]:
        return self.model_defaults.dialect

    @property
    def fingerprint(self) -> str:
        return str(zlib.crc32(pickle.dumps(self.dict(exclude={"loader", "notification_targets"}))))
