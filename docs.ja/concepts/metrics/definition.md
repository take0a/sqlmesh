# 定義

メトリックは、SQLMesh プロジェクトの `metrics/` ディレクトリ内の SQL ファイルで定義されます。1 つのファイルに複数のメトリック定義を含めることができます。

メトリックは関数 `METRIC()` で定義され、`name` キーと `expression` キーを含める必要があります。`name` は大文字と小文字が区別されず、一意である必要があります。`expression` には、メトリックの計算に使用する SQL コードが含まれます。

## SQL 式

式フィールドには、集計関数（例: `MAX`、`SUM`）を含む任意の SQL 文を指定できます。この例では `COUNT` 関数を使用しています。

```sql linenums="1"
METRIC (
  name unique_account_ids,
  expression COUNT(DISTINCT silver.accounts.account_id)
);
```

式で参照されるすべての列は、モデル名で完全修飾されている必要があります。たとえば、モデル名が `a.b` の場合、そのモデル内の列 `c` を参照するメトリックは、`a.b.c` として参照する必要があります。

上記の例では、`silver.accounts` モデル内の `account_id` 列を `silver.accounts.account_id` を使用して参照しています。

### 自動結合

メトリックは複数のテーブルを参照でき、モデルの [grains](../models/overview.md#grain) と [references](../models/overview.md#references) を使用してそれらを自動的に結合します。`grains` は、モデルの行を一意に識別するモデルのキー列を指定し、`references` は、他のテーブルが結合できる列を指定します。

たとえば、SQLMesh プロジェクトには、次のような `MODEL` DDL を持つ `prod.users` モデルと `prod.searches` モデルが含まれているとします。

`prod.users` モデルの粒度は `user_id` です。つまり、その行は `user_id` 列によって一意に識別されます。

```sql linenums="1"
MODEL (
  name prod.users,
  grain user_id
);
```

`prod.searches` モデルは `references` キーに `user_id` を指定し、他のモデルが `user_id` 列に結合できることを示します。

```sql linenums="1"
MODEL (
  name prod.searches,
  grain search_id,
  references user_id,
);
```

これらのモデルは粒度と参照を指定しているため、SQLMesh は両方のモデルの列を使用するメトリックのコードを正しく生成できます。

この例では、`canadian_searchers` はカナダに所在するユーザーによる検索を合計します。

```sql linenums="1"
METRIC (
  name canadian_searchers,
  expression SUM(IF(prod.users.country = 'CAD', prod.searches.num_searches, 0)),
);
```

`prod.users.country` モデルと `prod.searches.num_searches` モデルはそれぞれのグレイン/参照を指定しているため、SQLMesh はそれらの間の正しい結合を自動的に実行できます。

### 派生メトリクス

メトリクスは、他のメトリクスと追加の演算/計算を実行できます。

この例では、3 番目のメトリクス `clicks_per_search` は、1 番目のメトリクス `total_searches` を 2 番目のメトリクス `total_clicks` で割ることによって計算されます。

```sql linenums="1"
METRIC (
  name total_searches,
  expression SUM(prod.searchers.num_searches)
);

METRIC (
  name total_clicks,
  expression SUM(prod.clickers.num_clicks)
);

METRIC (
  name clicks_per_search,
  expression total_clicks / total_searches -- Calculated from the other two metrics
);
```

## プロパティ

`METRIC` 定義では、以下のキーがサポートされています。`name` キーと `expression` キーは必須です。

### name
- メトリックの名前。この名前は大文字と小文字を区別せず、プロジェクト内で一意である必要があります。

### expression
- 集計、他のメトリックを含む式、またはその両方の組み合わせで構成される SQL 式。

### description
- メトリックの説明。

### owner
- メトリックの所有者。組織およびガバナンスの目的で使用されます。

### dialect
- 式が記述されている方言。このフィールドは空のままにして、プロジェクトのデフォルトの方言を使用することをお勧めします。
