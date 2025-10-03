# SQLMesh configuration

このページでは、SQLMesh の設定オプションとそのパラメータの一覧を示します。SQLMesh の設定の詳細については、[設定ガイド](../guides/configuration.md) をご覧ください。

モデル定義の設定オプションについては、[モデル設定リファレンスページ](./model_configuration.md) に記載されています。

## Root configurations

SQLMesh プロジェクト構成は、ルートレベルパラメータで構成され、その中で他のパラメータが定義されます。

重要なルートレベルパラメータとして [`gateways`](#gateways) と [gateway/connection defaults](#gatewayconnection-defaults) の 2 つがあり、それぞれ以下に専用のセクションがあります。

このセクションでは、その他のルートレベル構成パラメータについて説明します。

### Projects

SQLMesh プロジェクト ディレクトリの構成オプション。

| オプション | 説明 | タイプ | 必須 |
| ------------------ | ----------------------------------------------------------------------------------------------------------------------------- | :----------: | :------: |
| `ignore_patterns` | このリストで指定された glob パターンに一致するファイルは、プロジェクト フォルダのスキャン時に無視されます (デフォルト: `[]`) | list[string] | N |
| `project` | この構成のプロジェクト名。[マルチリポジトリ セットアップ](../guides/multi_repo.md) に使用されます。 | string | N |
| `cache_dir` | SQLMesh キャッシュを保存するディレクトリ。絶対パスまたはプロジェクト ディレクトリへの相対パスを指定できます (デフォルト: `.cache`) | string | N |
| `log_limit` | 保持する履歴ログ ファイルのデフォルト数 (デフォルト: `20`) | int | N |

### Database (Physical Layer)

SQLMesh が [物理レイヤー](../concepts/glossary.md#physical-layer) 内のデータベース オブジェクトを管理する方法の構成オプションです。

| オプション | 説明 | タイプ | 必須 |
|------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:--------------------:|:--------:|
| `snapshot_ttl` | どの環境にも属さないモデルのスナップショットが削除されるまでの期間。これは文字列として定義され、デフォルトは `in 1 week` です。`in 30 days` などの他の [相対日付](https://dateparser.readthedocs.io/en/latest/) も使用できます。(デフォルト: `in 1 week`) | 文字列 | N |
| `physical_schema_override` | (非推奨) 代わりに `physical_schema_mapping` を使用してください。モデル スキーマ名から、対応するモデルの物理テーブルが配置されるスキーマ名へのマッピング。 | dict[文字列、文字列] | N |
| `physical_schema_mapping` | 正規表現から、対応するモデルの物理テーブルが配置されるスキーマ名へのマッピング。(デフォルトの物理スキーマ名: `sqlmesh__[モデル スキーマ]`) | dict[文字列、文字列] | N |
| `physical_table_naming_convention`| モデル名のどの部分を物理テーブル名に含めるかを設定します。オプションは `schema_and_table`、`table_only`、または `hash_md5` です - [追加の詳細](../guides/configuration.md#physical-table-naming-convention)。(デフォルト: `schema_and_table`) | 文字列 | N |

### Environments (Virtual Layer)

SQLMesh が [仮想レイヤー](../concepts/glossary.md#virtual-layer) で環境の作成と昇格を管理する方法の構成オプションです。

| オプション | 説明 | タイプ | 必須 |
|------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:--------------------:|:--------:|
| `environment_ttl` | 開発環境が削除されるまでの存続期間。これは文字列として定義され、デフォルトは `in 1 week` です。`in 30 days` などの他の [相対日付](https://dateparser.readthedocs.io/en/latest/) も使用できます。(デフォルト: `in 1 week`) | 文字列 | N |
| `pinned_environments` | 有効期限切れにより削除されない開発環境のリスト | list[string] | N |
| `default_target_environment` | `sqlmesh plan` コマンドと `sqlmesh run` コマンドのデフォルトのターゲットとなる環境の名前。(デフォルト: `prod`) | 文字列 | N |
| `environment_suffix_target` | SQLMesh ビューが `schema`、`table`、または `catalog` に環境名を追加するかどうか - [追加の詳細](../guides/configuration.md#view-schema-override)。(デフォルト: `schema`) | 文字列 | N |
| `gateway_managed_virtual_layer` | 仮想レイヤーの SQLMesh ビューがデフォルト ゲートウェイによって作成されるか、モデルで指定されたゲートウェイによって作成されるか - [追加の詳細](../guides/multi_engine.md#gateway-managed-virtual-layer)。(デフォルト: False) | ブール値 | N |
| `environment_catalog_mapping` | 正規表現からカタログ名へのマッピング。カタログ名は、特定の環境のターゲットカタログを決定するために使用されます。 | dict[string, string] | N |
| `virtual_environment_mode` | 仮想データ環境 (VDE) モードを決定します。`full` に設定すると、VDE は運用環境と開発環境の両方で使用されます。`dev_only` オプションは開発環境でのみ VDE を有効にし、運用環境では仮想レイヤーは使用されず、モデルは元の名前 (つまり、バージョン管理された物理テーブルなし) を使用して直接マテリアライズされます。(デフォルト: `full`) | string | N |

### Models

| オプション | 説明 | タイプ | 必須 |
|------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:--------------------:|:--------:|
| `time_column_format` | すべてのモデル時間列に使用するデフォルトの形式。この時間形式では、[python 形式コード](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes) が使用されます (デフォルト: `%Y-%m-%d`) | 文字列 | N |
| `infer_python_dependencies` | SQLMesh が Python コードを静的に分析して、Python パッケージの要件を自動的に推測するかどうか。(デフォルト: True) | ブール値 | N |
| `model_defaults` | 各モデルに設定するデフォルトの [プロパティ](./model_configuration.md#model-defaults)。少なくとも `dialect` を設定する必要があります。| dict[文字列、任意] | Y |

`model_defaults` キーは **必須** であり、`dialect` キーの値が含まれている必要があります。

`model_defaults` で使用できるすべてのキーについては、[モデル設定リファレンスページ](./model_configuration.md#model-defaults) を参照してください。

### Variables

`variables` キーは、ユーザー定義変数の値を指定するために使用できます。ユーザー定義変数には、SQL モデル定義では [`@VAR` マクロ関数](../concepts/macros/sqlmesh_macros.md#global-variables)、Python モデル定義では [`context.var` メソッド](../concepts/models/python_models.md#global-variables)、Python マクロ関数では [`evaluator.var` メソッド](../concepts/macros/sqlmesh_macros.md#accessing-global-variable-values) を使用してアクセスできます。

`variables` キーは、変数名と値のマッピングで構成されます。[SQLMesh マクロの概念ページ](../concepts/macros/sqlmesh_macros.md#global-variables) の例を参照してください。キーの大文字と小文字は区別されないことに注意してください。

グローバル変数の値は、以下の表のいずれかのデータ型、またはそれらの型を含むリストや辞書にすることができます。

| オプション | 説明 | 型 | 必須 |
|------------|-------------------------------------|:------------------------------------------------------------:|:--------:|
| `variables` | 変数名と値のマッピング | dict[string, int \| float \| bool \| string \| list \| dict] | N |

### Before_all / after_all

`before_all` キーと `after_all` キーは、それぞれ `sqlmesh plan` コマンドと `sqlmesh run` コマンドの開始時と終了時に実行される SQL 文と SQLMesh マクロのリストを指定するために使用できます。詳細と例については、[設定ガイド](../guides/configuration.md#before_all-and-after_all-statements) を参照してください。

| オプション | 説明 | タイプ | 必須 |
|--------------|------------------------------------------------------------------------------------|:------------:|:---------:|
| `before_all` | `plan` コマンドと `run` コマンドの開始時に実行される SQL 文のリスト。| list[string] | N |
| `after_all` | `plan` コマンドと `run` コマンドの終了時に実行される SQL 文のリスト。| list[string] | N |

## Plan

`sqlmesh plan` コマンドの構成。

| オプション | 説明 | タイプ | 必須 |
|--------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:--------------------:|:--------:|
| `auto_categorize_changes` | SQLMesh がプラン作成時にモデルソースタイプごとにモデルの変更を自動的に [分類](../concepts/plans.md#change-categories) するかどうかを示します ([追加の詳細](../guides/configuration.md#auto-categorize-changes)) | dict[文字列、文字列] | N |
| `include_unmodified` | ターゲット開発環境のすべてのモデルに対してビューを作成するか、変更されたモデルに対してのみビューを作成するかを示します (デフォルト: False) | ブール値 | N |
| `auto_apply` |作成後に新しいプランを自動的に適用するかどうかを示します (デフォルト: False) | ブール値 | N |
| `forward_only` | プランを [forward-only](../concepts/plans.md#forward-only-plans) にするかどうかを示します (デフォルト: False) | ブール値 | N |
| `enable_preview` | 開発環境をターゲットにするときに、forward-only モデルの [データ プレビュー](../concepts/plans.md#data-preview) を有効にするかどうかを示します (デフォルト: True、ターゲット エンジンがクローン作成をサポートしていない dbt プロジェクトを除く) | ブール値 | N |
| `no_diff` | 変更されたモデルの差分を表示しません (デフォルト: False) | ブール値 | N |
| `no_prompts` | CLI で対話型プロンプトを無効にします (デフォルト: True) | ブール値 | N |
| `always_recreate_environment` |常に `create_from` で指定された環境 (デフォルトでは `prod`) からターゲット環境を再作成します (デフォルト: False) | ブール値 | N |

## Run

`sqlmesh run` コマンドの構成。これは、[組み込み](#builtin) スケジューラが構成されている場合にのみ適用されます。

| オプション | 説明 | タイプ | 必須 |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------ | :--: | :------: |
| `environment_check_interval` | ターゲット環境の準備状況を確認する試行間隔の秒数 (デフォルト: 30 秒) | int | N |
| `environment_check_max_wait` | ターゲット環境の準備完了を待機する最大秒数 (デフォルト: 6 時間) | int | N |

## Format

`sqlmesh format` コマンドと UI のフォーマット設定。

| オプション | 説明 | タイプ | 必須 |
| --------------------- | ------------------------------------------------------------------------------------------------ | :-----: | :------: |
| `normalize` | SQL を正規化するかどうか (デフォルト: False) | ブール値 | N |
| `pad` | パディングに使用するスペースの数 (デフォルト: 2) | int | N |
| `indent` | インデントに使用するスペースの数 (デフォルト: 2) | int | N |
| `normalize_functions` | 関数名を正規化するかどうか。サポートされる値は 'upper' と 'lower' です (デフォルト: なし) | 文字列 | N |
| `leading_comma` | 先頭のカンマを使用するかどうか (デフォルト: False) | ブール値 | N |
| `max_text_width` |改行を作成する前のセグメント内の最大テキスト幅 (デフォルト: 80) | int | N |
| `append_newline` | ファイルの末尾に改行を追加するかどうか (デフォルト: False) | boolean | N |
| `no_rewrite_casts` | :: 構文を使用するように書き換えずに、既存のキャストを保持します。 (デフォルト: False) | boolean | N |


## Janitor

`sqlmesh janitor` コマンドの設定。

| オプション | 説明 | タイプ | 必須 |
|-------------------------|----------------------------------------------------------------------------------------------------------------------------------------------|:-------:|:--------:|
| `warn_on_delete_failure` | janitor が期限切れの環境スキーマ/ビューの削除に失敗した場合、エラーではなく警告を表示するかどうか (デフォルト: False) | ブール値 | N |

## UI

SQLMesh UI 設定。

| オプション | 説明 | タイプ | 必須 |
| ---------------- | ----------------------------------------------------------------------------------------------- | :-----: | :------: |
| `format_on_save` | モデル定義をファイルに保存するときに自動的にフォーマットするかどうか (デフォルト: False) | ブール値 | N |

## Gateways

`gateways` ディクショナリは、SQLMesh がデータウェアハウス、状態バックエンド、テストバックエンド、およびスケジューラに接続する方法を定義します。

このディクショナリは、1 つ以上の名前付き `gateway` 構成キーを受け取ります。各キーは独自の接続を定義できます。**ゲートウェイ名は大文字と小文字を区別しません** - SQLMesh は構成検証中にすべてのゲートウェイ名を小文字に正規化するため、ゲートウェイを参照する際には大文字と小文字を自由に使用できます。名前付きゲートウェイでは、4 つのコンポーネントすべてを指定する必要はなく、いずれかが省略された場合はデフォルトが使用されます。[ゲートウェイのデフォルト](#gatewayconnection-defaults) の詳細については、以下を参照してください。

例えば、プロジェクトで `gate1` ゲートウェイと `gate2` ゲートウェイを構成するとします。

```yaml linenums="1"
gateways:
  gate1:
    connection:
      ...
    state_connection: # defaults to `connection` if omitted
      ...
    test_connection: # defaults to `connection` if omitted
      ...
    scheduler: # defaults to `builtin` if omitted
      ...
  gate2:
    connection:
      ...
```

ゲートウェイに関する追加情報については、構成ガイドの [ゲートウェイ セクション](../guides/configuration.md#gateways) を参照してください。

### Gateway

名前付きゲートウェイごとの構成。

#### Connections

名前付きゲートウェイキーは、データウェアハウス接続、状態バックエンド接続、状態スキーマ名、テストバックエンド接続、およびスケジューラのいずれかまたはすべてを定義できます。

一部の接続では、指定されていない場合はデフォルト値が使用されます。

- [`default_connection`](#default-connectionsscheduler) が指定されている場合、`connection` キーは省略できます。
- 状態接続は省略された場合、デフォルトで `connection` になります。
- テスト接続は省略された場合、デフォルトで `connection` になります。

注: Spark エンジンと Trino エンジンは、状態接続には使用できません。

| オプション | 説明 | タイプ | 必須 |
|--------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:------------------------------------------------------------:|:----------------------------------------------------------------------:|
| `connection` | コア SQLMesh 関数のデータウェアハウス接続。| [接続構成](#connection) | N ([`default_connection`](#default-connectionsscheduler) が指定されている場合) |
| `state_connection` | SQLMesh がプロジェクトに関する内部情報を保存するデータ ウェアハウス接続。(デフォルト: 組み込みスケジューラを使用する場合は `connection`、それ以外の場合はスケジューラ データベース) | [接続構成](#connection) | N |
| `state_schema` | 状態情報を保存するスキーマの名前。(デフォルト: `sqlmesh`) | 文字列 | N |
| `test_connection` | SQLMesh がテスト実行に使用するデータ ウェアハウス接続。(デフォルト: `connection`) | [接続構成](#connection) | N |
| `scheduler` | SQLMesh がテスト実行に使用するスケジューラ。(デフォルト: `builtin`) | [スケジューラ構成](#scheduler) | N |
| `variables` | ルートレベルの [variables](#variables) をキーによってオーバーライドするゲートウェイ固有の変数。| dict[string, int \| float \| bool \| 文字列 \| リスト \| 辞書] | N |

### Connection

データウェアハウス接続の設定。

ほとんどのパラメータは接続エンジンの `type` に固有です。[下記](#エンジン固有) を参照してください。デフォルトのデータウェアハウス接続タイプは、インメモリ DuckDB データベースです。

#### General

| オプション | 説明 | タイプ | 必須 |
|---------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:----:|:--------:|
| `type` | エンジン タイプ名。以下のエンジン固有の設定ページにリストされています。 | str | Y |
| `concurrent_tasks` | SQLMesh によって実行される同時タスクの最大数。(同時タスクをサポートするエンジンの場合、デフォルト: 4) | int | N |
| `register_comments` | SQLMesh がモデル コメントを SQL エンジンに登録するかどうか (エンジンがサポートしている場合)。(デフォルト: `true`) | bool | N |
| `pre_ping` | 新しいトランザクションを開始する前に、接続がまだ有効であることを確認するために、接続を事前に ping するかどうか。これは、トランザクションをサポートするエンジンでのみ有効にできます。 | bool | N |
| `pretty_sql` |実行前に SQL をフォーマットする必要がある場合、実稼働環境では推奨されません。(デフォルト: `false`) | bool | N |

#### Engine-specific

これらのページでは、各実行エンジンの接続構成オプションについて説明します。

* [Athena](../integrations/engines/athena.md)
* [BigQuery](../integrations/engines/bigquery.md)
* [ClickHouse](../integrations/engines/clickhouse.md)
* [Databricks](../integrations/engines/databricks.md)
* [DuckDB](../integrations/engines/duckdb.md)
* [MotherDuck](../integrations/engines/motherduck.md)
* [MySQL](../integrations/engines/mysql.md)
* [MSSQL](../integrations/engines/mssql.md)
* [Postgres](../integrations/engines/postgres.md)
* [GCP Postgres](../integrations/engines/gcp-postgres.md)
* [Redshift](../integrations/engines/redshift.md)
* [Snowflake](../integrations/engines/snowflake.md)
* [Spark](../integrations/engines/spark.md)
* [Trino](../integrations/engines/trino.md)

### Scheduler

使用するスケジューラバックエンドを指定します。スケジューラバックエンドは、メタデータの保存と[プラン](../concepts/plans.md)の実行の両方に使用されます。

デフォルトでは、スケジューラタイプは「builtin」に設定され、ゲートウェイ接続を使用してメタデータを保存します。

以下は、対応する各スケジューラタイプに固有の設定オプションの一覧です。詳細については、[設定の概要](../guides/configuration.md#scheduler)のスケジューラセクションをご覧ください。

#### Builtin

**Type:** `builtin`

このスケジューラ タイプでは構成オプションはサポートされていません。

## Gateway/connection defaults

デフォルトゲートウェイと接続キーは、ゲートウェイまたは接続が明示的に指定されていない場合の動作を指定します。詳細は、構成の概要ページ[ゲートウェイ/接続のデフォルト設定セクション](../guides/configuration.md#gatewayconnection-defaults)をご覧ください。

### Default gateway

構成に複数のゲートウェイが含まれている場合、SQLMesh はデフォルトで `gateways` ディクショナリの最初のゲートウェイを使用します。`default_gateway` キーは、SQLMesh のデフォルトとして別のゲートウェイ名を指定するために使用されます。

| オプション | 説明 | タイプ | 必須 |
| ----------------- | -------------------------------------------------------------------------------------------------------------------------------- | :----: | :------: |
| `default_gateway` | ゲートウェイ名が明示的に指定されていない場合に使用するゲートウェイの名前 (デフォルト: `gateways` オプションで最初に定義されたゲートウェイ)。ゲートウェイ名は大文字と小文字を区別しません。 | 文字列 | N |

### Default connections/scheduler

`default_connection`、`default_test_connection`、および `default_scheduler` キーは、複数のゲートウェイ間で共有されるデフォルトを指定するために使用されます。

例えば、どのゲートウェイが使用されているかに関係なく、テストを実行する特定の接続があるとします。各ゲートウェイの指定でテスト接続情報を重複させるのではなく、`default_test_connection` キーで 1 回だけ指定します。

| オプション | 説明 | タイプ | 必須 |
| ------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | :---------: | :------: |
| `default_connection` | ゲートウェイで指定されていない場合に使用するデフォルトの接続 (デフォルト: インメモリデータベースを作成する DuckDB 接続) | 接続 | N |
| `default_test_connection` |ゲートウェイで指定されていない場合にテストを実行するときに使用するデフォルトの接続 (デフォルト: メモリ内データベースを作成する DuckDB 接続) | connection | N |
| `default_scheduler` | ゲートウェイで指定されていない場合に使用するデフォルトのスケジューラ構成 (デフォルト: 組み込みスケジューラ) | scheduler | N |

## Debug mode

デバッグモードを有効にするには、以下の2つの方法があります。

- CLIコマンドとサブコマンドの間に `--debug` フラグを渡します。例：`sqlmesh --debug plan`。
- `SQLMESH_DEBUG` 環境変数を、"1"、"true"、"t"、"yes"、"y" のいずれかの値に設定します。

このモードを有効にすると、CLI使用時に完全なバックトレースが出力されるようになります。このモードを有効にすると、デフォルトのログレベルは `DEBUG` に設定されます。

CLIコマンド `sqlmesh plan` でデバッグモードを有効にする例：

=== "Bash"

    ```bash
    $ sqlmesh --debug plan
    ```

    ```bash
    $ SQLMESH_DEBUG=1 sqlmesh plan
    ```

=== "MS Powershell"

    ```powershell
    PS> sqlmesh --debug plan
    ```

    ```powershell
    PS> $env:SQLMESH_DEBUG=1
    PS> sqlmesh plan
    ```

=== "MS CMD"

    ```cmd
    C:\> sqlmesh --debug plan
    ```

    ```cmd
    C:\> set SQLMESH_DEBUG=1
    C:\> sqlmesh plan
    ```

## Runtime Environment

SQLMesh はさまざまなランタイム環境で実行できます。例えば、通常のコマンドラインターミナル、Jupyter Notebook、あるいは Github の CI/CD プラットフォームで実行できます。

SQLMesh は起動時に自動的にランタイム環境を検出し、それに応じて動作を調整します。例えば、Jupyter Notebook の場合は `%magic` コマンドを登録し、CI/CD 環境の場合はログ出力の動作を調整します。

必要に応じて、`SQLMESH_RUNTIME_ENVIRONMENT` 環境変数を設定することで、SQLMesh が特定のランタイム環境を使用するように強制できます。

以下の値を受け入れることで、SQLMesh は括弧内のランタイム環境にあるかのように動作します。

- `terminal` (CLI コンソール)
- `databricks` (Databricks ノートブック)
- `google_colab` (Google Colab ノートブック)
- `jupyter` (Jupyter ノートブック)
- `debugger` (デバッグ出力)
- `ci` (CI/CD またはその他の非対話型環境)

## Anonymized usage information

私たちは、SQLMesh を市場で最高のデータ変換ツールにすることを目指しています。その実現に向けて、バグ修正、機能追加、そして SQLMesh のパフォーマンス向上に継続的に取り組んでいます。

SQLMesh ユーザーのニーズに基づいて開発作業を優先順位付けしています。Slack や Github コミュニティでニーズを共有してくださっているユーザーもいますが、そうでないユーザーも少なくありません。すべてのユーザーのニーズに応えられるよう、SQLMesh にシンプルな匿名の使用状況情報（テレメトリ）を追加しました。

すべての情報はハッシュ関数によって匿名化されるため、たとえ望んでも（望んではいませんが）、データを特定の企業、ユーザー、またはプロジェクトにリンクすることはできません。資格情報や認証に関連する情報は一切収集しません。

SQLMesh プロジェクトの複雑さと使用状況に関する匿名情報を収集します。たとえば、モデル数、モデルの種類数、プロジェクトの読み込み時間、プラン/実行中にエラーが発生したかどうか（スタックトレースやエラーメッセージは含みません）、CLI コマンドに渡される引数の名前（値は含みません）などです。

匿名化された使用状況情報の収集を無効にするには、以下の方法があります。

- SQLMesh プロジェクト設定ファイルのルートキー「disable_anonymized_analytics: true」を設定します。
- 環境変数「SQLMESH__DISABLE_ANONYMIZED_ANALYTICS」を「1」、「true」、「t」、「yes」、または「y」に設定して、SQLMesh コマンドを実行します。

## Parallel loading
SQLMesh は、モデルとスナップショットをロードする際にデフォルトですべてのコアを使用します。Windows では利用できない `fork` を利用します。デフォルトでは、fork が利用可能な場合、マシン上のコア数と同じ数のワーカーを使用します。

この設定は、環境変数 `MAX_FORK_WORKERS` を設定することで上書きできます。値を 1 にすると、fork は無効になり、順番にロードされます。
