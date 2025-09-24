# モデルガイド

## 前提条件

---

モデルを追加する前に、[プロジェクトを作成済み](./projects.md)であること、[開発環境](../concepts/environments.md)で作業していることを確認してください。

---

## モデルの追加

モデルを追加するには：

1. `models` フォルダ内に新しいファイルを作成します。例えば、[quickstart](../quick_start.md) プロジェクトに `new_model.sql` を追加します。
2. ファイル内にモデルを定義します。例：

        MODEL (
          name sqlmesh_example.new_model,
          kind INCREMENTAL_BY_TIME_RANGE (
            time_column (model_time_column, '%Y-%m-%d'),
          ),
        );

        SELECT *
        FROM sqlmesh_example.incremental_model
        WHERE model_time_column BETWEEN @start_ds and @end_ds

    **注:** モデルが増分型の場合、このファイルの最後の行は必須です。作成可能なモデルの種類の詳細については、[モデルの種類](../concepts/models/model_kinds.md)を参照してください。

## 既存モデルの編集

既存モデルを編集するには：

1. 編集したいモデルファイルを任意のエディタで開き、変更を加えます。
2. 実際にテーブルを作成せずに変更内容を確認するには、`sqlmesh evaluate` コマンドを使用します。以下の[モデルの評価](#evaluating-a-model)を参照してください。
3. この変更を反映するには、`sqlmesh plan` コマンドを使用します。以下の[`plan` コマンドを使用した変更のプレビュー](#previewing-changes-using-the-plan-command)を参照してください。

### モデルの評価

`evaluate` コマンドは、データベースまたはエンジンに対してクエリを実行し、データフレームを返します。SQLMesh はデータをマテリアライズしないため、データベースへの副作用がなく、コストも最小限でモデルのテストや反復処理を行うことができます。

モデルを評価するには:

1. [CLI](../reference/cli.md) または [Notebook](../reference/notebook.md) を使用して `evaluate` コマンドを実行します。例えば、[quickstart](../quick_start.md) プロジェクトの `incremental_model` に対して `evaluate` コマンドを実行すると、次のようになります。

        $ sqlmesh evaluate sqlmesh_example.incremental_model --start=2020-01-07 --end=2020-01-07

        id  item_id          model_time_column
        0   7        1  2020-01-07

2. `evaluate` コマンドを実行すると、SQLMesh はモデルに加えられた変更を検出し、`evaluate` に渡されたオプションを使用してモデルをクエリとして実行し、モデル クエリによって返された出力を表示します。

### `plan` コマンドを使用した変更のプレビュー

SQLMesh が環境に対して `plan` コマンドを実行すると、変更によって下流のモデルが影響を受けるかどうかが表示されます。影響を受ける場合、SQLMesh は変更を適用する前に、変更を [破壊的](../concepts/plans.md#breaking-change) または [非破壊的](../concepts/plans.md#non-breaking-change) に分類するよう促します。

`plan` を使用して変更をプレビューするには:

1. `sqlmesh plan <environment name>` コマンドを入力します。
2. 変更を `破壊的` に分類する場合は `1` を、変更を `非破壊的` に分類する場合は `2` を入力します。この例では、変更は `非破壊的` に分類されています。

```bash linenums="1" hl_lines="27-28"
$ sqlmesh plan dev
======================================================================
Successfully Ran 1 tests against duckdb
----------------------------------------------------------------------
New environment `dev` will be created from `prod`

Differences from the `prod` environment:

Models
├── Directly Modified:
│   └── sqlmesh_example.incremental_model
└── Indirectly Modified:
    └── sqlmesh_example.full_model
---
+++
@@ -1,6 +1,7 @@
SELECT
id,
item_id,
+  1 AS new_column,
model_time_column
FROM (VALUES
(1, 1, '2020-01-01'),
Directly Modified: sqlmesh_example.incremental_model
└── Indirectly Modified Children:
    └── sqlmesh_example.full_model
[1] [Breaking] Backfill sqlmesh_example.incremental_model and indirectly modified children
[2] [Non-breaking] Backfill sqlmesh_example.incremental_model but not indirectly modified children: 2
Models needing backfill (missing dates):
└── sqlmesh_example.incremental_model: (2020-01-01, 2023-02-17)
Enter the backfill start date (eg. '1 year', '2020-01-01') or blank for the beginning of history:
Enter the backfill end date (eg. '1 month ago', '2020-01-01') or blank to backfill up until now:
Apply - Backfill Tables [y/n]: y

sqlmesh_example__dev.incremental_model ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100.0% • 1/1 • 0:00:00

All model batches have been executed successfully

Virtually Updating 'dev' ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100.0% • 0:00:00

The target environment has been updated successfully
```

詳細については、[プラン](../concepts/plans.md) を参照してください。

## モデルへの変更を元に戻す

---

変更を元に戻す前に、変更が既に行われており、`sqlmesh plan` コマンドが実行されていることを確認してください。

---

変更を元に戻すには：

1. 編集したいモデルファイルを任意のエディタで開き、先ほど行った変更を元に戻します。この例では、[クイックスタート](../quick_start.md) の例で追加した列を削除します。
2. `sqlmesh plan` を実行し、変更を適用します。仮想更新を実行するには `y` と入力します。

```bash linenums="1" hl_lines="26"
$ sqlmesh plan dev
======================================================================
Successfully Ran 1 tests against duckdb
----------------------------------------------------------------------
Differences from the `dev` environment:

Models
├── Directly Modified:
│   └── sqlmesh_example.incremental_model
└── Indirectly Modified:
    └── sqlmesh_example.full_model
---
+++
@@ -1,7 +1,6 @@

SELECT
id,
item_id,
-  1 AS new_column,
model_time_column
FROM (VALUES
    (1, 1, '2020-01-01'),
Directly Modified: sqlmesh_example.incremental_model (Non-breaking)
└── Indirectly Modified Children:
    └── sqlmesh_example.full_model
Apply - Virtual Update [y/n]: y

Virtual Update executed successfully
```
### 仮想更新

以前のモデルバージョンへの復元は、追加の作業が不要なため、短時間で完了します。詳細については、[プランの適用](../concepts/plans.md#plan-application)および[仮想更新](../concepts/plans.md#virtual-update)を参照してください。

**注:** SQLMesh Janitor は定期的に自動的に実行され、使用されなくなった SQLMesh アーティファクトをクリーンアップし、テーブルの有効期限 (TTL) (復元ができなくなるまでの時間) を決定します。

## モデルの変更の検証

### 自動モデル検証

SQLMesh は、データの品質と精度を確保するために、モデルを自動的に検証します。これは、以下の方法で実行されます。

* `plan` コマンドを実行すると、デフォルトでユニットテストを実行します。これにより、あらゆる環境に適用されたすべての変更が論理的に検証されます。詳細については、[テスト](../concepts/tests.md) を参照してください。
* データがテーブルにロードされるたびに監査を実行します（バックフィル用または定期的なロード用）。これにより、あらゆるテーブルに存在するすべてのデータが、定義されたすべての監査に合格したことを確認できます。詳細については、[監査](../concepts/audits.md) を参照してください。

SQLMesh は、プレビュー環境を自動的に作成することで、CI/CD による自動検証も提供します。

### 手動モデル検証

モデルを手動で検証するには、以下のタスクのいずれか、または複数を実行できます。

* [モデルの評価](#evaluating-a-model)
* [ユニットテストを使用したモデルのテスト](../guides/testing.md#auditing-changes-to-models)
* [モデルの監査](../guides/testing.md#auditing-changes-to-models)
* [`plan` コマンドを使用した変更のプレビュー](#previewing-changes-using-the-plan-command)

## モデルの削除

---

モデルを削除する前に、`sqlmesh plan` を実行済みであることを確認してください。

---

モデルを削除するには:

1. `models` ディレクトリ内のモデルと、`tests` ディレクトリ内の関連テストを含むファイルを削除します。この例では、[quickstart](../quick_start.md) プロジェクトから `models/full_model.sql` ファイルと `tests/test_full_model.yaml` ファイルを削除します。
2. 変更を適用する環境を指定して、`sqlmesh plan <environment>` コマンドを実行します。この例では、開発環境 `dev` に変更を適用します。

        ```bash linenums="1"
        $ sqlmesh plan dev
        ======================================================================
        Successfully Ran 0 tests against duckdb
        ----------------------------------------------------------------------
        Differences from the `dev` environment:

        Models
        └── Removed Models:
            └── sqlmesh_example.full_model
        Apply - Virtual Update [y/n]: y
        Virtually Updating 'dev' ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100.0% • 0:00:00

        The target environment has been updated successfully


        Virtual Update executed successfully
        ```

    **注:** 削除したいモデルを参照する他のファイル（テストなど）がある場合は、エラーメッセージに参照を含むファイルが表示されます。変更を適用するには、これらのファイルも削除する必要があります。

3. 変更を計画し、本番環境に適用し、仮想更新のために `y` と入力します。デフォルトでは、`sqlmesh plan` コマンドは本番環境を対象とします。

        ```bash linenums="1"
        $ sqlmesh plan
        ======================================================================
        Successfully Ran 0 tests against duckdb
        ----------------------------------------------------------------------
        Differences from the `prod` environment:

        Models
        └── Removed Models:
            └── sqlmesh_example.full_model
        Apply - Virtual Update [y/n]: y
        Virtually Updating 'prod' ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100.0% • 0:00:00

        The target environment has been updated successfully


        Virtual Update executed successfully
        ```

4. 出力から `full_model.sql` モデルが削除されたことを確認します。

## プロジェクトのモデルのDAGの表示

---

DAGを生成する前に、graphvizパッケージがインストールされていることを確認してください。

`pip`を使ってパッケージをインストールするには、以下のコマンドを入力します。

```bash
pip install graphviz
```

あるいは、次のコマンドを入力して、`apt-get` を使用して graphviz をインストールします。

```bash
sudo apt-get install graphviz
```

---

DAG を表示するには、次のコマンドを入力します:

`sqlmesh dag FILE`

プロジェクトの DAG を含む HTML ファイルがプロジェクトフォルダのルートに配置されます。このファイルをブラウザで開くと、DAG を表示できます。