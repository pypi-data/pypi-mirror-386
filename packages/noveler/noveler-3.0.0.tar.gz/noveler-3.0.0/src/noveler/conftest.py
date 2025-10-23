#!/usr/bin/env python3
"""pytest設定ファイル - 基本版

基本的なフィクスチャとテスト設定
"""

import shutil
import sys
import tempfile
from pathlib import Path

try:
    from collections.abc import Callable, Generator
except ImportError:
    from collections.abc import Callable, Generator
from typing import Any

import pytest

from noveler.infrastructure.logging.unified_logger import configure_logging, LogFormat

# scriptsディレクトリをPythonパスに追加
sys.path.insert(0, str(Path(__file__).parent))


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """各テスト用の一時ディレクトリ"""
    temp_dir = tempfile.mkdtemp(prefix="novel_test_")
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_project_config() -> dict[str, Any]:
    """テスト用プロジェクト設定"""
    return {
        "title": "テスト小説",
        "ncode": "n1234567890",
        "author": "テスト作者",
        "genre": "ファンタジー",
        "start_date": "2024-01-01",
        "status": "連載中",
    }


@pytest.fixture
def sample_episode_yaml() -> dict[str, Any]:
    """テスト用話数管理YAML"""
    return {
        "episodes": [
            {
                "id": "第001話",
                "title": "始まりの物語",
                "word_count": 5000,
                "status": "公開済み",
                "published_date": "2024-01-01",
                "pv": 1000,
                "unique": 800,
            },
        ],
    }


@pytest.fixture
def sample_markdown_content() -> str:
    """テスト用Markdownコンテンツ"""
    return """# 第001話 始まりの物語

 朝の光が窓から差し込んでいた。
「おはよう」と彼女は言った。
 私は振り返り、微笑んだ。
"""


@pytest.fixture
def create_test_manuscript(temp_dir: Path) -> Callable[[str, str | None], Path]:
    """テスト用原稿ファイルを作成"""

    def _create(filename: str, content: str | None) -> Path:
        if content is None:
            content = sample_markdown_content()

        file_path = temp_dir / filename
        file_path.write_text(content, encoding="utf-8")
        return file_path

    return _create


@pytest.fixture(autouse=True)
def reset_logging() -> Generator[None, None, None]:
    """各テストの前後でログ設定をリセット"""

    # テスト前にログレベルをリセット
    configure_logging(preset="development", console_format=LogFormat.RICH)
    yield
    # テスト後にハンドラーをクリア
    # Reset logging handlers to defaults
    configure_logging(preset="development")


@pytest.fixture
def temp_project(tmp_path: Path) -> Generator[Path, None, None]:
    """テスト用の簡易プロジェクト構造を作成して提供

    - manuscripts/ ディレクトリ
    - .noveler/checks/ ディレクトリ
    - manuscripts/episode_001.md サンプル原稿
    """
    project_root = tmp_path
    (project_root / "manuscripts").mkdir(parents=True, exist_ok=True)
    (project_root / ".noveler" / "checks").mkdir(parents=True, exist_ok=True)

    sample_md = project_root / "manuscripts" / "episode_001.md"
    sample_md.write_text(
        "これはテスト用の原稿です。誤字や文法の問題が含まれているかもしれません。",
        encoding="utf-8",
    )

    return project_root


def pytest_addoption(parser: pytest.Parser) -> None:
    """カスタムコマンドラインオプション"""
    parser.addoption(
        "--skip-slow",
        action="store_true",
        default=False,
        help="Skip slow tests",
    )

    parser.addoption(
        "--integration",
        action="store_true",
        default=False,
        help="Run integration tests",
    )


@pytest.fixture
def slow_test(request: pytest.FixtureRequest) -> None:
    """遅いテストをスキップするためのフィクスチャ"""
    if request.config.getoption("--skip-slow"):
        pytest.skip("Skipping slow test")
