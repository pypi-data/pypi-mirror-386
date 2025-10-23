# SPEC-A31-DET-001: A31詳細評価システム

## 仕様概要
手動Claude Code分析と同等の詳細フィードバックを提供するA31評価システム

## 機能要件

### FR-001: 詳細評価セッション管理
**Given**: エピソード内容とA31チェックリスト項目
**When**: 詳細評価を実行
**Then**:
- 行番号付き具体的問題点を特定
- カテゴリ別詳細分析結果を生成
- 改善提案と修正例を提供
- 総合評価スコア（0-100点）を算出

### FR-002: 行別フィードバック生成
**Given**: エピソード各行とカテゴリ別分析結果
**When**: 行別分析を実行
**Then**:
- 問題のある行を特定（行番号付き）
- 問題種別を分類（critical/major/minor）
- 具体的改善提案を生成
- 修正例を提示

### FR-003: カテゴリ別詳細分析
**Given**: A31評価カテゴリ（FORMAT_CHECK, CONTENT_BALANCE等）
**When**: カテゴリ特化分析を実行
**Then**:
- カテゴリ固有の評価観点を適用
- 詳細スコア（0-100点）を算出
- カテゴリ別改善提案を生成
- 参照ガイドライン遵守度を評価

### FR-004: YAML詳細結果出力
**Given**: 詳細評価結果
**When**: YAML出力を実行
**Then**:
- 手動分析と同等の詳細度でYAML出力
- 行番号付き問題点リスト
- カテゴリ別評価詳細
- 優先改善項目リスト

## 非機能要件

### NFR-001: パフォーマンス
- 単一エピソード評価: ≤5秒
- メモリ使用量: ≤100MB per session

### NFR-002: 品質
- 評価精度: 手動分析との一致率≥85%
- テストカバレッジ: ≥90%

### NFR-003: 保守性
- DDD準拠設計
- 単一責任原則遵守
- 拡張可能アーキテクチャ

## 受け入れ基準

### AC-001: 基本評価機能
```python
# テストケース例
def test_detailed_evaluation_provides_comprehensive_feedback():
    # Given
    episode_content = load_test_episode()
    checklist_items = load_a31_checklist()

    # When
    session = DetailedEvaluationSession.create(episode_content)
    result = detailed_analysis_engine.analyze(session, checklist_items)

    # Then
    assert result.overall_score > 0
    assert len(result.line_feedbacks) > 0
    assert len(result.category_analyses) == 6  # 6カテゴリ
    assert result.has_improvement_suggestions()
```

### AC-002: 行別フィードバック精度
```python
def test_line_specific_feedback_accuracy():
    # Given
    problematic_line = "だった。だった。だった。"  # 文末単調

    # When
    feedback = line_analyzer.analyze_line(problematic_line, line_number=10)

    # Then
    assert feedback.has_issues()
    assert feedback.issue_type == IssueType.STYLE_MONOTONY
    assert "文末バリエーション" in feedback.suggestion.content
    assert feedback.line_number == 10
```

## 実装制約
- Claude Code API使用禁止
- 既存A31システムとの互換性維持
- scripts.プレフィックス必須
- 型注釈完全準拠
