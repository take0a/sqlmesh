# 概要

## ツール

SQLMesh は以下のツールとの統合をサポートしています。

* [dbt](dbt.md)
* [dlt](dlt.md)
* [GitHub Actions](github.md)
* [Kestra](https://kestra.io/plugins/plugin-sqlmesh/tasks/cli/io.kestra.plugin.sqlmesh.cli.sqlmeshcli)

## 実行エンジン

SQLMesh は、SQLMesh プロジェクトを実行するために次の実行エンジンをサポートしています (括弧内のエンジンの `type` - 使用例: `pip install "sqlmesh[databricks]"`):

* [Athena](./engines/athena.md) (athena)
* [Azure SQL](./engines/azuresql.md) (azuresql)
* [BigQuery](./engines/bigquery.md) (bigquery)
* [ClickHouse](./engines/clickhouse.md) (clickhouse)
* [Databricks](./engines/databricks.md) (databricks)
* [DuckDB](./engines/duckdb.md) (duckdb)
* [Fabric](./engines/fabric.md) (fabric)
* [MotherDuck](./engines/motherduck.md) (motherduck)
* [MSSQL](./engines/mssql.md) (mssql)
* [MySQL](./engines/mysql.md) (mysql)
* [Postgres](./engines/postgres.md) (postgres)
* [GCP Postgres](./engines/gcp-postgres.md) (gcppostgres)
* [Redshift](./engines/redshift.md) (redshift)
* [Snowflake](./engines/snowflake.md) (snowflake)
* [Spark](./engines/spark.md) (spark)
* [Trino](./engines/trino.md) (trino)
