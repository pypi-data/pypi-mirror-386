# SPEC-EPISODE-015: 話数管理.yaml自動同期機能 仕様書

## 1. 目的
完成処理時に話数管理.yamlファイルを自動的に更新し、手動でのメタデータ更新作業を不要にする。品質チェック結果、完成状態、統計情報を自動で話数管理.yamlに同期する。

## 2. 前提条件
- 既存のプロジェクトに話数管理.yamlファイルが存在する
- 品質記録活用システムが実装されている
- 完成処理コマンド（novel complete-episode --enhanced）が実行される
- YAMLファイルの読み書き権限がある

## 3. 主要な振る舞い

### 3.1 完成処理時の自動同期
- 入力: プロジェクト名、エピソード番号、品質チェック結果、完成状態
- 処理: 話数管理.yamlの対象エピソード情報を更新
- 出力: 更新成功/失敗の結果

### 3.2 更新対象データ
- completion_status: 完成状態（執筆済み、推敲済み、公開済み等）
- completion_date: 完成日時
- quality_score: 品質スコア
- quality_grade: 品質グレード（A、B、C等）
- word_count: 文字数
- revision_count: 修正回数
- last_updated: 最終更新日時

### 3.3 統計情報の自動計算
- 完成済み話数の自動カウント
- 平均品質スコアの自動計算
- 章別進捗率の自動算出
- 全体進捗率の自動更新

## 4. 入出力仕様

### 4.1 入力データ型
```python
@dataclass
class EpisodeCompletionData:
    project_name: str
    episode_number: int
    completion_status: str
    quality_score: float
    quality_grade: str
    word_count: int
    revision_count: int
    completion_date: datetime
    quality_check_results: Dict[str, Any]
```

### 4.2 出力データ型
```python
@dataclass
class SyncResult:
    success: bool
    updated_fields: List[str]
    error_message: Optional[str] = None
    backup_created: bool = False
```

## 5. エラーハンドリング
- ファイルが存在しない場合: 適切なエラーメッセージを返す
- 権限エラー: 書き込み権限がない場合のエラー処理
- YAML構文エラー: 既存ファイルの構文が不正な場合の処理
- エピソード番号不一致: 存在しないエピソード番号の場合
- バックアップ作成: 更新前に自動バックアップを作成

## 6. パフォーマンス要件
- レスポンスタイム: 1秒以内での更新完了
- ファイルサイズ: 10MB以下のYAMLファイルに対応
- 同期処理: 他の処理をブロックしない非同期処理

## 7. セキュリティ考慮事項
- ファイルパス検証: パストラバーサル攻撃の防止
- 入力値検証: 不正な値の混入防止
- バックアップ保護: 機密情報の適切な保護
- 権限チェック: 適切なファイル権限の確認

## 8. 実装チェックリスト
- [ ] 話数管理.yamlの読み込み機能
- [ ] エピソード情報の更新機能
- [ ] 統計情報の自動計算機能
- [ ] バックアップ作成機能
- [ ] エラーハンドリングの実装
- [ ] パフォーマンス要件の確認
- [ ] セキュリティ考慮事項の実装
- [ ] 型定義の完全性確認
- [ ] テストケース作成
- [ ] ドキュメント更新
- [ ] コードレビュー
