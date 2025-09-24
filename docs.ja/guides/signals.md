# シグナルガイド

SQLMesh の [組み込みスケジューラ](./scheduling.md#built-in-scheduler) は、`sqlmesh run` コマンド実行時にどのモデルを評価するかを制御します。

モデルを評価するかどうかは、モデルの [`cron`](../concepts/models/overview.md#cron) が前回の評価から経過しているかどうかに基づいて決定されます。例えば、モデルの `cron` が `@daily` の場合、スケジューラはモデルが今日より前に最終評価された場合にのみ評価を行います。

残念ながら、世の中は常にデータシステムのスケジュールに追従するとは限りません。データがシステムに到着するのは、下流の毎日のモデルが既に実行された後である可能性があります。スケジューラは正しく処理しましたが、本日の遅れたデータは明日のスケジュールされた実行まで処理されません。

シグナルを使用することで、この問題を回避できます。

## シグナルとは？

スケジューラは、モデルを評価する必要があるかどうかを判断するために、最後の評価以降に `cron` が経過したかどうかと、上流の依存関係の実行が完了したかどうかという 2 つの基準を使用します。

シグナルを使用すると、スケジューラがモデルを評価する前に満たすべき追加の基準を指定できます。

シグナル定義とは、基準が満たされているかどうかを確認する関数です。確認関数について説明する前に、スケジューラの動作に関する背景情報をいくつか説明します。

スケジューラは実際には「モデル」を評価するのではなく、特定の時間間隔にわたってモデルを評価します。これは、評価中に時間間隔内の行のみが取り込まれる増分モデルの場合に最も明確です。ただし、`FULL` や `VIEW` などの非時間的なモデルの評価も、時間間隔、つまりモデルの `cron` 頻度に基づいています。

スケジューラの決定は、これらの時間間隔に基づいています。各モデルについて、スケジューラは候補となる区間のセットを検査し、評価の準備ができているものを特定します。

次に、それらをバッチに分割します（バッチのサイズはモデルの [batch_size](../concepts/models/overview.md#batch_size) パラメータで設定されます）。増分モデルの場合、各バッチごとにモデルを1回評価します。非増分モデルの場合、バッチに区間が含まれている場合、モデルを1回評価します。

シグナルチェック関数は、時間間隔のバッチを検査します。この関数は常に時間間隔のバッチ（DateTimeRanges）とともに呼び出されます。オプションでキーワード引数とともに呼び出すこともできます。すべての区間が評価の準備ができている場合は `True` を、準備ができている区間がない場合は `False` を、一部の区間だけが評価の準備ができている場合は時間間隔そのものを返します。チェック関数は `@signal` デコレータで定義されます。

!!! note "1つのモデル、複数の信号"

    モデルには複数のシグナルを指定できます。SQLMesh は、**すべての**シグナルチェック関数によって準備完了と判断された場合、候補区間を評価準備完了として分類します。

## シグナルの定義

シグナルを定義するには、プロジェクトフォルダに `signals` ディレクトリを作成します。そのディレクトリに `__init__.py` というファイルを作成し、そこにシグナルを定義します（Python ファイル名は任意です）。

シグナルとは、バッチ（`DateTimeRanges: t.List[t.Tuple[datetime, datetime]]`）を受け取り、バッチまたはブール値を返す関数です。`@signal` デコレータを使用する必要があります。

ここでは、さまざまな複雑さのシグナルの例を示します。

### 簡単な例

この例では、`RandomSignal` メソッドを定義します。

このメソッドは、乱数がモデル定義で指定された閾値より大きい場合、`True` （すべての区間が評価の準備ができていることを示す）を返します。

```python linenums="1"
import random
import typing as t
from sqlmesh import signal, DatetimeRanges


@signal()
def random_signal(batch: DatetimeRanges, threshold: float) -> t.Union[bool, DatetimeRanges]:
    return random.random() > threshold
```

`random_signal()` は、必須のユーザー定義の `threshold` 引数を取ることに注意してください。

`random_signal()` メソッドは、しきい値メタデータを抽出し、乱数と比較します。型は [SQLMesh マクロと同じルール](../concepts/macros/sqlmesh_macros.md#typed-macros) に基づいて推論されます。

これでシグナルが準備できたので、モデル DDL の `signals` キーにメタデータを渡すことで、モデルがこのシグナルを使用するように指定する必要があります。

`signals` キーは、角括弧 `[]` で区切られた配列を受け入れます。リスト内の各関数には、1 回のシグナル評価に必要なメタデータを含める必要があります。

次の例では、`random_signal()` がしきい値 0.5 で 1 回評価するように指定しています。

```sql linenums="1" hl_lines="4-6"
MODEL (
  name example.signal_model,
  kind FULL,
  signals (
    random_signal(threshold := 0.5), # specify threshold value
  )
);

SELECT 1
```

このプロジェクトが次に `sqlmesh run` されるとき、私たちのシグナルは比喩的にコインを投げて、モデルを評価する必要があるかどうかを決定します。

### 高度な例

この例では、シグナルのより高度な使用方法を示します。シグナルは、バッチ内のすべての区間に対して単一の `True` / `False` 値を返すのではなく、バッチから区間のサブセットを返します。

```python
import typing as t

from sqlmesh import signal, DatetimeRanges
from sqlmesh.utils.date import to_datetime


# signal that returns only intervals that are <= 1 week ago
@signal()
def one_week_ago(batch: DatetimeRanges) -> t.Union[bool, DatetimeRanges]:
    dt = to_datetime("1 week ago")

    return [
        (start, end)
        for start, end in batch
        if start <= dt
    ]
```

`one_week_ago()` 関数は、一連の間隔が評価の準備ができているかどうかについて単一の `True`/`False` 値を返すのではなく、バッチから特定の間隔を返します。

この関数は datetime 引数を生成し、バッチ内の各間隔の開始時点と比較します。間隔の開始時点がその引数より前であれば、その間隔は評価の準備が整っており、返されるリストに含まれます。
これらのシグナルは、次のようにモデルに追加できます。

```sql linenums="1" hl_lines="7-10"
MODEL (
  name example.signal_model,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column ds,
  ),
  start '2 week ago',
  signals (
    one_week_ago(),
  )
);


SELECT @start_ds AS ds
```

### 実行コンテキスト/エンジンアダプタへのアクセス

シグナル内の実行コンテキストにアクセスし、エンジンアダプタ（ウェアハウス接続）にアクセスすることができます。

```python
import typing as t

from sqlmesh import signal, DatetimeRanges, ExecutionContext


# add the context argument to your function
@signal()
def one_week_ago(batch: DatetimeRanges, context: ExecutionContext) -> t.Union[bool, DatetimeRanges]:
    return len(context.engine_adapter.fetchdf("SELECT 1")) > 1
```

### シグナルのテスト

シグナルは `run` または `check_intervals` でのみ評価されます。

[check_intervals](../reference/cli.md#check_intervals) コマンドを使用してシグナルをテストするには、以下の手順に従います。

1. `sqlmesh plan my_dev` を使用して、変更を環境にデプロイします。
2. `sqlmesh check_intervals my_dev` を実行します。

    * モデルのサブセットをチェックするには、--select-model フラグを使用します。
    * シグナルをオフにして、欠落している間隔のみをチェックするには、--no-signals フラグを使用します。

3. 反復処理を実行するには、シグナルに変更を加え、手順 1 で再デプロイします。

!!! note
    `check_intervals` は環境内のリモートモデルに対してのみ機能します。ローカル信号の変更は実行されません。
