# SPEC-ARCH-002: FC/IS契約テストフレームワーク実装

**最終更新**: 2025年8月28日
**対象**: Phase 4 FC/IS（Functional Core / Imperative Shell）アーキテクチャ完全実装
**用途**: 純粋関数の契約保証とアーキテクチャ境界の自動検証

## 概要

B20_Claude_Code開発作業指示書.mdに基づき、FC/ISアーキテクチャパターンの完全実装を行う。
Domain層の純粋関数化（Functional Core）とInfrastructure層の副作用分離（Imperative Shell）により、
テスタビリティとメンテナビリティを向上させる。

## 実装要件

### 1. 契約テストフレームワーク

#### 1.1 FunctionalCoreContract基底クラス
```python
# scripts/tests/contracts/functional_core_contract.py
from abc import ABC, abstractmethod
from typing import Any, TypeVar, Generic, Callable

T = TypeVar('T')
R = TypeVar('R')

class FunctionalCoreContract(ABC, Generic[T, R]):
    """Functional Core契約保証基底クラス

    Domain層の純粋関数であることを保証
    """

    @abstractmethod
    def is_pure(self) -> bool:
        """純粋関数であることを保証"""
        pass

    @abstractmethod
    def is_deterministic(self) -> bool:
        """決定論的であることを保証"""
        pass

    @abstractmethod
    def has_no_side_effects(self) -> bool:
        """副作用がないことを保証"""
        pass
```

#### 1.2 純粋関数検証デコレータ
```python
# scripts/domain/value_objects/function_signature.py
from functools import wraps
from typing import Any, Callable, TypeVar

F = TypeVar('F', bound=Callable[..., Any])

def ensure_pure_function(func: F) -> F:
    """純粋関数であることを保証するデコレータ

    Functional Core強化:
    - 入力が同じなら出力も同じ（決定論的）
    - 副作用を持たない
    - 外部状態に依存しない
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # 実行前状態のキャプチャ（開発時のみ）
        if __debug__:
            result = func(*args, **kwargs)
            # 同一入力での決定論的テスト
            result2 = func(*args, **kwargs)
            assert result == result2, f"関数{func.__name__}は決定論的ではありません"
            return result
        return func(*args, **kwargs)

    return wrapper
```

### 2. Domain層純粋関数化

#### 2.1 評価サービスのリファクタリング
- `A31EvaluationService`を純粋関数群に分解
- 副作用（コンソール出力、ファイルI/O）をInfrastructure層に移動
- 入力→出力の関数型アプローチ

#### 2.2 ビジネスルールの純粋関数化
- `domain/services/`内の各サービスを純粋関数に変換
- 外部依存を排除し、引数による依存性注入のみ

### 3. Infrastructure層Imperative Shell実装

#### 3.1 ShellServiceアダプター
```python
# scripts/infrastructure/adapters/shell_service_adapter.py
class ShellServiceAdapter:
    """Imperative Shell実装

    副作用を局所化し、純粋関数（Core）を呼び出す薄いラッパー
    """

    def __init__(self, functional_core: FunctionalCoreContract):
        self._core = functional_core

    def execute_with_side_effects(self, input_data: Any) -> Any:
        """副作用を伴う処理の実行

        1. 外部から入力取得（I/O）
        2. 純粋関数で計算実行
        3. 結果を外部に出力（I/O）
        """
        # Step 1: Input (Side Effect)
        processed_input = self._prepare_input(input_data)

        # Step 2: Pure Computation (No Side Effects)
        result = self._core.compute(processed_input)

        # Step 3: Output (Side Effect)
        self._handle_output(result)

        return result
```

### 4. 品質ゲート統合

#### 4.1 純粋関数検証テスト
```python
# tests/contracts/test_functional_core_purity.py
@pytest.mark.spec("SPEC-ARCH-002")
class TestFunctionalCorePurity:
    """純粋関数性の検証"""

    def test_evaluation_service_purity(self):
        """評価サービスが純粋関数であることを確認"""
        # 同一入力での決定論的テスト
        # 副作用の存在チェック
        pass

    def test_domain_services_purity(self):
        """Domain層サービス群の純粋性確認"""
        pass
```

#### 4.2 アーキテクチャ境界検証の強化
既存の`test_ddd_architecture_rules.py`にFC/IS検証ルールを追加

## 実装手順

### Phase 1: 契約フレームワーク基盤実装
1. `FunctionalCoreContract`基底クラス作成
2. `ensure_pure_function`デコレータ実装
3. 基本的な契約テスト作成

### Phase 2: Domain層純粋関数化
1. `A31EvaluationService`のリファクタリング
2. 主要Domain Serviceの純粋関数化
3. 純粋性検証テスト追加

### Phase 3: Infrastructure層Shell実装
1. `ShellServiceAdapter`基底クラス実装
2. 既存Adapterのシェル化
3. E2Eテストでシェル動作確認

## 品質基準

- テストカバレッジ: 85%以上（契約テスト含む）
- 純粋関数割合: Domain層の80%以上
- 副作用分離: Infrastructure層に100%局所化
- アーキテクチャルール: 違反0件

## 関連仕様

- SPEC-ARCH-001: DDD基本アーキテクチャ
- B20_Claude_Code開発作業指示書.md
- B30_Claude_Code品質作業指示書.md
