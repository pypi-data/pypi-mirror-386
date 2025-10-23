#!/usr/bin/env python3
"""YamlA31ChecklistRepository実装

SPEC-QUALITY-001に基づくA31チェックリストのYAML管理実装
"""

import re
import shutil
from pathlib import Path
from typing import Any

import yaml

from noveler.domain.entities.a31_checklist_item import A31ChecklistItem, ChecklistItemType
from noveler.domain.entities.a31_complete_evaluation_engine import A31EvaluationBatch
from noveler.domain.entities.auto_fix_session import AutoFixSession
from noveler.domain.repositories.a31_checklist_repository import A31ChecklistRepository
from noveler.domain.value_objects.a31_auto_fix_strategy import AutoFixStrategy
from noveler.domain.value_objects.a31_threshold import Threshold, ThresholdType
from noveler.infrastructure.performance.comprehensive_performance_optimizer import (
    performance_monitor,
    performance_optimizer,
)

_yaml_optimizer = performance_optimizer.yaml_optimizer


def _format_project_timestamp(now_obj: Any, fmt: str) -> str:
    """ProjectDateTime/Mock互換のタイムスタンプ整形"""

    if hasattr(now_obj, "format_timestamp") and callable(now_obj.format_timestamp):
        return now_obj.format_timestamp(fmt)
    if hasattr(now_obj, "strftime") and callable(now_obj.strftime):
        return now_obj.strftime(fmt)
    if hasattr(now_obj, "datetime"):
        dt = now_obj.datetime
        if hasattr(dt, "strftime") and callable(dt.strftime):
            return dt.strftime(fmt)
    return str(now_obj)


def _iso_project_timestamp(now_obj: Any) -> str:
    """ProjectDateTime/Mock互換のISO文字列取得"""

    if hasattr(now_obj, "isoformat") and callable(now_obj.isoformat):
        return now_obj.isoformat()
    if hasattr(now_obj, "to_iso_string") and callable(now_obj.to_iso_string):
        return now_obj.to_iso_string()
    if hasattr(now_obj, "datetime"):
        dt = now_obj.datetime
        if hasattr(dt, "isoformat") and callable(dt.isoformat):
            return dt.isoformat()
    return str(now_obj)


def _project_now() -> Any:
    """遅延インポートで project_now を取得"""

    from noveler.domain.value_objects.project_time import project_now as _project_now_func

    return _project_now_func()



class YamlA31ChecklistRepository(A31ChecklistRepository):
    """A31チェックリスト設定のYAML管理実装（キャッシュ最適化対応）"""

    def __init__(self, guide_root: Path) -> None:
        """初期化

        Args:
            guide_root: ガイドルートディレクトリ
        """
        self.guide_root = guide_root
        self.template_path = guide_root / "templates" / "A31_原稿執筆チェックリストテンプレート.yaml"
        self._template_cache_key = None  # テンプレートキャッシュキー保存用

    @performance_monitor("YamlA31ChecklistRepository.load_template")
    def load_template(self) -> dict[str, Any]:
        """テンプレートYAMLの読み込み（新旧フォーマット自動対応）

        Returns:
            Dict[str, Any]: テンプレートデータ（システム統合形式）

        Raises:
            FileNotFoundError: テンプレートファイルが見つからない場合
            yaml.YAMLError: YAML解析エラーの場合
        """
        # 新フォーマット（A31.yaml）を優先チェック
        new_template_path = self.guide_root / "templates" / "A31.yaml"
        if new_template_path.exists():
            try:
                # YAMLOptimizer使用でキャッシュ最適化
                data = _yaml_optimizer.optimized_yaml_load(new_template_path)

                if self._is_simple_format(data):
                    return self._convert_simple_to_system_format(data)
                # 新ファイルが既にシステム形式の場合はそのまま使用
                return data

            except yaml.YAMLError:
                # 新フォーマット読み込み失敗時は旧フォーマットにフォールバック
                pass

        # 旧フォーマット（A31_原稿執筆チェックリストテンプレート.yaml）を使用
        if not self.template_path.exists():
            msg = f"テンプレートファイルが見つかりません: {self.template_path} または {new_template_path}"
            raise FileNotFoundError(msg)

        try:
            # YAMLOptimizer使用でキャッシュ最適化
            return _yaml_optimizer.optimized_yaml_load(self.template_path)
        except yaml.YAMLError as e:
            msg = f"YAMLファイルの解析に失敗しました: {e}"
            raise yaml.YAMLError(msg) from e

    def create_episode_checklist(self, episode_number: int, episode_title: str, project_root: Path) -> Path:
        """エピソード用チェックリストファイルの作成（共通パス管理サービス経由）"""
        template = self.load_template()

        from noveler.infrastructure.adapters.path_service_adapter import create_path_service

        path_service = create_path_service(project_root)

        management_dir = path_service.get_management_dir()
        if not management_dir.is_absolute():
            management_dir = project_root / str(management_dir)

        checklist_dir = management_dir / "A31_チェックリスト"
        checklist_dir.mkdir(parents=True, exist_ok=True)

        # ファイル名に使用できない文字を置換
        safe_title = re.sub(r'[<>:"/\\|?*]', '_', episode_title)
        filename = f"A31_チェックリスト_第{episode_number:03d}話_{safe_title}.yaml"
        output_path = checklist_dir / filename

        template_now = _project_now()
        template["metadata"]["target_episode"] = episode_number
        template["metadata"]["target_title"] = episode_title
        template["metadata"]["created_date"] = _iso_project_timestamp(template_now)

        try:
            with output_path.open("w", encoding="utf-8") as file:
                yaml.dump(template, file, allow_unicode=True, default_flow_style=False, indent=2)
        except OSError as e:
            msg = f"チェックリストファイルの作成に失敗しました: {e}"
            raise OSError(msg) from e

        return output_path

    @performance_monitor("YamlA31ChecklistRepository.save_results")
    def save_results(self, session: AutoFixSession, results_path: Path) -> None:
        """修正結果をエピソード用チェックリストに保存

        Args:
            session: 自動修正セッション
            results_path: 結果保存先パス

        Raises:
            FileNotFoundError: チェックリストファイルが見つからない場合
            yaml.YAMLError: YAML解析・保存エラーの場合
        """
        if not results_path.exists():
            msg = f"チェックリストファイルが見つかりません: {results_path}"
            raise FileNotFoundError(msg)

        try:
            # 既存のチェックリストを読み込み（YAMLOptimizer使用でキャッシュ最適化）
            checklist = _yaml_optimizer.optimized_yaml_load(results_path)

            # チェック結果を更新
            for result in session.results:
                # チェックリスト項目からA31項目を検索
                for phase_items in checklist["checklist_items"].values():
                    if isinstance(phase_items, list):
                        for item_data in phase_items:
                            if item_data.get("id") == result.item_id:
                                item_data["status"] = result.fix_applied
                                item_data["auto_fix_applied"] = True
                                item_data["fix_details"] = result.changes_made

                                # 修正情報を記録
                                if "fix_history" not in item_data:
                                    item_data["fix_history"] = []

                                fix_now = _project_now()
                                item_data["fix_history"].append(
                                    {
                                        "session_id": str(session.session_id),
                                        "fix_type": result.fix_type,
                                        "before_score": result.before_score,
                                        "after_score": result.after_score,
                                        "timestamp": _iso_project_timestamp(fix_now),
                                    }
                                )
                                break

            # 検証サマリーを更新
            completed_items = 0
            for phase_items in checklist["checklist_items"].values():
                if isinstance(phase_items, list):
                    for item_data in phase_items:
                        if item_data.get("status", False):
                            completed_items += 1

            total_items = checklist["validation_summary"]["total_items"]

            checklist["validation_summary"]["completed_items"] = completed_items
            checklist["validation_summary"]["completion_rate"] = (
                completed_items / total_items if total_items > 0 else 0.0
            )
            summary_now = _project_now()
            checklist["validation_summary"]["last_updated"] = _iso_project_timestamp(summary_now)

            # ファイルに保存
            with results_path.open("w", encoding="utf-8") as file:
                yaml.dump(checklist, file, allow_unicode=True, default_flow_style=False, indent=2)

        except yaml.YAMLError as e:
            msg = f"チェックリストファイルの保存に失敗しました: {e}"
            raise yaml.YAMLError(msg) from e

    @performance_monitor("YamlA31ChecklistRepository.get_checklist_items")
    def get_checklist_items(self, _project_name: str, item_ids: list[str]) -> list[A31ChecklistItem]:
        """チェックリスト項目を取得

        Args:
            project_name: プロジェクト名(この実装では未使用)
            item_ids: 取得する項目IDのリスト

        Returns:
            list[A31ChecklistItem]: チェックリスト項目のリスト
        """
        template = self.load_template()
        items = []

        # チェックリスト項目から指定されたIDの項目を抽出
        checklist_items = template.get("checklist_items", {})

        for phase_items in checklist_items.values():
            if isinstance(phase_items, list):
                for item_data in phase_items:
                    if item_data.get("id") in item_ids:
                        items.append(self._create_checklist_item_from_dict(item_data))

        return items

    @performance_monitor("YamlA31ChecklistRepository.get_all_items")
    def get_all_items(self) -> list[A31ChecklistItem]:
        """全チェックリスト項目を取得

        Returns:
            list[A31ChecklistItem]: 全チェックリスト項目
        """
        template = self.load_template()
        items = []

        checklist_items = template.get("checklist_items", {})

        for phase_items in checklist_items.values():
            if isinstance(phase_items, list):
                for item_data in phase_items:
                    items.append(self._create_checklist_item_from_dict(item_data))

        return items

    def get_all_checklist_items(self, project_name: str) -> list[A31ChecklistItem]:
        """全チェックリスト項目を取得(プロジェクト依存版)

        Args:
            project_name: プロジェクト名

        Returns:
            list[A31ChecklistItem]: 全チェックリスト項目
        """
        # 現在の実装では、プロジェクト名に関係なく全項目を返す
        # 将来的にはプロジェクト固有の設定を考慮する予定
        return self.get_all_items()

    def save_evaluation_results(
        self, project_name: str, episode_number: int, evaluation_batch: A31EvaluationBatch
    ) -> Path:
        """評価結果をYAML形式で保存

        Args:
            project_name: プロジェクト名
            episode_number: エピソード番号
            evaluation_batch: 評価バッチ結果

        Returns:
            Path: 保存されたファイルのパス

        Raises:
            OSError: ファイル保存に失敗した場合
        """
        try:
            # 保存先ディレクトリの作成
            results_dir = self.guide_root / "temp" / "a31_evaluation_results"
            results_dir.mkdir(parents=True, exist_ok=True)

            # ファイル名の生成
            now_obj = _project_now()
            safe_project_name = re.sub(r'[<>:"/\\|?*]', "_", project_name)
            timestamp = _format_project_timestamp(now_obj, "%Y%m%d_%H%M%S")
            filename = f"A31_evaluation_{safe_project_name}_episode_{episode_number:03d}_{timestamp}.yaml"
            output_path = results_dir / filename

            # 評価結果をYAML形式に変換
            evaluation_data: dict[str, Any] = {
                "metadata": {
                    "project_name": project_name,
                    "episode_number": episode_number,
                    "evaluation_timestamp": _iso_project_timestamp(now_obj),
                    "total_items": evaluation_batch.total_items,
                    "evaluated_items": evaluation_batch.evaluated_items,
                    "execution_time_ms": evaluation_batch.execution_time_ms,
                },
                "evaluation_results": {
                    "average_score": evaluation_batch.get_average_score(),
                    "pass_rate": evaluation_batch.get_pass_rate(),
                    "category_statistics": self._serialize_category_stats(evaluation_batch.get_category_statistics()),
                    "item_results": self._serialize_evaluation_results(evaluation_batch.results),
                },
            }

            # ファイルに保存
            with output_path.open("w", encoding="utf-8") as file:
                yaml.dump(evaluation_data, file, allow_unicode=True, default_flow_style=False, indent=2)

            return output_path

        except OSError as e:
            msg = f"評価結果の保存に失敗しました: {e}"
            raise OSError(msg) from e

    def _serialize_category_stats(self, category_stats: dict) -> dict[str, dict[str, float]]:
        """カテゴリ統計をシリアライズ可能な形式に変換

        Args:
            category_stats: カテゴリ別統計情報

        Returns:
            dict[str, dict[str, float]]: シリアライズ可能な統計情報
        """
        serialized = {}
        for category, stats in category_stats.items():
            # Enumを文字列に変換
            category_key = category.value if hasattr(category, "value") else str(category)
            serialized[category_key] = stats
        return serialized

    def _serialize_evaluation_results(self, results: dict) -> dict[str, dict[str, Any]]:
        """評価結果をシリアライズ可能な形式に変換

        Args:
            results: 評価結果

        Returns:
            dict[str, dict[str, Any]]: シリアライズ可能な評価結果
        """
        serialized = {}
        for item_id, result in results.items():
            # A31EvaluationResultのto_dict()メソッドを使用
            serialized[item_id] = (
                result.to_dict()
                if hasattr(result, "to_dict")
                else {
                    "item_id": getattr(result, "item_id", item_id),
                    "category": str(getattr(result, "category", "")),
                    "score": getattr(result, "score", 0.0),
                    "passed": getattr(result, "passed", False),
                    "details": getattr(result, "details", ""),
                    "execution_time_ms": getattr(result, "execution_time_ms", 0.0),
                }
            )
        return serialized

    def get_auto_fixable_items(self, fix_level: str) -> list[A31ChecklistItem]:
        """自動修正可能な項目を取得

        Args:
            fix_level: 修正レベル(safe/standard/interactive)

        Returns:
            list[A31ChecklistItem]: 自動修正可能な項目のリスト
        """
        all_items = self.get_all_items()
        return [
            item
            for item in all_items
            if item.is_auto_fixable() and self._is_compatible_fix_level(item.auto_fix_strategy.fix_level, fix_level)
        ]

    @performance_monitor("YamlA31ChecklistRepository.validate_checklist_structure")
    def validate_checklist_structure(self, checklist_path: Path) -> bool:
        """チェックリスト構造の検証

        Args:
            checklist_path: チェックリストファイルパス

        Returns:
            bool: 構造が正しい場合True
        """
        try:
            # YAMLOptimizer使用でキャッシュ最適化
            data = _yaml_optimizer.optimized_yaml_load(checklist_path)

            # 必要なキーの存在確認
            required_keys = ["metadata", "checklist_items", "validation_summary"]
            return all(key in data for key in required_keys)

        except (OSError, yaml.YAMLError):
            return False

    def backup_checklist(self, checklist_path: Path) -> Path:
        """チェックリストのバックアップ作成

        Args:
            checklist_path: チェックリストファイルパス

        Returns:
            Path: バックアップファイルのパス

        Raises:
            FileNotFoundError: 元ファイルが見つからない場合
            OSError: バックアップ作成に失敗した場合
        """
        if not checklist_path.exists():
            msg = f"バックアップ対象ファイルが見つかりません: {checklist_path}"
            raise FileNotFoundError(msg)

        timestamp = _format_project_timestamp(_project_now(), "%Y%m%d_%H%M%S")
        backup_path = checklist_path.with_suffix(f".backup_{timestamp}.yaml")

        try:
            shutil.copy2(checklist_path, backup_path)
            return backup_path
        except OSError as e:
            msg = f"バックアップの作成に失敗しました: {e}"
            raise OSError(msg) from e

    def restore_checklist(self, backup_path: Path, target_path: Path) -> bool:
        """チェックリストをバックアップから復元

        Args:
            backup_path: バックアップファイルパス
            target_path: 復元先パス

        Returns:
            bool: 復元成功時True
        """
        try:
            if not backup_path.exists():
                return False

            shutil.copy2(backup_path, target_path)
            return True
        except OSError:
            return False

    def _create_checklist_item_from_dict(self, item_data: dict[str, Any]) -> A31ChecklistItem:
        """辞書データからA31ChecklistItemを作成

        Args:
            item_data: 項目データ

        Returns:
            A31ChecklistItem: チェックリスト項目
        """
        # 項目タイプの決定
        item_type = self._determine_item_type(item_data.get("type", ""))

        # 閾値の作成
        threshold = self._create_threshold_from_item(item_data)

        # 自動修正サポート状況
        auto_fix_supported = item_data.get("auto_fix_supported", False)

        # 自動修正戦略の作成
        auto_fix_strategy = AutoFixStrategy(
            supported=auto_fix_supported,
            fix_level=item_data.get("auto_fix_level", "none"),
            priority=self._get_fix_priority(item_data.get("id", "")) if auto_fix_supported else 0,
        )

        return A31ChecklistItem(
            item_id=item_data.get("id", ""),
            title=item_data.get("item", ""),
            required=item_data.get("required", False),
            item_type=item_type,
            threshold=threshold,
            auto_fix_strategy=auto_fix_strategy,
        )

    def _is_simple_format(self, data: dict[str, Any]) -> bool:
        """簡易フォーマット（新A31.yaml）の判定

        Args:
            data: YAML読み込みデータ

        Returns:
            bool: 簡易フォーマットの場合True
        """
        # 新フォーマットは "原稿執筆チェックリスト" キーを持つ
        return "原稿執筆チェックリスト" in data and "metadata" not in data

    def _convert_simple_to_system_format(self, simple_data: dict[str, Any]) -> dict[str, Any]:
        """簡易フォーマットをシステム統合形式に変換

        Args:
            simple_data: 簡易フォーマットデータ

        Returns:
            dict[str, Any]: システム統合形式データ
        """
        converted = {
            "metadata": {
                "checklist_name": "A31_原稿執筆チェックリスト",
                "version": "3.0",
                "purpose": "エピソード原稿の執筆から公開までの作業確認",
                "template_update": _format_project_timestamp(_project_now(), "%Y-%m-%d"),
                "target_episode": None,
                "target_title": None,
                "created_date": None,
                "validation_date": None,
                "format_type": "simple_converted",
                "features": [
                    "novel writeおよびnovel check実行時に関連チェックリストが自動表示",
                    "簡易フォーマットから自動変換",
                    "人間可読性重視設計",
                ],
            },
            "checklist_items": {},
            "validation_summary": {
                "total_items": 0,
                "completed_items": 0,
                "required_items": 0,
                "required_completed": 0,
                "completion_rate": 0.0,
                "required_completion_rate": 0.0,
                "phases": [],
                "notes": [
                    "簡易A31.yamlから自動変換",
                    f"変換日時: {_format_project_timestamp(_project_now(), '%Y-%m-%d %H:%M:%S')}",
                ],
            },
        }

        # カテゴリマッピング（簡易フォーマット → システムフェーズ名）
        category_to_phase_mapping = {
            "構成・展開": "Phase2_執筆段階",
            "キャラクター": "Phase2_執筆段階",
            "情報・世界観提示": "Phase2_執筆段階",
            "感情導線・没入感": "Phase2_執筆段階",
            "メタファ・演出": "Phase2_執筆段階",
            "読後感・テーマ性": "Phase4_品質チェック段階",
            "文章リズム・可読性": "Phase3_推敲段階",
            "語尾・語調チェック": "Phase3_推敲段階",
            "スマホ・縦読み最適化": "Phase3_推敲段階",
            "段落設計・視認性": "Phase3_推敲段階",
            "感情テンポと読者呼吸": "Phase3_推敲段階",
        }

        # 項目変換処理
        item_id_counter = 1
        phase_totals = {}

        checklist_content = simple_data.get("原稿執筆チェックリスト", {})

        for category_name, items in checklist_content.items():
            if not isinstance(items, list):
                continue

            # フェーズ名を決定
            phase_name = category_to_phase_mapping.get(category_name, "Phase4_品質チェック段階")

            if phase_name not in converted["checklist_items"]:
                converted["checklist_items"][phase_name] = []
                phase_totals[phase_name] = 0

            # 各項目を変換
            for item_text in items:
                if not item_text or not item_text.strip():
                    continue

                item_id = f"A31-{item_id_counter:03d}"
                converted_item = {
                    "id": item_id,
                    "item": item_text.strip(),
                    "status": False,
                    "required": True,  # デフォルトで必須とする
                    "type": self._infer_item_type_from_text(item_text, category_name),
                    "auto_fix_supported": self._is_auto_fixable_from_text(item_text),
                    "auto_fix_applied": False,
                    "fix_details": [],
                    "reference_guides": [],
                    "input_files": [],
                    "output_validation": [f"{category_name}の評価"],
                }

                # 自動修正サポートの詳細設定
                if converted_item["auto_fix_supported"]:
                    converted_item["auto_fix_level"] = "safe"

                converted["checklist_items"][phase_name].append(converted_item)
                phase_totals[phase_name] += 1
                item_id_counter += 1

        # validation_summary の統計情報を更新
        total_items = item_id_counter - 1
        converted["validation_summary"]["total_items"] = total_items
        converted["validation_summary"]["required_items"] = total_items  # 全て必須とした

        # フェーズ情報を更新
        for phase_name, total in phase_totals.items():
            converted["validation_summary"]["phases"].append({"name": phase_name, "total": total, "completed": 0})

        return converted

    def _infer_item_type_from_text(self, item_text: str, category_name: str) -> str:
        """項目テキストからitem_typeを推論

        Args:
            item_text: 項目テキスト
            category_name: カテゴリ名

        Returns:
            str: 推論されたitem_type
        """
        # カテゴリベースの推論
        category_type_mapping = {
            "文章リズム・可読性": "readability_check",
            "語尾・語調チェック": "style_consistency",
            "段落設計・視認性": "format_check",
            "スマホ・縦読み最適化": "format_check",
            "構成・展開": "content_review",
            "キャラクター": "character_consistency",
            "情報・世界観提示": "content_balance",
            "感情導線・没入感": "content_quality",
            "メタファ・演出": "content_quality",
            "読後感・テーマ性": "content_review",
            "感情テンポと読者呼吸": "readability_check",
        }

        # テキスト内容ベースの推論
        if "文字" in item_text or "字" in item_text:
            return "readability_check"
        if "段落" in item_text or "改行" in item_text:
            return "format_check"
        if "語尾" in item_text or "文末" in item_text:
            return "style_consistency"
        if "キャラクター" in item_text or "台詞" in item_text:
            return "character_consistency"
        if "バランス" in item_text:
            return "content_balance"

        return category_type_mapping.get(category_name, "content_review")

    def _is_auto_fixable_from_text(self, item_text: str) -> bool:
        """項目テキストから自動修正可能性を判定

        Args:
            item_text: 項目テキスト

        Returns:
            bool: 自動修正可能と推定される場合True
        """
        # 自動修正しやすい項目のパターン
        auto_fixable_patterns = ["段落", "改行", "字下げ", "記号", "語尾", "文末", "三点リーダー", "ダッシュ"]

        return any(pattern in item_text for pattern in auto_fixable_patterns)

    def _determine_item_type(self, type_str: str) -> ChecklistItemType:
        """文字列からChecklistItemTypeを決定

        Args:
            type_str: タイプ文字列

        Returns:
            ChecklistItemType: チェックリスト項目タイプ
        """
        type_mapping = {
            "format_check": ChecklistItemType.FORMAT_CHECK,
            "style_consistency": ChecklistItemType.STYLE_CONSISTENCY,
            "quality_threshold": ChecklistItemType.QUALITY_THRESHOLD,
            "content_balance": ChecklistItemType.CONTENT_BALANCE,
            "content_review": ChecklistItemType.CONTENT_REVIEW,
            "command_execution": ChecklistItemType.COMMAND_EXECUTION,
            "system_function": ChecklistItemType.SYSTEM_FUNCTION,
        }
        return type_mapping.get(type_str, ChecklistItemType.CONTENT_REVIEW)

    def _create_threshold_from_item(self, item_data: dict[str, Any]) -> Threshold:
        """項目データから閾値を作成

        Args:
            item_data: 項目データ

        Returns:
            Threshold: 閾値オブジェクト
        """
        item_id = item_data.get("id", "")

        # 項目IDに基づく閾値設定(SPEC-QUALITY-001仕様に基づく)
        if item_id == "A31-045":  # 段落頭字下げ:
            return Threshold(ThresholdType.PERCENTAGE, 100.0)
        if item_id == "A31-042":  # 品質スコア70点以上:
            return Threshold(ThresholdType.SCORE, 70.0)
        if item_id == "A31-022":  # 会話と地の文バランス:
            return Threshold.create_range(30.0, 40.0)
        if item_id == "A31-035":  # 記号統一:
            return Threshold(ThresholdType.PERCENTAGE, 100.0)
        # デフォルト閾値
        return Threshold(ThresholdType.BOOLEAN, 1.0)

    def _get_fix_priority(self, item_id: str) -> int:
        """項目IDから修正優先度を取得

        Args:
            item_id: 項目ID

        Returns:
            int: 修正優先度(低い値ほど高優先度)
        """
        priority_mapping = {
            "A31-045": 1,  # 段落字下げ(高優先度)
            "A31-035": 1,  # 記号統一(高優先度)
            "A31-031": 2,  # 誤字脱字(中優先度)
            "A31-042": 3,  # 品質スコア(中優先度)
            "A31-022": 4,  # 会話バランス(低優先度)
        }
        return priority_mapping.get(item_id, 5)

    def _is_compatible_fix_level(self, item_level: str, requested_level: str) -> bool:
        """修正レベルの互換性チェック

        Args:
            item_level: 項目の修正レベル
            requested_level: 要求された修正レベル

        Returns:
            bool: 互換性がある場合True
        """
        level_hierarchy = {"safe": 1, "standard": 2, "interactive": 3}

        item_priority = level_hierarchy.get(item_level, 0)
        requested_priority = level_hierarchy.get(requested_level, 0)

        return item_priority <= requested_priority
