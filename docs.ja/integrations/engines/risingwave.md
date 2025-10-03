# RisingWave

このページでは、[RisingWave](https://risingwave.com/) ストリーミング データベース エンジンで SQLMesh を使用する方法について説明します。

!!! info

    RisingWaveエンジンアダプターはコミュニティからの貢献です。そのため、コミュニティからのサポートは限定的です。

## ローカル/組み込みスケジューラ

**エンジンアダプタタイプ**: `risingwave`

### インストール

```
pip install "sqlmesh[risingwave]"
```

## 接続オプション

RisingWave は Postgres をベースとしており、同じ `psycopg2` 接続ライブラリを使用します。そのため、接続パラメータは [Postgres](./postgres.md) と非常に似ています。

| オプション | 説明 | タイプ | 必須 |
|------------------|-------------------------------------------------------------------|:------:|:--------:|
| `type` | エンジンタイプ名 - `risingwave` である必要があります | 文字列 | Y |
| `host` | RisingWave サーバーのホスト名 | 文字列 | Y |
| `user` | RisingWave サーバーでの認証に使用するユーザー名 | 文字列 | Y |
| `password` | RisingWave サーバーでの認証に使用するパスワード | 文字列 | N |
| `port` | RisingWave エンジンサーバーのポート番号 | 整数 | Y |
| `database` |接続するデータベースインスタンスの名前 | 文字列 | Y |
| `role` | RisingWave サーバーでの認証に使用するロール | 文字列 | N |
| `sslmode` | RisingWave サーバーへの接続のセキュリティ | 文字列 | N |

## 追加機能

ストリーミングデータベースエンジンであるRisingWaveには、ストリーミングユースケースに特化した追加機能が搭載されています。

主な機能は以下のとおりです。
- [ソース](https://docs.risingwave.com/sql/commands/sql-create-source): KafkaなどのストリーミングソースからRisingWaveにレコードをストリーミングするために使用されます。
- [シンク](https://docs.risingwave.com/sql/commands/sql-create-sink): RisingWaveによって処理されたデータの結果を、オブジェクトストレージ内のApache Icebergテーブルなどの外部ターゲットに書き込むために使用されます。

RisingWaveは、これらの機能を通常のSQL文、つまり`CREATE SOURCE`と`CREATE SINK`で公開しています。SQLMeshでこれらの機能を利用するには、[pre / post ステートメント](../../concepts/models/sql_models.md#optional-prepost-statements)で使用できます。

以下は、 post ステートメントを使用して SQLMesh モデルからシンクを作成する例です。

```sql
MODEL (
    name sqlmesh_example.view_model,
    kind VIEW (
      materialized true
    )
);

SELECT
  item_id,
  COUNT(DISTINCT id) AS num_orders,
FROM
  sqlmesh_example.incremental_model
GROUP BY item_id;

CREATE
  SINK IF NOT EXISTS kafka_sink
FROM
  @this_model
WITH (
  connector='kafka',
  "properties.bootstrap.server"='localhost:9092',
  topic='test1',
)
FORMAT PLAIN
ENCODE JSON (force_append_only=true);
```

!!! info "@this_model"

    `@this_model` マクロは、モデルの現在のバージョンの物理テーブルに解決されます。詳細については、[こちら](../../concepts/macros/macro_variables.md#runtime-variables) を参照してください。