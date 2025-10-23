#!/usr/bin/env python3
"""Claude分析リクエスト生成ユースケース

A31重点項目からClaude Code問い合わせ形式への変換を行う
アプリケーションサービス。DDD準拠でビジネスフローを管理。
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from noveler.domain.entities.a31_priority_item import A31PriorityItem
from noveler.domain.services.a31_priority_extractor_service import (
    A31ChecklistData,
    A31PriorityExtractorService,
    ExtractionStrategy,
    PriorityExtractionCriteria,
)
from noveler.domain.value_objects.a31_evaluation_category import A31EvaluationCategory


@dataclass
class ClaudeAnalysisRequest:
    """Claude分析リクエスト データ構造"""

    analysis_context: dict[str, Any]
    analysis_focus: dict[str, Any]
    source_content: dict[str, Any]
    output_requirements: dict[str, Any]
    metadata: dict[str, Any]

    def to_yaml(self) -> str:
        """YAML形式で出力"""
        request_data: dict[str, Any] = {
            "claude_analysis_request": {
                "analysis_context": self.analysis_context,
                "analysis_focus": self.analysis_focus,
                "source_content": self.source_content,
                "output_requirements": self.output_requirements,
            },
            "metadata": self.metadata,
        }

        return yaml.dump(request_data, default_flow_style=False, allow_unicode=True, sort_keys=False)


@dataclass
class GenerateClaudeAnalysisRequest:
    """Claude分析リクエスト生成要求"""

    checklist_file_path: str
    episode_number: int
    focus_categories: list[str] | None = None
    max_priority_items: int = 20
    extraction_strategy: str = "hybrid"
    output_file_path: str | None = None


@dataclass
class GenerateClaudeAnalysisResponse:
    """Claude分析リクエスト生成応答"""

    success: bool
    claude_request: ClaudeAnalysisRequest | None = None
    extracted_items_count: int = 0
    statistics: dict[str, Any] | None = None
    output_file_path: str | None = None
    error_message: str | None = None


class ClaudeAnalysisRequestGenerationUseCase:
    """Claude分析リクエスト生成ユースケース

    A31チェックリストから重点項目を抽出し、
    Claude Code分析用の構造化YAML形式に変換する。
    """

    def __init__(self, priority_extractor: A31PriorityExtractorService) -> None:
        """ユースケース初期化

        Args:
            priority_extractor: A31重点項目抽出サービス
        """
        self._priority_extractor = priority_extractor

    def execute(self, request: GenerateClaudeAnalysisRequest) -> GenerateClaudeAnalysisResponse:
        """Claude分析リクエスト生成を実行

        Args:
            request: 生成要求

        Returns:
            GenerateClaudeAnalysisResponse: 生成結果
        """
        try:
            # 1. A31チェックリストデータ読み込み
            checklist_data: dict[str, Any] = self._load_checklist_data(request.checklist_file_path)

            # 2. 抽出基準設定
            criteria = self._create_extraction_criteria(request)

            # 3. 重点項目抽出
            priority_items = self._priority_extractor.extract_priority_items(checklist_data, criteria)

            if not priority_items:
                return GenerateClaudeAnalysisResponse(
                    success=False, error_message="重点項目が抽出されませんでした。基準を見直してください。"
                )

            # 4. Claude分析リクエスト構築
            claude_request = self._build_claude_analysis_request(priority_items, checklist_data, request)

            # 5. 統計情報生成
            statistics = self._priority_extractor.get_extraction_statistics(priority_items)

            # 6. ファイル出力（オプション）
            output_path = None
            if request.output_file_path:
                output_path = self._save_claude_request(claude_request, request.output_file_path)

            return GenerateClaudeAnalysisResponse(
                success=True,
                claude_request=claude_request,
                extracted_items_count=len(priority_items),
                statistics=statistics,
                output_file_path=output_path,
            )

        except Exception as e:
            return GenerateClaudeAnalysisResponse(success=False, error_message=f"Claude分析リクエスト生成エラー: {e!s}")

    def _load_checklist_data(self, file_path: str) -> A31ChecklistData:
        """A31チェックリストデータを読み込み"""
        checklist_path = Path(file_path)

        if not checklist_path.exists():
            msg = f"チェックリストファイルが見つかりません: {file_path}"
            raise FileNotFoundError(msg)

        with checklist_path.open(encoding="utf-8") as f:
            yaml_data: dict[str, Any] = yaml.safe_load(f)

        if not yaml_data or "checklist_items" not in yaml_data:
            msg = "無効なA31チェックリスト形式です"
            raise ValueError(msg)

        metadata = yaml_data.get("metadata", {})

        return A31ChecklistData(
            checklist_items=yaml_data["checklist_items"],
            metadata=metadata,
            target_episode=metadata.get("target_episode"),
            target_title=metadata.get("target_title"),
        )

    def _create_extraction_criteria(self, request: GenerateClaudeAnalysisRequest) -> PriorityExtractionCriteria:
        """抽出基準を作成"""
        # フォーカスカテゴリの変換
        focus_categories = None
        if request.focus_categories:
            focus_categories = []
            for category_str in request.focus_categories:
                try:
                    category = A31EvaluationCategory(category_str)
                    focus_categories.append(category)
                except ValueError:
                    # 無効なカテゴリはスキップ
                    continue

        # 抽出戦略の変換
        strategy_mapping = {
            "manual": ExtractionStrategy.MANUAL_CURATION,
            "auto": ExtractionStrategy.AUTO_SCORING,
            "hybrid": ExtractionStrategy.HYBRID,
        }

        strategy = strategy_mapping.get(request.extraction_strategy, ExtractionStrategy.HYBRID)

        return PriorityExtractionCriteria(
            priority_threshold=0.7,
            focus_categories=focus_categories,
            max_items=request.max_priority_items,
            strategy=strategy,
        )

    def _build_claude_analysis_request(
        self,
        priority_items: list[A31PriorityItem],
        checklist_data: A31ChecklistData,
        request: GenerateClaudeAnalysisRequest,
    ) -> ClaudeAnalysisRequest:
        """Claude分析リクエストを構築"""

        # 分析コンテキスト構築
        analysis_context = self._build_analysis_context(checklist_data, request)

        # 分析フォーカス構築
        analysis_focus = self._build_analysis_focus(priority_items)

        # ソース内容指定
        source_content = self._build_source_content(checklist_data, request)

        # 出力要求定義
        output_requirements = self._build_output_requirements(priority_items)

        # メタデータ
        metadata = self._build_metadata(priority_items, checklist_data)

        return ClaudeAnalysisRequest(
            analysis_context=analysis_context,
            analysis_focus=analysis_focus,
            source_content=source_content,
            output_requirements=output_requirements,
            metadata=metadata,
        )

    def _build_analysis_context(
        self, checklist_data: A31ChecklistData, request: GenerateClaudeAnalysisRequest
    ) -> dict[str, Any]:
        """分析コンテキストを構築"""
        return {
            "based_on_checklist": Path(request.checklist_file_path).name,
            "improvement_reason": (
                f"A31チェックリスト第{request.episode_number}話の重点項目について、"
                "Claude Code詳細分析による具体的改善提案を求めます。"
            ),
            "work_info": {
                "title": checklist_data.target_title or "未設定",
                "episode": checklist_data.target_episode or request.episode_number,
                "quality_target": 80.0,
            },
        }

    def _build_analysis_focus(self, priority_items: list[A31PriorityItem]) -> dict[str, Any]:
        """分析フォーカスを構築"""
        phase_groups = self._group_items_by_phase(priority_items)
        primary_phases = self._build_primary_phases(phase_groups)
        critical_checks = self._build_critical_checks(priority_items)

        return {"primary_phases": primary_phases, "critical_checks": critical_checks}

    def _group_items_by_phase(self, priority_items: list[A31PriorityItem]) -> dict[str, list[A31PriorityItem]]:
        """優先度項目をフェーズ別にグループ化"""
        phase_groups = {}
        for item in priority_items:
            phase_key = item.phase.value
            if phase_key not in phase_groups:
                phase_groups[phase_key] = []
            phase_groups[phase_key].append(item)
        return phase_groups

    def _build_primary_phases(self, phase_groups: dict[str, list[A31PriorityItem]]) -> dict[str, dict[str, Any]]:
        """重点分析項目を構築"""
        primary_phases = {}
        for phase_key, items in phase_groups.items():
            item_summaries = [f'"{item.item_id.value}"' for item in items[:5]]
            focus_areas = self._extract_focus_areas(items[:5])

            primary_phases[phase_key] = {"items": item_summaries, "focus": list(set(focus_areas))}
        return primary_phases

    def _extract_focus_areas(self, items: list[A31PriorityItem]) -> list[str]:
        """項目からフォーカス領域を抽出"""
        focus_areas = []
        for item in items:
            if "冒頭" in item.content:
                focus_areas.append("冒頭引き込み効果")
            elif "バランス" in item.content:
                focus_areas.append("内容バランス最適化")
            elif "五感" in item.content or "描写" in item.content:
                focus_areas.append("感覚描写強化")
            elif "リズム" in item.content:
                focus_areas.append("文体リズム改善")
        return focus_areas

    def _build_critical_checks(self, priority_items: list[A31PriorityItem]) -> list[dict[str, str]]:
        """重要項目の詳細プロンプトを構築"""
        return [
            {
                "id": item.item_id.value,
                "item": item.content,
                "claude_prompt": item.generate_claude_prompt_template()[:200] + "...",
            }
            for item in priority_items[:8]
            if item.is_claude_suitable()
        ]

    def _build_source_content(
        self, checklist_data: A31ChecklistData, request: GenerateClaudeAnalysisRequest
    ) -> dict[str, Any]:
        """ソース内容を構築（PathServiceの標準命名に準拠）"""
        try:
            from noveler.infrastructure.adapters.path_service_adapter import create_path_service
            manuscript_name = create_path_service().get_manuscript_path(request.episode_number).name
        except Exception:
            manuscript_name = f"第{request.episode_number:03d}話_タイトル.md"
        return {
            "manuscript": manuscript_name,
            "analysis_scope": "full_content",
            "reference_checklist": request.checklist_file_path,
        }

    def _build_output_requirements(self, priority_items: list[A31PriorityItem]) -> dict[str, Any]:
        """出力要求を構築"""
        return {
            "format": "a31_integrated_feedback",
            "analysis_depth": "line_level",
            "include_components": [
                "quantitative_metrics",
                "specific_line_suggestions",
                "priority_item_evaluation",
                "improvement_effectiveness_prediction",
            ],
            "integration": {
                "update_a31_checklist": True,
                "save_prompt_records": True,
                "generate_improvement_report": True,
            },
        }

    def _build_metadata(
        self, priority_items: list[A31PriorityItem], checklist_data: A31ChecklistData
    ) -> dict[str, Any]:
        """メタデータを構築"""
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "extracted_items_count": len(priority_items),
            "high_priority_count": sum(1 for item in priority_items if item.is_high_priority()),
            "claude_suitable_count": sum(1 for item in priority_items if item.is_claude_suitable()),
            "source_checklist": {
                "total_items": len(checklist_data.get_all_items()),
                "target_episode": checklist_data.target_episode,
                "target_title": checklist_data.target_title,
            },
            "extraction_version": "1.0.0",
        }

    def _save_claude_request(self, claude_request: ClaudeAnalysisRequest, output_file_path: str) -> str:
        """Claude分析リクエストをファイル保存"""
        output_path = Path(output_file_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # バッチ書き込みを使用
        output_path.write_text(claude_request.to_yaml(), encoding="utf-8")

        return str(output_path)
