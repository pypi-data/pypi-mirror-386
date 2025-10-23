# SPEC-PLOT-101: Enhanced Episode Plot Entity Claude Code統合実装仕様書

## 概要

Claude Code最終版プロンプトで96%一致度を達成した制作指針⇔出力形式対応関係を、Enhanced Episode Plot Entityのドメインエンティティとして実装する。

## 前提条件

- SPEC-PLOT-001で設計された基本構造
- Claude Code プロンプト最終版テストで実証された構造要素
- SDD+DDD+TDD準拠の開発プロセス
- 統合インポート管理システム（scripts.プレフィックス必須）

## 技術要件

### 1. シーン描写5要素構造

```python
@dataclass
class SceneDetails:
    """シーン詳細（制作指針対応版）"""
    title: str
    location_description: str  # 【指針1対応】具体的な場所描写（視覚的詳細）
    character_actions: str     # 【指針2対応】主要キャラクターの具体的行動・表情・仕草
    emotional_expressions: str # 【指針3対応】感情を示す身体反応・表情変化
    technical_integration: str # 【指針4対応】このシーンで説明する技術概念と説明方法
    scene_hook: str           # 【指針5対応】次のシーンや読者の興味を引く要素
    time: str = "時間設定"
    weather: str = "天候・雰囲気"
    purpose: str = "シーンの目的"
    character_focus: Optional[str] = None
    emotional_beats: Optional[list[str]] = None
    opening_description: Optional[str] = None
```

### 2. 感情アーク4段階詳細構造

```python
@dataclass
class EmotionalStage:
    """感情変化段階（制作指針対応版）"""
    emotion_name: str          # 感情状態の名称
    trigger_event: str         # 【指針対応】きっかけとなる具体的出来事
    physical_expression: str   # 【指針対応】身体的表現（眉間のしわ、ため息等）
    internal_dialogue: str     # 【指針対応】内面を表すセリフ・思考
    transition_condition: str  # 【指針対応】次段階への移行きっかけ

@dataclass
class CharacterEmotionalArc:
    """キャラクター感情アーク（4段階制作指針準拠）"""
    stage1: EmotionalStage
    stage2: EmotionalStage
    stage3: EmotionalStage
    stage4: EmotionalStage
```

### 3. 技術要素3レベル説明構造

```python
@dataclass
class ProgrammingConcept:
    """プログラミング概念（3レベル説明制作指針準拠）"""
    concept: str
    level1_explanation: str    # 【指針対応】完全初心者向け日常比喩説明
    level2_explanation: str    # 【指針対応】入門者向け基本概念+実例
    level3_explanation: str    # 【指針対応】経験者向け応用+思考プロセス
    story_integration_method: str  # 【指針対応】物語への自然な組み込み方法
    dialogue_example: str     # 【指針対応】実際のキャラクター説明セリフ例
    educational_value: str = "教育的価値"
    magic_adaptation: str = "魔法システムへの適応"
```

### 4. 読者エンゲージメント指針対応

```python
@dataclass
class EngagementElements:
    """読者エンゲージメント要素（制作指針4対応）"""
    opening_hook: OpeningHook
    emotional_peaks: list[EmotionalPeak]
    chapter_endings: ChapterEnding

@dataclass
class OpeningHook:
    """冒頭3行の黄金パターン"""
    line1_impact: str     # 【指針対応】インパクトのあるセリフ・状況
    line2_context: str    # 【指針対応】主人公の現状を示す描写
    line3_intrigue: str   # 【指針対応】読者の興味を引く謎・予感

@dataclass
class EmotionalPeak:
    """感情のピーク"""
    scene_location: str   # 【指針対応】感情が高まるシーンの場所
    peak_emotion: str     # 【指針対応】ピーク時の感情種類
    trigger_method: str   # 【指針対応】感情を引き起こす具体的方法
```

## 実装手順

### Phase 1: Value Objects拡張 (高優先度)
1. SceneDetails クラスの5要素構造化
2. EmotionalStage, CharacterEmotionalArc の実装
3. ProgrammingConcept の3レベル説明対応

### Phase 2: Integration System (高優先度)
1. 【指針X対応】マーカーシステムの実装
2. 制作指針⇔出力形式対応テーブルの作成
3. 検証メソッドの拡張

### Phase 3: Enhancement Methods (中優先度)
1. from_claude_code_specification() メソッドの実装
2. to_claude_code_prompt() メソッドの実装
3. validate_claude_code_compliance() メソッドの実装

## 制約条件

### DDD準拠
- ドメインエンティティとしての純粋性維持
- 外部依存の排除
- 統合インポート管理システム準拠

### TDD準拠
- 仕様書作成 → テスト作成 → 実装の順序
- @pytest.mark.spec("SPEC-PLOT-002") マーカー必須
- 各フェーズでのテスト先行実装

### 品質要件
- 型安全性: すべてのメソッド引数に型注釈
- デフォルト値: Optional以外は適切なデフォルト値
- mypy strict準拠
- ruff linter通過

## 成功指標

1. **機能要件**: Claude Code最終版プロンプトの96%一致度構造の完全実装
2. **品質要件**: mypy, ruff, pytest全通過
3. **性能要件**: to_comprehensive_yaml_dict()の実行時間≤100ms
4. **保守要件**: 各構造要素の独立性とテスタビリティ

## リスク管理

### 高リスク
- 既存GeneratedEpisodePlotとの互換性維持
- メモリ使用量の増加（236行テンプレート対応）

### 中リスク
- 複雑性増大による保守コストの上昇
- パフォーマンス劣化の可能性

### 軽減策
- 段階的リファクタリング
- 包括的テストカバレッジ
- パフォーマンス監視の実装

## 実装期限

- Phase 1: 即座実行（構造拡張）
- Phase 2: 24時間以内（統合システム）
- Phase 3: 48時間以内（Enhancement Methods）

## 検証方法

1. Claude Code最終版プロンプト構造との対応関係検証
2. 既存システムとの互換性テスト
3. パフォーマンス・メモリ使用量測定
4. ドメインロジックの整合性確認
