# CLI

```
使用方法: sqlmesh [オプション] コマンド [引数]...

  SQLMesh コマンドラインツール。

オプション:
  --version           バージョンを表示して終了します。
  -p, --paths TEXT    SQLMesh 設定/プロジェクトへのパス。
  --config TEXT       設定オブジェクトの名前。
                      Python スクリプトを使用して定義された設定にのみ適用されます。
  --gateway TEXT      ゲートウェイの名前。
  --ignore-warnings   警告を無視します。
  --debug             デバッグモードを有効にします。
  --log-to-stdout     ログを標準出力に表示します。
  --log-file-dir TEXT ログファイルを書き込むディレクトリ。
  --help              このメッセージを表示して終了します。

コマンド:
  audit                   対象モデルの監査を実行します。
  clean                   SQLMesh キャッシュとビルドアーティファクトをすべてクリアします。
  create_external_models  外部モデルを含むスキーマファイルを作成します...
  create_test             指定されたモデルのユニットテストフィクスチャを生成します。
  dag                     DAG を HTML ファイルとしてレンダリングします。
  destroy                 destroy コマンドは、すべてのプロジェクト リソースを削除します。
  diff                    ローカル状態と... の差分を表示します。
  dlt_refresh             DLT パイプラインにアタッチし、次のオプションを指定します。
  environments            SQLMesh 環境のリストを出力します。
  evaluate                モデルを評価し、... を含むデータフレームを返します。
  fetchdf                 SQL クエリを実行し、結果を表示します。
  format                  すべての SQL モデルと監査をフォーマットします。
  info                    SQLMesh プロジェクトに関する情報を出力します。
  init                    新しい SQLMesh リポジトリを作成します。
  invalidate              ターゲット環境を無効化し、... を強制的に適用します。
  janitor                 janitor プロセスをオンデマンドで実行します。
  migrate                 SQLMesh を現在実行中のバージョンに移行します。
  plan                    ローカルの変更をターゲット環境に適用します。
  prompt                  LLM を使用して、プロンプトから SQL クエリを生成します。
  render                  モデルのクエリをレンダリングします。オプションで拡張します...
  rewrite                 セマンティックを使用して SQL 式を書き換えます...
  rollback                SQLMesh を以前のマイグレーションにロールバックします。
  run                     ターゲットの欠落区間を評価します...
  state                   状態を操作するためのコマンド
  table_diff              2 つのテーブル間の差分を表示します。
  table_name              物理テーブルの名前を出力します...
  test                    モデルの単体テストを実行します。
  ui                      ブラウザベースの SQLMesh UI を起動します。
  lint                    ターゲットモデルのリンターを実行します。
```

## audit

```
使用方法: sqlmesh audit [オプション]

  対象モデルの監査を実行します。

オプション:
  --model TEXT          監査するモデル。複数のモデルを監査できます。
  -s, --start TEXT      このコマンドを適用する期間の開始日時。
  -e, --end TEXT        このコマンドを適用する期間の終了日時。
  --execution-time TEXT 実行時刻（デフォルトは現在）。
  --help                このメッセージを表示して終了します。
```

## check_intervals

```
使用方法: sqlmesh check_intervals [オプション] [環境]

  シグナルを考慮し、環境内の欠損区間を表示します。

オプション:
  --no-signals          シグナルチェックを無効にし、欠損区間のみを表示します。
  --select-model TEXT   欠損区間を表示するモデルを選択します。
  -s, --start TEXT      このコマンドが適用される区間の開始日時。
  -e, --end TEXT        このコマンドが適用される区間の終了日時。
  --help                このメッセージを表示して終了します。
```

## clean

```
使用方法: sqlmesh clean [オプション]

  SQLMesh キャッシュとビルドアーティファクトをクリアします。

オプション:
  --help  このメッセージを表示して終了します。
```

## create_external_models

```
使用方法: sqlmesh create_external_models [OPTIONS]

  外部モデルスキーマを含むスキーマファイルを作成します。

オプション:
  --help  このメッセージを表示して終了します。
```

## create_test

```
使用方法: sqlmesh create_test [OPTIONS] MODEL

  指定されたモデルのユニットテストフィクスチャを生成します。

オプション:
  -q, --query <TEXT TEXT>...  モデルの依存関係のデータを生成するために使用するクエリ。
  -o, --overwrite             true の場合、フィクスチャファイルが既に存在する場合は上書きされます。
  -v, --var <TEXT TEXT>...    モデルに必要な変数を定義するキーと値のペア。
  -p, --path TEXT             フィクスチャに対応するファイルパス（テストディレクトリからの相対パス）。
                              デフォルトでは、フィクスチャはテストディレクトリの下に作成され、
                              ファイル名はテスト名に基づいて推測されます。
  -n, --name TEXT             作成されるテストの名前。
                              デフォルトでは、モデル名に基づいて推測されます。
  --include-ctes              true の場合、CTE フィクスチャも生成されます。
  --help                      このメッセージを表示して終了します。
```

## dag

```
使用方法: sqlmesh dag [OPTIONS] FILE

  DAG を HTML ファイルとしてレンダリングします。

オプション:
  --select-model TEXT   DAG に含める特定のモデルを選択します。
  --help                このメッセージを表示して終了します。
```

## destroy

```
使用方法: sqlmesh destroy

  すべての状態テーブル、SQLMesh キャッシュ、およびウェアハウスオブジェクトを含む
  すべてのプロジェクトリソースを削除します。
  これには、SQLMesh によって管理されるすべてのテーブル、ビュー、スキーマ、および
  それらのスキーマ内で他のツールによって作成された可能性のある外部リソースが含まれます。

オプション:
  --help    このメッセージを表示して終了します。
```

## dlt_refresh

```
使用方法: dlt_refresh PIPELINE [OPTIONS]

  SQLMesh プロジェクトの特定のモデルまたはすべてのモデルを更新するオプション付きで、
  DLT パイプラインに接続します。

オプション:
  -t, --table TEXT  SQLMesh モデルを生成する DLT テーブル。
                    指定しない場合は、不足しているすべての新しいテーブルが生成されます。
  -f, --force       設定すると、既存のモデルが DLT テーブルから生成された新しいモデルで上書きされます。
  --help            このメッセージを表示して終了します。
```

## diff

```
使用方法: sqlmesh diff [OPTIONS] ENVIRONMENT

  ローカル状態とターゲット環境の差分を表示します。

オプション:
  --help    このメッセージを表示して終了します。
```

## environments
```
使用方法: sqlmesh environments [OPTIONS]

  SQLMesh 環境のリストとその有効期限を出力します。

オプション:
  --help    このメッセージを表示して終了します。
```

## evaluate

```
使用方法: sqlmesh evaluate [OPTIONS] MODEL

  モデルを評価し、デフォルトの制限値 1000 のデータフレームを返します。

オプション:
  -s, --start TEXT      このコマンドが適用される期間の開始日時。
  -e, --end TEXT        このコマンドが適用される期間の終了日時。
  --execution-time TEXT 実行時刻 (デフォルトは現在)。
  --limit INTEGER       クエリの制限行数。
  --help                このメッセージを表示して終了します。
```

## fetchdf

```
使用方法: sqlmesh fetchdf [OPTIONS] SQL

  SQLクエリを実行し、結果を表示します。

オプション:
  --help                このメッセージを表示して終了します。
```

## format

```
使用方法: sqlmesh format [OPTIONS]

  すべてのSQLモデルと監査をフォーマットします。

オプション:
  -t, --transpile TEXT        プロジェクトモデルを指定された方言にトランスパイルします。
  --append-newline            各ファイルの末尾に改行を挿入します。
  --no-rewrite-casts          既存のキャストを、:: 構文に書き換えずに保持します。
  --normalize                 識別子を小文字に正規化するかどうかを指定します。
  --pad INTEGER               フォーマットされた文字列のパディングサイズを指定します。
  --indent INTEGER            フォーマットされた文字列のインデントサイズを指定します。
  --normalize-functions TEXT  すべての関数名を正規化するかどうかを指定します。
                              指定可能な値: 'upper'、'lower'
  --leading-comma             select 式において、カンマを先頭にするか末尾にするかを指定します。
                              デフォルトは末尾です。
  --max-text-width INTEGER    プリティモードで改行する前のセグメントの最大文字数。
  --check                     フォーマットをチェックするかどうか
                              （ただし、実際にフォーマットするわけではありません）。
  --help                      このメッセージを表示して終了します。
```

## info

```
使用方法: sqlmesh info [OPTIONS]

  SQLMesh プロジェクトに関する情報を出力します。

  プロジェクトモデルとマクロの数、およびデータウェアハウスの接続テストが含まれます。

オプション:
  --skip-connection   接続テストをスキップします。
  -v, --verbose       詳細出力を表示します。
  --help              このメッセージを表示して終了します。
```

## init

```
使用方法: sqlmesh init [OPTIONS] [ENGINE]

  新しいSQLMeshリポジトリを作成します。

オプション:
  -t, --template TEXT   プロジェクトテンプレート。
                        サポートされる値: dbt、dlt、default、empty。
  --dlt-pipeline TEXT   SQLMeshプロジェクトを生成するDLTパイプライン。
                        テンプレート: dlt と一緒に使用します。
  --dlt-path TEXT       DLTパイプラインが存在するディレクトリ。
                        テンプレート: dlt と一緒に使用します。
  --help                このメッセージを表示して終了します。
```

## invalidate

```
使用方法: sqlmesh invalidate [OPTIONS] ENVIRONMENT

  ターゲット環境を無効化し、janitor プロセスの次回実行時に強制的に削除します。

オプション:
  -s, --sync  環境が削除されるまで待機してから戻ります。
              指定しない場合は、janitor プロセスによって非同期的に環境が削除されます。
              このオプションを使用するには、データウェアハウスへの接続が必要です。
  --help      このメッセージを表示して終了します。
```

## janitor

```
使用方法: sqlmesh janitor [OPTIONS]

  janitor プロセスをオンデマンドで実行します。

  janitor は古い環境と期限切れのスナップショットをクリーンアップします。

オプション:
  --ignore-ttl  どの環境からも参照されていないスナップショットを、
                有効期限の設定に関係なくクリーンアップします。
  --help        このメッセージを表示して終了します。
```

## migrate

```
使用方法: sqlmesh migrate [OPTIONS]

  SQLMesh を現在実行中のバージョンに移行します。

オプション:
  --help    このメッセージを表示して終了します。
```

!!! danger "Caution"

    `migrate` コマンドはすべての SQLMesh ユーザーに影響します。実行する前に SQLMesh 管理者に問い合わせてください。

## plan

```
使用方法: sqlmesh plan [OPTIONS] [ENVIRONMENT]

  ローカルの変更をターゲット環境に適用します。

オプション:
  -s, --start TEXT                このコマンドが適用される間隔の開始日時。
  -e, --end TEXT                  このコマンドが適用される間隔の終了日時。
  --execution-time TEXT           実行時刻（デフォルトは現在）。
  --create-from TEXT              ターゲット環境が存在しない場合、その環境を作成する環境。
                                  デフォルト: prod。
  --skip-tests                    テストが定義されている場合、プラン生成前にテストをスキップします。
  --skip-linter                   リンターが有効な場合、プラン生成前にリンティングをスキップします。
  -r, --restate-model TEXT        指定されたモデルと、指定されたモデルの下流にあるモデルのデータを
                                  再ステートします。
                                  本番環境では、関連するすべてのモデルバージョンの間隔が消去されますが、
                                  現在のバージョンのみがバックフィルされます。
                                  開発環境では、現在のモデルバージョンのみが影響を受けます。
  --no-gaps                       ターゲット環境の一致するモデルの既存のスナップショットと比較する際に、
                                  新しいスナップショットにデータギャップがないことを確認します。
  --skip-backfill, --dry-run      バックフィル手順をスキップし、プランの仮想更新のみを作成します。
  --empty-backfill                空のバックフィルを生成します。
                                  --skip-backfill と同様にモデルはバックフィルされませんが、
                                  --skip-backfill とは異なり、バックフィルされていない間隔は
                                  バックフィルされたかのように記録されます。
  --forward-only                  フォワードのみの変更のプランを作成します。
  --allow-destructive-model TEXT  式に一致する名前のモデルに対して、破壊的なフォワードのみの変更を許可します。
  --allow-additive-model TEXT     式に一致する名前のモデルに対して、追加的なフォワードのみの変更を許可します。
  --effective-from TEXT           本番環境でフォワードのみの変更を適用する有効日。
  --no-prompts                    バックフィルの時間範囲に対する対話型プロンプトを無効にします。
                                  このフラグが設定されていて、分類されていない変更がある場合、
                                  プランの作成は失敗することに注意してください。
  --auto-apply                    作成後に新しいプランを自動的に適用します。
  --no-auto-categorization        変更の自動分類を無効にします。
  --include-unmodified            ターゲット環境に変更されていないモデルを含めます。
  --select-model TEXT             プランに含める特定のモデル変更を選択します。
  --backfill-model TEXT           式に一致する名前のモデルのみをバックフィルします。
  --no-diff                       変更されたモデルのテキスト差分を非表示にします。
  --run                           プラン適用の一部として最新の間隔を実行します（本番環境のみ）。
  --enable-preview                開発環境をターゲットとする場合、順方向のみのモデルのプレビューを有効にします。
  --diff-rendered                 レンダリングされたモデルとスタンドアロン監査のテキスト差分を出力します。
  --explain                       プランを適用する代わりに、プランを説明します。
  -v, --verbose                   詳細出力。非常に詳細な出力には -vv を使用します。
  --help                          このメッセージを表示して終了します。
```

## prompt

```
使用方法: sqlmesh prompt [OPTIONS] PROMPT

  LLM を使用してプロンプトから SQL クエリを生成します。

オプション:
  -e, --evaluate          生成された SQL クエリを評価し、結果を表示します。
  -t, --temperature FLOAT サンプリング温度。
                          0.0 - 正確で予測可能、
                          0.5 - バランスが取れている、
                          1.0 - クリエイティブ。
                          デフォルト: 0.7
  -v, --verbose           詳細出力。
  --help                  このメッセージを表示して終了します。
```

## render

```
使用方法: sqlmesh render [OPTIONS] MODEL

  モデルのクエリをレンダリングします。オプションで参照モデルを拡張することもできます。

オプション:
  -s, --start TEXT            このコマンドが適用される期間の開始日時。
  -e, --end TEXT              このコマンドが適用される期間の終了日時。
  --execution-time TEXT       実行時刻（デフォルトは現在）。
  --expand TEXT               マテリアライズドモデルを拡張するかどうか。（デフォルトはFalse）。
                              Trueの場合、参照されているすべてのモデルが生のクエリとして拡張されます。
                              複数のモデル名を指定することもできます。
                              その場合は、それらのモデルのみが生のクエリとして拡張されます。
  --dialect TEXT              クエリをレンダリングするSQL方言。
  --no-format                 クエリの特殊フォーマットを無効にします。
  --max-text-width INTEGER    プリティーモードで改行する前のセグメントの最大文字数。
  --leading-comma             選択した式において、カンマが先頭か末尾かを決定します。
                              デフォルトは末尾です。
  --normalize-functions TEXT  すべての関数名を正規化するかどうかを指定します。
                              指定可能な値は「upper」、「lower」です。
  --indent INTEGER            フォーマットされた文字列のインデントサイズを決定します。
  --pad INTEGER               フォーマットされた文字列のパディングサイズを決定します。
  --normalize                 識別子を小文字に正規化するかどうかを指定します。
  --help                      このメッセージを表示して終了します。
```

## rewrite

```
使用方法: sqlmesh rewrite [OPTIONS] SQL

  セマンティック参照を含むSQL式を実行可能なクエリに書き換えます。

  https://sqlmesh.readthedocs.io/en/latest/concepts/metrics/overview/

オプション:
  --read TEXT   SQL文字列の入力言語。
  --write TEXT  SQL文字列の出力言語。
  --help        このメッセージを表示して終了します。
```

## rollback

```
使用方法: sqlmesh rollback [OPTIONS]

  SQLMesh を以前の移行状態にロールバックします。

オプション:
  --help    このメッセージを表示して終了します。
```

!!! danger "Caution"

    `rollback` コマンドはすべての SQLMesh ユーザーに影響します。実行する前に SQLMesh 管理者に問い合わせてください。

## run

```
使用方法: sqlmesh run [OPTIONS] [ENVIRONMENT]

  ターゲット環境の欠落した間隔を評価します。

オプション:
  -s, --start TEXT              このコマンドが適用される間隔の開始日時。
  -e, --end TEXT                このコマンドが適用される間隔の終了日時。
  --skip-janitor                管理タスクをスキップします。
  --ignore-cron                 個々の cron スケジュールを無視し、
                                すべての欠落した間隔で実行します。
  --select-model TEXT           実行する特定のモデルを選択します。
                                注: これは常に上流の依存関係を含みます。
  --exit-on-env-update INTEGER  設定されている場合、
                                ターゲット環境の更新によって実行が中断された場合、
                                コマンドは指定されたコードで終了します。
  --no-auto-upstream            上流モデルを自動的に含めません。
                                --select-model が使用されている場合にのみ適用されます。
                                注: これにより、選択したモデルのデータが欠落または
                                無効になる可能性があります。
  --help                        このメッセージを表示して終了します。
```

## state

```
使用方法: sqlmesh state [OPTIONS] COMMAND [ARGS]...

  状態を操作するためのコマンド

オプション:
  --help  このメッセージを表示して終了します。

コマンド:
  export  状態データベースをファイルにエクスポートします。
  import  状態エクスポートファイルを状態データベースにインポートします。
```

### export

```
使用方法: sqlmesh state export [OPTIONS]

  状態データベースをファイルにエクスポートします。

オプション:
  -o, --output-file FILE  状態エクスポートの出力先パス [必須]
  --environment TEXT      エクスポートする環境名。
                          複数の環境をエクスポートするには、
                          --environment 引数を複数指定します。
  --local                 ローカル状態のみをエクスポートします。
                          出力ファイルはインポートできませんのでご注意ください。
  --no-confirm            既存の状態をエクスポートする前に確認メッセージを表示しません。
  --help                  このメッセージを表示して終了します。
```

### import

```
使用方法: sqlmesh state import [OPTIONS]

  状態エクスポートファイルを状態データベースにインポートします。

オプション:
  -i, --input-file FILE 状態ファイルへのパス [必須]
  --replace             ファイルをロードする前にリモート状態をクリアします。
                        省略した場合は、代わりにマージが実行されます。
  --no-confirm          既存の状態を更新する前に確認メッセージを表示しません。
  --help                このメッセージを表示して終了します。
```

## table_diff

```
使用方法: sqlmesh table_diff [OPTIONS] SOURCE:TARGET [MODEL]

  2つの環境にわたる2つのテーブルまたは複数のモデル間の差分を表示します。

オプション:
  -o, --on TEXT           結合する列。複数回指定できます。
                          指定がない場合は、モデルの粒度が使用されます。
  -s, --skip-columns TEXT ソーステーブルとターゲットテーブルを比較する際にスキップする列。
  --where TEXT            結果をフィルタリングするためのオプションのwhere文。
  --limit INTEGER         サンプルデータフレームの制限。
  --show-sample           差異のある行のサンプルを表示します。
                          列数が多い場合、出力が非常に長くなる可能性があります。
  -d, --decimals INTEGER  浮動小数点列を比較する際に保持する小数点以下の桁数。
                          デフォルト: 3
  --skip-grain-check      主キー（粒度）が欠落しているか一意でない場合のチェックを無効にします。
  --warn-grain-check      選択したモデルにグレインが欠落している場合に警告を発し、
                          残りのモデルの差分を計算します。
  --temp-schema TEXT      一時テーブルに使用するスキーマ。
                          指定できる値は `CATALOG.SCHEMA` または `SCHEMA` です。
                          デフォルト: `sqlmesh_temp`
  -m, --select-model TEXT 差分テーブルを作成するモデルを選択します。
  --help                  このメッセージを表示して終了します。
```

## table_name

```
使用方法: sqlmesh table_name [OPTIONS] MODEL_NAME

  指定されたモデルの物理テーブル名を出力します。

オプション:
  --environment, --env TEXT モデルバージョンの取得元となる環境。
  --prod                    設定されている場合、ターゲット環境で昇格されたモデルバージョンで
                            本番環境で使用される物理テーブル名を返します。
  --help                    このメッセージを表示して終了します。
```

## test

```
使用方法: sqlmesh test [OPTIONS] [TESTS]...

  モデルの単体テストを実行します。

オプション:
  -k TEXT             部分文字列のパターンに一致するテストのみを実行します。
  -v, --verbose       詳細出力を表示します。
  --preserve-fixtures テストデータベース内のフィクスチャテーブルを保存します。
                      デバッグに役立ちます。
  --help              このメッセージを表示して終了します。
```

## ui

```
使用方法: sqlmesh ui [OPTIONS]

  ブラウザベースの SQLMesh UI を起動します。

オプション:
  --host TEXT                     ソケットをこのホストにバインドします。
                                  デフォルト: 127.0.0.1
  --port INTEGER                  ソケットをこのポートにバインドします。
                                  デフォルト: 8000
  --mode [ide|catalog|docs|plan]  UI を起動するモード。デフォルト: ide
  --help                          このメッセージを表示して終了します。
```

## lint

```
使用方法: sqlmesh lint [OPTIONS]

  対象モデルに対してリンターを実行します。

オプション:
  --model TEXT  リンターを実行するモデル。
                複数のモデルをリンターできます。
                モデルを指定しない場合は、すべてのモデルがリンターされます。
  --help        このメッセージを表示して終了します。
```
