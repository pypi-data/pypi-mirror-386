"""Domain.services.quality_config_auto_update_service
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

"""品質設定自動更新ドメインサービス"""


from dataclasses import dataclass
import datetime as dt
from enum import Enum
from typing import TYPE_CHECKING, Any

from noveler.domain.value_objects.genre_type import GenreType
from noveler.domain.value_objects.project_time import project_now

# Legacy tests expect to patch module-level datetime/timezone via
# domain.services.quality_config_auto_update_service.*
datetime = dt.datetime
timezone = dt.timezone

import sys as _sys

_sys.modules.setdefault("domain.services.quality_config_auto_update_service", _sys.modules[__name__])

if TYPE_CHECKING:

    from pathlib import Path

    from noveler.domain.repositories.project_repository import ProjectRepository
    from noveler.domain.repositories.quality_record_repository import QualityRecordRepository


# 旧モジュールパス互換: testsが domain.services.* を参照するためのエイリアス


class UpdateTrigger(Enum):
    """更新トリガーの種類"""

    PROJECT_START = "project_start"
    MASTER_PLOT_COMPLETED = "master_plot_completed"
    PERIODIC_REVIEW = "periodic_review"


@dataclass
class UpdateResult:
    """更新結果"""

    success: bool
    message: str
    trigger: UpdateTrigger | None = None
    suggestions: list[str] | None = None


class QualityConfigAutoUpdateService:
    """品質設定自動更新サービス"""

    def __init__(self, quality_repo: QualityRecordRepository, project_repo: ProjectRepository) -> None:
        """初期化"""
        self.quality_repo = quality_repo
        self.project_repo = project_repo

    def initialize_for_project(self, project_root: Path) -> UpdateResult:
        """プロジェクト開始時の初期設定"""
        try:
            # 既存設定の確認
            if self.quality_repo.exists(project_root):
                return UpdateResult(
                    success=True,
                    message="品質設定ファイルは既に存在します",
                )

            # ジャンルを取得
            genre = self.project_repo.get_genre(project_root)
            if not isinstance(genre, GenreType):
                genre = GenreType(genre)

            # ジャンル別デフォルト設定を取得
            config = genre.get_default_quality_config()

            # メタデータを追加
            config["metadata"] = {
                "created_at": project_now().datetime.isoformat(),
                "updated_at": project_now().datetime.isoformat(),
                "genre": genre.value,
                "auto_generated": True,
                "update_reason": f"{genre.value}ジャンルのデフォルト設定で初期化",
            }

            # 保存
            self.quality_repo.save(project_root, config)

            return UpdateResult(
                success=True,
                message=f"{genre.value}ジャンルの品質設定を作成しました",
                trigger=UpdateTrigger.PROJECT_START,
            )

        except Exception as e:
            return UpdateResult(
                success=False,
                message=f"品質設定の初期化中にエラーが発生しました: {e}",
            )

    def adjust_by_master_plot(self, project_root: Path, plot_data: dict[str, Any]) -> UpdateResult:
        """マスタープロット完成時の調整"""
        try:
            # 既存設定を読み込み
            current_config: dict[str, Any] = self.quality_repo.load(project_root)

            # バックアップを作成
            if self.quality_repo.exists(project_root):
                backup_suffix = f"backup.{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
                self.quality_repo.backup(project_root, backup_suffix)

            # プロットからキーワードを分析
            keywords = plot_data.get("keywords", [])
            themes = plot_data.get("themes", [])

            # 調整ルール
            adjustments = []

            # バトル要素がある場合
            if any(k in ["バトル", "戦闘", "アクション"] for k in keywords):
                current_config.setdefault("composition", {})["short_sentence_ratio"] = 0.45
                adjustments.append("バトル要素を検出")

            # 恋愛要素がある場合
            if any(k in ["恋愛", "ラブコメ", "ロマンス"] for k in keywords + themes):
                current_config.setdefault("composition", {})["dialog_ratio_range"] = [0.40, 0.70]
                adjustments.append("恋愛要素を検出")

            # 更新理由を記録
            current_config.setdefault("metadata", {})["updated_at"] = project_now().datetime.isoformat()
            current_config["metadata"]["update_reason"] = "マスタープロット分析による自動調整"
            current_config["metadata"]["adjustments"] = adjustments

            # 保存
            self.quality_repo.save(project_root, current_config)

            message = "マスタープロット分析により品質設定を調整しました"
            if adjustments:
                message += f": {', '.join(adjustments)}"

            return UpdateResult(
                success=True,
                message=message,
                trigger=UpdateTrigger.MASTER_PLOT_COMPLETED,
            )

        except Exception as e:
            return UpdateResult(
                success=False,
                message=f"品質設定の調整中にエラーが発生しました: {e}",
            )

    def suggest_optimization(self, project_root: Path, episode_number: int) -> UpdateResult:
        """執筆中の定期見直し提案"""
        try:
            # 10話ごとにチェック
            REVIEW_INTERVAL = 10
            if episode_number < REVIEW_INTERVAL or episode_number % REVIEW_INTERVAL != 0:
                return UpdateResult(
                    success=True,
                    message=f"第{episode_number}話完了。品質設定の見直しはまだ早いです",
                )

            # 過去の品質チェック結果を取得
            results: Any = self.quality_repo.get_recent_results(project_root, count=10)
            if not results:
                return UpdateResult(
                    success=True,
                    message="品質チェック結果が不足しています",
                )

            # 現在の設定を読み込み
            self.quality_repo.load(project_root)

            # 分析と提案
            suggestions = []

            # 文体スコアが低い傾向
            basic_scores = [r.get("scores", {}).get("basic_style", 100) for r in results]
            avg_basic = sum(basic_scores) / len(basic_scores)
            if avg_basic < 70:
                suggestions.append("文体スコアが低い傾向があります。ひらがな比率の基準を緩和することを検討してください")

            # 構成スコアが低い傾向
            comp_scores = [r.get("scores", {}).get("composition", 100) for r in results]
            avg_comp = sum(comp_scores) / len(comp_scores)
            if avg_comp < 70:
                suggestions.append("構成スコアが低い傾向があります。会話比率の範囲を調整することを検討してください")

            if suggestions:
                return UpdateResult(
                    success=True,
                    message=f"第{episode_number}話到達。品質設定の最適化提案があります",
                    trigger=UpdateTrigger.PERIODIC_REVIEW,
                    suggestions=suggestions,
                )

            return UpdateResult(
                success=True,
                message=f"第{episode_number}話到達。現在の品質設定は適切です",
                trigger=UpdateTrigger.PERIODIC_REVIEW,
                suggestions=None,  # テストが期待するNoneを返す
            )

        except Exception as e:
            return UpdateResult(
                success=False,
                message=f"品質設定の最適化提案中にエラーが発生しました: {e}",
            )
