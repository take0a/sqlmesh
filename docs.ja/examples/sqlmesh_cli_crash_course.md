# SQLMesh CLI Crash Course

<div style="position: relative; padding-bottom: 56.25%; height: 0;"><iframe src="https://www.loom.com/embed/03582d14ac7c4b27a254705ac25c380a?sid=75acdb2f-4fa1-4762-8cf8-c52a81712eac" frameborder="0" webkitallowfullscreen mozallowfullscreen allowfullscreen style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></iframe></div>

このドキュメントは、変換データパイプラインの構築と保守に使用するSQLMeshワークフローの**大部分**を詳しく理解できるように設計されています。目標は、30分以内にSQLMeshを体感できるようにすることです。

このドキュメントは、コミュニティの観察、対面での会話、ライブスクリーン共有、デバッグセッションから着想を得ています。網羅的なリストではありませんが、実際の経験に基づいています。

[オープンソースのGitHubリポジトリ](https://github.com/sungchun12/sqlmesh-cli-crash-course)で、手順を追って学ぶことができます。

SQLMesh が仮想データ環境を使用する方法を初めて知る場合は、[この簡単な説明をご覧ください](https://www.loom.com/share/216835d64b3a4d56b2e061fa4bd9ee76?sid=88b3289f-e19b-4ccc-8b88-3faf9d7c9ce3)。

!!! tip

    このページを 2 番目のモニターまたは横並びのウィンドウに表示して、ターミナルにすばやくコピー/貼り付けできます。

## 開発ワークフロー

モデルへの変更を適用するには、これらのコマンドを80%ほど使用します。ワークフローは以下のとおりです。

1. SQLファイルとPythonファイル（以下の例で既に作成済み）でモデルに直接変更を加える
2. 開発環境で変更を計画する
3. 開発環境に変更を適用する
4. 変更を監査する（データ品質をテストする）
5. 本番環境とのデータ比較を実行する
6. 本番環境に変更を適用する

### `dev` での変更のプレビュー、適用、監査

`sqlmesh plan dev` というシンプルなコマンド 1 つで、迅速かつ確実に変更を加えることができます。

- 開発環境で変更を計画します。
- プロンプトで `y` と入力して、開発環境に変更を適用します。
- 変更を監査します（データ品質をテストします）。これは、開発環境に変更を適用すると自動的に実行されます。

注: 変更を加えずにこのコマンドを実行すると、SQLMesh から変更を行うように求められます。または、`sqlmesh plan dev --include-unmodified` のように `--include-unmodified` フラグを使用します。不要な仮想レイヤービューによって開発環境に多くのノイズが発生しないように、このコマンドを実行する前に変更を加えることをお勧めします。

=== "SQLMesh"

    ```bash
    sqlmesh plan dev
    ```

    ```bash
    sqlmesh plan <environment>
    ```

    より速く実行したい場合は、`--auto-apply` フラグを追加して手動プロンプトをスキップし、計画を適用できます。計画の出力に慣れており、計画を適用する前に diff 出力で小さな変更を確認する必要がない場合は、このフラグを追加してください。

    ```bash
    sqlmesh plan <environment> --auto-apply
    ```

=== "Tobiko Cloud"

    ```bash
    tcloud sqlmesh plan dev
    ```

    ```bash
    tcloud sqlmesh plan <environment>
    ```

    より速く実行したい場合は、`--auto-apply` フラグを追加して手動プロンプトをスキップし、計画を適用できます。計画の出力に慣れており、計画を適用する前に diff 出力で小さな変更を確認する必要がない場合は、このフラグを追加してください。

    ```bash
    tcloud sqlmesh plan <environment> --auto-apply
    ```

??? "Example Output"
    `incremental_model` と `full_model` に重大な変更を加えました。

    SQLMesh:

      - 変更の影響を受けるモデルを表示しました。
      - モデルに加えられる変更を表示しました。
      - バックフィルが必要なモデルを表示しました。
      - `dev` に変更を適用するように促しました。
      - 警告として発生する監査エラーを表示しました。
      - SQL を検証するために物理レイヤーを更新しました。
      - データを物理レイヤーに挿入してモデルバッチを実行しました。
      - 変更を反映するために仮想レイヤーのビューポインターを更新しました。

    ```bash
    > sqlmesh plan dev
    Differences from the `dev` environment:

    Models:
    ├── Directly Modified:
    │   ├── sqlmesh_example__dev.incremental_model
    │   └── sqlmesh_example__dev.full_model
    └── Indirectly Modified:
        └── sqlmesh_example__dev.view_model

    ---

    +++

    @@ -9,7 +9,8 @@

     SELECT
       item_id,
       COUNT(DISTINCT id) AS num_orders,
    -  6 AS new_column
    +  new_column
     FROM sqlmesh_example.incremental_model
     GROUP BY
    -  item_id
    +  item_id,
    +  new_column

    Directly Modified: sqlmesh_example__dev.full_model (Breaking)

    ---

    +++

    @@ -15,7 +15,7 @@

       id,
       item_id,
       event_date,
    -  5 AS new_column
    +  7 AS new_column
     FROM sqlmesh_example.seed_model
     WHERE
       event_date BETWEEN @start_date AND @end_date

    Directly Modified: sqlmesh_example__dev.incremental_model (Breaking)
    └── Indirectly Modified Children:
        └── sqlmesh_example__dev.view_model (Indirect Breaking)
    Models needing backfill:
    ├── sqlmesh_example__dev.full_model: [full refresh]
    ├── sqlmesh_example__dev.incremental_model: [2020-01-01 - 2025-04-16]
    └── sqlmesh_example__dev.view_model: [recreate view]
    Apply - Backfill Tables [y/n]: y

    Updating physical layer ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100.0% • 2/2 • 0:00:00

    ✔ Physical layer updated

    [1/1]  sqlmesh_example__dev.incremental_model               [insert 2020-01-01 - 2025-04-16]                 0.03s
    Executing model batches ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 0.0% • pending • 0:00:00
    sqlmesh_example__dev.incremental_model .
    [WARNING] sqlmesh_example__dev.full_model: 'assert_positive_order_ids' audit error: 2 rows failed. Learn more in logs:
    /Users/sung/Desktop/git_repos/sqlmesh-cli-revamp/logs/sqlmesh_2025_04_18_10_33_43.log
    [1/1]  sqlmesh_example__dev.full_model                      [full refresh, audits ❌1]                       0.01s
    Executing model batches ━━━━━━━━━━━━━╺━━━━━━━━━━━━━━━━━━━━━━━━━━ 33.3% • 1/3 • 0:00:00
    sqlmesh_example__dev.full_model .
    [WARNING] sqlmesh_example__dev.view_model: 'assert_positive_order_ids' audit error: 2 rows failed. Learn more in logs:
    /Users/sung/Desktop/git_repos/sqlmesh-cli-revamp/logs/sqlmesh_2025_04_18_10_33_43.log
    [1/1]  sqlmesh_example__dev.view_model                      [recreate view, audits ✔2 ❌1]                   0.01s
    Executing model batches ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100.0% • 3/3 • 0:00:00

    ✔ Model batches executed

    Updating virtual layer  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100.0% • 3/3 • 0:00:00

    ✔ Virtual layer updated
    ```

### 本番環境とのデータ比較

<div style="position: relative; padding-bottom: 56.25%; height: 0;"><iframe src="https://www.loom.com/embed/a3c8beffe46840f38487180f401f0a1c?sid=941a7283-38c8-4527-b5b9-49e68c5b9f0c" frameborder="0" webkitallowfullscreen mozallowfullscreen allowfullscreen style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></iframe></div>

prod に対してデータ比較を実行します。これは、変更を `dev` に適用した後、期待どおりに動作しているかどうかを確認するのに適した方法です。

この作業をより簡単かつ迅速に行うには、以下の例のように `-m '*'` フラグを使用して、適用したプランの変更の影響を受ける環境内のすべてのモデルに対してデータ比較を実行できます。モデル名を指定する必要はありません。オプションの詳細については、[こちら](../guides/tablediff.md) をご覧ください。

=== "SQLMesh"

    ```bash
    sqlmesh table_diff prod:dev sqlmesh_example.full_model --show-sample
    ```

    ```bash
    sqlmesh table_diff <environment>:<environment> <model_name> --show-sample
    ```

    ```bash
    sqlmesh table_diff prod:dev -m '*' --show-sample
    ```

=== "Tobiko Cloud"

    ```bash
    tcloud sqlmesh table_diff prod:dev sqlmesh_example.full_model --show-sample
    ```

    ```bash
    tcloud sqlmesh table_diff <environment>:<environment> <model_name> --show-sample
    ```

    ```bash
    tcloud sqlmesh table_diff prod:dev -m '*' --show-sample
    ```

??? "Example Output"
    `sqlmesh_example.full_model` の `prod` 環境と `dev` 環境を比較します。

    - 検証済みの環境とモデル、および設定された結合粒度に関する差異を表示します。
    - 環境間のスキーマの差異を表示します。
    - 環境間の行数の差異を表示します。
    - 環境間の共通行統計を表示します。
    - 環境間のサンプルデータの違いを表示します。
    - ここで、変更が期待どおりに動作していることを確認するために、人間の判断が役立ちます。

    モデル定義：

    ```sql linenums="1" hl_lines="6"
    -- models/full_model.sql
    MODEL (
      name sqlmesh_example.full_model,
      kind FULL,
      cron '@daily',
      grain item_id, -- grain is optional BUT necessary for table diffs to work correctly. It's your primary key that is unique and not null.
      audits (assert_positive_order_ids),
    );

    SELECT
      item_id,
      COUNT(DISTINCT id) AS num_orders,
      new_column
    FROM
        sqlmesh_example.incremental_model
    GROUP BY item_id, new_column
    ```

    Table diff:
    ```bash
    > sqlmesh table_diff prod:dev sqlmesh_example.full_model --show-sample
    Table Diff
    ├── Model:
    │   └── sqlmesh_example.full_model
    ├── Environment:
    │   ├── Source: prod
    │   └── Target: dev
    ├── Tables:
    │   ├── Source: db.sqlmesh_example.full_model
    │   └── Target: db.sqlmesh_example__dev.full_model
    └── Join On:
        └── item_id

    Schema Diff Between 'PROD' and 'DEV' environments for model 'sqlmesh_example.full_model':
    └── Schemas match


    Row Counts:
    └──  PARTIAL MATCH: 5 rows (100.0%)

    COMMON ROWS column comparison stats:
                pct_match
    num_orders      100.0
    new_column        0.0


    COMMON ROWS sample data differences:
    Column: new_column
    ┏━━━━━━━━━┳━━━━━━┳━━━━━┓
    ┃ item_id ┃ PROD ┃ DEV ┃
    ┡━━━━━━━━━╇━━━━━━╇━━━━━┩
    │ -11     │ 5    │ 7   │
    │ -3      │ 5    │ 7   │
    │ 1       │ 5    │ 7   │
    │ 3       │ 5    │ 7   │
    │ 9       │ 5    │ 7   │
    └─────────┴──────┴─────┘
    ```

### 本番環境への変更の適用

変更内容に問題がなければ、`prod` に適用します。

!!! warning "変更を本番環境に適用する"
    ベストプラクティスとして、変更は [**CI/CD を使用**](../integrations/github.md) `prod` にのみ適用することをお勧めします。
    学習目的やホットフィックスの場合は、プロンプトで `y` と入力して、変更を手動で prod に適用できます。

=== "SQLMesh"

    ```bash
    sqlmesh plan
    ```

=== "Tobiko Cloud"

    ```bash
    tcloud sqlmesh plan
    ```

??? "Example Output"
    変更内容に確信が持てるようになったら、`prod` に適用します。

    SQLMesh:

    - 変更の影響を受けるモデルが表示されました。
    - モデルに加えられる変更が表示されました。
    - バックフィルが必要なモデルが表示されました。この場合は、`dev` で既にバックフィルされているため、バックフィルは必要ありません。
    - 変更を `prod` に適用するようにプロンプ​​トが表示されました。
    - 変更はすでに `dev` に適用されているため、物理レイヤーと実行ステップがスキップされることが表示されました。
    - 変更を反映するように、仮想レイヤーのビューポインターが更新されました。

    ```bash
    > sqlmesh plan
    Differences from the `prod` environment:

    Models:
    ├── Directly Modified:
    │   ├── sqlmesh_example.full_model
    │   └── sqlmesh_example.incremental_model
    └── Indirectly Modified:
        └── sqlmesh_example.view_model

    ---

    +++

    @@ -9,7 +9,8 @@

    SELECT
      item_id,
      COUNT(DISTINCT id) AS num_orders,
    -  5 AS new_column
    +  new_column
    FROM sqlmesh_example.incremental_model
    GROUP BY
    -  item_id
    +  item_id,
    +  new_column

    Directly Modified: sqlmesh_example.full_model (Breaking)

    ---

    +++

    @@ -15,7 +15,7 @@

      id,
      item_id,
      event_date,
    -  5 AS new_column
    +  7 AS new_column
    FROM sqlmesh_example.seed_model
    WHERE
      event_date BETWEEN @start_date AND @end_date

    Directly Modified: sqlmesh_example.incremental_model (Breaking)
    └── Indirectly Modified Children:
        └── sqlmesh_example.view_model (Indirect Breaking)
    Apply - Virtual Update [y/n]: y

    SKIP: No physical layer updates to perform

    SKIP: No model batches to execute

    Updating virtual layer  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100.0% • 3/3 • 0:00:00

    ✔ Virtual layer updated
    ```

---

## 強化されたテストワークフロー

これらのコマンドを使用して、変更が期待どおりに動作しているかどうかを検証します。監査（データテスト）は優れた最初のステップであり、そこから段階的に進めていくことで、パイプラインに自信を持つことができます。ワークフローは以下のとおりです。

1. SQLMesh の管理外にある外部モデル（例：Fivetran、Airbyte などによって読み込まれたデータ）を作成し、監査する。
2. モデルのユニットテストを自動生成する。
3. CLI で直接データに対してアドホッククエリを実行する。
4. 既知の構文エラーを検出するためにモデルに lint を実行する。

---

### 外部モデルの作成と監査

モデルは、SQLMesh の管理外にあるテーブルやビューに対して `SELECT` を実行する場合があります。SQLMesh は、モデル定義（例: `bigquery-public-data`.`ga4_obfuscated_sample_ecommerce`.`events_20210131`）からそれらの完全修飾名を自動的に解析し、完全なスキーマと列のデータ型を特定します。

これらの「外部モデル」スキーマは、列レベルのリネージに使用されます。また、データ品質をテストするための監査を追加することもできます。監査に失敗した場合、SQLMesh は下流のモデルが無駄に実行されるのを防ぎます。

=== "SQLMesh"

    ```bash
    sqlmesh create_external_models
    ```

=== "Tobiko Cloud"

    ```bash
    tcloud sqlmesh create_external_models
    ```

??? "Example Output"
    注: これは別の Tobiko Cloud プロジェクトの例であるため、GitHub リポジトリでは手順を追うことはできません。

    - モデルの SQL で解析された `bigquery-public-data`.`ga4_obfuscated_sample_ecommerce`.`events_20210131` テーブルから外部モデルを生成しました。
    - 外部モデルに監査を追加し、`event_date` が NULL でないことを確認しました。
    - 外部モデルに加えられる変更のプランプレビューを確認しました。

    ```sql linenums="1" hl_lines="29"  title="models/external_model_example.sql"
    MODEL (
      name tcloud_demo.external_model
    );

    SELECT
      event_date,
      event_timestamp,
      event_name,
      event_params,
      event_previous_timestamp,
      event_value_in_usd,
      event_bundle_sequence_id,
      event_server_timestamp_offset,
      user_id,
      user_pseudo_id,
      privacy_info,
      user_properties,
      user_first_touch_timestamp,
      user_ltv,
      device,
      geo,
      app_info,
      traffic_source,
      stream_id,
      platform,
      event_dimensions,
      ecommerce
    /*   items */
    FROM bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_20210131 -- I fully qualified the external table name and sqlmesh will automatically create the external model
    ```

    `sqlmesh create_external_models` output file:

    ```yaml linenums="1" hl_lines="2 3 4" title="external_models.yaml"
    - name: '`bigquery-public-data`.`ga4_obfuscated_sample_ecommerce`.`events_20210131`'
      audits: # I added this audit manually to the external model YAML file
        - name: not_null
          columns: "[event_date]"
      columns:
        event_date: STRING
        event_timestamp: INT64
        event_name: STRING
        event_params: ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value
          INT64, float_value FLOAT64, double_value FLOAT64>>>
        event_previous_timestamp: INT64
        event_value_in_usd: FLOAT64
        event_bundle_sequence_id: INT64
        event_server_timestamp_offset: INT64
        user_id: STRING
        user_pseudo_id: STRING
        privacy_info: STRUCT<analytics_storage INT64, ads_storage INT64, uses_transient_token
          STRING>
        user_properties: ARRAY<STRUCT<key INT64, value STRUCT<string_value INT64, int_value
          INT64, float_value INT64, double_value INT64, set_timestamp_micros INT64>>>
        user_first_touch_timestamp: INT64
        user_ltv: STRUCT<revenue FLOAT64, currency STRING>
        device: STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING,
          mobile_marketing_name STRING, mobile_os_hardware_model INT64, operating_system
          STRING, operating_system_version STRING, vendor_id INT64, advertising_id INT64,
          language STRING, is_limited_ad_tracking STRING, time_zone_offset_seconds INT64,
          web_info STRUCT<browser STRING, browser_version STRING>>
        geo: STRUCT<continent STRING, sub_continent STRING, country STRING, region STRING,
          city STRING, metro STRING>
        app_info: STRUCT<id STRING, version STRING, install_store STRING, firebase_app_id
          STRING, install_source STRING>
        traffic_source: STRUCT<medium STRING, name STRING, source STRING>
        stream_id: INT64
        platform: STRING
        event_dimensions: STRUCT<hostname STRING>
        ecommerce: STRUCT<total_item_quantity INT64, purchase_revenue_in_usd FLOAT64,
          purchase_revenue FLOAT64, refund_value_in_usd FLOAT64, refund_value FLOAT64,
          shipping_value_in_usd FLOAT64, shipping_value FLOAT64, tax_value_in_usd FLOAT64,
          tax_value FLOAT64, unique_items INT64, transaction_id STRING>
        items: ARRAY<STRUCT<item_id STRING, item_name STRING, item_brand STRING, item_variant
          STRING, item_category STRING, item_category2 STRING, item_category3 STRING,
          item_category4 STRING, item_category5 STRING, price_in_usd FLOAT64, price FLOAT64,
          quantity INT64, item_revenue_in_usd FLOAT64, item_revenue FLOAT64, item_refund_in_usd
          FLOAT64, item_refund FLOAT64, coupon STRING, affiliation STRING, location_id
          STRING, item_list_id STRING, item_list_name STRING, item_list_index STRING,
          promotion_id STRING, promotion_name STRING, creative_name STRING, creative_slot
          STRING>>
      gateway: public-demo
    ```

    ```bash
    > sqlmesh plan dev_sung
    Differences from the `dev_sung` environment:

    Models:
    └── Metadata Updated:
        └── "bigquery-public-data".ga4_obfuscated_sample_ecommerce__dev_sung.events_20210131

    ---

    +++

    @@ -29,5 +29,6 @@

        ecommerce STRUCT<total_item_quantity INT64, purchase_revenue_in_usd FLOAT64, purchase_revenue FLOAT64, refund_value_in_usd FLOAT64, refund_value FLOAT64, shipping_value_in_usd FLOAT64, shipping_value FLOAT64,
    tax_value_in_usd FLOAT64, tax_value FLOAT64, unique_items INT64, transaction_id STRING>,
        items ARRAY<STRUCT<item_id STRING, item_name STRING, item_brand STRING, item_variant STRING, item_category STRING, item_category2 STRING, item_category3 STRING, item_category4 STRING, item_category5 STRING,
    price_in_usd FLOAT64, price FLOAT64, quantity INT64, item_revenue_in_usd FLOAT64, item_revenue FLOAT64, item_refund_in_usd FLOAT64, item_refund FLOAT64, coupon STRING, affiliation STRING, location_id STRING,
    item_list_id STRING, item_list_name STRING, item_list_index STRING, promotion_id STRING, promotion_name STRING, creative_name STRING, creative_slot STRING>>
      ),
    +  audits (not_null('columns' = [event_date])),
      gateway `public-demo`
    )

    Metadata Updated: "bigquery-public-data".ga4_obfuscated_sample_ecommerce__dev_sung.events_20210131
    Models needing backfill:
    └── "bigquery-public-data".ga4_obfuscated_sample_ecommerce__dev_sung.events_20210131: [full refresh]
    Apply - Backfill Tables [y/n]:
    ```

### ユニットテストを自動生成

静的なサンプルデータに対してモデルを実行することで、ビジネスロジックが期待どおりに動作していることを確認できます。

ユニットテストは、プランが自動的に適用される*前*に実行されます。これは、データのバックフィル*前*に複雑なビジネスロジック（例：`CASE WHEN` 条件）をテストするのに最適です。手動でテストを記述する必要もありません。

=== "SQLMesh"

    アップストリーム `sqlmesh_example.incremental_model` からの 5 行に基づいて単体テストを作成します。

    ```bash
    sqlmesh create_test sqlmesh_example.full_model \
      --query sqlmesh_example.incremental_model \
      "select * from sqlmesh_example.incremental_model limit 5"
    ```

    ```bash
    sqlmesh create_test <model_name> \
      --query <model_name upstream> \
      "select * from <model_name upstream> limit 5"
    ```


=== "Tobiko Cloud"

    ```bash
    tcloud sqlmesh create_test demo.stg_payments \
      --query demo.seed_raw_payments \
      "select * from demo.seed_raw_payments limit 5"
    ```

    ```bash
    tcloud sqlmesh create_test <model_name> \
      --query <model_name upstream> \
      "select * from <model_name upstream> limit 5"
    ```

??? "Example Output"

    SQLMesh:

    - データに対してライブクエリを実行し、`sqlmesh_example.full_model` モデルのユニットテストを生成しました。
    - テストを実行し、DuckDB でローカルにパスしました。
    - クラウドデータウェアハウスを使用している場合は、SQL 構文を DuckDB 内の同等の構文にトランスパイルします。
    - ローカルマシン上で高速かつ無料で実行できます。

    生成されたテスト定義ファイル:

    ```yaml linenums="1" title="tests/test_full_model.yaml"
    test_full_model:
      model: '"db"."sqlmesh_example"."full_model"'
      inputs:
        '"db"."sqlmesh_example"."incremental_model"':
        - id: -11
          item_id: -11
          event_date: 2020-01-01
          new_column: 7
        - id: 1
          item_id: 1
          event_date: 2020-01-01
          new_column: 7
        - id: 3
          item_id: 3
          event_date: 2020-01-03
          new_column: 7
        - id: 4
          item_id: 1
          event_date: 2020-01-04
          new_column: 7
        - id: 5
          item_id: 1
          event_date: 2020-01-05
          new_column: 7
      outputs:
        query:
        - item_id: 3
          num_orders: 1
          new_column: 7
        - item_id: 1
          num_orders: 3
          new_column: 7
        - item_id: -11
          num_orders: 1
          new_column: 7
    ```

    `sqlmesh test` を使用して手動でテストを実行します。

    ```bash
    (demo) ➜  demo git:(main) ✗ sqlmesh test
    .
    ----------------------------------------------------------------------
    Ran 1 test in 0.053s

    OK
    ```

    ```bash
    # what do we see if the test fails?
    (demo) ➜  demo git:(main) ✗ sqlmesh test
    F
    ======================================================================
    FAIL: test_full_model (/Users/sung/Desktop/git_repos/sqlmesh-cli-revamp/tests/test_full_model.yaml)
    None
    ----------------------------------------------------------------------
    AssertionError: Data mismatch (exp: expected, act: actual)

      new_column
            exp  act
    0        0.0  7.0

    ----------------------------------------------------------------------
    Ran 1 test in 0.020s

    FAILED (failures=1)
    ```

### アドホッククエリの実行

CLI から直接ライブクエリを実行できます。これは、クエリコンソールにコンテキストを切り替えることなく、変更の外観と操作性を検証するのに最適です。

ヒント: 変更の全体像を把握するには、`sqlmesh table_diff` の後にこれを実行します。

=== "SQLMesh"

    ```bash
    sqlmesh fetchdf "select * from sqlmesh_example__dev.full_model limit 5"
    ```

    ```bash
    # construct arbitrary query
    sqlmesh fetchdf "select * from <schema__environment>.<model_name> limit 5" # double underscore in schema name is important. Not needed for prod.
    ```

=== "Tobiko Cloud"

    ```bash
    tcloud sqlmesh fetchdf "select * from sqlmesh_example__dev.full_model limit 5"
    ```

    ```bash
    # construct arbitrary query
    tcloud sqlmesh fetchdf "select * from <schema__environment>.<model_name> limit 5" # double underscore in schema name is important. Not needed for prod.
    ```

??? "Example Output"
    ```bash
    item_id  num_orders  new_column
    0        9           1           7
    1      -11           1           7
    2        3           1           7
    3       -3           1           7
    4        1           4           7
    ```

### リンティング

有効にすると、開発中にリンティングが自動的に実行されます。リンティングルールはモデルごとにオーバーライドすることもできます。

これは、データウェアハウスで実行時間を無駄にする前にSQLの問題を検出するのに最適な方法です。自動的に実行されますが、手動で実行して問題を事前にチェックすることもできます。

=== "SQLMesh"

    ```bash
    sqlmesh lint
    ```

=== "Tobiko Cloud"

    ```bash
    tcloud sqlmesh lint
    ```

??? "Example Output"

    `config.yaml` ファイルに linting ルールを追加します。

    ```yaml linenums="1" hl_lines="13-17" title="config.yaml"
    gateways:
      duckdb:
        connection:
          type: duckdb
          database: db.db

    default_gateway: duckdb

    model_defaults:
      dialect: duckdb
      start: 2025-03-26

    linter:
      enabled: true
      rules: ["ambiguousorinvalidcolumn", "invalidselectstarexpansion"] # raise errors for these rules
      warn_rules: ["noselectstar", "nomissingaudits"]
      # ignored_rules: ["noselectstar"]
    ```

    ```bash
    > sqlmesh lint
    [WARNING] Linter warnings for /Users/sung/Desktop/git_repos/sqlmesh-cli-revamp/models/lint_warn.sql:
    - noselectstar: Query should not contain SELECT * on its outer most projections, even if it can be
    expanded.
    - nomissingaudits: Model `audits` must be configured to test data quality.
    [WARNING] Linter warnings for
    /Users/sung/Desktop/git_repos/sqlmesh-cli-revamp/models/incremental_by_partition.sql:
    - nomissingaudits: Model `audits` must be configured to test data quality.
    [WARNING] Linter warnings for /Users/sung/Desktop/git_repos/sqlmesh-cli-revamp/models/seed_model.sql:
    - nomissingaudits: Model `audits` must be configured to test data quality.
    [WARNING] Linter warnings for
    /Users/sung/Desktop/git_repos/sqlmesh-cli-revamp/models/incremental_by_unique_key.sql:
    - nomissingaudits: Model `audits` must be configured to test data quality.
    [WARNING] Linter warnings for
    /Users/sung/Desktop/git_repos/sqlmesh-cli-revamp/models/incremental_model.sql:
    - nomissingaudits: Model `audits` must be configured to test data quality.
    ```

## デバッグワークフロー

必要に応じてこれらのコマンドを使用し、変更が期待どおりに動作していることを確認します。これは、上記のデフォルト設定よりも詳細な情報を取得するのに便利です。ワークフローは以下のとおりです。

1. モデルをレンダリングし、SQL が期待どおりであることを確認します。
2. SQLMesh を詳細モードで実行し、動作を確認します。
3. ターミナルでログを簡単に表示します。

### SQL の変更をレンダリングする

これは、変更を適用する前に、モデルの SQL が期待どおりに動作していることを確認するのに最適な方法です。特に、クエリエンジンを別のエンジンに移行する場合（例：PostgreSQL から Databricks へ）は重要です。

=== "SQLMesh"

    ```bash
    sqlmesh render sqlmesh_example.incremental_model
    ```

    ```bash
    sqlmesh render sqlmesh_example.incremental_model --dialect databricks
    ```

    ```bash
    sqlmesh render <model_name> --dialect <dialect>
    ```

=== "Tobiko Cloud"

    ```bash
    tcloud sqlmesh render sqlmesh_example.incremental_model
    ```

    ```bash
    tcloud sqlmesh render sqlmesh_example.incremental_model --dialect databricks
    ```

    ```bash
    tcloud sqlmesh render <model_name> --dialect <dialect>
    ```

??? "Example Output"

    モデル定義:

    ```sql linenums="1" title="models/incremental_model.sql"
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
      7 as new_column
    FROM
      sqlmesh_example.seed_model
    WHERE
      event_date BETWEEN @start_date AND @end_date
    ```

    SQLMesh は、デフォルトまたはターゲット方言で完全な SQL コードを返します。

    ```sql hl_lines="11"
    > sqlmesh render sqlmesh_example.incremental_model
    -- rendered sql in default dialect
    SELECT
      "seed_model"."id" AS "id",
      "seed_model"."item_id" AS "item_id",
      "seed_model"."event_date" AS "event_date",
      7 AS "new_column"
    FROM "db"."sqlmesh__sqlmesh_example"."sqlmesh_example__seed_model__3294646944" AS "seed_model" /*
    db.sqlmesh_example.seed_model */
    WHERE
      "seed_model"."event_date" <= CAST('1970-01-01' AS DATE) -- placeholder dates for date macros
      AND "seed_model"."event_date" >= CAST('1970-01-01' AS DATE)
    ```

    ```sql
    > sqlmesh render sqlmesh_example.incremental_model --dialect databricks
    -- rendered sql in databricks dialect
    SELECT
      `seed_model`.`id` AS `id`,
      `seed_model`.`item_id` AS `item_id`,
      `seed_model`.`event_date` AS `event_date`,
      7 AS `new_column`
    FROM `db`.`sqlmesh__sqlmesh_example`.`sqlmesh_example__seed_model__3294646944` AS `seed_model` /*
    db.sqlmesh_example.seed_model */
    WHERE
      `seed_model`.`event_date` <= CAST('1970-01-01' AS DATE)
      AND `seed_model`.`event_date` >= CAST('1970-01-01' AS DATE)
    ```

### 詳細モードでプラン変更を適用する

詳細モードでは、物理レイヤーと仮想レイヤーにおける詳細な操作を確認できます。これは、SQLMesh が各ステップで何を実行しているかを正確に把握するのに役立ちます。その後、完全修飾テーブル/ビュー名をクエリコンソールにコピー/貼り付けして、データを検証できます（必要に応じて）。

=== "SQLMesh"

    ```bash
    sqlmesh plan dev -vv
    ```

    ```bash
    sqlmesh plan <environment> -vv
    ```

=== "Tobiko Cloud"

    ```bash
    tcloud sqlmesh plan dev -vv
    ```

    ```bash
    tcloud sqlmesh plan <environment> -vv
    ```

??? "Example Output"

    ```bash hl_lines="48-50"
    > sqlmesh plan dev -vv
    [WARNING] Linter warnings for
    /Users/sung/Desktop/git_repos/sqlmesh-cli-revamp/models/incremental_by_partition.sql:
    - nomissingaudits: Model `audits` must be configured to test data quality.
    [WARNING] Linter warnings for /Users/sung/Desktop/git_repos/sqlmesh-cli-revamp/models/seed_model.sql:
    - nomissingaudits: Model `audits` must be configured to test data quality.
    [WARNING] Linter warnings for
    /Users/sung/Desktop/git_repos/sqlmesh-cli-revamp/models/incremental_by_unique_key.sql:
    - nomissingaudits: Model `audits` must be configured to test data quality.
    [WARNING] Linter warnings for
    /Users/sung/Desktop/git_repos/sqlmesh-cli-revamp/models/incremental_model.sql:
    - nomissingaudits: Model `audits` must be configured to test data quality.

    Differences from the `dev` environment:

    Models:
    ├── Directly Modified:
    │   └── db.sqlmesh_example__dev.incremental_model
    └── Indirectly Modified:
        ├── db.sqlmesh_example__dev.full_model
        └── db.sqlmesh_example__dev.view_model

    ---

    +++

    @@ -15,7 +15,7 @@

      id,
      item_id,
      event_date,
    -  9 AS new_column
    +  7 AS new_column
    FROM sqlmesh_example.seed_model
    WHERE
      event_date BETWEEN @start_date AND @end_date

    Directly Modified: db.sqlmesh_example__dev.incremental_model (Breaking)
    └── Indirectly Modified Children:
        ├── db.sqlmesh_example__dev.full_model (Breaking)
        └── db.sqlmesh_example__dev.view_model (Indirect Breaking)
    Apply - Virtual Update [y/n]: y

    SKIP: No physical layer updates to perform

    SKIP: No model batches to execute

    db.sqlmesh_example__dev.incremental_model  updated # you'll notice that it's updated vs. promoted because we changed the existing view definition
    db.sqlmesh_example__dev.full_model         updated
    db.sqlmesh_example__dev.view_model         updated
    Updating virtual layer  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100.0% • 3/3 • 0:00:00

    ✔ Virtual layer updated
    ```

### ログを簡単に表示

SQLMesh コマンドを実行するたびに、`logs` ディレクトリにログファイルが作成されます。最新のタイムスタンプを持つ正しいファイル名を手動で指定するか、以下の簡単なシェルコマンドを使用することで、ログファイルを表示できます。

これは、変更を適用するために実行されたクエリを正確に確認するのに役立ちます。これはネイティブ機能の範囲外ですが、ログを素早く簡単に表示する方法となります。

```bash
# install this open source tool that enhances the default `cat` command
# https://github.com/sharkdp/bat
brew install bat # installation command if using homebrew
```

```bash
bat --theme='ansi' $(ls -t logs/ | head -n 1 | sed 's/^/logs\//')
```

- 簡単に言うと、このコマンドは次のように動作します。「`logs/` ディレクトリ内の最新のログファイルの内容を、適切なフォーマットと構文の強調表示で表示します。」
- ターミナルで大きなファイルを表示するには、`q` を押します。

??? "Example Output"

    これは `sqlmesh plan dev` コマンドのログファイルです。ログファイルを直接確認したい場合は、出力内のファイルパスをクリックしてコードエディタで開くことができます。

    ```bash
    ──────┬──────────────────────────────────────────────────────────────────────────────────────────────
          │ File: logs/sqlmesh_2025_04_18_12_34_35.log
    ──────┼──────────────────────────────────────────────────────────────────────────────────────────────
      1   │ 2025-04-18 12:34:35,715 - MainThread - sqlmesh.core.config.connection - INFO - Creating new D
          │ uckDB adapter for data files: {'db.db'} (connection.py:319)
      2   │ 2025-04-18 12:34:35,951 - MainThread - sqlmesh.core.console - WARNING - Linter warnings for /
          │ Users/sung/Desktop/git_repos/sqlmesh-cli-revamp/models/incremental_by_partition.sql:
      3   │  - nomissingaudits: Model `audits` must be configured to test data quality. (console.py:1848)
      4   │ 2025-04-18 12:34:35,953 - MainThread - sqlmesh.core.console - WARNING - Linter warnings for /
          │ Users/sung/Desktop/git_repos/sqlmesh-cli-revamp/models/seed_model.sql:
      5   │  - nomissingaudits: Model `audits` must be configured to test data quality. (console.py:1848)
      6   │ 2025-04-18 12:34:35,953 - MainThread - sqlmesh.core.console - WARNING - Linter warnings for /
          │ Users/sung/Desktop/git_repos/sqlmesh-cli-revamp/models/incremental_by_unique_key.sql:
      7   │  - nomissingaudits: Model `audits` must be configured to test data quality. (console.py:1848)
      8   │ 2025-04-18 12:34:35,953 - MainThread - sqlmesh.core.console - WARNING - Linter warnings for /
          │ Users/sung/Desktop/git_repos/sqlmesh-cli-revamp/models/incremental_model.sql:
      9   │  - nomissingaudits: Model `audits` must be configured to test data quality. (console.py:1848)
      10  │ 2025-04-18 12:34:35,954 - MainThread - sqlmesh.core.config.connection - INFO - Using existing
          │  DuckDB adapter due to overlapping data file: db.db (connection.py:309)
      11  │ 2025-04-18 12:34:37,071 - MainThread - sqlmesh.core.snapshot.evaluator - INFO - Listing data
          │ objects in schema db.sqlmesh__sqlmesh_example (evaluator.py:338)
      12  │ 2025-04-18 12:34:37,072 - MainThread - sqlmesh.core.engine_adapter.base - INFO - Executing SQ
          │ L: SELECT CURRENT_CATALOG() (base.py:2128)
      13  │ 2025-04-18 12:34:37,072 - MainThread - sqlmesh.core.engine_adapter.base - INFO - Executing SQ
          │ L: SELECT CURRENT_CATALOG() (base.py:2128)
    ```

## 本番環境スケジュールで実行

SQLMesh は、モデルごとに適切な DAG 順序で変換をスケジュールします。これにより、パイプラインの各ステップでデータのバックフィルを実行する頻度を簡単に設定できます。

SQLMesh は、上流モデルが遅延または失敗したモデルをスケジュールせず、デフォルトで障害発生時点から再実行します。

シナリオとモデル DAG の例:

`stg_transactions`(cron: `@hourly`) -> `fct_transcations`(cron: `@daily`)。時刻はすべて UTC です。

1. `stg_transactions` は1時間ごとに実行されます。
2. `stg_transactions` が最新の1時間間隔以降に更新されている場合、`fct_transcations` は午前0時（UTC）に実行されます。
3. `stg_transactions` が午後11時から午後11時59分59秒までの間に失敗した場合、`fct_transcations` の実行が阻止され、`pending` 状態になります。
4. `fct_transactions` が、指定された間隔（丸1日）を超えて `pending` 状態の場合、`late` 状態になります。
5. 再試行またはプルリクエストによる修正によって `stg_transactions` が正常に実行されると、`fct_transactions` は失敗した時点から再実行されます。これは、`fct_transactions` が数日間 `late` 状態であった場合でも当てはまります。

注: `pending` および `late` 状態は、Tobiko Cloud でのみサポートされています。 SQLMesh では、モデルが実行可能かどうかは認識されますが、これらの状態については言及されません。

オープンソースの SQLMesh を使用している場合は、このコマンドをオーケストレーター（例：Dagster、GitHub Actions など）で 5 分ごと、またはモデルの最小 cron スケジュール（例：1 時間ごと）で実行できます。必要な実行のみが実行されるのでご安心ください。

Tobiko Cloud を使用している場合は、追加の設定なしで自動的に構成されます。

### モデルの実行

このコマンドはスケジュールに従って実行されることを目的としています。物理レイヤーと仮想レイヤーの更新はスキップされ、モデルのバッチ処理のみが実行されます。

=== "SQLMesh"

    ```bash
    sqlmesh run
    ```

=== "Tobiko Cloud"

    ```bash
    tcloud sqlmesh run
    ```

??? "Example Output"

    モデルの実行準備が完了すると、次のようになります。

    ```bash
    > sqlmesh run
    [1/1] sqlmesh_example.incremental_model               [insert 2025-04-17 - 2025-04-17]
    0.01s
    [1/1] sqlmesh_example.incremental_unique_model        [insert/update rows]
    0.01s
    [1/1] sqlmesh_example_v3.incremental_partition_model  [insert partitions]
    0.01s
    Executing model batches ━━━━━━━━━━━━━━━━╺━━━━━━━━━━━━━━━━━━━━━━━ 40.0% • 2/5 • 0:00:00
    sqlmesh_example_v3.incremental_partition_model .
    [WARNING] sqlmesh_example.full_model: 'assert_positive_order_ids' audit error: 2 rows failed. Learn
    more in logs: /Users/sung/Desktop/git_repos/sqlmesh-cli-revamp/logs/sqlmesh_2025_04_18_12_48_35.log
    [1/1] sqlmesh_example.full_model                      [full refresh, audits ❌1]
    0.01s
    Executing model batches ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╺━━━━━━━ 80.0% • 4/5 • 0:00:00
    sqlmesh_example.view_model .
    [WARNING] sqlmesh_example.view_model: 'assert_positive_order_ids' audit error: 2 rows failed. Learn
    more in logs: /Users/sung/Desktop/git_repos/sqlmesh-cli-revamp/logs/sqlmesh_2025_04_18_12_48_35.log
    [1/1] sqlmesh_example.view_model                      [recreate view, audits ✔2 ❌1]
    0.01s
    Executing model batches ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100.0% • 5/5 • 0:00:00

    ✔ Model batches executed

    Run finished for environment 'prod'
    ```

    実行できるモデルがない場合、このようになります。

    ```bash
    > sqlmesh run
    No models are ready to run. Please wait until a model `cron` interval has elapsed.

    Next run will be ready at 2025-04-18 05:00PM PDT (2025-04-19 12:00AM UTC).
    ```

### 不完全な間隔でモデルを実行する（警告）

アドホックまたはスケジュールに基づいて、`run` を呼び出すたびにバックフィルを実行するモデルを実行できます。

!!! warning "不完全な間隔でモデルを実行する"
    これは、`allow_partials` が `true` に設定されている増分モデルにのみ適用されます。
    不完全なデータを送信すると、壊れたデータとして認識されるリスクがあるため、通常、本番環境では推奨されません。

=== "SQLMesh"

    ```bash
    sqlmesh run --ignore-cron
    ```

=== "Tobiko Cloud"

    ```bash
    tcloud sqlmesh run --ignore-cron
    ```

??? "Example Output"

    モデル定義:
    ```sql linenums="1" hl_lines="15" title="models/incremental_model.sql"
    MODEL (
      name sqlmesh_example.incremental_model,
      kind INCREMENTAL_BY_TIME_RANGE (
        time_column event_date
      ),
      start '2020-01-01',
      cron '@daily',
      grain (id, event_date),
      audits( UNIQUE_VALUES(columns = (
          id,
      )), NOT_NULL(columns = (
          id,
          event_date
      ))),
      allow_partials true
    );

    SELECT
      id,
      item_id,
      event_date,
      16 as new_column
    FROM
      sqlmesh_example.seed_model
    WHERE
      event_date BETWEEN @start_date AND @end_date
    ```

    ```bash
    > sqlmesh run --ignore-cron
    [1/1] sqlmesh_example.incremental_model  [insert 2025-04-19 - 2025-04-19, audits ✔2] 0.05s
    Executing model batches ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100.0% • 1/1 • 0:00:00

    ✔ Model batches executed

    Run finished for environment 'prod'
    ```

## フォワードオンリー開発ワークフロー

これは高度なワークフローであり、開発段階であっても実行に長い時間を要する大規模な増分モデル（例：2億行超）向けに特別に設計されています。このワークフローは、以下の問題を解決します。

- `struct` およびネストされた `array` データ型のスキーマ進化を伴うデータ変換。
- 計算列の履歴を保持し、以降の新しい行に新しい計算を適用する。
- 複雑な条件付き `CASE WHEN` ロジックを含む列の履歴を保持し、以降の新しい行に新しい条件を適用する。

開発ワークフロー後にフォワードオンリーモデルを変更し、プランを `prod` に適用しても、履歴データはバックフィルされません。**時間的に前進する** 新しい間隔（つまり、新しい行のみ）のモデルバッチのみが実行されます。

詳細なウォークスルーについては、[こちら](incremental_time_full_walkthrough.md) をご覧ください。

=== "SQLMesh"

    ```bash
    sqlmesh plan dev --forward-only
    ```

    ```bash
    sqlmesh plan <environment> --forward-only
    ```

=== "Tobiko Cloud"

    ```bash
    tcloud sqlmesh plan dev --forward-only
    ```

    ```bash
    tcloud sqlmesh plan <environment> --forward-only
    ```

??? "Example Output"

    - 新しい列に変更を適用しました。
    - 2つの下流モデルに影響します。
    - 増分モデルの履歴データのバックフィルを回避するため、フォワードオンリープランを適用しました（例：CLI出力の「preview」言語）。
    - 影響を受ける増分モデルのクローン（クローンは本番環境では再利用されません）と、フルモデルおよびビューモデル（これらはクローンではありません）で変更をプレビューしました。

    ```bash
    > sqlmesh plan dev
    Differences from the `dev` environment:

    Models:
    ├── Directly Modified:
    │   └── sqlmesh_example__dev.incremental_model
    └── Indirectly Modified:
        ├── sqlmesh_example__dev.view_model
        └── sqlmesh_example__dev.full_model

    ---

    +++

    @@ -16,7 +16,7 @@

      id,
      item_id,
      event_date,
    -  9 AS new_column
    +  10 AS new_column
    FROM sqlmesh_example.seed_model
    WHERE
      event_date BETWEEN @start_date AND @end_date

    Directly Modified: sqlmesh_example__dev.incremental_model (Forward-only)
    └── Indirectly Modified Children:
        ├── sqlmesh_example__dev.full_model (Forward-only)
        └── sqlmesh_example__dev.view_model (Forward-only)
    Models needing backfill:
    ├── sqlmesh_example__dev.full_model: [full refresh] (preview)
    ├── sqlmesh_example__dev.incremental_model: [2025-04-17 - 2025-04-17] (preview)
    └── sqlmesh_example__dev.view_model: [recreate view] (preview)
    Apply - Preview Tables [y/n]: y

    Updating physical layer ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100.0% • 3/3 • 0:00:00

    ✔ Physical layer updated

    [1/1] sqlmesh_example__dev.incremental_model  [insert 2025-04-17 - 2025-04-17]                0.01s
    [1/1] sqlmesh_example__dev.full_model         [full refresh, audits ✔1]                       0.01s
    [1/1] sqlmesh_example__dev.view_model         [recreate view, audits ✔3]                      0.01s
    Executing model batches ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100.0% • 3/3 • 0:00:00

    ✔ Model batches executed

    Updating virtual layer  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100.0% • 3/3 • 0:00:00

    ✔ Virtual layer updated
    ```

    プランが `prod` に適用されると、新しい間隔 (新しい行) のモデル バッチのみが実行されます。これにより、`preview` モデル（バックフィルされたデータ）は開発環境で再利用されません。

    ```bash
    > sqlmesh plan
    Differences from the `prod` environment:

    Models:
    ├── Directly Modified:
    │   └── sqlmesh_example.incremental_model
    └── Indirectly Modified:
        ├── sqlmesh_example.view_model
        └── sqlmesh_example.full_model

    ---

    +++

    @@ -9,13 +9,14 @@

        disable_restatement FALSE,
        on_destructive_change 'ERROR'
      ),
    -  grains ((id, event_date))
    +  grains ((id, event_date)),
    +  allow_partials TRUE
    )
    SELECT
      id,
      item_id,
      event_date,
    -  7 AS new_column
    +  10 AS new_column
    FROM sqlmesh_example.seed_model
    WHERE
      event_date BETWEEN @start_date AND @end_date

    Directly Modified: sqlmesh_example.incremental_model (Forward-only)
    └── Indirectly Modified Children:
        ├── sqlmesh_example.full_model (Forward-only)
        └── sqlmesh_example.view_model (Forward-only)
    Apply - Virtual Update [y/n]: y

    SKIP: No physical layer updates to perform

    SKIP: No model batches to execute

    Updating virtual layer  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100.0% • 3/3 • 0:00:00

    ✔ Virtual layer updated
    ```


## その他

古い開発スキーマやデータが大量にあることに気づいた場合は、以下のコマンドでクリーンアップできます。このプロセスは、`sqlmesh run` コマンドの実行中に自動的に実行されます。デフォルトでは、7日以上経過したデータが削除されます。

=== "SQLMesh"

    ```bash
    sqlmesh janitor
    ```

=== "Tobiko Cloud"

    ```bash
    tcloud sqlmesh janitor
    ```