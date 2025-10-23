# YAMLリポジトリインターフェース 仕様書

## 1. 目的
小説執筆支援システムにおけるデータ永続化を担当するリポジトリのインターフェースと実装仕様を定義する。DDD原則に基づき、ドメイン層とインフラ層を適切に分離する。

## 2. 前提条件
- YAMLファイル形式でデータを永続化
- ファイルシステムベースのストレージ
- プロジェクトごとに標準化されたディレクトリ構造
- ドメインエンティティとの相互変換が可能

## 3. 主要な振る舞い

### 3.1 リポジトリインターフェース（ドメイン層）

#### EpisodeRepository
**責務**: エピソードの永続化抽象化

**主要メソッド**:
- `save(episode: Episode, project_id: str)` - エピソード保存
- `find_by_project_and_number(project_id: str, episode_number: int)` - 番号検索
- `find_all_by_project(project_id: str)` - 全エピソード取得
- `get_next_episode_number(project_id: str)` - 次番号取得
- `delete(episode_id: str, project_id: str)` - 削除

**高度な検索**:
- `find_by_status(project_id, status)` - ステータス検索
- `find_by_tags(project_id, tags)` - タグ検索
- `find_by_quality_score_range(project_id, min, max)` - 品質スコア範囲検索
- `find_ready_for_publication(project_id)` - 公開準備完了検索

#### ProjectRepository
**責務**: プロジェクトメタデータの永続化抽象化

**主要メソッド**:
- `exists(project_id: str)` - 存在確認
- `create(project: Project)` - プロジェクト作成
- `find_by_id(project_id: str)` - ID検索
- `update(project: Project)` - 更新
- `list_all()` - 全プロジェクト一覧

### 3.2 YAML実装（インフラ層）

#### ディレクトリ構造
```
プロジェクトルート/
├── 40_原稿/
│   ├── 第001話_タイトル.md
│   ├── 第002話_タイトル.md
│   └── ...
└── 50_管理資料/
    ├── 話数管理.yaml
    ├── 品質記録.yaml
    └── アクセス分析.yaml
```

#### YamlEpisodeRepository実装詳細

**ファイル形式**:
1. **原稿ファイル** (Markdown)
   - パス: `40_原稿/第{番号:03d}話_{タイトル}.md`
   - 内容: エピソードの本文のみ

2. **話数管理.yaml**
```yaml
episodes:
  - number: 1
    title: "始まりの朝"
    status: "DRAFT"
    word_count: 2500
    target_words: 3000
    version: 2
    quality_score: 85
    started_at: "2025-01-20T10:00:00"
    completed_at: "2025-01-20T15:30:00"
    updated_at: "2025-01-20T15:30:00"
  - number: 2
    title: "新たな出会い"
    status: "IN_PROGRESS"
    # ...
updated_at: "2025-01-20T15:30:00"
```

**データ変換ロジック**:
1. **エンティティ → YAML**:
   - エピソード番号、タイトル、ステータスを辞書形式に変換
   - 日時はISO形式文字列に変換
   - None値は除外

2. **YAML → エンティティ**:
   - EpisodeFactoryを使用してエンティティ再構築
   - 日時文字列をdatetimeオブジェクトに変換
   - ステータスをEnumに変換

### 3.3 トランザクション管理

**原子性保証**:
- ファイル書き込みは一時ファイル経由
- 成功時のみ本番ファイルに移動
- エラー時は変更をロールバック

**整合性保証**:
- 原稿ファイルと管理YAMLの同期更新
- バージョン番号による楽観的ロック

## 4. エラーハンドリング

### 4.1 ファイルシステムエラー
- **ファイル不在**: 新規作成として処理
- **権限エラー**: InfrastructureExceptionを送出
- **ディスク容量不足**: 明確なエラーメッセージ

### 4.2 データ整合性エラー
- **YAML形式エラー**: デフォルト値で復旧試行
- **必須フィールド欠損**: DomainExceptionを送出
- **型変換エラー**: 詳細ログ出力後、エラー送出

## 5. パフォーマンス最適化

### 5.1 キャッシュ戦略
- 話数管理YAMLをメモリキャッシュ
- 更新時のみファイル書き込み
- TTL: 5分（設定可能）

### 5.2 遅延読み込み
- 原稿ファイルは必要時のみ読み込み
- リスト取得時はメタデータのみ

### 5.3 バッチ処理
- 複数エピソードの一括更新対応
- トランザクション単位での書き込み

## 6. 拡張性

### 6.1 プラガブルストレージ
- インターフェースベースの実装
- 将来的なDB移行を考慮
- ストレージアダプターパターン

### 6.2 クエリオブジェクト
```python
query = EpisodeQuery()
    .with_project("my-novel")
    .with_statuses(["COMPLETED", "REVIEWED"])
    .with_quality_score_range(70, 100)
    .order_by_field("episode_number", desc=False)
    .with_pagination(limit=20, offset=0)
```

## 7. 実装メモ
- インターフェース: `src/noveler/domain/repositories/episode_repository.py`
- YAML実装: `src/noveler/infrastructure/repositories/yaml_episode_repository.py`
- テスト: `tests/integration/test_yaml_episode_repository.py`
- 作成日: 2025-07-21

## 8. セキュリティ考慮事項
- パスインジェクション対策（Path.resolve()使用）
- ファイル名のサニタイズ
- YAMLの安全な読み込み（safe_load使用）

## 9. 未決定事項
- [ ] 分散環境での同時書き込み制御
- [ ] 大量エピソード時のページング最適化
- [ ] バックアップ・リストアの詳細仕様
- [ ] 暗号化対応
