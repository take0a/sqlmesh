# Fabric

!!! info

    Fabricエンジンアダプタはコミュニティからの貢献です。そのため、コミュニティによるサポートは限定的なものとなります。

## ローカル/組み込みスケジューラ
**エンジンアダプタタイプ**: `fabric`

注: SQLMesh [状態接続](../../reference/configuration.md#connections) には Fabric Warehouse の使用は推奨されません。

### インストール
#### Microsoft Entra ID / Azure Active Directory 認証:

```
pip install "sqlmesh[fabric]"
```

### 接続オプション

| オプション | 説明 | タイプ | 必須 |
| ----------------- | ---------------------------------------------------------- | :---------: | :------: |
| `type` | エンジンタイプ名 - `fabric` である必要があります | 文字列 | Y |
| `host` | Fabric Warehouse サーバーのホスト名 | 文字列 | Y |
| `user` | Fabric Warehouse サーバーでの認証に使用するクライアント ID | 文字列 | N |
| `password` | Fabric Warehouse サーバーでの認証に使用するクライアントシークレット | 文字列 | N |
| `port` | Fabric Warehouse サーバーのポート番号 | int | N |
| `database` | ターゲットデータベース | 文字列 | N |
| `charset` | 接続に使用する文字セット | 文字列 | N |
| `timeout` | クエリのタイムアウト値 (秒)。デフォルト: タイムアウトなし | int | N |
| `login_timeout` | 接続およびログインのタイムアウト (秒)。既定値: 60 | int | N |
| `appname` | 接続に使用するアプリケーション名 | 文字列 | N |
| `conn_properties` | 接続プロパティのリスト | list[string] | N |
| `autocommit` | 自動コミット モードが有効かどうか。既定値: false | bool | N |
| `driver` | 接続に使用するドライバー。既定値: pyodbc | 文字列 | N |
| `driver_name` | 接続に使用するドライバー名。例: *ODBC Driver 18 for SQL Server* | 文字列 | N |
| `tenant_id` | Azure / Entra テナント UUID | 文字列 | Y |
| `workspace_id` | Fabric ワークスペース UUID。これを取得するには、Python ノートブックで `notebookutils.runtime.context.get("currentWorkspaceId")` を実行することをお勧めします。| string | Y |
| `odbc_properties` | ODBC 接続プロパティの辞書。例: 認証: ActiveDirectoryServicePrincipal。詳細については、[こちら](https://learn.microsoft.com/en-us/sql/connect/odbc/dsn-connection-string-attribute?view=sql-server-ver16) を参照してください。| dict | N |