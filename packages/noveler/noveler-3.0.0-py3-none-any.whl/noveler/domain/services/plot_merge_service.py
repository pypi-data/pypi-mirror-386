"""Domain.services.plot_merge_service
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

"""
プロットマージドメインサービス

プロットデータのマージ戦略を実装するドメインサービス
ビジネスロジックに基づいて、既存データと新規データを統合する
"""


from typing import Any

from noveler.domain.value_objects.merge_strategy import MergeStrategy


class PlotMergeService:
    """プロットデータのマージを担当するドメインサービス"""

    def merge_plot_data(
        self, existing_data: dict[str, Any], new_data: dict[str, Any], strategy: MergeStrategy = MergeStrategy.MERGE
    ) -> dict[str, Any]:
        """プロットデータをマージする

        Args:
            existing_data: 既存のプロットデータ
            new_data: 新規のプロットデータ
            strategy: マージ戦略

        Returns:
            マージ後のデータ
        """
        if strategy == MergeStrategy.REPLACE:
            # REPLACE戦略:新規データで完全に置き換え
            return new_data.copy()

        if not existing_data:
            # 既存データが空の場合は新規データを返す
            return new_data.copy()

        # MERGE戦略:既存データと新規データを統合
        return self._deep_merge(existing_data, new_data)

    def _deep_merge(self, base: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
        """ディープマージを実行する

        Args:
            base: ベースとなる辞書(既存データ)
            update: 更新する辞書(新規データ)

        Returns:
            マージ後の辞書
        """
        result = base.copy()

        for key, value in update.items():
            if key in result:
                # 既存のキーがある場合
                if isinstance(result[key], dict) and isinstance(value, dict):
                    # 両方が辞書の場合は再帰的にマージ
                    result[key] = self._deep_merge(result[key], value)
                elif isinstance(result[key], list) and isinstance(value, list):
                    # 両方がリストの場合は特別な処理
                    result[key] = self._merge_lists(result[key], value, key)
                else:
                    # それ以外は新規データで上書き
                    result[key] = value
            else:
                # 新規キーの場合はそのまま追加
                result[key] = value

        return result

    def _merge_lists(self, base_list: list[Any], update_list: list[Any], key: str = "") -> list[Any]:
        """リストをマージする

        Args:
            base_list: ベースとなるリスト
            update_list: 更新するリスト
            key: リストのキー名(処理の判断に使用)

        Returns:
            マージ後のリスト
        """
        # タグのような単純なリストの場合
        if key in ["tags", "keywords", "genres"]:
            # 重複を除去して結合
            return list(dict.fromkeys(base_list + update_list))

        # chaptersやcharactersのような辞書のリストの場合
        if base_list and isinstance(base_list[0], dict):
            return self._merge_dict_lists(base_list, update_list)

        # デフォルトは更新リストで置き換え
        return update_list

    def _merge_dict_lists(self, base_list: list[dict], update_list: list[dict]) -> list[dict]:
        """辞書のリストをマージする

        Args:
            base_list: ベースとなる辞書のリスト
            update_list: 更新する辞書のリスト

        Returns:
            マージ後の辞書のリスト
        """
        # 識別キーを特定(name, number, id など)
        id_key = self._find_id_key(base_list + update_list)

        if not id_key:
            # 識別キーがない場合は更新リストで置き換え
            return update_list

        # 結果リストを構築
        result = []
        processed_ids = set()

        # 更新リストの項目を処理(優先)
        for update_item in update_list:
            item_id = update_item.get(id_key)
            if item_id is None:
                result.append(update_item)
                continue

            processed_ids.add(item_id)

            # 既存リストから対応する項目を探す
            base_item = next((item for item in base_list if item.get(id_key) == item_id), None)

            if base_item:
                # 既存項目がある場合はマージ
                merged_item = self._deep_merge(base_item, update_item)
                result.append(merged_item)
            else:
                # 新規項目
                result.append(update_item)

        # 既存リストの未処理項目を追加
        for base_item in base_list:
            item_id = base_item.get(id_key)
            if item_id and item_id not in processed_ids:
                result.append(base_item)

        return result

    def _find_id_key(self, dict_list: list[dict]) -> str | None:
        """辞書リストの識別キーを特定する

        Args:
            dict_list: 辞書のリスト

        Returns:
            識別キー名、見つからない場合はNone
        """
        if not dict_list:
            return None

        # 一般的な識別キー候補
        id_candidates = ["name", "number", "id", "title", "key"]

        # 最初の要素からキーを確認
        first_item = dict_list[0]
        for candidate in id_candidates:
            if candidate in first_item:
                return candidate

        return None
