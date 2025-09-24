# 状態

SQLMesh は、プロジェクトに関する情報を状態データベースに保存します。このデータベースは通常、メインのウェアハウスとは別のものです。

SQLMesh 状態データベースには、以下の情報が含まれます。

- プロジェクト内のすべての [モデルバージョン](./models/overview.md) に関する情報 (クエリ、読み込み間隔、依存関係)
- プロジェクト内のすべての [仮想データ環境](./environments.md) のリスト
- 各 [仮想データ環境](./environments.md) に [昇格](./plans.md#plan-application) されているモデルバージョン
- プロジェクト内に存在する [自動再ステートメント](./models/overview.md#auto_restatement_cron) に関する情報
- 現在の SQLMesh / SQLGlot バージョンなど、プロジェクトに関するその他のメタデータ

状態データベースは、SQLMesh が過去の実行内容を「記憶」する手段です。これにより、毎回すべてを再構築するのではなく、変更を適用するための最小限の操作セットを計算できます。これは、SQLMesh が [増分モデル](./models/model_kinds.md#incremental_by_time_range) にすでにバックフィルされている履歴データを追跡する方法でもあるため、これを処理するためにモデル クエリに分岐ロジックを追加する必要はありません。

!!! info "状態データベースのパフォーマンス"

    状態データベースへのワークロードは、正常に動作するためにトランザクションのサポートを必要とする OLTP ワークロードです。

    最適なエクスペリエンスを得るには、[Tobiko Cloud](../cloud/cloud_index.md) または [PostgreSQL](../integrations/engines/postgres.md) などの OLTP ワークロード向けに設計されたデータベースの使用をお勧めします。

    ウェアハウス OLAP データベースを使用して状態を保存することは、概念実証プロジェクトではサポートされていますが、本番環境には適しておらず、**パフォーマンスと一貫性の低下**につながります。

    SQLMesh 状態データベースに適したエンジンの詳細については、[構成ガイド](../guides/configuration.md#state-connection) をご覧ください。

## 状態のエクスポート/インポート

SQLMesh は、状態データベースを `.json` ファイルへエクスポートする機能をサポートしています。エクスポートしたファイルは、テキストファイルを読み込める任意のツールで確認できます。また、このファイルを他の SQLMesh プロジェクトに渡したり、別の場所で実行されている SQLMesh プロジェクトにインポートしたりすることも可能です。

### 状態のエクスポート

SQLMesh は、状態データベースを以下のようにファイルにエクスポートできます。

```bash
$ sqlmesh state export -o state.json
Exporting state to 'state.json' from the following connection:

Gateway: dev
State Connection:
├── Type: postgres
├── Catalog: sushi_dev
└── Dialect: postgres

Continue? [y/n]: y

    Exporting versions ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100.0% • 3/3   • 0:00:00
   Exporting snapshots ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100.0% • 17/17 • 0:00:00
Exporting environments ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100.0% • 1/1   • 0:00:00

State exported successfully to 'state.json'
```

これにより、SQLMesh の状態を含むファイル `state.json` が現在のディレクトリに生成されます。

状態ファイルは、次のような単純な `json` ファイルです。

```json
{
    /* State export metadata */
    "metadata": {
        "timestamp": "2025-03-16 23:09:00+00:00", /* UTC timestamp of when the file was produced */
        "file_version": 1, /* state export file format version */
        "importable": true /* whether or not this file can be imported with `sqlmesh state import` */
    },
    /* Library versions used to produce this state export file */
    "versions": {
        "schema_version": 76 /* sqlmesh state database schema version */,
        "sqlglot_version": "26.10.1" /* version of SQLGlot used to produce the state file */,
        "sqlmesh_version": "0.165.1" /* version of SQLMesh used to produce the state file */,
    },
    /* array of objects containing every Snapshot (physical table) tracked by the SQLMesh project */
    "snapshots": [
        { "name": "..." }
    ],
    /* object for every Virtual Data Environment in the project. key = environment name, value = environment details */
    "environments": {
        "prod": {
            /* information about the environment itself */
            "environment": {
                "..."
            },
            /* information about any before_all / after_all statements for this environment */
            "statements": [
                "..."
            ]
        }
    }
}
```

#### 特定の環境

特定の環境をエクスポートするには、次のようにします。

```sh
$ sqlmesh state export --environment my_dev -o my_dev_state.json
```

`prod` との差分だけでなく、環境を構成するすべてのスナップショットがエクスポートされることに注意してください。これは、どのスナップショットが既に状態に存在するかを前提とすることなく、環境を他の場所に完全にインポートできるようにするためです。

#### ローカル状態

ローカル状態は次のようにエクスポートできます。

```bash
$ sqlmesh state export --local -o local_state.json
```

これは基本的に、ローカルコンテキストの状態のみをエクスポートするものであり、これには仮想データ環境に適用されていないローカルの変更が含まれます。

したがって、ローカル状態のエクスポートには `snapshots` のみが入力されます。仮想データ環境はウェアハウス/リモート状態にのみ存在するため、`environments` は空になります。さらに、ファイルは **インポート不可** としてマークされているため、後続の `sqlmesh state import` コマンドで使用することはできません。

### 状態のインポート

!!! warning "まず状態データベースをバックアップしてください。"

    状態インポート中に問題が発生した場合に備えて、状態データベースの独立したバックアップを作成してください。

    SQLMesh は状態インポートをトランザクションでラップしようとしますが、一部のデータベースエンジンは DDL に対するトランザクションをサポートしていないため、
    インポートエラーが発生すると状態データベースが不整合な状態になる可能性があります。

SQLMesh は、次のように状態ファイルを状態データベースにインポートできます。

```bash
$ sqlmesh state import -i state.json --replace
Loading state from 'state.json' into the following connection:

Gateway: dev
State Connection:
├── Type: postgres
├── Catalog: sushi_dev
└── Dialect: postgres

[WARNING] This destructive operation will delete all existing state against the 'dev' gateway
and replace it with what\'s in the 'state.json' file.

Are you sure? [y/n]: y

State File Information:
├── Creation Timestamp: 2025-03-31 02:15:00+00:00
├── File Version: 1
├── SQLMesh version: 0.170.1.dev0
├── SQLMesh migration version: 76
└── SQLGlot version: 26.12.0

    Importing versions ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100.0% • 3/3   • 0:00:00
   Importing snapshots ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100.0% • 17/17 • 0:00:00
Importing environments ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100.0% • 1/1   • 0:00:00

State imported successfully from 'state.json'
```

状態データベース構造が存在し、最新の状態である必要があることに注意してください。バージョン不一致エラーが発生した場合は、`sqlmesh state import` を実行する前に `sqlmesh migrate` を実行してください。

単一環境など、状態を部分的にエクスポートしている場合は、`--replace` パラメータを省略することでマージできます。

```bash
$ sqlmesh state import -i state.json
...

[WARNING] This operation will merge the contents of the state file to the state located at the 'dev' gateway.
Matching snapshots or environments will be replaced.
Non-matching snapshots or environments will be ignored.

Are you sure? [y/n]: y

...
State imported successfully from 'state.json'
```


### 特定のゲートウェイ

プロジェクトに複数のゲートウェイがあり、ゲートウェイごとに異なる状態接続が設定されている場合は、次のように特定のゲートウェイの [state_connection](../guides/configuration.md#state-connection) をターゲットにすることができます。

```bash
# state export
$ sqlmesh --gateway <gateway> state export -o state.json

# state import
$ sqlmesh --gateway <gateway> state import -i state.json
```

## バージョン互換性

状態をインポートする際、状態ファイルは、インポートに使用したSQLMeshと同じメジャーバージョンとマイナーバージョンで作成されている必要があります。

互換性のないバージョンで状態をインポートしようとすると、次のエラーが発生します。

```bash
$ sqlmesh state import -i state.json
...SNIP...

State import failed!
Error: SQLMesh version mismatch. You are running '0.165.1' but the state file was created with '0.164.1'.
Please upgrade/downgrade your SQLMesh version to match the state file before performing the import.
```

### 状態ファイルのアップグレード

古いバージョンの SQLMesh で生成された状態ファイルを、新しいバージョンの SQLMesh と互換性を持たせるために、以下の手順でアップグレードできます。

- 古いバージョンの SQLMesh を使用して、状態ファイルをローカルデータベースにロードする。
- 新しいバージョンの SQLMesh をインストールする。
- `sqlmesh migrate` を実行して、ローカルデータベース内の状態ファイルをアップグレードする。
- `sqlmesh state export` を実行して、状態ファイルを再度エクスポートする。これで、新しいバージョンの SQLMesh と互換性を持つようになります。

以下は、SQLMesh `0.164.1` で作成された状態ファイルを SQLMesh `0.165.1` と互換性を持たせるためにアップグレードする方法の例です。

まず、仮想環境を作成してアクティブ化し、SQLMesh のバージョンをメイン環境から分離します。

```bash
$ python -m venv migration-env

$ . ./migration-env/bin/activate

(migration-env)$
```

状態ファイルと互換性のあるバージョンのSQLMeshをインストールしてください。正しいバージョンはエラーメッセージに表示されます。例えば、`the state file was created with '0.164.1'` というメッセージは、SQLMesh `0.164.1` をインストールする必要があることを意味します。

```bash
(migration-env)$ pip install "sqlmesh==0.164.1"
```

次のように `config.yaml` にゲートウェイを追加します。

```yaml
gateways:
  migration:
    connection:
      type: duckdb
      database: ./state-migration.duckdb
```

ここでの目標は、SQLMeshがローカルデータベースを使用して状態のエクスポート/インポートコマンドを実行できるようにするための、最低限の設定を定義することです。SQLMeshは、状態を正しく移行するために、プロジェクトから「model_defaults」などの設定を継承する必要があるため、独立したディレクトリは使用していません。

!!! warning

    今後は、すべての SQLMesh コマンドに `--gateway migration` を指定してください。そうしないと、メインゲートウェイの状態が誤って上書きされてしまう可能性があります。

これで、作成時と同じバージョンの SQLMesh を使用して、状態エクスポートをインポートできるようになりました。

```bash
(migration-env)$ sqlmesh --gateway migration migrate

(migration-env)$ sqlmesh --gateway migration state import -i state.json
...
State imported successfully from 'state.json'
```

状態がインポートされたので、SQLMesh をアップグレードして新しいバージョンから状態をエクスポートできます。
新しいバージョンは元のエラーメッセージに表示されています（例：`You are running '0.165.1'）。

SQLMesh をアップグレードするには、新しいバージョンをインストールするだけです。

```bash
(migration-env)$ pip install --upgrade "sqlmesh==0.165.1"
```

状態を新しいバージョンに移行します。

```bash
(migration-env)$ sqlmesh --gateway migration migrate
```

最後に、新しい SQLMesh バージョンと互換性のある新しい状態ファイルを作成します。

```bash
 (migration-env)$ sqlmesh --gateway migration state export -o state-migrated.json
```

`state-migrated.json` ファイルは、新しいバージョンの SQLMesh と互換性があります。
このファイルを元の場所に転送し、以下の場所にインポートできます。

```bash
$ sqlmesh state import -i state-migrated.json
...
State imported successfully from 'state-migrated.json'
```