# Model configuration

このページでは、SQLMesh モデルの設定オプションとそのパラメータについて説明します。

SQLMesh モデルのプロパティの指定方法の詳細については、[モデルの概念の概要ページ](../concepts/models/overview.md#model-properties) をご覧ください。

## General model properties

SQLMeshモデルのプロパティの設定オプション。[`SEED`モデル](#seed-models)以外のすべてのモデルでサポートされています。

| オプション | 説明 | タイプ | 必須 |
|-----------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:-----------------:|:--------:|
| `name` | モデル名。少なくとも修飾スキーマ (`<schema>.<model>`) を含める必要があり、カタログ (`<catalog>.<schema>.<model>`) を含めることができます。[infer_names](#model-naming) が true に設定されている場合は省略できます。| str | N |
| `project` | モデルが属するプロジェクトの名前 - マルチリポジトリのデプロイメントで使用されます | str | N |
| `kind` | モデルの種類 ([追加の詳細](#model-kind-properties))。(デフォルト: `VIEW`) | str \| dict | N |
| `audits` |モデルの出力に対して実行する SQLMesh [監査](../concepts/audits.md) | 配列 [str] | N |
| `dialect` | モデルのクエリが記述されている SQL 方言。[SQLGlot ライブラリでサポートされている](https://github.com/tobymao/sqlglot/blob/main/sqlglot/dialects/dialect.py) すべての SQL 方言が許可されます。 | str | N |
| `owner` | モデルの所有者。通知の目的で使用できます | str | N |
| `stamp` | モデル名を変更せずにモデルのバージョンを示すために使用される任意の文字列 | str | N |
| `tags` | モデルを整理または分類するために使用される任意の文字列 | array[str] | N |
| `cron` | モデルを更新する頻度を指定する cron 式。(デフォルト: `@daily`) | str | N |
| `interval_unit` | モデルのデータ間隔の時間粒度。サポートされる値: `year`、`month`、`day`、`hour`、`half_hour`、`quarter_hour`、`five_minute`。(デフォルト: `cron` から推定) | str | N |
| `start` | モデルによって処理される最も古い日付間隔を決定する日付/時刻。日付時刻文字列、ミリ秒単位のエポック時間、または `1 year ago` などの相対日付時刻を指定できます。(デフォルト: `yesterday`) | str \| int | N |
| `end` | モデルで処理する最後の日付間隔を決定する日付/時刻。日付時刻文字列、ミリ秒単位のエポックタイム、または `1 year ago` などの相対日付時刻を指定できます。| str \| int | N |
| `description` | モデルの説明。SQL エンジンのテーブル COMMENT フィールドまたは同等のフィールドに自動的に登録されます (エンジンでサポートされている場合)。| str | N |
| `column_descriptions` | 列名と列コメントのキーと値のマッピング。SQL エンジンのテーブル COMMENT フィールドに登録されます (エンジンでサポートされている場合)。キーと値のペアとして指定します (`column_name = 'column comment'`)。存在する場合、[インライン列コメント](../concepts/models/overview.md#inline-column-comments) は SQL エンジンに登録されません。| dict | N |
| `grains` |モデル内の各行を一意に識別する組み合わせの列 | str \| array[str] | N |
| `references` | 他のモデルのグレインに結合するために使用されるモデル列 | str \| array[str] | N |
| `depends_on` | このモデルが依存するモデル、およびモデルのクエリから推論されたモデル。(デフォルト: モデルコードから推論された依存関係) | array[str] | N |
| `table_format` | 物理ファイルの管理に使用するテーブル形式 (例: `iceberg`、`hive`、`delta`)。Spark や Athena などのエンジンにのみ適用されます | str | N |
| `storage_format` | 物理ファイルの保存に使用するストレージ形式 (例: `parquet`、`orc`)。Spark や Athena などのエンジンにのみ適用されます。 | str | N |
| `partitioned_by` | モデルのパーティション キーを定義する列や列式。`INCREMENTAL_BY_PARTITION` モデルの種類では必須です。その他すべてのモデルの種類ではオプションです。パーティション分割をサポートするエンジンでモデルの物理テーブルをパーティション分割するために使用されます。 | str \| array[str] | N |
| `clustered_by` | モデルの物理テーブルをクラスター化するために使用される列や列式。クラスタリングをサポートするエンジンにのみ適用されます。 | str | N |
| `columns` | モデルによって返される列名とデータ型。 SQL クエリからの [列名と型の自動推論](../concepts/models/overview.md#conventions) を無効にします。 | array[str] | N |
| `physical_properties` | 物理レイヤーのモデル テーブル/ビューに適用される、ターゲット エンジンに固有の任意のプロパティのキーと値のマッピング。キーと値のペア (`key = value`) として指定します。ビュー/テーブル タイプ (例: `TEMPORARY`、`TRANSIENT`) は、`creatable_type` キーを使用して追加できます。 | dict | N |
| `virtual_properties` | 仮想レイヤーのモデル ビューに適用される、ターゲット エンジンに固有の任意のプロパティのキーと値のマッピング。キーと値のペア (`key = value`) として指定します。ビュー タイプ (例: `SECURE`) は、`creatable_type` キーを使用して追加できます。 | dict | N |
| `session_properties` | エンジン セッションに適用される、ターゲット エンジンに固有の任意のプロパティのキーと値のマッピング。キーと値のペア (`key = value`) として指定します。 | dict | N |
| `allow_partials` | このモデルが部分的な (不完全な) データ間隔を処理できるかどうか | bool | N |
| `enabled` | モデルが有効かどうか。この属性の既定値は `true` です。これを `false` に設定すると、SQLMesh はプロジェクトの読み込み時にこのモデルを無視します。 | bool | N |
| `gateway` | このモデルの実行に使用するゲートウェイを指定します。指定しない場合は、デフォルトのゲートウェイが使用されます。 | str | N |
| `optimize_query` | モデルのクエリを最適化するかどうか。この属性はデフォルトで `true` です。これを `false` に設定すると、SQLMesh はクエリの正規化と簡素化を無効にします。最適化されたクエリがテキスト制限を超えるなどのエラーを引き起こす場合にのみ、これをオフにする必要があります。 | bool | N |
| `ignored_rules` | このモデルで無視/除外するリンタールール名のリスト (または "ALL") | str \| array[str] | N |
| `formatting` | モデルをフォーマットするかどうか。デフォルトではすべてのモデルがフォーマットされます。これを `false` に設定すると、SQLMesh は `sqlmesh format` 中にこのモデルを無視します。 | bool | N |

### Model defaults

SQLMesh プロジェクトレベル設定には、`model_defaults` キーが含まれ、その `dialect` キーの値を指定する必要があります。その他の値は、モデル定義で明示的にオーバーライドされない限り、自動的に設定されます。プロジェクトレベル設定の詳細については、[設定ガイド](../guides/configuration.md) を参照してください。

`physical_properties`、`virtual_properties`、および `session_properties` において、プロジェクトレベルとモデル固有のプロパティの両方が定義されている場合、それらはマージされ、モデルレベルのプロパティが優先されます。特定のモデルのプロジェクト全体にわたるプロパティの設定を解除するには、`MODEL` の DDL プロパティ、または Python モデルの `@model` デコレータ内でそのプロパティを `None` に設定します。

例えば、次の `model_defaults` 設定では、次のようになります。

=== "YAML"

    ```yaml linenums="1"
    model_defaults:
      dialect: snowflake
      start: 2022-01-01
      physical_properties:
        partition_expiration_days: 7
        require_partition_filter: True
        project_level_property: "value"
    ```

=== "Python"

    ```python linenums="1"
    from sqlmesh.core.config import Config, ModelDefaultsConfig

    config = Config(
      model_defaults=ModelDefaultsConfig(
        dialect="snowflake",
        start="2022-01-01",
        physical_properties={
          "partition_expiration_days": 7,
          "require_partition_filter": True,
          "project_level_property": "value"
        },
      ),
    )
    ```

`partition_expiration_days` をオーバーライドするには、新しい `creatable_type` プロパティを追加し、`project_level_property` を設定解除して、次のようにモデルを定義します。

=== "SQL"

    ```sql linenums="1"
    MODEL (
      ...,
      physical_properties (
        partition_expiration_days = 14,
        creatable_type = TRANSIENT,
        project_level_property = None,
      )
    );
    ```

=== "Python"

    ```python linenums="1"
    @model(
      ...,
      physical_properties={
        "partition_expiration_days": 14,
        "creatable_type": "TRANSIENT",
        "project_level_property": None
      },
    )
    ```

`@model_kind_name` 変数を使用して、`model_defaults` の `physical_properties` を細かく制御することもできます。この変数は現在のモデルの種類名を保持し、条件に応じてプロパティを割り当てる場合に便利です。例えば、プロジェクトの `VIEW` 種類のモデルで `creatable_type` を無効にするには、次のようにします。

=== "YAML"

    ```yaml linenums="1"
    model_defaults:
      dialect: snowflake
      start: 2022-01-01
      physical_properties:
        creatable_type: "@IF(@model_kind_name != 'VIEW', 'TRANSIENT', NULL)"
    ```

=== "Python"

    ```python linenums="1"
    from sqlmesh.core.config import Config, ModelDefaultsConfig

    config = Config(
      model_defaults=ModelDefaultsConfig(
        dialect="snowflake",
        start="2022-01-01",
        physical_properties={
          "creatable_type": "@IF(@model_kind_name != 'VIEW', 'TRANSIENT', NULL)",
        },
      ),
    )
    ```

プロジェクトレベルで `pre_statements`、`post_statements`、`on_virtual_update` ステートメントを定義し、すべてのモデルに適用することもできます。これらのデフォルトステートメントはモデル固有のステートメントとマージされ、デフォルトステートメントが最初に実行され、その後にモデル固有のステートメントが実行されます。

=== "YAML"

    ```yaml linenums="1"
    model_defaults:
      dialect: duckdb
      pre_statements:
        - "SET timeout = 300000"
      post_statements:
        - "@IF(@runtime_stage = 'evaluating', ANALYZE @this_model)"
      on_virtual_update:
        - "GRANT SELECT ON @this_model TO ROLE analyst_role"
    ```

=== "Python"

    ```python linenums="1"
    from sqlmesh.core.config import Config, ModelDefaultsConfig

    config = Config(
      model_defaults=ModelDefaultsConfig(
        dialect="duckdb",
        pre_statements=[
          "SET query_timeout = 300000",
        ],
        post_statements=[
          "@IF(@runtime_stage = 'evaluating', ANALYZE @this_model)",
        ],
        on_virtual_update=[
          "GRANT SELECT ON @this_model TO ROLE analyst_role",
        ],
      ),
    )
    ```


SQLMesh プロジェクト レベルの `model_defaults` キーは、上記の [一般的なモデル プロパティ](#general-model-properties) の表で説明されている次のオプションをサポートしています。

- kind
- dialect
- cron
- owner
- start
- table_format
- storage_format
- physical_properties
- virtual_properties
- session_properties (on per key basis)
- on_destructive_change (described [below](#incremental-models))
- on_additive_change (described [below](#incremental-models))
- audits (described [here](../concepts/audits.md#generic-audits))
- optimize_query
- allow_partials
- enabled
- interval_unit
- pre_statements (described [here](../concepts/models/sql_models.md#pre--and-post-statements))
- post_statements (described [here](../concepts/models/sql_models.md#pre--and-post-statements))
- on_virtual_update (described [here](../concepts/models/sql_models.md#on-virtual-update-statements))


### Model Naming

名前推論の設定オプションです。詳しくは[モデル命名ガイド](../guides/configuration.md#model-naming)をご覧ください。

| オプション | 説明 | タイプ | 必須 |
|--------------|------------------------------------------------------------------------------------------------|:----:|:--------:|
| `infer_names` | ディレクトリ構造に基づいてモデル名を自動的に推論するかどうか (デフォルト: `False`) | bool | N |

## Model kind properties

上記の[一般的なモデルプロパティ](#general-model-properties)に加えて、種類固有のSQLMeshモデルプロパティの構成オプションがあります。

モデルの種類の詳細については、[モデルの種類の概念ページ](../concepts/models/model_kinds.md)をご覧ください。Pythonモデルでのモデル種類の指定の詳細については、[Pythonモデルの概念ページ](../concepts/models/python_models.md#model-specification)をご覧ください。

### `VIEW` models

[`VIEW` 種類](../concepts/models/model_kinds.md#view) のモデルの構成オプション（[一般的なモデルプロパティ](#general-model-properties) に加えて）。

| オプション | 説明 | タイプ | 必須 |
|----------------|--------------------------------------------------------------------------------------------------|:----:|:--------:|
| `materialized` | ビューをマテリアライズするかどうか（マテリアライズドビューをサポートするエンジンの場合）。(デフォルト: `False`) | bool | N |

Python モデル種類 `name` 列挙値: [ModelKindName.VIEW](https://sqlmesh.readthedocs.io/en/stable/_readthedocs/html/sqlmesh/core/model/kind.html#ModelKindName)

### `FULL` models

[`FULL` モデル種別](../concepts/models/model_kinds.md#full) は、[上記の一般的なモデルプロパティ](#general-model-properties) 以外の構成オプションをサポートしていません。

Python モデル種別 `name` 列挙値: [ModelKindName.FULL](https://sqlmesh.readthedocs.io/en/stable/_readthedocs/html/sqlmesh/core/model/kind.html#ModelKindName)

### Incremental models

すべての増分モデルの設定オプション（[一般的なモデルプロパティ](#general-model-properties)に加えて）。

| オプション | 説明 | タイプ | 必須 |
|------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:----:|:--------:|
| `forward_only` | モデルの変更を常に [forward-only](../concepts/plans.md#forward-only-change) として分類するかどうか。(デフォルト: `False`) | bool | N |
| `on_destructive_change` | [forward-only モデル](../guides/incremental_time.md#forward-only-models) または [forward-only プラン](../concepts/plans.md#forward-only-plans) 内の増分モデルへの変更によって、モデル スキーマに破壊的な変更が発生した場合に何が起こるか。有効な値: `allow`、`warn`、`error`、`ignore`。(既定値: `error`) | str | N |
| `on_additive_change` | [forward-only モデル](../guides/incremental_time.md#forward-only-models) または [forward-only プラン](../concepts/plans.md#forward-only-plans) 内の増分モデルへの変更によって、モデル スキーマに追加的な変更 (新しい列の追加など) が発生した場合に何が起こるか。有効な値: `allow`、`warn`、`error`、`ignore`。(デフォルト: `allow`) | str | N |
| `disable_restatement` | モデルに対して [restatements](../concepts/plans.md#restatement-plans) を無効にするかどうか。(デフォルト: `False`) | bool | N |

#### Incremental by time range

[`INCREMENTAL_BY_TIME_RANGE` モデル](../concepts/models/model_kinds.md#incremental_by_time_range) の設定オプション ([一般モデルプロパティ](#general-model-properties) および [増分モデルプロパティ](#incremental-models) に加えて)。

| オプション | 説明 | タイプ | 必須 |
| ------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :--: | :------: |
| `time_column` | 各行のタイムスタンプを格納するモデル列。UTC タイムゾーンである必要があります。 | str | Y |
| `format` | `time_column` への引数。時刻列のデータの形式。(デフォルト: `%Y-%m-%d`) | str | N |
| `batch_size` | 1 回のバックフィルタスクで評価できる間隔の最大数。これが `None` の場合、すべての間隔が 1 つのタスクの一部として処理されます。これが設定されている場合、モデルのバックフィルはチャンクに分割され、各タスクには最大 `batch_size` 間隔のジョブのみが含まれます。(デフォルト: `None`) | int | N |
| `batch_concurrency` | このモデルで同時に実行できるバッチの最大数。(デフォルト: 接続設定で設定された同時実行タスク数) | int | N |
| `lookback` | 現在の間隔より前の処理対象となる `interval_unit` の数 - [詳細](../concepts/models/overview.md#lookback)。(デフォルト: `0`) | int | N |

Python モデルの種類 `name` 列挙値: [ModelKindName.INCREMENTAL_BY_TIME_RANGE](https://sqlmesh.readthedocs.io/en/stable/_readthedocs/html/sqlmesh/core/model/kind.html#ModelKindName)

#### Incremental by unique key

[`INCREMENTAL_BY_UNIQUE_KEY` モデル](../concepts/models/model_kinds.md#incremental_by_unique_key) の設定オプションです ([一般モデルプロパティ](#general-model-properties) および [増分モデルプロパティ](#incremental-models) に加えて)。増分 by unique key モデルは安全に並列実行できないため、バッチ同時実行は設定できません。

| オプション | 説明 | タイプ | 必須 |
|----------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------|----------|
| `unique_key` | 各行の一意のキーを含むモデル列 | str \| array[str] | Y |
| `when_matched` | 一致が発生した場合に列を更新するために使用する SQL ロジック - `MERGE` をサポートするエンジンでのみ使用できます。 (デフォルト: すべての列を更新) | str | N |
| `merge_filter` | MERGE 操作の ON 句でデータをフィルター処理するために使用される述語 (単一または複数の述語の組み合わせ) - `MERGE` をサポートするエンジンでのみ使用可能 | str | N |
| `batch_size` | 1 回のバックフィル タスクで評価できる間隔の最大数。これが `None` の場合、すべての間隔が 1 つのタスクの一部として処理されます。これが設定されている場合、モデルのバックフィルは、各タスクに最大 `batch_size` 間隔のジョブのみが含まれるようにチャンク化されます。(デフォルト: `None`) | int | N |
| `lookback` | 現在の間隔より前の処理対象となる時間単位間隔の数。(デフォルト: `0`) | int | N |

Python モデルの種類 `name` 列挙値: [ModelKindName.INCREMENTAL_BY_UNIQUE_KEY](https://sqlmesh.readthedocs.io/en/stable/_readthedocs/html/sqlmesh/core/model/kind.html#ModelKindName)

#### Incremental by partition

[`INCREMENTAL_BY_PARTITION` モデル](../concepts/models/model_kinds.md#incremental_by_partition) 種類は、[一般モデルプロパティ](#general-model-properties) と [増分モデルプロパティ](#incremental-models) 以外の構成オプションをサポートしていません。

Python モデル種類 `name` 列挙値: [ModelKindName.INCREMENTAL_BY_PARTITION](https://sqlmesh.readthedocs.io/en/stable/_readthedocs/html/sqlmesh/core/model/kind.html#ModelKindName)

#### SCD Type 2 models

[`SCD_TYPE_2` モデル](../concepts/models/model_kinds.md#scd-type-2) の設定オプション ([一般モデルプロパティ](#general-model-properties) および [増分モデルプロパティ](#incremental-models) に加えて)。

| オプション | 説明 | タイプ | 必須 |
| ------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :--------: | :------: |
| `unique_key` | 各行の一意のキーを含むモデル列 | 配列[str] | Y |
| `valid_from_name` | 各行の有効開始日を含むモデル列。(デフォルト: `valid_from`) | str | N |
| `valid_to_name` | 各行の有効終了日を含むモデル列。 (デフォルト: `valid_to`) | str | N |
| `invalidate_hard_deletes` | true に設定すると、ソース テーブルにレコードがない場合、そのレコードは無効としてマークされます。詳細については、[こちら](../concepts/models/model_kinds.md#deletes) を参照してください。(デフォルト: `True`) | bool | N |

##### SCD Type 2 By Time

[`SCD_TYPE_2_BY_TIME` モデル](../concepts/models/model_kinds.md#scd-type-2) の設定オプション ([一般モデルプロパティ](#general-model-properties)、[増分モデルプロパティ](#incremental-models)、[SCD タイプ 2 プロパティ](#scd-type-2-models) に加えて)。

| オプション | 説明 | タイプ | 必須 |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | :--: | :------: |
| `updated_at_name` | 各行の更新日時を含むモデル列。(デフォルト: `updated_at`) | str | N |
| `updated_at_as_valid_from` |デフォルトでは、新しい行の `valid_from` 列は 1970-01-01 00:00:00 に設定されます。これにより、行が挿入されたときの `updated_at` の値が `valid_from` に設定されます。(デフォルト: `False`) | bool | N |

Python モデルの種類 `name` 列挙値: [ModelKindName.SCD_TYPE_2_BY_TIME](https://sqlmesh.readthedocs.io/en/stable/_readthedocs/html/sqlmesh/core/model/kind.html#ModelKindName)

##### SCD Type 2 By Column

[`SCD_TYPE_2_BY_COLUMN` モデル](../concepts/models/model_kinds.md#scd-type-2) の設定オプション ([一般モデルプロパティ](#general-model-properties)、[増分モデルプロパティ](#incremental-models)、[SCD タイプ 2 プロパティ](#scd-type-2-models) に加えて)。

| オプション | 説明 | タイプ | 必須 |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :---------------: | :------: |
| `columns` | 変更されたデータ値がデータ更新を示す列 (`updated_at` 列ではなく)。`*` はすべての列をチェックする必要があることを表します。 | str \| array[str] | Y |
| `execution_time_as_valid_from` |デフォルトでは、新しい行の `valid_from` は 1970-01-01 00:00:00 に設定されています。これにより、パイプラインが実行された時点の execution_time に設定されるようになります。(デフォルト: `False`) | bool | N |

Python モデルの種類 `name` 列挙値: [ModelKindName.SCD_TYPE_2_BY_COLUMN](https://sqlmesh.readthedocs.io/en/stable/_readthedocs/html/sqlmesh/core/model/kind.html#ModelKindName)

### `SEED` models

[`SEED` モデル](../concepts/models/model_kinds.md#seed) の設定オプション。`SEED` モデルは、他のモデルでサポートされているすべての一般プロパティをサポートしているわけではなく、この表に記載されているプロパティのみをサポートしています。

MODEL DDL 内の最上位オプション:

| オプション | 説明 | タイプ | 必須 |
| ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :--------: | :------: |
| `name` | モデル名。少なくとも修飾スキーマ (`<schema>.<model>`) を含める必要があり、カタログ (`<catalog>.<schema>.<model>`) を含めることもできます。[infer_names](#model-naming) が true に設定されている場合は省略できます。 | str | N |
| `kind` | モデルの種類。`SEED` である必要があります。 | str | Y |
| `columns` | CSV ファイル内の列名とデータ型。pandas CSV リーダーによる列名と型の自動推論を無効にします。注: 列の順序は、CSV ヘッダー行 (存在する場合) で指定された順序よりも優先されます。 | array[str] | N |
| `audits` | モデルの出力に対して実行する SQLMesh [監査](../concepts/audits.md) | array[str] | N |
| `owner` | モデルの所有者。通知目的で使用される場合があります | str | N |
| `stamp` | モデル名を変更せずにモデルのバージョンを示すために使用される任意の文字列 | str | N |
| `tags` | モデルを整理または分類するために使用される任意の文字列 | array[str] | N |
| `description` | モデルの説明。 SQL エンジンのテーブル COMMENT フィールドまたは同等のフィールド (エンジンでサポートされている場合) に自動的に登録されます。 | str | N |

最上位の `kind` プロパティ内で指定されるオプション:

| オプション | 説明 | タイプ | 必須 |
| -------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---- | -------- |
| `path` | シード CSV ファイルへのパス。 | str | Y |
| `batch_size` | 各バッチで取り込まれる CSV 行の最大数。指定されていない場合は、すべての行が 1 つのバッチで取り込まれます。 | int | N |
| `csv_settings` | Pandas CSV リーダー設定 ([デフォルト値](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.read_csv.html) をオーバーライドします)。キーと値のペア (`key = value`) として指定します。 | dict | N |

<a id="csv_settings"></a>
`kind` プロパティの `csv_settings` プロパティ内で指定されたオプション（[Pandas CSV リーダーのデフォルト設定](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.read_csv.html) をオーバーライドします）:

| オプション | 説明 | タイプ | 必須 |
| ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---- | -------- |
| `delimiter` | 区切り文字として扱う文字または正規表現パターン。詳細については、[Pandas のドキュメント](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.read_csv.html)を参照してください。 | str | N |
| `quotechar` | 引用符で囲まれた項目の開始と終了を示すために使用される文字。詳細については、[Pandas のドキュメント](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.read_csv.html)を参照してください。 | str | N |
| `doublequote` | quotechar が指定されている場合、フィールド内にある 2 つの連続する quotechar 要素を 1 つの quotechar 要素として解釈するかどうかを示します。詳細については、[Pandas のドキュメント](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.read_csv.html) を参照してください。 | bool | N |
| `escapechar` | 他の文字をエスケープするために使用される文字。詳細については、[Pandas のドキュメント](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.read_csv.html) を参照してください。 | str | N |
| `skipinitialspace` | 区切り文字の後のスペースをスキップします。詳細については、[Pandas のドキュメント](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.read_csv.html) を参照してください。 | bool | N |
| `lineterminator` | 改行を示すために使用される文字。詳細については、[Pandas のドキュメント](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.read_csv.html) を参照してください。 | str | N |
| `encoding` | 読み取り/書き込み時に UTF に使用するエンコーディング (例: 'utf-8')。詳細については、[Pandas のドキュメント](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.read_csv.html) を参照してください。 | str | N |
| `na_values` | NA/NaN として認識される値の配列。列ごとにこのような配列を指定するには、代わりに `(col1 = (v1, v2, ...), col2 = ...)` という形式のマッピングを渡すことができます。これらの値は、整数、文字列、ブール値、または NULL にすることができ、対応する Python 値に変換されます。詳細については、[Pandas ドキュメント](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.read_csv.html) をご覧ください。 | array[value] \| array[array[key = value]] | N |
| `keep_default_na` | データの解析時にデフォルトの NaN 値を含めるかどうか。詳細については、[Pandas ドキュメント](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.read_csv.html) をご覧ください。 | bool | N |

Python モデルの種類 `name` 列挙値: [ModelKindName.SEED](https://sqlmesh.readthedocs.io/en/stable/_readthedocs/html/sqlmesh/core/model/kind.html#ModelKindName)