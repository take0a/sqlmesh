# dbt

SQLMesh は、dbt アダプターを使用して dbt プロジェクトを実行するためのネイティブ サポートを備えています。

!!! tip

    これまで SQLMesh を使用したことがない場合は、[SQLMesh クイックスタート](../quick_start.md)で SQLMesh の基本動作を学習してください。

## はじめに

### SQLMesh のインストール

SQLMesh は、`pip` コマンドでインストールする Python ライブラリです。SQLMesh プロジェクトは [Python 仮想環境](../installation.md#python-virtual-environment) で実行することをお勧めします。`pip` コマンドを実行する前に、仮想環境を作成してアクティブ化する必要があります。

ほとんどのユーザーは、SQLMesh のすべての機能を使用するわけではありません。たとえば、ほとんどのプロジェクトは 1 つの [SQL 実行エンジン](../integrations/overview.md#execution-engines) でのみ実行されます。

そのため、SQLMesh は複数の「追加機能」と共にパッケージ化されており、プロジェクトに必要な機能に応じてオプションでインストールできます。プロジェクトのすべての追加機能を 1 回の `pip` 呼び出しで指定できます。

SQLMesh dbt アダプターを使用するには、少なくとも dbt 追加機能をインストールする必要があります。

```bash
> pip install "sqlmesh[dbt]"
```

プロジェクトでDuckDB以外のSQL実行エンジンを使用している場合は、そのエンジン用のextraをインストールする必要があります。例えば、プロジェクトがPostgres SQLエンジンで動作している場合、以下のようになります。

```bash
> pip install "sqlmesh[dbt,postgres]"
```

[SQLMesh ブラウザー UI](../guides/ui.md) を使用して列レベルの系統を表示する場合は、`web` エクストラを追加します。

```bash
> pip install "sqlmesh[dbt,web]"
```

[SQLMesh のインストールと追加機能の詳細については、ここ](../installation.md#install-extras) を参照してください。

### dbt プロジェクトの読み込み

既存の dbt プロジェクトを SQLMesh で実行できるように準備するには、*dbt プロジェクトのルートディレクトリ内*で、`dbt` テンプレートオプションを指定して `sqlmesh init` コマンドを実行します。

```bash
$ sqlmesh init -t dbt
```

これにより、[デフォルトのモデル開始日](../reference/model_configuration.md#model-defaults)を含む `sqlmesh.yaml` というファイルが作成されます。この構成ファイルは、DBT プロジェクトで SQLMesh を動作させるための最低限の開始点となります。

SQLMesh でプロジェクトを実行することに慣れてきたら、必要に応じて追加の SQLMesh [構成](../reference/configuration.md) を指定して、より多くの機能を利用できるようになります。

!!! note "profiles.yml"

    SQLMesh は、dbt プロジェクトの `profiles.yml` ファイルにある既存のデータウェアハウス接続ターゲットを使用するため、`sqlmesh.yaml` で接続設定を複製する必要はありません。dbt 設定でいつでもターゲットを変更でき、SQLMesh は新しいターゲットを取得します。

### モデルのバックフィル開始日の設定

モデルでは、`start` 構成パラメータを使用して、データのバックフィルの開始日を**指定する必要があります**。`start` は、`config` ブロック内でモデルごとに個別に定義することも、`sqlmesh.yaml` ファイル内で次のようにグローバルに定義することもできます。

=== "sqlmesh.yaml"

    ```yaml
    model_defaults:
      start: '2000-01-01'
    ```

=== "dbt Model"

    ```jinja
    {{
      config(
        materialized='incremental',
        start='2000-01-01',
        ...
      )
    }}
    ```

### 構成

SQLMesh は、dbt 構成ファイルからプロジェクトの構成を取得します。このセクションでは、SQLMesh 固有の追加設定について説明します。

#### 別の状態接続の選択

Trino などの [一部のエンジン](https://sqlmesh.readthedocs.io/en/stable/guides/configuration/?h=unsupported#state-connection) は、SQLMesh の状態を保存するために使用できません。

また、ウェアハウスが状態をサポートしている場合でも、分析ワークロード向けに最適化されたウェアハウスよりも、[従来のデータベース](../concepts/state.md) を使用して状態を保存した方がパフォーマンスが向上する場合があります。

このような場合は、`state_connection` 構成を使用して、[サポートされている本番環境の状態エンジン](../concepts/state.md#state) を指定することをお勧めします。

これには、`sqlmesh.yaml` を更新して、状態接続用のゲートウェイ構成を追加する必要があります。

```yaml
gateways:
  "": # "" (empty string) is the default gateway
    state_connection:
      type: postgres
      ...

model_defaults:
  start: '2000-01-01'
```

または、`profiles.yml` で定義された特定の dbt プロファイル (例: `dev`) の場合:

```yaml
gateways:
  dev: # must match the target dbt profile name
    state_connection:
      type: postgres
      ...

model_defaults:
  start: '2000-01-01'
```

状態接続を構成する方法の詳細については、[こちら](https://sqlmesh.readthedocs.io/en/stable/guides/configuration/#state-connection) を参照してください。

#### 実行時変数

dbt は、[CLI の `vars` オプション](https://docs.getdbt.com/docs/build/project-variables#defining-variables-on-the-command-line) を使用して、実行時に変数値を渡すことができます。

SQLMesh では、これらの変数は構成を介して渡されます。`sqlmesh init` を使用して dbt プロジェクトを初期化すると、プロジェクトディレクトリに `sqlmesh.yaml` ファイルが作成されます。

ネイティブプロジェクトと同様に、構成に `variables` セクションを追加することで、グローバル変数を定義できます。

例えば、実行時変数 `is_marketing` とその値 `no` を次のように指定できます。

```yaml
variables:
  is_marketing: no

model_defaults:
  start: '2000-01-01'
```

ゲートウェイ/プロファイルレベルで変数を設定することもできます。これらの変数は、プロジェクトレベルで設定された変数をオーバーライドします。各レベルで変数を指定する方法の詳細については、[変数のドキュメント](../concepts/macros/sqlmesh_macros.md#gateway-variables)をご覧ください。

#### 組み合わせ

一部のプロジェクトでは、ランタイム変数の組み合わせを使用してプロジェクトの動作を制御します。異なる `sqlmesh_config` オブジェクトで異なる組み合わせを指定し、関連する設定を SQLMesh CLI コマンドに渡すことができます。

!!! info "Python config"

    異なる設定オブジェクトを切り替えるには、デフォルトの YAML 設定ではなく、[Python 設定](../guides/configuration.md#python) を使用する必要があります。

    プロジェクトのルートに、以下の内容を含む `config.py` というファイルを作成する必要があります。

    ```py
    from pathlib import Path
    from sqlmesh.dbt.loader import sqlmesh_config

    config = sqlmesh_config(Path(__file__).parent)
    ```

    `sqlmesh.yaml` の設定はアクティブな Python 設定の上に上書きされるため、`sqlmesh.yaml` ファイルを削除する必要はありません。

例えば、`marketing` 部門用の特別な設定を持つプロジェクトを考えてみましょう。実行時に渡す個別の設定を以下のように作成できます。

```python
config = sqlmesh_config(
  Path(__file__).parent,
  variables={"is_marketing": "no", "include_pii": "no"}
)

marketing_config = sqlmesh_config(
  Path(__file__).parent,
  variables={"is_marketing": "yes", "include_pii": "yes"}
)
```

デフォルトでは、SQLMesh は `config` という名前の構成オブジェクトを使用します。`--config` オプションを使用してオブジェクト名を SQLMesh CLI コマンドに渡すことで、別の構成を使用します。たとえば、次のようにマーケティング構成で `plan` を実行できます。

```python
sqlmesh --config marketing_config plan
```

`--config` オプションは、`sqlmesh` という単語と実行されるコマンド (例: `plan`、`run`) の間に指定されることに注意してください。

#### コメントの登録

SQLMesh は、[モデルの概要ドキュメント](../concepts/models/overview#model-description-and-comments) に記載されているように、モデルの説明と列のコメントを対象の SQL エンジンに自動的に登録します。コメントの登録は、それをサポートするすべてのエンジンでデフォルトで有効になっています。

dbt は、モデルごとに指定する [`persist_docs` モデル構成パラメータ](https://docs.getdbt.com/reference/resource-configs/persist_docs) を介して、同様のコメント登録機能を提供します。SQLMesh のコメント登録はプロジェクトレベルで構成されるため、dbt のモデル固有の `persist_docs` 構成は使用されません。

SQLMesh のプロジェクトレベルのコメント登録のデフォルトは、`sqlmesh_config()` の `register_comments` 引数によってオーバーライドされます。たとえば、次の構成はコメント登録を無効にします。

```python
config = sqlmesh_config(
    Path(__file__).parent,
    register_comments=False,
    )
```

### SQLMesh の実行

SQLMesh プロジェクトと同様に SQLMesh を実行し、[プラン](../concepts/overview.md#make-a-plan) を生成・適用し、[テスト](../concepts/overview.md#tests) または [監査](../concepts/overview.md#audits) を実行し、必要に応じて [スケジューラ](../guides/scheduling.md) を使用してモデルを実行します。

dbt ファイルとプロジェクト形式は引き続き使用できます。

## SQLMesh と dbt のワークフローの違い

dbt プロジェクトを使用する際は、以下の点にご注意ください。

* SQLMesh は、`plan` コマンドの実行と変更の適用の一環として、新規または変更されたシードを検出してデプロイします。個別のシードコマンドはありません。詳細については、[シードモデル](../concepts/models/seed_models.md) を参照してください。
* `plan` コマンドは環境を動的に作成するため、環境を `profiles.yml` ファイルにターゲットとしてハードコードする必要はありません。SQLMesh を最大限に活用するには、dbt プロファイルターゲットを本番環境ターゲットに設定し、残りの処理は SQLMesh に任せましょう。
* 「テスト」という用語は、dbt と SQLMesh では意味が異なります。
  - dbt の「テスト」は、SQLMesh では [監査](../concepts/audits.md) です。
  - SQLMesh の「テスト」は [ユニットテスト](../concepts/tests.md) であり、SQLMesh プランを適用する前にクエリロジックをテストします。
* dbt が推奨する増分ロジックは SQLMesh と互換性がないため、モデルに小さな調整が必要です (心配しないでください。dbt は引き続きモデルを使用できます)。

## dbt プロジェクトで SQLMesh の増分モデルを使用する方法

データセットが大きく、テーブルの再計算にコストがかかる場合、増分ロードは強力な手法です。SQLMesh は増分モデルを強力にサポートしますが、そのアプローチは dbt とは異なります。

このセクションでは、dbt の増分モデルを sqlmesh で実行できるように適応させ、dbt との下位互換性を維持する方法について説明します。

### 増分型

SQLMesh は、[べき等](../concepts/glossary.md#idempotency) な増分ロードを実装するための 2 つのアプローチをサポートしています。

* マージを使用する (sqlmesh の [`INCREMENTAL_BY_UNIQUE_KEY` モデル種類](../concepts/models/model_kinds.md#incremental_by_unique_key) を使用)
* [`INCREMENTAL_BY_TIME_RANGE` モデル種類](../concepts/models/model_kinds.md#incremental_by_time_range) を使用する

#### ユニークキーによる増分

incremental_by_unique_key による増分を有効にするには、モデル設定に以下を含める必要があります。

* モデルのユニークキーフィールド名を値として持つ `unique_key` キー
* 値を `'incremental'` とする `materialized` キー
* 次のいずれか:
  * `incremental_strategy` キーがない、または
  * 値を `'merge'` とする `incremental_strategy` キー

#### 時間範囲による増分

incremental_by_time_range による増分を有効にするには、モデル設定に以下の設定が含まれている必要があります。

* `materialized` キーに値 `'incremental'` を設定
* `incremental_strategy` キーに値 `incremental_by_time_range` を設定
* `time_column` キーにモデルの時間列フィールド名を設定（詳細は [`time column`](../concepts/models/model_kinds.md#time-column) を参照）

### 増分ロジック

dbt の増分戦略とは異なり、SQLMesh では増分ロジックを実装するために `is_incremental` Jinja ブロックを使用する必要はありません。
代わりに、SQLMesh は定義済みの時間マクロ変数を提供します。これらの変数は、モデルの SQL で時間列に基づいてデータをフィルタリングするために使用できます。

例えば、「ds」列を含む SQL `WHERE` 句は、次のように `{% if sqlmesh_incremental is defined %}` でゲートされた新しい Jinja ブロックに記述されます。

```bash
>   WHERE
>     ds BETWEEN '{{ start_ds }}' AND '{{ end_ds }}'
```

`{{ start_ds }}` と `{{ end_ds }}` は、SQLMesh の `@start_ds` と `@end_ds` という定義済みの時間マクロ変数に相当する Jinja の関数です。Jinja で利用可能なすべての [定義済みの時間変数](../concepts/macros/macro_variables.md) を参照してください。

### 増分モデルの設定

SQLMesh には、増分計算の実行方法を制御できる設定パラメータが用意されています。これらのパラメータは、モデルの `config` ブロックで設定します。

増分モデルの設定パラメータの完全なリストについては、[増分モデルのプロパティ](../concepts/models/overview.md#incremental-model-properties) を参照してください。

**注:** デフォルトでは、すべての増分 dbt モデルは [forward-only](../concepts/plans.md#forward-only-plans) に設定されています。ただし、個々のモデルの設定で、または `dbt_project.yaml` ファイル内のすべてのモデルに対してグローバルに `forward_only: false` を設定することで、この動作を変更できます。[forward-only](../concepts/plans.md#forward-only-plans) モードは、dbt の一般的な動作により近いため、ユーザーの期待に応えることができます。

同様に、[allow_partials](../concepts/models/overview.md#allow_partials) パラメータは、モデル設定で `allow_partials` パラメータが明示的に `false` に設定されていない限り、デフォルトで `true` に設定されます。

#### on_schema_change

SQLMesh は、[forward-only 増分モデル](../guides/incremental_time.md#forward-only-models) および [forward-only プラン](../concepts/plans.md#destructive-changes) 内のすべての増分モデルに対する破壊的および追加的なスキーマ変更を自動的に検出します。

モデルの [`on_destructive_change` および `on_additive_change` 設定](../guides/incremental_time.md#schema-changes) によって、変更をエラー、警告、警告なしで許可、または無視するかどうかが決まります。SQLMesh は、破壊的な変更（列の削除など）と追加的な変更（新しい列の追加など）の両方をきめ細かく制御できます。

`on_schema_change` 設定値は、以下の SQLMesh 設定にマッピングされます。

| `on_schema_change` | SQLMesh `on_destructive_change` | SQLMesh `on_additive_change` |
|--------------------|---------------------------------|------------------------------|
| ignore             | ignore                          | ignore                       |
| fail               | error                           | error                        |
| append_new_columns | ignore                          | allow                        |
| sync_all_columns   | allow                           | allow                        |


## スナップショットのサポート

SQLMesh は、`timestamp` または `check` の両方の dbt スナップショット戦略をサポートしています。
サポートされていないスナップショット機能は `invalidate_hard_deletes` のみで、`True` に設定する必要があります。
`False` に設定した場合、スナップショットはスキップされ、その旨を示す警告がログに記録されます。
この機能のサポートは近日中に追加される予定です。

## テスト
SQLMesh は dbt テストを使用して SQLMesh [監査](../concepts/audits.md) を実行します (近日公開予定)。

SQLMesh [ユニットテスト](../concepts/tests.md) を "tests" ディレクトリに配置して、dbt プロジェクトに追加します。

## シード列の型

SQLMesh は、[Panda の `read_csv` ユーティリティ](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.read_csv.html) とそのデフォルトの列型推論を使用して、シード CSV ファイルを解析します。

dbt は、[agate の csv リーダー](https://agate.readthedocs.io/en/latest/api/csv.html#csv-reader-and-writer) を使用してシード CSV ファイルを解析し、[agate のデフォルトの型推論をカスタマイズ](https://github.com/dbt-labs/dbt-common/blob/ae8ffe082926fdb3ef2a15486588f40c7739aea9/dbt_common/clients/agate_helper.py#L59) を使用してシード CSV ファイルを解析します。

SQLMesh と dbt がシード CSV ファイルの異なる列タイプを推測する場合は、`dbt_project.yml` ファイルで [column_types](https://docs.getdbt.com/reference/resource-configs/column_types) ディクショナリを指定できます。ここで、キーは列名を定義し、値はデータ型を定義します。

``` yaml
seeds:
  <seed name>
    +column_types:
      <column name>: <SQL data type>
```

あるいは、シード [シード プロパティ構成ファイル](https://docs.getdbt.com/reference/seed-properties) でこの辞書を定義することもできます。

``` yaml
seeds:
  - name: <seed name>
    config:
      column_types:
        <column name>: <SQL data type>
```

列のSQLデータ型を`data_type`キーで指定することもできます（以下を参照）。ファイルにはCSVファイル内のすべての列をリストする必要があります。`data_type`キーが指定されていない列には、SQLMeshのデフォルトの型推論が使用されます。

``` yaml
seeds:
  - name: <seed name>
    columns:
      - name: <column name>
        data_type: <SQL data type>
```

## パッケージ管理
SQLMesh には独自のパッケージマネージャーはありませんが、SQLMesh の dbt アダプターは dbt のパッケージマネージャーと互換性があります。パッケージの更新、追加、削除には、引き続き [dbt deps](https://docs.getdbt.com/reference/commands/deps) と [dbt clean](https://docs.getdbt.com/reference/commands/clean) をご利用ください。

## ドキュメント
モデルのドキュメントは、[SQLMesh UI](../quickstart/ui.md#2-open-the-sqlmesh-web-ui) でご覧いただけます。

## サポートされている dbt jinja メソッド

SQLMesh は、以下を含むほとんどの dbt jinja メソッドを使用した dbt プロジェクトの実行をサポートしています。

| Method    | Method         | Method       | Method  |
| --------- | -------------- | ------------ | ------- |
| adapter   | env_var        | project_name | target  |
| as_bool   | exceptions     | ref          | this    |
| as_native | from_yaml      | return       | to_yaml |
| as_number | is_incremental | run_query    | var     |
| as_text   | load_result    | schema       | zip     |
| api       | log            | set          |         |
| builtins  | modules        | source       |         |
| config    | print          | statement    |         |

## サポートされていない dbt jinja メソッド

現在サポートされていない dbt jinja メソッドは次のとおりです。

* debug
* selected_sources
* graph.nodes.values
* graph.metrics.values

## 必要な情報が不足していますか？

[問題](https://github.com/TobikoData/sqlmesh/issues) を送信していただければ、調査いたします。
