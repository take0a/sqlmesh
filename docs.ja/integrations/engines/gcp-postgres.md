# GCP Postgres

## ローカル/組み込みスケジューラ
**エンジンアダプタタイプ**: `gcp_postgres`

### インストール
```
pip install "sqlmesh[gcppostgres]"
```

### 接続オプション

| オプション | 説明 | タイプ | 必須 |
|----------------------------|------------------------------------------------------------------------------------------------------|:---------:|:--------:|
| `type` | エンジンタイプ名 - `gcp_postgres` である必要があります | 文字列 | Y |
| `instance_connection_string` | Postgres インスタンスの接続名 | 文字列 | Y |
| `user` | 認証に使用するユーザー名（Postgres または IAM） | 文字列 | Y |
| `password` | 認証に使用するパスワード。Postgres ユーザーとして接続する場合は必須 | 文字列 | N |
| `enable_iam_auth` | IAM 認証を有効にします。IAM ユーザーとして接続する場合は必須 | ブール値 | N |
| `keyfile` | ADC の代わりに enable_iam_auth で使用するキーファイルへのパス | 文字列 | N |
| `keyfile_json` | キーファイルの情報はインラインで提供されます (非推奨) | dict | N |
| `db` | 接続先のデータベース インスタンスの名前 | 文字列 | Y |
| `ip_type` | 接続に使用する IP タイプ。`public`、`private`、または `psc` のいずれかである必要があります。デフォルト: `public` | 文字列 | N |
| `timeout` | 接続タイムアウト (秒)。デフォルト: `30` | 整数 | N |
| `scopes` | 接続に使用するスコープ。デフォルト: `(https://www.googleapis.com/auth/sqlservice.admin,)` | tuple[str] | N |
| `driver` | 接続に使用するドライバ。デフォルト: `pg8000`。注: `pg8000` のみがテストされています | 文字列 | N |