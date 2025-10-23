# 品質サービス統合 影響調査レポート

**作成日**: 2025-01-29
**調査方法**: rg (ripgrep) による依存関係分析

## 1. 影響サマリー

### 影響を受けるレイヤー
- **Application層**: 10ファイル
- **Domain層**: 2ファイル
- **Infrastructure層**: 未調査（次フェーズ）

### 優先度別分類
- **高優先度**: UseCase層の依存（直接的な影響）
- **中優先度**: Orchestrator層の依存
- **低優先度**: 間接的な参照

## 2. 詳細な影響箇所

### Application層 - Orchestrators
1. `plot_generation_orchestrator.py`
   - 影響度: 高
   - 移行方針: アダプター経由で段階的移行

### Application層 - Use Cases
1. `quality_record_enhancement_use_case.py`
   - 影響度: 高
   - 移行方針: 新QualityCheckCoreへの直接移行

2. `plot_quality_assurance_use_case.py`
   - 影響度: 高
   - 移行方針: 新QualityCheckCoreへの直接移行

3. `plot_generation_use_case.py`
   - 影響度: 中
   - 移行方針: アダプター維持

4. `interactive_plot_improvement_use_case.py`
   - 影響度: 中
   - 移行方針: アダプター維持

5. `initialize_quality_config_use_case.py`
   - 影響度: 高
   - 移行方針: QualityConfigurationManagerへの移行

6. `integrated_quality_check_use_case.py`
   - 影響度: 最高
   - 移行方針: 段階的な書き換え必須

7. `stepwise_writing_use_case.py`
   - 影響度: 低
   - 移行方針: 間接参照のため後回し

### Domain層
1. `enhanced_quality_evaluation_engine.py`
   - 影響度: 低
   - 移行方針: 独立サービスとして維持

2. `writing_steps/publishing_preparation_service.py`
   - 影響度: 低
   - 移行方針: 間接参照のため影響最小

## 3. 移行戦略

### Phase 1: アダプター層の実装
```python
class QualityServiceAdapter:
    """既存APIを新実装にマッピング"""
    def __init__(self):
        self.new_core = QualityCheckCore()
        self.config = QualityConfigurationManager()

    # 旧APIメソッドを維持
    def analyze_quality(self, *args, **kwargs):
        return self.new_core.analyze_quality(*args, **kwargs)
```

### Phase 2: 高優先度UseCaseの移行
1. `integrated_quality_check_use_case.py`を最初に
2. 設定系UseCaseを次に
3. レポート系を最後に

### Phase 3: 間接参照の更新
- import文の一括更新
- 設定ファイルの移行

## 4. リスク評価

### 高リスク
- `integrated_quality_check_use_case.py`の複雑な依存関係
- 対策: 十分なテストカバレッジとアダプターパターン

### 中リスク
- 設定の互換性
- 対策: バージョニングとフォールバック

### 低リスク
- 間接参照の更新漏れ
- 対策: 自動化ツールによる一括更新

## 5. テスト戦略

### 単体テスト
- 新サービスの全機能をカバー
- アダプター層のマッピング確認

### 統合テスト
- UseCase層の動作確認
- E2Eシナリオ

### 回帰テスト
- 既存の品質チェック機能が維持されることを確認

## 6. 次のアクション

1. アダプター層の実装とテスト
2. 高優先度UseCaseから段階的移行
3. 統合テストの実施
4. ドキュメント更新

---
**推定作業時間**: 3-4週間
**推奨チーム規模**: 2-3名