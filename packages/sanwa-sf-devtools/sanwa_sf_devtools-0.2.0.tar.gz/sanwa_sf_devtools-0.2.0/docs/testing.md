# テストと品質ゲート

本プロジェクトは `pytest` によるユニットテスト、`black`/`isort` による整形、`mypy` による型チェックを想定しています。

## すぐ試す

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
```

## 詳細

- テスト: `python -m pytest -q`
- 整形: `black src/sf_devtools src/tests` `isort src/sf_devtools src/tests`
- 型: `mypy src/sf_devtools`

CI（GitHub Actions）では push/PR 時にこれらを自動実行する構成を推奨します。

## ヒント

- 外部コマンド（sf, git, rsync）はモック化し、副作用を避けます。
- 対話 UI は直接起動しないようにし、サービス層の関数をテスト対象にします。
