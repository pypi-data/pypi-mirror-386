#!/usr/bin/env python3

"""Domain.services.auto_extraction_service
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

from typing import Any

"""自動抽出ドメインサービス

ファイル変更イベントを受けて固有名詞抽出を実行し、
結果をキャッシュに保存するドメインサービス
"""


from dataclasses import dataclass

# Phase 6修正: Service → Repository循環依存解消のため、Protocolインターフェースに変更
from typing import Protocol

from noveler.domain.entities.proper_noun_collection import ProperNounCollection


class IProperNounCacheRepository(Protocol):
    """固有名詞キャッシュリポジトリインターフェース（循環依存解消）"""

    def save_cache(self, collection: ProperNounCollection) -> bool: ...
    def load_cache(self) -> ProperNounCollection | None: ...


class ISettingsFileRepository(Protocol):
    """設定ファイルリポジトリインターフェース（循環依存解消）"""

    def get_extraction_settings(self) -> dict: ...
    def update_settings(self, settings: dict) -> bool: ...


@dataclass(frozen=True)
class ExtractionResult:
    """抽出結果"""

    success: bool
    extracted_terms: ProperNounCollection
    processed_files: list[str]
    errors: list[str]

    @property
    def has_errors(self) -> bool:
        """エラーがあるかどうか"""
        return len(self.errors) > 0

    @property
    def partial_success(self) -> bool:
        """部分的成功かどうか"""
        return self.success and self.has_errors


class AutoExtractionService:
    """自動抽出ドメインサービス"""

    def __init__(
        self, settings_repository: ISettingsFileRepository, cache_repository: IProperNounCacheRepository
    ) -> None:
        """Args:
        settings_repository: 設定ファイルリポジトリ
        cache_repository: 固有名詞キャッシュリポジトリ
        """
        self.settings_repository = settings_repository
        self.cache_repository = cache_repository

    def process_file_changes(self, changes: list[str]) -> ExtractionResult:
        """ファイル変更イベントを処理して固有名詞抽出を実行

        Args:
            changes: ファイル変更イベントのリスト

        Returns:
            ExtractionResult: 抽出結果
        """
        if not changes:
            # 変更がない場合は既存のキャッシュを返す
            cached_terms = self.cache_repository.get_cached_terms()
            return ExtractionResult(
                success=True,
                extracted_terms=cached_terms,
                processed_files=[],
                errors=[],
            )

        # 抽出が必要なイベントのみフィルタ
        extraction_events = [e for e in changes if e.requires_extraction()]

        if not extraction_events:
            # 抽出不要な変更のみの場合
            cached_terms = self.cache_repository.get_cached_terms()
            return ExtractionResult(
                success=True,
                extracted_terms=cached_terms,
                processed_files=[],
                errors=[],
            )

        # ファイル別に抽出を実行
        all_extracted_terms: set[str] = set()
        processed_files = []
        errors: list[Any] = []

        for event in extraction_events:
            try:
                if event.is_deletion():
                    # 削除イベントの場合は処理をスキップ
                    # (削除されたファイルからは抽出できない)
                    file_name = str(event.file_path).split("/")[-1]
                    processed_files.append(f"{file_name} (削除)")
                    continue

                # ファイルから固有名詞を抽出
                file_terms = self.settings_repository.extract_proper_nouns_from_file(str(event.file_path))
                all_extracted_terms.update(file_terms)
                file_name = str(event.file_path).split("/")[-1]
                processed_files.append(file_name)

            except Exception as e:
                file_name = str(event.file_path).split("/")[-1]
                error_msg = f"{file_name}: {e!s}"
                errors.append(error_msg)
                continue

        # 既存のキャッシュと統合
        try:
            cached_terms = self.cache_repository.get_cached_terms()

            # 削除されたファイルの影響を考慮
            # (実装簡略化のため、全体を新しい抽出結果で置き換え)
            final_collection = ProperNounCollection(all_extracted_terms)

            # キャッシュに保存
            self.cache_repository.save_terms(final_collection)

            return ExtractionResult(
                success=True,
                extracted_terms=final_collection,
                processed_files=processed_files,
                errors=errors,
            )

        except Exception as e:
            errors.append(f"キャッシュ操作エラー: {e}")

            # エラーが発生しても部分的な結果は返す
            partial_collection = ProperNounCollection(all_extracted_terms)
            return ExtractionResult(
                success=len(processed_files) > 0,  # 少しでも処理できていれば成功
                extracted_terms=partial_collection,
                processed_files=processed_files,
                errors=errors,
            )

    def force_extract_all(self) -> ExtractionResult:
        """全設定ファイルから強制的に固有名詞を抽出

        Returns:
            ExtractionResult: 抽出結果
        """
        try:
            # 全ファイルから抽出
            all_terms = self.settings_repository.extract_all_proper_nouns()
            final_collection = ProperNounCollection(all_terms)

            # キャッシュに保存
            self.cache_repository.save_terms(final_collection)

            return ExtractionResult(
                success=True,
                extracted_terms=final_collection,
                processed_files=["全設定ファイル"],
                errors=[],
            )

        except Exception as e:
            return ExtractionResult(
                success=False,
                extracted_terms=ProperNounCollection(set()),
                processed_files=[],
                errors=[f"全体抽出エラー: {e!s}"],
            )

    def get_current_terms(self) -> ProperNounCollection:
        """現在キャッシュされている固有名詞を取得

        Returns:
            ProperNounCollection: 現在の固有名詞コレクション
        """
        return self.cache_repository.get_cached_terms()

    def clear_cache(self) -> bool:
        """キャッシュをクリア

        Returns:
            bool: 成功した場合True
        """
        try:
            self.cache_repository.clear_cache()
            return True
        except Exception:
            return False
