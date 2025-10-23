#!/usr/bin/env python3
"""YAML品質記録拡張リポジトリ実装
品質記録活用システムのインフラ層
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import yaml

from noveler.domain.entities.learning_session import LearningSession
from noveler.domain.entities.quality_record_enhancement import QualityRecordEnhancement
from noveler.domain.exceptions import QualityRecordNotFoundError, ValidationError
from noveler.domain.repositories.quality_record_enhancement_repository import QualityRecordEnhancementRepository
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now
from noveler.infrastructure.utils.yaml_utils import YAMLHandler

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class YamlQualityRecordEnhancementRepository(QualityRecordEnhancementRepository):
    """YAML形式の品質記録拡張リポジトリ実装"""

    def __init__(self, base_path: Path | str | None) -> None:
        if base_path is None:
            # デフォルトのベースパスを設定
            current_dir = Path(__file__).parent.parent.parent
            self.base_path = current_dir / "test_data" / "quality_records"
        else:
            self.base_path = Path(base_path)

        # ディレクトリが存在しない場合は作成
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_quality_record_path(self, _project_name: str) -> Path:
        """品質記録ファイルのパスを取得"""
        # プロジェクト名に関係なく、同じディレクトリに統一ファイルとして保存
        return self.base_path / "品質記録_AI学習用.yaml"

    def _get_learning_session_path(self, _project_name: str) -> Path:
        """学習セッションファイルのパスを取得"""
        # プロジェクト名に関係なく、同じディレクトリに統一ファイルとして保存
        return self.base_path / "学習セッション記録.yaml"

    def _sanitize_filename(self, filename: str) -> str:
        """ファイル名を安全な形式に変換"""
        # 危険な文字を除去
        safe_chars = []
        for char in filename:
            if char.isalnum() or char in "-_":
                safe_chars.append(char)
            else:
                safe_chars.append("_")
        return "".join(safe_chars)

    def save(self, quality_record: "QualityRecordEnhancement") -> None:
        """品質記録を保存"""
        file_path = self._get_quality_record_path(quality_record.project_name)

        # エンティティをYAML形式に変換
        yaml_data: dict[str, Any] = {
            "metadata": {
                "project_name": quality_record.project_name,
                "version": quality_record.version,
                "last_updated": quality_record.last_updated.isoformat(),
                "entry_count": quality_record.entry_count,
            },
            "quality_checks": quality_record.quality_checks,
            "learning_data": self._extract_learning_data(quality_record),
        }

        try:
            # YAMLHandlerを使用して保存を試みる(フォーマッターは無効)
            try:
                YAMLHandler.save_yaml(file_path, yaml_data, use_formatter=False)
            except ImportError:
                # フォールバック: 従来の方法で保存
                with Path(file_path).open("w", encoding="utf-8") as file:
                    yaml.dump(yaml_data, file, default_flow_style=False, allow_unicode=True, sort_keys=False)
        except Exception as e:
            msg = f"品質記録の保存に失敗しました: {e!s}"
            raise ValidationError(msg) from e

    def _extract_learning_data(self, quality_record: "QualityRecordEnhancement") -> dict[str, Any]:
        """学習データを抽出"""
        learning_data: dict[str, Any] = {
            "improvement_trends": {},
            "common_issues": {"frequent_errors": [], "recurring_warnings": [], "improvement_patterns": []},
            "personal_growth": {
                "strengths": quality_record.get_strongest_categories(),
                "areas_for_improvement": quality_record.get_weakest_categories(),
                "learning_goals": [],
            },
        }

        # 各カテゴリの改善トレンドを抽出
        latest_scores = quality_record.get_latest_scores()
        for category in latest_scores:
            trend = quality_record.get_improvement_trend(category)
            if trend:
                learning_data["improvement_trends"][category] = [
                    {
                        "episode_number": point["episode_number"],
                        "timestamp": point["timestamp"],
                        "score": point["score"],
                        "improvement": point["improvement"],
                    }
                    for point in trend
                ]

        return learning_data

    def find_by_project_name(self, project_name: str) -> QualityRecordEnhancement | None:
        """プロジェクト名で品質記録を検索"""
        file_path = self._get_quality_record_path(project_name)

        if not file_path.exists():
            return None

        try:
            with Path(file_path).open(encoding="utf-8") as file:
                yaml_data: dict[str, Any] = yaml.safe_load(file)

            # YAMLデータからエンティティを復元
            return QualityRecordEnhancement(
                project_name=yaml_data["metadata"]["project_name"],
                version=yaml_data["metadata"]["version"],
                last_updated=datetime.fromisoformat(yaml_data["metadata"]["last_updated"]),
                entry_count=yaml_data["metadata"]["entry_count"],
                quality_checks=yaml_data.get("quality_checks", []),
            )

        except Exception as e:
            msg = f"品質記録の読み込みに失敗しました: {e!s}"
            raise ValidationError(msg) from e

    def find_by_project_and_episode(self, project_name: str, episode_number: int) -> dict[str, Any] | None:
        """プロジェクト名とエピソード番号で品質記録を検索"""
        quality_record = self.find_by_project_name(project_name)

        if not quality_record:
            return None

        # 指定されたエピソードの品質チェック結果を検索
        for check in quality_record.quality_checks:
            if check["episode_number"] == episode_number:
                return check

        return None

    def find_learning_history(self, project_name: str, period: str) -> list[dict[str, Any]]:
        """学習履歴を検索"""
        quality_record = self.find_by_project_name(project_name)

        if not quality_record:
            return []

        # 期間に基づいてフィルタリング
        cutoff_date = self._get_cutoff_date(period)

        filtered_history = []
        for check in quality_record.quality_checks:
            check_date = datetime.fromisoformat(check["timestamp"])
            if check_date >= cutoff_date:
                filtered_history.append(check)

        return sorted(filtered_history, key=lambda x: x.get("timestamp", ""))

    def _get_cutoff_date(self, period: str) -> datetime:
        """期間指定からカットオフ日時を取得"""
        now = project_now().datetime

        if period == "last_7_days":
            return now - timedelta(days=7)
        if period == "last_30_days":
            return now - timedelta(days=30)
        if period == "last_90_days":
            return now - timedelta(days=90)
        if period == "last_year":
            return now - timedelta(days=365)
        # デフォルトは30日
        return now - timedelta(days=30)

    def get_trend_analysis_data(self, project_name: str, episode_range: str) -> list[dict[str, Any]]:
        """トレンド分析データを取得"""
        quality_record = self.find_by_project_name(project_name)

        if not quality_record:
            msg = f"プロジェクト '{project_name}' の品質記録が見つかりません"
            raise QualityRecordNotFoundError(msg)

        # エピソード範囲を解析
        start_episode, end_episode = self._parse_episode_range(episode_range)

        # 範囲内の品質チェック結果を取得
        filtered_checks = []
        for check in quality_record.quality_checks:
            episode_num = check["episode_number"]
            if start_episode <= episode_num <= end_episode:
                filtered_checks.append(check)

        return sorted(filtered_checks, key=lambda x: x.get("episode_number", 0))

    def _parse_episode_range(self, episode_range: str) -> tuple[int, int]:
        """エピソード範囲を解析"""
        try:
            if "-" in episode_range:
                start_str, end_str = episode_range.split("-", 1)
                start_episode = int(start_str.strip())
                end_episode = int(end_str.strip())
            else:
                # 単一のエピソード
                episode_num = int(episode_range.strip())
                start_episode = end_episode = episode_num

            if start_episode > end_episode:
                msg = "開始エピソード番号は終了エピソード番号以下である必要があります"
                raise ValidationError(msg)

            return start_episode, end_episode

        except ValueError as e:
            msg = f"無効なエピソード範囲: {episode_range}"
            raise ValidationError(msg) from e

    def exists(self, project_name: str) -> bool:
        """品質記録の存在確認"""
        file_path = self._get_quality_record_path(project_name)
        return file_path.exists()

    def delete(self, project_name: str) -> bool:
        """品質記録を削除"""
        file_path = self._get_quality_record_path(project_name)
        session_path = self._get_learning_session_path(project_name)

        deleted = False

        if file_path.exists():
            file_path.unlink()
            deleted = True

        if session_path.exists():
            session_path.unlink()
            deleted = True

        return deleted

    def get_all_projects(self) -> list[str]:
        """全てのプロジェクト名を取得"""
        projects = []

        if not self.base_path.exists():
            return projects

        for file_path in self.base_path.glob("品質記録_AI学習用.yaml"):
            # 品質記録ファイルが存在する場合はプロジェクトを追加
            if file_path.name == "品質記録_AI学習用.yaml":
                # プロジェクト名はファイル内容から取得する必要がある
                try:
                    with Path(file_path).open(encoding="utf-8") as f:
                        data = yaml.safe_load(f)
                        if data and "metadata" in data:
                            project_name = data["metadata"].get("project_name")
                            if project_name:
                                projects.append(project_name)
                except Exception:
                    pass

        return sorted(projects)

    def save_learning_session(self, session: "LearningSession") -> None:
        """学習セッションを保存"""
        file_path = self._get_learning_session_path(session.project_name)

        # 既存のセッションデータを読み込み
        sessions_data: dict[str, Any] = []
        if file_path.exists():
            try:
                with Path(file_path).open(encoding="utf-8") as file:
                    sessions_data: dict[str, Any] = yaml.safe_load(file) or []
            except Exception:
                sessions_data: dict[str, Any] = []

        # 新しいセッションを追加
        session_dict = session.get_session_context()
        sessions_data.append(session_dict)

        # ファイルに保存
        try:
            with Path(file_path).open("w", encoding="utf-8") as file:
                yaml.dump(sessions_data, file, default_flow_style=False, allow_unicode=True, sort_keys=False)
        except Exception as e:
            msg = f"学習セッションの保存に失敗しました: {e!s}"
            raise ValidationError(msg) from e

    def find_learning_session(self, project_name: str, episode_number: int) -> LearningSession | None:
        """学習セッションを検索"""
        file_path = self._get_learning_session_path(project_name)

        if not file_path.exists():
            return None

        try:
            with Path(file_path).open(encoding="utf-8") as file:
                sessions_data: dict[str, Any] = yaml.safe_load(file) or []

            # 指定されたエピソードのセッションを検索
            for session_dict in sessions_data:
                if session_dict["episode_number"] == episode_number:
                    # 辞書からLearningSessionオブジェクトを復元
                    return LearningSession(
                        project_name=session_dict["project_name"],
                        episode_number=session_dict["episode_number"],
                        start_time=datetime.fromisoformat(session_dict["start_time"]),
                        writing_environment=session_dict.get("writing_environment"),
                        target_audience=session_dict.get("target_audience"),
                        writing_goal=session_dict.get("writing_goal"),
                        end_time=datetime.fromisoformat(session_dict["end_time"])
                        if session_dict.get("end_time")
                        else None,
                        total_writing_time=session_dict.get("total_writing_time", 0),
                        is_completed=session_dict.get("is_completed", False),
                    )

            return None

        except Exception as e:
            msg = f"学習セッションの読み込みに失敗しました: {e!s}"
            raise ValidationError(msg) from e

    def get_quality_statistics(self, project_name: str) -> dict[str, Any]:
        """品質統計を取得"""
        quality_record = self.find_by_project_name(project_name)

        if not quality_record:
            return {}

        return quality_record.get_learning_summary()
