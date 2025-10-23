"""Domain.services.writing_steps.manuscript_generator_service
Where: Domain service module implementing a specific writing workflow step.
What: Provides helper routines and data structures for this writing step.
Why: Allows stepwise writing orchestrators to reuse consistent step logic.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""STEP 10: ManuscriptGeneratorService

A38執筆プロンプトガイドのSTEP 10に対応するマイクロサービス。
既存のIntegratedWritingUseCaseをベースに15ステップ体系に適応。
"""

import re
import time
import uuid
from dataclasses import dataclass, field
import importlib
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from noveler.domain.exceptions.manuscript_exceptions import (
    InvalidProjectConfigError,
    ProjectConfigNotFoundError,
    TargetLengthNotDefinedError,
    WorkspaceInitializationError,
)
from noveler.domain.interfaces.path_service import IPathService

if TYPE_CHECKING:
    from noveler.domain.interfaces.logger_service_protocol import ILoggerService
    from noveler.domain.interfaces.path_service_protocol import IPathService
    from typing import Any as ConfigurationManager

from noveler.domain.services.writing_steps.base_writing_step import BaseWritingStep, WritingStepResponse
from noveler.domain.services.writing_steps.plot_analyzer_service import PlotAnalysisResult
from noveler.domain.value_objects.project_time import project_now
from noveler.domain.value_objects.scene_data import SceneData


@dataclass
class ManuscriptGenerationWorkspace:
    """原稿生成作業領域"""

    # 基本設定
    episode_number: int
    project_root: Path
    target_word_count: int = 4000

    # ファイルパス管理
    yaml_prompt_path: Path | None = None
    manuscript_path: Path | None = None

    # コンテンツ管理
    manuscript_header: str = ""
    template_content: str = ""
    episode_title: str | None = None
    generated_content: str = ""  # SPEC-PLOT-MANUSCRIPT-001で追加

    # プロット関連（SPEC-PLOT-MANUSCRIPT-001で追加）
    plot_analysis_result: PlotAnalysisResult | None = None
    scenes: list[SceneData] = field(default_factory=list)

    # プロンプト統合情報
    custom_requirements: list[str] = field(default_factory=list)
    plot_requirements: list[str] = field(default_factory=list)

    # メタデータ
    generation_time_ms: float = 0.0
    file_exists: bool = False


@dataclass
class ManuscriptGeneratorResponse(WritingStepResponse):
    """原稿生成サービス結果"""

    # 基底クラスのフィールド継承
    # success, execution_time_ms, error_message

    # 原稿生成固有の結果
    manuscript_path: Path | None = None
    yaml_prompt_path: Path | None = None
    episode_title: str | None = None

    # コンテンツ情報
    content_created: bool = False
    existing_content_preserved: bool = False
    template_applied: bool = False

    # パフォーマンス情報
    file_size_bytes: int = 0
    title_extraction_time_ms: float = 0.0
    scenes_converted: int = 0  # SPEC-PLOT-MANUSCRIPT-001で追加
    plot_integration_enabled: bool = False  # SPEC-PLOT-MANUSCRIPT-001で追加


class ManuscriptGeneratorService(BaseWritingStep):
    """STEP 10: 原稿生成マイクロサービス

    IntegratedWritingUseCaseの原稿生成機能を15ステップ体系に適応。
    プロンプト連携、ファイル管理、テンプレート適用を統合管理。
    """

    def __init__(
        self,
        logger_service: ILoggerService | None = None,
        path_service: IPathService | None = None,
        config_manager: ConfigurationManager | None = None,
        **kwargs: Any
    ) -> None:
        """原稿生成サービス初期化

        ゴールデンサンプルパターンに基づく依存性注入対応。

        Args:
            logger_service: ロガーサービス
            path_service: パスサービス（DI注入）
            config_manager: 設定管理サービス（DI注入）
            **kwargs: BaseWritingStepの引数
        """
        super().__init__(step_number=10, step_name="manuscript_generator", **kwargs)

        self._logger_service = logger_service
        self._path_service = path_service
        self._config_manager = config_manager

        # 遅延初期化フラグ
        self._initialized = False

    async def execute(
        self,
        episode_number: int,
        previous_results: dict[int, Any] | None = None
    ) -> ManuscriptGeneratorResponse:
        """原稿生成実行

        Args:
            episode_number: エピソード番号
            previous_results: 前ステップの結果（STEP 0-9の結果を使用）

        Returns:
            ManuscriptGeneratorResponse: 原稿生成結果
        """
        start_time = time.time()
        self._generate_session_id()

        try:
            if self._logger_service:
                self._logger_service.info(f"STEP 10 原稿生成開始: エピソード={episode_number}")

            # 1. 作業領域初期化
            workspace = await self._initialize_workspace(episode_number, previous_results)

            # 2. エピソードタイトル抽出
            title_start = time.time()
            workspace.episode_title = await self._extract_episode_title(workspace)
            title_time = (time.time() - title_start) * 1000

            # 3. ファイルパス生成
            await self._generate_file_paths(workspace)

            # 4. YAMLプロンプト処理（前ステップ結果活用）
            await self._process_yaml_prompt(workspace, previous_results)

            # 4.5. プロット解析結果統合（SPEC-PLOT-MANUSCRIPT-001で追加）
            await self._integrate_plot_analysis(workspace, previous_results)

            # 5. 原稿テンプレート生成・適用
            await self._apply_manuscript_template(workspace)

            # 6. 成功応答作成
            execution_time = (time.time() - start_time) * 1000

            return ManuscriptGeneratorResponse(
                success=True,
                step_number=10,
                step_name="manuscript_generator",
                execution_time_ms=execution_time,

                # 原稿生成固有フィールド
                manuscript_path=workspace.manuscript_path,
                yaml_prompt_path=workspace.yaml_prompt_path,
                episode_title=workspace.episode_title,

                content_created=not workspace.file_exists,
                existing_content_preserved=workspace.file_exists,
                template_applied=True,

                # パフォーマンス情報
                file_size_bytes=self._get_file_size(workspace.manuscript_path),
                title_extraction_time_ms=title_time,
                scenes_converted=len(workspace.scenes),  # SPEC-PLOT-MANUSCRIPT-001で追加
                plot_integration_enabled=workspace.plot_analysis_result is not None  # SPEC-PLOT-MANUSCRIPT-001で追加
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_message = f"STEP 10 原稿生成エラー: {e}"

            if self._logger_service:
                self._logger_service.error(error_message)

            return ManuscriptGeneratorResponse(
                success=False,
                step_number=10,
                step_name="manuscript_generator",
                execution_time_ms=execution_time,
                error_message=error_message
            )

    async def _initialize_workspace(
        self,
        episode_number: int,
        previous_results: dict[int, Any] | None
    ) -> ManuscriptGenerationWorkspace:
        """作業領域初期化

        ゴールデンサンプルパターンに基づくリファクタリング版。
        ConfigurationManagerを使用して設定を管理。

        Args:
            episode_number: エピソード番号
            previous_results: 前ステップ結果

        Returns:
            ManuscriptGenerationWorkspace: 初期化された作業領域

        Raises:
            WorkspaceInitializationError: 作業領域の初期化に失敗した場合
        """
        try:
            # プロジェクトルート取得
            project_root = self._get_project_root(previous_results)

            # プロジェクト設定を読み込む
            project_config = await self._load_project_settings(project_root)

            # 目標文字数を取得
            target_word_count = self._extract_target_word_count(
                project_config, previous_results
            )

            # カスタム要件を収集
            custom_requirements, plot_requirements = self._collect_requirements(
                previous_results
            )

            return ManuscriptGenerationWorkspace(
                episode_number=episode_number,
                project_root=project_root,
                target_word_count=target_word_count,
                custom_requirements=custom_requirements,
                plot_requirements=plot_requirements
            )

        except Exception as e:
            raise WorkspaceInitializationError(
                reason=str(e),
                episode_number=episode_number
            ) from e

    def _get_project_root(self, previous_results: dict[int, Any] | None) -> Path:
        """プロジェクトルートを取得

        Args:
            previous_results: 前ステップ結果

        Returns:
            プロジェクトルートパス
        """
        if previous_results and 0 in previous_results:
            scope_result = previous_results[0]
            if "project_root" in scope_result:
                return Path(scope_result["project_root"])
        return Path.cwd()

    async def _load_project_settings(self, project_root: Path) -> dict[str, Any]:
        """プロジェクト設定を読み込む

        ConfigurationManagerを使用して設定を読み込む。

        Args:
            project_root: プロジェクトルート

        Returns:
            プロジェクト設定辞書

        Raises:
            ProjectConfigNotFoundError: 設定ファイルが見つからない場合
            InvalidProjectConfigError: 設定が不正な場合
        """
        # ConfigurationManagerの遅延初期化
        if self._config_manager is None:
            try:
                _mod = importlib.import_module('noveler.infrastructure.factories.configuration_service_factory')
                get_configuration_manager = getattr(_mod, 'get_configuration_manager')
                self._config_manager = get_configuration_manager()
            except Exception:
                self._config_manager = None

        # 設定を読み込む
        config = None
        if self._config_manager is not None:
            try:
                config = self._config_manager.get_project_configuration(project_root)
            except Exception:
                config = None
        if config is None:
            # フォールバック: 直接ファイルを確認
            config_path = project_root / "プロジェクト設定.yaml"
            if not config_path.exists():
                raise ProjectConfigNotFoundError(config_path)

            # 直接読み込みを試行
            try:
                with open(config_path, encoding="utf-8") as f:
                    config = yaml.safe_load(f)
            except Exception as e:
                raise InvalidProjectConfigError(
                    reason=f"設定ファイルの読み込みに失敗: {e}",
                    config_path=config_path
                ) from e

        return config

    def _extract_target_word_count(
        self,
        project_config: dict[str, Any],
        previous_results: dict[int, Any] | None
    ) -> int:
        """目標文字数を抽出

        Args:
            project_config: プロジェクト設定
            previous_results: 前ステップ結果

        Returns:
            目標文字数

        Raises:
            InvalidProjectConfigError: settingsセクションがない場合
            TargetLengthNotDefinedError: target_length_per_episodeが未定義の場合
        """
        # 前ステップから明示的に指定されている場合
        if previous_results:
            for result in previous_results.values():
                if isinstance(result, dict) and "target_word_count" in result:
                    return int(result["target_word_count"])

        # プロジェクト設定から取得
        if "settings" not in project_config:
            raise InvalidProjectConfigError(
                reason="'settings'セクションが定義されていません"
            )

        settings = project_config["settings"]
        if "target_length_per_episode" not in settings:
            raise TargetLengthNotDefinedError

        return int(settings["target_length_per_episode"])

    def _collect_requirements(
        self,
        previous_results: dict[int, Any] | None
    ) -> tuple[list[str], list[str]]:
        """前ステップから要件を収集

        Args:
            previous_results: 前ステップ結果

        Returns:
            (カスタム要件リスト, プロット要件リスト)のタプル
        """
        custom_requirements = []
        plot_requirements = []

        if previous_results:
            for step_result in previous_results.values():
                if isinstance(step_result, dict):
                    if "requirements" in step_result:
                        custom_requirements.extend(step_result["requirements"])
                    if "plot_points" in step_result:
                        plot_requirements.extend(step_result["plot_points"])

        return custom_requirements, plot_requirements

    async def _extract_episode_title(
        self,
        workspace: ManuscriptGenerationWorkspace
    ) -> str | None:
        """エピソードタイトル抽出

        IntegratedWritingUseCaseの_extract_episode_titleを15ステップ対応版として統合

        Args:
            workspace: 作業領域

        Returns:
            Optional[str]: 抽出されたタイトル
        """
        episode_number = workspace.episode_number
        project_root = workspace.project_root

        try:
            # 方法1: プロットディレクトリから話別プロットファイル検索
            if self._path_service:
                plot_dir = self._path_service.get_plot_dir() / "話別プロット"
            else:
                plot_dir = project_root / "設定" / "プロット" / "話別プロット"

            if plot_dir.exists():
                plot_file_patterns = [
                    f"ep{episode_number:03d}*.yaml",
                    f"ep{episode_number:03d}*.yml",
                    f"第{episode_number:03d}話*.yaml",
                    f"第{episode_number:03d}話*.yml",
                    f"episode{episode_number:03d}*.yaml",
                    f"EP{episode_number:03d}*.yaml",
                    f"EP{episode_number:03d}.yaml",
                    f"{episode_number:03d}*.yaml",
                ]

                for pattern in plot_file_patterns:
                    matching_files = list(plot_dir.glob(pattern))
                    if matching_files:
                        # ファイル名からタイトル抽出
                        filename = matching_files[0].stem
                        if "_" in filename:
                            title = filename.split("_", 1)[1]
                            return self._sanitize_filename(title)

                        # YAML内容からタイトル抽出
                        try:
                            with open(matching_files[0], encoding="utf-8") as f:
                                yaml_content = yaml.safe_load(f)
                                if isinstance(yaml_content, dict) and "title" in yaml_content:
                                    return self._sanitize_filename(yaml_content["title"])
                        except Exception:
                            continue

            # 方法2: エピソード設定ファイルから取得
            if self._path_service:
                episode_settings = self._path_service.get_settings_dir() / "エピソード設定.yaml"
            else:
                episode_settings = project_root / "設定" / "エピソード設定.yaml"

            if episode_settings.exists():
                with open(episode_settings, encoding="utf-8") as f:
                    settings = yaml.safe_load(f)
                    episodes = settings.get("episodes", {})
                    episode_key = f"第{episode_number:03d}話"
                    if episode_key in episodes:
                        episode_info = episodes[episode_key]
                        if isinstance(episode_info, dict) and "title" in episode_info:
                            return self._sanitize_filename(episode_info["title"])

            return None

        except Exception:
            return None

    async def _generate_file_paths(self, workspace: ManuscriptGenerationWorkspace) -> None:
        """ファイルパス生成

        Args:
            workspace: 作業領域
        """
        episode_number = workspace.episode_number
        episode_title = workspace.episode_title or "無題"

        # 原稿ファイル名生成（正式命名規則対応）
        filename = f"第{episode_number:03d}話_{episode_title}.md"
        workspace.manuscript_header = f"第{episode_number:03d}話　{episode_title}"

        # パス生成（DI注入パスサービス優先・B20集約）
        if self._path_service:
            workspace.manuscript_path = self._path_service.get_manuscript_path(episode_number)
            prompts_dir = self._path_service.get_prompts_dir()
        else:
            manuscript_dir = workspace.project_root / "原稿"
            manuscript_dir.mkdir(parents=True, exist_ok=True)
            prompts_dir = workspace.project_root / "プロンプト"
            prompts_dir.mkdir(parents=True, exist_ok=True)
            workspace.manuscript_path = manuscript_dir / filename
        workspace.yaml_prompt_path = prompts_dir / f"第{episode_number:03d}話_プロンプト.yaml"

        # 既存ファイル確認
        workspace.file_exists = workspace.manuscript_path.exists()

    async def _process_yaml_prompt(
        self,
        workspace: ManuscriptGenerationWorkspace,
        previous_results: dict[int, Any] | None
    ) -> None:
        """YAMLプロンプト処理

        Args:
            workspace: 作業領域
            previous_results: 前ステップ結果（プロンプト情報が含まれる可能性）
        """
        # 前ステップからYAMLプロンプトパス取得
        if previous_results:
            for step_result in previous_results.values():
                if isinstance(step_result, dict) and "yaml_prompt_path" in step_result:
                    workspace.yaml_prompt_path = Path(step_result["yaml_prompt_path"])  # TODO: IPathServiceを使用するように修正
                    break

        # YAMLプロンプトファイルが存在しない場合は基本情報で補完
        if not workspace.yaml_prompt_path or not workspace.yaml_prompt_path.exists():
            await self._create_basic_yaml_prompt(workspace)

    async def _create_basic_yaml_prompt(self, workspace: ManuscriptGenerationWorkspace) -> None:
        """基本YAMLプロンプト作成

        Args:
            workspace: 作業領域
        """
        if not workspace.yaml_prompt_path:
            return

        # 基本的なYAMLプロンプト内容作成

        yaml_content = {
            "metadata": {
                "title": f"第{workspace.episode_number:03d}話プロンプト",
                "episode": workspace.episode_number,
                "target_words": workspace.target_word_count,
                "created_at": project_now().datetime.strftime("%Y-%m-%d %H:%M:%S")
            },
            "requirements": workspace.custom_requirements,
            "plot_requirements": workspace.plot_requirements
        }

        try:
            workspace.yaml_prompt_path.parent.mkdir(parents=True, exist_ok=True)
            with open(workspace.yaml_prompt_path, "w", encoding="utf-8") as f:
                yaml.dump(yaml_content, f, allow_unicode=True, default_flow_style=False)
        except Exception as e:
            if self._logger_service:
                self._logger_service.warning(f"YAMLプロンプト作成失敗: {e}")

    async def _apply_manuscript_template(self, workspace: ManuscriptGenerationWorkspace) -> None:
        """原稿テンプレート適用

        Args:
            workspace: 作業領域
        """
        if not workspace.manuscript_path:
            return

        # 既存コンテンツ保護処理
        if workspace.file_exists:
            existing_content = workspace.manuscript_path.read_text(encoding="utf-8")

            # テンプレートのみかどうか判定
            if self._is_template_only(existing_content):
                # テンプレートのみの場合は更新
                template_content = self._generate_template_content(workspace)
                workspace.manuscript_path.write_text(template_content, encoding="utf-8")
            else:
                # 実コンテンツが存在する場合は保護
                return
        else:
            # 新規ファイル作成
            template_content = self._generate_template_content(workspace)
            workspace.manuscript_path.write_text(template_content, encoding="utf-8")

    def _is_template_only(self, content: str) -> bool:
        """テンプレートのみかどうか判定

        Args:
            content: ファイルコンテンツ

        Returns:
            bool: テンプレートのみの場合True
        """
        # 段階的執筆プロセスマーカーがあり、実コンテンツがない場合
        return ("段階的執筆プロセス" in content or
                "YAML プロンプトファイル" in content) and "Stage" not in content

    def _generate_template_content(self, workspace: ManuscriptGenerationWorkspace) -> str:
        """テンプレートコンテンツ生成

        Args:
            workspace: 作業領域

        Returns:
            str: 生成されたテンプレートコンテンツ
        """
        yaml_path_comment = ""
        if workspace.yaml_prompt_path:
            yaml_path_comment = f"<!-- YAML プロンプトファイル: {workspace.yaml_prompt_path} -->"

        return f"""# {workspace.manuscript_header}

## 本文

{yaml_path_comment}
<!-- 15ステップ段階的執筆プロセスに従って執筆してください -->
<!-- 目標文字数: {workspace.target_word_count}文字 -->

"""

    def _sanitize_filename(self, title: str) -> str:
        """ファイル名用文字列サニタイズ

        Args:
            title: 元のタイトル

        Returns:
            str: サニタイズされたタイトル
        """
        if not title:
            return ""


        # ファイル名に使用できない文字を除去・置換
        sanitized = re.sub(r'[<>:"/\\|?*]', "", title)
        # 連続空白を単一空白に
        sanitized = re.sub(r"\s+", " ", sanitized).strip()
        # 長すぎる場合は50文字に制限
        if len(sanitized) > 50:
            sanitized = sanitized[:50].strip()

        return sanitized

    def _get_file_size(self, file_path: Path | None) -> int:
        """ファイルサイズ取得

        Args:
            file_path: ファイルパス

        Returns:
            int: ファイルサイズ（バイト）
        """
        if file_path and file_path.exists():
            return file_path.stat().st_size
        return 0

    def _generate_session_id(self) -> str:
        """セッションID生成

        Returns:
            str: セッションID
        """
        return f"msg-{uuid.uuid4().hex[:8]}"

    async def _integrate_plot_analysis(
        self,
        workspace: ManuscriptGenerationWorkspace,
        previous_results: dict[int, Any] | None
    ) -> None:
        """プロット解析結果統合（SPEC-PLOT-MANUSCRIPT-001で追加）

        STEP 1のPlotAnalyzerServiceの結果を統合し、シーンベースの原稿生成を準備。

        Args:
            workspace: 作業領域
            previous_results: 前ステップの結果
        """
        if not previous_results or 1 not in previous_results:
            if self._logger_service:
                self._logger_service.info("STEP 1 プロット解析結果なし。テンプレートベース生成を継続。")
            return

        plot_analyzer_response = previous_results[1]
        if not hasattr(plot_analyzer_response, "analysis_result") or not plot_analyzer_response.analysis_result:
            if self._logger_service:
                self._logger_service.warning("STEP 1 プロット解析結果が無効。テンプレートベース生成を継続。")
            return

        # プロット解析結果を統合
        analysis_result = plot_analyzer_response.analysis_result
        workspace.plot_analysis_result = analysis_result
        workspace.scenes = analysis_result.scenes.copy()

        if self._logger_service:
            self._logger_service.info(f"プロット解析結果統合完了: {len(workspace.scenes)}シーン")

    async def generate_from_plot_analysis(
        self,
        episode_number: int,
        plot_analysis: PlotAnalysisResult
    ) -> ManuscriptGeneratorResponse:
        """プロット解析結果から原稿生成（SPEC-PLOT-MANUSCRIPT-001で追加）

        テスト用のパブリックメソッド。プロット解析結果を直接指定して原稿生成。

        Args:
            episode_number: エピソード番号
            plot_analysis: プロット解析結果

        Returns:
            ManuscriptGeneratorResponse: 原稿生成結果
        """
        # 模擬的なprevious_resultsを作成
        mock_response = type("MockResponse", (), {
            "analysis_result": plot_analysis
        })()

        previous_results = {1: mock_response}

        return await self.execute(episode_number, previous_results)

    def convert_scene_to_content(self, scene: SceneData) -> str:
        """シーンから原稿コンテンツに変換（SPEC-PLOT-MANUSCRIPT-001で追加）

        Args:
            scene: シーンデータ

        Returns:
            str: 原稿コンテンツ
        """
        # シーンタイトル
        content = [f"\n## {scene.title}\n"]

        # 場所・時間設定
        if scene.location or scene.time_setting:
            setting_parts = []
            if scene.location:
                setting_parts.append(f"場所: {scene.location}")
            if scene.time_setting:
                setting_parts.append(f"時間: {scene.time_setting}")
            content.append(f"**設定**: {' / '.join(setting_parts)}\n")

        # 登場キャラクター
        if scene.characters:
            characters_str = "、".join(scene.characters)
            content.append(f"**登場人物**: {characters_str}\n")

        # シーン説明
        content.append(f"{scene.description}\n")

        # 発生イベント
        if scene.events:
            content.append("\n**主要イベント**:")
            for event in scene.events:
                content.append(f"- {event}")
            content.append("")

        # プレースホルダーコンテンツ（実際の小説本文）
        content.extend([
            "\n---\n",
            f"<!-- シーン{scene.scene_number}の本文をここに執筆してください -->",
            f"<!-- テーマ: {scene.title} -->",
            f"<!-- 描写すべき要素: {', '.join(scene.events)} -->",
            "\n（このシーンの詳細な本文は、AI協創執筆またはマニュアル執筆で完成させてください）\n"
        ])

        return "\n".join(content)

    async def _apply_manuscript_template(self, workspace: ManuscriptGenerationWorkspace) -> None:
        """原稿テンプレート適用（SPEC-PLOT-MANUSCRIPT-001で改修）

        プロット統合機能を考慮した原稿生成。
        シーンデータがある場合はシーンベース生成、ない場合は従来のテンプレート生成。
        """
        if not workspace.manuscript_path:
            msg = "原稿ファイルパスが設定されていません"
            raise WorkspaceInitializationError(msg)

        # シーンベース生成
        if workspace.scenes and workspace.plot_analysis_result:
            content = self._generate_scene_based_manuscript(workspace)
            workspace.generated_content = content
        else:
            # 従来のテンプレート生成
            content = self._generate_template_content(workspace)

        # ファイル書き込み
        workspace.manuscript_path.write_text(content, encoding="utf-8")

        if self._logger_service:
            generation_type = "シーンベース" if workspace.scenes else "テンプレートベース"
            self._logger_service.info(f"{generation_type}原稿生成完了: {workspace.manuscript_path}")

    def _generate_scene_based_manuscript(self, workspace: ManuscriptGenerationWorkspace) -> str:
        """シーンベース原稿生成（SPEC-PLOT-MANUSCRIPT-001で追加）

        Args:
            workspace: 作業領域

        Returns:
            str: 生成された原稿コンテンツ
        """
        content_parts = []

        # ヘッダー
        episode_title = workspace.episode_title or f"第{workspace.episode_number:03d}話"
        content_parts.append(f"# {episode_title}")
        content_parts.append("")
        content_parts.append(f"**エピソード番号**: {workspace.episode_number}")
        content_parts.append(f"**シーン数**: {len(workspace.scenes)}")

        # プロット情報
        if workspace.plot_analysis_result:
            result = workspace.plot_analysis_result
            content_parts.append(f"**主な対立**: {', '.join(result.main_conflicts)}")
            content_parts.append(f"**重要イベント**: {', '.join(result.key_events)}")

        content_parts.append("")
        content_parts.append("---")
        content_parts.append("")

        # 各シーンのコンテンツ生成
        for scene in workspace.scenes:
            scene_content = self.convert_scene_to_content(scene)
            content_parts.append(scene_content)

        # フッター
        content_parts.extend([
            "\n---\n",
            f"*生成日時: {project_now().strftime('%Y-%m-%d %H:%M:%S')}*",
            f"*シーン数: {len(workspace.scenes)}*",
            "*SPEC-PLOT-MANUSCRIPT-001準拠*"
        ])

        return "\n".join(content_parts)
