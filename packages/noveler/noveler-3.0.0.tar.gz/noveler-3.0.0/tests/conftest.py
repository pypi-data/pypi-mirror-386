#!/usr/bin/env python3
"""統合pytest設定ファイル (pytest 8.x最適化)
全テストカテゴリ（unit/integration/e2e/architecture/contracts）での共通設定
DDD準拠・包括的テスト環境対応
src/noveler/tests とルートtests/の統合版
"""
import sys
import tempfile
from pathlib import Path
import os
# -----------------------------------------------------------------
# Compatibility shim: support Path.Path("w").open(encoding=...) pattern
# Several legacy tests and utilities rely on this chainable helper.
# This adds a lightweight proxy so that Path objects accept a .Path(...) call
# that returns an object exposing .open(...) with default mode/encoding.
# -----------------------------------------------------------------
try:
    import pathlib as _pathlib
    def _compat_Path(self, mode: str | None = None, encoding: str | None = None, **default_kwargs):
        class _OpenProxy:
            def __init__(self, p: _pathlib.Path, m: str | None, enc: str | None, dkw: dict):
                self._p = p
                self._m = m
                self._enc = enc
                self._dkw = dict(dkw) if dkw else {}
            def open(self, mode: str | None = None, encoding: str | None = None, **kwargs):
                use_mode = mode or self._m or "r"
                use_kwargs = {**self._dkw, **kwargs}
                if encoding is None:
                    encoding = self._enc
                if encoding is not None:
                    use_kwargs["encoding"] = encoding
                return self._p.open(use_mode, **use_kwargs)
        return _OpenProxy(self, mode, encoding, default_kwargs)
    for _cls_name in ("Path", "PosixPath", "WindowsPath"):
        _cls = getattr(_pathlib, _cls_name, None)
        if _cls is not None and not hasattr(_cls, "Path"):
            setattr(_cls, "Path", _compat_Path)
except Exception:
    # Best-effort compatibility; ignore if environment disallows monkeypatching
    pass
import pytest
import yaml
pytest_plugins = ("pytester",)
# -----------------------------------------------------------------
# Soft hint: suggest unified runner when called via raw pytest
# -----------------------------------------------------------------
def pytest_sessionstart(session):
    """Print a one-line hint when tests are invoked bypassing the unified runner.
    This is a soft warning and does not affect test outcomes.
    """
    import os as _os, sys as _sys
    if (_os.getenv("LLM_TEST_RUNNER") or "").strip().lower() in {"1", "true", "yes", "on"}:
        return
    try:
        _sys.stderr.write("[hint] テストは scripts/run_pytest.py または `make test` を使うと環境/出力が統一されます\n")
    except Exception:
        pass
from tests._utils.slow_marker_utils import extract_slow_marker_tokens
# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
src_root = project_root / "src"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_root))
# -----------------------------------------------------------------
# MCP stdout ガードをテスト全体で有効化
# - stdoutはMCP専用、ログはstderrへ（MCP_STDIO_SAFE=1）
# - SDK出力以外のstdout書き込みを検出（MCP_STRICT_STDOUT=1）
# -----------------------------------------------------------------
@pytest.fixture(scope="session", autouse=True)
def enable_mcp_stdout_guard():
    import os as _os
    saved = {k: _os.environ.get(k) for k in ("MCP_STRICT_STDOUT", "MCP_STDIO_SAFE", "PYTHONUNBUFFERED")}
    _os.environ["MCP_STRICT_STDOUT"] = "1"
    # Ensure server-side consoles default to stderr to avoid protocol noise
    _os.environ.setdefault("MCP_STDIO_SAFE", "1")
    _os.environ.setdefault("PYTHONUNBUFFERED", "1")
    try:
        yield
    finally:
        for k, v in saved.items():
            if v is None:
                _os.environ.pop(k, None)
            else:
                _os.environ[k] = v
# -----------------------------------------------------------------
# AsyncIO compatibility for Python 3.11+
# Many legacy calls use asyncio.get_event_loop() in sync context.
# Ensure a default loop is present on MainThread during tests.
# -----------------------------------------------------------------
@pytest.fixture(scope="session", autouse=True)
def ensure_default_event_loop():
    import asyncio as _asyncio
    try:
        _asyncio.get_running_loop()
    except RuntimeError:
        _asyncio.set_event_loop(_asyncio.new_event_loop())
    yield


# -----------------------------------------------------------------
# Reset shared path-service cache at session start to avoid cross-test
# contamination between projects/roots (flake prevention)
# -----------------------------------------------------------------
@pytest.fixture(scope="session", autouse=True)
def _reset_common_path_service_cache():
    try:
        from noveler.presentation.shared.shared_utilities import (
            reset_common_path_service as _reset_cps,
        )
        _reset_cps()
    except Exception:
        # Not fatal in environments without presentation layer available
        pass
    yield
# 遅延インポートでcircular import回避
def get_path_service():
    """パスサービス取得（遅延インポート）"""
    try:
        from noveler.presentation.shared.shared_utilities import get_common_path_service
        return get_common_path_service()
    except ImportError:
        # フォールバック: 基本的なパス操作
        class FallbackPathService:
            @property
            def project_root(self):
                return project_root
            def get_manuscript_dir(self):
                # 設定ベースのパス取得を試行
                try:
                    from noveler.infrastructure.factories.configuration_service_factory import get_configuration_manager
                    config_manager = get_configuration_manager()
                    project_config = config_manager.get_project_configuration(project_root)
                    if project_config and "paths" in project_config:
                        manuscripts_path = project_config["paths"].get("manuscripts", "40_原稿")
                    else:
                        manuscripts_path = "40_原稿"  # デフォルト
                    return project_root / f"temp/test_data/{manuscripts_path}"
                except Exception:
                    # フォールバックはデフォルト構造
                    return project_root / "temp/test_data/40_原稿"
            def get_management_dir(self):
                return project_root / "50_管理資料"
            def get_plots_dir(self):
                return project_root / "50_管理資料" / "plots"
            def get_settings_dir(self):
                return project_root / "config"
            def get_management_dir_1(self):
                return project_root / "50_管理資料"
            @property
            def manuscript_dir(self):
                # 設定ベースのパス取得を試行
                try:
                    from noveler.infrastructure.factories.configuration_service_factory import get_configuration_manager
                    config_manager = get_configuration_manager()
                    project_config = config_manager.get_project_configuration(project_root)
                    if project_config and "paths" in project_config:
                        manuscripts_path = project_config["paths"].get("manuscripts", "40_原稿")
                    else:
                        manuscripts_path = "40_原稿"  # デフォルト
                    return project_root / f"temp/test_data/{manuscripts_path}"
                except Exception:
                    # フォールバックはデフォルト構造
                    return project_root / "temp/test_data/40_原稿"
            @property
            def config_dir(self):
                return project_root / "config"
        return FallbackPathService()
def get_test_manuscripts_path(project_root=None):
    """プロジェクト設定に基づくテストデータのmanuscriptsパス取得"""
    try:
        if project_root:
            from noveler.infrastructure.ai_integration.repositories.yaml_project_config_repository import (
                YamlProjectConfigRepository,
            )
            from pathlib import Path
            import os
            repository = YamlProjectConfigRepository(Path(project_root))
            path_config = repository.get_path_config(Path(project_root))
            manuscripts_path = path_config.get("manuscripts", "40_原稿")
            return f"temp/test_data/{manuscripts_path}"
        # デフォルトまたはフォールバック
        return "temp/test_data/40_原稿"
    except Exception:
        # フォールバック
        return "temp/test_data/40_原稿"
def get_test_management_path(project_root=None):
    """プロジェクト設定に基づくテストデータのmanagementパス取得"""
    try:
        if project_root:
            from noveler.infrastructure.ai_integration.repositories.yaml_project_config_repository import (
                YamlProjectConfigRepository,
            )
            from pathlib import Path
            import os
            repository = YamlProjectConfigRepository(Path(project_root))
            path_config = repository.get_path_config(Path(project_root))
            management_path = path_config.get("management", "50_管理資料")
            return f"temp/test_data/{management_path}"
        # デフォルトまたはフォールバック
        return "temp/test_data/50_管理資料"
    except Exception:
        # フォールバック
        return "temp/test_data/50_管理資料"
def get_cleanup_manager():
    """クリーンアップマネージャー取得（遅延インポート）"""
    try:
        from noveler.infrastructure.shared.test_cleanup_manager import TestCleanupManager
        return TestCleanupManager(project_root)
    except ImportError:
        # フォールバック: 基本クリーンアップ
        class FallbackCleanupManager:
            def __init__(self, project_root=None):
                self.project_root = project_root or Path.cwd()
            def cleanup_test_files(self, test_dir):
                if test_dir.exists():
                    import shutil
                    shutil.rmtree(test_dir)
            def cleanup_test_artifacts(self, dry_run=False):
                return {
                    "files_deleted": [],
                    "dirs_deleted": [],
                    "errors": []
                }
        return FallbackCleanupManager(project_root)
# -----------------------------------------------------------------
# Sessionレベルフィクスチャ(重いI/O操作を一度だけ実行)
# -----------------------------------------------------------------
@pytest.fixture(scope="session")
def temp_project_dir():
    """テスト用一時ディレクトリ(sessionスコープ)"""
    path_service = get_path_service()
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        # 基本ディレクトリ構造を作成
        try:
            (temp_path / str(path_service.get_manuscript_dir())).mkdir(parents=True, exist_ok=True)
            (temp_path / str(path_service.get_management_dir())).mkdir(parents=True, exist_ok=True)
            (temp_path / str(path_service.get_plots_dir())).mkdir(parents=True, exist_ok=True)
            (temp_path / str(path_service.get_settings_dir())).mkdir(parents=True, exist_ok=True)
        except AttributeError:
            # フォールバック用ディレクトリ作成
            manuscripts_path = get_test_manuscripts_path()
            (temp_path / manuscripts_path).mkdir(parents=True, exist_ok=True)
            (temp_path / "50_管理資料").mkdir(exist_ok=True)
            (temp_path / "50_管理資料" / "plots").mkdir(parents=True, exist_ok=True)
            (temp_path / "config").mkdir(exist_ok=True)
        # 追加ディレクトリ（従来のtests/conftest.pyとの互換性）
        (temp_path / "plots").mkdir(exist_ok=True)
        (temp_path / "quality").mkdir(exist_ok=True)
        # プロジェクト設定ファイル作成（src/noveler/tests/conftest.py機能）
        project_config = {
            "project": {
                "title": "テストプロジェクト",
                "author": "テストユーザー",
                "genre": "ファンタジー",
                "ncode": "N0000XX",
            },
        }
        with open(temp_path / "プロジェクト設定.yaml", "w", encoding="utf-8") as f:
            yaml.dump(project_config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        yield temp_path
@pytest.fixture(scope="session")
def default_project_settings() -> dict[str, object]:
    """デフォルトプロジェクト設定(sessionスコープ)"""
    return {
        "project": {
            "title": "テストプロジェクト",
            "author": "テストユーザー",
            "genre": "ファンタジー",
            "target_audience": "一般",
            "writing_status": "連載中",
            "ncode": "N0000XX",
        },
        "quality": {
            "min_score": 70,
            "target_score": 85,
            "max_warnings": 5,
        },
    }
@pytest.fixture(scope="session")
def test_manuscript_file(temp_project_dir):
    """テスト用原稿ファイル作成(sessionスコープ)"""
    manuscripts_path = get_test_manuscripts_path(temp_project_dir)
    manuscript_dir = temp_project_dir / manuscripts_path
    manuscript_file = manuscript_dir / "第001話_テスト物語.md"
    test_content = """# 第1話 テスト物語
これはテスト用の原稿です。
文章の品質チェックをテストするための内容を含んでいます。
## シーン1
主人公が冒険を始めます。
長い文章でもテストできるように、複数の文を含む段落を用意しています。
## シーン2
展開部分での出来事。
"""
    manuscript_file.write_text(test_content, encoding="utf-8")
    return manuscript_file
@pytest.fixture(scope="session")
def test_config_file(temp_project_dir):
    """テスト用設定ファイル作成(sessionスコープ)"""
    config_dir = temp_project_dir / "config"
    config_file = config_dir / "novel_config.yaml"
    test_config = {
        "system": {
            "project_name": "test_novel",
            "author": "テストユーザー"
        },
        "paths": {
            "manuscripts": get_test_manuscripts_path().replace("temp/test_data/", ""),
            "plots": "plots",
            "quality": "quality"
        },
        "defaults": {
            "episode": {
                "target_words": 3000
            }
        }
    }
    config_file.write_text(yaml.dump(test_config, allow_unicode=True), encoding="utf-8")
    return config_file
# -----------------------------------------------------------------
# Packageレベルフィクスチャ(テストパッケージ単位で再利用)
# -----------------------------------------------------------------
@pytest.fixture(scope="package")
def sample_episode_content() -> str:
    """サンプルエピソードコンテンツ(packageスコープ)"""
    return """
# 第001話 テストタイトル
 朝の日差しが部屋に差し込んでくる。私はベッドから身を起こし、大きく伸びをした。
「おはよう、世界」
 今日も新しい一日の始まりだ。窓の外には青い空が広がっている。雲がゆっくりと流れていくのを見ていると、心が落ち着いてくる。
 私はキッチンに向かい、コーヒーを淹れた。香ばしい香りが部屋全体に広がっていく。この習慣を始めてから、毎日が少しだけ特別に感じられるようになった。
 マグカップを手に取り、バルコニーに出る。温かい風が頰を撫でていく。遠くの山々が朝霧に包まれて、幻想的な美しさを醸し出している。
 この平安な朝が、いつまでも続けばいいのに。そんなことを考えながら、私はコーヒーを一口飲んだ。
""".strip()
@pytest.fixture(scope="package")
def sample_yaml_metadata() -> dict[str, object]:
    """サンプルYAMLメタデータ(packageスコープ)"""
    return {
        "episode": {
            "number": 1,
            "title": "テストタイトル",
            "status": "draft",
            "target_words": 3000,
            "created_at": "2025-07-16T10:00:00",
            "tags": ["ファンタジー", "日常"],
        },
        "quality": {
            "last_checked": None,
            "score": None,
            "issues": [],
        },
    }
# -----------------------------------------------------------------
# Functionレベルフィクスチャ(各テストで独立したリソース)
# -----------------------------------------------------------------
@pytest.fixture
def isolated_temp_dir():
    """テスト毎に独立した一時ディレクトリ"""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        yield temp_path
@pytest.fixture
def mock_episode_file(isolated_temp_dir):
    """テスト用エピソードファイル作成"""
    manuscripts_path = get_test_manuscripts_path()
    manuscript_dir = isolated_temp_dir / manuscripts_path
    manuscript_dir.mkdir(parents=True, exist_ok=True)
    episode_file = manuscript_dir / "第001話_テストエピソード.md"
    episode_content = """# 第1話 テストエピソード
テスト用のエピソード内容です。
品質チェック機能をテストするため、様々な文章パターンを含んでいます。
長い文章のテストのために、意図的に複数の要素を含む複雑な構造の文章を作成して、読みやすさや文法の検証ができるようにしています。
短い文。
## 会話シーン
「こんにちは」と彼は言った。
「はい、こんにちは」と彼女は答えた。
"""
    episode_file.write_text(episode_content, encoding="utf-8")
    return episode_file
@pytest.fixture
def cleanup_test_files():
    """テスト後のファイルクリーンアップ"""
    created_files = []
    def track_file(file_path):
        created_files.append(Path(file_path))
    yield track_file
    # テスト後のクリーンアップ
    cleanup_manager = get_cleanup_manager()
    for file_path in created_files:
        try:
            if file_path.is_dir():
                cleanup_manager.cleanup_test_files(file_path)
            elif file_path.exists():
                file_path.unlink()
        except Exception:
            # クリーンアップエラーは無視（テスト結果に影響させない）
            pass
# -----------------------------------------------------------------
# パフォーマンス測定用フィクスチャ
# -----------------------------------------------------------------
@pytest.fixture
def benchmark_episode_content() -> str:
    """ベンチマーク用エピソードコンテンツ"""
    # 3000文字程度のコンテンツを生成
    base_text = "これはベンチマーク用のテストテキストです。"
    return base_text * 100  # 約 3000文字
# -----------------------------------------------------------------
# E2Eテスト専用フィクスチャ
# -----------------------------------------------------------------
@pytest.fixture
def e2e_test_environment(temp_project_dir, test_config_file, test_manuscript_file):
    """E2Eテスト用環境セットアップ"""
    return {
        "project_root": temp_project_dir,
        "config_file": test_config_file,
        "manuscript_file": test_manuscript_file,
        "manuscript_dir": temp_project_dir / get_test_manuscripts_path(temp_project_dir)
    }
# -----------------------------------------------------------------
# Architecture/Integration テスト専用フィクスチャ
# -----------------------------------------------------------------
@pytest.fixture
def mock_dependencies():
    """アーキテクチャテスト用のモック依存関係"""
    from unittest.mock import Mock
    return {
        "logger": Mock(),
        "path_service": Mock(),
        "repository": Mock(),
        "use_case": Mock()
    }
# -----------------------------------------------------------------
# テストマーカー用フック
# -----------------------------------------------------------------
def pytest_configure(config: pytest.Config) -> None:
    """pytest設定フック(pytest 8.x最適化) - 高速化版
    パフォーマンステストの自動スキップ、
    非同期テストの自動設定等を実装。
    """
    # MCP軽量出力を既定ON（B20準拠）
    os.environ.setdefault("MCP_LIGHTWEIGHT_DEFAULT", "1")
    # 継続CI環境でのパフォーマンステストスキップ
    if config.getoption("--maxfail") == 1:
        config.addinivalue_line("markers", "performance: skip in fail-fast mode")
    # マーカー一括登録（高速化）
    markers = [
        "spec(id): 仕様書IDとの紐付け",
        "requirement(id): 要件IDとの紐付け",
        "spec(spec_id): テスト仕様ID",
        "slow: 実行時間の長いテスト",
        "integration: 統合テスト",
        "e2e: E2Eテスト",
        "unit: ユニットテスト",
        "architecture: アーキテクチャテスト",
        "contracts: コントラクトテスト",
        "plot_episode: プロットエピソード領域のテスト",
        "quality_domain: 品質ドメイン関連のテスト",
        "vo_smoke: 値オブジェクトのスモークテスト"
    ]
    for marker in markers:
        config.addinivalue_line("markers", marker)
def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """テストアイテムの動的修正(pytest 8.x最適化) - 高速化版
    - fail-fastモードではパフォーマンステストをスキップ
    - 非同期テストに自動マーカー付与
    - 文字列操作を最適化
    """
    # マーカーを事前作成（キャッシュ効果）
    skip_performance = pytest.mark.skip(reason="Performance tests skipped in fail-fast mode")
    # maxfailオプションを一度だけチェック
    should_skip_performance = config.getoption("--maxfail") == 1
    # 文字列チェック用の高速化
    slow_keywords = {"slow", "heavy", "stress", "benchmark", "performance"}
    for item in items:
        # パフォーマンステストの条件付きスキップ
        if should_skip_performance and "performance" in item.keywords:
            item.add_marker(skip_performance)
        # asyncテストの自動認識
        if "async" in item.name or item.get_closest_marker("asyncio"):
            item.add_marker(pytest.mark.asyncio)
        # ファイルパスベースの自動マーキング（最適化: 一度の文字列変換）
        fspath_str = str(item.fspath)
        if "e2e" in fspath_str:
            item.add_marker(pytest.mark.e2e)
            item.add_marker(pytest.mark.slow)
        elif "integration" in fspath_str:
            item.add_marker(pytest.mark.integration)
        elif "architecture" in fspath_str:
            item.add_marker(pytest.mark.architecture)
        elif "contracts" in fspath_str:
            item.add_marker(pytest.mark.contracts)
        elif "unit" in fspath_str:
            item.add_marker(pytest.mark.unit)
        # 実行時間ベースのマーキング（最適化: set intersection）
        item_words = extract_slow_marker_tokens(item.name)
        if item_words & slow_keywords:
            item.add_marker(pytest.mark.slow)
def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """テストセッション終了時の自動クリーンアップ
    テスト実行で生成された一時ファイル・サンプルファイルを自動削除。
    """
    # Fast cleanup mode for LLM runs: skip heavy post-session cleanup if enabled
    try:
        fast_flag = os.environ.get("LLM_FAST_CLEANUP", "")
        _fast = fast_flag.strip().lower() in {"1", "true", "on", "yes"}
    except Exception:
        _fast = False

    if _fast and exitstatus == 0:
        # Skip heavy cleanup to speed up LLM-facing runs
        return

    try:
        # テスト失敗時はクリーンアップしない(デバッグ用にファイルを残す)
        if exitstatus != 0:
            print()
            print("⚠️ テストに失敗したため、デバッグ用にテストファイルを保持します")
            print("   手動でクリーンアップする場合: python scripts/tools/test_cleanup_manager.py")
            return
        # 自動クリーンアップ実行
        print()
        print("🧹 テスト後クリーンアップを実行中...")
        cleanup_manager = get_cleanup_manager()
        result = cleanup_manager.cleanup_test_artifacts(dry_run=False)
        if result["files_deleted"] or result["dirs_deleted"]:
            print(
                f"✅ クリーンアップ完了: {len(result['files_deleted'])} ファイル, {len(result['dirs_deleted'])} ディレクトリを削除"
            )
        else:
            print("✅ クリーンアップ対象なし")
        if result["errors"]:
            print(f"⚠️ {len(result['errors'])} 件のエラーが発生しました")
    except Exception as e:
        print(f"⚠️ 自動クリーンアップでエラーが発生: {e}")
        print("   手動でクリーンアップしてください: python scripts/tools/test_cleanup_manager.py")
# -----------------------------------------------------------------
# テスト実行時フック
# -----------------------------------------------------------------
@pytest.fixture(autouse=True)
def setup_test_logging():
    """各テストでのログ設定"""
    from noveler.infrastructure.logging.unified_logger import configure_logging, LogFormat
    configure_logging(preset="development", console_format=LogFormat.RICH)
    yield
    # テスト後はロギング設定を初期化
    from noveler.infrastructure.logging.unified_logger import configure_logging
    configure_logging(preset="development")


# -----------------------------------------------------------------
# Fail-only NDJSON streaming (opt-in): write a line when a test phase fails
# Enable with: LLM_REPORT_STREAM_FAIL=1
# -----------------------------------------------------------------


# -----------------------------------------------------------------
# Fail-only NDJSON streaming (opt-in): write per-worker lines on phase failure
# Enable with: LLM_REPORT_STREAM_FAIL=1
# -----------------------------------------------------------------

import json as _json
from datetime import datetime as _dt
from pathlib import Path as _Path


def _llm_fail_enabled() -> bool:
    try:
        import os as _os
        return (_os.getenv("LLM_REPORT_STREAM_FAIL") or "").strip().lower() in {"1", "true", "on", "yes"}
    except Exception:
        return False


def _llm_worker_id() -> str:
    try:
        import os as _os
        return _os.getenv("PYTEST_XDIST_WORKER", "main")
    except Exception:
        return "main"


def _llm_fail_path() -> _Path:
    base = _Path("reports") / "stream"
    base.mkdir(parents=True, exist_ok=True)
    return base / f"llm_fail_{_llm_worker_id()}.ndjson"


def pytest_runtest_logreport(report):
    if not _llm_fail_enabled():
        return
    try:
        outcome = getattr(report, "outcome", "") or ""
        if outcome not in {"failed", "error", "crashed"}:
            return
        nodeid = getattr(report, "nodeid", "")
        when = getattr(report, "when", "")
        duration = float(getattr(report, "duration", 0.0) or 0.0)
        payload = {
            "ts": _dt.utcnow().isoformat(timespec="milliseconds") + "Z",
            "event": "test_phase",
            "test_id": nodeid,
            "phase": when,
            "outcome": outcome,
            "duration_s": duration,
            "worker_id": _llm_worker_id(),
        }
        path = _llm_fail_path()
        with path.open("a", encoding="utf-8") as f:
            f.write(_json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        return


def _llm_merge_fail_logs() -> None:
    if not _llm_fail_enabled():
        return
    base = _Path("reports") / "stream"
    if not base.exists():
        return
    files = sorted(base.glob("llm_fail_*.ndjson"))
    if not files:
        return
    # Merge and compute summary
    merged = _Path("reports") / "llm_fail.ndjson"
    failed = error = crashed = 0
    workers = set()
    with merged.open("w", encoding="utf-8") as out:
        for f in files:
            try:
                workers.add(f.stem.split("_")[-1])
                for line in f.read_text(encoding="utf-8").splitlines():
                    if not line.strip():
                        continue
                    out.write(line + "\n")
                    try:
                        rec = _json.loads(line)
                        if rec.get("outcome") == "failed":
                            failed += 1
                        elif rec.get("outcome") == "error":
                            error += 1
                        elif rec.get("outcome") == "crashed":
                            crashed += 1
                    except Exception:
                        continue
            except Exception:
                continue
        summary = {
            "ts": _dt.utcnow().isoformat(timespec="milliseconds") + "Z",
            "event": "session_summary",
            "final_outcome": "failed" if (failed or error or crashed) else "passed",
            "failed_events": failed,
            "error_events": error,
            "crashed_events": crashed,
            "workers": sorted(workers),
            "files": len(files),
        }
        out.write(_json.dumps(summary, ensure_ascii=False) + "\n")
