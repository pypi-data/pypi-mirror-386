#!/usr/bin/env python3
"""強化されたファイル管理システム

スラッシュコマンド統合における自動ディレクトリ作成、
ファイル命名規則、バージョン管理機能を提供
"""

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from noveler.infrastructure.json.file_managers.file_reference_manager import (
    FileReferenceManager,
)
from noveler.infrastructure.json.models.file_reference_models import FileReferenceModel
from noveler.infrastructure.json.utils.hash_utils import calculate_sha256


class EnhancedFileManager(FileReferenceManager):
    """強化されたファイル管理システム"""

    def __init__(self, base_output_dir: Path) -> None:
        super().__init__(base_output_dir)
        self.manuscript_dir = self.base_output_dir.parent / "manuscripts"
        self.quality_reports_dir = self.base_output_dir.parent / "quality_reports"
        self.temp_dir = self.base_output_dir.parent / "temp"

    def ensure_directories(self) -> dict[str, Path]:
        """必要なディレクトリを自動作成"""
        directories = {
            "manuscripts": self.manuscript_dir,
            "quality_reports": self.quality_reports_dir,
            "temp": self.temp_dir,
            "json_output": self.base_output_dir,
        }

        created_dirs = {}
        for name, path in directories.items():
            path.mkdir(parents=True, exist_ok=True)
            created_dirs[name] = path

        return created_dirs

    def save_manuscript_with_metadata(
        self, content: str, episode_number: int, metadata: dict[str, Any] | None = None, backup_existing: bool = True
    ) -> dict[str, Any]:
        """メタデータ付き原稿保存"""
        self.ensure_directories()

        # ファイル名生成
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"{episode_number:03d}_第{episode_number}話_{timestamp}.md"
        manuscript_path = self.manuscript_dir / filename

        # 既存ファイルのバックアップ
        existing_files = []
        if backup_existing:
            pattern = f"{episode_number:03d}_第{episode_number}話_*.md"
            existing_files = list(self.manuscript_dir.glob(pattern))

            for existing_file in existing_files:
                backup_name = f"{existing_file.stem}_backup_{timestamp}{existing_file.suffix}"
                backup_path = self.manuscript_dir / backup_name
                shutil.copy2(existing_file, backup_path)

        # メタデータ準備
        full_metadata = {
            "episode_number": episode_number,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "word_count": self._count_words(content),
            "character_count": len(content),
            "file_name": filename,
            "backed_up_files": len(existing_files),
        }

        if metadata:
            full_metadata.update(metadata)

        # メタデータをMarkdownヘッダーとして追加
        content_with_metadata = self._add_metadata_header(content, full_metadata)

        # ファイル保存
        manuscript_path.write_text(content_with_metadata, encoding="utf-8")

        # ファイル参照生成（JSON変換用）
        file_reference = self.save_content(
            content=content_with_metadata,
            content_type="text/markdown",
            custom_filename=f"manuscript_{episode_number:03d}_{timestamp}.md",
        )

        return {
            "manuscript_path": str(manuscript_path),
            "file_reference": file_reference,
            "metadata": full_metadata,
            "backed_up_files": len(existing_files),
            "size_bytes": manuscript_path.stat().st_size,
        }

    def save_quality_report(
        self, report_data: dict[str, Any], episode_number: int, report_type: str = "quality"
    ) -> dict[str, Any]:
        """品質レポート保存"""
        self.ensure_directories()

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"{report_type}_report_{episode_number:03d}_{timestamp}.json"
        report_path = self.quality_reports_dir / filename

        # レポートデータに追加情報付与
        enhanced_report = {
            "episode_number": episode_number,
            "report_type": report_type,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "report_data": report_data,
        }

        # JSON保存
        with report_path.open("w", encoding="utf-8") as f:
            json.dump(enhanced_report, f, ensure_ascii=False, indent=2)

        # ファイル参照生成
        file_reference = FileReferenceModel(
            path=filename,
            sha256=self._calculate_file_hash(report_path),
            size_bytes=report_path.stat().st_size,
            content_type="application/json",
            created_at=datetime.now(timezone.utc),
        )

        return {
            "report_path": str(report_path),
            "file_reference": file_reference,
            "size_bytes": report_path.stat().st_size,
        }

    def get_manuscript_status(self, episode_number: int | None = None) -> dict[str, Any]:
        """原稿状況取得"""
        if not self.manuscript_dir.exists():
            return {"total_manuscripts": 0, "episodes": [], "latest_episode": None}

        pattern = f"{episode_number:03d}_第{episode_number}話_*.md" if episode_number else "*_第*話_*.md"

        manuscript_files = list(self.manuscript_dir.glob(pattern))
        manuscript_files.sort()

        episodes = []
        for file in manuscript_files:
            try:
                stat = file.stat()
                word_count = self._count_words(file.read_text(encoding="utf-8"))

                # ファイル名から情報抽出
                match = re.match(r"(\d+)_第(\d+)話_(\d+_\d+)\.md", file.name)
                if match:
                    ep_num = int(match.group(2))
                    timestamp = match.group(3)

                    episodes.append(
                        {
                            "episode_number": ep_num,
                            "file_name": file.name,
                            "file_path": str(file),
                            "size_bytes": stat.st_size,
                            "size_kb": stat.st_size / 1024,
                            "word_count": word_count,
                            "created_at": datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc).isoformat(),
                            "modified_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                            "timestamp": timestamp,
                        }
                    )
            except Exception:
                continue

        # エピソード番号でソート
        episodes.sort(key=lambda x: x["episode_number"])

        return {
            "total_manuscripts": len(episodes),
            "episodes": episodes,
            "latest_episode": episodes[-1] if episodes else None,
        }

    def cleanup_old_backups(self, max_backups_per_episode: int = 5) -> list[str]:
        """古いバックアップファイル削除"""
        if not self.manuscript_dir.exists():
            return []

        deleted_files = []
        backup_files = list(self.manuscript_dir.glob("*_backup_*.md"))

        # エピソード番号ごとにグループ化
        episode_backups = {}
        for backup_file in backup_files:
            match = re.match(r"(\d+)_第(\d+)話_.*_backup_.*\.md", backup_file.name)
            if match:
                episode_num = int(match.group(2))
                if episode_num not in episode_backups:
                    episode_backups[episode_num] = []
                episode_backups[episode_num].append(backup_file)

        # 各エピソードで古いバックアップを削除
        for backups in episode_backups.values():
            backups.sort(key=lambda f: f.stat().st_mtime, reverse=True)

            if len(backups) > max_backups_per_episode:
                files_to_delete = backups[max_backups_per_episode:]
                for file_to_delete in files_to_delete:
                    file_to_delete.unlink()
                    deleted_files.append(str(file_to_delete))

        return deleted_files

    def _add_metadata_header(self, content: str, metadata: dict[str, Any]) -> str:
        """Markdownコンテンツにメタデータヘッダー追加"""
        header_lines = ["---"]
        header_lines.append(f"episode: {metadata.get('episode_number', 'unknown')}")
        header_lines.append(f"created: {metadata.get('created_at', '')}")
        header_lines.append(f"words: {metadata.get('word_count', 0)}")
        header_lines.append(f"characters: {metadata.get('character_count', 0)}")

        if "quality_score" in metadata:
            header_lines.append(f"quality_score: {metadata['quality_score']}")

        if "execution_time_seconds" in metadata:
            header_lines.append(f"execution_time: {metadata['execution_time_seconds']}s")

        header_lines.append("---")
        header_lines.append("")

        return "\n".join(header_lines) + content

    def _count_words(self, text: str) -> int:
        """文字数カウント（日本語対応）"""
        # 日本語文字数カウント（空白・記号除く）
        japanese_chars = re.findall(r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]", text)
        # 英数字単語数カウント
        english_words = re.findall(r"[a-zA-Z0-9]+", text)

        return len(japanese_chars) + len(english_words)

    def _calculate_file_hash(self, file_path: Path) -> str:
        """ファイルハッシュ計算（既存機能利用）"""
        return calculate_sha256(file_path)
