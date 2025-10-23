"""Infrastructure.persistence.plot_viewpoint_repository
Where: Infrastructure repository persisting plot viewpoint data.
What: Implements storage and retrieval of viewpoint notes and metadata.
Why: Supports viewpoint-aware analysis with persistent data stores.
"""

from noveler.presentation.shared.shared_utilities import console

"プロット視点情報リポジトリ\n\n責務:\n    - プロットファイル(YAML)から視点情報を読み取り\n- ViewpointInfoエンティティへの変換\n- エピソード番号による視点情報検索\n"
import re
import shutil
from pathlib import Path
from typing import Any

import yaml

from noveler.domain.exceptions.viewpoint_exceptions import (
    ViewpointDataInvalidError,
    ViewpointFileNotFoundError,
    ViewpointRepositoryError,
    ViewpointYAMLParseError,
)
from noveler.domain.quality.viewpoint_entities import ComplexityLevel, ViewpointInfo, ViewpointType
from noveler.domain.value_objects.project_time import project_now
from noveler.infrastructure.factories.path_service_factory import create_path_service
from noveler.infrastructure.logging.unified_logger import get_logger


class PlotViewpointRepository:
    """プロット視点情報リポジトリ"""

    def __init__(self, project_path: Path, enable_backup: bool) -> None:
        """Args:
        project_path: プロジェクトルートパス
        enable_backup: バックアップ機能を有効にするか
        """
        self.project_path = Path(project_path)
        # B20準拠: パス管理はPathServiceを使用
        path_service = create_path_service()
        self.plot_dir = path_service.get_plots_dir() / "章別プロット"
        self.enable_backup = enable_backup
        self.logger = get_logger(__name__)
        if not self.project_path.exists():
            raise ViewpointFileNotFoundError(str(self.project_path), project_name=self.project_path.name)

    def get_episode_viewpoint_info(self, episode_number: str) -> ViewpointInfo | None:
        """エピソード番号から視点情報を取得

        Args:
            episode_number: エピソード番号(例: "episode001", "episode010")

        Returns:
            ViewpointInfo または None(見つからない場合)

        Raises:
            ViewpointDataInvalidError: エピソード番号が不正な形式の場合
            ViewpointRepositoryError: リポジトリ操作エラー
        """
        console.print(f"Getting viewpoint info for episode: {episode_number}")
        try:
            # 新形式 "episode001" から数値を抽出
            if episode_number.startswith("episode"):
                episode_num = int(episode_number.replace("episode", ""))
            else:
                # 旧形式との互換性を保持
                episode_num = int(episode_number)
            
            if episode_num <= 0:
                msg = "Episode number must be positive"
                raise ValueError(msg)
        except ValueError as e:
            raise ViewpointDataInvalidError(
                field_name="episode_number", expected_type="正の整数または数値文字列", actual_value=episode_number
            ) from e
        try:
            plot_data: dict[str, Any] = self._find_episode_in_plot_files(episode_number)
            if plot_data is None:
                console.print(f"No plot data found for episode {episode_number}")
                return None
            (episode_data, chapter_data) = plot_data
            return self._convert_to_viewpoint_info(episode_data, chapter_data)
        except Exception as e:
            console.print(f"Error getting viewpoint info: {e!s}")
            raise ViewpointRepositoryError(
                operation="get_episode_viewpoint_info", reason=str(e), episode_number=episode_number
            ) from e

    def _find_episode_in_plot_files(self, episode_number: str) -> tuple[dict[str, Any], dict[str, Any]] | None:
        """複数の章プロットファイルからエピソードを検索

        Returns:
            (episode_data, chapter_data) のタプル または None
        """
        if not self.plot_dir.exists():
            console.print(f"Plot directory does not exist: {self.plot_dir}")
            return None
        
        # 新しいフォーマットを優先: chapter01.yaml
        plot_files = list(self.plot_dir.glob("chapter*.yaml")) + list(self.plot_dir.glob("ch*.yaml")) + list(self.plot_dir.glob("第*章.yaml"))
        
        if not plot_files:
            console.print(f"No chapter plot files found in: {self.plot_dir}")
            return None
        console.print(f"Searching through {len(plot_files)} plot files")
        for plot_file in plot_files:
            try:
                console.print(f"Checking plot file: {plot_file.name}")
                if self.enable_backup:
                    self._create_backup(plot_file)
                with plot_file.open("r", encoding="utf-8") as f:
                    plot_data: dict[str, Any] = yaml.safe_load(f)
                if not plot_data:
                    console.print(f"Empty plot data in {plot_file.name}")
                    continue
                if "episode_breakdown" not in plot_data:
                    console.print(f"No episode_breakdown in {plot_file.name}")
                    continue
                episode_breakdown = plot_data["episode_breakdown"]
                if not isinstance(episode_breakdown, dict):
                    raise ViewpointDataInvalidError(
                        field_name="episode_breakdown",
                        expected_type="dict",
                        actual_value=episode_breakdown,
                        file_path=str(plot_file),
                    )
                
                # 数値を抽出
                if episode_number.startswith("episode"):
                    episode_num = int(episode_number.replace("episode", ""))
                else:
                    episode_num = int(episode_number)
                
                # 複数のキー形式をサポート（新形式を優先）
                ep_keys_to_try = [
                    f"episode{episode_num:03d}",        # "episode001", "episode010" 形式（新形式）
                    episode_number,                     # 渡された形式そのまま
                    f"{episode_num:03d}",              # "001", "010" 形式
                    f"ep{episode_num}",                # "ep1", "ep10" 形式（旧形式）
                    str(episode_num),                  # "1", "10" 形式
                    episode_num,                       # 1, 10 形式
                ]
                
                for ep_key in ep_keys_to_try:
                    if ep_key in episode_breakdown:
                        console.print(f"Found episode {episode_number} as {ep_key} in {plot_file.name}")
                        episode_data: dict[str, Any] = episode_breakdown[ep_key]
                        chapter_data: dict[str, Any] = plot_data.get("chapter_info", {})
                        return (episode_data, chapter_data)
                        
            except yaml.YAMLError as e:
                line_number = getattr(e, "problem_mark", None)
                if line_number:
                    raise ViewpointYAMLParseError(
                        file_path=str(plot_file),
                        line_number=line_number.line + 1,
                        column_number=line_number.column + 1,
                        original_error=str(e),
                    ) from e
                raise ViewpointYAMLParseError(file_path=str(plot_file), original_error=str(e)) from e
            except UnicodeDecodeError as e:
                self.logger.exception("Encoding error in %s", plot_file.name)
                raise ViewpointRepositoryError(
                    operation="read_plot_file",
                    reason=f"ファイルのエンコーディングエラー: {e!s}",
                    file_path=str(plot_file),
                ) from e
            except OSError as e:
                self.logger.exception("OS error reading %s", plot_file.name)
                raise ViewpointRepositoryError(
                    operation="read_plot_file", reason=f"ファイル読み込みエラー: {e!s}", file_path=str(plot_file)
                ) from e
        return None

    def _convert_to_viewpoint_info(self, episode_data: dict[str, Any], chapter_data: dict[str, Any]) -> ViewpointInfo:
        """プロットデータをViewpointInfoエンティティに変換

        Raises:
            ViewpointDataInvalidError: データ形式が不正な場合
        """
        try:
            if not isinstance(episode_data, dict):
                raise ViewpointDataInvalidError(
                    field_name="episode_data", expected_type="dict", actual_value=episode_data
                )
            if not isinstance(chapter_data, dict):
                raise ViewpointDataInvalidError(
                    field_name="chapter_data", expected_type="dict", actual_value=chapter_data
                )
            viewpoint_details = episode_data.get("viewpoint_details", {})
            viewpoint_label = episode_data.get("viewpoint_label", "")
            viewpoint_description = episode_data.get("viewpoint", "")
            chapter_viewpoint = chapter_data.get("viewpoint", "")
            chapter_viewpoint_mgmt = chapter_data.get("viewpoint_management", {})
            if "body_swap_details" in viewpoint_details or "→" in viewpoint_label:
                character = viewpoint_label if viewpoint_label else viewpoint_details.get("consciousness", "unknown")
            else:
                character = viewpoint_details.get("consciousness", viewpoint_label)
            if not character:
                character = chapter_viewpoint_mgmt.get("primary_pov_character", chapter_viewpoint)
            if not character:
                character = self._extract_character_from_description(viewpoint_description or chapter_viewpoint)
            viewpoint_type = self._determine_viewpoint_type(viewpoint_label, viewpoint_description, viewpoint_details)
            viewpoint_management = chapter_data.get("viewpoint_management", {})
            complexity_str = viewpoint_management.get("complexity_level", "中")
            complexity_level = self._parse_complexity_level(complexity_str)
            special_conditions = []
            if "body_swap_details" in viewpoint_details:
                special_conditions.append("body_swap")
            if "memory_share_details" in viewpoint_details:
                special_conditions.append("memory_share")
            chapter_conditions = viewpoint_management.get("special_conditions", [])
            special_conditions.extend(chapter_conditions)
            narrative_focus = viewpoint_details.get("narrative_focus", "general")
            return ViewpointInfo(
                character=character,
                viewpoint_type=viewpoint_type,
                complexity_level=complexity_level,
                special_conditions=special_conditions,
                narrative_focus=narrative_focus,
            )
        except Exception as e:
            self.logger.exception("Error converting to ViewpointInfo")
            raise ViewpointRepositoryError(
                operation="convert_to_viewpoint_info", reason=f"ViewpointInfo変換エラー: {e}"
            ) from e

    def _determine_viewpoint_type(
        self, viewpoint_label: str, viewpoint_description: str, viewpoint_details: dict[str, Any] | None = None
    ) -> ViewpointType:
        """視点タイプを判定"""
        if "→" in viewpoint_label and "Body" in viewpoint_label:
            return ViewpointType.BODY_SWAP
        if "body_swap_details" in viewpoint_description:
            return ViewpointType.BODY_SWAP
        if "&" in viewpoint_label or "&" in viewpoint_label:
            return ViewpointType.MULTIPLE_PERSPECTIVE
        if "切り替え" in viewpoint_label:
            return ViewpointType.MULTIPLE_PERSPECTIVE
        if any(
            keyword in viewpoint_description for keyword in ["inner_thoughts", "introspection", "internal_monologue"]
        ):
            return ViewpointType.SINGLE_INTROSPECTIVE
        introspective_keywords = ["内省", "内面", "思考", "独白", "心理"]
        interactive_keywords = ["会話", "交流", "対話", "コミュニケーション"]
        description_lower = viewpoint_description.lower()
        if any(keyword in description_lower for keyword in introspective_keywords):
            return ViewpointType.SINGLE_INTROSPECTIVE
        if any(keyword in description_lower for keyword in interactive_keywords):
            return ViewpointType.SINGLE_INTERACTIVE
        return ViewpointType.SINGLE_INTERACTIVE

    def _parse_complexity_level(self, complexity_str: str) -> ComplexityLevel:
        """複雑度文字列をEnum値に変換"""
        complexity_map = {
            "低": ComplexityLevel.LOW,
            "中": ComplexityLevel.MEDIUM,
            "高": ComplexityLevel.HIGH,
            "low": ComplexityLevel.LOW,
            "medium": ComplexityLevel.MEDIUM,
            "high": ComplexityLevel.HIGH,
        }
        return complexity_map.get(complexity_str, ComplexityLevel.MEDIUM)

    def _extract_character_from_description(self, description: str) -> str:
        """説明文からキャラクター名を抽出"""
        if not description:
            return "unknown"
        body_swap_match = re.search("(\\w+)→(\\w+)Body", description)
        if body_swap_match:
            return f"{body_swap_match.group(1)}→{body_swap_match.group(2)}Body"
        multi_match = re.search("(\\w+)[&&](\\w+)", description)
        if multi_match:
            return f"{multi_match.group(1)}&{multi_match.group(2)}"
        char_match = re.search("([ァ-ヾ一-龯\\w]+)", description)
        if char_match:
            return char_match.group(1)
        return "unknown"

    def _create_backup(self, file_path: Path) -> None:
        """ファイルのバックアップを作成

        Args:
            file_path: バックアップ対象のファイルパス
        """
        if not file_path.exists():
            return
        backup_dir = file_path.parent / "backup"
        backup_dir.mkdir(exist_ok=True)
        timestamp = project_now().format_timestamp()
        backup_path = backup_dir / f"{file_path.stem}_{timestamp}{file_path.suffix}"
        try:
            shutil.copy2(file_path, backup_path)
            console.print(f"Created backup: {backup_path}")
        except (OSError, shutil.Error) as e:
            console.print(f"Failed to create backup: {e}")
