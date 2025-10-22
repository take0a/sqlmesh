from __future__ import annotations

import typing as t
from enum import Enum
import re

from sqlmesh.utils import classproperty
from sqlmesh.utils.errors import ConfigError
from sqlmesh.utils.pydantic import field_validator

# Config files that can be present in the project dir
# プロジェクトディレクトリに存在できる設定ファイル
ALL_CONFIG_FILENAMES = ("config.py", "config.yml", "config.yaml", "sqlmesh.yml", "sqlmesh.yaml")

# For personal paths (~/.sqlmesh/) where python config is not supported
# Python 設定がサポートされていない個人パス (~/.sqlmesh/) の場合
YAML_CONFIG_FILENAMES = tuple(n for n in ALL_CONFIG_FILENAMES if not n.endswith(".py"))

# Note: is here to prevent having to import from sqlmesh.dbt.loader which introduces a dependency
# on dbt-core in a native project
# 注: ネイティブ プロジェクトで dbt-core への依存関係を導入する sqlmesh.dbt.loader 
# からのインポートを回避するためにここにあります。
DBT_PROJECT_FILENAME = "dbt_project.yml"


class EnvironmentSuffixTarget(str, Enum):
    # Intended to create virtual environments in their own schemas, with names like "<model_schema_name>__<env name>". The view name is untouched.
    # For example, a model named 'sqlmesh_example.full_model' created in an environment called 'dev'
    # would have its virtual layer view created as 'sqlmesh_example__dev.full_model'
    # 仮想環境を独自のスキーマ内に作成し、「<model_schema_name>__<env name>」のような名前にします。ビュー名は変更されません。
    # 例えば、「dev」という環境に「sqlmesh_example.full_model」というモデルを作成した場合、
    # その仮想レイヤービューは「sqlmesh_example__dev.full_model」として作成されます。
    SCHEMA = "schema"

    # Intended to create virtual environments in the same schema as their production counterparts by adjusting the table name.
    # For example, a model named 'sqlmesh_example.full_model' created in an environment called 'dev'
    # would have its virtual layer view created as "sqlmesh_example.full_model__dev"
    # テーブル名を調整することで、本番環境と同じスキーマ内に仮想環境を作成することを目的としています。
    # たとえば、「dev」という環境で作成された「sqlmesh_example.full_model」という名前のモデルの場合、
    # 仮想レイヤービューは「sqlmesh_example.full_model__dev」として作成されます。
    TABLE = "table"

    # Intended to create virtual environments in their own catalogs to preserve the schema and view name of the models
    # For example, a model named 'sqlmesh_example.full_model' created in an environment called 'dev'
    # with a default catalog of "warehouse" would have its virtual layer view created as "warehouse__dev.sqlmesh_example.full_model"
    # note: this only works for engines that can query across catalogs
    # モデルのスキーマとビュー名を保持するために、独自のカタログ内に仮想環境を作成することを目的としています。
    # 例えば、「dev」という環境で「warehouse」というデフォルトカタログを持つ「sqlmesh_example.full_model」というモデルを作成すると、
    # その仮想レイヤービューは「warehouse__dev.sqlmesh_example.full_model」として作成されます。
    # 注: これは、複数のカタログにまたがってクエリを実行できるエンジンでのみ機能します。
    CATALOG = "catalog"

    @property
    def is_schema(self) -> bool:
        return self == EnvironmentSuffixTarget.SCHEMA

    @property
    def is_table(self) -> bool:
        return self == EnvironmentSuffixTarget.TABLE

    @property
    def is_catalog(self) -> bool:
        return self == EnvironmentSuffixTarget.CATALOG

    @classproperty
    def default(cls) -> EnvironmentSuffixTarget:
        return EnvironmentSuffixTarget.SCHEMA

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return str(self)


class VirtualEnvironmentMode(str, Enum):
    """Mode for virtual environment behavior.
    仮想環境の動作モード。

    FULL: Use full virtual environment functionality with versioned table names and virtual layer updates.
        バージョン管理されたテーブル名と仮想レイヤーの更新を備えた完全な仮想環境機能を使用します。
    DEV_ONLY: Bypass virtual environments in production, using original unversioned model names.
        元のバージョンなしのモデル名を使用して、運用環境で仮想環境をバイパスします。
    """

    FULL = "full"
    DEV_ONLY = "dev_only"

    @property
    def is_full(self) -> bool:
        return self == VirtualEnvironmentMode.FULL

    @property
    def is_dev_only(self) -> bool:
        return self == VirtualEnvironmentMode.DEV_ONLY

    @classproperty
    def default(cls) -> VirtualEnvironmentMode:
        return VirtualEnvironmentMode.FULL

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return str(self)


class TableNamingConvention(str, Enum):
    # Causes table names at the physical layer to follow the convention:
    # 物理層のテーブル名が次の規則に従うようになります。
    # <schema-name>__<table-name>__<fingerprint>
    SCHEMA_AND_TABLE = "schema_and_table"

    # Causes table names at the physical layer to follow the convention:
    # 物理層のテーブル名が次の規則に従うようになります。
    # <table-name>__<fingerprint>
    TABLE_ONLY = "table_only"

    # Takes the table name that would be returned from SCHEMA_AND_TABLE and wraps it in md5()
    # to generate a hash and prefixes the has with `sqlmesh_md5__`, for the following reasons:
    # - at a glance, you can still see it's managed by sqlmesh and that md5 was used to generate the hash
    # - unquoted identifiers that start with numbers can trip up DB engine parsers, so having a text prefix prevents this
    # This causes table names at the physical layer to follow the convention:
    # sqlmesh_md5__3b07384d113edec49eaa6238ad5ff00d
    # SCHEMA_AND_TABLE から返されるテーブル名を md5() でラップしてハッシュを生成し、
    # ハッシュの先頭に `sqlmesh_md5__` を付加します。理由は以下のとおりです。
    # - 一目見ただけで、sqlmesh によって管理されていること、そしてハッシュの生成に md5 が使用されていることがわかります。
    # - 数字で始まる引用符なしの識別子は DB エンジンのパーサーを誤作動させる可能性があるため、テキストのプレフィックスを付けることでこれを防ぎます。
    # これにより、物理層のテーブル名は規則に従います。
    # sqlmesh_md5__3b07384d113edec49eaa6238ad5ff00d
    HASH_MD5 = "hash_md5"

    @classproperty
    def default(cls) -> TableNamingConvention:
        return TableNamingConvention.SCHEMA_AND_TABLE

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return str(self)


def _concurrent_tasks_validator(v: t.Any) -> int:
    if isinstance(v, str):
        v = int(v)
    if not isinstance(v, int) or v <= 0:
        raise ConfigError(
            f"The number of concurrent tasks must be an integer value greater than 0. '{v}' was provided"
        )
    return v


concurrent_tasks_validator = field_validator(
    "backfill_concurrent_tasks",
    "ddl_concurrent_tasks",
    "concurrent_tasks",
    mode="before",
    check_fields=False,
)(_concurrent_tasks_validator)


def _http_headers_validator(v: t.Any) -> t.Any:
    if isinstance(v, dict):
        return [(key, value) for key, value in v.items()]
    return v


http_headers_validator = field_validator(
    "http_headers",
    mode="before",
    check_fields=False,
)(_http_headers_validator)


def _variables_validator(value: t.Dict[str, t.Any]) -> t.Dict[str, t.Any]:
    if not isinstance(value, dict):
        raise ConfigError(f"Variables must be a dictionary, not {type(value)}")

    def _validate_type(v: t.Any) -> None:
        if isinstance(v, list):
            for item in v:
                _validate_type(item)
        elif isinstance(v, dict):
            for item in v.values():
                _validate_type(item)
        elif v is not None and not isinstance(v, (str, int, float, bool)):
            raise ConfigError(f"Unsupported variable value type: {type(v)}")

    _validate_type(value)
    return {k.lower(): v for k, v in value.items()}


variables_validator = field_validator(
    "variables",
    mode="before",
    check_fields=False,
)(_variables_validator)


def compile_regex_mapping(value: t.Dict[str | re.Pattern, t.Any]) -> t.Dict[re.Pattern, t.Any]:
    """
    Utility function to compile a dict of { "string regex pattern" : "string value" } into { "<re.Pattern>": "string value" }
    { "string regex pattern" : "string value" } の辞書を { "<re.Pattern>": "string value" } にコンパイルするユーティリティ関数
    """
    compiled_regexes = {}
    for k, v in value.items():
        try:
            compiled_regexes[re.compile(k)] = v
        except re.error:
            raise ConfigError(f"`{k}` is not a valid regular expression.")
    return compiled_regexes
