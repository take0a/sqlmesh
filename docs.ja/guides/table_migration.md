# テーブル移行ガイド

SQLMesh プロジェクトは、SQLMesh が管理していないテーブルから直接データを読み取ることができますが、シナリオによっては、既存のテーブルを SQLMesh プロジェクトに移行することが有効な場合があります。

このガイドでは、既存のテーブルを SQLMesh プロジェクトに移行する 2 つの方法について説明します。

## 移行が必要ですか？

SQLMesh はすべてのデータソースを管理できるわけではありません。SQL モデルは、SQL エンジンがアクセス可能な任意のデータソースから読み取り、それらを列レベルの系統を含む [外部モデル](../concepts/models/model_kinds.md#external) または汎用ソースとして扱うことができます。既存のテーブルを SQLMesh プロジェクトに移行するよりも、このアプローチが推奨されます。

以下の両方の条件を満たす場合にのみ、テーブルを移行する必要があります。

1. テーブルが、継続的に新しいデータを生成する上流ソースからデータを取り込んでいる場合
2. テーブルが再構築するには大きすぎるか、必要な履歴データが利用できないために再構築できない場合

テーブルの上流ソースがこれ以上データを生成しない場合、SQLMesh が管理する継続的なアクティビティはありません。SQLMesh モデルまたはその他の下流のコンシューマーは、現在の名前でテーブルから直接データを選択できます。

テーブルの上流ソースが新しいデータを生成している場合、テーブルは既に増分ロードされていると想定します。テーブルを完全に再構築できる場合は移行の必要はありません。

以下では2つの移行方法について説明します。ステージングとユニオン方式が推奨され、実行可能な場合はこの方式を使用する必要があります。

## 移行方法

このセクションでは、SQLMesh にテーブルを移行する 2 つの方法について説明します。

これらの方法の説明には、下流のコンシューマーが元のテーブル名から選択する必要がある場合にのみ必要な名前変更手順が含まれています（例：最初の例の手順 2）。そうでない場合は、元のテーブル名を維持できます。

以下の例のテーブル名とモデル名は任意です。プロジェクトに適した名前を付けてください。

### ステージングとユニオン

ステージングとユニオン方式は、新規データと履歴データを別々のソースとして扱うことで機能します。

この方式では、新規レコードを取り込むための増分ステージングモデルと、それらのレコードを既存のテーブルの静的な履歴レコードとユニオンする「VIEW」モデルを作成する必要があります。

#### 例

`my_schema.existing_table` という名前の既存のテーブルを考えてみましょう。ステージングとユニオン方式によるこのテーブルの移行は、以下の5つのステップで構成されます。

1. `my_schema.existing_table` が最新であることを確認します（利用可能なすべてのソースデータが取り込まれている必要があります）。
2. `my_schema.existing_table` の名前を、`my_schema.existing_table_historical` など、任意の名前に変更します。
- 必要に応じて、テーブルを [`EXTERNAL` モデル](../concepts/models/model_kinds.md#external) にして、プロジェクトの `external_models.yaml` ファイルに追加することで、列レベルのリネージを有効にします。
3. `my_schema.existing_table_staging` という名前の新しい増分ステージングモデルを作成します（コードは以下を参照）。
4. `my_schema.existing_table` という名前の新しい [`VIEW` モデル](../concepts/models/model_kinds.md#view) を作成します。 (コードは下記を参照)
5. `sqlmesh plan` を実行してモデルを作成し、バックフィルします。

ステージングモデルには、`INCREMENTAL_BY_TIME_RANGE` モデルの場合、以下のようなコードが含まれます。`INCREMENTAL_BY_UNIQUE_KEY` モデルの場合は、`MODEL` DDL の `kind` 指定が異なり、クエリの `WHERE` 句が含まれていない可能性があります。

``` sql linenums="1"
MODEL(
  name my_schema.existing_table_staging,
  kind INCREMENTAL_BY_TIME_RANGE ( -- or INCREMENTAL_BY_UNIQUE_KEY
    time_column table_time_column
  )
);

SELECT
  col1,
  col2,
  col3
FROM
  [your model's ongoing data source]
WHERE
  table_time_column BETWEEN @start_ds and @end_ds;
```

プライマリ モデルには次のようなコードが含まれます。

``` sql linenums="1"
MODEL(
  name my_schema.existing_table,
  kind VIEW
)

SELECT
  col1,
  col2,
  col3
FROM
  my_schema.existing_table_staging -- New data
UNION
SELECT
  col1,
  col2,
  col3
FROM
  my_schema.existing_table_historical; -- Historical data
```

ソース データまたはステージング モデルの列を変更する場合は、2 つのテーブルを安全に結合できるように、履歴データから選択するコードの変更が必要になることがあります。

### スナップショットの置き換え

スナップショットの置き換え方法は、既存のテーブルの名前を、SQLMesh が既存の SQLMesh モデルとして認識できる名前に変更することで機能します。

#### 背景

このセクションでは、SQLMesh の仮想データ環境、順方向のみのモデル、および開始時刻の仕組みについて簡単に説明します。この情報はテーブルの移行には必要ありませんが、移行プロセスの各ステップが必要な理由を理解するために必要です。

##### 仮想データ環境

概念的には、SQLMesh はデータベースを、データが格納される「物理層」と、エンドユーザーがデータにアクセスする「仮想層」に分割します。物理層にはテーブルなどのマテリアライズドオブジェクトが格納され、仮想層には物理層オブジェクトを参照するビューが含まれます。

SQLMesh のプランがモデルを追加または変更するたびに、SQLMesh は仮想層ビューが参照する物理層の「スナップショット」オブジェクトを作成します。スナップショット置換方式では、移行対象のテーブルの名前を適切なスナップショットテーブルの名前に変更するだけです。

##### 前方参照のみのモデル

モデルのデータが非常に大きいため、モデル自体または下流モデルの物理テーブルを再構築することが現実的でない場合があります。このような状況では、「前方参照のみのモデル」を使用できます。この名前は、変更が時間的に「前方」にのみ適用されることを示しています。

移行されたテーブルにすでに含まれている履歴データは上書きされないようにするため、以下の手順 3a で新しいモデルが前方参照のみであることを指定します。

##### 開始時刻

SQLMesh の時間増分モデルは、[間隔アプローチ](https://sqlmesh.readthedocs.io/en/stable/guides/incremental_time/#counting-time) を用いて、モデルがデータをロードした期間を追跡します。

間隔アプローチでは、SQLMesh が追跡する最も早い時間間隔、つまりモデルの時間が「開始」する時点を指定する必要があります。移行されたテーブルの場合、SQLMesh は移行前にテーブルが取り込んだ時間間隔のデータをロードしないため、間隔の追跡は最後に取り込まれたレコードの時刻の直後から開始する必要があります。

以下の例では、モデルの開始時刻を `MODEL` DDL (手順 3b) で設定し、それを `sqlmesh plan` コマンド (手順 3c) のオプションとして渡しています。`MODEL` DDL と plan コマンドの両方で同じ値を使用する必要があります。この例では、既存のテーブルのデータ取り込みが 2023-12-31 に停止したため、モデルとプランの開始日は翌日の 2024-01-01 になります。

#### 例

`my_schema.existing_table` という既存のテーブルがあるとします。このテーブルをスナップショット置換方式で移行するには、次の 5 つの手順が必要です。

1. `my_schema.existing_table` が最新である（利用可能なすべてのソースデータが取り込まれている）ことを確認します。
2. `my_schema.existing_table` の名前を、`my_schema.existing_table_temp` など、任意の名前に変更します。
3. `my_schema.existing_table` という空の増分モデルを作成し、初期化します。

    a. `MODEL` DDL `kind` の `forward_only` キーを `true` に設定して、モデルを [forward only](./incremental_time.md#forward-only-models) にします。

    b. SQLMesh が追跡する最初の時間間隔の開始日を `MODEL` DDL の `start` キーで指定します (例では "2024-01-01" を使用)。

    c. `sqlmesh plan [environment name] --empty-backfill --start 2024-01-01` を実行し、データのバックフィルを行わずに SQLMesh プロジェクトにモデルを作成します。[environment name] を `prod` 以外の環境名に置き換え、手順 3b の `MODEL` DDL と同じ開始日を使用します。

4. `sqlmesh table_name --env [environment name] --prod my_schema.existing_table` を実行し、モデルのスナップショット物理テーブルの名前を確認します。たとえば、`sqlmesh__my_schema.existing_table_123456` が返されます。
5. 元のテーブル「my_schema.existing_table_temp」の名前を「sqlmesh__my_schema.existing_table_123456」に変更します。

モデルのコードは次のようになります。

``` sql linenums="1" hl_lines="5 7-9"
MODEL(
  name my_schema.existing_table,
  kind INCREMENTAL_BY_TIME_RANGE( -- or INCREMENTAL_BY_UNIQUE_KEY
    time_column table_time_column,
    forward_only true -- Forward-only model
  ),
  -- Start of first time interval SQLMesh should track, immediately
  --  after the last data point the table ingested. Must match
  --  the value passed to the `sqlmesh plan --start` option.
  start "2024-01-01"
)

SELECT
  col1,
  col2,
  col3
FROM
  [your model's ongoing data source]
WHERE
  table_time_column BETWEEN @start_ds and @end_ds;
```
