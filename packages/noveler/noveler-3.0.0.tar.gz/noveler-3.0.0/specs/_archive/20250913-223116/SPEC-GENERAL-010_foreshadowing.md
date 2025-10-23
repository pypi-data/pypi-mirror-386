# SPEC-GENERAL-010: Foreshadowing 値オブジェクト群仕様書

## SPEC-PLOT-001: 伏線管理


## 1. 目的
小説における伏線の計画、仕込み、回収を体系的に管理するための値オブジェクト群。DDD原則に従い、豊富なビジネスロジックと不変性を持つ。

## 2. 前提条件
- すべての値オブジェクトは不変（frozen=True）
- 必須フィールドの検証を実施
- 伏線のライフサイクル管理（計画→仕込み→回収準備→回収）
- エピソード番号の形式は「第XXX話」

## 3. 主要コンポーネント

### 3.1 列挙型（Enum）

#### ForeshadowingCategory（伏線カテゴリー）
- MAIN: メインプロット関連
- CHARACTER: キャラクター関連
- WORLDBUILDING: 世界観・設定関連
- MYSTERY: 謎・ミステリー関連
- EMOTIONAL: 感情的伏線
- THEMATIC: テーマ的伏線

#### ForeshadowingStatus（伏線ステータス）
- PLANNED: 計画済み
- PLANTED: 仕込み済み
- READY_TO_RESOLVE: 回収準備完了
- RESOLVED: 回収済み

#### SubtletyLevel（巧妙さレベル）
- HIGH: 非常に巧妙（読者が気づきにくい）
- MEDIUM: 適度に巧妙
- LOW: 明確（読者が気づきやすい）

### 3.2 値オブジェクト

#### ForeshadowingId
- **検証**:
  - 必須
  - 'F'で始まる4文字（例: F001）
- **メソッド**: __str__()

#### PlantingInfo（仕込み情報）
- **必須フィールド**: episode, chapter, method, content
- **検証**:
  - episodeは必須
  - chapter >= 1
  - methodは必須
  - contentは必須
- **メソッド**: is_subtle() - 巧妙な仕込みかどうか

#### ResolutionInfo（回収情報）
- **必須フィールド**: episode, chapter, method, impact
- **検証**:
  - episodeは必須
  - chapter >= 1
  - methodは必須
  - impactは必須

#### Hint（ヒント情報）
- **必須フィールド**: episode, content, subtlety
- **検証**:
  - episodeは必須
  - contentは必須

#### ReaderReaction（読者反応予測）
- **必須フィールド**: on_planting, on_hints, on_resolution
- **検証**: すべてのフィールドが必須

### 3.3 メインエンティティ（値オブジェクトとして扱う）

#### Foreshadowing
- **必須フィールド**: id, title, category, description, importance, planting, resolution, status
- **検証**:
  - titleは必須
  - descriptionは必須
  - importance: 1-5の範囲
- **ビジネスメソッド**:
  - get_planting_to_resolution_distance(): 仕込みから回収までの話数間隔
  - is_long_term(): 長期的な伏線か（10話以上）
  - is_critical(): 重要な伏線か（importance >= 4 かつ MAIN/MYSTERY）
  - can_be_resolved(): 回収可能な状態か
  - get_hint_episodes(): ヒントエピソードのリスト
  - to_summary(): サマリー文字列生成

#### ForeshadowingRelationship
- **必須フィールド**: from_id, to_id, relationship_type, description
- **検証**:
  - 同一IDの関係は不可
  - relationship_typeは["prerequisite", "parallel", "contradictory"]のいずれか

## 4. 使用例

```python
# 伏線IDの作成
foreshadowing_id = ForeshadowingId("F001")

# 仕込み情報
planting = PlantingInfo(
    episode="第001話",
    chapter=1,
    method="さりげない会話の中で言及",
    content="主人公の過去に関する謎めいた発言",
    subtlety_level=SubtletyLevel.HIGH
)

# 回収情報
resolution = ResolutionInfo(
    episode="第020話",
    chapter=3,
    method="衝撃的な真実の開示",
    impact="主人公の正体が明らかになる"
)

# 伏線の作成
foreshadowing = Foreshadowing(
    id=foreshadowing_id,
    title="主人公の隠された過去",
    category=ForeshadowingCategory.CHARACTER,
    description="主人公の記憶喪失の真相",
    importance=5,
    planting=planting,
    resolution=resolution,
    status=ForeshadowingStatus.PLANTED
)

# ビジネスロジックの使用
distance = foreshadowing.get_planting_to_resolution_distance()  # 19
is_long = foreshadowing.is_long_term()  # True
is_critical = foreshadowing.is_critical()  # False (CHARACTERカテゴリ)
```

## 5. 実装チェックリスト
- [x] すべての列挙型の定義
- [x] 各値オブジェクトの不変性保証
- [x] 必須フィールドの検証
- [x] ビジネスロジックの実装
- [x] エピソード番号抽出ロジック
- [x] 状態遷移の管理
- [ ] テストケース作成
