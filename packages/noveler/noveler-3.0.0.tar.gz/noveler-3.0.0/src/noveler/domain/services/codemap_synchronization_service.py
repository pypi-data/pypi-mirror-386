#!/usr/bin/env python3
"""CODEMAP同期ドメインサービス

仕様書: SPEC-CODEMAP-AUTO-UPDATE-001
"""

from typing import Any

from noveler.domain.entities.codemap_entity import CircularImportIssue, CodeMapEntity
from noveler.domain.value_objects.commit_information import CommitInformation


class CodeMapSynchronizationService:
    """CODEMAP同期ビジネスロジック

    コミット情報からCODEMAPの自動更新を行うドメインサービス
    """

    def __init__(self) -> None:
        """初期化"""

    def synchronize_with_commit(self, codemap: CodeMapEntity, commit_info: CommitInformation) -> CodeMapEntity:
        """コミット情報に基づいてCODEMAPを同期

        Args:
            codemap: 現在のCODEMAPエンティティ
            commit_info: 最新コミット情報

        Returns:
            CodeMapEntity: 更新されたCODEMAPエンティティ
        """
        # 基本的なメタデータ更新
        codemap.update_from_commit(commit_info)

        # 実装完了状況の高度な分析・更新
        self._update_implementation_status(codemap, commit_info)

        # アーキテクチャ変更の検出と反映
        self._update_architecture_changes(codemap, commit_info)

        # B20準拠状況の更新
        self._update_compliance_status(codemap, commit_info)

        return codemap

    def _update_implementation_status(self, codemap: CodeMapEntity, commit_info: CommitInformation) -> None:
        """実装完了状況の詳細分析・更新"""

        # 循環インポート対策の完了検出
        self._detect_circular_import_fixes(codemap, commit_info)

        # バレルモジュール実装の検出
        self._detect_barrel_module_implementation(codemap, commit_info)

        # DDD層分離違反修正の検出
        self._detect_layer_violation_fixes(codemap, commit_info)

    def _detect_circular_import_fixes(self, codemap: CodeMapEntity, commit_info: CommitInformation) -> None:
        """循環インポート修正の自動検出"""

        # 循環インポート関連ファイルの変更を検出

        changed_files = [str(f) for f in commit_info.changed_files]

        from pathlib import Path as _P

        for issue in codemap.circular_import_issues:
            if issue.is_completed():
                continue

            # 該当ファイルが変更されているかチェック
            issue_file = str(issue.location)
            issue_basename = _P(issue_file).name
            # 文字列比較で安全に部分一致を判定（basename でも許容）
            if any((issue_file in changed_file) or (issue_basename in changed_file) for changed_file in changed_files):
                # コミットメッセージで修正確認
                if self._is_fix_commit_for_issue(commit_info, issue):
                    issue.mark_completed(commit_info.short_hash)

    def _detect_barrel_module_implementation(self, codemap: CodeMapEntity, commit_info: CommitInformation) -> None:
        """バレルモジュール実装の検出"""

        # commands/__init__.pyの変更を検出
        commands_init_files = [f for f in commit_info.changed_files if "commands/__init__.py" in f]

        if commands_init_files:
            # バレルモジュール関連の問題を完了としてマーク
            for issue in codemap.circular_import_issues:
                if "バレルモジュール" in issue.solution and not issue.is_completed():
                    issue.mark_completed(commit_info.short_hash)

    def _detect_layer_violation_fixes(self, codemap: CodeMapEntity, commit_info: CommitInformation) -> None:
        """DDD層分離違反修正の検出"""

        # アプリケーション層ファイルの変更を検出
        app_layer_changes = [f for f in commit_info.changed_files if "noveler/application/" in f]

        if app_layer_changes and "layer" in commit_info.commit_message.lower():
            # レイヤー依存違反修正として認識
            for issue in codemap.circular_import_issues:
                if ("依存" in issue.issue or "layer" in issue.issue.lower()) and not issue.is_completed():
                    issue.mark_completed(commit_info.short_hash)

    def _update_architecture_changes(self, codemap: CodeMapEntity, commit_info: CommitInformation) -> None:
        """アーキテクチャ変更の検出と反映"""

        commit_info.get_affected_architecture_layers()

        # 新しいレイヤーや重要な構造変更を検出
        # 実装に応じて詳細化

    def _update_compliance_status(self, codemap: CodeMapEntity, commit_info: CommitInformation) -> None:
        """B20準拠状況の更新"""

        # アーキテクチャリンターやハードコーディング検出器の結果を反映
        # 実際の品質ゲート結果との連携は後続実装で詳細化

        if "architecture" in commit_info.commit_message.lower():
            codemap.b20_compliance.update_compliance_status(
                "ddd_layer_separation", "dependency_direction", "✅ Domain←Application←Infrastructure←Presentation"
            )

    def _is_fix_commit_for_issue(self, commit_info: CommitInformation, issue: CircularImportIssue) -> bool:
        """コミットが特定の問題の修正かどうかを判定"""

        message = commit_info.commit_message.lower()

        # 修正関連キーワードの検出
        # "resolution"（解決）や過去形も許容してヒット率を上げる
        fix_keywords = [
            "fix", "fixed", "resolve", "resolved", "resolution", "solve", "solved",
            "close", "closed", "complete", "completed", "done",
            "修正", "解決", "対策"
        ]

        if not any(keyword in message for keyword in fix_keywords):
            return False

        # 問題に関連するキーワードの検出
        issue_keywords = issue.issue.lower().split()

        # 問題固有のキーワードがコミットメッセージに含まれているかチェック
        relevant_keywords = ["circular", "import", "循環", "インポート", "依存"]

        return any(
            keyword in message
            for keyword in relevant_keywords + issue_keywords
            if len(keyword) > 2  # 短すぎるキーワードは除外
        )

    def validate_synchronization_result(self, codemap: CodeMapEntity) -> list[str]:
        """同期結果の検証"""

        validation_errors = []

        # 構造整合性チェック
        validation_errors.extend(codemap.validate_structure())

        # メタデータ整合性チェック
        if not codemap.metadata.commit:
            validation_errors.append("Commit hash is missing after synchronization")

        # 日付の妥当性チェック
        if codemap.metadata.last_updated is None:
            validation_errors.append("Last updated timestamp is missing")

        return validation_errors

    def calculate_synchronization_impact(self, original: CodeMapEntity, updated: CodeMapEntity) -> dict[str, Any]:
        """同期による変更影響の分析

        Args:
            original: 同期前のCODEMAP
            updated: 同期後のCODEMAP

        Returns:
            Dict[str, Any]: 変更影響の分析結果
        """

        impact = {
            "metadata_changed": original.metadata != updated.metadata,
            "issues_resolved": 0,
            "compliance_improved": 0,
            "completion_rate_change": 0.0,
        }

        # 解決された問題数の計算
        original_completed = len([i for i in original.circular_import_issues if i.is_completed()])
        updated_completed = len([i for i in updated.circular_import_issues if i.is_completed()])
        resolved_delta = updated_completed - original_completed

        if resolved_delta <= 0 and updated.metadata.commit:
            # 同一オブジェクト参照による差分ロスを防ぐため、最新コミットで完了した問題を再カウント
            latest_commit = updated.metadata.commit
            previous_commit = getattr(original.metadata, "commit", None)
            resolved_in_latest = sum(
                1
                for issue in updated.circular_import_issues
                if issue.is_completed() and issue.commit == latest_commit and latest_commit != previous_commit
            )
            resolved_delta = max(resolved_delta, resolved_in_latest)

        impact["issues_resolved"] = resolved_delta

        # 完了率の変化
        impact["completion_rate_change"] = updated.get_completion_rate() - original.get_completion_rate()

        return impact
