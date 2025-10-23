#!/usr/bin/env python3
"""ファイル参照管理クラス（SPEC-MCP-HASH-001準拠）

Concurrency & durability notes:
- Updates to the in-memory hash index and its persistence file are protected by
  an `RLock` to avoid race conditions when `save_content()` is called from
  multiple threads (as exercised by concurrent tests).
- The index file is now written atomically: content is flushed to a temporary
  file in the same directory and then swapped into place with `os.replace()` to
  prevent partial writes being observed by other threads or file watchers.
"""

import json
import os
import threading
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from noveler.infrastructure.json.models.file_reference_models import FileReferenceModel
from noveler.infrastructure.json.utils.hash_utils import calculate_sha256, verify_hash_format

# B20準拠: 共有コンポーネント利用（必須）
from noveler.presentation.shared.shared_utilities import console, get_logger


class FileReferenceManager:
    """ファイル参照管理クラス（SPEC-MCP-HASH-001準拠）

    B20準拠:
    - 共有コンポーネント利用（console, logger, path_service）
    - 重複実装回避（既存実装拡張）
    - DDD + Clean Architecture準拠
    """

    def __init__(self, base_output_dir: Path) -> None:
        # B20準拠: 統一Logger使用
        self.logger = get_logger(__name__)

        self.base_output_dir = Path(base_output_dir)
        self._ensure_base_directory()

        # SPEC-MCP-HASH-001: ハッシュインデックス管理
        self._hash_index: dict[str, list[Path]] = {}
        self._hash_cache: dict[str, FileReferenceModel] = {}
        self._hash_index_file = self.base_output_dir / ".hash_index.json"
        # Thread-safety: protect index mutations and saves
        self._index_lock = threading.RLock()
        self._load_hash_index()
        self._populate_hash_cache()

        self.logger.debug("FileReferenceManager initialized: %s", self.base_output_dir)

    def _ensure_base_directory(self) -> None:
        """基底ディレクトリ確保"""
        self.base_output_dir.mkdir(parents=True, exist_ok=True)

    def save_content(
        self, content: str, content_type: str, filename_prefix: str = "output", custom_filename: str | None = None
    ) -> FileReferenceModel:
        """コンテンツ保存・ファイル参照生成（SPEC-MCP-HASH-001拡張）"""
        # content_typeを許可された値に制限
        allowed_types = {"text/markdown", "text/yaml", "application/json", "text/plain"}
        if content_type not in allowed_types:
            content_type = "text/plain"  # 未知のタイプはtext/plainとして扱う

        # ファイル名生成
        if custom_filename:
            filename = custom_filename
        else:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            extension = self._get_extension_from_content_type(content_type)
            filename = f"{filename_prefix}_{timestamp}_{unique_id}{extension}"

        # ファイルパス作成
        file_path = self.base_output_dir / filename

        # コンテンツ書き込み
        file_path.write_text(content, encoding="utf-8")

        # SHA256計算
        sha256_hash = calculate_sha256(file_path)

        # ファイルサイズ取得
        size_bytes = file_path.stat().st_size

        # SPEC-MCP-HASH-001: ハッシュインデックス更新（排他制御）
        self._update_hash_index(sha256_hash, file_path)

        # B20準拠: 統一Console使用（pytest実行時は騒がしくしない）
        if not os.getenv("PYTEST_CURRENT_TEST"):
            console.print(f"✅ ファイル保存完了: {filename} ({size_bytes} bytes)", style="green")
        self.logger.info("File saved: %s, hash: %s...", filename, sha256_hash[:16])

        # FileReferenceModel作成（ファイル名のみの相対パス）
        file_reference = FileReferenceModel(
            path=filename,  # ファイル名のみ
            sha256=sha256_hash,
            size_bytes=size_bytes,
            content_type=content_type,
            created_at=datetime.now(timezone.utc),
        )
        self._hash_cache[sha256_hash] = file_reference
        return file_reference

    def verify_file_integrity(self, file_reference: FileReferenceModel) -> bool:
        """ファイル完全性検証"""
        # ファイルパス解決
        file_path = self.base_output_dir / file_reference.path

        if not file_path.exists():
            return False

        # SHA256再計算・比較
        current_hash = calculate_sha256(file_path)
        return current_hash == file_reference.sha256

    def load_file_content(self, file_reference: FileReferenceModel) -> str:
        """ファイル内容読み込み（完全性検証付き）"""

        # ファイルパス解決
        file_path = self.base_output_dir / file_reference.path

        # 完全性チェック
        if not self.verify_file_integrity(file_reference):
            msg = f"ファイル完全性エラー: {file_reference.path}"
            raise ValueError(msg)

        # ファイル読み込み
        return file_path.read_text(encoding=file_reference.encoding)

    def _get_extension_from_content_type(self, content_type: str) -> str:
        """コンテンツタイプから拡張子取得"""
        extension_map = {
            "text/markdown": ".md",
            "text/yaml": ".yaml",
            "application/json": ".json",
            "text/plain": ".txt",
        }
        return extension_map.get(content_type, ".txt")

    def cleanup_old_files(self, max_age_days: int = 30) -> list[str]:
        """古いファイル削除（SPEC-MCP-HASH-001拡張）"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=max_age_days)
        deleted_files = []

        for file_path in self.base_output_dir.rglob("*"):
            if file_path.is_file() and file_path.name != ".hash_index.json":
                file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc)
                if file_mtime < cutoff_date:
                    # SPEC-MCP-HASH-001: ハッシュインデックスからも削除
                    self._remove_from_hash_index(file_path)
                    file_path.unlink()
                    deleted_files.append(str(file_path))

        if deleted_files:
            self._save_hash_index()
            console.print(f"🗑️ 古いファイル削除: {len(deleted_files)}個", style="yellow")

        return deleted_files

    # SPEC-MCP-HASH-001: 新規ハッシュベース機能

    def find_file_by_hash(self, sha256: str) -> FileReferenceModel | None:
        """FR-001: SHA256ハッシュによるファイル検索"""
        # ハッシュ形式検証
        if not verify_hash_format(sha256):
            error_msg = f"Invalid hash format: {sha256}"
            raise ValueError(error_msg)

        self.logger.debug("Searching for file with hash: %s...", sha256[:16])

        cached_ref = self._hash_cache.get(sha256)
        if cached_ref:
            file_path = self.base_output_dir / cached_ref.path
            if file_path.exists():
                return cached_ref
            del self._hash_cache[sha256]

        # ハッシュインデックスから検索（O(1)性能）
        file_paths = self._hash_index.get(sha256, [])

        for file_path in file_paths:
            if file_path.exists():
                file_reference = self._create_file_reference_from_path(file_path, sha256)
                self._hash_cache[sha256] = file_reference
                return file_reference

        self.logger.debug("File not found for hash: %s...", sha256[:16])
        return None

    def get_file_by_hash(self, sha256: str) -> tuple[FileReferenceModel, str] | None:
        """FR-002: ハッシュ指定でのファイル内容取得"""
        file_ref = self.find_file_by_hash(sha256)
        if not file_ref:
            return None

        try:
            content = self.load_file_content(file_ref)
            self.logger.debug("File content loaded: %d chars", len(content))
            return (file_ref, content)
        except Exception:
            self.logger.exception("Failed to load file content")
            raise

    def has_file_changed(self, file_path: Path, previous_hash: str) -> bool:
        """FR-003: ファイル変更検知"""
        if not file_path.exists():
            error_msg = f"File not found: {file_path}"
            raise FileNotFoundError(error_msg)

        current_hash = calculate_sha256(file_path)
        changed = current_hash != previous_hash

        if changed:
            self.logger.debug("File changed detected: %s", file_path.name)

        return changed

    def track_changes(self) -> dict[str, bool]:
        """FR-003: 複数ファイルの変更追跡"""
        changes = {}

        for sha256, file_paths in self._hash_index.items():
            for file_path in file_paths:
                if file_path.exists():
                    try:
                        changed = self.has_file_changed(file_path, sha256)
                        changes[str(file_path)] = changed
                    except Exception:
                        self.logger.exception("Error tracking changes for %s", file_path)
                        changes[str(file_path)] = True  # エラー時は変更ありとして扱う

        return changes

    def list_files_with_hashes(self) -> dict[str, list[str]]:
        """ファイル・ハッシュ一覧取得

        Returns a mapping of file path -> [sha256] for compatibility with tests.
        """
        result: dict[str, list[str]] = {}

        for sha256, file_paths in self._hash_index.items():
            for p in file_paths:
                if p.exists():
                    result[str(p)] = [sha256]

        self.logger.debug("Listed %d files with hashes", len(result))
        return result

    # ハッシュインデックス管理メソッド

    def _build_hash_index(self) -> dict[str, list[Path]]:
        """ハッシュインデックス構築"""
        console.print("🔍 ハッシュインデックス構築中...", style="blue")
        index = {}

        total_files = 0
        for file_path in self.base_output_dir.rglob("*"):
            if file_path.is_file() and file_path.name != ".hash_index.json":
                try:
                    sha256 = calculate_sha256(file_path)
                    if sha256 not in index:
                        index[sha256] = []
                    index[sha256].append(file_path)
                    total_files += 1
                except Exception as e:
                    self.logger.warning("Failed to hash file %s: %s", file_path, e)

        console.print(f"✅ ハッシュインデックス構築完了: {total_files}ファイル", style="green")
        return index

    def _update_hash_index(self, sha256: str, file_path: Path) -> None:
        """ハッシュインデックス更新（排他制御）"""
        with self._index_lock:
            if sha256 not in self._hash_index:
                self._hash_index[sha256] = []

            if file_path not in self._hash_index[sha256]:
                self._hash_index[sha256].append(file_path)

            self._hash_cache[sha256] = self._create_file_reference_from_path(file_path, sha256)

            # インデックス永続化
            self._save_hash_index()

    def _remove_from_hash_index(self, file_path: Path) -> None:
        """ハッシュインデックスからファイル削除（排他制御）"""
        with self._index_lock:
            for sha256, file_paths in list(self._hash_index.items()):
                if file_path in file_paths:
                    file_paths.remove(file_path)
                    if not file_paths:  # 空になったら削除
                        del self._hash_index[sha256]
                        self._hash_cache.pop(sha256, None)
                    else:
                        self._hash_cache[sha256] = self._create_file_reference_from_path(file_paths[0], sha256)
                    break

    def _save_hash_index(self) -> None:
        """ハッシュインデックス永続化（排他制御＋アトミック保存）"""
        try:
            with self._index_lock:
                # Path → str 変換
                serializable_index: dict[str, list[str]] = {}
                for sha256, file_paths in self._hash_index.items():
                    serializable_index[sha256] = [str(p) for p in file_paths]

                index_data = {
                    "version": "1.0.0",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "index": serializable_index,
                }

                tmp_path = self._hash_index_file.with_name(
                    f"{self._hash_index_file.name}.tmp.{uuid.uuid4().hex}"
                )
                tmp_path.write_text(
                    json.dumps(index_data, indent=2, ensure_ascii=False), encoding="utf-8"
                )
                # Atomic replace even on Windows
                os.replace(tmp_path, self._hash_index_file)

                self.logger.debug("Hash index saved: %d entries", len(self._hash_index))

        except Exception:
            self.logger.exception("Failed to save hash index")

    def _load_hash_index(self) -> None:
        """ハッシュインデックス読み込み（排他制御）"""
        with self._index_lock:
            if not self._hash_index_file.exists():
                self.logger.debug("Hash index file not found, building from scratch")
                self._hash_index = self._build_hash_index()
                self._save_hash_index()
                return

            try:
                index_data = json.loads(self._hash_index_file.read_text(encoding="utf-8"))

                # str → Path 変換
                self._hash_index = {}
                for sha256, file_paths in index_data.get("index", {}).items():
                    self._hash_index[sha256] = [Path(p) for p in file_paths]

                self.logger.debug("Hash index loaded: %d entries", len(self._hash_index))

                # 存在しないファイルのクリーンアップ
                self._cleanup_hash_index()

            except Exception as e:
                self.logger.warning("Failed to load hash index, rebuilding: %s", e)
                self._hash_index = self._build_hash_index()
                self._save_hash_index()

    def _populate_hash_cache(self) -> None:
        """Populate in-memory cache for fast hash lookups (guarded)."""
        with self._index_lock:
            self._hash_cache.clear()
            for sha256, file_paths in self._hash_index.items():
                for file_path in file_paths:
                    if file_path.exists():
                        self._hash_cache[sha256] = self._create_file_reference_from_path(file_path, sha256)
                        break

    def _cleanup_hash_index(self) -> None:
        """存在しないファイルをハッシュインデックスから削除（排他制御）"""
        with self._index_lock:
            cleaned = False

            for sha256, file_paths in list(self._hash_index.items()):
                existing_paths = [p for p in file_paths if p.exists()]

                if len(existing_paths) != len(file_paths):
                    if existing_paths:
                        self._hash_index[sha256] = existing_paths
                    else:
                        del self._hash_index[sha256]
                    cleaned = True

            if cleaned:
                self._save_hash_index()
                self.logger.debug("Hash index cleaned up")
                self._populate_hash_cache()

    def _create_file_reference_from_path(self, file_path: Path, sha256: str) -> FileReferenceModel:
        """ファイルパスからFileReferenceModel作成"""
        stat = file_path.stat()

        # ファイル名のみの相対パス
        relative_path = file_path.relative_to(self.base_output_dir)

        # コンテンツタイプ推定
        extension = file_path.suffix.lower()
        content_type_map = {
            ".txt": "text/plain",
            ".md": "text/markdown",
            ".json": "application/json",
            ".yaml": "text/yaml",
            ".yml": "text/yaml",
        }
        content_type = content_type_map.get(extension, "text/plain")

        return FileReferenceModel(
            path=str(relative_path),
            sha256=sha256,
            size_bytes=stat.st_size,
            content_type=content_type,
            created_at=datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc),
        )
