# マルチリポジトリガイド

モノリポジトリは便利で使いやすいですが、組織によっては複数のリポジトリを使用することを選択する場合があります。
SQLMesh は複数のリポジトリをネイティブにサポートしており、複数のリポジトリがあってもデータの一貫性と正確性を容易に維持できます。
システム/データを分離したい場合は、[分離システムガイド](https://sqlmesh.readthedocs.io/en/stable/guides/isolated_systems/?h=isolated) をご覧ください。

## 複数プロジェクトのブートストラップ

複数のリポジトリでSQLMeshを設定するのは非常に簡単です。このサンプル[マルチリポジトリプロジェクト](https://github.com/TobikoData/sqlmesh/tree/main/examples/multi)の内容をコピーしてください。

プロジェクトをブートストラップするには、SQLMesh に両方のプロジェクトを指定します。

```
$ sqlmesh -p examples/multi/repo_1 -p examples/multi/repo_2/ plan
======================================================================
Successfully Ran 0 tests against duckdb
----------------------------------------------------------------------
`prod` environment will be initialized

Models
└── Added:
    ├── silver.d
    ├── bronze.a
    ├── bronze.b
    └── silver.c
Models needing backfill (missing dates):
├── bronze.a: (2023-04-17, 2023-04-17)
├── bronze.b: (2023-04-17, 2023-04-17)
├── silver.d: (2023-04-17, 2023-04-17)
└── silver.c: (2023-04-17, 2023-04-17)
Apply - Backfill Tables [y/n]: y
bronze.a ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100.0% • 1/1 • 0:00:00
silver.c ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100.0% • 1/1 • 0:00:00
bronze.b ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100.0% • 1/1 • 0:00:00
silver.d ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100.0% • 1/1 • 0:00:00

All model batches have been executed successfully

Virtually Updating 'prod' ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100.0% • 0:00:00

The target environment has been updated successfully
```

ブロンズが repo_1 にあり、シルバーが repo_2 にあるにもかかわらず、4 つのモデルすべてが計画され、適用されていることがわかります。

## 1つのプロジェクトの編集と計画

bronze.a に列 c を追加して、互換性に影響のない変更を加えます。

```
--- a/examples/multi/repo_1/models/a.sql
+++ b/examples/multi/repo_1/models/a.sql
@@ -4,4 +4,5 @@ MODEL (

 SELECT
   1 AS col_a,
-  'b' AS col_b
+  'b' AS col_b,
+  'c' AS col_c
```

repo_1 のみを使用してプランを実行します。

```
$ sqlmesh -p examples/multi/repo_1 plan
======================================================================
Successfully Ran 0 tests against duckdb
----------------------------------------------------------------------
Differences from the `prod` environment:

Models
├── Directly Modified:
│   └── bronze.a
└── Indirectly Modified:
    ├── bronze.b
    ├── silver.d
    └── silver.c
---

+++

@@ -1,3 +1,4 @@

 SELECT
   1 AS col_a,
-  'b' AS col_b
+  'b' AS col_b,
+  'c' AS col_c
Directly Modified: bronze.a (Non-breaking)
└── Indirectly Modified Children:
    ├── silver.c
    ├── bronze.b
    └── silver.d
Models needing backfill (missing dates):
└── bronze.a: (2023-04-17, 2023-04-17)
Apply - Backfill Tables [y/n]: y
bronze.a ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100.0% • 1/1 • 0:00:00

All model batches have been executed successfully

Virtually Updating 'prod' ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100.0% • 0:00:00

The target environment has been updated successfully
```

SQLMesh は、1 つのプロジェクトのみが「チェックアウト」されている場合でも、非破壊的な変更の系統全体を検出します。

## 重大な変更を加えてバックフィルします。

col_a を 1 + 1 に変更します。

```
--- a/examples/multi/repo_1/models/a.sql
+++ b/examples/multi/repo_1/models/a.sql
@@ -3,5 +3,6 @@ MODEL (
 );

 SELECT
-  1 AS col_a,
-  'b' AS col_b
+  1 + 1 AS col_a,
+  'b' AS col_b,
+  'c' AS col_c
```

```
$ sqlmesh -p examples/multi/repo_1 plan
======================================================================
Successfully Ran 0 tests against duckdb
----------------------------------------------------------------------
Differences from the `prod` environment:

Models
├── Directly Modified:
│   └── bronze.a
└── Indirectly Modified:
    ├── bronze.b
    ├── silver.d
    └── silver.c
---

+++

@@ -1,4 +1,4 @@

 SELECT
-  1 AS col_a,
+  1 + 1 AS col_a,
   'b' AS col_b,
   'c' AS col_c
Directly Modified: bronze.a (Breaking)
└── Indirectly Modified Children:
    ├── silver.d
    ├── bronze.b
    └── silver.c
Models needing backfill (missing dates):
├── bronze.a: (2023-04-17, 2023-04-17)
├── bronze.b: (2023-04-17, 2023-04-17)
├── silver.d: (2023-04-17, 2023-04-17)
└── silver.c: (2023-04-17, 2023-04-17)
Apply - Backfill Tables [y/n]: y
bronze.a ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100.0% • 1/1 • 0:00:00
silver.c ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100.0% • 1/1 • 0:00:00
bronze.b ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100.0% • 1/1 • 0:00:00
silver.d ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100.0% • 1/1 • 0:00:00

All model batches have been executed successfully

Virtually Updating 'prod' ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100.0% • 0:00:00

The target environment has been updated successfully
```

SQLMesh は重大な変更を正しく検出し、複数のリポジトリのバックフィルを実行できるようにします。

## 複数のリポジトリを持つプロジェクトの設定

複数のリポジトリをサポートするには、各リポジトリの設定ファイルに `project` キーを追加します。

```yaml
project: repo_1

gateways:
...
```

現時点で複数のリポジトリが必要ない場合でも、将来複数のリポジトリを簡単にサポートできるように `project` キーを追加することを検討してください。

## 複数のリポジトリでマイグレーションを実行する

[マイグレーション](./migrations.md)を実行する際は、`-p` フラグを使用して単一のリポジトリパスを渡してください。どのリポジトリを選択しても問題ありません。

```
$ sqlmesh -p examples/multi/repo_1 migrate
```

## マルチリポジトリ DBT プロジェクト

SQLMesh は DBT プロジェクトのマルチリポジトリもサポートしているため、複数の DBT プロジェクトにまたがる変更であっても、変更を正しく検出し、バックフィルを調整できます。

この設定の [クイックデモ](https://www.loom.com/share/69c083428bb348da8911beb2cd4d30b2) をご覧いただくか、[マルチリポジトリ DBT サンプル](https://github.com/TobikoData/sqlmesh/tree/main/examples/multi_dbt) を実際にお試しください。

## マルチリポジトリ混合プロジェクト

マルチリポジトリ設定では、ネイティブ SQLMesh プロジェクトを dbt プロジェクトと併用できます。

これにより、同じマルチリポジトリプロジェクト内でどちらのプロジェクトタイプからでもテーブルの管理と取得が可能になり、dbt から SQLMesh への段階的な移行が容易になります。

SQLMesh のみのマルチリポジトリプロジェクトと同じ構文を使用して、dbt プロジェクトまたは dbt プロジェクトと SQLMesh プロジェクトの組み合わせでマルチリポジトリプロジェクトを実行します。

```
$ sqlmesh -p examples/multi_hybrid/dbt_repo -p examples/multi_hybrid/sqlmesh_repo plan
```

SQLMesh は、モデルが異なるプロジェクトタイプからソースされている場合でも、SQLMesh プロジェクトと dbt プロジェクトの両方にわたって依存関係と系統を自動的に検出します。

この設定の例については、[SQLMesh と dbt の混在例](https://github.com/TobikoData/sqlmesh/tree/main/examples/multi_hybrid) を参照してください。
