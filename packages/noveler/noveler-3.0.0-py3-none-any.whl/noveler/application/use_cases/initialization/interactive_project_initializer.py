"""対話式プロジェクト初期化ユースケース

アプリケーション層:ドメインサービスの調整・外部システム連携
"""

import uuid
from typing import Any

from noveler.domain.initialization.entities import ProjectInitialization
from noveler.domain.initialization.repositories import ProjectInitializationRepository, ProjectTemplateRepository
from noveler.domain.initialization.services import (
    ProjectSetupService,
    QualityStandardConfigService,
    TemplateSelectionService,
)
from noveler.domain.initialization.value_objects import Genre, InitializationConfig, UpdateFrequency, WritingStyle


class InteractiveProjectInitializerUseCase:
    """対話式プロジェクト初期化ユースケース

    責務:
    - ユーザー入力の調整
    - ドメインサービス間の協調
    - 外部システム(ファイルシステム)との連携
    """

    def __init__(
        self,
        template_repository: ProjectTemplateRepository,
        initialization_repository: ProjectInitializationRepository,
        template_selection_service: TemplateSelectionService,
        setup_service: ProjectSetupService,
        quality_config_service: QualityStandardConfigService,
    ) -> None:
        self.template_repository = template_repository
        self.initialization_repository = initialization_repository
        self.template_selection_service = template_selection_service
        self.setup_service = setup_service
        self.quality_config_service = quality_config_service

    def initialize_project_interactively(self, user_inputs: dict[str, Any]) -> dict[str, Any]:
        """対話式プロジェクト初期化実行"""
        try:
            # 1. ユーザー入力から設定作成
            config = self._create_configuration_from_inputs(user_inputs)

            # 2. 初期化プロセス開始
            initialization = ProjectInitialization(
                initialization_id=str(uuid.uuid4()),
                config=config,
            )

            # 3. 最適テンプレート選択
            template_id = self.template_selection_service.select_optimal_template(config)
            template = self.template_repository.find_by_id(template_id)

            if not template:
                return {"success": False, "error": f"テンプレート {template_id} が見つかりません"}

            # 4. 初期化プロセス実行
            initialization.select_template(template_id)
            initialization.validate_configuration()

            # 5. プロジェクトセットアップ
            directory_structure = self.setup_service.generate_directory_structure(config, template)
            initial_files = self.setup_service.generate_initial_files(config)

            # 6. 品質基準設定
            quality_standards = self.quality_config_service.generate_quality_standards(config)

            # 7. ファイル作成(実際の実装では外部サービス呼び出し)
            initialization.create_project_files()
            initialization.complete_initialization()

            # 8. 初期化履歴保存
            self.initialization_repository.save(initialization)

            return {
                "success": True,
                "project_id": initialization.initialization_id,
                "project_name": config.project_name,
                "template_used": template_id,
                "directory_structure": directory_structure,
                "initial_files": list(initial_files.keys()),
                "quality_standards": quality_standards,
                "initialization_date": initialization.created_at.isoformat(),
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _create_configuration_from_inputs(self, inputs: dict[str, Any]) -> InitializationConfig:
        """ユーザー入力から設定オブジェクト作成"""
        genre = Genre(inputs["genre"])
        writing_style = WritingStyle(inputs["writing_style"])
        update_frequency = UpdateFrequency(inputs["update_frequency"])

        return InitializationConfig(
            genre=genre,
            writing_style=writing_style,
            update_frequency=update_frequency,
            project_name=inputs["project_name"],
            author_name=inputs["author_name"],
        )

    def get_available_options(self) -> dict[str, list[str]]:
        """利用可能な選択肢取得"""
        return {
            "genres": [genre.value for genre in Genre],
            "writing_styles": [style.value for style in WritingStyle],
            "update_frequencies": [freq.value for freq in UpdateFrequency],
        }

    def preview_template_selection(self, user_inputs: dict[str, Any]) -> dict[str, Any]:
        """テンプレート選択プレビュー"""
        try:
            config = self._create_configuration_from_inputs(user_inputs)

            # テンプレートランキング取得
            rankings = self.template_selection_service.rank_templates(config)

            preview_results = []
            for ranking in rankings[:3]:  # 上位3つ
                template = self.template_repository.find_by_id(ranking.template_id)
                if template:
                    preview_results.append(
                        {"template_id": template.template_id, "template_name": template.template_name}
                    )

            return {
                "success": True,
                "recommended_templates": preview_results,
                "optimal_choice": preview_results[0] if preview_results else None,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_initialization_history(self, limit: int = 10) -> list[dict[str, Any]]:
        """初期化履歴取得"""
        try:
            recent_initializations = self.initialization_repository.find_recent_initializations(limit)

            return [
                {
                    "initialization_id": init.initialization_id,
                    "project_name": init.config.project_name,
                    "author_name": init.config.author_name,
                    "genre": init.config.genre.value,
                    "status": init.status.value,
                    "created_at": init.created_at.isoformat(),
                    "success": init.is_completed(),
                }
                for init in recent_initializations
            ]

        except Exception as e:
            return [{"error": str(e)}]


class ProjectInitializationOrchestrator:
    """プロジェクト初期化オーケストレーター

    複数のユースケースとドメインサービスを統合
    """

    def __init__(self, interactive_initializer: InteractiveProjectInitializerUseCase) -> None:
        self.interactive_initializer = interactive_initializer

    def execute_full_initialization_workflow(self, user_inputs: dict[str, Any]) -> dict[str, Any]:
        """完全な初期化ワークフロー実行"""
        workflow_results = {
            "phase_1_preview": None,
            "phase_2_initialization": None,
            "phase_3_verification": None,
        }

        try:
            # Phase 1: テンプレート選択プレビュー
            preview_result = self.interactive_initializer.preview_template_selection(user_inputs)
            workflow_results["phase_1_preview"] = preview_result

            if not preview_result["success"]:
                return workflow_results

            # Phase 2: 実際の初期化実行
            init_result = self.interactive_initializer.initialize_project_interactively(user_inputs)
            workflow_results["phase_2_initialization"] = init_result

            if not init_result["success"]:
                return workflow_results

            # Phase 3: 初期化検証
            verification_result = self._verify_initialization(init_result)
            workflow_results["phase_3_verification"] = verification_result

            return workflow_results

        except Exception as e:
            return {
                "success": False,
                "error": f"ワークフロー実行エラー: {e!s}",
                "partial_results": workflow_results,
            }

    def _verify_initialization(self, init_result: dict[str, Any]) -> dict[str, Any]:
        """初期化結果検証"""
        verification_checks = {
            "project_files_created": len(init_result.get("initial_files", [])) > 0,
            "directory_structure_valid": len(init_result.get("directory_structure", [])) > 5,
            "quality_standards_configured": bool(init_result.get("quality_standards")),
            "template_applied": bool(init_result.get("template_used")),
        }

        all_checks_passed = all(verification_checks.values())

        return {
            "success": all_checks_passed,
            "checks": verification_checks,
            "verification_summary": (
                "全ての検証項目が成功しました" if all_checks_passed else "一部の検証項目が失敗しました"
            ),
        }
