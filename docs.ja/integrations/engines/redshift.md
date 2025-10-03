# Redshift

## ローカル/組み込みスケジューラ
**エンジンアダプタタイプ**: `redshift`

### インストール
```
pip install "sqlmesh[redshift]"
```

### 接続オプション

| オプション | 説明 | タイプ | 必須 |
|------------------------|----------------------------------------------------------------------------------------------------------------------------|:-------:|:--------:|
| `type` | エンジンタイプ名 - `redshift` である必要があります | 文字列 | Y |
| `user` | Amazon Redshift クラスターでの認証に使用するユーザー名 | 文字列 | N |
| `password` | Amazon Redshift クラスターでの認証に使用するパスワード | 文字列 | N |
| `database` | 接続するデータベースインスタンスの名前 | 文字列 | N |
| `host` | Amazon Redshift クラスターのホスト名 | 文字列 | N |
| `port` | Amazon Redshift クラスターのポート番号 | int | N |
| `ssl` | SSL が有効かどうか。IAM を使用して認証する場合は SSL が有効になっている必要があります (デフォルト: `True`) | bool | N |
| `sslmode` | Amazon Redshift クラスターへの接続のセキュリティ。`verify-ca` と `verify-full` がサポートされています。 | 文字列 | N |
| `timeout` | サーバーへの接続がタイムアウトするまでの秒数。 | int | N |
| `tcp_keepalive` | [TCP キープアライブ](https://en.wikipedia.org/wiki/Keepalive#TCP_keepalive) が使用されているかどうか。(デフォルト: `True`) | bool | N |
| `application_name` | アプリケーションの名前 | 文字列 | N |
| `preferred_role` | 現在の接続に優先する IAM ロール | 文字列 | N |
| `principal_arn` | ポリシーを生成する IAM エンティティ (ユーザーまたはロール) の ARN | 文字列 | N |
| `credentials_provider` | Amazon Redshift クラスターでの認証に使用される IdP のクラス名 | 文字列 | N |
| `region` | Amazon Redshift クラスターの AWS リージョン | 文字列 | N |
| `cluster_identifier` | Amazon Redshift クラスターのクラスター識別子 | 文字列 | N |
| `iam` | IAM 認証が有効な場合。IdP を使用して認証する場合、IAM は True である必要があります | dict | N |
| `is_serverless` | Amazon Redshift クラスターがサーバーレスの場合 (デフォルト: `False`) | bool | N |
| `serverless_acct_id` | サーバーレスクラスターのアカウント ID | 文字列 | N |
| `serverless_work_group` | サーバーレスエンドポイントのワークグループの名前 | 文字列 | N |
| `enable_merge` | incremental_by_unique_key モデルの種類で、ネイティブの Redshift MERGE 操作を使用するか、SQLMesh の論理マージを使用するか。 (デフォルト: `False`) | bool | N |

## パフォーマンスに関する考慮事項

### タイムスタンプマクロ変数とソートキー

`TIMESTAMP` ソートキーを持つ Redshift テーブルを操作する場合、標準の `@start_dt` および `@end_dt` マクロ変数を使用するとパフォーマンス上の問題が発生する可能性があります。これらのマクロは SQL クエリで `TIMESTAMP WITH TIME ZONE` 値としてレンダリングされるため、`TIMESTAMP`（タイムゾーンなし）ソートキーでフィルタリングする際に Redshift が効率的なプルーニングを実行できなくなります。

その結果、テーブル全体のスキャンが実行され、パフォーマンスが大幅に低下する可能性があります。

**解決策**: マクロ変数の `_dtntz` (datetime no timezone) バリアントを使用します。

- `@start_dt` ではなく `@start_dtntz`
- `@end_dt` ではなく `@end_dtntz`

これらのバリアントは `TIMESTAMP WITHOUT TIME ZONE` としてレンダリングされるため、Redshift はソートキーの最適化を適切に利用できます。

**例**：

```sql linenums="1"
-- Inefficient: May cause full table scan
SELECT * FROM my_table
WHERE timestamp_column >= @start_dt
  AND timestamp_column < @end_dt

-- Efficient: Uses sort key optimization
SELECT * FROM my_table
WHERE timestamp_column >= @start_dtntz
  AND timestamp_column < @end_dtntz

-- Alternative: Cast to timestamp
SELECT * FROM my_table
WHERE timestamp_column >= @start_ts::timestamp
  AND timestamp_column < @end_ts::timestamp
```
