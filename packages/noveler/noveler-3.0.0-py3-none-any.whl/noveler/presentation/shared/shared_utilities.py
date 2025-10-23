#!/usr/bin/env python3
"""共通ユーティリティ関数

CLI コマンド間で共有される関数群
循環インポートを避けるため、別ファイルに分離
"""

import importlib
import os
import re
import sys
import types
import warnings
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml
from rich.console import Console

# B30準拠: from rich.console import Console → shared console service使用
from rich.panel import Panel

from noveler.domain.interfaces.i_path_service import IPathService
from noveler.domain.value_objects.path_configuration import DEFAULT_PATH_CONFIG
from noveler.infrastructure.logging.unified_logger import (
    get_logger as _get_unified_logger,
)

if TYPE_CHECKING:
    from noveler.domain.value_objects.project_paths import ProjectPaths
    # 削除されたCLIコマンドハンドラーへの参照をコメントアウト（Typer CLI削除対応）
    # from noveler.presentation.cli.plot_commands import PlotCommandHandler
    # from noveler.presentation.cli.project_commands import ProjectCommandHandler
    # from noveler.presentation.cli.quality_commands import QualityCommandHandler
    # from noveler.presentation.cli.writing_commands import WritingCommandHandler

# 循環インポート修正: environment_setupは遅延インポート
# from noveler.presentation.cli.environment_setup import initialize_environment
from noveler.presentation.shared.guide_root_finder import find_guide_root


# B30品質作業指示書準拠: 共有コンソール実装（DI対応）
def _get_console() -> Console:
    """統一Console管理システム（DI対応・Singleton Pattern）

    B30品質作業指示書準拠:
    # B30準拠: Console() → self.get_console_service()使用
    - 統一インスタンス管理でリソース効率化
    - 依存性注入対応設計
    """
    if not hasattr(_get_console, "_instance"):
        # 統一Console設定（プロジェクト全体で共通仕様）
        # STDIO安全性のため、既定の出力先はstderrにする
        console = Console(
            file=sys.stderr, force_terminal=True, force_interactive=True, highlight=False, markup=True, emoji=True
        )
        # 互換メソッドを注入（以前のConsoleService APIに合わせる）
        # Rich Console には print_info 等が無いため、軽量なラッパを動的追加
        def _print_info(self: Console, message: str) -> None:
            self.print(f"[blue]{message}[/blue]")

        def _print_success(self: Console, message: str) -> None:
            self.print(f"[green]{message}[/green]")

        def _print_warning(self: Console, message: str) -> None:
            self.print(f"[yellow]{message}[/yellow]")

        def _print_error(self: Console, message: str) -> None:
            self.print(f"[red]{message}[/red]")

        def _print_debug(self: Console, message: str) -> None:
            self.print(f"[dim]{message}[/dim]")

        # 既に存在する場合は上書きしない（安全側）
        if not hasattr(console, "print_info"):
            console.print_info = types.MethodType(_print_info, console)  # type: ignore[attr-defined]
        if not hasattr(console, "print_success"):
            console.print_success = types.MethodType(_print_success, console)  # type: ignore[attr-defined]
        if not hasattr(console, "print_warning"):
            console.print_warning = types.MethodType(_print_warning, console)  # type: ignore[attr-defined]
        if not hasattr(console, "print_error"):
            console.print_error = types.MethodType(_print_error, console)  # type: ignore[attr-defined]
        if not hasattr(console, "print_debug"):
            console.print_debug = types.MethodType(_print_debug, console)  # type: ignore[attr-defined]

        # 互換エイリアス（.info/.success/.warning/.error/.debug）
        if not hasattr(console, "info"):
            console.info = console.print_info  # type: ignore[attr-defined]
        if not hasattr(console, "success"):
            console.success = console.print_success  # type: ignore[attr-defined]
        if not hasattr(console, "warning"):
            console.warning = console.print_warning  # type: ignore[attr-defined]
        if not hasattr(console, "error"):
            console.error = console.print_error  # type: ignore[attr-defined]
        if not hasattr(console, "debug"):
            console.debug = console.print_debug  # type: ignore[attr-defined]

        _get_console._instance = console
    return _get_console._instance

# 公開用のコンソール取得関数
def get_console() -> Console:
    """統一Console取得関数（公開API）"""
    return _get_console()


# B30準拠: 共有Consoleインスタンス（統一管理システム）
console = _get_console()


def get_logger(name: str):
    """統一ログ管理サービス取得（委譲版）

    Note:
        過去の互換APIを維持しつつ、実体は
        `noveler.infrastructure.logging.unified_logger.get_logger` に完全委譲します。
        これにより、コンソール/ファイル出力・フォーマット・レベル制御を
        統一ロガー側の設定に集約します。

    Args:
        name: ロガー名（通常は__name__を指定）

    Returns:
        logging.Logger: 設定済みロガーインスタンス
    """
    return _get_unified_logger(name)


def get_logger_service(name: str = "noveler"):
    """Return a logger implementing the ILoggerService contract."""
    return _get_unified_logger(name)


class AppState:
    """アプリケーション状態管理"""

    def __init__(self) -> None:
        self.guide_root: Path | None = None
        self.project_root: Path | None = None
        self.scripts_dir: Path | None = None
        # Typer CLI削除により無効化（MCPサーバー専用アーキテクチャ対応）
        self.project_handler: object | None = None  # ProjectCommandHandler | None = None
        self.writing_handler: object | None = None  # WritingCommandHandler | None = None
        # self.plot_handler: PlotCommandHandler | None = None  # TODO: Module missing
        # self.quality_handler: QualityCommandHandler | None = None  # TODO: Module missing
        # self.health_handler: HealthCommandHandler | None = None  # TODO: Module missing
        self._initialized = False

    def initialize(self) -> bool:
        """アプリケーション状態の初期化"""
        if self._initialized:
            return True

        try:
            self.guide_root = find_guide_root()
            self.scripts_dir = self.guide_root / "scripts"

            # PROJECT_ROOT環境変数を最優先でチェック
            project_root_env = os.getenv("PROJECT_ROOT")
            if project_root_env:
                # 環境変数が設定されている場合はそれを使用
                self.project_root = Path(project_root_env)
                # ロガーの初期化が後になるため、この段階ではロギングしない
            else:
                # 環境初期化による自動検出（Typer CLI削除により無効化）
                # from noveler.presentation.cli.environment_setup import initialize_environment
                # env_result = initialize_environment()
                # self.project_root = env_result.get("project_root")
                # フォールバック: 現在ディレクトリを使用
                self.project_root = Path.cwd()

            # ハンドラー初期化（Typer CLI削除により無効化）
            # from noveler.presentation.cli.health_commands import HealthCommandHandler  # TODO: Module missing
            # from noveler.presentation.cli.plot_commands import PlotCommandHandler  # TODO: Module missing
            # from noveler.presentation.cli.project_commands import ProjectCommandHandler
            # from noveler.presentation.cli.quality_commands import QualityCommandHandler  # TODO: Module missing
            # from noveler.presentation.cli.writing_commands import WritingCommandHandler

            # self.project_handler = ProjectCommandHandler(self.project_root, self.scripts_dir)
            # self.writing_handler = WritingCommandHandler(self.project_root, self.scripts_dir)
            self.project_handler = None  # Typer CLI削除により無効化
            self.writing_handler = None  # Typer CLI削除により無効化
            # self.plot_handler = PlotCommandHandler(self.project_root, self.scripts_dir)  # TODO: Module missing
            # self.quality_handler = QualityCommandHandler(self.project_root, self.scripts_dir)  # TODO: Module missing
            # self.health_handler = HealthCommandHandler(self.project_root, self.scripts_dir)  # TODO: Module missing

            self._initialized = True
            return True

        except Exception as e:
            console.print(f"[red]初期化エラー: {e}[/red]")
            return False


# グローバル状態インスタンス
_app_state = AppState()


def get_app_state() -> AppState:
    """アプリケーション状態取得"""
    if not _app_state._initialized:
        _app_state.initialize()
    return _app_state


def get_project_folder_service(project_path: Path | None = None) -> "CommonPathService":
    """プロジェクトフォルダ構成サービス取得（CommonPathServiceに統合）

    Args:
        project_path: プロジェクトパス（省略時は自動検出）

    Returns:
        CommonPathService: 統合されたフォルダ構成サービス
    """
    return get_common_path_service(project_path)


def get_project_paths() -> "ProjectPaths":
    """プロジェクトパス情報取得（プロジェクト設定.yaml準拠）

    Returns:
        ProjectPaths: プロジェクトパス情報
    """
    common_service = get_common_path_service()
    return common_service.get_project_paths()


def get_writing_handler() -> object:
    """執筆ハンドラー取得（Typer CLI削除により無効化）"""
    msg = "執筆ハンドラーは利用できません（Typer CLIが削除され、MCPサーバー専用アーキテクチャに移行済み）"
    raise RuntimeError(msg)


def get_quality_handler() -> object:
    """品質ハンドラー取得（Typer CLI削除により無効化）"""
    msg = "品質ハンドラーは利用できません（Typer CLIが削除され、MCPサーバー専用アーキテクチャに移行済み）"
    raise RuntimeError(msg)


def get_project_handler() -> object:
    """プロジェクトハンドラー取得（Typer CLI削除により無効化）"""
    msg = "プロジェクトハンドラーは利用できません（Typer CLIが削除され、MCPサーバー専用アーキテクチャに移行済み）"
    raise RuntimeError(msg)


def get_plot_handler() -> object:
    """プロットハンドラー取得（Typer CLI削除により無効化）"""
    msg = "プロットハンドラーは利用できません（Typer CLIが削除され、MCPサーバー専用アーキテクチャに移行済み）"
    raise RuntimeError(msg)


def handle_command_error(error: Exception, context: str = "コマンド実行") -> None:
    """コマンドエラーハンドリング"""
    console.print(
        Panel(
            f"[red]{context}中にエラーが発生しました[/red]\n\n"
            f"エラー詳細: {error}\n\n"
            f"Traceback:\n"
            f'  File "{__file__}", line XXX, in {context.lower()}\n'
            f"    {type(error).__name__}: {error}",
            title="❌ エラー",
            border_style="red",
        )
    )


def handle_error(error: Exception, context: str = "処理") -> None:
    """B30品質作業指示書遵守: 統一エラーハンドリング

    Args:
        error: 発生した例外
        context: エラー発生コンテキスト
    """
    logger = get_logger(__name__)
    logger.error("%s中にエラーが発生: %s: %s", context, (type(error).__name__), error)
    handle_command_error(error, context)


def show_success_summary(action: str, details: dict[str, Any] | None = None) -> None:
    """成功サマリー表示"""
    panel_content = f"[green]{action}が完了しました[/green]"

    if details:
        panel_content += "\n\n詳細:"
        for key, value in details.items():
            panel_content += f"\n  • {key}: {value}"

    console.print(Panel(panel_content, title="✅ 完了", border_style="green"))


# 共通パス管理サービス
class CommonPathService(IPathService):
    """プロジェクト内のファイルパスを統一管理するサービス（プロジェクト設定.yaml対応版）"""

    def __init__(self, project_root: Path | None = None) -> None:
        self._project_root = project_root or self._detect_project_root()
        self._config_cache: dict | None = None
        self._paths_config: dict | None = None

    def _detect_project_root(self) -> Path:
        """プロジェクトルートを自動検出"""
        # 1. TARGET_PROJECT_ROOT 環境変数から取得（$GUIDE_ROOT環境での外部指定用）
        target_project_root = os.environ.get("TARGET_PROJECT_ROOT")
        if target_project_root:
            return Path(target_project_root)

        # 2. PROJECT_ROOT 環境変数から取得（従来の外部指定）
        env_project_root = os.environ.get("PROJECT_ROOT")
        if env_project_root:
            return Path(env_project_root)

        # 3. プロジェクト検出器による自動検出
        try:
            project_detector_module = importlib.import_module("noveler.infrastructure.config.project_detector")
            detect_project_root = getattr(project_detector_module, "detect_project_root")

            detected_root = detect_project_root()
            if detected_root:
                return detected_root
        except ImportError:
            pass  # フォールバック仕様なので、ログは不要

        # 4. 従来の方法でフォールバック
        current_dir = Path.cwd()
        while current_dir != current_dir.parent:
            if (current_dir / DEFAULT_PATH_CONFIG.manuscripts).exists() and (current_dir / DEFAULT_PATH_CONFIG.management).exists():
                return current_dir
            current_dir = current_dir.parent

        return Path.cwd()

    def _load_project_config(self) -> dict:
        """プロジェクト設定.yamlを読み込み"""
        if self._config_cache is not None:
            return self._config_cache

        config_file = self.project_root / "プロジェクト設定.yaml"
        if not config_file.exists():
            config_file = self.project_root / "project.yaml"
            if not config_file.exists():
                self._config_cache = {}
                return self._config_cache

        try:
            with Path(config_file).open(encoding="utf-8") as f:
                self._config_cache = yaml.safe_load(f) or {}
                return self._config_cache
        except (ImportError, Exception):
            self._config_cache = {}
            return self._config_cache

    def _get_folder_config(self, folder_key: str, default_name: str) -> Path:
        """設定ファイルからフォルダ設定を取得（デフォルト値付き）

        統合設定管理システム（novel_config.yaml）に対応。
        プロジェクト設定.yamlとnovel_config.yamlの両方をサポート。
        """
        if self._paths_config is None:
            # 1. プロジェクト設定.yaml から取得を試行
            project_config: dict[str, Any] = self._load_project_config()
            self._paths_config = project_config.get("paths", {})

            # 2. プロジェクト設定.yamlに設定がない場合、novel_config.yamlから取得
            if not self._paths_config or folder_key not in self._paths_config:
                try:
                    config_factory_module = importlib.import_module("noveler.infrastructure.factories.configuration_service_factory")
                    get_configuration_manager = getattr(config_factory_module, "get_configuration_manager")

                    config_manager = get_configuration_manager()
                    novel_config: dict[str, Any] = config_manager.get_configuration()

                    # project_pathsセクションから取得
                    project_paths_config: dict[str, Any] = {}
                    project_paths_str = novel_config._get_nested_value(["paths", "project_paths"])
                    if isinstance(project_paths_str, dict):
                        project_paths_config: dict[str, Any] = project_paths_str

                    # 統合設定を構築
                    self._paths_config = {**self._paths_config, **project_paths_config}
                except Exception:
                    # フォールバック: 空の設定
                    if not self._paths_config:
                        self._paths_config = {}

        folder_name = self._paths_config.get(folder_key, default_name)
        return self._project_root / folder_name

    # === 基本ディレクトリアクセス（プロジェクト設定.yaml対応） ===

    def get_manuscript_dir(self) -> Path:
        """原稿ディレクトリのパスを取得 (相対: 40_原稿)

        テストや一時プロジェクトの相対結合を安定化するため、
        ここでは相対パスを返します。実際の絶対解決は呼び出し側の
        project_rootとの結合で行われます。
        """
        return Path(DEFAULT_PATH_CONFIG.manuscripts)

    def get_cache_dir(self) -> Path:
        """キャッシュディレクトリのパスを取得"""
        return self.get_management_dir() / "cache"

    def get_management_dir(self) -> Path:
        """管理資料ディレクトリのパスを取得 (50_管理資料)

        既定ではプロジェクトルートからの相対パスを返却し、
        テスト環境でも安全に結合できるようにする。
        設定で絶対パスが指定されている場合はそのまま返却する。
        """
        management_path = self._get_folder_config("management", "50_管理資料")
        try:
            return management_path.relative_to(self._project_root)
        except ValueError:
            return management_path

    def get_plots_dir(self) -> Path:
        """プロットディレクトリのパスを取得 (相対: 20_プロット)

        テストや一時プロジェクトの相対結合を安定化するため、
        get_manuscript_dir() と同様に相対パスを返す。
        実際の絶対解決は呼び出し側の project_root との結合で行う。
        """
        return Path("20_プロット")

    # 旧メソッド名との互換性のため残す（廃止予定）
    def get_plot_dir(self) -> Path:
        """[DEPRECATED] プロットディレクトリのパスを取得 - get_plots_dir()を使用してください"""
        return self.get_plots_dir()

    def get_settings_dir(self) -> Path:
        """[DEPRECATED] 設定集ディレクトリのパスを取得 - get_management_dir()を使用してください"""
        return self.get_management_dir()

    def get_planning_dir(self) -> Path:
        """[DEPRECATED] 企画ディレクトリのパスを取得 - get_plots_dir()を使用してください"""
        return self.get_plots_dir()

    def get_archive_dir(self) -> Path:
        """アーカイブディレクトリのパスを取得 (90_アーカイブ)"""
        return self._get_folder_config("archive", "90_アーカイブ")

    # === 専用ディレクトリアクセス ===

    def get_checklist_dir(self) -> Path:
        """A31チェックリストディレクトリのパスを取得"""
        return self.get_management_dir() / "A31_チェックリスト"

    def get_backup_dir(self) -> Path:
        """バックアップディレクトリのパスを取得"""
        return self._get_folder_config("backup", "backup")

    def get_phase2_records_dir(self) -> Path:
        """Phase2記録ディレクトリのパスを取得"""
        return self.get_management_dir() / "phase2_records"

    def get_execution_records_dir(self) -> Path:
        """執筆記録ディレクトリのパスを取得"""
        return self.get_management_dir() / "執筆記録"

    def get_learning_data_dir(self) -> Path:
        """学習データディレクトリのパスを取得"""
        return self.get_management_dir() / "学習データ"

    def get_prompts_dir(self) -> Path:
        """プロンプト保存ディレクトリパスを取得"""
        return self._get_folder_config("prompts_dir", "60_プロンプト")

    # === サブディレクトリアクセス（章別プロット等） ===

    def get_chapter_plots_dir(self) -> Path:
        """章別プロットディレクトリのパスを取得（20_プロット/章別プロット）"""
        subfolder_name = self._get_subfolder_name("plot_subdirs", "chapter_plots")
        return self.get_plot_dir() / subfolder_name

    def get_episode_plots_dir(self) -> Path:
        """話別プロットディレクトリのパスを取得（20_プロット/話別プロット）"""
        subfolder_name = self._get_subfolder_name("plot_subdirs", "episode_plots")
        return self.get_plot_dir() / subfolder_name

    def get_quality_records_dir(self) -> Path:
        """品質記録ディレクトリのパスを取得（50_管理資料/品質記録）"""
        subfolder_name = self._get_subfolder_name("management_subdirs", "quality_records")
        return self.get_management_dir() / subfolder_name

    def get_a31_checklist_dir(self) -> Path:
        """A31チェックリストディレクトリのパスを取得（50_管理資料/A31_チェックリスト）"""
        subfolder_name = self._get_subfolder_name("management_subdirs", "checklist_records")
        return self.get_management_dir() / subfolder_name

    def get_analysis_results_dir(self) -> Path:
        """全話分析結果ディレクトリのパスを取得（60_プロンプト/全話分析結果）"""
        subfolder_name = self._get_subfolder_name("prompt_subdirs", "analysis_results")
        return self.get_prompts_dir() / subfolder_name

    def ensure_subfolder_directories_exist(self) -> None:
        """サブフォルダディレクトリの存在確保"""
        subdirs_to_create = [
            self.get_chapter_plots_dir(),
            self.get_episode_plots_dir(),
            self.get_quality_records_dir(),
            self.get_a31_checklist_dir(),
            self.get_analysis_results_dir(),
        ]

        for dir_path in subdirs_to_create:
            dir_path.mkdir(parents=True, exist_ok=True)

    # === IPathService抽象メソッド実装 ===

    def get_quality_dir(self) -> Path:
        """品質チェックディレクトリパスを取得"""
        return self.get_quality_records_dir()

    def get_reports_dir(self) -> Path:
        """レポートディレクトリパスを取得"""
        return self.get_management_dir() / "レポート"

    def ensure_directory_exists(self, directory: Path) -> None:
        """指定ディレクトリの存在確認・作成"""
        directory.mkdir(parents=True, exist_ok=True)

    @property
    def project_root(self) -> Path:
        """プロジェクトルートパスを取得

        Returns:
        Path: プロジェクトルートパス

        Note:
        統合API設計により、プロパティアクセスのみを提供。
        get_project_root()メソッドは廃止予定（互換性のため残存）
        """
        return self._project_root

    def get_project_root(self) -> Path:
        """プロジェクトルートパスを取得（廃止予定）

        Returns:
            Path: プロジェクトルートパス

        Deprecated:
            このメソッドは廃止予定です。代わりにproject_rootプロパティを使用してください。

        Migration:
            path_service.get_project_root() → path_service.project_root
        """
        warnings.warn(
            "get_project_root() method is deprecated. Use project_root property instead.",
            DeprecationWarning,
            stacklevel=2,
        )

        return self.project_root

    def get_episode_prompts_dir(self) -> Path:
        """話別プロットプロンプト保存ディレクトリパスを取得"""
        return self.get_prompts_dir() / "話別プロット"

    def get_quality_prompt_file_path(self, episode_number: int, episode_title: str = "") -> Path:
        """品質チェックプロンプトファイルパスを取得

        Args:
            episode_number: エピソード番号
            episode_title: エピソードタイトル（空の場合は番号のみ）

        Returns:
            品質チェックプロンプトファイルパス (第000話_{タイトル}.yaml形式)
        """
        episode_dir = self.get_episode_prompts_dir()
        if episode_title:
            sanitized_title = self._sanitize_filename(episode_title)
            filename = f"第{episode_number:03d}話_{sanitized_title}.yaml"
        else:
            filename = f"第{episode_number:03d}話.yaml"
        return episode_dir / filename

    def get_episode_title(self, episode_number: int) -> str:
        """エピソードタイトルを取得（PathServiceへ委譲）

        章/話別プロット・設定からの解決を共通基盤に集約。
        取得できない場合は空文字を返す。
        """
        try:
            path_service_adapter_module = importlib.import_module("noveler.infrastructure.adapters.path_service_adapter")
            create_path_service = getattr(path_service_adapter_module, "create_path_service")
            path_service = create_path_service(self.project_root)
            title = path_service.get_episode_title(episode_number)
            return title or ""
        except Exception:
            return ""

    # === ファイルパス生成 ===

    def get_episode_file_path(self, episode_number: int, title: str) -> Path:
        """エピソードファイルのパスを取得（PathServiceへ委譲）

        title引数は後方互換のため残置。実際のファイル名はPathService側の
        タイトル解決ロジックに基づく統一命名で返す。
        """
        try:
            path_service_adapter_module = importlib.import_module("noveler.infrastructure.adapters.path_service_adapter")
            create_path_service = getattr(path_service_adapter_module, "create_path_service")
            path_service = create_path_service(self.project_root)
            return path_service.get_manuscript_path(episode_number)
        except Exception:
            # フォールバック: 従来の組み立て
            safe_title = self._sanitize_filename(title)
            return self.get_manuscript_dir() / f"第{episode_number:03d}話_{safe_title}.md"

    def get_episode_file_pattern(self, episode_number: int) -> str:
        """エピソードファイル検索パターンを取得"""
        return f"第{episode_number:03d}話_*.md"

    def get_checklist_file_path(self, episode_number: int, title: str) -> Path:
        """A31チェックリストファイルのパスを取得"""
        safe_title = self._sanitize_filename(title)
        return self.get_checklist_dir() / f"A31_チェックリスト_第{episode_number:03d}話_{safe_title}.yaml"

    # === 管理ファイルアクセス ===

    def get_episode_management_file(self) -> Path:
        """話数管理ファイルのパスを取得"""
        try:
            cfg_mod = importlib.import_module("noveler.infrastructure.factories.configuration_service_factory")
            get_configuration_manager = getattr(cfg_mod, "get_configuration_manager")
            cm = get_configuration_manager()
            fname = cm.get_file_template("episode_management")
        except Exception:
            fname = self._get_file_name_config("episode_management", "話数管理.yaml")
        return self.get_management_dir() / fname

    # === 追加実装: IPathServiceの必須メソッド ===
    def get_manuscript_filename(self, episode_number: int) -> str:
        """原稿ファイル名を取得（第NNN話_{title}.md 規約）"""
        try:
            title = self.get_episode_title(episode_number) or "無題"
        except Exception:
            title = "無題"
        safe_title = self._sanitize_filename(str(title).strip() or "無題")
        return f"第{episode_number:03d}話_{safe_title}.md"

    def get_manuscript_path(self, episode_number: int) -> Path:
        """原稿ファイルの絶対パスを取得（ディレクトリ自動生成含む）"""
        mdir = self.get_manuscript_dir()
        try:
            mdir.mkdir(parents=True, exist_ok=True)
        except Exception:
            # ディレクトリ作成に失敗してもパスは返す（呼び出し側で扱う）
            pass
        return mdir / self.get_manuscript_filename(episode_number)

    def get_episode_plot_path(self, episode_number: int) -> Path | None:
        """話別プロットファイルのパスを取得（存在しなければNone）"""
        # 優先: 20_プロット/話別プロット の新旧命名
        try:
            ep_dir = self.get_episode_plots_dir()
        except Exception:
            ep_dir = self.get_plots_dir() / "話別プロット"

        candidates: list[Path] = [
            ep_dir / f"ep{episode_number:03d}.yaml",  # A38 v2正式
            ep_dir / f"ep{episode_number:03d}.yml",
            ep_dir / f"episode{episode_number:03d}_plot.yaml",
            ep_dir / f"第{episode_number:03d}話_プロット.yaml",
            ep_dir / f"第{episode_number:03d}話.yaml",
            ep_dir / f"EP{episode_number:03d}.yaml",
        ]

        # ルート直下のフォールバック
        plots_root = self.get_plots_dir()
        candidates.extend([
            plots_root / f"ep{episode_number:03d}.yaml",
            plots_root / f"ep{episode_number:03d}.yml",
            plots_root / f"episode{episode_number:03d}.yaml",
            plots_root / f"EP{episode_number:03d}.yaml",
        ])

        for p in candidates:
            try:
                if p.exists():
                    return p
            except Exception:
                continue
        return None

    def get_quality_config_file(self) -> Path:
        """品質チェック設定ファイルのパスを取得"""
        return self.get_management_dir() / "品質チェック設定.yaml"

    def get_quality_record_file(self) -> Path:
        """品質記録ファイルのパスを取得"""
        return self.get_management_dir() / "品質記録.yaml"

    def get_project_config_file(self) -> Path:
        """プロジェクト設定ファイルのパスを取得"""
        # B30品質作業指示書準拠: プロジェクト設定.yamlファイル名もカスタマイズ可能
        filename = self._get_file_name_config("project_config", "プロジェクト設定.yaml")
        return self._project_root / filename

    def get_project_settings_file(self) -> Path:
        """プロジェクト設定ファイルのパスを取得（非推奨）"""
        warnings.warn(
            "get_project_settings_file() is deprecated. Use get_project_config_file() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.get_project_config_file()

    def get_proposal_file(self) -> Path:
        """企画書ファイルのパスを取得"""
        # B30品質作業指示書準拠: ファイル名もプロジェクト設定から取得
        filename = self._get_file_name_config("proposal_file", "企画書.yaml")
        return self.get_planning_dir() / filename

    def get_reader_analysis_file(self) -> Path:
        """読者分析ファイルのパスを取得"""
        # B30品質作業指示書準拠: ファイル名もプロジェクト設定から取得
        filename = self._get_file_name_config("reader_analysis_file", "読者分析.yaml")
        return self.get_planning_dir() / filename

    def get_foreshadowing_file(self) -> Path:
        """伏線管理ファイルのパスを取得"""
        return self.get_management_dir() / "伏線管理.yaml"

    def get_scene_file(self) -> Path:
        """重要シーンファイルのパスを取得"""
        return self.get_management_dir() / "重要シーン.yaml"

    def get_character_file(self) -> Path:
        """キャラクター設定ファイルのパスを取得"""
        return self.get_settings_dir() / "キャラクター.yaml"

    def get_plot_progress_file(self) -> Path:
        """プロット進捗ファイルのパスを取得"""
        return self.get_management_dir() / "プロット進捗.yaml"

    def get_plot_validation_rules_file(self) -> Path:
        """プロット検証ルールファイルのパスを取得"""
        return self.get_management_dir() / "プロット検証ルール.yaml"

    def get_plot_validation_results_file(self) -> Path:
        """プロット検証結果ファイルのパスを取得"""
        return self.get_management_dir() / "プロット検証結果.yaml"

    def get_revision_history_file(self) -> Path:
        """改訂履歴ファイルのパスを取得"""
        return self.get_management_dir() / "改訂履歴.yaml"

    def get_access_analysis_file(self) -> Path:
        """アクセス分析ファイルのパスを取得"""
        return self.get_management_dir() / "アクセス分析.yaml"

    def get_ai_learning_file(self) -> Path:
        """AI学習用品質記録ファイルのパスを取得"""
        return self.get_management_dir() / "品質記録_AI学習用.yaml"

    def get_learning_session_file(self) -> Path:
        """学習セッション記録ファイルのパスを取得"""
        return self.get_management_dir() / "学習セッション記録.yaml"

    def get_writing_logs_dir(self) -> Path:
        """原稿執筆ログディレクトリのパスを取得"""
        return self.get_management_dir() / "執筆ログ"

    # === ディレクトリ判定 ===

    def get_required_directories(self) -> list[str]:
        """必須ディレクトリリストを取得"""
        # B20準拠: デフォルト値を使用（設定管理システムの移行まで）
        return [
            "10_企画",
            DEFAULT_PATH_CONFIG.plots,
            DEFAULT_PATH_CONFIG.settings,
            DEFAULT_PATH_CONFIG.manuscripts,
            DEFAULT_PATH_CONFIG.management,
        ]

    def get_all_directories(self) -> list[str]:
        """全ディレクトリリストを取得"""
        # B20準拠: デフォルト値を使用（設定管理システムの移行まで）
        return [
            "10_企画",
            DEFAULT_PATH_CONFIG.plots,
            DEFAULT_PATH_CONFIG.settings,
            DEFAULT_PATH_CONFIG.manuscripts,
            DEFAULT_PATH_CONFIG.management,
            DEFAULT_PATH_CONFIG.backup,
        ]

    def is_project_directory(self, path: Path) -> bool:
        """プロジェクトディレクトリかどうかを判定"""
        # B20準拠: 動的にディレクトリ名を取得
        manuscript_dir = self.get_manuscript_dir().name
        management_dir = self.get_management_dir().name
        return (path / manuscript_dir).exists() and (path / management_dir).exists()

    def is_manuscript_file(self, file_path: Path) -> bool:
        """原稿ファイルかどうかを判定"""
        # B20準拠: 動的にディレクトリ名を取得
        manuscript_dir_name = self.get_manuscript_dir().name
        return (
            file_path.suffix == ".md"
            and file_path.parent.name == manuscript_dir_name
            and "第" in file_path.stem
            and "話_" in file_path.stem
        )

    # === ユーティリティ ===

    def _sanitize_filename(self, filename: str) -> str:
        """ファイル名として使用できない文字を置換"""
        # Windows/Linux で使用できない文字を_に置換
        return re.sub(r'[\\/:*?"<>|]', "_", filename)

    def resolve_path_template(self, template_path: str) -> Path:
        """パステンプレート($PROJECT_ROOT等)を実際のパスに解決"""
        resolved = template_path.replace("$PROJECT_ROOT", str(self.project_root))
        resolved = resolved.replace("$GUIDE_ROOT", str(os.environ.get("GUIDE_ROOT", "")))
        return Path(resolved)

    # === 新機能：プロジェクト設定.yaml統合 ===

    def get_project_paths(self) -> "ProjectPaths":
        """プロジェクトパス情報をProjectPathsオブジェクトとして取得"""
        try:
            project_paths_module = importlib.import_module("noveler.domain.value_objects.project_paths")
            ProjectPaths = getattr(project_paths_module, "ProjectPaths")

            return ProjectPaths(
                project_root=self.project_root,
                manuscripts=self.get_manuscript_dir(),
                management=self.get_management_dir(),
                plots=self.get_plot_dir(),
                settings=self.get_settings_dir(),
                backup=self.get_backup_dir(),
            )

        except ImportError as e:
            # ProjectPathsが利用できない場合のフォールバック
            msg = "ProjectPaths バリューオブジェクトがインポートできません"
            raise RuntimeError(msg) from e

    def _get_subfolder_name(self, category: str, key: str) -> str:
        """サブフォルダ名を設定から取得"""
        try:
            config_factory_module = importlib.import_module("noveler.infrastructure.factories.configuration_service_factory")
            get_configuration_manager = getattr(config_factory_module, "get_configuration_manager")

            config_manager = get_configuration_manager()
            config = config_manager.get_configuration()

            subfolder_name = config.get_nested_value(["paths", "sub_directories", category, key])
            if subfolder_name:
                return subfolder_name
        except Exception:
            # 設定取得エラー時はデフォルト値を使用（意図的なフォールバック）
            pass

        # デフォルト値のフォールバック
        defaults = {
            ("plot_subdirs", "chapter_plots"): "章別プロット",
            ("plot_subdirs", "episode_plots"): "話別プロット",
            ("management_subdirs", "quality_records"): "品質記録",
            ("management_subdirs", "checklist_records"): "A31_チェックリスト",
            ("prompt_subdirs", "analysis_results"): "全話分析結果",
        }
        return defaults.get((category, key), key)

    def _get_file_name_config(self, config_key: str, default_filename: str) -> str:
        """プロジェクト設定からファイル名を取得

        Args:
            config_key: 設定キー
            default_filename: デフォルトファイル名

        Returns:
            設定されたファイル名またはデフォルト
        """
        try:
            if hasattr(self, "_project_config") and self._project_config:
                file_names = self._project_config.get("file_names", {})
                return file_names.get(config_key, default_filename)
        except Exception:
            pass
        return default_filename

    def ensure_directories_exist(self) -> None:
        """必要なディレクトリが存在することを確認し、なければ作成"""
        directories_to_create = [
            self.get_manuscript_dir(),
            self.get_management_dir(),
            self.get_quality_records_dir(),  # サブディレクトリメソッド使用
            self.get_checklist_dir(),
            self.get_plot_dir(),
            self.get_chapter_plots_dir(),  # サブディレクトリメソッド使用
            self.get_settings_dir(),
            self.get_prompts_dir(),
            self.get_episode_plots_dir(),  # サブディレクトリメソッド使用
        ]

        for directory in directories_to_create:
            directory.mkdir(parents=True, exist_ok=True)

    # 互換API: get_spec_path（テストが利用）
    def get_spec_path(self) -> Path:
        """仕様書ディレクトリパス（後方互換API）"""
        path = self.project_root / "specs"
        path.mkdir(parents=True, exist_ok=True)
        return path


# グローバルインスタンス
_common_path_service = None


def get_common_path_service(
    project_root: Path | None = None, target_project_root: Path | None = None
) -> "CommonPathService":
    """共通パス管理サービスのインスタンスを取得

    Args:
        project_root: プロジェクトルートパス（既存機能・後方互換）
        target_project_root: ターゲットプロジェクトルートパス（$GUIDE_ROOT環境での外部指定用）
    """
    global _common_path_service

    # target_project_rootが指定された場合は、一時的に環境変数に設定
    original_target_project_root = None
    if target_project_root:
        original_target_project_root = os.environ.get("TARGET_PROJECT_ROOT")
        os.environ["TARGET_PROJECT_ROOT"] = str(target_project_root)

    try:
        # 既存のproject_rootパラメータ、または環境変数によってルートを決定
        effective_project_root = project_root or (Path(target_project_root) if target_project_root else None)

        cached_service = _common_path_service

        # Some tests replace the global cache with stand-in mocks; ensure we rebuild
        # the concrete service when that happens so downstream callers receive the
        # real path manager.
        need_reinit = cached_service is None or not isinstance(cached_service, CommonPathService)

        env_designated_root: Path | None = None
        if effective_project_root is None:
            env_target = os.environ.get("TARGET_PROJECT_ROOT")
            env_fallback = os.environ.get("PROJECT_ROOT") if env_target is None else None
            env_value = env_target or env_fallback
            if env_value:
                env_designated_root = Path(env_value)

        if not need_reinit:
            # 指定のプロジェクトルートがある場合は一致性を優先
            if (
                effective_project_root
                and _common_path_service.project_root != effective_project_root
            ) or not _common_path_service.project_root.exists():
                need_reinit = True
            elif env_designated_root and _common_path_service.project_root != env_designated_root:
                need_reinit = True

        if need_reinit:
            resolved_root = effective_project_root or env_designated_root or Path.cwd()
            _common_path_service = CommonPathService(resolved_root)
        return _common_path_service
    finally:
        # 環境変数を元に戻す
        if target_project_root:
            if original_target_project_root is not None:
                os.environ["TARGET_PROJECT_ROOT"] = original_target_project_root
            else:
                os.environ.pop("TARGET_PROJECT_ROOT", None)


def reset_common_path_service() -> None:
    """Reset the cached CommonPathService instance (test utility).

    Purpose:
        Allow tests or callers to explicitly clear the global cache so that
        the next call to get_common_path_service() will reinitialise with the
        desired project root.

    Side Effects:
        Sets the module-level _common_path_service to None.
    """
    global _common_path_service
    _common_path_service = None
