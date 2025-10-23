"""Domain.services.project_structure_diagnostic_service
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

from contextlib import suppress
from pathlib import Path
from typing import Any, Protocol


class SupportsProjectRoot(Protocol):
    """Protocol for repositories exposing get_project_root."""

    def get_project_root(self) -> Path | None:  # pragma: no cover - protocol definition
        """Return project root path when available."""
        ...

"プロジェクト構造診断サービス\n\nシステム診断のプロジェクト構造チェック専用ドメインサービス\n"


class ProjectStructureDiagnosticService:
    """プロジェクト構造診断専用サービス"""

    def __init__(self, project_repository: SupportsProjectRoot | None, guide_root: Path) -> None:
        self.project_repository = project_repository
        self.guide_root = guide_root

    def check_project_structure(self, quiet: bool = False) -> dict:
        """プロジェクト構造のチェック"""
        log_messages: list[dict[str, str]] = []
        self._append_log(log_messages, "info", "📁 プロジェクト構造チェック...", quiet)
        structure_check = {"status": "OK", "details": {}}
        errors: list[Any] = []
        warnings = []
        project_root_result = self._detect_project_root()
        structure_check["details"].update(project_root_result["details"])
        errors.extend(project_root_result["errors"])
        warnings.extend(project_root_result["warnings"])
        if project_root_result.get("project_root"):
            dir_result = self._validate_directory_structure(project_root_result["project_root"])
            structure_check["details"].update(dir_result["details"])
            errors.extend(dir_result["errors"])
            warnings.extend(dir_result["warnings"])
            file_result = self._check_required_files(project_root_result["project_root"])
            structure_check["details"].update(file_result["details"])
            errors.extend(file_result["errors"])
            warnings.extend(file_result["warnings"])
        if errors:
            structure_check["status"] = "ERROR"
        elif warnings:
            structure_check["status"] = "WARNING"
        return {
            "check_result": structure_check,
            "errors": errors,
            "warnings": warnings,
            "log_messages": log_messages,
        }

    @staticmethod
    def _append_log(
        log_messages: list[dict[str, str]],
        level: str,
        message: str,
        quiet: bool,
    ) -> None:
        """Record diagnostic log entries when output is not suppressed."""
        if quiet:
            return
        log_messages.append({"level": level, "message": message})

    def _detect_project_root(self) -> dict:
        """プロジェクトルートを検出"""
        errors: list[Any] = []
        warnings = []
        details: dict[str, Any] = {}
        config_result = self._detect_from_config_file()
        if config_result:
            details["project_root"] = str(config_result)
            details["detection_method"] = "config_file"
            return {"details": details, "errors": errors, "warnings": warnings, "project_root": config_result}
        current_result = self._detect_current_project_root()
        if current_result:
            details["project_root"] = str(current_result)
            details["detection_method"] = "current_directory"
            return {"details": details, "errors": errors, "warnings": warnings, "project_root": current_result}
        repo_result = self._detect_from_repository()
        if repo_result:
            details["project_root"] = str(repo_result)
            details["detection_method"] = "repository"
            return {"details": details, "errors": errors, "warnings": warnings, "project_root": repo_result}
        errors.append("プロジェクトルートが検出できませんでした")
        return {"details": details, "errors": errors, "warnings": warnings, "project_root": None}

    def _detect_from_config_file(self) -> None:
        """設定ファイルからプロジェクトルートを検出"""
        config_path = self._find_project_config(Path.cwd())
        if config_path and config_path.exists():
            return config_path.parent
        return None

    def _detect_current_project_root(self) -> None:
        """現在のディレクトリ構造からプロジェクトルートを検出"""
        current = Path.cwd()
        project_indicators = ["pyproject.toml", "setup.py", ".git", "CLAUDE.md"]
        while current != current.parent:
            if any((current / indicator).exists() for indicator in project_indicators):
                return current
            current = current.parent
        return None

    def _detect_from_repository(self) -> None:
        """リポジトリからプロジェクトルートを検出"""
        if self.project_repository is None:
            return None

        if hasattr(self.project_repository, "get_project_root"):
            with suppress(Exception):
                return self.project_repository.get_project_root()
        return None

    def _validate_directory_structure(self, project_root: Path) -> dict:
        """ディレクトリ構造を検証"""
        errors: list[Any] = []
        warnings = []
        details: dict[str, Any] = {}
        required_dirs = ["scripts", "templates", "config"]
        optional_dirs = ["projects", "docs", "temp"]
        details["required_directories"] = {}
        details["optional_directories"] = {}
        for dir_name in required_dirs:
            dir_path = project_root / dir_name
            exists = dir_path.exists() and dir_path.is_dir()
            details["required_directories"][dir_name] = exists
            if not exists:
                errors.append(f"必須ディレクトリが見つかりません: {dir_name}")
        for dir_name in optional_dirs:
            dir_path = project_root / dir_name
            exists = dir_path.exists() and dir_path.is_dir()
            details["optional_directories"][dir_name] = exists
            if not exists:
                warnings.append(f"推奨ディレクトリが見つかりません: {dir_name}")
        return {"details": details, "errors": errors, "warnings": warnings}

    def _check_required_files(self, project_root: Path) -> dict:
        """必須ファイルをチェック"""
        errors: list[Any] = []
        warnings = []
        details: dict[str, Any] = {}
        required_files = ["pyproject.toml", "CLAUDE.md"]
        optional_files = ["README.md", ".gitignore"]
        details["required_files"] = {}
        details["optional_files"] = {}
        for file_name in required_files:
            file_path = project_root / file_name
            exists = file_path.exists() and file_path.is_file()
            details["required_files"][file_name] = exists
            if not exists:
                errors.append(f"必須ファイルが見つかりません: {file_name}")
        for file_name in optional_files:
            file_path = project_root / file_name
            exists = file_path.exists() and file_path.is_file()
            details["optional_files"][file_name] = exists
            if not exists:
                warnings.append(f"推奨ファイルが見つかりません: {file_name}")
        return {"details": details, "errors": errors, "warnings": warnings}

    def _find_project_config(self, start_path: Path) -> None:
        """プロジェクト設定ファイルを検索"""
        current = start_path.resolve()
        while current != current.parent:
            config_path = current / "プロジェクト設定.yaml"
            if config_path.exists():
                return config_path
            current = current.parent
        return None
