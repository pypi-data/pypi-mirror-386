#!/usr/bin/env python3
"""SPEC-PLOT-MANUSCRIPT-001: EP001完全生成E2E（非CLI）統合テスト

EP001の生成プロセスを内部API直呼びで統合検証するテストスイート。
CLIからMCPへの移行に伴い、CLI実行部分を撤去し内部APIに置換。
"""

import asyncio
import pytest
import yaml
from pathlib import Path
from typing import Dict, Any

from noveler.main import execute_18_step_writing


@pytest.mark.spec("SPEC-PLOT-MANUSCRIPT-001")
@pytest.mark.e2e
class TestEP001CompleteGenerationE2E:
    """EP001完全生成E2Eテスト"""

    @pytest.fixture
    def project_root(self, isolated_temp_dir: Path) -> Path:
        """テスト用プロジェクトルート（分離環境）"""
        # 分離された一時ディレクトリをプロジェクトルートとして使用
        root = isolated_temp_dir
        # 必要最低限のディレクトリを作成
        (root / "temp").mkdir(parents=True, exist_ok=True)
        return root

    @pytest.fixture
    def path_service(self, project_root: Path):
        """パスサービス（簡易・ローカル）"""
        class _DummyPathService:
            def __init__(self, root: Path) -> None:
                self._root = root

            def get_plot_dir(self) -> Path:
                return self._root / "プロット"

            def get_manuscript_dir(self) -> Path:
                return self._root / "原稿"

        # 必要なディレクトリを用意
        (project_root / "プロット" / "話別プロット").mkdir(parents=True, exist_ok=True)
        (project_root / "原稿").mkdir(parents=True, exist_ok=True)
        return _DummyPathService(project_root)

    @pytest.fixture
    def episode001_yaml_path(self, path_service) -> Path:
        """EP001.yamlファイルパス"""
        # プロットディレクトリからEP001.yamlを検索
        plot_dir = path_service.get_plot_dir()

        # 複数の可能なパスをチェック
        possible_paths = [
            plot_dir / "話別プロット" / "EP001.yaml",
            plot_dir / "話別プロット" / "第001話.yaml",
            plot_dir / "EP001.yaml",
            plot_dir / "第001話.yaml",
        ]

        for path in possible_paths:
            if path.exists():
                return path

        # 見つからない場合はデフォルトパス
        return plot_dir / "話別プロット" / "EP001.yaml"

    @pytest.fixture
    def manuscript_path(self, path_service) -> Path:
        """第001話.mdファイルパス"""
        manuscript_dir = path_service.get_manuscript_dir()
        return manuscript_dir / "第001話.md"

    @pytest.fixture
    def backup_existing_files(self, episode001_yaml_path: Path, manuscript_path: Path):
        """既存ファイルのバックアップ"""
        backups = {}

        # EP001.yamlのバックアップ
        if episode001_yaml_path.exists():
            backup_plot_path = episode001_yaml_path.with_suffix('.yaml.backup')
            episode001_yaml_path.rename(backup_plot_path)
            backups['plot'] = backup_plot_path

        # 第001話.mdのバックアップ
        if manuscript_path.exists():
            backup_manuscript_path = manuscript_path.with_suffix('.md.backup')
            manuscript_path.rename(backup_manuscript_path)
            backups['manuscript'] = backup_manuscript_path

        yield backups

        # テスト後の復元
        for file_type, backup_path in backups.items():
            if backup_path.exists():
                if file_type == 'plot':
                    backup_path.rename(episode001_yaml_path)
                elif file_type == 'manuscript':
                    backup_path.rename(manuscript_path)

    @pytest.mark.asyncio
    async def test_complete_episode001_generation_workflow(
        self,
        project_root: Path,
        episode001_yaml_path: Path,
        manuscript_path: Path,
        backup_existing_files: Dict[str, Path]
    ):
        """EP001の完全生成（内部API直呼び）統合テスト"""
        # Given: テスト用EP001.yamlを作成（将来の参照互換用）
        test_plot_data = self._create_test_episode001_yaml_data()
        episode001_yaml_path.parent.mkdir(parents=True, exist_ok=True)
        with open(episode001_yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(test_plot_data, f, allow_unicode=True, default_flow_style=False)

        # When: 内部APIを直接実行（非CLI）
        result = await execute_18_step_writing(episode=1, dry_run=False, project_root=str(project_root))

        # Then: 正常終了と完了ステップ数
        assert result["success"] is True
        assert result["total_steps"] == 19
        assert result["completed_steps"] == 19

        # And: 原稿が保存されている（EnhancedFileManager経由）
        assert len(result.get("saved_files", [])) == 1
        saved_path = Path(result["saved_files"][0])
        assert saved_path.exists(), f"manuscript not found: {saved_path}"

        # And: 品質レポートが生成されている
        quality_dir = project_root / "temp" / "quality_reports"
        assert quality_dir.exists()
        assert any(quality_dir.glob("*.json")), "quality reports not generated"

    @pytest.mark.asyncio
    async def test_asuka_character_integration(
        self,
        project_root: Path,
        episode001_yaml_path: Path,
        backup_existing_files: Dict[str, Path]
    ):
        """内部APIでの一連フロー結果検証（内容には依存しない）"""
        # Given
        test_plot_data = self._create_test_episode001_yaml_data()
        episode001_yaml_path.parent.mkdir(parents=True, exist_ok=True)
        with open(episode001_yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(test_plot_data, f, allow_unicode=True, default_flow_style=False)

        # When
        result = await execute_18_step_writing(episode=1, dry_run=True, project_root=str(project_root))

        # Then: 実行結果構造とコンテンツ長
        assert result["success"] is True
        assert result.get("file_manager_used") == "EnhancedFileManager"
        assert result["content_length"] > 0
        assert len(result.get("saved_files", [])) == 0  # dry_runでは保存しない

    @pytest.mark.asyncio
    async def test_debug_log_awakening_scene_generation(
        self,
        project_root: Path,
        episode001_yaml_path: Path,
        backup_existing_files: Dict[str, Path]
    ):
        """内部API経由の品質レポート生成確認テスト"""
        # Given
        test_plot_data = self._create_test_episode001_yaml_data()
        episode001_yaml_path.parent.mkdir(parents=True, exist_ok=True)
        with open(episode001_yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(test_plot_data, f, allow_unicode=True, default_flow_style=False)

        # When
        result = await execute_18_step_writing(episode=1, dry_run=False, project_root=str(project_root))

        # Then: 品質レポートが複数生成されていること
        quality_dir = project_root / "temp" / "quality_reports"
        reports = list(quality_dir.glob("*.json"))
        assert len(reports) >= 3, "expected multiple quality reports for steps"

        # And: 実行ログにステップ11（初稿生成）が含まれる
        step_ids = {e.get("step") for e in result.get("execution_log", [])}
        assert 11 in step_ids

    def _create_test_episode001_yaml_data(self) -> Dict[str, Any]:
        """テスト用EP001.yamlデータ作成"""
        return {
            "episode_number": 1,
            "title": "最初の出会い",
            "scope_definition": {
                "theme": "新世界への第一歩",
                "conflicts": ["環境適応", "言語の壁"]
            },
            "structure": {
                "phases": 3,
                "beats_per_phase": 4
            },
            "scenes": [
                {
                    "scene_number": 1,
                    "title": "DEBUGログ覚醒",
                    "description": "主人公がDEBUGログ能力に目覚める導入シーン",
                    "characters": ["主人公"],
                    "events": ["ログ能力発現", "世界観説明"],
                    "location": "学校",
                    "time_setting": "放課後"
                },
                {
                    "scene_number": 2,
                    "title": "能力の発見",
                    "description": "DEBUG能力の詳細が判明",
                    "characters": ["主人公"],
                    "events": ["能力テスト", "限界確認"],
                    "location": "教室",
                    "time_setting": "夕方"
                },
                {
                    "scene_number": 3,
                    "title": "謎の現象",
                    "description": "不可解な現象が発生",
                    "characters": ["主人公"],
                    "events": ["異常現象", "混乱"],
                    "location": "廊下",
                    "time_setting": "夜"
                },
                {
                    "scene_number": 4,
                    "title": "あすかとの出会い",
                    "description": "協力者あすかとの初対面",
                    "characters": ["主人公", "あすか"],
                    "events": ["キャラクター登場", "協力関係構築", "情報共有"],
                    "location": "屋上",
                    "time_setting": "深夜"
                },
                {
                    "scene_number": 5,
                    "title": "協力開始",
                    "description": "あすかとの本格的な協力開始",
                    "characters": ["主人公", "あすか"],
                    "events": ["作戦立案", "役割分担"],
                    "location": "図書館",
                    "time_setting": "翌日"
                },
                {
                    "scene_number": 6,
                    "title": "調査活動",
                    "description": "謎の現象について調査",
                    "characters": ["主人公", "あすか"],
                    "events": ["情報収集", "手がかり発見"],
                    "location": "街中",
                    "time_setting": "昼間"
                },
                {
                    "scene_number": 7,
                    "title": "危機の接近",
                    "description": "より大きな危機が迫る",
                    "characters": ["主人公", "あすか"],
                    "events": ["危険察知", "緊張感増大"],
                    "location": "公園",
                    "time_setting": "夕方"
                },
                {
                    "scene_number": 8,
                    "title": "能力の覚醒",
                    "description": "真の能力が覚醒",
                    "characters": ["主人公", "あすか"],
                    "events": ["能力強化", "覚醒"],
                    "location": "秘密基地",
                    "time_setting": "夜"
                },
                {
                    "scene_number": 9,
                    "title": "危機解決",
                    "description": "DEBUGログ能力で危機を脱出",
                    "characters": ["主人公", "あすか"],
                    "events": ["能力活用", "問題解決", "絆深化"],
                    "location": "戦闘エリア",
                    "time_setting": "深夜"
                }
            ]
        }

    def _assert_all_scenes_included(self, manuscript_content: str, plot_data: Dict[str, Any]) -> None:
        """全シーンが含まれることを確認"""
        scenes = plot_data.get("scenes", [])

        # 各シーンのタイトルが含まれることを確認
        for scene in scenes:
            scene_title = scene.get("title", "")
            scene_number = scene.get("scene_number", 0)

            # シーンタイトルまたはシーン番号の言及があることを確認
            title_found = scene_title in manuscript_content
            number_found = f"シーン{scene_number}" in manuscript_content or f"場面{scene_number}" in manuscript_content

            assert title_found or number_found, f"シーン{scene_number}「{scene_title}」の言及が見つかりません"

        # 重要キャラクターの確認
        assert "あすか" in manuscript_content, "あすかキャラクターが見つかりません"

        # 重要イベントの確認
        debug_related = any(keyword in manuscript_content for keyword in ["DEBUG", "ログ", "覚醒"])
        assert debug_related, "DEBUGログ関連の描写が見つかりません"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
