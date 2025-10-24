# リリース公開・導入ガイド（GitHub Actions 前提）

本プロジェクトは GitHub Actions により、バージョンタグを push するだけで PyPI/TestPyPI へ自動公開されます。

## 方針と使い分け

- 開発版（PEP 440: `X.Y.Z.devN`）
  - Git タグ: `vX.Y.Z.devN`
  - 公開先: TestPyPI
- プレリリース（例: `X.Y.ZrcN`）/ 安定版（`X.Y.Z`）
  - Git タグ: `vX.Y.ZrcN` / `vX.Y.Z`
  - 公開先: 本番 PyPI

※ PEP 440 に準拠したバージョニングを使用します。

## 手順（共通）

1. `pyproject.toml` の `[project] version` を更新（例: `0.2.0.dev1` / `0.2.0rc1` / `0.2.0`）
2. バージョンと同一の Git タグを作成して push

```zsh
git tag v0.2.0.dev1   # 例: 開発版
git push origin v0.2.0.dev1
```

CI が起動し、ビルド→検査→公開まで自動実行されます。

## インストール（利用側）

- 開発版（TestPyPI）

```zsh
python -m pip install \
  --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple \
  "sanwa-sf-devtools==X.Y.Z.devN"
```

- プレリリース（rc 等）/ 安定版（PyPI）

厳密ピン（推奨）:

```zsh
python -m pip install "sanwa-sf-devtools==X.Y.ZrcN"   # rc の例
python -m pip install "sanwa-sf-devtools==X.Y.Z"      # 安定版の例
```

範囲指定でプレリリースを含める場合は `--pre` を明示:

```zsh
python -m pip install --pre "sanwa-sf-devtools>=X.Y.Z.dev0,<X.Y.Z"
```

## バージョニング（PEP 440）概要

- 安定版: `0.2.0`
- プレリリース: `0.2.0a1` / `0.2.0b1` / `0.2.0rc1`
- 開発版: `0.2.0.dev1`

pip は既定でプレリリース/開発版を自動採用しません。導入側で厳密ピンか `--pre` を使用してください。

## CI の前提（リポジトリ側）

- 開発版タグ `v*.*.*.dev*` で TestPyPI に公開（`.github/workflows/testpypi.yml`）
- rc / 安定版タグで PyPI に公開（別ワークフローを運用）
- Secrets
  - TestPyPI: `TEST_PYPI_API_TOKEN`
  - PyPI: `PYPI_API_TOKEN`

## トラブルシューティング

- 既に同じバージョンが存在: バージョンを上げて再タグ付け
- 認証エラー: GitHub Secrets の API トークンを確認
- TestPyPI で依存が解決しない: `--extra-index-url https://pypi.org/simple` を付与
- CLI が見つからない: 仮想環境の有効化と PATH を確認
