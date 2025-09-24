#

<p align="center">
  <img src="https://github.com/TobikoData/sqlmesh/blob/main/docs/readme/sqlmesh.png?raw=true" alt="SQLMesh logo" width="50%" height="50%">
</p>

SQLMeshは、データを迅速かつ効率的に、そしてエラーなく送信できるように設計された次世代のデータ変換フレームワークです。データチームは、SQLまたはPythonで記述されたデータ変換を、あらゆる規模の可視性と制御性を備えながら、効率的に実行および展開できます。

これは単なる [dbt の代替](https://tobikodata.com/reduce_costs_with_cron_and_partitions.html) ではありません。

<p align="center">
  <img src="https://github.com/TobikoData/sqlmesh/blob/main/docs/readme/architecture_diagram.png?raw=true" alt="Architecture Diagram" width="100%" height="100%">
</p>

## コア機能
<img src="https://github.com/TobikoData/sqlmesh-public-assets/blob/main/sqlmesh_plan_mode.gif?raw=true" alt="SQLMesh Plan Mode">

> CLI でも [SQLMesh プラン モード](https://sqlmesh.readthedocs.io/en/stable/guides/ui/?h=modes#working-with-an-ide) でも、変更の SQL 影響分析を即座に取得できます。

??? tip "仮想データ環境"

    - [仮想データ環境](https://whimsical.com/virtual-data-environments-MCT8ngSxFHict4wiL48ymz)の仕組みを詳しく解説した図をご覧ください。
    - [詳しくはこちらの動画をご覧ください](https://www.youtube.com/watch?v=weJH3eM0rzc)

* データウェアハウスのコストをかけずに、独立した開発環境を構築できます。
* [Terraform](https://www.terraform.io/) のようなワークフローを計画・適用することで、変更による潜在的な影響を把握できます。
* 真のブルーグリーンデプロイメントを実現する、使いやすい [CI/CD ボット](https://sqlmesh.readthedocs.io/en/stable/integrations/github/) もご利用いただけます。

??? tip "効率とテスト"

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

* テーブルを[複数回](https://tobikodata.com/simplicity-or-efficiency-how-dbt-makes-you-choose.html)作成しないでください。
* 変更されたデータを追跡し、[増分モデル](https://tobikodata.com/correctly-loading-incremental-data-at-scale.html)に必要な変換のみを実行します。
* [ユニットテスト](https://tobikodata.com/we-need-even-greater-expectations.html)を無料で実行し、自動監査を設定します。

??? tip "SQLをレベルアップ"

    任意の方言で SQL を記述すると、SQLMesh はそれをウェアハウスに送信する前に、ターゲットの SQL 方言に即座に変換します。
    <img src="https://github.com/TobikoData/sqlmesh/blob/main/docs/readme/transpile_example.png?raw=true" alt="Transpile Example">

* ウェアハウスで実行する前に、[10種類以上のSQL方言](https://sqlmesh.readthedocs.io/en/stable/integrations/overview/#execution-engines)で変換エラーをデバッグできます。
* [シンプルなSQL](https://sqlmesh.readthedocs.io/en/stable/concepts/models/sql_models/#sql-based-definition)を使用した定義（冗長でわかりにくい`Jinja` + `YAML`は不要です）
* 列レベルの系統情報を使用して、ウェアハウスで実行する前に変更の影響を確認できます。

詳細については、[ウェブサイト](https://sqlmesh.com)と[ドキュメント](https://sqlmesh.readthedocs.io/en/stable/)をご覧ください。

## はじめる
次のコマンドを実行して、[pypi](https://pypi.org/project/sqlmesh/) 経由で SQLMesh をインストールします。

```bash
mkdir sqlmesh-example
cd sqlmesh-example
python -m venv .venv
source .venv/bin/activate
pip install sqlmesh
source .venv/bin/activate # reactivate the venv to ensure you're using the right installation
sqlmesh init duckdb # get started right away with a local duckdb instance
sqlmesh plan # see the plan for the changes you're making
```

> 注意: Python のインストール状況に応じて、`python` または `pip` の代わりに `python3` または `pip3` を実行する必要がある場合があります。

SQLMeshの使い方を学ぶには、[クイックスタートガイド](https://sqlmesh.readthedocs.io/en/stable/quickstart/cli/#1-create-the-sqlmesh-project)をご覧ください。すでに順調なスタートを切っています！

SQLMeshの完全な使い方を学ぶには、こちらの[例](https://sqlmesh.readthedocs.io/en/stable/examples/incremental_time_full_walkthrough/)をご覧ください。

## コミュニティに参加する
私たちは共に、無駄のないデータ変換を実現したいと考えています。以下の方法で私たちとつながりましょう。

* [Tobiko Slackコミュニティ](https://tobikodata.com/slack)に参加して、質問したり、ただ挨拶したりしましょう！
* [GitHub](https://github.com/TobikoData/sqlmesh/issues/new)で問題を報告してください。
* ご質問やフィードバックは、[hello@tobikodata.com](mailto:hello@tobikodata.com)までメールでお送りください。
* [ブログ](https://tobikodata.com/blog)をご覧ください。

## 貢献
Issue やプルリクエストによる貢献を心よりお待ちしております。

SQLMesh オープンソースへの貢献方法については、[詳細はこちら](https://sqlmesh.readthedocs.io/en/stable/development/) をご覧ください。

[こちらのビデオ ウォークスルーをご覧ください](https://www.loom.com/share/2abd0d661c12459693fa155490633126?sid=b65c1c0f-8ef7-4036-ad19-3f85a3b87ff2) で、私たちのチームが SQLMesh に機能をどのように貢献しているかをご覧ください。
