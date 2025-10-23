"""Tools.prompt_validation_tool
Where: Tool validating prompts for quality and constraints.
What: Runs prompt validation logic and reports issues to users.
Why: Ensures generated prompts meet defined quality standards.
"""

import argparse
import json
import os
import statistics
import sys
from pathlib import Path
from typing import Any

from noveler.presentation.shared.shared_utilities import console

"\nプロンプト品質検証ツール\n\nSPEC-PROMPT-SAVE-001: プロンプト保存機能仕様書準拠\nデプロイ後の品質監視・検証用ツール\n"

from noveler.domain.entities.episode_prompt import EpisodePrompt
from noveler.infrastructure.repositories.episode_prompt_repository import EpisodePromptRepository
from noveler.presentation.shared.shared_utilities import get_common_path_service


class PromptValidationReport:
    """プロンプト品質検証レポート"""

    def __init__(self, logger_service: Any | None = None, console_service: Any | None = None) -> None:
        self.total_prompts: int = 0
        self.quality_scores: list[float] = []
        self.file_sizes: list[int] = []
        self.validation_errors: list[str] = []
        self.naming_violations: list[str] = []
        self.high_quality_count: int = 0
        self.logger_service = logger_service
        self.console_service = console_service

    def add_prompt_result(self, prompt: EpisodePrompt, file_path: Path, quality_score: float) -> None:
        """プロンプト検証結果追加"""
        self.total_prompts += 1
        self.quality_scores.append(quality_score)
        if file_path.exists():
            self.file_sizes.append(file_path.stat().st_size)
        if quality_score >= 0.8:
            self.high_quality_count += 1

    def add_validation_error(self, error: str) -> None:
        """検証エラー追加"""
        self.validation_errors.append(error)

    def add_naming_violation(self, violation: str) -> None:
        """命名規則違反追加"""
        self.naming_violations.append(violation)

    def generate_summary(self) -> str:
        """検証サマリー生成"""
        if not self.quality_scores:
            return "❌ 検証対象のプロンプトが見つかりませんでした"
        avg_quality = statistics.mean(self.quality_scores)
        avg_file_size = statistics.mean(self.file_sizes) if self.file_sizes else 0
        high_quality_rate = self.high_quality_count / self.total_prompts * 100
        summary = f"\n🔍 プロンプト品質検証結果\n\n📊 基本統計:\n  - 総プロンプト数: {self.total_prompts}\n  - 平均品質スコア: {avg_quality:.3f}\n  - 高品質率(≥0.8): {high_quality_rate:.1f}% ({self.high_quality_count}/{self.total_prompts})\n  - 平均ファイルサイズ: {avg_file_size:,.0f} bytes\n\n🎯 品質分析:\n  - 最高品質: {max(self.quality_scores):.3f}\n  - 最低品質: {min(self.quality_scores):.3f}\n  - 品質標準偏差: {statistics.stdev(self.quality_scores):.3f}\n\n{('✅ 品質目標達成' if avg_quality >= 0.8 else '⚠️ 品質改善が必要')}\n"
        if self.validation_errors:
            summary += f"\n❌ 検証エラー ({len(self.validation_errors)}件):\n"
            for error in self.validation_errors[:5]:
                summary += f"  - {error}\n"
        if self.naming_violations:
            summary += f"\n⚠️ 命名規則違反 ({len(self.naming_violations)}件):\n"
            for violation in self.naming_violations[:5]:
                summary += f"  - {violation}\n"
        return summary


class PromptValidationTool:
    """プロンプト品質検証ツール"""

    def __init__(
        self, project_root: Path | None = None, logger_service: Any | None = None, console_service: Any | None = None
    ) -> None:
        """ツール初期化"""

        self.project_root = project_root or self._get_project_root()
        self.path_service = get_common_path_service(self.project_root)
        self.repository = EpisodePromptRepository()

        self.prompt_dir = self.path_service.get_prompts_dir() / "話別プロット"
        self.logger_service = logger_service
        self.console_service = console_service

    def validate_all_prompts(self) -> PromptValidationReport:
        """全プロンプトの品質検証"""
        report = PromptValidationReport()
        if not self.prompt_dir.exists():
            report.add_validation_error(f"プロンプトディレクトリが存在しません: {self.prompt_dir}")
            return report
        prompt_files = self.repository.list_prompts(self.prompt_dir)
        for file_path in prompt_files:
            try:
                prompt = self.repository.load_prompt(file_path)
                if not prompt:
                    report.add_validation_error(f"プロンプト読み込み失敗: {file_path.name}")
                    continue
                quality_score = self._validate_prompt_quality(prompt, file_path, report)
                self._validate_file_naming(prompt, file_path, report)
                report.add_prompt_result(prompt, file_path, quality_score)
            except Exception as e:
                report.add_validation_error(f"プロンプト検証エラー {file_path.name}: {e!s}")
        return report

    def _validate_prompt_quality(self, prompt: EpisodePrompt, file_path: Path, report: PromptValidationReport) -> float:
        """プロンプト品質検証"""
        quality_score = prompt.get_content_quality_score()
        if len(prompt.prompt_content) < 1000:
            report.add_validation_error(f"{file_path.name}: プロンプト長さ不足 ({len(prompt.prompt_content)}文字)")
        if len(prompt.content_sections) < 3:
            report.add_validation_error(
                f"{file_path.name}: コンテンツセクション不足 ({len(prompt.content_sections)}個)"
            )
        yaml_content = prompt.get_yaml_content()
        metadata = yaml_content.get("metadata", {})
        required_metadata = ["spec_id", "episode_number", "title", "generation_timestamp"]
        for field in required_metadata:
            if field not in metadata:
                report.add_validation_error(f"{file_path.name}: 必須メタデータ不足 - {field}")
        return quality_score

    def _validate_file_naming(self, prompt: EpisodePrompt, file_path: Path, report: PromptValidationReport) -> None:
        """ファイル命名規則検証"""
        try:
            expected_filename = prompt.get_file_name().to_filename()
            if file_path.name != expected_filename:
                report.add_naming_violation(f"ファイル名不一致: 実際={file_path.name}, 期待={expected_filename}")
        except Exception as e:
            report.add_validation_error(f"ファイル名検証エラー {file_path.name}: {e!s}")

    def analyze_quality_trends(self) -> dict[str, Any]:
        """品質トレンド分析"""
        prompt_files = self.repository.list_prompts(self.prompt_dir)
        quality_by_episode = {}
        size_by_episode = {}
        for file_path in prompt_files:
            prompt = self.repository.load_prompt(file_path)
            if prompt:
                episode_num = prompt.episode_number
                quality_score = prompt.get_content_quality_score()
                file_size = file_path.stat().st_size if file_path.exists() else 0
                quality_by_episode[episode_num] = quality_score
                size_by_episode[episode_num] = file_size
        return {
            "quality_by_episode": quality_by_episode,
            "size_by_episode": size_by_episode,
            "episode_count": len(quality_by_episode),
            "quality_trend": "improving" if self._is_improving_trend(quality_by_episode) else "stable",
        }

    def _is_improving_trend(self, quality_by_episode: dict[int, float]) -> bool:
        """品質改善トレンド判定"""
        if len(quality_by_episode) < 3:
            return False
        sorted_episodes = sorted(quality_by_episode.items())
        recent_scores = [score for (_, score) in sorted_episodes[-3:]]
        early_scores = [score for (_, score) in sorted_episodes[:3]]
        return statistics.mean(recent_scores) > statistics.mean(early_scores)

    def _get_project_root(self) -> Path:
        """プロジェクトルート取得"""

        env_project_root = os.environ.get("PROJECT_ROOT")
        if env_project_root:
            return Path(env_project_root)
        return Path.cwd()


def main() -> None:
    """メイン実行関数"""
    from noveler.infrastructure.adapters.console_service_adapter import get_console_service  # noqa: PLC0415

    parser = argparse.ArgumentParser(description="プロンプト品質検証ツール")
    parser.add_argument("--project-root", type=Path, help="プロジェクトルートパス（省略時は環境変数PROJECT_ROOT使用）")
    parser.add_argument("--detailed", action="store_true", help="詳細な分析結果を表示")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="出力形式")
    args = parser.parse_args()
    get_console_service()
    try:
        tool = PromptValidationTool(project_root=args.project_root)
        report = tool.validate_all_prompts()
        if args.format == "json":

            result = {
                "total_prompts": report.total_prompts,
                "average_quality": statistics.mean(report.quality_scores) if report.quality_scores else 0,
                "high_quality_count": report.high_quality_count,
                "validation_errors": report.validation_errors,
                "naming_violations": report.naming_violations,
            }
            console.print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            console.print(report.generate_summary())
            if args.detailed:
                trends = tool.analyze_quality_trends()
                console.print("\n📈 品質トレンド分析:")
                console.print(f"  - エピソード数: {trends['episode_count']}")
                console.print(f"  - 品質傾向: {trends['quality_trend']}")
    except Exception as e:
        console.print(f"❌ 検証ツール実行エラー: {e!s}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
