# DuckDB

!!! warning "DuckDB 状態接続の制限"

    DuckDB は [シングルユーザー](https://duckdb.org/docs/connect/concurrency.html#writing-to-duckdb-from-multiple-processes) データベースです。SQLMesh プロジェクトで DuckDB を状態接続に使用する場合、使用できるワークステーションは 1 台に制限されます。つまり、プロジェクトをチームメンバーや CI/CD インフラストラクチャ間で共有することはできません。これは通常、概念実証やテストプロジェクトには適していますが、本番環境での使用には適していません。

    本番環境プロジェクトでは、[Tobiko Cloud](https://tobikodata.com/product.html) または [Postgres](./postgres.md) などのより堅牢な状態データベースを使用してください。

## ローカル/組み込みスケジューラ
**エンジンアダプタタイプ**: `duckdb`

### 接続オプション

| オプション | 説明 | タイプ | 必須 |
|--------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:---------:|:--------:|
| `type` | エンジンタイプ名 - `duckdb` である必要があります | 文字列 | Y |
| `database` | オプションのデータベース名。指定しない場合は、インメモリデータベースが使用されます。`catalogs` を使用している場合は定義できません。 | 文字列 | N |
| `catalogs` | 複数のカタログを定義するためのマッピング。[DuckDB カタログをアタッチ](#duckdb-catalogs-example) または [他の接続用のカタログ](#other-connection-catalogs-example) できます。最初のエントリはデフォルトのカタログです。`database` を使用している場合は定義できません。 | dict | N |
| `extensions` | duckdb に読み込む拡張機能。自動ロード可能な拡張機能のみがサポートされています。 | list | N |
| `connector_config` | duckdb コネクタに渡す設定。 | dict | N |
| `secrets` | DuckDB シークレットを使用して外部ソース (例: S3) を認証するための設定。シークレット設定のリスト、またはカスタム シークレット名を含む辞書を指定できます。 | list/dict | N |
| `filesystems` | `fsspec` ファイルシステムを DuckDB 接続に登録するための設定。 | dict | N |

#### DuckDB カタログの例

この例では、2 つのカタログを指定します。1 つ目のカタログは「persistent」という名前で、DuckDB ファイルデータベース `local.duckdb` にマッピングされます。2 つ目のカタログは「ephemeral」という名前で、DuckDB インメモリデータベースにマッピングされます。

`persistent` は辞書の最初のエントリであるため、デフォルトのカタログです。SQLMesh は、`my_schema.my_model` のように明示的なカタログを持たないモデルを、`persistent` カタログの `local.duckdb` DuckDB ファイルデータベースに配置します。

SQLMesh は、`ephemeral.other_schema.other_model` のように明示的なカタログ「ephemeral」を持つモデルを、DuckDB インメモリデータベースの `ephemeral` カタログに配置します。

=== "YAML"

    ```yaml linenums="1"
    gateways:
      my_gateway:
        connection:
          type: duckdb
          catalogs:
            persistent: 'local.duckdb'
            ephemeral: ':memory:'
    ```

=== "Python"

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
                connection=DuckDBConnectionConfig(
                    catalogs={
                        "persistent": "local.duckdb"
                        "ephemeral": ":memory:"
                    }
                )
            ),
        }
    )
    ```

#### DuckLakeカタログの例

=== "YAML"

    ```yaml linenums="1"
    gateways:
      my_gateway:
        connection:
          type: duckdb
          catalogs:
            ducklake:
              type: ducklake
              path: 'catalog.ducklake'
              data_path: data/ducklake
              encrypted: True
              data_inlining_row_limit: 10
    ```
    
=== "Python"

    ```python linenums="1"
    from sqlmesh.core.config import (
        Config,
        ModelDefaultsConfig,
        GatewayConfig,
        DuckDBConnectionConfig
    )
    from sqlmesh.core.config.connection import DuckDBAttachOptions

    config = Config(
        model_defaults=ModelDefaultsConfig(dialect=<dialect>),
        gateways={
            "my_gateway": GatewayConfig(
                connection=DuckDBConnectionConfig(
                    catalogs={
                        "ducklake": DuckDBAttachOptions(
                            type="ducklake",
                            path="catalog.ducklake",
                            data_path="data/ducklake",
                            encrypted=True,
                            data_inlining_row_limit=10,
                        ),
                    }
                )
            ),
        }
    )
    ```

#### その他の接続カタログの例

カタログは、[DuckDB が接続可能な](https://duckdb.org/docs/sql/statements/attach.html)あらゆるものに接続できるように定義することもできます。

以下は、SQLite データベースと PostgreSQL データベースへの接続例です。
SQLite データベースは読み書き可能ですが、PostgreSQL データベースは読み取り専用です。

=== "YAML"

    ```yaml linenums="1"
    gateways:
      my_gateway:
        connection:
          type: duckdb
          catalogs:
            memory: ':memory:'
            sqlite:
              type: sqlite
              path: 'test.db'
            postgres:
              type: postgres
              path: 'dbname=postgres user=postgres host=127.0.0.1'
              read_only: true
    ```

=== "Python"

    ```python linenums="1"
    from sqlmesh.core.config import (
        Config,
        ModelDefaultsConfig,
        GatewayConfig,
        DuckDBConnectionConfig
    )
    from sqlmesh.core.config.connection import DuckDBAttachOptions

    config = Config(
        model_defaults=ModelDefaultsConfig(dialect=<dialect>),
        gateways={
            "my_gateway": GatewayConfig(
                connection=DuckDBConnectionConfig(
                    catalogs={
                        "memory": ":memory:",
                        "sqlite": DuckDBAttachOptions(
                            type="sqlite",
                            path="test.db"
                        ),
                        "postgres": DuckDBAttachOptions(
                            type="postgres",
                            path="dbname=postgres user=postgres host=127.0.0.1",
                            read_only=True
                        ),
                    }
                )
            ),
        }
    )
    ```

##### PostgreSQL のカタログ

PostgreSQL では、カタログ名は、関連付けられている実際のカタログ名と一致する必要があります。上記の例では、データベース名（パス内の `dbname`）はカタログ名と同じです。

##### スキーマのないコネクタ

SQLite などの一部の接続ではスキーマ名がサポートされていないため、オブジェクトはデフォルトのスキーマ名である `main` でアタッチされます。

例: `example_table` というテーブルを持つ `sqlite` という名前の SQLite データベースをマウントすると、`sqlite.main.example_table` としてアクセスできるようになります。

##### パス内の機密フィールド

Postgres などのコネクタがパス内に機密情報を必要とする場合、代わりに環境変数の定義をサポートしている可能性があります。
[詳細については、DuckDB ドキュメントをご覧ください](https://duckdb.org/docs/extensions/postgres#configuring-via-environment-variables)。

#### クラウドサービス認証

DuckDBは、拡張機能（例：[httpfs](https://duckdb.org/docs/extensions/httpfs/s3api)、[azure](https://duckdb.org/docs/extensions/azure)）を介してクラウドサービスから直接データを読み取ることができます。

`secrets` オプションを使用すると、DuckDBの[Secrets Manager](https://duckdb.org/docs/configuration/secrets_manager.html) を設定して、S3などの外部サービスとの認証を行うことができます。これは、DuckDB v0.10.0以降におけるクラウドストレージ認証の推奨アプローチであり、変数を介した[従来の認証方法](https://duckdb.org/docs/stable/extensions/httpfs/s3api_legacy_authentication.html)に代わるものです。

##### シークレットの設定

`secrets` オプションは 2 つの形式をサポートしています。

1. **リスト形式** (デフォルトのシークレット): シークレット設定のリスト。各シークレットには DuckDB のデフォルトの命名規則が適用されます。
2. **辞書形式** (名前付きシークレット): キーがカスタムシークレット名、値がシークレット設定である辞書。

この柔軟性により、同じ種類の複数のシークレットを整理したり、SQL クエリで特定のシークレットを名前で参照したりできます。

##### リスト形式の例 (デフォルトのシークレット)

リストを使用すると、DuckDB のデフォルトの命名規則に従ってシークレットが作成されます。

=== "YAML"

    ```yaml linenums="1"
    gateways:
      duckdb:
        connection:
          type: duckdb
          catalogs:
            local: local.db
            remote: "s3://bucket/data/remote.duckdb"
          extensions:
            - name: httpfs
          secrets:
            - type: s3
              region: "YOUR_AWS_REGION"
              key_id: "YOUR_AWS_ACCESS_KEY"
              secret: "YOUR_AWS_SECRET_KEY"
    ```

=== "Python"

    ```python linenums="1"
    from sqlmesh.core.config import (
        Config,
        ModelDefaultsConfig,
        GatewayConfig,
        DuckDBConnectionConfig
    )

    config = Config(
        model_defaults=ModelDefaultsConfig(dialect="duckdb"),
        gateways={
            "duckdb": GatewayConfig(
                connection=DuckDBConnectionConfig(
                    catalogs={
                        "local": "local.db",
                        "remote": "s3://bucket/data/remote.duckdb"
                    },
                    extensions=[
                        {"name": "httpfs"},
                    ],
                    secrets=[
                        {
                            "type": "s3",
                            "region": "YOUR_AWS_REGION",
                            "key_id": "YOUR_AWS_ACCESS_KEY",
                            "secret": "YOUR_AWS_SECRET_KEY"
                        }
                    ]
                )
            ),
        }
    )
    ```

##### 辞書形式の例 (名前付きシークレット)

辞書を使用すると、シークレットにカスタム名を割り当てて整理し、参照しやすくすることができます。

=== "YAML"

    ```yaml linenums="1"
    gateways:
      duckdb:
        connection:
          type: duckdb
          catalogs:
            local: local.db
            remote: "s3://bucket/data/remote.duckdb"
          extensions:
            - name: httpfs
          secrets:
            my_s3_secret:
              type: s3
              region: "YOUR_AWS_REGION"
              key_id: "YOUR_AWS_ACCESS_KEY"
              secret: "YOUR_AWS_SECRET_KEY"
            my_azure_secret:
              type: azure
              account_name: "YOUR_AZURE_ACCOUNT"
              account_key: "YOUR_AZURE_KEY"
    ```

=== "Python"

    ```python linenums="1"
    from sqlmesh.core.config import (
        Config,
        ModelDefaultsConfig,
        GatewayConfig,
        DuckDBConnectionConfig
    )

    config = Config(
        model_defaults=ModelDefaultsConfig(dialect="duckdb"),
        gateways={
            "duckdb": GatewayConfig(
                connection=DuckDBConnectionConfig(
                    catalogs={
                        "local": "local.db",
                        "remote": "s3://bucket/data/remote.duckdb"
                    },
                    extensions=[
                        {"name": "httpfs"},
                    ],
                    secrets={
                        "my_s3_secret": {
                            "type": "s3",
                            "region": "YOUR_AWS_REGION",
                            "key_id": "YOUR_AWS_ACCESS_KEY",
                            "secret": "YOUR_AWS_SECRET_KEY"
                        },
                        "my_azure_secret": {
                            "type": "azure",
                            "account_name": "YOUR_AZURE_ACCOUNT",
                            "account_key": "YOUR_AZURE_KEY"
                        }
                    }
                )
            ),
        }
    )
    ```

シークレットを設定すると、追加の認証手順なしで、カタログまたはSQLクエリでS3パスを直接参照できます。

[サポートされているS3シークレットパラメータ](https://duckdb.org/docs/stable/extensions/httpfs/s3api.html#overview-of-s3-secret-parameters)の完全なリストと[Secrets Managerの設定](https://duckdb.org/docs/configuration/secrets_manager.html)の詳細については、DuckDBの公式ドキュメントを参照してください。

> 注: SQLMeshを使用する場合、`load_aws_credentials()`または同様の非推奨関数を使用して実行時に認証情報を読み込むと失敗する可能性があります。

##### Microsoft Onelake のファイルシステム設定例

`filesystems` は、DuckDB 接続に登録するファイルシステムのリストを受け取ります。これは、DuckDB がネイティブにサポートしていない書き込みサポートを Azure ストレージアカウントに追加するため、特に便利です。


=== "YAML"

    ```yaml linenums="1"
    gateways:
      ducklake:
        connection:
          type: duckdb
          catalogs:
            ducklake:
              type: ducklake
              path: myducklakecatalog.duckdb
              data_path: abfs://MyFabricWorkspace/MyFabricLakehouse.Lakehouse/Files/DuckLake.Files
        extensions:
          - ducklake
        filesystems:
          - fs: abfs
            account_name: onelake
            account_host: onelake.blob.fabric.microsoft.com
            client_id: {{ env_var('AZURE_CLIENT_ID') }}
            client_secret: {{ env_var('AZURE_CLIENT_SECRET') }}
            tenant_id: {{ env_var('AZURE_TENANT_ID') }}
            # anon: False # To use azure.identity.DefaultAzureCredential authentication 
    ```


ストレージ オプションの完全な一覧については、`fsspec` [fsspec.filesystem](https://filesystem-spec.readthedocs.io/en/latest/api.html#fsspec.filesystem) および `adlfs` [adlfs.AzureBlobFileSystem](https://fsspec.github.io/adlfs/api/#api-reference) のドキュメントを参照してください。
