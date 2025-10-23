"""Claude Code連携セッション

SPEC-CLAUDE-001に基づくClaude Code連携システムのエンティティ
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

# from noveler.domain.entities.file_quality_check_session import FileQualityCheckSession
from noveler.domain.value_objects.claude_session_id import ClaudeSessionId
from noveler.domain.value_objects.error_export_format import ErrorExportFormat
from noveler.domain.value_objects.integration_status import IntegrationStatus
from noveler.domain.value_objects.project_time import project_now


@dataclass
class ErrorCollection:
    """エラー情報のコレクション"""

    quality_sessions: list[object] = field(default_factory=list)
    total_errors: int = 0
    syntax_errors: int = 0
    type_errors: int = 0
    style_errors: int = 0

    def add_quality_session(self, session: object) -> None:
        """品質チェックセッションを追加

        Args:
            session: 品質チェックセッション
        """
        if session not in self.quality_sessions:
            self.quality_sessions.append(session)
            self._update_statistics()

    def remove_quality_session(self, session: object) -> None:
        """品質チェックセッションを削除

        Args:
            session: 品質チェックセッション
        """
        if session in self.quality_sessions:
            self.quality_sessions.remove(session)
            self._update_statistics()

    def _update_statistics(self) -> None:
        """統計情報更新"""
        self.total_errors = 0
        self.syntax_errors = 0
        self.type_errors = 0
        self.style_errors = 0

        for session in self.quality_sessions:
            if session.has_errors():
                session_errors = session.get_error_details()
                self.total_errors += len(session_errors)

                for error in session_errors:
                    error_code = error.get("code", "")
                    if error_code.startswith(("E9", "F")):
                        self.syntax_errors += 1
                    elif error_code.startswith("ANN"):
                        self.type_errors += 1
                    else:
                        self.style_errors += 1

    def get_error_summary(self) -> dict[str, int]:
        """エラー要約取得

        Returns:
            エラー種別ごとの統計
        """
        return {
            "total": self.total_errors,
            "syntax": self.syntax_errors,
            "type": self.type_errors,
            "style": self.style_errors,
        }

    def has_errors(self) -> bool:
        """エラー有無判定

        Returns:
            エラーがあるかどうか
        """
        return self.total_errors > 0

    def get_high_priority_sessions(self) -> list[object]:
        """高優先度セッション取得

        Returns:
            構文エラーを含むセッション一覧
        """
        return [
            session for session in self.quality_sessions if session.has_errors() and self._has_syntax_errors(session)
        ]

    def _has_syntax_errors(self, session: object) -> bool:
        """構文エラー有無判定

        Args:
            session: 品質チェックセッション

        Returns:
            構文エラーがあるかどうか
        """
        errors: Any = session.get_error_details()
        return any(error.get("code", "").startswith(("E9", "F")) for error in errors)


@dataclass
class SuggestionMetadata:
    """修正提案メタデータ"""

    created_at: datetime = field(default_factory=lambda: project_now().datetime)
    format_used: ErrorExportFormat | None = None
    priority_focus: str = "all"
    suggestion_count: int = 0
    estimated_fix_time_minutes: int = 0

    def calculate_fix_time(self, error_collection: ErrorCollection) -> None:
        """修正時間推定

        Args:
            error_collection: エラーコレクション
        """
        summary = error_collection.get_error_summary()

        # エラー種別ごとの修正時間(分)
        syntax_time = summary["syntax"] * 5  # 構文エラー: 5分/件
        type_time = summary["type"] * 2  # 型エラー: 2分/件
        style_time = summary["style"] * 1  # スタイルエラー: 1分/件

        self.estimated_fix_time_minutes = syntax_time + type_time + style_time
        self.suggestion_count = summary["total"]


class ClaudeIntegrationSession:
    """Claude Code連携セッション

    Claude Code連携システムの中核エンティティ
    リアルタイム監視システムからのエラー情報をClaude向けに変換・出力する
    """

    def __init__(
        self, session_id: ClaudeSessionId | None = None, error_collection: ErrorCollection | None = None
    ) -> None:
        """初期化

        Args:
            session_id: セッションID(Noneの場合は自動生成)
            error_collection: エラーコレクション(Noneの場合は空のコレクション)
        """
        self.session_id = session_id or ClaudeSessionId.generate()
        self.error_collection = error_collection or ErrorCollection()
        self.integration_status = IntegrationStatus.initial()
        self.export_timestamp: datetime | None = None
        self.suggestion_metadata = SuggestionMetadata()

        # エンティティの不変条件をチェック
        self._validate_entity()

    def _validate_entity(self) -> None:
        """エンティティの不変条件チェック"""
        if not isinstance(self.session_id, ClaudeSessionId):
            msg = "session_idはClaudeSessionIdである必要があります"
            raise TypeError(msg)

        if not isinstance(self.error_collection, ErrorCollection):
            msg = "error_collectionはErrorCollectionである必要があります"
            raise TypeError(msg)

        if not isinstance(self.integration_status, IntegrationStatus):
            msg = "integration_statusはIntegrationStatusである必要があります"
            raise TypeError(msg)

    def add_quality_sessions(self, sessions: list[object]) -> None:
        """品質チェックセッション群追加

        Args:
            sessions: 品質チェックセッション一覧
        """
        for session in sessions:
            self.error_collection.add_quality_session(session)

        # メタデータ更新
        self.suggestion_metadata.calculate_fix_time(self.error_collection)

    def export_for_claude(self, format_config: ErrorExportFormat) -> dict[str, Any]:
        """Claude向けエクスポート実行

        Args:
            format_config: 出力フォーマット設定

        Returns:
            Claude向けエラー情報
        """
        try:
            # エクスポート実行
            export_data: dict[str, Any] = self._create_export_data(format_config)

            # 成功状態更新
            self.integration_status = self.integration_status.with_successful_export()
            self.export_timestamp = project_now().datetime
            self.suggestion_metadata.format_used = format_config

            return export_data

        except Exception as e:
            # 失敗状態更新
            self.integration_status = self.integration_status.with_failed_export(str(e))
            raise

    def _create_export_data(self, format_config: ErrorExportFormat) -> dict[str, Any]:
        """エクスポートデータ作成

        Args:
            format_config: フォーマット設定

        Returns:
            エクスポートデータ
        """
        errors: list[Any] = []

        for session in self.error_collection.quality_sessions:
            if not session.has_errors():
                continue

            session_errors = session.get_error_details()

            # ファイル別エラー数制限
            limited_errors = session_errors[: format_config.max_errors_per_file]

            for error in limited_errors:
                claude_error = {
                    "file_path": str(session.file_path).replace("\\", "/"),
                    "line_number": error.get("line_number", 0),
                    "error_type": self._classify_error_type(error.get("code", "")),
                    "error_code": error.get("code", "UNKNOWN"),
                    "message": error.get("message", ""),
                    "priority": self._get_error_priority(error.get("code", "")),
                }

                # 修正提案追加(設定に基づく)
                if format_config.include_suggestions:
                    claude_error["claude_suggestion"] = self._generate_suggestion(error)

                # 優先度フィルタ適用
                if self._passes_priority_filter(claude_error["priority"], format_config.priority_filter):
                    errors.append(claude_error)

        return {
            "session_id": str(self.session_id),
            "timestamp": project_now().datetime.isoformat(),
            "format_version": format_config.structure_version,
            "errors": errors,
            "summary": {**self.error_collection.get_error_summary(), "by_priority": self._count_by_priority(errors)},
            "metadata": {
                "estimated_fix_time_minutes": self.suggestion_metadata.estimated_fix_time_minutes,
                "suggestion_count": len(errors),
                "export_format": str(format_config),
            },
        }

    def _classify_error_type(self, error_code: str) -> str:
        """エラータイプ分類

        Args:
            error_code: エラーコード

        Returns:
            エラータイプ
        """
        if error_code.startswith(("E9", "F")):
            return "syntax"
        if error_code.startswith("ANN"):
            return "type"
        return "style"

    def _get_error_priority(self, error_code: str) -> str:
        """エラー優先度取得

        Args:
            error_code: エラーコード

        Returns:
            エラー優先度
        """
        if error_code.startswith(("E9", "F")):
            return "high"  # 構文エラーは高優先度
        if error_code.startswith("ANN"):
            return "medium"  # 型エラーは中優先度
        return "low"  # スタイルエラーは低優先度

    def _generate_suggestion(self, error: dict[str, Any]) -> str:
        """修正提案生成

        Args:
            error: エラー情報

        Returns:
            修正提案
        """
        code = error.get("code", "")
        suggestions = {
            "E999": "Python構文エラー - 括弧、クォート、インデントを確認してください",
            "F401": "未使用インポート - 不要なimport文を削除してください",
            "ANN001": "型注釈不足 - 引数に型注釈を追加してください(例: def func(x: int) -> str:)",
            "ANN201": "戻り値型注釈不足 - 戻り値の型注釈を追加してください",
        }
        return suggestions.get(code, f"エラーコード {code} の修正が必要です")

    def _passes_priority_filter(self, priority: str, filter_setting: str) -> bool:
        """優先度フィルタ判定

        Args:
            priority: エラー優先度
            filter_setting: フィルタ設定

        Returns:
            フィルタを通過するかどうか
        """
        if filter_setting == "all":
            return True
        return priority == filter_setting

    def _count_by_priority(self, errors: list[dict[str, Any]]) -> dict[str, int]:
        """優先度別カウント

        Args:
            errors: エラー一覧

        Returns:
            優先度別カウント
        """
        counts = {"high": 0, "medium": 0, "low": 0}
        for error in errors:
            priority = error.get("priority", "low")
            if priority in counts:
                counts[priority] += 1
        return counts

    def activate_integration(self) -> None:
        """連携をアクティベート"""
        self.integration_status = self.integration_status.activate()

    def deactivate_integration(self) -> None:
        """連携を非アクティベート"""
        self.integration_status = self.integration_status.deactivate()

    def get_export_summary(self) -> dict[str, Any]:
        """エクスポート概要取得

        Returns:
            エクスポート概要情報
        """
        return {
            "session_id": str(self.session_id),
            "is_active": self.integration_status.is_active,
            "total_errors": self.error_collection.total_errors,
            "has_high_priority": len(self.error_collection.get_high_priority_sessions()) > 0,
            "last_export": self.export_timestamp,
            "estimated_fix_time": self.suggestion_metadata.estimated_fix_time_minutes,
            "success_rate": self.integration_status.get_success_rate(),
        }

    def __str__(self) -> str:
        """文字列表現"""
        return f"ClaudeIntegrationSession({self.session_id}, errors={self.error_collection.total_errors})"

    def __repr__(self) -> str:
        """デバッグ用文字列表現"""
        return (
            f"ClaudeIntegrationSession("
            f"session_id={self.session_id!r}, "
            f"total_errors={self.error_collection.total_errors}, "
            f"is_active={self.integration_status.is_active}"
            f")"
        )
