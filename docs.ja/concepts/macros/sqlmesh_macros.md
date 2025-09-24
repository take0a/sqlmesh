# SQLMesh マクロ

## マクロシステム：2つのアプローチ

SQLMesh マクロは、[Jinja](https://jinja.palletsprojects.com/en/3.1.x/) などのテンプレートシステムのマクロとは動作が異なります。

マクロシステムは文字列の置換に基づいています。マクロシステムはコードファイルをスキャンし、マクロの内容を表す特殊文字を識別し、マクロ要素を他のテキストに置き換えます。

一般的に言えば、これがテンプレートシステムの全機能です。テンプレートシステムには制御フローロジック (if-then) などの機能を提供するツールがありますが、*それらの機能は正しい文字列への置換のみをサポートするものです*。

テンプレートシステムは、テンプレート化されるプログラミング言語に意図的に依存せず、そのほとんどはブログ投稿から HTML、SQL まであらゆるものに対応しています。

一方、SQLMesh マクロは SQL コードの生成に特化して設計されています。これらは、Python [sqlglot](https://github.com/tobymao/sqlglot) ライブラリを使用して分析することにより、作成されている SQL コードの *意味的理解* を備えており、Python コードの使用を許可しているため、ユーザーは高度なマクロ ロジックをきちんと実装できます。

### SQLMesh マクロのアプローチ

このセクションでは、SQLMesh マクロが内部でどのように動作するかについて説明します。このセクションは読み飛ばしていただいても構いません。必要に応じて戻ってください。この情報は SQLMesh マクロの使用に必須ではありませんが、不可解な動作を示すマクロをデバッグする際に役立ちます。

SQLMesh マクロのアプローチとテンプレートシステムの重要な違いは、文字列置換の役割です。テンプレートシステムでは、文字列置換が唯一の目的です。

SQLMesh では、文字列置換は SQL クエリのセマンティック表現を変更するための一歩にすぎません。*SQLMesh マクロは、SQL クエリのセマンティック表現を構築および変更することで機能します。*

SQL 以外のテキストをすべて処理した後、置換された値を使用してクエリのセマンティック表現を最終状態に修正します。

これを実現するために、以下の5つのステップを採用しています。

1. 適切な sqlglot SQL 方言（Postgres、BigQuery など）を使用してテキストを解析します。解析中に、特殊なマクロ記号 `@` を検出し、非SQL テキストと SQL テキストを区別します。パーサーは SQL コードの構造のセマンティック表現を構築し、非SQL テキストを後続のステップで使用する「プレースホルダ」値としてキャプチャします。

2. プレースホルダ値を調べ、以下のいずれかのタイプに分類します。

- `@DEF` 演算子を使用したユーザー定義マクロ変数の作成（[ユーザー定義マクロ変数](#user-defined-variables) の詳細については、こちらをご覧ください）
- マクロ変数：[SQLMesh 定義済み](./macro_variables.md)、[ユーザー定義ローカル](#local-variables)、[ユーザー定義グローバル](#global-variables)
- マクロ関数（[SQLMesh マクロ演算子](#sqlmesh-macro-operators) と [ユーザー定義](#user-defined-macro-functions) の両方）

3. 検出されたマクロ変数値を置き換えます。ほとんどの場合、テンプレートシステムと同様に、直接文字列を置き換えます。

4. マクロ関数を実行し、戻り値を置き換えます。

5. (3) で置き換えた変数値と (4) の関数を使用して、SQL クエリのセマンティック表現を変更します。

### 文字列への変数の埋め込み

SQLMesh は、マクロ変数の値を常に SQL クエリのセマンティック表現に組み込みます（上記の手順 5）。そのために、SQLMesh は各マクロ変数の値がクエリ内で果たす役割を推測します。

コンテキストとして、SQL でよく使用される 2 種類の文字列は次のとおりです。

- 文字列リテラル。テキスト値を表し、一重引用符で囲まれます（例: `'the_string'`）。
- 識別子。列、テーブル、エイリアス、関数名などのデータベースオブジェクトを参照します。
  - SQL 方言に応じて、引用符で囲まれていない場合もあれば、二重引用符、バッククォート、または角括弧で囲まれている場合もあります。

通常のクエリでは、SQLMesh は特定の文字列が果たしている役割を簡単に判断できます。しかし、マクロ変数が文字列に直接埋め込まれている場合、特に文字列がクエリ自体ではなく `MODEL` ブロック内にある場合は、判断が難しくなります。

例えば、`gateway_var` という名前の [ゲートウェイ変数](#gateway-variables) を定義するプロジェクトを考えてみましょう。このプロジェクトには、モデルの `name` （SQL *識別子*）のスキーマの一部として `@gateway_var` を参照するモデルが含まれています。

このモデルは次のように記述できます。

``` sql title="Incorrectly rendered to string literal"
MODEL (
  name the_@gateway_var_schema.table
);
```

SQLMesh の観点から見ると、モデルスキーマは 3 つの部分文字列 (`the_`、`@gateway_var` の値、`_schema`) の組み合わせです。

SQLMesh はこれらの文字列を連結しますが、SQL 識別子を構築していることを認識するためのコンテキストがないため、文字列リテラルを返します。

SQLMesh に必要なコンテキストを提供するには、マクロ変数参照に中括弧 (`@gateway_var` ではなく `@{gateway_var}`) を追加する必要があります。

``` sql title="Correctly rendered to identifier"
MODEL (
  name the_@{gateway_var}_schema.table
);
```

中括弧は、SQLMesh に文字列を SQL 識別子として扱うように指示し、SQL 方言の引用規則に基づいて引用符で囲みます。

中括弧構文の最も一般的な用途は、文字列にマクロ変数を埋め込むことですが、SQL クエリ内で文字列リテラルと識別子を区別するためにも使用できます。例えば、値が `col` であるマクロ変数 `my_variable` を考えてみましょう。

この値を通常のマクロ構文で `SELECT` すると、文字列リテラルに変換されます。

``` sql
SELECT @my_variable AS the_column; -- renders to SELECT 'col' AS the_column
```

`'col'` は一重引用符で囲まれており、SQL エンジンはその文字列を列のデータ値として使用します。

中括弧を使用すると、SQLMesh はレンダリングされた文字列を識別子として使用することを認識します。

``` sql
SELECT @{my_variable} AS the_column; -- renders to SELECT col AS the_column
```

`col` は一重引用符で囲まれていないため、SQL エンジンはクエリが `col` という名前の列またはその他のオブジェクトを参照していると判断します。

## ユーザー定義変数

SQLMesh は、4 種類のユーザー定義マクロ変数をサポートしています。[global](#global-variables)、[gateway](#gateway-variables)、[blueprint](#blueprint-variables)、[local](#local-variables) です。

グローバルおよびゲートウェイのマクロ変数はプロジェクト構成ファイルで定義され、どのプロジェクト モデルからでもアクセスできます。ブループリントおよびマクロ変数はモデル定義で定義され、そのモデル内でのみアクセスできます。

同じ名前のマクロ変数は、グローバル、ゲートウェイ、ブループリント、ローカルのいずれかまたはすべてのレベルで指定できます。変数が複数のレベルで指定されている場合、最も具体的なレベルの値が優先されます。たとえば、ローカル変数の値は、同じ名前のブループリントまたはゲートウェイ変数の値よりも優先され、ゲートウェイ変数の値はグローバル変数の値よりも優先されます。

### グローバル変数

グローバル変数は、プロジェクト設定ファイルの [`variables` キー](../../reference/configuration.md#variables) で定義されます。

グローバル変数の値は、以下のいずれかのデータ型、またはこれらの型を含むリストや辞書になります: `int`、`float`、`bool`、`str`。

モデル定義内のグローバル変数値には、`@<VAR_NAME>` マクロまたは `@VAR()` マクロ関数を使用してアクセスします。後者の関数では、最初の引数として変数名（一重引用符で囲む）を指定し、2番目の引数としてオプションのデフォルト値を指定します。デフォルト値は、プロジェクト設定ファイル内に変数名が見つからない場合に使用される安全策です。

例えば、この SQLMesh 設定キーは、異なるデータ型の 6 つの変数を定義しています。

=== "YAML"

    ```yaml linenums="1"
    variables:
      int_var: 1
      float_var: 2.0
      bool_var: true
      str_var: "cat"
      list_var: [1, 2, 3]
      dict_var:
        key1: 1
        key2: 2
    ```

=== "Python"

    ``` python linenums="1"
    variables = {
        "int_var": 1,
        "float_var": 2.0,
        "bool_var": True,
        "str_var": "cat",
        "list_var": [1, 2, 3],
        "dict_var": {"key1": 1, "key2": 2},
    }

    config = Config(
        variables=variables,
        ... # other Config arguments
    )
    ```

モデル定義では、次のように `WHERE` 句の `int_var` 値にアクセスできます。

```sql linenums="1"
SELECT *
FROM table
WHERE int_variable = @INT_VAR
```

あるいは、変数名を `@VAR()` マクロ関数に渡すことで、同じ変数にアクセスすることもできます。`@VAR('int_var')` という呼び出しでは、変数名が一重引用符で囲まれていることに注意してください。

```sql linenums="1"
SELECT *
FROM table
WHERE int_variable = @VAR('int_var')
```

`@VAR()` マクロ関数の2番目の引数としてデフォルト値を渡すことができ、設定ファイルに変数が定義されていない場合にフォールバック値として使用されます。

この例では、プロジェクト設定ファイルに `missing_var` という変数が定義されていないため、`WHERE` 句は `WHERE some_value = 0` と表示されます。

```sql linenums="1"
SELECT *
FROM table
WHERE some_value = @VAR('missing_var', 0)
```

同様の API は、`evaluator.var` メソッドを介して [Python マクロ関数](#グローバル変数値へのアクセス) と `context.var` メソッドを介して [Python モデル](../models/python_models.md#グローバル変数) で使用できます。

### ゲートウェイ変数

グローバル変数と同様に、ゲートウェイ変数はプロジェクト設定ファイルで定義されます。ただし、ゲートウェイ変数は特定のゲートウェイの `variables` キーで指定します。

=== "YAML"

    ```yaml linenums="1"
    gateways:
      my_gateway:
        variables:
          int_var: 1
        ...
    ```

=== "Python"

    ``` python linenums="1"
    gateway_variables = {
      "int_var": 1
    }

    config = Config(
        gateways={
          "my_gateway": GatewayConfig(
            variables=gateway_variables
            ... # other GatewayConfig arguments
            ),
          }
    )
    ```

モデル内では、[グローバル変数](#global-variables)と同じ方法でアクセスできます。

ゲートウェイ固有の変数値は、ルートの `variables` キーで指定された同じ名前の変数よりも優先されます。

### ブループリント変数

ブループリントマクロ変数はモデル内で定義されます。ブループリント変数の値は、同じ名前の [グローバル](#global-variables) または [ゲートウェイ固有](#gateway-variables) 変数よりも優先されます。

ブループリント変数は `MODEL` ステートメントのプロパティとして定義され、[モデルテンプレートを作成する](../models/sql_models.md) ためのメカニズムとして機能します。

```sql linenums="1"
MODEL (
  name @customer.some_table,
  kind FULL,
  blueprints (
    (customer := customer1, field_a := x, field_b := y, field_c := 'foo'),
    (customer := customer2, field_a := z, field_b := w, field_c := 'bar')
  )
);

SELECT
  @field_a,
  @{field_b} AS field_b,
  @field_c AS @{field_c}
FROM @customer.some_source

/*
When rendered for customer1.some_table:
SELECT
  x,
  y AS field_b,
  'foo' AS foo
FROM customer1.some_source

When rendered for customer2.some_table:
SELECT
  z,
  w AS field_b,
  'bar' AS bar
FROM customer2.some_source
*/
```

モデルクエリでは、通常のマクロ変数参照である `@field_a` と中括弧構文の `@{field_b}` の両方が使用されていることに注意してください。これらはどちらも識別子としてレンダリングされます。ブループリントでは文字列である `field_c` の場合、通常のマクロ構文である `@field_c` と組み合わせると文字列リテラルとしてレンダリングされます。文字列を識別子として使用する場合は、中括弧 `@{field_c}` を使用します。詳しくは [上記](#文字列への変数の埋め込み) をご覧ください。

ブループリント変数には、上記の構文、または `@BLUEPRINT_VAR()` マクロ関数を使用してアクセスできます。このマクロ関数は、変数が未定義の場合のデフォルト値の指定もサポートしています (`@VAR()` と同様)。

### ローカル変数

ローカルマクロ変数はモデル内で定義されます。ローカル変数の値は、同じ名前の [グローバル](#global-variables)、[ブループリント](#blueprint-variables)、または [ゲートウェイ固有](#gateway-variables) 変数よりも優先されます。

`@DEF` マクロ演算子を使用して、独自のローカルマクロ変数を定義します。例えば、次のようにしてマクロ変数 `macro_var` の値を `1` に設定できます。

```sql linenums="1"
@DEF(macro_var, 1);
```

SQLMesh では、`@DEF` 演算子を使用する際に 3 つの基本要件があります。

1. `MODEL` ステートメントはセミコロン `;` で終わる必要があります。
2. すべての `@DEF` の使用は、`MODEL` ステートメントの後、SQL クエリの前に行う必要があります。
3. すべての `@DEF` の使用は、セミコロン `;` で終わる必要があります。

例えば、[SQLMesh クイックスタート ガイド](../../quick_start.md) に記載されている次のモデル `sqlmesh_example.full_model` を考えてみましょう。

```sql linenums="1"
MODEL (
  name sqlmesh_example.full_model,
  kind FULL,
  cron '@daily',
  audits (assert_positive_order_ids),
);

SELECT
  item_id,
  count(distinct id) AS num_orders,
FROM
  sqlmesh_example.incremental_model
GROUP BY item_id
```

このモデルは、ユーザー定義のマクロ変数を使用して拡張し、次のように `item_size` に基づいてクエリ結果をフィルター処理できます。

```sql linenums="1"
MODEL (
  name sqlmesh_example.full_model,
  kind FULL,
  cron '@daily',
  audits (assert_positive_order_ids),
); -- NOTE: semi-colon at end of MODEL statement

@DEF(size, 1); -- NOTE: semi-colon at end of @DEF operator

SELECT
  item_id,
  count(distinct id) AS num_orders,
FROM
  sqlmesh_example.incremental_model
WHERE
  item_size > @size -- Reference to macro variable `@size` defined above with `@DEF()`
GROUP BY item_id
```

この例では、マクロ変数 `size` を `@DEF(size, 1)` で定義しています。モデルを実行すると、SQLMesh は `WHERE` 句内の `@size` に数値 `1` を代入します。

### マクロ関数

SQLMesh は、インラインユーザー定義変数に加えて、インラインマクロ関数もサポートしています。これらの関数を使用することで、変数のみで記述する場合よりも可読性と再利用性に優れたロジックを表現できます。例を見てみましょう。

```sql linenums="1"
MODEL(...);

@DEF(
  rank_to_int,
  x -> case when left(x, 1) = 'A' then 1 when left(x, 1) = 'B' then 2 when left(x, 1) = 'C' then 3 end
);

SELECT
  id,
  cust_rank_1,
  cust_rank_2,
  cust_rank_3
  @rank_to_int(cust_rank_1) as cust_rank_1_int,
  @rank_to_int(cust_rank_2) as cust_rank_2_int,
  @rank_to_int(cust_rank_3) as cust_rank_3_int
FROM
  some.model
```

マクロ関数では複数の引数も表現できます。

```sql linenums="1"
@DEF(pythag, (x,y) -> sqrt(pow(x, 2) + pow(y, 2)));

SELECT
  sideA,
  sideB,
  @pythag(sideA, sideB) AS sideC
FROM
  some.triangle
```

```sql linenums="1"
@DEF(nrr, (starting_mrr, expansion_mrr, churned_mrr) -> (starting_mrr + expansion_mrr - churned_mrr) / starting_mrr);

SELECT
  @nrr(fy21_mrr, fy21_expansions, fy21_churns) AS fy21_net_retention_rate,
  @nrr(fy22_mrr, fy22_expansions, fy22_churns) AS fy22_net_retention_rate,
  @nrr(fy23_mrr, fy23_expansions, fy23_churns) AS fy23_net_retention_rate,
FROM
  some.revenue
```

次のようにマクロ関数をネストできます。

```sql linenums="1"
MODEL (
  name dummy.model,
  kind FULL
);

@DEF(area, r -> pi() * r * r);
@DEF(container_volume, (r, h) -> @area(@r) * h);

SELECT container_id, @container_volume((cont_di / 2), cont_hi) AS volume
```

## マクロ演算子

SQLMesh のマクロシステムには、モデル内でさまざまな動的動作を可能にする複数の演算子があります。

### @EACH

`@EACH` は、`for` ループと同様に、各項目に関数を適用することでリストを変換するために使用されます。

??? info "`for` ループと `@EACH` について詳しく学ぶ"

    `@EACH` 演算子について詳しく説明する前に、`for` ループを詳しく分析して、その構成要素を理解しましょう。

    `for` ループは、項目のコレクションと、各項目に対して実行されるアクションという2つの主要な部分から構成されます。例えば、Python の `for` ループは次のようになります。

    ```python linenums="1"
    for number in [4, 5, 6]:
        print(number)
    ```

    この for ループは、括弧内の各数値を出力します。

    ```python linenums="1"
    4
    5
    6
    ```

    例の最初の行はループを設定し、次の2つの処理を行います。

    1. ループ内のコードでは各項目を`number`として参照することをPythonに指示します。
    2. 括弧内の項目のリストを1つずつ処理するようにPythonに指示します。

    2行目は、各項目に対して実行するアクションをPythonに指示します。この場合は、項目を出力します。

    ループはリスト内の各項目に対して1回実行され、コード内の単語`number`が各項目に置き換えられます。例えば、ループの1回目は`print(4)`として実行され、2回目は`print(5)`として実行されます。

    SQLMeshの`@EACH`演算子は、SQLMeshマクロで`for`ループに相当する機能を実装するために使用されます。

    `@EACH`という名前は、ループがコレクション内の項目ごとにアクションを実行することに由来しています。これは基本的に上記のPythonループと同じですが、2つのループ構成要素の指定方法が異なります。

    `@EACH` takes two arguments: a list of items and a function definition.

```sql linenums="1"
@EACH([list of items], [function definition])
```

関数定義はインラインで指定されます。この例では、入力をそのまま返す恒等関数を指定しています。

```sql linenums="1"
SELECT
  @EACH([4, 5, 6], number -> number)
FROM table
```

ループは最初の引数で設定されます。`@EACH([4, 5, 6]` は、SQLMesh に括弧内の項目のリストを順に処理するように指示します。

2 番目の引数 `number -> number` は、SQLMesh に各項目に対して実行するアクションを「匿名」関数（別名「ラムダ」関数）を使用して指示します。矢印の左側は、右側のコードが各項目を参照する名前を指定します（Python の `for` ループにおける `for [name] in [items]` の `name` のように）。

矢印の右側は、リスト内の各項目に対して実行する処理を指定します。`number -> number` は、`@EACH` に、`number` の各項目に対してその項目（例 `1`）を返すように指示します。

SQLMesh マクロは、SQL コードのセマンティックな理解に基づき、SQL クエリ内でマクロ変数が使用されている場所に基づいて自動的にアクションを実行します。`@EACH` が SQL の `SELECT` 句で使用されている場合、ステートメント:

1. 項目を出力します。
2. `SELECT` ではフィールドがカンマで区切られていることを認識しているため、出力項目は自動的にカンマで区切られます。

自動出力とカンマ区切りのため、匿名関数 `number -> number` は `@EACH` に対し、`number` の各項目について、項目を出力し、項目をカンマで区切るように指示します。したがって、この例の完全な出力は次のようになります。

```sql linenums="1"
SELECT
  4,
  5,
  6
FROM table
```

この基本的な例は単純すぎて役に立ちません。`@EACH` の多くの用途では、値をリテラル値と識別子のいずれか、あるいは両方として使用します。

例えば、データ内の列 `favorite_number` に値 `4`、`5`、`6` が含まれているとします。この列を3つのインジケーター列（つまり、バイナリ列、ダミー列、One-Hot エンコードされた列）に展開したいとします。これは次のように手動で記述できます。

```sql linenums="1"
SELECT
  CASE WHEN favorite_number = 4 THEN 1 ELSE 0 END as favorite_4,
  CASE WHEN favorite_number = 5 THEN 1 ELSE 0 END as favorite_5,
  CASE WHEN favorite_number = 6 THEN 1 ELSE 0 END as favorite_6
FROM table
```

このSQLクエリでは、各数値が2つの異なる方法で使用されています。例えば、「4」は次のように使用されています。

1. 「favorite_number = 4」におけるリテラル数値として
2. 「favorite_4」における列名の一部として

それぞれの使用方法を個別に説明します。

リテラル数値の場合、「@EACH」は括弧内に渡された値（*引用符を含む*）を正確に置き換えます。例えば、上記の「CASE WHEN」の例に似た次のクエリを考えてみましょう。

```sql linenums="1"
SELECT
  @EACH([4,5,6], x -> CASE WHEN favorite_number = x THEN 1 ELSE 0 END as column)
FROM table
```

これは次の SQL に変換されます:

```sql linenums="1"
SELECT
  CASE WHEN favorite_number = 4 THEN 1 ELSE 0 END AS column,
  CASE WHEN favorite_number = 5 THEN 1 ELSE 0 END AS column,
  CASE WHEN favorite_number = 6 THEN 1 ELSE 0 END AS column
FROM table
```

入力された括弧内の `@EACH` 配列と結果の SQL クエリの両方で、数値 `4`、`5`、`6` が引用符で囲まれていないことに注意してください。

代わりに、入力された `@EACH` 配列内でこれらの数値を引用符で囲むことができます。

```sql linenums="1"
SELECT
  @EACH(['4','5','6'], x -> CASE WHEN favorite_number = x THEN 1 ELSE 0 END as column)
FROM table
```

これらは結果の SQL クエリで引用符で囲まれます。

```sql linenums="1"
SELECT
  CASE WHEN favorite_number = '4' THEN 1 ELSE 0 END AS column,
  CASE WHEN favorite_number = '5' THEN 1 ELSE 0 END AS column,
  CASE WHEN favorite_number = '6' THEN 1 ELSE 0 END AS column
FROM table
```

`@EACH` 関数定義内で SQLMesh マクロ演算子 `@` を使用すると、配列値を列名の末尾に配置できます。

```sql linenums="1"
SELECT
  @EACH(['4','5','6'], x -> CASE WHEN favorite_number = x THEN 1 ELSE 0 END as column_@x)
FROM table
```

このクエリは次のようにレンダリングされます:

```sql linenums="1"
SELECT
  CASE WHEN favorite_number = '4' THEN 1 ELSE 0 END AS column_4,
  CASE WHEN favorite_number = '5' THEN 1 ELSE 0 END AS column_5,
  CASE WHEN favorite_number = '6' THEN 1 ELSE 0 END AS column_6
FROM table
```

この構文は、配列の値が引用符で囲まれているかどうかに関係なく機能します。

!!! note "文字列にマクロを埋め込む"

    SQLMesh マクロは、`column_@x` を使用して列名の末尾にマクロ値を配置することをサポートしています。

    ただし、識別子内の他の場所で変数を置換する場合は、曖昧さを避けるために、より明確な中括弧構文 `@{}` を使用する必要があります。例えば、`@{x}_column` や `my_@{x}_column` は有効な使用例です。

    文字列へのマクロの埋め込みの詳細については、[上記](#文字列への変数の埋め込み) をご覧ください。

### @IF

SQLMesh の `@IF` マクロを使用すると、SQL クエリのコンポーネントを論理条件の結果に基づいて変更できます。

このマクロには 3 つの要素が含まれます。

1. `TRUE` または `FALSE` と評価される論理条件
2. 条件が `TRUE` の場合に返す値
3. 条件が `FALSE` の場合に返す値 [オプション]

これらの要素は次のように指定します。

```sql linenums="1"
@IF([logical condition], [value if TRUE], [value if FALSE])
```

条件が `FALSE` の場合に返す値はオプションです。値が指定されず、条件が `FALSE` の場合、マクロは結果のクエリに影響を与えません。

論理条件は *SQL* で記述し、[SQLGlot](https://github.com/tobymao/sqlglot) の SQL エグゼキュータで評価されます。以下の演算子をサポートしています。

- 等価性: 等しい場合は `=`、等しくない場合は `!=` または `<>`
- 比較: `<`、`>`、`<=`、`>=`
- 範囲: `[数値] BETWEEN [下限値] AND [上限値]`
- メンバーシップ: `[項目] IN ([項目のカンマ区切りリスト])`

例えば、以下の単純な条件はすべて有効なSQLであり、`TRUE`と評価されます。

- `'a' = 'a'`
- `'a' != 'b'`
- `0 < 1`
- `1 >= 1`
- `2 BETWEEN 1 AND 3`
- `'a' IN ('a', 'b')`

`@IF` は、SQLクエリの任意の部分を変更するために使用できます。たとえば、次のクエリは条件付きでクエリ結果に `sensitive_col` を含めます。

```sql linenums="1"
SELECT
  col1,
  @IF(1 > 0, sensitive_col)
FROM table
```

`1 > 0` は `TRUE` と評価されるため、クエリは次のようにレンダリングされます。

```sql linenums="1"
SELECT
  col1,
  sensitive_col
FROM table
```

`@IF(1 > 0, sensitive_col)` には、`FALSE` の場合の値を指定する3番目の引数が含まれていないことに注意してください。条件が `FALSE` と評価された場合、`@IF` は何も返さず、`col1` のみが選択されます。

あるいは、条件が `FALSE` と評価された場合に `nonsensitive_col` を返すように指定することもできます。

```sql linenums="1"
SELECT
  col1,
  @IF(1 > 2, sensitive_col, nonsensitive_col)
FROM table
```

`1 > 2` は `FALSE` と評価されるため、クエリは次のようにレンダリングされます。

```sql linenums="1"
SELECT
  col1,
  nonsensitive_col
FROM table
```

[マクロレンダリング](#sqlmesh-macro-approach)は、`@IF` 条件が評価される前に実行されます。例えば、SQLMesh は `my_column > @my_value` という条件を、`@my_value` が表す数値を最初に代入するまで評価しません。

マクロは、値を返す以外にも、メッセージの出力やステートメントの実行など、さまざまな処理を実行する場合があります（つまり、マクロには「副作用がある」ことになります）。副作用コードは、レンダリング段階で常に実行されます。これを防ぐには、マクロコードを変更し、評価段階で副作用が発生するようにします。

#### 事前/事後文

`@IF` は、事前/事後文を条件付きで実行するために使用できます。

```sql linenums="1"
@IF([logical condition], [statement to execute if TRUE]);
```

`@IF` 文自体はセミコロンで終わる必要がありますが、内部の文の引数はセミコロンで終わる必要はありません。

この例では、モデルの [実行時ステージ](./macro_variables.md#predefined-variables) に応じて、事前/事後ステートメントを条件付きで実行します。実行時ステージは、定義済みマクロ変数 `@runtime_stage` を介してアクセスします。`@IF` 事後ステートメントは、モデルの評価時にのみ実行されます。

```sql linenums="1" hl_lines="17-20"
MODEL (
  name sqlmesh_example.full_model,
  kind FULL,
  cron '@daily',
  grain item_id,
  audits (assert_positive_order_ids),
);

SELECT
  item_id,
  count(distinct id) AS num_orders,
FROM
  sqlmesh_example.incremental_model
GROUP BY item_id
ORDER BY item_id;

@IF(
  @runtime_stage = 'evaluating',
  ALTER TABLE sqlmesh_example.full_model ALTER item_id TYPE VARCHAR
);
```

注: あるいは、`@runtime_stage = 'creating'` の場合は列の型を変更することもできますが、これはモデルが増分的で変更が持続する場合にのみ役立ちます。`FULL` モデルは評価ごとに再構築されるため、作成段階で行われた変更はモデルが評価されるたびに上書きされます。

### @EVAL

`@EVAL` は、SQLGlot の SQL エグゼキュータを使って引数を評価します。

これにより、SQL コード内で数学的計算やその他の計算を実行できます。[`@IF` 演算子](#if) の最初の引数と同様に動作しますが、論理条件に限定されません。

例えば、マクロ変数に 5 を加算するクエリを考えてみましょう。

```sql linenums="1"
MODEL (
  ...
);

@DEF(x, 1);

SELECT
  @EVAL(5 + @x) as my_six
FROM table
```

マクロ変数の置換後、これは `@EVAL(5 + 1)` としてレンダリングされ、 `6` と評価され、最終的にレンダリングされたクエリは次のようになります。

```sql linenums="1"
SELECT
  6 as my_six
FROM table
```

### @FILTER

`@FILTER` は、入力配列の項目を、匿名関数で指定された論理条件を満たす項目のみにサブセット化するために使用されます。その出力は、[`@EACH`](#each) や [`@REDUCE`](#reduce) などの他のマクロ演算子で使用できます。

ユーザーが指定した匿名関数は、`TRUE` または `FALSE` に評価される必要があります。`@FILTER` は、配列内の各項目に関数を適用し、条件を満たす項目のみを出力配列に含めます。

匿名関数は *SQL* で記述し、[SQLGlot](https://github.com/tobymao/sqlglot) SQL エグゼキュータで評価されます。SQL 標準の等価演算子と比較演算子をサポートしています。サポートされている演算子の詳細については、上記の [`@IF`](#if) を参照してください。

例えば、次の `@FILTER` 呼び出しを考えてみましょう。

```sql linenums="1"
@FILTER([1,2,3], x -> x > 1)
```

入力配列 `[1,2,3]` の各項目に条件 `x > 1` を適用し、 `[2,3]` を返します。

### @REDUCE

`@REDUCE` は、配列内の項目を結合するために使用されます。

この無名関数は、入力配列内の項目をどのように結合するかを指定します。`@EACH` や `@FILTER` とは異なり、無名関数は括弧で囲まれた値を持つ 2 つの引数を取ります。

例えば、`@EACH` の無名関数は `x -> x + 1` と指定できます。矢印の左側の `x` は、SQLMesh に対して、矢印の右側のコードでは配列項目が `x` として参照されることを伝えます。

`@REDUCE` 無名関数は 2 つの引数を取るため、矢印の左側のテキストには、括弧で囲まれた 2 つの名前をコンマで区切って記述する必要があります。例えば、`(x, y) -> x + y` は、SQLMesh に対して、矢印の右側のコードでは項目が `x` と `y` として参照されることを伝えます。

無名関数は引数を2つしか取りませんが、入力配列には必要な数の項目を含めることができます。

無名関数 `(x, y) -> x + y` を考えてみましょう。概念的には、引数 `y` のみが配列の項目に対応し、引数 `x` は関数の評価時に作成される一時的な値です。

呼び出し `@REDUCE([1,2,3,4], (x, y) -> x + y)` では、無名関数は次の手順で配列に適用されます。

1. 配列の最初の2つの項目を `x` と `y` として、関数を適用します。`1 + 2` = `3`。
2. 手順 (1) の出力を `x` として、配列の次の項目 `3` を `y` として、関数を適用します。`3 + 3` = `6`。
3. 手順 (2) の出力を `x` とし、配列の次の要素 `4` を `y` として、関数 `6 + 4` = `10` を適用します。
4. 残りの要素はありません。手順 (3) の戻り値: `10`。

`@REDUCE` は、ほとんどの場合、他のマクロ演算子と組み合わせて使用​​されます。例えば、複数の列名から `WHERE` 句を構築したい場合などです。

```sql linenums="1"
SELECT
  my_column
FROM
  table
WHERE
  col1 = 1 and col2 = 1 and col3 = 1
```

`@EACH` を使用して各列の述語 (例: `col1 = 1`) を構築し、`@REDUCE` を使用してそれらを 1 つのステートメントに結合することができます。

```sql linenums="1"
SELECT
  my_column
FROM
  table
WHERE
  @REDUCE(
    @EACH([col1, col2, col3], x -> x = 1), -- Builds each individual predicate `col1 = 1`
    (x, y) -> x AND y -- Combines individual predicates with `AND`
  )
```

### @STAR

`@STAR` は、クエリ内の列選択セットを返すために使用されます。

`@STAR` は SQL のスター演算子 `*` にちなんで名付けられていますが、利用可能なすべての列を選択するだけでなく、プログラムで列選択セットとエイリアスを生成することができます。クエリでは複数の `@STAR` を使用でき、明示的な列選択を含めることもできます。

`@STAR` は、SQLMesh が各テーブルの列とデータ型に関する知識に基づいて、適切な列リストを生成します。

列のデータ型が既知の場合、結果のクエリは列をソーステーブルのデータ型に `CAST` します。そうでない場合は、列はキャストされずにリストされます。

`@STAR` は以下の引数をこの順序でサポートします。

- `relation`: 列を選択するリレーション/テーブル
- `alias` (オプション): リレーションのエイリアス (存在する場合)
- `exclude` (オプション): 除外する列のリスト
- `prefix` (オプション): 選択したすべての列名の接頭辞として使用する文字列
- `suffix` (オプション): 選択したすべての列名の接尾辞として使用する文字列
- `quote_identifiers` (オプション): 結果の識別子を引用符で囲むかどうか (デフォルトは true)

**注意**: `exclude` 引数は以前は `except_` という名前でした。後者は現在もサポートされていますが、将来的に非推奨となるため、使用は推奨されません。

すべての SQLMesh マクロ関数と同様に、`@STAR` の呼び出し時に引数を省略するには、後続の引数に引数名と特殊なキーワード演算子 `:=` を渡す必要があります。例えば、`@STAR(foo, exclude := [c])` という形で `alias` 引数を省略できます。マクロ関数の引数の詳細については、[下記](#位置引数とキーワード引数) をご覧ください。

`@STAR` の例として、次のクエリを考えてみましょう。

```sql linenums="1"
SELECT
  @STAR(foo, bar, [c], 'baz_', '_qux')
FROM foo AS bar
```

`@STAR` の引数は次のとおりです。

1. テーブル名 `foo` (クエリの `FROM foo` から)
2. テーブル別名 `bar` (クエリの `AS bar` から)
3. 選択から除外する列のリスト (`c` 列を 1 つ含む)
4. すべての列名の接頭辞として使用する文字列 `baz_`
5. すべての列名の接尾辞として使用する文字列 `_qux`

`foo` は、`a` (`TEXT`)、`b` (`TEXT`)、`c` (`TEXT`)、`d` (`INT`) の 4 つの列を含むテーブルです。マクロ展開後、列の型がわかっている場合、クエリは次のように表示されます。

```sql linenums="1"
SELECT
  CAST("bar"."a" AS TEXT) AS "baz_a_qux",
  CAST("bar"."b" AS TEXT) AS "baz_b_qux",
  CAST("bar"."d" AS INT) AS "baz_d_qux"
FROM foo AS bar
```

レンダリングされたクエリの以下の点に注意してください。

- 各列は、テーブル `foo` 内の対応するデータ型に `CAST` されています（例：`a` は `TEXT` に）
- 各列の選択では、エイリアス `bar` が使用されています（例：`"bar"."a"`）
- 列 `c` は、`@STAR` の `exclude` 引数に渡されたため、存在しません。
- 各列エイリアスには、プレフィックス `baz_`、サフィックス `_qux` が付けられています（例：`"baz_a_qux"`）

次に、`a` と `b` に `d` とは異なるプレフィックスを付け、明示的に列 `my_column` を含む、より複雑な例を考えてみましょう。

```sql linenums="1"
SELECT
  @STAR(foo, bar, exclude := [c, d], 'ab_pre_'),
  @STAR(foo, bar, exclude := [a, b, c], 'd_pre_'),
  my_column
FROM foo AS bar
```

先ほどと同様に、`foo` は `a` (`TEXT`)、`b` (`TEXT`)、`c` (`TEXT`)、`d` (`INT`) の4つの列を含むテーブルです。マクロ展開後、クエリは次のようにレンダリングされます。

```sql linenums="1"
SELECT
  CAST("bar"."a" AS TEXT) AS "ab_pre_a",
  CAST("bar"."b" AS TEXT) AS "ab_pre_b",
  CAST("bar"."d" AS INT) AS "d_pre_d",
  my_column
FROM foo AS bar
```

レンダリングされたクエリの以下の点に注意してください。

- 列 `a` と `b` にはプレフィックス `"ab_pre_"` が付き、列 `d` にはプレフィックス `"d_pre_"` が付きます。
- 列 `c` は、両方の `@STAR` 呼び出しで `exclude` 引数に渡されたため、存在しません。
- クエリには `my_column` が存在します。

### @GENERATE_SURROGATE_KEY

`@GENERATE_SURROGATE_KEY` は、列セットから代理キーを生成します。代理キーとは、連結された列値に対して [`MD5`](https://en.wikipedia.org/wiki/MD5) などのハッシュ関数によって返される英数字のシーケンスです。

代理キーは、以下の手順で作成されます。
1. 各列の値を `TEXT`（またはSQLエンジンの同等の型）に `CAST` する。
2. 各列の `NULL` 値をテキスト `'_sqlmesh_surrogate_key_null_'` に置き換える。
3. 手順 (1) と (2) を実行した後、列の値を連結する。
4. 手順 (3) で返された連結値に [`MD5()` ハッシュ関数](https://en.wikipedia.org/wiki/MD5) を適用する。

例えば、次のクエリがあります。

```sql linenums="1"
SELECT
  @GENERATE_SURROGATE_KEY(a, b, c) AS col
FROM foo
```

次のように表示されます。

```sql linenums="1"
SELECT
  MD5(
    CONCAT(
      COALESCE(CAST("a" AS TEXT), '_sqlmesh_surrogate_key_null_'),
      '|',
      COALESCE(CAST("b" AS TEXT), '_sqlmesh_surrogate_key_null_'),
      '|',
      COALESCE(CAST("c" AS TEXT), '_sqlmesh_surrogate_key_null_')
    )
  ) AS "col"
FROM "foo" AS "foo"
```

デフォルトでは `MD5` 関数が使用されますが、次のように `hash_function` 引数を設定することでこの動作を変更できます。

```sql linenums="1"
SELECT
  @GENERATE_SURROGATE_KEY(a, b, c, hash_function := 'SHA256') AS col
FROM foo
```

このクエリも同様に次のようにレンダリングされます。

```sql linenums="1"
SELECT
  SHA256(
    CONCAT(
      COALESCE(CAST("a" AS TEXT), '_sqlmesh_surrogate_key_null_'),
      '|',
      COALESCE(CAST("b" AS TEXT), '_sqlmesh_surrogate_key_null_'),
      '|',
      COALESCE(CAST("c" AS TEXT), '_sqlmesh_surrogate_key_null_')
    )
  ) AS "col"
FROM "foo" AS "foo"
```

### @SAFE_ADD

`@SAFE_ADD` は、2つ以上のオペランドを加算し、`NULL` を `0` に置き換えます。すべてのオペランドが `NULL` の場合、`NULL` を返します。

例えば、次のクエリがあります。

```sql linenums="1"
SELECT
  @SAFE_ADD(a, b, c)
FROM foo
```

次のように表示されます。

```sql linenums="1"
SELECT
  CASE WHEN a IS NULL AND b IS NULL AND c IS NULL THEN NULL ELSE COALESCE(a, 0) + COALESCE(b, 0) + COALESCE(c, 0) END
FROM foo
```

### @SAFE_SUB

`@SAFE_SUB` は、2つ以上のオペランドを減算し、`NULL` を `0` に置き換えます。すべてのオペランドが `NULL` の場合、`NULL` を返します。

例えば、次のクエリがあります。

```sql linenums="1"
SELECT
  @SAFE_SUB(a, b, c)
FROM foo
```

次のように表示されます。

```sql linenums="1"
SELECT
  CASE WHEN a IS NULL AND b IS NULL AND c IS NULL THEN NULL ELSE COALESCE(a, 0) - COALESCE(b, 0) - COALESCE(c, 0) END
FROM foo
```

### @SAFE_DIV

`@SAFE_DIV` は2つの数値を割り算し、分母が `0` の場合は `NULL` を返します。

例えば、次のクエリがあります。

```sql linenums="1"
SELECT
  @SAFE_DIV(a, b)
FROM foo
```
would be rendered as:

```sql linenums="1"
SELECT
  a / NULLIF(b, 0)
FROM foo
```

### @UNION

`@UNION` は、テーブルから名前とデータ型が一致するすべての列を選択する `UNION` クエリを返します。

最初の引数には、条件または `UNION` の「型」を指定できます。最初の引数がブール値（`TRUE` または `FALSE`）に評価された場合は、条件として扱われます。条件が `FALSE` の場合、最初のテーブルのみが返されます。`TRUE` の場合、結合演算が実行されます。

最初の引数がブール値条件でない場合は、`UNION` の「型」として扱われます。つまり、`'DISTINCT'`（重複行を削除）または `'ALL'`（すべての行を返す）のいずれかです。後続の引数は、結合するテーブルです。

以下の状況を想定しましょう。

- `foo` は 3 つの列 `a` (`INT`), `b` (`TEXT`), `c` (`TEXT`) を含むテーブルです。
- `bar` は 3 つの列 `a` (`INT`), `b` (`INT`), `c` (`TEXT`) を含むテーブルです。

次の式を考えます。

```sql linenums="1"
@UNION('distinct', foo, bar)
```

次のように表示されます。

```sql linenums="1"
SELECT
  CAST(a AS INT) AS a,
  CAST(c AS TEXT) AS c
FROM foo
UNION
SELECT
  CAST(a AS INT) AS a,
  CAST(c AS TEXT) AS c
FROM bar
```

共用体型が省略された場合、デフォルトで `'ALL'` が使用されます。つまり、次の式は次のようになります。

```sql linenums="1"
@UNION(foo, bar)
```

次のように表示されます。

```sql linenums="1"
SELECT
  CAST(a AS INT) AS a,
  CAST(c AS TEXT) AS c
FROM foo
UNION ALL
SELECT
  CAST(a AS INT) AS a,
  CAST(c AS TEXT) AS c
FROM bar
```

条件を使用して、結合が行われるかどうかを制御することもできます。

```sql linenums="1"
@UNION(1 > 0, 'all', foo, bar)
```

これは上記と同じ結果になります。ただし、条件が `FALSE` の場合:

```sql linenums="1"
@UNION(1 > 2, 'all', foo, bar)
```

最初のテーブルだけが選択されます。

```sql linenums="1"
SELECT
  CAST(a AS INT) AS a,
  CAST(c AS TEXT) AS c
FROM foo
```

### @HAVERSINE_DISTANCE

`@HAVERSINE_DISTANCE` は、2 つの地理的な点間の [Haversine 距離](https://en.wikipedia.org/wiki/Haversine_formula) を返します。

以下の引数をこの順序でサポートします。

- `lat1`: 最初の点の緯度
- `lon1`: 最初の点の経度
- `lat2`: 2 番目の点の緯度
- `lon2`: 2 番目の点の経度
- `unit` (オプション): 測定単位。現在は `'mi'` (マイル、デフォルト) と `'km'` (キロメートル) のみがサポートされています。

SQLMesh マクロ演算子は名前付き引数を受け入れません。たとえば、`@HAVERSINE_DISTANCE(lat1=lat_column)` はエラーになります。

例えば、次のクエリ:

```sql linenums="1"
SELECT
  @HAVERSINE_DISTANCE(driver_y, driver_x, passenger_y, passenger_x, 'mi') AS dist
FROM rides
```

次のように表示されます。

```sql linenums="1"
SELECT
  7922 * ASIN(SQRT((POWER(SIN(RADIANS((passenger_y - driver_y) / 2)), 2)) + (COS(RADIANS(driver_y)) * COS(RADIANS(passenger_y)) * POWER(SIN(RADIANS((passenger_x - driver_x) / 2)), 2)))) * 1.0 AS dist
FROM rides
```

### @PIVOT

`@PIVOT` は、入力列を指定された値でピボットした結果の列セットを返します。この操作は、「長い」形式（1つの列に複数の値）から「広い」形式（複数の列それぞれに1つの値）へのピボット操作と呼ばれることもあります。

以下の引数をこの順序でサポートします。

- `column`: ピボットする列
- `values`: ピボットに使用する値（`values` の値ごとに 1 つの列が作成されます）
- `alias` (オプション): 結果の列にエイリアスを作成するかどうか。デフォルトは true
- `agg` (オプション): 使用する集計関数。デフォルトは `SUM`
- `cmp` (オプション): 列の値を比較するために使用する比較演算子。デフォルトは `=`
- `prefix` (オプション): すべてのエイリアスに使用するプレフィックス
- `suffix` (オプション): すべてのエイリアスに使用するサフィックス
- `then_value` (オプション): 比較が成功した場合に使用する値。デフォルトは `1`
- `else_value` (オプション): 比較が失敗した場合に使用する値失敗します。デフォルトは `0` です。
- `quote` (オプション): 結果のエイリアスを引用符で囲むかどうか。デフォルトは true です。
- `distinct` (オプション): 集計関数に `DISTINCT` 句を適用するかどうか。デフォルトは false です。

すべての SQLMesh マクロ関数と同様に、`@PIVOT` を呼び出す際に引数を省略するには、後続の引数に引数名と特殊なキーワード演算子 `:=` を渡す必要があります。例えば、`@PIVOT(status, ['cancelled', 'completed'], cmp := '<')` のように、`agg` 引数を省略できます。マクロ関数の引数の詳細については、[下記](#positional-and-keyword-arguments) をご覧ください。

例えば、次のクエリ:

```sql linenums="1"
SELECT
  date_day,
  @PIVOT(status, ['cancelled', 'completed'])
FROM rides
GROUP BY 1
```

次のように表示されます。

```sql linenums="1"
SELECT
  date_day,
  SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) AS "'cancelled'",
  SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS "'completed'"
FROM rides
GROUP BY 1
```

### @DEDUPLICATE

`@DEDUPLICATE` は、指定されたパーティションに基づいてテーブル内の行を重複排除し、ウィンドウ関数を使用して列を順序付けするために使用されます。

以下の引数をこの順序でサポートします。

- `relation`: 重複排除するテーブルまたは CTE の名前
- `partition_by`: 重複排除する行を選択するための行ウィンドウを識別するために使用する列名または式
- `order_by`: ORDER BY 句を表す文字列のリスト（オプション）。['<c​​olumn_name> desc nulls last'] のように、null の順序を追加できます。

例えば、次のクエリがあります。

```sql linenums="1"
with raw_data as (
@deduplicate(my_table, [id, cast(event_date as date)], ['event_date DESC', 'status ASC'])
)

select * from raw_data
```

次のように表示されます。

```sql linenums="1"
WITH "raw_data" AS (
  SELECT
    *
  FROM "my_table" AS "my_table"
  QUALIFY
    ROW_NUMBER() OVER (PARTITION BY "id", CAST("event_date" AS DATE) ORDER BY "event_date" DESC, "status" ASC) = 1
)
SELECT
  *
FROM "raw_data" AS "raw_data"
```

### @DATE_SPINE

`@DATE_SPINE` は、日付スパインを構築するために必要な SQL を返します。スパインには start_date（日付部分と一致している場合）と end_date が含まれます。これは、end_date を含まない `dbt-utils` の [`date_spine`](https://github.com/dbt-labs/dbt-utils?tab=readme-ov-file#date_spine-source) マクロとは異なります。これは通常、一意のハードコードされた日付範囲を他のテーブル/ビューに結合するために使用されます。これにより、多くの SQL モデルにわたって `where` 句で日付範囲を頻繁に調整する必要がなくなります。

以下の引数をこの順序でサポートします。

- `datepart`: 日付スパインに使用する日付要素（日、週、月、四半期、年）
- `start_date`: 日付スパインの開始日（YYYY-MM-DD 形式）
- `end_date`: 日付スパインの終了日（YYYY-MM-DD 形式）

例えば、次のクエリがあります。

```sql linenums="1"
WITH discount_promotion_dates AS (
  @date_spine('day', '2024-01-01', '2024-01-16')
)

SELECT * FROM discount_promotion_dates
```

次のように表示されます。

```sql linenums="1"
WITH "discount_promotion_dates" AS (
  SELECT
    "_exploded"."date_day" AS "date_day"
  FROM UNNEST(CAST(GENERATE_SERIES(CAST('2024-01-01' AS DATE), CAST('2024-01-16' AS DATE), INTERVAL '1' DAY) AS
DATE[])) AS "_exploded"("date_day")
)
SELECT
  "discount_promotion_dates"."date_day" AS "date_day"
FROM "discount_promotion_dates" AS "discount_promotion_dates"
```

注: これはDuckDB SQLであり、他の方言はそれに応じてトランスパイルされます。
- `Redshift / MySQL / MSSQL`では再帰CTE（共通テーブル式）が使用されます。
- 特に`MSSQL`の場合、再帰回数の制限は約100回です。これが問題になる場合は、日付スパインマクロロジックの後に`OPTION (MAXRECURSION 0)`句を追加することで制限を解除できます。これは長い日付範囲に適用されます。

### @RESOLVE_TEMPLATE

`@resolve_template` は、物理オブジェクト名の *構成要素* にアクセスする必要がある場合に使用するためのヘルパーマクロです。以下の状況での使用を想定しています。

- ストレージとコンピューティングを分離するエンジン (Athena、Trino、Spark など) において、モデルごとにテーブルの場所を明示的に制御する。
- 物理テーブル名から派生したエンジン固有のメタデータテーブル (Trino の [`<table>$properties`](https://trino.io/docs/current/connector/iceberg.html#metadata-tables) メタデータテーブルなど) への参照を生成する。

内部的には `@this_model` 変数を使用しているため、`creating` および `evaluation` [実行時ステージ](./macro_variables.md#runtime-variables) でのみ使用できます。 `loading` 実行段階で使用しようとすると、何も実行されません。

`@resolve_template` マクロは以下の引数をサポートします。

- `template` - AST ノードにレンダリングする文字列テンプレート
- `mode` - テンプレートをレンダリングした後に返す SQLGlot AST ノードの型。有効な値は `literal` または `table` です。デフォルトは `literal` です。

`template` には、以下の置換対象となるプレースホルダを含めることができます。

- `@{catalog_name}` - カタログ名（例：`datalake`）
- `@{schema_name}` - SQLMesh がモデルバージョンテーブルに使用している物理スキーマ名（例：`sqlmesh__landing`）
- `@{table_name}` - SQLMesh がモデルバージョンテーブルに使用している物理テーブル名（例：`landing__customers__2517971505`）

テンプレートのプレースホルダでは中括弧構文 `@{}` が使用されていることに注意してください。詳しくは [上記](#文字列への変数の埋め込み) をご覧ください。

`@resolve_template` マクロは `MODEL` ブロックで使用できます。

```sql linenums="1" hl_lines="5"
MODEL (
  name datalake.landing.customers,
  ...
  physical_properties (
    location = @resolve_template('s3://warehouse-data/@{catalog_name}/prod/@{schema_name}/@{table_name}')
  )
);
-- CREATE TABLE "datalake"."sqlmesh__landing"."landing__customers__2517971505" ...
-- WITH (location = 's3://warehouse-data/datalake/prod/sqlmesh__landing/landing__customers__2517971505')
```

また、クエリ内では、`mode := 'table'` を使用します。

```sql linenums="1"
SELECT * FROM @resolve_template('@{catalog_name}.@{schema_name}.@{table_name}$properties', mode := 'table')
-- SELECT * FROM "datalake"."sqlmesh__landing"."landing__customers__2517971505$properties"
```

### @AND

`@AND` は、`AND` 演算子を使用してオペランドのシーケンスを結合し、NULL 式を除外します。

例えば、次の式を考えます。

```sql linenums="1"
@AND(TRUE, NULL)
```

次のように表示されます。

```sql linenums="1"
TRUE
```

### @OR

`@OR` は、`OR` 演算子を使用してオペランドのシーケンスを結合し、NULL 式を除外します。

例えば、次の式があります。

```sql linenums="1"
@OR(TRUE, NULL)
```

次のように表示されます。

```sql linenums="1"
TRUE
```

### SQL 句演算子

SQLMesh のマクロシステムには、SQL 構文のさまざまな句に対応する 6 つの演算子があります。これらは次のとおりです。

- `@WITH`: 共通テーブル式の `WITH` 句
- `@JOIN`: テーブルの `JOIN` 句
- `@WHERE`: フィルタリングの `WHERE` 句
- `@GROUP_BY`: グループ化の `GROUP BY` 句
- `@HAVING`: グループ化フィルタリングの `HAVING` 句
- `@ORDER_BY`: 順序付けの `ORDER BY` 句
- `@LIMIT`: 制限の `LIMIT` 句

これらの演算子はそれぞれ、対応する句のコードをモデルの SQL クエリに動的に追加するために使用されます。

#### SQL 句演算子の動作

SQL 句演算子は、句を生成するかどうかを決定する単一の引数を取ります。

引数が `TRUE` の場合、句のコードが生成され、`FALSE` の場合、コードは生成されません。引数は *SQL* で記述し、その値は [SQLGlot](https://github.com/tobymao/sqlglot) SQL エンジンによって評価されます。

各 SQL 句演算子はクエリ内で 1 回しか使用できませんが、共通テーブル式やサブクエリでも、その演算子を 1 回だけ使用できます。

SQL 句演算子の例として、上記の [ユーザー定義変数](#user-defined-variables) セクションのサンプルモデルをもう一度見てみましょう。

記述されているとおり、モデルには常に `WHERE` 句が含まれます。`@WHERE` マクロ演算子を使用することで、この句の存在を動的にすることができます。

```sql linenums="1"
MODEL (
  name sqlmesh_example.full_model,
  kind FULL,
  cron '@daily',
  audits (assert_positive_order_ids),
);

@DEF(size, 1);

SELECT
  item_id,
  count(distinct id) AS num_orders,
FROM
  sqlmesh_example.incremental_model
@WHERE(TRUE) item_id > @size
GROUP BY item_id
```

`@WHERE` 引数は `TRUE` に設定されているため、レンダリングされたモデルに WHERE コードが含まれます。

```sql linenums="1"
SELECT
  item_id,
  count(distinct id) AS num_orders,
FROM
  sqlmesh_example.incremental_model
WHERE item_id > 1
GROUP BY item_id
```

`@WHERE` 引数を `FALSE` に設定した場合、`WHERE` 句はクエリから省略されます。

これらの演算子は、引数の値がハードコードされている場合はあまり役に立ちません。代わりに、引数は SQLGlot SQL エグゼキュータで実行可能なコードで構成できます。

例えば、次のクエリでは 1 が 2 より小さいため、`WHERE` 句が含まれます。

```sql linenums="1"
MODEL (
  name sqlmesh_example.full_model,
  kind FULL,
  cron '@daily',
  audits (assert_positive_order_ids),
);

@DEF(size, 1);

SELECT
  item_id,
  count(distinct id) AS num_orders,
FROM
  sqlmesh_example.incremental_model
@WHERE(1 < 2) item_id > @size
GROUP BY item_id
```

演算子の引数コードにはマクロ変数を含めることができます。

この例では、比較対象となる2つの数値はハードコードされるのではなく、マクロ変数として定義されています。

```sql linenums="1"
MODEL (
  name sqlmesh_example.full_model,
  kind FULL,
  cron '@daily',
  audits (assert_positive_order_ids),
);

@DEF(left_number, 1);
@DEF(right_number, 2);
@DEF(size, 1);

SELECT
  item_id,
  count(distinct id) AS num_orders,
FROM
  sqlmesh_example.incremental_model
@WHERE(@left_number < @right_number) item_id > @size
GROUP BY item_id
```

マクロ変数 `left_number` と `right_number` が代入された後、`@WHERE` への引数は、前のハードコードされた例と同様に "1 < 2" になります。

### SQL 句演算子の例

このセクションでは、各 SQL 句演算子の使用例を簡単に示します。

例では、次の単純な SELECT 文のバリエーションを使用します。

```sql linenums="1"
SELECT *
FROM all_cities
```

#### @WITH 演算子

`@WITH` 演算子は、[共通テーブル式](https://en.wikipedia.org/wiki/Hierarchical_and_recursive_queries_in_SQL#Common_table_expression)、つまり「CTE」を作成するために使用されます。

CTE は通常、派生テーブル（`FROM` 句内のサブクエリ）の代わりに使用され、SQL コードの可読性を高めます。あまり一般的ではありませんが、再帰 CTE は SQL による階層データの分析をサポートします。

```sql linenums="1"
@WITH(True) all_cities as (select * from city)
select *
FROM all_cities
```

renders to

```sql linenums="1"
WITH all_cities as (select * from city)
select *
FROM all_cities
```

#### @JOIN 演算子

`@JOIN` 演算子は、テーブル間または他の SQL オブジェクト間の結合を指定します。さまざまな結合タイプ（INNER、OUTER、CROSS など）をサポートしています。

```sql linenums="1"
select *
FROM all_cities
LEFT OUTER @JOIN(True) country
  ON city.country = country.name
```

renders to

```sql linenums="1"
select *
FROM all_cities
LEFT OUTER JOIN country
  ON city.country = country.name
```

`@JOIN` 演算子は、`LEFT OUTER` が `JOIN` 仕様のコンポーネントであることを認識し、`@JOIN` 引数が False と評価された場合はそれを省略します。

#### @WHERE 演算子

`@WHERE` 演算子は、引数が True と評価された場合に、クエリにフィルタリング用の `WHERE` 句を追加します。

```sql linenums="1"
SELECT *
FROM all_cities
@WHERE(True) city_name = 'Toronto'
```

renders to

```sql linenums="1"
SELECT *
FROM all_cities
WHERE city_name = 'Toronto'
```

#### @GROUP_BY operator

```sql linenums="1"
SELECT *
FROM all_cities
@GROUP_BY(True) city_id
```

renders to

```sql linenums="1"
SELECT *
FROM all_cities
GROUP BY city_id
```

#### @HAVING operator

```sql linenums="1"
SELECT
count(city_pop) as population
FROM all_cities
GROUP BY city_id
@HAVING(True) population > 1000
```

renders to

```sql linenums="1"
SELECT
count(city_pop) as population
FROM all_cities
GROUP BY city_id
HAVING population > 1000
```

#### @ORDER_BY operator

```sql linenums="1"
SELECT *
FROM all_cities
@ORDER_BY(True) city_pop
```

renders to

```sql linenums="1"
SELECT *
FROM all_cities
ORDER BY city_pop
```

#### @LIMIT operator

```sql linenums="1"
SELECT *
FROM all_cities
@LIMIT(True) 10
```

renders to

```sql linenums="1"
SELECT *
FROM all_cities
LIMIT 10
```

## ユーザー定義マクロ関数

ユーザー定義マクロ関数を使用すると、同じマクロコードを複数のモデルで使用できます。

SQLMesh は、SQL と Python の 2 つの言語で記述されたユーザー定義マクロ関数をサポートしています。

- SQL マクロ関数は [Jinja テンプレートシステム](./jinja_macros.md#user-defined-macro-functions) を使用する必要があります。
- Python マクロ関数は SQLGlot ライブラリを使用することで、マクロ変数と演算子だけでは実現できない複雑な操作を可能にします。

### Python マクロ関数

#### セットアップ

Python マクロ関数は、SQLMesh プロジェクトの `macros` ディレクトリ内の `.py` ファイルに配置する必要があります。1 つの `.py` ファイルに複数の関数を定義することも、複数のファイルに分散させることもできます。

SQLMesh プロジェクトの `macros` ディレクトリには、空の `__init__.py` ファイルが必要です。このファイルは、`sqlmesh init` でプロジェクトのスキャフォールドを作成すると自動的に作成されます。

マクロ定義を含む各 `.py` ファイルには、`from sqlmesh import macro` を使用して SQLMesh の `macro` デコレータをインポートする必要があります。

Python マクロは、SQLMesh の `@macro()` デコレータで修飾された通常の Python 関数として定義されます。関数の最初の引数は `evaluator` である必要があります。これは、マクロ関数が実行されるマクロ評価コンテキストを提供します。

#### 入力と出力

Python マクロは、マクロ呼び出しに渡されるすべての引数を、関数本体で使用される前に SQLGlot で解析します。したがって、関数定義で [引数の型アノテーションが指定されていない限り](#引数データ型)、マクロ関数コードは SQLGlot 式を処理する必要があり、式の属性/内容を抽出して使用する必要がある場合があります。

Python マクロ関数は、`string` 型または SQLGlot `expression` 型のいずれかの値を返すことができます。SQLMesh は、関数の実行後に返された文字列を自動的に SQLGlot 式に解析し、モデルクエリのセマンティック表現に組み込むことができます。

マクロ関数は、クエリ内ですべて同じ役割を果たす [文字列または式のリストを返す](#複数の値を返す) 場合があります（例: 列定義の指定）。たとえば、複数の `CASE WHEN` ステートメントを含むリストはクエリに適切に組み込まれますが、 `CASE WHEN` ステートメントと `WHERE` 句の両方を含むリストは組み込まれません。

#### マクロ関数の基本

この例は、Python マクロを定義するための基本的な要件を示しています。マクロはユーザー指定の引数を取らず、文字列 `text` を返します。

```python linenums="1"
from sqlmesh import macro

@macro() # Note parentheses at end of `@macro()` decorator
def print_text(evaluator):
  return 'text'
```

これを SQLMesh SQL モデルで次のように使用できます。

```sql linenums="1"
SELECT
  @print_text() as my_text
FROM table
```

処理後、次のようにレンダリングされます。

```sql linenums="1"
SELECT
  text as my_text
FROM table
```

Python関数は文字列「'text'」を返しましたが、レンダリングされたクエリでは列名として「text」を使用していることに注意してください。これは、関数が返したテキストがSQLGlotによってSQLコードとして解析され、クエリのセマンティック表現に統合されるためです。

関数定義内の一重引用符で囲まれた値を二重引用符で囲んで「"'text'"」とすると、レンダリングされたクエリでは「text」が文字列として扱われます。

```python linenums="1"
from sqlmesh import macro

@macro()
def print_text(evaluator):
    return "'text'"
```

前と同じモデルクエリで実行すると、次のようにレンダリングされます。

```sql linenums="1"
SELECT
  'text' as my_text
FROM table
```

#### 引数のデータ型

ほとんどのマクロ関数は引数を提供し、ユーザーは関数の呼び出し時にカスタム値を指定できます。引数のデータ型は、マクロコードがその値を処理する方法において重要な役割を果たします。マクロ定義に型アノテーションを指定することで、マクロコードが期待するデータ型を確実に受け取ることができます。このセクションでは、SQLMesh マクロ型アノテーションについて簡単に説明します。詳細については、[下記](#typed-macros) を参照してください。

[上記](#inputs-and-outputs) のとおり、マクロ呼び出しに渡される引数の値は、関数コードで使用できるようになる前に SQLGlot によって解析されます。マクロ関数定義で引数に型アノテーションが指定されていない場合、その値は常に関数本体内で SQLGlot 式になります。したがって、マクロ関数コードは式を直接操作する必要があります（使用前に式から情報を抽出する必要がある場合があります）。

マクロ関数定義において引数に型アノテーションが付与されている場合、マクロ呼び出しに渡される値は、SQLGlot による解析後、関数本体で使用される前に、その型に強制変換されます。基本的に、SQLMesh は式からアノテーション付きデータ型の関連情報を（可能な場合）抽出します。

例えば、次のマクロ関数は、引数の値が整数 1、2、または 3 のいずれかであるかどうかを判定します。

```python linenums="1"
from sqlmesh import macro

@macro()
def arg_in_123(evaluator, my_arg):
    return my_arg in [1,2,3]
```

このマクロが呼び出されると、呼び出し時に整数が渡された場合でも `FALSE` が返されます。次のマクロ呼び出しを考えてみましょう。

``` sql linenums="1"
SELECT
  @arg_in_123(1)
```

`SELECT FALSE` を返す理由は次のとおりです。

1. 渡された値 `1` は、関数コードが実行される前に SQLGlot によって SQLGlot 式に変換されます。
2. `[1,2,3]` には一致する SQLGlot 式がありません。

ただし、関数定義で `my_arg` に整数 `int` 型をアノテーションすると、マクロは引数を通常の Python 関数と同様に扱います。

```python linenums="1"
from sqlmesh import macro

@macro()
def arg_in_123(evaluator, my_arg: int): # Type annotation `my_arg: int`
    return my_arg in [1,2,3]
```

マクロ呼び出しは `SELECT TRUE` を返します。これは、関数コードの実行前に値が Python 整数に強制変換され、`[1,2,3]` に `1` が含まれているためです。

引数にデフォルト値がある場合、関数コードの実行前に SQLGlot によってその値が解析されることはありません。したがって、型アノテーションを追加するか、デフォルト値を SQLGlot 式にするか、デフォルト値を `None` にすることで、デフォルト値のデータ型がユーザーが指定した引数のデータ型と一致するように注意してください。

#### 位置引数とキーワード引数

マクロ呼び出しでは、引数を省略しない場合は、位置引数で引数を指定できます。

例えば、`add_args()` 関数を考えてみましょう。この関数には3つの引数があり、関数定義でデフォルト値が指定されています。

```python linenums="1"
from sqlmesh import macro

@macro()
def add_args(
    evaluator,
    argument_1: int = 1,
    argument_2: int = 2,
    argument_3: int = 3
):
    return argument_1 + argument_2 + argument_3
```

すべての引数に値を指定する `@add_args` 呼び出しは、`@add_args(5, 6, 7)` のように位置引数を受け入れます（5 + 6 + 7 = `18` を返します）。最後の `argument_3` を省略してデフォルト値を使用する呼び出しも、位置引数を使用できます（5 + 6 + 3 = `14` を返します）。

ただし、引数を省略するには、後続の引数の名前を指定する必要があります（つまり、「キーワード引数」を使用する必要があります）。例えば、上記の 2 番目の引数を省略して `@add_args(5, , 7)` とすると、エラーが発生します。

Python とは異なり、SQLMesh のキーワード引数では特殊演算子 `:=` を使用する必要があります。上記の 2 番目の引数をスキップしてデフォルト値を使用するには、呼び出しで 3 番目の引数に名前を付ける必要があります: `@add_args(5, argument_3 := 8)` (5 + 2 + 8 = `15` を返します)。

#### 可変長引数

[前のセクション](#位置引数とキーワード引数)で定義した `add_args()` マクロは、引数を3つしか受け入れず、3つすべてに値が必要です。ユーザーは任意の数の値を加算したい場合があるため、このマクロの柔軟性は大きく制限されます。

このマクロは、ユーザーが呼び出し時に任意の数の引数を指定できるようにすることで改善できます。これを実現するために、Python の「可変長引数」を使用します。

```python linenums="1"
from sqlmesh import macro

@macro()
def add_args(evaluator, *args: int): # Variable-length arguments of integer type `*args: int`
    return sum(args)
```

このマクロは1つ以上の引数を指定して呼び出すことができます。例:

- `@add_args(1)` は 1 を返します。
- `@add_args(1, 2)` は 3 を返します。
- `@add_args(1, 2, 3)` は 6 を返します。

#### 複数の値を返す

マクロ関数は、1回の関数呼び出しから複数の出力を作成することで、モデルコードを整理する便利な方法です。Python マクロ関数は、文字列または SQLGlot 式のリストを返すことでこれを実現します。

例えば、文字列列の値からインジケータ変数を作成したいとします。これは、列名と、インジケータを作成する値のリストを渡し、それを `CASE WHEN` 文に挿入することで実現できます。

SQLMesh は入力オブジェクトを解析するため、関数本体では SQLGLot 式になります。そのため、関数コードでは入力リストを通常の Python リストとして扱うことはできません。

関数コードが実行される前に、入力 Python リストに対して次の 2 つの処理が行われます。

1. 各エントリが SQLGlot によって解析されます。異なる入力は、それぞれ異なるSQLGlot式に解析されます。
    - 数値は[`Literal`式](https://sqlglot.com/sqlglot/expressions.html#Literal)に解析されます。
    - 引用符で囲まれた文字列は[`Literal`式](https://sqlglot.com/sqlglot/expressions.html#Literal)に解析されます。
    - 引用符で囲まれていない文字列は[`Column`式](https://sqlglot.com/sqlglot/expressions.html#Column)に解析されます。

2. 解析されたエントリは、SQLGlotの[`Array`式](https://sqlglot.com/sqlglot/expressions.html#Array)に格納されます。これは、Pythonのリストに相当するSQLエンティティです。

入力された`Array`式である`values`はPythonのリストではないため、直接反復処理することはできません。代わりに、`values.expressions`を使用して、`expressions`属性を反復処理します。

```python linenums="1"
from sqlmesh import macro

@macro()
def make_indicators(evaluator, string_column, values):
    cases = []

    for value in values.expressions: # Iterate over `values.expressions`
        cases.append(f"CASE WHEN {string_column} = '{value}' THEN '{value}' ELSE NULL END AS {string_column}_{value}")

    return cases
```

モデル クエリでこの関数を呼び出して、次のように `vehicle` 列の値 `truck` と `bus` に対して `CASE WHEN` ステートメントを作成します。

```sql linenums="1"
SELECT
  @make_indicators(vehicle, [truck, bus])
FROM table
```

結果は次のようになります:

```sql linenums="1"
SELECT
  CASE WHEN vehicle = 'truck' THEN 'truck' ELSE NULL END AS vehicle_truck,
  CASE WHEN vehicle = 'bus' THEN 'bus' ELSE NULL END AS vehicle_bus,
FROM table
```

`@make_indicators(vehicle, [truck, bus])` という呼び出しでは、3つの値のいずれも引用符で囲まれていないことに注意してください。

引用符で囲まれていないため、SQLGlot はすべてを `Column` 式として解析します。文字列の構築時に一重引用符を使用した箇所 (`'{value}'`) は、出力でも一重引用符で囲まれます。引用符で囲まなかった箇所 (`{string_column} = ` および `{string_column}_{value}`) は、一重引用符で囲まれません。

#### 定義済み変数とローカル変数の値へのアクセス

[定義済み変数](./macro_variables.md#predefined-variables) と [ユーザー定義ローカル変数](#local-variables) は、マクロ本体内で `evaluator.locals` 属性を介してアクセスできます。

すべてのマクロ関数の最初の引数であるマクロ評価コンテキスト `evaluator` の `locals` 属性には、マクロ変数の値が格納されています。`evaluator.locals` は、マクロ変数名とそれに対応する値をキーと値のペアとして持つ辞書です。

例えば、関数は、実行開始時のエポックタイムスタンプを含む定義済み変数 `execution_epoch` にアクセスできます。

```python linenums="1"
from sqlmesh import macro

@macro()
def get_execution_epoch(evaluator):
    return evaluator.locals['execution_epoch']
```

この関数は、モデル クエリで呼び出されたときに `execution_epoch` 値を返します。

```sql linenums="1"
SELECT
  @get_execution_epoch() as execution_epoch
FROM table
```

同じアプローチはユーザー定義のローカル マクロ変数にも適用され、キー `"execution_epoch"` はアクセスするユーザー定義変数の名前に置き換えられます。

この方法でユーザー定義のローカル変数にアクセスする場合の欠点の一つは、変数名が関数内にハードコードされてしまうことです。より柔軟なアプローチとしては、ローカルマクロ変数の名前を関数の引数として渡す方法があります。

```python linenums="1"
from sqlmesh import macro

@macro()
def get_macro_var(evaluator, macro_var):
    return evaluator.locals[macro_var]
```

次のように、値 1 を持つローカル マクロ変数 `my_macro_var` を定義し、それを `get_macro_var` 関数に渡すことができます。

```sql linenums="1"
MODEL (...);

@DEF(my_macro_var, 1); -- Define local macro variable 'my_macro_var'

SELECT
  @get_macro_var('my_macro_var') as macro_var_value -- Access my_macro_var value from Python macro function
FROM table
```

モデルクエリは次のようにレンダリングされます。

```sql linenums="1"
SELECT
  1 as macro_var_value
FROM table
```

#### グローバル変数の値へのアクセス

[ユーザー定義グローバル変数](#global-variables)は、マクロ本体内で `evaluator.var` メソッドを使用してアクセスできます。

グローバル変数が定義されていない場合、このメソッドは Python の `None` 値を返します。メソッドの2番目の引数として、異なるデフォルト値を指定することもできます。

例:

```python linenums="1"
from sqlmesh.core.macros import macro

@macro()
def some_macro(evaluator):
    var_value = evaluator.var("<var_name>") # Default value is `None`
    another_var_value = evaluator.var("<another_var_name>", "default_value") # Default value is `"default_value"`
    ...
```

#### モデル、物理テーブル、仮想レイヤービューの名前へのアクセス

すべての SQLMesh モデルは、`MODEL` 仕様に名前を持ちます。この名前は SQL エンジン内の特定のオブジェクトに対応しない可能性があるため、モデルの「未解決」名と呼ばれます。

SQLMesh は、モデルをレンダリングして実行する際に、異なる段階でモデル名を 3 つの形式に変換します。

1. *完全修飾* 名

    - モデル名が `schema.table` 形式の場合、SQLMesh は適切なカタログを特定し、`catalog.schema.table` のように追加します。
    - SQLMesh は、SQL エンジンの引用符と大文字小文字の区別のルールを使用して、名前の各構成要素を引用符で囲みます。`"catalog"."schema"."table"` のように。

2. *解決済み* 物理テーブル名

    - モデルの基盤となる物理テーブルの修飾名

3. *解決済み* 仮想レイヤービュー名

    - モデルが実行される環境におけるモデルの仮想レイヤービューの修飾名

Python マクロでは、`evaluation` コンテキストオブジェクトのプロパティを介して、これらの 3 つの形式にアクセスできます。

未解決の完全修飾名には、`this_model_fqn` プロパティを介してアクセスできます。

```python linenums="1"
from sqlmesh.core.macros import macro

@macro()
def some_macro(evaluator):
    # Example:
    # Name in model definition: landing.customers
    # Value returned here: '"datalake"."landing"."customers"'
    unresolved_model_fqn = evaluator.this_model_fqn
    ...
```

`this_model` プロパティを介して、解決済みの物理テーブル名と仮想レイヤービュー名にアクセスします。

`this_model` プロパティは、ランタイムステージに応じて異なる名前を返します。

- `promoting` ランタイムステージ: `this_model` は仮想レイヤービュー名に解決されます。

  - 例
    - モデル名は `db.test_model` です。
    - `plan` は `dev` 環境で実行されています。
    - `this_model` は `"catalog"."db__dev"."test_model"` に解決されます (スキーマ名に `__dev` サフィックスが付いていることに注意してください)。

- その他のすべてのランタイムステージ: `this_model` は物理テーブル名に解決されます。

  - 例
    - モデル名は `db.test_model` です。
    - `plan` はどの環境でも実行されています。
    - `this_model` は `"catalog"."sqlmesh__project"."project__test_model__684351896"` に解決されます。

```python linenums="1"
from sqlmesh.core.macros import macro

@macro()
def some_macro(evaluator):
    if evaluator.runtime_stage == "promoting":
        # virtual layer view name '"catalog"."db__dev"."test_model"'
        resolved_name = evaluator.this_model
    else:
        # physical table name '"catalog"."sqlmesh__project"."project__test_model__684351896"'
        resolved_name = evaluator.this_model
    ...
```

#### モデルスキーマへのアクセス

列の型を静的に決定できる場合、Python マクロ関数内では、評価コンテキストの `column_to_types()` メソッドを介してモデルスキーマにアクセスできます。たとえば、[外部モデル](../models/external_models.md) のスキーマには、`sqlmesh create_external_models` コマンドを実行した後にのみアクセスできます。

このマクロ関数は、上流モデルの列名にプレフィックスを追加して変更します。

```python linenums="1"
from sqlglot import exp
from sqlmesh.core.macros import macro

@macro()
def prefix_columns(evaluator, model_name, prefix: str):
    renamed_projections = []

    # The following converts `model_name`, which is a SQLGlot expression, into a lookup key,
    # assuming that it does not contain quotes. If it did, we would have to generate SQL for
    # each part of `model_name` separately and then concatenate these parts, because in that
    # case `model_name.sql()` would produce an invalid lookup key.
    model_name_sql = model_name.sql()

    for name in evaluator.columns_to_types(model_name_sql):
        new_name = prefix + name
        renamed_projections.append(exp.column(name).as_(new_name))

    return renamed_projections
```

これは次のような SQL モデルで使用できます。

```sql linenums="1"
MODEL (
  name schema.child,
  kind FULL
);

SELECT
  @prefix_columns(schema.parent, 'stg_')
FROM
  schema.parent
```

`columns_to_types` は `schema.parent` のような _引用符で囲まれていないモデル名_ を期待することに注意してください。型アノテーションのないマクロ引数は SQLGlot 式であるため、マクロコードはそこから意味のある情報を抽出する必要があります。例えば、上記のマクロ定義のルックアップキーは、`sql()` メソッドを用いて `model_name` の SQL コードを生成することで抽出されます。

上流モデルのスキーマへのアクセスは、さまざまな理由で有用です。例:

- 下流のコンシューマーが外部テーブルまたはソーステーブルに密結合しないように列名を変更する
- 特定の条件を満たす列のサブセットのみを選択する（例: 特定のプレフィックスで始まる列）
- 列に変換を適用する（PII のマスキングや列の型に基づく各種統計の計算など）

したがって、`columns_to_types` を利用することで、[DRY](https://en.wikipedia.org/wiki/Don%27t_repeat_yourself) 原則に従ってコードを記述することもできます。対象となるモデルごとに異なるマクロを作成する代わりに、単一のマクロ関数で変換を実装できるためです。

注: プロジェクトのロード時にスキーマが利用できないモデルが存在する場合があります。その場合、`__schema_unavailable_at_load__` という適切な名前の特別なプレースホルダー列が返されます。場合によっては、スキーマが利用できないことによる問題を回避するために、マクロの実装でこのプレースホルダーを考慮する必要があります。

#### スナップショットへのアクセス

SQLMesh プロジェクトが正常にロードされると、Python マクロ関数や SQL を生成する Python モデルから、`MacroEvaluator` の `get_snapshot` メソッドを介してスナップショットにアクセスできるようになります。

これにより、以下の例に示すように、実行時に物理テーブル名や特定のスナップショットの処理間隔を検査できるようになります。

```python linenums="1"
from sqlmesh.core.macros import macro

@macro()
def some_macro(evaluator):
    if evaluator.runtime_stage == "evaluating":
        # Check the intervals a snapshot has data for and alter the behavior of the macro accordingly
        intervals = evaluator.get_snapshot("some_model_name").intervals
        ...
    ...
```

#### SQLGlot 式の使用

SQLMesh は、Python マクロ関数から返される文字列を [SQLGlot](https://github.com/tobymao/sqlglot) 式に自動的に解析し、モデルクエリのセマンティック表現に組み込むことができます。関数は SQLGlot 式を直接返すこともできます。

例えば、`WHERE` 句の述語で `BETWEEN` 演算子を使用するマクロ関数を考えてみましょう。述語を文字列として返す関数は次のようになります。関数の引数は Python の f 文字列に置換されます。

```python linenums="1"
from sqlmesh import macro, SQL

@macro()
def between_where(evaluator, column_name: SQL, low_val: SQL, high_val: SQL):
    return f"{column_name} BETWEEN {low_val} AND {high_val}"
```

この関数はクエリ内で呼び出すことができます。

```sql linenums="1"
SELECT
  a
FROM table
WHERE @between_where(a, 1, 3)
```

And it would render to:

```sql linenums="1"
SELECT
  a
FROM table
WHERE a BETWEEN 1 and 3
```

あるいは、この関数は、セマンティック表現を構築するための SQLGlot の式メソッドを使用して、その文字列と同等の [SQLGLot 式](https://github.com/tobymao/sqlglot/blob/main/sqlglot/expressions.py) を返すこともできます。

```python linenums="1"
from sqlmesh import macro

@macro()
def between_where(evaluator, column, low_val, high_val):
    return column.between(low_val, high_val)
```

これらのメソッドは、マクロ関数の実行時に `column` 引数が SQLGlot [列式](https://sqlglot.com/sqlglot/expressions.html#Column) として解析されるため使用できます。

列式は [Condition クラス](https://sqlglot.com/sqlglot/expressions.html#Condition) のサブクラスであるため、[`between`](https://sqlglot.com/sqlglot/expressions.html#Condition.between) や [`like`](https://sqlglot.com/sqlglot/expressions.html#Condition.like) などのビルダーメソッドがあります。

#### マクロの pre/post ステートメント

マクロ関数は、モデル内で pre/post ステートメントを生成するために使用できます。

デフォルトでは、pre/post ステートメントのマクロ関数をモデルに初めて追加すると、SQLMesh はそれらのモデルを直接変更したものとして扱い、次のプランでバックフィルを要求します。また、SQLMesh は pre/post ステートメントのマクロの編集または削除を互換性のない変更として扱います。

マクロがモデルによって返されるデータに影響を与えず、その追加、編集、削除によってバックフィルをトリガーしたくない場合は、マクロ定義で、マクロがモデルのメタデータのみに影響を与えるように指定できます。SQLMesh は、マクロを追加、編集、削除した場合でも変更を検出し、モデルの新しいスナップショットを作成しますが、その変更を互換性のない変更と見なしてバックフィルを要求することはありません。

マクロがモデルのメタデータのみに影響を与えるように指定するには、`@macro()` デコレータの `metadata_only` 引数を `True` に設定します。例えば：

```python linenums="1" hl_lines="3"
from sqlmesh import macro

@macro(metadata_only=True)
def print_message(evaluator, message):
  print(message)
```

### 型付きマクロ

SQLMesh の型付きマクロは、Python の型ヒントを活用し、SQL マクロの可読性、保守性、使いやすさを向上させます。これらのマクロを使用すると、開発者は引数に想定される型を指定できるため、マクロをより直感的に記述でき、エラーの発生を抑えられます。

#### 型付きマクロのメリット

1. **可読性の向上**: 型を指定することで、マクロの意図が他の開発者や将来の開発者にとって明確になります。
2. **定型コードの削減**: マクロ関数内で手動で型変換を行う必要がなくなり、コアロジックに集中できます。
3. **自動補完の強化**: 指定された型に基づいて、IDE による自動補完とドキュメントの精度が向上します。

#### 型付きマクロの定義

SQLMesh の型付きマクロは、Python の型ヒントを使用します。以下は、文字列を指定された回数繰り返す型付きマクロの簡単な例です。

```python linenums="1"
from sqlmesh import macro

@macro()
def repeat_string(evaluator, text: str, count: int):
    return text * count
```

このマクロは、`str` 型の `text` と `int` 型の `count` という2つの引数を取り、文字列を返します。

型ヒントがない場合、入力は2つの SQLGlot `exp.Literal` オブジェクトとなり、Python の `str` 型と `int` 型に手動で変換する必要があります。型ヒントを使用すると、これらを文字列型と整数型として直接操作できます。

SQLMesh モデルでこのマクロを使ってみましょう。

```sql linenums="1"
SELECT
  @repeat_string('SQLMesh ', 3) as repeated_string
FROM some_table;
```

残念ながら、このモデルはレンダリング時にエラーを生成します。

```
Error: Invalid expression / Unexpected token. Line 1, Col: 23.
  SQLMesh SQLMesh SQLMesh
```

なぜでしょうか? マクロは期待どおりに `SQLMesh SQLMesh SQLMesh` を返しましたが、その文字列はレンダリングされたクエリでは有効な SQL ではありません。

```sql linenums="1" hl_lines="2"
SELECT
  SQLMesh SQLMesh SQLMesh as repeated_string ### invalid SQL code
FROM some_table;
```

問題は、マクロの Python 戻り値型 `str` と、解析された SQL クエリが期待する型が一致していないことです。

SQLMesh マクロは、クエリのセマンティック表現を変更することで動作することに注意してください。この表現では、SQLGlot の文字列リテラル型が期待されます。SQLMesh はクエリのセマンティック表現が期待する型を返すよう最善を尽くしますが、すべてのシナリオでそれが可能というわけではありません。

したがって、SQLGlot の `exp.Literal.string()` メソッドを使用して、出力を明示的に変換する必要があります。

```python linenums="1" hl_lines="5"
from sqlmesh import macro

@macro()
def repeat_string(evaluator, text: str, count: int):
    return exp.Literal.string(text * count)
```

これで、クエリは有効な一重引用符で囲まれた文字列リテラルでレンダリングされます。

```sql linenums="1"
SELECT
  'SQLMesh SQLMesh SQLMesh ' AS "repeated_string"
FROM "some_table" AS "some_table"
```

型付きマクロは **入力** をマクロ関数に強制変換しますが、マクロ コードは **出力** をクエリのセマンティック表現によって予期される型に強制変換する役割を担います。

#### サポートされる型

SQLMesh は、型付きマクロで以下の一般的な Python 型をサポートしています。

- `str` -- 文字列リテラルと基本的な識別子を処理しますが、これより複雑な型は強制変換しません。
- `int`
- `float`
- `bool`
- `datetime.datetime`
- `datetime.date`
- `SQL` -- 渡された引数の SQL 文字列表現が必要な場合
- `list[T]` -- ここで、`T` は sqlglot 式を含むサポートされている任意の型です
- `tuple[T]` -- ここで、`T` は sqlglot 式を含むサポートされている任意の型です
- `T1 | T2 | ...` - ここで、`T1`、`T2` などは、SQLGlot 式を含むサポートされている任意の型です。

SQLGlot 式を型ヒントとしてサポートしているため、入力が目的の SQL AST ノードに確実に強制変換されます。便利な例としては、次のようなものがあります。

- `exp.Table`
- `exp.Column`
- `exp.Literal`
- `exp.Identifier`

これらは明らかな例かもしれませんが、入力を任意の SQLGlot 式型に効果的に強制変換できるため、より複雑なマクロで役立ちます。より複雑な型に強制変換する場合、式間の強制変換には制限があるため、ほとんどの場合、文字列リテラルを渡す必要があります。SQLGlot 式をヒントとするマクロに文字列リテラルを渡すと、文字列は SQLGlot を使用して解析され、正しい型に強制変換されます。正しい型に強制変換できない場合は、元の式がマクロに渡され、ユーザーが必要に応じて対処するための警告が記録されます。

```python linenums="1"
@macro()
def stamped(evaluator, query: exp.Select) -> exp.Subquery:
    return query.select(exp.Literal.string(str(datetime.now())).as_("stamp")).subquery()

# Coercing to a complex node like `exp.Select` works as expected given a string literal input
# SELECT * FROM @stamped('SELECT a, b, c')
```

型変換に失敗した場合、常に警告がログに記録されますが、クラッシュすることはありません。マクロシステムはデフォルトで柔軟であるべきだと考えています。つまり、型変換が失敗した場合でもデフォルトの動作が維持されるということです。そのため、ユーザーは必要なレベルの追加チェックを自由に記述できます。例えば、型変換が失敗した場合にエラーを発生させたい場合は、`assert` ステートメントを使用できます。例:

```python linenums="1"
@macro()
def my_macro(evaluator, table: exp.Table) -> exp.Column:
    assert isinstance(table, exp.Table)
    table.set("catalog", "dev")
    return table

# Works
# SELECT * FROM @my_macro('some.table')
# SELECT * FROM @my_macro(some.table)

# Raises an error thanks to the users inclusion of the assert, otherwise would pass through the string literal and log a warning
# SELECT * FROM @my_macro('SELECT 1 + 1')
```

このように assert を使用すると、型の強制変換に必要な定型文を削減/削除できるというメリットはそのままに、入力の型に関する保証も得られます。これは便利なパターンであり、ユーザー定義なので、必要に応じて使用できます。これにより、マクロ定義を簡潔に保ち、コアとなるビジネスロジックに集中できるようになります。

#### 高度な型付きマクロ

ジェネリクスなどの高度な Python 機能を使用することで、より複雑なマクロを作成できます。例えば、整数のリストを受け取り、その合計を返すマクロは次のようになります。

```python linenums="1"
from typing import List
from sqlmesh import macro

@macro()
def sum_integers(evaluator, numbers: List[int]) -> int:
    return sum(numbers)
```

SQLMesh での使用法:

```sql linenums="1"
SELECT
  @sum_integers([1, 2, 3, 4, 5]) as total
FROM some_table;
```

ジェネリックはネスト可能で、再帰的に解決されるため、非常に堅牢な型ヒントが可能になります。

テストスイートにおける強制変換関数の動作例は、[こちら](https://github.com/TobikoData/sqlmesh/blob/main/tests/core/test_macros.py) をご覧ください。

#### まとめ

SQLMesh の型付きマクロは、マクロの可読性と使いやすさを向上させることで開発エクスペリエンスを向上させるだけでなく、コードの堅牢性と保守性も向上させます。Python の型ヒントシステムを活用することで、開発者は SQL クエリ用の強力で直感的なマクロを作成でき、SQL と Python のギャップをさらに埋めることができます。

## マクロシステムの混在

SQLMesh は、SQLMesh と [Jinja](./jinja_macros.md) の両方のマクロシステムをサポートしています。モデルではど​​ちらか一方のシステムのみを使用することを強くお勧めします。両方を同時に使用すると、エラーが発生したり、直感的でない動作をしたりする可能性があります。
