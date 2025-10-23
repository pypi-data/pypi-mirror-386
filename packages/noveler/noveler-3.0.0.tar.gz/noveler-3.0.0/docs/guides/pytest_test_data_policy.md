# pytestテストデータ運用ガイド

## 目的
- `temp\test_data` を pytest 実行時の一時データ専用ベースとして固定し、テスト終了後に残骸を残さない。
- テスト間のデータ衝突や、失敗後の復旧コストを最小化し、CI／ローカルの状態を揃える。
- 既存の起動フックを尊重しつつ、追加実装を最小限に留める。

## 適用範囲
- `bin/test`／`make test`／`pytest` による全テスト。
- `tests/` 配下のユニット／統合／E2E テストおよび付随スクリプト。
- `temp\test_data` に依存する補助 CLI・ユーティリティ。

## 方針概要
- `pyproject.toml` の pytest 設定に `--basetemp=temp/test_data` を必須で追加し、pytest（>=8.0）の `tmp_path` / `tmp_path_factory` が必ず同一ベースを使うよう統一する。
- 既存の `tests/conftest.py` 内 `pytest_sessionstart` / `pytest_sessionfinish` を拡張し、テスト開始前の初期化と終了後の残骸検知を差し込む。
- 各テストでは関数スコープの `test_data_dir` フィクスチャを受け取り、`temp\test_data` の直参照をやめる。
- プロダクションコードが固定パスを内部参照している場合は、フィクスチャでパスを注入するか `monkeypatch` で差し替える。
- CI では残骸検知に失敗した場合にテストを失敗させ、運用上の抜け漏れを早期発見する。

## 実装手順
1. **ベースディレクトリの明示化**  
   - `tests/conftest.py` 冒頭で `project_root = Path(__file__).parent.parent` を利用し、`TEST_DATA_ROOT = project_root / "temp/test_data"` を定義する。  
   - 既存のパスサービスを併用する場合は、ヘルパー内で `path_service.get_temp_dir() / "test_data"` を解決させる。
2. **Pytest 設定の統一**  
   - `pyproject.toml` → `[tool.pytest.ini_options].addopts` に `--basetemp=temp/test_data` を追加する（pytest>=8.0 前提）。  
   - ローカルで直接 `pytest` を叩く際も、この設定が常に読み込まれるよう管理する。
3. **セッションフックの拡張**  
   - 既存の `pytest_sessionstart` の先頭または末尾に初期化ヘルパーを呼び出す行を追加する。  
   - `pytest_sessionfinish` の早期 `return` より前に残骸検知を挿入し、成功時のみ検証する。
4. **フィクスチャ整備とテスト移行**  
   - `tmp_path_factory.mktemp("case", numbered=True)` を利用した `test_data_dir` フィクスチャを定義し、各テストで依存注入する。  
   - `temp/test_data` を文字列で組み立てている箇所は、フィクスチャ経由に置き換え、共通シードは `tests/fixtures/` からコピーする。
5. **CI／運用確認**  
   - `bin/test` 実行後に `temp/test_data` が空であることを確認し、残骸検知失敗時は原因テストの特定と修正を行う。  
   - TODO／運用メモ等で手順を共有し、継続的にモニタリングする。

## 実装スニペット（既存フックに追記する例）
```python
# tests/conftest.py 抜粋
from __future__ import annotations

import shutil
from pathlib import Path
import pytest

project_root = Path(__file__).parent.parent
TEST_DATA_ROOT = project_root / "temp/test_data"

def _ensure_empty_test_data_root() -> None:
    """temp/test_data を初期化する（存在すれば削除して再作成）。"""
    if TEST_DATA_ROOT.exists():
        shutil.rmtree(TEST_DATA_ROOT, ignore_errors=True)
    TEST_DATA_ROOT.mkdir(parents=True, exist_ok=True)

def _assert_test_data_clean() -> None:
    leftovers = [p for p in TEST_DATA_ROOT.iterdir()] if TEST_DATA_ROOT.exists() else []
    if leftovers:
        joined = ", ".join(p.name for p in leftovers[:5])
        pytest.fail(f"leftover test data detected under {TEST_DATA_ROOT}: {joined}")

# --- 既存の pytest_sessionstart 内で呼び出す ---
def pytest_sessionstart(session):
    ...
    _ensure_empty_test_data_root()  # 追加行
    ...

# --- 既存の pytest_sessionfinish 内で呼び出す ---
def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    ...
    if exitstatus == 0:
        _assert_test_data_clean()  # 追加行（return より前に配置）
    ...

@pytest.fixture(scope="function")
def test_data_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    TEST_DATA_ROOT.mkdir(parents=True, exist_ok=True)
    tmp = tmp_path_factory.mktemp("case", numbered=True)
    try:
        yield tmp
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
```

> 補足: フック内には try/except や早期 return が既に存在するため、追加行の位置を誤ると実行されません。`return` より前、例外ハンドリング外で呼び出してください。  
> `tmp_path_factory.mktemp` は `--basetemp` の設定に従って `temp/test_data` 配下へディレクトリを生成します。設定を付け忘れないよう `pyproject.toml` に固定することが重要です。

## 運用チェックリスト
- `tests/` 内で `temp/test_data` を直接 `Path` 化している箇所が残っていないか。
- `pytest_sessionstart` / `pytest_sessionfinish` の追加処理が既存のハンドリングを壊していないか。
- Windows／WSL／macOS のパス差異を吸収するために `Path` API で統一しているか。
- `bin/test` 実行後に残骸検知の結果が CI／ローカルで共有されているか（TODO やログなど）。

## よくある落とし穴
- フィクスチャを介さず `temp/test_data` 直下へファイルを書き込むと、クリーンアップ対象から漏れ残骸が残る。
- サンプルデータを原本のまま編集すると、別テストで予期しない差分が発生する。
- `pytest.fail` を使用せず `print` やログのみで通知すると、CI で検知できない。
- `tmp_path_factory.mktemp` の `numbered` を `False` にすると並列実行時に衝突しやすくなる。

## 導入後のフォロー
- 初週は CI の実行ログで `leftover test data` アラートが出ていないかを確認する。
- 残骸検知が発生した場合は対象テスト名と生成パスをレポート（例: `reports/llm_summary.txt`）に記載し、根本原因を共有する。
- `temp/test_data` の扱いを変更する場合は本ガイドを更新し、必要に応じて CHANGELOG にも記載する。
