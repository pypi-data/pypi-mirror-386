# SPEC-A31-EXT-001: A31重点項目抽出エンティティ仕様

## 仕様概要
A31チェックリストから重点項目を抽出し、Claude Code分析に最適化された形式で管理するドメインエンティティの仕様。

## ドメインエンティティ: A31PriorityItem

### 責務
- A31チェック項目の重要度評価と分類
- Claude分析適性の判定
- 分析プロンプトの生成管理
- 分析結果との紐づけ管理

### 不変条件
- item_id は null または空文字列であってはならない
- priority_score は 0.0 ≤ score ≤ 1.0 の範囲内
- claude_analysis_suitable は boolean値
- phase_category は定義済みフェーズのみ

### ビジネスルール
- priority_score >= 0.7 の項目のみが重点項目として認定される
- Phase2_執筆段階 の項目は priority_score に +0.2 ボーナス
- type が ["content_balance", "sensory_check", "style_variety"] の項目は Claude分析適性 = True

## バリューオブジェクト: PriorityExtractionCriteria

### 責務
- 重点項目抽出の基準定義
- 抽出ルールの集約管理
- 基準の妥当性検証

### 不変条件
- target_phases は空リストであってはならない
- priority_threshold は 0.0 < threshold <= 1.0
- keyword_weights は負の値を含んではならない

## ドメインサービス: A31PriorityExtractorService

### 責務
- A31チェックリストの解析
- 重点項目の自動識別
- 抽出基準の適用と評価

### メソッド仕様
```python
def extract_priority_items(
    checklist_data: A31ChecklistData,
    criteria: PriorityExtractionCriteria
) -> list[A31PriorityItem]:
    """重点項目を抽出する"""
    # 実装要件:
    # 1. 各項目の priority_score を計算
    # 2. criteria.priority_threshold 以上の項目を選出
    # 3. A31PriorityItem エンティティとして返却
```

## テスト要件
- 68項目のA31チェックリストから約15-20項目が抽出されること
- Phase2項目が優先的に選出されること
- Claude分析適性判定の精度が90%以上であること
