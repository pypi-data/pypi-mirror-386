#!/usr/bin/env python3
"""
プロンプト生成アダプター

プロンプト生成機能の依存性注入とファクトリーパターンを実装する
インフラストラクチャ層のアダプター。
"""

from pathlib import Path
from typing import Any

from noveler.application.use_cases.prompt_generation_use_case import PromptGenerationUseCase
from noveler.domain.services.prompt_generation_service import PromptGenerationService
from noveler.infrastructure.repositories.file_a24_guide_repository import FileA24GuideRepository
from noveler.infrastructure.repositories.yaml_project_context_repository import YamlProjectContextRepository
from noveler.infrastructure.services.claude_code_prompt_optimizer import ClaudeCodePromptOptimizer
from noveler.presentation.shared.shared_utilities import get_common_path_service
try:
    from noveler.infrastructure.factories.configuration_service_factory import get_configuration_manager as _get_configuration_manager
except Exception:  # pragma: no cover
    _get_configuration_manager = None


class PromptGenerationAdapterFactory:
    """プロンプト生成アダプターファクトリー

    DDD設計に基づくプロンプト生成機能の依存性注入を管理し、
    統合されたユースケースインスタンスを提供する。
    """

    @classmethod
    def create_use_case(
        cls, project_root: Path | None = None, guide_root: Path | None = None
    ) -> PromptGenerationUseCase:
        """プロンプト生成ユースケース作成

        Args:
            project_root: プロジェクトルートパス（自動検出も可能）
            guide_root: ガイドルートパス（自動検出も可能）

        Returns:
            PromptGenerationUseCase: 完全に構成されたユースケース

        Raises:
            FileNotFoundError: 必要なファイルが見つからない場合
            ValueError: パス設定が不正な場合
        """
        # パス自動検出
        if not guide_root:
            guide_root = Path(__file__).parents[3]  # scripts/infrastructure/adapters から3つ上

        if not project_root:
            # Configuration Manager経由で取得
            config_manager = _get_configuration_manager() if _get_configuration_manager else None
            env_project_root = config_manager.get_system_setting("PROJECT_ROOT")
            if env_project_root:
                project_root = Path(env_project_root)
            else:
                # デフォルトプロジェクトパス（00_ガイドの隣接想定）
                project_root = guide_root.parent / "10_Fランク魔法使いはDEBUGログを読む"

        # A24ガイドリポジトリ作成
        a24_guide_file = guide_root / "docs" / "A24_話別プロットプロンプト.md"
        a24_guide_repo = FileA24GuideRepository(a24_guide_file)

        # プロジェクトコンテキストリポジトリ作成
        context_repo = YamlProjectContextRepository(project_root)

        # プロンプト最適化器作成
        optimizer = ClaudeCodePromptOptimizer()

        # ドメインサービス作成
        prompt_service = PromptGenerationService(a24_guide_repo, context_repo, optimizer)

        # ユースケース作成
        return PromptGenerationUseCase(prompt_service)

    @classmethod
    def create_use_case_with_custom_paths(cls, a24_guide_path: Path, project_root: Path) -> PromptGenerationUseCase:
        """カスタムパス指定でのユースケース作成

        テスト時や特殊な環境での使用を想定。

        Args:
            a24_guide_path: A24ガイドファイルの完全パス
            project_root: プロジェクトルートパス

        Returns:
            PromptGenerationUseCase: カスタム構成のユースケース
        """
        # カスタムパスでリポジトリ作成
        a24_guide_repo = FileA24GuideRepository(a24_guide_path)
        context_repo = YamlProjectContextRepository(project_root)
        optimizer = ClaudeCodePromptOptimizer()

        # サービスとユースケース作成
        prompt_service = PromptGenerationService(a24_guide_repo, context_repo, optimizer)

        return PromptGenerationUseCase(prompt_service)

    @classmethod
    def validate_environment(cls, project_root: Path | None = None, guide_root: Path | None = None) -> dict[str, bool]:
        """環境検証

        プロンプト生成に必要なファイルとディレクトリの存在確認。

        Args:
            project_root: プロジェクトルートパス
            guide_root: ガイドルートパス

        Returns:
            Dict[str, bool]: 検証結果の辞書
        """
        results: dict[str, Any] = {}

        # パス自動検出（create_use_caseと同じロジック）
        if not guide_root:
            guide_root = Path(__file__).parents[3]

        if not project_root:
            config_manager = _get_configuration_manager() if _get_configuration_manager else None
            env_project_root = config_manager.get_system_setting("PROJECT_ROOT")
            if env_project_root:
                project_root = Path(env_project_root)
            else:
                project_root = guide_root.parent / "10_Fランク魔法使いはDEBUGログを読む"

        # A24ガイドファイル
        a24_guide_file = guide_root / "docs" / "A24_話別プロットプロンプト.md"
        results["a24_guide_exists"] = a24_guide_file.exists()

        # プロジェクトルート
        results["project_root_exists"] = project_root.exists() if project_root else False

        # プロジェクト管理資料ディレクトリ（修正: 50_管理資料に変更）
        if project_root:
            mgmt_dir = project_root / "50_管理資料"
            results["settings_dir_exists"] = mgmt_dir.exists()

            # 伏線管理ファイル（修正: 50_管理資料配下）
            foreshadowing_file = mgmt_dir / "伏線管理.yaml"
            results["foreshadowing_file_exists"] = foreshadowing_file.exists()

            # 重要シーンファイル（修正: 50_管理資料配下）
            scenes_file = mgmt_dir / "重要シーン.yaml"
            results["important_scenes_file_exists"] = scenes_file.exists()

            # 章別プロットディレクトリ
            plot_dir = get_common_path_service(project_root).get_plot_dir() / "章別プロット"
            results["chapter_plot_dir_exists"] = plot_dir.exists()
        else:
            results["settings_dir_exists"] = False
            results["foreshadowing_file_exists"] = False
            results["important_scenes_file_exists"] = False
            results["chapter_plot_dir_exists"] = False

        return results

    @classmethod
    def get_environment_info(cls, project_root: Path | None = None, guide_root: Path | None = None) -> dict[str, str]:
        """環境情報取得

        デバッグやトラブルシューティング用の環境情報を収集。

        Returns:
            Dict[str, str]: 環境情報辞書
        """

        # パス自動検出
        if not guide_root:
            guide_root = Path(__file__).parents[3]

        if not project_root:
            config_manager = _get_configuration_manager() if _get_configuration_manager else None
            env_project_root = config_manager.get_system_setting("PROJECT_ROOT")
            if env_project_root:
                project_root = Path(env_project_root)
            else:
                project_root = guide_root.parent / "10_Fランク魔法使いはDEBUGログを読む"

        return {
            "guide_root": str(guide_root),
            "project_root": str(project_root) if project_root else "未設定",
            "a24_guide_path": str(guide_root / "docs" / "A24_話別プロットプロンプト.md"),
            "current_working_dir": str(Path.cwd()),
            "project_root_env": config_manager.get_system_setting("PROJECT_ROOT", "未設定"),
            "python_path": str(Path(__file__).parent),
        }
