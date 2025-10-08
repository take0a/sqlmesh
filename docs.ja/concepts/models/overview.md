# 概要

モデルは、テーブルとビューを作成するメタデータとクエリで構成され、他のモデルやSQLMeshの外部でも使用できます。モデルはSQLMeshプロジェクトの`models/`ディレクトリに定義され、`.sql`ファイルに格納されます。

SQLMeshはSQLを解析することでモデル間の関係と系統を自動的に判断するため、依存関係を手動で設定する必要はありません。

## 例
以下はSQLで定義されたモデルの例です。以下の点に注意してください。

- モデルには、最初の行のように、説明的な情報をコメントとして含めることができます。
- ファイル内の最初の非コメント文は`MODEL` DDLです。
- 最後の非コメント文は、データを変換するロジックを含む`SELECT`クエリです。

```sql linenums="1"
-- Customer revenue computed and stored daily.
MODEL (
  name sushi.customer_total_revenue,
  owner toby,
  cron '@daily',
  grain customer_id
);

SELECT
  o.customer_id::TEXT,
  SUM(o.amount)::DOUBLE AS revenue
FROM sushi.orders AS o
GROUP BY o.customer_id;
```

## 規約

SQLMesh は、YAML などの別の形式への切り替えに伴う認知オーバーヘッドを削減するため、SQL のみでパイプラインについて可能な限り多くの情報を推測しようとします。

その方法の一つとして、SQL クエリからモデルの列名とデータ型を推測する方法があります。[`columns` モデルプロパティ](#columns) でモデルの列名とデータ型を手動で指定することで、この動作をモデルに対して無効にすることができます。

SQLMesh が動作に必要なメタデータを検出するには、モデルの `SELECT` 式が特定の規約に従う必要があります。

### 一意の列名

モデルのクエリの最後の `SELECT` には、一意の列名が含まれている必要があります。

### 明示的な型

SQLMesh では、モデルのクエリの最後の `SELECT` で明示的な型キャストを行うことが推奨されています。これは、モデルのテーブルのスキーマに予期しない型が含まれるのを防ぐためのベストプラクティスと考えられています。

SQLMesh はキャストに PostgreSQL の `x::int` 構文を使用します。キャストは実行エンジンに適した形式に自動的に変換されます。

```sql linenums="1"
WITH cte AS (
  SELECT 1 AS foo -- don't need to cast here
)
SELECT foo::int -- need to cast here because it's in the final select statement
```

### 推論可能な名前

モデルのクエリの最後の `SELECT` には、推論可能な名前またはエイリアスが必要です。

明示的なエイリアスの使用が推奨されますが、必須ではありません。SQLMesh フォーマッタは、モデルの SQL をレンダリングする際に、エイリアスのない列に自動的にエイリアスを追加します。

次の例は、推論不可能なエイリアス、推論可能なエイリアス、および明示的なエイリアスを示しています。

```sql linenums="1"
SELECT
  1, -- not inferrable
  x + 1, -- not inferrable
  SUM(x), -- not inferrable
  x, -- inferrable as x
  x::int, -- inferrable as x
  x + 1 AS x, -- explicitly x
  SUM(x) as x, -- explicitly x
```

### モデルの説明とコメント

モデルファイルには、モデルのSQL方言でサポートされている形式のSQLコメントを含めることができます。（コメントはほとんどの方言で `--` で始まるか、`/*` と `*/` で区切られます。）

一部のSQLエンジンは、テーブルまたはビューに関連付けられたメタデータとしてコメントを登録することをサポートしています。テーブルレベルのコメント（例："各顧客の売上データ"）や列レベルのコメント（例："顧客の一意のID"）をサポートしている場合があります。

SQLMeshは、エンジンがコメントをサポートし、[接続の `register_comments` 設定](../../reference/configuration.md#connection) が `true`（デフォルトは `true`）の場合、自動的にコメントを登録します。エンジンによってコメントのサポートは異なります。[以下の表](#engine-comment-support) を参照してください。

#### モデルコメント

SQLMesh は、`MODEL` DDL ブロックの前に指定されたコメントを、基盤となる SQL エンジンのテーブルコメントとして登録します。[`MODEL` DDL `description` フィールド](#description) も指定されている場合、SQLMesh はそれをエンジンに登録します。

#### 明示的な列コメント

`MODEL` DDL の `column_descriptions` フィールドで、列コメントを明示的に指定できます。

列コメントは、イコール記号 `=` で区切られたキー/値ペアの辞書として指定します。列名がキー、列コメントが値となります。例:

```sql linenums="1" hl_lines="4-6"
MODEL (
  name sushi.customer_total_revenue,
  cron '@daily',
  column_descriptions (
    id = 'This is the ID column comment'
  )
);
```

`column_descriptions` キーが存在する場合、SQLMesh はモデル クエリからインライン列コメントを検出して登録しません。

#### インライン列コメント

`MODEL` 定義に `column_descriptions` キーが存在しない場合、SQLMesh はクエリの列選択内のコメントを自動的に検出し、各列の最終コメントを基盤となる SQL エンジンに登録します。

例えば、以下のモデル定義用に作成された物理テーブルには、以下のコメントが含まれます。

1. `MODEL` DDL の `description` フィールドの値 "Revenue data for each customer" が、SQL エンジンにテーブルコメントとして登録されます。
2. `customer_id` 列定義のコメント "Customer's unique ID" が、テーブルの `customer_id` 列の列コメントとして登録されます。
3. `revenue` 列定義の 2 番目のコメント "Revenue from customer orders" が、テーブルの `revenue` 列の列コメントとして登録されます。

```sql linenums="1" hl_lines="7 11 13"
-- The MODEL DDL 'description' field is present, so this comment will not be registered with the SQL engine
MODEL (
  name sushi.customer_total_revenue,
  owner toby,
  cron '@daily',
  grain customer_id,
  description 'Revenue data for each customer'
);

SELECT
  o.customer_id::TEXT, -- Customer's unique ID
  -- This comment will not be registered because another `revenue` comment is present
  SUM(o.amount)::DOUBLE AS revenue -- Revenue from customer orders
FROM sushi.orders AS o
GROUP BY o.customer_id;
```

#### Python モデル

[Python モデル](./python_models.md) は SQL モデルのように解析されないため、モデル定義のインラインコメントから列コメントを推測することはできません。

代わりに、`@model` デコレータの `column_descriptions` キーで列コメントを指定します。列コメントは、キーが列名、値が列コメントである辞書で指定します。`columns` キーに含まれていない列名が指定された場合、SQLMesh はエラーを生成します。

例:

```python linenums="1" hl_lines="8-10"
from sqlmesh import ExecutionContext, model

@model(
    "my_model.name",
    columns={
        "column_name": "int",
    },
    column_descriptions={
        "column_name": "The `column_name` column comment",
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

#### オブジェクトタイプ別のコメント登録

一部のテーブル/ビューのみにコメントが登録されています。

- 一時テーブルは登録されていません。
- 物理レイヤー（つまり、`sqlmesh__[プロジェクトスキーマ名]` という名前のスキーマ）内の非一時テーブルとビューは登録されています。
- 非本番環境のビューは登録されていません。
- `prod` 環境のビューは登録されています。

一部のエンジンでは、物理テーブルからのコメントを、それらを選択するビューに自動的に渡します。これらのエンジンでは、SQLMesh が明示的にコメントを登録していなくても、ビューにコメントが表示されることがあります。

#### エンジンのコメントサポート {#engine-comment-support}

エンジンによって、コメントのサポートとコメント登録方法は異なります。エンジンは、オブジェクトを作成する `CREATE` コマンド内、または作成後に実行する特定のコマンドのいずれか、あるいは両方の登録方法をサポートします。

前者の方法では、列コメントは `CREATE` スキーマ定義に埋め込まれます。例: `CREATE TABLE my_table (my_col INTEGER COMMENT 'comment on my_col') COMMENT 'comment on my_table'`。つまり、すべてのテーブルコメントと列コメントを 1 つのコマンドで登録できます。

後者の方法では、コメントごとに別々のコマンドが必要になります。そのため、テーブルコメント用と列コメント用にそれぞれ 1 つずつ、複数のコマンドが必要になる場合があります。場合によっては、SQLMesh は前者の `CREATE` 方法を使用できず、別々のコマンドを発行する必要があります。SQLMesh は状況に応じて異なる方法を使用する必要があり、エンジンによってサポートされる方法が異なるため、すべてのオブジェクトに対してコメントが登録されない可能性があります。

この表は、各エンジンの `TABLE` および `VIEW` オブジェクト コメントのサポートを示します。

| エンジン | `TABLE` コメント | `VIEW` コメント |
| ------------- | ---------------- | --------------- |
| Athena        | N                | N               |
| BigQuery      | Y                | Y               |
| ClickHouse    | Y                | Y               |
| Databricks    | Y                | Y               |
| DuckDB <=0.9  | N                | N               |
| DuckDB >=0.10 | Y                | Y               |
| MySQL         | Y                | Y               |
| MSSQL         | N                | N               |
| Postgres      | Y                | Y               |
| GCP Postgres  | Y                | Y               |
| Redshift      | Y                | N               |
| Snowflake     | Y                | Y               |
| Spark         | Y                | Y               |
| Trino         | Y                | Y               |


## モデルプロパティ

`MODEL` DDL ステートメントは、メタデータと動作の制御の両方に使用されるさまざまなプロパティを受け取ります。

これらのプロパティとそのデフォルト値の詳細については、[モデル構成リファレンス](../../reference/model_configuration.md#general-model-properties) を参照してください。

### name
: name はモデル名を指定します。この名前はモデルが出力する本番環境のビュー名を表すため、通常は `"schema"."view_name"` という形式になります。モデル名は SQLMesh プロジェクト内で一意である必要があります。

    モデルを本番環境以外で使用する場合、SQLMesh は自動的に名前にプレフィックスを付けます。例えば、`"sushi"."customers"` という名前のモデルがあるとします。本番環境ではそのビュー名は `"sushi"."customers"` となり、開発環境ではそのビュー名は `"sushi__dev"."customers"` となります。

    name は ***必須*** であり、[名前推論](../../reference/model_configuration.md#model-naming) が有効でない限り、***一意*** である必要があります。

### project
:   project は、モデルが属するプロジェクトの名前を指定します。マルチリポジトリの SQLMesh デプロイメントで使用されます。

### kind
:   kind は、モデルの [種類](model_kinds.md) を指定します。モデルの種類によって、その計算方法と保存方法が決まります。SQL モデルのデフォルトの種類は `VIEW` で、ビューが作成され、そのビューにアクセスするたびにクエリが実行されます。一方、Python モデルのデフォルトの種類は `FULL` で、モデルが評価されるたびにテーブルが作成され、Python コードが実行されます。増分モデルの種類に適用されるプロパティについては、[下記](#incremental-model-properties) を参照してください。

### audits
:   audits は、モデルの評価後に実行する [audits](../audits.md) を指定します。

### dialect
:   dialect は、モデルの SQL 方言を定義します。デフォルトでは、[設定ファイル `model_defaults` `dialect` キー](../../reference/configuration.md#model-configuration) で指定された方言が使用されます。[SQLGlot ライブラリ](https://github.com/tobymao/sqlglot/blob/main/sqlglot/dialects/__init__.py) でサポートされているすべての SQL 方言が許可されます。

### owner
:   owner は、モデルの主な連絡担当者を指定します。これは、多くのデータ共同作業者を持つ組織にとって重要なフィールドです。

### stamp
:   定義の機能コンポーネントを変更せずに新しいモデルバージョンを作成するために使用される、任意の文字列シーケンス（省略可能）。

### tags
:   tags は、モデルを整理するために使用する1つ以上のラベルです。

### cron
:   cron は、モデルがデータを処理または更新するタイミングをスケジュールするために使用されます。[cron式](https://en.wikipedia.org/wiki/Cron)、または `@hourly`、`@daily`、`@weekly`、`@monthly` のいずれかを指定できます。デフォルトでは、すべての時間はUTCタイムゾーンとみなされます。

### cron_tz
:   cron タイムゾーンは、cronのタイムゾーンを指定するために使用されます。これはスケジュール設定にのみ使用され、増分モデルで処理される間隔には影響しません。例えば、モデルが `@daily` で、cron_tz が `America/Los_Angeles` の場合、モデルは毎日太平洋標準時の午前0時に実行されますが、増分モデルに渡される `start` および `end` 変数はUTCの日付の境界を表します。

### interval_unit
:   間隔単位は、モデルの時間間隔を計算する際の時間粒度を決定します。

    デフォルトでは、間隔単位は [`cron`](#cron) 式から自動的に導出されるため、指定する必要はありません。

    サポートされている値は、`year`、`month`、`day`、`hour`、`half_hour`、`quarter_hour`、`five_minute` です。

    #### [`cron`](#cron) との関係

    SQLMesh スケジューラは、モデルから 2 つの時間情報を必要とします。1 つはモデルを実行する具体的な時刻、もう 1 つはデータの処理または保存に使用する最も細かい時間粒度です。`interval_unit` はこの粒度を指定します。

    モデルの `cron` パラメータが `@daily` のような頻度の場合、実行時間と `interval_unit` は簡単に決定できます。モデルは 1 日の開始時に実行準備が完了し、その `interval_unit` は `day` です。同様に、`@hourly` の `cron` は毎時開始時に実行準備が完了し、その `interval_unit` は `hour` です。

    ただし、cron 式で [`cron`](#cron) が指定されている場合、SQLMesh はより複雑な方法で `interval_unit` を導出します。

    [cron式](https://en.wikipedia.org/wiki/Cron) は複雑な時間間隔を生成できるため、SQLMesh はそれを直接解析しません。代わりに、以下の処理を行います。

      1. cron式から（計算時刻を基準として）次の5つの実行時刻を生成します。
      2. これらの5つの値の間の間隔の長さを計算します。
      3. (2) の最小間隔以下の最大の間隔単位値をモデルの `interval_unit` として決定します。

    例えば、「43分ごとに実行」に対応する cron式を考えてみましょう。この `interval_unit` は `half_hour` です。これは、43分より*短い*最大の `interval_unit` 値だからです。cron式が「67分ごとに実行」の場合、同じロジックで `interval_unit` は `hour` になります。

    ただし、`interval_unit` は [`cron`](#cron) から推測する必要はなく、明示的に指定してバックフィルの発生方法をカスタマイズできます。

    #### `interval_unit` の指定

    モデルは通常、一定の周期で実行されます。この場合、各実行間の経過時間は同じで、各実行で処理されるデータの長さも同じです。

    例えば、モデルは毎日午前 0 時に実行され（1 日に 1 回実行）、前日のデータ（1 回の実行で 1 日分のデータ）を処理するとします。実行間隔と各実行で処理されるデータの長さはどちらも 1 日です（実行を 1 回逃した場合はどちらも 2 日です）。

    ただし、実行周期の長さと処理されるデータの長さは同じである必要はありません。

    毎日午前 7 時 30 分に実行され、今日の午前 7 時までデータを処理するモデルを考えてみましょう。モデルの `cron` は「毎日午前 7 時 30 分に実行」を表す cron 式であり、SQLMesh はそこから `interval_unit` として `day` を推測します。

    このモデルを実行すると何が起こるでしょうか？まず、SQLMesh は最後に完了した間隔を特定します。`interval_unit` は `day` と推定されたため、最後に完了した間隔は昨日でした。SQLMesh は、本日の午前 0 時から午前 7 時までのデータは実行に含めません。

    本日のデータを含めるには、`interval_unit` に `hour` を手動で指定します。モデルが午前 7 時 30 分に実行されると、SQLMesh は最後に完了した `hour` 間隔を午前 6 時から午前 7 時までと特定し、その間隔のデータをバックフィルに含めます。

    ```sql
    MODEL (
        name sqlmesh_example.up_until_7,
        kind INCREMENTAL_BY_TIME_RANGE (
          time_column date_column,
        ),
        start '2024-11-01',
        cron '30 7 * * *', -- cron expression for "every day at 7:30am"
        interval_unit 'hour', -- backfill up until the most recently completed hour (rather than day)
      );
    ```

    !!! warning "注意: 複雑なユースケース"

        以下の例は、`allow_partials` 構成オプションを使用した複雑なユースケースです。絶対に必要な場合を除き、このオプションは**使用しない**ことをお勧めします。

        部分的なデータ取得を許可すると、データ欠損の原因を特定できなくなります。パイプラインの問題と、正しく実行された部分的なバックフィルの両方でデータ欠損が発生するため、両者を区別できない可能性があります。

        全体として、SQLMesh が正常に実行された場合でも、不完全または不正確なデータを共有するリスクがあります。詳細については、[Tobiko ブログ](https://tobikodata.com/data-completeness.html) をご覧ください。

    このセクションでは、以下のモデルを設定します。

    - 1時間ごとに実行
    - 毎回の実行で過去2日間のデータを処理する
    - 毎回の実行で今日までに蓄積されたデータを処理する

    このモデルを設定するには、モデル構成の「allow_partials」を「True」に設定し、SQLMeshが部分的に完了した間隔を処理できるようにする必要があります。

    部分的な間隔のデータは一時的なものであり、間隔が完了するとSQLMeshはそれを再処理します。

    ```sql
    MODEL (
        name sqlmesh_example.demo,
        kind INCREMENTAL_BY_TIME_RANGE (
          time_column date_column,
          lookback 2, -- 2 days of late-arriving data to backfill
        ),
        start '2024-11-01',
        cron '@hourly', -- run model hourly, not tied to the interval_unit
        allow_partials true, -- allow partial intervals so today's data is processed in each run
        interval_unit 'day', -- finest granularity of data to be time bucketed
    );
    ```

    モデルの `interval_unit` が `day` に指定されているため、 `lookback` は日数で計算されます。

### start
:   start は、モデルの処理に必要な最も早い時刻を決定するために使用されます。絶対日時 (`2022-01-01`) または相対日時 (`1年前`) を指定できます。

### end
:   end は、モデルの処理に必要な最も遅い時刻を決定するために使用されます。絶対日時 (`2022-01-01`) または相対日時 (`1年前`) を指定できます。

### description
:   モデルの説明 (オプション)。基盤となる SQL エンジンでテーブルの説明/コメントとして自動的に登録されます (エンジンでサポートされている場合)。

### column_descriptions
:   [キー/値ペア](#explicit-column-comments) のディクショナリ (オプション)。基盤となる SQL エンジンで列の説明/コメントとして自動的に登録されます (エンジンでサポートされている場合)。指定されていない場合は、[インラインコメント](#inline-column-comments) が自動的に登録されます。

### grain
:   モデルの grain とは、モデルのクエリによって返される結果内の行を一意に識別する列または列の組み合わせです。グレインが設定されている場合、`table_diff` などの SQLMesh ツールは、手動で指定する必要のあるパラメータにモデルのグレインを自動的に使用するため、実行が簡素化されます。

### grains
:   モデルに複数の一意のキーまたはキーの組み合わせがある場合、複数の grain を定義できます。

### references
:   references とは、他のモデルとの結合関係を識別する、一意でない列または列の組み合わせです。

    たとえば、モデルで参照 `account_id` を定義すると、`account_id` 粒度を持つ任意のモデルに自動的に結合できることを示します。参照は一意ではなく、これを行うと多対多の結合になるため、`account_id` 参照を持つテーブルに安全に結合することはできません。

    列名が異なる場合もありますが、その場合は列名に共通のエンティティ名をエイリアスとして使用できます。たとえば、`guest_id AS account_id` を使用すると、列 guest\_id を持つモデルを粒度 account\_id を持つモデルに結合できるようになります。

### depend_on
:   depends_on は、モデルコードから自動的に推論されるモデルに加えて、モデルが依存するモデルを明示的に指定します。

### table_format
:   table_format は、`iceberg` や `hive` などのテーブル形式をサポートし、物理ファイル形式が設定可能なエンジンのオプションプロパティです。`table_format` を使用してテーブルの種類を定義し、`storage_format` を使用してテーブル内のファイルのディスク上の形式を定義します。

    このプロパティは、`table_format` を `storage_format` とは独立して設定できるエンジンでのみ実装されていることに注意してください。

### storage_format
:   storage_format は、`parquet` や `orc` などのストレージ形式をサポートする Spark や Hive などのエンジンのプロパティです。一部のエンジンでは `table_format` と `storage_format` を区別しないことに注意してください。その場合には `storage_format` が使用され、 `table_format` は無視されます。

### partitioned_by
:   partitioned_by には2つの役割があります。ほとんどのモデル種別において、Spark や BigQuery などのテーブルパーティショニングをサポートするエンジンではオプションのプロパティです。

    [`INCREMENTAL_BY_PARTITION` モデル種別](./model_kinds.md#incremental_by_partition) では、データの増分ロードに使用するパーティションキーを定義します。

    複数列のパーティションキーを指定したり、パーティション分割のために日付列を変更したりできます。例えば、BigQuery では、`partitioned_by TIMESTAMP_TRUNC(event_ts, DAY)` を使用してタイムスタンプ列 `event_ts` の日付部分を抽出することで、日付ごとにパーティション分割できます。

### clustered_by
:   clustered_by は、BigQuery などのクラスタリングをサポートするエンジンのオプションプロパティです。

### columns
:   デフォルトでは、SQLMesh は SQL クエリから [モデルの列名と型を推測](#conventions) します。この動作を無効にするには、モデルの `columns` プロパティにすべての列名とデータ型を手動で指定します。

    **警告**: `columns` プロパティにクエリで返されない列が含まれている場合、クエリで返される列が省略されている場合、またはクエリで返されるデータ型以外のデータ型が指定されている場合、SQLMesh は予期しない動作を示す可能性があります。

    たとえば、これは `columns` キーを含むシードモデル定義を示しています。このキーはファイル内のすべての列のデータ型を指定しています。`holiday_name` 列はデータ型 `VARCHAR`、`holiday_date` 列はデータ型 `DATE` です。

    ```sql linenums="1" hl_lines="6-9"
    MODEL (
      name test_db.national_holidays,
      kind SEED (
        path 'national_holidays.csv'
      ),
      columns (
        holiday_name VARCHAR,
        holiday_date DATE
      )
    );
    ```

    注: DataFrames を返す [Python モデル](../models/python_models.md) では、列名とデータ型を指定する必要があります。

### physical_properties
:   以前の名称は `table_properties`

    physical_properties は、物理レイヤーのモデルテーブル/ビューに適用される任意のプロパティのキーと値のマッピングです。パーティションの詳細と、作成されるモデル/ビューの種類をオーバーライドする `creatable_type` に注意してください。この例では `TRANSIENT TABLE` が作成されます。`creatable_type` は汎用ですが、その他のプロパティはアダプタ固有のため、エンジンのドキュメントをご確認ください。例:

    ```sql linenums="1"
    MODEL (
      ...,
      physical_properties (
        partition_expiration_days = 7,
        require_partition_filter = true,
        creatable_type = TRANSIENT
      )
    );

    ```

### virtual_properties
:   virtual_properties は、仮想レイヤーのモデルビューに適用される任意のプロパティのキーと値のマッピングです。パーティションの詳細と、作成されるモデル/ビューの種類をオーバーライドする `creatable_type` に注意してください。この例では `SECURE VIEW` が作成されます。`creatable_type` は汎用ですが、その他のプロパティはアダプタ固有のため、エンジンのドキュメントを確認してください。例:

    ```sql linenums="1"
    MODEL (
      ...,
      virtual_properties (
        creatable_type = SECURE,
        labels = [('test-label', 'label-value')]
      )
    );

    ```

### session_properties
:   session_properties は、エンジンセッションに適用される、ターゲットエンジン固有の任意のプロパティのキーと値のマッピングです。

### allow_partials
:   このモデルが部分的な（不完全な）データ間隔に対して実行可能であることを示します。

    デフォルトでは、各モデルは部分的なデータによって発生する一般的なエラーを防ぐため、完全な間隔のみを処理します。間隔のサイズは、モデルの[interval_unit](#interval_unit)によって決まります。

    `allow_partials` を `true` に設定すると、この動作がオーバーライドされ、モデルは一部のデータポイントが欠落している入力データのセグメントを処理できるようになります。

    注: モデルを毎回強制的に実行するには、`allow_partials` を `true` に設定し、`--ignore-cron` 引数を使用します（`sqlmesh run --ignore-cron`）。 `allow_partials` を `true` に設定するだけでは、`sqlmesh run` コマンドの呼び出しごとにモデルが実行される保証はありません。部分的な実行間隔が許可されている場合でも、モデルに設定された `cron` スケジュールは引き続き尊重されます。

    同様に、`allow_partials` を `true` に設定せずに `--ignore-cron` を使用した場合、モデルが毎回実行される保証はありません。時間帯によっては、`cron` スケジュールを無視していても、実行間隔が完了しておらず、実行準備が整っていない可能性があります。したがって、`sqlmesh run` の呼び出しごとにモデルが実行されることを確認するには、両方の設定が必要です。

### enabled
:   モデルが有効かどうか。この属性はデフォルトで `true` です。`false` に設定すると、SQLMesh はプロジェクトの読み込み時にこのモデルを無視します。

### physical_version
:   このモデルの物理テーブルのバージョンを、指定された値に固定します。

    注: これは forward-only モデルにのみ設定できます。

### gateway
:   このモデルの実行に使用するゲートウェイを指定します。指定しない場合は、デフォルトのゲートウェイが使用されます。

### optimize_query
:   モデルのクエリを最適化するかどうか。すべてのSQLモデルはデフォルトで最適化されます。これを
`false` に設定すると、SQLMesh はクエリの正規化と簡素化を無効にします。最適化されたクエリによってテキスト制限を超えるなどのエラーが発生する場合にのみ、これをオフにしてください。

!!! warning
    オプティマイザーをオフにすると、モデルのクエリ内のすべての列が修飾され、スター プロジェクションが含まれていない限り (例: `SELECT *`)、影響を受けるモデルとその子孫に対して列レベルの系統が機能しなくなる可能性があります。

### valid_query
:   モデルのクエリをコンパイル時に検証するかどうか。この属性はデフォルトでは `false` です。`true` に設定すると、SQLMesh は警告ではなくエラーを生成します。これにより、SQL 文内の無効な列と、すべての列をリストするために自動的に展開できない `SELECT *` を含むモデルが表示されます。これにより、データウェアハウスで SQL を実行する時間とコストがかかる前に、SQL がローカルで検証されることが保証されます。

!!! warning
    このフラグはv.0.159.7以降では非推奨となり、[linter](../../guides/linter.md)が推奨されます。コンパイル時の検証を維持するには、正確性をチェックする[組み込みルール](../../guides/linter.md#built-in-rules)をエラーの重大度に[設定](../../guides/linter.md#rule-violation-behavior)する必要があります。

### ignore_rules
:   このモデルで無視/除外するリンタールールを指定します。

### formatting
:   モデルをフォーマットするかどうか。すべてのモデルはデフォルトでフォーマットされます。これを `false` に設定すると、SQLMesh は `sqlmesh format` の実行中にこのモデルを無視します。

## 増分モデルのプロパティ

これらのプロパティは、増分モデルの `kind` 定義で指定できます。

一部のプロパティは特定のモデルの種類でのみ使用できます。詳細と各 `kind` のプロパティの完全なリストについては、[モデル設定リファレンス](../../reference/model_configuration.md#incremental-models) を参照してください。

### time_column
:   time_column は増分モデルに必須のプロパティです。増分挿入時に上書きするレコードを決定するために使用されます。time_column には、モデルのSQL方言で指定されたオプションのフォーマット文字列を含めることができます。

    SparkやBigQueryなどのパーティション分割をサポートするエンジンは、time_column をモデルのパーティションキーとして使用します。複数列のパーティションや列の変更は、[`partitioned_by`プロパティ](#partitioned_by)で指定できます。

    !!! tip "重要"

        `time_column` 変数は UTC タイムゾーンにする必要があります - 詳細については、[こちら](./model_kinds.md#timezones) を参照してください。

### batch_size
:   batch_size は、バックフィルする間隔の数が多すぎてエンジンが1回のパスで実行できない場合に、増分データをバックフィルするために使用されます。これにより、システムで実行可能なサイズに分割された間隔セットをバッチ処理できます。`batch_size` パラメータは、1回のジョブで実行するデータの最大数（[`interval_unit`s](#interval_unit)）を決定します。

    例えば、3日間実行されていない `@hourly` [`cron`](#cron) を持つモデルを考えてみましょう。このモデルの [`cron`](#cron) は `@hourly` なので、[`interval_unit`](#interval_unit) は `hour` です。

    まず、バックフィルする未処理の間隔の総数を計算してみましょう。3日間の未処理データ × 24時間/日 = 72 `hour` 間隔です。

    これで、次の式を使って、異なる `batch_size` 値に対するジョブ数を計算できます。

      間隔数 / `batch_size` = 実行するジョブ数

    いくつかの異なる `batch_size` 値に対するジョブ数を見てみましょう。
      - `batch_size` を指定しない場合：スケジューラは 72 間隔すべてを処理するジョブを 1 つ生成します（SQLMesh のデフォルトの動作）。
      - `batch_size` が 1 の場合：スケジューラは [72 `時間` 間隔 / ジョブあたり 1 間隔] = 72 個のジョブを生成します。
      - `batch_size` が 12 の場合：スケジューラは [72 `時間` 間隔 / ジョブあたり 12 間隔] = 6 個のジョブを生成します。

### batch_concurrency
:   このモデルで同時に実行できる [バッチ](#batch_size) の最大数です。指定しない場合、同時実行数は接続設定で設定された同時タスク数によってのみ制限されます。

### lookback
:   lookback は、[時間範囲による増分](model_kinds.md#incremental_by_time_range) および [一意キーによる増分](model_kinds.md#incremental_by_unique_key) モデルで使用され、遅れて到着したデータをキャプチャします。これにより、モデルは現在処理中の時間間隔外にあるデータポイントにアクセスできます。

    正の整数で、モデルに含める現在の間隔より前の [`interval_unit`](#interval_unit) 間隔の数を指定します。

    例えば、cron `@daily` ([`interval_unit`](#interval_unit) `day`) を持つモデルを考えてみましょう。モデルで `lookback` を 7 に指定すると、SQLMesh は処理対象の期間の 7 日前までをデータに含めます。cron が `@weekly` で `lookback` が 7 に設定されているモデルは、処理対象の期間の 7 週間前までをデータに含めます。

    あるいは、cron 式が「6 時間ごとに実行」(`0 */6 * * *`) であるモデルを考えてみましょう。SQLMesh は [`interval_unit`](#interval_unit) を `hour` として計算します。`lookback` 値は `interval_units` 単位で計算されるため、`lookback` が 1 の場合、処理対象の期間の 1 時間前までをデータに含めます。

### forward_only
:   このモデルへのすべての変更を [forward-only](../plans.md#forward-only-plans) にするには、これを true に設定します。

### on_destructive_change
:   [forward-only モデル](../../guides/incremental_time.md#forward-only-models) または [forward-only プラン](../plans.md#forward-only-plans) 内の増分モデルへの変更によってテーブルスキーマに破壊的な変更が発生した場合（つまり、既存の列の削除や、データ損失を引き起こす可能性のある列制約の変更が必要な場合）の処理を指定します。

    SQLMesh は、モデル定義に基づいてプラン時に破壊的な変更の有無を確認し、モデルの基盤となる物理テーブルに基づいて実行時に破壊的な変更の有無を確認します。

    次のいずれかの値を指定する必要があります: `allow`、`warn`、`error`（デフォルト）、または `ignore`。

### on_additive_change
:   [forward-only モデル](../../guides/incremental_time.md#forward-only-models) または [forward-only プラン](../plans.md#forward-only-plans) 内の増分モデルへの変更によってテーブルスキーマに追加的な変更 (新しい列の追加、互換性のある方法での列のデータ型の変更など) が発生した場合の動作を指定します。

    SQLMesh は、モデル定義に基づいてプラン時に、またモデルの基盤となる物理テーブルに基づいて実行時に、追加的な変更の有無を確認します。

    次のいずれかの値を指定する必要があります: `allow` (デフォルト)、`warn`、`error`、または `ignore`。

### disable_restatement
:   このモデルで [データ再ステートメント](../plans.md#restatement-plans) を無効にするには、これを true に設定します。

### auto_restatement_cron
:   SQLMesh がこのモデルを自動的に再ステートするタイミングを決定する cron 式。再ステートとは、サポートされるモデルの種類の場合は最後の間隔の数（[`auto_restatement_intervals`](#auto_restatement_intervals) で制御）を再評価し、サポートされないモデルの種類の場合はモデル全体を再評価することを意味します。このモデルに依存する下流モデルも再ステートされます。自動再ステートは、実稼働環境に対して `sqlmesh run` コマンドを実行する場合にのみ適用されます。

    自動再ステートの一般的な使用例は、遅れて到着するデータやディメンションの変更を考慮するために、モデルを定期的に（モデルの cron よりも低い頻度で）再評価することです。ただし、この機能に依存することは、データモデルまたは依存関係チェーンに根本的な問題があることを示している場合が多いため、通常は推奨されません。代わりに、遅れて到着するデータをより効率的に処理するには、[`lookback`](#lookback) プロパティを設定することをお勧めします。

    スキャンされるデータの時間範囲のみを制御する [`lookback`](#lookback) プロパティとは異なり、自動再ステートメントは、このモデルの以前に処理されたすべてのデータをターゲットテーブルに書き換えます。

    [`auto_restatement_intervals`](#auto_restatement_intervals) をサポートしていないモデルの種類の場合、テーブルは最初から再作成されます。

    [`disable_restatement`](#disable_restatement) が `true` に設定されているモデルは、このプロパティが設定されていても自動的に再ステートメントされません。

    **注意**: このプロパティが設定されているモデルは、開発環境でのみ [プレビュー](../plans.md#data-preview-for-forward-only-changes) できます。つまり、これらの環境で計算されたデータは本番環境で再利用されません。

    ```sql linenums="1" hl_lines="6"
    MODEL (
      name test_db.national_holidays,
      cron '@daily',
      kind INCREMENTAL_BY_UNIQUE_KEY (
        unique_key key,
        auto_restatement_cron '@weekly',
      )
    );
    ```

### auto_restatement_intervals
:   自動再実行を行う最後の間隔の数。これは [`auto_restatement_cron`](#auto_restatement_cron) と併用した場合にのみ適用されます。

    指定しない場合は、モデル全体が再実行されます。

    このプロパティは、`INCREMENTAL_BY_TIME_RANGE` モデル種別でのみサポートされます。

    ```sql linenums="1" hl_lines="7"
    MODEL (
      name test_db.national_holidays,
      cron '@daily',
      kind INCREMENTAL_BY_TIME_RANGE (
        time_column event_ts,
        auto_restatement_cron '@weekly',
        auto_restatement_intervals 7, -- automatically restate the last 7 days of data
      )
    );
    ```

## マクロ
マクロは、日付などのパラメータ化された引数を渡したり、SQL の繰り返しを減らしたりするために使用できます。SQLMesh はデフォルトで、使用可能な定義済みのマクロ変数をいくつか提供しています。マクロは、先頭に `@` 記号を付けて使用します。詳細については、[マクロ](../macros/overview.md) を参照してください。

## ステートメント
モデルには、メインクエリの前後に実行される追加のステートメントを含めることができます。これらは、[UDF](../glossary.md#user-defined-function-udf) などの読み込みや、モデルクエリ実行後のクリーンアップに役立ちます。

一般に、事前ステートメントはメインクエリの準備にのみ使用してください。テーブルの作成や変更には使用しないでください。複数のモデルを同時に実行した場合に予期しない動作が発生する可能性があるためです。

```sql linenums="1" hl_lines="5-7"
MODEL (
...
);

-- Additional statements preparing for main query
ADD JAR s3://special_udf.jar;
CREATE TEMPORARY FUNCTION UDF AS 'my.jar.udf';

SELECT UDF(x)::int AS x
FROM y;
```

メインクエリの後に追加のステートメントを指定することもできます。その場合、SELECTクエリの各評価後に実行されます。モデルクエリは、後続ステートメントの前にセミコロンで終了する必要があることに注意してください。

```sql linenums="1" hl_lines="10-11"
MODEL (
...
);

...

SELECT UDF(x)::int AS x
FROM y;

-- Cleanup statements
DROP TABLE temp_table;
```
