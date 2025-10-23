"""Domain.services.chapter_plot_compatibility_service
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

"""章別プロットファイル互換性サービス

新旧両方の命名規則に対応するための互換性レイヤー
- 新形式: chapter01.yaml, chapter02.yaml, ...
- 旧形式: 第1章.yaml, 第2章.yaml, ...
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from noveler.domain.interfaces.path_service import IPathService



class ChapterPlotCompatibilityService:
    """章別プロットファイルの新旧形式互換性を提供"""

    def __init__(self, path_service: IPathService) -> None:
        """初期化

        Args:
            path_service: パスサービス
        """
        self.path_service = path_service
        self.chapter_plot_dir = self.path_service.get_plot_dir() / "章別プロット"

    def get_chapter_plot_path(self, chapter: int) -> Path:
        """章番号から実際のプロットファイルパスを取得

        新形式を優先し、存在しない場合は旧形式を試行

        Args:
            chapter: 章番号

        Returns:
            Path: 実際のプロットファイルパス
        """
        # 新形式を優先
        new_format_path = self.chapter_plot_dir / f"chapter{chapter:02d}.yaml"
        if new_format_path.exists():
            return new_format_path

        # 旧形式にフォールバック
        old_format_path = self.chapter_plot_dir / f"第{chapter}章.yaml"
        if old_format_path.exists():
            return old_format_path

        # どちらも存在しない場合は新形式のパスを返す（新規作成用）
        return new_format_path

    def list_chapter_plot_files(self) -> list[Path]:
        """章別プロットファイルの一覧を取得

        新旧両形式のファイルを統合して返す

        Returns:
            list[Path]: 章別プロットファイルのリスト
        """
        if not self.chapter_plot_dir.exists():
            return []

        # 新形式のファイル
        new_format_files = list(self.chapter_plot_dir.glob("chapter*.yaml"))

        # 旧形式のファイル
        old_format_files = list(self.chapter_plot_dir.glob("第*章.yaml"))

        # 重複を除去（同じ章番号の新旧両形式がある場合は新形式を優先）
        seen_chapters = set()
        result = []

        # 新形式を先に処理
        for file_path in new_format_files:
            if file_path.stem.startswith("chapter"):
                try:
                    chapter_num = int(file_path.stem[7:])  # "chapter" の後の数字を取得
                    seen_chapters.add(chapter_num)
                    result.append(file_path)
                except (ValueError, IndexError):
                    continue

        # 旧形式で新形式にない章のみ追加
        for file_path in old_format_files:
            stem = file_path.stem
            if stem.startswith("第") and stem.endswith("章"):
                try:
                    chapter_num = int(stem[1:-1])  # "第" と "章" の間の数字を取得
                    if chapter_num not in seen_chapters:
                        result.append(file_path)
                except ValueError:
                    continue

        # 章番号順にソート
        return sorted(result, key=self._extract_chapter_number)

    def _extract_chapter_number(self, file_path: Path) -> int:
        """ファイルパスから章番号を抽出

        Args:
            file_path: ファイルパス

        Returns:
            int: 章番号（抽出できない場合は999999）
        """
        stem = file_path.stem

        # 新形式
        if stem.startswith("chapter"):
            try:
                return int(stem[7:])
            except (ValueError, IndexError):
                return 999999

        # 旧形式
        if stem.startswith("第") and stem.endswith("章"):
            try:
                return int(stem[1:-1])
            except ValueError:
                return 999999

        return 999999

    def migrate_to_new_format(self, chapter: int) -> tuple[bool, str]:
        """指定章のファイルを新形式に移行

        Args:
            chapter: 章番号

        Returns:
            tuple[bool, str]: (成功フラグ, メッセージ)
        """
        old_format_path = self.chapter_plot_dir / f"第{chapter}章.yaml"
        new_format_path = self.chapter_plot_dir / f"chapter{chapter:02d}.yaml"

        if not old_format_path.exists():
            return False, f"旧形式ファイルが存在しません: {old_format_path}"

        if new_format_path.exists():
            return False, f"新形式ファイルが既に存在します: {new_format_path}"

        try:
            old_format_path.rename(new_format_path)
            return True, f"移行成功: {old_format_path.name} → {new_format_path.name}"
        except Exception as e:
            return False, f"移行失敗: {e}"

    def migrate_all_to_new_format(self) -> tuple[int, int, list[str]]:
        """全ての章別プロットファイルを新形式に移行

        Returns:
            tuple[int, int, list[str]]: (成功数, 失敗数, エラーメッセージリスト)
        """
        success_count = 0
        failure_count = 0
        error_messages = []

        if not self.chapter_plot_dir.exists():
            return 0, 0, ["章別プロットディレクトリが存在しません"]

        old_format_files = list(self.chapter_plot_dir.glob("第*章.yaml"))

        for file_path in old_format_files:
            stem = file_path.stem
            if stem.startswith("第") and stem.endswith("章"):
                try:
                    chapter_num = int(stem[1:-1])
                    success, message = self.migrate_to_new_format(chapter_num)
                    if success:
                        success_count += 1
                    else:
                        failure_count += 1
                        error_messages.append(message)
                except ValueError as e:
                    failure_count += 1
                    error_messages.append(f"章番号の解析失敗: {file_path.name} - {e}")

        return success_count, failure_count, error_messages
