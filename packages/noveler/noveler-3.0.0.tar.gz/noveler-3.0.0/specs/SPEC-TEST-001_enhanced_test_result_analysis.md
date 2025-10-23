# SPEC-TEST-001: Enhanced Test Result Analysis System

## 1.0 概要

pytest結果をMCP経由でLLMに送信する際のトークン効率化と精度向上のための機能拡張仕様。

### 1.1 背景
- 現状: TestResultAnalysisToolがpytest-json-report形式を解析しLLMへ送信
- 課題: トークン消費量が多く、同じエラーの繰り返し、前回との差分が不明

### 1.2 目的
- トークン使用量を40-60%削減
- エラー相関分析により修正精度を20-30%向上
- 差分分析により反復修正時間を50%短縮

## 2.0 機能要件

### 2.1 差分分析機能
```python
class IncrementalAnalyzer:
    """前回実行結果との差分を分析"""

    def analyze_delta(
        self,
        current_results: dict,
        previous_results: Optional[dict] = None
    ) -> DeltaAnalysis:
        """
        Returns:
            - newly_failed: 新規失敗テスト
            - newly_passed: 修正済みテスト
            - still_failing: 継続的問題
            - regression: リグレッション
        """
```

### 2.2 エラーグルーピング機能
```python
class ErrorGrouper:
    """類似エラーをグループ化してトークンを節約"""

    def group_similar_errors(
        self,
        errors: List[TestError]
    ) -> Dict[str, List[TestError]]:
        """
        エラーパターンでグループ化
        - 同じエラータイプ
        - 類似スタックトレース
        - 同じモジュール起因
        """
```

### 2.3 コンテキスト階層化
```python
class HierarchicalContext:
    """情報を階層的に提供"""

    def build_context(
        self,
        issues: List[ToolIssue],
        detail_level: int = 1
    ) -> dict:
        """
        レベル1: 要約のみ
        レベル2: 重要なエラー詳細
        レベル3: 全詳細情報
        """
```

## 3.0 非機能要件

### 3.1 パフォーマンス
- 差分分析: 1000テスト結果を100ms以内で処理
- グルーピング: O(n log n)の計算量
- メモリ使用: 前回結果の保持は最大10MB

### 3.2 互換性
- 既存のTestResultAnalysisToolとの後方互換性維持
- 新機能はすべてオプショナルパラメータ
- pytest-json-report形式の変更なし

## 4.0 既存実装調査（B20必須）

### 4.1 CODEMAP確認結果
- TestResultAnalysisTool: src/mcp_servers/noveler/tools/test_result_analysis_tool.py
- 基底クラス: MCPToolBase (src/mcp_servers/noveler/domain/entities/mcp_tool_base.py)
- 共有コンポーネント: 統一Logger, PathService使用済み

### 4.2 再利用可能コンポーネント
- ToolIssue: 既存のエラー構造体を継続使用
- ToolResponse: 既存のレスポンス形式を拡張
- 品質スコア計算: _calculate_analysis_scoreを活用

## 5.0 設計詳細

### 5.1 データ構造
```python
@dataclass
class DeltaAnalysis:
    """差分分析結果"""
    newly_failed: List[str]      # 新規失敗
    newly_passed: List[str]      # 修正済み
    still_failing: List[str]     # 継続失敗
    regression: List[str]        # リグレッション
    improvement_rate: float      # 改善率

@dataclass
class ErrorGroup:
    """エラーグループ"""
    pattern: str                 # エラーパターン
    count: int                   # 発生回数
    examples: List[TestError]    # 代表例（最大3件）
    affected_modules: Set[str]   # 影響モジュール
```

### 5.2 インターフェース拡張
```python
# 既存のget_input_schemaに追加
"enable_delta_analysis": {
    "type": "boolean",
    "description": "差分分析を有効化（前回結果との比較）"
},
"enable_error_grouping": {
    "type": "boolean",
    "description": "エラーグルーピングを有効化"
},
"context_detail_level": {
    "type": "integer",
    "minimum": 1,
    "maximum": 3,
    "description": "コンテキスト詳細度（1:要約、2:重要、3:全詳細）"
}
```

## 6.0 テストケース

### 6.1 差分分析テスト
- 初回実行（前回結果なし）
- 改善ケース（失敗→成功）
- 悪化ケース（成功→失敗）
- 変化なしケース

### 6.2 グルーピングテスト
- 同一エラーの複数発生
- 類似エラーのグループ化
- 異なるエラーの分離
- 空リストの処理

### 6.3 階層化テスト
- レベル1: 要約のみ出力
- レベル2: 重要情報追加
- レベル3: 全詳細出力

## 7.0 実装計画

### Phase 1: 基盤整備（このコミット）
- 仕様書作成
- テストケース作成（RED状態）

### Phase 2: コア実装
- IncrementalAnalyzer実装
- ErrorGrouper実装
- HierarchicalContext実装

### Phase 3: 統合
- TestResultAnalysisToolへの統合
- 既存テストの維持確認
- E2Eテスト追加

## 8.0 受け入れ基準

- [ ] トークン使用量が40%以上削減
- [ ] 差分分析により新規/修正済み/継続エラーが識別可能
- [ ] 類似エラーが自動グループ化される
- [ ] 既存APIとの後方互換性が維持される
- [ ] 全単体テストがパス
- [ ] パフォーマンス基準を満たす

## 9.0 リスクと対策

### リスク
- メモリ使用量増加（前回結果の保持）
- 計算時間の増加（グルーピング処理）

### 対策
- キャッシュサイズ制限（10MB）
- 非同期処理オプション
- 段階的ロールアウト

## 10.0 関連ドキュメント

- [B20_Claude_Code開発作業指示書.md](../docs/B20_Claude_Code開発作業指示書.md)
- [TestResultAnalysisTool実装](../src/mcp_servers/noveler/tools/test_result_analysis_tool.py)
- [MCPツール統合仕様](SPEC-MCP-001_mcp-tool-integration-system.md)
