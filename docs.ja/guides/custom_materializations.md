# カスタムマテリアライゼーションガイド

SQLMesh は、データ変換の評価とマテリアライゼーションにおける最も一般的なアプローチを反映した、多様な [モデルの種類](../concepts/models/model_kinds.md) をサポートしています。

しかしながら、特定のユースケースでは既存のモデルの種類では対応できない場合があります。このようなシナリオでは、SQLMesh ではユーザーが Python を使用して独自のマテリアライゼーション実装を作成できます。

__注意__: これは高度な機能であり、他のすべてのアプローチを試した場合にのみ検討してください。この判断段階にある場合は、カスタムマテリアライゼーションの構築に時間をかける前に、[コミュニティ Slack](https://tobikodata.com/community.html) でチームに問い合わせることをお勧めします。既存のモデルの種類で問題を解決できる場合は、SQLMesh のドキュメントを明確にします。既存のモデルの種類でほぼ問題を解決できる場合は、すべての SQLMesh ユーザーが問題を解決できるように、モデルの種類を変更することを検討します。

## 背景

SQLMesh モデル種別は、データ変換の出力を実行および管理するためのメソッドで構成されます。これらをまとめて、種別の「マテリアライゼーション」と呼びます。

一部のマテリアライゼーションは比較的単純です。例えば、SQL の [FULL モデル種別](../concepts/models/model_kinds.md#full) は、実行されるたびに既存のデータを完全に置き換えるため、そのマテリアライゼーションは `CREATE OR REPLACE [テーブル名] AS [モデルクエリ]` を実行するだけで済みます。

[INCREMENTAL BY TIME RANGE](../concepts/models/model_kinds.md#incremental_by_time_range) などの他の種別のマテリアライゼーションでは、適切な時間間隔を処理し、その結果を既存のテーブルに置換/挿入するための追加ロジックが必要です。

モデル種別のマテリアライゼーションは、モデルを実行する SQL エンジンによって異なる場合があります。例えば、PostgreSQLは「CREATE OR REPLACE TABLE」をサポートしていないため、モデルの種類を「FULL」するのではなく、既存のテーブルを「DROP」してから新しいテーブルを「CREATE」する必要があります。SQLMeshには、すべての[サポート対象エンジン](../integrations/overview.md#execution-engines)で既存のモデルの種類をマテリアライズするために必要なロジックが既に含まれています。

## 概要

カスタムマテリアライゼーションは、新しいモデルの種類に似ています。ユーザーはモデル定義の `MODEL` ブロック内で [名前で指定](#using-custom-materializations-in-models) し、ユーザー指定の引数を受け入れることができます。

カスタムマテリアライゼーションは、以下の要件を満たす必要があります。

- Python コードで記述されている
- SQLMesh の `CustomMaterialization` 基本クラスを継承する Python クラスである
- SQLMesh [`MaterializableStrategy`](https://github.com/TobikoData/sqlmesh/blob/034476e7f64d261860fd630c3ac56d8a9c9f3e3a/sqlmesh/core/snapshot/evaluator.py#L1146) クラス/サブクラスの `insert` メソッドを使用またはオーバーライドする
- 実行時に SQLMesh によってロードまたはインポートされる

カスタムマテリアライゼーションは、以下の要件を満たすことができます。

- SQLMesh のメソッドを使用またはオーバーライドする[`MaterializableStrategy`](https://github.com/TobikoData/sqlmesh/blob/034476e7f64d261860fd630c3ac56d8a9c9f3e3a/sqlmesh/core/snapshot/evaluator.py#L1146) クラス/サブクラス
- SQLMesh [`EngineAdapter`](https://github.com/TobikoData/sqlmesh/blob/034476e7f64d261860fd630c3ac56d8a9c9f3e3a/sqlmesh/core/engine_adapter/base.py#L67) クラス/サブクラスのメソッドを使用またはオーバーライドします。
- エンジンアダプタの `execute` および関連メソッドを使用して、任意の SQL コードを実行し、結果を取得します。

カスタムマテリアライゼーションでは、Pandas などの任意の Python 処理を実行できます。ライブラリはありますが、ほとんどの場合、そのロジックはマテリアライゼーションではなく [Python モデル](../concepts/models/python_models.md) に配置する必要があります。

SQLMesh プロジェクトは、`materializations/` ディレクトリにあるカスタム マテリアライゼーションを自動的に読み込みます。あるいは、マテリアライゼーションを [Python パッケージ](#python-packaging) にバンドルし、標準的な方法でインストールすることもできます。

## カスタムマテリアライゼーションの作成

実装を含む `.py` ファイルをプロジェクトディレクトリの `materializations/` フォルダに追加することで、新しいカスタムマテリアライゼーションを作成できます。SQLMesh は、プロジェクトのロード時にこのフォルダ内のすべての Python モジュールを自動的にインポートし、カスタムマテリアライゼーションを登録します。(カスタムマテリアライゼーションの共有とパッケージ化の詳細については、[下記](#sharing-custom-materializations) を参照してください。)

カスタムマテリアライゼーションは、`CustomMaterialization` 基本クラスを継承し、`insert` メソッドの実装を提供するクラスである必要があります。

例えば、最小限のフルリフレッシュカスタムマテリアライゼーションは次のようになります。

```python linenums="1"
from sqlmesh import CustomMaterialization # required

# argument typing: strongly recommended but optional best practice
from __future__ import annotations
from sqlmesh import Model
import typing as t
if t.TYPE_CHECKING:
    from sqlmesh import QueryOrDF

class CustomFullMaterialization(CustomMaterialization):
    NAME = "my_custom_full"

    def insert(
        self,
        table_name: str, # ": str" is optional argument typing
        query_or_df: QueryOrDF,
        model: Model,
        is_first_insert: bool,
        render_kwargs: t.Dict[str, t.Any],
        **kwargs: t.Any,
    ) -> None:
        self.adapter.replace_query(table_name, query_or_df)

```

このマテリアライゼーションを詳しく見てみましょう。

* `NAME` - カスタムマテリアライゼーションの名前。この名前は、モデル定義の `MODEL` ブロックでマテリアライゼーションを指定するために使用されます。カスタムマテリアライゼーションで指定されていない場合は、代わりにクラス名が `MODEL` ブロックで使用されます。
* `insert` メソッドには以下の引数があります。
    * `table_name` - データを挿入するターゲットテーブルまたはビューの名前
    * `query_or_df` - 挿入するクエリ（SQLGlot 式型）または DataFrame（Pandas、PySpark、または Snowpark）インスタンス
    * `model` - モデルパラメータとユーザー指定のマテリアライズ引数にアクセスするために使用するモデル定義オブジェクト
    * `is_first_insert` - これが現在のバージョンのモデルの最初の挿入かどうか（バッチ挿入またはマルチステップ挿入で使用）
    * `render_kwargs` - モデルクエリをレンダリングするために使用する引数のディクショナリ
    * `kwargs` - 追加および将来の引数
* `self.adapter` インスタンスは、ターゲットエンジンとのやり取りに使用されます。 `replace_query`、`columns`、`table_exists` といった便利な高水準 API が付属しているだけでなく、`execute` メソッドを使用して任意の SQL 式を実行することもできます。

`MaterializableStrategy` クラスの `create` メソッドと `delete` メソッドをオーバーライドすることで、データオブジェクト（テーブル、ビューなど）の作成方法と削除方法を制御できます。

```python linenums="1"
from sqlmesh import CustomMaterialization # required

# argument typing: strongly recommended but optional best practice
from __future__ import annotations
from sqlmesh import Model
import typing as t

class CustomFullMaterialization(CustomMaterialization):
    # NAME and `insert` method code here
    ...

    def create(
        self,
        table_name: str,
        model: Model,
        is_table_deployable: bool,
        render_kwargs: t.Dict[str, t.Any],
        **kwargs: t.Any,
    ) -> None:
        # Custom table/view creation logic.
        # Likely uses `self.adapter` methods like `create_table`, `create_view`, or `ctas`.

    def delete(self, name: str, **kwargs: t.Any) -> None:
        # Custom table/view deletion logic.
        # Likely uses `self.adapter` methods like `drop_table` or `drop_view`.
```

## カスタムマテリアライゼーションの使用

カスタムマテリアライゼーションを使用するには、モデル定義の `MODEL` ブロックでモデルの種類 `CUSTOM` を指定します。`CUSTOM` の種類の `materialization` 属性に、カスタムマテリアライゼーションコードの `NAME` を指定します。

```sql linenums="1"
MODEL (
  name my_db.my_model,
  kind CUSTOM (
      materialization 'my_custom_full'
  )
);
```

カスタムマテリアライゼーションは、`CUSTOM` 種類の `materialization_properties` 属性のキーと値のペアの配列で指定された引数を受け入れる場合があります。

```sql linenums="1" hl_lines="5-7"
MODEL (
  name my_db.my_model,
  kind CUSTOM (
    materialization 'my_custom_full',
    materialization_properties (
      'config_key' = 'config_value'
    )
  )
);
```

カスタムマテリアライゼーション実装は、`model` オブジェクトの `custom_materialization_properties` ディクショナリを介して `materialization_properties` にアクセスします。

```python linenums="1" hl_lines="12"
class CustomFullMaterialization(CustomMaterialization):
    NAME = "my_custom_full"

    def insert(
        self,
        table_name: str,
        query_or_df: QueryOrDF,
        model: Model,
        is_first_insert: bool,
        render_kwargs: t.Dict[str, t.Any],
        **kwargs: t.Any,
    ) -> None:
        config_value = model.custom_materialization_properties["config_key"]
        # Proceed with implementing the insertion logic.
        # Example existing materialization for look and feel: https://github.com/TobikoData/sqlmesh/blob/main/sqlmesh/core/snapshot/evaluator.py
```

## `CustomKind` の拡張

!!! warning
    これはさらに低レベルな使用法であり、多くの追加の複雑さを伴い、SQLMesh の内部構造に関する知識に依存します。
    このレベルの複雑さが必要ない場合は、上記の方法を使用してください。

多くの場合、上記のカスタムマテリアライゼーションの使用で十分です。

ただし、SQLMesh の内部構造とのより緊密な統合が必要な場合があります。

- データベース接続を行う前に、カスタムプロパティが正しいことを検証したい場合
- 特定のプロパティの存在を前提とする SQLMesh の既存機能を活用したい場合

この場合、SQLMesh が `CustomKind` 自体の代わりに使用する `CustomKind` のサブクラスを提供できます。

プロジェクトのロード時に、SQLMesh は `CustomKind` ではなく、*サブクラス* をインスタンス化します。

これにより、`CustomMaterialization` で `insert()` が呼び出されたときに追加の検証を実行するのではなく、ロード時にカスタム検証を実行できます。

標準のPython `@property`メソッドを定義して、`materialization_properties`内で宣言されたプロパティを`Kind`オブジェクトの最上位に「持ち上げる」こともできます。これにより、カスタムマテリアライゼーション内でそれらのプロパティを簡単に使用できるようになります。

`CustomKind` を拡張するには、まず次のようにサブクラスを定義します。

```python linenums="1" hl_lines="7"
from typing_extensions import Self
from pydantic import field_validator, ValidationInfo
from sqlmesh import CustomKind
from sqlmesh.utils.pydantic import list_of_fields_validator
from sqlmesh.utils.errors import ConfigError

class MyCustomKind(CustomKind):

    _primary_key: t.List[exp.Expression]

    @model_validator(mode="after")
    def _validate_model(self) -> Self:
        self._primary_key = list_of_fields_validator(
            self.materialization_properties.get("primary_key"),
            { "dialect": self.dialect }
        )
        if not self.primary_key:
            raise ConfigError("primary_key must be specified")
        return self

    @property
    def primary_key(self) -> t.List[exp.Expression]:
        return self._primary_key

```

モデル内でこれを使用するには、次のようにします。

```sql linenums="1" hl_lines="4"
MODEL (
  name my_db.my_model,
  kind CUSTOM (
    materialization 'my_custom_full',
    materialization_properties (
        primary_key = (col1, col2)
    )
  )
);
```

SQLMesh に `CustomKind` ではなく `MyCustomKind` サブクラスを使用するように指示するには、次のようにカスタム マテリアライゼーション クラスのジェネリック型パラメータとして指定します。

```python linenums="1" hl_lines="1 16"
class CustomFullMaterialization(CustomMaterialization[MyCustomKind]):
    NAME = "my_custom_full"

    def insert(
        self,
        table_name: str,
        query_or_df: QueryOrDF,
        model: Model,
        is_first_insert: bool,
        render_kwargs: t.Dict[str, t.Any],
        **kwargs: t.Any,
    ) -> None:
        assert isinstance(model.kind, MyCustomKind)

        self.adapter.merge(
            ...,
            unique_key=model.kind.primary_key
        )
```

SQLMesh はカスタム マテリアライゼーションをロードする際に、Python の型シグネチャを検査し、`CustomKind` のサブクラスであるジェネリックパラメータを探します。見つかった場合、`model.kind` の構築時に、デフォルトの `CustomKind` クラスではなく、そのサブクラスをインスタンス化します。

この例では、次のようになります。

- `primary_key` の検証は、評価時ではなくロード時に行われます。そのため、問題が発生した場合、プランの適用の途中ではなく、早期に中止できます。
- カスタム マテリアライゼーションが呼び出されてテーブルにデータをロードすると、`model.kind` はカスタム kind オブジェクトに解決されるため、定義した追加プロパティに、事前に検証したり、使用可能な型に強制変換したりすることなくアクセスできます。


## カスタムマテリアライゼーションの共有

### ファイルのコピー

複数の SQLMesh プロジェクトでカスタムマテリアライゼーションを使用する最も簡単な方法（ただし、堅牢性は最も低い）は、各プロジェクトの `materializations/` ディレクトリに、マテリアライゼーションの Python コードのコピーを配置することです。

この方法を使用する場合は、マテリアライゼーションコードをバージョン管理されたリポジトリに保存し、更新時にユーザーに通知する信頼性の高い方法を作成することを強くお勧めします。

この方法は小規模な組織には適しているかもしれませんが、堅牢性は低いです。

### Python パッケージ化

カスタムマテリアライゼーションを複数の SQLMesh プロジェクトで使用するより複雑（ただし堅牢）な方法は、実装を含む Python パッケージを作成して公開することです。

Python パッケージ化が必要となるシナリオの 1 つは、SQLMesh プロジェクトが Airflow などの外部スケジューラを使用しており、スケジューラクラスタに `materializations/` フォルダがない場合です。クラスタは、標準の Python パッケージインストール方法を使用してカスタムマテリアライゼーションをインポートします。

[setuptools エントリポイント](https://packaging.python.org/en/latest/guides/creating-and-discovering-plugins/#using-package-metadata) メカニズムを使用して、カスタムマテリアライゼーションをパッケージ化して公開します。パッケージがインストールされると、SQLMesh はエントリポイントリストからカスタムマテリアライゼーションを自動的に読み込みます。

たとえば、カスタムマテリアライゼーションクラスが `my_package/my_materialization.py` モジュールで定義されている場合、次のように `pyproject.toml` ファイルでエントリポイントとして公開できます。

```toml
[project.entry-points."sqlmesh.materializations"]
my_materialization = "my_package.my_materialization:CustomFullMaterialization"
```

または `setup.py` では次のようになります:

```python
setup(
    ...,
    entry_points={
        "sqlmesh.materializations": [
            "my_materialization = my_package.my_materialization:CustomFullMaterialization",
        ],
    },
)
```

Python パッケージ化の詳細については、SQLMesh Github [custom_materializations](https://github.com/TobikoData/sqlmesh/tree/main/examples/custom_materializations) の例を参照してください。
