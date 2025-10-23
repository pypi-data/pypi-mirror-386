#!/usr/bin/env python3

"""Domain.services.chapter_plot_services
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

"""チャプタープロット関連ドメインサービス集

ChapterPlotWithScenesUseCaseから分離された専門ロジックを格納
"""

from typing import TYPE_CHECKING, Any

from noveler.domain.value_objects.episode_number import EpisodeNumber

if TYPE_CHECKING:
    from pathlib import Path


class ProjectValidationService:
    """プロジェクト検証専用サービス"""

    def __init__(self, project_repository) -> None:
        self.project_repository = project_repository

    def validate_project(self, project_name: str) -> dict[str, Any]:
        """プロジェクトの検証"""
        try:
            project = self.project_repository.get_project(project_name)
            if not project:
                return {"success": False, "error": f"プロジェクト '{project_name}' が見つかりません"}

            return {"success": True, "project": project}

        except Exception as e:
            return {"success": False, "error": f"プロジェクト検証エラー: {e}"}


class ChapterPlotContextService:
    """チャプタープロットコンテキスト管理サービス"""

    def __init__(self, project_repository, plot_repository, foreshadowing_repository, scene_repository) -> None:
        self.project_repository = project_repository
        self.plot_repository = plot_repository
        self.foreshadowing_repository = foreshadowing_repository
        self.scene_repository = scene_repository

    def initialize_context(self, project_name: str, episode_numbers: list[int]) -> dict[str, Any]:
        """コンテキストの初期化"""
        try:
            context = {
                "project_name": project_name,
                "episode_numbers": episode_numbers,
                "existing_plots": [],
                "existing_foreshadowings": [],
                "existing_scenes": [],
            }

            # 既存のプロットを読み込み
            for episode_num in episode_numbers:
                episode_number = EpisodeNumber(episode_num)
                try:
                    plot = self.plot_repository.get_plot(project_name, episode_number)
                    if plot:
                        context["existing_plots"].append(plot)
                except Exception:
                    # プロットが見つからない場合はスキップ
                    pass

            return {"success": True, "context": context}

        except Exception as e:
            return {"success": False, "error": f"コンテキスト初期化エラー: {e}"}


class ChapterPlotCreationService:
    """チャプタープロット作成専用サービス"""

    def __init__(self, plot_orchestrator) -> None:
        self.plot_orchestrator = plot_orchestrator

    def create_chapter_plot(self, project_name: str, episode_numbers: list[int], context: dict) -> dict[str, Any]:
        """チャプタープロットの作成"""
        try:
            # プロットオーケストレーターを使用してプロット生成
            plot_request = {"project_name": project_name, "episode_numbers": episode_numbers, "context": context}

            response = self.plot_orchestrator.generate_chapter_plot(plot_request)

            if not response.success:
                return {"success": False, "error": f"チャプタープロット作成失敗: {response.error}"}

            return {"success": True, "plot_content": response.plot_content, "metadata": response.metadata}

        except Exception as e:
            return {"success": False, "error": f"チャプタープロット作成エラー: {e}"}


class PlotFileExtractionService:
    """プロットファイル抽出専用サービス"""

    def extract_plot_file(self, plot_content: str, output_path: Path) -> dict[str, Any]:
        """プロットファイルの抽出と保存"""
        try:
            # プロット内容をファイルに保存
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with output_path.open("w", encoding="utf-8") as f:  # TODO: IPathServiceを使用するように修正
                f.write(plot_content)

            return {"success": True, "file_path": output_path, "content_length": len(plot_content)}

        except Exception as e:
            return {"success": False, "error": f"プロットファイル抽出エラー: {e}"}


class ForeshadowingExtractionService:
    """伏線抽出専用サービス"""

    def __init__(self, foreshadowing_extractor, foreshadowing_repository) -> None:
        self.foreshadowing_extractor = foreshadowing_extractor
        self.foreshadowing_repository = foreshadowing_repository

    def extract_foreshadowing(self, plot_content: str, project_name: str, episode_numbers: list[int]) -> dict[str, Any]:
        """伏線の抽出"""
        try:
            # 伏線抽出器を使用
            extract_request = {
                "plot_content": plot_content,
                "project_name": project_name,
                "episode_numbers": episode_numbers,
            }

            response = self.foreshadowing_extractor.extract(extract_request)

            if not response.success:
                return {"success": False, "error": f"伏線抽出失敗: {response.error}"}

            # 抽出された伏線を処理
            processed_foreshadowings = self._process_foreshadowing_response(response)

            return {"success": True, "foreshadowings": processed_foreshadowings, "count": len(processed_foreshadowings)}

        except Exception as e:
            return {"success": False, "error": f"伏線抽出エラー: {e}"}

    def _process_foreshadowing_response(self, response) -> list[dict]:
        """伏線レスポンスの処理"""
        processed = []

        for foreshadowing_data in response.foreshadowings:
            processed_item = {
                "id": foreshadowing_data.get("id"),
                "type": foreshadowing_data.get("type", "unknown"),
                "content": foreshadowing_data.get("content", ""),
                "target_episode": foreshadowing_data.get("target_episode"),
                "importance": foreshadowing_data.get("importance", "medium"),
                "resolution_hint": foreshadowing_data.get("resolution_hint", ""),
            }
            processed.append(processed_item)

        return processed


class SceneExtractionService:
    """シーン抽出専用サービス"""

    def __init__(self, scene_extractor, scene_repository) -> None:
        self.scene_extractor = scene_extractor
        self.scene_repository = scene_repository

    def extract_scenes(self, plot_content: str, project_name: str, episode_numbers: list[int]) -> dict[str, Any]:
        """シーンの抽出"""
        try:
            # シーン抽出器を使用
            extract_request = {
                "plot_content": plot_content,
                "project_name": project_name,
                "episode_numbers": episode_numbers,
            }

            response = self.scene_extractor.extract(extract_request)

            if not response.success:
                return {"success": False, "error": f"シーン抽出失敗: {response.error}"}

            # 抽出されたシーンを処理
            processed_scenes = self._process_scene_response(response)

            return {"success": True, "scenes": processed_scenes, "count": len(processed_scenes)}

        except Exception as e:
            return {"success": False, "error": f"シーン抽出エラー: {e}"}

    def _process_scene_response(self, response) -> list[dict]:
        """シーンレスポンスの処理"""
        processed = []

        for scene_data in response.scenes:
            processed_item = {
                "id": scene_data.get("id"),
                "title": scene_data.get("title", "無題シーン"),
                "description": scene_data.get("description", ""),
                "episode_number": scene_data.get("episode_number"),
                "scene_order": scene_data.get("scene_order", 1),
                "location": scene_data.get("location", ""),
                "characters": scene_data.get("characters", []),
                "mood": scene_data.get("mood", "neutral"),
                "purpose": scene_data.get("purpose", ""),
                "duration": scene_data.get("duration", "unknown"),
            }
            processed.append(processed_item)

        return processed


class ChapterPlotResponseBuilderService:
    """チャプタープロットレスポンス構築専用サービス"""

    def build_success_response(
        self, plot_result: dict, foreshadowing_result: dict, scene_result: dict, metadata: dict
    ) -> dict[str, Any]:
        """成功レスポンスの構築"""
        try:
            return {
                "success": True,
                "plot": {
                    "content": plot_result.get("plot_content", ""),
                    "file_path": str(plot_result.get("file_path", "")),
                    "metadata": plot_result.get("metadata", {}),
                },
                "foreshadowing": {
                    "items": foreshadowing_result.get("foreshadowings", []),
                    "count": foreshadowing_result.get("count", 0),
                },
                "scenes": {"items": scene_result.get("scenes", []), "count": scene_result.get("count", 0)},
                "summary": {
                    "total_episodes": len(metadata.get("episode_numbers", [])),
                    "plot_generated": plot_result.get("success", False),
                    "foreshadowing_extracted": foreshadowing_result.get("success", False),
                    "scenes_extracted": scene_result.get("success", False),
                    "created_at": metadata.get("created_at"),
                    "processing_time": metadata.get("processing_time", 0),
                },
            }

        except Exception as e:
            return {"success": False, "error": f"レスポンス構築エラー: {e}"}

    def build_error_response(self, error_message: str, context: dict | None = None) -> dict[str, Any]:
        """エラーレスポンスの構築"""
        response_data: dict[str, Any] = {
            "success": False,
            "error": error_message,
            "plot": {"content": "", "file_path": "", "metadata": {}},
            "foreshadowing": {"items": [], "count": 0},
            "scenes": {"items": [], "count": 0},
            "summary": {
                "total_episodes": 0,
                "plot_generated": False,
                "foreshadowing_extracted": False,
                "scenes_extracted": False,
                "created_at": None,
                "processing_time": 0,
            },
        }

        if context:
            response_data["context"] = context

        return response_data
