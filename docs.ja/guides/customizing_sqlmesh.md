# SQLMesh のカスタマイズ

SQLMesh は、大多数のデータエンジニアリングチームが使用するワークフローをサポートしています。しかし、企業によっては、SQLMesh との特別な統合を必要とする独自のプロセスやツールを使用している可能性があります。

SQLMesh はオープンソースの Python ライブラリであるため、基盤となるコードを参照し、ニーズに合わせてカスタマイズできます。

カスタマイズでは、通常、SQLMesh クラスをサブクラス化して機能を拡張または変更します。

!!! danger "注意"

    SQLMesh をカスタマイズする際は、細心の注意を払ってください。エラーが発生すると、SQLMesh が予期しない結果を生成する可能性があります。

## カスタムローダー

ロードとは、プロジェクトファイルを読み込み、その内容をSQLMeshの内部Pythonオブジェクトに変換するプロセスです。

ロード段階は、ファイルから読み込んだ後、SQLMeshが使用する前にプロジェクトのオブジェクトにアクセスできるため、SQLMeshの動作をカスタマイズするのに便利な段階です。

SQLMeshの`SqlMeshLoader`クラスはロードプロセスを処理します。このクラスをサブクラス化し、メソッドをオーバーライドすることでカスタマイズできます。

!!! note "Python設定のみ"

    カスタム ローダーでは、[Python 構成形式](./configuration.md#python) を使用する必要があります (YAML はサポートされていません)。

### すべてのモデルを変更する

ロードプロセスをカスタマイズする理由の一つは、すべてのモデルに何らかの処理を施すことです。例えば、すべてのモデルに post 文を追加したい場合などです。

ロードプロセスではすべてのモデルの SQL 文が解析されるため、新規または変更された SQL は、モデルオブジェクトに渡す前に SQLGlot で解析する必要があります。

このカスタムローダーの例では、すべてのモデルに post 文を追加します。

``` python linenums="1" title="config.py"
from sqlmesh.core.loader import SqlMeshLoader
from sqlmesh.utils import UniqueKeyDict
from sqlmesh.core.dialect import parse_one
from sqlmesh.core.config import Config

# New `CustomLoader` class subclasses `SqlMeshLoader`
class CustomLoader(SqlMeshLoader):
    # Override SqlMeshLoader's `_load_models` method to access every model
    def _load_models(
        self,
        macros: "MacroRegistry",
        jinja_macros: "JinjaMacroRegistry",
        gateway: str | None,
        audits: UniqueKeyDict[str, "ModelAudit"],
        signals: UniqueKeyDict[str, "signal"],
    ) -> UniqueKeyDict[str, "Model"]:
        # Call SqlMeshLoader's normal `_load_models` method to ingest models from file and parse model SQL
        models = super()._load_models(macros, jinja_macros, gateway, audits, signals)

        new_models = {}
        # Loop through the existing model names/objects
        for model_name, model in models.items():
            # Create list of existing and new post-statements
            new_post_statements = [
                # Existing post-statements from model object
                *model.post_statements,
                # New post-statement is raw SQL, so we parse it with SQLGlot's `parse_one` function.
                # Make sure to specify the SQL dialect if different from the project default.
                parse_one(f"VACUUM @this_model"),
            ]
            # Create a copy of the model with the `post_statements_` field updated
            new_models[model_name] = model.copy(update={"post_statements_": new_post_statements})

        return new_models

# Pass the CustomLoader class to the SQLMesh configuration object
config = Config(
    # < your configuration parameters here >,
    loader=CustomLoader,
)
```