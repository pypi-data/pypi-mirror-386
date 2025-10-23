#!/usr/bin/env python3
"""YAMLプロンプト記録リポジトリ

品質チェックプロンプト記録をYAML形式で永続化するリポジトリ実装。
構造化データの保存・検索・管理機能を提供。
"""

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yaml

from noveler.domain.entities.quality_check_prompt_record import (
    ExecutionMetadata,
    PromptContent,
    QualityCheckPromptRecord,
)
from noveler.domain.repositories.prompt_record_repository import PromptRecordRepository
from noveler.domain.value_objects.a31_evaluation_category import A31EvaluationCategory
from noveler.domain.value_objects.execution_result import ExecutionResult
from noveler.domain.value_objects.improvement_suggestion import ImprovementSuggestion
from noveler.domain.value_objects.quality_issue import QualityIssue


class YamlPromptRecordRepository(PromptRecordRepository):
    """YAMLプロンプト記録リポジトリ実装

    品質チェックプロンプト記録をYAML形式で永続化し、
    効率的な検索・管理機能を提供する実装クラス。
    """

    def __init__(self, base_path: str = "quality_records", logger_service=None, console_service=None) -> None:
        """初期化

        Args:
            base_path: 記録保存ベースパス
        """
        self._base_path = Path(base_path)
        self._ensure_directory_structure()

        self.logger_service = logger_service
        self.console_service = console_service
    def save_record(self, record: QualityCheckPromptRecord) -> bool:
        """プロンプト記録保存

        Args:
            record: 保存する記録

        Returns:
            bool: 保存成功の場合True
        """
        try:
            # 保存パス決定
            project_dir = self._get_project_directory(record.project_name)
            episode_dir = project_dir / f"episode_{record.episode_number:03d}"
            episode_dir.mkdir(parents=True, exist_ok=True)

            # 記録ファイルパス
            record_file = episode_dir / "prompt_records.yaml"

            # 既存記録の読み込み
            existing_records = self._load_records_from_file(record_file)

            # 新規記録追加
            existing_records.append(record.to_detailed_dict())

            # ファイル保存
            with record_file.open("w", encoding="utf-8") as f:
                yaml.dump(
                    {"records": existing_records}, f, default_flow_style=False, allow_unicode=True, sort_keys=False
                )

            # インデックス更新
            self._update_index(record)

            # プロジェクト統計更新
            self._update_project_statistics(record)

            return True

        except Exception as e:
            self.console_service.print(f"プロンプト記録保存エラー: {e}")
            return False

    def find_by_id(self, record_id: str) -> QualityCheckPromptRecord | None:
        """ID指定記録検索

        Args:
            record_id: 記録ID

        Returns:
            Optional[QualityCheckPromptRecord]: 記録（見つからない場合None）
        """
        # インデックスから検索
        index = self._load_index()
        record_info = index.get("records", {}).get(record_id)

        if not record_info:
            return None

        # 実際のファイルから記録を読み込み
        record_file = Path(record_info["file_path"])
        if not record_file.exists():
            return None

        records_data: dict[str, Any] = self._load_records_from_file(record_file)
        for record_dict in records_data:
            if record_dict.get("record_id") == record_id:
                return self._dict_to_record(record_dict)

        return None

    def find_by_project_and_episode(self, project_name: str, episode_number: int) -> list[QualityCheckPromptRecord]:
        """プロジェクト・エピソード指定記録検索

        Args:
            project_name: プロジェクト名
            episode_number: エピソード番号

        Returns:
            list[QualityCheckPromptRecord]: 該当記録リスト
        """
        episode_dir = self._get_project_directory(project_name) / f"episode_{episode_number:03d}"
        record_file = episode_dir / "prompt_records.yaml"

        if not record_file.exists():
            return []

        records_data: dict[str, Any] = self._load_records_from_file(record_file)
        return [self._dict_to_record(record_dict) for record_dict in records_data]

    def find_by_category(
        self, category: A31EvaluationCategory, project_name: str | None = None
    ) -> list[QualityCheckPromptRecord]:
        """カテゴリ指定記録検索

        Args:
            category: チェックカテゴリ
            project_name: プロジェクト名（オプション）

        Returns:
            list[QualityCheckPromptRecord]: 該当記録リスト
        """
        records = []

        if project_name:
            # 特定プロジェクトから検索
            project_dir = self._get_project_directory(project_name)
            records.extend(self._search_project_by_category(project_dir, category))
        else:
            # 全プロジェクトから検索
            projects_dir = self._base_path / "projects"
            if projects_dir.exists():
                for project_dir in projects_dir.iterdir():
                    if project_dir.is_dir():
                        records.extend(self._search_project_by_category(project_dir, category))

        return records

    def find_by_date_range(
        self, start_date: datetime, end_date: datetime, project_name: str | None = None
    ) -> list[QualityCheckPromptRecord]:
        """日付範囲指定記録検索

        Args:
            start_date: 開始日時
            end_date: 終了日時
            project_name: プロジェクト名（オプション）

        Returns:
            list[QualityCheckPromptRecord]: 該当記録リスト
        """
        records = []

        if project_name:
            # 特定プロジェクトから検索
            project_dir = self._get_project_directory(project_name)
            records.extend(self._search_project_by_date_range(project_dir, start_date, end_date))
        else:
            # 全プロジェクトから検索
            projects_dir = self._base_path / "projects"
            if projects_dir.exists():
                for project_dir in projects_dir.iterdir():
                    if project_dir.is_dir():
                        records.extend(self._search_project_by_date_range(project_dir, start_date, end_date))

        return records

    def find_successful_records(
        self, project_name: str | None = None, limit: int | None = None
    ) -> list[QualityCheckPromptRecord]:
        """成功記録検索

        Args:
            project_name: プロジェクト名（オプション）
            limit: 取得件数制限（オプション）

        Returns:
            list[QualityCheckPromptRecord]: 成功記録リスト
        """
        # 過去30日間の記録から成功したもの
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=30)

        all_records = self.find_by_date_range(start_date, end_date, project_name)
        successful_records = [r for r in all_records if r.is_successful_execution()]

        # 効果性スコアでソート
        successful_records.sort(key=lambda r: r.get_effectiveness_score(), reverse=True)

        if limit:
            successful_records = successful_records[:limit]

        return successful_records

    def find_high_impact_records(
        self, min_impact_score: float = 80.0, project_name: str | None = None
    ) -> list[QualityCheckPromptRecord]:
        """高インパクト記録検索

        Args:
            min_impact_score: 最小インパクトスコア
            project_name: プロジェクト名（オプション）

        Returns:
            list[QualityCheckPromptRecord]: 高インパクト記録リスト
        """
        # 過去30日間の記録から高インパクトなもの
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=30)

        all_records = self.find_by_date_range(start_date, end_date, project_name)
        high_impact_records = [r for r in all_records if r.calculate_quality_impact() >= min_impact_score]

        # インパクトスコアでソート
        high_impact_records.sort(key=lambda r: r.calculate_quality_impact(), reverse=True)

        return high_impact_records

    def get_records_statistics(self, project_name: str | None = None, days_back: int = 30) -> dict[str, Any]:
        """記録統計情報取得

        Args:
            project_name: プロジェクト名（オプション）
            days_back: 過去何日分を対象とするか

        Returns:
            dict[str, Any]: 統計情報辞書
        """
        # 指定期間の記録取得
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days_back)
        records = self.find_by_date_range(start_date, end_date, project_name)

        if not records:
            return {
                "total_records": 0,
                "success_rate": 0.0,
                "average_effectiveness": 0.0,
                "category_breakdown": {},
                "analysis_period": f"{start_date.strftime('%Y-%m-%d')} - {end_date.strftime('%Y-%m-%d')}",
            }

        # 基本統計
        total_records = len(records)
        successful_records = [r for r in records if r.is_successful_execution()]
        success_rate = len(successful_records) / total_records

        # 効果性統計
        effectiveness_scores = [r.get_effectiveness_score() for r in successful_records]
        average_effectiveness = sum(effectiveness_scores) / len(effectiveness_scores) if effectiveness_scores else 0.0

        # カテゴリ別統計
        category_stats = defaultdict(lambda: {"total": 0, "successful": 0, "effectiveness_sum": 0.0})

        for record in records:
            category = record.check_category.value
            stats = category_stats[category]
            stats["total"] += 1

            if record.is_successful_execution():
                stats["successful"] += 1
                stats["effectiveness_sum"] += record.get_effectiveness_score()

        # カテゴリ別詳細統計生成
        category_breakdown = {}
        for category, stats in category_stats.items():
            success_rate_cat = stats["successful"] / stats["total"] if stats["total"] > 0 else 0.0
            avg_effectiveness_cat = stats["effectiveness_sum"] / stats["successful"] if stats["successful"] > 0 else 0.0

            category_breakdown[category] = {
                "total_records": stats["total"],
                "success_rate": success_rate_cat,
                "average_effectiveness": avg_effectiveness_cat,
            }

        return {
            "total_records": total_records,
            "success_rate": success_rate,
            "average_effectiveness": average_effectiveness,
            "category_breakdown": category_breakdown,
            "analysis_period": f"{start_date.strftime('%Y-%m-%d')} - {end_date.strftime('%Y-%m-%d')}",
            "high_impact_records": len([r for r in records if r.calculate_quality_impact() >= 80.0]),
        }

    def delete_record(self, record_id: str) -> bool:
        """記録削除

        Args:
            record_id: 削除する記録ID

        Returns:
            bool: 削除成功の場合True
        """
        try:
            # インデックスから検索
            index = self._load_index()
            record_info = index.get("records", {}).get(record_id)

            if not record_info:
                return False

            # ファイルから記録削除
            record_file = Path(record_info["file_path"])
            if record_file.exists():
                records_data: dict[str, Any] = self._load_records_from_file(record_file)
                records_data: dict[str, Any] = [r for r in records_data if r.get("record_id") != record_id]

                # ファイル更新
                with record_file.open("w", encoding="utf-8") as f:
                    yaml.dump(
                        {"records": records_data}, f, default_flow_style=False, allow_unicode=True, sort_keys=False
                    )

            # インデックスから削除
            del index["records"][record_id]
            self._save_index(index)

            return True

        except Exception as e:
            self.console_service.print(f"記録削除エラー: {e}")
            return False

    def cleanup_old_records(self, days_to_keep: int = 90) -> int:
        """古い記録のクリーンアップ

        Args:
            days_to_keep: 保持日数

        Returns:
            int: 削除した記録数
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
        deleted_count = 0

        try:
            # インデックスから古い記録を特定
            index = self._load_index()
            old_record_ids = []

            for record_id, record_info in index.get("records", {}).items():
                created_at = datetime.fromisoformat(record_info["created_at"])
                if created_at < cutoff_date:
                    old_record_ids.append(record_id)

            # 古い記録を削除
            for record_id in old_record_ids:
                if self.delete_record(record_id):
                    deleted_count += 1

            return deleted_count

        except Exception as e:
            self.console_service.print(f"古い記録のクリーンアップエラー: {e}")
            return 0

    def _ensure_directory_structure(self) -> None:
        """ディレクトリ構造確保"""
        directories = [
            self._base_path,
            self._base_path / "projects",
            self._base_path / "templates",
            self._base_path / "indices",
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def _get_project_directory(self, project_name: str) -> Path:
        """プロジェクトディレクトリ取得

        Args:
            project_name: プロジェクト名

        Returns:
            Path: プロジェクトディレクトリパス
        """
        # プロジェクト名をファイルシステム安全な形式に変換
        safe_name = "".join(c for c in project_name if c.isalnum() or c in ("-", "_"))
        return self._base_path / "projects" / safe_name

    def _load_records_from_file(self, file_path: Path) -> list[dict[str, Any]]:
        """ファイルから記録読み込み

        Args:
            file_path: ファイルパス

        Returns:
            list[dict[str, Any]]: 記録リスト
        """
        if not file_path.exists():
            return []

        try:
            with file_path.open(encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return data.get("records", []) if data else []
        except Exception as e:
            self.console_service.print(f"記録ファイル読み込みエラー ({file_path}): {e}")
            return []

    def _dict_to_record(self, record_dict: dict[str, Any]) -> QualityCheckPromptRecord:
        """辞書から記録オブジェクト生成

        Args:
            record_dict: 記録辞書

        Returns:
            QualityCheckPromptRecord: 記録オブジェクト
        """
        # プロンプト内容復元
        prompt_data: dict[str, Any] = record_dict["prompt_content"]
        prompt_content = PromptContent(
            template_id=prompt_data["template_id"],
            raw_prompt=prompt_data["raw_prompt"],
            parameters=prompt_data["parameters"],
            expected_output_format=prompt_data["expected_output_format"],
            input_hash=prompt_data["input_hash"],
        )

        # 実行結果復元
        result_data: dict[str, Any] = record_dict["execution_result"]

        # 問題リスト復元
        issues = [
            QualityIssue(
                issue_type=issue["type"],
                line_number=issue["line_number"],
                description=issue["description"],
                severity=issue["severity"],
                confidence=issue["confidence"],
            )
            for issue in result_data["issues_found"]
        ]

        # 提案リスト復元
        suggestions = [
            ImprovementSuggestion(
                suggestion_type=suggestion["type"],
                content=suggestion["content"],
                expected_impact=suggestion["expected_impact"],
                implementation_difficulty=suggestion["implementation_difficulty"],
            )
            for suggestion in result_data["suggestions"]
        ]

        execution_result = ExecutionResult(
            success=result_data["success"],
            output_content=result_data["output_content"],
            confidence_score=result_data["confidence_score"],
            processing_time=result_data["processing_time"],
            issues_found=tuple(issues),
            suggestions=tuple(suggestions),
            error_message=result_data.get("error_message"),
        )

        # 実行メタデータ復元
        metadata_data: dict[str, Any] = record_dict["execution_metadata"]
        execution_metadata = ExecutionMetadata(
            analyzer_version=metadata_data["analyzer_version"],
            environment_info=metadata_data["environment_info"],
            execution_context=metadata_data["execution_context"],
            quality_threshold=metadata_data["quality_threshold"],
            enhanced_analysis_enabled=metadata_data.get("enhanced_analysis_enabled", True),
        )

        # 記録オブジェクト生成
        return QualityCheckPromptRecord(
            project_name=record_dict["project_name"],
            episode_number=record_dict["episode_number"],
            check_category=A31EvaluationCategory(record_dict["check_category"]),
            prompt_content=prompt_content,
            execution_result=execution_result,
            execution_metadata=execution_metadata,
            record_id=record_dict["record_id"],
            created_at=datetime.fromisoformat(record_dict["created_at"]),
        )

    def _search_project_by_category(
        self, project_dir: Path, category: A31EvaluationCategory
    ) -> list[QualityCheckPromptRecord]:
        """プロジェクト内カテゴリ検索

        Args:
            project_dir: プロジェクトディレクトリ
            category: チェックカテゴリ

        Returns:
            list[QualityCheckPromptRecord]: 該当記録リスト
        """
        records = []

        if not project_dir.exists():
            return records

        # エピソードディレクトリを検索
        for episode_dir in project_dir.iterdir():
            if episode_dir.is_dir() and episode_dir.name.startswith("episode_"):
                record_file = episode_dir / "prompt_records.yaml"
                if record_file.exists():
                    records_data: dict[str, Any] = self._load_records_from_file(record_file)
                    for record_dict in records_data:
                        if record_dict.get("check_category") == category.value:
                            records.append(self._dict_to_record(record_dict))

        return records

    def _search_project_by_date_range(
        self, project_dir: Path, start_date: datetime, end_date: datetime
    ) -> list[QualityCheckPromptRecord]:
        """プロジェクト内日付範囲検索

        Args:
            project_dir: プロジェクトディレクトリ
            start_date: 開始日時
            end_date: 終了日時

        Returns:
            list[QualityCheckPromptRecord]: 該当記録リスト
        """
        records = []

        if not project_dir.exists():
            return records

        # エピソードディレクトリを検索
        for episode_dir in project_dir.iterdir():
            if episode_dir.is_dir() and episode_dir.name.startswith("episode_"):
                record_file = episode_dir / "prompt_records.yaml"
                if record_file.exists():
                    records_data: dict[str, Any] = self._load_records_from_file(record_file)
                    for record_dict in records_data:
                        try:
                            created_at = datetime.fromisoformat(record_dict["created_at"])
                            if start_date <= created_at <= end_date:
                                records.append(self._dict_to_record(record_dict))
                        except (ValueError, KeyError):
                            continue

        return records

    def _update_index(self, record: QualityCheckPromptRecord) -> None:
        """インデックス更新

        Args:
            record: 更新対象記録
        """
        try:
            index = self._load_index()

            if "records" not in index:
                index["records"] = {}

            # 記録情報をインデックスに追加
            record_file_path = (
                self._get_project_directory(record.project_name)
                / f"episode_{record.episode_number:03d}"
                / "prompt_records.yaml"
            )

            index["records"][record.record_id] = {
                "project_name": record.project_name,
                "episode_number": record.episode_number,
                "check_category": record.check_category.value,
                "created_at": record.created_at.isoformat(),
                "file_path": str(record_file_path),
                "success": record.is_successful_execution(),
            }

            self._save_index(index)

        except Exception as e:
            self.console_service.print(f"インデックス更新エラー: {e}")

    def _load_index(self) -> dict[str, Any]:
        """インデックス読み込み

        Returns:
            dict[str, Any]: インデックスデータ
        """
        index_file = self._base_path / "indices" / "records_index.yaml"

        if not index_file.exists():
            return {"records": {}, "last_updated": datetime.now(timezone.utc).isoformat()}

        try:
            with index_file.open(encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            self.console_service.print(f"インデックス読み込みエラー: {e}")
            return {"records": {}, "last_updated": datetime.now(timezone.utc).isoformat()}

    def _save_index(self, index: dict[str, Any]) -> None:
        """インデックス保存

        Args:
            index: インデックスデータ
        """
        try:
            index["last_updated"] = datetime.now(timezone.utc).isoformat()
            index_file = self._base_path / "indices" / "records_index.yaml"

            with index_file.open("w", encoding="utf-8") as f:
                yaml.dump(index, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

        except Exception as e:
            self.console_service.print(f"インデックス保存エラー: {e}")

    def _update_project_statistics(self, record: QualityCheckPromptRecord) -> None:
        """プロジェクト統計更新

        Args:
            record: 対象記録
        """
        try:
            project_dir = self._get_project_directory(record.project_name)
            stats_file = project_dir / "project_statistics.yaml"

            # 既存統計読み込み
            if stats_file.exists():
                with stats_file.open(encoding="utf-8") as f:
                    stats = yaml.safe_load(f) or {}
            else:
                stats = {}

            # 統計情報更新
            if "total_records" not in stats:
                stats["total_records"] = 0
            if "successful_records" not in stats:
                stats["successful_records"] = 0
            if "category_counts" not in stats:
                stats["category_counts"] = {}

            stats["total_records"] += 1
            if record.is_successful_execution():
                stats["successful_records"] += 1

            category = record.check_category.value
            if category not in stats["category_counts"]:
                stats["category_counts"][category] = 0
            stats["category_counts"][category] += 1

            stats["last_updated"] = datetime.now(timezone.utc).isoformat()

            # 統計ファイル保存
            with stats_file.open("w", encoding="utf-8") as f:
                yaml.dump(stats, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

        except Exception as e:
            self.console_service.print(f"プロジェクト統計更新エラー: {e}")
