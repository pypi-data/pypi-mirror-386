"""
Sanwa Main (汎用) プロジェクト向けサービス群

このパッケージは、migrate配下のシェルスクリプト機能をPythonサービスとして提供します。
最初の実装では以下をサポートします:
- prod-full.xml のマニフェスト生成
- 本番 org からのメタデータ取得と prod-full への展開
- Git 操作（add/commit/push/tag）

UI層は `sf_devtools.ui.sanwa_main` を参照してください。
"""
