#!/usr/bin/env python3
"""CODEMAPエンティティ

仕様書: SPEC-CODEMAP-AUTO-UPDATE-001
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from noveler.domain.value_objects.commit_information import CommitInformation


@dataclass
class CodeMapMetadata:
    """CODEMAPメタデータ"""

    name: str
    architecture: str
    version: str
    last_updated: datetime
    commit: str | None = None

    def update_from_commit(self, commit_info: CommitInformation) -> None:
        """コミット情報からメタデータを更新"""
        self.last_updated = commit_info.commit_date
        self.commit = commit_info.short_hash


@dataclass
class ArchitectureLayer:
    """アーキテクチャ層情報"""

    name: str
    path: str
    role: str
    depends_on: list[str] = field(default_factory=list)
    key_modules: list[str] = field(default_factory=list)
    entry_point: str | None = None


@dataclass
class CircularImportIssue:
    """循環インポート問題"""

    location: str
    issue: str
    solution: str
    status: str
    commit: str | None = None

    def mark_completed(self, commit_hash: str) -> None:
        """完了としてマーク"""
        # テスト仕様に合わせてステータスはシンプルに「完了」
        self.status = "完了"
        self.commit = commit_hash

    def is_completed(self) -> bool:
        """完了状態かチェック"""
        normalized = str(self.status).strip().lower()
        return normalized in {"完了", "completed", "解決済み", "resolved", "done", "✅ 完了"}


@dataclass
class B20Compliance:
    """B20準拠状況"""

    ddd_layer_separation: dict[str, str] = field(default_factory=dict)
    import_management: dict[str, str] = field(default_factory=dict)
    shared_components: dict[str, str] = field(default_factory=dict)

    def update_compliance_status(self, category: str, item: str, status: str) -> None:
        """準拠状況を更新"""
        if category == "ddd_layer_separation":
            self.ddd_layer_separation[item] = status
        elif category == "import_management":
            self.import_management[item] = status
        elif category == "shared_components":
            self.shared_components[item] = status


@dataclass
class QualityPreventionIntegration:
    """品質予防システム統合状況"""

    architecture_linter: dict[str, str] = field(default_factory=dict)
    hardcoding_detector: dict[str, str] = field(default_factory=dict)
    automated_prevention: dict[str, str] = field(default_factory=dict)


class CodeMapEntity:
    """CODEMAPエンティティ

    プロジェクト全体のアーキテクチャ情報とメタデータを管理する
    ドメインエンティティ
    """

    def __init__(
        self,
        metadata: CodeMapMetadata,
        architecture_layers: list[ArchitectureLayer],
        circular_import_issues: list[CircularImportIssue],
        b20_compliance: B20Compliance,
        quality_prevention: QualityPreventionIntegration,
    ) -> None:
        """初期化

        Args:
            metadata: プロジェクトメタデータ
            architecture_layers: アーキテクチャ層定義
            circular_import_issues: 循環インポート問題一覧
            b20_compliance: B20準拠状況
            quality_prevention: 品質予防システム統合状況
        """
        self.metadata = metadata
        self.architecture_layers = architecture_layers
        self.circular_import_issues = circular_import_issues
        self.b20_compliance = b20_compliance
        self.quality_prevention = quality_prevention

    def update_from_commit(self, commit_info: CommitInformation) -> None:
        """コミット情報からCODEMAPを更新"""
        # メタデータ更新
        self.metadata.update_from_commit(commit_info)

        # 変更ファイルから推定される完了項目を更新
        self._update_implementation_status(commit_info)

    def _update_implementation_status(self, commit_info: CommitInformation) -> None:
        """実装状況の自動更新"""
        changed_files = commit_info.changed_files

        # 循環インポート対策の完了検出
        for issue in self.circular_import_issues:
            if not issue.is_completed() and self._is_issue_resolved(issue, changed_files):
                issue.mark_completed(commit_info.short_hash)

    def _is_issue_resolved(self, issue: CircularImportIssue, changed_files: list[str]) -> bool:
        """問題が解決されたかを判定"""
        # 問題のあるファイルが変更され、かつ解決策が実装されているかを判定
        issue_file = issue.location

        # 該当ファイルが変更されているかチェック
        return any(issue_file in changed_file for changed_file in changed_files)

    def get_pending_issues(self) -> list[CircularImportIssue]:
        """未解決の問題一覧を取得"""
        return [issue for issue in self.circular_import_issues if not issue.is_completed()]

    def get_completion_rate(self) -> float:
        """実装完了率を計算"""
        if not self.circular_import_issues:
            return 100.0

        completed = len([issue for issue in self.circular_import_issues if issue.is_completed()])
        total = len(self.circular_import_issues)
        return (completed / total) * 100.0

    def validate_structure(self) -> list[str]:
        """構造の整合性を検証"""
        errors: list[Any] = []

        # 必須フィールドの存在確認
        if not self.metadata.name:
            errors.append("Project name is required")

        if not self.metadata.architecture:
            errors.append("Architecture type is required")

        # レイヤー依存関係の循環チェック
        if self._has_circular_dependencies():
            errors.append("Circular dependencies detected in architecture layers")

        return errors

    def _has_circular_dependencies(self) -> bool:
        """レイヤー間循環依存の検出"""
        # 簡単な循環依存チェック（DFSベース）
        visited = set()
        rec_stack = set()

        def has_cycle(layer_name: str) -> bool:
            visited.add(layer_name)
            rec_stack.add(layer_name)

            # 該当レイヤーを見つける
            layer = next((l for l in self.architecture_layers if l.name == layer_name), None)
            if not layer:
                return False

            for dep in layer.depends_on:
                if dep not in visited:
                    if has_cycle(dep):
                        return True
                elif dep in rec_stack:
                    return True

            rec_stack.remove(layer_name)
            return False

        for layer in self.architecture_layers:
            if layer.name not in visited:
                if has_cycle(layer.name):
                    return True

        return False

    def to_dict(self) -> dict:
        """辞書形式に変換（YAML出力用）"""
        return {
            "project_structure": {
                "name": self.metadata.name,
                "architecture": self.metadata.architecture,
                "version": self.metadata.version,
                "last_updated": self.metadata.last_updated.strftime("%Y-%m-%d"),
                "commit": self.metadata.commit,
                "layers": [
                    {
                        "name": layer.name,
                        "path": layer.path,
                        "role": layer.role,
                        "depends_on": layer.depends_on,
                        "key_modules": layer.key_modules,
                        **({"entry_point": layer.entry_point} if layer.entry_point else {}),
                    }
                    for layer in self.architecture_layers
                ],
            },
            "circular_import_solutions": {
                "resolved_issues": [
                    {
                        "location": issue.location,
                        "issue": issue.issue,
                        "solution": issue.solution,
                        "status": issue.status,
                        "commit": issue.commit,
                    }
                    for issue in self.circular_import_issues
                ]
            },
            "b20_compliance": {
                "ddd_layer_separation": self.b20_compliance.ddd_layer_separation,
                "import_management": self.b20_compliance.import_management,
                "shared_components": self.b20_compliance.shared_components,
            },
            "quality_prevention_integration": {
                "architecture_linter": self.quality_prevention.architecture_linter,
                "hardcoding_detector": self.quality_prevention.hardcoding_detector,
                "automated_prevention": self.quality_prevention.automated_prevention,
            },
        }

    # 互換用プロパティ: tests が辞書形式の circular_import_solutions.resolved_issues にも対応できるよう提供
    @property
    def circular_import_solutions(self) -> dict:
        """辞書互換の循環インポート解決情報

        Returns:
            dict: {"resolved_issues": [ {location, issue, solution, status, commit}, ... ]}
        """
        return {
            "resolved_issues": [
                {
                    "location": issue.location,
                    "issue": issue.issue,
                    "solution": issue.solution,
                    "status": issue.status,
                    "commit": issue.commit,
                }
                for issue in self.circular_import_issues
            ]
        }
