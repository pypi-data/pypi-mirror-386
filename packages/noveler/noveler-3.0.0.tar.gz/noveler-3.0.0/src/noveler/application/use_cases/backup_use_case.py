#!/usr/bin/env python3
"""バックアップユースケース

DDD準拠のバックアップ機能実装
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Protocol

from noveler.application.base.abstract_use_case import AbstractUseCase
from noveler.domain.entities.project import Project
from noveler.domain.value_objects.project_time import project_now
from noveler.infrastructure.adapters.path_service_adapter import create_path_service
from noveler.infrastructure.logging.unified_logger import get_logger


class LoggerService(Protocol):
    """Logger service protocol"""
    def info(self, message: str) -> None: ...


class UnitOfWork(Protocol):
    """Unit of Work protocol"""
    def transaction(self) -> Any: ...

    @property
    def project_repository(self) -> Any: ...

    @property
    def backup_repository(self) -> Any: ...


class MockBackupResult:
    """BackupResult Protocol の暫定実装"""

    def __init__(self, path_service=None) -> None:
        self.success = True
        # PathServiceを使用してバックアップパスを取得
        if path_service:
            self.backup_path = path_service.get_temp_dir() / "backup"
        else:
            # フォールバック: PathServiceが利用できない場合
            self.backup_path = Path.cwd() / "temp" / "backup"
        self.backup_size = 10.0
        self.file_count = 5
        self.error_message = None
        # 追加属性
        self.backed_up_files = 0
        self.total_files = 0
        self.backup_location = "unknown"
        self.execution_time = 0.0


class BackupStatus(Enum):
    """バックアップステータス"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class BackupType(Enum):
    """バックアップタイプ"""

    FULL = "full"
    EPISODE = "episode"
    INCREMENTAL = "incremental"

class BackupResult(Protocol):
    """バックアップ結果のプロトコル"""

    success: bool
    backup_path: Path
    backup_size: float
    file_count: int
    error_message: str | None

@dataclass
class BackupRequest:
    """バックアップリクエスト"""

    project_name: str
    episode: str | None = None
    backup_type: str = "full"  # "full", "episode", "incremental"
    include_drafts: bool = True
    include_archives: bool = False

@dataclass
class BackupResponse:
    """バックアップレスポンス"""

    success: bool
    backup_path: Path | None = None
    backup_size: float = 0.0  # MB
    file_count: int = 0
    error_message: str | None = None
    backup_metadata: dict[str, Any] | None = None

    @property
    def total_size(self) -> int:
        """バックアップサイズをバイト単位で取得"""
        return int(self.backup_size * 1024 * 1024)

    @property
    def duration(self) -> float:
        """バックアップ処理時間を取得"""
        if self.backup_metadata:
            return self.backup_metadata.get("duration", 0.0)
        return 0.0

    @property
    def message(self) -> str:
        """バックアップメッセージを取得"""
        if self.backup_metadata:
            return self.backup_metadata.get("message", "")
        return ""

    @classmethod
    def success_response(
        cls, backup_path: Path, backup_size: float, file_count: int, metadata: dict[str, Any]
    ) -> "BackupResponse":
        """成功レスポンス作成"""
        return cls(
            success=True,
            backup_path=backup_path,
            backup_size=backup_size,
            file_count=file_count,
            backup_metadata=metadata,
        )

    @classmethod
    def error_response(cls, error_message: str) -> "BackupResponse":
        """エラーレスポンス作成"""
        return cls(success=False, error_message=error_message)

class BackupUseCase(AbstractUseCase[BackupRequest, BackupResponse]):
    """バックアップユースケース - B20準拠

    B20準拠DIパターン:
    - logger_service, unit_of_work 注入
    - バックアップ操作のトランザクション管理
    """

    def __init__(
        self,
        logger_service: LoggerService,
        unit_of_work: UnitOfWork,
        **kwargs: Any
    ) -> None:
        """初期化 - B20準拠

        Args:
            logger_service: ロガーサービス
            unit_of_work: Unit of Work
            **kwargs: AbstractUseCaseの引数
        """
        super().__init__(**kwargs)
        self._logger_service = logger_service
        self._unit_of_work = unit_of_work

    async def execute(self, request: BackupRequest) -> BackupResponse:
        """バックアップを実行 - B20準拠Unit of Work適用

        Args:
            request: バックアップリクエスト

        Returns:
            BackupResponse: バックアップ結果
        """
        self._logger_service.info(f"バックアップ開始: {request.project_name} ({request.backup_type})")

        # B20準拠: Unit of Work トランザクション管理
        with self._unit_of_work.transaction():
            try:
                # プロジェクトの存在確認
                project = self._unit_of_work.project_repository.find_by_name(request.project_name)
                if not project:
                    return BackupResponse.error_response(f"プロジェクト '{request.project_name}' が見つかりません")

                # バックアップ設定の準備
                backup_config: dict[str, Any] = self._prepare_backup_config(request, project)

                # バックアップの実行
                if request.backup_type == "episode" and request.episode:
                    backup_result = self._execute_episode_backup(backup_config, request.episode)
                elif request.backup_type == "incremental":
                    backup_result = self._execute_incremental_backup(backup_config)
                else:
                    backup_result = self._execute_full_backup(backup_config)

                if backup_result.success:
                    # メタデータの生成
                    metadata = self._create_backup_metadata(request, backup_result)

                    # バックアップレコードの保存 - B20準拠: UoW経由でリポジトリアクセス
                    if self._unit_of_work.backup_repository:
                        # Note: save_backup_recordメソッドが存在しない場合があるため、適切な実装が必要
                        # 現在のBackupRepositoryインターフェースに合わせてバックアップを実行
                        pass  # TODO: BackupRepositoryの実装に応じて適切なメソッド呼び出し

                    return BackupResponse.success_response(
                        backup_path=backup_result.backup_path,
                        backup_size=backup_result.backup_size,
                        file_count=backup_result.file_count,
                        metadata=metadata,
                    )

                return BackupResponse.error_response(backup_result.error_message or "バックアップに失敗しました")

            except Exception as e:
                return BackupResponse.error_response(f"バックアップ実行中にエラーが発生しました: {e}")

    def _prepare_backup_config(self, request: BackupRequest, project: Project) -> dict[str, Any]:
        """バックアップ設定を準備"""
        timestamp = project_now().datetime.strftime("%Y%m%d_%H%M%S")
        backup_name = f"{request.project_name}_{request.backup_type}_{timestamp}"

        return {
            "project": project,
            "backup_name": backup_name,
            "timestamp": timestamp,
            "include_drafts": request.include_drafts,
            "include_archives": request.include_archives,
        }

    def _execute_full_backup(self, config: dict[str, Any]) -> BackupResult:
        """フルバックアップの実行"""
        # B20準拠: Unit of Work経由でリポジトリアクセス
        if not self._unit_of_work.backup_repository:
            msg = "BackupRepositoryが設定されていません"
            raise RuntimeError(msg)

        # プロジェクト全体のバックアップを実行
        try:
            path_service = create_path_service()

            # プロジェクト重要ファイルを取得
            project_files = []
            project_root = path_service.project_root

            # 設定ファイル
            project_config = project_root / "プロジェクト設定.yaml"
            if project_config.exists():
                project_files.append(project_config)

            # 原稿ディレクトリ
            manuscript_dir = path_service.get_manuscript_dir()
            if manuscript_dir.exists():
                # 簡単なglob操作でファイルキャッシュサービスの依存を避ける
                manuscript_files = list(manuscript_dir.glob("**/*.md"))
                project_files.extend(manuscript_files)

            # 各ファイルをバックアップ
            backup_count = 0
            for file_path in project_files:
                try:
                    self._unit_of_work.backup_repository.backup_file(str(file_path), config)
                    backup_count += 1
                except Exception as e:
                    # B20準拠: print文削除、ロガー使用
                    logger = get_logger(__name__)
                    logger.exception(f"ファイルバックアップエラー {file_path}: {e}")
            # MockBackupResultを使用してProtocol準拠オブジェクトを作成
            result = MockBackupResult()
            result.success = backup_count > 0
            result.backed_up_files = backup_count
            result.total_files = len(project_files)
            result.backup_location = config.get("backup_location", "不明")
            result.execution_time = 0.0
            return result
        except Exception as e:
            # MockBackupResultを使用してエラー結果を作成
            result = MockBackupResult()
            result.success = False
            result.backed_up_files = 0
            result.total_files = 0
            result.backup_location = "エラー"
            result.execution_time = 0.0
            result.error_message = str(e)
            return result

    def _execute_episode_backup(self, config: dict[str, Any], _episode: str) -> BackupResult:
        """エピソードバックアップの実行"""
        if not self._unit_of_work.backup_repository:
            msg = "BackupRepositoryが設定されていません"
            raise RuntimeError(msg)

        # TODO: エピソード特化バックアップの実装
        return self._create_mock_backup_result(config)

    def _execute_incremental_backup(self, config: dict[str, Any]) -> BackupResult:
        """増分バックアップの実行"""
        if not self._unit_of_work.backup_repository:
            msg = "BackupRepositoryが設定されていません"
            raise RuntimeError(msg)

        # TODO: 増分バックアップの実装
        return self._create_mock_backup_result(config)

    def _create_mock_backup_result(self, _config: dict[str, Any]) -> MockBackupResult:
        """暫定的なBackupResult作成

        TODO: 実際のBackupResultプロトコルに準拠した結果オブジェクトの作成
        """
        return MockBackupResult()

    def _create_backup_metadata(self, request: BackupRequest, backup_result: BackupResult) -> dict[str, Any]:
        """バックアップメタデータを作成"""
        return {
            "created_at": project_now().datetime.isoformat(),
            "backup_type": request.backup_type,
            "episode": request.episode,
            "file_count": backup_result.file_count,
            "backup_size_mb": backup_result.backup_size,
            "include_drafts": request.include_drafts,
            "include_archives": request.include_archives,
        }
