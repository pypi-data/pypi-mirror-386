# SPEC-YAML-001: DDD準拠YAML処理統合基盤仕様書

## 1. 概要

### 1.1 目的
Domain-Driven Design（DDD）原則に準拠したYAML処理統合基盤を実装し、ドメイン層とインフラ層の適切な分離を実現する。

### 1.2 背景
現状のコードベースでDDD違反が多数発見されている：
- エンティティ層違反: `scripts/domain/entities/episode_prompt.py:74` でインフラ層への直接依存
- ドメインサービス層違反: 5ファイル・8箇所でインフラ層への直接依存
- 統合基盤普及率: 100+箇所中わずか2%の統合度

### 1.3 適用範囲
- ドメインエンティティのYAML処理機能
- ドメインサービスのYAML操作機能
- アプリケーション層での統合YAML処理
- インフラ層の具体実装との疎結合

## 2. 要求仕様

### 2.1 機能要求

#### FR-001: ドメイン層インターフェース
- **要求**: ドメイン層でYAML処理抽象インターフェースを定義
- **仕様**:
  - `IYamlProcessor` インターフェースの提供
  - マルチライン文字列処理の抽象化
  - YAML読み取り・書き込み操作の抽象化

#### FR-002: アプリケーション層統合サービス
- **要求**: アプリケーション層でYAML処理統合サービスを実装
- **仕様**:
  - `YamlProcessingService` クラスの実装
  - 依存性注入による具体実装の注入
  - エラーハンドリングの統一化

#### FR-003: インフラ層具体実装
- **要求**: 既存のYAMLUtils機能を具体実装として移行
- **仕様**:
  - `YamlProcessorAdapter` クラスの実装
  - `YAMLMultilineString` 機能の継承
  - パフォーマンス最適化の維持

### 2.2 非機能要求

#### NFR-001: DDD準拠性
- **レベル**: 必須
- **仕様**: ドメイン→アプリケーション→インフラの依存方向厳守
- **検証**: 静的解析によるimport依存関係チェック

#### NFR-002: パフォーマンス
- **レベル**: 重要
- **仕様**: 既存YAML処理パフォーマンスの95%以上を維持
- **検証**: ベンチマークテストによる性能測定

#### NFR-003: 後方互換性
- **レベル**: 推奨
- **仕様**: 既存YAMLファイル形式との100%互換性
- **検証**: 既存ファイル読み込みテスト

## 3. アーキテクチャ設計

### 3.1 レイヤー構成

```
┌─────────────────────────────────────┐
│ ドメイン層 (Domain Layer)             │
├─────────────────────────────────────┤
│ - IYamlProcessor (Interface)        │
│ - YamlContentProcessor (Entity)     │
│ - MultilineContent (Value Object)   │
└─────────────────────────────────────┘
                   ↑
┌─────────────────────────────────────┐
│ アプリケーション層 (Application)       │
├─────────────────────────────────────┤
│ - YamlProcessingService             │
│ - YamlContentOrchestrator           │
└─────────────────────────────────────┘
                   ↑
┌─────────────────────────────────────┐
│ インフラ層 (Infrastructure)           │
├─────────────────────────────────────┤
│ - YamlProcessorAdapter              │
│ - YAMLUtilsWrapper                  │
└─────────────────────────────────────┘
```

### 3.2 クラス設計

#### 3.2.1 ドメイン層
```python
> 注記: 本仕様の `scripts/...` パスは旧構成の例です。現行は `src/noveler/` 配下の関連サービス/インターフェースをご参照ください。

# 参考: 旧構成 `scripts/domain/interfaces/yaml_processor.py`
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class IYamlProcessor(ABC):
    @abstractmethod
    def create_multiline_string(self, content: str) -> Any:
        """マルチライン文字列オブジェクト生成"""
        pass

    @abstractmethod
    def process_content_to_dict(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """コンテンツ辞書のYAML処理対応変換"""
        pass
```

#### 3.2.2 アプリケーション層
```python
# 参考: 旧構成 `scripts/application/services/yaml_processing_service.py`
from scripts.domain.interfaces.yaml_processor import IYamlProcessor

class YamlProcessingService:
    def __init__(self, yaml_processor: IYamlProcessor):
        self._yaml_processor = yaml_processor

    def process_episode_content(self, content: str) -> Dict[str, Any]:
        """エピソード内容のYAML処理"""
        pass
```

#### 3.2.3 インフラ層
```python
# 参考: 旧構成 `scripts/infrastructure/adapters/yaml_processor_adapter.py`
from scripts.infrastructure.utils.yaml_utils import YAMLMultilineString

class YamlProcessorAdapter(IYamlProcessor):
    def create_multiline_string(self, content: str) -> YAMLMultilineString:
        return YAMLMultilineString(content)
```

## 4. 実装計画

### 4.1 Phase 1: 基盤実装 (1-2日)
1. ドメイン層インターフェース実装
2. アプリケーション層サービス実装
3. インフラ層アダプター実装
4. 依存性注入設定

### 4.2 Phase 2: マイグレーション (2-3日)
1. エンティティ層違反修正
2. ドメインサービス層違反修正
3. 段階的な移行実行
4. 統合テスト実行

### 4.3 Phase 3: 品質保証 (1日)
1. 全テストケース実行
2. パフォーマンス測定
3. 静的解析による依存関係検証
4. ドキュメント更新

## 5. テスト戦略

### 5.1 単体テスト
- **対象**: 各レイヤーのクラス単体
- **カバレッジ**: 95%以上
- **ツール**: pytest + @pytest.mark.spec("SPEC-YAML-001")

### 5.2 統合テスト
- **対象**: レイヤー間連携動作
- **シナリオ**: 既存YAML処理機能の完全再現
- **検証**: 出力結果の完全一致

### 5.3 回帰テスト
- **対象**: 既存機能への影響確認
- **範囲**: episode_prompt, ドメインサービス5ファイル
- **基準**: 機能動作の100%維持

## 6. 受け入れ基準

### 6.1 DDD準拠性
- [x] ドメイン層→インフラ層直接依存の完全排除
- [x] 適切な依存性注入パターンの実装
- [x] 静的解析による依存関係検証パス

### 6.2 機能性
- [x] 既存YAML処理機能の100%再現
- [x] マルチライン文字列処理の正常動作
- [x] エラーハンドリングの適切な実装

### 6.3 品質
- [x] 全テストケースの成功
- [x] パフォーマンス95%以上の維持
- [x] コードカバレッジ95%以上

## 7. リスク管理

### 7.1 技術的リスク
- **リスク**: 依存性注入設定の複雑化
- **対策**: 段階的導入とテスト駆動開発
- **影響度**: 中

### 7.2 スケジュールリスク
- **リスク**: 既存コード影響範囲の想定外拡大
- **対策**: 詳細な影響範囲調査と並行開発
- **影響度**: 中

## 8. 成果物

### 8.1 実装成果物
1. `scripts/domain/interfaces/yaml_processor.py`
2. `scripts/application/services/yaml_processing_service.py`
3. `scripts/infrastructure/adapters/yaml_processor_adapter.py`
4. 依存性注入設定ファイル

### 8.2 テスト成果物
1. 単体テストスイート (95%+ カバレッジ)
2. 統合テストスイート
3. パフォーマンステスト結果
4. 回帰テスト結果

### 8.3 ドキュメント成果物
1. 実装ガイド
2. マイグレーション手順書
3. アーキテクチャドキュメント更新
4. CLAUDE.md 更新

---

**仕様策定者**: Claude Code Integration Team
**承認者**: DDD Architecture Team
**版数**: 1.0
**策定日**: 2025-08-06
