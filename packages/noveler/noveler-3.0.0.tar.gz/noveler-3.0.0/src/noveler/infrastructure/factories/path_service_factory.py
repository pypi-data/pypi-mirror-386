"""Infrastructure.factories.path_service_factory
Where: Infrastructure factory for creating path service instances.
What: Builds path service implementations based on project configuration.
Why: Supplies consistent path utilities to the application and domain layers.
"""

#!/usr/bin/env python3

from __future__ import annotations

"""パスサービスファクトリ

Protocol基盤統合による循環依存解決とレガシー互換性確保
DDD準拠: インフラストラクチャ層のパスサービス生成
DIコンテナと統合されたファクトリパターン実装
MCP統合: Claude CodeのMCP設定を活用した自動プロジェクトルート解決
"""

import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from noveler.domain.interfaces.path_service import IPathService

from noveler.domain.interfaces.path_service_protocol import get_path_service_manager
from noveler.infrastructure.adapters.path_service_adapter import PathServiceAdapter
from noveler.infrastructure.factories.configuration_service_factory import ConfigurationManager


def create_path_service(project_root: Path | str | None = None) -> IPathService:
    """パスサービスのインスタンスを作成（Protocol基盤統合版）

    Args:
        project_root: プロジェクトルートパス（オプション）

    Returns:
        IPathService: パスサービスインスタンス

    Raises:
        ImportError: 必要なモジュールがインポートできない場合
    """
    try:
        # Protocol基盤を使用した新しい実装
        manager = get_path_service_manager()
        return manager.create_path_service(project_root)
    except Exception:
        # フォールバック: 具体実装に直接委譲して再帰を回避
        base_path = _resolve_project_root(project_root)
        return PathServiceAdapter(base_path)


def get_path_service() -> IPathService:
    """グローバルパスサービスインスタンスを取得

    DIコンテナから登録済みのインスタンスを取得、
    未登録の場合は新規作成

    Returns:
        IPathService: パスサービスインスタンス
    """
    try:
        from noveler.infrastructure.di.container import container

        # DIコンテナから取得を試行
        path_service = container.get("IPathService")
        if path_service:
            return path_service

    except Exception:
        # DIコンテナが利用できない場合は直接作成
        pass

    # フォールバック: 直接作成
    return create_path_service()


def is_mcp_environment() -> bool:
    """MCP実行環境の判定

    Claude CodeのMCP設定でcwdが設定されている環境かを判定

    Returns:
        bool: MCP環境の場合True
    """
    # PYTHONPATH環境変数でプロジェクトパスが設定されているかチェック
    pythonpath = os.environ.get("PYTHONPATH", "")

    # MCPサーバーとして実行されている場合の判定条件
    mcp_indicators = [
        # PYTHONPATH にプロジェクトルートが設定されている
        pythonpath and Path(pythonpath).exists() and (Path(pythonpath) / "src" / "noveler").exists(),
        # mcp-server引数で起動されている
        "mcp-server" in sys.argv,
        # json_conversion_cli.py から実行されている
        any("json_conversion_cli.py" in arg for arg in sys.argv),
    ]

    return any(mcp_indicators)


def create_mcp_aware_path_service() -> IPathService:
    """MCP設定統合PathService作成

    Claude CodeのMCP設定cwd値を活用した自動プロジェクトルート解決
    MCPサーバー実行時は設定済みcwdを使用、通常実行時は従来ロジック

    Returns:
        IPathService: MCP環境を考慮したPathServiceインスタンス
    """
    if is_mcp_environment():
        # MCP環境：cwdがプロジェクトルート（claude_code_mcp_config.jsonのcwd設定）
        current_dir = Path.cwd()
        return create_path_service(current_dir)

    # 通常環境：従来のproject_root解決ロジック
    return create_path_service()


# 後方互換性のためのエイリアス
def create_common_path_service(project_root: Path | str | None = None) -> IPathService:
    """後方互換性のためのエイリアス関数"""
    # 直接具体実装を返し、再帰呼び出しを回避
    base_path = _resolve_project_root(project_root)
    return PathServiceAdapter(base_path)


def _resolve_project_root(project_root: Path | str | None) -> Path:
    """プロジェクトルートを堅牢に解決（フォールバック用）"""
    if isinstance(project_root, Path):
        return project_root
    if isinstance(project_root, str) and project_root:
        return Path(project_root).absolute()
    # 1) 明示環境変数があれば最優先
    env_root = os.environ.get("PROJECT_ROOT") or os.environ.get("NOVELER_TEST_PROJECT_ROOT")
    if env_root:
        return Path(env_root).absolute()
    default_sample_name = "10_Fランク魔法使いはDEBUGログを読む"
    guide_root: Path | None = None
    default_sample_candidate: Path | None = None
    try:
        current_file = Path(__file__).resolve()
        guide_root = current_file.parents[4]
        default_sample_candidate = guide_root.parent / default_sample_name
    except Exception:
        guide_root = None
        default_sample_candidate = None

    # 1.5) 現在のディレクトリにプロジェクトインジケーターがあり、ガイド配下でなければ最優先
    current_dir = Path.cwd().resolve()
    project_indicators = [
        "project.yaml",
        "プロジェクト設定.yaml",
        "pyproject.toml",
        ".git",
        "CLAUDE.md",
        "40_原稿",
    ]
    if any((current_dir / indicator).exists() for indicator in project_indicators):
        if not (guide_root and current_dir.is_relative_to(guide_root)):
            return current_dir
    # 2) 設定ファイルでのサンプルプロジェクト指定（優先）
    try:
        cfg_mgr = ConfigurationManager()
        cfg = cfg_mgr.get_configuration()
        if cfg:
            # 推奨キー: paths.samples.root
            # 互換キー: paths.sample_project_root
            configured = (
                cfg.get_path_setting("samples", "root", None)
                or cfg.get_path_setting("", "sample_project_root", None)
            )
            if configured:
                candidate = Path(configured)
                if candidate.exists():
                    return candidate.absolute()
    except Exception:
        pass

    # 3) NOVELER_SAMPLES_ROOT 経由のサンプルプロジェクト（config より後）
    try:
        samples_root_env = os.environ.get("NOVELER_SAMPLES_ROOT")
        if samples_root_env:
            samples_root = Path(samples_root_env)
            default_candidate = samples_root / default_sample_name
            if default_candidate.exists():
                return default_candidate.absolute()
            if samples_root.exists():
                return samples_root.absolute()
    except Exception:
        pass

    # 4) 実際のプロジェクトを自動検出（ガイド直下サンプルの特例調整含む）
    try:
        from noveler.infrastructure.config.project_detector import detect_project_root

        detected = detect_project_root()
        if detected:
            detected_path = detected.absolute()
            if (
                guide_root
                and default_sample_candidate
                and default_sample_candidate.exists()
                and detected_path == guide_root.absolute()
            ):
                return default_sample_candidate.absolute()
            return detected_path
    except Exception:
        pass

    # 5) サンプルプロジェクト既定（GUIDE_ROOT 直下で実行されている場合のみ）
    try:
        current_cwd = Path.cwd().resolve()
        if (
            default_sample_candidate
            and default_sample_candidate.exists()
            and guide_root
            and current_cwd.is_relative_to(guide_root)
        ):
            return default_sample_candidate.absolute()
    except Exception:
        pass
    # 6) 最終フォールバック: 現在ディレクトリ
    return Path.cwd()
