# Athena

## インストール

```
pip install "sqlmesh[athena]"
```

## 接続オプション

### PyAthena 接続オプション

SQLMesh は [PyAthena](https://github.com/laughingman7743/PyAthena) DBAPI ドライバーを使用して Athena に接続します。したがって、接続オプションは PyAthena の接続オプションと関連しています。
PyAthena は内部で [boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html) を使用しているため、設定には [boto3 環境変数](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html#using-environment-variables) も使用できます。

| Option                  | Description                                                                                                                                                  |  Type  | Required |
|-------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------|:------:|:--------:|
| `type` | エンジンタイプ名 - `athena` である必要があります | 文字列 | Y |
| `aws_access_key_id` | AWS ユーザーのアクセスキー | 文字列 | N |
| `aws_secret_access_key` | AWS ユーザーのシークレットキー | 文字列 | N |
| `role_arn` | 認証後に引き受けるロールの ARN | 文字列 | N |
| `role_session_name` | `role_arn` を引き受けるときに使用するセッション名 | 文字列 | N |
| `region_name` | 使用する AWS リージョン | 文字列 | N |
| `work_group` | クエリの送信先となる Athena [ワークグループ](https://docs.aws.amazon.com/athena/latest/ug/workgroups-manage-queries-control-costs.html) | 文字列 | N |
| `s3_staging_dir` | Athena がクエリ結果を書き込む S3 の場所です。`work_group` を使用していない場合、または設定された `work_group` に結果の場所が設定されていない場合にのみ必要です | 文字列 | N |
| `schema_name` | スキーマが指定されていない場合にオブジェクトを配置するデフォルトのスキーマ。デフォルトは `default` です | 文字列 | N |
| `catalog_name` | スキーマを配置するデフォルトのカタログ。デフォルトは `AwsDataCatalog` です | 文字列 | N |

### SQLMesh 接続オプション

これらのオプションは SQLMesh 自体に固有のものであり、PyAthena には渡されません。

| Option                  | Description                                                                                                                                                                                      | Type   | Required |
|-------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------|----------|
| `s3_warehouse_location` | SQLMesh が Athena にテーブルデータの配置を指示する S3 のベースパスを設定します。モデル自体で場所を指定していない場合にのみ必要です。下記の [S3 の場所](#s3-locations) を参照してください。 | 文字列 | N |

## モデルプロパティ

Athena アダプターは、以下のモデル最上位レベルの [プロパティ](../../concepts/models/overview.md#model-properties) を使用します。

| Name             | Description                                                                                                                                                                                                                                                                                                                          | Type   | Required |
|------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------|----------|
| `table_format` | Athena がテーブル作成時に使用する [table_type](https://docs.aws.amazon.com/athena/latest/ug/create-table-as.html#ctas-table-properties) を設定します。有効な値は `hive` または `iceberg` です。 | 文字列 | N |
| `storage_format` | `table_format` で使用するファイル形式を設定します。Hive テーブルの場合、これにより [STORED AS](https://docs.aws.amazon.com/athena/latest/ug/create-table.html#parameters) オプションが設定されます。Iceberg テーブルの場合、これにより [format](https://docs.aws.amazon.com/athena/latest/ug/create-table-as.html#ctas-table-properties) プロパティが設定されます。 | 文字列 | N |

Athena アダプターは次のモデル [physical_properties](../../concepts/models/overview.md#physical_properties) を認識します。

| Name              | Description                                                                                                                                                                               | Type   | Default |
|-------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------|---------|
| `s3_base_location`| このモデルのスナップショットテーブルを書き込む場所の `s3://` ベース URI。`s3_warehouse_location` が設定されている場合は、これを上書きします。| 文字列 | |


## S3 のロケーション
テーブルを作成する際、Athena はテーブルデータが S3 のどこに保存されているかを認識する必要があります。テーブルデータの `LOCATION` を指定せずに `CREATE TABLE` ステートメントを発行することはできません。

また、Trino などの他のエンジンとは異なり、Athena は `CREATE SCHEMA <schema> LOCATION 's3://schema/location'` でスキーマのロケーションを設定しても、テーブルの場所を推測しません。

したがって、SQLMesh が Athena に正しい `CREATE TABLE` ステートメントを発行するには、テーブルの保存場所を設定する必要があります。これには 2 つのオプションがあります。

- **プロジェクト全体:** 接続設定で `s3_warehouse_location` を設定します。SQLMesh は、モデルのスナップショットを作成する際に、テーブル `LOCATION` を `<s3_warehouse_location>/<schema_name>/<snapshot_table_name>` に設定します。
- **モデルごと:** モデルの `physical_properties` に `s3_base_location` を設定します。SQLMesh は、モデルのスナップショットを作成するたびに、テーブル `LOCATION` を `<s3_base_location>/<snapshot_table_name>` に設定します。これは、接続設定で設定された `s3_warehouse_location` よりも優先されます。


## 制限事項
Athena は当初、S3 に保存されたデータを読み取り、そのデータを変更せずに実行することを目的として設計されました。そのため、テーブルの変更に対するサポートは十分ではありません。特に、Hive テーブルからデータを削除することはできません。

Athena は Hive テーブルに対するスキーマ変更を非常に限定的にしかサポートしていないため、既存テーブルのスキーマを変更する [forward only changes](../../concepts/plans.md#forward-only-change) は失敗する可能性が高くなります。

ただし、Athena は [Apache Iceberg](https://docs.aws.amazon.com/athena/latest/ug/querying-iceberg.html) テーブルをサポートしており、あらゆる操作が可能です。これらは、[`INCREMENTAL_BY_UNIQUE_KEY`](../../concepts/models/model_kinds.md#incremental_by_unique_key) や [`SCD_TYPE_2`](../../concepts/models/model_kinds.md#scd-type-2) といった、より複雑なモデルタイプに使用できます。

モデルで Iceberg テーブルを使用するには、モデルの [properties](../../concepts/models/overview.md#model-properties) で `table_format iceberg` を設定します。

一般的に、Iceberg テーブルは最も柔軟性が高く、SQLMesh の制限も最も少なくなります。ただし、Athena はデフォルトで Hive テーブルを作成するため、Iceberg テーブルもデフォルトで作成されます。つまり、Iceberg テーブルはオプトアウトではなくオプトインです。
