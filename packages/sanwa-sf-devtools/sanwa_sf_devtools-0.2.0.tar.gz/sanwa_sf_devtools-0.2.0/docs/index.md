# SF DevTools ドキュメント

Salesforce 開発を効率化する対話型 CLI「SF DevTools」のドキュメントです。UI 主導で安全・簡単に日常作業を支援します。

## できること（ハイライト）

- 対話型メニューでの操作（汎用/Sanwa Main と MES の二段メニュー）
- マニフェスト生成（project:generate manifest）と本番メタデータの取得・展開
- 変換（source→mdapi）とデプロイ（検証/本番）
- Git スナップショットコミット、ブランチ作成、手動タグ作成
- 旧シェルスクリプトからの移行支援（JSON→TOML 設定移行）

## UI 全体像

- トップメニュー
  - 汎用（Sanwa Main）
  - MES 機能メニュー
  - 設定・環境確認
  - ヘルプ・ドキュメント
  - 終了

詳しくは「UI ガイド」を参照してください。

## まずは使ってみる

- 対話 UI 起動: `sf_devtools --interactive`
- バージョン確認: `sf_devtools --version`

## ドキュメント一覧

- UI ガイド: `docs/ui.md`
- 設定とTOML: `docs/configuration.md`
- 移行ガイド（旧スクリプト→UI）: `docs/migration.md`
- テスト/品質: `docs/testing.md`
