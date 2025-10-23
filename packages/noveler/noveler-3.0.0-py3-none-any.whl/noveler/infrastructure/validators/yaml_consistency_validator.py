"""Infrastructure.validators.yaml_consistency_validator
Where: Infrastructure validator checking YAML consistency.
What: Scans YAML documents for structural issues and reports problems.
Why: Helps maintain reliable YAML configuration and data files.
"""

from noveler.presentation.shared.shared_utilities import console

"YAML一貫性検証スクリプト\n話数管理.yamlと執筆進捗管理.yamlの整合性をチェック\n\n使用方法:\n    python3 validate_yaml_consistency.py [--project プロジェクト名]\n"
import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

from noveler.domain.value_objects.project_time import ProjectTimezone, project_now
from noveler.infrastructure.adapters.console_service_adapter import ConsoleServiceAdapter

sys.path.append(str(Path(__file__).resolve().parent.parent))
from noveler.infrastructure.adapters.path_service_adapter import create_path_service
from noveler.infrastructure.logging.logger import log_error, log_result, log_step, setup_logger

logger = setup_logger("validate_yaml_consistency")
JST = ProjectTimezone.jst().timezone


class YAMLConsistencyValidator:
    def __init__(self, project_dir: Path | str, logger_service=None, console_service=None) -> None:
        self.project_dir = Path(project_dir)

        path_service = create_path_service(self.project_dir)
        self.management_dir = path_service.get_management_dir()
        logger_service = logger_service
        console_service = console_service

    def validate_consistency(self) -> bool:
        """YAML一貫性検証の実行"""
        log_step(logger, "validate_consistency", f"Starting validation for {self.project_dir.name}")
        self.console_service.print(f"=== {self.project_dir.name} YAML整合性check ===")
        episode_file = self.management_dir / "話数管理.yaml"
        progress_file = self.management_dir / "執筆進捗管理.yaml"
        if not episode_file.exists():
            self.console_service.print(f"❌ 話数管理.yamlが見つかりません: {episode_file}")
            log_error(logger, "validate_consistency", FileNotFoundError(f"話数管理.yaml not found: {episode_file}"))
            return False
        if not progress_file.exists():
            self.console_service.print(f"❌ 執筆進捗管理.yamlが見つかりません: {progress_file}")
            log_error(
                logger, "validate_consistency", FileNotFoundError(f"執筆進捗管理.yaml not found: {progress_file}")
            )
            return False
        derived_stats = self._derive_statistics_from_episodes(episode_file)
        if not derived_stats:
            self.console_service.print("❌ 話数管理.yamlから統計を導出できませんでした")
            return False
        current_stats = self._get_current_progress_stats(progress_file)
        if not current_stats:
            self.console_service.print("❌ 執筆進捗管理.yamlから現在の統計を取得できませんでした")
            return False
        return self._check_consistency(derived_stats, current_stats)

    def _derive_statistics_from_episodes(self, episode_file: Path) -> dict[str, Any] | None:
        """話数管理.yamlから統計を導出"""
        try:
            with Path(episode_file).open(encoding="utf-8") as f:
                episode_data: dict[str, Any] = yaml.safe_load(f)
            if not episode_data:
                return None
            episodes = episode_data.get("episodes", {})
            all_episodes = episode_data.get("all_episodes", {})
            all_episode_data: dict[str, Any] = {**episodes, **all_episodes}
            total_count = len(all_episode_data)
            completed_count = sum(
                1 for ep in all_episode_data.values() if isinstance(ep, dict) and ep.get("status") == "completed"
            )
            metadata_total = episode_data.get("metadata", {}).get("total_episodes")
            if metadata_total and isinstance(metadata_total, int):
                total_count = metadata_total
            completion_rate = f"{completed_count / total_count * 100:.1f}%" if total_count > 0 else "0.0%"
            return {
                "completed_episodes": completed_count,
                "total_episodes": total_count,
                "completion_rate": completion_rate,
            }
        except (yaml.YAMLError, FileNotFoundError, KeyError) as e:
            self.console_service.print(f"❌ 話数管理.yaml読み込みエラー: {e}")
            return None

    def _get_current_progress_stats(self, progress_file: Path) -> dict[str, Any] | None:
        """執筆進捗管理.yamlから現在の統計を取得"""
        try:
            with Path(progress_file).open(encoding="utf-8") as f:
                progress_data: dict[str, Any] = yaml.safe_load(f)
            if not progress_data:
                return None
            project_progress = progress_data.get("project_progress", {})
            return {
                "completed_episodes": project_progress.get("completed_episodes", 0),
                "total_target": project_progress.get("total_target", 0),
                "completion_rate": project_progress.get("completion_rate", "0%"),
                "current_date": project_progress.get("current_date", "未設定"),
            }
        except (yaml.YAMLError, FileNotFoundError, KeyError) as e:
            self.console_service.print(f"❌ 執筆進捗管理.yaml読み込みエラー: {e}")
            log_error(logger, "_get_current_progress_stats", e)
            return None

    def _check_consistency(self, derived_stats: dict[str, Any] | None, current_stats: dict[str, Any] | None) -> bool:
        """整合性チェック"""
        log_step(logger, "_check_consistency", "Starting consistency check")
        all_consistent = True
        self.console_service.print("\n【整合性チェック結果】")
        if derived_stats["completed_episodes"] != current_stats["completed_episodes"]:
            self.console_service.print("❌ 完了話数が不一致")
            self.console_service.print(f"   話数管理.yamlから導出: {derived_stats['completed_episodes']}")
            self.console_service.print(f"   執筆進捗管理.yaml: {current_stats['completed_episodes']}")
            all_consistent = False
        else:
            self.console_service.print(f"✅ 完了話数: {derived_stats['completed_episodes']}")
        if derived_stats["total_episodes"] != current_stats["total_target"]:
            self.console_service.print("⚠️  総話数が不一致")
            self.console_service.print(f"   話数管理.yamlから導出: {derived_stats['total_episodes']}")
            self.console_service.print(f"   執筆進捗管理.yaml: {current_stats['total_target']}")
            self.console_service.print("   (total_targetと話数管理の実際の話数の違いは許容範囲の場合があります)")
        else:
            self.console_service.print(f"✅ 総話数: {derived_stats['total_episodes']}")
        derived_rate = derived_stats["completion_rate"].rstrip("%")
        current_rate = current_stats["completion_rate"].rstrip("%")
        try:
            derived_float = float(derived_rate)
            current_float = float(current_rate)
            if abs(derived_float - current_float) > 0.1:
                self.console_service.print("❌ 完了率が不一致")
                self.console_service.print(f"   話数管理.yamlから導出: {derived_stats['completion_rate']}")
                self.console_service.print(f"   執筆進捗管理.yaml: {current_stats['completion_rate']}")
                all_consistent = False
            else:
                self.console_service.print(f"✅ 完了率: {derived_stats['completion_rate']}")
        except ValueError:
            if derived_stats["completion_rate"] != current_stats["completion_rate"]:
                self.console_service.print("❌ 完了率が不一致")
                self.console_service.print(f"   話数管理.yamlから導出: {derived_stats['completion_rate']}")
                self.console_service.print(f"   執筆進捗管理.yaml: {current_stats['completion_rate']}")
                all_consistent = False
            else:
                self.console_service.print(f"✅ 完了率: {derived_stats['completion_rate']}")
        today = project_now().datetime.strftime("%Y-%m-%d")
        if current_stats["current_date"] != today:
            self.console_service.print("⚠️  更新日付が古い可能性があります")
            self.console_service.print(f"   執筆進捗管理.yaml: {current_stats['current_date']}")
            self.console_service.print(f"   今日の日付: {today}")
        else:
            self.console_service.print(f"✅ 更新日付: {current_stats['current_date']}")
        if all_consistent:
            self.console_service.print("\n🎉 すべての重要な統計が一致しています!")
            return True
        self.console_service.print("\n❌ 整合性の問題が見つかりました。")
        self.console_service.print("\n【修正方法】")
        self.console_service.print("以下のコマンドで自動修正できます:")
        self.console_service.print(f"python3 {Path(__file__).parent}/complete_episode.py --fix-consistency")
        return False


def auto_detect_project() -> None:
    """プロジェクトディレクトリを自動検出"""
    from noveler.infrastructure.di.container import resolve_service

    try:
        resolve_service("IConsoleService")
    except ValueError:
        ConsoleServiceAdapter()
    script_dir = Path(__file__).parent
    scripts_dir = script_dir.parent
    guide_dir = scripts_dir.parent
    novel_base_dir = guide_dir.parent
    exclude_dirs = {"00_ガイド", "90_アーカイブ"}
    project_dirs = sorted([d for d in novel_base_dir.iterdir() if d.is_dir() and d.name not in exclude_dirs])
    if len(project_dirs) == 0:
        return None
    if len(project_dirs) == 1:
        return str(project_dirs[0])
    console.print("複数のプロジェクトが見つかりました:")
    for i, project_dir in enumerate(project_dirs, 1):
        console.print(f"  {i}. {project_dir.name}")
    try:
        choice = int(input(f"プロジェクトを選択してください (1-{len(project_dirs)}): "))
        if 1 <= choice <= len(project_dirs):
            return str(project_dirs[choice - 1])
        console.print("エラー: 無効な選択です")
        return None
    except (ValueError, KeyboardInterrupt):
        console.print("エラー: 操作がキャンセルされました")
        return None


def main() -> None:
    log_step(logger, "main", "Starting YAML consistency validation")
    from noveler.infrastructure.di.container import resolve_service

    try:
        resolve_service("IConsoleService")
    except ValueError:
        ConsoleServiceAdapter()
    parser = argparse.ArgumentParser(description="YAML一貫性検証")
    parser.add_argument("--project", help="プロジェクトディレクトリ(指定しない場合は自動検出)")
    args = parser.parse_args()
    if args.project:
        project_dir = args.project
    else:
        project_dir = auto_detect_project()
        if not project_dir:
            console.print("エラー: プロジェクトを自動検出できませんでした")
            console.print("--project オプションでプロジェクトディレクトリを指定してください")
            sys.exit(1)
        console.print(f"自動検出されたプロジェクト: {Path(project_dir).name}")
    if not Path(project_dir).exists():
        console.print(f"エラー: プロジェクトディレクトリが存在しません: {project_dir}")
        sys.exit(1)
    validator = YAMLConsistencyValidator(project_dir)
    is_consistent = validator.validate_consistency()
    if is_consistent:
        log_result(logger, "main", "Validation completed successfully")
    else:
        log_result(logger, "main", "Validation completed with errors")
    sys.exit(0 if is_consistent else 1)


if __name__ == "__main__":
    main()
