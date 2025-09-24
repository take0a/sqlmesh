# プロジェクトガイド

## プロジェクトの作成

---

始める前に、SQLMesh を使用するための [前提条件](../prerequisites.md) を満たしていることを確認してください。

---

コマンドラインからプロジェクトを作成するには、次の手順に従います。

1. プロジェクト用のディレクトリを作成します。

    ```bash
    mkdir my-project
    ```

2. 新しいプロジェクトのディレクトリへ移動します。

    ```bash
    cd my-project
    ```

    ここから、プロジェクト構造をゼロから作成することも、SQLMesh がスキャフォールディングして構築することもできます。このガイドでは、プロジェクトのスキャフォールディング方法を説明し、すぐにプロジェクトを立ち上げて実行できるようにします。

1. プロジェクトのスキャフォールディングを行うには、以下のコマンドを実行して Python 仮想環境を使用することをお勧めします。

    ```bash
    python -m venv .venv
    ```

    ```bash
    source .venv/bin/activate
    ```

    ```bash
    pip install sqlmesh
    ```

    **注:** Python 仮想環境を使用する場合は、まずその環境がアクティブ化されていることを確認する必要があります。コマンドラインに `(.venv)` が表示されるはずです。表示されない場合は、プロジェクトディレクトリから `source .venv/bin/activate` を実行して環境をアクティブ化してください。

1. 環境をアクティブ化したら、以下のコマンドを実行すると、SQLMesh によってプロジェクトがビルドされます。

    ```bash
    sqlmesh init [SQL_DIALECT]
    ```

    上記のコマンドでは、[sqlglot でサポートされている任意の SQL 方言](https://sqlglot.com/sqlglot/dialects.html)（例："duckdb"）を使用できます。

    SQLMesh プロジェクトを整理するために使用できる以下のディレクトリとファイルが作成されます。

    - config.py (データベース構成ファイル)
    - ./models (SQL および Python モデル)
    - ./audits (共有監査)
    - ./tests (ユニットテスト)
    - ./macros

## 既存プロジェクトの編集

既存プロジェクトを編集するには、編集したいプロジェクトファイルを任意のエディタで開きます。

CLI または Notebook を使用している場合は、`sqlmesh` コマンドに `-p` 変数を指定し、以下のようにプロジェクトのパスを指定することで、プロジェクト内のファイルを開いて編集できます。

```bash
sqlmesh -p <your-project-path>
```

詳細については、[CLI](../reference/cli.md) および [Notebook](../reference/notebook.md) を参照してください。

## プロジェクトのインポート

### dbt

dbt プロジェクトをインポートするには、次のように `sqlmesh init` コマンドに `dbt` フラグを指定します。

```bash
sqlmesh init -t dbt
```
