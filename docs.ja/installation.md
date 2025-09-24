# インストール

このページでは、SQLMesh をコンピューターにインストールする手順を説明します。

## Python 仮想環境

SQLMesh では Python 仮想環境の使用が推奨されますが、必須ではありません。

まず、仮想環境を作成します。
```bash
python -m venv .venv
```

次にそれをアクティブ化します。
```bash
source .venv/bin/activate
```

## SQLMesh コアのインストール

`pip` を使用して SQLMesh コアライブラリをインストールします。
```bash
pip install sqlmesh
```

## エクストラのインストール
SQLMesh の一部の機能には、追加の Python ライブラリが必要です。これらのライブラリは、SQLMesh に「エクストラ」としてバンドルされています。

`pip` コマンドでエクストラの名前を括弧で囲んで指定すると、追加ライブラリが自動的にインストールされます。たとえば、SQLMesh Github CI/CD ボットのエクストラをインストールするには、「pip install "sqlmesh[github]"」と入力します。

エクストラには 2 種類あります。

SQLMesh VSCode 拡張機能や Github CI/CD ボットなど、一部のエクストラは機能を追加します。

??? info "機能追加コマンド"
    | 機能 | `pip` コマンド |
    | ------------------- | ------------------------------- |
    | VSCode extension    | `pip install "sqlmesh[lsp]"`    |
    | Github CI/CD bot    | `pip install "sqlmesh[github]"` |
    | dbt projects        | `pip install "sqlmesh[dbt]"`    |
    | dlt projects        | `pip install "sqlmesh[dlt]"`    |
    | Slack notifications | `pip install "sqlmesh[slack]"`  |
    | Development setup   | `pip install "sqlmesh[dev]"`    |
    | Browser UI          | `pip install "sqlmesh[web]"`    |
    | LLM SQL prompt      | `pip install "sqlmesh[llm]"`    |

Bigquery や Postgres などの特定の SQL エンジンを使用するには、その他の追加機能も必要です。

??? info "SQLエンジンの追加コマンド"
    | SQL エンジン | `pip` コマンド |
    | ------------- | ------------------------------------ |
    | Athena        | `pip install "sqlmesh[athena]"`      |
    | Azure SQL     | `pip install "sqlmesh[azuresql]"`    |
    | Bigquery      | `pip install "sqlmesh[bigquery]"`    |
    | ClickHouse    | `pip install "sqlmesh[clickhouse]"`  |
    | Databricks    | `pip install "sqlmesh[databricks]"`  |
    | GCP Postgres  | `pip install "sqlmesh[gcppostgres]"` |
    | MS SQL Server | `pip install "sqlmesh[mssql]"`       |
    | MySQL         | `pip install "sqlmesh[mysql]"`       |
    | Postgres      | `pip install "sqlmesh[postgres]"`    |
    | Redshift      | `pip install "sqlmesh[redshift]"`    |
    | RisingWave    | `pip install "sqlmesh[risingwave]"`  |
    | Snowflake     | `pip install "sqlmesh[snowflake]"`   |
    | Trino         | `pip install "sqlmesh[trino]"`       |

`pip install "sqlmesh[github,slack]"` のように、複数の追加機能を一度にインストールできます。

## 次のステップ

SQLMesh をインストールしたら、SQLMesh サンプルプロジェクトを使い始めましょう。

SQLMesh には 3 つのユーザーインターフェースがあります。サンプルプロジェクトで 1 つを選択して、すぐに使い始めてください。

- [コマンドラインインターフェース (CLI)](./quickstart/cli.md)
- [ノートブックインターフェース](./quickstart/notebook.md)
- [ブラウザ UI グラフィカルインターフェース](./quickstart/ui.md)

実行したい既存の dbt プロジェクトをお持ちですか？ dbt エクストラをインストールし、[SQLMesh の dbt アダプターを確認してください](./integrations/dbt.md)。