#!/usr/bin/env python3
"""Service responsible for generating scene checklist documents."""

from collections import defaultdict
from pathlib import Path
from typing import Any

from noveler.domain.entities.scene_management_entities import SceneCategory, SceneInfo


class SceneChecklistService:
    """Produce formatted checklists summarizing scene progress and metadata."""

    def __init__(self, logger=None) -> None:
        """Initialize the service with an optional logger dependency."""
        # DDD準拠: Infrastructure層への直接依存を回避（遅延初期化）
        self._logger = logger

    def _get_default_logger(self) -> Any:
        """Return the configured logger or lazily acquire the unified logger."""
        if self._logger is None:
            # 遅延初期化: Infrastructure層インポートを実行時まで遅延
            from noveler.infrastructure.logging.unified_logger import get_logger
            self._logger = get_logger(__name__)
        return self._logger

    def generate_checklist_content(self, scenes: list[SceneInfo]) -> str:
        """Generate a Markdown checklist summarizing scene status."""
        # DDD準拠: 遅延初期化されたロガーを使用
        logger = self._get_default_logger()
        logger.info(f"チェックリスト生成開始: {len(scenes)}シーン")

        checklist_lines = ["# 重要シーンチェックリスト\n"]

        # カテゴリ別に整理
        scenes_by_category = self._group_scenes_by_category(scenes)

        # 進捗状況セクション
        progress_info = self._generate_progress_section(scenes)
        checklist_lines.extend(progress_info)

        # カテゴリ別セクション
        category_sections = self._generate_category_sections(scenes_by_category)
        checklist_lines.extend(category_sections)

        return "\n".join(checklist_lines)

    def save_checklist_to_file(self, content: str, output_path: str) -> Path:
        """Write the checklist content to disk using UTF-8 encoding."""
        file_path = Path(output_path)
        try:
            file_path.write_text(content, encoding="utf-8")
            # DDD準拠: 遅延初期化されたロガーを使用
            logger = self._get_default_logger()
            logger.info(f"チェックリスト保存完了: {file_path}")
            return file_path
        except Exception:
            # DDD準拠: 遅延初期化されたロガーを使用
            logger = self._get_default_logger()
            logger.exception("チェックリスト保存エラー")
            raise

    def _group_scenes_by_category(self, scenes: list[SceneInfo]) -> dict[SceneCategory, list[SceneInfo]]:
        """Return scenes grouped by their category."""
        scenes_by_category = defaultdict(list)
        for scene in scenes:
            scenes_by_category[scene.category].append(scene)
        return dict(scenes_by_category)

    def _generate_progress_section(self, scenes: list[SceneInfo]) -> list[str]:
        """Build the progress section of the checklist in Markdown format."""
        total_scenes = len(scenes)
        completed_scenes = sum(1 for scene in scenes if scene.completion_status == "完了")
        completion_rate = (completed_scenes / total_scenes * 100) if total_scenes > 0 else 0

        return [
            "## 進捗状況",
            f"- 総シーン数: {total_scenes}",
            f"- 完了シーン数: {completed_scenes}",
            f"- 完了率: {completion_rate:.1f}%",
            "",
        ]

    def _generate_category_sections(self, scenes_by_category: dict[SceneCategory, list[SceneInfo]]) -> list[str]:
        """Render Markdown sections for each scene category."""
        sections = []

        for category in SceneCategory:
            if category in scenes_by_category:
                sections.append(f"\n## {category.value}\n")
                for scene in scenes_by_category[category]:
                    status_icon = "✅" if scene.completion_status == "完了" else "⬜"
                    sections.append(f"- {status_icon} **{scene.title}** (ID: {scene.scene_id})")
                    sections.append(f"  - {scene.description}")

                    if scene.episodes:
                        episodes_str = ", ".join(map(str, scene.episodes))
                        sections.append(f"  - エピソード: {episodes_str}")

                    sections.append("")

        return sections
