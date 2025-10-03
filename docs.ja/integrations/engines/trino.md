# Trino

## ローカル/組み込みスケジューラ
**エンジンアダプタタイプ**: `trino`

注: Trino は SQLMesh の [状態接続](../../reference/configuration.md#connections) には使用できません。

## インストール
```
pip install "sqlmesh[trino]"
```

認証に Oauth を使用している場合は、キーリング キャッシュをインストールすることをお勧めします。
```
pip install "trino[external-authentication-token-cache]"
```

### Trino コネクタのサポート

Trino エンジンアダプタは、[Hive コネクタ](https://trino.io/docs/current/connector/hive.html)、[Iceberg コネクタ](https://trino.io/docs/current/connector/iceberg.html)、[Delta Lake コネクタ](https://trino.io/docs/current/connector/delta-lake.html) でテストされています。

別のコネクタをご利用になりたい場合、または別のコネクタを試したことがある場合は、[Slack](https://tobikodata.com/slack) でお知らせください。

#### Hive コネクタの設定

推奨される Hive カタログプロパティの設定 (`<catalog_name>.properties`):

```properties linenums="1"
hive.metastore-cache-ttl=0s
hive.metastore-refresh-interval=5s
hive.metastore-timeout=10s
hive.allow-drop-table=true
hive.allow-add-column=true
hive.allow-drop-column=true
hive.allow-rename-column=true
hive.allow-rename-table=true
```

#### Iceberg コネクタの設定

Iceberg カタログに Hive メタストアを使用している場合、[プロパティ](https://trino.io/docs/current/connector/metastores.html#general-metastore-configuration-properties) は Hive コネクタとほぼ同じです。

```properties linenums="1"
iceberg.catalog.type=hive_metastore
# metastore properties as per the Hive Connector Configuration above
```

**注**: Trino Iceberg コネクタは、ビューをサポートする `iceberg.catalog.type` で構成する必要があります。この記事の執筆時点では、`hive_metastore`、`glue`、`rest` がこれに該当します。

`jdbc` および `nessie` アイスバーグカタログタイプはビューをサポートしていないため、SQLMesh と互換性がありません。

!!! info "Nessie"

    Nessie は、Iceberg REST カタログ (`iceberg.catalog.type=rest`) として使用する場合にサポートされます。
    Trino Iceberg コネクタをこの目的で設定する方法の詳細については、[Nessie ドキュメント](https://projectnessie.org/nessie-latest/trino/) を参照してください。

#### Delta Lakeコネクタの設定

TrinoアダプタのDelta Lakeコネクタは、Hiveメタストアカタログタイプでのみテストされています。

[プロパティファイル](https://trino.io/docs/current/connector/delta-lake.html#general-configuration)には、その他の[一般プロパティ](https://trino.io/docs/current/object-storage/metastores.html#general-metastore-properties)に加えて、HiveメタストアのURIとカタログ名を含める必要があります。

``` properties linenums="1"
hive.metastore.uri=thrift://example.net:9083
delta.hive-catalog-name=datalake_delta # example catalog name, can be any valid string
```

#### AWS Glue

[AWS Glue](https://aws.amazon.com/glue/) は、Hive メタストアカタログの実装を提供します。

Trino プロジェクトの物理データオブジェクトは、[AWS S3](https://aws.amazon.com/s3/) バケットなどの特定の場所に保存されます。Hive はデフォルトの場所を提供しますが、設定ファイルで上書きできます。

プロジェクトのテーブルのデフォルトの場所は、Hive カタログ設定の [`hive.metastore.glue.default-warehouse-dir` パラメータ](https://trino.io/docs/current/object-storage/metastores.html#aws-glue-catalog-configuration-properties) で設定します。

例:

```linenums="1"
hive.metastore=glue
hive.metastore.glue.default-warehouse-dir=s3://my-bucket/
```

### 接続オプション

| オプション | 説明 | タイプ | 必須 |
|--------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:------:|:--------:|
| `type` | エンジンタイプ名 - `trino` である必要があります | 文字列 | Y |
| `user` | クラスターにログインするためのユーザー名（アカウントのユーザー名）。Starburst Galaxy クラスターに接続する場合は、ユーザー名のサフィックスとしてユーザーのロールを含める必要があります。 | 文字列 | Y |
| `host` | クラスターのホスト名。`http://` または `https://` プレフィックスを含めないでください。 | 文字列 | Y |
| `catalog` | クラスター内のカタログ名。 | 文字列 | Y |
| `http_scheme` | クラスターへの接続時に使用する HTTP スキーム。デフォルトでは `https` で、認証なしまたは基本認証の場合は `http` のみになります。 | 文字列 | N |
| `port` | クラスターに接続するためのポート。デフォルトでは、`https` スキームの場合は `443`、`http` の場合は `80` です。 | int | N |
| `roles` | カタログ名とロールのマッピング | dict | N |
| `http_headers` | 各リクエストで送信する追加の HTTP ヘッダー。 | dict | N |
| `session_properties` | Trino セッション プロパティ。すべてのオプションを表示するには、`SHOW SESSION` を実行します。 | dict | N |
| `retries` | リクエストが失敗した場合に試行する再試行回数。デフォルト: `3` | int | N |
| `timezone` | 接続に使用するタイムゾーン。デフォルト: クライアント側のローカル タイムゾーン | 文字列 | N |
| `schema_location_mapping` | スキーマ作成時に `LOCATION` プロパティに使用する S3 の場所への正規表現パターンのマッピング。詳細については、[テーブルとスキーマの場所](#table-and-schema-locations) を参照してください。 | dict | N |
| `catalog_type_overrides` | カタログ名とコネクタタイプとのマッピング。これは、コネクタ固有の動作を有効/無効にするために使用されます。詳細については、[カタログタイプのオーバーライド](#catalog-type-overrides) を参照してください。 | dict | N |

## テーブルとスキーマの場所

ストレージから分離されたコネクタ（Iceberg、Hive、Delta コネクタなど）を使用する場合、新しいテーブルを作成する際に、Trino はテーブルデータを書き込む物理ストレージ内の場所を認識する必要があります。

この場所はメタストア内のテーブルに対して保存されるため、データを読み取ろうとするすべてのエンジンは、どこを参照すればよいかを知ることができます。

### デフォルトの動作

Trino では、[Metastore](https://trino.io/docs/current/object-storage/metastores.html) レベルで `default-warehouse-dir` プロパティをオプションで設定できます。オブジェクト作成時に、Trino はスキーマの場所を `<default warehouse dir>/<schema name>`、テーブルの場所を `<default warehouse dir>/<schema name>/<table name>` と推測します。

ただし、このプロパティを設定しない場合でも、*schema* の場所が明示的に設定されていれば、Trino はテーブルの場所を推測できます。

例えば、スキーマ作成時に `LOCATION` プロパティを次のように指定した場合:

```sql
CREATE SCHEMA staging_data
WITH (LOCATION = 's3://warehouse/production/staging_data')
```

すると、そのスキーマで作成されたすべてのテーブルの場所は、`<schema location>/<table name>` として推測されます。

メタストア設定で `default-warehouse-dir` を指定せず、スキーマ作成時にスキーマの場所も指定しない場合は、テーブル作成時に明示的にテーブルの場所を指定する必要があります。そうしないと、Trino はエラーを生成します。

特定の場所にテーブルを作成することは、特定の場所にスキーマを作成することと非常によく似ています。

```sql
CREATE TABLE staging_data.customers (customer_id INT)
WITH (LOCATION = 's3://warehouse/production/staging_data/customers')
```

### SQLMesh での設定

SQLMesh では、SQLMesh がテーブルとスキーマを作成する際に `LOCATION` プロパティに使用する値を設定できます。この設定は、クラスター構成に基づいて Trino が推測する値をオーバーライドします。

#### スキーマ

SQLMesh が `CREATE SCHEMA` ステートメントを発行する際に指定する `LOCATION` プロパティを設定するには、`schema_location_mapping` 接続プロパティを使用します。これは、SQLMesh が作成するすべてのスキーマ（内部スキーマも含む）に適用されます。

最も簡単な例は、`default-warehouse-dir` をエミュレートすることです。

```yaml title="config.yaml"
gateways:
  trino:
    connection:
      type: trino
      ...
      schema_location_mapping:
        '.*': 's3://warehouse/production/@{schema_name}'
```

これにより、すべてのスキーマが作成され、その場所が `s3://warehouse/production/<schema name>` に設定されます。テーブルの場所は Trino によって `s3://warehouse/production/<schema name>/<table name>` と推測されるため、すべてのオブジェクトは実質的に `s3://warehouse/production/` 以下に作成されます。

モデルで `<catalog>.<schema>.<name>` のような 3 部構成の完全修飾名を使用している場合、`schema_location_mapping` 正規表現に照合される文字列は `<schema>` 自体ではなく `<catalog>.<schema>` になります。これにより、同じスキーマ名が複数のカタログで使用されている場合でも、異なる場所を設定できます。

モデルで `<schema>.<table>` のような 2 部構成名を使用している場合、`<schema>` 部分のみが正規表現に照合されます。

例を挙げます。

```yaml title="config.yaml"
gateways:
  trino:
    connection:
      type: trino
      ...
      schema_location_mapping:
        '^utils$': 's3://utils-bucket/@{schema_name}'
        '^landing\..*$': 's3://raw-data/@{catalog_name}/@{schema_name}'
        '^staging.*$': 's3://bucket/@{schema_name}_dev'
        '^sqlmesh.*$': 's3://sqlmesh-internal/dev/@{schema_name}'
```

これにより、以下のマッピングが実行されます。

-  `sales` というスキーマは、どのパターンにも一致しないため、場所にマッピングされません。これは `LOCATION` プロパティなしで作成されます。
- `utils` というスキーマは、`^utils$` パターンに直接一致するため、`s3://utils-bucket/utils` という場所にマッピングされます。
- `landing` というカタログ内の `transactions` というスキーマは、`landing.transactions` という文字列が `^landing\..*$` パターンに一致するため、`s3://raw-data/landing/transactions` という場所にマッピングされます。
- `staging_customers` と `staging_accounts` というスキーマは、`^staging.*$` パターンに一致するため、それぞれ `s3://bucket/staging_customers_dev` と `s3://bucket/staging_accounts_dev` という場所にマッピングされます。
- `staging` というカタログ内の `accounts` というスキーマは、`s3://bucket/accounts_dev` という場所にマッピングされます。文字列 `staging.accounts` は `^staging.*$` パターンに一致します。
- `sqlmesh__staging_customers` および `sqlmesh__staging_utils` というスキーマは、`^sqlmesh.*$` パターンに一致するため、それぞれ `s3://sqlmesh-internal/dev/sqlmesh__staging_customers` および `s3://sqlmesh-internal/dev/sqlmesh__staging_utils` にマッピングされます。

!!! info "Placeholders"

    マッピング値には、`@{catalog_name}` および `@{schema_name}` プレースホルダーを使用できます。

    いずれかのパターンに一致する場合、SQLMesh が `CREATE SCHEMA` ステートメントで使用するカタログ/スキーマがこれらのプレースホルダーに置き換えられます。

    これらのプレースホルダーを参照する際は、中括弧構文 `@{}` を使用することに注意してください。詳細については、[こちら](../../concepts/macros/sqlmesh_macros.md#embedding-variables-in-strings) をご覧ください。

#### テーブル

多くの場合、明示的にテーブルの場所を設定する必要はありません。スキーマの場所を明示的に設定している場合、Trino はスキーマの場所のサブディレクトリをテーブルの場所として自動的に推測します。

ただし、必要に応じて、モデルの `physical_properties` に `location` プロパティを追加することで、明示的にテーブルの場所を設定できます。

[@resolve_template](../../concepts/macros/sqlmesh_macros.md#resolve_template) マクロを使用して、モデルバージョンごとに一意のテーブルの場所を生成する必要があることに注意してください。そうしないと、すべてのモデルバージョンが同じ場所に書き込まれ、互いに上書きされてしまいます。

```sql hl_lines="5"
MODEL (
  name staging.customers,
  kind FULL,
  physical_properties (
    location = @resolve_template('s3://warehouse/@{catalog_name}/@{schema_name}/@{table_name}')
  )
);

SELECT ...
```

これにより、SQLMesh は `CREATE TABLE` ステートメントを発行する際に、指定された `LOCATION` を設定します。

## カタログタイプのオーバーライド

SQLMesh は、`system.metadata.catalogs` テーブルをクエリし、`connector_name` 列をチェックすることで、カタログのコネクタタイプを判別しようとします。
コネクタ名が、Hive コネクタの動作の場合は `hive` であるか、Iceberg コネクタの動作の場合は `iceberg` または `delta_lake` を含んでいるかどうかを確認します。
ただし、カスタムコネクタや既存のコネクタのフォークを使用している場合など、コネクタ名だけでコネクタタイプを判別できるとは限りません。
このようなケースに対処するには、`catalog_type_overrides` 接続プロパティを使用して、特定のカタログのコネクタタイプを明示的に指定できます。
たとえば、`datalake` カタログが Iceberg コネクタを使用し、`analytics` カタログが Hive コネクタを使用するように指定するには、次のように接続を構成できます。

```yaml title="config.yaml"
gateways:
  trino:
    connection:
      type: trino
      ...
      catalog_type_overrides:
        datalake: iceberg
        analytics: hive
```

## 認証

=== "No Auth"

    | オプション | 説明 | タイプ | 必須 |
    |-----------|------------------------------------------|:------:|:--------:|
    | `method` | `no-auth` (デフォルト) | 文字列 | N |

    ```yaml linenums="1"
    gateway_name:
      connection:
        type: trino
        user: [user]
        host: [host]
        catalog: [catalog]
        # Most likely you will want http for scheme when not using auth
        http_scheme: http
    ```


=== "Basic Auth"

    | オプション | 説明 | タイプ | 必須 |
    | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | :----: | :------: |
    | `method` | `basic` | 文字列 | Y |
    | `password` | 認証時に使用するパスワード。 | 文字列 | Y |
    | `verify` | SSL 検証を行うかどうかのブール値フラグ。デフォルト: [trinodb Python クライアント](https://github.com/trinodb/trino-python-client) デフォルト (執筆時点では `true`) | bool | N |


    ```yaml linenums="1"
    gateway_name:
      connection:
        type: trino
        method: basic
        user: [user]
        password: [password]
        host: [host]
        catalog: [catalog]
    ```

    * [Trino Basic認証に関するドキュメント](https://trino.io/docs/current/security/password-file.html)
    * [Pythonクライアント Basic認証](https://github.com/trinodb/trino-python-client#basic-authentication)

=== "LDAP"

    | オプション | 説明 | タイプ | 必須 |
    |----------------------|------------------------------------------------------------------------------------|:------:|:--------:|
    | `method` | `ldap` | 文字列 | Y |
    | `password` | 認証時に使用するパスワード。 | 文字列 | Y |
    | `impersonation_user` | 指定されたユーザー名を上書きします。これにより、別のユーザーを偽装できます。 | 文字列 | N |

    ```yaml linenums="1"
    gateway_name:
      connection:
        type: trino
        method: ldap
        user: [user]
        password: [password]
        host: [host]
        catalog: [catalog]
    ```

    * [LDAP認証に関するTrinoドキュメント](https://trino.io/docs/current/security/ldap.html)
    * [PythonクライアントLDAP認証](https://github.com/trinodb/trino-python-client#basic-authentication)

=== "Kerberos"

    | オプション | 説明 | タイプ | 必須 |
    |----------------------------------|-----------------------------------------------------------------------------------|:------:|:--------:|
    | `method` | `kerberos` | 文字列 | Y |
    | `keytab` | keytab へのパス。例: `/tmp/trino.keytab` | 文字列 | Y |
    | `krb5_config` | config へのパス。例: `/tmp/krb5.conf` | 文字列 | Y |
    | `principal` | プリンシパル。例: `user@company.com` | 文字列 | Y |
    | `service_name` | サービス名 (デフォルトは `trino`) | 文字列 | N |
    | `hostname_override` | DNS 名が一致しないホストの Kerberos ホスト名 | 文字列 | N |
    | `mutual_authentication` | 相互認証のブールフラグ。デフォルト: `false` | bool | N |
    | `force_preemptive` | Kerberos GSS 交換を事前に開始するためのブールフラグ。デフォルト: `false` | bool | N |
    | `sanitize_mutual_error_response` | エラー応答からコンテンツとヘッダーを削除するためのブールフラグ。デフォルト: `true` | bool | N |
    | `delegate` | 資格情報の委任 (`GSS_C_DELEG_FLAG`) のブールフラグ。デフォルト: `false` | bool | N |

    ```yaml linenums="1"
    gateway_name:
      connection:
        type: trino
        method: kerberos
        user: user
        keytab: /tmp/trino.keytab
        krb5_config: /tmp/krb5.conf
        principal: trino@company.com
        host: trino.company.com
        catalog: datalake
    ```

    * [Kerberos認証に関するTrinoドキュメント](https://trino.io/docs/current/security/kerberos.html)
    * [PythonクライアントKerberos認証](https://github.com/trinodb/trino-python-client#kerberos-authentication)

=== "JWT"

    | オプション | 説明 | タイプ | 必須 |
    |------------|-----------------|:------:|:--------:|
    | `method` | `jwt` | 文字列 | Y |
    | `jwt_token` | JWT 文字列。 | 文字列 | Y |

    ```yaml linenums="1"
    gateway_name:
      connection:
        type: trino
        method: jwt
        user: [user]
        password: [password]
        host: [host]
        catalog: [catalog]
    ```

    * [JWT認証に関するTrinoドキュメント](https://trino.io/docs/current/security/jwt.html)
    * [PythonクライアントJWT認証](https://github.com/trinodb/trino-python-client#jwt-authentication)

=== "Certificate"

    | オプション | 説明 | タイプ | 必須 |
    |----------------------|---------------------------------------------------|:------:|:--------:|
    | `method` | `certificate` | 文字列 | Y |
    | `cert` | 証明書ファイルへのフルパス | 文字列 | Y |
    | `client_certificate` | クライアント証明書へのパス。例: `/tmp/client.crt` | 文字列 | Y |
    | `client_private_key` | クライアント秘密鍵へのパス。例: `/tmp/client.key` | 文字列 | Y |

    ```yaml linenums="1"
    gateway_name:
      connection:
        type: trino
        method: certificate
        user: [user]
        password: [password]
        host: [host]
        catalog: [catalog]
        cert: [path/to/cert_file]
        client_certificate: [path/to/client/cert]
        client_private_key: [path/to/client/key]
    ```

=== "Oauth"

    | オプション | 説明 | タイプ | 必須 |
    |----------------------|---------------------------------------------------|:------:|:--------:|
    | `method` | `oauth` | 文字列 | Y |

    ```yaml linenums="1"
    gateway_name:
      connection:
        type: trino
        method: oauth
        host: trino.company.com
        catalog: datalake
    ```

    * [OAuth認証に関するTrinoドキュメント](https://trino.io/docs/current/security/oauth2.html)
    * [PythonクライアントOAuth認証](https://github.com/trinodb/trino-python-client#oauth2-authentication)
