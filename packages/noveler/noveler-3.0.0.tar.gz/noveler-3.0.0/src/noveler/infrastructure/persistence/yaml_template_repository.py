#!/usr/bin/env python3
"""YAMLテンプレートリポジトリ実装

TemplateRepositoryインターフェースの実装
YAMLファイルからテンプレートを読み込み
"""

import os
import sys
from pathlib import Path
from typing import Any

import yaml

# スクリプトのルートディレクトリをパスに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
scripts_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, scripts_root)

from noveler.domain.repositories.template_repository import TemplateRepository
from noveler.domain.value_objects.workflow_stage_type import WorkflowStageType


class YamlTemplateRepository(TemplateRepository):
    """YAMLテンプレートリポジトリ実装"""

    def __init__(self, templates_dir: Path | str) -> None:
        """Args:
        templates_dir: テンプレートディレクトリ
        """
        self.templates_dir = Path(templates_dir)

        # 段階別テンプレートファイルマッピング
        self.template_files = {
            WorkflowStageType.MASTER_PLOT: "マスタープロットテンプレート.yaml",
            WorkflowStageType.CHAPTER_PLOT: "章別プロットテンプレート.yaml",
            WorkflowStageType.EPISODE_PLOT: "話数別プロットテンプレート.yaml",
        }

    def load_template(self, stage_type: WorkflowStageType) -> dict[str, Any]:
        """指定段階のテンプレートを読み込み

        Args:
            stage_type: ワークフロー段階タイプ

        Returns:
            Dict[str, Any]: テンプレート内容

        Raises:
            FileNotFoundError: テンプレートが存在しない場合
        """
        template_file = self.get_template_path(stage_type)
        template_path = self.templates_dir / template_file

        if not template_path.exists():
            # テンプレートファイルが存在しない場合はデフォルトテンプレートを生成
            return self._generate_default_template(stage_type)

        try:
            with Path(template_path).open(encoding="utf-8") as f:
                template_content = yaml.safe_load(f)
                return template_content or {}
        except (OSError, yaml.YAMLError) as e:
            msg = f"テンプレート読み込みエラー: {e}"
            raise FileNotFoundError(msg) from e

    def get_template_path(self, stage_type: WorkflowStageType) -> str:
        """指定段階のテンプレートファイルパスを取得

        Args:
            stage_type: ワークフロー段階タイプ

        Returns:
            str: テンプレートファイルパス
        """
        return self.template_files.get(stage_type, "デフォルトテンプレート.yaml")

    def _generate_default_template(self, stage_type: WorkflowStageType) -> dict[str, Any]:
        """デフォルトテンプレートを生成

        Args:
            stage_type: ワークフロー段階タイプ

        Returns:
            Dict[str, Any]: デフォルトテンプレート内容
        """
        if stage_type == WorkflowStageType.MASTER_PLOT:
            return {
                "project_info": {
                    "title": "プロジェクトタイトル",
                    "description": "プロジェクトの概要説明",
                },
                "story_structure": {
                    "theme": "メインテーマ",
                    "genre": "ジャンル",
                    "target_audience": "ターゲット読者",
                },
                "chapters": {
                    "第1章": {
                        "title": "第1章タイトル",
                        "purpose": "章の目的・役割",
                        "episodes_count": 10,
                    },
                },
                "character_arcs": {
                    "protagonist": {
                        "start_state": "物語開始時の状態",
                        "end_state": "物語終了時の状態",
                        "growth_path": "成長の道筋",
                    },
                },
                "plot_points": {
                    "inciting_incident": "きっかけとなる事件",
                    "plot_point_1": "第1プロットポイント",
                    "midpoint": "中間点",
                    "plot_point_2": "第2プロットポイント",
                    "climax": "クライマックス",
                    "resolution": "解決",
                },
            }

        if stage_type == WorkflowStageType.CHAPTER_PLOT:
            return {
                "chapter_number": 1,
                "title": "章タイトル",
                "summary": "この章の概要・あらすじ",
                "key_events": ["主要イベント1", "主要イベント2", "主要イベント3"],
                "episodes": [
                    {
                        "number": 1,
                        "title": "話タイトル",
                        "purpose": "話の目的",
                        "main_events": ["主要イベント1", "主要イベント2"],
                    }
                ],
                "character_arcs": {
                    "protagonist": {
                        "chapter_start": "章開始時の状態",
                        "chapter_end": "章終了時の状態",
                        "key_moments": ["重要な瞬間1", "重要な瞬間2"],
                    }
                },
                "foreshadowing": ["仕込み・伏線1", "仕込み・伏線2"],
                "settings": {"location": "主要舞台", "time_period": "時期・期間", "mood": "章の雰囲気"},
                "writing_notes": {
                    "goals": ["章の目標1", "章の目標2"],
                    "themes": ["テーマ1", "テーマ2"],
                    "conflicts": ["葛藤要素1", "葛藤要素2"],
                },
                "metadata": {"template_type": "chapter_plot", "version": "1.0"},
            }

        if stage_type == WorkflowStageType.EPISODE_PLOT:
            return {
                "episode_info": {
                    "number": 1,
                    "title": "話タイトル",
                    "purpose": "この話の目的・達成したいこと",
                    "word_count_target": 3000,
                },
                "scenes": {
                    "scene_01": {
                        "title": "導入",
                        "location": "場所",
                        "characters": ["登場キャラクター"],
                        "purpose": "シーンの目的",
                        "events": ["起こる出来事"],
                        "emotions": ["感情の変化"],
                    },
                    "scene_02": {
                        "title": "展開",
                        "location": "場所",
                        "characters": ["登場キャラクター"],
                        "purpose": "シーンの目的",
                        "events": ["起こる出来事"],
                        "emotions": ["感情の変化"],
                    },
                    "scene_03": {
                        "title": "山場",
                        "location": "場所",
                        "characters": ["登場キャラクター"],
                        "purpose": "シーンの目的",
                        "events": ["起こる出来事"],
                        "emotions": ["感情の変化"],
                    },
                    "scene_04": {
                        "title": "結末",
                        "location": "場所",
                        "characters": ["登場キャラクター"],
                        "purpose": "シーンの目的",
                        "events": ["起こる出来事"],
                        "emotions": ["感情の変化"],
                    },
                },
                "notes": {
                    "foreshadowing": "伏線・仕込み",
                    "character_development": "キャラクター成長",
                    "plot_advancement": "プロット進行",
                    "world_building": "世界観描写",
                },
            }

        return {
            "template_type": stage_type.value,
            "description": "デフォルトテンプレート",
            "content": {},
        }
