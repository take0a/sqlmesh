# Snowflake

このページでは、Snowflake SQL エンジンで SQLMesh を使用する方法について説明します。

まずは、Snowflake への接続方法を示す [接続クイックスタート](#connection-quickstart) から始めます。または、[組み込み](#localbuilt-in-scheduler) を使用して Snowflake を使用する方法の情報に直接進むこともできます。

## 接続クイックスタート

クラウドウェアハウスへの接続にはいくつかの手順が必要です。この接続クイックスタートでは、Snowflake を使い始めるために必要な情報を提供します。

SQLMesh にバンドルされている `snowflake-connector-python` ライブラリを使用して Snowflake に接続する方法を説明します。

Snowflake は、接続を認証するための複数の方法（パスワード、SSO など）を提供しています。このクイックスタートではパスワードによる認証方法を説明しますが、その他の方法の設定については[以下で説明](#snowflake-authorization-methods) します。

!!! tip

    このクイックスタートは、SQLMesh の基本的なコマンドと機能に精通していることを前提としています。

    まだ習得していない場合は、先に [SQLMesh クイックスタート](../../quick_start.md) をお読みください。

### 前提条件

この接続クイックスタートを実行する前に、以下の点を確認してください。

1. Snowflakeアカウントをお持ちで、ユーザー名とパスワードを把握していること。
2. Snowflakeアカウントに、計算実行に使用できる[ウェアハウス](https://docs.snowflake.com/en/user-guide/warehouses-overview)が少なくとも1つあること。
3. コンピューターに[SQLMeshがインストール](../../installation.md)され、[Snowflakeエクストラが利用可能](../../installation.md#install-extras)になっていること。
    - コマンドラインからコマンド `pip install "sqlmesh[snowflake]"` を使用してインストールすること。
4. コンピューターで[SQLMeshサンプルプロジェクト](../../quickstart/cli#1-create-the-sqlmesh-project)を初期化していること。
    - コマンドラインインターフェースを開き、プロジェクトファイルを配置するディレクトリに移動すること。
    - コマンド `sqlmeshスノーフレークを初期化する

### アクセス制御権限

SQLMesh には、さまざまな種類のデータベースオブジェクトを作成およびアクセスするための十分な権限が必要です。

SQLMesh のコア機能には、次のような比較的広範な権限が必要です。

1. データベース内のスキーマを作成および削除する権限
2. 作成したスキーマ内のテーブルとビューを作成、変更、削除、およびクエリする権限

プロジェクトでマテリアライズドビューまたは動的テーブルを使用している場合、SQLMesh にはこれらのオブジェクトタイプを作成、変更、削除、およびクエリする権限も必要です。

ここでは、SQLMesh に適切な権限を付与する方法について説明します。

#### Snowflake のロール

Snowflake では、ユーザーに直接権限を付与することも、「ロール」を作成して権限を割り当て、そのロールをユーザーに付与することもできます。

ロールは、複数のユーザーに権限セットをまとめて付与するための便利な方法です。このクイックスタートでは、ロールを作成してユーザーに権限を付与します。

ロールには、計算を実行できるように、ウェアハウスに対する `USAGE` 権限を付与する必要があります。その他の権限については、以下で説明します。

#### データベース権限
Snowflake の最上位オブジェクトコンテナは「データベース」（他のエンジンでは「カタログ」と呼ばれることが多い）です。SQLMesh はデータベースを作成する権限を必要とせず、既存のデータベースを使用できます。

SQLMesh にデータベースに対する十分な権限を付与する最も簡単な方法は、必要なすべての権限を含むデータベースの `OWNERSHIP` を付与することです。

あるいは、SQLMesh がデータベース内で操作するすべてのアクションとオブジェクトに対して、きめ細かな権限を付与することもできます。

#### 権限の付与

このセクションでは、`sqlmesh` ロールを作成し、適切な権限を付与してユーザーに付与するサンプルコードを示します。

このコードは、`USERADMIN` レベル以上の権限を持つユーザーが実行する必要があります。このコードには、ロールにデータベースの `OWNERSHIP` 権限を付与するバージョンと付与しないバージョンの 2 つのバージョンがあります。

どちらの例でも、`sqlmesh` というロールを作成し、ウェアハウス `compute_wh` の使用権限を付与し、`demo_db` というデータベースを作成し、そのロールをユーザー `demo_user` に割り当てます。データベースが既に存在する場合は、データベースを作成する手順は省略できます。

=== "With database ownership"

    ```sql linenums="1"
    USE ROLE useradmin; -- This code requires USERADMIN privileges or higher

    CREATE ROLE sqlmesh; -- Create role for permissions
    GRANT USAGE ON WAREHOUSE compute_wh TO ROLE sqlmesh; -- Can use warehouse

    CREATE DATABASE demo_db; -- Create database for SQLMesh to use (omit if database already exists)
    GRANT OWNERSHIP ON DATABASE demo_db TO ROLE sqlmesh; -- Role owns database

    GRANT ROLE sqlmesh TO USER demo_user; -- Grant role to user
    ALTER USER demo_user SET DEFAULT ROLE = sqlmesh; -- Make role user's default role
    ```

=== "Without database ownership"

    ```sql linenums="1"
    USE ROLE useradmin; -- This code requires USERADMIN privileges or higher

    CREATE ROLE sqlmesh; -- Create role for permissions
    CREATE DATABASE demo_db; -- Create database for SQLMesh to use (omit if database already exists)

    GRANT USAGE ON WAREHOUSE compute_wh TO ROLE sqlmesh; -- Can use warehouse
    GRANT USAGE ON DATABASE demo_db TO ROLE sqlmesh; -- Can use database

    GRANT CREATE SCHEMA ON DATABASE demo_db TO ROLE sqlmesh; -- Can create SCHEMAs in database
    GRANT USAGE ON FUTURE SCHEMAS IN DATABASE demo_db TO ROLE sqlmesh; -- Can use schemas it creates
    GRANT CREATE TABLE ON FUTURE SCHEMAS IN DATABASE demo_db TO ROLE sqlmesh; -- Can create TABLEs in schemas
    GRANT CREATE VIEW ON FUTURE SCHEMAS IN DATABASE demo_db TO ROLE sqlmesh; -- Can create VIEWs in schemas
    GRANT SELECT, INSERT, TRUNCATE, UPDATE, DELETE ON FUTURE TABLES IN DATABASE demo_db TO ROLE sqlmesh; -- Can SELECT and modify TABLEs in schemas
    GRANT REFERENCES, SELECT ON FUTURE VIEWS IN DATABASE demo_db TO ROLE sqlmesh; -- Can SELECT and modify VIEWs in schemas

    GRANT ROLE sqlmesh TO USER demo_user; -- Grant role to user
    ALTER USER demo_user SET DEFAULT ROLE = sqlmesh; -- Make role user's default role
    ```

### 接続情報を取得する

ユーザーに十分なアクセス権限が付与されたので、SQLMesh 接続を構成するために必要な情報を収集する準備が整いました。

#### アカウント名

Snowflake の接続構成には、SQLMesh が接続する Snowflake アカウントを識別する `account` パラメーターが必要です。

Snowflake アカウント識別子は、組織名とアカウント名の 2 つの要素で構成されます。どちらも Snowflake ウェブインターフェースの URL に埋め込まれており、`/` で区切られています。

これは、Snowflake アカウントにログインしたときに表示されるデフォルトのビューで、アカウント識別子の 2 つの要素が表示されています。

![ウェブ URL 内の Snowflake アカウント情報](./snowflake/snowflake_db-guide_account-url.png){ loading=lazy }

この例では、組織名は `idapznw`、アカウント名は `wq29399` です。

SQLMesh の `account` パラメーターでは、2 つの要素を `-` で区切って連結し、`idapznw-wq29399` とします。

#### ウェアハウス名

Snowflake アカウントでは複数のウェアハウスが利用可能になっている場合があります。このクイックスタートでは計算をほとんど実行しないため、どのウェアハウスでも問題ありません。

一部の Snowflake ユーザーアカウントでは、接続時に自動的に使用されるデフォルトのウェアハウスが設定されている場合があります。

接続構成の `warehouse` パラメーターは必須ではありませんが、ユーザーのデフォルトのウェアハウスが変更されても SQLMesh の動作が変化しないように、構成でウェアハウスを明示的に指定することをお勧めします。

#### データベース名

Snowflake ユーザーアカウントには、接続時に自動的に使用されるデフォルトのデータベースを含む「デフォルトの名前空間」が設定されている場合があります。

接続構成の `database` パラメータは必須ではありませんが、ユーザーのデフォルトの名前空間が変更されても SQLMesh の動作が変化しないように、構成でデータベースを明示的に指定することをお勧めします。

### 接続を構成する

これで、SQLMesh から Snowflake への接続を構成するために必要な情報が揃いました。

構成を開始するには、まず、サンプル プロジェクトの config.yaml ファイルに `snowflake` という名前のゲートウェイを追加し、それを `default_gateway` にします。

```yaml linenums="1" hl_lines="2-6"
gateways:
  snowflake:
    connection:
      type: snowflake

default_gateway: snowflake

model_defaults:
  dialect: snowflake
  start: 2024-07-24
```

上記の情報を使用して、`account`、`user`、`password`、`database`、および `warehouse` 接続パラメータを指定します。

```yaml linenums="1" hl_lines="5-9"
gateways:
  snowflake:
    connection:
      type: snowflake
      account: idapznw-wq29399
      user: DEMO_USER
      password: << password here >>
      database: DEMO_DB
      warehouse: COMPUTE_WH

default_gateway: snowflake

model_defaults:
  dialect: snowflake
  start: 2024-07-24
```

!!! warning

    パスワードなどのシークレット情報を保存するベストプラクティスは、[設定ファイルが動的に読み込む環境変数](../../guides/configuration.md#environment-variables)に配置することです。簡潔にするため、このガイドでは設定ファイルに直接値を設定します。

    以下のコードは、設定ファイルの「password」パラメータに環境変数「SNOWFLAKE_PASSWORD」を使用する方法を示しています。

    ```yaml linenums="1" hl_lines="5"
    gateways:
      snowflake:
        connection:
          type: snowflake
          password: {{ env_var('SNOWFLAKE_PASSWORD') }}
    ```

### 接続の確認

`snowflake` ゲートウェイの接続情報を指定したので、SQLMesh が Snowflake に正常に接続できることを確認できます。`sqlmesh info` コマンドで接続をテストします。

まず、コマンドラインターミナルを開きます。`sqlmesh info` コマンドを入力します。

![Run sqlmesh info command in CLI](./snowflake/snowflake_db-guide_sqlmesh-info.png){ loading=lazy }

出力は、データ ウェアハウスの接続が成功したことを示しています。

![Successful data warehouse connection](./snowflake/snowflake_db-guide_sqlmesh-info-succeeded.png){ loading=lazy }

ただし、出力には、SQLMesh の状態を保存するために Snowflake SQL エンジンを使用することに関する  `WARNING` が含まれます。

![Snowflake state connection warning](./snowflake/snowflake_db-guide_sqlmesh-info-warning.png){ loading=lazy }

!!! warning

    Snowflake はトランザクションワークロード向けに設計されていないため、テスト環境であっても SQLMesh の状態を保存するために使用しないでください。

    SQLMesh の状態の保存の詳細については、[こちら](../../guides/configuration.md#state-connection) をご覧ください。

### 状態接続の指定

`snowflake` ゲートウェイで `state_connection` を指定することで、SQLMesh の状態を別の SQL エンジンに保存できます。

この例では、DuckDB エンジンを使用して、ローカルの `snowflake_state.db` ファイルに状態を保存しています。

```yaml linenums="1" hl_lines="10-12"
gateways:
  snowflake:
    connection:
      type: snowflake
      account: idapznw-wq29399
      user: DEMO_USER
      password: << your password here >>
      database: DEMO_DB
      warehouse: COMPUTE_WH
    state_connection:
      type: duckdb
      database: snowflake_state.db

default_gateway: snowflake

model_defaults:
  dialect: snowflake
  start: 2024-07-24
```

これで、`sqlmesh info` の実行時に警告が表示されなくなり、新しいエントリ `State backend connection successful` が表示されます。

![No state connection warning](./snowflake/snowflake_db-guide_sqlmesh-info-no-warning.png){ loading=lazy }

### `sqlmesh plan` を実行する

これで、Snowflake で `sqlmesh plan` を実行する準備が整いました。

![Run sqlmesh plan in snowflake](./snowflake/snowflake_db-guide_sqlmesh-plan.png){ loading=lazy }

スキーマとオブジェクトが Snowflake カタログに存在することを確認します。

![Sqlmesh plan objects in snowflake](./snowflake/snowflake_db-guide_sqlmesh-plan-objects.png){ loading=lazy }

おめでとうございます。SQLMesh プロジェクトが Snowflake 上で稼働しています。

### 行数はどこに表示されますか？

SQLMesh は、各モデルで処理された行数を `plan` および `run` ターミナル出力で報告します。

ただし、Snowflake Python コネクタの制限により、`CREATE TABLE AS` ステートメントの行数を特定できません。そのため、SQLMesh は `FULL` モデルなど、特定の種類のモデルの行数を報告しません。

コネクタの制限の詳細については、[Github](https://github.com/snowflakedb/snowflake-connector-python/issues/645) をご覧ください。

## ローカル/組み込みスケジューラ
**エンジンアダプタタイプ**: `snowflake`

### インストール
```
pip install "sqlmesh[snowflake]"
```

### 接続オプション

| オプション | 説明 | タイプ | 必須 |
|-------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:------:|:--------:|
| `type` | エンジンタイプ名 - `snowflake` である必要があります | 文字列 | Y |
| `account` | Snowflake アカウント名 | 文字列 | Y |
| `user` | Snowflake ユーザー名 | 文字列 | N |
| `password` | Snowflake パスワード | 文字列 | N |
| `authenticator` | Snowflake 認証方式 | 文字列 | N |
| `warehouse` | Snowflake ウェアハウス名 | 文字列 | N |
| `database` | Snowflake データベース名 | 文字列 | N |
| `role` | Snowflake ロール名 | 文字列 | N |
| `token` | Snowflake OAuth 2.0 アクセス トークン | 文字列 | N |
| `private_key` | 認証に使用するオプションの秘密キー。キーは、Base64 エンコードされた DER 形式 (キー バイトを表す)、プレーンテキストの PEM 形式、またはバイト (Python 構成のみ) にすることができます。 | 文字列 | N |
| `private_key_path` | 認証に使用する秘密キーへのオプションのパス。これは `private_key` の代わりに使用されます。 | 文字列 | N |
| `private_key_passphrase` | `private_key` (PEM 形式の場合) または `private_key_path` を復号化するために使用するオプションのパスフレーズ。キーは暗号化なしで作成できるため、必要な場合にのみ指定してください。 | 文字列 | N |
| `session_parameters` | 接続に設定するオプションのセッション パラメーター。 | dict | N |


### 小文字のオブジェクト名

Snowflakeのオブジェクト名は、デフォルトでは大文字と小文字が区別されず、自動的に大文字に変換されます。たとえば、コマンド `CREATE SCHEMA sqlmesh` は、Snowflake に `SQLMESH` という名前のスキーマを生成します。

大文字と小文字が区別される小文字の名前を持つオブジェクトを作成する必要がある場合、SQLコードでは名前を二重引用符で囲む必要があります。SQLMesh設定ファイルでは、外側の単一引用符も必要です。

たとえば、データベース `"my_db"` への接続には次の内容が含まれます。

``` yaml
connection:
  type: snowflake
  <other connection options>
  database: '"my_db"' # outer single and inner double quotes
```

### Snowflake の認証方法

Snowflake への接続を認証する最も簡単な方法（ただし、安全性は最も低いと言えるでしょう）は、ユーザー名とパスワードを使用することです。

このセクションでは、他の認証方法の設定方法について説明します。

#### Snowflake SSO 認証

SQLMesh は、`externalbrowser` 認証方法を使用した Snowflake SSO 認証接続をサポートしています。例:

```yaml
gateways:
  snowflake:
    connection:
      type: snowflake
      account: ************
      user: ************
      authenticator: externalbrowser
      warehouse: ************
      database: ************
      role: ************
```

#### Snowflake OAuth 認証

SQLMesh は、`oauth` 認証メソッドを使用した Snowflake OAuth 認証接続をサポートしています。例:

=== "YAML"

    ```yaml linenums="1"
    gateways:
      snowflake:
        connection:
          type: snowflake
          account: account
          user: user
          authenticator: oauth
          token: eyJhbGciOiJSUzI1NiIsImtpZCI6ImFmZmM...
    ```

=== "Python"

    ```python linenums="1"
    config = Config(
        model_defaults=ModelDefaultsConfig(dialect="snowflake"),
        gateways={
           "my_gateway": GatewayConfig(
                connection=SnowflakeConnectionConfig(
                    user="user",
                    account="account",
                    authenticator="oauth",
                    token="eyJhbGciOiJSUzI1NiIsImtpZCI6ImFmZmM...",
                ),
            ),
        }
    )
    ```

#### Snowflake 秘密キー認証

SQLMesh は、秘密キーをパス、Base64 エンコードされた DER 形式（キーバイトを表す）、プレーンテキストの PEM 形式、またはバイト（Python のみ）として提供することで、Snowflake 秘密キー認証接続をサポートします。

これらの各メソッドには、`account` および `user` パラメーターが必要です。

__秘密キーのパス__

注: `private_key_passphrase` は、キーがパスフレーズで暗号化されている場合にのみ必要です。

=== "YAML"

    ```yaml linenums="1"
    gateways:
      snowflake:
        connection:
          type: snowflake
          account: account
          user: user
          private_key_path: '/path/to/key.key'
          private_key_passphrase: supersecret
    ```

=== "Python"

    ```python linenums="1"
    config = Config(
        model_defaults=ModelDefaultsConfig(dialect="snowflake"),
        gateways={
           "my_gateway": GatewayConfig(
                connection=SnowflakeConnectionConfig(
                    user="user",
                    account="account",
                    private_key_path="/path/to/key.key",
                    private_key_passphrase="supersecret",
                ),
            ),
        }
    )
    ```


__秘密鍵 PEM__

注: `private_key_passphrase` は、鍵がパスフレーズで暗号化されている場合にのみ必要です。

=== "YAML"

    ```yaml linenums="1"
    gateways:
      snowflake:
        connection:
          type: snowflake
          account: account
          user: user
          private_key: |
            -----BEGIN PRIVATE KEY-----
            ...
            -----END PRIVATE KEY-----
          private_key_passphrase: supersecret
    ```

=== "Python"

    ```python linenums="1"
    config = Config(
        model_defaults=ModelDefaultsConfig(dialect="snowflake"),
        gateways={
           "my_gateway": GatewayConfig(
                connection=SnowflakeConnectionConfig(
                    user="user",
                    account="account",
                    private_key="""
                    -----BEGIN PRIVATE KEY-----
                    ...
                    -----END PRIVATE KEY-----""",
                    private_key_passphrase="supersecret",
                ),
            ),
        }
    )
    ```


__秘密鍵 Base64__

注: これは、PEM ファイルの内容ではなく、鍵自体のバイト列を Base64 でエンコードしたものです。

=== "YAML"

    ```yaml linenums="1"
    gateways:
      snowflake:
        connection:
          type: snowflake
          account: account
          user: user
          private_key: 'MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCvMKgsYzoDMnl7QW9nWTzAMMQToyUTslgKlH9MezcEYUvvCv+hYEsY9YGQ5dhI5MSY1vkQ+Wtqc6KsvJQzMaHDA1W+Z5R/yA/IY+Mp2KqJijQxnp8XjZs1t6Unr0ssL2yBjlk2pNOZX3w4A6B6iwpkqUi/HtqI5t2M15FrUMF3rNcH68XMcDa1gAasGuBpzJtBM0bp4/cHa18xWZZfu3d2d+4CCfYUvE3OYXQXMjJunidnU56NZtYlJcKT8Fmlw16fSFsPAG01JOIWBLJmSMi5qhhB2w90AAq5URuupCbwBKB6KvwzPRWn+fZKGAvvlR7P3CGebwBJEJxnq85MljzRAgMBAAECggEAKXaTpwXJGi6dD+35xvUY6sff8GHhiZrhOYfR5TEYYWIBzc7Fl9UpkPuyMbAkk4QJf78JbdoKcURzEP0E+mTZy0UDyy/Ktr+L9LqnbiUIn8rk9YV8U9/BB2KypQTY/tkuji85sDQsnJU72ioJlldIG3DxdcKAqHwznXz7vvF7CK6rcsz37hC5w7MTtguvtzNyHGkvJ1ZBTHI1vvGR/VQJoSSFkv6nLFs2xl197kuM2x+Ss539Xbg7GGXX90/sgJP+QLyNk6kYezekRt5iCK6n3UxNfEqd0GX03AJ1oVtFM9SLx0RMHiLuXVCKlQLJ1LYf8zOT31yOun6hhowNmHvpLQKBgQDzXGQqBLvVNi9gQzQhG6oWXxdtoBILnGnd8DFsb0YZIe4PbiyoFb8b4tJuGz4GVfugeZYL07I8TsQbPKFH3tqFbx69hENMUOo06PZ4H7phucKk8Er/JHW8dhkVQVg1ttTK8J5kOm+uKjirqN5OkLlUNSSJMblaEr9AHGPmTu21MwKBgQC4SeYzJDvq/RTQk5d7AwVEokgFk95aeyv77edFAhnrD3cPIAQnPlfVyG7RgPA94HrSAQ5Hr0PL2hiQ7OxX1HfP+66FMcTVbZwktYULZuj4NMxJqwxKbCmmzzACiPF0sibg8efGMY9sAmcQRw5JRS2s6FQns1MqeksnjzyMf3196wKBgFf8zJ5AjeT9rU1hnuRliy6BfQf+uueFyuUaZdQtuyt1EAx2KiEvk6QycyCqKtfBmLOhojVued/CHrc2SZ2hnmJmFbgxrN9X1gYBQLOXzRxuPEjENGlhNkxIarM7p/frva4OJ0ZXtm9DBrBR4uaG/urKOAZ+euRtKMa2PQxU9y7vAoGAeZWX4MnZFjIe13VojWnywdNnPPbPzlZRMIdG+8plGyY64Km408NX492271XoKoq9vWug5j6FtiqP5p3JWDD/UyKzg4DQYhdM2xM/UcR1k7wRw9Cr7TXrTPiIrkN3OgyHhgVTavkrrJDxOlYG4ORZPCiTzRWMmwvQJatkwTUjsD0CgYEA8nAWBSis9H8n9aCEW30pGHT8LwqlH0XfXwOTPmkxHXOIIkhNFiZRAzc4NKaefyhzdNlc7diSMFVXpyLZ4K0l5dY1Ou2xRh0W+xkRjjKsMib/s9g/crtam+tXddADJDokLELn5PAMhaHBpti+PpOMGqdI3Wub+5yT1XCXT9aj6yU='
    ```

=== "Python"

    ```python linenums="1"
    config = Config(
        model_defaults=ModelDefaultsConfig(dialect="snowflake"),
        gateways={
           "my_gateway": GatewayConfig(
                connection=SnowflakeConnectionConfig(
                    user="user",
                    account="account",
                    private_key="MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCvMKgsYzoDMnl7QW9nWTzAMMQToyUTslgKlH9MezcEYUvvCv+hYEsY9YGQ5dhI5MSY1vkQ+Wtqc6KsvJQzMaHDA1W+Z5R/yA/IY+Mp2KqJijQxnp8XjZs1t6Unr0ssL2yBjlk2pNOZX3w4A6B6iwpkqUi/HtqI5t2M15FrUMF3rNcH68XMcDa1gAasGuBpzJtBM0bp4/cHa18xWZZfu3d2d+4CCfYUvE3OYXQXMjJunidnU56NZtYlJcKT8Fmlw16fSFsPAG01JOIWBLJmSMi5qhhB2w90AAq5URuupCbwBKB6KvwzPRWn+fZKGAvvlR7P3CGebwBJEJxnq85MljzRAgMBAAECggEAKXaTpwXJGi6dD+35xvUY6sff8GHhiZrhOYfR5TEYYWIBzc7Fl9UpkPuyMbAkk4QJf78JbdoKcURzEP0E+mTZy0UDyy/Ktr+L9LqnbiUIn8rk9YV8U9/BB2KypQTY/tkuji85sDQsnJU72ioJlldIG3DxdcKAqHwznXz7vvF7CK6rcsz37hC5w7MTtguvtzNyHGkvJ1ZBTHI1vvGR/VQJoSSFkv6nLFs2xl197kuM2x+Ss539Xbg7GGXX90/sgJP+QLyNk6kYezekRt5iCK6n3UxNfEqd0GX03AJ1oVtFM9SLx0RMHiLuXVCKlQLJ1LYf8zOT31yOun6hhowNmHvpLQKBgQDzXGQqBLvVNi9gQzQhG6oWXxdtoBILnGnd8DFsb0YZIe4PbiyoFb8b4tJuGz4GVfugeZYL07I8TsQbPKFH3tqFbx69hENMUOo06PZ4H7phucKk8Er/JHW8dhkVQVg1ttTK8J5kOm+uKjirqN5OkLlUNSSJMblaEr9AHGPmTu21MwKBgQC4SeYzJDvq/RTQk5d7AwVEokgFk95aeyv77edFAhnrD3cPIAQnPlfVyG7RgPA94HrSAQ5Hr0PL2hiQ7OxX1HfP+66FMcTVbZwktYULZuj4NMxJqwxKbCmmzzACiPF0sibg8efGMY9sAmcQRw5JRS2s6FQns1MqeksnjzyMf3196wKBgFf8zJ5AjeT9rU1hnuRliy6BfQf+uueFyuUaZdQtuyt1EAx2KiEvk6QycyCqKtfBmLOhojVued/CHrc2SZ2hnmJmFbgxrN9X1gYBQLOXzRxuPEjENGlhNkxIarM7p/frva4OJ0ZXtm9DBrBR4uaG/urKOAZ+euRtKMa2PQxU9y7vAoGAeZWX4MnZFjIe13VojWnywdNnPPbPzlZRMIdG+8plGyY64Km408NX492271XoKoq9vWug5j6FtiqP5p3JWDD/UyKzg4DQYhdM2xM/UcR1k7wRw9Cr7TXrTPiIrkN3OgyHhgVTavkrrJDxOlYG4ORZPCiTzRWMmwvQJatkwTUjsD0CgYEA8nAWBSis9H8n9aCEW30pGHT8LwqlH0XfXwOTPmkxHXOIIkhNFiZRAzc4NKaefyhzdNlc7diSMFVXpyLZ4K0l5dY1Ou2xRh0W+xkRjjKsMib/s9g/crtam+tXddADJDokLELn5PAMhaHBpti+PpOMGqdI3Wub+5yT1XCXT9aj6yU=",
                ),
            ),
        }
    )
    ```

__秘密鍵バイト__

=== "YAML"

    バイトを Base64 でエンコードし、[秘密キー Base64](#private-key-base64) の指示に従います。

=== "Python"

    ```python
    from sqlmesh.core.config import (
        Config,
        GatewayConfig,
        ModelDefaultsConfig,
        SnowflakeConnectionConfig,
    )

    from cryptography.hazmat.primitives import serialization

    key = """-----BEGIN PRIVATE KEY-----
    ...
    -----END PRIVATE KEY-----""".encode()

    p_key= serialization.load_pem_private_key(key, password=None)

    pkb = p_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    config = Config(
        model_defaults=ModelDefaultsConfig(dialect="snowflake"),
        gateways={
           "my_gateway": GatewayConfig(
                connection=SnowflakeConnectionConfig(
                    user="user",
                    account="account",
                    private_key=pkb,
                ),
            ),
        }
    )
    ```

`private_key` が指定された場合、認証方法は `snowflake_jwt` であると想定されますが、接続構成で明示的に指定することもできます。

## 仮想ウェアハウスの設定

モデルが使用する Snowflake 仮想ウェアハウスは、モデル定義の `session_properties` 属性で指定できます。

```sql linenums="1"
MODEL (
  name schema_name.model_name,
  session_properties (
    'warehouse' = TEST_WAREHOUSE,
  ),
);
```

## カスタムビューとテーブルタイプ

SQLMesh は、Snowflake モデルのカスタムビューとテーブルタイプをサポートしています。これらの修飾子は、モデルの物理レイヤーまたは仮想レイヤーにそれぞれ `physical_properties` 属性と `virtual_properties` 属性を使用して適用できます。例:

### セキュアビュー

仮想レイヤーの `SECURE` ビューを通じてテーブルを公開するには、`creatable_type` プロパティを `SECURE` に設定します。

```sql linenums="1"
MODEL (
  name schema_name.model_name,
  virtual_properties (
      creatable_type = SECURE
  )
);

SELECT a FROM schema_name.model_b;
```

### 一時テーブル

モデルは、`creatable_type` プロパティを `TRANSIENT` に設定することで、物理レイヤーで `TRANSIENT` テーブルを使用できます。

```sql linenums="1"
MODEL (
  name schema_name.model_name,
  physical_properties (
      creatable_type = TRANSIENT
  )
);

SELECT a FROM schema_name.model_b;
```

### Iceberg テーブル

Snowflake で Iceberg テーブルを作成するには、Iceberg テーブルのデータを保存するための [外部ボリューム](https://docs.snowflake.com/en/user-guide/tables-iceberg-configure-external-volume) が設定されている必要があります。

設定が完了したら、次のように `table_format iceberg` を使用して、Iceberg テーブルを基盤とするモデルを作成できます。

```sql linenums="1" hl_lines="4 6-7"
MODEL (
  name schema_name.model_name,
  kind FULL,
  table_format iceberg,
  physical_properties (
    catalog = 'snowflake',
    external_volume = '<external volume name>'
  )
);
```

すべてのモデルで `catalog = 'snowflake'` と `external_volume = '<外部ボリューム名>'` を指定する必要がないようにするには、Snowflake のドキュメントで以下の項目を参照してください。

- [デフォルトのカタログの設定](https://docs.snowflake.com/en/user-guide/tables-iceberg-configure-catalog-integration#set-a-default-catalog-at-the-account-database-or-schema-level)
- [デフォルトの外部ボリュームの設定](https://docs.snowflake.com/en/user-guide/tables-iceberg-configure-external-volume#set-a-default-external-volume-at-the-account-database-or-schema-level)

または、[モデルのデフォルト](../../guides/configuration.md#model-defaults) を使用して、SQLMesh レベルでデフォルトを設定することもできます。代わりに、Snowflake が Iceberg テーブルで利用できるさまざまな [オプションのプロパティ](https://docs.snowflake.com/en/sql-reference/sql/create-iceberg-table-snowflake#optional-parameters) を利用するには、それらを `physical_properties` として指定するだけです。

```sql linenums="1" hl_lines="8"
MODEL (
  name schema_name.model_name,
  kind FULL,
  table_format iceberg,
  physical_properties (
    catalog = 'snowflake',
    external_volume = 'my_external_volume',
    base_location = 'my/product_reviews/'
  )
);
```

!!! warning "外部カタログ"

    SQLMesh は管理対象のテーブルに書き込み可能である必要があり、Snowflake は外部カタログで構成された Iceberg テーブルへの書き込みを [サポートしていません](https://docs.snowflake.com/en/user-guide/tables-iceberg#catalog-options) ため、Snowflake の内部カタログを使用するように `catalog = 'snowflake'` を設定するのが適切なデフォルト設定です。

    ただし、モデル内で外部カタログのテーブルを通常の [外部テーブル](../../concepts/models/external_models.md) として参照することは可能です。

## トラブルシューティング

### 頻繁な認証プロンプト

Snowflake を多要素認証 (MFA) などのセキュリティ機能と組み合わせて使用​​している場合、SQLMesh コマンドの実行中に認証プロンプトが繰り返し表示されることがあります。これは通常、Snowflake アカウントが短期トークンを発行するように設定されていない場合に発生します。

認証プロンプトを減らすには、Snowflake の接続設定でトークンのキャッシュを有効にできます。

- 一般的な認証については、[接続キャッシュに関するドキュメント](https://docs.snowflake.com/en/user-guide/admin-security-fed-auth-use#using-connection-caching-to-minimize-the-number-of-prompts-for-authentication-optional) をご覧ください。
- MFA について詳しくは、[MFA トークンのキャッシュに関するドキュメント](https://docs.snowflake.com/en/user-guide/security-mfa#using-mfa-token-caching-to-minimize-the-number-of-prompts-during-authentication-optional) をご覧ください。