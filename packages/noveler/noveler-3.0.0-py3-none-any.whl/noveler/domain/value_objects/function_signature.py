"""Domain.value_objects.function_signature
Where: Domain value object module defining typed data structures.
What: Declares dataclasses and helpers used to pass structured domain data.
Why: Keeps domain data definitions consistent across services and entities.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""関数シグネチャValue Object

仕様書: SPEC-NIH-PREVENTION-CODEMAP-001, SPEC-ARCH-002
FC/IS純粋関数保証機能統合
"""


import functools
import hashlib
import re
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, TypeVar

from noveler.domain.value_objects.import_statement import ImportStatement

if TYPE_CHECKING:
    from pathlib import Path

# FC/IS純粋関数デコレータ用
F = TypeVar("F", bound=Callable[..., Any])


@dataclass(frozen=True)
class FunctionSignature:
    """関数シグネチャ表現"""

    # 基本情報
    name: str
    module_path: str
    file_path: Path
    line_number: int

    # 関数構造
    parameters: list[str] = field(default_factory=list)
    return_type: str | None = None
    decorators: list[str] = field(default_factory=list)

    # 意味情報
    docstring: str | None = None
    comments: list[str] = field(default_factory=list)

    # 構文構造
    ast_structure_hash: str | None = None
    control_flow_patterns: list[str] = field(default_factory=list)

    # メタ情報
    imports_used: list[ImportStatement] = field(default_factory=list)
    calls_made: list[str] = field(default_factory=list)
    variables_accessed: set[str] = field(default_factory=set)

    # DDD層情報
    ddd_layer: str | None = None
    responsibility_category: str | None = None

    def get_semantic_tokens(self) -> list[str]:
        """意味的トークンの取得"""
        tokens = []

        # 関数名の分割（キャメルケース・スネークケース対応）
        tokens.extend(self._split_identifier(self.name))

        # パラメータ名
        for param in self.parameters:
            tokens.extend(self._split_identifier(param))

        # docstringからのキーワード抽出
        if self.docstring:
            tokens.extend(self._extract_keywords_from_text(self.docstring))

        # コメントからのキーワード抽出
        for comment in self.comments:
            tokens.extend(self._extract_keywords_from_text(comment))

        return [token.lower() for token in tokens if token.isalnum()]

    def get_structural_features(self) -> dict[str, int]:
        """構造的特徴の取得"""
        return {
            "parameter_count": len(self.parameters),
            "decorator_count": len(self.decorators),
            "import_count": len(self.imports_used),
            "call_count": len(self.calls_made),
            "variable_access_count": len(self.variables_accessed),
            "control_flow_complexity": len(self.control_flow_patterns),
        }

    def get_functional_characteristics(self) -> dict[str, bool]:
        """機能的特性の取得"""
        characteristics = {}

        # 純粋関数かどうか（副作用の有無）
        characteristics["is_pure_function"] = self._analyze_purity()

        # データ変換関数かどうか
        characteristics["is_data_transformer"] = self._is_data_transformer()

        # ファクトリ関数かどうか
        characteristics["is_factory"] = "create" in self.name.lower() or "build" in self.name.lower()

        # バリデータ関数かどうか
        characteristics["is_validator"] = "validate" in self.name.lower() or "check" in self.name.lower()

        # 計算・処理関数かどうか
        characteristics["is_processor"] = "process" in self.name.lower() or "calculate" in self.name.lower()

        return characteristics

    def calculate_signature_hash(self) -> str:
        """シグネチャハッシュの計算"""
        signature_components = [
            self.name,
            "|".join(sorted(self.parameters)),
            self.return_type or "None",
            "|".join(sorted(self.decorators)),
            self.ddd_layer or "unknown",
        ]

        signature_string = "::".join(signature_components)
        return hashlib.sha256(signature_string.encode()).hexdigest()[:16]

    def get_similarity_vector(self) -> dict[str, float]:
        """類似度計算用ベクトルの生成"""
        semantic_tokens = self.get_semantic_tokens()
        structural_features = self.get_structural_features()
        functional_chars = self.get_functional_characteristics()

        # TF-IDF計算用の正規化された特徴ベクトル
        vector = {}

        # 意味的特徴（単語頻度）
        token_counts = {}
        for token in semantic_tokens:
            token_counts[token] = token_counts.get(token, 0) + 1

        total_tokens = len(semantic_tokens) if semantic_tokens else 1
        for token, count in token_counts.items():
            vector[f"semantic_{token}"] = count / total_tokens

        # 構造的特徴（正規化）
        max_structural = max(structural_features.values()) if structural_features.values() else 1
        for feature, value in structural_features.items():
            vector[f"structural_{feature}"] = value / max_structural

        # 機能的特徴（バイナリ）
        for feature, value in functional_chars.items():
            vector[f"functional_{feature}"] = 1.0 if value else 0.0

        return vector

    def get_dependency_fingerprint(self) -> str:
        """依存関係フィンガープリントの生成"""
        dependencies = []

        # インポート依存
        for import_stmt in self.imports_used:
            dependencies.append(f"import:{import_stmt.module_name}")

        # 関数呼び出し依存
        for call in self.calls_made:
            dependencies.append(f"call:{call}")

        # 変数アクセス依存
        for var in sorted(self.variables_accessed):
            dependencies.append(f"var:{var}")

        dependency_string = "|".join(sorted(dependencies))
        return hashlib.md5(dependency_string.encode()).hexdigest()[:12]

    def is_architecturally_similar(self, other: FunctionSignature) -> bool:
        """アーキテクチャ的類似性の判定"""
        if not isinstance(other, FunctionSignature):
            return False

        # DDD層の一致
        if self.ddd_layer != other.ddd_layer:
            return False

        # 責務カテゴリの類似性
        if (
            self.responsibility_category
            and other.responsibility_category
            and self.responsibility_category == other.responsibility_category
        ):
            return True

        # デコレータパターンの類似性
        common_decorators = set(self.decorators) & set(other.decorators)
        decorator_similarity = len(common_decorators) / max(len(self.decorators), len(other.decorators), 1)

        return decorator_similarity > 0.5

    def _split_identifier(self, identifier: str) -> list[str]:
        """識別子の分割（キャメルケース・スネークケース対応）"""

        # スネークケースの分割
        parts = identifier.split("_")

        # キャメルケースの分割
        split_parts = []
        for part in parts:
            # キャメルケースパターンの検出と分割
            camel_parts = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)", part)
            split_parts.extend(camel_parts if camel_parts else [part])

        return [p for p in split_parts if p and p.isalpha()]

    def _extract_keywords_from_text(self, text: str) -> list[str]:
        """テキストからキーワードを抽出"""

        # 一般的な英単語のみ抽出（日本語は除外）
        words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())

        # ストップワードの除外
        stopwords = {"the", "and", "for", "are", "but", "not", "you", "all", "can", "had", "was"}
        return [word for word in words if word not in stopwords]

    def _analyze_purity(self) -> bool:
        """純粋関数の分析"""
        # 簡易的な判定（実際にはより詳細なAST解析が必要）
        impure_indicators = [
            "global",
            "nonlocal",
            "print",
            "input",
            "open",
            "write",
            "commit",
            "save",
            "update",
            "delete",
            "create",
        ]

        function_content = self.docstring or ""
        function_content += " ".join(self.comments)
        function_content += " ".join(self.calls_made)

        return not any(indicator in function_content.lower() for indicator in impure_indicators)

    def ensure_pure_function(self) -> bool:
        """純粋関数であることを保証（Functional Core強化）"""
        if not self._analyze_purity():
            msg = f"関数{self.name}は純粋関数ではありません。副作用を排除してください。"
            raise ValueError(msg)
        return True

    def get_functional_core_compliance(self) -> dict[str, Any]:
        """Functional Core準拠性チェック"""
        return {
            "is_pure": self._analyze_purity(),
            "has_side_effects": not self._analyze_purity(),
            "functional_characteristics": self.get_functional_characteristics(),
            "compliance_level": "FULL" if self._analyze_purity() else "VIOLATION",
        }

    def _is_data_transformer(self) -> bool:
        """データ変換関数の判定"""
        transform_keywords = [
            "convert",
            "transform",
            "parse",
            "format",
            "normalize",
            "serialize",
            "deserialize",
            "encode",
            "decode",
            "map",
        ]

        return any(keyword in self.name.lower() for keyword in transform_keywords)


@dataclass
class FunctionSimilarityMatch:
    """関数類似性マッチ結果"""

    source_function: FunctionSignature
    target_function: FunctionSignature
    overall_similarity: float
    similarity_breakdown: dict[str, float]
    confidence_level: float
    match_reason: str

    def is_high_confidence_match(self) -> bool:
        """高信頼度マッチの判定"""
        return (
            self.overall_similarity >= 0.8
            and self.confidence_level >= 0.75
            and self.similarity_breakdown.get("semantic", 0.0) >= 0.7
        )

    def get_reuse_recommendation(self) -> dict[str, str]:
        """再利用推奨の生成"""
        if self.overall_similarity >= 0.9:
            return {
                "action": "direct_reuse",
                "description": f"{self.target_function.name}を直接利用可能",
                "effort": "low",
            }
        if self.overall_similarity >= 0.7:
            return {
                "action": "extend_existing",
                "description": f"{self.target_function.name}を拡張して利用",
                "effort": "medium",
            }
        if self.overall_similarity >= 0.5:
            return {
                "action": "refactor_commonality",
                "description": "共通部分を抽出してリファクタリング",
                "effort": "high",
            }
        return {"action": "separate_implementation", "description": "別途実装が適切", "effort": "high"}


# FC/IS純粋関数保証システム（SPEC-ARCH-002統合）

@dataclass(frozen=True)
class PurityTestRecord:
    """純粋性テスト記録"""
    function_name: str
    input_hash: str
    output_hash: str
    execution_time: float
    timestamp: float
    passed: bool
    failure_reason: str = ""


class PurityCache:
    """純粋性テスト結果キャッシュ"""

    def __init__(self) -> None:
        self._test_records: dict[str, list[PurityTestRecord]] = {}
        self._function_signatures: dict[str, FunctionSignature] = {}

    def add_test_record(self, record: PurityTestRecord) -> None:
        """テスト記録を追加"""
        if record.function_name not in self._test_records:
            self._test_records[record.function_name] = []
        self._test_records[record.function_name].append(record)

    def get_test_history(self, function_name: str) -> list[PurityTestRecord]:
        """関数のテスト履歴を取得"""
        return self._test_records.get(function_name, [])

    def is_verified_pure(self, function_name: str, min_tests: int = 3) -> bool:
        """関数が検証済み純粋関数かチェック"""
        history = self.get_test_history(function_name)
        if len(history) < min_tests:
            return False

        # 最近のテストが全てパスしているかチェック
        recent_tests = history[-min_tests:]
        return all(record.passed for record in recent_tests)


class PurityViolationError(Exception):
    """純粋性違反エラー"""


# グローバル純粋性キャッシュ
_purity_cache = PurityCache()


def ensure_pure_function(func: F) -> F:
    """純粋関数であることを保証するデコレータ

    Functional Core強化:
    - 入力が同じなら出力も同じ（決定論的）
    - 副作用を持たない
    - 外部状態に依存しない

    Args:
        func: 検証対象の関数

    Returns:
        F: 純粋性が保証された関数

    Raises:
        PurityViolationError: 純粋性違反が検出された場合
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if __debug__:
            # 開発時のみ純粋性チェックを実行
            return _execute_with_purity_check(func, args, kwargs)
        # 本番環境では通常実行
        return func(*args, **kwargs)

    # 関数メタデータを記録
    _register_pure_function(func)

    return wrapper


def _execute_with_purity_check(func: Callable, args: tuple, kwargs: dict) -> Any:
    """純粋性チェック付きで関数を実行"""
    function_name = func.__name__

    # 入力のハッシュ化
    input_hash = _hash_inputs(args, kwargs)

    # 既存のキャッシュをチェック
    if _purity_cache.is_verified_pure(function_name):
        # 検証済みの場合は通常実行
        return func(*args, **kwargs)

    # 決定論性テスト（同じ入力で複数回実行）
    start_time = time.time()
    results = []

    for _i in range(3):  # 3回実行して結果を比較
        try:
            result = func(*args, **kwargs)
            results.append(result)
        except Exception as e:
            # 例外発生は純粋性違反
            _record_purity_failure(
                function_name, input_hash, 0.0,
                f"例外が発生: {e!s}"
            )
            msg = f"関数 {function_name} で例外が発生: {e!s}"
            raise PurityViolationError(
                msg
            ) from e

    execution_time = (time.time() - start_time) / 3

    # 決定論性チェック
    if not _are_results_deterministic(results):
        _record_purity_failure(
            function_name, input_hash, execution_time,
            f"決定論的ではない: {[str(r) for r in results]}"
        )
        msg = f"関数 {function_name} は決定論的ではありません: {results}"
        raise PurityViolationError(
            msg
        )

    # 成功記録
    output_hash = _hash_output(results[0])
    record = PurityTestRecord(
        function_name=function_name,
        input_hash=input_hash,
        output_hash=output_hash,
        execution_time=execution_time,
        timestamp=time.time(),
        passed=True
    )
    _purity_cache.add_test_record(record)

    return results[0]


def _hash_inputs(args: tuple, kwargs: dict) -> str:
    """入力引数のハッシュ値を生成"""
    try:
        # 引数を文字列化してハッシュ化
        args_str = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(args_str.encode()).hexdigest()
    except Exception:
        # ハッシュ化不可能な場合は固定値
        return "unhashable_input"


def _hash_output(output: Any) -> str:
    """出力値のハッシュ値を生成"""
    try:
        output_str = str(output)
        return hashlib.md5(output_str.encode()).hexdigest()
    except Exception:
        return "unhashable_output"


def _are_results_deterministic(results: list[Any]) -> bool:
    """結果が決定論的（全て同じ）かチェック"""
    if not results:
        return True

    first_result = results[0]

    # 全ての結果が最初の結果と同じかチェック
    for result in results[1:]:
        try:
            if result != first_result:
                return False
        except Exception:
            # 比較不可能な場合は文字列化して比較
            if str(result) != str(first_result):
                return False

    return True


def _record_purity_failure(
    function_name: str,
    input_hash: str,
    execution_time: float,
    reason: str
) -> None:
    """純粋性テスト失敗を記録"""
    record = PurityTestRecord(
        function_name=function_name,
        input_hash=input_hash,
        output_hash="",
        execution_time=execution_time,
        timestamp=time.time(),
        passed=False,
        failure_reason=reason
    )
    _purity_cache.add_test_record(record)


def _register_pure_function(func: Callable) -> None:
    """純粋関数をレジストリに登録（簡易版）"""
    # 実際の実装では、より詳細なシグネチャ分析を行う


def get_pure_function_registry() -> dict[str, Any]:
    """登録済み純粋関数一覧を取得"""
    return _purity_cache._function_signatures.copy()


def get_purity_test_report(function_name: str) -> dict[str, Any]:
    """関数の純粋性テストレポートを取得"""
    history = _purity_cache.get_test_history(function_name)

    if not history:
        return {"function_name": function_name, "status": "no_tests"}

    passed_tests = [r for r in history if r.passed]
    failed_tests = [r for r in history if not r.passed]

    return {
        "function_name": function_name,
        "total_tests": len(history),
        "passed_tests": len(passed_tests),
        "failed_tests": len(failed_tests),
        "success_rate": len(passed_tests) / len(history) if history else 0,
        "is_verified_pure": _purity_cache.is_verified_pure(function_name),
        "recent_failures": [
            {
                "timestamp": r.timestamp,
                "reason": r.failure_reason,
                "input_hash": r.input_hash
            }
            for r in failed_tests[-3:]  # 最近の3件
        ],
        "average_execution_time": sum(r.execution_time for r in history) / len(history)
    }
