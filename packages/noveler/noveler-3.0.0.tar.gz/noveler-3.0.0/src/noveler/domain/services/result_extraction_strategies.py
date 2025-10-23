#!/usr/bin/env python3
"""結果抽出戦略パターン

仕様書: SPEC-CLAUDE-CODE-002
"""

import json
import re
from abc import ABC, abstractmethod
from typing import Any

from noveler.domain.value_objects.claude_code_execution import ClaudeCodeExecutionResponse
from noveler.domain.value_objects.universal_prompt_execution import PromptType


class ResultExtractor(ABC):
    """結果抽出戦略の基底クラス

    REQ-1.4: 結果解析・構造化データ取得（種別対応）
    """

    @abstractmethod
    def extract(self, response: ClaudeCodeExecutionResponse) -> dict[str, Any]:
        """結果抽出

        Args:
            response: Claude Code実行レスポンス

        Returns:
            Dict[str, Any]: 抽出された構造化データ
        """

    def _extract_json_content(self, content: str) -> dict[str, Any] | None:
        """JSONコンテンツ抽出（共通機能）"""
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Markdown形式のJSONブロック抽出を試行
            json_match = re.search(r"```json\s*(.*?)\s*```", content, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass
            return None

    def _extract_markdown_sections(self, content: str) -> dict[str, str]:
        """Markdownセクション抽出（共通機能）"""
        sections = {}
        current_section = None
        current_content = []

        for line in content.split("\n"):
            if line.startswith("##"):
                if current_section:
                    sections[current_section] = "\n".join(current_content).strip()
                current_section = line[2:].strip()
                current_content = []
            elif current_section:
                current_content.append(line)

        if current_section:
            sections[current_section] = "\n".join(current_content).strip()

        return sections


class WritingResultExtractor(ResultExtractor):
    """執筆結果抽出戦略

    REQ-3.2: 種別固有の結果抽出メソッド実装
    """

    def extract(self, response: ClaudeCodeExecutionResponse) -> dict[str, Any]:
        """執筆結果抽出"""
        extracted_data: dict[str, Any] = {}

        # JSON データからの抽出を優先
        if response.has_json_data():
            self._extract_from_json_data(response.json_data, extracted_data)

        # JSON から抽出できない場合は生コンテンツから抽出
        if "manuscript" not in extracted_data:
            self._extract_from_raw_content(response.response_content, extracted_data)

        return extracted_data

    def _extract_from_json_data(self, json_data: dict[str, Any], extracted_data: dict[str, Any]) -> None:
        """JSON データからの抽出"""
        # 原稿内容の抽出
        manuscript_keys = ["manuscript", "content", "text", "output", "result"]
        for key in manuscript_keys:
            if key in json_data:
                extracted_data["manuscript"] = json_data[key]
                break

        # メタデータの抽出
        if "metadata" in json_data:
            extracted_data["metadata"] = json_data["metadata"]

        # 統計情報の抽出
        stats_keys = ["word_count", "character_count", "statistics", "stats"]
        for key in stats_keys:
            if key in json_data:
                extracted_data["statistics"] = json_data[key]
                break

    def _extract_from_raw_content(self, content: str, extracted_data: dict[str, Any]) -> None:
        """生コンテンツからの抽出"""
        json_content = self._extract_json_content(content)
        if json_content and "manuscript" in json_content:
            extracted_data["manuscript"] = json_content["manuscript"]
        else:
            # Markdown セクションからの抽出
            sections = self._extract_markdown_sections(content)
            for section_name, section_content in sections.items():
                if any(keyword in section_name.lower() for keyword in ["原稿", "manuscript", "本文", "内容"]):
                    extracted_data["manuscript"] = section_content
                    break

            # セクションからも抽出できない場合は全体を原稿とみなす
            if "manuscript" not in extracted_data:
                extracted_data["manuscript"] = content


class PlotResultExtractor(ResultExtractor):
    """プロット結果抽出戦略

    REQ-3.2: 種別固有の結果抽出メソッド実装
    """

    def extract(self, response: ClaudeCodeExecutionResponse) -> dict[str, Any]:
        """プロット結果抽出"""
        extracted_data: dict[str, Any] = {}

        # JSONデータからの抽出を優先
        if response.has_json_data():
            json_data: dict[str, Any] = response.json_data

            # プロット構造の抽出
            plot_keys = ["plot", "episode_plot", "structure", "outline", "content"]
            for key in plot_keys:
                if key in json_data:
                    extracted_data["plot"] = json_data[key]
                    break

            # シーン情報の抽出
            scene_keys = ["scenes", "scene_list", "episode_scenes"]
            for key in scene_keys:
                if key in json_data:
                    extracted_data["scenes"] = json_data[key]
                    break

            # 品質評価の抽出
            quality_keys = ["quality", "evaluation", "assessment"]
            for key in quality_keys:
                if key in json_data:
                    extracted_data["quality"] = json_data[key]
                    break

        # JSONから抽出できない場合は生コンテンツから抽出
        if "plot" not in extracted_data:
            json_content = self._extract_json_content(response.response_content)
            if json_content:
                extracted_data["plot"] = json_content
            else:
                # Markdownセクションからの抽出
                sections = self._extract_markdown_sections(response.response_content)

                # プロット構造の抽出
                for section_name, content in sections.items():
                    if any(keyword in section_name.lower() for keyword in ["プロット", "plot", "構成", "あらすじ"]):
                        extracted_data["plot"] = content
                        break

                # シーン情報の抽出
                for section_name, content in sections.items():
                    if any(keyword in section_name.lower() for keyword in ["シーン", "scene", "場面"]):
                        extracted_data["scenes"] = content.split("\n")
                        break

                # 全体をプロットとみなす（最終フォールバック）
                if "plot" not in extracted_data:
                    extracted_data["plot"] = response.response_content

        return extracted_data


class QualityCheckResultExtractor(ResultExtractor):
    """品質チェック結果抽出戦略

    REQ-3.3: 品質評価・メタデータ管理機能
    """

    def extract(self, response: ClaudeCodeExecutionResponse) -> dict[str, Any]:
        """品質チェック結果抽出"""
        extracted_data: dict[str, Any] = {}

        # JSONデータからの抽出を優先
        if response.has_json_data():
            json_data: dict[str, Any] = response.json_data

            # 品質スコアの抽出
            score_keys = ["score", "total_score", "quality_score", "rating"]
            for key in score_keys:
                if key in json_data:
                    extracted_data["score"] = json_data[key]
                    break

            # 問題点の抽出
            issues_keys = ["issues", "problems", "violations", "errors"]
            for key in issues_keys:
                if key in json_data:
                    extracted_data["issues"] = json_data[key]
                    break

            # 推奨事項の抽出
            recommendations_keys = ["recommendations", "suggestions", "improvements"]
            for key in recommendations_keys:
                if key in json_data:
                    extracted_data["recommendations"] = json_data[key]
                    break

            # 詳細分析の抽出
            analysis_keys = ["analysis", "detailed_analysis", "breakdown"]
            for key in analysis_keys:
                if key in json_data:
                    extracted_data["analysis"] = json_data[key]
                    break

        # JSONから抽出できない場合は生コンテンツから抽出
        if not extracted_data:
            json_content = self._extract_json_content(response.response_content)
            if json_content:
                extracted_data: dict[str, Any] = json_content
            else:
                # Markdownセクションからの抽出
                sections = self._extract_markdown_sections(response.response_content)

                # スコア情報の抽出
                for section_name, content in sections.items():
                    if any(keyword in section_name.lower() for keyword in ["スコア", "score", "評価", "点数"]):
                        # 数値抽出を試行
                        score_match = re.search(r"(\d+(?:\.\d+)?)", content)
                        if score_match:
                            extracted_data["score"] = float(score_match.group(1))
                        break

                # 問題点の抽出
                for section_name, content in sections.items():
                    if any(keyword in section_name.lower() for keyword in ["問題", "issue", "エラー", "違反"]):
                        extracted_data["issues"] = content.split("\n")
                        break

                # 全体を分析結果とみなす（最終フォールバック）
                if not extracted_data:
                    extracted_data: dict[str, Any] = {"analysis": response.response_content}

        return extracted_data


class ResultExtractorFactory:
    """結果抽出戦略ファクトリー

    REQ-1.4: 種別に応じた適切な抽出戦略の提供
    """

    @staticmethod
    def create_extractor(prompt_type: PromptType) -> ResultExtractor:
        """プロンプト種別に応じた抽出戦略作成

        Args:
            prompt_type: プロンプト種別

        Returns:
            ResultExtractor: 対応する抽出戦略
        """
        if prompt_type == PromptType.WRITING:
            return WritingResultExtractor()
        if prompt_type == PromptType.PLOT:
            return PlotResultExtractor()
        if prompt_type == PromptType.QUALITY_CHECK:
            return QualityCheckResultExtractor()
        msg = f"Unsupported prompt type: {prompt_type}"
        raise ValueError(msg)
