#!/usr/bin/env python3

"""Domain.entities.error_context
Where: Domain entity capturing context around errors.
What: Stores error metadata, triggers, and related resources.
Why: Aids diagnostics by preserving detailed error context.
"""

from __future__ import annotations

"""エラーコンテキストエンティティ

エラー情報とユーザーコンテキストを管理するドメインエンティティ
スマートなエラーハンドリングのためのビジネスロジックを含む
"""


from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from noveler.domain.value_objects.workflow_stage_type import WorkflowStageType


class ErrorSeverity(Enum):
    """エラーの深刻度"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ErrorContext:
    """エラーコンテキストエンティティ"""

    error_type: str
    severity: ErrorSeverity
    affected_stage: WorkflowStageType
    missing_files: list[str] = field(default_factory=list)
    error_details: str | None = None
    user_context: dict[str, Any] = field(default_factory=dict)
    timestamp: str | None = None

    def __post_init__(self) -> None:
        """値の検証"""
        if not self.error_type.strip():
            msg = "エラータイプは必須です"
            raise ValueError(msg)
        if not isinstance(self.missing_files, list):
            msg = "missing_filesはリストである必要があります"
            raise TypeError(msg)

    def is_critical(self) -> bool:
        """クリティカルなエラーかどうか判定"""
        return self.severity in [ErrorSeverity.ERROR, ErrorSeverity.CRITICAL]

    def is_prerequisite_error(self) -> bool:
        """前提条件エラーかどうか判定"""
        return self.error_type == "PREREQUISITE_MISSING" and bool(self.missing_files)

    def get_user_experience_level(self) -> str:
        """ユーザーの経験レベルを取得"""
        return self.user_context.get("experience_level", "beginner")

    def get_project_type(self) -> str | None:
        """プロジェクトタイプを取得"""
        return self.user_context.get("project_type")

    def has_multiple_missing_files(self) -> bool:
        """複数のファイルが不足しているかチェック"""
        return len(self.missing_files) > 1

    def get_primary_missing_file(self) -> str | None:
        """主要な不足ファイルを取得(優先度順)"""
        if not self.missing_files:
            return None

        # 前提条件ファイルの優先度順序
        priority_order = [
            "企画書.yaml",
            "プロジェクト設定.yaml",
            "全体構成.yaml",
            "キャラクター.yaml",
            "世界観.yaml",
        ]

        # 優先度順に確認
        for priority_file in priority_order:
            for missing_file in self.missing_files:
                if priority_file in missing_file:
                    return missing_file

        # 優先度に該当しない場合は最初のファイル
        return self.missing_files[0]

    def generate_user_message(self) -> str:
        """ユーザー向けメッセージを生成"""
        experience_level = self.get_user_experience_level()

        if self.is_prerequisite_error():
            primary_file = self.get_primary_missing_file()
            stage_name = self._get_stage_japanese_name()

            if experience_level == "beginner":
                return self._generate_beginner_message(primary_file, stage_name)
            return self._generate_expert_message(primary_file, stage_name)

        # その他のエラー
        return f"エラーが発生しました: {self.error_type}"

    def _get_stage_japanese_name(self) -> str:
        """ワークフロー段階の日本語名を取得"""
        stage_names = {
            WorkflowStageType.MASTER_PLOT: "全体構成",
            WorkflowStageType.CHAPTER_PLOT: "章別プロット",
            WorkflowStageType.EPISODE_PLOT: "話数別プロット",
        }
        return stage_names.get(self.affected_stage, "プロット作成")

    def _generate_beginner_message(self, primary_file: str, stage_name: str) -> str:
        """初心者向け詳細メッセージ"""
        project_type = self.get_project_type()
        genre_advice = ""

        if project_type == "fantasy":
            genre_advice = "ファンタジー作品では特に世界観設定が重要です。魔法システムや種族設定も忘れずに。"

        return f"""
{stage_name}を作成する前に、必要なファイルが不足しています。

📋 不足ファイル: {primary_file}

💡 詳細な手順:
   1. まず基本設定を完了させましょう
   2. テンプレートをコピーして編集します
   3. プロジェクトの特性に合わせてカスタマイズします

{genre_advice}

次のコマンドで解決できます。所要時間は約30-60分です。
"""

    def _generate_expert_message(self, primary_file: str, stage_name: str) -> str:
        """熟練者向け簡潔メッセージ"""
        return f"""
{stage_name}作成: {primary_file} が必要です。

実行すべきコマンドと所要時間(約15-30分)を確認してください。
"""
