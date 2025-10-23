#!/usr/bin/env python3
"""仕様書アーカイブユースケース - B20準拠

SPEC-ARCHIVE-001: Legacy Specification Archive System
仕様書の段階的アーカイブとレガシー仕様書の安全な移行を担当する。
"""

import shutil
from pathlib import Path
from typing import Any

from noveler.application.use_cases.abstract_use_case import AbstractUseCase
from noveler.domain.entities.value_objects import project_now
from noveler.domain.services.common_path_service import create_path_service
from noveler.domain.value_objects.project_time import project_now
from noveler.infrastructure.logging.unified_logger import get_logger
from noveler.infrastructure.repositories.abstract_unit_of_work import UnitOfWork


class SpecificationArchiveRequest:
    """仕様書アーカイブリクエスト"""

    def __init__(
        self,
        archive_type: str = "legacy-specs",
        target_patterns: list[str] | None = None,
        create_backup: bool = True,
        verify_integrity: bool = True,
    ) -> None:
        self.archive_type = archive_type
        self.target_patterns = target_patterns or ["*.spec.md"]
        self.create_backup = create_backup
        self.verify_integrity = verify_integrity


class SpecificationArchiveResponse:
    """仕様書アーカイブレスポンス"""

    def __init__(
        self,
        success: bool,
        message: str = "",
        archived_files: list[str] | None = None,
        archive_location: str = "",
        backup_id: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.success = success
        self.message = message
        self.archived_files = archived_files or []
        self.archive_location = archive_location
        self.backup_id = backup_id
        self.metadata = metadata or {}

    @classmethod
    def success_response(
        cls,
        archived_files: list[str],
        archive_location: str,
        backup_id: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> "SpecificationArchiveResponse":
        """成功レスポンスを作成"""
        return cls(
            success=True,
            message=f"{len(archived_files)}個のファイルをアーカイブしました",
            archived_files=archived_files,
            archive_location=archive_location,
            backup_id=backup_id,
            metadata=metadata or {},
        )

    @classmethod
    def error_response(cls, message: str) -> "SpecificationArchiveResponse":
        """エラーレスポンスを作成"""
        return cls(success=False, message=message)


class SpecificationArchiveUseCase(AbstractUseCase[SpecificationArchiveRequest, SpecificationArchiveResponse]):
    """仕様書アーカイブユースケース - B20準拠

    B20準拠DIパターン:
    - unit_of_work 注入
    - アーカイブ操作のトランザクション管理
    - BackupUseCaseとの連携による安全なアーカイブ
    """

    def __init__(
        self,
        unit_of_work: UnitOfWork,
        **kwargs: Any
    ) -> None:
        """初期化 - B20準拠

        Args:
            unit_of_work: Unit of Work
            **kwargs: AbstractUseCaseの引数
        """
        super().__init__(**kwargs)
        self._unit_of_work = unit_of_work
        self._logger = get_logger(__name__)

    async def execute(self, request: SpecificationArchiveRequest) -> SpecificationArchiveResponse:
        """仕様書アーカイブを実行 - B20準拠Unit of Work適用

        Args:
            request: アーカイブリクエスト

        Returns:
            SpecificationArchiveResponse: アーカイブ結果
        """
        self._logger.info(f"仕様書アーカイブ開始: {request.archive_type}")

        # B20準拠: Unit of Work トランザクション管理
        with self._unit_of_work.transaction():
            try:
                # 1. アーカイブ対象ファイルの特定
                target_files = self._discover_target_files(request)
                if not target_files:
                    return SpecificationArchiveResponse.error_response(
                        "アーカイブ対象のファイルが見つかりません"
                    )

                self._logger.info(f"アーカイブ対象ファイル: {len(target_files)}個")

                # 2. バックアップ作成（オプション）
                backup_id = ""
                if request.create_backup:
                    backup_id = await self._create_archive_backup(target_files)
                    self._logger.info(f"バックアップ作成完了: {backup_id}")

                # 3. アーカイブディレクトリの準備
                archive_location = self._prepare_archive_directory(request.archive_type)

                # 4. ファイルの安全な移動
                archived_files = self._move_files_to_archive(target_files, archive_location)

                # 5. アーカイブメタデータの生成
                metadata = self._create_archive_metadata(request, archived_files, backup_id)

                # 6. 整合性検証（オプション）
                if request.verify_integrity:
                    verification_result = self._verify_archive_integrity(archived_files, archive_location)
                    if not verification_result:
                        return SpecificationArchiveResponse.error_response(
                            "アーカイブ後の整合性検証に失敗しました"
                        )

                return SpecificationArchiveResponse.success_response(
                    archived_files=[str(f) for f in archived_files],
                    archive_location=str(archive_location),
                    backup_id=backup_id,
                    metadata=metadata,
                )

            except Exception as e:
                self._logger.exception(f"仕様書アーカイブ実行中にエラーが発生: {e}")
                return SpecificationArchiveResponse.error_response(
                    f"アーカイブ実行中にエラーが発生しました: {e}"
                )

    def _discover_target_files(self, request: SpecificationArchiveRequest) -> list[Path]:
        """アーカイブ対象ファイルを特定"""
        path_service = create_path_service()
        specs_dir = path_service.project_root / "specs"

        if not specs_dir.exists():
            self._logger.warning("specsディレクトリが存在しません")
            return []

        target_files = []

        # パターンマッチングでファイル検索
        for pattern in request.target_patterns:
            matching_files = list(specs_dir.glob(pattern))
            # archiveディレクトリ内のファイルは除外
            matching_files = [f for f in matching_files if "archive" not in str(f)]
            target_files.extend(matching_files)

        # 重複除去
        return list(set(target_files))

    async def _create_archive_backup(self, target_files: list[Path]) -> str:
        """アーカイブ前のバックアップ作成"""
        timestamp = project_now().datetime.strftime("%Y%m%d_%H%M%S")
        backup_id = f"spec_archive_backup_{timestamp}"

        # BackupUseCaseとの連携でバックアップ実行
        if self._unit_of_work.backup_repository:
            try:
                backup_config = {
                    "backup_name": backup_id,
                    "timestamp": timestamp,
                    "backup_type": "specification_archive",
                }

                for file_path in target_files:
                    self._unit_of_work.backup_repository.backup_file(str(file_path), backup_config)

                self._logger.info(f"バックアップ完了: {backup_id}")
                return backup_id

            except Exception as e:
                self._logger.exception(f"バックアップ作成エラー: {e}")
                raise

        return backup_id

    def _prepare_archive_directory(self, archive_type: str) -> Path:
        """アーカイブディレクトリの準備"""
        path_service = create_path_service()
        archive_base = path_service.project_root / "specs" / "archive"
        archive_location = archive_base / archive_type

        # ディレクトリ作成
        archive_location.mkdir(parents=True, exist_ok=True)

        self._logger.info(f"アーカイブディレクトリ準備完了: {archive_location}")
        return archive_location

    def _move_files_to_archive(self, target_files: list[Path], archive_location: Path) -> list[Path]:
        """ファイルをアーカイブディレクトリに移動"""
        archived_files = []

        for file_path in target_files:
            try:
                # 移動先パス決定
                destination = archive_location / file_path.name

                # 同名ファイルが存在する場合のリネーム処理
                if destination.exists():
                    timestamp = project_now().datetime.strftime("%Y%m%d_%H%M%S")
                    stem = destination.stem
                    suffix = destination.suffix
                    destination = archive_location / f"{stem}_{timestamp}{suffix}"

                # ファイル移動
                shutil.move(str(file_path), str(destination))
                archived_files.append(destination)

                self._logger.debug(f"ファイル移動完了: {file_path} → {destination}")

            except Exception as e:
                self._logger.exception(f"ファイル移動エラー {file_path}: {e}")
                raise

        return archived_files

    def _verify_archive_integrity(self, archived_files: list[Path], archive_location: Path) -> bool:
        """アーカイブ後の整合性検証"""
        try:
            # 全アーカイブファイルの存在確認
            for file_path in archived_files:
                if not file_path.exists():
                    self._logger.error(f"アーカイブファイルが見つかりません: {file_path}")
                    return False

            # アーカイブメタデータファイルの作成
            metadata_file = archive_location / "ARCHIVE_METADATA.yaml"
            metadata_content = self._generate_metadata_content(archived_files)

            metadata_file.write_text(metadata_content, encoding="utf-8")
            self._logger.info(f"アーカイブメタデータ作成: {metadata_file}")

            return True

        except Exception as e:
            self._logger.exception(f"整合性検証エラー: {e}")
            return False

    def _create_archive_metadata(
        self,
        request: SpecificationArchiveRequest,
        archived_files: list[Path],
        backup_id: str
    ) -> dict[str, Any]:
        """アーカイブメタデータを作成"""
        return {
            "created_at": project_now().datetime.isoformat(),
            "archive_type": request.archive_type,
            "file_count": len(archived_files),
            "archived_files": [str(f) for f in archived_files],
            "backup_id": backup_id,
            "target_patterns": request.target_patterns,
            "verification_enabled": request.verify_integrity,
        }

    def _generate_metadata_content(self, archived_files: list[Path]) -> str:
        """アーカイブメタデータのYAMLコンテンツ生成"""
        timestamp = project_now().datetime.isoformat()

        content = f"""# Specification Archive Metadata
# Generated at: {timestamp}

archive_info:
  created_at: {timestamp}
  archive_type: "legacy-specs"
  total_files: {len(archived_files)}

archived_files:
"""

        for file_path in archived_files:
            content += f"  - name: {file_path.name}\n"
            content += f"    size_bytes: {file_path.stat().st_size}\n"
            content += f"    archived_at: {timestamp}\n"

        content += """
notes: |
  These files were automatically archived as part of the legacy specification cleanup process.
  Files were moved from specs/ root to specs/archive/legacy-specs/ to maintain SPEC-XXX-YYY
  naming convention consistency.

  To restore a file: mv specs/archive/legacy-specs/[filename] specs/
"""

        return content
