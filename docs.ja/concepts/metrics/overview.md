# 概要

メトリクスは現在プロトタイプ段階にあり、本番環境での使用を想定していません。

SQLMesh は、メトリクス（セマンティックレイヤーとも呼ばれます）の定義と操作のためのフレームワークを提供します。メトリクスとは、分析、データサイエンス、機械学習で使用するための集計を実行する任意の SQL 関数です。

セマンティックレイヤーは、メトリクスの定義と言語に一貫性があるため、有用です。例えば、経営幹部が「アクティブユーザーは何人いますか？」と質問した場合、誰に質問するか、どのダッシュボードを参照するかによって、答えは異なる可能性があります。答えを正しく計算するために必要なテーブル、集計、結合は複雑で、人によって実装が異なる（あるいは誤っている）可能性があります。

メトリクスは SQLMesh プロジェクトのメトリクスディレクトリに定義され、モデルクエリ内で名前によって選択されます。SQLMesh はクエリのセマンティックな理解に基づいて、クエリにおけるメトリクスの役割を決定し、メトリクスを計算するための適切な SQL 操作を決定し、それらを SQL エンジンに送信されるクエリコードに追加します。

## 例

### 定義

メトリクスは、SQLMesh の SQL ベースの [メトリクス定義言語](definition.md) を使用して定義されます。

以下はメトリクス定義の例です。以下の点に注意してください。

- メトリクスの `expression` は、任意の集計 SQL 関数 (この例では `COUNT`) を使用できます。
- `expression` で参照される列は完全修飾されています (`sushi.customers.status`)。
- メトリクスは、モデルの [grains](../models/overview.md#grain)/[references](../models/overview.md#references) が適切に指定されている限り、複数のモデルを参照できます (`expression` は `sushi.customers` モデルと `sushi.orders` モデルの両方を使用します)。

```sql linenums="1"
METRIC (
  name total_orders_from_active_customers,
  expression COUNT(IF(sushi.customers.status = 'ACTIVE', sushi.orders.id, NULL))
);
```

### クエリ

SQLMesh モデルは、クエリの `SELECT` 句で `METRIC` 関数とメトリック名を使用してメトリックにアクセスします。

例えば、このモデルクエリは `total_orders_from_active_customer` メトリックを選択します。これはメトリックとそのグループ化列のみを選択する単純なクエリであるため、特別なテーブル `__semantic.__table` から選択できます。

```sql linenums="1"
SELECT
  ds,
  METRIC(total_orders_from_active_customers), -- METRIC function
FROM __semantic.__table  -- special table for simple metric queries
GROUP BY ds
```

そのモデル クエリが実行されると、SQLMesh はクエリとメトリック定義の意味を理解して、SQL エンジンによって実際に実行されるコードを生成します。

``` sql linenums="1"
SELECT
  __table.ds AS ds,
  __table.total_orders_from_active_customers AS total_orders_from_active_customers
FROM (
  SELECT
    sushi__orders.ds,
    COUNT(CASE WHEN sushi__customers.status = 'ACTIVE' THEN sushi__orders.id ELSE NULL END) AS total_orders_from_active_customers
  FROM sushi.orders AS sushi__orders
  LEFT JOIN sushi.customers AS sushi__customers
    ON sushi__orders.customer_id = sushi__customers.customer_id
  GROUP BY
    sushi__orders.ds
) AS __table
```

SQLMesh は、`sushi.orders` テーブルと `sushi.customers` テーブルの両方の値を使用するために正しい結合を自動的に生成します。
