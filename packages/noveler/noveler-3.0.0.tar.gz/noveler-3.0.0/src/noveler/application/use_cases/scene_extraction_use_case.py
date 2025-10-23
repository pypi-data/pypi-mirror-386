"""Application.use_cases.scene_extraction_use_case
Where: Application use case responsible for extracting important scenes.
What: Analyzes structure and foreshadowing to update the important scenes registry.
Why: Keeps scene highlights synchronized without manual curation steps.
"""


import traceback
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

from noveler.domain.repositories.foreshadowing_repository import ForeshadowingRepository
from noveler.domain.repositories.plot_repository import PlotRepository
from noveler.domain.repositories.scene_repository import SceneRepository
from noveler.domain.services.scene_extractor import ExtractedScene, SceneExtractor
from noveler.infrastructure.adapters.path_service_adapter import create_path_service
from noveler.infrastructure.logging.unified_logger import get_logger


class SceneExtractionStatus(Enum):
    """シーン抽出のステータス"""

    SUCCESS = "success"
    PROJECT_NOT_FOUND = "project_not_found"
    MASTER_PLOT_NOT_FOUND = "master_plot_not_found"
    CHAPTER_PLOT_NOT_FOUND = "chapter_plot_not_found"
    SCENE_FILE_NOT_FOUND = "scene_file_not_found"
    ERROR = "error"


@dataclass
class SceneExtractionRequest:
    """シーン抽出リクエスト"""

    project_name: str
    use_master_plot: bool = True
    use_foreshadowing: bool = True
    use_chapter_plots: bool = False  # 章別プロットからシーン抽出
    merge_existing: bool = True
    auto_categorize: bool = True
    detailed_mode: bool = False  # 細かなシーンモード(章別プロット用)


@dataclass
class SceneExtractionResponse:
    """シーン抽出レスポンス"""

    status: SceneExtractionStatus
    message: str
    extracted_count: int = 0
    existing_count: int = 0
    scene_file: Path | None = None
    scene_summary: str = ""


class SceneExtractionUseCase:
    """重要シーン抽出ユースケース"""

    def __init__(
        self,
        plot_repository: PlotRepository,
        foreshadowing_repository: ForeshadowingRepository,
        scene_repository: SceneRepository,
        scene_extractor: SceneExtractor,
        project_repository = None,
    ) -> None:
        self.project_repository = project_repository
        self.plot_repository = plot_repository
        self.foreshadowing_repository = foreshadowing_repository
        self.scene_repository = scene_repository
        self.scene_extractor = scene_extractor

    def execute(self, request: SceneExtractionRequest) -> SceneExtractionResponse:
        """
        重要シーン抽出を実行する

        Args:
            request: シーン抽出リクエスト

        Returns:
            シーン抽出レスポンス
        """
        try:
            # プロジェクトの存在確認
            if not self.project_repository.exists(request.project_name):
                return SceneExtractionResponse(
                    status=SceneExtractionStatus.PROJECT_NOT_FOUND,
                    message=f"プロジェクト '{request.project_name}' が見つかりません",
                )

            project_root = self.project_repository.get_project_root(request.project_name)

            path_service = create_path_service(project_root)
            scene_file = path_service.get_scene_file(1)  # デフォルトエピソードの汎用シーンファイル

            # 細かなシーンモード(章別プロット基準)
            if request.detailed_mode or request.use_chapter_plots:
                return self._extract_detailed_scenes(request, project_root, scene_file)

            # 主要シーンモード(全体構成基準)
            return self._extract_major_scenes(request, project_root, scene_file)

        except (FileNotFoundError, OSError, ValueError) as e:
            return SceneExtractionResponse(
                status=SceneExtractionStatus.ERROR, message=f"シーン抽出中にエラーが発生しました: {e}"
            )

    def _extract_major_scenes(
        self, request: SceneExtractionRequest, project_root: Path, scene_file: Path
    ) -> SceneExtractionResponse:
        """主要シーンを抽出(全体構成基準)"""
        # 抽出されたシーンを格納
        all_extracted_scenes: list[ExtractedScene] = []

        # 全体構成からシーンを抽出
        if request.use_master_plot:
            try:
                master_plot_data: dict[str, Any] = self.plot_repository.load_master_plot(project_root)
                master_scenes = self.scene_extractor.extract_from_master_plot(master_plot_data)
                all_extracted_scenes.extend(master_scenes)
            except FileNotFoundError:
                return SceneExtractionResponse(
                    status=SceneExtractionStatus.MASTER_PLOT_NOT_FOUND,
                    message="全体構成.yamlが見つかりません。先に 'novel plot master' を実行してください。",
                )

        # 伏線情報からシーンを抽出
        if request.use_foreshadowing and self.foreshadowing_repository.exists(project_root):
            foreshadowings = self.foreshadowing_repository.load_all(project_root)
            foreshadowing_scenes = self.scene_extractor.extract_from_foreshadowing(foreshadowings)
            all_extracted_scenes.extend(foreshadowing_scenes)

        # シーンをマージして重複を除去
        merged_scenes = self.scene_extractor.merge_and_deduplicate(all_extracted_scenes)

        # 既存のシーンと統合
        existing_count = 0
        if request.merge_existing and scene_file.exists():
            existing_data: dict[str, Any] = self.scene_repository.load_scenes(project_root)
            existing_count = len(self._count_existing_scenes(existing_data))

        # シーンファイルを更新
        self._update_scene_file(project_root, merged_scenes, request.merge_existing)

        # サマリー作成
        summary = self._create_summary(merged_scenes)

        return SceneExtractionResponse(
            status=SceneExtractionStatus.SUCCESS,
            message=f"重要シーンを抽出しました(新規: {len(merged_scenes)}件)",
            extracted_count=len(merged_scenes),
            existing_count=existing_count,
            scene_file=scene_file,
            scene_summary=summary,
        )

    def _extract_detailed_scenes(
        self, request: SceneExtractionRequest, project_root: Path, scene_file: Path
    ) -> SceneExtractionResponse:
        """章別プロットから細かなシーンを抽出して既存ファイルに追加(リファクタリング済み:複雑度12→5に削減)"""
        # シーンファイルの初期化
        self._ensure_scene_file_exists(scene_file, project_root)

        # 章別プロットファイルの検証
        chapter_plot_files = self._validate_chapter_plot_files(project_root)
        if isinstance(chapter_plot_files, SceneExtractionResponse):
            return chapter_plot_files

        # シーン抽出処理
        detailed_scenes = self._extract_scenes_from_chapters_and_foreshadowing(
            request, project_root, chapter_plot_files
        )

        if not detailed_scenes:
            return SceneExtractionResponse(
                status=SceneExtractionStatus.SUCCESS,
                message="章別プロットから細かなシーンは見つかりませんでした",
                extracted_count=0,
                scene_file=scene_file,
            )

        # シーンのマージと更新
        return self._merge_and_update_scenes(project_root, scene_file, detailed_scenes)

    def _ensure_scene_file_exists(self, scene_file: Path, project_root: Path) -> None:
        """シーンファイルの存在を確保"""
        if not scene_file.exists():
            self.scene_repository.initialize_scene_file(project_root)

    def _validate_chapter_plot_files(self, project_root: Path) -> list[Path] | SceneExtractionResponse:
        """章別プロットファイルの検証"""
        try:
            chapter_plot_files = self.plot_repository.get_chapter_plot_files(project_root)
            if not chapter_plot_files:
                return SceneExtractionResponse(
                    status=SceneExtractionStatus.CHAPTER_PLOT_NOT_FOUND,
                    message="章別プロットが見つかりません。先に 'novel plot chapter N' を実行してください。",
                )

            return chapter_plot_files
        except (FileNotFoundError, OSError):
            return SceneExtractionResponse(
                status=SceneExtractionStatus.CHAPTER_PLOT_NOT_FOUND,
                message="章別プロットが見つかりません。先に 'novel plot chapter N' を実行してください。",
            )

    def _extract_scenes_from_chapters_and_foreshadowing(
        self, request: SceneExtractionRequest, project_root: Path, chapter_plot_files: list[Path]
    ) -> list[ExtractedScene]:
        """章別プロットと伏線からシーンを抽出"""
        detailed_scenes = []

        # 章別プロットからシーン抽出
        chapter_scenes = self._extract_scenes_from_chapter_files(chapter_plot_files)
        detailed_scenes.extend(chapter_scenes)

        # 伏線からシーン抽出(オプション)
        if request.use_foreshadowing and self.foreshadowing_repository.exists(project_root):
            foreshadowing_scenes = self._extract_scenes_from_foreshadowing(chapter_plot_files, project_root)
            detailed_scenes.extend(foreshadowing_scenes)

        return detailed_scenes

    def _extract_scenes_from_chapter_files(self, chapter_plot_files: list[Path]) -> list[ExtractedScene]:
        """章別プロットファイルからシーンを抽出"""
        detailed_scenes = []
        failed_files = []

        for chapter_file in chapter_plot_files:
            result = self._process_chapter_file_safely(chapter_file)
            if result["success"]:
                detailed_scenes.extend(result["scenes"])
            else:
                failed_files.append((chapter_file, result["error"]))

        # B20準拠: エラーログ出力をlogger_service経由で実行
        if failed_files:
            for file_path, error_msg in failed_files:
                # logger_serviceが利用可能な場合は使用、そうでなければ統一ロガーを使用
                if hasattr(self, "_logger_service") and self._logger_service:
                    self._logger_service.error(f"章別プロット読み込みエラー: {file_path}, エラー: {error_msg}")
                else:
                    # フォールバック: 統一ロガー使用
                    logger = get_logger(__name__)
                    logger.error(f"章別プロット読み込みエラー: {file_path}, エラー: {error_msg}")
                traceback.print_exc()

        return detailed_scenes

    def _process_chapter_file_safely(self, chapter_file: Path) -> dict:
        """章別プロットファイルを安全に処理"""
        try:
            chapter_data: dict[str, Any] = self.plot_repository.load_chapter_plot(chapter_file)
            if chapter_data:
                chapter_scenes = self.scene_extractor.extract_from_chapter_plot(chapter_data)
                return {"success": True, "scenes": chapter_scenes}
            return {"success": True, "scenes": []}
        except (FileNotFoundError, OSError, ValueError) as e:
            return {"success": False, "error": str(e)}

    def _extract_scenes_from_foreshadowing(
        self, chapter_plot_files: list[Path], project_root: Path
    ) -> list[ExtractedScene]:
        """伏線からシーンを抽出"""
        try:
            foreshadowings = self.foreshadowing_repository.load_all(project_root)
            try:
                # 高度な抽出方法を試行
                return self.scene_extractor.extract_scenes_from_chapter_and_foreshadowing(
                    chapter_plot_files, foreshadowings
                )

            except AttributeError:
                # フォールバック:基本的な抽出方法
                return self.scene_extractor.extract_from_foreshadowing(foreshadowings)
        except Exception:
            return []

    def _merge_and_update_scenes(
        self, project_root: Path, scene_file: Path, detailed_scenes: list[ExtractedScene]
    ) -> SceneExtractionResponse:
        """シーンのマージと更新"""
        # 重複除去と既存データ統合
        merged_detailed_scenes = self.scene_extractor.merge_and_deduplicate(detailed_scenes)
        existing_data: dict[str, Any] = self.scene_repository.load_scenes(project_root)
        existing_count = len(self._count_existing_scenes(existing_data))

        # ファイル更新とサマリー作成
        self._update_scene_file(project_root, merged_detailed_scenes, merge=True)
        detailed_summary = self._create_detailed_summary(merged_detailed_scenes)

        return SceneExtractionResponse(
            status=SceneExtractionStatus.SUCCESS,
            message=f"細かなシーンを追加しました(新規: {len(merged_detailed_scenes)}件)",
            extracted_count=len(merged_detailed_scenes),
            existing_count=existing_count,
            scene_file=scene_file,
            scene_summary=detailed_summary,
        )

    def _update_scene_file(self, project_root: Path, scenes: list[ExtractedScene], merge: bool = False) -> None:
        """重要シーンファイルを更新"""

        path_service = create_path_service(project_root)
        scene_file = path_service.get_scene_file(1)  # デフォルトエピソードの汎用シーンファイル

        if not scene_file.exists():
            # 新規作成
            self.scene_repository.initialize_scene_file(project_root)

        # 既存データを読み込む(repositoryはリストを返すが、ファイル構造全体が必要)

        path_service = create_path_service(project_root)
        scene_file = path_service.get_scene_file(1)  # デフォルトエピソードの汎用シーンファイル
        if scene_file.exists():
            with scene_file.open(encoding="utf-8") as f:
                scene_data: dict[str, Any] = yaml.safe_load(f) or {}
        else:
            scene_data: dict[str, Any] = {"metadata": {}, "scenes": {}}

        # データが辞書でない場合の安全チェック
        if not isinstance(scene_data, dict):
            scene_data: dict[str, Any] = {"metadata": {}, "scenes": {}}

        if "scenes" not in scene_data:
            scene_data["scenes"] = {}

        if not merge:
            # 既存のシーンをクリア
            scene_data["scenes"] = {}

        # 抽出したシーンを追加
        for scene in scenes:
            category_key = self._get_category_key(scene.category.value)
            if category_key not in scene_data["scenes"]:
                scene_data["scenes"][category_key] = {}

            scene_dict = scene.to_dict()
            # YAMLフォーマットに合わせて調整
            scene_data["scenes"][category_key][scene.scene_id] = {
                "title": scene_dict["title"],
                "description": scene_dict["description"],
                "importance": scene_dict["importance"],
                "episodes": scene_dict["episodes"],
                "completion_status": "未着手",
                "sensory_details": {"visual": "", "auditory": "", "tactile": "", "olfactory": "", "gustatory": ""},
                "emotional_arc": "",
                "key_dialogues": [],
                "notes": f"自動抽出元: {scene_dict['source']}",
            }

        # ファイルに直接保存(repositoryの不整合を回避)
        with scene_file.open("w", encoding="utf-8") as f:
            yaml.dump(scene_data, f, allow_unicode=True, default_flow_style=False)

    def _get_category_key(self, category_value: str) -> str:
        """カテゴリ値からYAMLキーを取得"""
        category_map = {
            "opening": "opening",
            "development": "development",
            "turning_point": "turning_points",
            "climax_scenes": "climax_scenes",
            "emotional_scenes": "emotional_scenes",
            "action_scenes": "action_scenes",
            "ending": "ending",
            "foreshadowing": "emotional_scenes",  # 伏線シーンは感情的シーンに分類
        }
        return category_map.get(category_value, "development")

    def _count_existing_scenes(self, scene_data: dict[str, Any]) -> list[str]:
        """既存のシーンIDをカウント"""
        scene_ids = []
        if isinstance(scene_data, dict) and "scenes" in scene_data:
            scenes = scene_data["scenes"]
            if isinstance(scenes, dict):
                for category in scenes.values():
                    if isinstance(category, dict):
                        scene_ids.extend(category.keys())
        return scene_ids

    def _create_summary(self, scenes: list[ExtractedScene]) -> str:
        """抽出されたシーンのサマリーを作成"""
        if not scenes:
            return "シーンが見つかりませんでした"

        lines = ["抽出された重要シーン:"]

        # 章ごとにグループ化
        by_chapter: dict[int, list[ExtractedScene]] = {}
        for scene in scenes:
            if scene.chapter not in by_chapter:
                by_chapter[scene.chapter] = []
            by_chapter[scene.chapter].append(scene)

        # 章ごとに表示
        for chapter in sorted(by_chapter.keys()):
            lines.append(f"\n【第{chapter}章】")
            for scene in by_chapter[chapter]:
                ep_str = f"第{scene.episode_range[0]:03d}話"
                if scene.episode_range[0] != scene.episode_range[1]:
                    ep_str += f"〜第{scene.episode_range[1]:03d}話"
                lines.append(f"  {scene.scene_id})")
                lines.append(f"    カテゴリ: {scene.category.value}, 重要度: {scene.importance}")

        return "\n".join(lines)

    def _create_detailed_summary(self, scenes: list[ExtractedScene]) -> str:
        """細かなシーンのサマリーを作成"""
        if not scenes:
            return "細かなシーンが見つかりませんでした"

        lines = ["追加された細かなシーン:"]
        for scene in scenes:
            ep_str = f"第{scene.episode_range[0]:03d}話"
            if scene.episode_range[0] != scene.episode_range[1]:
                ep_str += f"〜第{scene.episode_range[1]:03d}話"
            lines.append(f"- {scene.scene_id})")
            lines.append(f"  カテゴリ: {scene.category.value}, 重要度: {scene.importance}")

        return "\n".join(lines)
