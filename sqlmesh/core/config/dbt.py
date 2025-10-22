from sqlmesh.core.config.base import BaseConfig


class DbtConfig(BaseConfig):
    """
    Represents dbt-specific options on the SQLMesh root config.
    SQLMesh ルート設定における dbt 固有のオプションを表します。

    These options are only taken into account for dbt projects and are ignored on native projects
    これらのオプションは dbt プロジェクトでのみ考慮され、ネイティブ プロジェクトでは無視されます。
    """

    infer_state_schema_name: bool = False
    """If set, indicates to the dbt loader that the state schema should be inferred based on the profile/target
    so that each target gets its own isolated state
    設定されている場合、各ターゲットが独自の分離された状態を取得するように、
    プロファイル/ターゲットに基づいて状態スキーマを推論する必要があることを dbt ローダーに示します。"""
