# 通知ガイド

SQLMesh は、特定のイベントが発生した際に Slack またはメールで通知を送信できます。このページでは、通知の設定方法と受信者の指定方法について説明します。

## 通知ターゲット

通知は `notification targets` で設定します。ターゲットはプロジェクトの [configuration](https://sqlmesh.readthedocs.io/en/stable/reference/configuration/) ファイル (`config.yml` または `config.py`) で指定され、プロジェクトごとに複数のターゲットを指定できます。

プロジェクトでは、グローバル通知とユーザー固有の通知の両方を指定できます。各ターゲットの通知は、各 [イベントタイプ](#sqlmesh-event-types) のすべてのインスタンスに対して送信されます (例: `run` の通知は、プロジェクトのすべての環境に対して送信されます)。ただし、監査の失敗と [開発用にオーバーライドが設定されている場合](#notifications-during-development) は例外です。

[監査](../concepts/audits.md) の失敗通知は、以下の5つの条件が満たされた場合に、特定のモデルに対して送信できます。

1. モデルの `owner` フィールドが入力されている
2. モデルが1つ以上の監査を実行する
3. オーナーがユーザー固有の通知先を設定している
4. オーナーの通知先の `notify_on` キーに監査失敗イベントが含まれている
5. `prod` 環境で監査が失敗する

これらの条件が満たされた場合、`prod` 環境で監査が失敗した場合に、監査オーナーに通知が送信されます。

通知先は3種類あり、それぞれ [Slack 通知方法](#slack-notifications) と [メール通知](#email-notifications) の2つに対応しています。これらは、特定のユーザーの `notification_targets` キーまたは最上位の `notification_targets` 設定キーで指定します。

次の例は、ユーザー固有の通知先とグローバル通知先の両方の場所を示しています。

=== "YAML"

    ```yaml linenums="1"
    # User notification targets
    users:
      - username: User1
        ...
        notification_targets:
          - notification_target_1
            ...
          - notification_target_2
            ...
      - username: User2
        ...
        notification_targets:
          - notification_target_1
            ...
          - notification_target_2
            ...

    # Global notification targets
    notification_targets:
      - notification_target_1
        ...
      - notification_target_2
        ...
    ```

=== "Python"

    ```python linenums="1"
    config = Config(
        ...,
        # User notification targets
        users=[
            User(
                username="User1",
                notification_targets=[
                    notification_target_1(...),
                    notification_target_2(...),
                ],
            ),
            User(
                username="User2",
                notification_targets=[
                    notification_target_1(...),
                    notification_target_2(...),
                ],
            )
        ],

        # Global notification targets
        notification_targets=[
            notification_target_1(...),
            notification_target_2(...),
        ],
        ...
    )
    ```

### 開発中の通知

コード開発中は、通知をトリガーするイベントが繰り返し実行されることがあります。過剰な通知を防ぐため、SQLMesh は特定のユーザー以外のすべての通知ターゲットを停止できます。

最上位の `username` 設定キーに、特定のユーザー固有の通知ターゲットの `username` キーと同じ値を指定すると、そのユーザーのみに通知が送信されます。このキーは、プロジェクト設定ファイルまたは `~/.sqlmesh` にあるマシン固有の設定ファイルのいずれかで指定できます。後者は、特定のマシンを常に開発に使用する場合に便利です。

次の例では、`User1` 以外のすべての通知を停止します。

=== "YAML"

    ```yaml linenums="1" hl_lines="1-2"
    # Top-level `username` key: only notify User1
    username: User1
    # User1 notification targets
    users:
      - username: User1
        ...
        notification_targets:
          - notification_target_1
            ...
          - notification_target_2
            ...
    ```

=== "Python"

    ```python linenums="1" hl_lines="3-4"
    config = Config(
        ...,
        # Top-level `username` key: only notify User1
        username="User1",
        users=[
            User(
                # User1 notification targets
                username="User1",
                notification_targets=[
                    notification_target_1(...),
                    notification_target_2(...),
                ],
            ),
        ]
    )
    ```

## SQLMesh イベントの種類

SQLMesh 通知はイベントによってトリガーされます。通知をトリガーするイベントは、通知対象の `notify_on` フィールドで指定します。

通知は、[`plan` アプリケーション](../concepts/plans.md) の開始/終了/失敗、[`run`](../reference/cli.md#run) の開始/終了/失敗、および [`audit`](../concepts/audits.md) の失敗に対してサポートされます。

`plan` および `run` の開始/終了の場合、通知メッセージにはターゲット環境名が含まれます。失敗の場合、通知メッセージには Python 例外またはエラーテキストが含まれます。

以下の表に、各イベント、それに対応する `notify_on` 値、および通知メッセージを示します。

| イベント | `notify_on` キー値 | 通知メッセージ |
| ----------------------------- | ---------------------- | -------------------------------------------------------- |
| プラン適用の開始 | apply_start | 「環境 `{environment}` へのプラン適用が開始されました。」 |
| プラン適用の終了 | apply_end | 「環境 `{environment}` へのプラン適用が終了しました。」 |
| プラン適用の失敗 | apply_failure | 「プランの適用に失敗しました。\n{exception}」 |
| SQLMesh 実行の開始 | run_start | 「環境 `{environment}` への SQLMesh の実行が開始されました。」 |
| SQLMesh 実行の終了 | run_end | 「環境 `{environment}` への SQLMesh の実行が終了しました。」 |
| SQLMesh 実行の失敗 | run_failure | 「SQLMesh の実行に失敗しました。\n{exception}」 |
| 監査の失敗 | audit_failure | 「{audit_error}」 |

これらのイベントの任意の組み合わせを、通知ターゲットの `notify_on` フィールドで指定できます。

## Slack 通知

SQLMesh は 2 種類の Slack 通知をサポートしています。Slack Webhook は Slack チャンネルに通知できますが、特定のユーザーにメッセージを送信することはできません。Slack Web API はチャンネルまたはユーザーに通知できます。

### Webhook の設定

SQLMesh は、Webhook 通知に Slack の「Incoming Webhooks」を使用します。Slack で [Incoming Webhook を作成](https://api.slack.com/messaging/webhooks) すると、特定の Slack チャンネルに関連付けられた一意の URL が送信されます。SQLMesh は、その URL に JSON ペイロードを送信することで通知メッセージを送信します。

この例は、Slack Webhook の通知ターゲットを示しています。通知は、プラン適用の開始、プラン適用の失敗、または SQLMesh 実行の開始によってトリガーされます。この仕様では、URL を設定ファイルに直接ハードコーディングするのではなく、環境変数 `SLACK_WEBHOOK_URL` を使用します。

=== "YAML"

    ```yaml linenums="1"
    notification_targets:
      - type: slack_webhook
        notify_on:
          - apply_start
          - apply_failure
          - run_start
        url: "{{ env_var('SLACK_WEBHOOK_URL') }}"
    ```

=== "Python"

    ```python linenums="1"
    notification_targets=[
        SlackWebhookNotificationTarget(
            notify_on=["apply_start", "apply_failure", "run_start"],
            url=os.getenv("SLACK_WEBHOOK_URL"),
        )
    ]
    ```

### API 設定

ユーザーに通知したい場合は、Slack API 通知ターゲットを使用できます。この通知には Slack API トークンが必要です。このトークンは、異なるチャンネルやユーザーを持つ複数の通知ターゲットに使用できます。API トークンの取得方法については、[Slack の公式ドキュメント](https://api.slack.com/tutorials/tracks/getting-a-token) をご覧ください。

この例は、Slack API 通知ターゲットを示しています。通知は、プランの適用開始、プランの適用終了、または監査の失敗によってトリガーされます。仕様では、トークンを設定ファイルに直接ハードコーディングするのではなく、環境変数 `SLACK_API_TOKEN` を使用します。

=== "YAML"

    ```yaml linenums="1"
    notification_targets:
      - type: slack_api
        notify_on:
          - apply_start
          - apply_end
          - audit_failure
        token: "{{ env_var('SLACK_API_TOKEN') }}"
        channel: "UXXXXXXXXX"  # Channel or a user's Slack member ID
    ```

=== "Python"

    ```python linenums="1"
    notification_targets=[
        SlackApiNotificationTarget(
            notify_on=["apply_start", "apply_end", "audit_failure"],
            token=os.getenv("SLACK_API_TOKEN"),
            channel="UXXXXXXXXX",  # Channel or a user's Slack member ID
        )
    ]
    ```

## メール通知

SQLMesh はメールによる通知をサポートしています。通知先は、SMTP ホスト、ユーザー名、パスワード、送信者アドレスを指定します。1 つの通知先で複数の受信者メールアドレスに通知できます。

この例は、SQLMesh の実行が失敗した場合に `sushi@example.com` が `data-team@example.com` にメールを送信するメール通知先を示しています。この仕様では、設定ファイルに値を直接ハードコーディングするのではなく、環境変数 `SMTP_HOST`、`SMTP_USER`、`SMTP_PASSWORD` を使用します。

=== "YAML"

    ```yaml linenums="1"
    notification_targets:
      - type: smtp
        notify_on:
          - run_failure
        host: "{{ env_var('SMTP_HOST') }}"
        user: "{{ env_var('SMTP_USER') }}"
        password: "{{ env_var('SMTP_PASSWORD') }}"
        sender: sushi@example.com
        recipients:
          - data-team@example.com
    ```

=== "Python"

    ```python linenums="1"
    notification_targets=[
        BasicSMTPNotificationTarget(
            notify_on=["run_failure"],
            host=os.getenv("SMTP_HOST"),
            user=os.getenv("SMTP_USER"),
            password=os.getenv("SMTP_PASSWORD"),
            sender="notifications@example.com",
            recipients=[
                "data-team@example.com",
            ],
        )
    ]
    ```

## 高度な使用方法

### 通知ターゲットのオーバーライド

Python 設定ファイルでは、新しい通知ターゲットを設定してカスタムメッセージを送信できます。

通知をカスタマイズするには、上記の 3 つのターゲットクラス (`SlackWebhookNotificationTarget`、`SlackApiNotificationTarget`、`BasicSMTPNotificationTarget`) のいずれかのサブクラスとして、新しい通知ターゲットクラスを作成します。これらのクラスの定義は、Github [こちら](https://github.com/TobikoData/sqlmesh/blob/main/sqlmesh/core/notification_target.py) で参照できます。

これらの通知ターゲットクラスはそれぞれ、`BaseNotificationTarget` のサブクラスであり、`BaseNotificationTarget` には各イベントタイプに対応する `notify` 関数が含まれています。以下の表に、通知関数と、呼び出し時に利用可能なコンテキスト情報 (開始/終了イベントの環境名など) を示します。

| 関数名 | コンテキスト情報 |
| -------------------- | -------------------------------- |
| notify_apply_start   | Environment name: `env`          |
| notify_apply_end     | Environment name: `env`          |
| notify_apply_failure | Exception stack trace: `exc`     |
| notify_run_start     | Environment name: `env`          |
| notify_run_end       | Environment name: `env`          |
| notify_run_failure   | Exception stack trace: `exc`     |
| notify_audit_failure | Audit error trace: `audit_error` |

この例では、新しい通知ターゲットクラス `CustomSMTPNotificationTarget` を作成します。

デフォルトの `notify_run_failure` 関数をオーバーライドして、ログファイル `"/home/sqlmesh/sqlmesh.log"` を読み取り、その内容を例外スタックトレース `exc` に追加します。

=== "Python"

```python
from sqlmesh.core.notification_target import BasicSMTPNotificationTarget

class CustomSMTPNotificationTarget(BasicSMTPNotificationTarget):
    def notify_run_failure(self, exc: str) -> None:
        with open("/home/sqlmesh/sqlmesh.log", "r", encoding="utf-8") as f:
            msg = f"{exc}\n\nLogs:\n{f.read()}"
        super().notify_run_failure(msg)
```

この新しいクラスを使用するには、構成ファイルで通知ターゲットとして指定します。

=== "Python"

    ```python linenums="1" hl_lines="2"
    notification_targets=[
        CustomSMTPNotificationTarget(
            notify_on=["run_failure"],
            host=os.getenv("SMTP_HOST"),
            user=os.getenv("SMTP_USER"),
            password=os.getenv("SMTP_PASSWORD"),
            sender="notifications@example.com",
            recipients=[
                "data-team@example.com",
            ],
        )
    ]
    ```