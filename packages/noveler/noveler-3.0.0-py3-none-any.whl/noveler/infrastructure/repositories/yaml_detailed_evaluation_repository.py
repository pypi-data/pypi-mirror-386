#!/usr/bin/env python3
"""YAML詳細評価リポジトリ 実装

DetailedEvaluationSessionとDetailedAnalysisResultをYAMLファイルに
永続化するインフラ層実装。Claude Code分析結果の長期保存と
再利用を可能にする。
"""

from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from noveler.domain.entities.category_analysis_result import AnalysisResultId, CategoryAnalysisResult
from noveler.domain.entities.detailed_evaluation_session import (
    DetailedEvaluationSession,
    EvaluationSessionStatus,
    SessionId,
)
from noveler.domain.repositories.detailed_evaluation_repository import DetailedEvaluationRepository, RepositoryError
from noveler.domain.services.detailed_analysis_engine import DetailedAnalysisResult
from noveler.domain.value_objects.a31_evaluation_category import A31EvaluationCategory
from noveler.domain.value_objects.episode_number import EpisodeNumber
from noveler.domain.value_objects.improvement_suggestion import ImprovementSuggestion
from noveler.domain.value_objects.line_specific_feedback import IssueSeverity, IssueType, LineSpecificFeedback


class YamlDetailedEvaluationRepository(DetailedEvaluationRepository):
    """YAML詳細評価リポジトリ 実装

    評価セッションと分析結果をYAMLファイルに永続化。
    Claude Code分析結果の構造化保存と効率的な検索を提供。
    """

    def __init__(self, storage_path: str = "temp/detailed_evaluations") -> None:
        """YAML詳細評価リポジトリ初期化

        Args:
            storage_path: YAML保存ディレクトリパス
        """
        self._storage_path = Path(storage_path)
        self._sessions_dir = self._storage_path / "sessions"
        self._results_dir = self._storage_path / "results"

        # ディレクトリを作成
        self._ensure_directories()

    def save_evaluation_session(self, session: DetailedEvaluationSession) -> None:
        """評価セッションをYAMLファイルに保存

        Args:
            session: 保存対象の評価セッション

        Raises:
            RepositoryError: 保存に失敗した場合
        """
        try:
            session_data: dict[str, Any] = self._serialize_session(session)
            file_path = self._get_session_file_path(session.project_name, session.episode_number)

            with file_path.open("w", encoding="utf-8") as f:
                yaml.dump(session_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

        except Exception as e:
            msg = f"評価セッション保存に失敗しました: {e!s}"
            raise RepositoryError(msg) from e

    def save_analysis_result(self, result: DetailedAnalysisResult) -> None:
        """分析結果をYAMLファイルに保存

        Args:
            result: 保存対象の分析結果

        Raises:
            RepositoryError: 保存に失敗した場合
        """
        try:
            result_data: dict[str, Any] = self._serialize_analysis_result(result)
            file_path = self._get_result_file_path(result.session_id)

            with file_path.open("w", encoding="utf-8") as f:
                yaml.dump(result_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

        except Exception as e:
            msg = f"分析結果保存に失敗しました: {e!s}"
            raise RepositoryError(msg) from e

    def get_evaluation_session(
        self, project_name: str, episode_number: EpisodeNumber
    ) -> DetailedEvaluationSession | None:
        """評価セッションをYAMLファイルから取得

        Args:
            project_name: プロジェクト名
            episode_number: エピソード番号

        Returns:
            Optional[DetailedEvaluationSession]: 見つかった場合は評価セッション
        """
        try:
            file_path = self._get_session_file_path(project_name, episode_number)

            if not file_path.exists():
                return None

            with file_path.open(encoding="utf-8") as f:
                session_data: dict[str, Any] = yaml.safe_load(f)

            return self._deserialize_session(session_data)

        except Exception as e:
            msg = f"評価セッション取得に失敗しました: {e!s}"
            raise RepositoryError(msg) from e

    def get_analysis_result(self, session_id: str) -> DetailedAnalysisResult | None:
        """分析結果をYAMLファイルから取得

        Args:
            session_id: セッションID

        Returns:
            Optional[DetailedAnalysisResult]: 見つかった場合は分析結果
        """
        try:
            file_path = self._get_result_file_path(session_id)

            if not file_path.exists():
                return None

            with file_path.open(encoding="utf-8") as f:
                result_data: dict[str, Any] = yaml.safe_load(f)

            return self._deserialize_analysis_result(result_data)

        except Exception as e:
            msg = f"分析結果取得に失敗しました: {e!s}"
            raise RepositoryError(msg) from e

    def list_evaluation_sessions(self, project_name: str) -> list[DetailedEvaluationSession]:
        """プロジェクトの評価セッション一覧を取得

        Args:
            project_name: プロジェクト名

        Returns:
            list[DetailedEvaluationSession]: 評価セッション一覧
        """
        sessions = []
        try:
            pattern = f"{project_name}_episode_*.yaml"

            for file_path in self._sessions_dir.glob(pattern):
                with file_path.open(encoding="utf-8") as f:
                    session_data: dict[str, Any] = yaml.safe_load(f)
                session = self._deserialize_session(session_data)
                sessions.append(session)

            # エピソード番号順にソート
            sessions.sort(key=lambda s: s.episode_number.value)
            return sessions

        except Exception as e:
            msg = f"評価セッション一覧取得に失敗しました: {e!s}"
            raise RepositoryError(msg) from e

    def delete_evaluation_session(self, project_name: str, episode_number: EpisodeNumber) -> bool:
        """評価セッションを削除

        Args:
            project_name: プロジェクト名
            episode_number: エピソード番号

        Returns:
            bool: 削除に成功した場合True
        """
        try:
            file_path = self._get_session_file_path(project_name, episode_number)

            if not file_path.exists():
                return False

            file_path.unlink()

            # 対応する分析結果も削除を試行
            session = self.get_evaluation_session(project_name, episode_number)
            if session:
                result_path = self._get_result_file_path(session.session_id.value)
                if result_path.exists():
                    result_path.unlink()

            return True

        except Exception as e:
            msg = f"評価セッション削除に失敗しました: {e!s}"
            raise RepositoryError(msg) from e

    def exists_evaluation_session(self, project_name: str, episode_number: EpisodeNumber) -> bool:
        """評価セッションの存在確認

        Args:
            project_name: プロジェクト名
            episode_number: エピソード番号

        Returns:
            bool: 存在する場合True
        """
        file_path = self._get_session_file_path(project_name, episode_number)
        return file_path.exists()

    def _ensure_directories(self) -> None:
        """必要なディレクトリを作成"""
        self._sessions_dir.mkdir(parents=True, exist_ok=True)
        self._results_dir.mkdir(parents=True, exist_ok=True)

    def _get_session_file_path(self, project_name: str, episode_number: EpisodeNumber) -> Path:
        """セッションファイルパスを取得"""
        safe_project_name = self._sanitize_filename(project_name)
        filename = f"{safe_project_name}_episode_{episode_number.value:03d}.yaml"
        return self._sessions_dir / filename

    def _get_result_file_path(self, session_id: str) -> Path:
        """分析結果ファイルパスを取得"""
        filename = f"result_{session_id}.yaml"
        return self._results_dir / filename

    def _sanitize_filename(self, filename: str) -> str:
        """ファイル名を安全な形に変換"""
        # 危険な文字を置換
        unsafe_chars = '<>:"/\\|?*'
        safe_filename = filename
        for char in unsafe_chars:
            safe_filename = safe_filename.replace(char, "_")
        return safe_filename

    def _serialize_session(self, session: DetailedEvaluationSession) -> dict[str, Any]:
        """評価セッションをシリアライズ"""
        return {
            "session_id": session.session_id.value,
            "project_name": session.project_name,
            "episode_number": session.episode_number.value,
            "episode_content": session.episode_content,
            "status": session.status.value,
            "created_at": session.created_at.isoformat(),
            "started_at": session.started_at.isoformat() if session.started_at else None,
            "completed_at": session.completed_at.isoformat() if session.completed_at else None,
            "overall_score": session.overall_score,
            "category_analyses": [self._serialize_category_result(result) for result in session.category_analyses],
            "line_feedbacks": [self._serialize_line_feedback(feedback) for feedback in session.line_feedbacks],
        }

    def _serialize_category_result(self, result: CategoryAnalysisResult) -> dict[str, Any]:
        """カテゴリ分析結果をシリアライズ"""
        return {
            "result_id": result.result_id.value,
            "category": result.category.value,
            "score": result.score,
            "issues_found": result.issues_found,
            "suggestions": result.suggestions,
            "analyzed_at": result.analyzed_at.isoformat(),
            "detailed_suggestions": [
                self._serialize_improvement_suggestion(suggestion) for suggestion in result.detailed_suggestions
            ],
            "confidence_score": result.confidence_score,
        }

    def _serialize_improvement_suggestion(self, suggestion: ImprovementSuggestion) -> dict[str, Any]:
        """改善提案をシリアライズ"""
        return {
            "content": suggestion.content,
            "suggestion_type": suggestion.suggestion_type.value,
            "confidence": suggestion.confidence,
            "fix_example": suggestion.fix_example,
            "expected_impact": suggestion.expected_impact,
            "implementation_difficulty": suggestion.implementation_difficulty,
        }

    def _serialize_line_feedback(self, feedback: LineSpecificFeedback) -> dict[str, Any]:
        """行別フィードバックをシリアライズ"""
        return {
            "line_number": feedback.line_number,
            "original_text": feedback.original_text,
            "issue_type": feedback.issue_type.value,
            "severity": feedback.severity.value,
            "suggestion": self._serialize_improvement_suggestion(feedback.suggestion),
            "confidence": feedback.confidence,
            "auto_fixable": feedback.auto_fixable,
            "context_lines": feedback.context_lines,
        }

    def _serialize_analysis_result(self, result: DetailedAnalysisResult) -> dict[str, Any]:
        """分析結果をシリアライズ"""
        return {
            "session_id": result.session_id.value if hasattr(result.session_id, "value") else result.session_id,
            "overall_score": result.overall_score,
            "confidence_score": result.confidence_score,
            "category_results": [
                self._serialize_category_result(category_result) for category_result in result.category_results
            ],
            "line_feedbacks": [self._serialize_line_feedback(feedback) for feedback in result.line_feedbacks],
            "analysis_summary": result.analysis_summary,
        }

    def _deserialize_session(self, data: dict[str, Any]) -> DetailedEvaluationSession:
        """評価セッションをデシリアライズ"""
        session_id = SessionId(data["session_id"])
        episode_number = EpisodeNumber(data["episode_number"])
        status = EvaluationSessionStatus(data["status"])

        created_at = datetime.fromisoformat(data["created_at"])
        started_at = datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None
        completed_at = datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None

        # セッションを再構築
        session = DetailedEvaluationSession._create_with_id(
            session_id=session_id,
            project_name=data["project_name"],
            episode_number=episode_number,
            episode_content=data["episode_content"],
            status=status,
            created_at=created_at,
            started_at=started_at,
            completed_at=completed_at,
            overall_score=data.get("overall_score"),
        )

        # カテゴリ分析結果を復元
        for category_data in data.get("category_analyses", []):
            category_result = self._deserialize_category_result(category_data)
            session.add_category_analysis(category_result)

        # 行別フィードバックを復元
        for feedback_data in data.get("line_feedbacks", []):
            line_feedback = self._deserialize_line_feedback(feedback_data)
            session.add_line_feedback(line_feedback)

        return session

    def _deserialize_category_result(self, data: dict[str, Any]) -> CategoryAnalysisResult:
        """カテゴリ分析結果をデシリアライズ"""
        result_id = AnalysisResultId(data["result_id"])
        category = A31EvaluationCategory(data["category"])
        analyzed_at = datetime.fromisoformat(data["analyzed_at"])

        detailed_suggestions = [
            self._deserialize_improvement_suggestion(suggestion_data)
            for suggestion_data in data.get("detailed_suggestions", [])
        ]

        return CategoryAnalysisResult(
            result_id=result_id,
            category=category,
            score=data["score"],
            issues_found=data["issues_found"],
            suggestions=data["suggestions"],
            analyzed_at=analyzed_at,
            detailed_suggestions=detailed_suggestions,
            confidence_score=data.get("confidence_score"),
        )

    def _deserialize_improvement_suggestion(self, data: dict[str, Any]) -> ImprovementSuggestion:
        """改善提案をデシリアライズ"""
        from noveler.domain.value_objects.improvement_suggestion import SuggestionType

        suggestion_type = SuggestionType(data["suggestion_type"])

        return ImprovementSuggestion(
            content=data["content"],
            suggestion_type=suggestion_type,
            confidence=data.get("confidence", 0.8),
            fix_example=data.get("fix_example"),
            expected_impact=data.get("expected_impact"),
            implementation_difficulty=data.get("implementation_difficulty", "medium"),
        )

    def _deserialize_line_feedback(self, data: dict[str, Any]) -> LineSpecificFeedback:
        """行別フィードバックをデシリアライズ"""

        issue_type = IssueType(data["issue_type"])
        severity = IssueSeverity(data["severity"])
        suggestion = self._deserialize_improvement_suggestion(data["suggestion"])

        return LineSpecificFeedback(
            line_number=data["line_number"],
            original_text=data["original_text"],
            issue_type=issue_type,
            severity=severity,
            suggestion=suggestion,
            confidence=data.get("confidence", 1.0),
            auto_fixable=data.get("auto_fixable", False),
            context_lines=data.get("context_lines", []),
        )

    def _deserialize_analysis_result(self, data: dict[str, Any]) -> DetailedAnalysisResult:
        """分析結果をデシリアライズ"""
        category_results = [
            self._deserialize_category_result(category_data) for category_data in data["category_results"]
        ]

        line_feedbacks = [self._deserialize_line_feedback(feedback_data) for feedback_data in data["line_feedbacks"]]

        session_identifier = data.get("session_id")
        session_id = SessionId(session_identifier) if session_identifier is not None else SessionId.generate()

        return DetailedAnalysisResult(
            session_id=session_id,
            overall_score=data["overall_score"],
            category_results=category_results,
            line_feedbacks=line_feedbacks,
            confidence_score=data["confidence_score"],
            analysis_summary=data["analysis_summary"],
        )
