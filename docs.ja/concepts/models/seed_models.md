# シードモデル

`SEED` は、SQL または Python 経由でアクセスされるデータソースではなく、CSV ファイルとして定義された静的データセットからデータを取得する特殊なモデルです。CSV ファイル自体は SQLMesh プロジェクトの一部です。

シードは SQLMesh のモデルでもあるため、SQL または Python モデルが提供するのと同じ利点をすべて活用できます。

* データウェアハウスに物理テーブルが作成され、シードの CSV ファイルの内容が反映されます。
* シードモデルは、他のモデルと同様に下流のモデルから参照できます。
* CSV ファイルへの変更は [プランニング](../plans.md#plan-application) 中にキャプチャされ、同じ [フィンガープリント](../architecture/snapshots.md#fingerprinting) メカニズムを使用してバージョン管理されます。
* [環境](../environments.md) 分離はシードモデルにも適用されます。

シードモデルは、変更頻度が低い、または全く変更されない静的データセットに適しています。このようなデータセットの例としては、次のようなものがあります。

* 国民の祝日名と日付
* 除外すべき識別子の静的リストd

!!! warning "Pythonモデルではサポートされていません"

    Python モデルは `SEED` [モデルの種類](./model_kinds.md) をサポートしていません。代わりに SQL モデルを使用してください。

## シードモデルの作成

[SQL モデル](./sql_models.md) と同様に、`SEED` モデルは SQLMesh プロジェクトの `models/` ディレクトリ内の `.sql` 拡張子のファイルで定義されます。

`MODEL` 定義で特別な種類 `SEED` を使用して、モデルがシードモデルであることを示します。

```sql linenums="1" hl_lines="3-5"
MODEL (
  name test_db.national_holidays,
  kind SEED (
    path 'national_holidays.csv'
  )
);
```

`path` 属性には、モデルの `.sql` ファイルのパスを基準とした、シードの CSV ファイルへの **相対パス** が含まれます。SQLMesh プロジェクトのルートからの相対パスを指定する場合は、`$root` マーカーを使用します ([マーカー](#markers) を参照)。

シードファイルに特別な引用符ルールや区切り文字が含まれている場合は、`csv_settings` ディクショナリを使用して [Pandas の `read_csv` 関数](https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html) に設定を渡すことができます (サポートされているすべての設定は [こちら](../../reference/model_configuration.md#csv_settings) に記載されています)。


```sql linenums="1" hl_lines="5-7"
MODEL (
  name test_db.national_holidays,
  kind SEED (
    path 'national_holidays.csv',
    csv_settings (
      delimiter = "|"
    )
  )
);
```

シードCSVの内容を含む物理テーブルは、Pandasによって推論された列型を使用して作成されます。あるいは、`MODEL`定義の一部としてデータセットスキーマを手動で指定することもできます。

```sql linenums="1" hl_lines="9-12"
MODEL (
  name test_db.national_holidays,
  kind SEED (
    path 'national_holidays.csv',
    csv_settings (
      delimiter = "|"
    )
  ),
  columns (
    name VARCHAR,
    date DATE
  )
);
```

**注:** 定義で指定されたデータセットスキーマは、CSVファイルのヘッダーで定義された列名よりも優先されます。つまり、`MODEL`定義で指定された列の順序は、CSVファイル内の列の順序と一致する必要があります。

### マーカー

`$root` マーカーを `path` 属性で使用すると、CSV ファイルのパスが SQLMesh プロジェクトのルートからの相対パスであることを示すことができます。

```sql linenums="1" hl_lines="3-5"
MODEL (
  name test_db.national_holidays,
  kind SEED (
    path '$root/seeds/national_holidays.csv'
  )
);
```

これは、すべてのシード CSV ファイルを `seeds/` などの最上位ディレクトリに保存したいが、多数の相対パスを追跡したり管理したりしたくない場合に便利です。

### エンコーディング

SQLMesh は、シードファイルが [UTF-8](https://en.wikipedia.org/wiki/UTF-8) 標準に従ってエンコードされていることを前提としています。異なるエンコーディングを使用すると、予期しない動作が発生する可能性があります。

## 例

この例では、前のセクションで SQLMesh プロジェクトの `models/national_holidays.sql` ファイルに保存したモデル定義を使用します。

また、シード CSV ファイル自体を `national_holidays.csv` という CSV ファイルとして `models/` ディレクトリに追加し、以下の内容を記述します。

```csv linenums="1"
name,date
New Year,2023-01-01
Christmas,2023-12-25
```

`sqlmesh plan` コマンドを実行すると、新しいシード モデルが自動的に検出されます。

```bash hl_lines="8-9"
$ sqlmesh plan
======================================================================
Successfully Ran 0 tests against duckdb
----------------------------------------------------------------------
`prod` environment will be initialized

Models
└── Added:
    └── test_db.national_holidays
Models needing backfill (missing dates):
└── test_db.national_holidays: (2023-02-16, 2023-02-16)
Enter the backfill start date (eg. '1 year', '2020-01-01') or blank for the beginning of history:
Apply - Backfill Tables [y/n]: y

All model batches have been executed successfully

test_db.national_holidays ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100.0% • 1/1 • 0:00:00
```

プランを適用すると、新しいテーブル「test_db.national_holidays」が作成されます。

これで、「sqlmesh fetchdf」を使用して、このテーブルに対してカスタムクエリを実行できます。

```bash
$ sqlmesh fetchdf "SELECT * FROM test_db.national_holidays"

        name        date
0   New Year  2023-01-01
1  Christmas  2023-12-25
```

シード CSV ファイルへの変更は、`sqlmesh plan` コマンドの実行時に取得されます。

```bash
$ sqlmesh plan
======================================================================
Successfully Ran 0 tests against duckdb
----------------------------------------------------------------------
Differences from the `prod` environment:

Models:
└── Directly Modified:
    └── test_db.national_holidays
---

+++

@@ -1,3 +1,4 @@

 name,date
 New Year,2023-01-01
 Christmas,2023-12-25
+Independence Day,2023-07-04
Directly Modified: test_db.national_holidays
[1] [Breaking] Backfill test_db.national_holidays and indirectly modified children
[2] [Non-breaking] Backfill test_db.national_holidays but not indirectly modified children: 1
Models needing backfill (missing dates):
└── test_db.national_holidays: (2023-02-16, 2023-02-16)
Enter the backfill start date (eg. '1 year', '2020-01-01') or blank for the beginning of history:
Apply - Backfill Tables [y/n]: y

All model batches have been executed successfully

test_db.national_holidays ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100.0% • 1/1 • 0:00:00
```

## 事前ステートメントと事後ステートメント

シードモデルは、事前ステートメントと事後ステートメントもサポートしています。これらは、シードの内容を挿入する前と挿入した後にそれぞれ評価されます。

以下は、事前ステートメントのみを使用する例です。

```sql linenums="1" hl_lines="8"
MODEL (
  name test_db.national_holidays,
  kind SEED (
    path 'national_holidays.csv'
  )
);

ALTER SESSION SET TIMEZONE = 'UTC';
```

事後ステートメントを追加するには、特別な `@INSERT_SEED()` マクロを使用して、事前ステートメントと事後ステートメントを分離する必要があります。

```sql linenums="1" hl_lines="11"
MODEL (
  name test_db.national_holidays,
  kind SEED (
    path 'national_holidays.csv'
  )
);

-- These are pre-statements
ALTER SESSION SET TIMEZONE = 'UTC';

@INSERT_SEED();

-- These are post-statements
ALTER SESSION SET TIMEZONE = 'PST';
```

## on-virtual-update ステートメント

シードモデルは、[仮想更新](#virtual-update) の完了後に実行される on-virtual-update ステートメントもサポートしています。

**プロジェクトレベルのデフォルト:** 設定で `model_defaults` を使用して、プロジェクトレベルで on-virtual-update ステートメントを定義することもできます。これらのステートメントは、プロジェクト内のすべてのモデル（シードモデルを含む）に適用され、モデル固有のステートメントとマージされます。デフォルトのステートメントが最初に実行され、次にモデル固有のステートメントが実行されます。詳細については、[モデル設定リファレンス](../../reference/model_configuration.md#model-defaults) を参照してください。

これらのステートメントは、`ON_VIRTUAL_UPDATE_BEGIN;` ...; `ON_VIRTUAL_UPDATE_END;` ブロックで囲む必要があります。

```sql linenums="1" hl_lines="8-13"
MODEL (
  name test_db.national_holidays,
  kind SEED (
    path 'national_holidays.csv'
  )
);

ON_VIRTUAL_UPDATE_BEGIN;
GRANT SELECT ON VIEW @this_model TO ROLE dev_role;
JINJA_STATEMENT_BEGIN;
GRANT SELECT ON VIEW {{ this_model }} TO ROLE admin_role;
JINJA_END;
ON_VIRTUAL_UPDATE_END;
```


上記の例のように、[Jinja式](../macros/jinja_macros.md)も使用できます。これらの式は、`JINJA_STATEMENT_BEGIN;` ブロックと `JINJA_END;` ブロック内に適切にネストする必要があります。

!!! note

    これらのステートメントのテーブル解決は仮想レイヤーで行われます。つまり、`@this_model` マクロを含むテーブル名は、修飾されたビュー名に解決されます。例えば、`dev` という環境でプランを実行すると、`db.customers` と `@this_model` は物理テーブル名ではなく `db__dev.customers` に解決されます。