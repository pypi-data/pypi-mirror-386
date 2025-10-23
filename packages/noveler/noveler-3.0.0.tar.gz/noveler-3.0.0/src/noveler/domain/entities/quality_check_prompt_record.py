#!/usr/bin/env python3
"""品質チェックプロンプト記録エンティティ

各品質チェック項目実行時のプロンプト内容と結果を構造化して保存・管理する
ドメインエンティティ。品質向上プロセスのトレーサビリティを確保。
"""

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from noveler.domain.value_objects.a31_evaluation_category import A31EvaluationCategory
from noveler.domain.value_objects.execution_result import ExecutionResult


@dataclass
class PromptContent:
    """プロンプト内容バリューオブジェクト"""

    template_id: str  # プロンプトテンプレートID
    raw_prompt: str  # 実際に使用したプロンプト文
    parameters: dict[str, Any]  # プロンプトパラメータ
    expected_output_format: str  # 期待する出力形式
    input_hash: str  # 入力内容のハッシュ値

    def calculate_prompt_complexity(self) -> float:
        """プロンプト複雑度計算

        Returns:
            float: 複雑度スコア（0-100）
        """
        complexity_factors = []

        # プロンプト長による複雑度
        length_complexity = min(100.0, len(self.raw_prompt) / 50)
        complexity_factors.append(length_complexity)

        # パラメータ数による複雑度
        param_complexity = min(100.0, len(self.parameters) * 10)
        complexity_factors.append(param_complexity)

        # 特殊指示の有無による複雑度
        special_instructions = sum(
            1 for keyword in ["例：", "具体的に", "詳細に", "分析"] if keyword in self.raw_prompt
        )
        instruction_complexity = min(100.0, special_instructions * 15)
        complexity_factors.append(instruction_complexity)

        return sum(complexity_factors) / len(complexity_factors) if complexity_factors else 0.0


@dataclass
class ExecutionMetadata:
    """実行メタデータバリューオブジェクト"""

    analyzer_version: str  # 分析エンジンバージョン
    environment_info: dict[str, str]  # 環境情報
    execution_context: dict[str, Any]  # 実行コンテキスト
    quality_threshold: float  # 品質閾値
    enhanced_analysis_enabled: bool = True  # 高度分析有効フラグ

    def get_environment_signature(self) -> str:
        """環境シグネチャ生成

        Returns:
            str: 環境識別用シグネチャ
        """
        key_info = [
            self.analyzer_version,
            self.environment_info.get("python_version", ""),
            self.environment_info.get("system_type", ""),
            str(self.enhanced_analysis_enabled),
        ]
        return "_".join(key_info)


class QualityCheckPromptRecord:
    """品質チェックプロンプト記録エンティティ

    各品質チェック項目実行時のプロンプト内容と結果を構造化保存し、
    品質向上プロセスのトレーサビリティを提供するドメインエンティティ。
    """

    def __init__(
        self,
        project_name: str,
        episode_number: int,
        check_category: A31EvaluationCategory,
        prompt_content: PromptContent,
        execution_result: ExecutionResult,
        execution_metadata: ExecutionMetadata,
        record_id: str | None = None,
        created_at: datetime | None = None,
    ) -> None:
        """品質チェックプロンプト記録初期化

        Args:
            project_name: プロジェクト名
            episode_number: エピソード番号
            check_category: チェックカテゴリ
            prompt_content: プロンプト内容
            execution_result: 実行結果
            execution_metadata: 実行メタデータ
            record_id: 記録ID（オプション）
            created_at: 作成日時（オプション）
        """
        self._record_id = record_id or str(uuid.uuid4())
        self._project_name = project_name
        self._episode_number = episode_number
        self._check_category = check_category
        self._prompt_content = prompt_content
        self._execution_result = execution_result
        self._execution_metadata = execution_metadata
        self._created_at = created_at or datetime.now(timezone.utc)
        self._last_accessed_at: datetime | None = None

    @classmethod
    def create(
        cls,
        project_name: str,
        episode_number: int,
        check_category: A31EvaluationCategory,
        prompt_content: PromptContent,
        execution_result: ExecutionResult,
        execution_metadata: ExecutionMetadata,
    ) -> "QualityCheckPromptRecord":
        """品質チェックプロンプト記録生成

        Args:
            project_name: プロジェクト名
            episode_number: エピソード番号
            check_category: チェックカテゴリ
            prompt_content: プロンプト内容
            execution_result: 実行結果
            execution_metadata: 実行メタデータ

        Returns:
            QualityCheckPromptRecord: 新規記録インスタンス
        """
        return cls(
            project_name=project_name,
            episode_number=episode_number,
            check_category=check_category,
            prompt_content=prompt_content,
            execution_result=execution_result,
            execution_metadata=execution_metadata,
        )

    @property
    def record_id(self) -> str:
        """記録ID"""
        return self._record_id

    @property
    def project_name(self) -> str:
        """プロジェクト名"""
        return self._project_name

    @property
    def episode_number(self) -> int:
        """エピソード番号"""
        return self._episode_number

    @property
    def check_category(self) -> A31EvaluationCategory:
        """チェックカテゴリ"""
        return self._check_category

    @property
    def prompt_content(self) -> PromptContent:
        """プロンプト内容"""
        return self._prompt_content

    @property
    def execution_result(self) -> ExecutionResult:
        """実行結果"""
        return self._execution_result

    @property
    def execution_metadata(self) -> ExecutionMetadata:
        """実行メタデータ"""
        return self._execution_metadata

    @property
    def created_at(self) -> datetime:
        """作成日時"""
        return self._created_at

    @property
    def last_accessed_at(self) -> datetime | None:
        """最終アクセス日時"""
        return self._last_accessed_at

    def mark_accessed(self) -> None:
        """アクセス記録更新"""
        self._last_accessed_at = datetime.now(timezone.utc)

    def is_successful_execution(self) -> bool:
        """実行成功判定

        Returns:
            bool: 実行成功の場合True
        """
        return self._execution_result.success

    def get_effectiveness_score(self) -> float:
        """効果性スコア取得

        Returns:
            float: 効果性スコア（0-100）
        """
        return self._execution_result.calculate_effectiveness_score()

    def get_prompt_complexity(self) -> float:
        """プロンプト複雑度取得

        Returns:
            float: プロンプト複雑度（0-100）
        """
        return self._prompt_content.calculate_prompt_complexity()

    def get_critical_issues_count(self) -> int:
        """重要問題数取得

        Returns:
            int: 重要問題数
        """
        return len(self._execution_result.get_critical_issues())

    def calculate_quality_impact(self) -> float:
        """品質インパクト計算

        Returns:
            float: 品質インパクトスコア（0-100）
        """
        if not self.is_successful_execution():
            return 0.0

        impact_factors = []

        # 効果性スコアによるインパクト
        effectiveness_impact = self.get_effectiveness_score() * 0.4
        impact_factors.append(effectiveness_impact)

        # 重要問題検出によるインパクト
        critical_issues_impact = min(100.0, self.get_critical_issues_count() * 25) * 0.3
        impact_factors.append(critical_issues_impact)

        # 信頼度によるインパクト
        confidence_impact = self._execution_result.confidence_score * 100 * 0.2
        impact_factors.append(confidence_impact)

        # プロンプト複雑度によるインパクト（複雑なほど価値が高い）
        complexity_impact = self.get_prompt_complexity() * 0.1
        impact_factors.append(complexity_impact)

        return sum(impact_factors)

    def to_summary_dict(self) -> dict[str, Any]:
        """サマリー辞書変換

        Returns:
            dict[str, Any]: サマリー辞書
        """
        return {
            "record_id": self._record_id,
            "project_name": self._project_name,
            "episode_number": self._episode_number,
            "check_category": self._check_category.value,
            "created_at": self._created_at.isoformat(),
            "success": self.is_successful_execution(),
            "effectiveness_score": self.get_effectiveness_score(),
            "prompt_complexity": self.get_prompt_complexity(),
            "quality_impact": self.calculate_quality_impact(),
            "issues_count": len(self._execution_result.issues_found),
            "critical_issues_count": self.get_critical_issues_count(),
            "suggestions_count": len(self._execution_result.suggestions),
            "processing_time": self._execution_result.processing_time,
            "confidence_score": self._execution_result.confidence_score,
        }

    def to_detailed_dict(self) -> dict[str, Any]:
        """詳細辞書変換

        Returns:
            dict[str, Any]: 詳細辞書
        """
        base_dict = self.to_summary_dict()

        # 詳細情報を追加
        base_dict.update(
            {
                "prompt_content": {
                    "template_id": self._prompt_content.template_id,
                    "raw_prompt": self._prompt_content.raw_prompt,
                    "parameters": self._prompt_content.parameters,
                    "expected_output_format": self._prompt_content.expected_output_format,
                    "input_hash": self._prompt_content.input_hash,
                },
                "execution_result": {
                    "output_content": self._execution_result.output_content,
                    "issues_found": [
                        {
                            "type": issue.issue_type,
                            "line_number": issue.line_number,
                            "description": issue.description,
                            "severity": issue.severity,
                            "confidence": issue.confidence,
                        }
                        for issue in self._execution_result.issues_found
                    ],
                    "suggestions": [
                        {
                            "type": suggestion.suggestion_type,
                            "content": suggestion.content,
                            "expected_impact": suggestion.expected_impact,
                            "implementation_difficulty": suggestion.implementation_difficulty,
                        }
                        for suggestion in self._execution_result.suggestions
                    ],
                    "error_message": self._execution_result.error_message,
                },
                "execution_metadata": {
                    "analyzer_version": self._execution_metadata.analyzer_version,
                    "environment_info": self._execution_metadata.environment_info,
                    "execution_context": self._execution_metadata.execution_context,
                    "quality_threshold": self._execution_metadata.quality_threshold,
                    "enhanced_analysis_enabled": self._execution_metadata.enhanced_analysis_enabled,
                    "environment_signature": self._execution_metadata.get_environment_signature(),
                },
                "last_accessed_at": self._last_accessed_at.isoformat() if self._last_accessed_at else None,
            }
        )

        return base_dict

    def __str__(self) -> str:
        """文字列表現"""
        return (
            f"QualityCheckPromptRecord("
            f"project={self._project_name}, "
            f"episode={self._episode_number}, "
            f"category={self._check_category.value}, "
            f"success={self.is_successful_execution()})"
        )

    def __repr__(self) -> str:
        """デバッグ表現"""
        return (
            f"QualityCheckPromptRecord("
            f"record_id='{self._record_id}', "
            f"project_name='{self._project_name}', "
            f"episode_number={self._episode_number}, "
            f"check_category={self._check_category}, "
            f"created_at={self._created_at})"
        )
