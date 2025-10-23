"""Infrastructure.simple_quality_record_creator
Where: Infrastructure module generating basic quality records.
What: Writes simplified quality record files for lightweight workflows and tests.
Why: Provides a fallback record creator when full pipelines are unnecessary.
"""

from noveler.presentation.shared.shared_utilities import console

"簡易品質記録作成システム\n\nTDDアプローチで品質記録作成問題の解決策を提供する\ncomplete-episodeの複雑性を回避し、直接的に品質記録を作成する\n"
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from noveler.infrastructure.adapters.path_service_adapter import create_path_service


class SimpleQualityRecordCreator:
    """簡易品質記録作成器

    novel writeコマンドから直接呼び出される軽量な品質記録作成機能
    """

    def __init__(self, project_path, logger_service=None, console_service=None) -> None:
        """初期化

        Args:
            project_path: プロジェクトのルートパス
        """
        self.project_path = project_path
        path_service = create_path_service(project_path)
        self.quality_dir = path_service.get_management_dir()
        self.record_dir = self.quality_dir / "執筆記録"
        self.record_dir.mkdir(parents=True, exist_ok=True)
        self.logger_service = logger_service
        self.console_service = console_service

    def create_episode_quality_record(self, episode_number: int, title: str, content: str) -> None:
        """個別エピソードの品質記録を作成

        Args:
            episode_number: エピソード番号
            title: エピソードタイトル
            content: エピソード本文
        """
        quality_data: dict[str, Any] = self._analyze_basic_quality(content)
        record_data: dict[str, Any] = {
            "基本情報": {
                "話数": f"第{episode_number:03d}話",
                "タイトル": title,
                "執筆日": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "最終更新日": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "文字数": len(content),
            },
            "品質チェック結果": {
                "最終スコア": quality_data["total_score"],
                "チェック実施日": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "詳細スコア": quality_data["detailed_scores"],
                "主な指摘事項": quality_data["issues"],
            },
            "執筆内容の特徴": {
                "構成要素": quality_data["structure_elements"],
                "文体の特徴": quality_data["writing_style"],
            },
            "特記事項": quality_data["notes"],
        }
        record_file = self.record_dir / f"第{episode_number:03d}話_品質記録.yaml"
        with record_file.Path("w").open(encoding="utf-8") as f:
            yaml.dump(record_data, f, allow_unicode=True, default_flow_style=False)

    def create_ai_learning_record(self, project_name: str, episode_number: int, quality_data: dict) -> None:
        """AI学習用の統合品質記録を作成・更新

        Args:
            project_name: プロジェクト名
            episode_number: エピソード番号
            quality_data: 品質分析データ
        """
        ai_record_file = self.quality_dir / "品質記録_AI学習用.yaml"
        if ai_record_file.exists():
            with ai_record_file.Path(encoding="utf-8").open() as f:
                ai_record = yaml.safe_load(f) or {}
        else:
            ai_record = {
                "metadata": {
                    "project_name": project_name,
                    "version": "1.0",
                    "last_updated": datetime.now(timezone.utc).isoformat(),
                    "entry_count": 0,
                },
                "quality_checks": [],
                "learning_data": {
                    "improvement_trends": {},
                    "common_issues": [],
                    "personal_growth": {"strengths": [], "areas_for_improvement": [], "learning_goals": []},
                },
            }
        episode_entry = {
            "episode_number": episode_number,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "category_scores": quality_data["detailed_scores"],
            "total_score": quality_data["total_score"],
            "issues_count": len(quality_data["issues"]),
            "improvement_from_previous": 0.0,
        }
        ai_record["quality_checks"].append(episode_entry)
        ai_record["metadata"]["entry_count"] = len(ai_record["quality_checks"])
        ai_record["metadata"]["last_updated"] = datetime.now(timezone.utc).isoformat()
        with ai_record_file.Path("w").open(encoding="utf-8") as f:
            yaml.dump(ai_record, f, allow_unicode=True, default_flow_style=False)

    def create_learning_session_record(
        self, project_name: str, episode_number: int, writing_time_minutes: int | None = None
    ) -> None:
        """学習セッション記録を作成

        Args:
            project_name: プロジェクト名
            episode_number: エピソード番号
            writing_time_minutes: 執筆時間(分)
        """
        session_file = self.quality_dir / "学習セッション記録.yaml"
        if session_file.exists():
            with session_file.Path(encoding="utf-8").open() as f:
                sessions = yaml.safe_load(f) or []
        else:
            sessions = []
        session_entry = {
            "project_name": project_name,
            "episode_number": episode_number,
            "start_time": datetime.now(timezone.utc).isoformat(),
            "end_time": datetime.now(timezone.utc).isoformat(),
            "total_writing_time": writing_time_minutes or 60,
            "is_completed": True,
            "writing_environment": "standard",
            "target_audience": "一般",
            "writing_goal": "品質向上",
        }
        sessions.append(session_entry)
        with session_file.Path("w").open(encoding="utf-8") as f:
            yaml.dump(sessions, f, allow_unicode=True, default_flow_style=False)

    def _analyze_basic_quality(self, content) -> dict[str, Any]:
        """基本的な品質分析を実行

        Args:
            content: エピソード本文

        Returns:
            品質分析結果
        """
        char_count = len(content)
        len(content.split("\n"))
        paragraph_count = len([p for p in content.split("\n\n") if p.strip()])
        detailed_scores = {
            "文章構成": min(95, 70 + paragraph_count * 2),
            "読みやすさ": min(95, 75 + char_count // 100),
            "内容の充実度": min(95, 60 + char_count // 50),
            "技術的品質": 85,
        }
        total_score = sum(detailed_scores.values()) / len(detailed_scores)
        issues = []
        if char_count < 1000:
            issues.append("文字数が少ない(1000文字未満)")
        if paragraph_count < 3:
            issues.append("段落数が少ない")
        if "。。。" in content:
            issues.append("三点リーダーの形式(...→……)")
        structure_elements = []
        if "##" in content:
            structure_elements.append("見出し構造を使用")
        if "「" in content and "」" in content:
            structure_elements.append("対話描写あり")
        if "~" in content:
            structure_elements.append("描写的表現あり")
        return {
            "total_score": round(total_score, 1),
            "detailed_scores": detailed_scores,
            "issues": issues,
            "structure_elements": structure_elements,
            "writing_style": ["標準的な小説文体"],
            "notes": [f"文字数: {char_count}文字", f"段落数: {paragraph_count}段落", "基本的な品質チェックを実施"],
        }


def create_quality_records_for_episode(project_path, episode_number: int, title: str, content: str) -> None:
    """エピソードの全品質記録を作成する便利関数

    Args:
        project_path: プロジェクトパス
        episode_number: エピソード番号
        title: エピソードタイトル
        content: エピソード本文
    """
    creator = SimpleQualityRecordCreator(project_path)
    creator.create_episode_quality_record(episode_number, title, content)
    quality_data: dict[str, Any] = creator._analyze_basic_quality(content)
    project_name = project_path.name
    creator.create_ai_learning_record(project_name, episode_number, quality_data)
    creator.create_learning_session_record(project_name, episode_number)


if __name__ == "__main__":
    import tempfile

    from noveler.infrastructure.di.container import resolve_service

    try:
        console_service = resolve_service("IConsoleService")
    except ValueError:
        from noveler.infrastructure.adapters.console_service_adapter import ConsoleServiceAdapter

        console_service = ConsoleServiceAdapter()
    with tempfile.TemporaryDirectory() as temp_dir:
        test_project = Path(temp_dir) / "テストプロジェクト"
        test_project.mkdir()
        sample_content = "# 第001話 テスト\n\n## あらすじ\nこれはテスト用のエピソードです。\n\n## 本文\n\n「こんにちは」と彼は言った。\n風が吹いている。\nそして物語は続く。\n\n彼女は振り返った。\n「さようなら」\nそう言って去っていく。\n\n## 結末\n\n物語は終わりを迎えた。\n"
        create_quality_records_for_episode(test_project, 1, "テストエピソード", sample_content)
        console.print("✅ 品質記録作成テストが完了しました")
        quality_dir = test_project / "50_管理資料"
        for file_path in quality_dir.rglob("*.yaml"):
            console.print(f"📄 作成ファイル: {file_path}")
