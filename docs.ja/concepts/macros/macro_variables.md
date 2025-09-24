# マクロ変数

マクロ変数は、マクロの実行時に値が代入されるプレースホルダーです。

マクロ変数は動的なマクロの動作を可能にします。例えば、日付パラメータの値は、マクロの実行日時に基づいて決定されます。

!!! note

    このページでは、SQLMesh の組み込みマクロ変数について説明します。ユーザー定義のカスタムマクロ変数の詳細については、[SQLMesh マクロページ](./sqlmesh_macros.md#user-defined-variables) をご覧ください。

## 例

`WHERE` 句で日付をフィルタリングする SQL クエリを考えてみましょう。

モデルを実行するたびに日付を手動で変更する代わりに、マクロ変数を使用して日付を動的に変更することができます。動的アプローチでは、クエリの実行時刻に基づいて日付が自動的に変更されます。

次のクエリは、列 `my_date` が '2023-01-01' より後である行をフィルタリングします。

```sql linenums="1"
SELECT *
FROM table
WHERE my_date > '2023-01-01'
```

このクエリの日付を動的にするには、定義済みの SQLMesh マクロ変数 `@execution_ds` を使用できます。

```sql linenums="1"
SELECT *
FROM table
WHERE my_date > @execution_ds
```

`@` 記号は、`@execution_ds` がマクロ変数であり、SQL 実行前に置換が必要であることを SQLMesh に伝えます。

マクロ変数 `@execution_ds` は事前定義されているため、実行開始時刻に基づいて SQLMesh によって自動的に値が設定されます。モデルが 2023 年 2 月 1 日に実行された場合、レンダリングされたクエリは次のようになります。

```sql linenums="1"
SELECT *
FROM table
WHERE my_date > '2023-02-01'
```

この例では SQLMesh の定義済み変数の 1 つを使用しましたが、独自のマクロ変数を定義することもできます。

SQLMesh の定義済み変数については以下で説明します。ユーザー定義のマクロ変数については、[SQLMesh マクロ](./sqlmesh_macros.md#user-defined-variables) および [Jinja マクロ](./jinja_macros.md#user-defined-variables) のページで説明します。

## 定義済み変数

SQLMesh には、クエリで使用できる定義済み変数が付属しています。これらは SQLMesh ランタイムによって自動的に設定されます。

定義済み変数のほとんどは時間関連で、接頭辞（start、end など）と接尾辞（date、ds、ts など）の組み合わせを使用します。これらについては次のセクションで説明します。[その他の定義済み変数](#runtime-variables)については、その次のセクションで説明します。

### 時間変数

SQLMesh は、日付と時刻の処理に Python [datetime モジュール](https://docs.python.org/3/library/datetime.html) を使用します。このモジュールは、標準の [Unix エポック](https://en.wikipedia.org/wiki/Unix_time) の開始日である 1970 年 1 月 1 日を使用します。

!!! tip "重要"

    時間コンポーネントを持つ定義済み変数は、常に [UTC タイムゾーン](https://en.wikipedia.org/wiki/Coordinated_Universal_Time) を使用します。

    タイムゾーンと増分モデルの詳細については、[こちら](../models/model_kinds.md#timezones) をご覧ください。

接頭辞:

* start - モデル実行の開始間隔（両端を含む）
* end - モデル実行の終了間隔（両端を含む）
* execution - 実行開始時のタイムスタンプ

接尾辞:

* dt - Python の datetime オブジェクト。ネイティブ SQL の `TIMESTAMP`（または SQL エンジンの同等の型）に変換されます。
* dtntz - Python の datetime オブジェクト。ネイティブ SQL の `TIMESTAMP WITHOUT TIME ZONE`（または SQL エンジンの同等の型）に変換されます。
* date - Python の date オブジェクト。ネイティブ SQL の `DATE` に変換されます。
* ds - '%Y-%m-%d' 形式の日付文字列
* ts - ISO 8601 日付時刻形式の文字列。'%Y-%m-%d %H:%M:%S'
* tstz - タイムゾーン付きの ISO 8601 日付時刻形式の文字列。'%Y-%m-%d' %H:%M:%S%z'
* hour - 時刻を表す整数（0～23）
* epoch - Unixエポックからの秒数を表す整数
* millis - Unixエポックからのミリ秒数を表す整数

すべての定義済み時間マクロ変数：

* dt
    * @start_dt
    * @end_dt
    * @execution_dt

* dtntz
    * @start_dtntz
    * @end_dtntz
    * @execution_dtntz

* date
    * @start_date
    * @end_date
    * @execution_date

* ds
    * @start_ds
    * @end_ds
    * @execution_ds

* ts
    * @start_ts
    * @end_ts
    * @execution_ts

* tstz
    * @start_tstz
    * @end_tstz
    * @execution_tstz

* hour
    * @start_hour
    * @end_hour
    * @execution_hour

* epoch
    * @start_epoch
    * @end_epoch
    * @execution_epoch

* millis
    * @start_millis
    * @end_millis
    * @execution_millis

### ランタイム変数

SQLMesh は、実行時に利用可能な情報に基づいてモデルの動作を変更するための、追加の定義済み変数を提供します。

* @runtime_stage - SQLMesh ランタイムの現在のステージを示す文字列値。通常、モデル内で条件付きで pre/post ステートメントを実行するために使用されます (詳細については、[こちら](../models/sql_models.md#optional-prepost-statements) を参照してください)。以下のいずれかの値を返します。
* 'loading' - プロジェクトが SQLMesh のランタイムコンテキストにロードされています。
* 'creating' - モデルテーブルが初めて作成されています。テーブル作成中にデータが挿入される可能性があります。
* 'evaluating' - モデルクエリロジックが評価され、データが既存のモデルテーブルに挿入されています。
* 'promoting' - モデルがターゲット環境でプロモートされています (仮想レイヤーの更新中にビューが作成されます)。
* 'demoting' - モデルはターゲット環境で降格中です（仮想レイヤーの更新中にビューが削除されました）。
* 'auditing' - 監査が実行されています。
* 'testing' - モデルのクエリロジックが単体テストのコンテキストで評価されています。
* @gateway - 現在の [ゲートウェイ](../../guides/connections.md) の名前を含む文字列値。
* @this_model - モデルのビューが選択する物理テーブル名。通常は [汎用監査](../audits.md#generic-audits) の作成に使用されます。[on_virtual_update ステートメント](../models/sql_models.md#optional-on-virtual-update-statements) 内で使用される場合は、代わりに修飾ビュー名が含まれます。
* @model_kind_name - 現在のモデルの種類の名前を含む文字列値。 [モデルのデフォルトの物理プロパティ](../../reference/model_configuration.md#model-defaults)を制御する必要があるシナリオで使用することを目的としています。

!!! note "文字列に変数を埋め込む"

    マクロ変数参照では、中括弧構文 `@{variable}` が使用されることがあります。これは、通常の `@variable` 構文とは異なる目的を持ちます。

    中括弧構文は、SQLMesh に対し、レンダリングされた文字列をマクロ変数の値を単純に置き換えるのではなく、識別子として扱うように指示します。

    例えば、`variable` が `@DEF(`variable`, foo.bar)` と定義されている場合、`@variable` は `foo.bar` を生成し、`@{variable}` は `"foo.bar"` を生成します。これは、SQLMesh が `foo.bar` を識別子に変換する際に、二重引用符を使用して識別子名に `.` 文字を正しく含めるためです。

    実際には、`@{variable}` は識別子内の値の挿入に最もよく使用されます（例: `@{variable}_suffix`）。一方、`@variable` は文字列リテラルの単純な置換に使用されます。

    詳しくは [上記](#文字列への変数の埋め込み) をご覧ください。

#### すべての前とすべての後の変数

以下の変数は、[`before_all` および `after_all` ステートメント](../../guides/configuration.md#before_all-and-after_all-statements)、およびそれらの中で呼び出されるマクロでも使用できます。

* @this_env - 現在の [環境](../environments.md) の名前を含む文字列値。
* @schemas - 現在の環境の [仮想レイヤー](../../concepts/glossary.md#virtual-layer) のスキーマ名のリスト。
* @views - 現在の環境の [仮想レイヤー](../../concepts/glossary.md#virtual-layer) のビュー名のリスト。