# 外部モデル

SQLMesh モデルクエリは、SQLMesh プロジェクトの外部で作成および管理される「外部」テーブルを参照する場合があります。たとえば、モデルはサードパーティの読み取り専用データシステムからデータを取り込む場合があります。

SQLMesh は外部テーブルを管理しませんが、テーブルの列とデータ型に関する情報を使用することで、機能をより便利にすることができます。たとえば、列情報を使用することで、列レベルのリネージに外部テーブルの列を含めることができます。

SQLMesh は外部テーブルの列情報を `EXTERNAL` モデルとして保存します。

## 外部モデルは実行されません

`EXTERNAL` モデルは外部テーブルの列情報のみで構成されているため、SQLMesh が実行するクエリはありません。

SQLMesh は、`EXTERNAL` モデルで表されるテーブルに含まれるデータに関する情報を持っていません。テーブルが変更されたり、すべてのデータが削除されたりしても、SQLMesh はそれを検出しません。SQLMesh がテーブルについて認識しているのは、`EXTERNAL` モデルのファイルで指定された列が含まれていることだけです（詳細は後述）。

SQLMesh は、`EXTERNAL` モデルに基づいてアクションを実行しません。そのアクションは、クエリが `EXTERNAL` モデルから選択するモデルによってのみ決定されます。

クエリを実行するモデルの [`kind`](./model_kinds.md)、[`cron`](./overview.md#cron)、および以前にロードされた時間間隔によって、SQLMesh が `EXTERNAL` モデルにクエリを実行するタイミングが決まります。

## 外部モデルスキーマファイルの生成

外部モデルは、SQLMesh プロジェクトのルートフォルダにある `external_models.yaml` ファイルで定義できます。このファイルの別名は `schema.yaml` です。

このファイルを作成するには、YAML を手動で記述するか、CLI コマンド `create_external_models` を使用して SQLMesh に外部テーブルに関する情報を取得させる方法があります。

外部テーブル `external_db.external_table` をクエリする以下のサンプルモデルを考えてみましょう。

```sql
MODEL (
  name my_db.my_table,
  kind FULL
);

SELECT
  *
FROM
  external_db.external_table;
```

以下のセクションでは、`external_db.external_table` の列情報を含む外部モデルを作成する方法を説明します。

SQLMesh プロジェクトのすべての外部モデルは単一の `external_models.yaml` ファイルで定義されるため、以下で作成されるファイルには、他の外部モデルの列情報も含まれる場合があります。

または、[external_models/](#using-the-external_models-directory) フォルダに追加の外部モデルを定義することもできます。

### CLI の使用

`external_models.yaml` ファイルを手動で作成する代わりに、SQLMesh は [create_external_models](../../reference/cli.md#create_external_models) CLI コマンドを使用してこのファイルを自動生成できます。

このコマンドは、SQLMesh プロジェクトで参照されているすべての外部テーブルを識別し、SQL エンジンのメタデータからそれらの列情報を取得して、`external_models.yaml` ファイルに保存します。

SQLMesh が外部テーブルのメタデータにアクセスできない場合、そのテーブルはファイルから省略され、SQLMesh は警告を発します。

`create_external_models` は SQL エンジンのメタデータのみをクエリし、外部テーブル自体はクエリしません。

### ゲートウェイ固有の外部モデル

[複数のゲートウェイを持つ分離システム](../../guides/isolated_systems.md#multiple-gateways) などの一部のユースケースでは、特定のゲートウェイにのみ存在する外部モデルが存在します。

**外部モデル設定では、ゲートウェイ名の大文字と小文字は区別されません。** ゲートウェイ名は大文字と小文字のどちらでも指定できます（例: `gateway: dev`、`gateway: DEV`、`gateway: Dev`）。SQLMesh はこれらの一致を正しく処理します。

現在のゲートウェイに基づいて動的データベースを持つ外部テーブルをクエリする次のモデルを考えてみましょう。

```
MODEL (
  name my_db.my_table,
  kind FULL
);

SELECT
  *
FROM
  @{gateway}_db.external_table;
```

このテーブルの名前は、SQLMesh の実行時にどの `--gateway` オプションが使用されるかによって変わります（中括弧 `@{gateway}` 構文の詳細については、[こちら](../../concepts/macros/sqlmesh_macros.md#embedding-variables-in-strings) を参照してください）。

例:

- `sqlmesh --gateway dev plan` - SQLMesh は `dev_db.external_table` へのクエリを試みます。
- `sqlmesh --gateway prod plan` - SQLMesh は `prod_db.external_table` へのクエリを試みます。

関連するゲートウェイが設定されている場合、SQLMesh が正しいスキーマを参照できるようにするには、`--gateway` 引数を指定して `create_external_models` を実行します。例:

- `sqlmesh --gateway dev create_external_models`

これにより、外部モデルに `gateway: dev` が設定され、現在のゲートウェイが `dev` に設定されている場合にのみ読み込まれるようになります。

### YAML を手動で記述する

この例は、`external_models.yaml` ファイルの構造を示しています。

```yaml
- name: external_db.external_table
  description: An external table
  columns:
    column_a: int
    column_b: text
- name: external_db.some_other_external_table
  description: Another external table
  columns:
    column_c: bool
    column_d: float
- name: external_db.gateway_specific_external_table
  description: Another external table that only exists when the gateway is set to "test"
  gateway: test  # Case-insensitive - could also be "TEST", "Test", etc.
  columns:
    column_e: int
    column_f: varchar
```

このファイルには、各 `EXTERNAL` モデルの名前、オプションの説明、オプションのゲートウェイ、および外部テーブルの各列の名前とデータ型が含まれます。

このファイルは、標準的なテキストエディタまたは IDE を使用して手動で作成できます。

### `external_models` ディレクトリの使用

SQLMesh がモデルの構造を推測できない場合があり、手動で追加する必要があります。

ただし、`sqlmesh create_external_models` は `external_models.yaml` ファイルを置き換えるため、このファイルに手動で加えた変更は上書きされます。

解決策としては、次のように `external_models/` ディレクトリに手動でモデル定義ファイルを作成することです。

```
external_models.yaml
external_models/more_external_models.yaml
external_models/even_more_external_models.yaml
```

`external_models` ディレクトリ内のファイルは、`external_models.yaml` ファイルと同じ構造の `.yaml` ファイルである必要があります。

SQLMesh が定義を読み込む際、まず `external_models.yaml` (または `schema.yaml`) で定義されたモデルと `external_models/*.yaml` にあるモデルが読み込まれます。

したがって、`sqlmesh create_external_models` を使用して `external_models.yaml` ファイルを管理し、その後、手動で定義する必要があるモデルを `external_models/` ディレクトリ内に配置することができます。

### 外部監査

外部モデルに [audits](../audits.md) を定義できます。これは、内部モデルを評価する前に、上流の依存関係のデータ品質を確認するのに役立ちます。

この例は、2つの監査を含む外部モデルを示しています。

```yaml
- name: raw.demographics
  description: Table containing demographics information
  audits:
    - name: not_null
      columns: "[customer_id]"
    - name: accepted_range
      column: zip
      min_v: "'00000'"
      max_v: "'99999'"
  columns:
    customer_id: int
    zip: text
```
