"""成果物チェックサービス"""
import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from noveler.domain.utils.domain_console import console

"成果物確認システム(ハイブリッド方式)\n\n実ファイル確認をベースとし、YAML記録で補完する\n安全性と効率性を両立したアプローチ\n"

from noveler.domain.value_objects.project_time import ProjectTimezone, project_now
from noveler.domain.interfaces.path_service_protocol import get_path_service_manager

# B20準拠: Infrastructure依存をInterface経由に修正済み

JST = ProjectTimezone.jst().timezone


@dataclass
class DeliverableStatus:
    """成果物ステータス"""

    exists: bool
    file_path: Path | None
    last_modified: datetime | None
    size_bytes: int | None
    recorded_in_yaml: bool


class DeliverableChecker:
    """成果物確認システム"""

    def __init__(self, project_root: str) -> None:
        self.project_root = Path(project_root)  # TODO: IPathServiceを使用するように修正
        manager = get_path_service_manager()
        path_service = manager.create_common_path_service(self.project_root)
        self.management_dir = path_service.get_management_dir()
        self.deliverable_record = self.management_dir / "成果物管理.yaml"
        self._path_service = path_service
        # paths computed dynamically; keys kept for compatibility
        self.deliverable_patterns = {
            "plot_outline": "20_プロット/第{episode:03d}話_プロット.yaml",
            "character_sheet": "30_設定集/キャラクター.yaml",
            "world_setting": "30_設定集/世界観.yaml",
            "draft_manuscript": "40_原稿/第{episode:03d}話_*.md",
            "quality_check": "50_管理資料/品質記録.yaml",
            "access_analysis": "50_管理資料/アクセス分析.yaml",
        }

    def check_episode_deliverables(self, episode_num: int) -> dict[str, DeliverableStatus]:
        """指定話数の成果物をチェック

        Args:
            episode_num: 話数

        Returns:
            Dict[str, DeliverableStatus]: 成果物名→ステータス
        """
        results: dict[str, Any] = {}
        yaml_record = self._load_yaml_record()
        for deliverable_name in self.deliverable_patterns.keys():
            file_status = self._check_actual_file(deliverable_name, episode_num)
            yaml_status = self._check_yaml_record(yaml_record, episode_num, deliverable_name)
            results[deliverable_name] = DeliverableStatus(
                exists=file_status["exists"],
                file_path=file_status["file_path"],
                last_modified=file_status["last_modified"],
                size_bytes=file_status["size_bytes"],
                recorded_in_yaml=yaml_status,
            )
        return results

    def _check_actual_file(self, deliverable_name: str, episode_num: int) -> dict[str, Any]:
        """実ファイルの存在確認"""
        ps = self._path_service
        file_path = None
        is_glob = False
        if deliverable_name == "plot_outline":
            try:
                file_path = ps.get_episode_plot_path(episode_num)
            except Exception:
                file_path = None
            if not file_path:
                file_path = ps.get_plots_dir() / f"第{episode_num:03d}話_*.yaml"
                is_glob = True
        elif deliverable_name == "character_sheet":
            try:
                get_char = getattr(ps, "get_character_settings_file", None)
                file_path = get_char() if callable(get_char) else ps.get_settings_dir() / "キャラクター.yaml"
            except Exception:
                file_path = ps.get_settings_dir() / "キャラクター.yaml"
        elif deliverable_name == "world_setting":
            file_path = ps.get_settings_dir() / "世界観.yaml"
        elif deliverable_name == "draft_manuscript":
            file_path = ps.get_manuscript_dir() / f"第{episode_num:03d}話_*.md"
            is_glob = True
        elif deliverable_name == "quality_check":
            try:
                file_path = ps.get_quality_record_file()
            except Exception:
                file_path = ps.get_management_dir() / "品質記録.yaml"
        elif deliverable_name == "access_analysis":
            file_path = ps.get_management_dir() / "アクセス分析.yaml"
        else:
            return {"exists": False, "file_path": None, "last_modified": None, "size_bytes": None}
        # glob handling
        if is_glob or (file_path and "*" in str(file_path)):
            matches = list(file_path.parent.glob(file_path.name))
            if matches:
                latest_file = max(matches, key=lambda p: p.stat().st_mtime)
                file_path = latest_file
            else:
                return {"exists": False, "file_path": None, "last_modified": None, "size_bytes": None}
        if file_path.exists():
            stat = file_path.stat()
            return {
                "exists": True,
                "file_path": file_path,
                "last_modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
                "size_bytes": stat.st_size,
            }
        return {"exists": False, "file_path": None, "last_modified": None, "size_bytes": None}

    def _check_yaml_record(self, yaml_record: dict[str, Any], episode_num: int, deliverable_name: str) -> bool:
        """YAML記録の確認"""
        episode_key = f"episode_{episode_num:03d}"
        if episode_key not in yaml_record:
            return False
        episode_data: dict[str, Any] = yaml_record[episode_key]
        if "deliverables" not in episode_data:
            return False
        return episode_data["deliverables"].get(deliverable_name, False)

    def _load_yaml_record(self) -> dict[str, Any]:
        """YAML記録ファイルの読み込み"""
        if not self.deliverable_record.exists():
            return {}
        try:
            with Path(self.deliverable_record).open(encoding="utf-8") as f:  # TODO: IPathServiceを使用するように修正
                return yaml.safe_load(f) or {}
        except (OSError, yaml.YAMLError, UnicodeDecodeError):
            return {}

    def update_yaml_record(self, episode_num: int, deliverable_statuses: dict[str, DeliverableStatus]) -> None:
        """実ファイル状況をYAML記録に反映

        Args:
            episode_num: 話数
            deliverable_statuses: 成果物ステータス
        """
        yaml_record = self._load_yaml_record()
        episode_key = f"episode_{episode_num:03d}"
        if episode_key not in yaml_record:
            yaml_record[episode_key] = {"deliverables": {}}
        for name, status in deliverable_statuses.items():
            yaml_record[episode_key]["deliverables"][name] = status.exists
        yaml_record[episode_key]["last_checked"] = project_now().datetime.isoformat()
        self.management_dir.mkdir(exist_ok=True)
        with Path(self.deliverable_record).open("w", encoding="utf-8") as f:  # TODO: IPathServiceを使用するように修正
            yaml.dump(yaml_record, f, allow_unicode=True, default_flow_style=False)

    def generate_progress_report(self, max_episodes: int) -> str:
        """進捗レポート生成

        Args:
            max_episodes: チェック対象最大話数

        Returns:
            str: 進捗レポート
        """
        report_lines = ["# 📊 成果物進捗レポート", ""]
        for episode_num in range(1, max_episodes + 1):
            statuses = self.check_episode_deliverables(episode_num)
            existing_deliverables = [name for (name, status) in statuses.items() if status.exists]
            if not existing_deliverables:
                continue
            report_lines.append(f"## 第{episode_num}話")
            for name, status in statuses.items():
                if status.exists:
                    icon = "✅"
                    detail = f"({status.size_bytes} bytes, {status.last_modified.strftime('%Y-%m-%d %H:%M:%S')})"
                else:
                    icon = "❌"
                    detail = ""
                consistency = "🔄" if status.exists != status.recorded_in_yaml else ""
                report_lines.append(f"- {icon} **{name}** {detail} {consistency}")
            report_lines.append("")
        return "\n".join(report_lines)

    def check_prerequisites(self, episode_num: int, required_deliverables: list[str]) -> tuple[bool, list[str]]:
        """前提条件チェック

        Args:
            episode_num: 話数
            required_deliverables: 必要な成果物リスト

        Returns:
            Tuple[bool, list[str]]: (全て満たしているか, 不足している成果物リスト)
        """
        statuses = self.check_episode_deliverables(episode_num)
        missing = [
            required for required in required_deliverables if required not in statuses or not statuses[required].exists
        ]
        return (len(missing) == 0, missing)

    def sync_yaml_with_reality(self, max_episodes: int) -> None:
        """YAML記録を実ファイル状況と同期

        Args:
            max_episodes: 同期対象最大話数
        """
        console.print("🔄 YAML記録を実ファイル状況と同期中...")
        for episode_num in range(1, max_episodes + 1):
            statuses = self.check_episode_deliverables(episode_num)
            if any(status.exists for status in statuses.values()):
                self.update_yaml_record(episode_num, statuses)
        console.print("✅ 同期完了")


def main() -> None:
    """CLI実行用メイン関数"""
    parser = argparse.ArgumentParser(description="成果物確認システム")
    parser.add_argument("--project-root", default=".", help="プロジェクトルート")
    parser.add_argument("--episode", type=int, help="特定話数をチェック")
    parser.add_argument("--report", action="store_true", help="進捗レポート生成")
    parser.add_argument("--sync", action="store_true", help="YAML記録を実ファイルと同期")
    parser.add_argument("--check-prerequisites", nargs="+", help="前提条件チェック")
    args = parser.parse_args()
    checker = DeliverableChecker(Path(args.project_root))  # TODO: IPathServiceを使用するように修正
    if args.sync:
        checker.sync_yaml_with_reality()
    elif args.report:
        report = checker.generate_progress_report()
        console.print(report)
    elif args.episode:
        if args.check_prerequisites:
            (all_satisfied, missing) = checker.check_prerequisites(args.episode, args.check_prerequisites)
            if all_satisfied:
                console.print(f"✅ 第{args.episode:03d}話の前提条件満足済み")
            else:
                console.print(f"❌ 第{args.episode:03d}話の前提条件不足: {', '.join(missing)}")
        else:
            statuses = checker.check_episode_deliverables(args.episode)
            console.print(f"📋 第{args.episode:03d}話の成果物状況")
            for name, status in statuses.items():
                icon = "✅" if status.exists else "❌"
                console.print(f"  {icon} {name}")


if __name__ == "__main__":
    main()
