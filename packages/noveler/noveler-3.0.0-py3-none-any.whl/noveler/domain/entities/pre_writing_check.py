#!/usr/bin/env python3

"""Domain.entities.pre_writing_check
Where: Domain entity modelling pre-writing checks.
What: Stores check results, issues, and guidance for pre-writing review.
Why: Helps authors address issues before drafting begins.
"""

from __future__ import annotations

"""事前執筆チェックエンティティ

TDD+DDD原則に基づくリッチなドメインエンティティ
執筆開始前の必須チェック項目を管理
"""


from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from noveler.domain.exceptions import DomainException
from noveler.domain.value_objects.episode_number import EpisodeNumber
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class CheckItemType(Enum):
    """チェック項目タイプ"""

    EPISODE_INFO = "episode_info"  # 話数管理.yamlの基本情報
    PREVIOUS_FLOW = "previous_flow"  # 前話からの流れ
    EPISODE_PURPOSE = "episode_purpose"  # 今話の目的と到達点
    DROPOUT_RISK = "dropout_risk"  # 離脱リスクポイント
    IMPORTANT_SCENE = "important_scene"  # 重要シーンの詳細設計
    CUSTOM = "custom"  # カスタム項目


class CheckItemStatus(Enum):
    """チェック項目ステータス"""

    PENDING = "pending"  # 未確認
    COMPLETED = "completed"  # 完了
    SKIPPED = "skipped"  # スキップ


@dataclass
class PreWritingCheckItem:
    """事前チェック項目"""

    type: CheckItemType
    title: str
    description: str
    status: CheckItemStatus = field(default=CheckItemStatus.PENDING)
    checked_at: datetime | None = field(default=None)
    notes: str = field(default="")

    @property
    def item_type(self) -> CheckItemType:
        """互換性のためのエイリアス属性"""
        return self.type

    def complete(self, notes: str = "") -> None:
        """項目を完了"""
        self.status = CheckItemStatus.COMPLETED
        self.checked_at = project_now().datetime
        self.notes = notes or ""

    def skip(self, reason: str = "") -> None:
        """項目をスキップ"""
        self.status = CheckItemStatus.SKIPPED
        self.checked_at = project_now().datetime
        self.notes = reason or ""

    def is_done(self) -> bool:
        """完了またはスキップされているか"""
        return self.status in [CheckItemStatus.COMPLETED, CheckItemStatus.SKIPPED]


@dataclass
class PreWritingCheck:
    """事前執筆チェックエンティティ"""

    episode_number: EpisodeNumber
    project_name: str
    check_items: list[PreWritingCheckItem] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime | None = field(default=None)

    def __post_init__(self) -> None:
        """初期化後処理"""
        # 必須チェック項目を自動生成
        if not self.check_items:
            self._initialize_standard_items()

        # 第1話の場合、前話チェックを自動スキップ
        if self.episode_number.value == 1:
            prev_flow_item = self.get_check_item(CheckItemType.PREVIOUS_FLOW)
            if prev_flow_item:
                prev_flow_item.skip("第1話のため前話確認は不要")

    def _initialize_standard_items(self) -> None:
        """標準チェック項目を初期化"""
        self.check_items = [
            PreWritingCheckItem(
                type=CheckItemType.EPISODE_INFO,
                title="話数管理.yamlの基本情報記入",
                description="エピソード番号、タイトル、あらすじ等の基本情報を確認",
            ),
            PreWritingCheckItem(
                type=CheckItemType.PREVIOUS_FLOW,
                title="前話からの流れ確認",
                description="前話の終わり方と今話の始まりの整合性を確認",
            ),
            PreWritingCheckItem(
                type=CheckItemType.EPISODE_PURPOSE,
                title="今話の目的と到達点の明確化",
                description="この話で達成すべき目標と終着点を明確にする",
            ),
            PreWritingCheckItem(
                type=CheckItemType.DROPOUT_RISK,
                title="離脱リスクポイントの事前チェック",
                description="読者が離脱しやすいポイントを事前に特定し対策を検討",
            ),
            PreWritingCheckItem(
                type=CheckItemType.IMPORTANT_SCENE,
                title="重要シーンの詳細設計完了",
                description="クライマックスや感情的な重要シーンの演出を事前設計",
            ),
        ]

    def get_check_item(self, item_type: CheckItemType) -> PreWritingCheckItem | None:
        """特定タイプのチェック項目を取得"""
        for item in self.check_items:
            if item.type == item_type:
                return item
        return None

    def complete_item(self, item_type: CheckItemType, notes: str | None = None) -> None:
        """チェック項目を完了"""
        item = self.get_check_item(item_type)
        if not item:
            msg = f"チェック項目が見つかりません: {item_type.value}"
            raise DomainException(msg)

        item.complete(notes or "")

        # 全項目完了なら完了日時を記録
        if self.is_completed():
            self.completed_at = project_now().datetime

    def skip_item(self, item_type: CheckItemType, reason: str = "") -> None:
        """チェック項目をスキップ"""
        item = self.get_check_item(item_type)
        if not item:
            msg = f"チェック項目が見つかりません: {item_type.value}"
            raise DomainException(msg)

        item.skip(reason)

    def add_custom_item(self, item: PreWritingCheckItem) -> None:
        """カスタムチェック項目を追加"""
        if item.type != CheckItemType.CUSTOM:
            msg = "カスタム項目のタイプはCUSTOMである必要があります"
            raise DomainException(msg)

        self.check_items.append(item)

    def is_completed(self) -> bool:
        """全てのチェックが完了しているか"""
        return all(item.is_done() for item in self.check_items)

    def get_completion_rate(self) -> float:
        """完了率を取得(0-100%)"""
        if not self.check_items:
            return 0.0

        completed_count = sum(1 for item in self.check_items if item.is_done())
        return (completed_count / len(self.check_items)) * 100.0

    def get_summary(self) -> dict[str, any]:
        """チェック結果のサマリーを取得"""
        completed = sum(1 for item in self.check_items if item.status == CheckItemStatus.COMPLETED)
        skipped = sum(1 for item in self.check_items if item.status == CheckItemStatus.SKIPPED)
        pending = sum(1 for item in self.check_items if item.status == CheckItemStatus.PENDING)

        return {
            "episode_number": self.episode_number.value,
            "project_name": self.project_name,
            "total_items": len(self.check_items),
            "completed_items": completed,
            "skipped_items": skipped,
            "pending_items": pending,
            "completion_rate": self.get_completion_rate(),
            "is_completed": self.is_completed(),
            "created_at": self.created_at,
            "completed_at": self.completed_at,
        }

    def get_check_details(self) -> list[dict[str, any]]:
        """チェック項目の詳細情報を取得"""
        return [
            {
                "type": item.type.value,
                "title": item.title,
                "description": item.description,
                "status": item.status.value,
                "checked_at": item.checked_at,
                "notes": item.notes,
            }
            for item in self.check_items
        ]

    def get_dropout_risks(self) -> list[str]:
        """離脱リスクポイントのリストを取得"""
        risk_item = self.get_check_item(CheckItemType.DROPOUT_RISK)
        if not risk_item or not risk_item.notes:
            return []

        # ノートから箇条書きを抽出
        risks = []
        for raw_line in risk_item.notes.split("\n"):
            line = raw_line.strip()
            if line.startswith(("-", "・")):
                risks.append(line[1:].strip())

        return risks

    def get_important_scenes(self) -> list[str]:
        """重要シーンのリストを取得"""
        scene_item = self.get_check_item(CheckItemType.IMPORTANT_SCENE)
        if not scene_item or not scene_item.notes:
            return []

        # ノートから箇条書きを抽出
        scenes = []
        for raw_line in scene_item.notes.split("\n"):
            line = raw_line.strip()
            if line.startswith(("-", "・")):
                scenes.append(line[1:].strip())

        return scenes

    def get_pending_items(self) -> list[PreWritingCheckItem]:
        """未確認の項目リストを取得"""
        return [item for item in self.check_items if item.status == CheckItemStatus.PENDING]

    def validate_for_writing(self) -> list[str]:
        """執筆開始可能かを検証し、問題点を返す"""
        issues = []

        # 必須項目の確認
        issues.extend(
            f"未確認項目: {item.item_type.value}" for item in self.check_items if item.status == CheckItemStatus.PENDING
        )

        # 離脱リスクの確認
        risk_item = self.get_check_item(CheckItemType.DROPOUT_RISK)
        if risk_item and risk_item.status == CheckItemStatus.COMPLETED:
            # 離脱リスクポイントが記録されているかチェック
            # notes が空でない場合は確認済みとみなす
            if not risk_item.notes.strip():
                issues.append("離脱リスクポイントが記録されていません")

        return issues


class PreWritingCheckFactory:
    """事前チェックファクトリー"""

    @staticmethod
    def create_standard_check(episode_number: int, project_name: str) -> PreWritingCheck:
        """標準的なチェックリストを作成"""
        return PreWritingCheck(episode_number=EpisodeNumber(episode_number), project_name=project_name)

    @staticmethod
    def create_first_episode_check(project_name: str) -> PreWritingCheck:
        """第1話用のチェックリストを作成"""
        check = PreWritingCheck(episode_number=EpisodeNumber(1), project_name=project_name)

        # 第1話特有の項目を追加
        check.add_custom_item(
            PreWritingCheckItem(
                type=CheckItemType.CUSTOM,
                title="世界観の導入方法確認",
                description="読者に世界観を自然に伝える方法を確認",
            )
        )

        check.add_custom_item(
            PreWritingCheckItem(
                type=CheckItemType.CUSTOM,
                title="主人公の第一印象設計",
                description="読者が主人公に共感・興味を持てる導入を設計",
            )
        )

        return check

    @staticmethod
    def create_climax_episode_check(episode_number: int, project_name: str) -> PreWritingCheck:
        """クライマックス話用のチェックリストを作成"""
        check = PreWritingCheck(episode_number=EpisodeNumber(episode_number), project_name=project_name)

        # クライマックス特有の項目を追加
        check.add_custom_item(
            PreWritingCheckItem(
                type=CheckItemType.CUSTOM, title="伏線回収の確認", description="これまでの伏線が適切に回収されるか確認"
            )
        )

        check.add_custom_item(
            PreWritingCheckItem(
                type=CheckItemType.CUSTOM,
                title="感情的盛り上がりの設計",
                description="読者の感情を最高潮に持っていく演出を設計",
            )
        )

        return check
