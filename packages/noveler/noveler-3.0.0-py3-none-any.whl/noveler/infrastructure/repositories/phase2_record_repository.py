
r"""Phase 2執筆記録管理システム\n\nAI協創型執筆の3ステップ作業過程を体系的に記録・分析するシステム\n"""
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

from noveler.domain.value_objects.project_time import ProjectTimezone, project_now
from noveler.presentation.shared.shared_utilities import console

JST = ProjectTimezone.jst().timezone


class Phase2RecordManager:
    """Phase 2執筆記録の管理・分析を行うクラス"""

    def __init__(self, project_root: str | Path, logger_service=None, console_service=None) -> None:
        self.project_root = Path(project_root)
        from noveler.infrastructure.adapters.path_service_adapter import create_path_service

        path_service = create_path_service(self.project_root)
        self.records_dir = path_service.get_phase2_records_dir()
        self.template_path = Path(__file__).parent.parent.parent / "templates" / "Phase2執筆記録テンプレート.yaml"
        self.records_dir.mkdir(parents=True, exist_ok=True)
        self.logger_service = logger_service
        self.console_service = console_service or console

    def create_new_record(self, episode: str, title: str) -> str:
        """新しいPhase 2記録を作成"""
        with Path(self.template_path).open(encoding="utf-8") as f:
            template_data: dict[str, Any] = yaml.safe_load(f)
        template_data["phase_2_record"]["episode"] = episode
        template_data["phase_2_record"]["title"] = title
        template_data["phase_2_record"]["writing_date"] = project_now().datetime.strftime("%Y-%m-%d")
        safe_episode = re.sub("[^\\w\\-_]", "_", episode)
        filename = f"phase2_record_{safe_episode}.yaml"
        record_path = self.records_dir / filename
        with Path(record_path).open("w", encoding="utf-8") as f:
            yaml.dump(template_data, f, default_flow_style=False, allow_unicode=True, indent=2)
        self.console_service.print(f"新しいPhase 2記録を作成: {record_path}")
        return str(record_path)

    def update_step1_record(self, episode: str, step1_data: dict[str, Any]) -> bool:
        """Step 1の記録を更新"""
        record_path = self._get_record_path(episode)
        if not record_path:
            return False
        with Path(record_path).open(encoding="utf-8") as f:
            record_data: dict[str, Any] = yaml.safe_load(f)
        record_data["phase_2_record"]["step_1_draft"].update(step1_data)
        with Path(record_path).open("w", encoding="utf-8") as f:
            yaml.dump(record_data, f, default_flow_style=False, allow_unicode=True, indent=2)
        self.console_service.print(f"Step 1記録を更新: {record_path}")
        return True

    def update_step2a_record(self, episode: str, step2a_data: dict[str, Any]) -> bool:
        """Step 2Aの記録を更新"""
        record_path = self._get_record_path(episode)
        if not record_path:
            return False
        with Path(record_path).open(encoding="utf-8") as f:
            record_data: dict[str, Any] = yaml.safe_load(f)
        record_data["phase_2_record"]["step_2a_structure_alignment"].update(step2a_data)
        with Path(record_path).open("w", encoding="utf-8") as f:
            yaml.dump(record_data, f, default_flow_style=False, allow_unicode=True, indent=2)
        self.console_service.print(f"Step 2A記録を更新: {record_path}")
        return True

    def update_step2b_record(self, episode: str, step2b_data: dict[str, Any]) -> bool:
        """Step 2Bの記録を更新"""
        record_path = self._get_record_path(episode)
        if not record_path:
            return False
        with Path(record_path).open(encoding="utf-8") as f:
            record_data: dict[str, Any] = yaml.safe_load(f)
        record_data["phase_2_record"]["step_2b_emotional_optimization"].update(step2b_data)
        with Path(record_path).open("w", encoding="utf-8") as f:
            yaml.dump(record_data, f, default_flow_style=False, allow_unicode=True, indent=2)
        self.console_service.print(f"Step 2B記録を更新: {record_path}")
        return True

    def update_step3_record(self, episode: str, step3_data: dict[str, Any]) -> bool:
        """Step 3の記録を更新"""
        record_path = self._get_record_path(episode)
        if not record_path:
            return False
        with Path(record_path).open(encoding="utf-8") as f:
            record_data: dict[str, Any] = yaml.safe_load(f)
        record_data["phase_2_record"]["step_3_final_adjustment"].update(step3_data)
        with Path(record_path).open("w", encoding="utf-8") as f:
            yaml.dump(record_data, f, default_flow_style=False, allow_unicode=True, indent=2)
        self.console_service.print(f"Step 3記録を更新: {record_path}")
        return True

    def update_quality_verification(self, episode: str, quality_data: dict[str, Any]) -> bool:
        """品質検証結果を更新"""
        record_path = self._get_record_path(episode)
        if not record_path:
            return False
        with Path(record_path).open(encoding="utf-8") as f:
            record_data: dict[str, Any] = yaml.safe_load(f)
        record_data["phase_2_record"]["quality_verification"].update(quality_data)
        with Path(record_path).open("w", encoding="utf-8") as f:
            yaml.dump(record_data, f, default_flow_style=False, allow_unicode=True, indent=2)
        self.console_service.print(f"品質検証記録を更新: {record_path}")
        return True

    def update_lessons_learned(self, episode: str, lessons_data: dict[str, Any]) -> bool:
        """学習・改善ポイントを更新"""
        record_path = self._get_record_path(episode)
        if not record_path:
            return False
        with Path(record_path).open(encoding="utf-8") as f:
            record_data: dict[str, Any] = yaml.safe_load(f)
        record_data["phase_2_record"]["lessons_learned"].update(lessons_data)
        with Path(record_path).open("w", encoding="utf-8") as f:
            yaml.dump(record_data, f, default_flow_style=False, allow_unicode=True, indent=2)
        self.console_service.print(f"学習記録を更新: {record_path}")
        return True

    def _get_record_path(self, episode: str) -> Path | None:
        """エピソードの記録ファイルパスを取得"""
        safe_episode = re.sub("[^\\w\\-_]", "_", episode)
        filename = f"phase2_record_{safe_episode}.yaml"
        record_path = self.records_dir / filename
        if record_path.exists():
            return record_path
        self.console_service.print(f"記録ファイルが見つかりません: {episode}")
        return None

    def get_record(self, episode: str) -> dict[str, Any] | None:
        """指定エピソードの記録を取得"""
        record_path = self._get_record_path(episode)
        if not record_path:
            return None
        with Path(record_path).open(encoding="utf-8") as f:
            return yaml.safe_load(f)

    def list_records(self) -> list[str]:
        """すべての記録ファイルを一覧表示"""
        records = []
        for record_file in self.records_dir.glob("phase2_record_*.yaml"):
            match = re.search("phase2_record_(.+)\\.yaml", record_file.name)
            if match:
                episode = match.group(1).replace("_", "第").replace("話", "話")
                records.append(episode)
        return sorted(records)

    def analyze_prompt_effectiveness(self) -> dict[str, Any]:
        """プロンプトの効果分析"""
        analysis = {
            "total_records": 0,
            "effectiveness_distribution": {"very_good": 0, "good": 0, "fair": 0, "poor": 0},
            "successful_patterns": [],
            "improvement_areas": [],
        }
        for record_file in self.records_dir.glob("phase2_record_*.yaml"):
            match = re.search("phase2_record_(.+)\\.yaml", record_file.name)
            episode = match.group(1).replace("_", "第").replace("話", "話") if match else "不明"
            with Path(record_file).open(encoding="utf-8") as f:
                record = yaml.safe_load(f)
            analysis["total_records"] += 1
            step1 = record["phase_2_record"]["step_1_draft"]
            effectiveness = step1.get("prompt_effectiveness", "fair")
            if effectiveness in analysis["effectiveness_distribution"]:
                analysis["effectiveness_distribution"][effectiveness] += 1
            if effectiveness in ["very_good", "good"]:
                prompt_notes = step1.get("prompt_notes", "")
                if prompt_notes:
                    analysis["successful_patterns"].append(
                        {"episode": episode, "effectiveness": effectiveness, "notes": prompt_notes}
                    )
        return analysis

    def analyze_technique_effectiveness(self) -> dict[str, Any]:
        """技法効果の分析(新4ステップ対応)"""
        analysis = {
            "structure_alignment": {"準備完了": 0, "要微調整": 0, "要大幅修正": 0},
            "emotion_conversion": {"very_effective": 0, "effective": 0, "limited": 0, "ineffective": 0},
            "narou_optimization": {"excellent": 0, "good": 0, "fair": 0, "poor": 0},
            "successful_conversions": [],
            "structure_improvements": [],
        }
        for record_file in self.records_dir.glob("phase2_record_*.yaml"):
            match = re.search("phase2_record_(.+)\\.yaml", record_file.name)
            episode = match.group(1).replace("_", "第").replace("話", "話") if match else "不明"
            with Path(record_file).open(encoding="utf-8") as f:
                record = yaml.safe_load(f)
            step2a = record["phase_2_record"].get("step_2a_structure_alignment", {})
            structure_readiness = step2a.get("explanatory_style_assessment", {}).get(
                "ready_for_optimization", "要微調整"
            )
            if structure_readiness in analysis["structure_alignment"]:
                analysis["structure_alignment"][structure_readiness] += 1
            structural_issues = step2a.get("descriptive_writing_quality", {}).get("structural_issues_found", [])
            revision_notes = step2a.get("descriptive_writing_quality", {}).get("revision_notes", "")
            if structural_issues and revision_notes:
                analysis["structure_improvements"].append(
                    {"episode": episode, "issues": structural_issues, "revision_notes": revision_notes}
                )
            step2b = record["phase_2_record"].get("step_2b_emotional_optimization", {})
            emotion_eff = step2b.get("emotion_body_conversion", {}).get("conversion_effectiveness", "effective")
            if emotion_eff in analysis["emotion_conversion"]:
                analysis["emotion_conversion"][emotion_eff] += 1
            narou_eff = (
                step2b.get("optimization_results", {}).get("quality_metrics", {}).get("narou_compatibility", "good")
            )
            if narou_eff in analysis["narou_optimization"]:
                analysis["narou_optimization"][narou_eff] += 1
            conversion_examples = step2b.get("emotion_body_conversion", {}).get("conversion_examples", [])
            for example in conversion_examples:
                if "original" in example and "converted" in example:
                    analysis["successful_conversions"].append(
                        {
                            "episode": episode,
                            "original": example["original"],
                            "converted": example["converted"],
                            "body_sense": example.get("body_sense", ""),
                            "scene_context": example.get("scene_context", ""),
                        }
                    )
        return analysis

    def generate_improvement_report(self) -> str:
        """改善レポートを生成"""
        prompt_analysis = self.analyze_prompt_effectiveness()
        technique_analysis = self.analyze_technique_effectiveness()
        report = f"\n# Phase 2執筆記録 改善レポート\n\n## 分析サマリー\n- 分析対象記録数: {prompt_analysis['total_records']}\n- 生成日時: {project_now().datetime.strftime('%Y-%m-%d %H:%M:%S')}\n\n## プロンプト効果分析\n\n### 効果分布\n"
        for level, count in prompt_analysis["effectiveness_distribution"].items():
            percentage = count / max(1, prompt_analysis["total_records"]) * 100
            report += f"- {level}: {count}件 ({percentage:.1f}%)\n"
        report += "\n### 成功パターン\n"
        for pattern in prompt_analysis["successful_patterns"][:5]:
            report += f"- {pattern['episode']} ({pattern['effectiveness']}): {pattern['notes']}\n"
        report += "\n\n## 技法効果分析(新4ステップ\n)\n### Step 2A: 構造整合性の準備状況\n"
        for level, count in technique_analysis["structure_alignment"].items():
            percentage = count / max(1, prompt_analysis["total_records"]) * 100
            report += f"- {level}: {count}件 ({percentage:.1f}%)\n"
        report += "\n### Step 2B: 感情の身体感覚変換効果\n"
        for level, count in technique_analysis["emotion_conversion"].items():
            percentage = count / max(1, prompt_analysis["total_records"]) * 100
            report += f"- {level}: {count}件 ({percentage:.1f}%)\n"
        report += "\n### なろう最適化効果\n"
        for level, count in technique_analysis["narou_optimization"].items():
            percentage = count / max(1, prompt_analysis["total_records"]) * 100
            report += f"- {level}: {count}件 ({percentage:.1f}%)\n"
        report += "\n### 効果的な変換例\n"
        for example in technique_analysis["successful_conversions"][:3]:
            scene_info = f" ({example['scene_context']})" if example.get("scene_context") else ""
            report += f"- {example['episode']}{scene_info}: 「{example['original']}」→「{example['converted']}」\n"
        report += "\n\n## 改善提案\n\n### プロンプト改善\n- 効果的だった要素を標準プロンプトテンプレートに反映\n- poor評価のパターンを分析して回避策を策定\n\n### 技法改善\n- 身体感覚変換の成功パターンをライブラリ化\n- 効果の低い技法の代替手法を検討\n\n### ワークフロー改善\n- 記録の継続性を高めるための簡略化\n- 分析結果の即時フィードバック機能の追加\n"
        return report

    def export_records_summary(self, output_path: str | Path) -> bool:
        """記録のサマリーをエクスポート"""
        summary = {"export_date": project_now().datetime.isoformat(), "total_records": 0, "records": []}
        for record_file in self.records_dir.glob("phase2_record_*.yaml"):
            with Path(record_file).open(encoding="utf-8") as f:
                record = yaml.safe_load(f)
            phase2 = record["phase_2_record"]
            record_summary = {
                "episode": phase2["episode"],
                "title": phase2["title"],
                "writing_date": phase2["writing_date"],
                "prompt_effectiveness": phase2["step_1_draft"].get("prompt_effectiveness"),
                "emotion_effectiveness": phase2["step_2_style_fusion"]
                .get("emotion_body_conversion", {})
                .get("effectiveness"),
                "overall_satisfaction": phase2["quality_verification"]
                .get("manual_review", {})
                .get("overall_satisfaction"),
                "word_count": phase2["quality_verification"].get("automated_checks", {}).get("word_count"),
            }
            summary["records"].append(record_summary)
            summary["total_records"] += 1
        summary["records"].sort(key=lambda x: x.get("created_at", ""))
        with Path(output_path).open("w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        self.console_service.print(f"記録サマリーをエクスポート: {output_path}")
        return True


def main() -> None:
    """使用例とテスト"""
    from noveler.infrastructure.di.container import resolve_service

    try:
        console = resolve_service("IConsoleService")
    except ValueError:
        from noveler.infrastructure.adapters.console_service_adapter import ConsoleServiceAdapter
        console = ConsoleServiceAdapter()
    if len(sys.argv) < 2:
        console.print("使用方法:")
        console.print("  新規作成: python phase2_record_repository.py create episode_001")
        console.print("  分析: python phase2_record_repository.py analyze")
        console.print("  一覧: python phase2_record_repository.py list")
        return
    command = sys.argv[1]
    if command == "create" and len(sys.argv) >= 5:
        project_root = sys.argv[2]
        episode = sys.argv[3]
        title = sys.argv[4]
        manager = Phase2RecordManager(project_root)
        record_path = manager.create_new_record(episode, title)
        console.print(f"作成完了: {episode} -> {record_path}")
        print(f"作成完了: {episode} -> {record_path}")
    elif command == "analyze" and len(sys.argv) >= 3:
        project_root = sys.argv[2]
        manager = Phase2RecordManager(project_root)
        report = manager.generate_improvement_report()
        console.print(report)
        print(report)
    elif command == "list" and len(sys.argv) >= 3:
        project_root = sys.argv[2]
        manager = Phase2RecordManager(project_root)
        records = manager.list_records()
        console.print("Phase 2記録一覧:")
        print("Phase 2記録一覧:")
        for record in records:
            console.print(f"  - {record}")
            print(f"  - {record}")
    else:
        console.print("無効なコマンドまたは引数が不足しています")


if __name__ == "__main__":
    main()
