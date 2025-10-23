---
spec_id: SPEC-EPISODE-001
status: canonical
owner: bamboocity
last_reviewed: 2025-09-13
category: EPISODE
sources: [E2E]
tags: [episode]
---
# エピソード管理システム仕様

## SPEC-EPISODE-001: エピソード作成機能

### 概要
新規エピソードの作成と初期設定を行う機能。

### 要件
- REQ-1.1.1: 自動的に話数を割り当てる
- REQ-1.1.2: テンプレートから初期コンテンツを生成
- REQ-1.1.3: メタデータを初期化

### 機能仕様

#### 1. 話数管理
- 既存エピソードから自動的に次の番号を決定
- フォーマット: `第XXX話_タイトル.md`
- 番号は3桁ゼロパディング

#### 2. テンプレート機能
```markdown
# 第001話　タイトル

　[本文をここに記述]

---
文字数: 0
```

#### 3. メタデータ
```yaml
episode:
  number: 1
  title: "タイトル"
  status: "draft"
  created_at: "2025-01-24T12:00:00"
  target_words: 3000
```

### テストケース
- `tests/unit/domain/entities/test_episode.py::test_エピソード作成`
- `tests/integration/test_episode_creation_flow.py`

### 実装
- `scripts/domain/entities/episode.py`
- `scripts/application/use_cases/create_episode_use_case.py`
- `scripts/bin/noveler`

### CLIコマンド
```bash
# 新規エピソード作成
novel write new

# タイトル指定
novel write new --title "冒険の始まり"

# テンプレート使用
novel write new --template battle_scene
```

---

## SPEC-EPISODE-002: エピソード編集機能

### 概要
既存エピソードの編集と自動保存機能。

### 要件
- REQ-1.2.1: エディタとの統合
- REQ-1.2.2: 自動保存とバックアップ
- REQ-1.2.3: 編集前後の品質チェック

### 機能仕様

#### 1. エディタ起動
- 環境変数EDITORまたはデフォルト（nano/vim）を使用
- 編集完了後に自動的に処理を継続

#### 2. 自動保存
- 編集前にバックアップ作成
- 5分ごとの自動保存（設定可能）
- 変更検知による保存

#### 3. 品質チェック統合
- 編集完了時に自動品質チェック
- 問題がある場合は警告表示
- オプションで編集継続

### テストケース
- `tests/unit/writing/test_episode_editor.py`
- `tests/e2e/features/episode_editing.feature`

### 実装
- `scripts/writing/episode_editor.py`
- `scripts/domain/services/file_watcher_service.py`

---

## SPEC-EPISODE-003: エピソードステータス管理

### 概要
エピソードのライフサイクル管理機能。

### 要件
- REQ-1.3.1: ステータス遷移の制御
- REQ-1.3.2: ステータスに応じた操作制限
- REQ-1.3.3: ステータス履歴の記録

### 機能仕様

#### 1. ステータス定義
```python
class EpisodeStatus(Enum):
    UNWRITTEN = "未執筆"
    DRAFT = "下書き"
    IN_PROGRESS = "執筆中"
    COMPLETED = "執筆済み"
    REVIEWED = "確認済み"
    PUBLISHED = "公開済み"
```

#### 2. 遷移ルール
- UNWRITTEN → DRAFT: 執筆開始時
- DRAFT → IN_PROGRESS: 本格執筆開始
- IN_PROGRESS → COMPLETED: 執筆完了
- COMPLETED → REVIEWED: 品質確認完了
- REVIEWED → PUBLISHED: 公開処理

#### 3. 制約事項
- PUBLISHEDは編集不可
- 逆方向遷移は特定条件下のみ
- 品質スコア基準を満たさない場合は遷移不可

### テストケース
- `tests/unit/domain/entities/test_episode.py::test_ステータス遷移`
- `tests/unit/domain/value_objects/test_episode_status.py`

### 実装
- `scripts/domain/entities/episode.py::EpisodeStatus`
- `scripts/domain/services/episode_lifecycle_service.py`

### 使用例
```python
episode = Episode(number=1, title="始まりの章")
episode.start_writing()  # UNWRITTEN → DRAFT
episode.complete()       # エラー: まだIN_PROGRESSではない
episode.progress()       # DRAFT → IN_PROGRESS
episode.complete()       # IN_PROGRESS → COMPLETED
```

---

## SPEC-EPISODE-004: エピソード完了処理

### 概要
エピソード執筆完了時の統合処理機能。

### 要件
- REQ-1.4.1: 文字数の自動集計
- REQ-1.4.2: 品質チェックの実行
- REQ-1.4.3: メタデータの更新

### 機能仕様

#### 1. 完了時処理フロー
1. 文字数カウント（ルビ除外）
2. 品質チェック実行
3. ステータス更新
4. 話数管理ファイル更新
5. 完了通知

#### 2. 文字数計算
- ルビ記法を除外: `｜漢字《かんじ》` → 「漢字」
- 空白行・メタデータ除外
- 実際の表示文字数を算出

#### 3. 統計情報
```yaml
statistics:
  total_episodes: 10
  total_words: 35000
  average_words: 3500
  completion_rate: 0.85
```

### テストケース
- `tests/integration/test_episode_completion_flow.py`
- `tests/unit/domain/entities/test_episode_completion.py`

### 実装
- `scripts/domain/entities/episode_completion.py`
- `scripts/management/complete_episode.py`
- `scripts/application/use_cases/complete_episode_use_case.py`

### コマンド
```bash
# エピソード完了処理
novel complete-episode プロジェクト名 1

# ステータス指定
novel complete-episode プロジェクト名 1 --status 確認済み

# 品質チェックスキップ
novel complete-episode プロジェクト名 1 --skip-quality
```
