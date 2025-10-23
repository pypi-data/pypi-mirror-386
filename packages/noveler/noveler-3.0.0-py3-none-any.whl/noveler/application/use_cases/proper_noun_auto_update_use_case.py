#!/usr/bin/env python3
"""固有名詞自動更新ユースケース

設定ファイル変更を監視して自動的に固有名詞を更新する
アプリケーション層でドメインサービスを調整
"""

import json
from dataclasses import dataclass
from pathlib import Path

import yaml

from noveler.domain.entities.file_change_event import FileChangeEvent
from noveler.domain.entities.settings_file_watcher import SettingsFileWatcher
from noveler.domain.repositories.proper_noun_cache_repository import ProperNounCacheRepository
from noveler.domain.repositories.settings_file_repository import SettingsFileRepository
from noveler.domain.services.auto_extraction_service import AutoExtractionService, ExtractionResult


@dataclass(frozen=True)
class AutoUpdateResult:
    """自動更新結果"""

    success: bool
    message: str
    extracted_count: int
    processed_files: list[str]
    errors: list[str]

    @property
    def has_updates(self) -> bool:
        """更新があったかどうか"""
        return self.extracted_count > 0 or len(self.processed_files) > 0

    @property
    def has_errors(self) -> bool:
        """エラーがあったかどうか"""
        return len(self.errors) > 0


class ProperNounAutoUpdateUseCase:
    """固有名詞自動更新ユースケース"""

    def __init__(
        self, settings_repository: SettingsFileRepository, cache_repository: ProperNounCacheRepository
    ) -> None:
        """Args:
        settings_repository: 設定ファイルリポジトリ
        cache_repository: 固有名詞キャッシュリポジトリ
        """
        self.settings_repository = settings_repository
        self.cache_repository = cache_repository
        self.extraction_service = AutoExtractionService(
            settings_repository,
            cache_repository,
        )

        self._watchers = {}  # プロジェクトごとのウォッチャーを保持

    def check_and_update(self, project_root: Path) -> AutoUpdateResult:
        """設定ファイルの変更をチェックして自動更新

        Args:
            project_root: プロジェクトルートディレクトリ

        Returns:
            AutoUpdateResult: 更新結果
        """
        try:
            project_key = str(project_root)

            # プロジェクトごとのウォッチャーを取得または作成
            if project_key not in self._watchers:
                watcher = SettingsFileWatcher(project_root)
                self._watchers[project_key] = watcher

                # 初回実行時の処理
                if watcher.can_watch():
                    # 既存ファイルから初期抽出
                    initial_result = self.extraction_service.force_extract_all()

                    # 初期状態を記録
                    watcher.initialize_file_states()

                    if initial_result.success and len(initial_result.extracted_terms) > 0:
                        return AutoUpdateResult(
                            success=True,
                            message="初回実行: 既存ファイルから固有名詞を抽出しました",
                            extracted_count=len(initial_result.extracted_terms),
                            processed_files=["初期化時の全設定ファイル"],
                            errors=initial_result.errors,
                        )

                else:
                    return AutoUpdateResult(
                        success=True,
                        message="監視対象ファイルが存在しません",
                        extracted_count=0,
                        processed_files=[],
                        errors=[],
                    )

            watcher = self._watchers[project_key]

            if not watcher.can_watch():
                return AutoUpdateResult(
                    success=True,
                    message="監視対象ファイルが存在しません",
                    extracted_count=0,
                    processed_files=[],
                    errors=[],
                )

            # 変更検出
            changes = watcher.detect_changes()

            if not changes:
                # 変更なしの場合、既存キャッシュの情報を返す
                current_terms = self.extraction_service.get_current_terms()
                return AutoUpdateResult(
                    success=True,
                    message="設定ファイルの変更はありません",
                    extracted_count=len(current_terms),
                    processed_files=[],
                    errors=[],
                )

            # 変更を処理
            extraction_result = self.extraction_service.process_file_changes(changes)

            return self._convert_to_auto_update_result(extraction_result, changes)

        except (OSError, FileNotFoundError, ValueError, yaml.YAMLError) as e:
            return AutoUpdateResult(
                success=False,
                message=f"自動更新処理でエラーが発生: {e!s}",
                extracted_count=0,
                processed_files=[],
                errors=[str(e)],
            )

    def force_full_update(self, _project_root: Path) -> AutoUpdateResult:
        """全設定ファイルから強制的に固有名詞を更新

        Args:
            project_root: プロジェクトルートディレクトリ

        Returns:
            AutoUpdateResult: 更新結果
        """
        try:
            # キャッシュをクリア
            self.extraction_service.clear_cache()

            # 全体抽出を実行
            extraction_result = self.extraction_service.force_extract_all()

            return AutoUpdateResult(
                success=extraction_result.success,
                message=(
                    "全設定ファイルから固有名詞を更新しました"
                    if extraction_result.success
                    else "全体更新でエラーが発生"
                ),
                extracted_count=len(extraction_result.extracted_terms),
                processed_files=extraction_result.processed_files,
                errors=extraction_result.errors,
            )

        except (OSError, FileNotFoundError, ValueError, yaml.YAMLError) as e:
            return AutoUpdateResult(
                success=False,
                message=f"強制更新処理でエラーが発生: {e!s}",
                extracted_count=0,
                processed_files=[],
                errors=[str(e)],
            )

    def get_current_terms(self) -> AutoUpdateResult:
        """現在キャッシュされている固有名詞を取得

        Returns:
            AutoUpdateResult: 現在の状態
        """
        try:
            current_terms = self.extraction_service.get_current_terms()

            return AutoUpdateResult(
                success=True,
                message=f"現在の固有名詞: {len(current_terms)}件",
                extracted_count=len(current_terms),
                processed_files=[],
                errors=[],
            )

        except (OSError, FileNotFoundError, ValueError, json.JSONDecodeError) as e:
            return AutoUpdateResult(
                success=False,
                message=f"現在の固有名詞取得でエラーが発生: {e!s}",
                extracted_count=0,
                processed_files=[],
                errors=[str(e)],
            )

    def clear_cache(self) -> AutoUpdateResult:
        """固有名詞キャッシュをクリア

        Returns:
            AutoUpdateResult: クリア結果
        """
        try:
            success = self.extraction_service.clear_cache()

            return AutoUpdateResult(
                success=success,
                message="固有名詞キャッシュをクリアしました" if success else "キャッシュクリアに失敗",
                extracted_count=0,
                processed_files=[],
                errors=[] if success else ["キャッシュクリアに失敗"],
            )

        except (OSError, FileNotFoundError, ValueError) as e:
            return AutoUpdateResult(
                success=False,
                message=f"キャッシュクリア処理でエラーが発生: {e!s}",
                extracted_count=0,
                processed_files=[],
                errors=[str(e)],
            )

    def _convert_to_auto_update_result(
        self, extraction_result: ExtractionResult, changes: list[FileChangeEvent]
    ) -> AutoUpdateResult:
        """抽出結果を自動更新結果に変換

        Args:
            extraction_result: ドメインサービスの抽出結果
            changes: ファイル変更イベント

        Returns:
            AutoUpdateResult: 変換された結果
        """
        if extraction_result.success:
            if extraction_result.partial_success:
                message = f"部分的に成功: {len(changes)}件の変更を処理"
            else:
                message = f"正常に更新: {len(changes)}件の変更を処理"
        else:
            message = f"更新に失敗: {len(changes)}件の変更でエラー"

        return AutoUpdateResult(
            success=extraction_result.success,
            message=message,
            extracted_count=len(extraction_result.extracted_terms),
            processed_files=extraction_result.processed_files,
            errors=extraction_result.errors,
        )
