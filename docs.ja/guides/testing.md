# テストガイド

## モデルの変更のテスト

モデルの単体テストを実行するには、次のように `sqlmesh test` コマンドを実行します。

```bash
$ sqlmesh test
.
----------------------------------------------------------------------
Ran 1 test in 0.042s

OK
```

ユニットテストを実行すると、SQLMesh は失敗したテストを特定します。

テストの詳細については、[テスト](../concepts/tests.md) を参照してください。

### 特定のモデルへの変更をテストする

特定のモデルテストを実行するには、スイートファイル名に続けて `::` とテスト名を渡します。例: `sqlmesh test tests/test_suite.yaml::test_example_full_model`。

### テストのサブセットを実行する

パターンまたは部分文字列に一致するテストを実行するには、次の構文を使用します: `sqlmesh test tests/test_example*`。

上記のコマンドを実行すると、先ほど `sqlmesh test` を使用して実行した `test_example_full_model` テストが実行されます。

```
$ sqlmesh test tests/test_example*
.
----------------------------------------------------------------------
Ran 1 test in 0.042s

OK
```

別の例として、`sqlmesh test tests/test_order*` コマンドを実行すると、以下のテストが実行されます。

* `test_orders`
* `test_orders_takeout`
* `test_order_items`
* `test_order_type`

## モデルの変更の監査

モデルを監査するには、次のように `sqlmesh audit` コマンドを実行します。

```bash
$ sqlmesh audit
Found 1 audit(s).
assert_positive_order_ids PASS.

Finished with 0 audit error(s).
Done.
```

**注:** 監査を実行する前に、変更を計画し、適用済みであることを確認してください。

デフォルトでは、SQLMesh は監査が失敗するとパイプラインを停止し、無効な可能性のあるデータが下流に伝播するのを防ぎます。この動作は、監査を [non-blocking](../concepts/audits.md#non-blocking-audits) として定義することで、個々の監査ごとに変更できます。

監査の詳細については、[auditing](../concepts/audits.md) を参照してください。