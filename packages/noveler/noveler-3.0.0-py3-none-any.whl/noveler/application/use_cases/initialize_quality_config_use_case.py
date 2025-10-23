"""品質設定初期化ユースケース"""

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from noveler.domain.services.quality_config_initialization_service import QualityConfigInitializationService


@dataclass
class InitializeQualityConfigCommand:
    """品質設定初期化コマンド"""

    project_root: Path
    genre: str
    force: bool = False


@dataclass
class InitializeQualityConfigResult:
    """品質設定初期化結果"""

    success: bool
    message: str
    config_path: Path | None = None


class InitializeQualityConfigUseCase:
    """品質設定初期化ユースケース"""

    def __init__(self, service: "QualityConfigInitializationService") -> None:
        """初期化"""
        self.service = service

    def execute(self, command: InitializeQualityConfigCommand) -> InitializeQualityConfigResult:
        """品質設定を初期化"""
        try:
            # ジャンルのバリデーション
            if not command.genre:
                return InitializeQualityConfigResult(
                    success=False,
                    message="ジャンルが指定されていません",
                )

            # 初期化実行
            result = self.service.initialize_for_project(command.project_root)

            if result.success:
                # DDD準拠: Infrastructure層のパスサービスを使用（Presentation層依存を排除）
                from noveler.infrastructure.adapters.path_service_adapter import create_path_service

                path_service = create_path_service(command.project_root)
                config_path = path_service.get_quality_config_file()
                return InitializeQualityConfigResult(
                    success=True,
                    message=result.message,
                    config_path=config_path,
                )

            return InitializeQualityConfigResult(
                success=False,
                message=result.message,
            )

        except ValueError as e:
            return InitializeQualityConfigResult(
                success=False,
                message=f"エラー: {e}",
            )

        except Exception as e:
            return InitializeQualityConfigResult(
                success=False,
                message=f"予期しないエラーが発生しました: {e}",
            )
