# File: src/noveler/domain/services/artifact_store_service.py
# Purpose: Provide hash-indexed storage and retrieval for MCP artifacts.
# Context: Used by MCP JSON conversion server and tool registry to persist references.

"""アーティファクトストアサービス

MCPシステム用の参照渡し（Pass-by-Reference）実装。
コンテンツをSHA256ハッシュで管理し、軽量な参照IDでアクセス。
"""

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from noveler.domain.interfaces.logger_service_protocol import ILoggerService


@dataclass
class ArtifactMetadata:
    """アーティファクトメタデータ"""
    artifact_id: str
    content_type: str
    created_at: str
    size_bytes: int
    source_file: str | None = None
    description: str | None = None
    tags: dict[str, str] | None = None


@dataclass
class StoredArtifact:
    """ストア済みアーティファクト"""
    content: str
    metadata: ArtifactMetadata



class ArtifactCatalog:
    """アーティファクトの一覧を多用途に扱うコンテナ。"""

    def __init__(self, metadata_map: dict[str, ArtifactMetadata]):
        self._metadata_map = dict(metadata_map)
        self._records = [asdict(meta) for meta in self._metadata_map.values()]

    def __iter__(self) -> Iterator[dict[str, Any]]:
        return iter(self._records)

    def __len__(self) -> int:
        return len(self._records)

    def __getitem__(self, key: int | slice | str):
        if isinstance(key, str):
            return self._metadata_map[key]
        return self._records[key]

    def __contains__(self, item: object) -> bool:
        if isinstance(item, str):
            return item in self._metadata_map
        return item in self._records

    def keys(self):
        """アーティファクトIDのビューを返す。"""
        return self._metadata_map.keys()

    def values(self):
        """メタデータのビューを返す。"""
        return self._metadata_map.values()

    def items(self):
        """(artifact_id, metadata) ペアを返す。"""
        return self._metadata_map.items()

    def as_list(self) -> list[dict[str, Any]]:
        """辞書形式のレコード一覧を返す。"""
        return list(self._records)

    def as_dict(self) -> dict[str, ArtifactMetadata]:
        """IDをキーとするメタデータ辞書を返す。"""
        return dict(self._metadata_map)


class ArtifactStoreService:
    """アーティファクトストアサービス

    責務:
    - コンテンツのSHA256ハッシュベース管理
    - 参照ID生成と解決
    - メモリ＋永続化ストレージ
    - セクション指定による部分取得
    """

    def __init__(
        self,
        logger_service: ILoggerService | None = None,
        storage_dir: Path | None = None
    ) -> None:
        """アーティファクトストア初期化

        Args:
            logger_service: ロガーサービス
            storage_dir: 永続化ストレージディレクトリ
        """
        # DDD準拠: 遅延importで統一ロガーへ委譲（フォールバックなし）
        if logger_service is not None:
            self._logger = logger_service
        else:
            from noveler.domain.interfaces.logger_service import NullLoggerService  # type: ignore
            self._logger = NullLoggerService()
        self._storage_dir = storage_dir or Path.cwd() / ".noveler" / "artifacts"

        # メモリキャッシュ
        self._memory_cache: dict[str, StoredArtifact] = {}

        # ストレージディレクトリの作成
        self._storage_dir.mkdir(parents=True, exist_ok=True)

        try:
            self._logger.info("ArtifactStoreService initialized")
        except Exception:
            pass

    def store(
        self,
        content: str,
        content_type: str = "text",
        source_file: str | None = None,
        description: str | None = None,
        tags: dict[str, str] | None = None
    ) -> str:
        """コンテンツをアーティファクトとしてストア

        Args:
            content: ストアするコンテンツ
            content_type: コンテンツタイプ（text, json, yaml等）
            source_file: ソースファイル名（オプション）
            description: 説明（オプション）
            tags: タグ情報（オプション）

        Returns:
            artifact:abc123形式の参照ID
        """
        # SHA256ハッシュ生成
        content_bytes = content.encode("utf-8")
        sha256_hash = hashlib.sha256(content_bytes).hexdigest()
        artifact_id = f"artifact:{sha256_hash[:12]}"

        # メタデータ作成
        metadata = ArtifactMetadata(
            artifact_id=artifact_id,
            content_type=content_type,
            created_at=datetime.now(tz=timezone.utc).isoformat(),
            size_bytes=len(content_bytes),
            source_file=source_file,
            description=description,
            tags=tags or {}
        )

        # アーティファクト作成
        artifact = StoredArtifact(
            content=content,
            metadata=metadata
        )

        # メモリキャッシュに保存
        self._memory_cache[artifact_id] = artifact

        # 永続化ストレージに保存
        self._save_to_storage(artifact_id, artifact)

        if self._logger:
            self._logger.info(f"Artifact stored: {artifact_id} ({len(content_bytes)} bytes)")

        # Domain層ではUI出力を行わない
        return artifact_id

    def fetch(
        self,
        artifact_id: str,
        section: str | None = None
    ) -> str | None:
        """アーティファクト参照IDからコンテンツを取得

        Args:
            artifact_id: artifact:abc123形式の参照ID
            section: 部分取得セクション名（オプション）

        Returns:
            コンテンツ、または見つからない場合None
        """
        # 正規化
        normalized_id = self._normalize_artifact_id(artifact_id)

        # メモリキャッシュから検索
        artifact = self._memory_cache.get(normalized_id)

        # ストレージから読み込み
        if not artifact:
            artifact = self._load_from_storage(normalized_id)
            if artifact:
                self._memory_cache[normalized_id] = artifact

        if not artifact:
            if self._logger:
                self._logger.warning(f"Artifact not found: {artifact_id}")
            return None

        content = artifact.content

        # セクション指定がある場合は部分取得
        if section:
            content = self._extract_section(content, section, artifact.metadata.content_type)

        if self._logger:
            self._logger.debug(f"Artifact fetched: {artifact_id} (section: {section})")

        return content

    def get_metadata(self, artifact_id: str) -> ArtifactMetadata | None:
        """アーティファクトのメタデータを取得

        Args:
            artifact_id: artifact:abc123形式の参照ID

        Returns:
            メタデータ、または見つからない場合None
        """
        normalized_id = self._normalize_artifact_id(artifact_id)

        artifact = self._memory_cache.get(normalized_id)
        if not artifact:
            artifact = self._load_from_storage(normalized_id)

        return artifact.metadata if artifact else None

    def list_artifacts(self, tags: dict[str, str] | None = None) -> ArtifactCatalog:
        """保存されているアーティファクト一覧を取得。

        Args:
            tags: フィルタリング用のタグ（オプション）

        Returns:
            ``ArtifactCatalog`` コンテナ。
            - イテレーションすると ``dict`` 形式のレコードを返す（integration用）。
            - ``[artifact_id]`` で ``ArtifactMetadata`` を取得できる（既存API互換）。
        """
        artifacts: dict[str, ArtifactMetadata] = {}

        # メモリキャッシュから優先的に取得
        for artifact_id, artifact in self._memory_cache.items():
            if self._matches_tags(artifact.metadata, tags):
                artifacts[artifact_id] = artifact.metadata

        # ストレージからの読み込み（メモリにないもの）
        for artifact_file in sorted(self._storage_dir.glob("*.json")):
            artifact_id = f"artifact:{artifact_file.stem}"
            if artifact_id not in artifacts:
                artifact = self._load_from_storage(artifact_id)
                if artifact and self._matches_tags(artifact.metadata, tags):
                    artifacts[artifact_id] = artifact.metadata

        return ArtifactCatalog(artifacts)

    def _matches_tags(self, metadata: ArtifactMetadata, filter_tags: dict[str, str] | None) -> bool:
        """メタデータがフィルタータグに一致するか確認

        Args:
            metadata: アーティファクトのメタデータ
            filter_tags: フィルタリング用のタグ

        Returns:
            一致する場合True
        """
        if not filter_tags:
            return True

        if not metadata.tags:
            return False

        return all(metadata.tags.get(key) == value for key, value in filter_tags.items())

    def delete_artifact(self, artifact_id: str) -> bool:
        """アーティファクトを削除

        Args:
            artifact_id: artifact:abc123形式の参照ID

        Returns:
            削除成功の場合True
        """
        normalized_id = self._normalize_artifact_id(artifact_id)

        # メモリキャッシュから削除
        if normalized_id in self._memory_cache:
            del self._memory_cache[normalized_id]

        # ストレージから削除
        storage_path = self._get_storage_path(normalized_id)
        if storage_path.exists():
            storage_path.unlink()

        if self._logger:
            self._logger.info(f"Artifact deleted: {artifact_id}")

        # Domain層ではUI出力を行わない
        return True

    def create_reference(
        self,
        content: str,
        alias: str | None = None,
        **kwargs
    ) -> dict[str, str]:
        """コンテンツから参照情報を生成（便利メソッド）

        Args:
            content: ストアするコンテンツ
            alias: エイリアス名（オプション）
            **kwargs: storeメソッドへの追加引数

        Returns:
            参照情報辞書
        """
        artifact_id = self.store(content, **kwargs)

        reference = {
            "artifact_id": artifact_id,
            "content_preview": content[:100] + "..." if len(content) > 100 else content,
            "size_bytes": len(content.encode("utf-8"))
        }

        if alias:
            reference["alias"] = alias

        return reference

    def _normalize_artifact_id(self, artifact_id: str) -> str:
        """アーティファクトIDを正規化

        Args:
            artifact_id: 様々な形式の参照ID

        Returns:
            artifact:abc123形式に正規化されたID
        """
        if artifact_id.startswith("artifact:"):
            return artifact_id
        if artifact_id.startswith("ref:"):
            # エイリアス形式の場合は、実装で拡張可能
            return artifact_id.replace("ref:", "artifact:")
        # 生のハッシュの場合
        return f"artifact:{artifact_id}"

    def _get_storage_path(self, artifact_id: str) -> Path:
        """ストレージパスを取得"""
        hash_part = artifact_id.replace("artifact:", "")
        return self._storage_dir / f"{hash_part}.json"

    def _save_to_storage(self, artifact_id: str, artifact: StoredArtifact) -> None:
        """アーティファクトを永続化ストレージに保存"""
        storage_path = self._get_storage_path(artifact_id)

        data = {
            "content": artifact.content,
            "metadata": asdict(artifact.metadata)
        }

        with storage_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _load_from_storage(self, artifact_id: str) -> StoredArtifact | None:
        """永続化ストレージからアーティファクトを読み込み"""
        storage_path = self._get_storage_path(artifact_id)

        if not storage_path.exists():
            return None

        try:
            with storage_path.open("r", encoding="utf-8") as f:
                data = json.load(f)

            metadata = ArtifactMetadata(**data["metadata"])
            return StoredArtifact(content=data["content"], metadata=metadata)

        except Exception as e:
            if self._logger:
                self._logger.exception(f"Failed to load artifact {artifact_id}: {e}")
            return None

    def _extract_section(
        self,
        content: str,
        section: str,
        content_type: str
    ) -> str:
        """コンテンツから指定セクションを抽出"""
        try:
            if content_type == "json":
                data = json.loads(content)
                return str(data.get(section, f"Section '{section}' not found"))

            if content_type == "yaml":
                import yaml
                data = yaml.safe_load(content)
                return str(data.get(section, f"Section '{section}' not found"))

            # テキスト形式の場合、見出しベースのセクション抽出
            return self._extract_text_section(content, section)

        except Exception as e:
            if self._logger:
                self._logger.exception(f"Section extraction error: {e}")
            return f"Error extracting section '{section}': {e}"

    def _extract_text_section(self, content: str, section: str) -> str:
        """テキストコンテンツからセクションを抽出（簡易実装）"""
        lines = content.split("\n")
        section_lines = []
        in_section = False

        for line in lines:
            # セクション開始の検出（# セクション名、## セクション名等）
            if line.strip().startswith("#") and section.lower() in line.lower():
                in_section = True
                section_lines.append(line)
                continue

            # 次のセクションの開始で終了
            if in_section and line.strip().startswith("#") and section.lower() not in line.lower():
                break

            if in_section:
                section_lines.append(line)

        if section_lines:
            return "\n".join(section_lines)
        return f"Section '{section}' not found in content"


def create_artifact_store(
    logger_service: ILoggerService | None = None,
    storage_dir: Path | None = None
) -> ArtifactStoreService:
    """ArtifactStoreServiceのファクトリ関数

    Args:
        logger_service: ロガーサービス
        storage_dir: ストレージディレクトリ

    Returns:
        ArtifactStoreServiceインスタンス
    """
    return ArtifactStoreService(logger_service, storage_dir)
