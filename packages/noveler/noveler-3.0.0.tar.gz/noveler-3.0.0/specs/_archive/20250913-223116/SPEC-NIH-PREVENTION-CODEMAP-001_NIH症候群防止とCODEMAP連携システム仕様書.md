# SPEC-NIH-PREVENTION-CODEMAP-001: NIH症候群防止とCODEMAP連携システム仕様書

## 概要

NIH（Not Invented Here）症候群を根本的に防止し、既存機能の重複実装を避けるため、CODEMAPシステムと連携した類似機能自動検出・提案システムを実装する。

## 背景

### 現状の問題
- 開発者が既存の類似機能に気づかずに重複実装を行う
- CODEMAPの手動確認に依存しており、見落としが発生
- 機能の意図や目的の類似度判定が困難
- 実装後に重複が発覚し、大きなリファクタリングが必要になる

### 解決すべき課題
1. **自動類似機能検出**: 機械学習ベースの類似度判定
2. **実装前強制チェック**: B20プロセスとの統合による義務化
3. **意味的類似性判定**: コード構造・命名・目的の総合評価
4. **提案システム**: 既存機能の活用方法提案と拡張戦略

## 機能要件

### REQ-1: 類似機能自動検出システム

#### REQ-1.1: 多角的類似度分析
- **構文的類似度**: AST構造比較・コードパターン分析
- **意味的類似度**: 関数名・変数名・コメントの自然言語処理
- **機能的類似度**: 入出力パターン・責務の分析
- **アーキテクチャ類似度**: DDD層配置・デザインパターンの比較

#### REQ-1.2: 機械学習ベース判定
- **TF-IDF**: 関数名・クラス名の重要度分析
- **Word2Vec/Doc2Vec**: 意味ベクトル空間での類似度計算
- **コード構造解析**: 制御フロー・データフローの比較
- **しきい値学習**: 過去の判定結果からの最適化

#### REQ-1.3: リアルタイム検索
- **インクリメンタル検索**: 実装中のリアルタイム類似機能提示
- **インデックス最適化**: 高速検索のためのコード構造インデックス
- **キャッシュシステム**: 類似度計算結果の効率的保存

### REQ-2: CODEMAP統合連携システム

#### REQ-2.1: CODEMAP自動解析
- **機能マッピング**: 既存機能の自動分類・タグ付け
- **依存関係分析**: 機能間の関連性グラフ構築
- **更新時同期**: CODEMAP変更時の自動再分析
- **メタデータ抽出**: 実装者・作成日・変更履歴の活用

#### REQ-2.2: B20プロセス統合
- **事前チェック強制化**: 類似機能確認の義務化
- **実装許可システム**: 類似度チェック合格後の実装許可
- **差分明確化**: 新規実装の独自性証明要求
- **統合提案**: 既存機能の拡張での対応推奨

### REQ-3: 提案・推奨システム

#### REQ-3.1: 活用方法提案
- **既存機能拡張**: パラメータ追加・オプション機能での対応
- **組み合わせパターン**: 複数既存機能の組み合わせ提案
- **インターフェース統一**: 既存機能のラッパー・アダプター提案
- **リファクタリング**: 既存機能の改善による対応

#### REQ-3.2: 設計レビュー自動化
- **アーキテクチャ適合性**: DDD原則・既存パターンとの整合性
- **再利用可能性**: 将来の類似要求への対応可能性
- **保守性評価**: 既存コードベースとの保守効率
- **テスト戦略**: 既存テストの活用可能性

## 技術仕様

### アーキテクチャ設計

```
Domain Layer:
├── SimilarityAnalyzer (Entity)
│   ├── SyntacticSimilarity (Value Object)
│   ├── SemanticSimilarity (Value Object)
│   ├── FunctionalSimilarity (Value Object)
│   └── ArchitecturalSimilarity (Value Object)
├── FunctionSignature (Value Object)
├── NIHPreventionResult (Value Object)
└── SimilarFunctionDetectionService (Domain Service)
    ├── detect_similar_functions()
    ├── calculate_overall_similarity()
    ├── suggest_reuse_strategies()
    └── validate_implementation_necessity()

Application Layer:
├── NIHPreventionUseCase
│   ├── execute_similarity_check()
│   ├── generate_reuse_recommendations()
│   └── approve_implementation_necessity()
└── CODEMAPIntegrationUseCase
    ├── sync_with_codemap()
    ├── update_similarity_index()
    └── extract_function_metadata()

Infrastructure Layer:
├── SimilarityCalculationAdapter - 類似度計算エンジン
├── CodeAnalysisAdapter - AST・静的解析
├── NLPAnalysisAdapter - 自然言語処理
├── CODEMAPAdapter - CODEMAP連携
└── SimilarityIndexRepository - 類似度インデックス管理
```

### 類似度計算アルゴリズム

#### 1. 構文的類似度（0-1）
```python
def calculate_syntactic_similarity(ast1: AST, ast2: AST) -> float:
    """
    抽象構文木の構造比較
    - ノード種別の分布比較
    - 制御構造の類似パターン検出
    - 変数・関数呼び出しパターン分析
    """
```

#### 2. 意味的類似度（0-1）
```python
def calculate_semantic_similarity(func1: FunctionSignature, func2: FunctionSignature) -> float:
    """
    自然言語処理による意味類似度
    - 関数名・変数名のword2vec類似度
    - docstring・コメントの意味ベクトル比較
    - 引数名・戻り値型の意味的関連性
    """
```

#### 3. 機能的類似度（0-1）
```python
def calculate_functional_similarity(func1: FunctionSignature, func2: FunctionSignature) -> float:
    """
    機能・責務の類似度分析
    - 入出力型パターンの比較
    - 例外処理パターンの類似性
    - 副作用・状態変更パターンの分析
    """
```

#### 4. 総合類似度計算
```python
def calculate_overall_similarity(similarities: Dict[str, float]) -> float:
    """
    重み付け総合評価
    - 構文的類似度: 0.25
    - 意味的類似度: 0.35
    - 機能的類似度: 0.30
    - アーキテクチャ類似度: 0.10
    """
```

### CODEMAP統合詳細

#### 1. メタデータ自動抽出
```yaml
function_metadata:
  id: "func_12345"
  name: "process_episode_content"
  layer: "application"
  purpose: "エピソード内容の加工処理"
  created_by: "developer_name"
  created_date: "2025-08-09"
  dependencies: ["domain/episode", "infrastructure/repository"]
  similar_functions:
    - id: "func_67890"
      similarity_score: 0.85
      reason: "類似の文字列処理ロジック"
```

#### 2. 類似度インデックス構造
```json
{
  "similarity_index": {
    "version": "1.0",
    "last_updated": "2025-08-09T12:00:00Z",
    "functions": {
      "func_12345": {
        "similar_to": [
          {"id": "func_67890", "score": 0.85, "type": "syntactic"},
          {"id": "func_11111", "score": 0.72, "type": "semantic"}
        ]
      }
    }
  }
}
```

## 実装計画

### Phase 1: 基本類似度検出 (1 commit)
- FunctionSignature・SimilarityAnalyzer実装
- 基本的な構文的・意味的類似度計算
- シンプルなCODEMAP連携

### Phase 2: 高度分析・提案システム (1 commit)
- 機械学習ベース判定システム
- B20プロセス統合
- 自動提案生成機能

### Phase 3: システム統合・最適化 (1 commit)
- リアルタイム検索・キャッシュ最適化
- CLI・Git Hooks統合
- パフォーマンス最適化

## 成功基準

### 機能面
- ✅ 95%以上の類似機能検出精度
- ✅ 重複実装の90%削減
- ✅ 実装前チェックの100%義務化
- ✅ 0.5秒以内のリアルタイム検索レスポンス

### 運用面
- ✅ B20開発プロセス完全統合
- ✅ CODEMAP自動更新・同期
- ✅ 開発者受け入れ率90%以上
- ✅ コードベース重複度20%削減

### 品質面
- ✅ 誤判定率5%以下
- ✅ 見逃し率3%以下
- ✅ 提案精度80%以上の実用性
- ✅ 毎日の継続的学習・改善

## 関連仕様書
- B20開発作業指示書準拠
- SPEC-CODEMAP-AUTO-UPDATE-001_CODEMAP自動更新システム
- SPEC-CIRCULAR-IMPORT-DETECTION-001_循環インポート予防システム

## 更新履歴
- 2025/08/09: 初版作成 (SPEC-NIH-PREVENTION-CODEMAP-001)
