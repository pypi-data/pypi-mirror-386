"""Domain.services.writing_steps.scope_definer_service
Where: Domain service module implementing a specific writing workflow step.
What: Provides helper routines and data structures for this writing step.
Why: Allows stepwise writing orchestrators to reuse consistent step logic.
"""

#!/usr/bin/env python3

from __future__ import annotations

"""スコープ定義サービス（STEP 0）

A38執筆プロンプトガイドのSTEP 0: スコープ定義を実装
既存のPreWritingCheckUseCaseを15ステップ体系に移行・拡張
"""


import datetime
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from noveler.domain.interfaces.logger_interface import ILogger
    from noveler.domain.interfaces.path_service import IPathService



@dataclass
class ScopeDefinitionRequest:
    """スコープ定義リクエスト"""

    episode_number: int
    project_root: Path
    previous_episode_data: dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ScopeDefinitionResult:
    """スコープ定義結果"""

    success: bool
    scope_definition: dict[str, Any] = field(default_factory=dict)
    validation_passed: bool = False
    validation_issues: list[str] = field(default_factory=list)
    output_file_path: Path | None = None
    error_message: str | None = None


class ScopeDefinerService:
    """スコープ定義サービス

    A38 STEP 0: エピソードの基本設定と制約条件の明確化
    - プロット上の位置付けを明確化
    - 前話との接続を設計
    - 今話の必達目標を設定
    - 制約条件を設定

    PreWritingCheckUseCaseの機能を継承・発展
    """

    def __init__(self, logger: ILogger, work_directory: Path | None = None, path_service: "IPathService" | None = None) -> None:
        """初期化

        Args:
            work_directory: 作業ディレクトリ（60_作業ファイル）
        """
        self._logger = logger
        self._logger.debug("ScopeDefinerService initialized")
        self._path_service = path_service

    async def execute(
        self, episode_number: int, previous_results: dict[int, Any] | None = None
    ) -> ScopeDefinitionResult:
        """スコープ定義実行

        Args:
            episode_number: エピソード番号
            previous_results: 前段階の実行結果

        Returns:
            ScopeDefinitionResult: スコープ定義結果
        """
        try:
            self._logger.info(f"スコープ定義開始: episode {episode_number}")

            # プロット情報の読み込み
            plot_data = await self._load_plot_data(episode_number)

            # 前話データの読み込み
            previous_episode_data = await self._load_previous_episode_data(episode_number)

            # スコープ定義の生成
            scope_definition = await self._generate_scope_definition(
                episode_number=episode_number, plot_data=plot_data, previous_episode_data=previous_episode_data
            )

            # 自己検証の実行
            validation_result = await self._validate_scope_definition(scope_definition)

            # 結果をファイルに保存
            output_path = await self._save_scope_definition(
                episode_number=episode_number, scope_definition=scope_definition
            )

            self._logger.info(f"スコープ定義完了: episode {episode_number}")

            return ScopeDefinitionResult(
                success=True,
                scope_definition=scope_definition,
                validation_passed=validation_result["passed"],
                validation_issues=validation_result["issues"],
                output_file_path=output_path,
            )

        except Exception as e:
            self._logger.exception(f"スコープ定義エラー: {e}")
            return ScopeDefinitionResult(success=False, error_message=str(e))

    async def _load_plot_data(self, episode_number: int) -> dict[str, Any]:
        """プロットデータを読み込み

        Args:
            episode_number: エピソード番号

        Returns:
            Dict[str, Any]: プロットデータ
        """
        # PathService優先でプロットパスを取得
        plot_file: Path | None = None
        if self._path_service:
            plot_file = self._path_service.get_episode_plot_path(episode_number)
        # 旧形式 fallback (episodeNNN.yaml)
        if not plot_file:
            plot_candidates = [
                Path(f"20_プロット/話別プロット/ep{episode_number:03d}.yaml"),
                Path(f"20_プロット/話別プロット/EP{episode_number:03d}.yaml"),
                Path(f"20_プロット/話別プロット/episode{episode_number:03d}.yaml"),
            ]
            for candidate in plot_candidates:
                if candidate.exists():
                    plot_file = candidate
                    break
            else:
                plot_file = plot_candidates[0]

        if not plot_file.exists():
            self._logger.warning(f"プロットファイルが見つかりません: {plot_file}")
            return {}

        try:
            with open(plot_file, encoding="utf-8") as f:
                plot_data = yaml.safe_load(f) or {}

            self._logger.debug(f"プロットデータ読み込み完了: {plot_file}")
            return plot_data

        except Exception as e:
            self._logger.exception(f"プロットデータ読み込みエラー: {e}")
            return {}

    async def _load_previous_episode_data(self, episode_number: int) -> dict[str, Any]:
        """前話データを読み込み

        Args:
            episode_number: エピソード番号

        Returns:
            Dict[str, Any]: 前話データ
        """
        if episode_number <= 1:
            return {}

        # PathService優先
        previous_episode_file: Path | None = None
        if self._path_service:
            previous_episode_file = self._path_service.get_episode_plot_path(episode_number - 1)
        if not previous_episode_file:
            plot_candidates = [
                Path(f"20_プロット/話別プロット/ep{episode_number - 1:03d}.yaml"),
                Path(f"20_プロット/話別プロット/EP{episode_number - 1:03d}.yaml"),
                Path(f"20_プロット/話別プロット/episode{episode_number - 1:03d}.yaml"),
            ]
            for candidate in plot_candidates:
                if candidate.exists():
                    previous_episode_file = candidate
                    break
            else:
                previous_episode_file = plot_candidates[0]

        if not previous_episode_file.exists():
            self._logger.warning(f"前話プロットファイルが見つかりません: {previous_episode_file}")
            return {}

        try:
            with open(previous_episode_file, encoding="utf-8") as f:
                previous_data = yaml.safe_load(f) or {}

            self._logger.debug(f"前話データ読み込み完了: {previous_episode_file}")
            return previous_data

        except Exception as e:
            self._logger.exception(f"前話データ読み込みエラー: {e}")
            return {}

    async def _generate_scope_definition(
        self, episode_number: int, plot_data: dict[str, Any], previous_episode_data: dict[str, Any]
    ) -> dict[str, Any]:
        """スコープ定義を生成

        Args:
            episode_number: エピソード番号
            plot_data: プロットデータ
            previous_episode_data: 前話データ

        Returns:
            Dict[str, Any]: スコープ定義
        """
        # 章情報の抽出
        chapter_info = self._extract_chapter_info(episode_number, plot_data)

        # プロット上の位置付けを明確化
        position_analysis = self._analyze_plot_position(episode_number, plot_data, chapter_info)

        # 前話との接続を設計
        connection_design = self._design_connection_with_previous(previous_episode_data, plot_data)

        # 必達目標を設定
        target_goals = self._set_target_goals(plot_data, chapter_info)

        # 制約条件を設定
        constraints = self._set_constraints()

        scope_definition = {
            "episode_info": {
                "episode_number": episode_number,
                "title": plot_data.get("title", f"第{episode_number}話"),
                "chapter_info": chapter_info,
            },
            "plot_position": position_analysis,
            "connection_with_previous": connection_design,
            "target_goals": target_goals,
            "constraints": constraints,
            "metadata": {
                "created_at": datetime.now(tz=datetime.timezone.utc).isoformat(),
                "step_number": 0,
                "step_name": "scope_definition",
            },
        }

        self._logger.debug(f"スコープ定義生成完了: episode {episode_number}")
        return scope_definition

    def _extract_chapter_info(self, episode_number: int, plot_data: dict[str, Any]) -> dict[str, Any]:
        """章情報を抽出

        Args:
            episode_number: エピソード番号
            plot_data: プロットデータ

        Returns:
            Dict[str, Any]: 章情報
        """
        # 簡易的な章番号計算（実際のプロジェクトに応じて調整）
        chapter_number = ((episode_number - 1) // 5) + 1
        chapter_episode_position = ((episode_number - 1) % 5) + 1

        return {
            "chapter_number": chapter_number,
            "episode_in_chapter": chapter_episode_position,
            "chapter_title": plot_data.get("chapter_title", f"第{chapter_number}章"),
            "chapter_role": self._determine_chapter_role(chapter_episode_position),
        }

    def _determine_chapter_role(self, position: int) -> str:
        """章内での役割を決定

        Args:
            position: 章内での位置（1-5）

        Returns:
            str: 役割（導入/展開/転換/結末）
        """
        role_map = {1: "導入", 2: "展開前半", 3: "展開後半", 4: "転換", 5: "結末"}
        return role_map.get(position, "展開")

    def _analyze_plot_position(
        self, episode_number: int, plot_data: dict[str, Any], chapter_info: dict[str, Any]
    ) -> dict[str, Any]:
        """プロット上の位置付けを分析

        Args:
            episode_number: エピソード番号
            plot_data: プロットデータ
            chapter_info: 章情報

        Returns:
            Dict[str, Any]: 位置付け分析
        """
        return {
            "chapter_role": chapter_info["chapter_role"],
            "story_importance": self._determine_story_importance(plot_data),
            "relationship_to_adjacent": self._analyze_adjacent_relationship(episode_number, plot_data),
        }

    def _determine_story_importance(self, plot_data: dict[str, Any]) -> str:
        """物語全体での重要度を決定

        Args:
            plot_data: プロットデータ

        Returns:
            str: 重要度（メイン/サブ/補完）
        """
        # プロットデータから重要度を推定
        if plot_data.get("is_climax", False) or plot_data.get("major_event", False):
            return "メイン"
        if plot_data.get("character_development", False):
            return "サブ"
        return "補完"

    def _analyze_adjacent_relationship(self, episode_number: int, plot_data: dict[str, Any]) -> dict[str, Any]:
        """前後エピソードとの関係性を分析

        Args:
            episode_number: エピソード番号
            plot_data: プロットデータ

        Returns:
            Dict[str, Any]: 関係性分析
        """
        return {
            "continues_from_previous": plot_data.get("continues_previous", False),
            "connects_to_next": plot_data.get("connects_next", False),
            "standalone_nature": plot_data.get("standalone", True),
        }

    def _design_connection_with_previous(
        self, previous_episode_data: dict[str, Any], current_plot_data: dict[str, Any]
    ) -> dict[str, Any]:
        """前話との接続を設計

        Args:
            previous_episode_data: 前話データ
            current_plot_data: 現在の話のプロットデータ

        Returns:
            Dict[str, Any]: 接続設計
        """
        if not previous_episode_data:
            return {"has_previous": False, "connection_type": "新規開始"}

        return {
            "has_previous": True,
            "previous_ending": previous_episode_data.get("ending_state", "未定義"),
            "inherited_elements": self._extract_inherited_elements(previous_episode_data, current_plot_data),
            "continuity_elements": self._extract_continuity_elements(previous_episode_data, current_plot_data),
        }

    def _extract_inherited_elements(self, previous_data: dict[str, Any], current_data: dict[str, Any]) -> list[str]:
        """引き継ぐべき要素を抽出

        Args:
            previous_data: 前話データ
            current_data: 現在のデータ

        Returns:
            List[str]: 引き継ぎ要素
        """
        inherited = []

        # キャラクター状態の引き継ぎ
        if previous_data.get("character_state"):
            inherited.append("キャラクター状態")

        # 未解決の問題
        if previous_data.get("unresolved_issues"):
            inherited.append("未解決の問題")

        # 世界観要素
        if previous_data.get("world_state"):
            inherited.append("世界観状態")

        return inherited

    def _extract_continuity_elements(self, previous_data: dict[str, Any], current_data: dict[str, Any]) -> list[str]:
        """継続性を保つ要素を抽出

        Args:
            previous_data: 前話データ
            current_data: 現在のデータ

        Returns:
            List[str]: 継続性要素
        """
        continuity = []

        # 感情の継続
        if previous_data.get("emotional_state"):
            continuity.append("感情状態")

        # 状況の継続
        if previous_data.get("situation"):
            continuity.append("状況設定")

        # キャラクター関係の継続
        if previous_data.get("relationships"):
            continuity.append("キャラクター関係性")

        return continuity

    def _set_target_goals(self, plot_data: dict[str, Any], chapter_info: dict[str, Any]) -> dict[str, Any]:
        """必達目標を設定

        Args:
            plot_data: プロットデータ
            chapter_info: 章情報

        Returns:
            Dict[str, Any]: 必達目標
        """
        return {
            "plot_achievement": plot_data.get("main_goal", "プロット進行"),
            "character_growth": plot_data.get("character_goal", "キャラクター成長"),
            "reader_experience": plot_data.get("reader_goal", "読者体験向上"),
            "specific_targets": [
                f"章の{chapter_info['chapter_role']}としての役割を果たす",
                "前話からの自然な流れを維持",
                "次話への適切な引きを作る",
            ],
        }

    def _set_constraints(self) -> dict[str, Any]:
        """制約条件を設定

        Returns:
            Dict[str, Any]: 制約条件
        """
        return {
            "word_count": {"minimum": 8000, "target": 10000, "maximum": 15000, "note": "なろう最適文字数"},
            "technical_constraints": {"viewpoint": "三人称単元視点", "tense": "過去形", "style": "だ・である調"},
            "content_constraints": {"genre_adherence": True, "character_consistency": True, "world_consistency": True},
        }

    async def _validate_scope_definition(self, scope_definition: dict[str, Any]) -> dict[str, Any]:
        """スコープ定義の自己検証

        Args:
            scope_definition: スコープ定義

        Returns:
            Dict[str, Any]: 検証結果
        """
        issues = []

        # 必須要素のチェック
        required_keys = ["episode_info", "plot_position", "connection_with_previous", "target_goals", "constraints"]

        for key in required_keys:
            if key not in scope_definition:
                issues.append(f"必須要素が不足: {key}")

        # プロット位置付けのチェック
        if "plot_position" in scope_definition:
            position = scope_definition["plot_position"]
            if not all(k in position for k in ["chapter_role", "story_importance"]):
                issues.append("プロット位置付けが不完全")

        # 必達目標のチェック
        if "target_goals" in scope_definition:
            goals = scope_definition["target_goals"]
            if not goals.get("plot_achievement"):
                issues.append("プロット目標が設定されていない")

        # 制約条件のチェック
        if "constraints" in scope_definition:
            constraints = scope_definition["constraints"]
            word_count = constraints.get("word_count", {})
            if word_count.get("minimum", 0) < 8000:
                issues.append("最小文字数が8000字未満")

        validation_passed = len(issues) == 0

        self._logger.debug(f"スコープ定義検証結果: passed={validation_passed}, issues={len(issues)}")

        return {"passed": validation_passed, "issues": issues, "validation_items_checked": len(required_keys) + 3}

    async def _save_scope_definition(self, episode_number: int, scope_definition: dict[str, Any]) -> Path:
        """スコープ定義をファイルに保存

        Args:
            episode_number: エピソード番号
            scope_definition: スコープ定義

        Returns:
            Path: 保存されたファイルパス
        """
        # 作業ディレクトリ作成
        self.work_directory.mkdir(parents=True, exist_ok=True)

        # ファイルパス生成
        filename = f"episode{episode_number:03d}_step00.yaml"
        file_path = self.work_directory / filename

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                yaml.dump(scope_definition, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

            self._logger.info(f"スコープ定義保存完了: {file_path}")
            return file_path

        except Exception as e:
            self._logger.exception(f"スコープ定義保存エラー: {e}")
            raise
