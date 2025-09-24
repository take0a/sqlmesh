# Python モデル

SQL は強力なツールですが、一部のユースケースでは Python の方が適しています。例えば、機械学習、外部 API とのやり取り、SQL では表現できない複雑なビジネスロジックを含むパイプラインでは、Python の方が適している場合があります。

SQLMesh は Python で定義されたモデルを全面的にサポートしています。Pandas または Spark DataFrame インスタンスを返す限り、Python モデルで実行できる処理に制限はありません。


!!! info "サポートされていないモデルの種類"

    Python モデルはこれらの [モデルの種類](./model_kinds.md) をサポートしていません。代わりに SQL モデルを使用してください。

    * `VIEW`
    * `SEED`
    * `MANAGED`
    * `EMBEDDED`

## 定義

Python モデルを作成するには、`models/` ディレクトリに `*.py` 拡張子の新しいファイルを追加します。ファイル内に `execute` という関数を定義します。例:

```python linenums="1"
import typing as t
from datetime import datetime

from sqlmesh import ExecutionContext, model

@model(
    "my_model.name",
    columns={
        "column_name": "int",
    },
)
def execute(
    context: ExecutionContext,
    start: datetime,
    end: datetime,
    execution_time: datetime,
    **kwargs: t.Any,
) -> pd.DataFrame:
```

`execute` 関数は、モデルのメタデータを取得するために使用される `@model` [デコレータ](https://wiki.python.org/moin/PythonDecorators) でラップされています（[SQL モデル](./sql_models.md) の `MODEL` DDL ステートメントに似ています）。

SQLMesh はモデルを評価する前にテーブルを作成するため、出力 DataFrame のスキーマは必須の引数です。`@model` の引数 `columns` には、列名と型の辞書が含まれています。

この関数は、クエリを実行し、処理中の現在の時間間隔を取得できる `ExecutionContext` と、実行時に渡される任意のキーと値の引数を受け取ります。この関数は、Pandas、PySpark、Bigframe、または Snowpark Dataframe インスタンスを返すことができます。

関数の出力が大きすぎる場合は、Python ジェネレータを使用してチャンクで返すこともできます。

## `@model` 仕様

`@model` 仕様で提供される引数は、SQL モデルの `MODEL` DDL で提供される引数と同じ名前です。

Python モデルの `kind` は、種類名と引数を含む Python 辞書で指定します。すべてのモデル種類引数は、[モデル設定リファレンスページ](../../reference/model_configuration.md#model-kind-properties) に記載されています。

モデルの `kind` 辞書には、値が [`ModelKindName` 列挙クラス](https://sqlmesh.readthedocs.io/en/stable/_readthedocs/html/sqlmesh/core/model/kind.html#ModelKindName) のメンバーである `name` キーが含まれている必要があります。`ModelKindName` クラスは、`@model` 仕様で使用する前に、モデル定義ファイルの先頭でインポートする必要があります。

サポートされている `kind` 辞書の `name` 値は次のとおりです。

- `ModelKindName.VIEW`
- `ModelKindName.FULL`
- `ModelKindName.SEED`
- `ModelKindName.INCREMENTAL_BY_TIME_RANGE`
- `ModelKindName.INCREMENTAL_BY_UNIQUE_KEY`
- `ModelKindName.INCREMENTAL_BY_PARTITION`
- `ModelKindName.SCD_TYPE_2_BY_TIME`
- `ModelKindName.SCD_TYPE_2_BY_COLUMN`
- `ModelKindName.EMBEDDED`
- `ModelKindName.CUSTOM`
- `ModelKindName.MANAGED`
- `ModelKindName.EXTERNAL`

この例では、Python で時間範囲による増分モデルの種類を指定する方法を示します。

```python linenums="1"
from sqlmesh import ExecutionContext, model
from sqlmesh.core.model.kind import ModelKindName

@model(
    "docs_example.incremental_model",
    kind=dict(
        name=ModelKindName.INCREMENTAL_BY_TIME_RANGE,
        time_column="model_time_column"
    )
)
```

## 実行コンテキスト

Python モデルはあらゆる処理を実行できますが、すべてのモデルを [べき等](../glossary.md#idempotency) にすることを強くお勧めします。Python モデルは上流モデルからデータを取得できるだけでなく、SQLMesh 外部のデータも取得できます。

実行コンテキスト `ExecutionContext` を指定すると、`fetchdf` メソッドで DataFrame を取得できます。

```python linenums="1"
df = context.fetchdf("SELECT * FROM my_table")
```

## オプションの pre/post ステートメント

オプションの pre/post ステートメントを使用すると、モデルの実行前と実行後にそれぞれ SQL コマンドを実行できます。

例えば、pre/post ステートメントは設定の変更やインデックスの作成などを行います。ただし、物理テーブルの作成など、モデルが同時に実行される場合に他のステートメントの実行と競合する可能性のあるステートメントは実行しないように注意してください。

`pre_statements` および `post_statements` 引数に、SQL 文字列、SQLGlot 式、またはマクロ呼び出しのリストを設定することで、モデルの pre/post ステートメントを定義できます。

**プロジェクトレベルのデフォルト:** 設定で `model_defaults` を使用して、プロジェクトレベルで pre/post ステートメントを定義することもできます。これらのステートメントはプロジェクト内のすべてのモデルに適用され、モデル固有のステートメントとマージされます。デフォルトのステートメントが最初に実行され、その後にモデル固有のステートメントが実行されます。詳細については、[モデル設定リファレンス](../../reference/model_configuration.md#model-defaults) をご覧ください。

``` python linenums="1" hl_lines="8-12"
@model(
    "db.test_model",
    kind="full",
    columns={
        "id": "int",
        "name": "text",
    },
    pre_statements=[
        "SET GLOBAL parameter = 'value';",
        exp.Cache(this=exp.table_("x"), expression=exp.select("1")),
    ],
    post_statements=["@CREATE_INDEX(@this_model, id)"],
)
def execute(
    context: ExecutionContext,
    start: datetime,
    end: datetime,
    execution_time: datetime,
    **kwargs: t.Any,
) -> pd.DataFrame:

    return pd.DataFrame([
        {"id": 1, "name": "name"}
    ])

```

前の例では、`post_statements` はユーザー定義の SQLMesh マクロ `@CREATE_INDEX(@this_model, id)` を呼び出していました。

`CREATE_INDEX` マクロは、プロジェクトの `macros` ディレクトリに次のように定義できます。このマクロは、[実行時ステージ](../macros/macro_variables.md#runtime-variables) が `creating` (テーブル作成時) であることを条件に、単一列にテーブルインデックスを作成します。


``` python linenums="1"
@macro()
def create_index(
    evaluator: MacroEvaluator,
    model_name: str,
    column: str,
):
    if evaluator.runtime_stage == "creating":
        return f"CREATE INDEX idx ON {model_name}({column});"
    return None
```

あるいは、SQLMesh の [`fetchdf` メソッド](../../reference/cli.md#fetchdf) [上記で説明](#execution-context) を使用して、事前ステートメントと事後ステートメントを発行することもできます。

事前ステートメントは、関数本体内の `return` または `yield` の前の任意の場所に指定できます。事後ステートメントは関数の完了後に実行される必要があるため、関数は値を `return` する代わりに、値を `yield` する必要があります。事後ステートメントは `yield` の後に指定する必要があります。

このサンプル関数には、事前ステートメントと事後ステートメントの両方が含まれています。

``` python linenums="1" hl_lines="9-10 12 17-18"
def execute(
    context: ExecutionContext,
    start: datetime,
    end: datetime,
    execution_time: datetime,
    **kwargs: t.Any,
) -> pd.DataFrame:

    # pre-statement
    context.engine_adapter.execute("SET GLOBAL parameter = 'value';")

    # post-statement requires using `yield` instead of `return`
    yield pd.DataFrame([
        {"id": 1, "name": "name"}
    ])

    # post-statement
    context.engine_adapter.execute("CREATE INDEX idx ON example.pre_post_statements (id);")
```

## オプションの on-virtual-update ステートメント

オプションの on-virtual-update ステートメントを使用すると、[仮想更新](#virtual-update) の完了後に SQL コマンドを実行できます。

これらは、例えば、仮想レイヤーのビューに対する権限を付与するために使用できます。

事前/事後ステートメントと同様に、`@model` デコレータの `on_virtual_update` 引数に、SQL 文字列、SQLGlot 式、またはマクロ呼び出しのリストを設定できます。

**プロジェクトレベルのデフォルト:** 設定で `model_defaults` を使用して、プロジェクトレベルで on-virtual-update ステートメントを定義することもできます。これらのステートメントは、プロジェクト内のすべてのモデル（Python モデルを含む）に適用され、モデル固有のステートメントとマージされます。デフォルトのステートメントが最初に実行され、次にモデル固有のステートメントが実行されます。詳細については、[モデル設定リファレンス](../../reference/model_configuration.md#model-defaults) を参照してください。

``` python linenums="1" hl_lines="8"
@model(
    "db.test_model",
    kind="full",
    columns={
        "id": "int",
        "name": "text",
    },
    on_virtual_update=["GRANT SELECT ON VIEW @this_model TO ROLE dev_role"],
)
def execute(
    context: ExecutionContext,
    start: datetime,
    end: datetime,
    execution_time: datetime,
    **kwargs: t.Any,
) -> pd.DataFrame:

    return pd.DataFrame([
        {"id": 1, "name": "name"}
    ])
```

!!! note

    これらのステートメントのテーブル解決は仮想レイヤーで行われます。つまり、`@this_model` マクロを含むテーブル名は、修飾されたビュー名に解決されます。例えば、`dev` という環境でプランを実行すると、`db.test_model` と `@this_model` は物理テーブル名ではなく `db__dev.test_model` に解決されます。

## 依存関係

上流モデルからデータを取得するには、まず `context` の `resolve_table` メソッドを使ってテーブル名を取得します。このメソッドは、現在のランタイム [environment](../environments.md) に適したテーブル名を返します。

```python linenums="1"
table = context.resolve_table("docs_example.upstream_model")
df = context.fetchdf(f"SELECT * FROM {table}")
```

`resolve_table` メソッドは、参照先のモデルを Python モデルの依存関係に自動的に追加します。

Python モデル内でモデルの依存関係を設定する唯一の他の方法は、`@model` デコレータ内でキーワード `depends_on` を使用して明示的に定義することです。モデルデコレータで定義された依存関係は、関数内の動的参照よりも優先されます。

この例では、`upstream_dependency` のみがキャプチャされ、`another_dependency` は無視されます。

```python linenums="1"
@model(
    "my_model.with_explicit_dependencies",
    depends_on=["docs_example.upstream_dependency"], # captured
)
def execute(
    context: ExecutionContext,
    start: datetime,
    end: datetime,
    execution_time: datetime,
    **kwargs: t.Any,
) -> pd.DataFrame:

    # ignored due to @model dependency "upstream_dependency"
    context.resolve_table("docs_example.another_dependency")
```

次の例に示すように、ユーザー定義の [グローバル変数](global-variables) または [ブループリント変数](#python-model-blueprinting) も `resolve_table` 呼び出しで使用できます (`blueprint_var()` の場合も同様)。

```python linenums="1"
@model(
    "@schema_name.test_model2",
    kind="FULL",
    columns={"id": "INT"},
)
def execute(context, **kwargs):
    table = context.resolve_table(f"{context.var('schema_name')}.test_model1")
    select_query = exp.select("*").from_(table)
    return context.fetchdf(select_query)
```

## 空のデータフレームを返す

Python モデルは空のデータフレームを返さない場合があります。

モデルが空のデータフレームを返す可能性がある場合は、`return` ではなく、条件付きでデータフレームまたは空のジェネレーターを `yield` してください。

```python linenums="1" hl_lines="10-13"
@model(
    "my_model.empty_df"
)
def execute(
    context: ExecutionContext,
) -> pd.DataFrame:

    [...code creating df...]

    if df.empty:
        yield from ()
    else:
        yield df
```

## ユーザー定義変数

[ユーザー定義グローバル変数](../../reference/configuration.md#variables) は、Python モデル内から `context.var` メソッドを使用してアクセスできます。

例えば、このモデルはユーザー定義変数 `var` と `var_with_default` にアクセスします。`variable_with_default` が欠損値に解決された場合、デフォルト値として `default_value` を指定します。

```python linenums="1" hl_lines="11 12"
@model(
    "my_model.name",
)
def execute(
    context: ExecutionContext,
    start: datetime,
    end: datetime,
    execution_time: datetime,
    **kwargs: t.Any,
) -> pd.DataFrame:
    var_value = context.var("var")
    var_with_default_value = context.var("var_with_default", "default_value")
    ...
```

あるいは、`execute` 関数の引数を介してグローバル変数にアクセスすることもできます。引数の名前は変数のキー名に対応します。

例えば、このモデルでは `execute` メソッドの引数として `my_var` を指定しています。モデルコードでは `my_var` オブジェクトを直接参照できます。

```python linenums="1" hl_lines="9 12"
@model(
    "my_model.name",
)
def execute(
    context: ExecutionContext,
    start: datetime,
    end: datetime,
    execution_time: datetime,
    my_var: Optional[str] = None,
    **kwargs: t.Any,
) -> pd.DataFrame:
    my_var_plus1 = my_var + 1
    ...
```

変数が欠落する可能性がある場合には、引数にデフォルト値が設定されていることを確認してください。

引数は明示的に指定する必要があることに注意してください。変数には `kwargs` を使用してアクセスすることはできません。

## Python モデルのブループリント

Python モデルは、`blueprints` プロパティにキーと値の辞書のリストを指定することにより、複数のモデル（つまり _ブループリント_）を作成するためのテンプレートとしても機能します。これを実現するには、モデル名をこのマッピング内に存在する変数でパラメータ化する必要があります。

例えば、次のモデルは `blueprints` プロパティ内の対応するマッピングを使用する 2 つの新しいモデルを生成します。

```python linenums="1"
import typing as t
from datetime import datetime

import pandas as pd
from sqlmesh import ExecutionContext, model

@model(
    "@{customer}.some_table",
    kind="FULL",
    blueprints=[
        {"customer": "customer1", "field_a": "x", "field_b": "y"},
        {"customer": "customer2", "field_a": "z", "field_b": "w"},
    ],
    columns={
        "field_a": "text",
        "field_b": "text",
        "customer": "text",
    },
)
def entrypoint(
    context: ExecutionContext,
    start: datetime,
    end: datetime,
    execution_time: datetime,
    **kwargs: t.Any,
) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "field_a": [context.blueprint_var("field_a")],
            "field_b": [context.blueprint_var("field_b")],
            "customer": [context.blueprint_var("customer")],
        }
    )
```

上記のモデル名で中括弧構文 `@{customer}` が使用されていることに注意してください。これは、SQLMesh がマクロ変数をモデル名識別子に正しく組み込めるようにするために使用されます。詳しくは [こちら](../../concepts/macros/sqlmesh_macros.md#embedding-variables-in-strings) をご覧ください。

ブループリント変数のマッピングは、マクロ `blueprints="@gen_blueprints()"` を使用することで動的に構築することもできます。これは、`blueprints` リストを CSV ファイルなどの外部ソースから取得する必要がある場合に便利です。

例えば、`gen_blueprints` の定義は次のようになります。

```python linenums="1"
from sqlmesh import macro

@macro()
def gen_blueprints(evaluator):
    return (
        "((customer := customer1, field_a := x, field_b := y),"
        " (customer := customer2, field_a := z, field_b := w))"
    )
```

`@EACH` マクロをグローバル リスト変数 (`@values`) と組み合わせて使用​​することもできます。

```python linenums="1"

@model(
    "@{customer}.some_table",
    blueprints="@EACH(@values, x -> (customer := schema_@x))",
    ...
)
...
```

## モデルプロパティでのマクロの使用

Python モデルは、モデルプロパティ内でマクロ変数をサポートしています。ただし、マクロ変数が文字列内で使用される場合は特別な注意が必要です。

例えば、cron 式内でマクロ変数を使用する場合は、式全体を引用符で囲み、先頭に `@` を付けることで、正しく解析されるようになります。

```python linenums="1"
# Correct: Wrap the cron expression containing a macro variable
@model(
    "my_model",
    cron="@'*/@{mins} * * * *'",  # Note the @'...' syntax
    ...
)

# This also works with blueprint variables
@model(
    "@{customer}.scheduled_model",
    cron="@'0 @{hour} * * *'",
    blueprints=[
        {"customer": "customer_1", "hour": 2}, # Runs at 2 AM
        {"customer": "customer_2", "hour": 8}, # Runs at 8 AM
    ],
    ...
)

```

これが必要なのは、cron 式ではエイリアスに `@` (`@daily`、`@hourly` など) が使用されることが多く、これが SQLMesh のマクロ構文と競合する可能性があるためです。

## 例

### 基本

以下は、静的な Pandas DataFrame を返す Python モデルの例です。

**注:** すべての [metadata](./overview.md#properties) フィールド名は、SQL `MODEL` DDL のものと同じです。

```python linenums="1"
import typing as t
from datetime import datetime

import pandas as pd
from sqlglot.expressions import to_column
from sqlmesh import ExecutionContext, model

@model(
    "docs_example.basic",
    owner="janet",
    cron="@daily",
    columns={
        "id": "int",
        "name": "text",
    },
    column_descriptions={
        "id": "Unique ID",
        "name": "Name corresponding to the ID",
    },
    audits=[
        ("not_null", {"columns": [to_column("id")]}),
    ],
)
def execute(
    context: ExecutionContext,
    start: datetime,
    end: datetime,
    execution_time: datetime,
    **kwargs: t.Any,
) -> pd.DataFrame:

    return pd.DataFrame([
        {"id": 1, "name": "name"}
    ])
```

### SQL クエリと Pandas

以下は、上流モデルをクエリして Pandas DataFrame を出力する、より複雑な例です。

```python linenums="1"
import typing as t
from datetime import datetime

import pandas as pd
from sqlmesh import ExecutionContext, model

@model(
    "docs_example.sql_pandas",
    columns={
        "id": "int",
        "name": "text",
    },
)
def execute(
    context: ExecutionContext,
    start: datetime,
    end: datetime,
    execution_time: datetime,
    **kwargs: t.Any,
) -> pd.DataFrame:
    # get the upstream model's name and register it as a dependency
    table = context.resolve_table("upstream_model")

    # fetch data from the model as a pandas DataFrame
    # if the engine is spark, this returns a spark DataFrame
    df = context.fetchdf(f"SELECT id, name FROM {table}")

    # do some pandas stuff
    df[id] += 1
    return df
```

### PySpark

この例では、PySpark DataFrame API の使用方法を示します。Spark を使用する場合は、分散型の計算が可能なため、Pandas よりも DataFrame API を使用することをお勧めします。

```python linenums="1"
import typing as t
from datetime import datetime

import pandas as pd
from pyspark.sql import DataFrame, functions

from sqlmesh import ExecutionContext, model

@model(
    "docs_example.pyspark",
    columns={
        "id": "int",
        "name": "text",
        "country": "text",
    },
)
def execute(
    context: ExecutionContext,
    start: datetime,
    end: datetime,
    execution_time: datetime,
    **kwargs: t.Any,
) -> DataFrame:
    # get the upstream model's name and register it as a dependency
    table = context.resolve_table("upstream_model")

    # use the spark DataFrame api to add the country column
    df = context.spark.table(table).withColumn("country", functions.lit("USA"))

    # returns the pyspark DataFrame directly, so no data is computed locally
    return df
```


### Snowpark

この例では、Snowpark DataFrame API の使用方法を示します。Snowflake を使用する場合は、分散型の計算が可能なため、Pandas よりも DataFrame API を使用することをお勧めします。

```python linenums="1"
import typing as t
from datetime import datetime

import pandas as pd
from snowflake.snowpark.dataframe import DataFrame

from sqlmesh import ExecutionContext, model

@model(
    "docs_example.snowpark",
    columns={
        "id": "int",
        "name": "text",
        "country": "text",
    },
)
def execute(
    context: ExecutionContext,
    start: datetime,
    end: datetime,
    execution_time: datetime,
    **kwargs: t.Any,
) -> DataFrame:
    # returns the snowpark DataFrame directly, so no data is computed locally
    df = context.snowpark.create_dataframe([[1, "a", "usa"], [2, "b", "cad"]], schema=["id", "name", "country"])
    df = df.filter(df.id > 1)
    return df
```

### Bigframe

この例では、[Bigframe](https://cloud.google.com/bigquery/docs/use-bigquery-dataframes#pandas-examples) DataFrame API の使用方法を示します。Bigquery を使用する場合は、すべての計算が Bigquery 内で行われるため、Pandas よりも Bigframe API の方が推奨されます。

```python linenums="1"
import typing as t
from datetime import datetime

from bigframes.pandas import DataFrame

from sqlmesh import ExecutionContext, model


def get_bucket(num: int):
    if not num:
        return "NA"
    boundary = 10
    return "at_or_above_10" if num >= boundary else "below_10"


@model(
    "mart.wiki",
    columns={
        "title": "text",
        "views": "int",
        "bucket": "text",
    },
)
def execute(
    context: ExecutionContext,
    start: datetime,
    end: datetime,
    execution_time: datetime,
    **kwargs: t.Any,
) -> DataFrame:
    # Create a remote function to be used in the Bigframe DataFrame
    remote_get_bucket = context.bigframe.remote_function([int], str)(get_bucket)

    # Returns the Bigframe DataFrame handle, no data is computed locally
    df = context.bigframe.read_gbq("bigquery-samples.wikipedia_pageviews.200809h")

    df = (
        # This runs entirely on the BigQuery engine lazily
        df[df.title.str.contains(r"[Gg]oogle")]
        .groupby(["title"], as_index=False)["views"]
        .sum(numeric_only=True)
        .sort_values("views", ascending=False)
    )

    return df.assign(bucket=df["views"].apply(remote_get_bucket))
```

### バッチ処理

Python モデルの出力が非常に大きく、Spark を使用できない場合は、出力を複数のバッチに分割すると便利です。

Pandas やその他の単一マシンの DataFrame ライブラリでは、すべてのデータがメモリに保存されます。単一の DataFrame インスタンスを返す代わりに、Python ジェネレーター API を使用して複数のインスタンスを返すことができます。これにより、メモリにロードされるデータのサイズが削減され、メモリ使用量が最小限に抑えられます。

この例では、Python ジェネレーター `yield` を使用してモデル出力をバッチ処理します。

```python linenums="1" hl_lines="20"
@model(
    "docs_example.batching",
    columns={
        "id": "int",
    },
)
def execute(
    context: ExecutionContext,
    start: datetime,
    end: datetime,
    execution_time: datetime,
    **kwargs: t.Any,
) -> pd.DataFrame:
    # get the upstream model's table name
    table = context.resolve_table("upstream_model")

    for i in range(3):
        # run 3 queries to get chunks of data and not run out of memory
        df = context.fetchdf(f"SELECT id from {table} WHERE id = {i}")
        yield df
```

## シリアル化

SQLMesh は、カスタムの [シリアル化フレームワーク](../architecture/serialization.md) を使用して、SQLMesh が実行されている場所で Python コードをローカルに実行します。
