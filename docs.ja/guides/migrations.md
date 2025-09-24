# 移行ガイド

SQLMesh の新しいバージョンは、プロジェクトに保存されているメタデータ形式と互換性がない可能性があります。移行により、プロジェクトのメタデータ形式をアップグレードし、新しい SQLMesh バージョンで動作するようにすることができます。

## 非互換性の検出

SQLMesh コマンドを実行すると、SQLMesh はインストールされている SQLMesh のバージョンとプロジェクトのメタデータ形式との間の非互換性を自動的にチェックし、必要なアクションを要求します。アクションが完了するまで、SQLMesh コマンドは実行されません。

### インストールされているバージョンがメタデータ形式よりも新しい

このシナリオでは、プロジェクトのメタデータ形式を移行する必要があります。

```bash
> sqlmesh plan my_dev
Error: SQLMesh (local) is using version '2' which is ahead of '1' (remote). Please run a migration ('sqlmesh migrate' command).
```

### インストールされているバージョンがメタデータ形式よりも古い

インストールされている SQLMesh のバージョンをアップグレードする必要があります。

```bash
> sqlmesh plan my_dev
SQLMeshError: SQLMesh (local) is using version '1' which is behind '2' (remote). Please upgrade SQLMesh.
```

## 移行方法

### 組み込みスケジューラによる移行

SQLMesh の migrate コマンドを使用して、プロジェクトメタデータを最新のメタデータ形式に移行できます。

```bash
> sqlmesh migrate
```

マイグレーションは単一のユーザーが手動で発行する必要があり、プロジェクトの全ユーザーに影響します。
マイグレーションは、plan/apply を実行しているユーザーがいないときに実行するのが理想的です。
マイグレーションは並列実行しないでください。
これらの制約のため、SQLMesh の管理責任者が手動でマイグレーションを発行することをお勧めします。
したがって、CI/CD パイプラインからマイグレーションを発行することは推奨されません。
