# SQL モデル

SQL モデルは、SQLMesh で使用される主なモデルの種類です。これらのモデルは、SQL または SQL を生成する Python を使用して定義できます。

## SQL ベースの定義

SQL ベースの SQL モデル定義は最も一般的なもので、以下のセクションで構成されます。

* `MODEL` DDL
* オプションの事前ステートメント
* 単一のクエリ
* オプションの事後ステートメント
* オプションの仮想更新ステートメント

これらのモデルは、SQL を使用しているかのような外観と操作性を実現するように設計されていますが、高度なユースケースに合わせてカスタマイズできます。

SQL ベースのモデルを作成するには、SQLMesh プロジェクト内の `models/` ディレクトリ（または `models/` のサブディレクトリ）に、`.sql` サフィックスを持つ新しいファイルを追加します。ファイル名は任意ですが、モデル名（スキーマなし）をファイル名として使用するのが慣例です。たとえば、モデル `sqlmesh_example.seed_model` を含むファイルは `seed_model.sql` という名前になります。

### Example

```sql linenums="1"
-- This is the MODEL DDL, where you specify model metadata and configuration information.
MODEL (
  name db.customers,
  kind FULL,
);

/*
  Optional pre-statements that will run before the model's query.
  You should NOT do things that cause side effects that could error out when
  executed concurrently with other statements, such as creating physical tables.
*/
CACHE TABLE countries AS SELECT * FROM raw.countries;

/*
  This is the single query that defines the model's logic.
  Although it is not required, it is considered best practice to explicitly
  specify the type for each one of the model's columns through casting.
*/
SELECT
  r.id::INT,
  r.name::TEXT,
  c.country::TEXT
FROM raw.restaurants AS r
JOIN countries AS c
  ON r.id = c.restaurant_id;

/*
  Optional post-statements that will run after the model's query.
  You should NOT do things that cause side effects that could error out when
  executed concurrently with other statements, such as creating physical tables.
*/
UNCACHE TABLE countries;
```

### `MODEL` DDL

`MODEL` DDL は、モデル名、[種類](./model_kinds.md)、所有者、cron など、モデルに関するメタデータを指定するために使用されます。これは、SQL ベースのモデルファイルの最初のステートメントである必要があります。

使用可能なプロパティの完全なリストについては、`MODEL` [プロパティ](./overview.md#properties) を参照してください。

### オプションの pre/post ステートメント

オプションの pre/post ステートメントを使用すると、モデルの実行前と実行後にそれぞれ SQL コマンドを実行できます。

例えば、pre/post ステートメントは設定の変更やテーブルインデックスの作成などを行います。ただし、物理テーブルの作成など、同時に実行した場合に他のモデルの実行と競合する可能性のあるステートメントは実行しないように注意してください。

pre/post ステートメントは、モデルクエリの前後に配置される標準的な SQL コマンドです。pre/post ステートメントはセミコロンで終了する必要があり、post ステートメントが存在する場合はモデルクエリもセミコロンで終了する必要があります。[上記の例](#example) には、pre/post ステートメントと post ステートメントの両方が含まれています。

**プロジェクトレベルのデフォルト:** 設定で `model_defaults` を使用して、プロジェクトレベルで pre/post ステートメントを定義することもできます。これらのステートメントはプロジェクト内のすべてのモデルに適用され、モデル固有のステートメントとマージされます。デフォルトのステートメントが最初に実行され、次にモデル固有のステートメントが実行されます。詳細については、[モデル構成リファレンス](../../reference/model_configuration.md#model-defaults)を参照してください。

!!! warning

    事前/事後ステートメントは、モデルのテーブル作成時とクエリロジック評価時の2回評価されます。ステートメントを複数回実行すると意図しない副作用が生じる可能性があるため、SQLMeshの[実行時ステージ](../macros/macro_variables.md#runtime-variables)に基づいて[条件付き実行](../macros/sqlmesh_macros.md#prepost-statements)できます。

[上記の例](#example)の事前/事後ステートメントは、実行時ステージで条件付けされていないため、2回実行されます。

[`@IF` マクロ演算子](../macros/sqlmesh_macros.md#if)と[`@runtime_stage` マクロ変数](../macros/macro_variables.md#runtime-variables)を使用して、モデルクエリが評価された後にのみ事後ステートメントが実行されるように条件付けできます。

```sql linenums="1" hl_lines="8-11"
MODEL (
  name db.customers,
  kind FULL,
);

[...same as example above...]

@IF(
  @runtime_stage = 'evaluating',
  UNCACHE TABLE countries
);
```

`@IF()` マクロ内の SQL コマンド `UNCACHE TABLE countries` はセミコロンで終わっていないことに注意してください。代わりに、セミコロンは `@IF()` マクロの閉じ括弧の後に来ます。

### オプションの on-virtual-update ステートメント

オプションの on-virtual-update ステートメントを使用すると、[仮想更新](#virtual-update) の完了後に SQL コマンドを実行できます。

これらは、例えば仮想レイヤーのビューに対する権限を付与するために使用できます。

**プロジェクトレベルのデフォルト:** 設定で `model_defaults` を使用して、プロジェクトレベルで on-virtual-update ステートメントを定義することもできます。これらのステートメントは、プロジェクト内のすべてのモデルに適用され、モデル固有のステートメントとマージされます。デフォルトのステートメントが最初に実行され、次にモデル固有のステートメントが実行されます。詳細については、[モデル設定リファレンス](../../reference/model_configuration.md#model-defaults) を参照してください。

これらの SQL ステートメントは、次のように `ON_VIRTUAL_UPDATE_BEGIN;` ...; `ON_VIRTUAL_UPDATE_END;` ブロックで囲む必要があります。

```sql linenums="1" hl_lines="10-15"
MODEL (
  name db.customers,
  kind FULL
);

SELECT
  r.id::INT
FROM raw.restaurants AS r;

ON_VIRTUAL_UPDATE_BEGIN;
GRANT SELECT ON VIEW @this_model TO ROLE role_name;
JINJA_STATEMENT_BEGIN;
GRANT SELECT ON VIEW {{ this_model }} TO ROLE admin;
JINJA_END;
ON_VIRTUAL_UPDATE_END;
```

上記の例のように、[Jinja式](../macros/jinja_macros.md)も使用できます。これらの式は、`JINJA_STATEMENT_BEGIN;` ブロックと `JINJA_END;` ブロック内に適切にネストする必要があります。

!!! note

    これらのステートメントのテーブル解決は仮想レイヤーで行われます。つまり、`@this_model` マクロを含むテーブル名は、修飾されたビュー名に解決されます。例えば、`dev` という環境でプランを実行すると、`db.customers` と `@this_model` は物理テーブル名ではなく `db__dev.customers` に解決されます。

### モデルクエリ

モデルにはスタンドアロンクエリが含まれている必要があります。これは、単一の `SELECT` 式、または `UNION`、`INTERSECT`、`EXCEPT` 演算子を組み合わせた複数の `SELECT` 式です。このクエリの結果は、モデルのテーブルまたはビューにデータを入力するために使用されます。

### SQL モデルのブループリント作成

SQL モデルは、`blueprints` プロパティにキーと値のマッピングのリストを指定することにより、複数のモデル（つまり「ブループリント」）を作成するためのテンプレートとしても機能します。これを実現するには、モデル名を、このマッピング内に存在する変数でパラメータ化する必要があります。

例えば、次のモデルは `blueprints` プロパティ内の対応するマッピングを使用する 2 つの新しいモデルを生成します。

```sql linenums="1"
MODEL (
  name @customer.some_table,
  kind FULL,
  blueprints (
    (customer := customer1, field_a := x, field_b := y),
    (customer := customer2, field_a := z, field_b := w)
  )
);

SELECT
  @field_a,
  @{field_b} AS field_b
FROM @customer.some_source
```

このテンプレートから生成される 2 つのモデルは次のとおりです。

```sql linenums="1"
-- This uses the first variable mapping
MODEL (
  name customer1.some_table,
  kind FULL
);

SELECT
  'x',
  y AS field_b
FROM customer1.some_source

-- This uses the second variable mapping
MODEL (
  name customer2.some_table,
  kind FULL
);

SELECT
  'z',
  w AS field_b
FROM customer2.some_source
```

上記のモデルクエリでは、中括弧構文 `@{field_b} AS field_b` が使用されていることに注意してください。これは、レンダリングされた変数値を文字列リテラルではなく SQL 識別子として扱うように SQLMesh に指示するために使用されます。

最初のレンダリングモデルで、この異なる動作を確認できます。`@field_a` は文字列リテラル `'x'`（一重引用符付き）に解決され、`@{field_b}` は識別子 `y`（引用符なし）に解決されます。中括弧構文の詳細については、[こちら](../../concepts/macros/sqlmesh_macros.md#embedding-variables-in-strings) を参照してください。

ブループリント変数のマッピングは、マクロ `blueprints @gen_blueprints()` を使用することで動的に構築することもできます。これは、`blueprints` リストを CSV ファイルなどの外部ソースから取得する必要がある場合に便利です。

たとえば、`gen_blueprints` の定義は次のようになります。

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

```sql linenums="1"
MODEL (
  name @customer.some_table,
  kind FULL,
  blueprints @EACH(@values, x -> (customer := schema_@x)),
);

SELECT
  1 AS c
```

## Python ベースの定義

SQL モデルを Python ベースで定義するには、SQLMesh の `@model` [デコレータ](https://wiki.python.org/moin/PythonDecorators) でデコレートされた単一の Python 関数を使用します。このデコレータは、DataFrame インスタンスを返す [Python モデル](./python_models.md) と区別するために、`is_sql` キーワード引数を `True` に設定する必要があります。

この関数の戻り値はモデルのクエリとして機能し、SQL 文字列または [SQLGlot 式](https://github.com/tobymao/sqlglot/blob/main/sqlglot/expressions.py) のいずれかである必要があります。`@model` デコレータは、モデルの [メタデータ](#MODEL-DDL) と、オプションで SQL 文字列または SQLGlot 式の pre/post ステートメントまたは on-virtual-update ステートメントを定義するために使用されます。

SQL モデルを Python で定義すると、クエリが複雑すぎて SQL で簡潔に表現できない場合（例えば、[マクロ](../macros/overview/) を多用する必要がある動的コンポーネントが多数ある場合など）に役立ちます。Python ベースのモデルは SQL を生成するため、列レベルの [lineage](../glossary/#lineage) など、通常の SQL モデルと同じ機能をサポートします。

Python ベースのモデルを作成するには、SQLMesh プロジェクト内の `models/` ディレクトリ（または `models/` のサブディレクトリ）に、`.py` サフィックスを持つ新しいファイルを追加します。Python ベースのモデルのファイル命名規則は、SQL ベースのモデルと同様です。このファイル内で、以下の例に示すように、1 つの `evaluator` 引数を持つ `entrypoint` という関数を定義します。

### 例

以下の例は、SQLGlot の `Expression` ビルダーメソッドを使用して、上記の `db.customers` モデルを Python ベースのモデルとして定義する方法を示しています。

```python linenums="1"
from sqlglot import exp

from sqlmesh.core.model import model
from sqlmesh.core.macros import MacroEvaluator

@model(
    "db.customers",
    is_sql=True,
    kind="FULL",
    pre_statements=["CACHE TABLE countries AS SELECT * FROM raw.countries"],
    post_statements=["UNCACHE TABLE countries"],
    on_virtual_update=["GRANT SELECT ON VIEW @this_model TO ROLE dev_role"],
)
def entrypoint(evaluator: MacroEvaluator) -> str | exp.Expression:
    return (
        exp.select("r.id::int", "r.name::text", "c.country::text")
        .from_("raw.restaurants as r")
        .join("countries as c", on="r.id = c.restaurant_id")
    )
```

このモデルは、SQLベースの例のSQLクエリを含む文字列を返すだけで定義できます。Pythonベースのモデルで前後文や戻り値として使用される文字列はSQLGlot式に解析されるため、SQLMeshはそれらを意味的に理解し、列レベルの系統などの情報を提供できます。

!!! note

    Python モデルはマクロ評価コンテキスト (`MacroEvaluator`) にアクセスできるため、`columns_to_types` メソッドを通じて [モデル スキーマにアクセス](../macros/sqlmesh_macros.md#accessing-model-schemas) することもできます。

### `@model` デコレータ

`@model` デコレータは、Python における `MODEL` DDL に相当します。

モデルのメタデータと設定情報に加えて、キーワード引数 `pre_statements`、`post_statements`、`on_virtual_update` に SQL 文字列または SQLGlot 式のリストを設定することで、それぞれモデルの事前/事後ステートメントと仮想更新時ステートメントを定義することができます。

!!! note

    すべての [メタデータ プロパティ](./overview.md#model-properties) フィールド名は、`MODEL` DDL のものと同じです。

### Python モデルのブループリント作成

Python ベースの SQL モデルは、`blueprints` プロパティにキーと値の辞書のリストを指定することにより、複数のモデル（つまり「ブループリント」）を作成するためのテンプレートとしても機能します。これを実現するには、モデル名をこのマッピング内に存在する変数でパラメータ化する必要があります。

例えば、次のモデルは `blueprints` プロパティ内の対応するマッピングを使用する 2 つの新しいモデルを生成します。

```python linenums="1"
from sqlglot import exp

from sqlmesh.core.model import model
from sqlmesh.core.macros import MacroEvaluator

@model(
    "@{customer}.some_table",
    is_sql=True,
    kind="FULL",
    blueprints=[
        {"customer": "customer1", "field_a": "x", "field_b": "y"},
        {"customer": "customer2", "field_a": "z", "field_b": "w"},
    ],
)
def entrypoint(evaluator: MacroEvaluator) -> str | exp.Expression:
    field_a = evaluator.blueprint_var("field_a")
    field_b = evaluator.blueprint_var("field_b")
    customer = evaluator.blueprint_var("customer")

    return exp.select(field_a, field_b).from_(f"{customer}.some_source")
```

このテンプレートから生成される2つのモデルは、SQLベースのブループリントの[例](#SQL-model-blueprinting)と同じです。

ブループリント変数のマッピングは、マクロ「blueprints="@gen_blueprints()"」などを使用して動的に構築することもできます。これは、「blueprints」リストをCSVファイルなどの外部ソースから取得する必要がある場合に便利です。

例えば、「gen_blueprints」の定義は次のようになります。

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
    is_sql=True,
    blueprints="@EACH(@values, x -> (customer := schema_@x))",
    ...
)
...
```

## 自動依存関係

SQLMesh は SQL を解析し、コードの動作や他のモデルとの関連性を理解します。特別なタグやコマンドを使って他のモデルへの依存関係を手動で指定する必要はありません。

例えば、次のクエリを持つモデルを考えてみましょう。

```sql linenums="1"
SELECT employees.id
FROM employees
JOIN countries
  ON employees.id = countries.employee_id
```

SQLMesh は、モデルが `employees` と `countries` の両方に依存していることを検出します。このモデルを実行する際、`employees` と `countries` が最初に実行されるようにします。

SQLMesh で定義されていない外部依存関係もサポートされています。SQLMesh は、実行順序によって暗黙的に依存関係に依存するか、[シグナル](../../guides/signals.md) を通じて依存関係に依存することができます。

自動依存関係検出はほとんどの場合に機能しますが、依存関係を手動で定義する必要がある特定のケースもあります。[dependencies プロパティ](./overview.md#properties) を使用して、`MODEL` DDL で依存関係を手動で定義できます。

## 規則

SQLMesh では、キャストによってモデルの列のデータ型を明示的に指定することを推奨しています。これにより、SQLMesh はモデル内のデータ型を理解できるようになり、誤った型推論を防ぐことができます。SQLMesh は、あらゆる SQL 方言のモデルで、キャスト形式 `<列名>::<データ型>` をサポートしています。

### 明示的な SELECT

`SELECT *` は便利ですが、モデルの結果は外部要因（上流ソースによる列の追加または削除など）によって変化する可能性があるため、危険です。一般的には、必要なすべての列をリストするか、[`create_external_models`](../../reference/cli.md#create_external_models) を使用して外部データソースのスキーマを取得することを推奨します。

外部ソースから選択する場合、`SELECT *` は SQLMesh による一部の最適化手順の実行と、上流の列レベルの系統の判定を妨げます。外部ソースの最適化と上流の列レベルのリネージを有効にするには、[`external` モデル種別](./model_kinds.md#external) を使用してください。

### エンコード

SQLMesh では、SQL モデルを含むファイルが [UTF-8](https://en.wikipedia.org/wiki/UTF-8) 標準に従ってエンコードされていることを前提としています。異なるエンコードを使用すると、予期しない動作が発生する可能性があります。

## トランスパイル

SQLMesh は [SQLGlot](https://github.com/tobymao/sqlglot) を利用して SQL を解析およびトランスパイルします。そのため、サポートされている任意の方言で SQL を記述し、別のサポートされている方言にトランスパイルできます。

また、選択したエンジンでは利用できない高度な構文も使用できます。例えば、`x::int` は `CAST(x as INT)` と同等ですが、一部の方言でのみサポートされています。SQLGlot を使用すると、使用しているエンジンに関係なくこの機能を使用できます。

さらに、末尾のカンマなどの細かい書式の違いは、SQLGlot が解析時に削除するため、心配する必要はありません。

## マクロ

標準SQLは非常に強力ですが、複雑なデータシステムでは、日付フィルターなどの動的なコンポーネントを含むSQLクエリの実行が必要になることがよくあります。例えば、最新のデータバッチを取得するために、`between`ステートメントの日付範囲を変更したい場合があります。SQLMeshは、[マクロ変数](../macros/macro_variables.md)を通じてこれらの日付を自動的に提供します。

さらに、大規模なクエリは読みにくく、保守も困難になる場合があります。クエリをよりコンパクトにするために、SQLMeshは強力な[マクロ構文](../macros/overview.md)と[Jinja](https://jinja.palletsprojects.com/en/3.1.x/)をサポートしており、SQLクエリの管理を容易にするマクロを作成できます。
