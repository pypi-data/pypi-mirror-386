"""Domain.services.writing_steps.plot_analyzer_service
Where: Domain service module implementing a specific writing workflow step.
What: Provides helper routines and data structures for this writing step.
Why: Allows stepwise writing orchestrators to reuse consistent step logic.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""STEP 1: PlotAnalyzerService

A38執筆プロンプトガイドのSTEP 1に対応するマイクロサービス。
プロット解析・要素抽出・構造分析を担当。
"""

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from noveler.domain.interfaces.path_service import IPathService

if TYPE_CHECKING:
    from noveler.domain.interfaces.logger_service_protocol import ILoggerService
    from noveler.domain.interfaces.path_service_protocol import IPathService

from noveler.domain.services.writing_steps.base_writing_step import BaseWritingStep, WritingStepResponse
from noveler.domain.value_objects.scene_data import SceneData


@dataclass
class PlotElement:
    """プロット要素"""

    element_type: str  # "conflict", "event", "character_arc", "theme"
    title: str
    description: str
    importance: int  # 1-10
    position: str  # "beginning", "middle", "end"
    dependencies: list[str] = field(default_factory=list)


@dataclass
class PlotStructure:
    """プロット構造"""

    act_structure: str  # "three_act", "four_act", "kishotenketsu"
    current_act: str
    act_position: float  # 0.0-1.0

    # 構造要素
    inciting_incident: str | None = None
    first_plot_point: str | None = None
    midpoint: str | None = None
    climax: str | None = None
    resolution: str | None = None


@dataclass
class PlotAnalysisResult:
    """プロット解析結果"""

    # 基本情報
    episode_number: int
    plot_exists: bool
    analysis_confidence: float = 0.0

    # プロット要素
    plot_elements: list[PlotElement] = field(default_factory=list)
    main_conflicts: list[str] = field(default_factory=list)
    key_events: list[str] = field(default_factory=list)
    character_arcs: list[str] = field(default_factory=list)

    # シーン情報（SPEC-PLOT-MANUSCRIPT-001で追加）
    scenes: list[SceneData] = field(default_factory=list)

    # 構造情報
    structure: PlotStructure | None = None

    # 前後関係
    previous_connections: list[str] = field(default_factory=list)
    next_expectations: list[str] = field(default_factory=list)

    # 技術的要素
    genre_elements: list[str] = field(default_factory=list)
    writing_techniques: list[str] = field(default_factory=list)


@dataclass
class PlotAnalyzerResponse(WritingStepResponse):
    """プロット解析サービス結果"""

    # 基底クラスのフィールド継承
    analysis_result: PlotAnalysisResult | None = None

    # パフォーマンス情報
    file_read_time_ms: float = 0.0
    parsing_time_ms: float = 0.0
    analysis_time_ms: float = 0.0

    # 統計情報
    files_analyzed: int = 0
    elements_extracted: int = 0


class PlotAnalyzerService(BaseWritingStep):
    """STEP 1: プロット解析マイクロサービス

    エピソードのプロット情報を解析し、執筆に必要な要素を抽出。
    構造分析、要素抽出、前後関係の把握を行う。
    """

    def __init__(
        self,
        logger_service: ILoggerService = None,
        path_service: IPathService = None,
        **kwargs: Any
    ) -> None:
        """プロット解析サービス初期化

        Args:
            logger_service: ロガーサービス
            path_service: パスサービス（DI注入）
            **kwargs: BaseWritingStepの引数
        """
        super().__init__(step_number=1, step_name="plot_analyzer", **kwargs)

        self._logger_service = logger_service
        self._path_service = path_service

    async def execute(
        self,
        episode_number: int,
        previous_results: dict[int, Any] | None = None
    ) -> PlotAnalyzerResponse:
        """プロット解析実行

        Args:
            episode_number: エピソード番号
            previous_results: 前ステップの結果（STEP 0のスコープ定義結果）

        Returns:
            PlotAnalyzerResponse: プロット解析結果
        """
        start_time = time.time()

        try:
            if self._logger_service:
                self._logger_service.info(f"STEP 1 プロット解析開始: エピソード={episode_number}")

            # 1. プロジェクト情報取得
            project_root = self._extract_project_root(previous_results)

            # 2. プロットファイル検索・読み込み
            file_read_start = time.time()
            plot_files = await self._find_plot_files(project_root, episode_number)
            plot_data = await self._read_plot_files(plot_files)
            file_read_time = (time.time() - file_read_start) * 1000

            # 3. プロット解析
            parsing_start = time.time()
            parsed_plot = await self._parse_plot_data(plot_data)
            parsing_time = (time.time() - parsing_start) * 1000

            # シーン抽出（SPEC-PLOT-MANUSCRIPT-001で追加）
            scenes = await self.extract_scenes(plot_data)

            analysis_start = time.time()
            analysis_result = await self._analyze_plot_structure(
                episode_number, parsed_plot, previous_results, scenes
            )
            analysis_time = (time.time() - analysis_start) * 1000

            # 4. 成功応答作成
            execution_time = (time.time() - start_time) * 1000

            return PlotAnalyzerResponse(
                success=True,
                step_number=1,
                step_name="plot_analyzer",
                execution_time_ms=execution_time,

                # プロット解析固有フィールド
                analysis_result=analysis_result,

                # パフォーマンス情報
                file_read_time_ms=file_read_time,
                parsing_time_ms=parsing_time,
                analysis_time_ms=analysis_time,

                # 統計情報
                files_analyzed=len(plot_files),
                elements_extracted=len(analysis_result.plot_elements)
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_message = f"STEP 1 プロット解析エラー: {e}"

            if self._logger_service:
                self._logger_service.error(error_message)

            return PlotAnalyzerResponse(
                success=False,
                step_number=1,
                step_name="plot_analyzer",
                execution_time_ms=execution_time,
                error_message=error_message
            )

    def _extract_project_root(self, previous_results: dict[int, Any] | None) -> Path:
        """プロジェクトルート抽出

        Args:
            previous_results: 前ステップ結果

        Returns:
            Path: プロジェクトルート
        """
        if previous_results and 0 in previous_results:
            scope_result = previous_results[0]
            if isinstance(scope_result, dict) and "project_root" in scope_result:
                return Path(scope_result["project_root"])  # TODO: IPathServiceを使用するように修正

        return Path.cwd()

    async def _find_plot_files(self, project_root: Path, episode_number: int) -> list[Path]:
        """プロットファイル検索

        Args:
            project_root: プロジェクトルート
            episode_number: エピソード番号

        Returns:
            List[Path]: プロットファイル一覧
        """
        plot_files: list[Path] = []

        # PathServiceがあれば統一解決を優先
        if self._path_service:
            p = self._path_service.get_episode_plot_path(episode_number)
            if p and p.exists():
                return [p]

        # フォールバック: 旧ディレクトリとパターンで探索
        plot_dirs = [
            project_root / "設定" / "プロット" / "話別プロット",
            project_root / "設定" / "プロット",
            project_root / "プロット",
        ]
        patterns = [
            f"ep{episode_number:03d}*.yaml",
            f"ep{episode_number:03d}*.yml",
            f"第{episode_number:03d}話*.yaml",
            f"第{episode_number:03d}話*.yml",
            f"episode{episode_number:03d}*.yaml",
            f"EP{episode_number:03d}*.yaml",
            f"EP{episode_number:03d}.yaml",
            f"{episode_number:03d}*.yaml",
        ]
        for plot_dir in plot_dirs:
            if plot_dir.exists():
                for pattern in patterns:
                    plot_files.extend(plot_dir.glob(pattern))
        return list(set(plot_files))

    async def _read_plot_files(self, plot_files: list[Path]) -> dict[str, Any]:
        """プロットファイル読み込み

        Args:
            plot_files: プロットファイル一覧

        Returns:
            Dict[str, Any]: 統合プロットデータ
        """
        combined_plot_data = {}

        for plot_file in plot_files:
            try:
                import yaml
                with open(plot_file, encoding="utf-8") as f:
                    plot_data = yaml.safe_load(f)
                    if isinstance(plot_data, dict):
                        # ファイル名をキーとして統合
                        combined_plot_data[plot_file.stem] = plot_data
            except Exception as e:
                if self._logger_service:
                    self._logger_service.warning(f"プロットファイル読み込み失敗: {plot_file} - {e}")

        return combined_plot_data

    async def _parse_plot_data(self, plot_data: dict[str, Any]) -> dict[str, Any]:
        """プロットデータ解析

        Args:
            plot_data: 読み込んだプロットデータ

        Returns:
            Dict[str, Any]: 解析済みプロットデータ
        """
        parsed_data = {
            "conflicts": [],
            "events": [],
            "characters": [],
            "themes": [],
            "structure": {},
            "metadata": {}
        }

        for content in plot_data.values():
            if not isinstance(content, dict):
                continue

            # 基本要素抽出
            parsed_data["conflicts"].extend(content.get("conflicts", []))
            parsed_data["events"].extend(content.get("events", []))
            parsed_data["characters"].extend(content.get("characters", []))
            parsed_data["themes"].extend(content.get("themes", []))

            # 構造情報
            if "structure" in content:
                parsed_data["structure"].update(content["structure"])

            # メタデータ
            for key in ["title", "summary", "genre", "act", "position"]:
                if key in content:
                    parsed_data["metadata"][key] = content[key]

        return parsed_data

    async def extract_scenes(self, yaml_content: dict[str, Any]) -> list[SceneData]:
        """シーン配列抽出（SPEC-PLOT-MANUSCRIPT-001で追加）

        Args:
            yaml_content: 解析済みYAMLコンテンツ

        Returns:
            list[SceneData]: 抽出されたシーンデータ一覧
        """
        scenes = []

        # 各プロットファイルからシーンを抽出
        for content in yaml_content.values():
            if not isinstance(content, dict):
                continue

            scenes_data = content.get("scenes", [])
            for scene_yaml in scenes_data:
                try:
                    scene_data = SceneData.from_yaml_data(scene_yaml)
                    scenes.append(scene_data)
                except (KeyError, ValueError) as e:
                    if self._logger_service:
                        self._logger_service.warning(f"シーンデータ変換エラー: {e} - データ: {scene_yaml}")
                    continue

        # シーン番号でソート
        scenes.sort(key=lambda s: s.scene_number)

        if self._logger_service:
            self._logger_service.info(f"シーン抽出完了: {len(scenes)}シーン")

        return scenes

    async def _analyze_plot_structure(
        self,
        episode_number: int,
        parsed_plot: dict[str, Any],
        previous_results: dict[int, Any] | None,
        scenes: list[SceneData] | None = None
    ) -> PlotAnalysisResult:
        """プロット構造解析

        Args:
            episode_number: エピソード番号
            parsed_plot: 解析済みプロットデータ
            previous_results: 前ステップ結果

        Returns:
            PlotAnalysisResult: プロット解析結果
        """
        # 基本情報
        plot_exists = bool(parsed_plot and any(parsed_plot.values()))
        confidence = 0.8 if plot_exists else 0.2

        # プロット要素抽出
        plot_elements = []
        main_conflicts = []
        key_events = []
        character_arcs = []

        if plot_exists:
            # 要素変換
            for conflict in parsed_plot.get("conflicts", []):
                plot_elements.append(PlotElement(
                    element_type="conflict",
                    title=conflict.get("title", ""),
                    description=conflict.get("description", ""),
                    importance=conflict.get("importance", 5),
                    position=conflict.get("position", "middle")
                ))
                main_conflicts.append(conflict.get("title", str(conflict)))

            for event in parsed_plot.get("events", []):
                plot_elements.append(PlotElement(
                    element_type="event",
                    title=event.get("title", ""),
                    description=event.get("description", ""),
                    importance=event.get("importance", 5),
                    position=event.get("position", "middle")
                ))
                key_events.append(event.get("title", str(event)))

            # キャラクター要素
            for character in parsed_plot.get("characters", []):
                if isinstance(character, dict) and "arc" in character:
                    character_arcs.append(character["arc"])

        # 構造解析
        structure = self._analyze_structure(parsed_plot, episode_number)

        # 前後関係解析
        previous_connections = self._extract_previous_connections(previous_results)
        next_expectations = self._generate_next_expectations(parsed_plot)

        # ジャンル・技術要素
        genre_elements = self._extract_genre_elements(parsed_plot)
        writing_techniques = self._recommend_techniques(parsed_plot, episode_number)

        return PlotAnalysisResult(
            episode_number=episode_number,
            plot_exists=plot_exists,
            analysis_confidence=confidence,
            plot_elements=plot_elements,
            main_conflicts=main_conflicts,
            key_events=key_events,
            character_arcs=character_arcs,
            scenes=scenes or [],  # SPEC-PLOT-MANUSCRIPT-001で追加
            structure=structure,
            previous_connections=previous_connections,
            next_expectations=next_expectations,
            genre_elements=genre_elements,
            writing_techniques=writing_techniques
        )

    def _analyze_structure(self, parsed_plot: dict[str, Any], episode_number: int) -> PlotStructure | None:
        """構造解析

        Args:
            parsed_plot: 解析済みプロットデータ
            episode_number: エピソード番号

        Returns:
            Optional[PlotStructure]: 構造情報
        """
        structure_data = parsed_plot.get("structure", {})
        metadata = parsed_plot.get("metadata", {})

        if not structure_data and not metadata:
            return None

        # Act構造推定
        act_structure = structure_data.get("type", "three_act")
        current_act = metadata.get("act", self._estimate_act(episode_number))
        act_position = metadata.get("position", self._estimate_position(episode_number))

        return PlotStructure(
            act_structure=act_structure,
            current_act=current_act,
            act_position=float(act_position) if isinstance(act_position, int | float) else 0.5,
            inciting_incident=structure_data.get("inciting_incident"),
            first_plot_point=structure_data.get("first_plot_point"),
            midpoint=structure_data.get("midpoint"),
            climax=structure_data.get("climax"),
            resolution=structure_data.get("resolution")
        )

    def _estimate_act(self, episode_number: int) -> str:
        """Act推定（エピソード番号ベース）"""
        if episode_number <= 3:
            return "first_act"
        if episode_number <= 10:
            return "second_act"
        return "third_act"

    def _estimate_position(self, episode_number: int) -> float:
        """位置推定（0.0-1.0）"""
        # 15エピソードを想定した位置計算
        return min(episode_number / 15.0, 1.0)

    def _extract_previous_connections(self, previous_results: dict[int, Any] | None) -> list[str]:
        """前エピソード接続要素抽出"""
        connections = []

        if previous_results and 0 in previous_results:
            scope_result = previous_results[0]
            if isinstance(scope_result, dict):
                connections.extend(scope_result.get("continuity_points", []))
                connections.extend(scope_result.get("unresolved_plots", []))

        return connections

    def _generate_next_expectations(self, parsed_plot: dict[str, Any]) -> list[str]:
        """次エピソード期待要素生成"""
        expectations = []

        # 未解決要素を次の期待として設定
        for conflict in parsed_plot.get("conflicts", []):
            if isinstance(conflict, dict) and not conflict.get("resolved", False):
                expectations.append(f"継続: {conflict.get('title', str(conflict))}")

        return expectations

    def _extract_genre_elements(self, parsed_plot: dict[str, Any]) -> list[str]:
        """ジャンル要素抽出"""
        elements = []

        metadata = parsed_plot.get("metadata", {})
        genre = metadata.get("genre", "")

        if "fantasy" in genre.lower():
            elements.extend(["魔法描写", "世界観説明", "ファンタジー要素"])
        elif "romance" in genre.lower():
            elements.extend(["感情描写", "関係性発展", "心理描写"])
        elif "action" in genre.lower():
            elements.extend(["戦闘描写", "緊迫感", "動的描写"])

        return elements

    def _recommend_techniques(self, parsed_plot: dict[str, Any], episode_number: int) -> list[str]:
        """執筆技術推奨"""
        techniques = []

        # エピソード位置による推奨
        if episode_number == 1:
            techniques.extend(["導入技法", "キャラクター紹介", "世界観提示"])
        elif episode_number <= 3:
            techniques.extend(["展開技法", "伏線設置", "読者の引きつけ"])
        else:
            techniques.extend(["発展技法", "クライマックス構築", "感情的盛り上がり"])

        # プロット内容による推奨
        if any("conflict" in str(c).lower() for c in parsed_plot.get("conflicts", [])):
            techniques.append("対立描写技法")

        return techniques
