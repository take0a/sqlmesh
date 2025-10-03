# dlt

SQLMesh は、[dlt](https://github.com/dlt-hub/dlt) を通じて取り込まれたデータを使用して、簡単にプロジェクトを生成できます。これには、ベースラインプロジェクトのスキャフォールディングの作成、パイプラインのテーブルからのデータを処理するための増分モデルの生成（スキーマの検査とパイプラインの資格情報を使用したゲートウェイ接続の構成による）が含まれます。

## はじめに
### DLT パイプラインからの読み取り

DLT パイプラインから SQLMesh にデータを読み込むには、DLT パイプラインがローカルで実行または復元されていることを確認してください。次に、*DLT プロジェクトのルートディレクトリ内で* sqlmesh の `init` コマンドを実行します。`dlt` テンプレートオプションを使用し、`dlt-pipeline` オプションでパイプライン名を指定します。

```bash
$ sqlmesh init -t dlt --dlt-pipeline <pipeline-name> dialect
```

これにより、すべての SQLMesh プロジェクトで使用される設定ファイルとディレクトリが作成されます。

- config.yaml
    - プロジェクト設定ファイル。[configuration](../reference/configuration.md) を参照してください。
- ./models
    - SQL および Python モデル。[models](../concepts/models/overview.md) を参照してください。
- ./seeds
    - シードファイル。[seeds](../concepts/models/seed_models.md) を参照してください。
- ./audits
    - 共有監査ファイル。[auditing](../concepts/audits.md) を参照してください。
- ./tests
    - ユニットテストファイル。[testing](../concepts/tests.md) を参照してください。
- ./macros
    - マクロファイル。[macros](../concepts/macros/overview.md) を参照してください。

SQLMesh は、パイプラインからデータを段階的に取り込むためのモデルも自動生成します。増分読み込みは、テーブル全体の再計算に多くのリソースを消費する大規模なデータセットに最適です。この場合、[`INCREMENTAL_BY_TIME_RANGE` モデル種類](../concepts/models/model_kinds.md#incremental_by_time_range) を使用します。ただし、これらのモデル定義は、特定のプロジェクトのニーズに合わせてカスタマイズできます。

#### パイプラインディレクトリへのパスを指定します。

DLTパイプラインのデフォルトの場所は `~/.dlt/pipelines/<pipeline_name>` です。パイプラインが[別のディレクトリ](https://dlthub.com/docs/general-usage/pipeline#separate-working-environments-with-pipelines_dir)にある場合は、`--dlt-path` 引数を使用してパスを明示的に指定してください。

```bash
$ sqlmesh init -t dlt --dlt-pipeline <pipeline-name> --dlt-path <pipelines-directory> dialect
```

### オンデマンドでのモデル生成

SQLMesh プロジェクト内のモデルをオンデマンドで更新するには、`dlt_refresh` コマンドを使用します。このコマンドでは、増分モデルを生成するテーブルを個別に指定するか、すべてのモデルを一括更新することができます。

- **不足しているすべてのテーブルを生成する**:

```bash
$ sqlmesh dlt_refresh <pipeline-name>
```

- **不足しているテーブルをすべて生成し、既存のテーブルを上書きします** (`--force` または `-f` と共に使用)。

```bash
$ sqlmesh dlt_refresh <pipeline-name> --force
```

- **特定の dlt テーブルを生成します** (`--table` または `-t` を使用):

```bash
$ sqlmesh dlt_refresh <pipeline-name> --table <dlt-table>
```

- **パイプライン ディレクトリへの明示的なパスを指定します** (`--dlt-path` を使用):

```bash
$ sqlmesh dlt_refresh <pipeline-name> --dlt-path <pipelines-directory>
```

#### 構成

SQLMesh は、DLT プロジェクトからデータウェアハウス接続の認証情報を取得し、`config.yaml` ファイルを構成します。この構成は必要に応じて変更またはカスタマイズできます。詳細については、[構成ガイド](../guides/configuration.md) を参照してください。

### 例

SQLMesh プロジェクトの dlt の生成は非常に簡単です。この例では、[sushi-dlt プロジェクト](https://github.com/TobikoData/sqlmesh/tree/main/examples/sushi_dlt) のサンプル `sushi_pipeline.py` を使用します。

まず、プロジェクトディレクトリ内でパイプラインを実行します。

```bash
$ python sushi_pipeline.py
Pipeline sushi load step completed in 2.09 seconds
Load package 1728074157.660565 is LOADED and contains no failed jobs
```

パイプラインの実行後、次のコマンドを実行して SQLMesh プロジェクトを生成します。

```bash
$ sqlmesh init -t dlt --dlt-pipeline sushi duckdb
```

これでSQLMeshプロジェクトのセットアップは完了です。SQLMeshの`plan`コマンドを実行して、DLTパイプラインデータを取り込み、SQLMeshテーブルにデータを入力します。

```bash
$ sqlmesh plan
`prod` environment will be initialized

Models:
└── Added:
    ├── sushi_dataset_sqlmesh.incremental__dlt_loads
    ├── sushi_dataset_sqlmesh.incremental_sushi_types
    └── sushi_dataset_sqlmesh.incremental_waiters
Models needing backfill (missing dates):
├── sushi_dataset_sqlmesh.incremental__dlt_loads: 2024-10-03 - 2024-10-03
├── sushi_dataset_sqlmesh.incremental_sushi_types: 2024-10-03 - 2024-10-03
└── sushi_dataset_sqlmesh.incremental_waiters: 2024-10-03 - 2024-10-03
Apply - Backfill Tables [y/n]: y
[1/1] sushi_dataset_sqlmesh.incremental__dlt_loads evaluated in 0.01s
[1/1] sushi_dataset_sqlmesh.incremental_sushi_types evaluated in 0.00s
[1/1] sushi_dataset_sqlmesh.incremental_waiters evaluated in 0.01s
Evaluating models ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100.0% • 3/3 • 0:00:00


All model batches have been executed successfully

Virtually Updating 'prod' ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100.0% • 0:00:00

The target environment has been updated successfully
```

モデルを計画して適用したら、他の SQLMesh プロジェクトと同様に、[プラン](../concepts/overview.md#make-a-plan) を生成して適用し、[テスト](../concepts/overview.md#tests) または [監査](../concepts/overview.md#audits) を実行し、必要に応じて [スケジューラ](../guides/scheduling.md) を使用してモデルを実行できます。
