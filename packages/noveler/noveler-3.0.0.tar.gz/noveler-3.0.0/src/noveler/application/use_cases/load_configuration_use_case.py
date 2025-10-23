#!/usr/bin/env python3
"""設定読み込みユースケース

config/novel_config.yamlから設定を読み込むユースケース
"""

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from noveler.domain.interfaces.logger_service_protocol import ILoggerService
    from noveler.infrastructure.unit_of_work import IUnitOfWork

from noveler.application.base.abstract_use_case import AbstractUseCase
from noveler.domain.entities.novel_configuration import NovelConfiguration


@dataclass
class LoadConfigurationRequest:
    """設定読み込みリクエスト"""

    config_file_path: Path


@dataclass
class LoadConfigurationResponse:
    """設定読み込みレスポンス"""

    success: bool
    configuration: NovelConfiguration | None = None
    error_message: str | None = None


class LoadConfigurationUseCase(AbstractUseCase[LoadConfigurationRequest, LoadConfigurationResponse]):
    """設定読み込みユースケース

    指定されたYAMLファイルから設定を読み込み、
    NovelConfigurationエンティティを作成する。
    """

    def __init__(self,
        repository=None,
        logger_service: "ILoggerService" = None,
        unit_of_work: "IUnitOfWork" = None,
        **kwargs) -> None:
        """ユースケースを初期化

        Args:
            repository: 設定リポジトリ
            logger_service: ロガーサービス
            unit_of_work: Unit of Work
            **kwargs: AbstractUseCaseの引数
        """
        super().__init__(**kwargs)
        # B20準拠: 標準DIサービス
        self._logger_service = logger_service
        self._unit_of_work = unit_of_work

        self._repository = repository

    async def execute(self, request: LoadConfigurationRequest) -> LoadConfigurationResponse:
        """設定読み込みを実行

        Args:
            request: 読み込みリクエスト

        Returns:
            読み込み結果
        """
        try:
            # 設定ファイルの存在確認
            if not request.config_file_path.exists():
                # より詳細なエラーメッセージとサポート情報
                error_msg = f"設定ファイルが見つかりません: {request.config_file_path}"

                # 実際のファイル存在状況を確認してヒントを提供
                from pathlib import Path

                # __file__ = .../scripts/application/use_cases/load_configuration_use_case.py
                # guide_root = .../00_ガイド (4つ上の親ディレクトリ)
                guide_root = Path(__file__).parent.parent.parent.parent
                expected_path = guide_root / "config" / "novel_config.yaml"

                if expected_path.exists():
                    error_msg += f"\n💡 ヒント: 設定ファイルは {expected_path} に存在します"
                else:
                    error_msg += f"\n💡 ヒント: 設定ファイルを {expected_path} に配置してください"

                return LoadConfigurationResponse(success=False, error_message=error_msg)

            # 設定データを読み込み
            config_data: dict[str, Any] = self._repository.load_config(request.config_file_path)

            # 設定エンティティを作成
            configuration = NovelConfiguration.from_dict(config_data)

            return LoadConfigurationResponse(success=True, configuration=configuration)

        except Exception as e:
            return LoadConfigurationResponse(success=False, error_message=f"設定読み込みエラー: {e!s}")
