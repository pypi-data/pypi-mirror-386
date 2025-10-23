#!/usr/bin/env python3
# File: src/noveler/infrastructure/repositories/yaml_quality_record_repository.py
# Purpose: Persist quality-related project data (records, revision history,
#          episode management) to YAML while providing transactional helpers.
# Context: Infrastructure layer component used by Noveler services and tools.
#          Relies on PathService adapters and domain entities for conversion.
"""Infrastructure repositories that persist quality artefacts in YAML format."""

import shutil
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from noveler.domain.entities.quality_record import QualityRecord, QualityRecordEntry
from noveler.domain.exceptions import QualityRecordError, RecordTransactionError
from noveler.domain.repositories.quality_record_repository import (
    EpisodeManagementRepository,
    QualityRecordRepository,
    RecordTransactionManager,
    RevisionHistoryRepository,
)
from noveler.domain.value_objects.quality_check_result import (
    AutoFix,
    CategoryScores,
    QualityCheckResult,
    QualityError,
    QualityScore,
)
from noveler.infrastructure.utils.yaml_utils import YAMLHandler


class YamlQualityRecordRepository(QualityRecordRepository):
    """YAML品質記録リポジトリ実装"""

    def __init__(self, base_path: Path | str) -> None:
        self._base_path = base_path

    def find_by_project(self, project_name: str) -> QualityRecord | None:
        """プロジェクト名で品質記録を検索"""
        file_path = self._get_quality_record_file_path(project_name)

        if not file_path.exists():
            return None

        try:
            with file_path.open(encoding="utf-8") as f:
                data = yaml.safe_load(f)

            return self._deserialize_quality_record(data)

        except yaml.YAMLError as e:
            msg = f"Failed to parse quality record file: {e!s}"
            raise QualityRecordError(None, msg) from e
        except Exception as e:
            msg = f"Failed to load quality record: {e!s}"
            raise QualityRecordError(None, msg) from e

    def save(self, quality_record: QualityRecord) -> None:
        """品質記録を保存"""
        file_path = self._get_quality_record_file_path(quality_record.project_name)

        # ディレクトリ作成
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # バックアップ作成(既存ファイルがある場合)
        if file_path.exists():
            self._create_backup(file_path)

        try:
            # YAML形式で保存
            data = quality_record.to_persistence_dict()

            # YAMLHandlerを使用して整形付き保存を試みる
            try:
                # from noveler.infrastructure.utils.yaml_utils import YAMLHandler  # Moved to top-level

                YAMLHandler.save_yaml(file_path, data, use_formatter=False, create_backup=False)
            except ImportError:
                # フォールバック: 従来の方法で保存
                with file_path.open("w", encoding="utf-8") as f:
                    yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False, indent=2)

        except Exception as e:
            msg = f"Failed to save quality record: {e!s}"
            raise QualityRecordError(None, msg) from e

        self._sync_legacy_management_alias(file_path)

    def exists(self, project_name: str) -> bool:
        """指定プロジェクトの記録が存在するか"""
        file_path = self._get_quality_record_file_path(project_name)
        return file_path.exists()

    def delete(self, project_name: str) -> bool:
        """品質記録を削除"""
        file_path = self._get_quality_record_file_path(project_name)

        if not file_path.exists():
            return False

        try:
            # バックアップ作成後削除
            self._create_backup(file_path)
            file_path.unlink()
            return True
        except Exception as e:
            msg = f"Failed to delete quality record: {e!s}"
            raise QualityRecordError(None, msg) from e

    def save_check_result(self, record: dict[str, Any]) -> None:
        """品質チェック結果を保存

        Args:
            record: 品質チェック記録データ
        """
        # recordから必要な情報を抽出
        project_name = record.get("project_name", "")
        episode_number = record.get("episode_number", 0)
        quality_result_data: dict[str, Any] = record.get("quality_result", {})

        # 既存の品質記録を取得または新規作成
        quality_record = self.find_by_project(project_name)
        if quality_record is None:
            quality_record = QualityRecord(project_name)

        # 品質チェック結果を追加
        if quality_result_data:
            quality_result = self._deserialize_quality_check_result(quality_result_data)
        else:
            quality_result = self._build_minimal_quality_check_result(record)
        quality_record.add_quality_check_result(
            quality_result,
            metadata=record.get("metadata", {}),
        )

        # 保存
        self.save(quality_record)

    def _get_quality_record_file_path(self, project_name: str) -> Path:
        """Resolve the YAML file path for a project's quality record.

        Purpose:
            Locate the existing quality record when present while ensuring new
            saves default to `<base_path>/<project_name>/管理/品質記録.yaml`.

        Args:
            project_name: Logical project identifier used to namespace records.

        Returns:
            Path: Fully-qualified path where the YAML record should be stored.
        """
        from noveler.infrastructure.adapters.path_service_adapter import create_path_service

        base_path = self._base_path if isinstance(self._base_path, Path) else Path(self._base_path)
        if project_name:
            if base_path.name == project_name:
                preferred_root = base_path
            else:
                preferred_root = base_path / project_name
        else:
            preferred_root = base_path

        candidates: list[Path] = []
        for candidate in (preferred_root, base_path):
            if candidate not in candidates:
                candidates.append(candidate)

        for candidate in candidates:
            path_service = create_path_service(candidate)
            quality_file = path_service.get_quality_record_file()
            if quality_file.exists():
                return quality_file

        path_service = create_path_service(preferred_root)
        return path_service.get_quality_record_file()

    def _create_backup(self, file_path: Path) -> None:
        """バックアップファイル作成"""
        backup_dir = file_path.parent / ".backup"
        backup_dir.mkdir(exist_ok=True)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"{file_path.stem}_{timestamp}.yaml"

        # import shutil # Moved to top-level

        shutil.copy2(file_path, backup_path)

    def _sync_legacy_management_alias(self, file_path: Path) -> None:
        """Ensure legacy 'management' directory reflects the latest record."""

        try:
            parent = file_path.parent
            if parent.name == "management":
                return

            legacy_dir = parent.parent / "management"
            legacy_dir.mkdir(parents=True, exist_ok=True)
            legacy_path = legacy_dir / file_path.name
            shutil.copy2(file_path, legacy_path)
        except Exception:
            # 非クリティカルな互換フォールバックのため、例外は握りつぶす
            pass

    def _deserialize_quality_record(self, data: dict[str, Any]) -> QualityRecord:
        """辞書データから品質記録エンティティを復元"""
        metadata = data.get("metadata", {})
        project_name = metadata.get("project_name", "")

        # エントリリストの復元
        entries = []
        for entry_data in data.get("quality_checks", []):
            quality_result = self._deserialize_quality_check_result(entry_data)

            entry = QualityRecordEntry(
                id=entry_data.get("id", ""),
                quality_result=quality_result,
                created_at=datetime.fromisoformat(entry_data.get("created_at", datetime.now(timezone.utc).isoformat())),
                metadata=entry_data.get("metadata", {}),
            )

            entries.append(entry)

        return QualityRecord(project_name, entries)

    def _build_minimal_quality_check_result(self, record: dict[str, Any]) -> QualityCheckResult:
        """最小限の情報から品質チェック結果を構築"""

        base_score = float(record.get("score", 0.0))
        episode_number = int(record.get("episode_number", 1) or 1)

        score_vo = QualityScore.from_float(base_score)
        category_scores = CategoryScores(
            basic_style=score_vo,
            composition=score_vo,
            character_consistency=score_vo,
            readability=score_vo,
        )

        issues_data = record.get("issues", [])
        errors: list[QualityError] = []
        warnings: list[QualityError] = []

        for issue in issues_data:
            if isinstance(issue, dict):
                severity = str(issue.get("severity", "warning")).lower()
                if severity not in {"error", "warning", "info"}:
                    severity = "info"
                message = issue.get("message") or issue.get("description") or str(issue)
                issue_type = issue.get("type") or ("quality_error" if severity == "error" else "quality_warning")
                line_number = issue.get("line_number") or issue.get("line")
                if isinstance(line_number, int) and line_number < 1:
                    line_number = None
                quality_issue = QualityError(
                    type=str(issue_type),
                    message=str(message),
                    line_number=line_number,
                    severity=severity,
                    fixed=bool(issue.get("fixed", False)),
                    suggestion=issue.get("suggestion"),
                )
            else:
                issue_text = str(issue)
                quality_issue = QualityError(
                    type="note",
                    message=issue_text,
                    severity="info",
                    fixed=False,
                )
            if quality_issue.severity == "error":
                errors.append(quality_issue)
            else:
                warnings.append(quality_issue)

        auto_fix_data = record.get("auto_fixes", [])
        auto_fixes: list[AutoFix] = []
        for entry in auto_fix_data:
            if isinstance(entry, dict):
                auto_fixes.append(
                    AutoFix(
                        type=str(entry.get("type", "auto_fix")),
                        description=str(entry.get("description", "")),
                        count=int(entry.get("count", 0)),
                        affected_lines=entry.get("affected_lines"),
                    )
                )

        timestamp = datetime.now(timezone.utc)
        checker_version = str(record.get("checker_version", "legacy-bridge"))

        return QualityCheckResult(
            episode_number=episode_number,
            timestamp=timestamp,
            checker_version=checker_version,
            category_scores=category_scores,
            errors=errors,
            warnings=warnings,
            auto_fixes=auto_fixes,
            word_count=record.get("word_count"),
        )

    def _deserialize_quality_check_result(self, data: dict[str, Any]) -> QualityCheckResult:
        """品質チェック結果の復元"""
        results: Any = data.get("results", {})

        # カテゴリ別スコアの復元
        scores_data: dict[str, Any] = results.get("category_scores", {})
        category_scores = CategoryScores(
            basic_style=QualityScore.from_float(scores_data.get("basic_style", 0.0)),
            composition=QualityScore.from_float(scores_data.get("composition", 0.0)),
            character_consistency=QualityScore.from_float(scores_data.get("character_consistency", 0.0)),
            readability=QualityScore.from_float(scores_data.get("readability", 0.0)),
        )

        # エラー・警告・修正の復元
        # from noveler.domain.value_objects.quality_check_result import AutoFix, QualityError # Moved to top-level

        errors: list[Any] = []
        for error_data in results.get("errors", []):
            if isinstance(error_data, dict):
                errors.append(
                    QualityError(
                        type=error_data.get("type", ""),
                        message=error_data.get("message", ""),
                        line_number=error_data.get("line_number"),
                        severity=error_data.get("severity", "error"),
                        fixed=error_data.get("fixed", False),
                        suggestion=error_data.get("suggestion"),
                    )
                )

            else:
                errors.append(error_data)

        warnings = []
        for warning_data in results.get("warnings", []):
            if isinstance(warning_data, dict):
                warnings.append(
                    QualityError(
                        type=warning_data.get("type", ""),
                        message=warning_data.get("message", ""),
                        line_number=warning_data.get("line_number"),
                        severity=warning_data.get("severity", "warning"),
                        fixed=warning_data.get("fixed", False),
                        suggestion=warning_data.get("suggestion"),
                    )
                )

            else:
                warnings.append(warning_data)

        auto_fixes = []
        for fix_data in results.get("auto_fixes", []):
            if isinstance(fix_data, dict):
                auto_fixes.append(
                    AutoFix(
                        type=fix_data.get("type", ""),
                        description=fix_data.get("description", ""),
                        count=fix_data.get("count", 0),
                        affected_lines=fix_data.get("affected_lines"),
                    )
                )

            else:
                auto_fixes.append(fix_data)

        return QualityCheckResult(
            episode_number=data.get("episode_number", 0),
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.now(timezone.utc).isoformat())),
            checker_version=data.get("checker_version", "unknown"),
            category_scores=category_scores,
            errors=errors,
            warnings=warnings,
            auto_fixes=auto_fixes,
        )


class YamlEpisodeManagementRepository(EpisodeManagementRepository):
    """YAML話数管理リポジトリ実装"""

    def update_quality_scores(
        self, project_path: Path, episode_number: int, quality_result: QualityCheckResult
    ) -> None:
        """エピソード状態の更新"""
        from noveler.infrastructure.adapters.path_service_adapter import create_path_service

        path_service = create_path_service(project_path)
        file_path = path_service.get_episode_management_file()

        # ファイルが存在しない場合は初期化
        if not file_path.exists():
            file_path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "episodes": [],
                "metadata": {"last_updated": datetime.now(timezone.utc).isoformat(), "total_episodes": 0},
            }
        else:
            with file_path.open(encoding="utf-8") as f:
                data = yaml.safe_load(f) or {"episodes": [], "metadata": {}}

        # エピソード情報の更新または追加
        episodes = data.get("episodes", [])
        episode_found = False

        for episode in episodes:
            if episode.get("episode_number") == episode_number:
                # 既存エピソードの更新
                episode["quality_score"] = quality_result.overall_score.to_float()
                episode["last_check"] = quality_result.timestamp.isoformat()
                episode["error_count"] = quality_result.error_count
                episode["warning_count"] = quality_result.warning_count
                episode_found = True
                break

        if not episode_found:
            # 新規エピソードの追加
            new_episode = {
                "episode_number": episode_number,
                "quality_score": quality_result.overall_score.to_float(),
                "last_check": quality_result.timestamp.isoformat(),
                "error_count": quality_result.error_count,
                "warning_count": quality_result.warning_count,
                "status": "quality_checked",
            }
            episodes.append(new_episode)

        # メタデータ更新
        data["episodes"] = episodes
        data["metadata"]["last_updated"] = datetime.now(timezone.utc).isoformat()
        data["metadata"]["total_episodes"] = len(episodes)

        # ファイル保存
        with file_path.open("w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False, indent=2)

    def get_episode_info(self, project_path: Path, episode_number: int) -> dict[str, Any] | None:
        """エピソード情報取得"""
        from noveler.infrastructure.adapters.path_service_adapter import create_path_service

        path_service = create_path_service(project_path)
        file_path = path_service.get_episode_management_file()

        if not file_path.exists():
            return None

        try:
            with file_path.open(encoding="utf-8") as f:
                data = yaml.safe_load(f)

            episodes = data.get("episodes", [])
            for episode in episodes:
                if episode.get("episode_number") == episode_number:
                    return episode

            return None

        except Exception:
            return None

    def _build_minimal_quality_check_result(self, record: dict[str, Any]) -> QualityCheckResult:
        """フラットなレコードから最小限のQualityCheckResultを組み立てる互換関数"""
        score_val = 0.0
        try:
            score_val = float(record.get("score", 0.0))
        except Exception:
            score_val = 0.0

        category_scores = CategoryScores(
            basic_style=QualityScore.from_float(score_val),
            composition=QualityScore.from_float(0.0),
            character_consistency=QualityScore.from_float(0.0),
            readability=QualityScore.from_float(0.0),
        )

        issues = record.get("issues", []) or []
        errors: list[QualityError] = []
        for issue in issues:
            if isinstance(issue, dict):
                errors.append(
                    QualityError(
                        type=str(issue.get("type", "issue")),
                        message=str(issue.get("message", issue)),
                        line_number=issue.get("line_number"),
                        severity=str(issue.get("severity", "error")),
                        fixed=bool(issue.get("fixed", False)),
                        suggestion=issue.get("suggestion"),
                    )
                )
            else:
                errors.append(QualityError(type="issue", message=str(issue), severity="error"))

        return QualityCheckResult(
            episode_number=int(record.get("episode_number", 0) or 0),
            timestamp=datetime.now(timezone.utc),
            checker_version="minimal",
            category_scores=category_scores,
            errors=errors,
            warnings=[],
            auto_fixes=[],
        )


class YamlRevisionHistoryRepository(RevisionHistoryRepository):
    """YAML改訂履歴リポジトリ実装"""

    def add_quality_revision(self, project_path: Path, quality_result: "QualityCheckResult") -> None:
        """品質チェック改訂履歴の追加"""
        from noveler.infrastructure.adapters.path_service_adapter import create_path_service

        path_service = create_path_service(project_path)
        file_path = path_service.get_revision_history_file()

        # ファイルが存在しない場合は初期化
        if not file_path.exists():
            file_path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "revisions": [],
                "metadata": {"total_revisions": 0, "last_updated": datetime.now(timezone.utc).isoformat()},
            }
        else:
            with file_path.open(encoding="utf-8") as f:
                data = yaml.safe_load(f) or {"revisions": [], "metadata": {}}

        # 新しい改訂履歴エントリ作成
        revision_entry = {
            "id": f"quality-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{quality_result.episode_number}",
            "timestamp": quality_result.timestamp.isoformat(),
            "episode_number": quality_result.episode_number,
            "revision_type": "quality_check",
            "quality_score": quality_result.overall_score.to_float(),
            "error_count": quality_result.error_count,
            "warning_count": quality_result.warning_count,
            "auto_fix_count": quality_result.total_fixes_count,
            "checker_version": quality_result.checker_version,
            "description": f"Episode {quality_result.episode_number} quality check (Score: {quality_result.overall_score.to_float():.1f})",
        }

        # 履歴の先頭に追加(最新が先頭)
        revisions = data.get("revisions", [])
        revisions.insert(0, revision_entry)

        # メタデータ更新
        data["revisions"] = revisions
        data["metadata"]["total_revisions"] = len(revisions)
        data["metadata"]["last_updated"] = datetime.now(timezone.utc).isoformat()

        # ファイル保存
        with file_path.open("w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False, indent=2)

    def get_recent_revisions(self, project_path: Path, episode_number: int, limit: int = 10) -> list[dict[str, Any]]:
        """最近の改訂履歴取得"""
        from noveler.infrastructure.adapters.path_service_adapter import create_path_service

        path_service = create_path_service(project_path)
        file_path = path_service.get_revision_history_file()

        if not file_path.exists():
            return []

        try:
            with file_path.open(encoding="utf-8") as f:
                data = yaml.safe_load(f)

            revisions = data.get("revisions", [])

            # 指定エピソードの改訂履歴をフィルタ
            episode_revisions = [rev for rev in revisions if rev.get("episode_number") == episode_number]

            # 指定件数に制限
            return episode_revisions[:limit]

        except Exception:
            return []


class YamlRecordTransactionManager(RecordTransactionManager):
    """YAML記録トランザクションマネージャー実装"""

    def __init__(
        self,
        quality_record_repository: "QualityRecordRepository",
        episode_management_repository: "EpisodeManagementRepository",
        revision_history_repository: "RevisionHistoryRepository",
    ) -> None:
        self._quality_repo = quality_record_repository
        self._episode_repo = episode_management_repository
        self._revision_repo = revision_history_repository
        self._operations: list[callable] = []
        self._committed = False
        self._rolled_back = False

    @contextmanager
    def begin_transaction(self) -> None:
        """トランザクション開始"""
        transaction = YamlTransaction(
            quality_repo=self._quality_repo, episode_repo=self._episode_repo, revision_repo=self._revision_repo
        )

        try:
            yield transaction
            if not transaction._committed and not transaction._rolled_back:
                transaction.commit()
        except Exception as e:
            transaction.rollback()
            if isinstance(e, RecordTransactionError):
                raise
            msg = f"Transaction failed: {e!s}"
            raise RecordTransactionError("begin_transaction", msg, {"stage": "begin"}) from e


class YamlTransaction:
    """YAML取引実装"""

    def __init__(
        self,
        quality_repo: "QualityRecordRepository",
        episode_repo: "EpisodeManagementRepository",
        revision_repo: "RevisionHistoryRepository",
    ) -> None:
        self._quality_repo = quality_repo
        self._episode_repo = episode_repo
        self._revision_repo = revision_repo
        self._operations: list[callable] = []
        self._committed = False
        self._rolled_back = False

    def update_quality_record(self, quality_record: "QualityRecord") -> None:
        """品質記録の更新をトランザクションに追加"""
        self._operations.append(lambda: self._quality_repo.save(quality_record))

    def update_episode_management(
        self, project_path: Path, episode_number: int, quality_result: "QualityCheckResult"
    ) -> None:
        """話数管理の更新をトランザクションに追加"""
        self._operations.append(
            lambda: self._episode_repo.update_quality_scores(project_path, episode_number, quality_result)
        )

    def update_revision_history(self, project_path: Path, quality_result: "QualityCheckResult") -> None:
        """改訂履歴の更新をトランザクションに追加"""
        self._operations.append(lambda: self._revision_repo.add_quality_revision(project_path, quality_result))

    def commit(self) -> None:
        """トランザクションのコミット"""
        if self._committed or self._rolled_back:
            return

        try:
            # 全操作を順次実行
            for operation in self._operations:
                operation()

            self._committed = True

        except Exception as e:
            self.rollback()
            if isinstance(e, RecordTransactionError):
                raise
            msg = f"Transaction commit failed: {e!s}"
            raise RecordTransactionError("commit", msg, {"operations": len(self._operations)}) from e

    def rollback(self) -> None:
        """トランザクションのロールバック"""
        if self._committed or self._rolled_back:
            return

        # 実際のファイルシステムでのロールバックは複雑なため、
        # 現在の実装では操作の実行を停止する
        self._operations.clear()
        self._rolled_back = True
