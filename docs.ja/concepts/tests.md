# テスト

テストでは、各モデルの出力が期待どおりであることを継続的に検証することで、プロジェクトの回帰を防ぐことができます。[監査](audits.md)とは異なり、テストはオンデマンド（CI/CDジョブの一環としてなど）または新しい[プラン](plans.md)が作成されるたびに実行されます。

ソフトウェア開発におけるユニットテストと同様に、SQLMeshは事前定義された入力に対してモデルのロジックを評価し、その出力を各テストで提供される期待される結果と比較します。

包括的なテストスイートにより、データ担当者はモデルに変更を適用した後も期待どおりに動作することを確認できるため、自信を持って作業を進めることができます。

## テストの作成

テストスイートは、SQLMesh プロジェクトの `tests/` フォルダに含まれる [YAML ファイル](https://learnxinyminutes.com/docs/yaml/) です。名前は `test` で始まり、`.yaml` または `.yml` で終わります。テストスイートには、一意の名前を持つ 1 つ以上の単体テストを含めることができ、各テストには動作を定義する複数の属性が含まれます。

単体テストでは、少なくとも、テスト対象のモデル、その上流モデルへの入力値、対象モデルのクエリまたは [共通テーブル式](glossary.md#cte) の期待される出力を指定する必要があります。その他のオプション属性には、説明、使用するゲートウェイ、モデルで参照される [マクロ変数](macros/macro_variables.md) に値を割り当てるマッピングなどがあります。

サポートされている属性の詳細については、[単体テストの構造セクション](#unit-test-structure) を参照してください。

### 例

この例では、`sqlmesh_example.full_model` モデルを使用します。このモデルは `sqlmesh init` コマンドの一部として提供され、次のように定義されています。

```sql linenums="1"
MODEL (
  name sqlmesh_example.full_model,
  kind FULL,
  cron '@daily',
  grain item_id,
  audits (assert_positive_order_ids),
);

SELECT
  item_id,
  COUNT(DISTINCT id) AS num_orders,
FROM
  sqlmesh_example.incremental_model
GROUP BY item_id
```

このモデルは、上流の `sqlmesh_example.incremental_model` から `item_id` ごとの注文数を集計します。テスト方法の一例を以下に示します。

```yaml linenums="1"
test_example_full_model:
  model: sqlmesh_example.full_model
  inputs:
    sqlmesh_example.incremental_model:
      rows:
      - id: 1
        item_id: 1
      - id: 2
        item_id: 1
      - id: 3
        item_id: 2
  outputs:
    query:
      rows:
      - item_id: 1
        num_orders: 2
      - item_id: 2
        num_orders: 1
```

このテストは、`sqlmesh_example.full_model` が `item_id` ごとに注文数を正しくカウントすることを検証します。`sqlmesh_example.incremental_model` への入力として3行を提供し、ターゲットモデルのクエリからの出力として2行を期待します。

### CTE のテスト

モデルのクエリ内の個々の CTE もテストできます。これを実証するために、`sqlmesh_example.full_model` のクエリを少し変更して、`filtered_orders_cte` という CTE を追加してみましょう。

```sql linenums="1"
WITH filtered_orders_cte AS (
  SELECT
    id,
    item_id
  FROM
    sqlmesh_example.incremental_model
  WHERE
    item_id = 1
)
SELECT
  item_id,
  COUNT(DISTINCT id) AS num_orders,
FROM
  filtered_orders_cte
GROUP BY item_id
```

次のテストは、集約が行われる前にこの CTE の出力を検証します。

```yaml linenums="1" hl_lines="13-19"
test_example_full_model:
  model: sqlmesh_example.full_model
  inputs:
    sqlmesh_example.incremental_model:
        rows:
        - id: 1
          item_id: 1
        - id: 2
          item_id: 1
        - id: 3
          item_id: 2
  outputs:
    ctes:
      filtered_orders_cte:
        rows:
          - id: 1
            item_id: 1
          - id: 2
            item_id: 1
    query:
      rows:
      - item_id: 1
        num_orders: 2
```

## サポートされているデータ形式

SQLMesh は現在、ユニットテストで入出力データを定義する以下の方法をサポートしています。

1. 各行の列と値がマッピングされた YAML 辞書をリストする
2. 行をカンマ区切り値 (CSV) としてリストする
3. テスト接続に対して SQL クエリを実行してデータを生成する

前の例では、ユニットテストでデータを定義するデフォルトの方法である最初の方法を示しました。以降の例では、残りの方法について説明します。

### データをCSVとして定義する

最初の[例](#例)と同じテストを、入力データをCSV形式で定義する方法は次のとおりです。

```yaml linenums="1"
test_example_full_model:
  model: sqlmesh_example.full_model
  inputs:
    sqlmesh_example.incremental_model:
      format: csv
      rows: |
        id,item_id
        1,1
        2,1
        3,2
  outputs:
    query:
      rows:
      - item_id: 1
        num_orders: 2
      - item_id: 2
        num_orders: 1
```

### SQLクエリを使用したデータ生成

最初の[例](#例)と同じテストを、SQLクエリから生成された入力データを使って定義する方法は次のとおりです。

```yaml linenums="1"
test_example_full_model:
  model: sqlmesh_example.full_model
  inputs:
    sqlmesh_example.incremental_model:
      query: |
        SELECT 1 AS id, 1 AS item_id
        UNION ALL
        SELECT 2 AS id, 1 AS item_id
        UNION ALL
        SELECT 3 AS id, 2 AS item_id
  outputs:
    query:
      rows:
      - item_id: 1
        num_orders: 2
      - item_id: 2
        num_orders: 1
```

## ファイルを使用したデータ入力

SQLMesh は外部ファイルからのデータの読み込みをサポートしています。これを行うには、読み込むデータのパス名を指定する `path` 属性を使用します。

```yaml linenums="1"
test_example_full_model:
  model: sqlmesh_example.full_model
  inputs:
    sqlmesh_example.incremental_model:
      format: csv
      path: filepath/test_data.csv
```

`format` を省略すると、ファイルは YAML ドキュメントとして読み込まれます。

## 列の省略

幅の広いテーブル、つまり列数の多いテーブルでは、完全な入力と期待される出力を定義するのは面倒な場合があります。そのため、特定の列を無視しても問題ない場合は、任意の行からその列を省略し、その行の値を `NULL` として扱うことができます。

さらに、対象の出力に対して `partial` を `true` に設定することで、出力列のサブセットのみをテストすることも可能です。

```yaml linenums="1"
  outputs:
    query:
      partial: true
      rows:
        - <column_name>: <column_value>
          ...
```

これは、欠落した列を `NULL` として扱うことができないが、無視したい場合に便利です。この設定をすべての期待される出力に適用するには、`outputs` キーの下に設定してください。

```yaml linenums="1"
  outputs:
    partial: true
    ...
```

## 時間の凍結

一部のモデルでは、`CURRENT_TIMESTAMP` など、特定の時点の日付時刻値を計算する SQL 式が使用される場合があります。これらの式は非決定論的であるため、期待される出力値を指定するだけではテストに不十分です。

`execution_time` マクロ変数を設定することで、テストのコンテキストで現在の時刻をモック化し、その値を決定論的にすることで、この問題に対処できます。

次の例は、`CURRENT_TIMESTAMP` を使用して計算された列を `execution_time` でテストする方法を示しています。テストするモデルは次のように定義されています。

```sql linenums="1"
MODEL (
  name colors,
  kind FULL
);

SELECT
  'Yellow' AS color,
  CURRENT_TIMESTAMP AS created_at
```

対応するテストは次のようになります。

```yaml linenums="1"
test_colors:
  model: colors
  outputs:
    query:
      - color: "Yellow"
        created_at: "2023-01-01 12:05:03"
  vars:
    execution_time: "2023-01-01 12:05:03"
```

`execution_time` にタイムゾーンを指定することも可能です。タイムゾーンはタイムスタンプ文字列に含めます。

タイムゾーンが指定されている場合、テストの期待される datetime 値はタイムゾーンを含まないタイムスタンプである必要があります。つまり、タイムゾーンに応じてオフセットを設定する必要があります。

上記のテストで時刻を UTC+2 に固定する場合、以下のように記述します。

```yaml linenums="1"
test_colors:
  model: colors
  outputs:
    query:
      - color: "Yellow"
        created_at: "2023-01-01 10:05:03"
  vars:
    execution_time: "2023-01-01 12:05:03+02:00"
```

## パラメータ化されたモデル名

`@{gold}.some_schema.some_table` のようなパラメータ化された名前を持つモデルは、Jinja を使用することでテストできます。

```yaml linenums="1"
test_parameterized_model:
  model: {{ var('gold') }}.some_schema.some_table
  ...
```

たとえば、`gold` が値 `gold_db` を持つ [config 変数](../reference/configuration.md#variables) であると仮定すると、上記のテストは次のようにレンダリングされます。

```yaml linenums="1"
test_parameterized_model:
  model: gold_db.some_schema.some_table
  ...
```

## 自動テスト生成

手動でテストを作成すると、繰り返し作業が多くなり、エラーが発生しやすくなります。そのため、SQLMesh では [`create_test` コマンド](../reference/cli.md#create_test) を使用してこのプロセスを自動化する方法も提供しています。

このコマンドは、上流モデルのテーブルがプロジェクトのデータウェアハウスに存在し、既にデータが入力されている限り、特定のモデルに対して完全なテストを生成できます。

### 例

この例では、`sqlmesh_example.incremental_model` のテストを生成する方法を示します。これは `sqlmesh init` コマンドの一部として提供される別のモデルであり、次のように定義されています。

```sql linenums="1"
MODEL (
  name sqlmesh_example.incremental_model,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column event_date
  ),
  start '2020-01-01',
  cron '@daily',
  grain (id, event_date)
);

SELECT
  id,
  item_id,
  event_date,
FROM
  sqlmesh_example.seed_model
WHERE
  event_date BETWEEN @start_date AND @end_date
```

まず、上流モデル `sqlmesh_example.seed_model` の入力データを指定する必要があります。`create_test` コマンドは、プロジェクトのデータ ウェアハウスに対してユーザー指定のクエリを実行してこのデータを取得することから始まります。

たとえば、次のクエリは、モデル `sqlmesh_example.seed_model` に対応するテーブルから 3 つの行を返します。

```sql linenums="1"
SELECT * FROM sqlmesh_example.seed_model LIMIT 3
```

次に、`sqlmesh_example.incremental_model` に、`@start_date` と `@end_date` [マクロ変数](macros/macro_variables.md) を参照するフィルターが含まれていることに注目してください。

生成されたテストを決定論的にし、常に成功するようにするには、これらの変数を定義し、上記のクエリを修正して `event_date` をそれに応じて制約する必要があります。

`@start_date` を `'2020-01-01'` に、`@end_date` を `'2020-01-04'` に設定する場合、上記のクエリを次のように変更する必要があります。

```sql linenums="1"
SELECT * FROM sqlmesh_example.seed_model WHERE event_date BETWEEN '2020-01-01' AND '2020-01-04' LIMIT 3
```

最後に、適切なマクロ変数定義と組み合わせることで、モデルのクエリに対する期待出力を計算し、完全なテストを生成できます。

これは次のコマンドで実現できます。

```
$ sqlmesh create_test sqlmesh_example.incremental_model --query sqlmesh_example.seed_model "SELECT * FROM sqlmesh_example.seed_model WHERE event_date BETWEEN '2020-01-01' AND '2020-01-04' LIMIT 3" --var start '2020-01-01' --var end '2020-01-04'
```

これを実行すると、`tests/test_incremental_model.yaml` に次の新しいテストが作成されます。

```yaml linenums="1"
test_incremental_model:
  model: sqlmesh_example.incremental_model
  inputs:
    sqlmesh_example.seed_model:
    - id: 1
      item_id: 2
      event_date: 2020-01-01
    - id: 2
      item_id: 1
      event_date: 2020-01-01
    - id: 3
      item_id: 3
      event_date: 2020-01-03
  outputs:
    query:
    - id: 1
      item_id: 2
      event_date: 2020-01-01
    - id: 2
      item_id: 1
      event_date: 2020-01-01
    - id: 3
      item_id: 3
      event_date: 2020-01-03
  vars:
    start: '2020-01-01'
    end: '2020-01-04'
```

ご覧のとおり、2 つのテストが合格しました。やったー!

```
$ sqlmesh test
.
----------------------------------------------------------------------
Ran 2 tests in 0.024s

OK
```

## 異なるテスト接続の使用

特定のテストに対してテスト接続を変更できます。これは、例えば、テスト対象のモデルをデフォルトのテストエンジンの方言に正しくトランスパイルできない場合などに便利です。

次の例では、`test_example_full_model` を変更して、プロジェクトの `config.yaml` ファイルで `spark_testing` ゲートウェイの `test_connection` として定義されたシングルスレッドのローカル Spark プロセスに対して実行するようにすることで、これを示しています。

```yaml linenums="1"
gateways:
  local:
    connection:
      type: duckdb
      database: db.db
  spark_testing:
    test_connection:
      type: spark
      config:
        # Run Spark locally with one worker thread
        "spark.master": "local"

        # Move data under /tmp so that it is only temporarily persisted
        "spark.sql.warehouse.dir": "/tmp/data_dir"
        "spark.driver.extraJavaOptions": "-Dderby.system.home=/tmp/derby_dir"

default_gateway: local

model_defaults:
  dialect: duckdb
```

テストは次のように更新されます。

```yaml linenums="1"
test_example_full_model:
  gateway: spark_testing
  # ... the other test attributes remain the same
```

## テストの実行

テストは新しい [プラン](plans.md) が作成されるたびに自動的に実行されますが、以下のセクションで説明するように、オンデマンドで実行することもできます。

### CLI を使用したテスト

次のように `sqlmesh test` コマンドを使用して、オンデマンドでテストを実行できます。

```
$ sqlmesh test
.
----------------------------------------------------------------------
Ran 1 test in 0.005s

OK
```

このコマンドは、失敗があった場合にはゼロ以外の終了コードを返し、標準エラー ストリームにそれを報告します。

```
$ sqlmesh test
F
======================================================================
FAIL: test_example_full_model (test/tests/test_full_model.yaml)
----------------------------------------------------------------------
AssertionError: Data mismatch (exp: expected, act: actual)

  num_orders
         exp  act
0        3.0  2.0

----------------------------------------------------------------------
Ran 1 test in 0.012s

FAILED (failures=1)
```

注: 異なる列が多数ある場合、対応するデータフレームはデフォルトで切り捨てられます。列全体を表示するには、`sqlmesh test` コマンドの `-v` (詳細) オプションを使用してください。

特定のモデルテストを実行するには、スイートファイル名に続けて `::` とテスト名を渡します。

```
$ sqlmesh test tests/test_full_model.yaml::test_example_full_model
```

glob パス名拡張構文を使用して、パターンまたは部分文字列に一致するテストを実行することもできます。

```
$ sqlmesh test tests/test_*
```

### ノートブックを使ったテスト

`%run_test` ノートブックマジックを使用して、次のようにオンデマンドでテストを実行できます。

```
# This import will register all needed notebook magics
In [1]: import sqlmesh
        %run_test

        ----------------------------------------------------------------------
        Ran 1 test in 0.018s

        OK
```

`%run_test` マジックは、対応する [CLI コマンド](#testing-using-the-CLI) と同じオプションをサポートします。

## 問題のトラブルシューティング

ユニットテストを実行する際、SQLMesh はテスト接続内に入力フィクスチャをビューとして作成します。

これらのフィクスチャは実行完了後にデフォルトで削除されますが、`sqlmesh test` CLI コマンドと `%run_test` ノートブックマジックの両方で利用可能な `--preserve-fixtures` オプションを使用することで保持できます。

これは、テストの失敗をデバッグする際に役立ちます。例えば、フィクスチャビューを直接クエリして、正しく定義されていることを確認できるからです。

!!! note
    デフォルトでは、ユニットテストの実行に必要なビューは、`sqlmesh_test_<random_ID>` のような名前の新しい一意のスキーマ内に作成されます。このスキーマにカスタム名を指定するには、[`<test_name>.schema`](#test_nameschema) テスト属性を設定します。

### 型の不一致

追加のコンテキストなしでは、ユニットテスト内の特定の値を正しく解釈できない場合があります。例えば、YAML辞書はSQLの`STRUCT`値と`MAP`値の両方を表すために使用できます。

この曖昧さを回避するために、SQLMeshは列の型を認識する必要があります。デフォルトでは、モデル定義に基づいてこれらの型を推論しようとしますが、明示的に指定することもできます。

- [`external_models.yaml`](models/external_models.md#generating-an-external-models-schema-file) ファイル内（外部モデルの場合）
- [`columns`](models/overview.md#columns) モデルプロパティを使用する
- ユニットテストの [`columns`](#creating_tests) 属性を使用する

これらのオプションがいずれも機能しない場合は、SQL [クエリ](#test_nameinputsupstream_modelquery) を使用してデータを生成することを検討してください。

## ユニットテストの構造

### `<test_name>`

テストの一意の名前。

### `<test_name>.model`

テスト対象のモデルの名前。このモデルは、プロジェクトの `models/` フォルダ内に定義されている必要があります。

### `<test_name>.description`

テストの説明（任意）。追加のコンテキストを提供するために使用できます。

### `<test_name>.schema`

このユニットテストの実行に必要なビューを含むスキーマの名前。

### `<test_name>.gateway`

このテストを実行するために `test_connection` が使用されるゲートウェイ。指定されていない場合は、デフォルトゲートウェイが使用されます。

### `<test_name>.inputs`

対象モデルのテストに使用される入力。モデルに依存関係がない場合は省略できます。

### `<test_name>.inputs.<upstream_model>`

ターゲットモデルが依存するモデル。

### `<test_name>.inputs.<upstream_model>.rows`

上流モデルの行。列とその値をマッピングする辞書の配列として定義されます。

```yaml linenums="1"
    <upstream_model>:
      rows:
        - <column_name>: <column_value>
        ...
```

`rows` が `<upstream_model>` の下の唯一のキーである場合は省略できます。

```yaml linenums="1"
    <upstream_model>:
      - <column_name>: <column_value>
      ...
```

入力形式が `csv` の場合、データは `rows` の下にインラインで指定できます。

```yaml linenums="1"
    <upstream_model>:
      rows: |
        <column1_name>,<column2_name>
        <row1_value>,<row1_value>
        <row2_value>,<row2_value>
```

### `<test_name>.inputs.<upstream_model>.format`
  
オプションの `format` キーを使用すると、入力データのロード方法を制御できます。

```yaml linenums="1"
    <upstream_model>:
      format: csv
```

現在、次の形式がサポートされています: `yaml` (デフォルト)、`csv`。

### `<test_name>.inputs.<upstream_model>.csv_settings`
  
`format` が CSV の場合、`csv_settings` でデータの読み込みの動作を制御できます。

```yaml linenums="1"
    <upstream_model>:
      format: csv
      csv_settings: 
        sep: "#"
        skip_blank_lines: true
      rows: |
        <column1_name>#<column2_name>
        <row1_value>#<row1_value>
        <row2_value>#<row2_value>
```

[サポートされている CSV 設定](https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html) の詳細をご覧ください。
  
### `<test_name>.inputs.<upstream_model>.path`

オプションの `path` キーは、ロードするデータのパス名を指定します。
  
```yaml linenums="1"
    <upstream_model>:
      path: filepath/test_data.yaml
```

### `<test_name>.inputs.<upstream_model>.columns`

列をその型にマッピングするオプションの辞書:

```yaml linenums="1"
    <upstream_model>:
      columns:
        <column_name>: <column_type>
        ...
```

これは、SQLMesh が SQL コンテキストで行の値を正しく解釈するのに役立ちます。

このマッピングから任意の数の列を省略できます。その場合、列の型はベストエフォートベースで推論されます。モデルのクエリで対応する列を明示的にキャストすることで、SQLMesh はより正確に型を推論できるようになります。

### `<test_name>.inputs.<upstream_model>.query`

入力行を生成するためにテスト接続に対して実行されるオプションの SQL クエリ:

```yaml linenums="1"
    <upstream_model>:
      query: <sql_query>
```

これにより、入力データの解釈方法をより細かく制御できます。

`query` キーは `rows` キーと一緒に使用することはできません。

### `<test_name>.outputs`

ターゲットモデルの期待される出力。

注: 期待される出力の各行の列は、対応するクエリで選択された順序と同じ相対順序で出現する必要があります。

### `<test_name>.outputs.partial`

出力列のサブセットのみをテストするかどうかを示すブール値フラグです。`true` に設定すると、対応する期待行で参照されている列のみがテストされます。

[列の省略](#omitting-columns)も参照してください。

### `<test_name>.outputs.query`

対象モデルのクエリの期待される出力。[`<test_name>.outputs.ctes`](#test_nameoutputsctes) が存在する限り、これはオプションです。

### `<test_name>.outputs.query.partial`

[`<test_name>.outputs.partial`](#test_nameoutputspartial) と同じですが、ターゲットモデルのクエリの出力にのみ適用されます。

### `<test_name>.outputs.query.rows`

ターゲットモデルのクエリの期待される行数です。

参照: [`<test_name>.inputs.<upstream_model>.rows`](#test_nameinputsupstream_modelrows)。

### `<test_name>.outputs.query.query`

ターゲットモデルのクエリの期待される行数を生成するために、テスト接続に対して実行されるオプションの SQL クエリです。

参照: [`<test_name>.inputs.<upstream_model>.query`](#test_nameinputsupstream_modelquery)。

### `<test_name>.outputs.ctes`

対象モデルのクエリで定義されている各トップレベルの[共通テーブル式](glossary.md#cte) (CTE) の期待出力。[`<test_name>.outputs.query`](#test_nameoutputsquery) が存在する限り、これはオプションです。

### `<test_name>.outputs.ctes.<cte_name>`

`<cte_name>` という名前の CTE の期待出力。

### `<test_name>.outputs.ctes.<cte_name>.partial`

[`<test_name>.outputs.partial`](#test_nameoutputs_partial) と同じですが、`<cte_name>` という名前の CTE の出力にのみ適用されます。

### `<test_name>.outputs.ctes.<cte_name>.rows`

`<cte_name>` という名前の CTE の期待される行数です。

参照: [`<test_name>.inputs.<upstream_model>.rows`](#test_nameinputsupstream_modelrows)。

### `<test_name>.outputs.ctes.<cte_name>.query`

`<cte_name` という名前の CTE の期待される行数を生成するために、テスト接続に対して実行されるオプションの SQL クエリです。

参照: [`<test_name>.inputs.<upstream_model>.query`](#test_nameinputsupstream_modelquery)。

### `<test_name>.vars`

マクロ変数に値を割り当てるオプションの辞書です。

```
  vars:
    start: 2022-01-01
    end: 2022-01-01
    execution_time: 2022-01-01
    <macro_variable_name>: <macro_variable_value>
```

特別なマクロ変数は3つあります。`start`、`end`、`execution_time`です。これらが設定されている場合、ターゲットモデルの対応する日付マクロがオーバーライドされます。例えば、`execution_time` がこの値に設定されている場合、`@execution_ds` は `2022-01-01` としてレンダリングされます。

さらに、`CURRENT_DATE` や `CURRENT_TIMESTAMP` などのSQL式は、`execution_time` が設定されている場合、それと同じ日時値を生成します。
