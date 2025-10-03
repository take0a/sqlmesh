# Azure SQL

[Azure SQL](https://azure.microsoft.com/en-us/products/azure-sql) は、「Azure クラウドで SQL Server データベース エンジンを使用する、管理された安全なインテリジェントな製品ファミリです。」

## ローカル/組み込みスケジューラー
**エンジン アダプターの種類**: `azuresql`

### インストール
#### ユーザー/パスワード認証:
```
pip install "sqlmesh[azuresql]"
```
#### Microsoft Entra ID/Azure Active Directory 認証:
```
pip install "sqlmesh[azuresql-odbc]"
```

### 接続オプション

| オプション | 説明 | 種類 | 必須 |
| ----------------- | ---------------------------------------------------------------- | :----------: | :------: |
| `type` | エンジンの種類名 - `azuresql` である必要があります | 文字列 | Y |
| `host` | Azure SQL Server のホスト名 | 文字列 | Y |
| `user` | Azure SQL Server での認証に使用するユーザー名 / クライアント ID | 文字列 | N |
| `password` | Azure SQL Server での認証に使用するパスワード / クライアント シークレット | 文字列 | N |
| `port` | Azure SQL Server のポート番号 | int | N |
| `database` | ターゲット データベース | 文字列 | N |
| `charset` | 接続に使用する文字セット | 文字列 | N |
| `timeout` | クエリのタイムアウト (秒)。既定値: タイムアウトなし | int | N |
| `login_timeout` | 接続およびログインのタイムアウト (秒)。既定値: 60 | int | N |
| `appname` | 接続に使用するアプリケーション名 | 文字列 | N |
| `conn_properties` | 接続プロパティのリスト | list[string] | N |
| `autocommit` | 自動コミット モードが有効かどうか。既定値: false | bool | N |
| `driver` | 接続に使用するドライバー。既定値: pymssql | 文字列 | N |
| `driver_name` | 接続に使用するドライバー名。例: *ODBC Driver 18 for SQL Server* | 文字列 | N |
| `odbc_properties` | ODBC 接続プロパティの辞書。例: 認証: ActiveDirectoryServicePrincipal。詳細については、[こちら](https://learn.microsoft.com/en-us/sql/connect/odbc/dsn-connection-string-attribute?view=sql-server-ver16) を参照してください。 | dict | N |