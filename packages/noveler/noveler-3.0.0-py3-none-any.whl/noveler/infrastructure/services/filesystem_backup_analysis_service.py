"""Infrastructure.services.filesystem_backup_analysis_service
Where: Infrastructure service analysing filesystem backups.
What: Evaluates backup contents, detects issues, and suggests remediation.
Why: Ensures backups remain reliable and complete.
"""

from __future__ import annotations

"""ファイルシステムバックアップ分析サービス

B20準拠実装 - Domain Service Implementation
"""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from noveler.noveler.domain.services.backup_analysis_service import (
    BackupAnalysisService,
    BackupStatistics,
    ChaosAnalysisResult,
)
from noveler.noveler.infrastructure.adapters.logger_service_adapter import LoggerServiceProtocol
from noveler.noveler.infrastructure.adapters.path_service_adapter import PathServiceProtocol

if TYPE_CHECKING:
    from pathlib import Path
from noveler.domain.value_objects.project_time import project_now


@dataclass
class BackupFolderInfo:
    """バックアップフォルダ情報"""

    path: Path
    name: str
    size_mb: float
    created_date: datetime
    is_legacy: bool
    folder_type: str  # 'manual', 'daily', 'backup_YYYYMMDD', 'tests_backup_YYYYMMDD'


class FilesystemBackupAnalysisService(BackupAnalysisService):
    """ファイルシステムバックアップ分析サービス

    B20準拠 Domain Service Implementation:
    - Functional Core（純粋なロジック）
    - Imperative Shell（I/O操作）
    - ビジネスロジックの実装
    """

    def __init__(self, *, path_service: PathServiceProtocol, logger_service: LoggerServiceProtocol) -> None:
        """分析サービス初期化"""
        self._path_service = path_service
        self._logger_service = logger_service

    def analyze_chaos_state(self, project_root: Path) -> ChaosAnalysisResult:
        """カオス状態分析 - メイン分析処理"""
        self._logger_service.info("バックアップカオス状態分析開始")

        # 全バックアップフォルダ検出
        backup_folders = self._discover_backup_folders(project_root)

        # 分類・分析
        classified_folders = self._classify_backup_folders(backup_folders)

        self._logger_service.info(f"バックアップフォルダ {len(backup_folders)}箇所検出")

        return ChaosAnalysisResult(
            backup_folders=classified_folders, total_folders=len(backup_folders), analysis_timestamp=project_now().datetime
        )

    def generate_statistics(self, chaos_result: ChaosAnalysisResult) -> BackupStatistics:
        """統計情報生成 - Functional Core（純粋関数）"""
        folders = chaos_result.backup_folders

        if not folders:
            return BackupStatistics(
                total_size_mb=0.0, oldest_backup_date=None, newest_backup_date=None, duplicate_candidates=[]
            )

        # サイズ集計
        total_size = sum(folder.size_mb for folder in folders)

        # 日付範囲
        dates = [folder.created_date for folder in folders]
        oldest_date = min(dates)
        newest_date = max(dates)

        # 重複候補検出
        duplicates = self._find_duplicate_candidates(folders)

        return BackupStatistics(
            total_size_mb=total_size,
            oldest_backup_date=oldest_date,
            newest_backup_date=newest_date,
            duplicate_candidates=duplicates,
        )

    def generate_recommendations(self, statistics: BackupStatistics) -> list[str]:
        """推奨事項生成 - Functional Core（純粋関数）"""
        recommendations = []

        if statistics.total_size_mb > 1000:  # 1GB以上
            recommendations.append("バックアップサイズが大きいため、古いバックアップのクリーンアップを推奨")

        if statistics.duplicate_candidates:
            recommendations.append(f"重複候補 {len(statistics.duplicate_candidates)}箇所の確認を推奨")

        if statistics.oldest_backup_date:
            days_old = (project_now().datetime - statistics.oldest_backup_date).days
            if days_old > 90:
                recommendations.append("90日以上古いバックアップの整理を推奨")

        recommendations.append("統一バックアップ構造への移行を推奨")

        return recommendations

    def _discover_backup_folders(self, project_root: Path) -> list[BackupFolderInfo]:
        """バックアップフォルダ検出 - Imperative Shell"""
        backup_folders = []

        # 検索パターン
        search_patterns = ["backup*", "*backup*", "tests_backup*", "*_backup_*"]

        try:
            for pattern in search_patterns:
                for folder_path in project_root.rglob(pattern):
                    if folder_path.is_dir() and self._is_backup_folder(folder_path):
                        folder_info = self._create_folder_info(folder_path)
                        backup_folders.append(folder_info)

        except Exception as e:
            self._logger_service.error(f"バックアップフォルダ検出エラー: {e}")

        # 重複除去
        return self._deduplicate_folders(backup_folders)

    def _is_backup_folder(self, path: Path) -> bool:
        """バックアップフォルダ判定 - Functional Core（純粋関数）"""
        name_lower = path.name.lower()

        # バックアップっぽいキーワード
        backup_keywords = ["backup", "bak", "old", "archive"]

        for keyword in backup_keywords:
            if keyword in name_lower:
                return True

        # 日付パターン（backup_YYYYMMDD_HHMMSS等）
        date_pattern = r".*\d{8}.*"
        return bool(re.match(date_pattern, name_lower))

    def _create_folder_info(self, path: Path) -> BackupFolderInfo:
        """フォルダ情報作成 - Imperative Shell"""
        try:
            # サイズ計算
            total_size = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
            size_mb = total_size / (1024 * 1024)

            # 作成日取得
            created_timestamp = path.stat().st_ctime
            created_date = datetime.fromtimestamp(created_timestamp)

            # タイプ判定
            folder_type = self._determine_folder_type(path.name)

            return BackupFolderInfo(
                path=path,
                name=path.name,
                size_mb=round(size_mb, 2),
                created_date=created_date,
                is_legacy=self._is_legacy_backup(path.name),
                folder_type=folder_type,
            )

        except Exception as e:
            self._logger_service.warning(f"フォルダ情報取得失敗 {path}: {e}")
            return BackupFolderInfo(
                path=path,
                name=path.name,
                size_mb=0.0,
                created_date=project_now().datetime,
                is_legacy=True,
                folder_type="unknown",
            )

    def _determine_folder_type(self, folder_name: str) -> str:
        """フォルダタイプ判定 - Functional Core（純粋関数）"""
        name_lower = folder_name.lower()

        if "tests_backup" in name_lower:
            return "tests_backup"
        if "backup_" in name_lower and len(folder_name) > 15:
            return "timestamped_backup"
        if name_lower == "backup":
            return "manual"
        if "daily" in name_lower:
            return "daily"
        return "unknown"

    def _is_legacy_backup(self, folder_name: str) -> bool:
        """レガシーバックアップ判定 - Functional Core（純粋関数）"""
        # タイムスタンプがない、または古い命名規則
        modern_patterns = ["backup_", "daily_", "manual_"]

        name_lower = folder_name.lower()
        return all(not name_lower.startswith(pattern) for pattern in modern_patterns)

    def _classify_backup_folders(self, folders: list[BackupFolderInfo]) -> list[BackupFolderInfo]:
        """バックアップフォルダ分類 - Functional Core（純粋関数）"""
        # タイプ別にソート
        return sorted(folders, key=lambda f: (f.folder_type, f.created_date))

    def _find_duplicate_candidates(self, folders: list[BackupFolderInfo]) -> list[str]:
        """重複候補検出 - Functional Core（純粋関数）"""
        duplicates = []

        # サイズベース重複検出
        size_groups = {}
        for folder in folders:
            size_key = round(folder.size_mb, 1)
            if size_key not in size_groups:
                size_groups[size_key] = []
            size_groups[size_key].append(folder)

        for size_mb, group in size_groups.items():
            if len(group) > 1 and size_mb > 0:
                folder_names = [f.name for f in group]
                duplicates.append(f"サイズ{size_mb}MB: {', '.join(folder_names)}")

        return duplicates

    def _deduplicate_folders(self, folders: list[BackupFolderInfo]) -> list[BackupFolderInfo]:
        """フォルダ重複除去 - Functional Core（純粋関数）"""
        seen_paths = set()
        unique_folders = []

        for folder in folders:
            path_str = str(folder.path.resolve())
            if path_str not in seen_paths:
                seen_paths.add(path_str)
                unique_folders.append(folder)

        return unique_folders
