# テーブル差分ガイド

SQLMesh のテーブル差分ツールを使用すると、2 つのデータオブジェクトのスキーマとデータを比較できます。2 つの環境間での SQLMesh モデルの比較、またはデータベース テーブルやビューの直接比較をサポートしています。

[モデルの評価](./models.md#evaluating-a-model) や [ユニットテストによるモデルのテスト](./testing.md#testing-changes-to-models) と併用できる、モデルを検証する手法を提供します。

**注:** テーブル差分を使用するには、2 つのオブジェクトがプロジェクトの基盤となるデータベースまたはエンジンに既に存在している必要があります。モデルを比較する場合は、変更内容を事前に計画し、環境に適用しておく必要があります。

## テーブル差分比較

テーブル差分は、ソースオブジェクトとターゲットオブジェクトに対して、スキーマ差分と行差分の2種類の比較を実行します。

スキーマ差分は、ソースオブジェクトと比較して、ターゲットオブジェクトでフィールドが追加、削除、またはデータ型が変更されたかどうかを識別します。

行差分は、両方のテーブルで同じ名前とデータ型を持つ列間のデータ値の変更を識別します。これは、2つのテーブル間で `OUTER JOIN` を実行し、同じ名前とデータ型を持つ各列について、一方のテーブルのデータ値ともう一方のテーブルのデータ値を比較することで行われます。

テーブル差分ツールは、2つのプロジェクト環境間でSQLMeshモデルを比較するか、テーブル/ビューを直接比較するかの2つの方法で呼び出すことができます。比較は、SQLMeshの[プロジェクト構成](../reference/configuration.md)で指定されたデータベースまたはエンジンを使用して実行されます。

## 環境間でのモデルの差分比較

SQLMesh CLI インターフェースを使用して、`sqlmesh table_diff [ソース環境]:[ターゲット環境] [モデル名]` コマンドを使用することで、SQLMesh モデルを環境間で比較できます。

例えば、[SQLMesh クイックスタート](../quick_start.md) モデル `sqlmesh_example.incremental_model` に次の 2 つの変更を加えることができます。

1. `CASE WHEN` ステートメントを使用して、`item_id` が `3` の行を `4` に変更します。
2. `WHERE` 句を追加して、`item_id` が `1` の行を削除します。

```sql linenums="1"
MODEL (
  name sqlmesh_example.incremental_model,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column event_date
  ),
  start '2020-01-01',
  cron '@daily',
  grain (id, event_date)
);

SELECT
  id,
  CASE WHEN item_id = 3 THEN 4 ELSE item_id END as item_id, -- Change item_id 3 to 4
  event_date,
FROM
  sqlmesh_example.seed_model
WHERE
  event_date between @start_ds and @end_ds
  AND id != 1 -- Remove row whose item_id is 1
```

`sqlmesh plan dev` を実行してプランを適用すると、更新されたモデルは `dev` 環境に存在しますが、`prod` 環境にはありません。

`sqlmesh table_diff prod:dev sqlmesh_example.incremental_model` を実行し、テーブル差分ツールで 2 つのバージョンのモデルを比較します。

最初の引数 `prod:dev` は、ターゲット環境 `dev` と比較するソース環境が `prod` であることを指定します。2 番目の引数 `sqlmesh_example.incremental_model` は、`prod` 環境と `dev` 環境間で比較するモデルの名前です。

`MODEL` ステートメントで `grain` が `[id, ds]` に設定されているため、SQLMesh は 2 つのモデル間の結合方法を認識しています。 `grain` が設定されていない場合、コマンドに `-o id -o ds` オプションを追加して、テーブルを列 `id` と `ds` で結合するように指定する必要があります。結合する列ごとに `-o` を 1 回ずつ指定してください。

テーブル diff は次の出力を返します。

```bash linenums="1"
$ sqlmesh table_diff prod:dev sqlmesh_example.incremental_model

Schema Diff Between 'PROD' and 'DEV' environments for model 'sqlmesh_example.incremental_model':
└── Schemas match


Row Counts:
├──  COMMON: 6 rows
├──  PROD ONLY: 1 rows
└──  DEV ONLY: 0 rows

COMMON ROWS column comparison stats:
         pct_match
item_id       83.3
```

「スキーマ差分」セクションには、列の追加、削除、またはデータ型の変更が行われていないため、`PROD` スキーマと `DEV` スキーマが一致していることがわかります。

「行数」セクションには、6 行が正常に結合され、削除した 1 行は `PROD` モデルにのみ存在することがわかります。

`COMMON ROWS 列比較統計` セクションには、結合された 6 行の `item_id` 列の値が 83.3% 一致していることがわかります（6 行のうち 5 行の値は `CASE WHEN` ステートメントによって変更されていません）。両方のテーブルで同じデータ型を持つ、結合されていないすべての列が比較統計に含まれます。

コマンドに `--show-sample` オプションを含めると、出力には異なる結合コンポーネントの行も含まれます。

```bash linenums="1"
$ sqlmesh table_diff prod:dev sqlmesh_example.incremental_model --show-sample

Schema Diff Between 'PROD' and 'DEV' environments for model 'sqlmesh_example.incremental_model':
└── Schemas match

Row Counts:
├──  FULL MATCH: 6 rows (92.31%)
└──  PROD ONLY: 1 rows

COMMON ROWS column comparison stats:
         pct_match
item_id      100.0


COMMON ROWS sample data differences:
  All joined rows match

PROD ONLY sample rows:
 id event_date  item_id
  1 2020-01-01        2
```

 `COMMON ROWS sample data differences` セクションには、`item_id` 値が変更された行が表示されます。`PROD__item_id` 列は `PROD` テーブル内の `item_id` が 3 であることを示しており、`DEV__item_id` 列は `DEV` テーブル内の `item_id` が 4.0 であることを示しています。

 `PROD ONLY sample rows` セクションには、 `PROD` には存在するが `DEV` には存在しない1行が表示されます。

`--skip-grain-check` オプションを追加すると、グレインは検証されません。このフラグがない場合、デフォルトでは、行にnullまたは重複するグレインが含まれている場合、ユーザーに警告が表示されます。

```bash linenums="1"
$ sqlmesh table_diff prod:dev2 sqlmesh_example.incremental_model

Grain should have unique and not-null audits for accurate results.

```

SQLMesh は内部的に、比較を実行するためにデータベースに一時データを保存します。
これらの一時テーブルのデフォルトのスキーマは `sqlmesh_temp` ですが、`--temp-schema` オプションで変更できます。
スキーマは `CATALOG.SCHEMA` または `SCHEMA` として指定できます。


## 環境間での複数モデルの差分比較

SQLMesh では、モデル選択式を使用して、複数の環境間で複数のモデルを一度に比較できます。これは、関連するモデルセットまたはプロジェクト全体にわたる変更を検証する場合に便利です。

複数のモデルを比較するには、table diff コマンドで `--select-model`（または短縮形 `-m`）オプションを使用します。

```bash
sqlmesh table_diff prod:dev --select-model "sqlmesh_example.*"
```

複数のモデルを比較する場合、SQLMesh は次の処理を行います。

1. セレクタによって返されたモデルのうち、両方の環境に存在し、差異のあるモデルを表示します。
2. これらのモデルを比較し、各モデルのデータ差分を表示します。

> 注: モデルは、モデルに影響を与える重大な変更があった場合にのみ、データ差分が行われます。

`--select-model` オプションは、パターン、タグ、依存関係、Git ステータスを使用してモデルを選択できる強力な選択構文をサポートしています。詳細については、[モデル選択ガイド](./model_selection.md) を参照してください。

> 注: 選択パターンは一重引用符または二重引用符で囲んでください。例: `'*'`、`"sqlmesh_example.*"`

一般的な例をいくつか示します。

```bash
# Select all models in a schema
sqlmesh table_diff prod:dev -m "sqlmesh_example.*"

# Select a model and its dependencies
sqlmesh table_diff prod:dev -m "+model_name"  # include upstream deps
sqlmesh table_diff prod:dev -m "model_name+"  # include downstream deps

# Select models by tag
sqlmesh table_diff prod:dev -m "tag:finance"

# Select models with git changes
sqlmesh table_diff prod:dev -m "git:feature"

# Use logical operators for complex selections
sqlmesh table_diff prod:dev -m "(metrics.* & ^tag:deprecated)"  # models in the metrics schema that aren't deprecated

# Combine multiple selectors
sqlmesh table_diff prod:dev -m "tag:finance" -m "metrics.*_daily"
```

複数のセレクターが指定されている場合、それらは OR ロジックで結合され、いずれかのセレクターに一致するモデルが含まれることになります。

!!! note
    比較されるすべてのモデルには、2 つの環境のテーブル間の結合を実行するために使用される、一意かつ null ではない `grain` が定義されている必要があります。

    `--warn-grain-check` オプションが使用される場合、この要件は強制されません。エラーを発生させる代わりに、grainが定義されていないモデルに対して警告が表示され、残りのモデルについては差分が計算されます。

## テーブルまたはビューの差分比較

SQLMesh CLI インターフェースで特定のテーブルまたはビューを比較するには、`sqlmesh table_diff [ソーステーブル]:[ターゲットテーブル]` コマンドを使用します。

ソーステーブルとターゲットテーブルは、`SELECT ... FROM [ソーステーブル]` 形式の SQL クエリが正しく実行されるように、カタログ名またはスキーマ名で完全修飾されている必要があります。

SQLMesh モデルはデータベースのビューからアクセスできることに注意してください。`prod` 環境では、ビューの名前はモデル名と同じです。たとえば、クイックスタートのサンプルプロジェクトでは、`prod` の増分モデルはビュー `sqlmesh_example.incremental_model` で表されます。`dev` 環境では、スキーマ名に `__dev` が追加されるため、増分モデルはビュー `sqlmesh_example__dev.incremental_model` で表されます。

前のセクションの比較は、モデルビューを直接比較することで再現できます。ビュー名を直接渡しているため、コマンドでは `-o id -o ds` フラグを使用して、結合が `id` 列と `ds` 列にあることを手動で指定する必要があります。

```bash linenums="1"
$ sqlmesh table_diff sqlmesh_example.incremental_model:sqlmesh_example__dev.incremental_model -o id -o event_date --show-sample

Schema Diff Between 'SQLMESH_EXAMPLE.INCREMENTAL_MODEL' and 'SQLMESH_EXAMPLE__DEV.INCREMENTAL_MODEL':
└── Schemas match


Row Counts:
├──  FULL MATCH: 6 rows (92.31%)
└──  SQLMESH_EXAMPLE.INCREMENTAL_MODEL ONLY: 1 rows

COMMON ROWS column comparison stats:
         pct_match
item_id      100.0


COMMON ROWS sample data differences:
  All joined rows match

SQLMESH_EXAMPLE.INCREMENTAL_MODEL ONLY sample rows:
 id event_date  item_id
  1 2020-01-01        2
```

`COMMON ROWS sample data differences` の列ラベルを除き、出力は一致しています。各列の基になるテーブルは、`s__`（「ソース」テーブル、コマンドのコロン演算子 `:` の最初のテーブル）と `t__`（「ターゲット」テーブル、コマンドのコロン演算子 `:` の2番目のテーブル）で示されます。

## ゲートウェイ間でのテーブルまたはビューの相違

!!! info "Tobiko Cloud Feature"

    データベース間のテーブル比較は、[Tobiko Cloud](../cloud/features/xdb_diffing.md) で利用できます。

SQLMesh は、プロジェクト構成で [ゲートウェイ](../guides/connections.md#overview) として指定された単一のデータベース システムを使用して、プロジェクトのモデルを実行します。

上記のデータベース内テーブル比較ツールは、このようなシステム内のテーブルまたは環境を比較します。ただし、2 つの異なるデータ システムに存在するテーブルを比較したい場合もあります。

たとえば、SQLMesh プロジェクトの設定中に、オンプレミスの SQL エンジンからクラウド SQL エンジンにデータ変換を移行するとします。システム間の同等性を証明するには、両方のシステムで変換を実行し、新しいテーブルと古いテーブルを比較します。

[データベース内テーブル diff](#環境間モデル diffing) ツールでは、以下の 2 つの理由により、このような比較を行うことができません。

1. 比較対象となる 2 つのテーブルを結合する必要がありますが、2 つのシステムでは、単一のデータベース エンジンから両方のテーブルにアクセスすることはできません。
2. このツールは、テーブル間でデータ値を変更せずに比較できることを前提としています。ただし、システムが異なる SQL エンジンを使用している場合は、エンジンのデータ型の違い（タイムスタンプにタイムゾーン情報を含めるかどうかなど）を考慮する必要があります。

SQLMesh のデータベース間テーブル diff ツールは、まさにこのようなシナリオを想定して構築されています。この比較アルゴリズムは、テーブルをあるシステムから別のシステムに移動することなく効率的に diff を行い、データ型の違いを自動的に処理します。

データベース間テーブル diff の詳細については、[Tobiko Cloud ドキュメント](../cloud/features/xdb_diffing.md) をご覧ください。