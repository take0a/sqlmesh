# シリアル化

SQLMesh は、[マクロ](../macros/overview.md) と [Python モデル](../../concepts/models/python_models.md) を介して Python コードを実行します。各 Python モデルはスタンドアロンの [スナップショット](../architecture/snapshots.md) として保存され、これにはモデルの生成に必要なすべての Python コードが含まれます。

## シリアル化形式

SQLMesh は Python の `pickle` 形式ではなく、独自のシリアル化形式を採用しています。これは、`pickle` 形式が Python のバージョン間で互換性がなく、例えば Python 3.9 で開発を行い、本番環境で Python 3.10 を実行することができないためです。

SQLMesh は Python 実装の文字列表現を保存し、それを再評価します。カスタム Python 関数またはマクロが指定されると、SQLMesh は関数の抽象構文木 (AST) を読み取り、それをすべての依存関係とグローバル変数とともに文字列表現に変換します。詳細については、[スナップショット フィンガープリント](../architecture/snapshots.md#fingerprinting) を参照してください。

### 制限事項

SQLMesh は、記述した Python コードのみをシリアル化し、ライブラリはシリアル化しません。つまり、コードのモジュールは SQLMesh の設定パスと一致している必要があります。また、ライブラリへの参照はすべてインポートに変換されるため、SQLMesh が実行されるすべての場所に、使用するライブラリがインストールされていることを確認する必要があります。
