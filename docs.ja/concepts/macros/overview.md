# 概要

SQL は [宣言型言語](https://en.wikipedia.org/wiki/Declarative_programming) です。SQL コマンドを状況に応じて異なる動作にするための変数や制御フローロジック (if-then、for ループ) といった機能はネイティブには備えていません。

しかし、データパイプラインは動的であり、コンテキストに応じて異なる動作が必要になります。SQL は *マクロ* によって動的に実現されます。

SQLMesh は、SQLMesh マクロと [Jinja](https://jinja.palletsprojects.com/en/3.1.x/) テンプレートシステムの 2 つのマクロシステムをサポートしています。

SQLMesh のマクロについて詳しくは、以下をご覧ください。

- [定義済みマクロ変数](./macro_variables.md) は両方のマクロシステムで使用可能です。
- [SQLMesh マクロ](./sqlmesh_macros.md)
- [Jinja マクロ](./jinja_macros.md)
