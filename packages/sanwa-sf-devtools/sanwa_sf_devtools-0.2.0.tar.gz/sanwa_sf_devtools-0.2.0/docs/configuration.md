# 設定と TOML 管理

本ツールはプロジェクト直下の `.sf-devtools/` を設定ルートとして使用します。

## 設定ファイルの場所

- `.sf-devtools/org-config.toml` : 組織関連の設定（alias/orgName/作成日時など）
- `.sf-devtools/config.toml` : プロジェクト固有のパスなど（存在すれば）

## org-config.toml の例

```toml
[org]
alias = "prod"
orgName = "Sanwa Main"
createdAt = "2025-10-01T12:00:00Z"

[paths]
sourceDir = "force-app"
metaDir = "metadata"
manifestDir = "manifest"
```

実際のキーは UI/実装の進捗により拡張される場合があります。

## 旧 JSON 設定からの移行

- 旧 `scripts/org-config.json` が存在する場合、初回起動時に自動的に検出し、TOML へ移行（バックアップ作成）します。
- UI の「org-config 初期化/移行」から手動実行も可能です。

## 優先順位と上書き

- 既定値 < `.sf-devtools/*.toml` < 環境変数（将来対応予定）
- 将来的に `pyproject.toml` からの継承やローカル設定（`.local.toml`）も検討中です。

## よくある質問（FAQ）

- TOML が読み込まれない: パスや拡張子、権限を確認してください。
- キーが反映されない: UI 再起動、キャッシュ削除、バージョン確認を行ってください。
