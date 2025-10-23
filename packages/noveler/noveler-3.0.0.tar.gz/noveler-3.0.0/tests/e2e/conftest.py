#!/usr/bin/env python3
"""E2Eテスト用pytest設定

E2Eテスト実行時の共通設定、フィクスチャ、クリーンアップ機能
"""

import os
import shutil
import tempfile
import time
from pathlib import Path

import psutil
import pytest


pytestmark = pytest.mark.slow

# --- Minimal-progress print override for LLM runs ---
import os as _llm_os, sys as _llm_sys

_def_builtin_print = (lambda: (__builtins__['print'] if isinstance(__builtins__, dict) else __builtins__.print))()

def _llm_e2e_print(*args, **kwargs):
    """Route E2E progress prints to stderr, or suppress when LLM_SILENT_PROGRESS=1."""
    if (_llm_os.getenv("LLM_SILENT_PROGRESS") or "").strip().lower() in {"1","true","on","yes"}:
        return
    kwargs.setdefault('file', _llm_sys.stderr)
    return _def_builtin_print(*args, **kwargs)

# Shadow built-in print in this module only
print = _llm_e2e_print


class E2ETestEnvironment:
    """E2Eテスト環境管理"""

    def __init__(self) -> None:
        self.test_start_time = time.time()
        self.baseline_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        self.temp_dirs: dict[str, Path] = {}
        self.cleanup_callbacks = []

        # プロセス情報の記録
        self.process = psutil.Process()
        self.initial_cpu_times = self.process.cpu_times()
        self.initial_memory = self.process.memory_info()

        print(f"🧪 E2Eテスト環境初期化 - メモリ: {self.baseline_memory:.1f}MB")

    def create_isolated_temp_dir(self, prefix: str = "e2e_test_") -> Path:
        """分離されたテンポラリディレクトリの作成"""
        temp_dir = Path(tempfile.mkdtemp(prefix=prefix))
        self.temp_dirs[prefix] = temp_dir

        # 適切な権限設定
        temp_dir.chmod(0o755)

        print(f"📁 テスト用ディレクトリ作成: {temp_dir}")
        return temp_dir

    def register_cleanup(self, callback):
        """クリーンアップコールバックの登録"""
        self.cleanup_callbacks.append(callback)

    def cleanup(self):
        """全体クリーンアップの実行"""
        cleanup_start = time.time()

        # カスタムクリーンアップの実行
        for callback in self.cleanup_callbacks:
            try:
                callback()
            except Exception as e:
                print(f"⚠️ クリーンアップエラー: {e}")

        # テンポラリディレクトリの削除
        for temp_dir in self.temp_dirs.values():
            if temp_dir.exists():
                try:
                    shutil.rmtree(temp_dir)
                    print(f"🗑️ クリーンアップ完了: {temp_dir}")
                except Exception as e:
                    print(f"⚠️ ディレクトリ削除エラー: {temp_dir} - {e}")

        # パフォーマンス統計の出力
        self._output_performance_stats()

        cleanup_time = time.time() - cleanup_start
        print(f"✅ E2Eテスト環境クリーンアップ完了 ({cleanup_time:.2f}s)")

    def _output_performance_stats(self) -> None:
        """パフォーマンス統計の出力"""
        try:
            test_duration = time.time() - self.test_start_time
            final_memory = self.process.memory_info().rss / 1024 / 1024
            memory_increase = final_memory - self.baseline_memory

            final_cpu_times = self.process.cpu_times()
            cpu_user_time = final_cpu_times.user - self.initial_cpu_times.user
            cpu_system_time = final_cpu_times.system - self.initial_cpu_times.system

            print("📊 E2Eテストパフォーマンス統計:")
            print(f"   実行時間: {test_duration:.2f}秒")
            print(f"   メモリ使用: {self.baseline_memory:.1f}MB → {final_memory:.1f}MB (+{memory_increase:.1f}MB)")
            print(f"   CPU時間: User {cpu_user_time:.2f}s, System {cpu_system_time:.2f}s")

            # 異常値の警告
            if memory_increase > 100:
                print(f"⚠️ メモリ使用量が大幅に増加しています: +{memory_increase:.1f}MB")

            if test_duration > 300:  # 5分以上
                print(f"⚠️ テスト実行時間が長すぎます: {test_duration:.1f}秒")

        except Exception as e:
            print(f"⚠️ パフォーマンス統計出力エラー: {e}")


# グローバルテスト環境インスタンス
_test_environment = None


@pytest.fixture(scope="session", autouse=True)
def e2e_test_environment():
    """E2Eテスト環境のセッションレベルフィクスチャ"""
    global _test_environment

    # 環境の初期化
    _test_environment = E2ETestEnvironment()

    # 必要なディレクトリの作成
    project_root = Path(__file__).parent.parent.parent
    temp_dir = project_root / "temp"
    temp_dir.mkdir(exist_ok=True)

    (temp_dir / "cache").mkdir(exist_ok=True)
    (temp_dir / "logs").mkdir(exist_ok=True)
    (temp_dir / "reports").mkdir(exist_ok=True)

    # 環境変数の設定
    original_env = dict(os.environ)

    # テスト専用の環境変数
    os.environ["PYTEST_CURRENT_TEST"] = "e2e"
    os.environ["NOVEL_TEST_MODE"] = "true"
    os.environ["NOVEL_CACHE_DIR"] = str(temp_dir / "cache")
    os.environ["NOVEL_LOG_LEVEL"] = "WARNING"  # ログを抑制

    print("🌍 E2Eテスト環境設定完了")

    yield _test_environment

    # 環境変数の復元
    os.environ.clear()
    os.environ.update(original_env)

    # クリーンアップの実行
    _test_environment.cleanup()


@pytest.fixture
def isolated_temp_dir(e2e_test_environment):
    """テスト用の分離されたテンポラリディレクトリ"""
    test_name = os.environ.get("PYTEST_CURRENT_TEST", "unknown").split("::")[-1]
    safe_test_name = "".join(c if c.isalnum() else "_" for c in test_name)

    return e2e_test_environment.create_isolated_temp_dir(f"e2e_{safe_test_name}_")


    # 個別テスト後のクリーンアップは環境管理に委譲


@pytest.fixture
def project_root():
    """プロジェクトルートパスの取得"""
    return Path(__file__).parent.parent.parent




@pytest.fixture
def test_environment_vars():
    """テスト用環境変数の設定"""
    original_env = dict(os.environ)

    # プロジェクトルートを取得
    project_root = Path(__file__).parent.parent.parent
    src_path = project_root / "src"

    # テスト用環境変数
    test_env_vars = {
        "NOVEL_TEST_ISOLATION": "true",
        "NOVEL_DISABLE_CACHE": "true",
        "NOVEL_SUPPRESS_PROMPTS": "true",
        "NOVEL_LOG_FORMAT": "simple",
        "PYTHONPATH": f"{src_path}:{os.environ.get('PYTHONPATH', '')}"  # src/パス追加
    }

    os.environ.update(test_env_vars)

    yield test_env_vars

    # 環境変数の復元
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def performance_monitor():
    """パフォーマンス監視フィクスチャ"""
    class PerformanceMonitor:
        def __init__(self) -> None:
            self.start_time = time.time()
            self.process = psutil.Process()
            self.start_memory = self.process.memory_info().rss / 1024 / 1024
            self.measurements = []

        def measure(self, label: str):
            """パフォーマンス測定点の記録"""
            current_time = time.time()
            current_memory = self.process.memory_info().rss / 1024 / 1024

            measurement = {
                "label": label,
                "time": current_time - self.start_time,
                "memory": current_memory,
                "memory_delta": current_memory - self.start_memory
            }

            self.measurements.append(measurement)
            return measurement

        def get_summary(self):
            """パフォーマンス測定サマリー"""
            if not self.measurements:
                return {}

            total_time = self.measurements[-1]["time"]
            max_memory = max(m["memory"] for m in self.measurements)
            total_memory_delta = self.measurements[-1]["memory_delta"]

            return {
                "total_time": total_time,
                "max_memory": max_memory,
                "total_memory_delta": total_memory_delta,
                "measurement_count": len(self.measurements)
            }

    monitor = PerformanceMonitor()
    yield monitor

    # テスト終了時にサマリーを出力
    summary = monitor.get_summary()
    if summary:
        print(f"⏱️ テストパフォーマンス: "
              f"{summary['total_time']:.2f}s, "
              f"最大メモリ: {summary['max_memory']:.1f}MB, "
              f"メモリ増加: {summary['total_memory_delta']:+.1f}MB")


# pytest フック関数

def pytest_configure(config):
    """pytest設定時の処理"""
    print("🔧 E2Eテスト設定の初期化...")

    # カスタムマーカーの登録
    config.addinivalue_line("markers", "e2e_critical: 重要なE2Eテスト")
    config.addinivalue_line("markers", "e2e_smoke: スモークテスト用E2E")
    config.addinivalue_line("markers", "e2e_regression: 回帰テスト用E2E")


def pytest_sessionstart(session):
    """テストセッション開始時の処理"""
    print("🚀 E2Eテストセッション開始")

    # システム情報の出力
    print(f"🖥️ システム情報: CPU {psutil.cpu_count()}コア, "
          f"メモリ {psutil.virtual_memory().total / 1024 / 1024 / 1024:.1f}GB")


def pytest_sessionfinish(session, exitstatus):
    """テストセッション終了時の処理"""
    print(f"🏁 E2Eテストセッション終了 (終了コード: {exitstatus})")


def pytest_runtest_setup(item):
    """各テスト実行前の処理"""
    # テスト名を環境変数に設定
    os.environ["PYTEST_CURRENT_TEST"] = item.nodeid


def pytest_runtest_teardown(item, nextitem):
    """各テスト実行後の処理"""
    # ガベージコレクション実行（メモリ解放）
    import gc
    gc.collect()


def pytest_collection_modifyitems(config, items):
    """テスト収集後の処理"""

    # E2Eテストの実行順序を最適化
    priority_markers = {
        "e2e_smoke": 1,      # スモークテストを最初に
        "e2e_critical": 2,   # 重要テストを次に
        "workflow": 3,       # ワークフローテスト
        "quality": 4,        # 品質テスト
        "performance": 5,    # パフォーマンステスト（最後）
        "stress": 6          # ストレステスト（最後）
    }

    def get_priority(item):
        for marker, priority in priority_markers.items():
            if item.get_closest_marker(marker):
                return priority
        return 10  # デフォルト優先度

    # 優先度順でソート
    items.sort(key=get_priority)

    skipped_count = sum(1 for item in items if item.get_closest_marker("skip"))
    active_count = len(items) - skipped_count

    print(f"📋 E2Eテスト設定完了: {active_count}テスト有効, {skipped_count}テスト無効化 (CLI廃止のため)")


# エラーハンドリング

def pytest_exception_interact(node, call, report):
    """例外発生時の処理"""
    if report.failed:
        # テスト失敗時の詳細情報出力
        test_name = node.name
        failure_info = {
            "test": test_name,
            "stage": call.when,
            "duration": getattr(call, "duration", 0),
            "memory": psutil.Process().memory_info().rss / 1024 / 1024
        }

        print(f"❌ テスト失敗詳細: {failure_info}")


# リソース制限とタイムアウト

def pytest_runtest_protocol(item, nextitem):
    """テスト実行プロトコル"""
    # テストごとのリソース制限設定
    try:
        import resource

        # メモリ制限（1GB）
        resource.setrlimit(resource.RLIMIT_AS, (1024 * 1024 * 1024, resource.RLIM_INFINITY))

        # CPU時間制限（10分）
        resource.setrlimit(resource.RLIMIT_CPU, (600, resource.RLIM_INFINITY))

    except ImportError:
        # Windowsでは resource モジュールが利用できない
        pass
    except Exception as e:
        print(f"⚠️ リソース制限設定エラー: {e}")



# テスト情報の収集

@pytest.fixture(autouse=True)
def test_metadata(request):
    """テストメタデータの収集"""
    test_info = {
        "name": request.node.name,
        "file": str(request.node.fspath),
        "markers": [marker.name for marker in request.node.iter_markers()],
        "start_time": time.time()
    }

    yield test_info

    # テスト終了時の情報更新
    test_info["duration"] = time.time() - test_info["start_time"]
    test_info["status"] = "completed"

    # 長時間実行の警告
    if test_info["duration"] > 60:  # 1分以上
        print(f"⏰ 長時間実行テスト: {test_info['name']} ({test_info['duration']:.1f}s)")


# カスタムアサーション

def pytest_assertrepr_compare(config, op, left, right):
    """カスタムアサーション表示"""
    if op == "==" and isinstance(left, Path) and isinstance(right, Path):
        return [
            "パス比較失敗:",
            f"  左辺: {left}",
            f"  右辺: {right}",
            f"  左辺存在: {left.exists()}",
            f"  右辺存在: {right.exists()}"
        ]
    return None
