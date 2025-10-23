#!/usr/bin/env python3
"""
A24ガイド ファイルリポジトリ

A24_話別プロット作成ガイド.mdからプロンプト生成情報を抽出する
インフラストラクチャ層の実装。
"""

from pathlib import Path
from typing import Any

from noveler.domain.entities.prompt_generation import A24Stage
from noveler.domain.services.prompt_generation_service import A24GuideRepository


class FileA24GuideRepository(A24GuideRepository):
    """A24ガイド ファイルリポジトリ実装

    A24_話別プロット作成ガイド.mdファイルから段階別指示、
    検証基準、テンプレート構造を抽出する。
    """

    def __init__(self, guide_file_path: Path) -> None:
        self._guide_file_path = guide_file_path
        self._cached_content: str | None = None

        if not guide_file_path.exists():
            msg = f"A24ガイドファイルが見つかりません: {guide_file_path}"
            raise FileNotFoundError(msg)

    def get_stage_instructions(self, stage: A24Stage) -> list[str]:
        """指定段階の指示取得"""
        content = self._get_guide_content()

        stage_mapping = {
            A24Stage.SKELETON: "Step 1: 基本設定・分析準備",
            A24Stage.THREE_ACT: "Step 2: テンプレート作成・構造設計",
            A24Stage.SCENE_DETAIL: "Step 3: キャラクター・感情詳細化",
            A24Stage.TECH_INTEGRATION: "Step 4: 技術統合・品質確保",
        }

        stage_header = stage_mapping.get(stage)
        if not stage_header:
            return []

        return self._extract_section_instructions(content, stage_header)

    def get_validation_criteria(self, stage: A24Stage) -> list[str]:
        """指定段階の検証基準取得"""
        content = self._get_guide_content()

        stage_mapping = {
            A24Stage.SKELETON: "Step 1: 基本設定・分析準備",
            A24Stage.THREE_ACT: "Step 2: テンプレート作成・構造設計",
            A24Stage.SCENE_DETAIL: "Step 3: キャラクター・感情詳細化",
            A24Stage.TECH_INTEGRATION: "Step 4: 技術統合・品質確保",
        }

        stage_header = stage_mapping.get(stage)
        if not stage_header:
            return []

        return self._extract_section_checklist(content, stage_header)

    def get_template_structure(self) -> dict[str, Any]:
        """テンプレート構造取得"""
        # A24ガイドから基本的なテンプレート構造を抽出
        # 実際の実装では話別プロットテンプレート.yamlを参照することも可能
        return {
            "episode_info": {
                "episode_number": "int",
                "title": "str",
                "chapter_number": "int",
                "theme": "str",
                "purpose": "str",
                "emotional_core": "str",
            },
            "viewpoint_info": {"viewpoint": "str", "character": "str"},
            "synopsis": "str (400字程度)",
            "story_structure": {"setup": "dict", "confrontation": "dict", "resolution": "dict"},
            "characters": {"main_character": "dict", "supporting_characters": "dict"},
            "technical_elements": {"programming_concepts": "list", "magic_system": "dict", "world_building": "dict"},
            "emotional_elements": {
                "primary_emotion": "str",
                "emotional_journey": "list",
                "relationship_dynamics": "list",
            },
            "plot_elements": {"foreshadowing": "list", "themes": "list", "mysteries": "list"},
        }

    def _get_guide_content(self) -> str:
        """ガイドファイル内容取得（キャッシュ付き）"""
        if self._cached_content is None:
            try:
                with self._guide_file_path.Path("r").open(encoding="utf-8") as f:
                    self._cached_content = f.read()
            except Exception as e:
                msg = f"A24ガイドファイル読み込みエラー: {e}"
                raise RuntimeError(msg) from e

        return self._cached_content

    def _extract_section_instructions(self, content: str, stage_header: str) -> list[str]:
        """セクションの作業手順抽出"""
        lines = content.split("\n")
        instructions = []
        in_stage_section = False
        in_work_procedure = False

        for line in lines:
            stripped = line.strip()

            # 段階セクションの開始検出
            if stage_header in stripped:
                in_stage_section = True
                continue

            # 次の段階セクション検出で終了
            if in_stage_section and stripped.startswith("## Stage") and stage_header not in stripped:
                break

            # 作業手順セクション検出
            if in_stage_section and "🛠 作業手順" in stripped:
                in_work_procedure = True
                continue

            # 作業手順内の番号付きリスト抽出
            if in_work_procedure and stripped.startswith(("1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.")):
                # 番号を除去して指示内容のみ抽出
                instruction = stripped.split(".", 1)[1].strip() if "." in stripped else stripped
                if instruction:
                    instructions.append(instruction)
                continue

            # チェックリストセクション到達で作業手順終了
            if in_work_procedure and "✅ チェックリスト" in stripped:
                in_work_procedure = False
                continue

        return instructions

    def _extract_section_checklist(self, content: str, stage_header: str) -> list[str]:
        """セクションのチェックリスト抽出"""
        lines = content.split("\n")
        checklist = []
        in_stage_section = False
        in_checklist = False

        for line in lines:
            stripped = line.strip()

            # 段階セクションの開始検出
            if stage_header in stripped:
                in_stage_section = True
                continue

            # 次の段階セクション検出で終了
            if in_stage_section and stripped.startswith("## Stage") and stage_header not in stripped:
                break

            # チェックリストセクション検出
            if in_stage_section and "✅ チェックリスト" in stripped:
                in_checklist = True
                continue

            # チェックリスト項目抽出（- で始まる行）
            if in_checklist and stripped.startswith("-"):
                item = stripped[1:].strip()  # "- " を除去
                if item:
                    checklist.append(item)
                continue

            # 次のセクション到達でチェックリスト終了
            if in_checklist and (stripped.startswith(("---", "##"))):
                break

        return checklist
