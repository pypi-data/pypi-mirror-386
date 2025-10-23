#!/usr/bin/env python3
"""品質チェックリストデータ バリューオブジェクト（旧称A31ChecklistData）

A31チェックリストの構造化データを管理し、
YAML形式との相互変換を提供するバリューオブジェクト。
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class QualityChecklistData:
    """A31チェックリストデータ バリューオブジェクト

    A31チェックリストの構造化データを不変オブジェクトとして管理し、
    YAML形式との相互変換とデータ妥当性検証を提供する。
    """

    checklist_items: dict[str, list[dict[str, Any]]]
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        """データ妥当性検証"""
        if not self.checklist_items:
            msg = "チェックリスト項目は空にできません"
            raise ValueError(msg)

        # 各フェーズに最低1項目は必要
        for phase_name, items in self.checklist_items.items():
            if not items:
                msg = f"フェーズ '{phase_name}' には最低1項目が必要です"
                raise ValueError(msg)

    @classmethod
    def from_yaml_data(cls, yaml_data: dict[str, Any]) -> "QualityChecklistData":
        """YAMLデータからインスタンス作成

        Args:
            yaml_data: YAML形式のチェックリストデータ

        Returns:
            QualityChecklistData: チェックリストデータインスタンス

        Raises:
            ValueError: 必須フィールドが不足している場合
        """
        if not isinstance(yaml_data, dict):
            msg = "YAMLデータは辞書形式である必要があります"
            raise ValueError(msg)

        if "checklist_items" not in yaml_data:
            msg = "'checklist_items' フィールドが必要です"
            raise ValueError(msg)

        checklist_items = yaml_data["checklist_items"]
        metadata = yaml_data.get("metadata", {})

        return cls(checklist_items=checklist_items, metadata=metadata)

    def to_yaml_data(self) -> dict[str, Any]:
        """YAML形式データへの変換

        Returns:
            Dict[str, Any]: YAML出力用の辞書データ
        """
        data = {"checklist_items": self.checklist_items}

        if self.metadata:
            data["metadata"] = self.metadata

        return data

    def get_total_items_count(self) -> int:
        """総項目数取得

        Returns:
            int: 全フェーズの項目数合計
        """
        return sum(len(items) for items in self.checklist_items.values())

    def get_phase_names(self) -> list[str]:
        """フェーズ名一覧取得

        Returns:
            List[str]: フェーズ名のリスト
        """
        return list(self.checklist_items.keys())

    def get_items_by_phase(self, phase_name: str) -> list[dict[str, Any]]:
        """指定フェーズの項目取得

        Args:
            phase_name: フェーズ名

        Returns:
            List[Dict[str, Any]]: 指定フェーズの項目リスト

        Raises:
            KeyError: 指定フェーズが存在しない場合
        """
        if phase_name not in self.checklist_items:
            available_phases = ", ".join(self.get_phase_names())
            msg = f"フェーズ '{phase_name}' が見つかりません。利用可能: {available_phases}"
            raise KeyError(msg)

        return self.checklist_items[phase_name].copy()

    def find_item_by_id(self, item_id: str) -> dict[str, Any] | None:
        """項目ID による項目検索

        Args:
            item_id: 検索対象の項目ID

        Returns:
            Optional[Dict[str, Any]]: 見つかった項目、または None
        """
        for phase_items in self.checklist_items.values():
            for item in phase_items:
                if isinstance(item, dict) and item.get("id") == item_id:
                    return item.copy()

        return None

    def get_items_by_criteria(
        self,
        claude_suitable: bool | None = None,
        min_priority: float | None = None,
        evaluation_category: str | None = None,
    ) -> list[dict[str, Any]]:
        """条件による項目フィルタリング

        Args:
            claude_suitable: Claude分析適性フィルタ
            min_priority: 最小優先度閾値
            evaluation_category: 評価カテゴリフィルタ

        Returns:
            List[Dict[str, Any]]: 条件に合致する項目リスト
        """
        filtered_items = []

        for phase_items in self.checklist_items.values():
            for item in phase_items:
                if not isinstance(item, dict):
                    continue

                # Claude適性フィルタ
                if claude_suitable is not None:
                    if item.get("claude_suitable", False) != claude_suitable:
                        continue

                # 優先度フィルタ
                if min_priority is not None:
                    item_priority = item.get("priority", 0.0)
                    if item_priority < min_priority:
                        continue

                # 評価カテゴリフィルタ
                if evaluation_category is not None:
                    if item.get("evaluation_category") != evaluation_category:
                        continue

                filtered_items.append(item.copy())

        return filtered_items

    def get_all_items(self) -> list[dict[str, Any]]:
        """全項目の平坦リスト取得（フェーズ情報付き）

        Returns:
            List[Dict[str, Any]]: 全フェーズの項目を平坦化したリスト（フェーズ情報含む）
        """
        all_items = []
        for phase_name, phase_items in self.checklist_items.items():
            for item in phase_items:
                # 項目にフェーズ情報を追加
                item_with_phase = item.copy() if isinstance(item, dict) else item
                if isinstance(item_with_phase, dict):
                    item_with_phase["phase_name"] = phase_name
                all_items.append(item_with_phase)
        return all_items

    def add_metadata_entry(self, key: str, value: Any) -> "QualityChecklistData":
        """メタデータエントリ追加（新しいインスタンスを返す）

        Args:
            key: メタデータキー
            value: メタデータ値

        Returns:
            QualityChecklistData: メタデータが追加された新しいインスタンス
        """
        new_metadata = (self.metadata or {}).copy()
        new_metadata[key] = value

        return QualityChecklistData(checklist_items=self.checklist_items, metadata=new_metadata)

    def get_statistics(self) -> dict[str, Any]:
        """チェックリスト統計情報取得

        Returns:
            Dict[str, Any]: 統計情報辞書
        """
        total_items = self.get_total_items_count()
        phase_counts = {phase: len(items) for phase, items in self.checklist_items.items()}

        # Claude適性項目数
        claude_suitable_items = self.get_items_by_criteria(claude_suitable=True)
        claude_suitable_count = len(claude_suitable_items)

        # 優先度統計
        all_items = self.get_items_by_criteria()
        priorities = [item.get("priority", 0.0) for item in all_items if "priority" in item]

        avg_priority = sum(priorities) / len(priorities) if priorities else 0.0
        high_priority_count = len([p for p in priorities if p >= 0.8])

        return {
            "total_items": total_items,
            "phase_counts": phase_counts,
            "claude_suitable_count": claude_suitable_count,
            "claude_suitable_rate": claude_suitable_count / total_items if total_items > 0 else 0.0,
            "average_priority": avg_priority,
            "high_priority_count": high_priority_count,
            "high_priority_rate": high_priority_count / len(priorities) if priorities else 0.0,
        }

    def __str__(self) -> str:
        """文字列表現"""
        stats = self.get_statistics()
        return (
            f"QualityChecklistData("
            f"total_items={stats['total_items']}, "
            f"phases={len(self.checklist_items)}, "
            f"claude_suitable={stats['claude_suitable_count']})"
        )

    def __repr__(self) -> str:
        """開発者向け文字列表現"""
        return self.__str__()

    def resolve_path_templates(self, project_root: Path | None = None) -> "QualityChecklistData":
        """パステンプレート変数を実際のパスに解決

        A31チェックリスト内の$PROJECT_ROOT、$GUIDE_ROOT等のテンプレート変数を
        実際のパスに置換した新しいインスタンスを返す。

        Args:
            project_root: プロジェクトルートパス。Noneの場合は自動検出を試行

        Returns:
            QualityChecklistData: パステンプレートが解決された新しいインスタンス
        """
        # DDD準拠: Domain層はPresentation層に依存できません
        # プロジェクトルートが未指定の場合はカレントディレクトリを使用
        if project_root is None:
            # フォールバック: 環境変数またはカレントディレクトリ（トップレベルimportを使用）
            project_root = Path(os.environ.get("PROJECT_ROOT", Path.cwd()))

        # テンプレート変数のマッピング
        template_vars = {
            "$PROJECT_ROOT": str(project_root),
            "$GUIDE_ROOT": "",  # TODO: IPathService注入による実装が必要
        }

        # チェックリスト項目のテンプレート解決
        resolved_items = {}
        for phase_name, items in self.checklist_items.items():
            resolved_phase_items = []
            for item in items:
                if isinstance(item, dict):
                    resolved_item = self._resolve_item_paths(item, template_vars)
                    resolved_phase_items.append(resolved_item)
                else:
                    resolved_phase_items.append(item)
            resolved_items[phase_name] = resolved_phase_items

        # メタデータのテンプレート解決
        resolved_metadata = None
        if self.metadata:
            resolved_metadata = self._resolve_dict_paths(self.metadata, template_vars)

        return QualityChecklistData(checklist_items=resolved_items, metadata=resolved_metadata)

    def _resolve_item_paths(self, item: dict[str, Any], template_vars: dict[str, str]) -> dict[str, Any]:
        """単一チェック項目内のパステンプレートを解決

        Args:
            item: チェック項目辞書
            template_vars: テンプレート変数マッピング

        Returns:
            Dict[str, Any]: パス解決済みの項目辞書
        """
        resolved_item = {}

        for key, value in item.items():
            if isinstance(value, str):
                resolved_item[key] = self._resolve_string_template(value, template_vars)
            elif isinstance(value, list):
                resolved_item[key] = [
                    self._resolve_string_template(v, template_vars) if isinstance(v, str) else v for v in value
                ]
            elif isinstance(value, dict):
                resolved_item[key] = self._resolve_dict_paths(value, template_vars)
            else:
                resolved_item[key] = value

        return resolved_item

    def _resolve_dict_paths(self, data: dict[str, Any], template_vars: dict[str, str]) -> dict[str, Any]:
        """辞書内のパステンプレートを再帰的に解決

        Args:
            data: 対象辞書
            template_vars: テンプレート変数マッピング

        Returns:
            Dict[str, Any]: パス解決済み辞書
        """
        resolved_data: dict[str, Any] = {}

        for key, value in data.items():
            if isinstance(value, str):
                resolved_data[key] = self._resolve_string_template(value, template_vars)
            elif isinstance(value, list):
                resolved_data[key] = [
                    self._resolve_string_template(v, template_vars) if isinstance(v, str) else v for v in value
                ]
            elif isinstance(value, dict):
                resolved_data[key] = self._resolve_dict_paths(value, template_vars)
            else:
                resolved_data[key] = value

        return resolved_data

    def _resolve_string_template(self, text: str, template_vars: dict[str, str]) -> str:
        """文字列内のテンプレート変数を置換

        Args:
            text: 対象文字列
            template_vars: テンプレート変数マッピング

        Returns:
            str: テンプレート変数が置換された文字列
        """
        resolved_text = text
        for template_var, replacement in template_vars.items():
            if template_var in resolved_text:
                resolved_text = resolved_text.replace(template_var, replacement)

        return resolved_text


# Backward compatibility alias
A31ChecklistData = QualityChecklistData
