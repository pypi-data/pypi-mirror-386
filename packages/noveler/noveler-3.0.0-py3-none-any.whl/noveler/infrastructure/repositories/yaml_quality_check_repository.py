"""Infrastructure.repositories.yaml_quality_check_repository
Where: Infrastructure repository persisting quality check data in YAML.
What: Stores quality records, violations, and history for quality workflows.
Why: Enables durable storage of quality check results across sessions.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""YAML品質チェックリポジトリ(インフラ層実装)

YAMLファイルベースの品質チェックリポジトリ実装。
ドメイン層のインターフェースを実装し、具体的な永続化を担当。
"""


from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from noveler.domain.entities.quality_check_aggregate import (
    QualityCheckConfiguration,
    QualityCheckResult,
    QualityRule,
    QualityViolation,
    RuleCategory,
    Severity,
)
from noveler.domain.repositories.quality_check_repository import QualityCheckRepository
from noveler.domain.value_objects.completion_status import QualityCheckResult as CompletionQualityCheckResult
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now
from noveler.domain.value_objects.quality_threshold import QualityThreshold
from noveler.infrastructure.adapters.path_service_adapter import create_path_service

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


# Phase 6修正: Infrastructure内循環依存解消
# from noveler.infrastructure.adapters.path_service_adapter import create_path_service


class YamlQualityCheckRepository(QualityCheckRepository):
    """YAML品質チェックリポジトリ

    品質チェックに関するデータをYAMLファイルで管理する実装。
    """

    def __init__(self, project_root: Path | str | None = None) -> None:
        self.project_root = Path(project_root) if isinstance(project_root, str) else (project_root or Path.cwd())
        path_service = create_path_service(self.project_root)
        self.management_dir = path_service.get_management_dir()
        self.quality_config_file = self.management_dir / "品質チェック設定.yaml"
        self.quality_record_file = self.management_dir / "品質記録.yaml"

        # ディレクトリが存在しない場合は作成
        self.management_dir.mkdir(exist_ok=True)

    def get_default_rules(self) -> list[QualityRule]:
        """デフォルトの品質ルールを取得"""
        config = self.get_configuration()
        return self._load_rules_from_config(config)

    def get_rules_by_category(self, category: str | RuleCategory) -> list[QualityRule]:
        """カテゴリ別の品質ルールを取得"""
        all_rules = self.get_default_rules()
        category_value = category.value if isinstance(category, RuleCategory) else category
        return [rule for rule in all_rules if rule.category.value == category_value]

    def get_quality_threshold(self) -> QualityThreshold:
        """品質閾値を取得"""
        config = self.get_configuration()
        return config.min_quality_score

    def save_result(self, result: QualityCheckResult) -> None:
        """品質チェック結果を保存"""
        # 既存の品質記録を読み込み
        quality_record = self._load_quality_record()

        # 新しい結果を追加
        result_dict = self._result_to_dict(result)

        if "checks" not in quality_record:
            quality_record["checks"] = []

        quality_record["checks"].append(result_dict)

        # メタデータを更新
        if "metadata" not in quality_record:
            quality_record["metadata"] = {}

        quality_record["metadata"]["last_updated"] = project_now().datetime.strftime("%Y-%m-%d")

        # ファイルに保存
        self._save_quality_record(quality_record)

    def find_result_by_id(self, check_id: str) -> QualityCheckResult | None:
        """IDで品質チェック結果を検索"""
        quality_record = self._load_quality_record()

        if "checks" not in quality_record:
            return None

        for check_dict in quality_record["checks"]:
            if check_dict.get("check_id") == check_id:
                return self._dict_to_result(check_dict)

        return None

    def find_results_by_episode(self, episode_id: str) -> list[QualityCheckResult]:
        """エピソードIDで品質チェック結果を検索"""
        quality_record = self._load_quality_record()

        if "checks" not in quality_record:
            return []

        results: list[Any] = []
        for check_dict in quality_record["checks"]:
            if check_dict.get("episode_id") == episode_id:
                result = self._dict_to_result(check_dict)
                if result:
                    results.append(result)

        return results

    def get_configuration(self) -> QualityCheckConfiguration:
        """品質チェック設定を取得"""
        if not self.quality_config_file.exists():
            # デフォルト設定を作成
            default_config: dict[str, Any] = self._create_default_configuration()
            self.save_configuration(default_config)
            return default_config

        try:
            with Path(self.quality_config_file).open(encoding="utf-8") as f:
                config_dict = yaml.safe_load(f)

            return self._dict_to_configuration(config_dict)

        except Exception:
            # エラーの場合はデフォルト設定を返す
            return self._create_default_configuration()

    def save_configuration(self, config: QualityCheckConfiguration) -> None:
        """品質チェック設定を保存"""
        config_dict = self._configuration_to_dict(config)

        with Path(self.quality_config_file).open("w", encoding="utf-8") as f:
            yaml.dump(config_dict, f, allow_unicode=True, default_flow_style=False)

    def delete_result(self, check_id: str) -> bool:
        """品質チェック結果を削除"""
        quality_record = self._load_quality_record()

        if "checks" not in quality_record:
            return False

        original_count = len(quality_record["checks"])
        quality_record["checks"] = [check for check in quality_record["checks"] if check.get("check_id") != check_id]

        deleted = len(quality_record["checks"]) < original_count

        if deleted:
            self._save_quality_record(quality_record)

        return deleted

    # ------------------------------
    # B20準拠: ドメインIF実装追加
    # ------------------------------
    def check_quality(self, project_name: str, episode_number: int, content: str | None = None) -> CompletionQualityCheckResult:  # type: ignore[override]
        """エピソードの品質をチェック（簡易実装）

        既存ルールの一部を用いて簡易的に減点方式でスコアを算出します。
        content が省略の場合は空文字列として処理します。
        """
        from noveler.domain.value_objects.quality_score import QualityScore
        from noveler.domain.value_objects.completion_status import QualityCheckResult as CompletionQualityCheckResult

        text = content or ""

        # ルール読込（enabledのみ）
        rules = self.get_default_rules()

        total_penalty = 0.0
        issues: list[str] = []

        try:
            import re

            for rule in rules:
                if hasattr(rule, "enabled") and not getattr(rule, "enabled"):
                    continue
                pattern = getattr(rule, "pattern", None)
                if not pattern:
                    continue
                try:
                    matches = re.findall(pattern, text, flags=re.MULTILINE)
                    if matches:
                        penalty = float(getattr(rule, "penalty_score", 1.0)) * len(matches)
                        total_penalty += penalty
                        issues.append(f"{rule.name}: {len(matches)}件検出")
                except re.error:
                    # パターンが無効な場合はスキップ
                    continue
        except Exception:
            # 解析失敗時はペナルティ0で継続
            pass

        score_value = max(0.0, 100.0 - total_penalty)
        score = QualityScore.from_float(score_value)

        threshold = float(self.get_quality_threshold().value)
        result = CompletionQualityCheckResult.from_score(score, threshold=threshold)

        # issuesを反映
        if issues:
            result = CompletionQualityCheckResult(score=score, passed=result.passed, issues=issues)
        return result

    def auto_fix_content(self, content: str, issues: list[str]) -> tuple[str, CompletionQualityCheckResult]:  # type: ignore[override]
        """コンテンツの簡易自動修正（B20簡易版）

        - 三点リーダー: "..."/"。。。" を "…" に正規化
        - 感嘆符の連続: "!!"以上を単一の "!" に縮約
        - 文末表現の重複: "です。\s*です。" を1つに縮約
        その後、check_qualityで再評価します。
        """
        import re

        fixed = content or ""
        try:
            fixed = fixed.replace("...", "…")
            fixed = fixed.replace("。。。", "…")
            fixed = re.sub(r"!{2,}", "!", fixed)
            fixed = re.sub(r"(です。)\s*(です。)", r"\1", fixed)
        except Exception:
            # 修正処理でエラーが出ても元文を返す
            fixed = content or ""

        # 再評価（プロジェクト名/話数はスコープ外のためダミー値）
        rechecked = self.check_quality(project_name="", episode_number=0, content=fixed)
        return fixed, rechecked

    def _load_quality_record(self) -> dict[str, Any]:
        """品質記録ファイルを読み込み"""
        if not self.quality_record_file.exists():
            return {"metadata": {"created": project_now().datetime.strftime("%Y-%m-%d")}}

        try:
            with Path(self.quality_record_file).open(encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}

    def _save_quality_record(self, quality_record: dict[str, Any]) -> None:
        """品質記録ファイルを保存"""
        with Path(self.quality_record_file).open("w", encoding="utf-8") as f:
            yaml.dump(quality_record, f, allow_unicode=True, default_flow_style=False)

    def _create_default_configuration(self) -> QualityCheckConfiguration:
        """デフォルトの品質チェック設定を作成"""
        return QualityCheckConfiguration(
            min_quality_score=QualityThreshold(
                name="最小品質スコア",
                value=70.0,
                min_value=0.0,
                max_value=100.0,
            ),
            enabled_categories=[
                RuleCategory.BASIC_STYLE,
                RuleCategory.COMPOSITION,
                RuleCategory.READABILITY,
            ],
            severity_weights={
                Severity.ERROR: 2.0,
                Severity.WARNING: 1.0,
                Severity.INFO: 0.5,
            },
        )

    def _load_rules_from_config(self, config: QualityCheckConfiguration) -> list[QualityRule]:
        """設定から品質ルールを読み込み"""
        # 基本的な品質ルールを定義
        default_rules = [
            QualityRule(
                rule_id="basic_001",
                name="三点リーダー",
                description="三点リーダーは「…」を使用する",
                category=RuleCategory.BASIC_STYLE,
                severity=Severity.WARNING,
                pattern=r"\\.{3}|。{3}",
                enabled=True,
                penalty_score=5.0,
            ),
            QualityRule(
                rule_id="basic_002",
                name="感嘆符の使いすぎ",
                description="感嘆符は連続使用を避ける",
                category=RuleCategory.BASIC_STYLE,
                severity=Severity.WARNING,
                pattern=r"!{2,}",
                enabled=True,
                penalty_score=3.0,
            ),
            QualityRule(
                rule_id="basic_003",
                name="文末表現の重複",
                description="同じ文末表現の連続を避ける",
                category=RuleCategory.BASIC_STYLE,
                severity=Severity.WARNING,
                pattern=r"です。\s*です。",
                enabled=True,
                penalty_score=5.0,
            ),
            QualityRule(
                rule_id="comp_001",
                name="段落の長さ",
                description="段落が長すぎる場合の警告",
                category=RuleCategory.COMPOSITION,
                severity=Severity.INFO,
                enabled=True,
                penalty_score=2.0,
            ),
        ]

        # 有効なカテゴリのルールのみを返す
        if config.enabled_categories:
            return [rule for rule in default_rules if rule.category in config.enabled_categories]

        return default_rules

    def _result_to_dict(self, result: QualityCheckResult) -> dict[str, Any]:
        """品質チェック結果を辞書に変換"""
        return result.to_dict()

    def _dict_to_result(self, result_dict: dict[str, Any]) -> QualityCheckResult | None:
        """辞書を品質チェック結果に変換"""
        try:
            violations: list[Any] = []
            if "violations" in result_dict:
                for v_dict in result_dict["violations"]:
                    violation = QualityViolation(
                        rule_id=v_dict["rule_id"],
                        line_number=v_dict["line_number"],
                        column_number=v_dict["column_number"],
                        severity=Severity(v_dict["severity"]),
                        message=v_dict["message"],
                        context=v_dict.get("context", ""),
                    )

                    violations.append(violation)

            return QualityCheckResult(
                check_id=result_dict["check_id"],
                episode_id=result_dict["episode_id"],
                violations=violations,
                total_score=result_dict["total_score"],
                executed_at=datetime.fromisoformat(result_dict["executed_at"]),
            )

        except Exception:
            return None

    def _configuration_to_dict(self, config: QualityCheckConfiguration) -> dict[str, Any]:
        """品質チェック設定を辞書に変換"""
        return {
            "min_quality_score": {
                "name": config.min_quality_score.name,
                "value": config.min_quality_score.value,
                "min_value": config.min_quality_score.min_value,
                "max_value": config.min_quality_score.max_value,
            },
            "enabled_categories": [cat.value for cat in config.enabled_categories],
            "severity_weights": {sev.value: weight for sev, weight in config.severity_weights.items()},
        }

    def _dict_to_configuration(self, config_dict: dict[str, Any]) -> QualityCheckConfiguration:
        """辞書を品質チェック設定に変換"""
        threshold_dict = config_dict.get("min_quality_score", {})
        min_quality_score = QualityThreshold(
            name=threshold_dict.get("name", "最小品質スコア"),
            value=threshold_dict.get("value", 70.0),
            min_value=threshold_dict.get("min_value", 0.0),
            max_value=threshold_dict.get("max_value", 100.0),
        )

        enabled_categories = [RuleCategory(cat) for cat in config_dict.get("enabled_categories", [])]

        severity_weights = {}
        weight_dict = config_dict.get("severity_weights", {})
        for sev_str, weight in weight_dict.items():
            severity_weights[Severity(sev_str)] = weight

        return QualityCheckConfiguration(
            min_quality_score=min_quality_score,
            enabled_categories=enabled_categories,
            severity_weights=severity_weights,
        )
