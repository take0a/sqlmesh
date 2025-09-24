# モデルの種類

このページでは、SQLMesh がサポートする [モデル](./overview.md) の種類について説明します。これらの種類によって、モデルのデータの読み込み方法が決定されます。

すべてのモデルの種類の設定パラメータに関する情報は、[モデル設定リファレンスページ](../../reference/model_configuration.md) をご覧ください。

## INCREMENTAL_BY_TIME_RANGE

`INCREMENTAL_BY_TIME_RANGE` タイプのモデルは、時間範囲に基づいて増分的に計算されます。これは、レコードが時間の経過とともにキャプチャされ、イベント、ログ、トランザクションなどの不変のファクトを表すデータセットに最適な選択肢です。適切なデータセットにこのタイプを使用すると、通常、コストと時間を大幅に節約できます。

`INCREMENTAL_BY_TIME_RANGE` モデルでは、実行ごとに欠落している時間間隔のみが処理されます。これは、モデルが実行されるたびにデータセット全体が再計算される [FULL](#full) モデルとは対照的です。

`INCREMENTAL_BY_TIME_RANGE` モデルには、他のモデルにはない 2 つの要件があります。時間範囲でデータをフィルタリングするために使用する時間データを含む列を認識している必要があること、そして上流のデータを時間でフィルタリングする `WHERE` 句が含まれている必要があることです。

時間データを含む列の名前は、モデルの`MODEL` DDLで指定します。これは、DDLの`kind`仕様の`time_column`キーで指定します。次の例は、"event_date"列に時間データを格納する`INCREMENTAL_BY_TIME_RANGE`モデルの`MODEL` DDLを示しています。

```sql linenums="1"
MODEL (
  name db.events,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column event_date -- This model's time information is stored in the `event_date` column
  )
);
```

<a id="timezones"></a>
`MODEL` DDLで時間列を指定することに加えて、モデルのクエリには、上流のレコードを時間範囲でフィルタリングする `WHERE` 句を含める必要があります。SQLMeshは、処理対象の時間範囲の開始と終了を表す特別なマクロ（`@start_date` / `@end_date`、`@start_ds` / `@end_ds`）を提供しています。詳細については、[マクロ](../macros/macro_variables.md) を参照してください。

??? "このモデル種別を適用する場合のSQLシーケンスの例 (ex: BigQuery)"
    これは、完全なウォークスルーから引用したものです: [時間範囲による増分](../../examples/incremental_time_full_walkthrough.md)

    以下の定義でモデルを作成し、`sqlmesh plan dev` を実行します。

    ```sql
    MODEL (
      name demo.incrementals_demo,
      kind INCREMENTAL_BY_TIME_RANGE (
        -- How does this model kind behave?
        --   DELETE by time range, then INSERT
        time_column transaction_date,

        -- How do I handle late-arriving data?
        --   Handle late-arriving events for the past 2 (2*1) days based on cron
        --   interval. Each time it runs, it will process today, yesterday, and
        --   the day before yesterday.
        lookback 2,
      ),

      -- Don't backfill data before this date
      start '2024-10-25',

      -- What schedule should I run these at?
      --   Daily at Midnight UTC
      cron '@daily',

      -- Good documentation for the primary key
      grain transaction_id,

      -- How do I test this data?
      --   Validate that the `transaction_id` primary key values are both unique
      --   and non-null. Data audit tests only run for the processed intervals,
      --   not for the entire table.
      -- audits (
      --   UNIQUE_VALUES(columns = (transaction_id)),
      --   NOT_NULL(columns = (transaction_id))
      -- )
    );

    WITH sales_data AS (
      SELECT
        transaction_id,
        product_id,
        customer_id,
        transaction_amount,
        -- How do I account for UTC vs. PST (California baby) timestamps?
        --   Make sure all time columns are in UTC and convert them to PST in the
        --   presentation layer downstream.
        transaction_timestamp,
        payment_method,
        currency
      FROM sqlmesh-public-demo.tcloud_raw_data.sales  -- Source A: sales data
      -- How do I make this run fast and only process the necessary intervals?
      --   Use our date macros that will automatically run the necessary intervals.
      --   Because SQLMesh manages state, it will know what needs to run each time
      --   you invoke `sqlmesh run`.
      WHERE transaction_timestamp BETWEEN @start_dt AND @end_dt
    ),

    product_usage AS (
      SELECT
        product_id,
        customer_id,
        last_usage_date,
        usage_count,
        feature_utilization_score,
        user_segment
      FROM sqlmesh-public-demo.tcloud_raw_data.product_usage  -- Source B
      -- Include usage data from the 30 days before the interval
      WHERE last_usage_date BETWEEN DATE_SUB(@start_dt, INTERVAL 30 DAY) AND @end_dt
    )

    SELECT
      s.transaction_id,
      s.product_id,
      s.customer_id,
      s.transaction_amount,
      -- Extract the date from the timestamp to partition by day
      DATE(s.transaction_timestamp) as transaction_date,
      -- Convert timestamp to PST using a SQL function in the presentation layer for end users
      DATETIME(s.transaction_timestamp, 'America/Los_Angeles') as transaction_timestamp_pst,
      s.payment_method,
      s.currency,
      -- Product usage metrics
      p.last_usage_date,
      p.usage_count,
      p.feature_utilization_score,
      p.user_segment,
      -- Derived metrics
      CASE
        WHEN p.usage_count > 100 AND p.feature_utilization_score > 0.8 THEN 'Power User'
        WHEN p.usage_count > 50 THEN 'Regular User'
        WHEN p.usage_count IS NULL THEN 'New User'
        ELSE 'Light User'
      END as user_type,
      -- Time since last usage
      DATE_DIFF(s.transaction_timestamp, p.last_usage_date, DAY) as days_since_last_usage
    FROM sales_data s
    LEFT JOIN product_usage p
      ON s.product_id = p.product_id
      AND s.customer_id = p.customer_id
    ```

    SQLMeshはこのSQLを実行し、物理レイヤーにバージョン管理されたテーブルを作成します。テーブルのバージョンフィンガープリント「50975949」がテーブル名の一部であることに注意してください。

    ```sql
    CREATE TABLE IF NOT EXISTS `sqlmesh-public-demo`.`sqlmesh__demo`.`demo__incrementals_demo__50975949` (
      `transaction_id` STRING,
      `product_id` STRING,
      `customer_id` STRING,
      `transaction_amount` NUMERIC,
      `transaction_date` DATE OPTIONS (description='We extract the date from the timestamp to partition by day'),
      `transaction_timestamp_pst` DATETIME OPTIONS (description='Convert this to PST using a SQL function'),
      `payment_method` STRING,
      `currency` STRING,
      `last_usage_date` TIMESTAMP,
      `usage_count` INT64,
      `feature_utilization_score` FLOAT64,
      `user_segment` STRING,
      `user_type` STRING OPTIONS (description='Derived metrics'),
      `days_since_last_usage` INT64 OPTIONS (description='Time since last usage')
      )
      PARTITION BY `transaction_date`
    ```

    SQLMesh は、データを処理する前に SQL を検証します (`WHERE FALSE LIMIT 0` とプレースホルダーのタイムスタンプに注意してください)。

    ```sql
    WITH `sales_data` AS (
      SELECT
        `sales`.`transaction_id` AS `transaction_id`,
        `sales`.`product_id` AS `product_id`,
        `sales`.`customer_id` AS `customer_id`,
        `sales`.`transaction_amount` AS `transaction_amount`,
        `sales`.`transaction_timestamp` AS `transaction_timestamp`,
        `sales`.`payment_method` AS `payment_method`,
        `sales`.`currency` AS `currency`
      FROM `sqlmesh-public-demo`.`tcloud_raw_data`.`sales` AS `sales`
      WHERE (
        `sales`.`transaction_timestamp` <= CAST('1970-01-01 23:59:59.999999+00:00' AS TIMESTAMP) AND
        `sales`.`transaction_timestamp` >= CAST('1970-01-01 00:00:00+00:00' AS TIMESTAMP)) AND
        FALSE
    ),
    `product_usage` AS (
      SELECT
        `product_usage`.`product_id` AS `product_id`,
        `product_usage`.`customer_id` AS `customer_id`,
        `product_usage`.`last_usage_date` AS `last_usage_date`,
        `product_usage`.`usage_count` AS `usage_count`,
        `product_usage`.`feature_utilization_score` AS `feature_utilization_score`,
        `product_usage`.`user_segment` AS `user_segment`
      FROM `sqlmesh-public-demo`.`tcloud_raw_data`.`product_usage` AS `product_usage`
      WHERE (
        `product_usage`.`last_usage_date` <= CAST('1970-01-01 23:59:59.999999+00:00' AS TIMESTAMP) AND
        `product_usage`.`last_usage_date` >= CAST('1969-12-02 00:00:00+00:00' AS TIMESTAMP)
        ) AND
        FALSE
    )

    SELECT
      `s`.`transaction_id` AS `transaction_id`,
      `s`.`product_id` AS `product_id`,
      `s`.`customer_id` AS `customer_id`,
      CAST(`s`.`transaction_amount` AS NUMERIC) AS `transaction_amount`,
      DATE(`s`.`transaction_timestamp`) AS `transaction_date`,
      DATETIME(`s`.`transaction_timestamp`, 'America/Los_Angeles') AS `transaction_timestamp_pst`,
      `s`.`payment_method` AS `payment_method`,
      `s`.`currency` AS `currency`,
      `p`.`last_usage_date` AS `last_usage_date`,
      `p`.`usage_count` AS `usage_count`,
      `p`.`feature_utilization_score` AS `feature_utilization_score`,
      `p`.`user_segment` AS `user_segment`,
      CASE
        WHEN `p`.`feature_utilization_score` > 0.8 AND `p`.`usage_count` > 100 THEN 'Power User'
        WHEN `p`.`usage_count` > 50 THEN 'Regular User'
        WHEN `p`.`usage_count` IS NULL THEN 'New User'
        ELSE 'Light User'
      END AS `user_type`,
      DATE_DIFF(`s`.`transaction_timestamp`, `p`.`last_usage_date`, DAY) AS `days_since_last_usage`
    FROM `sales_data` AS `s`
    LEFT JOIN `product_usage` AS `p`
      ON `p`.`customer_id` = `s`.`customer_id` AND
      `p`.`product_id` = `s`.`product_id`
    WHERE FALSE
    LIMIT 0
    ```

    SQLMesh はデータを空のテーブルにマージします。

    ```sql
    MERGE INTO `sqlmesh-public-demo`.`sqlmesh__demo`.`demo__incrementals_demo__50975949` AS `__MERGE_TARGET__` USING (
      WITH `sales_data` AS (
        SELECT
          `transaction_id`,
          `product_id`,
          `customer_id`,
          `transaction_amount`,
          `transaction_timestamp`,
          `payment_method`,
          `currency`
        FROM `sqlmesh-public-demo`.`tcloud_raw_data`.`sales` AS `sales`
        WHERE `transaction_timestamp` BETWEEN CAST('2024-10-25 00:00:00+00:00' AS TIMESTAMP) AND CAST('2024-11-04 23:59:59.999999+00:00' AS TIMESTAMP)
      ),
      `product_usage` AS (
        SELECT
          `product_id`,
          `customer_id`,
          `last_usage_date`,
          `usage_count`,
          `feature_utilization_score`,
          `user_segment`
        FROM `sqlmesh-public-demo`.`tcloud_raw_data`.`product_usage` AS `product_usage`
        WHERE `last_usage_date` BETWEEN DATE_SUB(CAST('2024-10-25 00:00:00+00:00' AS TIMESTAMP), INTERVAL '30' DAY) AND CAST('2024-11-04 23:59:59.999999+00:00' AS TIMESTAMP)
      )

      SELECT
        `transaction_id`,
        `product_id`,
        `customer_id`,
        `transaction_amount`,
        `transaction_date`,
        `transaction_timestamp_pst`,
        `payment_method`,
        `currency`,
        `last_usage_date`,
        `usage_count`,
        `feature_utilization_score`,
        `user_segment`,
        `user_type`,
        `days_since_last_usage`
      FROM (
        SELECT
          `s`.`transaction_id` AS `transaction_id`,
          `s`.`product_id` AS `product_id`,
          `s`.`customer_id` AS `customer_id`,
          `s`.`transaction_amount` AS `transaction_amount`,
          DATE(`s`.`transaction_timestamp`) AS `transaction_date`,
          DATETIME(`s`.`transaction_timestamp`, 'America/Los_Angeles') AS `transaction_timestamp_pst`,
          `s`.`payment_method` AS `payment_method`,
          `s`.`currency` AS `currency`,
          `p`.`last_usage_date` AS `last_usage_date`,
          `p`.`usage_count` AS `usage_count`,
          `p`.`feature_utilization_score` AS `feature_utilization_score`,
          `p`.`user_segment` AS `user_segment`,
          CASE
            WHEN `p`.`usage_count` > 100 AND `p`.`feature_utilization_score` > 0.8 THEN 'Power User'
            WHEN `p`.`usage_count` > 50 THEN 'Regular User'
            WHEN `p`.`usage_count` IS NULL THEN 'New User'
            ELSE 'Light User'
          END AS `user_type`,
          DATE_DIFF(`s`.`transaction_timestamp`, `p`.`last_usage_date`, DAY) AS `days_since_last_usage`
        FROM `sales_data` AS `s`
        LEFT JOIN `product_usage` AS `p`
          ON `s`.`product_id` = `p`.`product_id`
          AND `s`.`customer_id` = `p`.`customer_id`
      ) AS `_subquery`
      WHERE `transaction_date` BETWEEN CAST('2024-10-25' AS DATE) AND CAST('2024-11-04' AS DATE)
    ) AS `__MERGE_SOURCE__`
    ON FALSE
    WHEN NOT MATCHED BY SOURCE AND `transaction_date` BETWEEN CAST('2024-10-25' AS DATE) AND CAST('2024-11-04' AS DATE) THEN DELETE
    WHEN NOT MATCHED THEN
      INSERT (
        `transaction_id`, `product_id`, `customer_id`, `transaction_amount`, `transaction_date`, `transaction_timestamp_pst`,
        `payment_method`, `currency`, `last_usage_date`, `usage_count`, `feature_utilization_score`, `user_segment`, `user_type`,
        `days_since_last_usage`
      )
      VALUES (
        `transaction_id`, `product_id`, `customer_id`, `transaction_amount`, `transaction_date`, `transaction_timestamp_pst`,
        `payment_method`, `currency`, `last_usage_date`, `usage_count`, `feature_utilization_score`, `user_segment`, `user_type`,
        `days_since_last_usage`
      )
    ```

    SQLMesh は、プラン環境の名前に基づいて、サフィックスが付けられた `__dev` スキーマを作成します。

    ```sql
    CREATE SCHEMA IF NOT EXISTS `sqlmesh-public-demo`.`demo__dev`
    ```

    SQLMesh は、物理レイヤーのバージョン管理されたテーブルを指すビューを仮想レイヤーに作成します。

    ```sql
    CREATE OR REPLACE VIEW `sqlmesh-public-demo`.`demo__dev`.`incrementals_demo` AS
    SELECT *
    FROM `sqlmesh-public-demo`.`sqlmesh__demo`.`demo__incrementals_demo__50975949`
    ```

!!! tip "重要"

    SQLMesh のスケジューラおよび定義済みマクロ変数との適切な連携を確保するため、モデルの `time_column` は [UTC タイムゾーン](https://en.wikipedia.org/wiki/Coordinated_Universal_Time) で指定する必要があります。

    この要件は、datetime/timestamp 列がデータシステムに取り込まれるとすぐに UTC に変換し、下流での使用のためにシステムから出力される際にのみローカルタイムゾーンに変換するという、データエンジニアリングのベストプラクティスと一致しています。`cron_tz` フラグは**この要件を変更しません**。

    すべてのタイムゾーン変換コードをシステムの最初と最後の変換モデルに配置することで、モデル間のデータフローにおけるタイムゾーン関連のエラーを防止できます。

    モデルで異なるタイムゾーンを使用する必要がある場合は、[lookback](./overview.md#lookback)、[allow_partials](./overview.md#allow_partials)、オフセット時間を指定した [cron](./overview.md#cron) などのパラメータを使用して、モデルのタイムゾーンと SQLMesh で使用される UTC タイムゾーンの不一致を補正することができます。


この例では、`MODEL` DDL で時間列名 `event_date` を指定し、時間範囲でレコードをフィルター処理する SQL `WHERE` 句を含む完全な `INCREMENTAL_BY_TIME_RANGE` モデルを実装します。

```sql linenums="1" hl_lines="3-5 12-13"
MODEL (
  name db.events,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column event_date
  )
);

SELECT
  event_date::TEXT as event_date,
  event_payload::TEXT as payload
FROM raw_events
WHERE
  event_date BETWEEN @start_ds AND @end_ds;
```

### 時間列

SQLMesh は、モデルの出力のどの列が各レコードに関連付けられたタイムスタンプまたは日付を表すかを認識する必要があります。

!!! tip "重要"

    `time_column` 変数は UTC タイムゾーンで指定する必要があります。詳細は [上記](#timezones) をご覧ください。

time 列は、データ [restatement](../plans.md#restatement-plans) 中に上書きされるレコードを決定するために使用され、パーティション分割をサポートするエンジン (Apache Spark など) のパーティションキーとして使用されます。time 列の名前は、`MODEL` DDL の `kind` 仕様で指定します。

```sql linenums="1" hl_lines="4"
MODEL (
  name db.events,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column event_date -- This model's time information is stored in the `event_date` column
  )
);
```

デフォルトでは、SQLMesh は時刻列が `%Y-%m-%d` 形式であると想定します。他の形式の場合は、書式設定文字列を使用してデフォルトを上書きできます。

```sql linenums="1" hl_lines="4"
MODEL (
  name db.events,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column (event_date, '%Y-%m-%d')
  )
);
```

!!! note

    時間形式は、モデルのクエリの定義に使用したのと同じ SQL 方言を使用して定義する必要があります。

SQLMesh は、time 列を使用して、実行時にモデルのクエリに時間範囲フィルターを自動的に追加します。これにより、対象期間に含まれないレコードが格納されるのを防ぎます。これは、遅れて到着するデータを処理する際に、関連のないレコードが意図せず上書きされるのを防ぐ安全機構です。

モデルクエリの `WHERE` 句に記述する必須フィルターは、上流テーブルから読み取られる **入力** データをフィルター処理し、モデルによって処理されるデータ量を削減します。自動的に追加された時間範囲フィルターは、モデルクエリの **出力** データに適用され、データ漏洩を防ぎます。

次のモデル定義を考えてみましょう。`receipt_date` 列で `WHERE` 句フィルターを指定しています。モデルの `time_column` は別の列 `event_date` であり、そのフィルターはモデルクエリに自動的に追加されます。このアプローチは、上流モデルの時間列がモデルの時間列と異なる場合に役立ちます。

```sql linenums="1"
MODEL (
  name db.events,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column event_date -- `event_date` is model's time column
  )
);

SELECT
  event_date::TEXT as event_date,
  event_payload::TEXT as payload
FROM raw_events
WHERE
  receipt_date BETWEEN @start_ds AND @end_ds; -- Filter is based on the user-supplied `receipt_date` column
```

実行時に、SQLMesh はモデルのクエリを次のように自動的に変更します。

```sql linenums="1" hl_lines="7"
SELECT
  event_date::TEXT as event_date,
  event_payload::TEXT as payload
FROM raw_events
WHERE
  receipt_date BETWEEN @start_ds AND @end_ds
  AND event_date BETWEEN @start_ds AND @end_ds; -- `event_date` time column filter automatically added by SQLMesh
```

### パーティショニング

デフォルトでは、`time_column` がモデルの [partitioned_by](./overview.md#partitioned_by) プロパティの一部であることを確認しています。これにより、`time_column` はパーティションキーの一部となり、データベースエンジンによるパーティションプルーニングが可能になります。モデル定義に明示的に指定されていない場合は、自動的に追加されます。

ただし、別の列のみでパーティション分割したい場合や、`month(time_column)` のような条件でパーティション分割したいものの、使用しているエンジンが式に基づくパーティション分割をサポートしていない場合は、この設定は望ましくない場合があります。

この動作を無効にするには、次のように `partition_by_time_column false` を設定します。

```sql linenums="1" hl_lines="5"
MODEL (
  name db.events,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column event_date,
    partition_by_time_column false
  ),
  partitioned_by (other_col) -- event_date will no longer be automatically added here and the partition key will just be 'other_col'
);
```

### べき等性

データ[再記述](../plans.md#restatement-plans)中に予期しない結果が発生しないように、時間範囲による増分モデルクエリが[べき等性](../glossary.md#idempotency)であることを確認することをお勧めします。

ただし、上流のモデルとテーブルはモデルのべき等性に影響を与える可能性があることに注意してください。たとえば、モデルクエリで種類[FULL](#full)の上流モデルを参照すると、モデルの実行ごとにデータが変更される可能性があるため、モデルは自動的にべき等ではなくなります。

### マテリアライズ戦略

ターゲットエンジンに応じて、`INCREMENTAL_BY_TIME_RANGE` 種類のモデルは、以下の戦略を使用してマテリアライズされます。

| Engine     | Strategy                                  |
|------------|-------------------------------------------|
| Spark      | INSERT OVERWRITE by time column partition |
| Databricks | INSERT OVERWRITE by time column partition |
| Snowflake  | DELETE by time range, then INSERT         |
| BigQuery   | DELETE by time range, then INSERT         |
| Redshift   | DELETE by time range, then INSERT         |
| Postgres   | DELETE by time range, then INSERT         |
| DuckDB     | DELETE by time range, then INSERT         |

## INCREMENTAL_BY_UNIQUE_KEY

`INCREMENTAL_BY_UNIQUE_KEY` タイプのモデルは、キーに基づいて増分的に計算されます。

以下のルールに基づいて行が挿入または更新されます。

- 新しくロードされたデータのキーがモデルテーブルに存在しない場合、新しいデータ行が挿入されます。
- 新しくロードされたデータのキーがモデルテーブルに既に存在する場合、既存の行が新しいデータで更新されます。
- モデルテーブルには存在するが、新しくロードされたデータには存在しないキーの場合、その行は変更されず、モデルテーブルに残ります。

!!! important "重複キーの防止"

    モデルテーブルで重複キーを避けたい場合は、モデルクエリが重複キーを持つ行を返さないようにする必要があります。

    SQLMesh は重複を自動的に検出したり防止したりしません。

この種類は、以下の特性を持つデータセットに適しています。

* 各レコードには、一意のキーが関連付けられています。
* 各一意のキーに関連付けられているレコードは最大で 1 つだけです。
* レコードの upsert が適切であるため、キーが一致した場合、新しいレコードで既存のレコードを上書きできます。

[緩やかに変化するディメンション](../glossary.md#slowly-changing-dimension-scd) (SCD) は、この説明に適したアプローチの 1 つです。SCD タイプ 2 モデルの具体的なモデルの種類については、[SCD タイプ 2](#scd-type-2) モデルの種類を参照してください。

一意のキー列の名前は、次の例のように、`MODEL` DDL の一部として指定する必要があります。

```sql linenums="1" hl_lines="3-5"
MODEL (
  name db.employees,
  kind INCREMENTAL_BY_UNIQUE_KEY (
    unique_key name
  )
);

SELECT
  name::TEXT as name,
  title::TEXT as title,
  salary::INT as salary
FROM raw_employees;
```

複合キーもサポートされています:

```sql linenums="1" hl_lines="4"
MODEL (
  name db.employees,
  kind INCREMENTAL_BY_UNIQUE_KEY (
    unique_key (first_name, last_name)
  )
);
```

`INCREMENTAL_BY_UNIQUE_KEY` モデル種別では、SQL `WHERE` 句と `@start_date`、`@end_date`、またはその他のマクロ変数（[INCREMENTAL_BY_TIME_RANGE](#incremental_by_time_range) 種別と同様）を使用して、上流レコードを時間範囲でフィルタリングすることもできます。SQLMesh マクロの時間変数は UTC タイムゾーンであることに注意してください。

```sql linenums="1" hl_lines="6-7"
SELECT
  name::TEXT as name,
  title::TEXT as title,
  salary::INT as salary
FROM raw_employee_events
WHERE
  event_date BETWEEN @start_date AND @end_date;
```

??? "このモデル種別を適用する場合のSQLシーケンスの例 (ex: BigQuery)"

    次の定義でモデルを作成し、`sqlmesh plan dev` を実行します。

    ```sql
    MODEL (
      name demo.incremental_by_unique_key_example,
      kind INCREMENTAL_BY_UNIQUE_KEY (
        unique_key id
      ),
      start '2020-01-01',
      cron '@daily',
    );

    SELECT
      id,
      item_id,
      event_date
    FROM demo.seed_model
    WHERE
      event_date BETWEEN @start_date AND @end_date
    ```

    SQLMeshはこのSQLを実行し、物理レイヤーにバージョン管理されたテーブルを作成します。テーブルのバージョン フィンガープリント `1161945221` がテーブル名の一部であることに注意してください。

    ```sql
    CREATE TABLE IF NOT EXISTS `sqlmesh-public-demo`.`sqlmesh__demo`.`demo__incremental_by_unique_key_example__1161945221` (`id` INT64, `item_id` INT64, `event_date` DATE)
    ```

    SQLMesh は、データを処理する前にモデルのクエリを検証します (`WHERE` ステートメントの `FALSE LIMIT 0` とプレースホルダーの日付に注意してください)。

    ```sql
    SELECT `seed_model`.`id` AS `id`, `seed_model`.`item_id` AS `item_id`, `seed_model`.`event_date` AS `event_date`
    FROM `sqlmesh-public-demo`.`sqlmesh__demo`.`demo__seed_model__2834544882` AS `seed_model`
    WHERE (`seed_model`.`event_date` <= CAST('1970-01-01' AS DATE) AND `seed_model`.`event_date` >= CAST('1970-01-01' AS DATE)) AND FALSE LIMIT 0
    ```

    SQLMesh は物理レイヤーにバージョン管理されたテーブルを作成します。

    ```sql
    CREATE OR REPLACE TABLE `sqlmesh-public-demo`.`sqlmesh__demo`.`demo__incremental_by_unique_key_example__1161945221` AS
    SELECT CAST(`id` AS INT64) AS `id`, CAST(`item_id` AS INT64) AS `item_id`, CAST(`event_date` AS DATE) AS `event_date`
    FROM (SELECT `seed_model`.`id` AS `id`, `seed_model`.`item_id` AS `item_id`, `seed_model`.`event_date` AS `event_date`
    FROM `sqlmesh-public-demo`.`sqlmesh__demo`.`demo__seed_model__2834544882` AS `seed_model`
    WHERE `seed_model`.`event_date` <= CAST('2024-10-30' AS DATE) AND `seed_model`.`event_date` >= CAST('2020-01-01' AS DATE)) AS `_subquery`
    ```

    SQLMesh は、プラン環境の名前に基づいて、サフィックスが付けられた `__dev` スキーマを作成します。

    ```sql
    CREATE SCHEMA IF NOT EXISTS `sqlmesh-public-demo`.`demo__dev`
    ```

    SQLMesh は、物理レイヤーのバージョン管理されたテーブルを指すビューを仮想レイヤーに作成します。

    ```sql
    CREATE OR REPLACE VIEW `sqlmesh-public-demo`.`demo__dev`.`incremental_by_unique_key_example` AS
    SELECT * FROM `sqlmesh-public-demo`.`sqlmesh__demo`.`demo__incremental_by_unique_key_example__1161945221`
    ```

**注:** `INCREMENTAL_BY_UNIQUE_KEY` 型のモデルは本質的に[非べき等性](../glossary.md#idempotency)であるため、データの[再ステートメント](../plans.md#restatement-plans)を行う際にはこの点を考慮する必要があります。そのため、このモデルでは部分的なデータの再ステートメントはサポートされていません。つまり、再ステートメントを行うと、テーブル全体が最初から再作成されます。

### ユニークキー式

`unique_key` の値は、列名またはSQL式のいずれかになります。例えば、値の結合に基づいてキーを作成したい場合は、次のようにします。

```sql linenums="1" hl_lines="4"
MODEL (
  name db.employees,
  kind INCREMENTAL_BY_UNIQUE_KEY (
    unique_key COALESCE("name", '')
  )
);
```

### 一致した式の場合

一致が発生した場合（指定されたキーでソースとターゲットが一致した場合）に列を更新するロジックは、デフォルトではすべての列を更新します。これは、以下のようなカスタムロジックで上書きできます。

```sql linenums="1" hl_lines="5"
MODEL (
  name db.employees,
  kind INCREMENTAL_BY_UNIQUE_KEY (
    unique_key name,
    when_matched (
      WHEN MATCHED THEN UPDATE SET target.salary = COALESCE(source.salary, target.salary)
    )
  )
);
```

`when_matched` 式を使用する場合は、ソース列とターゲット列を区別するために `source` と `target` のエイリアスが必要です。

`WHEN MATCHED` 式は複数指定することもできます。例:

```sql linenums="1" hl_lines="5-6"
MODEL (
  name db.employees,
  kind INCREMENTAL_BY_UNIQUE_KEY (
    unique_key name,
    when_matched (
      WHEN MATCHED AND source.value IS NULL THEN UPDATE SET target.salary = COALESCE(source.salary, target.salary)
      WHEN MATCHED THEN UPDATE SET target.title = COALESCE(source.title, target.title)
    )
  )
);
```

**注**: `when_matched` は、`MERGE` ステートメントをサポートするエンジンでのみ使用できます。現在サポートされているエンジンは次のとおりです。

* BigQuery
* Databricks
* Postgres
* Redshift
* Snowflake
* Spark

Redshift の場合、ネイティブの `MERGE` ステートメントの使用を有効にするには、接続時に `enable_merge` フラグを渡し、`true` に設定する必要があります。デフォルトでは無効になっています。

```yaml linenums="1"
gateways:
  redshift:
    connection:
      type: redshift
      enable_merge: true
```

Redshift は、`WHEN MATCHED` 句に対して `UPDATE` または `DELETE` アクションのみをサポートしており、複数の `WHEN MATCHED` 式は許可されません。詳細については、[Redshift のドキュメント](https://docs.aws.amazon.com/redshift/latest/dg/r_MERGE.html#r_MERGE-parameters) を参照してください。

### マージフィルタ式

`MERGE` 文は通常、既存のテーブルの全テーブルスキャンを実行しますが、データ量が多い場合は問題が発生する可能性があります。

`merge_filter` パラメータにフィルタリング条件を渡すことで、全テーブルスキャンを回避できます。

`merge_filter` は、`MERGE` 操作の `ON` 句で使用する述語を 1 つまたは複数指定します。

```sql linenums="1" hl_lines="5"
MODEL (
  name db.employee_contracts,
  kind INCREMENTAL_BY_UNIQUE_KEY (
    unique_key id,
    merge_filter source._operation IS NULL AND target.contract_date > dateadd(day, -7, current_date)
  )
);
```

`when_matched` と同様に、`source` および `target` エイリアスは、ソーステーブルとターゲットテーブルを区別するために使用されます。

既存の dbt プロジェクトで [incremental_predicates](https://docs.getdbt.com/docs/build/incremental-strategy#about-incremental_predicates) 機能が使用されている場合、SQLMesh はそれらを同等の `merge_filter` 仕様に自動的に変換します。

### マテリアライズ戦略

ターゲットエンジンに応じて、`INCREMENTAL_BY_UNIQUE_KEY` 型のモデルは、以下の戦略を使用してマテリアライズされます。

| Engine     | Strategy                            |
|------------|-------------------------------------|
| Spark      | not supported                       |
| Databricks | MERGE ON unique key                 |
| Snowflake  | MERGE ON unique key                 |
| BigQuery   | MERGE ON unique key                 |
| Redshift   | MERGE ON unique key                 |
| Postgres   | MERGE ON unique key                 |
| DuckDB     | DELETE ON matched + INSERT new rows |

## FULL

`FULL` 型のモデルでは、モデルに関連付けられたデータセットは、モデル評価のたびに完全に更新（書き換え）されます。

`FULL` 型のモデルは、特別な設定や追加のクエリを考慮する必要がないため、増分型よりも多少使いやすくなっています。そのため、データを最初から再計算するコストが比較的低く、処理履歴の保存も不要な小規模なデータセットに適しています。ただし、大量のレコードを含むデータセットでこの型を使用すると、実行時間と計算コストが大幅に増加します。

この型は、時間軸を持たない集計テーブルに適しています。時間軸を持つ集計テーブルの場合は、代わりに [INCREMENTAL_BY_TIME_RANGE](#incremental_by_time_range) 型の使用を検討してください。

次の例では、`FULL` 型のモデルを指定しています。

```sql linenums="1" hl_lines="3"
MODEL (
  name db.salary_by_title_agg,
  kind FULL
);

SELECT
  title,
  AVG(salary)
FROM db.employees
GROUP BY title;
```

??? "このモデル種別を適用する場合のSQLシーケンスの例 (ex: BigQuery)"

    次の定義でモデルを作成し、`sqlmesh plan dev` を実行します。

    ```sql
    MODEL (
      name demo.full_model_example,
      kind FULL,
      cron '@daily',
      grain item_id,
    );

    SELECT
      item_id,
      COUNT(DISTINCT id) AS num_orders
    FROM demo.incremental_model
    GROUP BY
      item_id
    ```

    SQLMeshはこのSQLを実行し、物理レイヤーにバージョン管理されたテーブルを作成します。テーブルのバージョン フィンガープリント `2345651858` がテーブル名の一部であることに注意してください。

    ```sql
    CREATE TABLE IF NOT EXISTS `sqlmesh-public-demo`.`sqlmesh__demo`.`demo__full_model_example__2345651858` (`item_id` INT64, `num_orders` INT64)
    ```

    SQLMesh は、データを処理する前にモデルのクエリを検証します (`WHERE FALSE` と `LIMIT 0` に注意してください)。

    ```sql
    SELECT `incremental_model`.`item_id` AS `item_id`, COUNT(DISTINCT `incremental_model`.`id`) AS `num_orders`
    FROM `sqlmesh-public-demo`.`sqlmesh__demo`.`demo__incremental_model__89556012` AS `incremental_model`
    WHERE FALSE
    GROUP BY `incremental_model`.`item_id` LIMIT 0
    ```

    SQLMesh は物理レイヤーにバージョン管理されたテーブルを作成します。

    ```sql
    CREATE OR REPLACE TABLE `sqlmesh-public-demo`.`sqlmesh__demo`.`demo__full_model_example__2345651858` AS
    SELECT CAST(`item_id` AS INT64) AS `item_id`, CAST(`num_orders` AS INT64) AS `num_orders`
    FROM (SELECT `incremental_model`.`item_id` AS `item_id`, COUNT(DISTINCT `incremental_model`.`id`) AS `num_orders`
    FROM `sqlmesh-public-demo`.`sqlmesh__demo`.`demo__incremental_model__89556012` AS `incremental_model`
    GROUP BY `incremental_model`.`item_id`) AS `_subquery`
    ```

    SQLMesh は、プラン環境の名前に基づいて、サフィックスが付けられた `__dev` スキーマを作成します。

    ```sql
    CREATE SCHEMA IF NOT EXISTS `sqlmesh-public-demo`.`demo__dev`
    ```

    SQLMesh は、物理レイヤーのバージョン管理されたテーブルを指すビューを仮想レイヤーに作成します。

    ```sql
    CREATE OR REPLACE VIEW `sqlmesh-public-demo`.`demo__dev`.`full_model_example` AS
    SELECT * FROM `sqlmesh-public-demo`.`sqlmesh__demo`.`demo__full_model_example__2345651858`
    ```

### マテリアライズ戦略

ターゲットエンジンに応じて、 `FULL` タイプのモデルは以下の戦略を使用してマテリアライズされます。

| Engine     | Strategy                         |
|------------|----------------------------------|
| Spark      | INSERT OVERWRITE                 |
| Databricks | INSERT OVERWRITE                 |
| Snowflake  | CREATE OR REPLACE TABLE          |
| BigQuery   | CREATE OR REPLACE TABLE          |
| Redshift   | DROP TABLE, CREATE TABLE, INSERT |
| Postgres   | DROP TABLE, CREATE TABLE, INSERT |
| DuckDB     | CREATE OR REPLACE TABLE          |

## VIEW

これまで説明したモデルの種類では、モデルクエリの出力がマテリアライズされ、物理テーブルに保存されます。

`VIEW` の種類は異なり、モデル実行中に実際にデータが書き込まれることはありません。代わりに、モデルのクエリに基づいて、非マテリアライズドビュー（または「仮想テーブル」）が作成または置換されます。

**注:** モデルの種類が指定されていない場合、デフォルトのモデルの種類は `VIEW` です。

**注:** Python モデルは `VIEW` モデルの種類をサポートしていません。代わりに SQL モデルを使用してください。

**注:** この種類では、モデルのクエリは、下流のクエリでモデルが参照されるたびに評価されます。モデルのクエリが計算負荷が高い場合や、モデルが多数の下流のクエリで参照される場合、望ましくない計算コストと時間が発生する可能性があります。

次の例では、モデルの種類として `VIEW` を指定しています。

```sql linenums="1" hl_lines="3"
MODEL (
  name db.highest_salary,
  kind VIEW
);

SELECT
  MAX(salary)
FROM db.employees;
```

??? "このモデル種別を適用する場合のSQLシーケンスの例 (ex: BigQuery)"

    次の定義でモデルを作成し、`sqlmesh plan dev` を実行します。

    ```sql
    MODEL (
      name demo.example_view,
      kind VIEW,
      cron '@daily',
    );

    SELECT
      'hello there' as a_column
    ```

    SQLMeshはこのSQLを実行し、物理レイヤーにバージョン管理されたビューを作成します。ビューのバージョン フィンガープリント `1024042926` がビュー名の一部であることに注意してください。

    ```sql
    CREATE OR REPLACE VIEW `sqlmesh-public-demo`.`sqlmesh__demo`.`demo__example_view__1024042926`
    (`a_column`) AS SELECT 'hello there' AS `a_column`
    ```

    SQLMesh は、プラン環境の名前に基づいて、サフィックスが付けられた `__dev` スキーマを作成します。

    ```sql
    CREATE SCHEMA IF NOT EXISTS `sqlmesh-public-demo`.`demo__dev`
    ```

    SQLMesh は、物理レイヤーのバージョン管理されたビューを指すビューを仮想レイヤーに作成します。

    ```sql
    CREATE OR REPLACE VIEW `sqlmesh-public-demo`.`demo__dev`.`example_view` AS
    SELECT * FROM `sqlmesh-public-demo`.`sqlmesh__demo`.`demo__example_view__1024042926`
    ```


### マテリアライズド・ビュー

`VIEW` モデルの種類は、`materialized` フラグを `true` に設定することで、マテリアライズド・ビューを表すように設定できます。

```sql linenums="1" hl_lines="4"
MODEL (
  name db.highest_salary,
  kind VIEW (
    materialized true
  )
);
```

**注:** このフラグは、マテリアライズド・ビューをサポートするエンジンにのみ適用され、他のエンジンでは無視されます。サポートされているエンジンは次のとおりです。

* BigQuery
* Databricks
* Snowflake

この種のモデルの評価中、評価中にレンダリングされたモデルのクエリが、このモデルの以前のビュー作成時に使用されたクエリと一致しない場合、または対象のビューが存在しない場合にのみ、ビューが置換または再作成されます。したがって、マテリアライズド・ビューのメリットを最大限に活用するために必要な場合にのみ、ビューが再作成されます。

## EMBEDDED

埋め込みモデルは、異なる種類のモデル間で共通のロジックを共有する方法です。

データウェアハウス内の `EMBEDDED` モデルには、データアセット（テーブルやビュー）は関連付けられません。代わりに、`EMBEDDED` モデルのクエリは、それを参照する各下流モデルのクエリにサブクエリとして直接挿入されます。

**注:** Python モデルは `EMBEDDED` モデルをサポートしていません。代わりに SQL モデルを使用してください。

次の例では、`EMBEDDED` モデルを指定しています。

```sql linenums="1" hl_lines="3"
MODEL (
  name db.unique_employees,
  kind EMBEDDED
);

SELECT DISTINCT
  name
FROM db.employees;
```

## SEED

`SEED` モデルの種類は、SQLMesh プロジェクトで静的 CSV データセットを使用するための [シード モデル](./seed_models.md) を指定するために使用されます。

**注:**

- シードモデルは、SQL モデルまたはシードファイル（あるいはその両方）が更新されない限り、一度だけロードされます。
- Python モデルは `SEED` モデルをサポートしていません。代わりに SQL モデルを使用してください。

??? "このモデル種別を適用する場合のSQLシーケンスの例 (ex: BigQuery)"

    次の定義でモデルを作成し、`sqlmesh plan dev` を実行します。

    ```sql
    MODEL (
      name demo.seed_example,
      kind SEED (
        path '../../seeds/seed_example.csv'
      ),
      columns (
        id INT64,
        item_id INT64,
        event_date DATE
      ),
      grain (id, event_date)
    )
    ```

    SQLMeshはこのSQLを実行し、物理レイヤーにバージョン管理されたテーブルを作成します。テーブルのバージョン フィンガープリント `3038173937` がテーブル名の一部であることに注意してください。

    ```sql
    CREATE TABLE IF NOT EXISTS `sqlmesh-public-demo`.`sqlmesh__demo`.`demo__seed_example__3038173937` (`id` INT64, `item_id` INT64, `event_date` DATE)
    ```

    SQLMesh はシードを物理層の一時テーブルとしてアップロードします。

    ```sql
    sqlmesh-public-demo.sqlmesh__demo.__temp_demo__seed_example__3038173937_9kzbpld7
    ```

    SQLMesh は、一時テーブルから物理レイヤーにバージョン管理されたテーブルを作成します。

    ```sql
    CREATE OR REPLACE TABLE `sqlmesh-public-demo`.`sqlmesh__demo`.`demo__seed_example__3038173937` AS
    SELECT CAST(`id` AS INT64) AS `id`, CAST(`item_id` AS INT64) AS `item_id`, CAST(`event_date` AS DATE) AS `event_date`
    FROM (SELECT `id`, `item_id`, `event_date`
    FROM `sqlmesh-public-demo`.`sqlmesh__demo`.`__temp_demo__seed_example__3038173937_9kzbpld7`) AS `_subquery`
    ```

    SQLMesh は物理層内の一時テーブルを削除します。

    ```sql
    DROP TABLE IF EXISTS `sqlmesh-public-demo`.`sqlmesh__demo`.`__temp_demo__seed_example__3038173937_9kzbpld7`
    ```

    SQLMesh は、プラン環境の名前に基づいて、サフィックスが付けられた `__dev` スキーマを作成します。

    ```sql
    CREATE SCHEMA IF NOT EXISTS `sqlmesh-public-demo`.`demo__dev`
    ```

    SQLMesh は、物理レイヤーのバージョン管理されたテーブルを指すビューを仮想レイヤーに作成します。

    ```sql
    CREATE OR REPLACE VIEW `sqlmesh-public-demo`.`demo__dev`.`seed_example` AS
    SELECT * FROM `sqlmesh-public-demo`.`sqlmesh__demo`.`demo__seed_example__3038173937`
    ```

## SCD Type 2

SCD タイプ 2 は、SQLMesh プロジェクトで [緩やかに変化するディメンション](https://en.wikipedia.org/wiki/Slowly_changing_dimension#Type_2:_add_new_row) (SCD) をサポートするモデル種別です。SCD はデータウェアハウスでよく使用されるパターンで、レコードの変更を時間経過とともに追跡できます。

SQLMesh は、モデルに `valid_from` 列と `valid_to` 列を追加することでこれを実現します。`valid_from` 列はレコードが有効になったタイムスタンプ（その時点を含む）で、`valid_to` 列はレコードが無効になったタイムスタンプ（その時点を含まない）です。`valid_to` 列は、最新のレコードでは `NULL` に設定されます。

したがって、これらのモデルを使用することで、特定のレコードの最新の値だけでなく、過去の任意の時点の値も把握できます。この履歴を維持するには、ストレージとコンピューティングリソースの増加というコストがかかります。また、履歴が非常に大きくなる可能性があるため、頻繁に変更されるソースには適さない可能性があります。

**注**: このモデルの種類では、部分的なデータの再ステートメント[restatement](../plans.md#restatement-plans)はサポートされていません。つまり、再ステートメントを行うと、テーブル全体が最初から再作成されます。これはデータ損失につながる可能性があるため、この種類のモデルではデータの再ステートメントはデフォルトで無効になっています。

変更を追跡する方法は、時間別（推奨）と列別の2つがあります。

### SCD Type 2 By Time (Recommended)

SCD タイプ 2 (時間別) は、特定のレコードの最終更新日時を示す「更新日時」タイムスタンプがテーブルに定義されているテーブルからのソースをサポートします。
この「更新日時」によってレコードの最終更新日時が正確にわかるため、生成される SCD タイプ 2 テーブルの精度が向上するため、この方法が推奨されます。

この例では、`SCD_TYPE_2_BY_TIME` モデル種別を指定しています。

```sql linenums="1" hl_lines="3"
MODEL (
  name db.menu_items,
  kind SCD_TYPE_2_BY_TIME (
    unique_key id,
  )
);

SELECT
  id::INT,
  name::STRING,
  price::DOUBLE,
  updated_at::TIMESTAMP
FROM
  stg.current_menu_items;
```

SQLMesh は、こ​​のテーブルを次の構造で実現します。

```sql linenums="1"
TABLE db.menu_items (
  id INT,
  name STRING,
  price DOUBLE,
  updated_at TIMESTAMP,
  valid_from TIMESTAMP,
  valid_to TIMESTAMP
);
```

モデル定義に以下を追加することで、`updated_at` 列名を変更することもできます。

```sql linenums="1" hl_lines="5"
MODEL (
  name db.menu_items,
  kind SCD_TYPE_2_BY_TIME (
    unique_key id,
    updated_at_name my_updated_at -- Name for `updated_at` column
  )
);

SELECT
  id,
  name,
  price,
  my_updated_at
FROM
  stg.current_menu_items;
```

SQLMesh は、こ​​のテーブルを次の構造で実現します。

```sql linenums="1"
TABLE db.menu_items (
  id INT,
  name STRING,
  price DOUBLE,
  my_updated_at TIMESTAMP,
  valid_from TIMESTAMP,
  valid_to TIMESTAMP
);
```

### SCD Type 2 By Column

SCD タイプ 2 (列別) は、テーブルに「更新日時」タイムスタンプが定義されていないテーブルからのソースをサポートします。
代わりに、`columns` フィールドに定義された列の値が変更されているかどうかを確認し、変更されている場合は、変更が検出された実行時間として `valid_from` 時刻を記録します。

この例では、`SCD_TYPE_2_BY_COLUMN` モデルの種類を指定しています。

```sql linenums="1" hl_lines="3"
MODEL (
  name db.menu_items,
  kind SCD_TYPE_2_BY_COLUMN (
    unique_key id,
    columns [name, price]
  )
);

SELECT
  id::INT,
  name::STRING,
  price::DOUBLE,
FROM
  stg.current_menu_items;
```

SQLMesh は、こ​​のテーブルを次の構造で実現します。

```sql linenums="1"
TABLE db.menu_items (
  id INT,
  name STRING,
  price DOUBLE,
  valid_from TIMESTAMP,
  valid_to TIMESTAMP
);
```

### 列名の変更

SQLMesh は、`valid_from` 列と `valid_to` 列をテーブルに自動的に追加します。
これらの列の名前を指定したい場合は、モデル定義に以下のコードを追加してください。

```sql linenums="1" hl_lines="5-6"
MODEL (
  name db.menu_items,
  kind SCD_TYPE_2_BY_TIME (
    unique_key id,
    valid_from_name my_valid_from, -- Name for `valid_from` column
    valid_to_name my_valid_to -- Name for `valid_to` column
  )
);
```

SQLMesh は、こ​​のテーブルを次の構造で実現します。

```sql linenums="1"
TABLE db.menu_items (
  id INT,
  name STRING,
  price DOUBLE,
  updated_at TIMESTAMP,
  my_valid_from TIMESTAMP,
  my_valid_to TIMESTAMP
);
```

### 削除

ハード削除とは、ソーステーブルにレコードが存在しなくなった状態を指します。この場合、

`invalidate_hard_deletes` が `false` (デフォルト) に設定されている場合、以下のようになります。

* `valid_to` 列は引き続き `NULL` に設定されます (したがって、引き続き「有効」とみなされます)。
* レコードが再度追加された場合、`valid_to` 列は新しいレコードの `valid_from` に設定されます。

レコードが再び追加されると、新しいレコードはテーブルに挿入され、`valid_from` は次のように設定されます。

* SCD_TYPE_2_BY_TIME: SCD タイプ 2 テーブル内の新しいレコードの `updated_at` タイムスタンプ、または削除されたレコードの `valid_from` タイムスタンプのうち大きい方
* SCD_TYPE_2_BY_COLUMN: レコードが再び検出されたときの `execution_time`

`invalidate_hard_deletes` が `true` に設定されている場合:

* `valid_to` 列は、欠落レコードを検出した SQLMesh 実行の開始時刻 (`execution_time`) に設定されます。
* レコードが再び追加される場合、`valid_to` 列は変更されません。

`invalidate_hard_deletes` について考える一つの方法は、`invalidate_hard_deletes` が `true` に設定されている場合、SCD タイプ 2 テーブルでは削除がいつ行われたかが記録されるため、削除が最も正確に追跡されるということです。
ただし、その結果、削除されてから再度追加された時点の間に時間のギャップがある場合、レコード間にギャップが生じる可能性があります。
ギャップを生じさせたくない場合、つまり、ソース内の欠落レコードを依然として「有効」と見なしたい場合は、デフォルト値のままにするか、`invalidate_hard_deletes` を `false` に設定してください。

### Example of SCD Type 2 By Time in Action

ソース テーブルに次のデータがあり、`invalidate_hard_deletes` が `true` に設定されているとします。

| ID | Name             | Price |     Updated At      |
|----|------------------|:-----:|:-------------------:|
| 1  | Chicken Sandwich | 10.99 | 2020-01-01 00:00:00 |
| 2  | Cheeseburger     | 8.99  | 2020-01-01 00:00:00 |
| 3  | French Fries     | 4.99  | 2020-01-01 00:00:00 |

The target table, which is currently empty, will be materialized with the following data:

| ID | Name             | Price |     Updated At      |     Valid From      | Valid To |
|----|------------------|:-----:|:-------------------:|:-------------------:|:--------:|
| 1  | Chicken Sandwich | 10.99 | 2020-01-01 00:00:00 | 1970-01-01 00:00:00 |   NULL   |
| 2  | Cheeseburger     | 8.99  | 2020-01-01 00:00:00 | 1970-01-01 00:00:00 |   NULL   |
| 3  | French Fries     | 4.99  | 2020-01-01 00:00:00 | 1970-01-01 00:00:00 |   NULL   |

Now lets say that you update the source table with the following data:

| ID | Name             | Price |     Updated At      |
|----|------------------|:-----:|:-------------------:|
| 1  | Chicken Sandwich | 12.99 | 2020-01-02 00:00:00 |
| 3  | French Fries     | 4.99  | 2020-01-01 00:00:00 |
| 4  | Milkshake        | 3.99  | 2020-01-02 00:00:00 |

変更の概要:

* チキンサンドイッチの価格が 10.99 ドルから 12.99 ドルに引き上げられました。
* チーズバーガーがメニューから削除されました。
* ミルクシェイクがメニューに追加されました。

パイプラインが `2020-01-02 11:00:00` に実行されたと仮定すると、ターゲットテーブルは次のデータで更新されます。

| ID | Name             | Price |     Updated At      |     Valid From      |      Valid To       |
|----|------------------|:-----:|:-------------------:|:-------------------:|:-------------------:|
| 1  | Chicken Sandwich | 10.99 | 2020-01-01 00:00:00 | 1970-01-01 00:00:00 | 2020-01-02 00:00:00 |
| 1  | Chicken Sandwich | 12.99 | 2020-01-02 00:00:00 | 2020-01-02 00:00:00 |        NULL         |
| 2  | Cheeseburger     | 8.99  | 2020-01-01 00:00:00 | 1970-01-01 00:00:00 | 2020-01-02 11:00:00 |
| 3  | French Fries     | 4.99  | 2020-01-01 00:00:00 | 1970-01-01 00:00:00 |        NULL         |
| 4  | Milkshake        | 3.99  | 2020-01-02 00:00:00 | 2020-01-02 00:00:00 |        NULL         |

最後のパスでは、次のデータでソース テーブルを更新するとします。

| ID | Name                | Price |     Updated At      |
|----|---------------------|:-----:|:-------------------:|
| 1  | Chicken Sandwich    | 14.99 | 2020-01-03 00:00:00 |
| 2  | Cheeseburger        | 8.99  | 2020-01-03 00:00:00 |
| 3  | French Fries        | 4.99  | 2020-01-01 00:00:00 |
| 4  | Chocolate Milkshake | 3.99  | 2020-01-02 00:00:00 |

変更の概要：

* チキンサンドイッチの価格が 12.99 ドルから 14.99 ドルに値上げされました（きっと美味しいはずです！）。
* チーズバーガーが元の名称と価格でメニューに復活しました。
* ミルクシェイクの名称が「チョコレートミルクシェイク」に更新されました。

ターゲットテーブルは以下のデータで更新されます。

| ID | Name                | Price |     Updated At      |     Valid From      |      Valid To       |
|----|---------------------|:-----:|:-------------------:|:-------------------:|:-------------------:|
| 1  | Chicken Sandwich    | 10.99 | 2020-01-01 00:00:00 | 1970-01-01 00:00:00 | 2020-01-02 00:00:00 |
| 1  | Chicken Sandwich    | 12.99 | 2020-01-02 00:00:00 | 2020-01-02 00:00:00 | 2020-01-03 00:00:00 |
| 1  | Chicken Sandwich    | 14.99 | 2020-01-03 00:00:00 | 2020-01-03 00:00:00 |        NULL         |
| 2  | Cheeseburger        | 8.99  | 2020-01-01 00:00:00 | 1970-01-01 00:00:00 | 2020-01-02 11:00:00 |
| 2  | Cheeseburger        | 8.99  | 2020-01-03 00:00:00 | 2020-01-03 00:00:00 |        NULL         |
| 3  | French Fries        | 4.99  | 2020-01-01 00:00:00 | 1970-01-01 00:00:00 |        NULL         |
| 4  | Milkshake           | 3.99  | 2020-01-02 00:00:00 | 2020-01-02 00:00:00 | 2020-01-03 00:00:00 |
| 4  | Chocolate Milkshake | 3.99  | 2020-01-03 00:00:00 | 2020-01-03 00:00:00 |        NULL         |

**注:** `Cheeseburger` は `2020-01-02 11:00:00` から `2020-01-03 00:00:00` の間に削除されました。つまり、この期間にテーブルをクエリした場合、メニューに `Cheeseburger` は表示されません。
これは、提供されたソースデータに基づくメニューの最も正確な表現です。
`Cheeseburger` が `2020-01-01 00:00:00` のタイムスタンプで元の更新後にメニューに再度追加された場合、新しいレコードの `valid_from` タイムスタンプは `2020-01-02 11:00:00` となり、アイテムが削除された期間はなくなります。
この場合、更新日時のタイムスタンプは変更されていないため、項目が誤って削除された可能性があり、これもソース データに基づくメニューを最も正確に表しています。


### Example of SCD Type 2 By Column in Action

ソース テーブルに次のデータがあり、`invalidate_hard_deletes` が `true` に設定されているとします。

| ID | Name             | Price |
|----|------------------|:-----:|
| 1  | Chicken Sandwich | 10.99 |
| 2  | Cheeseburger     | 8.99  |
| 3  | French Fries     | 4.99  |

SCD タイプ 2 列別モデルを構成して、`Name` 列と `Price` 列の変更を確認します。

現在空であるターゲットテーブルは、以下のデータでマテリアライズされます。

| ID | Name             | Price |     Valid From      | Valid To |
|----|------------------|:-----:|:-------------------:|:--------:|
| 1  | Chicken Sandwich | 10.99 | 1970-01-01 00:00:00 |   NULL   |
| 2  | Cheeseburger     | 8.99  | 1970-01-01 00:00:00 |   NULL   |
| 3  | French Fries     | 4.99  | 1970-01-01 00:00:00 |   NULL   |

ここで、次のデータでソース テーブルを更新するとします。

| ID | Name             | Price |
|----|------------------|:-----:|
| 1  | Chicken Sandwich | 12.99 |
| 3  | French Fries     | 4.99  |
| 4  | Milkshake        | 3.99  |

変更の概要:

* チキンサンドイッチの価格が 10.99 ドルから 12.99 ドルに引き上げられました。
* チーズバーガーがメニューから削除されました。
* ミルクシェイクがメニューに追加されました。

パイプラインが `2020-01-02 11:00:00` に実行されたと仮定すると、ターゲットテーブルは次のデータで更新されます。

| ID | Name             | Price |     Valid From      |      Valid To       |
|----|------------------|:-----:|:-------------------:|:-------------------:|
| 1  | Chicken Sandwich | 10.99 | 1970-01-01 00:00:00 | 2020-01-02 11:00:00 |
| 1  | Chicken Sandwich | 12.99 | 2020-01-02 11:00:00 |        NULL         |
| 2  | Cheeseburger     | 8.99  | 1970-01-01 00:00:00 | 2020-01-02 11:00:00 |
| 3  | French Fries     | 4.99  | 1970-01-01 00:00:00 |        NULL         |
| 4  | Milkshake        | 3.99  | 2020-01-02 11:00:00 |        NULL         |

最後のパスでは、次のデータでソース テーブルを更新するとします。

| ID | Name                | Price |
|----|---------------------|:-----:|
| 1  | Chicken Sandwich    | 14.99 |
| 2  | Cheeseburger        | 8.99  |
| 3  | French Fries        | 4.99  |
| 4  | Chocolate Milkshake | 3.99  |

変更の概要:

* チキンサンドイッチの価格が 12.99 ドルから 14.99 ドルに値上げされました (きっとお得でしょう!)
* チーズバーガーが元の名称と価格でメニューに再追加されました。
* ミルクシェイクの名称が「チョコレートミルクシェイク」に更新されました。

パイプラインが `2020-01-03 11:00:00` に実行されたと仮定すると、ターゲットテーブルは次のデータで更新されます。

| ID | Name                | Price |     Valid From      |      Valid To       |
|----|---------------------|:-----:|:-------------------:|:-------------------:|
| 1  | Chicken Sandwich    | 10.99 | 1970-01-01 00:00:00 | 2020-01-02 11:00:00 |
| 1  | Chicken Sandwich    | 12.99 | 2020-01-02 11:00:00 | 2020-01-03 11:00:00 |
| 1  | Chicken Sandwich    | 14.99 | 2020-01-03 11:00:00 |        NULL         |
| 2  | Cheeseburger        | 8.99  | 1970-01-01 00:00:00 | 2020-01-02 11:00:00 |
| 2  | Cheeseburger        | 8.99  | 2020-01-03 11:00:00 |        NULL         |
| 3  | French Fries        | 4.99  | 1970-01-01 00:00:00 |        NULL         |
| 4  | Milkshake           | 3.99  | 2020-01-02 11:00:00 | 2020-01-03 11:00:00 |
| 4  | Chocolate Milkshake | 3.99  | 2020-01-03 11:00:00 |        NULL         |

**注:** `Cheeseburger` は `2020-01-02 11:00:00` から `2020-01-03 11:00:00` まで削除されました。つまり、その時間範囲内にテーブルをクエリした場合、メニューに `Cheeseburger` は表示されません。
これは、提供されたソースデータに基づくメニューの最も正確な表現です。

### 共有構成オプション

| 名前 | 説明 | タイプ |
|------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------|
| unique_key | ソースとターゲット間の行を識別するために使用される一意のキー | 文字列のリストまたは文字列 |
| valid_from_name | ターゲット テーブルに作成する `valid_from` 列の名前。デフォルト: `valid_from` | 文字列 |
| valid_to_name | ターゲット テーブルに作成する `valid_to` 列の名前。デフォルト: `valid_to` | 文字列 |
| invalidate_hard_deletes | `true` に設定すると、ソース テーブルにレコードがない場合、そのレコードは無効としてマークされます。デフォルト: `false` | bool |
| batch_size | 1 回のバックフィル タスクで評価できる間隔の最大数。 `None` の場合、すべての間隔が単一のタスクの一部として処理されます。このユースケースの詳細については、[履歴データを含むソーステーブルの処理](#processing-source-table-with-historical-data) を参照してください。(デフォルト: `None`) | int |

!!! tip "重要"

    BigQueryを使用する場合、valid_from/valid_to列のデフォルトのデータ型はDATETIMEです。TIMESTAMPを使用する場合は、モデル定義でデータ型を指定できます。

    ```sql linenums="1" hl_lines="5"
    MODEL (
      name db.menu_items,
      kind SCD_TYPE_2_BY_TIME (
        unique_key id,
        time_data_type TIMESTAMP
      )
    );
    ```

    これは、他のエンジンでも期待されるデータ型を変更するために使用できる可能性がありますが、BigQuery でのみテストされています。

### SCD Type 2 By Time Configuration Options

| 名前 | 説明 | タイプ |
|-------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------|
| updated_at_name | 新規または更新されたレコードを確認するためのタイムスタンプを含む列の名前。デフォルト: `updated_at` | 文字列 |
| updated_at_as_valid_from | デフォルトでは、新しい行の `valid_from` は `1970-01-01 00:00:00` に設定されています。これにより、行が挿入されたときに `updated_at` の有効値に設定するように動作が変更されます。デフォルト: `false` | bool |

### SCD Type 2 By Column Configuration Options

| 名前 | 説明 | タイプ |
|------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------|
| columns | 変更を確認する列の名前。すべての列を確認する場合は `*` を使用します。| 文字列のリストまたは文字列 |
| execution_time_as_valid_from | デフォルトでは、モデルが最初に読み込まれるときに `valid_from` は `1970-01-01 00:00:00` に設定され、それ以降の新しい行にはパイプラインが実行された時点の `execution_time` が含まれます。これにより、常に `execution_time` を使用するように動作が変更されます。デフォルト: `false` | bool |
| updated_at_name | valid_from として使用するタイムスタンプを含むテーブルから取得する場合は、このプロパティをその列に設定します。このユースケースの詳細については、[履歴データを含むソーステーブルの処理](#processing-source-table-with-historical-data)を参照してください。(デフォルト: `None`) | int |


### 履歴データを含むソーステーブルの処理

SCD タイプ 2 の最も一般的なケースは、テーブルにまだ履歴が含まれていない場合に、そのテーブルに履歴を作成することです。
レストランのメニューの例では、メニューには現在提供されているものだけが示されていますが、過去の履歴を知りたい場合があります。
この場合、`batch_size` のデフォルト設定である `None` が最適です。

もう 1 つのユースケースは、既に履歴が含まれているソーステーブルを処理することです。
この一般的な例としては、毎日の終わりにデータのスナップショットを取得するソースシステムによって作成される「日次スナップショット」テーブルが挙げられます。
ソーステーブルに「日次スナップショット」テーブルのような履歴レコードが含まれている場合は、`batch_size` を `1` に設定して、各間隔（`@daily` cron の場合は各日）を順番に処理します。
これにより、履歴レコードが SCD タイプ 2 テーブルに適切にキャプチャされます。

#### 例 - 日次スナップショットテーブルからのソース

```sql linenums="1"
MODEL (
    name db.table,
    kind SCD_TYPE_2_BY_COLUMN (
        unique_key id,
        columns [some_value],
        updated_at_name ds,
        batch_size 1
    ),
    start '2025-01-01',
    cron '@daily'
);
SELECT
    id,
    some_value,
    ds
FROM
    source_table
WHERE
    ds between @start_ds and @end_ds
```

これは、ソーステーブルの各日を順番に処理します（処理対象が複数日の場合）。`some_value` 列が変更されていないか確認します。変更されている場合は、`valid_from` が `ds` 列と一致するように設定されます（最初の値は `1970-01-01 00:00:00` になります）。

If the source data was the following:

| id | some_value |     ds      |
|----|------------|:-----------:|
| 1  | 1          | 2025-01-01  |
| 1  | 2          | 2025-01-02  |
| 1  | 3          | 2025-01-03  |
| 1  | 3          | 2025-01-04  |

結果の SCD タイプ 2 テーブルは次のようになります。

| id | some_value |     ds      |     valid_from      |      valid_to       |
|----|------------|:-----------:|:-------------------:|:-------------------:|
| 1  | 1          | 2025-01-01  | 1970-01-01 00:00:00 | 2025-01-02 00:00:00 |
| 1  | 2          | 2025-01-02  | 2025-01-02 00:00:00 | 2025-01-03 00:00:00 |
| 1  | 3          | 2025-01-03  | 2025-01-03 00:00:00 |        NULL         |

### SCD タイプ 2 モデルへのクエリ

#### レコードの最新バージョンへのクエリ

SCD タイプ 2 モデルは履歴をサポートしていますが、レコードの最新バージョンだけをクエリすることも非常に簡単です。他のテーブルと同じようにモデルに対してクエリを実行するだけです。
例えば、`menu_items` テーブルの最新バージョンをクエリしたい場合は、次のコマンドを実行します。

```sql linenums="1"
SELECT
  *
FROM
  menu_items
WHERE
  valid_to IS NULL;
```

また、SCD タイプ 2 モデルの上にビューを作成し、新しい `is_current` 列を作成して、消費者が現在のレコードを簡単に識別できるようにすることもできます。

```sql linenums="1"
SELECT
  *,
  valid_to IS NULL AS is_current
FROM
  menu_items;
```

#### 特定の時点におけるレコードの特定のバージョンをクエリする

`menu_items` テーブルを `2020-01-02 01:00:00` 時点でクエリしたい場合は、次のコマンドを実行します。

```sql linenums="1"
SELECT
  *
FROM
  menu_items
WHERE
  id = 1
  AND '2020-01-02 01:00:00' >= valid_from
  AND '2020-01-02 01:00:00' < COALESCE(valid_to, CAST('2199-12-31 23:59:59+00:00' AS TIMESTAMP));
```

結合の例:

```sql linenums="1"
SELECT
  *
FROM
  orders
INNER JOIN
  menu_items
  ON orders.menu_item_id = menu_items.id
  AND orders.created_at >= menu_items.valid_from
  AND orders.created_at < COALESCE(menu_items.valid_to, CAST('2199-12-31 23:59:59+00:00' AS TIMESTAMP));
```

`COALESCE` を自動的に実行するビューを作成できます。これを `is_current` フラグと組み合わせることで、レコードの特定のバージョンを簡単にクエリできるようになります。

```sql linenums="1"
SELECT
  id,
  name,
  price,
  updated_at,
  valid_from,
  COALESCE(valid_to, CAST('2199-12-31 23:59:59+00:00' AS TIMESTAMP)) AS valid_to
  valid_to IS NULL AS is_current,
FROM
  menu_items;
```

さらに、`valid_to` を包括的にして、ユーザーがクエリ時に `BETWEEN` を使用できるようにするには、次の操作を実行します。

```sql linenums="1"
SELECT
  id,
  name,
  price,
  updated_at,
  valid_from,
  COALESCE(valid_to, CAST('2200-01-01 00:00:00+00:00' AS TIMESTAMP)) - INTERVAL 1 SECOND AS valid_to
  valid_to IS NULL AS is_current,
```

注: この例ではタイムスタンプの精度は秒単位なので、1秒を減算しています。減算する値は、タイムスタンプの精度と同じ値にしてください。

#### 削除されたレコードのクエリ

削除されたレコードを識別する方法の一つは、`valid_to` レコードが `NULL` ではないレコードをクエリすることです。例えば、`menu_items` テーブル内のすべての削除済み ID をクエリしたい場合は、次のコマンドを実行します。

```sql linenums="1"
SELECT
  id,
  MAX(CASE WHEN valid_to IS NULL THEN 0 ELSE 1 END) AS is_deleted
FROM
  menu_items
GROUP BY
  id
```

### SCD タイプ 2 モデルのリセット（履歴のクリア）

SCD タイプ 2 モデルは、一度失われた履歴を再作成できないため、キャプチャされたデータを保護するようにデフォルトで設計されています。
しかし、履歴をクリアして最初からやり直したい場合もあります。
このユースケースでは、まずモデル定義で `disable_restatement` を `false` に設定する必要があります。

```sql linenums="1" hl_lines="5"
MODEL (
  name db.menu_items,
  kind SCD_TYPE_2_BY_TIME (
    unique_key id,
    disable_restatement false
  )
);
```

この変更を計画し、本番環境に適用します。
その後、[モデルを再定義](../plans.md#restatement-plans)する必要があります。

```bash
sqlmesh plan --restate-model db.menu_items
```

!!! warning

    これにより、モデル上の履歴データが削除されます。このデータはほとんどの場合復元できません。

完了したら、モデル定義の「disable_restatement」を削除して「true」に設定し、偶発的なデータ損失を防ぐ必要があります。

```sql linenums="1"
MODEL (
  name db.menu_items,
  kind SCD_TYPE_2_BY_TIME (
    unique_key id,
  )
);
```

この変更を計画し、本番環境に適用します。

## EXTERNAL

EXTERNALモデル種別は、外部テーブルに関するメタデータを格納する[外部モデル](./external_models.md)を指定するために使用されます。外部モデルは特別なモデルであり、他のモデル種別のように.sqlファイルで指定されません。オプションですが、SQLMeshプロジェクトでクエリされた外部テーブルの列と型情報を伝播するのに役立ちます。

## MANAGED

!!! warning

    マネージドモデルは現在開発中であり、サポートされるエンジンが増えるにつれて API とセマンティクスが変更される可能性があります。

**注:** Python モデルは `MANAGED` モデルをサポートしていません。代わりに SQL モデルを使用してください。

`MANAGED` モデルは、基盤となるデータベースエンジンがデータのライフサイクルを管理するモデルを作成するために使用されます。

これらのモデルは、新しい間隔で更新されたり、`sqlmesh run` が呼び出されてもリフレッシュされたりしません。*データ* を最新の状態に保つ責任はエンジンにあります。

エンジンがマネージドモデルを作成する方法は、[`physical_properties`](../overview#physical_properties-previously-table_properties) を使用して、アダプターが基盤となるデータベースにコマンドを発行する際に使用するエンジン固有のパラメータを渡すことで制御できます。

標準がないため、ベンダーごとに異なる実装があり、セマンティクスと構成パラメータも異なります。そのため、`MANAGED` モデルは、他の SQLMesh モデルタイプほどデータベースエンジン間で移植性が高くありません。さらに、ブラックボックス型であるため、SQLMesh ではモデルの整合性と状態を把握する能力が限られています。

まずは標準の SQLMesh モデルタイプを使用することをお勧めします。ただし、マネージドモデルを使用する必要がある場合でも、[仮想環境](../../concepts/overview#build-a-virtual-environment) で使用できるなど、SQLMesh の他の利点を享受できます。

サポートされているエンジンと利用可能なプロパティの詳細については、[マネージドモデル](./managed_models.md) を参照してください。

## INCREMENTAL_BY_PARTITION

`INCREMENTAL_BY_PARTITION` タイプのモデルは、パーティションに基づいて増分的に計算されます。列のセットはモデルのパーティションキーを定義し、パーティションは同じパーティションキー値を持つ行のグループです。

!!! question "このモデルの種類を使用する必要がありますか?"

    どの種類のモデルでも、`MODEL` DDL で [`partitioned_by` キー](../models/overview.md#partitioned_by) を指定することにより、パーティション分割された **テーブル** を使用できます。

    `INCREMENTAL_BY_PARTITION` の「パーティション」とは、モデル実行時にデータがどのように **ロード** されるかを指します。

    `INCREMENTAL_BY_PARTITION` モデルは本質的に [非べき等](../glossary.md#idempotency) であるため、再ステートメントなどの操作によってデータが失われる可能性があります。そのため、他の種類のモデルよりも管理が複雑になります。

    ほとんどのシナリオでは、`INCREMENTAL_BY_TIME_RANGE` モデルでニーズを満たし、管理も容易になります。`INCREMENTAL_BY_PARTITION` モデルは、データをパーティションごとにロードする必要がある場合にのみ使用してください（通常はパフォーマンス上の理由から）。

このモデル種別は、パーティションキーの共通値に基づいて、データ行をグループとして読み込み、更新する必要があるシナリオ向けに設計されています。

任意の SQL エンジンで使用できます。SQLMesh は、明示的なテーブル パーティション分割をサポートするエンジン (例: [BigQuery](https://cloud.google.com/bigquery/docs/creating-partitioned-tables)、[Databricks](https://docs.databricks.com/en/sql/language-manual/sql-ref-partition.html)) 上で、パーティション テーブルを自動的に作成します。

新しい行は、パーティションキーの値に基づいて読み込まれます。

- 新しく読み込まれたデータのパーティションキーがモデルテーブルに存在しない場合、新しいパーティションキーとそのデータ行が挿入されます。
- 新しく読み込まれたデータのパーティションキーがモデルテーブルに既に存在する場合、**モデルテーブル内のパーティションキーの既存のデータ行はすべて**、新しく読み込まれたデータのパーティションキーのデータ行に置き換えられます。
- パーティションキーがモデルテーブルに存在するが、新しくロードされたデータには存在しない場合、パーティションキーの既存のデータ行は変更されず、モデルテーブルに残ります。

この種類は、以下の特性を持つデータセットにのみ使用してください。

* データセットのレコードは、パーティションキーでグループ化できます。
* 各レコードには、パーティションキーが関連付けられています。
* レコードの upsert が適切であるため、パーティションキーが一致する場合、既存のレコードを新しいレコードで上書きできます。
* 特定のパーティションキーに関連付けられているすべての既存のレコードは、新しいレコードにパーティションキーの値が含まれる場合、削除または上書きできます。

パーティションキーを定義する列は、モデルの `MODEL` DDL の `partitioned_by` キーで指定されます。次の例は、パーティションキーが `region` 列の行の値である `INCREMENTAL_BY_PARTITION` モデルの `MODEL` DDL を示しています。

```sql linenums="1" hl_lines="4"
MODEL (
  name db.events,
  kind INCREMENTAL_BY_PARTITION,
  partitioned_by region,
);
```

`region` や `department` などの複合パーティション キーもサポートされています。

```sql linenums="1" hl_lines="4"
MODEL (
  name db.events,
  kind INCREMENTAL_BY_PARTITION,
  partitioned_by (region, department),
);
```

日付列やタイムスタンプ列の式もサポートされています（SQLエンジンによって異なります）。このBigQueryの例では、パーティションキーは各行の「event_date」が発生した月に基づいています。

```sql linenums="1" hl_lines="4"
MODEL (
  name db.events,
  kind INCREMENTAL_BY_PARTITION,
  partitioned_by DATETIME_TRUNC(event_date, MONTH)
);
```

!!! warning "完全な再ステートメントのみがサポートされています"

    部分データの再ステートメント（[restatements](../plans.md#restatement-plans)）は、テーブルデータの一部（通常は特定の期間）を再処理するために使用されます。

    部分データの再ステートメントは、`INCREMENTAL_BY_PARTITION` モデルではサポートされていません。`INCREMENTAL_BY_PARTITION` モデルを再ステートメントすると、テーブル全体が最初から再作成されます。

    `INCREMENTAL_BY_PARTITION` モデルの再ステートメントはデータ損失につながる可能性があるため、慎重に実行する必要があります。

### 例

これは、このモデル種別を実際にどのように使用するかを示す、より詳細な例です。`partitions_to_update` CTE の時間範囲に基づいて、バックフィルするパーティションの数を制限します。

```sql linenums="1"
MODEL (
  name demo.incremental_by_partition_demo,
  kind INCREMENTAL_BY_PARTITION,
  partitioned_by user_segment,
);

-- This is the source of truth for what partitions need to be updated and will join to the product usage data
-- This could be an INCREMENTAL_BY_TIME_RANGE model that reads in the user_segment values last updated in the past 30 days to reduce scope
-- Use this strategy to reduce full restatements
WITH partitions_to_update AS (
  SELECT DISTINCT
    user_segment
  FROM demo.incremental_by_time_range_demo  -- upstream table tracking which user segments to update
  WHERE last_updated_at BETWEEN DATE_SUB(@start_dt, INTERVAL 30 DAY) AND @end_dt
),

product_usage AS (
  SELECT
    product_id,
    customer_id,
    last_usage_date,
    usage_count,
    feature_utilization_score,
    user_segment
  FROM sqlmesh-public-demo.tcloud_raw_data.product_usage
  WHERE user_segment IN (SELECT user_segment FROM partitions_to_update) -- partition filter applied here
)

SELECT
  product_id,
  customer_id,
  last_usage_date,
  usage_count,
  feature_utilization_score,
  user_segment,
  CASE
    WHEN usage_count > 100 AND feature_utilization_score > 0.7 THEN 'Power User'
    WHEN usage_count > 50 THEN 'Regular User'
    WHEN usage_count IS NULL THEN 'New User'
    ELSE 'Light User'
  END as user_type
FROM product_usage
```

**注**: このモデルの種類では部分データ [restatement](../plans.md#restatement-plans) はサポートされていません。つまり、再ステートメントを実行するとテーブル全体が最初から再作成されます。これにより、データが失われる可能性があります。

### マテリアライズ戦略
ターゲットエンジンに応じて、`INCREMENTAL_BY_PARTITION` タイプのモデルは、以下の戦略を使用してマテリアライズされます。

| Engine     | Strategy                                |
|------------|-----------------------------------------|
| Databricks | REPLACE WHERE by partitioning key       |
| Spark      | INSERT OVERWRITE by partitioning key    |
| Snowflake  | DELETE by partitioning key, then INSERT |
| BigQuery   | DELETE by partitioning key, then INSERT |
| Redshift   | DELETE by partitioning key, then INSERT |
| Postgres   | DELETE by partitioning key, then INSERT |
| DuckDB     | DELETE by partitioning key, then INSERT |

## INCREMENTAL_UNMANAGED

`INCREMENTAL_UNMANAGED` モデルは、追加専用テーブルをサポートするために存在します。これは、SQLMesh がデータのロード方法を管理しないという意味で「非管理」です。SQLMesh は設定された頻度でクエリを実行し、取得したデータをテーブルに追加します。

!!! question "このモデルの種類を使用する必要がありますか?"

    Data Vault などのデータ管理パターンでは、追加専用のテーブルが使用される場合があります。このような状況では、`INCREMENTAL_UNMANAGED` 型が適切な型です。

    その他のほとんどの状況では、データの読み込み方法をより細かく制御できるため、`INCREMENTAL_BY_TIME_RANGE` または `INCREMENTAL_BY_UNIQUE_KEY` 型が適していると考えられます。

`INCREMENTAL_UNMANAGED` モデルの使用方法は簡単です。

```sql linenums="1" hl_lines="3"
MODEL (
  name db.events,
  kind INCREMENTAL_UNMANAGED,
);
```

これは管理されていないため、他の増分モデル タイプのようにデータの読み込み方法を制御する `batch_size` プロパティと `batch_concurrency` プロパティはサポートされていません。

!!! warning "完全な再ステートメントのみがサポートされています"

    `INCREMENTAL_BY_PARTITION` と同様に、`INCREMENTAL_UNMANAGED` モデルを [再ステートメント](../plans.md#restatement-plans) しようとすると、完全な再ステートメントがトリガーされます。つまり、指定したタイムスライスからではなく、モデルは最初から再構築されます。

    これは、追加専用テーブルが本質的に非べき等性であるためです。`INCREMENTAL_UNMANAGED` モデルの再ステートメントはデータ損失につながる可能性があるため、慎重に実行する必要があります。
