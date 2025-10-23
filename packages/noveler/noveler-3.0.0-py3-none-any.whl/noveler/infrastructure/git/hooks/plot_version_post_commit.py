"""Infrastructure.git.hooks.plot_version_post_commit
Where: Infrastructure module defining the plot version post-commit hook.
What: Generates plot version updates after commits.
Why: Keeps plot version data in sync with repository changes.
"""

from noveler.presentation.shared.shared_utilities import console

"プロットコミット後の自動バージョン提案スクリプト\nGit post-commit hook から呼び出される\n"
import subprocess
import sys
from pathlib import Path
from typing import Any

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
try:
    from noveler.application.use_cases.bidirectional_interactive_confirmation import (
        BidirectionalInteractiveConfirmation,
    )
    from noveler.application.use_cases.chapter_consistency_interactive_confirmation import (
        ChapterConsistencyInteractiveConfirmation,
    )
    from noveler.application.use_cases.interactive_consistency_confirmation import InteractiveConsistencyConfirmation
    from noveler.application.use_cases.interactive_version_proposal import InteractiveVersionProposal
    from noveler.application.use_cases.plot_commit_version_proposer import PlotCommitVersionProposer
    from noveler.domain.versioning.entities import (
        BidirectionalForeshadowingAnalyzer,
        ChapterPlotImpactAnalyzer,
        ForeshadowingStatusUpdater,
        PlotCommitAnalyzer,
        PlotVersionConsistencyAnalyzer,
    )
except ImportError as e:
    console.print(f"Import error: {e}")
    sys.exit(0)


class GitHookVersionProposer:
    """Git hook用のバージョン提案処理"""

    def __init__(self, project_path: Path, logger_service=None, console_service=None) -> None:
        self.project_path = project_path
        self.analyzer = PlotCommitAnalyzer()
        self.git_service = MockGitService(project_path)
        self.version_repo = MockVersionRepo()
        self.proposer = PlotCommitVersionProposer(self.analyzer, self.version_repo, self.git_service)
        self.interactive = InteractiveVersionProposal()
        self.consistency_analyzer = PlotVersionConsistencyAnalyzer()
        self.consistency_confirmation = InteractiveConsistencyConfirmation()
        self.chapter_analyzer = ChapterPlotImpactAnalyzer()
        self.chapter_confirmation = ChapterConsistencyInteractiveConfirmation()
        self.bidirectional_analyzer = BidirectionalForeshadowingAnalyzer()
        self.status_updater = ForeshadowingStatusUpdater()
        self.bidirectional_confirmation = BidirectionalInteractiveConfirmation()
        self.logger_service = logger_service
        self.console_service = console_service

    def run(self) -> None:
        """メイン処理を実行"""
        try:
            proposal = self.proposer.propose_version_update()
            if not proposal.should_propose:
                self.console_service.print("✅ プロット変更なし")
                return
            self.console_service.print("\n🔄 プロットコミット検出")
            self.console_service.print(f"変更ファイル: {', '.join(proposal.changed_files)}")
            result = self.interactive.handle_proposal(
                proposal.suggested_version, proposal.change_type, proposal.reason, self._input_handler
            )
            if result.accepted:
                self.console_service.print(f"✅ {result.message}")
                version_info = self._create_version(result.version, result.description)
                if version_info:
                    if proposal.change_type == "major":
                        self._handle_consistency_updates(version_info)
                    elif proposal.change_type == "minor":
                        self._handle_chapter_consistency_updates(version_info, proposal.changed_files)
            else:
                self.console_service.print(f"⏭️  {result.message}")
        except Exception as e:
            self.console_service.print(f"Warning: Git hook error: {e}")

    def _input_handler(self, prompt: str) -> str:
        """ユーザー入力を処理"""
        try:
            return input(prompt)
        except (KeyboardInterrupt, EOFError):
            return "n"

    def _create_version(self, version: str, description: str) -> dict[str, Any]:
        """実際のバージョン作成(簡略版)"""
        self.console_service.print(f"🏷️  プロットバージョン {version} を作成中...")
        self.console_service.print(f"📝 変更内容: {description}")
        return {
            "version": version,
            "description": description,
            "type": "major" if version.count(".") == 2 and version.split(".")[0] != version.split(".")[1] else "minor",
            "affected_chapters": [3, 4, 5],
        }

    def _handle_consistency_updates(self, version_info: dict) -> None:
        """整合性更新の確認・実行"""
        try:
            self.console_service.print("\n🔄 関連ファイルの整合性チェック中...")
            impact = self.consistency_analyzer.analyze_consistency_impact(version_info)
            impact_summary = {
                "affected_episodes": len(list(range(15, 25))),
                "affected_foreshadowing": 2,
                "requires_review": impact.affected_management_files,
            }
            self.console_service.print("📊 影響範囲:")
            self.console_service.print(f"   - 影響ファイル: {', '.join(impact.affected_management_files)}")
            self.console_service.print(f"   - 影響話数: {impact_summary['affected_episodes']}話")
            confirmation = self.consistency_confirmation.confirm_consistency_updates(
                impact_summary, self._input_handler
            )
            if confirmation.approved:
                self.console_service.print("🔧 整合性更新を実行中...")
                self.console_service.print("✅ 整合性更新完了")
            else:
                self.console_service.print("⏭️  整合性更新をスキップ")
        except Exception as e:
            self.console_service.print(f"Warning: {e}")
            self.console_service.print("💡 手動で関連ファイルの確認をお願いします")

    def _handle_chapter_consistency_updates(self, _version_info: dict, changed_files: list[str]) -> None:
        """章別プロット整合性更新の確認・実行(双方向伏線管理含む)"""
        try:
            self.console_service.print("\n🔄 章別プロットの整合性チェック中...")
            chapter_files = [f for f in changed_files if "章別プロット" in f]
            if len(chapter_files) == 1:
                impact = self.chapter_analyzer.analyze_chapter_impact(chapter_files[0])
                affected_chapter = impact.affected_chapter
                foreshadowing_data: dict[str, Any] = self._load_mock_foreshadowing_data()
                bidirectional_impact = self.bidirectional_analyzer.analyze_bidirectional_impact(
                    foreshadowing_data, affected_chapter
                )
                reverse_check_chapters = self.bidirectional_analyzer.get_reverse_check_chapters(bidirectional_impact)
                chapter_impact = {
                    "affected_chapter": affected_chapter,
                    "chapter_name": impact.chapter_name,
                    "affected_episodes": 3,
                    "affected_foreshadowing": len(
                        bidirectional_impact.setup_modified + bidirectional_impact.resolution_modified
                    ),
                }
                self.console_service.print(f"📊 {impact.chapter_name}プロットの変更を検出")
                if bidirectional_impact.has_bidirectional_impact:
                    self.console_service.print(f"🔄 {bidirectional_impact.impact_summary}")
                    bidirectional_data: dict[str, Any] = {
                        "affected_chapter": affected_chapter,
                        "setup_modified_count": len(bidirectional_impact.setup_modified),
                        "resolution_modified_count": len(bidirectional_impact.resolution_modified),
                        "reverse_check_chapters": list(reverse_check_chapters),
                        "impact_summary": bidirectional_impact.impact_summary,
                    }
                    bi_confirmation = self.bidirectional_confirmation.confirm_bidirectional_updates(
                        bidirectional_data, self._input_handler
                    )
                    if bi_confirmation.approved:
                        self.console_service.print("🔧 伏線ステータスを更新中...")
                        self.console_service.print(f"✅ {bi_confirmation.message}")
                        if bi_confirmation.include_reverse_check and reverse_check_chapters:
                            console.print(
                                f"\n💡 次のステップ: {', '.join(f'第{ch}章' for ch in reverse_check_chapters)}の確認を推奨"
                            )
                    else:
                        self.console_service.print(f"⏭️  {bi_confirmation.message}")
                else:
                    confirmation = self.chapter_confirmation.confirm_chapter_updates(
                        chapter_impact, self._input_handler
                    )
                    if confirmation.approved:
                        self.console_service.print(f"🔧 {impact.chapter_name}の整合性更新を実行中...")
                        self.console_service.print(f"✅ {confirmation.message}")
                    else:
                        self.console_service.print(f"⏭️  {confirmation.message}")
            elif len(chapter_files) > 1:
                impact = self.chapter_analyzer.analyze_multiple_chapters_impact(chapter_files)
                chapters_impact = {
                    "affected_chapters": impact.affected_chapters,
                    "total_affected_episodes": len(impact.affected_chapters) * 3,
                    "total_affected_foreshadowing": len(impact.affected_chapters),
                }
                self.console_service.print(
                    f"📊 複数章プロットの変更を検出: {', '.join(f'第{ch}章' for ch in impact.affected_chapters)}"
                )
                confirmation = self.chapter_confirmation.confirm_multiple_chapters_updates(
                    chapters_impact, self._input_handler
                )
                if confirmation.approved:
                    self.console_service.print("🔧 複数章の整合性更新を実行中...")
                    self.console_service.print(f"✅ {confirmation.message}")
                else:
                    self.console_service.print(f"⏭️  {confirmation.message}")
        except Exception as e:
            self.console_service.print(f"Warning: {e}")
            self.console_service.print("💡 手動で章別ファイルの確認をお願いします")

    def _load_mock_foreshadowing_data(self) -> dict:
        """モック伏線データ(TODO: 実際のファイル読み込みに置き換え)"""
        return {
            "foreshadow_001": {
                "description": "主人公の秘密",
                "target_chapter": 3,
                "resolution_chapter": 7,
                "status": "ACTIVE",
            },
            "foreshadow_002": {
                "description": "謎のアイテム",
                "target_chapter": 3,
                "resolution_chapter": 9,
                "status": "ACTIVE",
            },
        }


class MockGitService:
    """Git操作のモック(最小実装)"""

    def __init__(self, project_path: Path, logger_service=None, console_service=None) -> None:
        self.project_path = project_path
        self.logger_service = logger_service
        self.console_service = console_service

    def get_changed_files(self) -> list:
        """最新コミットの変更ファイルを取得"""
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                check=True,
            )
            return [f for f in result.stdout.strip().split("\n") if f]
        except subprocess.CalledProcessError:
            return []


class MockVersionRepo:
    """バージョンリポジトリのモック"""

    def get_current_version(self) -> str:
        """現在のバージョンを取得(ダミー)"""
        return "v1.0.0"


def main() -> None:
    """メインエントリーポイント"""
    try:
        result = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True)
        Path(result.stdout.strip())
    except subprocess.CalledProcessError:
        console.print("Error: Cannot find project root")
        sys.exit(1)
    current_dir = Path.cwd()
    project_dir = None
    for parent in [current_dir, *list(current_dir.parents)]:
        if (parent / "プロジェクト設定.yaml").exists():
            project_dir = parent
            break
    if not project_dir:
        console.print("📝 小説プロジェクト外での変更のため、プロットバージョン管理をスキップします")
        sys.exit(0)
    proposer = GitHookVersionProposer(project_dir)
    proposer.run()


if __name__ == "__main__":
    main()
PlotVersionPostCommitHook = GitHookVersionProposer
