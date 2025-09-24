# 開発への貢献

SQLMesh は [Apache 2.0](https://github.com/TobikoData/sqlmesh/blob/main/LICENSE) に基づいてライセンスされています。コミュニティへの貢献を奨励しており、皆様のご参加を心よりお待ちしております。以下のドキュメントでは、SQLMesh への貢献プロセスについて概説しています。

## 前提条件

始める前に、以下のソフトウェアがマシンにインストールされていることを確認してください。インストール方法は、お使いのオペレーティングシステムによって異なります。

* Docker
* Docker Compose V2
* OpenJDK >= 11
* Python >= 3.9 < 3.13

## 仮想環境の設定

SQLMesh の開発には、仮想環境の使用を推奨します。

```bash
python -m venv .venv
source .venv/bin/activate
```

仮想環境をアクティブ化したら、次のコマンドを実行して依存関係をインストールできます。

```bash
make install-dev
```

オプションとして、pre-commit を使用してリンター/フォーマッタを自動的に実行することもできます。

```bash
make install-pre-commit
```

## Python 開発

リンターとフォーマッタを実行します。

```bash
make style
```

より速いローカルフィードバックを得るために、より高速なテストを実行します。

```bash
make fast-test
```

各コミットで実行されるより包括的なテストを実行します。

```bash
make slow-test
```

## ドキュメント

ドキュメントサーバーを実行するには、次のコマンドを実行して依存関係をインストールする必要があります。

```bash
make install-doc
```

依存関係をインストールしたら、次のコマンドを実行してドキュメント サーバーを実行できます。

```bash
make docs-serve
```

ドキュメントテストを実行します。

```bash
make doc-test
```

## UI 開発

Python 開発に加えて、UI も開発できます。

UI は React と Typescript を使用して構築されています。UI を実行するには、以下のコマンドを実行して依存関係をインストールする必要があります。

```bash
pnpm install
```

Run ide:

```bash
make ui-up
```

## VSCode 拡張機能の開発

UI 開発と同様に、VSCode 拡張機能も開発できます。そのためには、`vscode/extension` ディレクトリ内で次のコマンドを実行し、依存関係がインストールされていることを確認してください。

```bash
pnpm install
```

完了したら、SQLMeshリポジトリのルートで開かれたVisual Studio Codeワークスペースから「Run Extensions」デバッグタスクを起動することで、VSCode拡張機能の開発が最も簡単に行えます。デフォルトでは、VSCode拡張機能はSQLMeshサーバーをローカルで実行し、SQLMesh IDEを試すことができる新しいVisual Studio Codeウィンドウを開きます。デフォルトでは「examples/sushi」プロジェクトが開きます。「Run Extensions」デバッグタスクを実行するようにVisual Studio Codeを設定するには、次のコマンドを実行します。このコマンドは、「launch.json」ファイルと「tasks.json」ファイルを「.vscode」ディレクトリにコピーします。

```bash 
make vscode_settings
```
