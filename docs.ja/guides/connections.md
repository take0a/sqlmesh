# 接続ガイド

## 概要

モデルをデプロイし、変更を適用するには、データウェアハウスへの接続と、必要に応じて SQLMesh の状態が保存されているデータベースへの接続を構成する必要があります。これは、プロジェクトフォルダ内の `config.yaml` ファイル、または `~/.sqlmesh` ファイルで行うことができます。

各接続は、固有の名前が関連付けられたゲートウェイの一部として構成されます。ゲートウェイ名は、CLI を使用する際に特定の接続設定の組み合わせを選択するために使用できます。例:

```yaml linenums="1"
gateways:
  local_db:
    connection:
      type: duckdb
```

定義された接続は、次のように `sqlmesh plan` CLI コマンドで選択できます。

```bash
sqlmesh --gateway local_db plan
```

## 状態接続

デフォルトでは、データウェアハウス接続はSQLMeshの状態を保存するためにも使用されます。

状態接続は、ゲートウェイ構成の`state_connection`キーに異なる接続設定を指定することで変更できます。

```yaml linenums="1"
gateways:
  local_db:
    state_connection:
      type: duckdb
      database: state.db
```

注意: Spark および Trino エンジンは、状態接続には使用できません。

## デフォルト接続

さらに、`default_connection` キーで設定を定義することで、デフォルト接続を設定することもできます。

```yaml linenums="1"
default_connection:
  type: duckdb
  database: local.db
```

ターゲット ゲートウェイで接続構成が提供されていない場合は、この接続構成が使用されます。

## テスト接続

デフォルトでは、[テスト](../concepts/tests.md) を実行する際に、SQLMesh はメモリ内の DuckDB データベース接続を使用します。この動作は、ゲートウェイ設定の `test_connection` キーに接続設定を指定することでオーバーライドできます。

```yaml linenums="1"
gateways:
  local_db:
    test_connection:
      type: duckdb
      database: test.db
```

### デフォルトのテスト接続

すべてのゲートウェイのデフォルトのテスト接続を設定するには、`default_test_connection` キーを使用します。

```yaml linenums="1"
default_test_connection:
  type: duckdb
  database: test.db
```

## デフォルトゲートウェイ

ゲートウェイ名が指定されていない場合に CLI で使用されるデフォルトゲートウェイを変更するには、`default_gateway` キーに希望する名前を設定します。

```yaml linenums="1"
default_gateway: local_db
```

## サポートされているエンジン

* [BigQuery](../integrations/engines/bigquery.md)
* [Databricks](../integrations/engines/databricks.md)
* [DuckDB](../integrations/engines/duckdb.md)
* [MotherDuck](../integrations/engines/motherduck.md)
* [MySQL](../integrations/engines/mysql.md)
* [MSSQL](../integrations/engines/mssql.md)
* [Postgres](../integrations/engines/postgres.md)
* [GCP Postgres](../integrations/engines/gcp-postgres.md)
* [Redshift](../integrations/engines/redshift.md)
* [Snowflake](../integrations/engines/snowflake.md)
* [Spark](../integrations/engines/spark.md)
* [Trino](../integrations/engines/trino.md)
