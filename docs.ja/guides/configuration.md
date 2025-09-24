# 設定ガイド

SQLMesh の動作は、プロジェクトのファイル（例：モデル）、ユーザーアクション（例：プランの作成）、そして SQLMesh の設定という 3 つの要素によって決まります。

このページでは、SQLMesh の設定の仕組みと、設定によって変更できる SQLMesh の動作について説明します。

[設定リファレンスページ](../reference/configuration.md) には、すべての設定パラメータとそのデフォルト値の簡潔なリストが記載されています。

## 設定ファイル

**注:** SQLMesh プロジェクトの設定には、以下の 2 つの要件があります。

1. プロジェクトフォルダに `config.yaml` ファイルまたは `config.py` ファイルが存在する必要があります。
2. この設定ファイルの [`model_defaults` `dialect` キー](#models) に、プロジェクトのモデルのデフォルトの SQL 方言が含まれている必要があります。

SQLMesh の設定パラメータは、環境変数、`~/.sqlmesh` フォルダ内の設定ファイル、またはプロジェクトフォルダ内の設定ファイルで設定できます。

設定ファイルの優先順位は次のとおりです。

1. 環境変数 (例: `SQLMESH__MODEL_DEFAULTS__DIALECT`) [最優先]
2. `~/.sqlmesh` フォルダ内の `config.yaml` または `config.py`
3. プロジェクトフォルダ内の `config.yaml` または `config.py` [最低優先順位]

### ファイルタイプ

SQLMesh の設定は、YAML または Python で指定できます。

YAML 設定はよりシンプルで、ほとんどのプロジェクトで推奨されます。Python 設定はより複雑ですが、YAML ではサポートされていない機能を有効にできます。

Python 設定ファイルは、SQLMesh が読み取る際に Python によって評価されるため、SQLMesh が実行される計算環境に基づいた動的なパラメータをサポートします。

例えば、Python 設定ファイルを使用すると、パスワードなどの機密情報を保存するためにサードパーティ製のシークレットマネージャーを使用できます。また、SQLMesh を実行しているユーザーアカウントに基づいてプロジェクトのデフォルトを自動的に設定するなど、ユーザー固有のパラメータもサポートされます。

#### YAML

YAML 設定ファイルは、設定キーと値で構成されます。文字列は引用符で囲まれておらず、一部のキーは1つ以上のサブキーを含む「辞書」です。

例えば、`default_gateway` キーは、SQLMesh がコマンド実行時に使用するデフォルトゲートウェイを指定します。値として、引用符で囲まれていない単一のゲートウェイ名を指定します。

```yaml linenums="1"
default_gateway: local
```

対照的に、`gateways` キーは辞書を値として受け取り、各ゲートウェイ辞書には1つ以上の接続辞書が含まれます。この例では、Snowflake の `connection` を使用して `my_gateway` ゲートウェイを指定しています。

```yaml linenums="1"
gateways:
  my_gateway:
    connection:
      type: snowflake
      user: <username>
      password: <password>
      account: <account>
```

異なるSQLMeshコンポーネントが異なる接続を使用する必要がある場合（例：SQLMeshの`test`はSQLMeshの`plan`とは異なるデータベースで実行する必要がある場合）、ゲートウェイ辞書には複数の接続辞書を含めることができます。ゲートウェイ設定の詳細については、[ゲートウェイセクション](#gateways)を参照してください。

#### Python

Python 構成ファイルは、SQLMesh 構成クラスをインポートするステートメントと、それらのクラスを使用する構成仕様で構成されます。

Python 構成ファイルには、少なくとも以下の内容が必要です。

1. SQLMesh の `Config` クラスの `config` という名前のオブジェクトを作成します。
2. そのオブジェクトの `model_defaults` 引数に、プロジェクトのモデルのデフォルトの SQL 方言を指定する `ModelDefaultsConfig()` オブジェクトを指定します。

例えば、以下の最小限の構成では、デフォルトの SQL 方言として `duckdb` を指定し、その他のすべての構成パラメータにはデフォルト値を使用します。

```python linenums="1"
from sqlmesh.core.config import Config, ModelDefaultsConfig

config = Config(
    model_defaults=ModelDefaultsConfig(dialect="duckdb"),
)
```

Python 構成ファイルでは、オプションで追加の構成オブジェクトを定義し、`sqlmesh` コマンドの実行時に構成を切り替えることができます。たとえば、構成ファイルに 2 番目の構成オブジェクト `my_second_config` が含まれている場合、`sqlmesh --config my_second_config plan` でその構成を使用したプランを作成できます。

`Config` 引数はそれぞれ異なるオブジェクト型を受け入れます。`model_defaults` など、SQLMesh 構成オブジェクトを受け入れるものもあれば、`default_gateway` など、文字列や辞書などの他の Python オブジェクト型を受け入れるものもあります。

SQLMesh の Python 構成コンポーネントについては、`sqlmesh.core.config` モジュールの [API ドキュメント](https://sqlmesh.readthedocs.io/en/latest/_readthedocs/html/sqlmesh/core/config.html) に記載されています。

`config` サブモジュールの API ドキュメントでは、関連する `Config` 引数に使用される個々のクラスについて説明しています。

- [モデルのデフォルト設定](https://sqlmesh.readthedocs.io/en/latest/_readthedocs/html/sqlmesh/core/config/model.html): `ModelDefaultsConfig()`
- [ゲートウェイ設定](https://sqlmesh.readthedocs.io/en/latest/_readthedocs/html/sqlmesh/core/config/gateway.html): `GatewayConfig()`
- [接続設定](https://sqlmesh.readthedocs.io/en/latest/_readthedocs/html/sqlmesh/core/config/connection.html) (サポートされているデータベース/エンジンごとに個別のクラス)
- [スケジューラ設定](https://sqlmesh.readthedocs.io/en/latest/_readthedocs/html/sqlmesh/core/config/scheduler.html) (サポートされるスケジューラごとに個別のクラス)
- [プラン変更の分類設定](https://sqlmesh.readthedocs.io/en/latest/_readthedocs/html/sqlmesh/core/config/categorizer.html#CategorizerConfig): `CategorizerConfig()`
- [ユーザー設定](https://sqlmesh.readthedocs.io/en/latest/_readthedocs/html/sqlmesh/core/user.html#User): `User()`
- [通知設定](https://sqlmesh.readthedocs.io/en/latest/_readthedocs/html/sqlmesh/core/notification_target.html) (通知対象ごとに個別のクラス)

ユーザーと通知の仕様の詳細については、[通知ガイド](../guides/notifications.md) を参照してください。

## 環境変数

すべてのソフトウェアは、情報を「環境変数」として保存するシステム環境内で実行されます。

SQLMesh は設定時に環境変数にアクセスできるため、パスワードやシークレットを構成ファイルの外部に保存したり、SQLMesh を実行しているユーザーに基づいて構成パラメータを動的に変更したりといったアプローチが可能になります。

環境変数は、構成ファイルで指定するか、`.env` ファイルに保存することで指定できます。

### .env ファイル

SQLMesh は、プロジェクトディレクトリ内の `.env` ファイルから環境変数を自動的に読み込みます。これにより、シェルで環境変数を設定する必要がなくなり、環境変数を簡単に管理できます。

プロジェクトルートに、キーと値のペアを含む `.env` ファイルを作成します。

```bash
# .env file
SNOWFLAKE_PW=my_secret_password
S3_BUCKET=s3://my-data-bucket/warehouse
DATABASE_URL=postgresql://user:pass@localhost/db

# Override specific SQLMesh configuration values
SQLMESH__DEFAULT_GATEWAY=production
SQLMESH__MODEL_DEFAULTS__DIALECT=snowflake
```

これらの定義方法の詳細については、[オーバーライド](#overrides) セクションを参照してください。

`.env` ファイルの残りの変数は、YAML では `{{ env_var('VARIABLE_NAME') }}` 構文を使用して設定ファイルで使用するか、Python では `os.environ['VARIABLE_NAME']` を介してアクセスできます。

#### カスタム dot env ファイルの場所と名前

デフォルトでは、SQLMesh は各プロジェクトディレクトリから `.env` ファイルを読み込みます。ただし、コマンド実行時に `--dotenv` CLI フラグを使用して、カスタムパスを直接指定することもできます。

```bash
sqlmesh --dotenv /path/to/custom/.env plan
```

!!! note
    `--dotenv` フラグはグローバル オプションであり、サブコマンド (例: `plan`、`run`) の後ではなく **前** に配置する必要があります。

あるいは、`SQLMESH_DOTENV_PATH` 環境変数を 1 回エクスポートして、シェル セッション内の後続のすべてのコマンドにわたってカスタム パスを保持することもできます。

```bash
export SQLMESH_DOTENV_PATH=/path/to/custom/.custom_env
sqlmesh plan
sqlmesh run
```

**重要な考慮事項:**

- 機密情報のコミットを避けるため、`.gitignore` ファイルに `.env` を追加してください。
- SQLMesh は、プロジェクトディレクトリ内に `.env` ファイルが存在する場合のみそれを読み込みます（カスタムパスが指定されている場合を除く）。
- カスタムパスを使用する場合、そのファイルはプロジェクトディレクトリ内のどの `.env` ファイルよりも優先されます。

### 設定ファイル

このセクションでは、YAML および Python 設定ファイルで環境変数を使用する方法を説明します。

例では、パスワードが環境変数 `SNOWFLAKE_PW` に保存されている Snowflake 接続を指定します。

=== "YAML"

    YAML 構成では、`{{ env_var('<環境変数名>') }}` という構文を使用して環境変数を指定します。環境変数名は一重引用符で囲むことに注意してください。

    Snowflake 接続構成で `SNOWFLAKE_PW` 環境変数にアクセスするには、次のようにします。

    ```yaml linenums="1"
    gateways:
      my_gateway:
        connection:
          type: snowflake
          user: <username>
          password: {{ env_var('SNOWFLAKE_PW') }}
          account: <account>
    ```

=== "Python"

    Python は、`os` ライブラリの `environ` ディクショナリを介して環境変数にアクセスします。

    Snowflake 接続設定で `SNOWFLAKE_PW` 環境変数にアクセスするには、次のようにします。

    ```python linenums="1"
    import os
    from sqlmesh.core.config import (
        Config,
        ModelDefaultsConfig,
        GatewayConfig,
        SnowflakeConnectionConfig
    )

    config = Config(
        model_defaults=ModelDefaultsConfig(dialect=<dialect>),
        gateways={
            "my_gateway": GatewayConfig(
                connection=SnowflakeConnectionConfig(
                    user=<username>,
                    password=os.environ['SNOWFLAKE_PW'],
                    account=<account>,
                ),
            ),
        }
    )
    ```

#### デフォルトのターゲット環境

SQLMesh の `plan` コマンドは、デフォルトで `prod` 環境で動作します（つまり、`sqlmesh plan` は `sqlmesh plan prod` と同等です）。

組織によっては、ユーザーが `prod` に対して直接プランを実行することはなく、SQLMesh のすべての作業を各自の開発環境で実行している場合があります。標準的な SQLMesh 構成では、`plan` コマンドを実行するたびに開発環境名を指定する必要があります（例: `sqlmesh plan dev_tony`）。

組織がこのような状況にある場合、`plan` コマンドのデフォルト環境を `prod` から各ユーザーの開発環境に変更すると便利です。そうすれば、ユーザーは毎回環境名を入力しなくても `sqlmesh plan` を実行できます。

SQLMesh 構成の `user()` 関数は、現在ログインして SQLMesh を実行しているユーザー名を返します。ユーザー名は、MacOS/Linux では `USER`、Windows では `USERNAME` などのシステム環境変数から取得します。

`user()` は、Jinja の中括弧内で `{{ user() }}` という構文で呼び出します。これにより、ユーザー名にプレフィックスまたはサフィックスを付けることができます。

以下の設定例では、文字列 `dev_` の末尾にユーザー名を追加することで環境名を構築します。SQLMesh を実行しているユーザーが `tony` の場合、SQLMesh 実行時のデフォルトのターゲット環境は `dev_tony` になります。つまり、`sqlmesh plan` は `sqlmesh plan dev_tony` と同じになります。

=== "YAML"

    デフォルトのターゲット環境は、SQLMesh を実行しているユーザー名と組み合わせた `dev_` です。

    ```yaml
    default_target_environment: dev_{{ user() }}
    ```

=== "Python"

    デフォルトのターゲット環境は、SQLMesh を実行しているユーザー名と組み合わせた `dev_` です。

    `getpass.getuser()` 関数を使用してユーザー名を取得し、それを Python f 文字列で `dev_` と組み合わせます。

    ```python linenums="1" hl_lines="1 17"
    import getpass
    import os
    from sqlmesh.core.config import (
        Config,
        ModelDefaultsConfig,
        GatewayConfig,
        SnowflakeConnectionConfig
    )

    config = Config(
        model_defaults=ModelDefaultsConfig(dialect="duckdb"),
        gateways={
            "my_gateway": GatewayConfig(
                connection=DuckDBConnectionConfig(),
            ),
        },
        default_target_environment=f"dev_{getpass.getuser()}",
    )
    ```

### オーバーライド

[上記](#configuration-files) で述べたように、環境変数は設定方法の中で最も高い優先順位を持ちます。特定の命名構造に従っている場合、環境変数は設定ファイルの仕様を自動的にオーバーライドします。

命名構造は設定フィールド名に基づいており、フィールド名とフィールド名は二重のアンダースコア `__` で区切られます。環境変数名は `SQLMESH__` で始まり、その後にルートから階層を下に向かって YAML フィールド名が続く必要があります。

例えば、Snowflake 接続で指定されたパスワードをオーバーライドできます。設定ファイルに含まれる YAML 仕様は次のとおりです。ここではパスワード `dummy_pw` が指定されています。

```yaml linenums="1"
gateways:
  my_gateway:
    connection:
      type: snowflake
      user: <username>
      password: dummy_pw
      account: <account>
```

環境変数を作成することで、`dummy_pw` の値を実際のパスワード `real_pw` で上書きできます。以下の例は、bash の `export` 関数を使って変数を作成する方法を示しています。

```bash
$ export SQLMESH__GATEWAYS__MY_GATEWAY__CONNECTION__PASSWORD="real_pw"
```

最初の文字列 `SQLMESH__` の後、環境変数名のコンポーネントは、YAML 仕様のキー階層を下に移動します: `GATEWAYS` --> `MY_GATEWAY` --> `CONNECTION` --> `PASSWORD`。

## 構成の種類

SQLMesh プロジェクト構成は階層構造になっており、ルートレベルのパラメータで構成され、その中で他のパラメータが定義されます。

概念的には、ルートレベルのパラメータは以下の種類に分類できます。各種類は、[SQLMesh 構成リファレンス ページ](../reference/configuration.md) のパラメータ一覧表にリンクされています。

1. [プロジェクト](../reference/configuration.md#projects) - SQLMesh プロジェクト ディレクトリの構成オプション。
2. [環境](../reference/configuration.md#environments) - SQLMesh 環境の作成/昇格、物理テーブル スキーマ、およびビュー スキーマの構成オプション。
3. [ゲートウェイ](../reference/configuration.md#gateways) - SQLMesh がデータ ウェアハウス、状態バックエンド、およびスケジューラに接続する方法の構成オプション。
4. [ゲートウェイ/接続のデフォルト](../reference/configuration.md#gatewayconnection-defaults) - ゲートウェイまたは接続がすべて明示的に指定されていない場合の動作に関する構成オプション。
5. [モデルのデフォルト](../reference/model_configuration.md) - モデル固有の構成がモデルのファイルで明示的に指定されていない場合の動作に関する構成オプション。
6. [デバッグモード](../reference/configuration.md#debug-mode) - SQLMesh がアクションと完全なバックトレースを出力およびログに記録するための構成オプション。

## 設定の詳細

このページの残りの部分では、いくつかの設定オプションについてさらに詳しく説明し、簡単な例を示します。設定オプションの包括的なリストは、[設定リファレンスページ](../reference/configuration.md) をご覧ください。

### キャッシュディレクトリ

デフォルトでは、SQLMesh キャッシュはプロジェクトフォルダ内の `.cache` ディレクトリに保存されます。`cache_dir` 設定オプションを使用して、キャッシュの場所をカスタマイズできます。

=== "YAML"

    ```yaml linenums="1"
    # Relative path to project directory
    cache_dir: my_custom_cache

    # Absolute path
    cache_dir: /tmp/sqlmesh_cache

    ```

=== "Python"

    ```python linenums="1"
    from sqlmesh.core.config import Config, ModelDefaultsConfig

    config = Config(
        model_defaults=ModelDefaultsConfig(dialect="duckdb"),
        cache_dir="/tmp/sqlmesh_cache",
    )
    ```

キャッシュディレクトリが存在しない場合は自動的に作成されます。`sqlmesh clean` コマンドを使用してキャッシュをクリアできます。

### テーブル/ビューの保存場所

SQLMesh は、データウェアハウス/エンジン内にスキーマ、物理テーブル、およびビューを作成します。SQLMesh がスキーマを作成する理由と方法の詳細については、[「SQLMesh はなぜスキーマを作成するのですか？」FAQ](../faq/faq.md#schema-question) をご覧ください。

FAQ に記載されている SQLMesh のデフォルトの動作はほとんどのデプロイメントに適していますが、`physical_schema_mapping`、`environment_suffix_target`、および `environment_catalog_mapping` 構成オプションを使用して、SQLMesh が物理テーブルとビューを作成する場所をオーバーライドできます。

また、`physical_table_naming_convention` オプションを使用して、物理テーブルの命名規則をオーバーライドすることもできます。

これらのオプションは、構成リファレンスページの [environments](../reference/configuration.md#environments) セクションにあります。

#### 物理テーブルスキーマ

デフォルトでは、SQLMesh は `sqlmesh__[モデルスキーマ]` という命名規則を使用してモデルの物理スキーマを作成します。

`physical_schema_mapping` オプションを使用すると、スキーマごとにこのスキーマをオーバーライドできます。このオプションは、`sqlmesh__` プレフィックスを削除し、指定した [正規表現パターン](https://docs.python.org/3/library/re.html#regular-expression-syntax) を使用して、モデルで定義されたスキーマを対応する物理スキーマにマッピングします。

この構成例では、`my_schema` モデルスキーマと、`dev` で始まるすべてのモデルスキーマのデフォルトの物理スキーマをオーバーライドします。

=== "YAML"

    ```yaml linenums="1"
    physical_schema_mapping:
      '^my_schema$': my_new_schema,
      '^dev.*': development
    ```

=== "Python"

    ```python linenums="1"
    from sqlmesh.core.config import Config, ModelDefaultsConfig

    config = Config(
        model_defaults=ModelDefaultsConfig(dialect=<dialect>),
        physical_schema_mapping={
            "^my_schema$": "my_new_schema",
            '^dev.*': "development"
        },
    )
    ```

この設定により、以下のマッピング動作が発生します。

| モデル名 | デフォルトの物理位置 | 解決された物理位置|
| --------------------- | ----------------------------------------- | ------------------------------------ |
| `my_schema.my_table`  | `sqlmesh__my_schema.table_<fingerprint>`  | `my_new_schema.table_<fingerprint>`  |
| `dev_schema.my_table` | `sqlmesh__dev_schema.table_<fingerprint>` | `development.table_<fingerprint>`    |
| `other.my_table`      | `sqlmesh__other.table_<fingerprint>`      | `sqlmesh__other.table_<fingerprint>` |


これは、SQLMesh が作成する _物理テーブル_ にのみ適用されます。ビューは引き続き `my_schema` (prod) または `my_schema__<env>` に作成されます。

#### 環境固有のスキーマを無効にする

SQLMesh は、`prod` 環境のビューをモデル名のスキーマに保存します。たとえば、モデル `my_schema.users` の `prod` ビューは `my_schema` に配置されます。

デフォルトでは、SQLMesh は非本番環境の場合、モデル名のスキーマに環境名を追加した新しいスキーマを作成します。たとえば、デフォルトでは、SQLMesh 環境 `dev` にあるモデル `my_schema.users` のビューは、スキーマ `my_schema__dev` に `my_schema__dev.users` として配置されます。

##### 代わりにテーブルレベルで表示

この動作は、テーブル/ビュー名の末尾にサフィックスを追加するように変更できます。テーブル/ビュー名にサフィックスを追加すると、非本番環境のビューが `prod` 環境と同じスキーマに作成されます。本番環境と非本番環境のビューは、非本番環境のビュー名が `__<env>` で終わることで区別されます。

例えば、`my_schema.users` というモデルを含むプロジェクトに `dev` 環境を作成した場合、モデルビューはデフォルトの動作である `my_schema__dev.users` ではなく、`my_schema.users__dev` として作成されます。

設定例:

=== "YAML"

    ```yaml linenums="1"
    environment_suffix_target: table
    ```

=== "Python"

    Python の `environment_suffix_target` 引数は、`EnvironmentSuffixTarget.TABLE`、`EnvironmentSuffixTarget.CATALOG`、または `EnvironmentSuffixTarget.SCHEMA` (デフォルト) の値を持つ `EnvironmentSuffixTarget` 列挙を取ります。

    ```python linenums="1"
    from sqlmesh.core.config import Config, ModelDefaultsConfig, EnvironmentSuffixTarget

    config = Config(
        model_defaults=ModelDefaultsConfig(dialect=<dialect>),
        environment_suffix_target=EnvironmentSuffixTarget.TABLE,
    )
    ```

!!! info "デフォルトの動作"
    スキーマにサフィックスを追加するデフォルトの動作は、ビューにアクセスするための単一のクリーンなインターフェースを本番環境で使用できるため、推奨されます。ただし、スキーマ作成に厳しい制限がある環境にSQLMeshを導入する場合、これはSQLMeshが使用するスキーマの数を減らすのに役立つ場合があります。

##### 代わりにカタログレベルで表示

スキーマ（デフォルト）とテーブルレベルのどちらもユースケースに十分でない場合は、代わりにカタログレベルで環境を指定できます。

これは、下流の BI レポートツールがあり、レポートクエリ内のすべてのテーブル/スキーマ参照の名前を変更せずに、開発環境でそれらをテストしたい場合に便利です。

これを実現するには、[environment_suffix_target](../reference/configuration.md#environments) を次のように設定します。

=== "YAML"

    ```yaml linenums="1"
    environment_suffix_target: catalog
    ```

=== "Python"

    Python の `environment_suffix_target` 引数は、`EnvironmentSuffixTarget.TABLE`、`EnvironmentSuffixTarget.CATALOG`、または `EnvironmentSuffixTarget.SCHEMA` (デフォルト) の値を持つ `EnvironmentSuffixTarget` 列挙を取ります。

    ```python linenums="1"
    from sqlmesh.core.config import Config, ModelDefaultsConfig, EnvironmentSuffixTarget

    config = Config(
        model_defaults=ModelDefaultsConfig(dialect=<dialect>),
        environment_suffix_target=EnvironmentSuffixTarget.CATALOG,
    )
    ```

`my_schema.users` というモデルで、デフォルトカタログが `warehouse` の場合、以下の動作が発生します。

- `prod` 環境では、ゲートウェイで設定されたデフォルトカタログが使用されます。そのため、ビューは `warehouse.my_schema.users` に作成されます。
- その他の環境（例：`dev`）では、デフォルトカタログに環境名が追加されます。そのため、ビューは `warehouse__dev.my_schema.users` に作成されます。
- モデルが既にカタログで完全修飾されている場合（例：`finance_mart.my_schema.users`）、環境カタログはデフォルトカタログではなく、モデルカタログに基づきます。この例では、ビューは `finance_mart__dev.my_schema.users` に作成されます。


!!! warning "注意点"
    - `environment_suffix_target: catalog` の使用は、異なるカタログ間のクエリをサポートするエンジンでのみ機能します。エンジンがカタログ間クエリをサポートしていない場合は、代わりに `environment_suffix_target: schema` または `environment_suffix_target: table` を使用する必要があります。
    - 自動カタログ作成は、カタログ間クエリをサポートしているエンジンであっても、すべてのエンジンでサポートされているわけではありません。自動カタログ作成がサポートされていないエンジンでは、カタログはSQLMeshの外部で管理され、SQLMeshを呼び出す前に存在している必要があります。

#### 物理テーブルの命名規則

SQLMesh には、デフォルトで以下のデフォルトが設定されています。

- `environment_suffix_target: schema`
- `physical_table_naming_convention: schema_and_table`
- `physical_schema_mapping` によるオーバーライドは行われないため、モデルスキーマごとに `sqlmesh__<model schema>` 物理スキーマが作成されます。

つまり、`warehouse` というカタログと `finance_mart.transaction_events_over_threshold` というモデル名が与えられた場合、SQLMesh は以下の規則に従って物理テーブルを作成します。

```
# <catalog>.sqlmesh__<schema>.<schema>__<table>__<fingerprint>

warehouse.sqlmesh__finance_mart.finance_mart__transaction_events_over_threshold__<fingerprint>
```

これは、物理レイヤーにおいて物理スキーマ名と物理テーブル名の両方で*モデル*スキーマが繰り返されているため、意図的に冗長性を持たせています。

このデフォルトは、異なる構成間で物理テーブル名を移植可能にするために存在します。すべてのモデルを同じ物理スキーマにマッピングする`physical_schema_mapping`を定義した場合、モデルスキーマがテーブル名にも含まれるため、名前の競合は発生しません。

##### テーブルのみ

一部のエンジンではオブジェクト名の長さに制限があり、この制限を超えるテーブル名やビュー名は[自動的に切り捨て](https://www.postgresql.org/docs/current/sql-syntax-lexical.html#SQL-SYNTAX-IDENTIFIERS)されます。この動作はSQLMeshの動作に支障をきたすため、作成しようとしているテーブル名がエンジンによって自動的に切り捨てられることを検知すると、実行時エラーが発生します。

物理テーブル名に冗長性を持たせると、モデル名に使用できる文字数は減少します。モデル名に使用できる文字数を増やすには、次のように `physical_table_naming_convention` を使用します。

=== "YAML"

    ```yaml linenums="1"
    physical_table_naming_convention: table_only
    ```

=== "Python"

    ```python linenums="1"
    from sqlmesh.core.config import Config, ModelDefaultsConfig, TableNamingConvention

    config = Config(
        model_defaults=ModelDefaultsConfig(dialect=<dialect>),
        physical_table_naming_convention=TableNamingConvention.TABLE_ONLY,
    )
    ```

これにより、SQLMesh はテーブル名からモデル スキーマを省略し、次のような物理名を生成します (上記の例を使用)。
```
# <catalog>.sqlmesh__<schema>.<table>__<fingerprint>

warehouse.sqlmesh__finance_mart.transaction_events_over_threshold__<fingerprint>
```

モデルスキーマ名が物理テーブル名に含まれなくなったことに注意してください。これにより、識別子の長さ制限が低いエンジンでは、モデル名を少し長く設定できるようになり、プロジェクトにとって便利な場合があります。

この構成では、`physical_schema_mapping` でスキーマをオーバーライドした場合に、各モデルスキーマが一意の物理スキーマにマッピングされるようにする必要があります。

例えば、次の構成は**データ破損**を引き起こします。

```yaml
physical_table_naming_convention: table_only
physical_schema_mapping:
  '.*': sqlmesh
```

これは、すべてのモデル スキーマが同じ物理スキーマにマップされているが、モデル スキーマ名が物理テーブル名から省略されているためです。

##### MD5ハッシュ

さらに文字数が必要な場合は、`physical_table_naming_convention: hash_md5` を次のように設定します。

=== "YAML"

    ```yaml linenums="1"
    physical_table_naming_convention: hash_md5
    ```

=== "Python"

    ```python linenums="1"
    from sqlmesh.core.config import Config, ModelDefaultsConfig, TableNamingConvention

    config = Config(
        model_defaults=ModelDefaultsConfig(dialect=<dialect>),
        physical_table_naming_convention=TableNamingConvention.HASH_MD5,
    )
    ```

これにより、SQLMesh は常に 45 ～ 50 文字の長さで次のような物理名を生成します。

```
# sqlmesh_md5__<hash of what we would have generated using 'schema_and_table'>

sqlmesh_md5__d3b07384d113edec49eaa6238ad5ff00

# or, for a dev preview
sqlmesh_md5__d3b07384d113edec49eaa6238ad5ff00__dev
```

これには欠点があり、SQLクライアントでデータベースを参照するだけでは、どのテーブルがどのモデルに対応しているかを判断するのがはるかに困難になります。ただし、テーブル名の長さは予測可能なので、物理層で識別子が最大長を超えるという問題は発生しなくなりました。

#### 仮想データ環境モード

デフォルトでは、仮想データ環境 (VDE) は開発環境と本番環境の両方に適用されます。これにより、SQLMesh は開発環境から本番環境へのプロモート時でも、必要に応じて物理テーブルを再利用できます。

ただし、本番環境を仮想化せずに運用したいというユーザーもいます。その理由としては、以下のようなものが挙げられます。

- データカタログなどのサードパーティ製ツールやプラットフォームとの統合が、SQLMesh がデフォルトで適用する仮想ビューレイヤーではうまく機能しない可能性がある。
- BigQuery、Snowflake、Databricks などのクラウドデータウェアハウスが提供するタイムトラベル機能を利用したい場合

この問題を軽減するために、SQLMesh は VDE を使用するための「開発専用」モードを提供しています。このモードは、プロジェクト構成で以下のように有効化できます。

=== "YAML"

    ```yaml linenums="1"
    virtual_environment_mode: dev_only
    ```

=== "Python"

    ```python linenums="1"
    from sqlmesh.core.config import Config

    config = Config(
        virtual_environment_mode="dev_only",
    )
    ```

「開発専用」モードは、VDE が開発環境にのみ適用されることを意味します。本番環境では、モデルテーブルとビューは仮想レイヤーを経由せずに直接更新されます。また、本番環境の物理テーブルは、元の**バージョン管理されていない**モデル名を使用して作成されます。ユーザーは引き続き、開発環境間での VDE とデータ再利用のメリットを享受できます。

このモードを有効にする際は、以下のトレードオフにご注意ください。

- 開発環境で挿入されたすべてのデータは、[プレビュー](../concepts/plans.md#data-preview-for-forward-only-changes) にのみ使用され、本番環境では**再利用されません**。
- モデルを以前のバージョンに戻す操作は、今後適用され、明示的なデータの再ステートメントが必要になる場合があります。

!!! warning
    既存のプロジェクトのモードを切り替えると、プロジェクト内のすべてのモデルが**完全に再構築**されます。既存のテーブルをゼロから再構築せずに移行するには、[テーブル移行ガイド](./table_migration.md)を参照してください。


#### 環境ビューカタログ

デフォルトでは、SQLMesh は、ビューが参照する物理テーブルと同じ [カタログ](../concepts/glossary.md#catalog) に環境ビューを作成します。物理テーブルのカタログは、モデル名で指定されたカタログ、または接続で定義されたデフォルトのカタログによって決定されます。

代わりに、`prod` と non-prod の仮想レイヤーオブジェクトを別々のカタログに作成することが望ましい場合があります。たとえば、すべての `prod` 環境ビューを含む「prod」カタログと、すべての `dev` 環境ビューを含む別の「dev」カタログが存在する場合があります。

[SQLMesh Github Actions CI/CD Bot](../integrations/github.md) のように、環境を作成する CI/CD パイプラインがある場合、prod と non-prod のカタログを別々にすることは便利です。CI/CD 環境オブジェクトは多数存在する可能性があるため、専用のカタログに保存することをお勧めします。

!!! info "仮想レイヤーのみ"
    以下の設定は[仮想レイヤー](../concepts/glossary.md#virtual-layer)にのみ影響することに注意してください。[物理レイヤー](../concepts/glossary.md#physical-layer)内の環境間でカタログによる完全な分離が必要な場合は、[分離システムガイド](../guides/isolated_systems.md)を参照してください。

個別のカタログを構成するには、[正規表現パターン](https://en.wikipedia.org/wiki/Regular_expression)からカタログ名へのマッピングを指定します。SQLMeshは環境名と正規表現パターンを比較し、一致するものが見つかると、その環境のオブジェクトを対応するカタログに格納します。

SQLMeshは、構成で定義された順序で正規表現パターンを評価し、最初に一致したパターンのカタログを使用します。一致するものが見つからない場合は、モデルで定義されたカタログ、または接続で定義されたデフォルトのカタログが使用されます。

構成例：

=== "YAML"

    ```yaml linenums="1"
    environment_catalog_mapping:
      '^prod$': prod
      '^dev.*': dev
      '^analytics_repo.*': cicd
    ```

=== "Python"

    ```python linenums="1"
    from sqlmesh.core.config import Config, ModelDefaultsConfig

    config = Config(
        model_defaults=ModelDefaultsConfig(dialect=<dialect>),
        environment_catalog_mapping={
            '^prod$': 'prod',
            '^dev.*': 'dev',
            '^analytics_repo.*': 'cicd',
        },
    )
    ```

上記の設定例では、SQLMesh は環境名を次のように評価します。

* 環境名が `prod` の場合、カタログは `prod` になります。
* 環境名が `dev` で始まる場合、カタログは `dev` になります。
* 環境名が `analytics_repo` で始まる場合、カタログは `cicd` になります。

!!! warning
    この機能は、曖昧なマッピングが定義されるのを防ぐため、`environment_suffix_target: catalog` とは相互に排他的です。`environment_catalog_mapping` と `environment_suffix_target: catalog` の両方を指定しようとすると、プロジェクトの読み込み時にエラーが発生します。

*注:* この機能は、カタログ間のクエリをサポートするエンジンでのみ利用可能です。執筆時点では、以下のエンジンは**サポートされていません**。

* [MySQL](../integrations/engines/mysql.md)
* [Postgres](../integrations/engines/postgres.md)
* [GCP Postgres](../integrations/engines/gcp-postgres.md)

##### 正規表現のヒント

* 正規表現にあまり詳しくない場合は、[regex101](https://regex101.com/) などのツールを使用して正規表現パターンを作成できます。
    * [ChatGPT](https://chat.openai.com) などの LLM は、正規表現パターンの生成に役立ちます。regex101 の提案を必ず検証してください。
* 単語の完全一致を行う場合は、上記の例のように `^` と `$` で囲みます。
* マッピングの最後に包括的な検索条件を指定し、モデルカタログやデフォルトカタログの使用を避けたい場合は、パターンとして `.*` を使用します。これにより、まだ一致していない環境名に一致します。

### モデル変更の自動分類

SQLMesh は、`sqlmesh plan` 実行時にプロジェクトファイルの現在の状態と環境を比較します。モデルの変更を検出し、互換性を損なう変更と互換性のない変更に分類できます。

SQLMesh は、検出した変更を自動的に [分類](../concepts/plans.md#change-categories) しようとします。`plan.auto_categorize_changes` オプションは、SQLMesh が変更の自動分類を試みるかどうかを決定します。このオプションは、構成リファレンスページの [plan](../reference/configuration.md#plan) セクションにあります。

サポートされている値:

* `full`: ユーザーに入力を求めず、カテゴリを自動的に決定できない場合は、最も保守的なカテゴリ ([breaking](../concepts/plans.md#breaking-change)) にフォールバックします。
* `semi`: 変更カテゴリを自動的に決定できない場合のみ、ユーザーに入力を求めます。
* `off`: 常にユーザーに入力を求めます。自動分類は試行されません。

デフォルト値の例:

=== "YAML"

    ```yaml linenums="1"
    plan:
      auto_categorize_changes:
        external: full
        python: off
        sql: full
        seed: full
    ```

=== "Python"

    Python の `auto_categorize_changes` 引数は `CategorizerConfig` オブジェクトを受け取ります。このオブジェクトの引数は `AutoCategorizationMode` 列挙型で、値は `AutoCategorizationMode.FULL`、`AutoCategorizationMode.SEMI`、または `AutoCategorizationMode.OFF` のいずれかになります。

    ```python linenums="1"
    from sqlmesh.core.config import (
        Config,
        ModelDefaultsConfig,
        AutoCategorizationMode,
        CategorizerConfig,
        PlanConfig,
    )

    config = Config(
        model_defaults=ModelDefaultsConfig(dialect=<dialect>),
        plan=PlanConfig(
            auto_categorize_changes=CategorizerConfig(
                external=AutoCategorizationMode.FULL,
                python=AutoCategorizationMode.OFF,
                sql=AutoCategorizationMode.FULL,
                seed=AutoCategorizationMode.FULL,
            )
        ),
    )
    ```


### 常に本番環境と比較

デフォルトでは、SQLMesh は `sqlmesh plan <env>` の実行時に、プロジェクトファイルの現在の状態をターゲットの `<env>` 環境と比較します。ただし、一般的には、ローカルでの変更は常に本番環境と比較することが求められます。

`always_recreate_environment` ブール型プランオプションを使用すると、この動作を変更できます。このオプションを有効にすると、SQLMesh は常にターゲット環境を再作成して本番環境と比較しようとします。`prod` が存在しない場合は、SQLMesh はターゲット環境と比較するモードにフォールバックします。

**注:**: プランの適用が成功した場合、変更はターゲットの `<env>` 環境にプロモートされます。

=== "YAML"

    ```yaml linenums="1"
    plan:
        always_recreate_environment: True
    ```

=== "Python"

    ```python linenums="1"
    from sqlmesh.core.config import (
        Config,
        ModelDefaultsConfig,
        PlanConfig,
    )

    config = Config(
        model_defaults=ModelDefaultsConfig(dialect=<dialect>),
        plan=PlanConfig(
            always_recreate_environment=True,
        ),
    )
    ```

#### 変更分類の例

`always_recreate_environment` が有効になっている場合の以下のシナリオを考えてみましょう。

1. `prod` の初期状態:
```sql
MODEL (name sqlmesh_example.test_model, kind FULL);
SELECT 1 AS col
```

1. `dev` の最初の（破壊的な）変更:
```sql
MODEL (name sqlmesh_example__dev.test_model, kind FULL);
SELECT 2 AS col
```

??? "出力計画例 #1"

    ```bash
    New environment `dev` will be created from `prod`

    Differences from the `prod` environment:

    Models:
    └── Directly Modified:
        └── sqlmesh_example__dev.test_model

    ---
    +++


    kind FULL
    )
    SELECT
    -  1 AS col
    +  2 AS col
    ```

3. `dev` での 2 番目の (メタデータ) 変更:
```sql
MODEL (name sqlmesh_example__dev.test_model, kind FULL, owner 'John Doe');
SELECT 5 AS col
```

??? "出力計画例 #2"

    ```bash
    New environment `dev` will be created from `prod`

    Differences from the `prod` environment:

    Models:
    └── Directly Modified:
        └── sqlmesh_example__dev.test_model

    ---

    +++

    @@ -1,8 +1,9 @@

    MODEL (
    name sqlmesh_example.test_model,
    +  owner "John Doe",
    kind FULL
    )
    SELECT
    -  1 AS col
    +  2 AS col

    Directly Modified: sqlmesh_example__dev.test_model (Breaking)
    Models needing backfill:
    └── sqlmesh_example__dev.test_model: [full refresh]
    ```

2番目の変更はメタデータの変更であるはず（したがってバックフィルは不要）ですが、比較対象が以前の開発状態ではなく本番環境であるため、破壊的変更として分類されます。これは意図的なものであり、変更が蓄積されるにつれて追加のバックフィルが発生する可能性があります。

### ゲートウェイ

`gateways` 設定は、SQLMesh がデータウェアハウス、状態バックエンド、およびスケジューラに接続する方法を定義します。これらのオプションは、設定リファレンスページの [gateway](../reference/configuration.md#gateway) セクションにあります。

各ゲートウェイキーは一意のゲートウェイ名を表し、その接続を設定します。**ゲートウェイ名は大文字と小文字を区別しません** - SQLMesh は設定検証時にゲートウェイ名を自動的に小文字に正規化します。つまり、設定ファイルでは大文字と小文字のどちらを使用しても（例: `MyGateway`、`mygateway`、`MYGATEWAY`）、すべて正常に動作します。

例えば、`my_gateway` ゲートウェイを設定するには、次のようにします。

=== "YAML"

    ```yaml linenums="1"
    gateways:
      my_gateway:
        connection:
          ...
        state_connection:
          ...
        test_connection:
          ...
        scheduler:
          ...
    ```

=== "Python"

    Python の `gateways` 引数は、ゲートウェイ名と `GatewayConfig` オブジェクトの辞書を受け取ります。`GatewayConfig` の接続関連の引数は [エンジン固有の接続設定](#engine-connection-configuration) オブジェクトを受け取り、`scheduler` 引数は [スケジューラ設定](#scheduler) オブジェクトを受け取ります。

    ```python linenums="1"
    from sqlmesh.core.config import (
        Config,
        ModelDefaultsConfig,
        GatewayConfig,
        ...
    )

    config = Config(
        model_defaults=ModelDefaultsConfig(dialect=<dialect>),
        gateways={
            "my_gateway": GatewayConfig(
                connection=...,
                state_connection=...,
                test_connection=...,
                scheduler=...,
            ),
        }
    )
    ```

ゲートウェイでは、上記の例にある4つのコンポーネントすべてを指定する必要はありません。ゲートウェイのデフォルトオプションは、すべてのコンポーネントが指定されていない場合の動作を制御します。詳細については、[ゲートウェイのデフォルト](#gatewayconnection-defaults)をご覧ください。

### 接続

`connection` 設定は、データウェアハウスへの接続を制御します。これらのオプションは、設定リファレンスページの [connection](../reference/configuration.md#connection) セクションにあります。

使用可能なキーは次のとおりです。

- オプションの [`concurrent_tasks`](#concurrent-tasks) キーは、SQLMesh が実行する同時タスクの最大数を指定します。同時タスクをサポートするエンジンの場合、デフォルト値は 4 です。
- ほとんどのキーは接続エンジンの `type` に固有です。[下記](#engine-connection-configuration) を参照してください。デフォルトのデータウェアハウス接続タイプは、インメモリ DuckDB データベースです。

Snowflake 接続設定の例:

=== "YAML"

    ```yaml linenums="1"
    gateways:
      my_gateway:
        connection:
          type: snowflake
          user: <username>
          password: <password>
          account: <account>
    ```

=== "Python"

    Snowflake 接続は `SnowflakeConnectionConfig` オブジェクトで指定されます。

    ```python linenums="1"
    from sqlmesh.core.config import (
        Config,
        ModelDefaultsConfig,
        GatewayConfig,
        SnowflakeConnectionConfig
    )

    config = Config(
        model_defaults=ModelDefaultsConfig(dialect=<dialect>),
        gateways={
            "my_gateway": GatewayConfig(
                connection=SnowflakeConnectionConfig(
                    user=<username>,
                    password=<password>,
                    account=<account>,
                ),
            ),
        }
    )
    ```

#### エンジン接続設定

このページでは、各実行エンジンの接続設定オプションについて説明します。

* [Athena](../integrations/engines/athena.md)
* [BigQuery](../integrations/engines/bigquery.md)
* [Databricks](../integrations/engines/databricks.md)
* [DuckDB](../integrations/engines/duckdb.md)
* [Fabric](../integrations/engines/fabric.md)
* [MotherDuck](../integrations/engines/motherduck.md)
* [MySQL](../integrations/engines/mysql.md)
* [MSSQL](../integrations/engines/mssql.md)
* [Postgres](../integrations/engines/postgres.md)
* [GCP Postgres](../integrations/engines/gcp-postgres.md)
* [Redshift](../integrations/engines/redshift.md)
* [Snowflake](../integrations/engines/snowflake.md)
* [Spark](../integrations/engines/spark.md)
* [Trino](../integrations/engines/trino.md)

#### 状態接続

データウェアハウス接続と異なる場合の状態バックエンド接続の設定。

`state_connection` キーが指定されていない場合、SQLMesh の状態を保存するにはデータウェアハウス接続が使用されます。

データ変換とは異なり、状態情報の保存にはデータベーストランザクションが必要です。データウェアハウスはトランザクションの実行に最適化されていないため、状態情報を保存すると、プロジェクトの速度が低下したり、同じテーブルへの同時書き込みによってデータが破損したりする可能性があります。したがって、本番環境の SQLMesh デプロイメントでは、専用の状態接続を使用する必要があります。

!!! note
    SQLMesh の本番環境への導入では、データウェアハウスと状態接続に同じ接続を使用することは推奨されません。

状態接続を管理する最も簡単で信頼性の高い方法は、[Tobiko Cloud](https://tobikodata.com/product.html) を利用することです。ご自身で管理したい場合は、以下に推奨される状態エンジンとサポート対象外の状態エンジンを記載しています。

本番環境への導入に推奨される状態エンジン：

* [Postgres](../integrations/engines/postgres.md)
* [GCP Postgres](../integrations/engines/gcp-postgres.md)

高速で信頼性の高いデータベース トランザクションを備えたその他の状態エンジン (推奨エンジンよりもテストが少ない):

* [DuckDB](../integrations/engines/duckdb.md)
    * With the caveat that it's a [single user](https://duckdb.org/docs/connect/concurrency.html#writing-to-duckdb-from-multiple-processes) database so will not scale to production usage
* [MySQL](../integrations/engines/mysql.md)
* [MSSQL](../integrations/engines/mssql.md)

開発用であってもサポートされていない状態エンジン:

* [ClickHouse](../integrations/engines/clickhouse.md)
* [Spark](../integrations/engines/spark.md)
* [Trino](../integrations/engines/trino.md)

このゲートウェイ構成の例では、データ ウェアハウス接続に Snowflake を使用し、状態バックエンド接続に Postgres を使用します。

=== "YAML"

    ```yaml linenums="1"
    gateways:
      my_gateway:
        connection:
          # snowflake credentials here
          type: snowflake
          user: <username>
          password: <password>
          account: <account>
        state_connection:
          # postgres credentials here
          type: postgres
          host: <host>
          port: <port>
          user: <username>
          password: <password>
          database: <database>
    ```

=== "Python"

    Postgres 接続は `PostgresConnectionConfig` オブジェクトで指定されます。

    ```python linenums="1"
    from sqlmesh.core.config import (
        Config,
        ModelDefaultsConfig,
        GatewayConfig,
        PostgresConnectionConfig,
        SnowflakeConnectionConfig
    )

    config = Config(
        model_defaults=ModelDefaultsConfig(dialect=<dialect>),
        gateways={
            "my_gateway": GatewayConfig(
                # snowflake credentials here
                connection=SnowflakeConnectionConfig(
                    user=<username>,
                    password=<password>,
                    account=<account>,
                ),
                # postgres credentials here
                state_connection=PostgresConnectionConfig(
                    host=<host>,
                    port=<port>,
                    user=<username>,
                    password=<password>,
                    database=<database>,
                ),
            ),
        }
    )
    ```

#### 状態スキーマ名

デフォルトでは、状態テーブルを保存するために使用するスキーマ名は `sqlmesh` です。これは、ゲートウェイ設定で `state_schema` 設定キーを指定することで変更できます。

Postgres データベースの `custom_name` スキーマに状態情報を保存する設定例:

=== "YAML"

    ```yaml linenums="1"
    gateways:
      my_gateway:
        state_connection:
          type: postgres
          host: <host>
          port: <port>
          user: <username>
          password: <password>
          database: <database>
        state_schema: custom_name
    ```

=== "Python"


    ```python linenums="1"
    from sqlmesh.core.config import (
        Config,
        ModelDefaultsConfig,
        GatewayConfig,
        PostgresConnectionConfig
    )

    config = Config(
        model_defaults=ModelDefaultsConfig(dialect=<dialect>),
        gateways={
            "my_gateway": GatewayConfig(
                state_connection=PostgresConnectionConfig(
                    host=<host>,
                    port=<port>,
                    user=<username>,
                    password=<password>,
                    database=<database>,
                ),
                state_schema="custom_name",
            ),
        }
    )
    ```

これにより、スキーマ `custom_name` 内にすべての状態テーブルが作成されます。

#### テスト接続

ユニットテストの実行に使用する接続の設定です。`test_connection` キーが指定されていない場合は、インメモリの DuckDB データベースが使用されます。

=== "YAML"

    ```yaml linenums="1"
    gateways:
      my_gateway:
        test_connection:
          type: duckdb
    ```

=== "Python"

    DuckDB接続は`DuckDBConnectionConfig`オブジェクトで指定します。引数が指定されていない`DuckDBConnectionConfig`は、メモリ内のDuckDBデータベースを使用します。

    ```python linenums="1"
    from sqlmesh.core.config import (
        Config,
        ModelDefaultsConfig,
        GatewayConfig,
        DuckDBConnectionConfig
    )

    config = Config(
        model_defaults=ModelDefaultsConfig(dialect=<dialect>),
        gateways={
            "my_gateway": GatewayConfig(
                test_connection=DuckDBConnectionConfig(),
            ),
        }
    )
    ```

### スケジューラ

使用するスケジューラバックエンドを指定します。スケジューラバックエンドは、メタデータの保存と[プラン](../concepts/plans.md)の実行の両方に使用されます。デフォルトでは、スケジューラタイプは「builtin」に設定されており、メタデータの保存には既存のSQLエンジンが使用されます。

これらのオプションは、設定リファレンスページの[スケジューラ](../reference/configuration.md#scheduler)セクションにあります。

#### 組み込み

設定例:

=== "YAML"

    ```yaml linenums="1"
    gateways:
      my_gateway:
        scheduler:
          type: builtin
    ```

=== "Python"

    組み込みスケジューラは、`BuiltInSchedulerConfig` オブジェクトで指定されます。

    ```python linenums="1"
    from sqlmesh.core.config import (
        Config,
        ModelDefaultsConfig,
        GatewayConfig,
        BuiltInSchedulerConfig,
    )

    config = Config(
        model_defaults=ModelDefaultsConfig(dialect=<dialect>),
        gateways={
            "my_gateway": GatewayConfig(
                scheduler=BuiltInSchedulerConfig(),
            ),
        }
    )
    ```

このスケジューラ タイプでは追加の構成オプションはサポートされていません。


### ゲートウェイ/接続のデフォルト

デフォルトのゲートウェイと接続キーは、ゲートウェイまたは接続が明示的に指定されていない場合の動作を指定します。これらのオプションは、設定リファレンスページの [ゲートウェイ/接続のデフォルト](../reference/configuration.md#gatewayconnection-defaults) セクションにあります。

`default_gateway` で指定されたゲートウェイは、`sqlmesh` コマンドでゲートウェイが明示的に指定されていない場合に使用されます。すべての SQLMesh CLI コマンドは、`sqlmesh` の後、コマンド名の前にゲートウェイオプションを指定できます。(../reference/cli.md#cli) 例: `sqlmesh --gateway my_gateway plan` コマンド呼び出しでゲートウェイオプションが指定されていない場合は、`default_gateway` が使用されます。

`gateways` 設定辞書内の一部のゲートウェイですべての接続タイプが指定されていない場合は、3 つのデフォルトの接続タイプが使用されます。

#### デフォルトゲートウェイ

設定に複数のゲートウェイが含まれている場合、SQLMesh はデフォルトで `gateways` ディクショナリの最初のゲートウェイを使用します。`default_gateway` キーは、SQLMesh のデフォルトとして別のゲートウェイ名を指定するために使用されます。

設定例:

=== "YAML"

    ```yaml linenums="1"
    gateways:
      my_gateway:
        <gateway specification>
    default_gateway: my_gateway
    ```

=== "Python"

    ```python linenums="1"
    from sqlmesh.core.config import (
        Config,
        ModelDefaultsConfig,
        GatewayConfig,
    )

    config = Config(
        model_defaults=ModelDefaultsConfig(dialect=<dialect>),
        gateways={
            "my_gateway": GatewayConfig(
                <gateway specification>
            ),
        },
        default_gateway="my_gateway",
    )
    ```

#### デフォルトの接続/スケジューラ

`default_connection`、`default_test_connection`、`default_scheduler` キーは、複数のゲートウェイ間で共有されるデフォルトを指定するために使用されます。

例えば、どのゲートウェイが使用されているかに関係なく、特定の接続でテストを実行する必要がある場合、各ゲートウェイの指定でテスト接続情報を重複させるのではなく、`default_test_connection` キーで 1 回だけ指定します。

Postgres のデフォルト接続、インメモリ DuckDB のデフォルトテスト接続、および組み込みのデフォルトスケジューラを指定する設定例:

=== "YAML"

    ```yaml linenums="1"
    default_connection:
      type: postgres
      host: <host>
      port: <port>
      user: <username>
      password: <password>
      database: <database>
    default_test_connection:
      type: duckdb
    default_scheduler:
      type: builtin
    ```

=== "Python"

    ```python linenums="1"
    from sqlmesh.core.config import (
        Config,
        ModelDefaultsConfig,
        PostgresConnectionConfig,
        DuckDBConnectionConfig,
        BuiltInSchedulerConfig
    )

    config = Config(
        model_defaults=ModelDefaultsConfig(dialect=<dialect>),
        default_connection=PostgresConnectionConfig(
            host=<host>,
            port=<port>,
            user=<username>,
            password=<password>,
            database=<database>,
        ),
        default_test_connection=DuckDBConnectionConfig(),
        default_scheduler=BuiltInSchedulerConfig(),
    )
    ```

### モデル

#### モデルのデフォルト

`model_defaults` キーは**必須** であり、`dialect` キーの値を含める必要があります。[SQLGlot ライブラリでサポートされている](https://github.com/tobymao/sqlglot/blob/main/sqlglot/dialects/dialect.py) すべての SQL 方言が使用できます。その他の値は、モデル定義で明示的に上書きされない限り、自動的に設定されます。

サポートされているすべての `model_defaults` キーは、[モデル設定リファレンスページ](../reference/model_configuration.md#model-defaults) に記載されています。

設定例:

=== "YAML"

    ```yaml linenums="1"
    model_defaults:
      dialect: snowflake
      owner: jen
      start: 2022-01-01
    ```

=== "Python"

    ```python linenums="1"
    from sqlmesh.core.config import Config, ModelDefaultsConfig

    config = Config(
        model_defaults=ModelDefaultsConfig(
            dialect="snowflake",
            owner="jen",
            start="2022-01-01",
        ),
    )
    ```

`kind` キーで上書きされない限り、デフォルトのモデル種別は `VIEW` です。モデル種別の詳細については、[モデルの概念ページ](../concepts/models/model_kinds.md) を参照してください。

##### 識別子の解決

SQLエンジンが「SELECT id FROM "some_table"」のようなクエリを受け取ると、最終的には識別子「id」と「"some_table"」がどのデータベースオブジェクトに対応しているかを理解する必要があります。このプロセスは通常、「識別子（または名前）解決」と呼ばれます。

SQL方言によって、クエリ内の識別子を解決する際のルールは異なります。例えば、一部の識別子は大文字と小文字が区別されることがあります（引用符で囲まれている場合など）。また、大文字と小文字を区別しない識別子は、エンジンが実際にどのオブジェクトに対応するかを調べる前に、通常は小文字または大文字に変換されます。

SQLMeshはモデルクエリを分析し、列レベルの系統の計算など、有用な情報を抽出します。この分析を容易にするために、各方言の解決ルールを尊重しながら、クエリ内のすべての識別子を_正規化_し_、_引用符で囲みます。(https://sqlglot.com/sqlglot/dialects/dialect.html#Dialect.normalize_identifier)

「正規化戦略」、つまり大文字と小文字を区別しない識別子を小文字にするか大文字にするかは、方言ごとに設定可能です。例えば、BigQueryプロジェクトですべての識別子を大文字と小文字を区別するようにするには、次のようにします。

=== "YAML"

    ```yaml linenums="1"
    model_defaults:
      dialect: "bigquery,normalization_strategy=case_sensitive"
    ```

これは、名前の大文字と小文字の区別を保持する必要がある場合に役立ちます。そうしないと、SQLMesh は正規化できません。

サポートされている正規化戦略の詳細については、[こちら](https://sqlglot.com/sqlglot/dialects/dialect.html#NormalizationStrategy) を参照してください。

##### ゲートウェイ固有のモデルデフォルト

`gateways` セクションでゲートウェイ固有の `model_defaults` を定義することもできます。これは、そのゲートウェイのグローバルデフォルトをオーバーライドします。

```yaml linenums="1" hl_lines="6 14"
gateways:
  redshift:
    connection:
      type: redshift
    model_defaults:
      dialect: "snowflake,normalization_strategy=case_insensitive"
  snowflake:
    connection:
      type: snowflake

default_gateway: snowflake

model_defaults:
  dialect: snowflake
  start: 2025-02-05
```

これにより、グローバルな `model_defaults` に影響を与えることなく、ゲートウェイごとにモデルの動作をカスタマイズできます。

例えば、一部の SQL エンジンではテーブル名や列名などの識別子の大文字と小文字が区別されますが、他のエンジンでは大文字と小文字が区別されません。デフォルトでは、両方の種類のエンジンを使用するプロジェクトでは、各エンジンのモデルがエンジンの正規化動作に準拠していることを確認する必要があり、プロジェクトのメンテナンスとデバッグがより困難になります。

ゲートウェイ固有の `model_defaults` を使用すると、SQLMesh が識別子の正規化を *エンジンごとに* 実行する方法を変更し、異なるエンジンの動作を揃えることができます。

上記の例では、プロジェクトのデフォルトのダイアレクトは `snowflake` (14 行目) です。`redshift` ゲートウェイ構成では、このグローバルなデフォルトのダイアレクトを `"snowflake,normalization_strategy=case_insensitive"` (6 行目) で上書きします。

この値は、SQLMesh に、`redshift` ゲートウェイのモデルが Snowflake SQL 方言で記述される (したがって、Snowflake から Redshift にトランスパイルする必要がある) が、結果の Redshift SQL は、Snowflake の動作に合わせて識別子を大文字と小文字を区別せずに扱う必要があることを伝えます。


#### モデルの種類

各モデルファイルの `MODEL` DDL 文には、モデルの種類が必須です。オプションで、モデルデフォルト設定キーでデフォルトの種類を指定できます。

すべてのモデルの種類指定キーは、[モデル設定リファレンスページ](../reference/model_configuration.md#model-kind-properties) に記載されています。

`VIEW`、`FULL`、`EMBEDDED` の各モデルの種類は名前のみで指定されますが、その他のモデルの種類は追加のパラメータが必要であり、パラメータの配列で提供されます。

=== "YAML"

    `FULL` model only requires a name:

    ```sql linenums="1"
    MODEL(
      name docs_example.full_model,
      kind FULL
    );
    ```

    `INCREMENTAL_BY_TIME_RANGE` には、モデルの `time_column` (UTC タイムゾーンである必要があります) を指定する配列が必要です。

    ```sql linenums="1"
    MODEL(
      name docs_example.incremental_model,
      kind INCREMENTAL_BY_TIME_RANGE (
        time_column model_time_column
      )
    );
    ```

Python モデルの種類は、モデル種類オブジェクトで指定します。Python モデル種類オブジェクトは、[モデル設定リファレンスページ](../reference/model_configuration.md#model-kind-properties) に記載されている SQL の対応する引数と同じ引数を持ちます。

この例は、Python で時間範囲による増分モデルの種類を指定する方法を示しています。

=== "Python"

    ```python linenums="1"
    from sqlmesh import ExecutionContext, model
    from sqlmesh.core.model.kind import ModelKindName

    @model(
        "docs_example.incremental_model",
        kind=dict(
            name=ModelKindName.INCREMENTAL_BY_TIME_RANGE,
            time_column="ds"
        )
    )
    ```

Python モデルの指定の詳細については、[Python モデルの概念ページ](../concepts/models/python_models.md#model-specification) を参照してください。


#### モデルの命名

`model_naming` 設定は、プロジェクトのディレクトリ構造に基づいてモデル名を推論するかどうかを制御します。`model_naming` が定義されていない、または `infer_names` が false に設定されている場合は、モデル名を明示的に指定する必要があります。

`infer_names` が true に設定されている場合、モデル名はパスに基づいて推論されます。たとえば、`models/catalog/schema/model.sql` にあるモデルの名前は `catalog.schema.model` になります。ただし、モデル定義で名前が指定されている場合は、推論された名前よりも優先されます。

名前の推論を有効にする例:

=== "YAML"

    ```yaml linenums="1"
    model_naming:
      infer_names: true
    ```

=== "Python"

    ```python linenums="1"
    from sqlmesh.core.config import Config, NameInferenceConfig

    config = Config(
        model_naming=NameInferenceConfig(
            infer_names=True
        )
    )
    ```

### before_all および after_all ステートメント

`before_all` および `after_all` ステートメントは、それぞれ `sqlmesh plan` コマンドと `sqlmesh run` コマンドの開始時と終了時に実行されます。

これらのステートメントは、設定ファイル内の `before_all` キーと `after_all` キーの下に、SQL ステートメントのリストとして、または SQLMesh マクロを使用して定義できます。

=== "YAML"

    ```yaml linenums="1"
    before_all:
      - CREATE TABLE IF NOT EXISTS analytics (table VARCHAR, eval_time VARCHAR)
    after_all:
      - "@grant_select_privileges()"
      - "@IF(@this_env = 'prod', @grant_schema_usage())"
    ```

=== "Python"

    ```python linenums="1"
    from sqlmesh.core.config import Config

    config = Config(
        before_all = [
            "CREATE TABLE IF NOT EXISTS analytics (table VARCHAR, eval_time VARCHAR)"
        ],
        after_all = [
            "@grant_select_privileges()",
            "@IF(@this_env = 'prod', @grant_schema_usage())"
        ],
    )
    ```

#### 例

これらのステートメントを使用すると、それぞれ、すべてのモデルステートメントの実行前、またはすべてのモデルステートメントの実行後にアクションを実行できます。また、権限の付与などのタスクを簡素化することもできます。

##### 例: 選択権限の付与

例えば、各モデルで `on_virtual_update` ステートメントを使用して仮想レイヤーのビューに対する権限を付与するのではなく、プランの最後に単一のマクロを定義して使用することができます。

```python linenums="1"
from sqlmesh.core.macros import macro

@macro()
def grant_select_privileges(evaluator):
    if evaluator.views:
        return [
            f"GRANT SELECT ON VIEW {view_name} /* sqlglot.meta replace=false */ TO ROLE admin_role;"
            for view_name in evaluator.views
        ]
```

コメント `/* sqlglot.meta replace=false */` を含めることで、レンダリング中に評価者がビュー名を物理テーブル名に置き換えないようにすることができます。

##### 例: スキーマ権限の付与

同様に、スキーマ使用権限を付与するマクロを定義し、上記の設定で示したように、`this_env` マクロを使用して、本番環境でのみ条件付きで実行することもできます。

```python linenums="1"
from sqlmesh import macro

@macro()
def grant_schema_usage(evaluator):
    if evaluator.this_env == "prod" and evaluator.schemas:
        return [
            f"GRANT USAGE ON SCHEMA {schema} TO admin_role;"
            for schema in evaluator.schemas
        ]
```

これらの例で示されているように、`before_all` および `after_all` ステートメント内で呼び出されるマクロでは、マクロ評価機能内で `schemas` と `views` を利用できます。さらに、マクロ `this_env` は現在の環境名へのアクセスを提供します。これは、動作を細かく制御する必要がある高度なユースケースに役立ちます。

### リンティング

SQLMesh は、モデルのコードに潜在的な問題がないかチェックするリンター機能を提供します。この機能を有効にし、設定ファイルの `linter` キーで適用するリンティングルールを指定してください。

リンティング設定の詳細については、[リンティングガイド](./linter.md) をご覧ください。

### デバッグモード

デバッグモードを有効にするには、環境変数 `SQLMESH_DEBUG` を以下のいずれかの値に設定します: "1", "true", "t", "yes", "y"。

このモードを有効にすると、CLI 使用時に完全なバックトレースが出力されるようになります。このモードを有効にすると、デフォルトのログレベルは `DEBUG` に設定されます。

CLI コマンド `sqlmesh plan` でデバッグモードを有効にする例:

=== "Bash"

    ```bash
    $ SQLMESH_DEBUG=1 sqlmesh plan
    ```

=== "MS Powershell"

    ```powershell
    PS> $env:SQLMESH_DEBUG=1
    PS> sqlmesh plan
    ```

=== "MS CMD"

    ```cmd
    C:\> set SQLMESH_DEBUG=1
    C:\> sqlmesh plan
    ```


### Python ライブラリの依存関係

SQLMesh では、サードパーティ製ライブラリに依存する Python モデルとマクロを作成できます。各実行/評価で同じバージョンが使用されるようにするには、プロジェクトのルートにある `sqlmesh-requirements.lock` ファイルでバージョンを指定します。

sqlmesh.lock は `dep==version` の形式である必要があります。`==` のみがサポートされています。

例:

```
numpy==2.1.2
pandas==2.2.3
```

この機能は、[Tobiko Cloud](https://tobikodata.com/product.html) でのみ利用できます。

#### 依存関係の除外

依存関係の前に `^` を付けることで、依存関係を除外できます。例:

```
^numpy
pandas==2.2.3
```
