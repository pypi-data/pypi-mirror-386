"""Domain.services.episode_metadata_management_service
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

"""
SPEC-EPISODE-004: エピソードメタデータ管理サービス

エピソードメタデータの統合管理を行うドメインサービス。
DDD設計に基づくビジネスロジックの実装。
"""


from datetime import timedelta
from typing import Any, TypedDict


class MetadataUpdate(TypedDict, total=False):
    """メタデータ更新用の型定義"""

    title: str
    status: str
    word_count: int
    quality_score: float
    tags: list[str]
    summary: str


# Phase 6修正: Service → Repository循環依存解消
from typing import Protocol

from noveler.domain.services.metadata_value_objects import (
    BasicMetadata,
    EpisodeMetadata,
    MetadataStatistics,
    QualityMetadata,
    TechnicalMetadata,
    WritingMetadata,
)
from noveler.domain.value_objects.episode_number import EpisodeNumber
from noveler.domain.value_objects.episode_title import EpisodeTitle
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now
from noveler.domain.value_objects.quality_score import QualityScore
from noveler.domain.value_objects.word_count import WordCount


class IEpisodeMetadataRepository(Protocol):
    """エピソードメタデータリポジトリインターフェース（循環依存解消）"""

    def exists(self, episode_number: EpisodeNumber) -> bool: ...

    def save(self, metadata: EpisodeMetadata) -> bool | None: ...

    def find_by_episode_number(self, episode_number: EpisodeNumber) -> EpisodeMetadata | None: ...

    def search_by_criteria(self, criteria: dict[str, Any]) -> list[EpisodeMetadata]: ...


# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class EpisodeMetadataManagementService:
    """エピソードメタデータ管理ドメインサービス"""

    def __init__(self, repository: IEpisodeMetadataRepository) -> None:
        """初期化

        Args:
            repository: メタデータリポジトリ
        """
        self._repository = repository

    def create_metadata(
        self,
        episode_number: EpisodeNumber,
        title: EpisodeTitle,
        author: str = "default_author",
        genre: str = "fantasy",
    ) -> EpisodeMetadata:
        """新規メタデータを作成

        Args:
            episode_number: エピソード番号値オブジェクト
            title: エピソードタイトル値オブジェクト
            author: 著者名（省略時、仕様既定値）
            genre: ジャンル（省略時、仕様既定値）

        Returns:
            作成されたメタデータ

        Raises:
            ValueError: 既にメタデータが存在する場合
        """
        # 既存チェック
        if self._repository.exists(episode_number):
            msg = f"エピソード番号 {episode_number.value} のメタデータは既に存在します"
            raise ValueError(msg)

        # デフォルト値でメタデータ作成
        now = project_now().datetime
        metadata = EpisodeMetadata(
            episode_number=episode_number,
            title=title,
            basic_info=BasicMetadata(author=author, genre=genre, tags=[], description=""),
            writing_info=WritingMetadata(
                word_count=WordCount(0), writing_duration=timedelta(0), status="unwritten", completion_rate=0.0
            ),
            quality_info=QualityMetadata(
                overall_score=QualityScore(0), category_scores={}, last_check_date=now, improvement_suggestions=[]
            ),
            technical_info=TechnicalMetadata(
                file_path=f"episode_{episode_number.value:03d}.md",
                file_hash="uninitialized",
                version="1.0.0",
                backup_paths=[],
            ),
            created_at=now,
            updated_at=now,
        )

        self._repository.save(metadata)
        return metadata

    def update_metadata(self, episode_number: EpisodeNumber, **updates: MetadataUpdate) -> EpisodeMetadata | None:
        """メタデータを更新

        Args:
            episode_number: エピソード番号
            **updates: 更新する属性

        Returns:
            更新されたメタデータ、存在しない場合はNone
        """
        existing = self._repository.find_by_episode_number(episode_number)
        if not existing:
            return None

        # 更新可能な属性を適用
        updated_fields = {}

        if "title" in updates:
            updated_fields["title"] = updates["title"]

        if "word_count" in updates:
            updated_fields["writing_info"] = WritingMetadata(
                word_count=updates["word_count"],
                writing_duration=existing.writing_info.writing_duration,
                status=existing.writing_info.status,
                completion_rate=existing.writing_info.completion_rate,
            )

        if "quality_score" in updates:
            updated_fields["quality_info"] = QualityMetadata(
                overall_score=updates["quality_score"],
                category_scores=existing.quality_info.category_scores,
                last_check_date=project_now().datetime,
                improvement_suggestions=existing.quality_info.improvement_suggestions,
            )

        # 新しいメタデータオブジェクト作成(不変オブジェクトのため)
        updated_metadata = EpisodeMetadata(
            episode_number=existing.episode_number,
            title=updated_fields.get("title", existing.title),
            basic_info=existing.basic_info,
            writing_info=updated_fields.get("writing_info", existing.writing_info),
            quality_info=updated_fields.get("quality_info", existing.quality_info),
            technical_info=existing.technical_info,
            created_at=existing.created_at,
            updated_at=project_now().datetime,
        )

        self._repository.save(updated_metadata)
        return updated_metadata

    def get_metadata(self, episode_number: int) -> EpisodeMetadata | None:
        """メタデータを取得

        Args:
            episode_number: エピソード番号

        Returns:
            メタデータ、存在しない場合はNone
        """
        return self._repository.find_by_episode_number(episode_number)

    def search_by_criteria(self, criteria: dict) -> list[EpisodeMetadata]:
        """検索条件でメタデータを検索

        Args:
            criteria: 検索条件

        Returns:
            条件に一致するメタデータのリスト
        """
        return self._repository.search_by_criteria(criteria)

    def merge_metadata(self, episode_number: EpisodeNumber, _sources: list[Any]) -> EpisodeMetadata | None:
        """複数ソースからメタデータを統合

        Args:
            episode_number: エピソード番号
            sources: 統合ソース(今回は未実装、将来拡張用)

        Returns:
            統合されたメタデータ
        """
        # 現在の実装では既存メタデータを返す(将来拡張用のプレースホルダー)
        return self._repository.find_by_episode_number(episode_number)

    def validate_consistency(self, metadata: EpisodeMetadata) -> dict[str, Any]:
        """メタデータの整合性を検証

        Args:
            metadata: 検証対象のメタデータ

        Returns:
            検証結果の辞書
        """
        issues = []

        # 基本的な整合性チェック
        if metadata.writing_info.completion_rate > 0 and metadata.writing_info.word_count.value == 0:
            issues.append("完成度が0%超なのに文字数が0です")

        if metadata.quality_info.overall_score.value > 0 and not metadata.quality_info.category_scores:
            issues.append("総合品質スコアが0超なのにカテゴリスコアが空です")

        if metadata.writing_info.status == "completed" and metadata.writing_info.completion_rate < 1.0:
            issues.append("ステータスが完成なのに完成度が100%未満です")

        return {"is_consistent": len(issues) == 0, "issues": issues, "severity": "high" if issues else "none"}

    def get_statistics(self, period: str) -> MetadataStatistics:
        """統計情報を取得

        Args:
            period: 統計期間

        Returns:
            統計情報
        """
        return self._repository.get_statistics(period)
