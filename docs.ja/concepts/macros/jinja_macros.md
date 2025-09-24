# Jinja マクロ

SQLMesh は [Jinja](https://jinja.palletsprojects.com/en/3.1.x/) テンプレートシステムのマクロをサポートしています。

Jinja のマクロのアプローチは、純粋な文字列置換です。SQLMesh マクロとは異なり、セマンティック表現を構築することなく SQL クエリテキストを組み立てます。

**注意:** SQLMesh プロジェクトは標準の Jinja 関数ライブラリのみをサポートしています。`{{ ref() }}` などの dbt 固有の Jinja 関数は**サポートしていません**。dbt 固有の関数は、[SQLMesh アダプタ](../../integrations/dbt.md) を使用して実行される dbt プロジェクトで使用できます。

## 基本

Jinja は、マクロテキストと非マクロテキストを区別するために中括弧 `{}` を使用します。左中括弧の後の 2 番目の文字によって、中括弧内のテキストの動作が決まります。

中括弧には以下の 3 つの記号があります。

- `{{...}}` は Jinja 式を作成します。式は、レンダリングされた SQL クエリに組み込まれるテキストに置き換えられます。式にはマクロ変数と関数を含めることができます。
- `{%...%}` は Jinja 文を作成します。文は、変数値の設定、`if` ループや `for` ループによるフロー制御、マクロ関数の定義など、Jinja に指示を与えます。
- `{#...#}` は Jinja コメントを作成します。これらのコメントは、レンダリングされた SQL クエリには含まれません。

Jinja 文字列は構文的に有効な SQL 式ではなく、そのまま解析することもできないため、モデルクエリは特別な `JINJA_QUERY_BEGIN; ...; で囲む必要があります。 SQLMesh がこれを検出できるように、`JINJA_END;` ブロックを追加します。

```sql linenums="1" hl_lines="5 9"
MODEL (
  name sqlmesh_example.full_model
);

JINJA_QUERY_BEGIN;

SELECT {{ 1 + 1 }};

JINJA_END;
```

同様に、モデル クエリの前または後に評価されるステートメントの一部として Jinja 式を使用するには、`JINJA_STATEMENT_BEGIN; ...; JINJA_END;` ブロックを使用する必要があります。

```sql linenums="1"
MODEL (
  name sqlmesh_example.full_model
);

JINJA_STATEMENT_BEGIN;
{{ pre_hook() }}
JINJA_END;

JINJA_QUERY_BEGIN;
SELECT {{ 1 + 1 }};
JINJA_END;

JINJA_STATEMENT_BEGIN;
{{ post_hook() }}
JINJA_END;
```

## SQLMesh 定義済み変数

SQLMesh は、Jinja コードで参照できる複数の [定義済みマクロ変数](./macro_variables.md) を提供しています。

一部の定義済み変数は、SQLMesh プロジェクト自体に関する情報を提供します。たとえば、[`runtime_stage`](./macro_variables.md#runtime-variables) や [`this_model`](./macro_variables.md#runtime-variables) などです。

その他の定義済み変数には、[temporal](./macro_variables.md#temporal-variables) があり、`start_ds` や `execution_date` などが挙げられます。これらは増分モデルクエリの構築に使用され、増分モデルの種類でのみ使用できます。

定義済みマクロ変数にアクセスするには、引用符で囲まない名前を中括弧で囲んで渡します。たとえば、`start_ds` 変数と `end_ds` 変数にアクセスする方法は次のとおりです。

```sql linenums="1"
JINJA_QUERY_BEGIN;

SELECT *
FROM table
WHERE time_column BETWEEN '{{ start_ds }}' and '{{ end_ds }}';

JINJA_END;
```

2 つのマクロ変数は文字列値を返すため、中括弧を一重引用符 `'` で囲む必要があります。`start_epoch` などの他のマクロ変数は数値を返すため、一重引用符は不要です。

`gateway` 変数は関数呼び出しであるため、他の定義済み変数とは若干異なる構文を使用します。`{{ gateway }}` という単純な名前ではなく、`{{ gateway() }}` のように括弧で囲む必要があります。

## ユーザー定義変数

SQLMesh は、グローバルとローカルの 2 種類のユーザー定義マクロ変数をサポートしています。

グローバルマクロ変数はプロジェクト設定ファイルで定義され、どのプロジェクトモデルからでもアクセスできます。

ローカルマクロ変数はモデル定義で定義され、そのモデル内でのみアクセスできます。

### グローバル変数

グローバル変数の定義の詳細については、[SQLMesh マクロのドキュメント](./sqlmesh_macros.md#global-variables) を参照してください。

モデル定義内のグローバル変数値にアクセスするには、`{{ var() }}` jinja関数を使用します。この関数では、最初の引数として変数名（一重引用符で囲む）を指定し、2番目の引数としてオプションのデフォルト値を指定します。デフォルト値は、プロジェクト設定ファイルに変数名が見つからない場合に使用される安全機構です。

例えば、モデルは次のように `int_var` というグローバル変数にアクセスします。

```sql linenums="1"
JINJA_QUERY_BEGIN;

SELECT *
FROM table
WHERE int_variable = {{ var('int_var') }};

JINJA_END;
```

`{{ var() }}` jinja 関数の 2 番目の引数としてデフォルト値を渡すことができ、設定ファイルに変数が定義されていない場合にフォールバック値として使用されます。

この例では、プロジェクト設定ファイルに `missing_var` という変数が定義されていない場合、`WHERE` 句は `WHERE some_value = 0` と表示されます。

```sql linenums="1"
JINJA_QUERY_BEGIN;

SELECT *
FROM table
WHERE some_value = {{ var('missing_var', 0) }};

JINJA_END;
```

### ゲートウェイ変数

グローバル変数と同様に、ゲートウェイ変数はプロジェクト設定ファイルで定義されます。ただし、ゲートウェイ変数は特定のゲートウェイの `variables` キーで指定します。ゲートウェイ変数の定義方法の詳細については、[SQLMesh マクロのドキュメント](./sqlmesh_macros.md#gateway-variables) を参照してください。

モデル内のゲートウェイ変数には、[グローバル変数](#global-variables) と同じ方法でアクセスします。

ゲートウェイ固有の変数値は、設定ファイルのルート `variables` キーで指定された同じ名前の変数よりも優先されます。

### ブループリント変数

ブループリント変数は `MODEL` ステートメントのプロパティとして定義され、[モデルテンプレートの作成](../models/sql_models.md) のメカニズムとして機能します。

```sql linenums="1"
MODEL (
  name @customer.some_table,
  kind FULL,
  blueprints (
    (customer := customer1, field_a := x, field_b := y),
    (customer := customer2, field_a := z)
  )
);

JINJA_QUERY_BEGIN;
SELECT
  {{ blueprint_var('field_a') }}
  {{ blueprint_var('field_b', 'default_b') }} AS field_b
FROM {{ blueprint_var('customer') }}.some_source
JINJA_END;
```

ブループリント変数には、`{{ blueprint_var() }}` マクロ関数を使用してアクセスできます。このマクロ関数は、変数が未定義の場合にデフォルト値を指定することもできます（`{{ var() }}` と同様）。

### ローカル変数

Jinja ステートメント `{% set ... %}` を使用して、独自の変数を定義します。例えば、`sqlmesh_example.full_model` の `num_orders` 列の名前を次のように指定できます。

```sql linenums="1"
MODEL (
  name sqlmesh_example.full_model,
  kind FULL,
  cron '@daily',
  audits (assert_positive_order_ids),
);

JINJA_QUERY_BEGIN;

{% set my_col = 'num_orders' %} -- Jinja definition of variable `my_col`

SELECT
  item_id,
  count(distinct id) AS {{ my_col }}, -- Reference to Jinja variable {{ my_col }}
FROM
  sqlmesh_example.incremental_model
GROUP BY item_id

JINJA_END;
```

Jinja の set 文は `MODEL` 文の後、SQL クエリの前に記述されていることに注意してください。

Jinja 変数は、文字列、整数、または浮動小数点のデータ型にすることができます。また、リスト、タプル、辞書などの反復可能なデータ構造にすることもできます。これらのデータ型と構造はそれぞれ、文字列の `upper()` メソッドなど、複数の [Python メソッド](https://jinja.palletsprojects.com/en/3.1.x/templates/#python-methods) をサポートしています。

## マクロ演算子

### 制御フロー演算子

#### for ループ

for ループを使用すると、一連の項目を反復処理することで繰り返しコードを圧縮し、コードで使用される値を簡単に変更できます。

Jinja の for ループは `{% for ... %}` で始まり `{% endfor %}` で終わります。次の例は、Jinja の for ループを使用して `CASE WHEN` でインジケータ変数を作成する方法を示しています。

```sql linenums="1"
SELECT
  {% for vehicle_type in ['car', 'truck', 'bus']}
    CASE WHEN user_vehicle = '{{ vehicle_type }}' THEN 1 ELSE 0 END as vehicle_{{ vehicle_type }},
  {% endfor %}
FROM table
```

リスト `['car', 'truck', 'bus']` 内の `vehicle_type` の値が引用符で囲まれていることに注意してください。Jinja は処理中にこれらの引用符を削除するため、`CASE WHEN` 文内の `'{{ vehicle_type }}` 参照は引用符で囲む必要があります。`vehicle_{{ vehicle_type }}` 参照には引用符は不要です。

また、`CASE WHEN` 行の末尾にカンマがあることにも注意してください。末尾のカンマは有効な SQL ではなく、通常は特別な処理が必要ですが、SQLMesh はクエリの意味を理解するため、問題のあるカンマを識別して削除できます。

SQLMesh による処理後、この例は次のようにレンダリングされます。

```sql linenums="1"
SELECT
  CASE WHEN user_vehicle = 'car' THEN 1 ELSE 0 END AS vehicle_car,
  CASE WHEN user_vehicle = 'truck' THEN 1 ELSE 0 END AS vehicle_truck,
  CASE WHEN user_vehicle = 'bus' THEN 1 ELSE 0 END AS vehicle_bus
FROM table
```

一般的に、値のリストとその用途を別々に定義するのがベストプラクティスです。例えば、次のように定義できます。

```sql linenums="1"
{% set vehicle_types = ['car', 'truck', 'bus'] %}

SELECT
  {% for vehicle_type in vehicle_types }
    CASE WHEN user_vehicle = '{{ vehicle_type }}' THEN 1 ELSE 0 END as vehicle_{{ vehicle_type }},
  {% endfor %}
FROM table
```

レンダリングされたクエリは以前と同じになります。

#### if

if ステートメントを使用すると、何らかの条件に基づいてアクションを実行する（または実行しない）ことができます。

Jinja の if ステートメントは `{% if ... %}` で始まり `{% endif %}` で終わります。開始の `if` ステートメントには、`True` または `False` に評価されるコードを含める必要があります。たとえば、`True`、`1 + 1 == 2`、`'a' in ['a', 'b']` はすべて `True` と評価されます。

例えば、モデルをテスト目的で実行する場合のみ、モデルに列を含めたいとします。これは、クエリに `testing_column` を含めるかどうかを決定する、テスト実行かどうかを示す変数を設定することで実現できます。

```sql linenums="1"
{% set testing = True %}

SELECT
  normal_column,
  {% if testing %}
    testing_column
  {% endif %}
FROM table
```

`testing` は `True` なので、レンダリングされたクエリは次のようになります。

```sql linenums="1"
SELECT
  normal_column,
  testing_column
FROM table
```

## ユーザー定義マクロ関数

ユーザー定義マクロ関数を使用すると、同じマクロコードを複数のモデルで使用できます。

Jinja マクロ関数は、SQLMesh プロジェクトの `macros` ディレクトリ内の `.sql` ファイルに配置する必要があります。複数の関数を 1 つの `.sql` ファイルに定義することも、複数のファイルに分散させることもできます。

Jinja マクロ関数は、`{% macro %}` および `{% endmacro %}` ステートメントで定義します。マクロ関数名と引数は、`{% macro %}` ステートメントで指定します。

例えば、引数を取らない `print_text` というマクロ関数は、次のように定義できます。

```sql linenums="1"
{% macro print_text() %}
text
{% endmacro %}
```

このマクロ関数は、SQL モデル内で `{{ print_text() }}` を使用して呼び出され、レンダリングされたクエリでは `text` に置き換えられます。

マクロ関数の引数は、マクロ名の横の括弧内に配置されます。例えば、次のマクロは、引数 `expression` と `alias` に基づいて、別名を持つ SQL 列を生成します。

```sql linenums="1"
{% macro alias(expression, alias) %}
  {{ expression }} AS {{ alias }}
{% endmacro %}
```

このマクロ関数は、次のように SQL クエリで呼び出すことができます。

```sql linenums="1"
SELECT
  item_id,
  {{ alias('item_id', 'item_id2')}}
FROM table
```

処理後は次のようにレンダリングされます。

```sql linenums="1"
SELECT
  item_id,
  item_id AS item_id2
FROM table
```

両方の引数値は `alias('item_id', 'item_id2')` という呼び出しでは引用符で囲まれていますが、レンダリングされたクエリでは引用符で囲まれていないことに注意してください。レンダリング処理中、SQLMesh はクエリのセマンティック理解に基づいてレンダリングされたテキストを構築します。つまり、最初の引数が列名であり、列のエイリアスはデフォルトで引用符で囲まれていないことを認識します。

この例では、SQL クエリはエイリアス `item_id2` を持つ列 `item_id` を選択します。代わりに、名前 `item_id2` を持つ *文字列* `'item_id'` を選択したい場合は、`expression` 引数を二重引用符で囲んで渡します（`"'item_id'"`）。

```sql linenums="1"
SELECT
  item_id,
  {{ alias("'item_id'", 'item_id2')}}
FROM table
```

処理後は次のようにレンダリングされます。

```sql linenums="1"
SELECT
  item_id,
  'item_id' AS item_id2
FROM table
```

`"'item_id'"` を囲む二重引用符は、SQLMesh にそれが列名ではないことを伝えます。

一部の SQL 方言では、二重引用符と一重引用符の解釈が異なります。前の例で、マクロ関数呼び出しの引用符の配置を入れ替えることで、一重引用符で囲まれた `'item_id'` を二重引用符で囲まれた `"item_id"` に置き換えることができます。`alias("'item_id'", 'item_id2')` の代わりに、`alias('"item_id"', 'item_id2')` を使用します。

## マクロシステムの混在

SQLMesh は Jinja と [SQLMesh](./sqlmesh_macros.md) の両方のマクロシステムをサポートしています。1 つのモデルではど​​ちらか一方のシステムのみを使用することを強くお勧めします。両方使用すると、エラーが発生したり、直感的でない動作をしたりする可能性があります。

[定義済み SQLMesh マクロ変数](./macro_variables.md) は、ユーザー定義の Jinja 変数と関数を含むクエリで使用できます。ただし、ユーザー定義の Jinja マクロ関数に引数として渡される定義済み変数には、SQLMesh マクロの `@` プレフィックス構文 `@start_ds` ではなく、Jinja の中括弧構文 `{{ start_ds }}` を使用する必要があります。中括弧構文では、`@` 構文と同等の構文を生成するために引用符で囲む必要がある場合があることに注意してください。
