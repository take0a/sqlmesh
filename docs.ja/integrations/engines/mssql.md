# MSSQL

## インストール

### ユーザー/パスワード認証:
```
pip install "sqlmesh[mssql]"
```
### Microsoft Entra ID / Azure Active Directory 認証:
```
pip install "sqlmesh[mssql-odbc]"
```

## 一意キーによる増分 `MERGE`

SQLMesh は `MERGE` ステートメントを実行し、[一意キーによる増分](../../concepts/models/model_kinds.md#incremental_by_unique_key) モデル種別の行を挿入します。

デフォルトでは、`MERGE` ステートメントは、同じキー値を持つ新しい行が挿入されると、既存の行のキー以外のすべての列を更新します。2 つの行のすべての列値が一致する場合、これらの更新は不要です。

SQLMesh は、列の値を `EXISTS` 演算子と `EXCEPT` 演算子で比較することで不要な更新をスキップするオプションのパフォーマンス最適化機能を提供しています。

この最適化を有効にするには、`MODEL` ステートメントの [`physical_properties`](../../concepts/models/overview.md#physical_properties) セクションで `mssql_merge_exists` キーを `true` に設定します。

例えば：

```sql linenums="1" hl_lines="7-9"
MODEL (
    name sqlmesh_example.unique_key,
    kind INCREMENTAL_BY_UNIQUE_KEY (
        unique_key id
    ),
    cron '@daily',
    physical_properties (
        mssql_merge_exists = true
    )
);
```

!!! warning "すべての列タイプがサポートされているわけではありません"

    `mssql_merge_exists` 最適化は、`GEOMETRY`、`XML`、`TEXT`、`NTEXT`、`IMAGE`、およびほとんどのユーザー定義型を含むすべての列型ではサポートされていません。

    詳細については、[MSSQL `EXCEPT` ステートメントのドキュメント](https://learn.microsoft.com/en-us/sql/t-sql/language-elements/set-operators-except-and-intersect-transact-sql?view=sql-server-ver17#arguments) をご覧ください。

## ローカル/組み込みスケジューラ
**エンジンアダプタタイプ**: `mssql`

### 接続オプション

| オプション | 説明 | タイプ | 必須 |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :----------: | :------: |
| `type` | エンジンタイプ名 - `mssql` である必要があります | 文字列 | Y |
| `host` | MSSQL サーバーのホスト名 | 文字列 | Y |
| `user` | MSSQL サーバーでの認証に使用するユーザー名 / クライアント ID | 文字列 | N |
| `password` | MSSQL サーバーでの認証に使用するパスワード / クライアントシークレット | 文字列 | N |
| `port` | MSSQL サーバーのポート番号 | int | N |
| `database` | ターゲットデータベース | 文字列 | N |
| `charset` | 接続に使用する文字セット | 文字列 | N |
| `timeout` | クエリのタイムアウト（秒）。デフォルト: タイムアウトなし | int | N |
| `login_timeout` | 接続およびログインのタイムアウト (秒)。 デフォルト: 60 | int | N |
| `appname` | 接続に使用するアプリケーション名 | string | N |
| `conn_properties` | 接続プロパティのリスト | list[string] | N |
| `autocommit` | 自動コミット モードが有効かどうか。 デフォルト: false | bool | N |
| `driver` | 接続に使用するドライバー。 デフォルト: pymssql | string | N |
| `driver_name` | 接続に使用するドライバー名 (例: *ODBC Driver 18 for SQL Server*)。 | string | N |
| `odbc_properties` | ODBC 接続プロパティ (例: *authentication: ActiveDirectoryServicePrincipal*)。詳細については、[こちら](https://learn.microsoft.com/en-us/sql/connect/odbc/dsn-connection-string-attribute?view=sql-server-ver16) を参照してください。 | dict | N |