"""Service that manages differential updates via JSON Patch and unified diff."""

import difflib
import hashlib
from datetime import datetime, timezone
from typing import Any

import jsonpatch

from noveler.domain.interfaces.logger_service import ILoggerService
from noveler.domain.value_objects.differential_update import DifferentialUpdate, UpdateType


class DifferentialUpdateService:
    """Create, apply, and analyze differential updates for writing workflows."""

    def __init__(self, logger_service: "ILoggerService | None" = None) -> None:
        """Initialize the service with an optional logger dependency."""
        self._update_counter = 0
        self._logger = logger_service

    def create_patch(
        self,
        original: dict[str, Any],
        modified: dict[str, Any],
        update_type: UpdateType = UpdateType.REVISION,
        metadata: dict[str, Any] | None = None,
    ) -> DifferentialUpdate:
        """Generate a differential update entity from original and modified data."""
        # JSON Patch生成
        json_patch = jsonpatch.make_patch(original, modified)

        # テキストコンテンツの抽出
        original_text = self._extract_text_content(original)
        modified_text = self._extract_text_content(modified)

        # Unified Diff生成
        unified_diff = self._generate_unified_diff(original_text, modified_text)

        # トークン効率計算
        token_saved = self._calculate_token_saving(original, json_patch)
        compression_ratio = self._calculate_compression_ratio(original, json_patch)

        # 品質メトリクス変化の計算
        quality_delta = self._calculate_quality_delta(original, modified)

        # 差分更新エンティティの作成
        return DifferentialUpdate(
            update_id=self._generate_update_id(),
            timestamp=datetime.now(timezone.utc),
            update_type=update_type,
            target_step=original.get("step_number", 0),
            json_patch=list(json_patch),
            unified_diff=unified_diff,
            quality_delta=quality_delta,
            token_saved=token_saved,
            compression_ratio=compression_ratio,
            metadata=metadata or {},
        )

    def apply_patch(self, target: dict[str, Any], patch: DifferentialUpdate) -> dict[str, Any]:
        """Apply a differential update to the provided target payload."""
        if not patch.validate():
            error_message = "無効な差分更新です"
            raise ValueError(error_message)

        return patch.apply_to(target)

    def preview_changes(self, patch: DifferentialUpdate, output_format: str = "both") -> str:
        """Return a human-readable preview of the differential update."""
        preview_parts = []

        if output_format in ("json", "both"):
            preview_parts.append("=== JSON Patch 操作 ===")
            for i, op in enumerate(patch.json_patch, 1):
                op_type = op.get("op", "unknown")
                path = op.get("path", "")
                preview_parts.append(f"{i}. {op_type}: {path}")

        if output_format in ("diff", "both"):
            if preview_parts:
                preview_parts.append("")
            preview_parts.append("=== Unified Diff ===")
            preview_parts.append(patch.unified_diff)

        return "\n".join(preview_parts)

    def _extract_text_content(self, data: dict[str, Any]) -> str:
        """Extract text content from a structured payload for diff generation."""
        text_parts = []

        # メインテキスト
        if "generated_text" in data:
            text_parts.append(data["generated_text"])

        # シーンテキスト
        if "scenes" in data and isinstance(data["scenes"], list):
            text_parts.extend(
                scene["content"] for scene in data["scenes"] if isinstance(scene, dict) and "content" in scene
            )

        # その他のテキストフィールド
        text_fields = ["content", "text", "description", "summary"]
        text_parts.extend(data[field] for field in text_fields if field in data and isinstance(data[field], str))

        return "\n\n".join(text_parts)

    def _generate_unified_diff(self, original: str, modified: str, context_lines: int = 3) -> str:
        """Generate a unified diff between the original and modified text."""
        original_lines = original.splitlines(keepends=True)
        modified_lines = modified.splitlines(keepends=True)

        # 空の場合の処理
        if not original_lines:
            original_lines = [""]
        if not modified_lines:
            modified_lines = [""]

        diff = difflib.unified_diff(
            original_lines, modified_lines, fromfile="original.txt", tofile="revised.txt", n=context_lines
        )

        return "".join(diff)

    def _calculate_token_saving(self, original: dict[str, Any], json_patch: jsonpatch.JsonPatch) -> int:
        """Estimate token savings achieved by sending patch operations."""
        # 簡易的なトークン計算（文字数ベース）
        # 実際のトークン計算はtiktokenなどを使用する想定
        original_size = len(str(original))
        patch_size = len(str(list(json_patch)))

        # 概算でトークン数を計算（4文字 = 1トークンと仮定）
        original_tokens = original_size // 4
        patch_tokens = patch_size // 4

        return max(0, original_tokens - patch_tokens)

    def _calculate_compression_ratio(self, original: dict[str, Any], json_patch: jsonpatch.JsonPatch) -> float:
        """Estimate compression ratio achieved by transmitting the patch only."""
        original_size = len(str(original))
        patch_size = len(str(list(json_patch)))

        if original_size == 0:
            return 0.0

        return max(0.0, 1.0 - (patch_size / original_size))

    def _calculate_quality_delta(self, original: dict[str, Any], modified: dict[str, Any]) -> dict[str, float]:
        """Compute the delta for quality-related metrics between two payloads."""
        delta = {}

        # 元データと修正データの品質メトリクスを比較
        original_metrics = original.get("quality_metrics", {})
        modified_metrics = modified.get("quality_metrics", {})

        # 新しいQualityMetrics形式への対応
        if isinstance(original_metrics, dict) and "overall_score" in original_metrics:
            # 新しい形式: {"overall_score": 0.8, "specific_metrics": {...}}
            original_flat = {"overall_score": original_metrics.get("overall_score", 0.0)}
            if "specific_metrics" in original_metrics:
                original_flat.update(original_metrics["specific_metrics"])
        else:
            # 古い形式または空の場合
            original_flat = original_metrics if isinstance(original_metrics, dict) else {}

        if isinstance(modified_metrics, dict) and "overall_score" in modified_metrics:
            # 新しい形式: {"overall_score": 0.8, "specific_metrics": {...}}
            modified_flat = {"overall_score": modified_metrics.get("overall_score", 0.0)}
            if "specific_metrics" in modified_metrics:
                modified_flat.update(modified_metrics["specific_metrics"])
        else:
            # 古い形式または空の場合
            modified_flat = modified_metrics if isinstance(modified_metrics, dict) else {}

        # 差分計算
        for key in set(original_flat.keys()) | set(modified_flat.keys()):
            original_value = original_flat.get(key, 0.0)
            modified_value = modified_flat.get(key, 0.0)

            # 数値型のチェック
            if isinstance(original_value, int | float) and isinstance(modified_value, int | float):
                delta[key] = modified_value - original_value
            else:
                # 数値でない場合はデフォルト値を使用
                delta[key] = 0.0

        return delta

    def _generate_update_id(self) -> str:
        """Generate a unique identifier for the differential update."""
        self._update_counter += 1

        # タイムスタンプとカウンターを組み合わせた一意のID
        timestamp = datetime.now(timezone.utc).isoformat()
        unique_string = f"{timestamp}-{self._update_counter}"

        # ハッシュ化して短縮
        hash_object = hashlib.sha256(unique_string.encode())
        short_hash = hash_object.hexdigest()[:8]

        return f"update-{short_hash}-{self._update_counter:04d}"

    def validate_patch(self, patch: DifferentialUpdate, target: dict[str, Any] | None = None) -> bool:
        """Validate that the differential update can be safely applied."""
        # 基本的な検証
        if not patch.validate():
            return False

        # ターゲットが指定されている場合、適用可能性を検証
        if target is not None:
            try:
                # テスト適用を実行
                test_patch = jsonpatch.JsonPatch(patch.json_patch)
                test_patch.apply(target)
                return True
            except (jsonpatch.JsonPatchException, KeyError, IndexError):
                return False

        return True
