# 監査

監査は、SQLMesh がモデルを検証するために提供するツールの 1 つです。[テスト](tests.md) と併用することで、データの品質を確保し、組織全体でデータへの信頼を構築するための優れた手段となります。

テストとは異なり、監査はモデルの実行ごとに出力を検証するために使用されます。[プラン](./plans.md) を適用すると、SQLMesh は各モデルの監査を自動的に実行します。

デフォルトでは、SQLMesh は監査が失敗するとプランの適用を停止し、無効な可能性のあるデータが下流に伝播しないようにします。この動作は個々の監査ごとに変更できます。[非ブロッキング監査](#non-blocking-audits) を参照してください。

包括的な監査スイートにより、ベンダーや他のチームに起因するデータの問題を上流で特定できます。また、監査により、データエンジニアやアナリストは新機能の開発やモデルの更新を行う際に問題を早期に把握できるため、自信を持って作業を進めることができます。

**注意**: 時間範囲による増分モデルの場合、監査は処理中の間隔にのみ適用され、基礎となるテーブル全体に対しては適用されません。

## ブロッキング監査

ブロッキング監査が失敗すると、無効なデータが下流のモデルに伝播するのを防ぐため、`plan` または `run` の実行が停止されます。失敗の影響は、`plan` を実行しているか `run` を実行しているかによって異なります。

SQLMesh のブロッキング監査プロセスは次のとおりです。

1. モデルを評価します（例: 新しいデータの挿入、テーブルの再構築）。
2. 新しく更新されたモデルテーブルに対して監査クエリを実行します。増分モデルの場合、監査は処理された時間間隔でのみ実行されます。
3. クエリが行を返す場合、監査は失敗し、`plan` または `run` が停止されます。

### プランと実行

主な違いは、モデルのデータが本番環境にプロモートされるタイミングです。

* **`plan`**: SQLMesh は、変更されたすべてのモデルを本番環境にプロモートする *前に* 評価と監査を行います。監査が失敗した場合、`plan` は停止し、本番環境のテーブルはそのまま残ります。無効なデータは分離されたテーブルに格納され、本番環境には送信されません。

* **`run`**: SQLMesh は、本番環境に対して直接モデルを評価および監査します。監査が失敗した場合、`run` は停止しますが、無効なデータは本番環境のテーブルに *既に* 存在します。「ブロッキング」アクションにより、この不正なデータが他の下流モデルの構築に使用されるのを防ぎます。

### 失敗した監査の修正

`run` 中にブロッキング監査が失敗した場合は、本番環境テーブル内の無効なデータを修正する必要があります。手順は次のとおりです。

1. **根本原因を特定**: 上流モデルとデータソースを確認します。
2. **ソースを修正**
    * 原因が **外部データソース** である場合は、そこで修正します。次に、ソースデータを取り込む最初の SQLMesh モデルに対して [再ステートメント プラン](./plans.md#restatement-plans) を実行します。これにより、監査に失敗したモデルを含むすべての下流モデルが再ステートメントされます。
    * 原因が **SQLMesh モデル** である場合は、モデルのロジックを更新します。次に、`plan` を使用して変更を適用します。これにより、すべての下流モデルが自動的に再評価されます。

## ユーザー定義の監査

SQLMesh では、ユーザー定義の監査は SQLMesh プロジェクトの `audits` ディレクトリ内の `.sql` ファイルで定義されます。1 つのファイルに複数の監査を定義できるため、必要に応じて整理できます。また、モデル定義自体に監査をインラインで定義することもできます。

監査は行を返さない SQL クエリです。つまり、不正なデータを検索するため、返される行は何か問題があることを示します。

最も単純な形式では、監査は `AUDIT` ステートメントとクエリで定義されます。次の例をご覧ください。

```sql linenums="1"
AUDIT (
  name assert_item_price_is_not_null,
  dialect spark
);
SELECT * from sushi.items
WHERE
  ds BETWEEN @start_ds AND @end_ds
  AND price IS NULL;
```

この例では、`assert_item_price_is_not_null` という監査を定義し、すべての寿司アイテムに価格が設定されていることを確認しています。

**注:** クエリがプロジェクトの他の部分とは異なる言語で記述されている場合は、`AUDIT` ステートメントでその言語を指定できます。上記の例では `spark` に設定しているため、SQLGlot はクエリの実行方法をバックグラウンドで自動的に理解します。

監査を実行するには、モデルの `MODEL` ステートメントに監査を含めます。

```sql linenums="1"
MODEL (
  name sushi.items,
  audits (assert_item_price_is_not_null)
);
```

これで、`sushi.items` モデルが実行されるたびに `assert_item_price_is_not_null` が実行されるようになります。

### 汎用監査
監査はパラメータ化してモデルに依存しない方法で実装できるため、同じ監査を複数のモデルで使用できます。

ターゲット列が設定されたしきい値を超えているかどうかを確認する次の監査定義を考えてみましょう。

```sql linenums="1"
AUDIT (
  name does_not_exceed_threshold
);
SELECT * FROM @this_model
WHERE @column >= @threshold;
```

この例では、[マクロ](./macros/overview.md) を使用して監査をパラメータ化します。`@this_model` は、監査対象のモデルを参照する特別なマクロです。増分モデルの場合、このマクロは関連するデータ間隔のみが影響を受けるようにします。

`@column` と `@threshold` は、モデル定義の `MODEL` ステートメントで値を指定するパラメータです。

`MODEL` ステートメントでモデルを参照することにより、汎用監査をモデルに適用します。

```sql linenums="1"
MODEL (
  name sushi.items,
  audits (
    does_not_exceed_threshold(column := id, threshold := 1000),
    does_not_exceed_threshold(column := price, threshold := 100)
  )
);
```

`column` と `threshold` パラメータがどのように設定されているかに注目してください。これらの値は監査クエリに反映され、`@column` および `@threshold` マクロ変数に代入されます。

同じ監査を、異なるパラメータセットを使用してモデルに複数回適用できることに注意してください。

汎用監査では、次のようにデフォルト値を定義できます。

```sql linenums="1"
AUDIT (
  name does_not_exceed_threshold,
  defaults (
    threshold = 10,
    column = id
  )
);
SELECT * FROM @this_model
WHERE @column >= @threshold;
```

あるいは、モデルのデフォルト設定に特定の監査を含めることで、特定の監査をグローバルに適用することもできます。

```sql linenums="1"
model_defaults:
  audits:
    - assert_positive_order_ids
    - does_not_exceed_threshold(column := id, threshold := 1000)
```

### 命名

監査パラメータの命名にはSQLキーワードの使用を避けることをお勧めします。SQLキーワードでもある監査引数は引用符で囲んでください。

例えば、監査パラメータ「my_audit」が「values」パラメータを使用している場合、「values」はSQLキーワードであるため、このパラメータを呼び出す際には引用符で囲む必要があります。

```sql linenums="1" hl_lines="4"
MODEL (
  name sushi.items,
  audits (
    my_audit(column := a, "values" := (1,2,3))
  )
)
```

### インライン監査

同じ構文を使用して、モデル定義内で直接監査を定義することもできます。同じSQLモデルファイル内に複数の監査を指定できます。


```sql linenums="1"
MODEL (
    name sushi.items,
    audits(does_not_exceed_threshold(column := id, threshold := 1000), price_is_not_null)
);
SELECT id, price
FROM sushi.seed;

AUDIT (name does_not_exceed_threshold);
SELECT * FROM @this_model
WHERE @column >= @threshold;

AUDIT (name price_is_not_null);
SELECT * FROM @this_model
WHERE price IS NULL;
```

## 組み込み監査

SQLMesh には、一般的なユースケースを幅広くカバーする、組み込みの汎用監査スイートが付属しています。組み込み監査はデフォルトでブロッキング監査ですが、すべてに非ブロッキング監査が用意されており、`_non_blocking` を付加することで使用できます。[非ブロッキング監査](#non-blocking-audits) を参照してください。

このセクションでは、汎用性別にグループ化された監査について説明します。

### 汎用アサーション監査

`forall` 監査は、任意のブールSQL式を使用できる、最も一般的な組み込み監査です。

#### forall、forall_non_blocking

モデル内のすべての行に対して、任意のブール式のセットが `TRUE` と評価されることを保証します。ブール式はSQLで記述する必要があります。

この例では、すべての行の `price` が0より大きく、`name` 値が少なくとも1文字を含むことをアサートします。

```sql linenums="1" hl_lines="4-7"
MODEL (
  name sushi.items,
  audits (
    forall(criteria := (
      price > 0,
      LENGTH(name) > 0
    ))
  )
);
```

### 行数と NULL 値の監査

これらの監査は、行数と `NULL` 値の存在に関するものです。

#### number_of_rows、number_of_rows_non_blocking

モデルのテーブル内の行数がしきい値を超えていることを確認します。

次の例では、モデルに 10 行以上あることをアサートしています。

```sql linenums="1"
MODEL (
  name sushi.orders,
  audits (
    number_of_rows(threshold := 10)
  )
);
```

#### not_null、not_null_non_blocking

指定された列に `NULL` 値が含まれていないことを確認します。

次の例では、`id`、`customer_id`、`waiter_id` のいずれの列にも `NULL` 値が含まれていないことをアサートします。

```sql linenums="1"
MODEL (
  name sushi.orders,
  audits (
    not_null(columns := (id, customer_id, waiter_id))
  )
);
```

#### at_least_one, at_least_one_non_blocking

指定された列に少なくとも1つの非NULL値が含まれていることを確認します。

この例では、`zip` 列に少なくとも1つの非NULL値が含まれていることをアサートします。

```sql linenums="1"
MODEL (
  name sushi.customers,
  audits (
    at_least_one(column := zip)
    )
);
```

#### not_null_proportion、not_null_proportion_non_blocking

指定された列の `NULL` 値の割合がしきい値以下であることを確認します。

次の例では、`zip` 列の `NULL` 値が 80% 以下であることを確認します。

```sql linenums="1"
MODEL (
  name sushi.customers,
  audits (
    not_null_proportion(column := zip, threshold := 0.8)
    )
);
```

### 特定のデータ値の監査

これらの監査は、列に存在する特定のデータ値セットに関するものです。

### not_constant、not_constant_non_blocking

指定された列が定数ではないこと（つまり、少なくとも2つのNULL以外の値があること）を確認します。

次の例では、列 `customer_id` に少なくとも2つのNULL以外の値があることをアサートしています。

```sql linenums="1"
MODEL (
  name sushi.customer_revenue_by_day,
  audits (
    not_constant(column := customer_id)
    )
);
```

#### unique_values、unique_values_non_blocking

指定された列に一意の値（つまり、重複する値がない）が含まれていることを確認します。

次の例では、`id` 列と `item_id` 列に一意の値が設定されていることをアサートしています。

```sql linenums="1"
MODEL (
  name sushi.orders,
  audits (
    unique_values(columns := (id, item_id))
  )
);
```

#### unique_combination_of_columns、unique_combination_of_columns_non_blocking

各行が、指定された列の値の組み合わせにおいて一意であることを保証します。

この例では、`id` 列と `ds` 列の組み合わせに重複する値がないことをアサートしています。

```sql linenums="1"
MODEL (
  name sushi.orders,
  audits (
    unique_combination_of_columns(columns := (id, ds))
  )
);
```

#### acceptable_values、accepted_values_non_blocking

指定された列のすべての行に、許容値のいずれかが含まれていることを確認します。

!!! note
    ほとんどのデータベース/エンジンでは、列に `NULL` 値を持つ行はこの監査に合格します。列に `NULL` 値がないことを確認するには、[`not_null` 監査](#not_null) を使用してください。

次の例では、列 `name` の値が 'Hamachi'、'Unagi'、または 'Sake' であることをアサートしています。

```sql linenums="1"
MODEL (
  name sushi.items,
  audits (
    accepted_values(column := name, is_in := ('Hamachi', 'Unagi', 'Sake'))
  )
);
```

#### not_accepted_values、not_accepted_values_non_blocking

指定された列の行に、受け入れられない値のいずれかが含まれていないことを確認します。

!!! note
    この監査では `NULL` 値の拒否はサポートされていません。列に `NULL` 値が含まれていないことを確認するには、[`not_null` 監査](#not_null) を使用してください。

次の例では、列 `name` が「ハンバーガー」または「フライドポテト」のいずれでもないことをアサートしています。

```sql linenums="1"
MODEL (
  name sushi.items,
  audits (
    not_accepted_values(column := name, is_in := ('Hamburger', 'French fries'))
  )
);
```

### 数値データ監査

これらの監査は、数値列の値の分布に関するものです。

#### sequential_values、sequential_values_non_blocking

順序付けされた数値列の各値に、前の行の値と `interval` が含まれていることを確認します。

例えば、最小値が 1、最大値が 4 で、`interval := 1` の列の場合、行には `[1, 2, 3, 4]` という値が含まれていることを確認します。

次の例では、列 `item_id` に `1` ずつ異なる連続した値が含まれていることをアサートしています。

```sql linenums="1"
MODEL (
  name sushi.items,
  audits (
    sequential_values(column := item_id, interval := 1)
  )
);
```

#### 許容範囲、許容範囲非ブロック

列の値が数値範囲内であることを確認します。範囲はデフォルトで包含的であるため、範囲の境界と等しい値は監査に合格します。

この例では、すべての行の「価格」が1以上100以下であることをアサートします。

```sql linenums="1"
MODEL (
  name sushi.items,
  audits (
    accepted_range(column := price, min_v := 1, max_v := 100)
  )
);
```

この例では、`inclusive := false` 引数を指定して、すべての行の `price` が 0 より大きく 100 より小さいことを主張します。

```sql linenums="1"
MODEL (
  name sushi.items,
  audits (
    accepted_range(column := price, min_v := 0, max_v := 100, inclusive := false)
  )
);
```

#### mutually_exclusive_ranges、mutually_exclusive_ranges_non_blocking

各行の数値範囲が他の行の範囲と重複しないことを保証します。

この例では、各行の範囲 [min_price, max_price] が他の行の範囲と重複しないことを保証します。

```sql linenums="1"
MODEL (
  audits (
    mutually_exclusive_ranges(lower_bound_column := min_price, upper_bound_column := max_price)
  )
);
```

### 文字データ監査

これらの監査は、文字/文字列列の値の特性に関するものです。

!!! warning
    データベース/エンジンは、文字セットや言語によって動作が異なる場合があります。

#### not_empty_string、not_empty_string_non_blocking

列のどの行にも空文字列値 `''` が含まれていないことを保証します。

この例では、`name` が空文字列ではないことをアサートします。

```sql linenums="1"
MODEL (
  name sushi.items,
  audits (
    not_empty_string(column := name)
  )
);
```

#### string_length_equal, string_length_equal_non_blocking

列のすべての行に、指定された文字数の文字列が含まれていることを確認します。

次の例では、すべての `zip` 値が5文字の長さであることを確認します。

```sql linenums="1"
MODEL (
  name sushi.customers,
  audits (
    string_length_equal(column := zip, v := 5)
    )
);
```

#### string_length_between、string_length_between_non_blocking

列のすべての行に、指定された範囲の文字数を持つ文字列が含まれていることを確認します。範囲はデフォルトで範囲に含まれており、範囲の境界と等しい値は監査に合格します。

次の例では、すべての `name` 値が 5 文字以上 50 文字以下であることをアサートします。

```sql linenums="1"
MODEL (
  name sushi.customers,
  audits (
    string_length_between(column := name, min_v := 5, max_v := 50)
    )
);
```

この例では、`inclusive := false` 引数を指定して、すべての行の `name` が 5 文字以上 59 文字以下であることを確認します。

```sql linenums="1"
MODEL (
  name sushi.customers,
  audits (
    string_length_between(column := zip, min_v := 4, max_v := 60, inclusive := false)
    )
);
```

#### valid_uuid、valid_uuid_non_blocking

列のすべての非NULL行に、UUID構造を持つ文字列が含まれていることを確認します。

UUID構造は、正規表現 `'^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'` に一致するように決定されます。

この例では、すべての `uuid` 値が UUID 構造を持つと主張します。

```sql linenums="1"
MODEL (
  audits (
    valid_uuid(column := uuid)
    )
);
```

#### valid_email、valid_email_non_blocking

列のNULL以外のすべての行に、メールアドレス構造を持つ文字列が含まれていることを確認します。

電子メール アドレスの構造は、正規表現 `'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'` に一致するように決定されます。

この例では、すべての `email` 値が電子メール アドレス構造を持つと主張します。

```sql linenums="1"
MODEL (
  audits (
    valid_email(column := email)
    )
);
```

#### valid_url、valid_url_non_blocking

列のNULL以外のすべての行に、URL構造を持つ文字列が含まれていることを確認します。

URL 構造は、正規表現 `'^(https?|ftp)://[^\s/$.?#].[^\s]*$'` に一致するように決定されます。

この例では、すべての `url` 値が URL 構造を持つと主張します。

```sql linenums="1"
MODEL (
  audits (
    valid_url(column := url)
    )
);
```

#### valid_http_method、valid_http_method_non_blocking

列のNULL以外のすべての行に有効なHTTPメソッドが含まれていることを確認します。

有効なHTTPメソッドは、値の照合によって決定されます。`GET`、`POST`、`PUT`、`DELETE`、`PATCH`、`HEAD`、`OPTIONS`、`TRACE`、`CONNECT`。

この例では、すべての`http_method`値が有効なHTTPメソッドであることをアサートします。

```sql linenums="1"
MODEL (
  audits (
    valid_http_method(column := http_method)
    )
);
```

#### match_regex_pattern_list、match_regex_pattern_list_non_blocking

列のNULL以外のすべての行が、指定された正規表現の少なくとも1つに一致することを確認します。

この例では、すべての `todo` 値が `'^\d.*'`（文字列が数字で始まる）または `'.*!$'`（感嘆符で終わる）のいずれかに一致することをアサートします。

```sql linenums="1"
MODEL (
  audits (
    match_regex_pattern_list(column := todo, patterns := ('^\d.*', '.*!$'))
  )
);
```

#### match_regex_pattern_list、match_regex_pattern_list_non_blocking

列のNULL以外のすべての行が、指定された正規表現の少なくとも1つに一致することを確認します。

この例では、すべての `todo` 値が `'^\d.*'`（文字列が数字で始まる）または `'.*!$'`（感嘆符で終わる）のいずれかに一致することをアサートします。

```sql linenums="1"
MODEL (
  audits (
    match_regex_pattern_list(column := todo, patterns := ('^!.*', '.*\d$'))
  )
);
```

#### match_like_pattern_list、match_like_pattern_list_non_blocking

列のすべての非NULL行が、指定されたパターンの少なくとも1つに `LIKE` されることを保証します。

この例では、すべての `name` 値が `'jim%'` または `'pam%'` のいずれかと `LIKE` していることを主張します。

```sql linenums="1"
MODEL (
  audits (
    match_like_pattern_list(column := name, patterns := ('jim%', 'pam%'))
  )
);
```

#### not_match_like_pattern_list、not_match_like_pattern_list_non_blocking

列のNULL以外の行が、指定されたパターンのいずれにも `LIKE` されないことを確認します。

この例では、`name` 値が `'%doe'` または `'%smith'` に `LIKE` されていないことを主張します。

```sql linenums="1"
MODEL (
  audits (
    not_match_like_pattern_list(column := name, patterns := ('%doe', '%smith'))
  )
);
```


### 統計監査

これらの監査は、数値列の統計分布に関するものです。

!!! note

    監査しきい値は、監査対象の列ごとに試行錯誤して微調整する必要がある可能性があります。

#### mean_in_range、mean_in_range_non_blocking

数値列の平均が指定された範囲内にあることを確認します。範囲はデフォルトで範囲に含まれており、範囲の境界と等しい値は監査に合格します。

次の例では、`age` 列の平均が 21 以上 50 以下であることをアサートします。

```sql linenums="1"
MODEL (
  audits (
    mean_in_range(column := age, min_v := 21, max_v := 50)
    )
);
```

この例では、`inclusive := false` 引数を指定して、`age` の平均が 18 より大きく 65 より小さいと主張します。

```sql linenums="1"
MODEL (
  audits (
    mean_in_range(column := age, min_v := 18, max_v := 65, inclusive := false)
    )
);
```

#### stddev_in_range、stddev_in_range_non_blocking

数値列の標準偏差が指定された範囲内にあることを確認します。範囲はデフォルトで範囲に含まれており、範囲の境界に等しい値は監査に合格します。

次の例では、`age` 列の標準偏差が 2 以上 5 以下であることをアサートします。

```sql linenums="1"
MODEL (
  audits (
    stddev_in_range(column := age, min_v := 2, max_v := 5)
    )
);
```

この例では、`inclusive := false` 引数を指定して、`age` の標準偏差が 3 より大きく 6 より小さいと主張します。

```sql linenums="1"
MODEL (
  audits (
    mean_in_range(column := age, min_v := 3, max_v := 6, inclusive := false)
    )
);
```

#### z_score、z_score_non_blocking

数値列の行に、絶対Zスコアがしきい値を超える値が含まれていないことを確認します。

Zスコアは `ABS(([行の値] - [列の平均]) / NULLIF([列の標準偏差], 0))` として計算されます。

次の例では、`age` 列に Z スコアが 3 を超える行が含まれていないことをアサートしています。

```sql linenums="1"
MODEL (
  audits (
    z_score(column := age, threshold := 3)
    )
);
```

#### kl_divergence、kl_divergence_non_blocking

2つの列間の[対称化Kullback-Leiblerダイバージェンス](https://en.wikipedia.org/wiki/Kullback%E2%80%93Leibler_divergence#Symmetrised_divergence)（別名「Jeffreysダイバージェンス」または「人口安定指数」）が閾値を超えないことを保証します。

この例では、列「age」と「reference_age」間の対称化KLダイバージェンスが0.1以下であることを確認します。

```sql linenums="1"
MODEL (
  audits (
    kl_divergence(column := age, target_column := reference_age, threshold := 0.1)
    )
);
```

#### chi_square, chi_square_non_blocking

2つのカテゴリ列の[カイ二乗](https://en.wikipedia.org/wiki/Chi-squared_test)統計量が臨界値を超えないことを保証します。

p値に対応する臨界値は、表（[こちら](https://www.medcalc.org/manual/chi-square-table.php)など）またはPythonの[scipyライブラリ](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.chi2.html)を使用して調べることができます。

```python linenums="1"
from scipy.stats import chi2

# critical value for p-value := 0.95 and degrees of freedom := 1
chi2.ppf(0.95, 1)
```

この例では、列 `user_state` と `user_type` のカイ二乗統計値が 6.635 を超えないことを主張します。

```sql linenums="1"
MODEL (
  audits (
    chi_square(column := user_state, target_column := user_type, critical_value := 6.635)
    )
);
```

## 監査の実行

### CLI 監査コマンド

次のように `sqlmesh audit` コマンドを使用して監査を実行できます。

```bash
$ sqlmesh -p project audit --start 2022-01-01 --end 2022-01-02
Found 1 audit(s).
assert_item_price_is_not_null FAIL.

Finished with 1 audit error(s).

Failure in audit assert_item_price_is_not_null for model sushi.items (audits/items.sql).
Got 3 results, expected 0.
SELECT * FROM sqlmesh.sushi__items__1836721418_83893210 WHERE ds BETWEEN '2022-01-01' AND '2022-01-02' AND price IS NULL
Done.
```

### 自動監査

プランを適用すると、SQLMesh は各モデルの監査を自動的に実行します。

デフォルトでは、SQLMesh は監査が失敗するとパイプラインを停止し、潜在的に無効なデータが下流に伝播するのを防ぎます。この動作は個々の監査ごとに変更できます。[非ブロッキング監査](#non-blocking-audits) を参照してください。

## 高度な使用方法

### 監査のスキップ

次の例のように、`skip` 引数を `true` に設定すると、監査をスキップできます。

```sql linenums="1" hl_lines="3"
AUDIT (
  name assert_item_price_is_not_null,
  skip true
);
SELECT * from sushi.items
WHERE ds BETWEEN @start_ds AND @end_ds AND
   price IS NULL;
```

### 非ブロッキング監査

デフォルトでは、監査が失敗するとパイプラインの実行が停止され、不正なデータがさらに伝播するのを防ぎます。

監査が失敗した場合にパイプラインの実行をブロックせずに通知するように設定することもできます。次の例をご覧ください。

```sql linenums="1" hl_lines="3"
AUDIT (
  name assert_item_price_is_not_null,
  blocking false
);
SELECT * from sushi.items
WHERE ds BETWEEN @start_ds AND @end_ds AND
   price IS NULL;
```

`blocking` プロパティは、特別な `blocking` 引数を使用して、監査の使用サイトで設定することもできます。

```sql linenums="1"
MODEL (
  name sushi.items,
  audits (
    does_not_exceed_threshold(column := id, threshold := 1000, blocking := false),
    does_not_exceed_threshold(column := price, threshold := 100, blocking := false)
  )
);
```
