#!/usr/bin/env python3
"""A30ガイドサービスファクトリー

SPEC-A30-STEPWISE-001準拠の段階的A30ガイド読み込み機能
Factoryパターンによるサービス依存関係構築
"""

from pathlib import Path
from typing import Any

from noveler.application.use_cases.stepwise_a30_loading_use_case import (
    StepwiseA30LoadingRequest,
    StepwiseA30LoadingResponse,
    StepwiseA30LoadingUseCase,
)
from noveler.domain.services.stepwise_a30_guide_loader import StepwiseA30GuideLoader
from noveler.domain.value_objects.writing_phase import WritingPhase


class A30GuideServiceFactory:
    """A30ガイドサービスファクトリー

    B20開発作業指示書のFactoryパターンに準拠した
    段階的A30ガイド読み込み機能の依存関係構築
    ConfigurationServiceFactory統合対応版
    """

    @staticmethod
    def create_stepwise_loading_use_case(guide_root_path: Path | None = None) -> StepwiseA30LoadingUseCase:
        """段階的A30読み込みユースケース作成

        Args:
            guide_root_path: ガイドファイル格納ディレクトリのパス

        Returns:
            StepwiseA30LoadingUseCase: 設定されたユースケース
        """
        # 統合設定管理システム準拠の設定サービス取得
        from noveler.infrastructure.factories.configuration_service_factory import ConfigurationServiceFactory

        config_service = ConfigurationServiceFactory.create_configuration_service()

        # 依存関係を順次作成
        guide_loader = A30GuideServiceFactory.create_guide_loader(guide_root_path, config_service=config_service)

        # ユースケース作成
        return StepwiseA30LoadingUseCase(guide_loader)

    @staticmethod
    def create_guide_loader(
        guide_root_path: Path | None = None, config_service: Any | None = None
    ) -> StepwiseA30GuideLoader:
        """段階的A30ガイドローダー作成

        Args:
            guide_root_path: ガイドファイル格納ディレクトリのパス
            config_service: 設定サービス（None時は自動作成）

        Returns:
            StepwiseA30GuideLoader: 設定されたローダー
        """
        # 設定サービス自動作成（B20準拠）
        if config_service is None:
            from noveler.infrastructure.factories.configuration_service_factory import ConfigurationServiceFactory

            config_service = ConfigurationServiceFactory.create_configuration_service()

        # B20準拠: ハードコーディング回避、設定管理システムによるデフォルトパス
        if guide_root_path is None:
            try:
                current_file = Path(__file__)
                guide_root_path = current_file.parent.parent.parent / "docs"
            except Exception:
                guide_root_path = Path("docs")

        return StepwiseA30GuideLoader(guide_root_path=guide_root_path, config_service=config_service)

    @staticmethod
    def create_test_use_case() -> StepwiseA30LoadingUseCase:
        """テスト環境用ユースケース作成

        Returns:
            StepwiseA30LoadingUseCase: テスト用ユースケース
        """
        # テスト用設定サービス
        from noveler.infrastructure.factories.configuration_service_factory import ConfigurationServiceFactory

        test_config_service = ConfigurationServiceFactory.create_test_configuration_service()

        # テスト用のローダー（フォールバックを多用）
        test_loader = StepwiseA30GuideLoader(
            guide_root_path=Path("/dev/null"),  # 存在しないパスでフォールバック動作
            config_service=test_config_service,
        )

        return StepwiseA30LoadingUseCase(test_loader)

    @staticmethod
    def load_guide_for_phase(
        phase: WritingPhase,
        project_name: str,
        guide_root_path: Path | None = None,
        problem_type: str | None = None,
        use_configuration_service: bool = True,
    ) -> StepwiseA30LoadingResponse:
        """指定フェーズのガイド読み込み便利メソッド

        Args:
            phase: 執筆フェーズ
            project_name: プロジェクト名
            guide_root_path: ガイドファイル格納ディレクトリのパス
            problem_type: 問題タイプ（トラブルシューティング用）
            use_configuration_service: 統合設定管理システム使用フラグ

        Returns:
            StepwiseA30LoadingResponse: 読み込み結果
        """
        # ユースケース作成
        use_case = A30GuideServiceFactory.create_stepwise_loading_use_case(guide_root_path)

        # リクエスト作成
        request = StepwiseA30LoadingRequest(
            phase=phase,
            project_name=project_name,
            problem_type=problem_type,
            guide_root_path=guide_root_path,
            use_configuration_service=use_configuration_service,
        )

        # 実行
        return use_case.execute(request)

    @staticmethod
    def create_draft_loading_service(project_name: str) -> tuple[StepwiseA30LoadingUseCase, StepwiseA30LoadingRequest]:
        """初稿フェーズ用の軽量読み込みサービス作成

        Args:
            project_name: プロジェクト名

        Returns:
            tuple: (ユースケース, 初稿用リクエスト)
        """
        use_case = A30GuideServiceFactory.create_stepwise_loading_use_case()
        request = StepwiseA30LoadingRequest(
            phase=WritingPhase.DRAFT, project_name=project_name, use_configuration_service=True
        )

        return use_case, request

    @staticmethod
    def create_refinement_loading_service(
        project_name: str,
    ) -> tuple[StepwiseA30LoadingUseCase, StepwiseA30LoadingRequest]:
        """仕上げフェーズ用の完全読み込みサービス作成

        Args:
            project_name: プロジェクト名

        Returns:
            tuple: (ユースケース, 仕上げ用リクエスト)
        """
        use_case = A30GuideServiceFactory.create_stepwise_loading_use_case()
        request = StepwiseA30LoadingRequest(
            phase=WritingPhase.REFINEMENT, project_name=project_name, use_configuration_service=True
        )

        return use_case, request

    @staticmethod
    def create_troubleshooting_loading_service(
        project_name: str, problem_type: str
    ) -> tuple[StepwiseA30LoadingUseCase, StepwiseA30LoadingRequest]:
        """トラブルシューティングフェーズ用読み込みサービス作成

        Args:
            project_name: プロジェクト名
            problem_type: 問題タイプ

        Returns:
            tuple: (ユースケース, トラブルシューティング用リクエスト)
        """
        use_case = A30GuideServiceFactory.create_stepwise_loading_use_case()
        request = StepwiseA30LoadingRequest(
            phase=WritingPhase.TROUBLESHOOTING,
            project_name=project_name,
            problem_type=problem_type,
            use_configuration_service=True,
        )

        return use_case, request

    @staticmethod
    def validate_guide_files_for_phase(phase: WritingPhase, guide_root_path: Path | None = None) -> dict[str, bool]:
        """フェーズ別ガイドファイル存在確認

        Args:
            phase: 執筆フェーズ
            guide_root_path: ガイドルートパス（None時はデフォルト）

        Returns:
            ファイル存在確認結果
        """
        # B20準拠: デフォルトパス設定
        if guide_root_path is None:
            try:
                current_file = Path(__file__)
                guide_root_path = current_file.parent.parent.parent / "docs"
            except Exception:
                guide_root_path = Path("docs")

        validation_result = {
            "master_guide_exists": False,
            "detailed_rules_exists": False,
            "quality_checklist_exists": False,
            "troubleshooting_guide_exists": False,
            "all_required_files_exist": False,
        }

        try:
            # 必須ファイル確認
            master_guide_path = guide_root_path / "A30_執筆ガイド.yaml"
            validation_result["master_guide_exists"] = master_guide_path.exists()

            # フェーズ別ファイル確認
            if phase.requires_detailed_rules():
                detailed_rules_path = guide_root_path / "A30_執筆ガイド（詳細ルール集）.yaml"
                validation_result["detailed_rules_exists"] = detailed_rules_path.exists()

                quality_checklist_path = guide_root_path / "A30_執筆ガイド（ステージ別詳細チェック項目）.yaml"
                validation_result["quality_checklist_exists"] = quality_checklist_path.exists()

            if phase.requires_troubleshooting_guide():
                troubleshooting_path = guide_root_path / "A30_執筆ガイド（トラブルシューティング）.yaml"
                validation_result["troubleshooting_guide_exists"] = troubleshooting_path.exists()

            # 全体的な必須ファイル存在確認
            required_files_exist = validation_result["master_guide_exists"]

            if phase.requires_detailed_rules():
                required_files_exist = required_files_exist and validation_result["detailed_rules_exists"]
                required_files_exist = required_files_exist and validation_result["quality_checklist_exists"]

            if phase.requires_troubleshooting_guide():
                required_files_exist = required_files_exist and validation_result["troubleshooting_guide_exists"]

            validation_result["all_required_files_exist"] = required_files_exist

        except Exception:
            # ファイル確認エラー時は全てFalse
            pass

        return validation_result

    @staticmethod
    def get_phase_requirements_summary(phase: WritingPhase) -> dict[str, Any]:
        """フェーズ別要件サマリー取得

        Args:
            phase: 執筆フェーズ

        Returns:
            フェーズ別要件サマリー
        """
        return {
            "phase": phase.value,
            "phase_description": phase.get_description(),
            "is_lightweight": phase.is_lightweight(),
            "requires_detailed_rules": phase.requires_detailed_rules(),
            "requires_quality_checklist": phase.requires_quality_checklist(),
            "requires_troubleshooting_guide": phase.requires_troubleshooting_guide(),
            "expected_file_patterns": phase.get_expected_file_patterns(),
            "performance_target": f"{phase.get_performance_target_improvement()}% improvement",
        }


# シングルトン的なファクトリーインスタンス（必要に応じて）
_a30_guide_factory = A30GuideServiceFactory()


def get_a30_guide_service_factory() -> A30GuideServiceFactory:
    """A30ガイドサービスファクトリーを取得

    Returns:
        A30GuideServiceFactory インスタンス
    """
    return _a30_guide_factory
