# SPEC-A31-SESSION-002: セッション内分析システム テスト仕様書

## テスト概要
Claude Codeセッション内A31重点項目分析システムの品質保証と信頼性検証のための包括的テスト仕様。

## テスト戦略

### TDD準拠テスト階層
1. **単体テスト**: 各ドメインエンティティ・サービスの個別機能検証
2. **統合テスト**: コンポーネント間連携の動作検証
3. **E2Eテスト**: CLIコマンド実行からファイル更新までの全工程检証
4. **パフォーマンステスト**: 30秒/20項目の要件検証

## 単体テストケース

### TEST-SESSION-001: SessionAnalysisResult エンティティテスト
```python
@pytest.mark.spec("SPEC-A31-SESSION-001")
class TestSessionAnalysisResult:

    def test_create_new_session_result(self):
        """新規セッション分析結果作成テスト"""

    def test_start_analysis_state_transition(self):
        """分析開始状態遷移テスト"""

    def test_add_item_analysis_result(self):
        """項目分析結果追加テスト"""

    def test_complete_analysis_status_determination(self):
        """分析完了ステータス決定テスト"""

    def test_completion_rate_calculation(self):
        """完了率計算精度テスト"""

    def test_high_confidence_improvements_filtering(self):
        """高信頼度改善提案フィルタリングテスト"""
```

### TEST-SESSION-002: InSessionClaudeAnalyzer サービステスト
```python
@pytest.mark.spec("SPEC-A31-SESSION-001")
class TestInSessionClaudeAnalyzer:

    def test_analyze_priority_items_sequential(self):
        """重点項目順次分析テスト"""

    def test_analyze_priority_items_parallel(self):
        """重点項目並列分析テスト"""

    def test_prompt_generation_context_injection(self):
        """プロンプト生成コンテキスト注入テスト"""

    def test_retry_mechanism_on_failure(self):
        """失敗時リトライ機構テスト"""

    def test_execution_statistics_tracking(self):
        """実行統計追跡テスト"""
```

### TEST-SESSION-003: A31ResultIntegrator サービステスト
```python
@pytest.mark.spec("SPEC-A31-SESSION-001")
class TestA31ResultIntegrator:

    def test_integrate_analysis_results_merge_smart(self):
        """分析結果スマートマージ統合テスト"""

    def test_confidence_threshold_filtering(self):
        """信頼度閾値フィルタリングテスト"""

    def test_backup_file_creation(self):
        """バックアップファイル作成テスト"""

    def test_improvement_comments_addition(self):
        """改善提案コメント追加テスト"""

    def test_integration_metadata_addition(self):
        """統合メタデータ追加テスト"""
```

## 統合テストケース

### TEST-SESSION-004: セッション分析ユースケース統合テスト
```python
@pytest.mark.spec("SPEC-A31-SESSION-001")
class TestSessionBasedAnalysisUseCase:

    def test_end_to_end_analysis_workflow(self):
        """E2E分析ワークフローテスト"""

    def test_error_handling_resilience(self):
        """エラーハンドリング回復性テスト"""

    def test_performance_requirements_compliance(self):
        """パフォーマンス要件準拠テスト (≤30秒/20項目)"""

    def test_concurrent_analysis_safety(self):
        """並行分析安全性テスト"""
```

### TEST-SESSION-005: プロンプトチェーン実行統合テスト
```python
@pytest.mark.spec("SPEC-A31-SESSION-001")
class TestPromptChainExecutor:

    def test_chain_execution_sequential_vs_parallel(self):
        """チェーン実行順次vs並列比較テスト"""

    def test_timeout_handling(self):
        """タイムアウトハンドリングテスト"""

    def test_semaphore_concurrency_control(self):
        """セマフォ同時実行制御テスト"""
```

## E2Eテストケース

### TEST-SESSION-006: CLIコマンドE2Eテスト
```python
@pytest.mark.spec("SPEC-A31-SESSION-001")
@pytest.mark.e2e
class TestA31ClaudeIntegrationE2E:

    def test_analyze_in_session_command_full_workflow(self):
        """analyze-in-sessionコマンド全工程テスト"""

    def test_analyze_in_session_with_integration(self):
        """analyze-in-session結果統合付きテスト"""

    def test_analyze_in_session_error_scenarios(self):
        """analyze-in-sessionエラーシナリオテスト"""
```

## パフォーマンステストケース

### TEST-SESSION-007: パフォーマンス要件検証
```python
@pytest.mark.spec("SPEC-A31-SESSION-001")
@pytest.mark.performance
class TestSessionAnalysisPerformance:

    def test_20_items_analysis_under_30_seconds(self):
        """20項目分析30秒以内完了テスト"""

    def test_memory_usage_under_500mb(self):
        """メモリ使用量500MB以下テスト"""

    def test_parallel_vs_sequential_performance(self):
        """並列vs順次実行パフォーマンス比較テスト"""

    def test_large_manuscript_handling(self):
        """大容量原稿処理テスト"""
```

## テストデータ要件

### 最小テストデータセット
```yaml
test_checklist_minimal.yaml:
  - 5項目のA31チェックリスト
  - 基本的なフェーズ構成
  - 最小限のメタデータ

test_manuscript_short.md:
  - 1000文字程度の短編原稿
  - 基本的な物語構成

test_manuscript_long.md:
  - 10000文字の長編原稿
  - 複雑な描写と展開
```

### 完全テストデータセット
```yaml
test_checklist_full.yaml:
  - 68項目の完全A31チェックリスト
  - 全フェーズ網羅
  - リッチメタデータ

test_manuscript_realistic.md:
  - 5000文字の現実的な原稿
  - Fランク魔法使いシリーズ準拠
  - 多様な分析対象要素
```

## 信頼性検証要件

### NFR-TEST-001: 成功率要件
- プロンプト実行成功率: ≥95%
- 分析結果整合性: 100%保証
- 統合処理成功率: ≥98%

### NFR-TEST-002: パフォーマンス要件
- 重点項目分析完了時間: ≤30秒/20項目
- メモリ使用量: ≤500MB
- 並列処理効果: ≥30%高速化

### NFR-TEST-003: 拡張性要件
- 新規分析項目追加: 既存テスト影響なし
- カスタムプロンプト対応: 動的テスト生成
- 分析戦略変更: テスト互換性維持

## テスト自動化要件

### CI/CD統合
```bash
# 基本テスト実行
pytest scripts/tests/ -m "spec('SPEC-A31-SESSION-001')"

# パフォーマンステスト
pytest scripts/tests/ -m "performance" --timeout=60

# E2Eテスト
pytest scripts/tests/ -m "e2e" --timeout=120
```

### カバレッジ要件
- ステートメントカバレッジ: ≥90%
- ブランチカバレッジ: ≥85%
- 関数カバレッジ: 100%

## 品質ゲート条件

### 必須条件
1. 全単体テスト PASS
2. 全統合テスト PASS
3. パフォーマンス要件クリア
4. カバレッジ要件達成

### 推奨条件
1. E2Eテスト PASS
2. エラーシナリオ網羅
3. セキュリティテスト実行
4. 負荷テスト実行

## 継続的品質改善

### メトリクス収集
- テスト実行時間トレンド
- 失敗率トレンド
- カバレッジ推移
- パフォーマンス推移

### 定期レビュー
- 月次テスト結果レビュー
- 四半期品質目標見直し
- 年次テスト戦略更新
