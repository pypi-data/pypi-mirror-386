---
spec_id: SPEC-PLOT-002
status: canonical
owner: bamboocity
last_reviewed: 2025-09-13
category: PLOT
sources: [REQ]
tags: [plot]
---
# SPEC-PLOT-002: 章別プロット整合性オーケストレータ仕様書

## 要件トレーサビリティ

**要件ID**: REQ-PLOT-003, REQ-PLOT-006, REQ-PLOT-008 (プロット整合性・推論・進捗管理)

**主要要件**:
- REQ-PLOT-003: プロット整合性検証機能
- REQ-PLOT-006: 章別プロット自動推論機能
- REQ-PLOT-008: プロット進捗管理機能

**実装状況**: ✅実装済み
**テストカバレッジ**: tests/unit/test_chapter_plot_consistency_orchestrator.py
**関連仕様書**: SPEC-PLOT-001_claude-code-integration-plot-generation.md

## 概要
`ChapterPlotConsistencyOrchestrator`は、マイナーバージョンアップ時の章固有影響を管理するオーケストレータです。章別プロットの変更に伴う話数管理、伏線管理の整合性維持を自動化し、必要なレビューポイントを特定・記録します。

## クラス設計

### ChapterPlotConsistencyOrchestrator

**責務**
- 章別プロット変更の影響分析
- 単一章・複数章変更の処理分岐
- 話数管理の自動更新
- 伏線管理の整合性チェック
- 章別レビューノートの生成

## データ構造

### ChapterConsistencyUpdateResult (DataClass)
```python
@dataclass(frozen=True)
class ChapterConsistencyUpdateResult:
    success: bool                           # 処理成功フラグ
    update_summary: list[str]               # 更新サマリー
    affected_chapters: list[int] = []       # 影響を受けた章番号
    error_message: str = ""                 # エラーメッセージ
```

## パブリックメソッド

### execute_chapter_consistency_update()

**シグネチャ**
```python
def execute_chapter_consistency_update(self, version_change: dict) -> ChapterConsistencyUpdateResult:
```

**目的**
バージョン変更に伴う章別プロットの整合性更新を実行する。

**引数**
```python
version_change = {
    "changed_files": list[str],         # 変更されたファイル一覧
    "to": str,                          # 新バージョン番号
    "from": str,                        # 前バージョン番号
    "description": str,                 # 変更内容説明
}
```

**戻り値**
- `ChapterConsistencyUpdateResult`: 整合性更新結果

**処理フロー**
1. **変更ファイル分析**: 章別プロットファイルの特定
2. **影響範囲判定**: 単一章 vs 複数章の判定
3. **処理分岐**:
   - **単一章**: `_update_single_chapter()`による個別処理
   - **複数章**: 各章に対する個別処理の実行
4. **結果統合**: 更新サマリーと影響章の集約

**成功パターン**
- 単一章変更の成功処理
- 複数章変更の成功処理
- 必要な更新の完了

**エラーパターン**
- ファイルアクセスエラー
- 依存サービスの実行エラー
- データ形式エラー

## プライベートメソッド

### _update_single_chapter()

**シグネチャ**
```python
def _update_single_chapter(self, chapter_impact, new_version: str, update_summary: list[str]):
```

**目的**
単一章の変更に対する各種ファイルの更新処理を実行する。

**処理内容**
1. **話数管理更新** (`requires_episode_review`が`True`の場合):
   - 話数データの読み込み
   - 章別エピソードの更新
   - 更新データの保存
   - サマリーへの追加

2. **伏線管理更新** (`requires_foreshadowing_review`が`True`の場合):
   - 伏線データの読み込み
   - 章別伏線の影響分析
   - レビューノートの追加
   - 更新データの保存
   - サマリーへの追加

### _add_chapter_foreshadowing_review()

**シグネチャ**
```python
def _add_chapter_foreshadowing_review(self, foreshadowing_data: dict, impact, new_version: str):
```

**目的**
章別プロット変更に伴う伏線レビューノートを伏線管理データに追加する。

**処理内容**
1. `chapter_review_notes`セクションの初期化
2. レビューノートエントリの作成
3. 伏線データへの追加

**レビューノート形式**
```python
{
    "version": str,                     # バージョン番号
    "chapter": int,                     # 対象章番号
    "affected_foreshadowing": list[str], # 影響を受けた伏線ID
    "recommendation": str,              # レビュー推奨事項
    "status": "PENDING_REVIEW",         # レビューステータス
}
```

## 処理分岐ロジック

### 単一章変更の場合
```python
if len(chapter_files) == 1:
    # 単一章の詳細影響分析
    impact = self.chapter_analyzer.analyze_chapter_impact(chapter_files[0])
    affected_chapters = [impact.affected_chapter]

    # 章固有の更新処理
    self._update_single_chapter(impact, new_version, update_summary)
```

### 複数章変更の場合
```python
elif len(chapter_files) > 1:
    # 複数章の総合影響分析
    impact = self.chapter_analyzer.analyze_multiple_chapters_impact(chapter_files)
    affected_chapters = impact.affected_chapters

    # 各章ごとに個別更新処理
    for chapter_impact in impact.chapter_impacts:
        self._update_single_chapter(chapter_impact, new_version, update_summary)
```

## 依存サービス

### chapter_analyzer
- `analyze_chapter_impact()`: 単一章の影響分析
- `analyze_multiple_chapters_impact()`: 複数章の影響分析

### episode_updater
- `update_chapter_episodes()`: 章別エピソードの更新

### foreshadow_analyzer
- `analyze_chapter_foreshadowing()`: 章別伏線の影響分析

### file_manager
- `load_episodes_data()`: 話数データの読み込み
- `save_episodes_data()`: 話数データの保存
- `load_foreshadowing_data()`: 伏線データの読み込み
- `save_foreshadowing_data()`: 伏線データの保存

## 設計原則遵守

### DDD準拠
- ✅ オーケストレータパターンによる複数サービスの調整
- ✅ 明確な責務分離（分析・更新・保存）
- ✅ 不変オブジェクトによる結果表現

### TDD準拠
- ✅ 明確な入出力定義
- ✅ 包括的なエラーハンドリング
- ✅ 型安全な実装

## 使用例

```python
# 依存サービスの準備
chapter_analyzer = ChapterAnalyzer()
episode_updater = EpisodeUpdater()
foreshadow_analyzer = ForeshadowAnalyzer()
file_manager = FileManager()

# オーケストレータ作成
orchestrator = ChapterPlotConsistencyOrchestrator(
    chapter_analyzer=chapter_analyzer,
    episode_updater=episode_updater,
    foreshadow_analyzer=foreshadow_analyzer,
    file_manager=file_manager
)

# 単一章変更の処理
single_chapter_change = {
    "changed_files": ["20_プロット/章別プロット/第3章.yaml"],
    "to": "v1.2.1",
    "from": "v1.2.0",
    "description": "第3章のキャラクター関係性を調整"
}

result = orchestrator.execute_chapter_consistency_update(single_chapter_change)

if result.success:
    print("章別整合性更新完了")
    print(f"影響を受けた章: {result.affected_chapters}")
    for summary in result.update_summary:
        print(f"- {summary}")
else:
    print(f"更新失敗: {result.error_message}")

# 複数章変更の処理
multiple_chapters_change = {
    "changed_files": [
        "20_プロット/章別プロット/第2章.yaml",
        "20_プロット/章別プロット/第3章.yaml",
        "20_プロット/章別プロット/第4章.yaml"
    ],
    "to": "v1.3.0",
    "from": "v1.2.1",
    "description": "中盤の展開を大幅改訂"
}

multi_result = orchestrator.execute_chapter_consistency_update(multiple_chapters_change)

# 結果の詳細確認
if multi_result.success:
    print(f"複数章更新完了: {len(multi_result.affected_chapters)}章")
    for i, summary in enumerate(multi_result.update_summary, 1):
        print(f"{i}. {summary}")
```

## 更新サマリー例

### 単一章変更の場合
```
- 第3章の話数ステータスを更新
- 第3章の伏線レビューノートを追加
```

### 複数章変更の場合
```
- 第2章の話数ステータスを更新
- 第2章の伏線レビューノートを追加
- 第3章の話数ステータスを更新
- 第3章の伏線レビューノートを追加
- 第4章の話数ステータスを更新
```

## 伏線レビューノート例

```yaml
chapter_review_notes:
  - version: "v1.2.1"
    chapter: 3
    affected_foreshadowing:
      - "F001"  # 主人公の出生の秘密
      - "F003"  # 魔法の剣の真の力
    recommendation: "キャラクター関係性の変更により、伏線の配置タイミングを見直すことを推奨"
    status: "PENDING_REVIEW"

  - version: "v1.3.0"
    chapter: 2
    affected_foreshadowing:
      - "F002"  # 敵の真の目的
    recommendation: "展開の前倒しにより、伏線解決のタイミング調整が必要"
    status: "PENDING_REVIEW"
```

## 影響分析データ例

### 章別影響情報
```python
chapter_impact = {
    "affected_chapter": 3,
    "requires_episode_review": True,
    "requires_foreshadowing_review": True,
    "change_severity": "medium",
    "estimated_episodes": [7, 8, 9],
    "foreshadowing_risk": ["F001", "F003"]
}
```

### 複数章影響情報
```python
multiple_impact = {
    "affected_chapters": [2, 3, 4],
    "chapter_impacts": [
        {"affected_chapter": 2, "requires_episode_review": True, ...},
        {"affected_chapter": 3, "requires_episode_review": True, ...},
        {"affected_chapter": 4, "requires_episode_review": False, ...}
    ],
    "cross_chapter_dependencies": True
}
```

## エラーハンドリング

### ファイルアクセスエラー
```python
try:
    episodes_data = self.file_manager.load_episodes_data()
except FileNotFoundError:
    # エラー情報をサマリーに追加
    error_message = "話数管理ファイルが見つかりません"
```

### サービス実行エラー
```python
try:
    impact = self.chapter_analyzer.analyze_chapter_impact(chapter_file)
except AnalysisError as e:
    return ChapterConsistencyUpdateResult(
        success=False,
        error_message=f"章影響分析エラー: {str(e)}"
    )
```

## テスト観点

### 単体テスト
- 単一章変更の正常処理
- 複数章変更の正常処理
- エラー条件での処理
- レビューノート生成の正確性
- 依存サービスとの協調

### 統合テスト
- 実際のプロットファイル変更での動作
- ファイル読み書きの確認
- バージョン管理システムとの連携

## 品質基準

- **整合性**: 章変更に伴う関連データの適切な更新
- **追跡性**: 詳細な更新サマリーとレビューノート
- **自動化**: 手動作業の最小化
- **柔軟性**: 単一・複数章変更への対応
- **信頼性**: エラー時の安全な処理と明確な報告
