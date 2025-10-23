#!/usr/bin/env python3

"""Domain.entities.test_error_diagnostic_engine
Where: Domain entity analysing test errors.
What: Captures error patterns, diagnostics, and fix suggestions.
Why: Supports automated assistance in resolving test failures.
"""

from __future__ import annotations

"""テストエラー診断エンジン - ドメインエンティティ

B20準拠のFC層実装。テストエラーの分類・診断・修正可能性判定を行う純粋関数群。
DDD構造に基づくドメインレイヤーのコアエンティティ。
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any


class TestErrorType(Enum):
    """テストエラー種別定義"""

    IMPORT_ERROR = "import_error"
    ATTRIBUTE_ERROR = "attribute_error"
    ASSERTION_FAILURE = "assertion_failure"
    TYPE_ERROR = "type_error"
    VALUE_ERROR = "value_error"
    FILE_NOT_FOUND = "file_not_found"
    KEY_ERROR = "key_error"
    NAME_ERROR = "name_error"
    SYNTAX_ERROR = "syntax_error"
    INDENTATION_ERROR = "indentation_error"
    FIXTURE_ERROR = "fixture_error"
    TIMEOUT_ERROR = "timeout_error"
    UNKNOWN_ERROR = "unknown_error"


class ErrorSeverityLevel(Enum):
    """テストエラー重要度定義"""

    CRITICAL = "critical"  # システム全体に影響
    HIGH = "high"         # 複数のテストに影響
    MEDIUM = "medium"     # 単一テストに影響
    LOW = "low"          # 軽微な問題


@dataclass(frozen=True)
class ErrorDiagnosticResult:
    """テストエラー診断結果値オブジェクト"""

    error_type: TestErrorType
    severity: ErrorSeverityLevel
    confidence: float  # 診断の確信度 (0.0-1.0)
    auto_fixable: bool  # 自動修正可能か
    priority_score: int  # 修正優先度スコア (1-100)
    affected_files: list[str]  # 影響を受けるファイル
    error_pattern: str  # エラーパターン
    root_cause_summary: str  # 根本原因の要約
    fix_suggestions: list[str]  # 修正提案
    related_errors: list[str] = None  # 関連エラー

    def __post_init__(self):
        if self.related_errors is None:
            object.__setattr__(self, "related_errors", [])

    def to_dict(self) -> dict[str, Any]:
        """辞書形式への変換"""
        return {
            "error_type": self.error_type.value,
            "severity": self.severity.value,
            "confidence": self.confidence,
            "auto_fixable": self.auto_fixable,
            "priority_score": self.priority_score,
            "affected_files": self.affected_files,
            "error_pattern": self.error_pattern,
            "root_cause_summary": self.root_cause_summary,
            "fix_suggestions": self.fix_suggestions,
            "related_errors": self.related_errors
        }


@dataclass(frozen=True)
class ErrorContext:
    """テストエラーのコンテキスト情報"""

    test_name: str
    test_file: str
    error_message: str
    stack_trace: str
    line_number: int | None = None
    test_type: str | None = None  # unit, integration, e2e
    test_markers: list[str] = None  # pytest markers
    execution_time: float = 0.0

    def __post_init__(self):
        if self.test_markers is None:
            object.__setattr__(self, "test_markers", [])


class ErrorDiagnosticEngine:
    """テストエラー診断エンジン

    B20準拠のFC層実装。すべてのメソッドは純粋関数として実装。
    テストエラーの分類・診断・修正可能性判定を担当。
    """

    @staticmethod
    def diagnose_error(context: ErrorContext) -> ErrorDiagnosticResult:
        """エラーの包括的診断

        Args:
            context: テストエラーのコンテキスト情報

        Returns:
            ErrorDiagnosticResult: 診断結果
        """
        # エラータイプの分類
        error_type = TestErrorDiagnosticEngine._classify_error_type(
            context.error_message,
            context.stack_trace
        )

        # 重要度の判定
        severity = TestErrorDiagnosticEngine._determine_severity(
            error_type,
            context
        )

        # 自動修正可能性の判定
        auto_fixable = TestErrorDiagnosticEngine._assess_auto_fixability(
            error_type,
            context
        )

        # 診断の確信度計算
        confidence = TestErrorDiagnosticEngine._calculate_confidence(
            error_type,
            context.error_message
        )

        # 優先度スコア計算
        priority_score = TestErrorDiagnosticEngine._calculate_priority_score(
            severity,
            error_type,
            confidence
        )

        # 影響ファイルの特定
        affected_files = TestErrorDiagnosticEngine._identify_affected_files(
            context.stack_trace,
            context.test_file
        )

        # エラーパターンの抽出
        error_pattern = TestErrorDiagnosticEngine._extract_error_pattern(
            context.error_message
        )

        # 根本原因の特定
        root_cause = TestErrorDiagnosticEngine._analyze_root_cause(
            error_type,
            context
        )

        # 修正提案の生成
        fix_suggestions = TestErrorDiagnosticEngine._generate_fix_suggestions(
            error_type,
            context,
            auto_fixable
        )

        # 関連エラーの特定
        related_errors = TestErrorDiagnosticEngine._identify_related_errors(
            error_type,
            context
        )

        return ErrorDiagnosticResult(
            error_type=error_type,
            severity=severity,
            confidence=confidence,
            auto_fixable=auto_fixable,
            priority_score=priority_score,
            affected_files=affected_files,
            error_pattern=error_pattern,
            root_cause_summary=root_cause,
            fix_suggestions=fix_suggestions,
            related_errors=related_errors
        )

    @staticmethod
    def _classify_error_type(error_message: str, stack_trace: str) -> TestErrorType:
        """エラータイプの分類（純粋関数）"""
        error_lower = error_message.lower()
        stack_trace.lower()

        # インポートエラーの検出
        if any(keyword in error_lower for keyword in ["importerror", "modulenotfounderror", "no module named"]):
            return TestErrorType.IMPORT_ERROR

        # 属性エラーの検出
        if "attributeerror" in error_lower:
            return TestErrorType.ATTRIBUTE_ERROR

        # アサーションエラーの検出
        if "assertionerror" in error_lower:
            return TestErrorType.ASSERTION_FAILURE

        # 型エラーの検出
        if "typeerror" in error_lower:
            return TestErrorType.TYPE_ERROR

        # 値エラーの検出
        if "valueerror" in error_lower:
            return TestErrorType.VALUE_ERROR

        # ファイル未発見エラーの検出
        if any(keyword in error_lower for keyword in ["filenotfounderror", "no such file"]):
            return TestErrorType.FILE_NOT_FOUND

        # キーエラーの検出
        if "keyerror" in error_lower:
            return TestErrorType.KEY_ERROR

        # 名前エラーの検出
        if "nameerror" in error_lower:
            return TestErrorType.NAME_ERROR

        # 構文エラーの検出
        if "syntaxerror" in error_lower:
            return TestErrorType.SYNTAX_ERROR

        # インデントエラーの検出
        if "indentationerror" in error_lower:
            return TestErrorType.INDENTATION_ERROR

        # フィクスチャエラーの検出
        if any(keyword in error_lower for keyword in ["fixture", "scope"]) and "error" in error_lower:
            return TestErrorType.FIXTURE_ERROR

        # タイムアウトエラーの検出
        if any(keyword in error_lower for keyword in ["timeout", "timeouterror"]):
            return TestErrorType.TIMEOUT_ERROR

        return TestErrorType.UNKNOWN_ERROR

    @staticmethod
    def _determine_severity(error_type: TestErrorType, context: ErrorContext) -> ErrorSeverityLevel:
        """重要度判定（純粋関数）"""
        # エラータイプ別の基本重要度
        type_severity_map = {
            TestErrorType.IMPORT_ERROR: ErrorSeverityLevel.CRITICAL,
            TestErrorType.SYNTAX_ERROR: ErrorSeverityLevel.CRITICAL,
            TestErrorType.INDENTATION_ERROR: ErrorSeverityLevel.HIGH,
            TestErrorType.FIXTURE_ERROR: ErrorSeverityLevel.HIGH,
            TestErrorType.ATTRIBUTE_ERROR: ErrorSeverityLevel.HIGH,
            TestErrorType.TYPE_ERROR: ErrorSeverityLevel.HIGH,
            TestErrorType.NAME_ERROR: ErrorSeverityLevel.HIGH,
            TestErrorType.ASSERTION_FAILURE: ErrorSeverityLevel.MEDIUM,
            TestErrorType.VALUE_ERROR: ErrorSeverityLevel.MEDIUM,
            TestErrorType.KEY_ERROR: ErrorSeverityLevel.MEDIUM,
            TestErrorType.FILE_NOT_FOUND: ErrorSeverityLevel.MEDIUM,
            TestErrorType.TIMEOUT_ERROR: ErrorSeverityLevel.LOW,
            TestErrorType.UNKNOWN_ERROR: ErrorSeverityLevel.MEDIUM,
        }

        base_severity = type_severity_map.get(error_type, ErrorSeverityLevel.MEDIUM)

        # コンテキストによる調整
        if context.test_type == "integration":
            # 統合テストは影響範囲が大きいため重要度を上げる
            if base_severity == ErrorSeverityLevel.MEDIUM:
                return ErrorSeverityLevel.HIGH
            if base_severity == ErrorSeverityLevel.LOW:
                return ErrorSeverityLevel.MEDIUM

        # 実行時間が長いテストの場合は重要度を下げる（パフォーマンステストの可能性）
        if context.execution_time > 10.0:
            if base_severity == ErrorSeverityLevel.HIGH:
                return ErrorSeverityLevel.MEDIUM

        return base_severity

    @staticmethod
    def _assess_auto_fixability(error_type: TestErrorType, context: ErrorContext) -> bool:
        """自動修正可能性の判定（純粋関数）"""
        # 自動修正しやすいエラータイプ
        easily_fixable = {
            TestErrorType.INDENTATION_ERROR,
            TestErrorType.IMPORT_ERROR,  # 相対インポートなど
            TestErrorType.SYNTAX_ERROR,  # 簡単な構文エラー
        }

        # 自動修正が困難なエラータイプ
        hard_to_fix = {
            TestErrorType.ASSERTION_FAILURE,  # ロジックの問題
            TestErrorType.FIXTURE_ERROR,      # テスト設計の問題
            TestErrorType.TIMEOUT_ERROR,      # パフォーマンスの問題
        }

        if error_type in easily_fixable:
            return True
        if error_type in hard_to_fix:
            return False
        # その他のエラータイプは条件によって判定
        return TestErrorDiagnosticEngine._assess_conditional_fixability(
            error_type,
            context
        )

    @staticmethod
    def _assess_conditional_fixability(error_type: TestErrorType, context: ErrorContext) -> bool:
        """条件付き自動修正可能性の判定（純粋関数）"""
        error_message = context.error_message.lower()

        if error_type == TestErrorType.ATTRIBUTE_ERROR:
            # 単純な属性名の間違いなら修正可能
            if "has no attribute" in error_message:
                return True
        elif error_type == TestErrorType.NAME_ERROR:
            # 変数名の間違いなら修正可能
            if "is not defined" in error_message:
                return True
        elif error_type == TestErrorType.TYPE_ERROR:
            # 引数の型チェックなら修正しやすい
            if "takes" in error_message and "argument" in error_message:
                return True

        return False

    @staticmethod
    def _calculate_confidence(error_type: TestErrorType, error_message: str) -> float:
        """診断の確信度計算（純粋関数）"""
        # エラータイプ別の基本確信度
        type_confidence_map = {
            TestErrorType.IMPORT_ERROR: 0.9,
            TestErrorType.SYNTAX_ERROR: 0.9,
            TestErrorType.INDENTATION_ERROR: 0.95,
            TestErrorType.ATTRIBUTE_ERROR: 0.8,
            TestErrorType.TYPE_ERROR: 0.8,
            TestErrorType.NAME_ERROR: 0.8,
            TestErrorType.ASSERTION_FAILURE: 0.7,
            TestErrorType.VALUE_ERROR: 0.7,
            TestErrorType.KEY_ERROR: 0.75,
            TestErrorType.FILE_NOT_FOUND: 0.85,
            TestErrorType.FIXTURE_ERROR: 0.8,
            TestErrorType.TIMEOUT_ERROR: 0.8,
            TestErrorType.UNKNOWN_ERROR: 0.4,
        }

        base_confidence = type_confidence_map.get(error_type, 0.5)

        # エラーメッセージの具体性による調整
        if len(error_message) > 100:  # 詳細なメッセージ
            return min(1.0, base_confidence + 0.1)
        if len(error_message) < 20:  # 短すぎるメッセージ
            return max(0.1, base_confidence - 0.2)

        return base_confidence

    @staticmethod
    def _calculate_priority_score(
        severity: ErrorSeverityLevel,
        error_type: TestErrorType,
        confidence: float
    ) -> int:
        """修正優先度スコア計算（純粋関数）"""
        # 重要度による基本スコア
        severity_score_map = {
            ErrorSeverityLevel.CRITICAL: 80,
            ErrorSeverityLevel.HIGH: 60,
            ErrorSeverityLevel.MEDIUM: 40,
            ErrorSeverityLevel.LOW: 20,
        }

        base_score = severity_score_map[severity]

        # エラータイプによる調整
        type_adjustment = {
            TestErrorType.IMPORT_ERROR: 15,      # 他への影響大
            TestErrorType.SYNTAX_ERROR: 15,     # 他への影響大
            TestErrorType.FIXTURE_ERROR: 10,    # テスト全体への影響
            TestErrorType.ASSERTION_FAILURE: -5, # 個別の問題
            TestErrorType.TIMEOUT_ERROR: -10,   # パフォーマンス問題
        }

        adjustment = type_adjustment.get(error_type, 0)

        # 確信度による調整
        confidence_adjustment = int((confidence - 0.5) * 20)

        final_score = base_score + adjustment + confidence_adjustment
        return max(1, min(100, final_score))

    @staticmethod
    def _identify_affected_files(stack_trace: str, test_file: str) -> list[str]:
        """影響を受けるファイルの特定（純粋関数）"""
        affected_files = {test_file}  # テストファイル自体は必ず含む

        # スタックトレースからファイルパスを抽出
        file_pattern = r'File "([^"]+\.py)"'
        matches = re.findall(file_pattern, stack_trace)

        for file_path in matches:
            # プロジェクト内のファイルのみを対象とする
            if not file_path.startswith(("/usr/", "/opt/", "/Library/")):
                affected_files.add(file_path)

        return list(affected_files)

    @staticmethod
    def _extract_error_pattern(error_message: str) -> str:
        """エラーパターンの抽出（純粋関数）"""
        # エラーメッセージから具体的な値を除去してパターン化
        patterns = [
            (r"'[^']*'", "'<value>'"),           # 文字列リテラル
            (r'"[^"]*"', '"<value>"'),           # 文字列リテラル
            (r"\b\d+\b", "<number>"),            # 数値
            (r"\b[a-zA-Z_]\w*\b(?=\s*=)", "<variable>"),  # 変数名
        ]

        pattern = error_message
        for regex, replacement in patterns:
            pattern = re.sub(regex, replacement, pattern)

        return pattern[:200]  # 長すぎる場合は切り詰める

    @staticmethod
    def _analyze_root_cause(error_type: TestErrorType, context: ErrorContext) -> str:
        """根本原因の分析（純粋関数）"""
        cause_analysis = {
            TestErrorType.IMPORT_ERROR: "モジュールまたはパッケージが見つからない、またはインポートパスが間違っている",
            TestErrorType.ATTRIBUTE_ERROR: "オブジェクトに存在しない属性にアクセスしようとした",
            TestErrorType.ASSERTION_FAILURE: "テストの期待値と実際の値が一致しない",
            TestErrorType.TYPE_ERROR: "関数やメソッドに間違った型の引数が渡された",
            TestErrorType.VALUE_ERROR: "正しい型だが不適切な値が使用された",
            TestErrorType.FILE_NOT_FOUND: "指定されたファイルやディレクトリが存在しない",
            TestErrorType.KEY_ERROR: "辞書に存在しないキーにアクセスしようとした",
            TestErrorType.NAME_ERROR: "定義されていない変数名や関数名が使用された",
            TestErrorType.SYNTAX_ERROR: "Pythonの構文規則に違反したコードが含まれている",
            TestErrorType.INDENTATION_ERROR: "インデントが正しくない",
            TestErrorType.FIXTURE_ERROR: "pytestのフィクスチャの設定や使用方法に問題がある",
            TestErrorType.TIMEOUT_ERROR: "処理時間が許容範囲を超えた",
            TestErrorType.UNKNOWN_ERROR: "特定できない問題が発生している",
        }

        base_cause = cause_analysis.get(error_type, "原因不明")

        # コンテキストからの追加情報
        if context.test_type:
            base_cause += f"（{context.test_type}テスト内での問題）"

        return base_cause

    @staticmethod
    def _generate_fix_suggestions(
        error_type: TestErrorType,
        context: ErrorContext,
        auto_fixable: bool
    ) -> list[str]:
        """修正提案の生成（純粋関数）"""
        suggestions_map = {
            TestErrorType.IMPORT_ERROR: [
                "インポートパスを確認してください",
                "必要なパッケージがインストールされているか確認してください",
                "相対インポートを絶対インポートに変更することを検討してください",
                "requirements.txtやsetup.pyに依存関係を追加してください"
            ],
            TestErrorType.ATTRIBUTE_ERROR: [
                "オブジェクトの型を確認してください",
                "属性名のスペルミスがないか確認してください",
                "オブジェクトが期待する型で初期化されているか確認してください",
                "APIドキュメントで正しい属性名を確認してください"
            ],
            TestErrorType.ASSERTION_FAILURE: [
                "期待値と実際の値を比較してください",
                "テストデータの準備が正しいか確認してください",
                "テスト対象の関数の実装を確認してください",
                "テストの前提条件を見直してください"
            ],
            TestErrorType.TYPE_ERROR: [
                "関数の引数の型を確認してください",
                "戻り値の型が期待されるものか確認してください",
                "型ヒントを追加して型チェックを改善してください",
                "引数の順序が正しいか確認してください"
            ],
            TestErrorType.VALUE_ERROR: [
                "引数の値の範囲や形式を確認してください",
                "入力値のバリデーションを追加してください",
                "設定値が適切な範囲内にあるか確認してください",
                "データの形式が期待されるものか確認してください"
            ],
            TestErrorType.FILE_NOT_FOUND: [
                "ファイルパスが正しいか確認してください",
                "テストデータファイルが存在するか確認してください",
                "相対パスから絶対パスへの変更を検討してください",
                "ファイルの配置場所を確認してください"
            ],
            TestErrorType.KEY_ERROR: [
                "辞書のキーが存在するか確認してください",
                "設定ファイルに必要なキーが含まれているか確認してください",
                "デフォルト値の使用を検討してください",
                "キー名のスペルミスがないか確認してください"
            ],
            TestErrorType.NAME_ERROR: [
                "変数名や関数名のスペルミスを確認してください",
                "必要なインポート文が含まれているか確認してください",
                "変数のスコープを確認してください",
                "定義の順序を確認してください"
            ],
            TestErrorType.SYNTAX_ERROR: [
                "構文エラーの箇所を修正してください",
                "括弧の対応を確認してください",
                "コロンや引用符の不足がないか確認してください",
                "Pythonのバージョンに対応した構文を使用してください"
            ],
            TestErrorType.INDENTATION_ERROR: [
                "インデントの一貫性を確認してください",
                "タブとスペースの混在を避けてください",
                "エディタの設定でインデントを可視化してください",
                "コードフォーマッターの使用を検討してください"
            ],
            TestErrorType.FIXTURE_ERROR: [
                "フィクスチャのスコープを確認してください",
                "フィクスチャの依存関係を確認してください",
                "フィクスチャの命名が正しいか確認してください",
                "conftest.pyの設定を確認してください"
            ],
            TestErrorType.TIMEOUT_ERROR: [
                "処理の最適化を検討してください",
                "タイムアウト時間の調整を検討してください",
                "非同期処理の使用を検討してください",
                "テストの分割を検討してください"
            ],
            TestErrorType.UNKNOWN_ERROR: [
                "エラーメッセージの詳細を確認してください",
                "スタックトレースを詳細に分析してください",
                "似たようなエラーの解決例を検索してください",
                "コードの該当箇所を段階的にデバッグしてください"
            ]
        }

        base_suggestions = suggestions_map.get(error_type, [])

        # 自動修正可能な場合の追加提案
        if auto_fixable:
            base_suggestions.insert(0, "このエラーは自動修正が可能です。LLMによる修正を実行してください")

        return base_suggestions[:4]  # 最大4つの提案に制限

    @staticmethod
    def _identify_related_errors(error_type: TestErrorType, context: ErrorContext) -> list[str]:
        """関連エラーの特定（純粋関数）"""
        related_errors_map = {
            TestErrorType.IMPORT_ERROR: [
                "ModuleNotFoundError",
                "AttributeError (モジュール属性)",
                "NameError (インポートされていない名前)"
            ],
            TestErrorType.ATTRIBUTE_ERROR: [
                "TypeError (None型への属性アクセス)",
                "NameError (未定義オブジェクト)"
            ],
            TestErrorType.TYPE_ERROR: [
                "AttributeError (型に存在しない属性)",
                "ValueError (型は正しいが値が不適切)"
            ],
            TestErrorType.SYNTAX_ERROR: [
                "IndentationError",
                "NameError (構文エラー後の影響)"
            ],
            TestErrorType.FIXTURE_ERROR: [
                "AttributeError (フィクスチャが提供されない)",
                "NameError (フィクスチャ名の間違い)"
            ]
        }

        return related_errors_map.get(error_type, [])
