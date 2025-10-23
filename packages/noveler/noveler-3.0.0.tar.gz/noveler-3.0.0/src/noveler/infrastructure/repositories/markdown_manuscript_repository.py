"""Markdownマニュスクリプトリポジトリ実装."""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from noveler.domain.repositories.manuscript_repository import ManuscriptRepository
from noveler.domain.value_objects.project_time import project_now


class MarkdownManuscriptRepository(ManuscriptRepository):
    """Markdownファイルベースのマニュスクリプトリポジトリ実装."""

    def __init__(self, manuscript_directory: Path) -> None:
        """初期化.

        Args:
            manuscript_directory: マニュスクリプト格納ディレクトリ
        """
        self.manuscript_directory = manuscript_directory
        self.manuscript_directory.mkdir(parents=True, exist_ok=True)

    def save_manuscript_with_metadata(
        self, manuscript_id: str, content: str, metadata: dict[str, Any] | None = None
    ) -> bool:
        """マニュスクリプトを保存.

        Args:
            manuscript_id: マニュスクリプトID
            content: マニュスクリプト内容
            metadata: メタデータ

        Returns:
            保存成功時True
        """
        try:
            # ファイル名の生成(IDから安全なファイル名を作成)
            safe_filename = self._sanitize_filename(manuscript_id)
            manuscript_file = self.manuscript_directory / f"{safe_filename}.md"

            # フロントマター付きでMarkdownを保存
            full_content = self._create_frontmatter_content(content, metadata or {})

            manuscript_file.write_text(full_content, encoding="utf-8")
            return True

        except Exception:
            return False

    def load_manuscript(self, manuscript_id: str) -> str | None:
        """マニュスクリプトを読み込み.

        Args:
            manuscript_id: マニュスクリプトID

        Returns:
            マニュスクリプト内容、見つからない場合はNone
        """
        try:
            safe_filename = self._sanitize_filename(manuscript_id)
            manuscript_file = self.manuscript_directory / f"{safe_filename}.md"

            if not manuscript_file.exists():
                return None

            content = manuscript_file.read_text(encoding="utf-8")

            # フロントマターを除去してコンテンツのみ返す
            return self._extract_content_from_frontmatter(content)

        except Exception:
            return None

    def get_manuscript_metadata_by_id(self, manuscript_id: str) -> dict[str, Any] | None:
        """マニュスクリプトのメタデータを取得.

        Args:
            manuscript_id: マニュスクリプトID

        Returns:
            メタデータ、見つからない場合はNone
        """
        try:
            safe_filename = self._sanitize_filename(manuscript_id)
            manuscript_file = self.manuscript_directory / f"{safe_filename}.md"

            if not manuscript_file.exists():
                return None

            content = manuscript_file.read_text(encoding="utf-8")
            return self._extract_metadata_from_frontmatter(content)

        except Exception:
            return None

    def list_manuscripts_by_id(self) -> list[str]:
        """マニュスクリプト一覧を取得.

        Returns:
            マニュスクリプトIDのリスト
        """
        try:
            manuscripts = []

            for md_file in self.manuscript_directory.glob("*.md"):
                # ファイル名からIDを復元
                manuscript_id = self._restore_filename(md_file.stem)
                manuscripts.append(manuscript_id)

            return sorted(manuscripts)

        except Exception:
            return []

    def delete_manuscript_by_id(self, manuscript_id: str) -> bool:
        """マニュスクリプトを削除.

        Args:
            manuscript_id: マニュスクリプトID

        Returns:
            削除成功時True
        """
        try:
            safe_filename = self._sanitize_filename(manuscript_id)
            manuscript_file = self.manuscript_directory / f"{safe_filename}.md"

            if manuscript_file.exists():
                manuscript_file.unlink()
                return True

            return False

        except Exception:
            return False

    def update_manuscript_metadata(self, manuscript_id: str, metadata: dict[str, Any]) -> bool:
        """マニュスクリプトのメタデータを更新.

        Args:
            manuscript_id: マニュスクリプトID
            metadata: 新しいメタデータ

        Returns:
            更新成功時True
        """
        try:
            # 既存のコンテンツを取得
            content = self.load_manuscript(manuscript_id)
            if content is None:
                return False

            # メタデータを更新して保存
            return self.save_manuscript_with_metadata(manuscript_id, content, metadata)

        except Exception:
            return False

    def search_manuscripts(self, query: str) -> list[str]:
        """マニュスクリプトを検索.

        Args:
            query: 検索クエリ

        Returns:
            マッチしたマニュスクリプトIDのリスト
        """
        try:
            matched_ids = []

            for manuscript_id in self.list_manuscripts():
                # コンテンツから検索
                content = self.load_manuscript(manuscript_id)
                if content and query.lower() in content.lower():
                    matched_ids.append(manuscript_id)
                    continue

                # メタデータから検索
                metadata = self.get_manuscript_metadata(manuscript_id)
                if metadata:
                    metadata_str = json.dumps(metadata, ensure_ascii=False).lower()
                    if query.lower() in metadata_str:
                        matched_ids.append(manuscript_id)

            return matched_ids

        except Exception:
            return []

    def _sanitize_filename(self, manuscript_id: str) -> str:
        """ファイル名を安全化.

        Args:
            manuscript_id: マニュスクリプトID

        Returns:
            安全化されたファイル名
        """
        # 危険な文字を置換
        safe_name = re.sub(r'[<>:"/\\|?*]', "_", manuscript_id)
        safe_name = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", safe_name)

        # 長すぎる場合は切り詰め
        if len(safe_name) > 200:
            safe_name = safe_name[:200]

        return safe_name

    def _restore_filename(self, filename: str) -> str:
        """ファイル名からIDを復元.

        Args:
            filename: ファイル名

        Returns:
            復元されたID
        """
        # 基本的にはファイル名をそのまま返す
        # より複雑な変換が必要な場合は別途マッピングを保持
        return filename

    def _create_frontmatter_content(self, content: str, metadata: dict[str, Any]) -> str:
        """フロントマター付きコンテンツを作成.

        Args:
            content: マークダウンコンテンツ
            metadata: メタデータ

        Returns:
            フロントマター付きコンテンツ
        """
        if not metadata:
            return content

        # YAMLフロントマターを作成
        #  # Moved to top-level
        frontmatter = yaml.dump(metadata, allow_unicode=True, default_flow_style=False)

        return f"---\n{frontmatter}---\n\n{content}"

    def _extract_content_from_frontmatter(self, full_content: str) -> str:
        """フロントマターからコンテンツを抽出.

        Args:
            full_content: フロントマター付きコンテンツ

        Returns:
            コンテンツ部分のみ
        """
        # YAMLフロントマターのパターンマッチ
        pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
        match = re.match(pattern, full_content, re.DOTALL)

        if match:
            return match.group(2).strip()

        # フロントマターがない場合はそのまま返す
        return full_content

    def _extract_metadata_from_frontmatter(self, full_content: str) -> dict[str, Any]:
        """フロントマターからメタデータを抽出.

        Args:
            full_content: フロントマター付きコンテンツ

        Returns:
            メタデータ
        """
        # YAMLフロントマターのパターンマッチ
        pattern = r"^---\s*\n(.*?)\n---\s*\n"
        match = re.match(pattern, full_content, re.DOTALL)

        if match:
            try:
                # import yaml  # Moved to top-level
                #  # Moved to top-level
                metadata = yaml.safe_load(match.group(1))
                return metadata if isinstance(metadata, dict) else {}
            except Exception:
                return {}

        # フロントマターがない場合は空辞書
        return {}

    # 抽象メソッドの実装(episode_numberベース)
    def get_manuscript(self, episode_number: int) -> str | None:
        """エピソード番号から原稿を取得."""
        return self.load_manuscript(str(episode_number))

    def save_manuscript(self, episode_number: int, content: str) -> bool:
        """エピソード番号で原稿を保存(抽象メソッド実装)."""
        return self.save_manuscript_with_metadata(str(episode_number), content, None)

    def get_manuscript_path(self, episode_number: int) -> Path | None:
        """エピソード番号から原稿ファイルパスを取得."""
        safe_filename = self._sanitize_filename(str(episode_number))
        manuscript_file = self.manuscript_directory / f"{safe_filename}.md"
        return manuscript_file if manuscript_file.exists() else None

    def get_word_count(self, episode_number: int) -> int:
        """エピソード番号から文字数を取得."""
        content = self.get_manuscript(episode_number)
        if content is None:
            return 0
        # 実際の文字をカウント(空白や改行も含む)
        return len(content)

    def get_last_modified(self, episode_number: int) -> datetime | None:
        """エピソード番号から最終更新日時を取得."""
        manuscript_path = self.get_manuscript_path(episode_number)
        if manuscript_path and manuscript_path.exists():
            try:
                stat = manuscript_path.stat()
                return datetime.fromtimestamp(stat.st_mtime, tz=project_now().timezone.timezone)
            except Exception:
                return None
        return None

    def list_manuscripts(self) -> list[int]:
        """エピソード番号の一覧を取得(抽象メソッド実装)."""
        manuscript_ids = self.list_manuscripts_by_id()
        # 数値に変換可能なもののみ返す
        episode_numbers = []
        for manuscript_id in manuscript_ids:
            try:
                episode_number = int(manuscript_id)
                episode_numbers.append(episode_number)
            except ValueError:
                continue
        return sorted(episode_numbers)

    def get_manuscript_metadata(self, episode_number: int) -> dict | None:
        """エピソード番号からメタデータを取得(抽象メソッド実装)."""
        return self.get_manuscript_metadata_by_id(str(episode_number))

    def delete_manuscript(self, episode_number: int) -> bool:
        """原稿を削除(抽象メソッド実装).

        Args:
            episode_number: エピソード番号

        Returns:
            削除成功時True
        """
        return self.delete_manuscript_by_id(str(episode_number))
