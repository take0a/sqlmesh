# 比較

**このドキュメントは現在作成中です。**

データエコシステムには多くのツールとフレームワークが存在します。このページでは、それらすべてを分かりやすく解説します。

SQLMesh に馴染みのない方は、まず [SQLMesh のメリット](../#why-sqlmesh) と [SQLMesh とは](../#what-is-sqlmesh) をお読みいただくと、比較の理解が深まります。

## dbt
[dbt](https://www.getdbt.com/) はデータ変換ツールです。この分野のパイオニアであり、変換フレームワークの価値を実証してきました。dbt は優れたツールですが、データや組織の規模に合わせて拡張するのが難しいという欠点があります。

dbt は、シンプルなデータ変換に重点を置いた製品を開発しました。デフォルトでは、テンプレート化された SQL を正しい順序で実行することで、データウェアハウスを完全にリフレッシュします。

dbt は、スケーラブルで堅牢なデータ製品を運用するには、データ変換だけでは不十分であることに長年にわたり気付いてきました。その結果、状態管理（遅延）や増分ロードといった高度な機能がパッチで追加され、これらのニーズに対応しようと試みる一方で、複雑さが増すにつれて正確性の負担がユーザーに押し付けられています。これらの「高度な」機能は、DataOpsフレームワークの基本的な構成要素の一部を構成しています。

言い換えれば、これらの機能をdbtに実装する際の課題は、主に**ユーザー**にかかっています。Jinjaマクロブロックの増加、手動設定の増加、カスタムツールの増加、そしてエラーの発生機会の増加です。私たちは、より簡単で信頼性の高い方法を必要としていました。そこで、SQLMeshを堅牢なDataOpsフレームワークとしてゼロから設計しました。

SQLMeshはdbt形式との互換性を目指しています。既存のdbtプロジェクトを若干の変更を加えてインポートする機能は開発中です。

### Feature comparisons
| Feature                           | dbt | SQLMesh
| -------                           | --- | -------
| Modeling
| `SQL models`                      | ✅ | [✅](../concepts/models/overview)
| `Python models`                   | ✅ | [✅✅](../concepts/models/python_models)
| `Jinja support`                   | ✅ | ✅
| `Jinja macros`                    | ✅ | [✅](../concepts/macros/jinja_macros)
| `Python macros`                   | ❌ | [✅](../concepts/macros/sqlmesh_macros)
| Validation
| `SQL semantic validation`         | ❌ | [✅](../concepts/glossary/#semantic-understanding)
| `Unit tests`                      | ❌ | [✅](../concepts/tests)
| `Table diff`                      | ❌ | ✅
| `Data audits`                     | ✅ | [✅](../concepts/audits)
| `Schema contracts`                | ✅ | [✅](../concepts/plans)
| `Data contracts`                  | ❌ | [✅](../concepts/plans)
| Deployment
| `Virtual Data Environments`       | ❌ | [✅](../concepts/environments)
| `Open-source CI/CD bot`           | ❌ | [✅](../integrations/github)
| `Data consistency enforcement`    | ❌ | ✅
| Interfaces
| `CLI`                             | ✅ | [✅](../reference/cli)
| `Paid UI`                         | ✅ | ❌
| `Open-source UI`                  | ❌ | ✅
| `Native Notebook Support`         | ❌ | [✅](../reference/notebook)
| Visualization
| `Documentation generation`        | ✅ | ✅
| `Column-level lineage`            | ❌ | ✅
| Miscellaneous
| `Package manager`                 | ✅ | ❌
| `Multi-repository support`        | ❌ | [✅](../guides/multi_repo)
| `SQL transpilation`               | ❌ | [✅](../concepts/models/sql_models/#transpilation)

### 環境
dbt の開発環境とステージング環境の構築にはコストがかかり、本番環境で使用される環境を完全に反映しているとは言えません。

dbt で新しい環境を作成するための標準的な方法は、ウェアハウス全体を新しい環境で再実行することです。これは小規模であればうまくいくかもしれませんが、それでも時間とコストの無駄になります。その理由は次のとおりです。

データ変換システムを実行する最初の段階は、モデルコードの作成または変更、モデルの実行、出力の評価という 3 つのステップを繰り返すことです。担当者は、1 日の業務でこれらのステップを何度も繰り返すことがあります。

これらのステップは、モデルを実行するための計算コストと、モデルの実行を待つスタッフの時間など、組織にコストを発生させます。これらのステップが頻繁に繰り返されるため、非効率性は急速に増大します。
dbt のデフォルトの完全更新アプローチは、このループの中で最もコストのかかるバージョン、つまりすべてのモデルを毎回再計算するバージョンにつながります。

SQLMesh は別のアプローチを採用しています。コードの変更内容とモデル間の依存関係構造を検証し、影響を受けるモデルを特定して、該当するモデルのみを実行します。これにより、ループのコストが最も低くなり、毎回必要なものだけが計算されます。

これにより、SQLMesh は効率的に分離された [仮想環境](./concepts/plans.md#plan-application) を提供できます。dbt の環境はコンピューティングとストレージにコストがかかりますが、SQLMesh での開発環境の作成は無料です。コマンド 1 つで、他の環境の完全なレプリカに簡単にアクセスできます。

さらに、SQLMesh はステージング環境から本番環境への昇格が予測可能かつ一貫性があることを保証します。dbt には昇格の概念がないため、何かをデプロイするときにすべてのクエリが再実行されます。SQLMesh では、昇格は単純なポインタのスワップであるため、無駄なコンピューティングは発生しません。

### 増分モデル
dbt では状態が追跡されないため、増分モデルの実装は困難でエラーが発生しやすくなります。

#### 複雑さ
dbt では増分間隔がすでに実行されたかどうかの状態がないため、ユーザーは欠落している日付境界を自分で見つけるためのサブクエリを記述して管理する必要があります。

```sql
-- dbt incremental
SELECT *
FROM {{ ref(raw.events) }} e
JOIN {{ ref(raw.event_dims) }} d
  ON e.id = d.id
-- must specify the is_incremental flag because this predicate will fail if the model has never run before
{% if is_incremental() %}
    -- this filter dynamically scans the current model to find the date boundary
    AND d.ds >= (SELECT MAX(ds) FROM {{ this }})
{% endif %}
{% if is_incremental() %}
  WHERE e.ds >= (SELECT MAX(ds) FROM {{ this }})
{% endif %}
```

日付の境界を見つけるためにマクロを手動で指定するのは、繰り返し作業になり、エラーが発生しやすくなります。

上記の例は、増分モデルが以前に実行されたことがあるかどうかによって、dbt でどのように動作が異なるかを示しています。モデルが複雑になるにつれて、「初回の完全更新」と「その後の増分更新」という2つの実行時間があることによる認知的負担は増大します。

SQLMesh は、存在する日付範囲を追跡し、次のように簡素化された効率的なクエリを生成します。

```sql
-- SQLMesh incremental
SELECT *
FROM raw.events e
JOIN raw.event_dims d
  -- date ranges are handled automatically by SQLMesh
  ON e.id = d.id AND d.ds BETWEEN @start_ds AND @end_ds
WHERE d.ds BETWEEN @start_ds AND @end_ds
```

#### データ漏洩

dbt は、増分テーブルに挿入されたデータがそこに存在すべきかどうかをチェックしません。そのため、遅れて到着したデータが過去のパーティションを上書きするなど、問題や整合性の問題が発生する可能性があります。これらの問題は「データ漏洩」と呼ばれます。

SQLMesh は、すべてのクエリを内部的に時間フィルターを含むサブクエリでラップすることで、特定のバッチに挿入されたデータが毎回期待どおりに再現可能であることを保証しています。

さらに、dbt は「挿入/上書き」増分ロードパターンをネイティブでサポートするシステムでのみサポートします。SQLMesh は「挿入/上書き」をあらゆるシステムで実行できます。これは、これが増分ロードに対する最も堅牢なアプローチであるためです。一方、「追加」パイプラインでは、特定の日付に対してパイプラインが複数回実行される可能性のあるさまざまなシナリオでデータの不正確さが生じるリスクがあります。

次の例は、データ漏洩を防ぐため、SQLMesh がすべてのクエリに適用する時間フィルターサブクエリを示しています。

```sql
-- original query
SELECT *
FROM raw.events
JOIN raw.event_dims d
  ON e.id = d.id AND d.ds BETWEEN @start_ds AND @end_ds
WHERE d.ds BETWEEN @start_ds AND @end_ds

-- with automated data leakage guard
SELECT *
FROM (
  SELECT *
  FROM raw.events
  JOIN raw.event_dims d
    ON e.id = d.id AND d.ds BETWEEN @start_ds AND @end_ds
  WHERE d.ds BETWEEN @start_ds AND @end_ds
)
WHERE ds BETWEEN @start_ds AND @end_ds
```

#### データギャップ
dbt で増分モデルを実装する際に主に用いられるパターンは、MAX(date) を用いて最新のデータを確認することです。このパターンでは、過去の欠落データ、つまり「データギャップ」は検出されません。

SQLMesh は、モデルが実行された各日付間隔を保存するため、欠落している日付を正確に把握できます。

```
Expected dates: 2022-01-01, 2022-01-02, 2022-01-03
Missing past data: ?, 2022-01-02, 2022-01-03
Data gap: 2022-01-01, ?, 2022-01-03
```

SQLMesh は、次回実行時にこれらのデータギャップを自動的に埋めます。

#### パフォーマンス
MAX(date) を検索するサブクエリは、プライマリクエリのパフォーマンスに影響を与える可能性があります。SQLMesh は、こ​​れらの余分なサブクエリを回避できます。

さらに、dbt は増分モデルが初回実行時に完全に更新できることを前提としています。一部の大規模なデータセットでは、これはコストがかかりすぎるか、実現不可能です。

SQLMesh は、バックフィルをより管理しやすいチャンクに [バッチ処理](../concepts/models/overview#batch_size) できます。

### SQL の理解
dbt は [Jinja](https://jinja.palletsprojects.com/en/3.1.x/) に大きく依存しています。Jinja は SQL を理解しておらず、すべてのクエリをコンテキストのない生の文字列として扱います。そのため、末尾のカンマなどの単純な構文エラーはデバッグが難しく、検出するには完全な実行が必要です。

SQLMesh は Jinja をサポートしていますが、Jinja に依存するのではなく、[SQLGlot](https://github.com/tobymao/sqlglot) を介して SQL を解析/理解します。単純なエラーはコンパイル時に検出できるため、列の参照が間違っている、またはカンマを忘れているなどの確認に数分、あるいはそれ以上待つ必要がなくなります。

さらに、SQL に関する高度な知識があれば、SQLMesh はトランスパイル、列レベルのリネージ、自動変更分類などの機能によってさらに強化されます。

### テスト
NULL 値や重複行の検出などのデータ品質チェックは、上流のデータの問題や大規模な問題を検出する上で非常に有用です。ただし、これらはエッジケースやビジネスロジックのテストには適しておらず、堅牢なデータパイプラインを構築するには不十分です。

[ユニットテストと統合テスト](./concepts/tests.md) は、ビジネスロジックを検証するためのツールです。 SQLMeshでは、変更によって想定外の不具合が発生しないように、すべてのモデルにユニットテストを追加することを推奨しています。ユニットテストは、継続的インテグレーション（CI）フレームワークで実行できるよう、高速かつ自己完結的に設計されています。

### Python モデル
dbt の Python モデルは、完全な Python ランタイムを備えたデータ プラットフォームのアダプター上でのみリモートで実行されるため、モデルを利用できるユーザー数が制限され、デバッグが困難になります。

SQLMesh の [Python モデル](../concepts/models/python_models) はローカルで実行され、あらゆるデータ ウェアハウスで使用できます。ブレークポイントを追加してモデルをデバッグできます。

### データ コントラクト
dbt は、手動で構成できるスキーマ コントラクトを提供します。このコントラクトは、実行時にモデルのスキーマを yaml スキーマと照合します。モデルをバージョン管理することで、下流のチームが最新バージョンに移行する時間を確保できますが、移行期間中は信頼できる情報源が断片化されるリスクがあります。

SQLMesh は、[`sqlmesh plan`](../concepts/plans) を介して自動スキーマ コントラクトとデータ コントラクトを提供します。このプランは、モデルのスキーマとクエリ ロジックに下流のユーザーに影響を与える変更がないか確認します。`sqlmesh plan` は、互換性に影響する変更があるモデルと、影響を受ける下流のモデルを表示します。

移行期間を確保するために、互換性を破る変更は個別のモデルとして展開できますが、SQLMesh の [仮想プレビュー](../concepts/glossary#virtual-preview) を使用すると、変更が本番環境にデプロイされる前にチームが移行について共同作業を行うことができ、ビジネス全体で信頼できる単一の情報源を維持できます。