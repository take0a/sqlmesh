# 概要

現実的な例は、SQLMesh をより深く理解するための素晴らしい方法です。

プロジェクトのコードとデータを操作し、様々な SQLMesh コマンドを実行して何が起こるかを確認できます。

例はいつでもリセットできるので、状況が変わっても最初からやり直すことができます。

このページでは、いくつかの異なるタイプの例へのリンクを提供しています。

- **ウォークスルー** では、特定のストーリーまたはタスクを提示し、そのストーリーに沿って進めていきます。
    - ウォークスルーではコードを実行する必要はありませんが、必要に応じてコードを入手できます。
    - ウォークスルーごとに使用する SQL エンジンが異なるため、コードを実行する場合は、お使いの SQL エンジンに合わせてコードを更新する必要がある場合があります。
- **プロジェクト** は、自己完結型の SQLMesh プロジェクトとデータセットです。
    - プロジェクトは通常 DuckDB を使用するため、別の SQL エンジンをインストールしたりアクセスしたりすることなく、ローカルで実行できます。

!!! tip

    これまで SQLMesh を試したことがない場合は、これらの例を試す前に [SQLMesh クイックスタート](../quick_start.md) を実行することをお勧めします。

## ウォークスルー

ウォークスルーはわかりやすく、自己完結型の形式で多くの情報を提供します。

- [SQLMesh CLI クラッシュコース](./sqlmesh_cli_crash_course.md) で SQLMesh ワークフローを習得しましょう。
- [時間範囲による増分：完全ウォークスルー](./incremental_time_full_walkthrough.md) で、エンドツーエンドのワークフローの実際の動作を確認してください (BigQuery SQL エンジン)

## プロジェクト

SQLMesh のサンプルプロジェクトは、[sqlmesh-examples Github リポジトリ](https://github.com/TobikoData/sqlmesh-examples) に保存されています。リポジトリのトップページには、ファイルのダウンロード方法とプロジェクトのセットアップ方法に関する追加情報が記載されています。

最も包括的な 2 つのサンプルプロジェクトでは、架空の寿司レストランをモデルにした SQLMesh の `sushi` データを使用しています。(「Tobiko」は寿司でよく使われるトビウオの卵を意味する日本語です。)

`sushi` データについては、リポジトリ内の [概要ノートブック](https://github.com/TobikoData/sqlmesh-examples/blob/main/001_sushi/sushi-overview.ipynb) で説明されています。

サンプルリポジトリには、複雑さの異なる2つのバージョンの `sushi` プロジェクトが含まれています。

- [`simple` プロジェクト](https://github.com/TobikoData/sqlmesh-examples/tree/main/001_sushi/1_simple) には、4 つの `VIEW` モデルと 1 つの `SEED` モデルが含まれています。
    - `VIEW` モデルは実行ごとに更新されるため、SQLMesh の動作を容易に理解できます。
- [`moderate` プロジェクト](https://github.com/TobikoData/sqlmesh-examples/tree/main/001_sushi/2_moderate) には、5 つの `INCREMENTAL_BY_TIME_RANGE` モデル、1 つの `FULL` モデル、1 つの `VIEW` モデル、1 つの `SEED` モデルが含まれています。
    - 増分モデルを使用すると、SQLMesh によって新しいデータがどのように、いつ変換されるかを観察できます。
    - `customer_revenue_lifetime` などの一部のモデルは、顧客生涯価値の計算など、より高度な増分クエリをデモンストレーションします。
