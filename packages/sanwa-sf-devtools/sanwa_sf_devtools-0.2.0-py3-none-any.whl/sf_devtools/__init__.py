"""
Salesforce 開発用統合CLI（Python版）
"""

from __future__ import annotations

import os
from importlib import metadata
from typing import Any, Dict


def _read_version() -> str:
    # 1) インストール済みパッケージのメタデータから取得
    try:
        return metadata.version("sanwa-sf-devtools")
    except Exception:
        pass

    # 2) ローカル開発時のフォールバック: pyproject.toml の [project].version を読む
    try:
        import tomllib  # py310+

        # リポジトリルートを推定（本ファイルから上へ辿る）
        here = os.path.dirname(os.path.abspath(__file__))
        root = os.path.abspath(os.path.join(here, os.pardir, os.pardir, os.pardir))
        pyproject = os.path.join(root, "pyproject.toml")
        if os.path.exists(pyproject):
            with open(pyproject, "rb") as f:
                data: Dict[str, Any] = tomllib.load(f)
                version = data.get("project", {}).get("version")
                if isinstance(version, str):
                    return version
                if version is not None:
                    return str(version)
    except Exception:
        pass

    # 3) 最終フォールバック
    return "0.0.0"


__version__ = _read_version()
