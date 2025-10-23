# 統合品質基準システム テスト戦略書

## 🎯 テスト目標

### 主要検証項目
1. **統合機能**: YAML→Markdown統合の完全性
2. **具体化精度**: 抽象基準→具体基準変換の正確性
3. **閾値動的変更**: 設定変更→評価結果変更の整合性
4. **後方互換性**: 既存システムとの互換性維持

## 🏗️ テスト階層設計

### Layer 1: 単体テスト（Unit Tests）
#### 1.1 抽象基準具体化テスト
```python
class TestAbstractionConcretization:
    """抽象基準具体化テスト"""

    def test_abstract_to_concrete_mapping(self):
        """「明確」→具体基準マッピングテスト"""
        engine = UnifiedQualityEngine("test_config.yaml")

        result = engine.get_concrete_criteria("明確")

        assert result.measurement == "文字数・要素数・記述完全性"
        assert result.threshold == "最低文字数+必須要素網羅"
        assert result.criteria["minimum_length"] > 0

    def test_all_abstract_terms_covered(self):
        """全抽象表現の具体化カバレッジテスト"""
        abstract_terms = ["明確", "具体的", "適切", "十分", "良好"]

        for term in abstract_terms:
            result = engine.get_concrete_criteria(term)
            assert result is not None, f"抽象表現 '{term}' の具体化が未定義"
```

#### 1.2 閾値動的変更テスト
```python
class TestDynamicThresholds:
    """動的閾値変更テスト"""

    def test_threshold_configuration_loading(self):
        """設定ファイルからの閾値読み込みテスト"""
        config = {
            "P-04_turning_points": {
                "minimum_score": 75,
                "target_score": 85,
                "excellent_score": 95
            }
        }

        engine = UnifiedQualityEngine.from_config(config)
        threshold = engine.get_threshold("P-04")

        assert threshold.minimum_score == 75
        assert threshold.target_score == 85
        assert threshold.excellent_score == 95

    def test_threshold_runtime_modification(self):
        """実行時閾値変更テスト"""
        engine = UnifiedQualityEngine("test_config.yaml")

        # 初期値確認
        original_threshold = engine.get_threshold("P-06")

        # 動的変更
        engine.update_threshold("P-06", minimum_score=80)
        updated_threshold = engine.get_threshold("P-06")

        assert updated_threshold.minimum_score == 80
        assert updated_threshold.target_score == original_threshold.target_score
```

### Layer 2: 統合テスト（Integration Tests）
#### 2.1 YAML統合完全性テスト
```python
class TestYAMLIntegration:
    """YAML統合テスト"""

    def test_yaml_to_markdown_consistency(self):
        """YAML→Markdown統合の整合性テスト"""
        # A25 YAMLの項目がA30 Markdownに統合されているか確認
        yaml_items = self.parse_yaml_checklist("A25_プロット作成チェックリスト.yaml")
        markdown_items = self.parse_markdown_quality("A30_執筆品質基準.md")

        for yaml_item in yaml_items:
            matching_md_item = self.find_matching_item(yaml_item, markdown_items)
            assert matching_md_item is not None, f"YAML項目 {yaml_item.id} がMarkdownに未統合"

            # 具体化改善確認
            if "明確" in yaml_item.description:
                assert self.has_concrete_criteria(matching_md_item), "抽象表現が具体化されていない"

    def test_all_yaml_items_migrated(self):
        """全YAML項目の移行完全性テスト"""
        yaml_files = ["A25_プロット作成チェックリスト.yaml", "A41_推敲品質チェックリスト.yaml"]

        for yaml_file in yaml_files:
            items = self.extract_checklist_items(yaml_file)

            for item in items:
                # A30品質基準またはA11ガイドに統合されているか確認
                assert self.is_item_migrated(item), f"項目 {item.id} が未移行"
```

#### 2.2 エンドツーエンド品質評価テスト
```python
class TestEndToEndQuality:
    """E2E品質評価テスト"""

    def test_complete_quality_evaluation_flow(self):
        """完全な品質評価フローテスト"""
        # テスト原稿準備
        test_manuscript = self.create_test_manuscript(
            word_count=8500,
            viewpoint_consistency=True,
            abstract_emotions=["嬉しいと思った", "悲しい気持ち"]  # 意図的な抽象表現
        )

        # 統合品質評価実行
        engine = UnifiedQualityEngine("production_config.yaml")
        result = engine.evaluate_complete_quality(test_manuscript)

        # 結果検証
        assert result.total_score > 0
        assert result.has_specific_scores_for_all_categories()
        assert result.abstract_emotion_violations == 2  # 抽象表現検出確認

        # 改善提案生成確認
        improvement_plan = engine.generate_improvement_plan(result)
        assert len(improvement_plan.concrete_suggestions) > 0
```

### Layer 3: パフォーマンステスト
#### 3.1 大規模評価テスト
```python
class TestPerformance:
    """パフォーマンステスト"""

    def test_large_manuscript_evaluation(self):
        """大規模原稿評価性能テスト"""
        # 50,000字の原稿シミュレート
        large_manuscript = self.generate_large_manuscript(50000)

        engine = UnifiedQualityEngine("production_config.yaml")

        start_time = time.time()
        result = engine.evaluate_complete_quality(large_manuscript)
        elapsed_time = time.time() - start_time

        # 性能要求: 50,000字を30秒以内で評価
        assert elapsed_time < 30.0, f"評価時間過大: {elapsed_time}秒"
        assert result.total_score > 0
```

## 📊 テストデータ設計

### 具体化検証用テストケース
```yaml
test_cases:
  abstract_improvements:
    - input: "各シーンの目的が明確か"
      expected_concrete:
        measurement: "シーン別目的分析"
        criteria:
          minimum_description_length: 30
          story_contribution_quantified: true
        validation:
          - "全シーンに目的30文字以上"
          - "物語進行への寄与明文化"

    - input: "感情表現の具体性"
      expected_concrete:
        measurement: "感情表現分析・身体化度チェック"
        criteria:
          abstract_emotion_count: 0
          body_reaction_ratio: 0.8
        validation:
          - "抽象感情表現0件"
          - "身体反応描写80%以上"
```

### 統合検証用原稿サンプル
```markdown
# テスト原稿（品質A判定想定）
## 文字数: 8,247字（基準クリア）
## 視点: 一人称統一（混在なし）
## 感情表現: 身体化100%実装

俺の胃がキリキリと音を立てた。（○ 身体反応による感情表現）
心臓が早鐘のように鳴り響く。（○ 具体的身体反応）

# テスト原稿（品質D判定想定）
## 文字数: 7,500字（基準未達）
## 感情表現: 抽象表現多数

俺は嬉しいと思った。（× 抽象的感情表現）
悲しい気持ちになった。（× 抽象的感情表現）
```

## 🔄 継続的テスト戦略

### 自動回帰テスト
```bash
# 毎日実行される回帰テストスイート
pytest tests/quality_standards/ \
  --cov=scripts.domain.services.quality \
  --cov-report=html \
  --integration \
  --performance
```

### 設定変更影響テスト
```python
def test_config_change_impact():
    """設定変更の影響範囲テスト"""

    # ベースライン評価
    baseline_result = evaluate_with_config("baseline_config.yaml")

    # 閾値変更後評価
    modified_result = evaluate_with_config("modified_config.yaml")

    # 変更影響の予測可能性確認
    expected_changes = calculate_expected_changes(baseline_config, modified_config)
    actual_changes = compare_results(baseline_result, modified_result)

    assert actual_changes.matches_expected(expected_changes)
```

## 📋 テスト実行計画

### Phase 1: 基盤テスト（1日）
1. **抽象基準具体化テスト**: 全抽象表現の具体化検証
2. **設定駆動テスト**: YAML設定→評価結果マッピング
3. **閾値動的変更テスト**: 実行時設定変更機能

### Phase 2: 統合テスト（1日）
1. **YAML統合完全性テスト**: 全項目移行検証
2. **品質評価一貫性テスト**: 新旧システム結果比較
3. **後方互換性テスト**: 既存API動作保証

### Phase 3: 本格稼働テスト（1日）
1. **パフォーマンステスト**: 大規模原稿対応確認
2. **エラー復旧テスト**: 異常系動作確認
3. **運用テスト**: 実際の執筆ワークフロー検証

## 🎯 合格基準

### 機能要件
- [ ] 全抽象表現の具体化完了（100%）
- [ ] YAML項目統合完了（100%）
- [ ] 設定駆動評価動作（100%）
- [ ] 後方互換性維持（100%）

### 非機能要件
- [ ] 評価性能: 10,000字/10秒以下
- [ ] 設定変更影響: 予測通り（±5%）
- [ ] テストカバレッジ: 85%以上
- [ ] 統合テスト: 全項目Pass

**この戦略により、ユーザー指摘の統合要求が技術的に完全実現され、品質保証されます。**
