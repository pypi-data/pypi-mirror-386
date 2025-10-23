"""Infrastructure.adapters.path_service_adapter
Where: Infrastructure adapter offering filesystem path utilities to the domain.
What: Resolves project directories, applies fallbacks, and ensures directories exist.
Why: Centralises path handling so domain code remains platform-agnostic.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""Adapter that implements `IPathService` via the path configuration functional core."""


import os as _os
import re as _re
from pathlib import Path as _Path
from typing import TYPE_CHECKING

import yaml

from noveler.domain.exceptions import PathResolutionError
from noveler.domain.interfaces.i_path_service import IPathService
from noveler.domain.value_objects.path_configuration import PathConfiguration
from noveler.domain.value_objects.path_alias_catalog import get_directory_aliases
from noveler.domain.value_objects.project_time import project_now
from noveler.infrastructure.ai_integration.repositories.yaml_project_config_repository import (
    YamlProjectConfigRepository,
)
from noveler.infrastructure.config.project_detector import detect_project_root
from noveler.infrastructure.logging.unified_logger import get_logger

if TYPE_CHECKING:
    from pathlib import Path


class PathServiceAdapter(IPathService):
    """Expose the functional path configuration through the `IPathService` shell."""

    def __init__(
        self,
        project_root: Path,
        config_repository: YamlProjectConfigRepository | None = None,
        strict: bool | None = None,
    ) -> None:
        """Initialize the adapter and configure strict path semantics.

        Args:
            project_root: Absolute path to the detected project root.
            config_repository: Optional repository instance used to load path settings.
            strict: Optional override for strict fallback behaviour.
        """
        self._project_root = project_root
        self._config_repository = config_repository or YamlProjectConfigRepository(project_root)
        self._path_configuration: PathConfiguration | None = None  # 遅延読み込み用
        # strictモード判定（環境変数 NOVELER_STRICT_PATHS または引数）
        if strict is None:
            env_val = _os.getenv("NOVELER_STRICT_PATHS", "").strip().lower()
            env_strict = env_val in {"1", "true", "yes", "on"}
            # 環境変数が未指定の場合のみ .novelerrc.* を確認
            if env_val == "":
                self._strict = self._load_strict_from_rc()
            else:
                self._strict = env_strict
        else:
            self._strict = bool(strict)
        self._logger = get_logger(__name__)
        self._fallback_events: list[dict] = []

    def _record_fallback(self, event: dict) -> None:
        """Record fallback activity so callers can inspect non-strict behaviour."""
        try:
            self._fallback_events.append(event)
        except Exception:
            pass

    def get_and_clear_fallback_events(self) -> list[dict]:
        """Return recorded fallback events and clear the internal buffer."""
        ev = list(self._fallback_events)
        self._fallback_events.clear()
        return ev

    def _load_configuration(self) -> PathConfiguration:
        """Load and cache the path configuration for the current project.

        Returns:
            PathConfiguration: Configuration entity used for path resolution.
        """
        if self._path_configuration is None:
            try:
                config_dict = self._config_repository.get_path_config(self._project_root)
                self._path_configuration = PathConfiguration.from_dict(config_dict)
            except (FileNotFoundError, PermissionError, ValueError, TypeError, KeyError, OSError):
                # 設定読み込みに失敗した場合はデフォルト値を使用
                self._path_configuration = PathConfiguration()

        return self._path_configuration

    @property
    def project_root(self) -> Path:
        """Return the absolute project root path."""
        return self._project_root

    def _resolve_project_config_filename(self) -> str:
        """Resolve the project configuration filename via templates with safe fallback."""
        # 1) プロジェクト直下の .novelerrc.yaml/.yml を優先
        try:
            from noveler.infrastructure.repositories.yaml_file_template_repository import (
                YamlFileTemplateRepository,
            )

            for rc_name in (".novelerrc.yaml", ".novelerrc.yml"):
                rc_path = self._project_root / rc_name
                if rc_path.exists():
                    repo = YamlFileTemplateRepository(config_path=rc_path)
                    filename = repo.get_template("project_config")
                    if isinstance(filename, str) and filename.strip():
                        return filename.strip()
        except Exception:
            pass

        # 2) ConfigurationManager 経由のグローバル設定
        try:
            from noveler.infrastructure.factories.configuration_service_factory import get_configuration_manager

            manager = get_configuration_manager()
            filename = manager.get_file_template("project_config")
            if isinstance(filename, str) and filename.strip():
                return filename.strip()
        except Exception:
            pass

        return "プロジェクト設定.yaml"

    def get_project_config_file(self) -> Path:
        """Return the path to the primary project configuration YAML file."""
        filename = self._resolve_project_config_filename()
        return self._project_root / filename

    def get_proposal_file(self) -> Path:
        """Return the path to the proposal YAML file."""
        return self._project_root / "企画書.yaml"

    def get_reader_analysis_file(self) -> Path:
        """Return the path to the reader analysis YAML file."""
        return self._project_root / "読者分析.yaml"

    def get_manuscript_dir(self) -> Path:
        """Return the manuscript directory path, creating it when missing."""
        config = self._load_configuration()  # Shell: 設定読み込み（副作用）
        manuscript_path = config.get_manuscript_path(self._project_root)  # Core: 純粋関数
        manuscript_path = self._resolve_directory_with_fallback(
            manuscript_path,
            get_directory_aliases("manuscript"),
            "manuscript_dir_fallback",
        )
        manuscript_path.mkdir(parents=True, exist_ok=True)  # Shell: ディレクトリ作成（副作用）
        return manuscript_path

    def get_management_dir(self) -> Path:
        """Return the management directory path, creating fallbacks if necessary."""
        config = self._load_configuration()  # Shell: 設定読み込み（副作用）
        management_path = config.get_management_path(self._project_root)  # Core: 純粋関数
        management_path = self._resolve_directory_with_fallback(
            management_path,
            get_directory_aliases("management"),
            "management_dir_fallback",
        )
        try:
            management_path.mkdir(parents=True, exist_ok=True)  # Shell: ディレクトリ作成（副作用）
            return management_path
        except (PermissionError, FileNotFoundError):
            # テスト環境などで不正パスが指定された場合に/tmp配下へフォールバック
            fallback = _Path("/tmp/noveler_management")
            try:
                fallback.mkdir(parents=True, exist_ok=True)
                return fallback
            except Exception:
                # 最終手段: カレントディレクトリ配下
                fallback2 = _Path.cwd() / "noveler_management"
                fallback2.mkdir(parents=True, exist_ok=True)
                return fallback2

    def get_settings_dir(self) -> Path:
        """Return the directory containing consolidated settings resources."""
        config = self._load_configuration()
        settings_path = config.get_settings_path(self._project_root)
        settings_path = self._resolve_directory_with_fallback(
            settings_path,
            get_directory_aliases("settings"),
            "settings_dir_fallback",
        )
        settings_path.mkdir(parents=True, exist_ok=True)
        return settings_path

    def get_checklist_file_path(self, episode_number: int, episode_title: str) -> Path:
        """Return the checklist file path for the requested episode.

        Args:
            episode_number: Episode identifier.
            episode_title: Episode title used to construct the filename.

        Returns:
            Path: Absolute path to the checklist file.

        Raises:
            ValueError: If the underlying configuration rejects the arguments.
        """
        config = self._load_configuration()  # Shell: 設定読み込み（副作用）
        return config.get_checklist_file_path(self._project_root, episode_number, episode_title)  # Core: 純粋関数

    def get_episode_file_path(self, episode_number: int, episode_title: str) -> Path:
        """Return the manuscript file path for the requested episode.

        Args:
            episode_number: Episode identifier.
            episode_title: Episode title used to construct the filename.

        Returns:
            Path: Absolute path to the manuscript file.

        Raises:
            ValueError: If the underlying configuration rejects the arguments.
        """
        config = self._load_configuration()  # Shell: 設定読み込み（副作用）
        return config.get_episode_file_path(self._project_root, episode_number, episode_title)  # Core: 純粋関数

    def get_backup_dir(self) -> Path:
        """Return the backup directory path, ensuring it exists."""
        config = self._load_configuration()  # Shell: 設定読み込み（副作用）
        backup_path = config.get_backup_path(self._project_root)  # Core: 純粋関数
        backup_path = self._resolve_directory_with_fallback(
            backup_path,
            get_directory_aliases("backup"),
            "backup_dir_fallback",
        )
        backup_path.mkdir(parents=True, exist_ok=True)  # Shell: ディレクトリ作成（副作用）
        return backup_path

    def get_cache_dir(self) -> Path:
        """Return the path to the cache directory, creating it if necessary."""
        cache_dir = self.get_management_dir() / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir

    def get_plots_dir(self) -> Path:
        """Return the plots directory path, ensuring it exists."""
        config = self._load_configuration()  # Shell: 設定読み込み（副作用）
        plots_path = config.get_plots_path(self._project_root)  # Core: 純粋関数
        plots_path = self._resolve_directory_with_fallback(
            plots_path,
            get_directory_aliases("plots"),
            "plots_dir_fallback",
        )
        plots_path.mkdir(parents=True, exist_ok=True)  # Shell: ディレクトリ作成（副作用）
        return plots_path

    # 後方互換エイリアス（旧メソッド名）
    def get_plot_dir(self) -> Path:  # pragma: no cover - 互換用
        """Deprecated alias retained for legacy callers."""
        return self.get_plots_dir()

    def get_prompts_dir(self) -> Path:
        """Return the prompts directory path, ensuring it exists."""
        config = self._load_configuration()  # Shell: 設定読み込み（副作用）
        prompts_path = config.get_prompts_path(self._project_root)  # Core: 純粋関数
        prompts_path = self._resolve_directory_with_fallback(
            prompts_path,
            get_directory_aliases("prompts"),
            "prompts_dir_fallback",
        )
        prompts_path.mkdir(parents=True, exist_ok=True)  # Shell: ディレクトリ作成（副作用）
        return prompts_path

    def get_quality_dir(self) -> Path:
        """Return the quality-check directory path, ensuring it exists."""
        config = self._load_configuration()  # Shell: 設定読み込み（副作用）
        quality_path = config.get_quality_path(self._project_root)  # Core: 純粋関数
        quality_path = self._resolve_directory_with_fallback(
            quality_path,
            get_directory_aliases("quality"),
            "quality_dir_fallback",
        )
        quality_path.mkdir(parents=True, exist_ok=True)  # Shell: ディレクトリ作成（副作用）
        return quality_path

    # === B20: 共有基盤へエピソード命名・パス解決を集約 ===
    def get_episode_title(self, episode_number: int) -> str | None:
        """Infer an episode title from various project resources.

        Priority order: episodic plot filename → episodic plot YAML title → episode settings
        → manuscript header. Returns ``None`` when no title can be derived.
        """
        try:
            # 1) 話別プロット（ファイル名ベース）
            episode_plots = self.get_plots_dir() / "話別プロット"
            if episode_plots.exists():
                patterns = [
                    f"ep{episode_number:03d}*.yaml",
                    f"ep{episode_number:03d}*.yml",
                    f"第{episode_number:03d}話_*.yaml",
                    f"第{episode_number:03d}話*.yaml",
                    f"EP{episode_number:03d}*.yaml",
                    f"{episode_number:03d}*.yaml",
                ]
                for pat in patterns:
                    files = list(episode_plots.glob(pat))
                    if files:
                        stem = files[0].stem
                        if "_" in stem:
                            title = stem.split("_", 1)[1].strip()
                            if title:
                                return self._sanitize_filename(title)
                        # YAML内のtitleを読む
                        try:
                            data = yaml.safe_load(files[0].read_text(encoding="utf-8")) or {}
                            if isinstance(data, dict):
                                t = data.get("title")
                                if isinstance(t, str) and t.strip():
                                    return self._sanitize_filename(t)
                        except Exception as exc:
                            logger = get_logger(__name__)
                            logger.debug("エピソードプロットYAML読み込みに失敗: %s (%s)", files[0], exc)

            # 2) 設定/エピソード設定.yaml から取得（フォールバック）
            ep_settings = self.project_root / "設定" / "エピソード設定.yaml"
            if ep_settings.exists():
                try:
                    data = yaml.safe_load(ep_settings.read_text(encoding="utf-8")) or {}
                    if isinstance(data, dict):
                        episodes = data.get("episodes", {})
                        key = f"第{episode_number:03d}話"
                        info = episodes.get(key) if isinstance(episodes, dict) else None
                        if isinstance(info, dict):
                            t = info.get("title")
                            if isinstance(t, str) and t.strip():
                                if self._strict:
                                    raise PathResolutionError(
                                        "Episode title resolved via fallback (episode settings)",
                                        {"episode": episode_number, "source": "episode_settings"},
                                    )
                                self._logger.warning(
                                    "[paths] Fallback title from settings used: episode=%s", episode_number
                                )
                                self._record_fallback({
                                    "kind": "title_fallback",
                                    "source": "episode_settings",
                                    "episode": episode_number,
                                })
                                return self._sanitize_filename(t)
                except Exception as exc:
                    logger = get_logger(__name__)
                    logger.debug("エピソード設定YAML読み込みに失敗: %s (%s)", ep_settings, exc)

            # 3) 既存原稿のヘッダから推定（フォールバック）
            mdir = self.get_manuscript_dir()
            for md in mdir.glob(f"第{episode_number:03d}話*.md"):
                try:
                    head = md.read_text(encoding="utf-8", errors="ignore").splitlines()[:5]
                    for line in head:
                        m = _re.search(rf"^#\s*第{episode_number:03d}話[\u3000\s]+(.+)$", line)
                        if m:
                            if self._strict:
                                raise PathResolutionError(
                                    "Episode title resolved via fallback (manuscript header)",
                                    {"episode": episode_number, "source": "manuscript_header", "file": str(md)},
                                )
                            self._logger.warning(
                                "[paths] Fallback title from manuscript header used: episode=%s file=%s",
                                episode_number,
                                md,
                            )
                            self._record_fallback({
                                "kind": "title_fallback",
                                "source": "manuscript_header",
                                "episode": episode_number,
                                "file": str(md)
                            })
                            return self._sanitize_filename(m.group(1).strip())
                except Exception:
                    continue

            return None
        except Exception:
            return None

    def _load_strict_from_rc(self) -> bool:
        """Read strict-path settings from configuration files when available."""
        # 1) 統合設定（config/novel_config.yaml）
        try:
            from noveler.infrastructure.factories.configuration_service_factory import get_configuration_manager

            cfg = get_configuration_manager().get_configuration()
            if cfg is not None and hasattr(cfg, "_sections"):
                paths_section = cfg._sections.get("paths")  # noqa: SLF001 (内部構造アクセスは既存慣例に倣う)
                if paths_section is not None:
                    val = paths_section.get_nested_bool(["strict"], False)
                    if isinstance(val, bool):
                        return val
        except Exception:
            pass

        # 2) .novelerrc.*
        try:
            for name in [".novelerrc.yaml", ".novelerrc.yml", ".novelerrc.json"]:
                rc = self._project_root / name
                if rc.exists():
                    try:
                        data = yaml.safe_load(rc.read_text(encoding="utf-8")) or {}
                        if isinstance(data, dict):
                            paths = data.get("paths", {})
                            if isinstance(paths, dict):
                                val = paths.get("strict")
                                if isinstance(val, bool):
                                    return val
                                if isinstance(val, str):
                                    return val.strip().lower() in {"1", "true", "yes", "on"}
                    except Exception:
                        continue
        except Exception:
            pass
        return False

    def get_manuscript_filename(self, episode_number: int) -> str:
        title = self.get_episode_title(episode_number) or "無題"
        return f"第{episode_number:03d}話_{title}.md"

    def get_manuscript_path(self, episode_number: int) -> Path:
        mdir = self.get_manuscript_dir()
        return mdir / self.get_manuscript_filename(episode_number)

    def _sanitize_filename(self, name: str) -> str:
        # Windows等で不正な文字を除去
        return _re.sub(r"[\\/:*?\"<>|]", "", name).strip()

    def get_reports_dir(self) -> Path:
        """Return the reports directory path, ensuring it exists."""
        config = self._load_configuration()  # Shell: 設定読み込み（副作用）
        reports_path = config.get_reports_path(self._project_root)  # Core: 純粋関数
        reports_path = self._resolve_directory_with_fallback(
            reports_path,
            get_directory_aliases("reports"),
            "reports_dir_fallback",
        )
        reports_path.mkdir(parents=True, exist_ok=True)  # Shell: ディレクトリ作成（副作用）
        return reports_path

    def generate_report_filename(
        self,
        episode_number: int,
        report_type: str,
        extension: str,
        *,
        include_timestamp: bool = False,
        version: str | None = None,
    ) -> str:
        """Return a canonical report filename used by quality/analysis workflows."""
        if not 1 <= episode_number <= 999:
            raise ValueError("episode_number must be between 1 and 999")
        if not isinstance(report_type, str) or not report_type.strip():
            raise ValueError("report_type must be a non-empty string")
        if not isinstance(extension, str) or not extension.strip():
            raise ValueError("extension must be a non-empty string")

        sanitized_type = self._sanitize_filename(report_type)
        ext_token = extension.lstrip(".").lower()

        tokens: list[str] = [f"episode_{episode_number:03d}", sanitized_type]

        if include_timestamp:
            timestamp = project_now().datetime.strftime("%Y%m%d%H%M%S")
            tokens.append(timestamp)

        if version:
            sanitized_version = self._sanitize_filename(version)
            if sanitized_version:
                tokens.append(sanitized_version)

        return "_".join(tokens) + f".{ext_token}"

    def get_spec_path(self) -> Path:
        """Return the directory used to store specification documents."""
        specs_path = self._project_root / "specs"
        specs_path.mkdir(parents=True, exist_ok=True)
        return specs_path

    def ensure_directory_exists(self, directory: Path) -> None:
        """Ensure the provided directory path exists on disk.

        Args:
            directory: Absolute directory path to create when missing.
        """
        directory.mkdir(parents=True, exist_ok=True)

    def ensure_directories_exist(self) -> None:
        """Create required project directories when they are absent."""
        # 基本的なプロジェクトディレクトリ構造を作成
        # 各メソッドが内部でmkdirを行うため、呼び出すだけで十分
        self.get_manuscript_dir()
        self.get_management_dir()
        self.get_backup_dir()
        self.get_plots_dir()
        self.get_prompts_dir()
        self.get_quality_dir()
        self.get_reports_dir()

    def _relativize(self, directory: Path) -> str:
        """Return a path string relative to the project root when possible."""
        try:
            return str(directory.relative_to(self._project_root))
        except ValueError:
            return str(directory)

    def _resolve_directory_with_fallback(
        self,
        primary: Path,
        fallback_names: list[str],
        event_kind: str,
    ) -> Path:
        """Return a directory path, falling back to legacy layouts when they already exist."""
        if primary.exists():
            return primary

        for name in fallback_names:
            candidate = self._project_root / name
            if candidate == primary:
                continue
            if candidate.exists():
                if self._strict:
                    raise PathResolutionError(
                        "Strict path resolution prevented legacy fallback",
                        {"event": event_kind, "primary": str(primary), "fallback": str(candidate)},
                    )
                self._logger.warning(
                    "[paths] Fallback directory resolved: kind=%s primary=%s fallback=%s",
                    event_kind,
                    primary,
                    candidate,
                )
                self._record_fallback(
                    {"kind": event_kind, "primary": str(primary), "fallback": str(candidate)}
                )
                return candidate

        return primary

    def get_required_directories(self) -> list[str]:
        """Return relative paths for directories considered mandatory."""
        directories = [
            self.get_manuscript_dir(),
            self.get_management_dir(),
            self.get_settings_dir(),
            self.get_plots_dir(),
            self.get_quality_dir(),
            self.get_reports_dir(),
        ]

        return [self._relativize(directory) for directory in directories]

    def get_all_directories(self) -> list[str]:
        """Return relative paths for core and optional project directories."""

        core_directories = [
            self.get_manuscript_dir(),
            self.get_management_dir(),
            self.get_settings_dir(),
            self.get_plots_dir(),
            self.get_quality_dir(),
            self.get_reports_dir(),
        ]

        optional_directories = [
            self.get_backup_dir(),
            self.get_prompts_dir(),
            self.get_management_dir() / "品質記録",
            self.get_management_dir() / "A31_チェックリスト",
            self.get_prompts_dir() / "全話分析結果",
            self.get_plots_dir() / "章別プロット",
            self.get_plots_dir() / "話別プロット",
            self._project_root / "10_企画",
            self._project_root / "90_アーカイブ",
        ]

        ordered: list[str] = []
        seen: set[str] = set()

        for directory in [*core_directories, *optional_directories]:
            rel = self._relativize(directory)
            if rel not in seen:
                ordered.append(rel)
                seen.add(rel)

        return ordered


    # === CommonPathService統合：高機能メソッド追加 ===

    def get_chapter_plots_dir(self) -> Path:
        """Return the chapter plots directory path, ensuring it exists."""
        # CommonPathServiceの高機能メソッドを統合
        plots_dir = self.get_plots_dir()
        chapter_plots_path = plots_dir / "章別プロット"
        chapter_plots_path.mkdir(parents=True, exist_ok=True)
        return chapter_plots_path

    def get_episode_plots_dir(self) -> Path:
        """Return the episodic plots directory path, ensuring it exists."""
        # CommonPathServiceの高機能メソッドを統合
        plots_dir = self.get_plots_dir()
        episode_plots_path = plots_dir / "話別プロット"
        episode_plots_path.mkdir(parents=True, exist_ok=True)
        return episode_plots_path

    def get_episode_plot_path(self, episode_number: int) -> Path | None:
        """Resolve the episodic plot file path when one exists.

        Search order:
            1. 20_プロット/話別プロット/epNNN.{yaml,yml}
            2. 20_プロット/話別プロット/第NNN話_*.{md,yaml,yml}
            3. 20_プロット/第NNN話_*.{md,yaml,yml} （フォールバック）
        """
        try:
            candidates: list[Path] = []
            episode_plots = self.get_episode_plots_dir()
            plots_root = self.get_plots_dir()
            patterns = [
                f"ep{episode_number:03d}.yaml",
                f"ep{episode_number:03d}.yml",
                f"ep{episode_number:03d}_*.yaml",
                f"第{episode_number:03d}話_*.md",
                f"第{episode_number:03d}話_*.yaml",
                f"第{episode_number:03d}話_*.yml",
                f"第{episode_number:03d}話.md",
                f"第{episode_number:03d}話.yaml",
                f"第{episode_number:03d}話.yml",
                f"第{episode_number:03d}話_プロット.md",
                f"第{episode_number:03d}話_プロット.yaml",
                f"第{episode_number:03d}話_プロット.yml",
                f"EP{episode_number:03d}*.yaml",
                f"EP{episode_number:03d}.yaml",
            ]
            # 1) 話別プロット直下（正式）
            for pat in patterns:
                matches = list(episode_plots.glob(pat))
                if matches:
                    candidates.extend(matches)
                    break
            # 2) プロットルート直下（フォールバック）
            for pat in patterns:
                matches = list(plots_root.glob(pat))
                if matches:
                    if self._strict:
                        raise PathResolutionError(
                            "Plot file resolved via fallback location",
                            {"episode": episode_number, "dir": str(plots_root), "pattern": pat},
                        )
                    self._logger.warning(
                        "[paths] Fallback plot path used at root: episode=%s pattern=%s", episode_number, pat
                    )
                    self._record_fallback({
                        "kind": "plot_fallback",
                        "location": "plots_root",
                        "episode": episode_number,
                        "pattern": pat
                    })
                    candidates.extend(matches)
                    break
            if candidates:
                return candidates[0]
            if self._strict:
                raise PathResolutionError(
                    "Plot file not found for episode",
                    {"episode": episode_number, "searched": [str(episode_plots), str(plots_root)]},
                )
            self._record_fallback({
                "kind": "plot_not_found",
                "episode": episode_number,
                "searched": [str(episode_plots), str(plots_root)]
            })
            return None
        except Exception:
            return None

    def get_checklist_dir(self) -> Path:
        """チェックリストディレクトリを取得"""
        primary = self.get_management_dir() / "checklists"
        checklists_dir = self._resolve_directory_with_fallback(
            primary,
            [".noveler/checklists"],
            "checklists_dir_fallback",
        )
        checklists_dir.mkdir(parents=True, exist_ok=True)
        return checklists_dir

    def get_phase2_records_dir(self) -> Path:
        """Phase2記録ディレクトリを取得"""
        primary = self.get_management_dir() / "phase2_records"
        records_dir = self._resolve_directory_with_fallback(
            primary,
            [".noveler/phase2_records"],
            "phase2_records_dir_fallback",
        )
        records_dir.mkdir(parents=True, exist_ok=True)
        return records_dir

    def get_scene_file(self, episode_number: int) -> Path:
        """シーンファイルパスを取得"""
        # 互換性維持のため、重要シーン.yaml を管理ディレクトリ配下に固定
        _ = episode_number  # 現状はエピソード番号に依存しない
        management_dir = self.get_management_dir()
        return management_dir / "重要シーン.yaml"

    def get_quality_records_dir(self) -> Path:
        """Return the quality records directory path, ensuring it exists."""
        # CommonPathServiceの高機能メソッドを統合
        management_dir = self.get_management_dir()
        quality_records_path = management_dir / "品質記録"
        quality_records_path.mkdir(parents=True, exist_ok=True)
        return quality_records_path

    def get_analysis_results_dir(self) -> Path:
        """Return the all-episodes analysis directory path, ensuring it exists."""
        # CommonPathServiceの高機能メソッドを統合
        prompts_dir = self.get_prompts_dir()
        analysis_results_path = prompts_dir / "全話分析結果"
        analysis_results_path.mkdir(parents=True, exist_ok=True)
        return analysis_results_path

    def get_episode_management_file(self) -> Path:
        """Return the path to the episode tracking file (template-aware)."""
        management_dir = self.get_management_dir()
        try:
            from noveler.infrastructure.factories.configuration_service_factory import get_configuration_manager  # type: ignore
            cm = get_configuration_manager()
            fname = cm.get_file_template("episode_management")
        except Exception:
            fname = "話数管理.yaml"
        return management_dir / fname

    def get_quality_config_file(self) -> Path:
        """Return the path to the quality-check settings file."""
        management_dir = self.get_management_dir()
        return management_dir / "品質チェック設定.yaml"

    def get_quality_record_file(self) -> Path:
        """Return the path to the quality record file (template-aware)."""
        management_dir = self.get_management_dir()
        try:
            from noveler.infrastructure.factories.configuration_service_factory import get_configuration_manager  # type: ignore
            cm = get_configuration_manager()
            fname = cm.get_file_template("quality_record")
        except Exception:
            fname = "品質記録.yaml"
        return management_dir / fname

    def get_revision_history_file(self) -> Path:
        """Return the path to the revision history file (template-aware)."""
        management_dir = self.get_management_dir()
        try:
            from noveler.infrastructure.factories.configuration_service_factory import get_configuration_manager  # type: ignore
            cm = get_configuration_manager()
            fname = cm.get_file_template("revision_history")
        except Exception:
            fname = "改訂履歴.yaml"
        return management_dir / fname

    def get_writing_logs_dir(self) -> Path:
        """Return the manuscript writing log directory path, ensuring it exists."""
        management_dir = self.get_management_dir()
        writing_logs_path = management_dir / "原稿執筆ログ"
        writing_logs_path.mkdir(parents=True, exist_ok=True)
        return writing_logs_path

    def is_project_directory(self, path: Path) -> bool:
        """Return ``True`` when the provided path is a recognized project root."""
        # B20準拠: 動的にパス名を取得
        manuscript_dir = self.get_manuscript_dir().name
        management_dir = self.get_management_dir().name
        return (path / manuscript_dir).exists() and (path / management_dir).exists()

    def is_manuscript_file(self, file_path: Path) -> bool:
        """Return ``True`` when the path points to a manuscript Markdown file."""
        # B20準拠: 動的にパス名を取得
        manuscript_dir_name = self.get_manuscript_dir().name
        return (
            file_path.suffix == ".md"
            and file_path.parent.name == manuscript_dir_name
            and "第" in file_path.stem
            and "話_" in file_path.stem
        )

    def get_noveler_output_dir(self) -> Path:
        """Return the `.noveler` directory used to store automation artifacts."""
        return self._project_root / ".noveler"

    def get_step_output_file_path(
        self,
        episode_number: int,
        step_number: int,
        timestamp: str | None = None
    ) -> Path:
        """Return the JSON file path for a step output record.

        Args:
            episode_number: Episode identifier.
            step_number: Write pipeline step number (1-19).
            timestamp: Optional timestamp override for the filename.

        Returns:
            Path: Target file path ``EP{episode:04d}_step{step:02d}_{timestamp}.json``.

        Raises:
            ValueError: When parameters fall outside allowed ranges.
        """
        if not 1 <= step_number <= 19:
            msg = f"ステップ番号は1-19の範囲である必要があります: {step_number}"
            raise ValueError(msg)

        if episode_number < 1:
            msg = f"エピソード番号は1以上である必要があります: {episode_number}"
            raise ValueError(msg)

        if timestamp is None:
            # 仕様: JSTで秒まで（yyyyMMddHHMMSS）
            timestamp = project_now().datetime.strftime("%Y%m%d%H%M%S")

        # 仕様変更: EPは4桁ゼロ埋め
        filename = f"EP{episode_number:04d}_step{step_number:02d}_{timestamp}.json"
        # B20準拠: チェック系のLLM I/Oログは .noveler/checks 配下
        checks_dir = self.get_noveler_output_dir() / "checks"
        checks_dir.mkdir(parents=True, exist_ok=True)
        return checks_dir / filename

    def get_write_command_file_path(self, episode_number: int, timestamp: str | None = None) -> Path:
        """Return the JSON file path used by `/noveler write` operations."""
        if episode_number < 1:
            msg = f"エピソード番号は1以上である必要があります: {episode_number}"
            raise ValueError(msg)
        if timestamp is None:
            timestamp = project_now().datetime.strftime("%Y%m%d%H%M%S")
        filename = f"EP{episode_number:04d}_{timestamp}.json"
        # B20準拠: write系のLLM I/Oログは .noveler/writes に保存
        writes_dir = self.get_noveler_output_dir() / "writes"
        writes_dir.mkdir(parents=True, exist_ok=True)
        return writes_dir / filename

    def get_write_step_output_file_path(
        self,
        episode_number: int,
        step_number: int,
        timestamp: str | None = None,
    ) -> Path:
        """Return the JSON file path for `/noveler write` step outputs."""
        if not 1 <= step_number <= 19:
            msg = f"ステップ番号は1-19の範囲である必要があります: {step_number}"
            raise ValueError(msg)
        if episode_number < 1:
            msg = f"エピソード番号は1以上である必要があります: {episode_number}"
            raise ValueError(msg)
        if timestamp is None:
            timestamp = project_now().datetime.strftime("%Y%m%d%H%M%S")
        filename = f"EP{episode_number:04d}_step{step_number:02d}_{timestamp}.json"
        writes_dir = self.get_noveler_output_dir() / "writes"
        writes_dir.mkdir(parents=True, exist_ok=True)
        return writes_dir / filename


class PathServiceAdapterFactory:
    """Simple factory retained for legacy creation paths."""

    @staticmethod
    def create_path_service(project_root: Path | str | None = None) -> PathServiceAdapter:
        root = Path(project_root) if project_root is not None else Path.cwd()
        return PathServiceAdapter(root)



def create_path_service(project_root: Path | str | None = None) -> PathServiceAdapter:
    """Factory function that constructs a `PathServiceAdapter` instance.

    Args:
        project_root: Explicit project root; when ``None`` auto-detection is used.

    Returns:
        PathServiceAdapter: Adapter configured for path operations.
    """
    # 環境変数でstrictモードを有効化可能
    strict_env = _os.getenv("NOVELER_STRICT_PATHS", "0").strip().lower() in {"1", "true", "yes", "on"}
    if project_root is None:
        detected_root = detect_project_root()
        return PathServiceAdapter(detected_root, strict=strict_env)
    # 受け取ったproject_rootがstrの場合はPathに正規化
    if isinstance(project_root, str):
        project_root = _Path(project_root)
    return PathServiceAdapter(project_root, strict=strict_env)  # type: ignore[arg-type]
