"""Application.use_cases.integrated_writing_use_case
Where: Application use case running integrated writing sessions.
What: Coordinates planning, drafting, review, and persistence for end-to-end writing flows.
Why: Allows callers to trigger integrated writing without hand-wiring the underlying services.
"""

from typing import Any


import asyncio
import re
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import yaml

if TYPE_CHECKING:
    from noveler.domain.interfaces.logger_service_protocol import ILoggerService
    from noveler.infrastructure.unit_of_work import IUnitOfWork

from noveler.application.base.abstract_use_case import AbstractUseCase
from noveler.domain.entities.integrated_writing_session import (
    IntegratedWritingSession,
    WritingWorkflowType,
)
from noveler.domain.interfaces.console_service_protocol import IConsoleService
from noveler.domain.interfaces.path_service_protocol import IPathService
from noveler.domain.value_objects.episode_number import EpisodeNumber
from noveler.domain.value_objects.yaml_prompt_content import YamlPromptContent, YamlPromptMetadata


@dataclass
class IntegratedWritingRequest:
    """統合執筆リクエスト"""

    episode_number: int
    project_root: Path
    word_count_target: str | None = None  # Noneの場合は設定から取得
    genre: str = "fantasy"
    viewpoint: str = "三人称単元視点"
    viewpoint_character: str = "主人公"
    custom_requirements: list[str] = None
    direct_claude_execution: bool = False  # Claude Code直接実行フラグ

    def __post_init__(self) -> None:
        if self.custom_requirements is None:
            self.custom_requirements = []

        # word_count_targetがNoneの場合は設定から取得
        if self.word_count_target is None:
            self.word_count_target = self._get_default_word_count()

    def _get_default_word_count(self) -> str:
        """設定から最低文字数を取得"""
        try:
            # DDD準拠: Application→Infrastructure違反を遅延初期化で回避
            # configuration_managerプロパティを使用（AbstractUseCase基底クラス）
            # DDD準拠: AbstractUseCaseのconfig_serviceを使用（Infrastructure依存排除）
            config_manager = self.config_service
            min_length = config_manager.get_default_setting("default_project", "min_length_per_episode", "4000")
            return str(min_length)
        except Exception:
            # フォールバック値
            return "4000"


@dataclass
class IntegratedWritingResponse:
    """統合執筆レスポンス"""

    success: bool
    session_id: str
    yaml_output_path: Path | None = None
    manuscript_path: Path | None = None
    execution_time_seconds: float = 0.0
    error_message: str | None = None
    fallback_executed: bool = False

    # パフォーマンス情報
    prompt_generation_time_ms: float = 0.0
    yaml_validation_time_ms: float = 0.0
    total_file_size_bytes: int = 0


class IntegratedWritingUseCase(AbstractUseCase[IntegratedWritingRequest, IntegratedWritingResponse]):
    """統合執筆ユースケース

    従来の執筆ワークフローにYAML段階的プロンプト生成を統合し、
    エラー時の適切なフォールバック機能を提供する
    """

    def __init__(self,
        logger_service: "ILoggerService" = None,
        unit_of_work: "IUnitOfWork" = None,
        console_service: Optional["IConsoleService"] = None,
        path_service: Optional["IPathService"] = None,
        yaml_prompt_repository: Any | None = None,
        episode_repository: Any | None = None,
        plot_repository: Any | None = None,
        **kwargs) -> None:
        """初期化

        Args:
            yaml_prompt_repository: YAMLプロンプトリポジトリ
            episode_repository: エピソードリポジトリ
            plot_repository: プロットリポジトリ
            console_service: コンソールサービス（DI注入）
            path_service: パスサービス（DI注入）
        """
        # 基底クラス初期化（共通サービス）
        super().__init__(console_service=console_service, path_service=path_service, **kwargs)
        # B20準拠: 標準DIサービス
        self._logger_service = logger_service
        self._unit_of_work = unit_of_work

        # TODO: B20準拠でUnit of Work経由でリポジトリアクセスに変更予定
        # 現在は暫定的に直接注入を保持
        # 互換性: 直接注入されたリポジトリを優先
        self.yaml_prompt_repository = yaml_prompt_repository  # Unit of Work経由に変更予定
        self.episode_repository = episode_repository
        self.plot_repository = plot_repository

        # DDD準拠: Infrastructure層への直接依存を回避（遅延初期化）
        self._configuration_manager = None

    async def execute(self, request: IntegratedWritingRequest) -> IntegratedWritingResponse:
        """統合執筆ワークフロー実行"""
        session_id = self._generate_session_id()

        try:
            # セッション初期化
            session = self._create_session(request, session_id)

            # Phase 1: プロンプト生成
            await self._execute_prompt_generation_phase(session, request)

            # Phase 2: 原稿テンプレート作成
            await self._execute_manuscript_creation_phase(session, request)

            # Phase 3: エディタ起動・完了
            await self._execute_completion_phase(session)

            return self._create_success_response(session)

        except Exception as e:
            # エラー時のフォールバック実行
            return await self._execute_fallback_workflow(request, session_id, str(e))

    def _generate_session_id(self) -> str:
        """セッションID生成"""
        return f"iww-{uuid.uuid4().hex[:8]}"

    def _create_session(self, request: IntegratedWritingRequest, session_id: str) -> IntegratedWritingSession:
        """セッション作成"""
        episode_number = EpisodeNumber(request.episode_number)

        return IntegratedWritingSession(
            session_id=session_id,
            episode_number=episode_number,
            project_root=request.project_root,
            workflow_type=WritingWorkflowType.INTEGRATED,
            custom_requirements=request.custom_requirements.copy(),
        )

    async def _execute_prompt_generation_phase(
        self, session: IntegratedWritingSession, request: IntegratedWritingRequest
    ) -> None:
        """プロンプト生成フェーズ実行"""

        start_time = time.perf_counter()

        # プロンプト生成開始
        session.start_prompt_generation()

        # プロット解析によるカスタム要件抽出
        plot_requirements = await self._extract_plot_requirements(request.episode_number, request.project_root)

        # カスタム要件を追加
        for req in plot_requirements:
            session.add_custom_requirement(req)

        # YAML プロンプト生成
        yaml_content = await self._generate_yaml_prompt(session, request)

        # プロンプト保存
        output_path = await self._save_yaml_prompt(session, yaml_content)

        # プロンプト生成完了
        session.complete_prompt_generation(yaml_content, output_path)

        generation_time = time.perf_counter() - start_time
        session.generation_metadata["prompt_generation_time_ms"] = str(generation_time * 1000)

    async def _execute_manuscript_creation_phase(
        self, session: IntegratedWritingSession, request: IntegratedWritingRequest
    ) -> None:
        """原稿作成フェーズ実行"""
        # 従来の原稿テンプレート作成ロジックを実行
        manuscript_path = await self._create_manuscript_template(session, request)
        session.complete_manuscript_creation(manuscript_path)

    async def _execute_completion_phase(self, session: IntegratedWritingSession) -> None:
        """完了フェーズ実行"""
        # エディタ起動（非同期）
        await self._open_editor_async(session.manuscript_path)
        session.complete_editor_opening()

        # セッション完了
        session.complete_session()

    async def _extract_plot_requirements(self, episode_number: int, project_root: Path) -> list[str]:
        """プロット解析によるカスタム要件抽出"""
        try:
            repo = getattr(self, "plot_repository", None)
            if repo is None and self._unit_of_work is not None:
                repo = getattr(self._unit_of_work, "plot_repository", None)
            if repo is None:
                return []

            res = repo.find_by_episode_number(episode_number)
            plot_data: dict[str, Any]
            if asyncio.iscoroutine(res) or hasattr(res, "__await__"):
                plot_data = await res
            else:
                plot_data = res
            if not plot_data:
                return []

            requirements = []

            # プロットから主要要素を抽出
            if hasattr(plot_data, "key_events"):
                requirements.extend(plot_data.key_events[:3])  # 最大3つ

            if hasattr(plot_data, "technical_elements"):
                requirements.extend(plot_data.technical_elements[:2])  # 最大2つ

            if hasattr(plot_data, "character_development"):
                requirements.append("キャラクター成長・関係性変化")

            return requirements

        except Exception:
            # プロット解析失敗時はデフォルト要件を返す
            return ["基本ストーリー進行", "キャラクター描写強化"]

    async def _generate_yaml_prompt(
        self, session: IntegratedWritingSession, request: IntegratedWritingRequest
    ) -> YamlPromptContent:
        """YAML プロンプト生成"""
        # メタデータ作成
        metadata = YamlPromptMetadata(
            title=f"段階的執筆プロンプト: 第{request.episode_number:03d}話.md",
            project=str(request.project_root.name),
            episode_file=f"第{request.episode_number:03d}話.md",
            genre=request.genre,
            word_count=request.word_count_target,
            viewpoint=request.viewpoint,
            viewpoint_character=request.viewpoint_character,
            detail_level="stepwise",
            methodology="A30準拠10段階構造化執筆プロセス（詳細分割方式）",
            generated_at=session.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        )

        # YAML コンテンツ生成（リポジトリが提供されている場合は例外を上位に伝播させる → フォールバック経路へ）
        if self.yaml_prompt_repository is not None:
            return await self.yaml_prompt_repository.generate_stepwise_prompt(
                metadata=metadata, custom_requirements=session.custom_requirements
            )

        # フォールバック: シンプルなYAMLを生成
        fallback_yaml = (
            "metadata:\n"
            f"  title: {metadata.title}\n"
            f"  project: {metadata.project}\n"
            f"  episode_file: {metadata.episode_file}\n"
            f"  genre: {metadata.genre}\n"
            f"  word_count: {metadata.word_count}\n"
            f"  viewpoint: {metadata.viewpoint}\n"
            f"  viewpoint_character: {metadata.viewpoint_character}\n"
            f"  detail_level: {metadata.detail_level}\n"
            f"  methodology: {metadata.methodology}\n"
            f"  generated_at: {metadata.generated_at}\n"
            "task_definition:\n  - Draft the manuscript according to A30 guidelines.\n"
        )
        return YamlPromptContent.create_from_yaml_string(
            yaml_content=fallback_yaml,
            metadata=metadata,
            custom_requirements=session.custom_requirements,
        )

    async def _save_yaml_prompt(self, session: IntegratedWritingSession, yaml_content: YamlPromptContent) -> Path:
        """YAML プロンプト保存（DI注入パスサービス使用）"""
        # パスサービス取得（DI注入による依存性解決）
        path_service = self.get_path_service(session.project_root)

        # 共通基盤を使用してプロンプト保存ディレクトリを取得
        prompts_dir = path_service.get_prompts_dir()
        prompts_dir.mkdir(parents=True, exist_ok=True)

        output_path = prompts_dir / f"第{session.episode_number.value:03d}話_プロンプト.yaml"

        try:
            if self.yaml_prompt_repository is not None:
                await self.yaml_prompt_repository.save_with_validation(
                    yaml_content=yaml_content, output_path=output_path
                )
            else:
                output_path.write_text(yaml_content.raw_yaml_content, encoding="utf-8")
        except Exception:
            # 最終フォールバック: 直接書き込み
            output_path.write_text(yaml_content.raw_yaml_content, encoding="utf-8")

        return output_path

    async def _create_manuscript_template(
        self, session: IntegratedWritingSession, request: IntegratedWritingRequest
    ) -> Path:
        """原稿テンプレート作成（正式ファイル名対応・既存ファイル処理）"""
        self.logger.debug("_create_manuscript_template called for episode %d", request.episode_number)

        # エピソードタイトルを取得
        episode_title = await self._extract_episode_title(request.episode_number, request.project_root)
        self.logger.debug("extracted title = %r", episode_title)

        # 正式なファイル名は共通基盤に委譲
        if not episode_title:
            episode_title = "無題"

        # パスサービス使用（B20: 共有基盤集約）
        path_service = self.get_path_service(request.project_root)
        manuscript_path = path_service.get_manuscript_path(request.episode_number)

        self.logger.debug("final manuscript_path = %s", manuscript_path)

        # ヘッダーもタイトル付きで生成
        header_title = f"第{request.episode_number:03d}話　{episode_title}"

        # 既存ファイル処理：段階的執筆は上書きではなく修正方式
        if manuscript_path.exists():
            self.logger.debug("File exists, checking for stepwise writing content")
            existing_content = manuscript_path.read_text(encoding="utf-8")

            # 段階的執筆プロセスのマーカーが含まれている場合は修正
            if "段階的執筆プロセス" in existing_content and "Stage" not in existing_content:
                self.logger.debug("Template-only file detected, will overwrite")
                # テンプレートのみの場合は上書き
                template_content = f"""# {header_title}

## 本文

<!-- YAML プロンプトファイル: {session.yaml_output_path} -->
<!-- 段階的執筆プロセスに従って執筆してください -->

"""
            else:
                self.logger.debug("Content exists, preserving existing content")
                # 既に内容がある場合は保持
                return manuscript_path
        else:
            # 新規ファイル作成時
            template_content = f"""# {header_title}

## 本文

<!-- YAML プロンプトファイル: {session.yaml_output_path} -->
<!-- 段階的執筆プロセスに従って執筆してください -->

"""

        manuscript_path.write_text(template_content, encoding="utf-8")
        return manuscript_path

    async def _extract_episode_title(self, episode_number: int, project_root: Path) -> str | None:
        """エピソードタイトル抽出（プロット・設定ファイルから）"""
        self.logger.debug(
            "_extract_episode_title called for episode %d, project_root = %s", episode_number, project_root
        )

        try:
            # 方法1: プロットリポジトリからタイトル取得
            self.logger.debug("Trying method 1 - plot repository")
            plot_data: dict[str, Any] = await self._unit_of_work.plot_repository.find_by_episode_number(episode_number)
            self.logger.debug("plot_data = %s, %s", type(plot_data), plot_data is not None)

            if plot_data:
                # plot_dataが辞書の場合
                if isinstance(plot_data, dict) and "title" in plot_data and plot_data["title"]:
                    title = self._sanitize_filename(plot_data["title"])
                    self.logger.debug("Method 1 success - dict title = %r", title)
                    return title
                # plot_dataがオブジェクトの場合
                if hasattr(plot_data, "title") and plot_data.title:
                    title = self._sanitize_filename(plot_data.title)
                    self.logger.debug("Method 1 success - object title = %r", title)
                    return title
                self.logger.debug("Method 1 failed - no valid title found")

            # 方法2: 話別プロットファイルから直接読み取り（プロジェクトルート基準）
            self.logger.debug("Trying method 2 - direct file reading")
            plot_file_patterns = [
                f"第{episode_number:03d}話*.yaml",
                f"第{episode_number:03d}話*.yml",
                f"episode{episode_number:03d}*.yaml",
                f"{episode_number:03d}*.yaml",
            ]

            # PROJECT_ROOT環境変数が設定されている場合の適切なプロジェクトルートを探す
            actual_project_root = project_root
            if "00_ガイド" in str(project_root):
                # 00_ガイドディレクトリの場合、実際のプロジェクトを探す
                parent_dir = project_root.parent
                if parent_dir.name == "9_小説":
                    for child in parent_dir.iterdir():
                        if child.is_dir() and "Fランク魔法使い" in child.name and "DEBUG" in child.name:
                            actual_project_root = child
                            self.logger.debug("Found actual project root = %s", actual_project_root)
                            break

            # パスサービス使用（DI注入による依存性解決）
            path_service = self.get_path_service(actual_project_root)
            plot_dir = path_service.get_plot_dir() / "話別プロット"
            self.logger.debug("plot_dir = %s, exists = %s", plot_dir, plot_dir.exists())

            if plot_dir.exists():
                # 高速化: ファイルキャッシュサービス使用でglob操作を最適化
                # ファイルキャッシュサービスは将来実装予定
                # cache_service = get_file_cache_service()

                for pattern in plot_file_patterns:
                    # 一時的にglobを直接使用（キャッシュサービス実装まで）
                    matches = list(plot_dir.glob(pattern))
                    self.logger.debug("pattern %s: %d matches", pattern, len(matches))
                    if matches:
                        # ファイル名からタイトル抽出
                        filename = matches[0].stem
                        self.logger.debug("filename = %s", filename)
                        # "第XXX話_タイトル" からタイトル部分を抽出
                        if "_" in filename:
                            title = filename.split("_", 1)[1]
                            sanitized_title = self._sanitize_filename(title)
                            self.logger.debug("Method 2 success - filename title = %r", sanitized_title)
                            return sanitized_title

                        # YAML内容からtitleフィールドを探す
                        try:
                            with matches[0].open(encoding="utf-8") as f:
                                yaml_content = yaml.safe_load(f)
                                if isinstance(yaml_content, dict) and "title" in yaml_content:
                                    title = self._sanitize_filename(yaml_content["title"])
                                    self.logger.debug("Method 2 success - yaml title = %r", title)
                                    return title
                        except Exception as yaml_e:
                            self.logger.debug("YAML parsing failed: %s", yaml_e)

            # 方法3: エピソード設定ファイルから取得（実際のプロジェクトルート基準）
            self.logger.debug("Trying method 3 - episode settings")
            episode_settings = path_service.get_settings_dir() / "エピソード設定.yaml"
            self.logger.debug("episode_settings = %s, exists = %s", episode_settings, episode_settings.exists())

            if episode_settings.exists():
                with episode_settings.open(encoding="utf-8") as f:
                    settings = yaml.safe_load(f)
                    episodes = settings.get("episodes", {})
                    episode_key = f"第{episode_number:03d}話"
                    if episode_key in episodes:
                        episode_info = episodes[episode_key]
                        if isinstance(episode_info, dict) and "title" in episode_info:
                            title = self._sanitize_filename(episode_info["title"])
                            self.logger.debug("Method 3 success - settings title = %r", title)
                            return title

            self.logger.debug("All methods failed - returning None")
            return None

        except Exception as e:
            # エラー時はNoneを返してフォールバック
            self.logger.debug("Exception occurred - %s", e)
            return None

    def _sanitize_filename(self, title: str) -> str:
        """ファイル名用文字列サニタイズ"""
        if not title:
            return ""

        # ファイル名に使用できない文字を除去・置換

        # Windows/Linux共通で使用できない文字を置換
        sanitized = re.sub(r'[<>:"/\\|?*]', "", title)
        # 連続空白を単一空白に
        sanitized = re.sub(r"\s+", " ", sanitized).strip()
        # 長すぎる場合は50文字に制限
        if len(sanitized) > 50:
            sanitized = sanitized[:50].strip()

        return sanitized

    async def _open_editor_async(self, manuscript_path: Path | None) -> None:
        """エディタ非同期起動"""
        if manuscript_path and manuscript_path.exists():
            # 非同期でエディタ起動（実装は省略）
            await asyncio.sleep(0.1)  # シンボリック待機

    async def _execute_fallback_workflow(
        self, request: IntegratedWritingRequest, session_id: str, error_message: str
    ) -> IntegratedWritingResponse:
        """フォールバックワークフロー実行"""
        # 従来ワークフローを実行
        fallback_manuscript = await self._create_simple_manuscript(request)

        return IntegratedWritingResponse(
            success=True,  # フォールバック成功
            session_id=session_id,
            manuscript_path=fallback_manuscript,
            error_message=f"統合ワークフロー失敗、従来方式で継続: {error_message}",
            fallback_executed=True,
        )

    async def _create_simple_manuscript(self, request: IntegratedWritingRequest) -> Path:
        """簡単な原稿作成（フォールバック用・正式ファイル名対応）"""
        # フォールバック時でもタイトル取得を試行
        episode_title = await self._extract_episode_title(request.episode_number, request.project_root)

        # 正式なファイル名生成（フォールバック時も同様）
        if episode_title:
            header_title = f"第{request.episode_number:03d}話　{episode_title}"
        else:
            header_title = f"第{request.episode_number:03d}話"

        # パスサービス使用（DI注入による依存性解決）
        path_service = self.get_path_service(request.project_root)
        manuscript_path = path_service.get_manuscript_path(request.episode_number)
        manuscript_path.parent.mkdir(parents=True, exist_ok=True)

        simple_template = f"""# {header_title}

## 本文

<!-- 従来テンプレート（統合ワークフロー失敗時） -->

"""

        manuscript_path.write_text(simple_template, encoding="utf-8")
        return manuscript_path

    def _create_success_response(self, session: IntegratedWritingSession) -> IntegratedWritingResponse:
        """成功レスポンス作成"""
        return IntegratedWritingResponse(
            success=True,
            session_id=session.session_id,
            yaml_output_path=session.yaml_output_path,
            manuscript_path=session.manuscript_path,
            execution_time_seconds=session.get_session_duration_seconds(),
            prompt_generation_time_ms=float(session.generation_metadata.get("prompt_generation_time_ms", "0")),
        )
