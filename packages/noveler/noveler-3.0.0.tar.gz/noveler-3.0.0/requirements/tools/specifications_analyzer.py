#!/usr/bin/env python3
"""
仕様書自動分析スクリプト

277個の仕様書から要件を自動抽出・分析し、
要件定義書作成をサポートするツール
"""

import json
import re
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class Requirement:
    """抽出された要件"""
    id: str
    title: str
    description: str
    priority: str
    category: str
    specifications: list[str]
    keywords: list[str]
    complexity: int  # 1-5
    dependencies: list[str]


@dataclass
class SpecificationAnalysis:
    """仕様書分析結果"""
    file_path: str
    title: str
    overview: str
    purpose: str
    requirements_mentioned: list[str]
    keywords: list[str]
    complexity_score: float
    size_lines: int
    last_modified: str


class SpecificationsAnalyzer:
    """仕様書分析エンジン"""

    def __init__(self, specs_directory: Path):
        self.specs_dir = specs_directory
        self.analyses: list[SpecificationAnalysis] = []
        self.requirements: list[Requirement] = []

        # キーワード分類辞書
        self.category_keywords = {
            "プロット管理": ["plot", "プロット", "構造", "hierarchy", "階層"],
            "AI協創執筆": ["ai", "claude", "write", "generation", "執筆", "協創", "mcp"],
            "品質管理": ["quality", "品質", "check", "チェック", "a31", "評価"],
            "ワークフロー": ["workflow", "ワークフロー", "flow", "process", "進捗"],
            "CLI・UI": ["cli", "command", "interface", "ui", "コマンド"],
            "データ管理": ["data", "yaml", "repository", "データ", "管理"],
            "統合・連携": ["integration", "adapter", "統合", "連携", "api"],
            "システム管理": ["system", "monitor", "log", "システム", "監視"],
            "設定管理": ["config", "setting", "設定", "configuration"],
            "セキュリティ": ["security", "auth", "セキュリティ", "認証"]
        }

        # 優先度判定キーワード
        self.priority_keywords = {
            "Critical": ["critical", "重要", "必須", "required", "essential"],
            "High": ["high", "高", "important", "重要度高"],
            "Medium": ["medium", "中", "normal", "通常"],
            "Low": ["low", "低", "optional", "オプション"]
        }

    def analyze_all_specifications(self) -> dict[str, Any]:
        """全仕様書の分析実行"""
        print("🔍 仕様書分析開始...")

        spec_files = list(self.specs_dir.rglob("*.md"))
        spec_files = [f for f in spec_files if "archive" not in str(f)]

        print(f"📁 対象仕様書: {len(spec_files)}件")

        for spec_file in spec_files:
            try:
                analysis = self._analyze_single_specification(spec_file)
                self.analyses.append(analysis)
                print(f"  ✅ {spec_file.name}")
            except Exception as e:
                print(f"  ❌ {spec_file.name}: {e}")

        print("🔧 要件抽出・分析中...")
        self._extract_requirements()

        print("📊 分析結果生成中...")
        result = self._generate_analysis_report()

        print("✅ 仕様書分析完了")
        return result

    def _analyze_single_specification(self, spec_file: Path) -> SpecificationAnalysis:
        """単一仕様書の分析"""
        content = spec_file.read_text(encoding="utf-8", errors="ignore")

        # 基本情報抽出
        title = self._extract_title(content)
        overview = self._extract_overview(content)
        purpose = self._extract_purpose(content)

        # キーワード抽出
        keywords = self._extract_keywords(content)

        # 要件言及の抽出
        requirements_mentioned = self._find_requirement_mentions(content)

        # 複雑度スコア算出
        complexity_score = self._calculate_complexity_score(content)

        # ファイル情報
        size_lines = len(content.split("\n"))

        try:
            # Git last modified (可能であれば)
            result = subprocess.run(
                ["git", "log", "-1", "--format=%ai", str(spec_file)],
                check=False, capture_output=True, text=True, cwd=self.specs_dir.parent
            )
            last_modified = result.stdout.strip() if result.returncode == 0 else "Unknown"
        except:
            last_modified = "Unknown"

        return SpecificationAnalysis(
            file_path=str(spec_file),
            title=title,
            overview=overview,
            purpose=purpose,
            requirements_mentioned=requirements_mentioned,
            keywords=keywords,
            complexity_score=complexity_score,
            size_lines=size_lines,
            last_modified=last_modified
        )

    def _extract_title(self, content: str) -> str:
        """タイトル抽出"""
        lines = content.split("\n")
        for line in lines:
            if line.startswith("# "):
                return line[2:].strip()
        return "No Title"

    def _extract_overview(self, content: str) -> str:
        """概要セクション抽出"""
        patterns = [
            r"## 概要\n(.*?)(?=\n##|\n#|$)",
            r"## Overview\n(.*?)(?=\n##|\n#|$)",
            r"概要[：:](.*?)(?=\n|$)",
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.DOTALL | re.MULTILINE)
            if match:
                return match.group(1).strip()[:500]  # 最初の500文字

        # フォールバック: 最初の段落
        lines = [l.strip() for l in content.split("\n") if l.strip()]
        if len(lines) > 1:
            return lines[1][:200]
        return "No overview"

    def _extract_purpose(self, content: str) -> str:
        """目的・背景抽出"""
        patterns = [
            r"## 目的\n(.*?)(?=\n##|\n#|$)",
            r"## Purpose\n(.*?)(?=\n##|\n#|$)",
            r"## 背景\n(.*?)(?=\n##|\n#|$)",
            r"目的[：:](.*?)(?=\n|$)",
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.DOTALL | re.MULTILINE)
            if match:
                return match.group(1).strip()[:300]
        return "No purpose defined"

    def _extract_keywords(self, content: str) -> list[str]:
        """キーワード抽出"""
        keywords = []
        content_lower = content.lower()

        # カテゴリキーワードから抽出
        for category, category_keywords in self.category_keywords.items():
            for keyword in category_keywords:
                if keyword.lower() in content_lower:
                    keywords.append(keyword)

        # 技術キーワード抽出
        tech_keywords = [
            "python", "yaml", "json", "api", "cli", "git", "docker",
            "test", "テスト", "unit", "integration", "統合",
            "ddd", "clean architecture", "solid",
            "claude", "openai", "ai", "人工知能"
        ]

        for keyword in tech_keywords:
            if keyword.lower() in content_lower:
                keywords.append(keyword)

        return list(set(keywords))  # 重複除去

    def _find_requirement_mentions(self, content: str) -> list[str]:
        """要件言及の発見"""
        req_patterns = [
            r"REQ-[A-Z]+-\d+",
            r"要件[：:]([^。\n]+)",
            r"requirement[：:]([^。\n]+)",
            r"機能[：:]([^。\n]+)",
        ]

        mentioned = []
        for pattern in req_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            mentioned.extend(matches)

        return mentioned

    def _calculate_complexity_score(self, content: str) -> float:
        """複雑度スコア算出"""
        score = 0.0

        # ファイルサイズベース
        lines = len(content.split("\n"))
        score += min(lines / 100, 5.0)  # 最大5点

        # セクション数ベース
        sections = len(re.findall(r"^##", content, re.MULTILINE))
        score += min(sections / 10, 3.0)  # 最大3点

        # 技術用語密度ベース
        tech_terms = len(re.findall(r"\b(class|function|method|API|JSON|YAML)\b", content, re.IGNORECASE))
        score += min(tech_terms / 20, 2.0)  # 最大2点

        return round(score, 2)

    def _extract_requirements(self) -> None:
        """要件抽出・生成"""
        print("  🔍 要件パターン分析中...")

        # カテゴリ別にグループ化
        category_groups = defaultdict(list)
        for analysis in self.analyses:
            category = self._categorize_specification(analysis)
            category_groups[category].append(analysis)

        req_id_counter = 1

        for category, specs in category_groups.items():
            print(f"    📋 {category}: {len(specs)}件")

            # カテゴリ内で要件を統合・抽出
            category_requirements = self._extract_category_requirements(category, specs)

            for req in category_requirements:
                req.id = f"REQ-{category[:4].upper()}-{req_id_counter:03d}"
                req_id_counter += 1
                self.requirements.append(req)

    def _categorize_specification(self, analysis: SpecificationAnalysis) -> str:
        """仕様書のカテゴリ分類"""
        content = analysis.file_path + " " + analysis.title + " " + analysis.overview
        content_lower = content.lower()

        scores = {}
        for category, keywords in self.category_keywords.items():
            score = sum(1 for keyword in keywords if keyword.lower() in content_lower)
            if score > 0:
                scores[category] = score

        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]
        return "その他"

    def _extract_category_requirements(self, category: str, specs: list[SpecificationAnalysis]) -> list[Requirement]:
        """カテゴリ別要件抽出"""
        requirements = []

        # 仕様書を分析して要件パターンを抽出
        common_patterns = self._find_common_patterns(specs)

        for pattern in common_patterns:
            req = Requirement(
                id="",  # 後で設定
                title=pattern["title"],
                description=pattern["description"],
                priority=self._determine_priority(pattern),
                category=category,
                specifications=[s.file_path for s in specs if pattern["title"].lower() in s.overview.lower()],
                keywords=pattern["keywords"],
                complexity=pattern["complexity"],
                dependencies=[]
            )
            requirements.append(req)

        return requirements

    def _find_common_patterns(self, specs: list[SpecificationAnalysis]) -> list[dict[str, Any]]:
        """共通パターン発見"""
        patterns = []

        # キーワード頻度分析
        all_keywords = []
        for spec in specs:
            all_keywords.extend(spec.keywords)

        keyword_freq = Counter(all_keywords)
        common_keywords = [k for k, v in keyword_freq.most_common(10) if v >= 2]

        # 共通機能パターンの抽出
        if common_keywords:
            pattern = {
                "title": f"{common_keywords[0]}機能",
                "description": f"{common_keywords[0]}に関する機能要件",
                "keywords": common_keywords[:5],
                "complexity": min(5, max(1, len(specs))),
                "frequency": len(specs)
            }
            patterns.append(pattern)

        # 個別パターンの抽出
        for spec in specs:
            if spec.complexity_score > 3.0:  # 複雑な仕様書
                pattern = {
                    "title": spec.title,
                    "description": spec.overview,
                    "keywords": spec.keywords,
                    "complexity": min(5, int(spec.complexity_score)),
                    "frequency": 1
                }
                patterns.append(pattern)

        return patterns

    def _determine_priority(self, pattern: dict[str, Any]) -> str:
        """優先度判定"""
        keywords_text = " ".join(pattern.get("keywords", [])).lower()

        for priority, priority_keywords in self.priority_keywords.items():
            if any(kw in keywords_text for kw in priority_keywords):
                return priority

        # 頻度ベースの優先度判定
        frequency = pattern.get("frequency", 1)
        if frequency >= 5:
            return "Critical"
        if frequency >= 3:
            return "High"
        if frequency >= 2:
            return "Medium"
        return "Low"

    def _generate_analysis_report(self) -> dict[str, Any]:
        """分析レポート生成"""
        # カテゴリ別統計
        category_stats = defaultdict(int)
        for analysis in self.analyses:
            category = self._categorize_specification(analysis)
            category_stats[category] += 1

        # 要件統計
        requirement_stats = {
            "total": len(self.requirements),
            "by_category": defaultdict(int),
            "by_priority": defaultdict(int),
        }

        for req in self.requirements:
            requirement_stats["by_category"][req.category] += 1
            requirement_stats["by_priority"][req.priority] += 1

        # キーワード分析
        all_keywords = []
        for analysis in self.analyses:
            all_keywords.extend(analysis.keywords)
        keyword_frequency = dict(Counter(all_keywords).most_common(20))

        return {
            "summary": {
                "total_specifications": len(self.analyses),
                "total_requirements": len(self.requirements),
                "analysis_date": "2025-09-03",
                "average_complexity": sum(a.complexity_score for a in self.analyses) / len(self.analyses) if self.analyses else 0
            },
            "specifications": [
                {
                    "file_path": a.file_path,
                    "title": a.title,
                    "category": self._categorize_specification(a),
                    "complexity_score": a.complexity_score,
                    "size_lines": a.size_lines,
                    "keywords_count": len(a.keywords)
                }
                for a in self.analyses
            ],
            "requirements": [
                {
                    "id": r.id,
                    "title": r.title,
                    "category": r.category,
                    "priority": r.priority,
                    "complexity": r.complexity,
                    "specifications_count": len(r.specifications)
                }
                for r in self.requirements
            ],
            "statistics": {
                "category_distribution": dict(category_stats),
                "requirement_stats": dict(requirement_stats),
                "keyword_frequency": keyword_frequency,
                "complexity_distribution": {
                    "low": sum(1 for a in self.analyses if a.complexity_score < 2.0),
                    "medium": sum(1 for a in self.analyses if 2.0 <= a.complexity_score < 4.0),
                    "high": sum(1 for a in self.analyses if a.complexity_score >= 4.0)
                }
            }
        }

    def export_results(self, output_dir: Path) -> None:
        """結果エクスポート"""
        output_dir.mkdir(parents=True, exist_ok=True)

        # 分析レポートJSON出力
        report = self._generate_analysis_report()
        with open(output_dir / "specification_analysis_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        # 要件リストYAML出力
        requirements_data = {
            "requirements": [
                {
                    "id": r.id,
                    "title": r.title,
                    "description": r.description,
                    "priority": r.priority,
                    "category": r.category,
                    "specifications": r.specifications,
                    "keywords": r.keywords,
                    "complexity": r.complexity,
                    "dependencies": r.dependencies
                }
                for r in self.requirements
            ]
        }

        with open(output_dir / "extracted_requirements.yaml", "w", encoding="utf-8") as f:
            yaml.dump(requirements_data, f, allow_unicode=True, sort_keys=False, indent=2)

        # サマリーレポート生成
        self._generate_summary_report(output_dir / "analysis_summary.md", report)

        print(f"📄 結果エクスポート完了: {output_dir}")

    def _generate_summary_report(self, output_path: Path, report: dict[str, Any]) -> None:
        """サマリーレポート生成"""
        content = f"""# 仕様書分析サマリーレポート

**分析日時**: {report['summary']['analysis_date']}
**対象仕様書数**: {report['summary']['total_specifications']}件
**抽出要件数**: {report['summary']['total_requirements']}件
**平均複雑度**: {report['summary']['average_complexity']:.2f}

## カテゴリ別分布

| カテゴリ | 仕様書数 | 割合 |
|---------|---------|------|
"""

        total_specs = report["summary"]["total_specifications"]
        for category, count in report["statistics"]["category_distribution"].items():
            percentage = (count / total_specs * 100) if total_specs > 0 else 0
            content += f"| {category} | {count} | {percentage:.1f}% |\n"

        content += """
## 要件優先度分布

| 優先度 | 要件数 |
|-------|-------|
"""

        for priority, count in report["statistics"]["requirement_stats"]["by_priority"].items():
            content += f"| {priority} | {count} |\n"

        content += """
## トップキーワード

| キーワード | 出現頻度 |
|-----------|----------|
"""

        for keyword, freq in list(report["statistics"]["keyword_frequency"].items())[:10]:
            content += f"| {keyword} | {freq} |\n"

        content += f"""
## 複雑度分布

- **低複雑度** (< 2.0): {report['statistics']['complexity_distribution']['low']}件
- **中複雑度** (2.0-4.0): {report['statistics']['complexity_distribution']['medium']}件
- **高複雑度** (≥ 4.0): {report['statistics']['complexity_distribution']['high']}件

## 次のアクション

1. 高優先度要件の詳細分析
2. 要件間の依存関係分析
3. 実装計画の策定
4. テスト戦略の確定

---
*このレポートは自動生成されました*
"""

        output_path.write_text(content, encoding="utf-8")


def main():
    """メイン実行"""
    specs_dir = Path("specs")
    if not specs_dir.exists():
        specs_dir = Path()  # カレントディレクトリから検索

    analyzer = SpecificationsAnalyzer(specs_dir)

    print("🚀 仕様書自動分析ツール開始")
    print("=" * 50)

    # 分析実行
    report = analyzer.analyze_all_specifications()

    # 結果出力
    output_dir = Path("analysis_results")
    analyzer.export_results(output_dir)

    print("=" * 50)
    print("📊 分析結果サマリー:")
    print(f"  仕様書数: {report['summary']['total_specifications']}件")
    print(f"  抽出要件数: {report['summary']['total_requirements']}件")
    print(f"  平均複雑度: {report['summary']['average_complexity']:.2f}")
    print(f"  出力先: {output_dir}/")
    print("\n✅ 仕様書分析完了")


if __name__ == "__main__":
    main()
