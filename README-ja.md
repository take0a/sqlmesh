<p align="center">
  <img src="docs/readme/sqlmesh.png" alt="SQLMesh logo" width="50%" height="50%">
</p>

SQLMeshは、データを迅速かつ効率的に、そしてエラーなく送信できるように設計された次世代のデータ変換フレームワークです。データチームは、SQLまたはPythonで記述されたデータ変換を、あらゆる規模のデータソースで可視性と制御性を確保しながら実行および展開できます。

これは単なる [dbt の代替](https://tobikodata.com/reduce_costs_with_cron_and_partitions.html) ではありません。

<p align="center">
  <img src="docs/readme/architecture_diagram.png" alt="Architecture Diagram" width="100%" height="100%">
</p>

## Core Features

<img src="https://github.com/TobikoData/sqlmesh-public-assets/blob/main/vscode.gif?raw=true" alt="SQLMesh Plan Mode">

> CLI と [SQLMesh VSCode 拡張機能](https://sqlmesh.readthedocs.io/en/latest/guides/vscode/?h=vs+cod) の両方で、変更による SQL の影響とコンテキストを即座に取得します。

  <details>
  <summary><b>仮想データ環境</b></summary>

  * [仮想データ環境](https://whimsical.com/virtual-data-environments-MCT8ngSxFHict4wiL48ymz)の仕組みを詳しく説明した図をご覧ください。
  * [詳しくはこちらの動画をご覧ください](https://www.youtube.com/watch?v=weJH3eM0rzc)

  </details>

  * データウェアハウスのコストをかけずに、独立した開発環境を構築できます。
  * [Terraform](https://www.terraform.io/) のようなワークフローを計画・適用することで、変更による潜在的な影響を把握できます。
  * 真のブルーグリーンデプロイメントを実現する、使いやすい [CI/CD ボット](https://sqlmesh.readthedocs.io/en/stable/integrations/github/) もご利用いただけます。

<details>
<summary><b>効率とテスト</b></summary>

このコマンドを実行すると、`tests/` フォルダにユニットテストファイル `test_stg_payments.yaml` が生成されます。

ライブクエリを実行し、モデルの期待される出力を生成します。

```bash
sqlmesh create_test tcloud_demo.stg_payments --query tcloud_demo.seed_raw_payments "select * from tcloud_demo.seed_raw_payments limit 5"

# run the unit test
sqlmesh test
```

```sql
MODEL (
  name tcloud_demo.stg_payments,
  cron '@daily',
  grain payment_id,
  audits (UNIQUE_VALUES(columns = (
      payment_id
  )), NOT_NULL(columns = (
      payment_id
  )))
);

SELECT
    id AS payment_id,
    order_id,
    payment_method,
    amount / 100 AS amount, /* `amount` is currently stored in cents, so we convert it to dollars */
    'new_column' AS new_column, /* non-breaking change example  */
FROM tcloud_demo.seed_raw_payments
```

```yaml
test_stg_payments:
model: tcloud_demo.stg_payments
inputs:
    tcloud_demo.seed_raw_payments:
      - id: 66
        order_id: 58
        payment_method: coupon
        amount: 1800
      - id: 27
        order_id: 24
        payment_method: coupon
        amount: 2600
      - id: 30
        order_id: 25
        payment_method: coupon
        amount: 1600
      - id: 109
        order_id: 95
        payment_method: coupon
        amount: 2400
      - id: 3
        order_id: 3
        payment_method: coupon
        amount: 100
outputs:
    query:
      - payment_id: 66
        order_id: 58
        payment_method: coupon
        amount: 18.0
        new_column: new_column
      - payment_id: 27
        order_id: 24
        payment_method: coupon
        amount: 26.0
        new_column: new_column
      - payment_id: 30
        order_id: 25
        payment_method: coupon
        amount: 16.0
        new_column: new_column
      - payment_id: 109
        order_id: 95
        payment_method: coupon
        amount: 24.0
        new_column: new_column
      - payment_id: 3
        order_id: 3
        payment_method: coupon
        amount: 1.0
        new_column: new_column
```
</details>

* テーブルを[複数回](https://tobikodata.com/simplicity-or-efficiency-how-dbt-makes-you-choose.html)作成しないでください。
* 変更されたデータを追跡し、[増分モデル](https://tobikodata.com/correctly-loading-incremental-data-at-scale.html)に必要な変換のみを実行します。
* [ユニットテスト](https://tobikodata.com/we-need-even-greater-expectations.html)を無料で実行し、自動監査を構成します。
* 変更の影響を受けるテーブル/ビューに基づいて、本番環境と開発環境間で[テーブルの差分](https://sqlmesh.readthedocs.io/en/stable/examples/sqlmesh_cli_crash_course/?h=crash#run-data-diff-against-prod)を実行します。

<details>
<summary><b>SQLをレベルアップ</b></summary>
任意の方言で SQL を記述すると、SQLMesh はそれをウェアハウスに送信する前に、ターゲットの SQL 方言に即座に変換します。
<img src="https://github.com/TobikoData/sqlmesh/blob/main/docs/readme/transpile_example.png?raw=true" alt="Transpile Example">
</details>

* ウェアハウスで実行する前に、[10種類以上のSQL方言](https://sqlmesh.readthedocs.io/en/stable/integrations/overview/#execution-engines)で変換エラーをデバッグできます。
* [シンプルなSQL](https://sqlmesh.readthedocs.io/en/stable/concepts/models/sql_models/#sql-based-definition)を使用した定義（冗長でわかりにくい`Jinja` + `YAML`は不要です）
* 列レベルの系統情報を使用して、ウェアハウスで実行する前に変更の影響を確認できます。

詳細については、[ウェブサイト](https://www.tobikodata.com/sqlmesh) と[ドキュメント](https://sqlmesh.readthedocs.io/en/stable/) をご覧ください。

## はじめに
以下のコマンドを実行して、[pypi](https://pypi.org/project/sqlmesh/) から SQLMesh をインストールします。

```bash
mkdir sqlmesh-example
cd sqlmesh-example
python -m venv .venv
source .venv/bin/activate
pip install 'sqlmesh[lsp]' # install the sqlmesh package with extensions to work with VSCode
source .venv/bin/activate # reactivate the venv to ensure you're using the right installation
sqlmesh init # follow the prompts to get started (choose DuckDB)
```

</details>

> 注意: Python のインストール状況に応じて、`python` または `pip` の代わりに `python3` または `pip3` を実行する必要がある場合があります。

<details>
<summary><b>Windowsのインストール</b></summary>

```bash
mkdir sqlmesh-example
cd sqlmesh-example
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install 'sqlmesh[lsp]' # install the sqlmesh package with extensions to work with VSCode
.\.venv\Scripts\Activate.ps1 # reactivate the venv to ensure you're using the right installation
sqlmesh init # follow the prompts to get started (choose DuckDB)
```
</details>


SQLMeshの使い方を学ぶには、[クイックスタートガイド](https://sqlmesh.readthedocs.io/en/stable/quickstart/cli/)をご覧ください。すでに有利なスタートを切っています！

[クラッシュコース](https://sqlmesh.readthedocs.io/en/stable/examples/sqlmesh_cli_crash_course/)でコアとなるムーブセットを学習し、簡単に参照できるチートシートを活用してください。

SQLMeshの完全な使い方を学ぶには、こちらの[例](https://sqlmesh.readthedocs.io/en/stable/examples/incremental_time_full_walkthrough/)をご覧ください。

## コミュニティに参加しませんか？
私たちは共に、無駄のないデータ変換を実現したいと考えています。以下の方法でコミュニティにご参加ください。

* [Tobiko Slackコミュニティ](https://tobikodata.com/slack)に参加して、質問したり、ただ挨拶したりしましょう！
* [GitHub](https://github.com/TobikoData/sqlmesh/issues/new)で問題を報告してください。
* ご質問やフィードバックは、[hello@tobikodata.com](mailto:hello@tobikodata.com)までメールでお送りください。
* [ブログ](https://tobikodata.com/blog)をご覧ください。

## 貢献
Issue や pull request（フォークから）といった形での貢献を心よりお待ちしております。

SQLMesh オープンソースへの貢献方法については、[詳細はこちら](https://sqlmesh.readthedocs.io/en/stable/development/) をご覧ください。

[こちらのビデオ ウォークスルーをご覧ください](https://www.loom.com/share/2abd0d661c12459693fa155490633126?sid=b65c1c0f-8ef7-4036-ad19-3f85a3b87ff2) で、私たちのチームが SQLMesh に機能をどのように貢献しているかをご覧ください。



# MEMO
## 日本語訳

このリポジトリで（機械）翻訳した日本語ドキュメントを見るには

```bash
git clone https://github.com/take0a/sqlmesh
cd sqlmesh
uv sync
# uv add -r docs.ja/requirements.txt
uv run mkdocs serve -f mkdocs-ja.yml
```

して、ブラウザで http://127.0.0.1:8000/ へ接続する

## 開発環境

`[project.optional-dependencies]` も sync したい場合は以下を実行する。
バージョンの制約を掛けずに pyarrow を入れると死ぬので、`pyproject.toml` で >18 縛りにした。

```bash
uv sync --extra dev --extra lsp
```

## 状態DB

VSCode 拡張の場合は、状態データベースを Duckdb にしないようにということなので、
実質的に唯一の推奨エンジンである Postgres を入れた。

```bash
sudo dnf upgrade --releasever=2023.8.20250915
sudo dnf install postgresql17-server
sudo postgresql-setup --initdb
sudo systemctl start postgresql
sudo systemctl enable postgresql
sudo passwd postgres
su - postgres
```

postgres でいる間に、psql で postgres ユーザーにパスワードを付与して

```psql
postgres=# alter user postgres with encrypted password 'xxxxxxxx';
```

pg_hba.conf で peer 認証からデータベースユーザーのパスワード認証に変更すると、
OS の postgres ユーザー以外も DB の postgres ユーザーを使えるようになる

```/var/lib/pgsql/data/pg_hba.conf
# TYPE  DATABASE        USER            ADDRESS                 METHOD
local   all             all                                     md5
```

exit して、元のユーザーに戻って

```bash
sudo systemctl restart postgresql
psql -U postgres
```

で接続できれば OK