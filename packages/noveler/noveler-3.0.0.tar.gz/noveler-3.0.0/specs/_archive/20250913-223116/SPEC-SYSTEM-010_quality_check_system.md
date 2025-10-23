# 品質チェックシステム仕様

## SPEC-QUALITY-001: 基本文体チェック

### 概要
小説の基本的な文体や表記の問題を検出するシステム。

### 要件
- REQ-2.1.1: 連続する同一表現を検出
- REQ-2.1.2: 過剰な修飾語を検出
- REQ-2.1.3: 不適切な文末表現を検出

### 機能仕様

#### 1. チェック項目
- 同一語句の連続使用（3回以上）
- 「とても」「非常に」等の過剰修飾
- 「です・ます」と「だ・である」の混在
- 読点の過不足
- 一文の長さ（100文字以上で警告）

#### 2. 評価基準
- 各項目を100点満点で評価
- 問題の重要度に応じて減点
- 総合スコアを算出

### テストケース
- `tests/unit/quality/test_basic_style_checker.py`
- `tests/integration/test_quality_check_flow.py`

### 実装
- （参考）旧構成: `scripts/quality/check_basic_style.py`, `scripts/domain/quality/services.py::BasicStyleChecker`
- 現行関連: `src/noveler/tools/unified_syntax_fixer.py`, `src/noveler/application/use_cases/quality_check_use_case.py`

### 使用例
```python
from scripts.quality.check_basic_style import check_basic_style

result = check_basic_style(episode_content)
print(f"基本文体スコア: {result.score}")
for issue in result.issues:
    print(f"- {issue.line}: {issue.message}")
```

---

## SPEC-QUALITY-002: 構成チェック

### 概要
小説の構成面（起承転結、場面転換など）を評価するシステム。

### 要件
- REQ-2.2.1: 章の構成バランスを評価
- REQ-2.2.2: 場面転換の適切性を評価
- REQ-2.2.3: 伏線と回収の整合性を確認

### 機能仕様

#### 1. 構成分析
- 序破急の配分チェック
- 場面転換の頻度と自然さ
- 視点の一貫性
- クライマックスの配置

#### 2. 伏線管理
- 伏線の登録と追跡
- 回収状況の確認
- 未回収伏線の警告

### テストケース
- `tests/unit/quality/test_composition_checker.py`
- `tests/e2e/features/quality_check.feature`

### 実装
- （参考）旧構成: `scripts/quality/check_composition.py`, `scripts/domain/entities/foreshadowing.py`
- 現行関連: `src/noveler/application/use_cases/quality_check_use_case.py`, `src/noveler/domain/entities/foreshadowing_validation_session.py`

---

## SPEC-QUALITY-003: AI協調品質チェック

### 概要
AIを活用した高度な品質チェック機能。

### 要件
- REQ-2.3.1: 個人の執筆傾向を学習
- REQ-2.3.2: パーソナライズされた改善提案
- REQ-2.3.3: 成長トレンドの可視化

### 機能仕様

#### 1. 学習機能
- 過去の執筆データから傾向を分析
- よくある間違いパターンの検出
- 改善履歴の追跡

#### 2. 提案機能
- 個人に最適化された改善案
- 具体的な修正例の提示
- 優先度付きの課題リスト

#### 3. 視点連動評価
- 一人称/三人称に応じた評価基準
- 視点の一貫性チェック
- 視点特有の表現チェック

### テストケース
- `tests/unit/domain/quality/test_viewpoint_entities.py`
- `tests/integration/test_ai_quality_enhancement.py`

### 実装
- （参考）旧構成: `scripts/domain/quality/viewpoint_entities.py`, `scripts/domain/services/quality_evaluation_service.py`, `scripts/application/use_cases/enhanced_quality_check_use_case.py`
- 現行関連: `src/noveler/application/use_cases/viewpoint_aware_quality_check.py`, `src/noveler/application/use_cases/integrated_quality_check_use_case.py`

### データ構造
```yaml
# 50_管理資料/品質記録.yaml
quality_checks:
  - episode_number: 1
    timestamp: "2025-01-24T12:00:00"
    scores:
      basic_style: 85.0
      composition: 90.0
      narrative_depth: 78.0
    improvements:
      - category: "修飾語"
        frequency: 5
        suggestion: "「とても」を別の表現に"
learning_data:
  common_issues:
    - "同一表現の繰り返し"
    - "視点の揺れ"
  improvement_rate: 0.15
```

---

## SPEC-QUALITY-004: 品質ゲートシステム

### 概要
公開前の品質保証を行うゲートキーパーシステム。

### 要件
- REQ-2.4.1: 最低品質スコアの設定と判定
- REQ-2.4.2: 必須チェック項目の確認
- REQ-2.4.3: 段階的な品質基準（初心者/中級/上級）

### 機能仕様

#### 1. 品質ゲート設定
```yaml
quality_gates:
  beginner:
    min_score: 60
    required_checks: ["basic_style"]
  intermediate:
    min_score: 75
    required_checks: ["basic_style", "composition"]
  advanced:
    min_score: 85
    required_checks: ["basic_style", "composition", "narrative_depth"]
```

#### 2. ゲート判定
- スコア閾値チェック
- 必須項目の完了確認
- ブロッキング/警告の判定

### テストケース
- `tests/unit/domain/test_quality_standards.py`
- `tests/integration/test_quality_gate_workflow.py`

### 実装
- `scripts/domain/quality_standards.py`
- `scripts/tools/quality_gate_check.py`

### コマンド
```bash
# 品質ゲートチェック
novel check episode.md --gate intermediate

# 強制的に通過
novel check episode.md --gate advanced --force
```
