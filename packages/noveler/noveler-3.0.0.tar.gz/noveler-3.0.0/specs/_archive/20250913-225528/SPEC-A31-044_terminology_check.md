---
spec_id: SPEC-A31-044
status: canonical
owner: bamboocity
last_reviewed: 2025-09-13
category: QUALITY
sources: [E2E]
tags: [a31, auto-evaluation, checklist, quality, terminology]
---
# SPEC-A31-044: 固有名詞表記統一自動修正機能

## 概要
A31チェックリスト項目「固有名詞の表記統一を確認」に対応する自動修正機能の実装。

## 機能要件

### 1. プロジェクト固有用語辞書連携
- **キャラクター名**: 「太郎」「タロウ」→「太郎」（統一）
- **地名**: 「魔法学院」「魔法学園」→「魔法学院」（統一）
- **技名・魔法名**: 「ファイアボール」「火球」→「ファイアボール」（統一）
- **組織名**: 「冒険者ギルド」「冒険者組合」→「冒険者ギルド」（統一）

### 2. 表記ゆれ自動検出
- **カタカナ表記**: 「モンスター」「怪物」「魔物」の使い分け
- **漢字表記**: 「魔法使い」「魔導師」「魔術師」の統一
- **敬語表記**: 「先生」「せんせい」「センセイ」の統一

### 3. プロジェクト設定ファイル参照
- **用語辞書ファイル**: `50_管理資料/用語辞書.yaml`
- **キャラクター設定**: `50_管理資料/キャラクター/`
- **世界観設定**: `50_管理資料/世界観設定.yaml`

### 4. 文脈考慮修正
- **同音異義語**: 文脈に応じた適切な漢字選択
- **敬語レベル**: キャラクター関係に応じた敬語調整
- **時代設定**: 世界観に合わせた表記選択

## 技術仕様

### インターフェース
```python
def _fix_terminology_issues(
    self,
    content: str,
    item: A31ChecklistItem,
    evaluation: EvaluationResult
) -> tuple[str, list[str]]:
```

### 依存サービス
- `TerminologyService`: 用語辞書管理（新規作成）
- `ProjectConfigProvider`: プロジェクト設定取得
- `CharacterSettingsRepository`: キャラクター設定参照

### 用語辞書構造
```yaml
terminology:
  characters:
    - canonical: "田中太郎"
      variants: ["太郎", "タロウ", "たろう"]
  locations:
    - canonical: "魔法学院"
      variants: ["魔法学園", "魔導学院"]
  spells:
    - canonical: "ファイアボール"
      variants: ["火球", "炎球", "ファイヤーボール"]
```

## 品質要件
- **精度**: 用語統一率 > 95%
- **誤修正**: 固有名詞誤修正率 < 2%
- **カバレッジ**: プロジェクト固有用語の90%以上対応

## テストケース
1. キャラクター名の表記統一
2. 地名・組織名の統一
3. 魔法・技名の統一
4. 文脈考慮修正
5. 用語辞書ファイル不在時の処理
