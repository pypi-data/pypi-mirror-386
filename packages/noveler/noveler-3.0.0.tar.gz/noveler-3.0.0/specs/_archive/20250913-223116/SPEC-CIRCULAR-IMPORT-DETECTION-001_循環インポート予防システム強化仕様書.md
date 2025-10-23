# SPEC-CIRCULAR-IMPORT-DETECTION-001: 循環インポート予防システム強化仕様書

## 概要

B20事前確認義務化システムと統合した高度な循環インポート検出・予防システムを実装し、実装着手前の段階で循環インポートリスクを完全に排除する。

## 背景

### 現状の問題
- 基本的な循環インポートチェック機能のみ実装
- 実装時の詳細なリスク分析が不足
- モジュール間依存関係の動的分析機能なし
- 新規実装による循環リスク予測機能なし

### 解決すべき課題
1. **静的分析の強化**: AST解析による正確なインポート依存関係把握
2. **動的リスク予測**: 新規実装が既存システムに与える影響の事前分析
3. **循環パス検出**: グラフ理論による循環依存パスの特定
4. **修正提案**: 循環リスクを回避する実装パターンの提案

## 機能要件

### REQ-1: 高度循環インポート検出システム

#### REQ-1.1: AST静的解析エンジン
- Pythonソースコードの抽象構文木解析
- インポート文の完全抽出（from, import, __import__, importlib）
- 相対インポート・絶対インポートの正確な解析
- 動的インポートの検出と警告

#### REQ-1.2: 依存関係グラフ構築
- モジュール間依存関係の有向グラフ作成
- DDD層間依存の可視化
- 実行時依存と設計時依存の分離
- グラフデータのCODEMAP統合

#### REQ-1.3: 循環検出アルゴリズム
- **深さ優先探索（DFS）**: 循環パス検出
- **強連結成分分解（SCC）**: 循環グループ特定
- **トポロジカルソート**: 依存順序の妥当性検証
- **最短循環パス検出**: 最も問題となる循環ルートの特定

### REQ-2: リスク予測システム

#### REQ-2.1: 新規実装影響分析
- 予定実装位置の依存関係分析
- 既存モジュールからの参照パターン予測
- 新規インポートによる循環リスクスコア算出
- 影響範囲の可視化

#### REQ-2.2: リアルタイム検証
- 実装中の段階的循環チェック
- インポート追加時の即座な検証
- IDE統合による開発時警告
- Git commit時の最終検証

### REQ-3: 修正提案・回避システム

#### REQ-3.1: 循環回避パターン提案
- **依存注入パターン**: Protocol-based DIによる疎結合
- **レイヤー分離提案**: DDDアーキテクチャ準拠の再配置
- **インターフェース分離**: 抽象基底クラス・プロトコル活用
- **イベント駆動**: 非同期通信による依存解消

#### REQ-3.2: 自動修正機能
- 相対インポートの絶対インポート変換
- scriptsプレフィックス統一
- 不要インポートの除去
- 循環を解消する最小限のリファクタリング提案

### REQ-4: 監視・レポートシステム

#### REQ-4.1: 継続的監視
- CI/CDパイプライン統合
- 定期的なシステム全体スキャン
- 循環リスク傾向の追跡
- 品質メトリクスの収集

#### REQ-4.2: 詳細レポート
- 循環インポート検出レポート
- 依存関係可視化図表
- リスクスコア推移グラフ
- 修正アクション進捗追跡

## 技術仕様

### アーキテクチャ設計

```
Domain Layer:
├── CircularImportDetector (Entity)
│   ├── DependencyGraph (Value Object)
│   ├── CircularPath (Value Object)
│   ├── RiskScore (Value Object)
│   └── ImportStatement (Value Object)
└── CircularImportPreventionService (Domain Service)
    ├── detect_circular_imports()
    ├── analyze_risk_impact()
    ├── suggest_fixes()
    └── validate_implementation_safety()

Application Layer:
└── CircularImportAnalysisUseCase
    ├── execute_full_analysis()
    ├── predict_implementation_impact()
    └── generate_prevention_report()

Infrastructure Layer:
├── ASTAnalysisAdapter - Python AST解析
├── GraphAnalysisAdapter - NetworkX統合
├── IDEIntegrationAdapter - VS Code統合
└── CircularImportReportRepository - レポート永続化
```

### 検出アルゴリズム詳細

#### 1. AST解析によるインポート抽出
```python
def extract_imports(self, source_code: str) -> List[ImportStatement]:
    """
    抽象構文木解析によるインポート文完全抽出
    - ast.Import, ast.ImportFrom の解析
    - __import__, importlib の動的インポート検出
    - 相対インポートの絶対パス変換
    """
```

#### 2. グラフ理論による循環検出
```python
def detect_circular_dependencies(self, dependency_graph: DependencyGraph) -> List[CircularPath]:
    """
    深さ優先探索とタルヤンのアルゴリズムによる
    強連結成分検出で循環依存を完全検出
    """
```

#### 3. リスク予測アルゴリズム
```python
def calculate_risk_score(
    self,
    new_import: ImportStatement,
    existing_graph: DependencyGraph
) -> RiskScore:
    """
    新規インポートによる循環リスクを
    0-100のスコアで定量評価
    """
```

## 実装計画

### Phase 1: コア検出エンジン (1 commit)
- AST解析エンジンの実装
- 基本的な循環検出アルゴリズム
- DependencyGraph構築機能

### Phase 2: 高度分析機能 (1 commit)
- 強連結成分分解実装
- リスク予測システム
- 修正提案アルゴリズム

### Phase 3: システム統合 (1 commit)
- B20事前確認システム統合
- CLI・Git Hooks連携
- レポート・監視機能

## 成功基準

### 機能面
- ✅ 100%の循環インポート検出精度
- ✅ 新規実装時の循環リスク完全予防
- ✅ 実装着手前の自動チェック統合
- ✅ 修正提案の90%以上の有効性

### 性能面
- ✅ 全ファイルスキャン: 30秒以内
- ✅ 単一ファイル検証: 1秒以内
- ✅ リアルタイム検証: 100ms以内

### 運用面
- ✅ B20開発プロセス完全統合
- ✅ CI/CDパイプライン自動実行
- ✅ 開発者向けIDEプラグイン提供
- ✅ 企業級品質保証達成

## 関連仕様書
- B20開発作業指示書準拠
- SPEC-CODEMAP-AUTO-UPDATE-001_CODEMAP自動更新システム
- アーキテクチャリンター品質ゲート統合

## 更新履歴
- 2025/08/09: 初版作成 (SPEC-CIRCULAR-IMPORT-DETECTION-001)
