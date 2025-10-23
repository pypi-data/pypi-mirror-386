# SPEC-GENERAL-033: 公開準備ユースケース仕様書

## 概要
`PublishPreparationUseCase`は、エピソードを外部プラットフォームに公開するための準備処理を統合管理するユースケースです。品質チェック、バックアップ作成、フォーマット変換を含む包括的な公開準備フローを提供します。

## クラス設計

### PublishPreparationUseCase

**責務**
- エピソード公開準備の統合管理
- 品質基準の確認
- バックアップ作成の調整
- プラットフォーム別フォーマット変換
- 公開可否の判定

## データ構造

### PublishFormat (Enum)
```python
class PublishFormat(Enum):
    NAROU = "narou"         # 小説家になろう
    KAKUYOMU = "kakuyomu"   # カクヨム
    PLAIN = "plain"         # プレーンテキスト
```

### PublishStatus (Enum)
```python
class PublishStatus(Enum):
    READY = "ready"                     # 公開準備完了
    NEEDS_REVIEW = "needs_review"       # レビューが必要
    NEEDS_IMPROVEMENT = "needs_improvement"  # 改善が必要
    ERROR = "error"                     # エラー
```

### PreparationStep (DataClass)
```python
@dataclass
class PreparationStep:
    name: str               # ステップ名
    status: str             # ステータス
    message: str            # メッセージ
```

### PublishPreparationRequest (DataClass)
```python
@dataclass
class PublishPreparationRequest:
    project_name: str                           # プロジェクト名
    episode_number: int | None = None           # エピソード番号（None=最新）
    format_type: PublishFormat = NAROU          # 公開フォーマット
    include_quality_check: bool = True          # 品質チェック実行フラグ
    create_backup: bool = True                  # バックアップ作成フラグ
    quality_threshold: float = 70.0             # 品質基準値
    project_directory: str | None = None        # プロジェクトディレクトリ
```

### PublishPreparationResponse (DataClass)
```python
@dataclass
class PublishPreparationResponse:
    status: PublishStatus                       # 公開準備ステータス
    episode_path: Path                          # エピソードファイルパス
    formatted_content: str                      # フォーマット済みコンテンツ
    preparation_steps: list[PreparationStep]   # 実行ステップ一覧
    quality_score: float | None = None          # 品質スコア
    backup_path: Path | None = None             # バックアップパス
    format_type: PublishFormat = NAROU          # 使用フォーマット
    message: str = ""                           # 結果メッセージ
```

## パブリックメソッド

### execute()

**シグネチャ**
```python
def execute(self, request: PublishPreparationRequest) -> PublishPreparationResponse:
```

**目的**
指定されたエピソードに対して包括的な公開準備処理を実行する。

**引数**
- `request`: 公開準備リクエスト

**戻り値**
- `PublishPreparationResponse`: 公開準備結果

**処理フロー**
1. **プロジェクト確認**: プロジェクトディレクトリの存在確認
2. **エピソード取得**: 指定エピソードまたは最新エピソードの取得
3. **品質チェック**: 品質スコアの確認と基準値との比較
4. **ステータス判定**: エピソードの公開可否判定
5. **バックアップ作成**: オプション指定時のバックアップ実行
6. **フォーマット変換**: プラットフォーム別のコンテンツ変換
7. **結果構築**: 統合結果の構築・返却

**公開準備ステータス判定**
- `READY`: 全ての条件をクリア
- `NEEDS_REVIEW`: 執筆中ステータス
- `NEEDS_IMPROVEMENT`: 下書き状態、品質基準未達
- `ERROR`: システムエラー

**例外処理**
- プロジェクト不存在：`ValueError`
- エピソード不存在：`ValueError`
- ファイルアクセスエラー：適切なエラーメッセージ

## プライベートメソッド

### _format_content()

**シグネチャ**
```python
def _format_content(self, content: str, format_type: PublishFormat) -> str:
```

**目的**
指定されたプラットフォーム形式にコンテンツを変換する。

**引数**
- `content`: 元のコンテンツ
- `format_type`: 対象フォーマット

**戻り値**
- `str`: フォーマット済みコンテンツ

### _format_for_narou()

**シグネチャ**
```python
def _format_for_narou(self, content: str) -> str:
```

**目的**
小説家になろう形式にコンテンツを変換する。

**変換処理**
- **Markdownヘッダー除去**: `#+`で始まるヘッダーを削除
- **空行調整**: 3行以上の連続空行を2行に統一
- **前後空白除去**: コンテンツの前後の不要な空白を削除

### _format_for_kakuyomu()

**シグネチャ**
```python
def _format_for_kakuyomu(self, content: str) -> str:
```

**目的**
カクヨム形式にコンテンツを変換する。

**現在の実装**
- プレースホルダー実装（将来拡張予定）

## 公開準備フロー

### 1. 基本確認
```python
# プロジェクト存在確認
project_dir = get_project_directory(project_name)

# エピソード取得
episode = get_episode(episode_number or latest)
```

### 2. 品質評価
```python
if include_quality_check:
    quality_score = episode.quality_score
    if quality_score < quality_threshold:
        status = NEEDS_IMPROVEMENT
```

### 3. ステータス判定
```python
if episode.status in [DRAFT, UNWRITTEN]:
    status = NEEDS_IMPROVEMENT
elif episode.status == IN_PROGRESS:
    status = NEEDS_REVIEW
```

### 4. バックアップ作成
```python
if create_backup:
    backup_request = BackupRequest(
        project_name=project_name,
        backup_type=EPISODE,
        episode_number=episode_number
    )
    backup_response = backup_use_case.execute(backup_request)
```

### 5. フォーマット変換
```python
formatted_content = format_content(episode.content, format_type)
```

## 依存関係

### アプリケーション層
- `BackupUseCase`: バックアップユースケース

### ドメイン層
- `Episode`: エピソードエンティティ
- `EpisodeStatus`: エピソードステータス値オブジェクト
- `EpisodeNumber`: エピソード番号値オブジェクト

### リポジトリ
- `ProjectRepository`: プロジェクトリポジトリ
- `EpisodeRepository`: エピソードリポジトリ

## 設計原則遵守

### DDD準拠
- ✅ エンティティ（`Episode`）の適切な使用
- ✅ 値オブジェクト（`EpisodeStatus`, `EpisodeNumber`）の活用
- ✅ リポジトリパターンによるデータアクセス抽象化
- ✅ アプリケーションサービス間の適切な調整

### TDD準拠
- ✅ 明確な責務分離
- ✅ 包括的なエラーハンドリング
- ✅ 型安全な実装
- ✅ 列挙型による型安全性

## 使用例

```python
# 依存関係の準備
project_repo = YamlProjectRepository()
episode_repo = YamlEpisodeRepository()
backup_use_case = BackupUseCase(project_repo, episode_repo)

# ユースケース作成
use_case = PublishPreparationUseCase(
    project_repository=project_repo,
    episode_repository=episode_repo,
    backup_use_case=backup_use_case
)

# 最新エピソードの公開準備（なろう形式）
request = PublishPreparationRequest(
    project_name="sample_novel",
    format_type=PublishFormat.NAROU,
    include_quality_check=True,
    create_backup=True,
    quality_threshold=75.0
)

response = use_case.execute(request)

# 結果の確認
print(f"公開準備ステータス: {response.status.value}")
print(f"品質スコア: {response.quality_score}")
print(f"メッセージ: {response.message}")

# 実行ステップの確認
for step in response.preparation_steps:
    print(f"- {step.name}: {step.status} ({step.message})")

# 公開可能な場合
if response.status == PublishStatus.READY:
    # フォーマット済みコンテンツを保存
    output_file = Path(f"publish_{response.format_type.value}.txt")
    output_file.write_text(response.formatted_content, encoding="utf-8")
    print(f"公開用ファイル: {output_file}")

    if response.backup_path:
        print(f"バックアップ: {response.backup_path}")

# 改善が必要な場合
elif response.status == PublishStatus.NEEDS_IMPROVEMENT:
    print("改善が必要な項目:")
    for step in response.preparation_steps:
        if step.status != "completed":
            print(f"- {step.message}")

# 指定エピソードの公開準備（カクヨム形式）
specific_request = PublishPreparationRequest(
    project_name="sample_novel",
    episode_number=10,
    format_type=PublishFormat.KAKUYOMU,
    quality_threshold=80.0
)

specific_response = use_case.execute(specific_request)
```

## プラットフォーム別設定

### 小説家になろう (NAROU)
- Markdownヘッダーの除去
- 空行の最適化
- プレーンテキスト化

### カクヨム (KAKUYOMU)
- 将来の拡張ポイント
- プラットフォーム固有の要件に対応

### プレーンテキスト (PLAIN)
- 最小限の変換
- 元のコンテンツをほぼそのまま使用

## エラーハンドリング

### プロジェクトエラー
- プロジェクト不存在
- ディレクトリアクセス権限エラー

### エピソードエラー
- エピソード不存在
- ファイル読み込みエラー

### バックアップエラー
- バックアップ作成失敗（処理は継続）

### フォーマットエラー
- 変換処理の失敗

## テスト観点

### 単体テスト
- 正常な公開準備フロー
- 各ステータス判定の正確性
- フォーマット変換の動作
- エラー条件での処理
- 品質基準の判定

### 統合テスト
- 実際のプロジェクトでの公開準備
- バックアップユースケースとの連携
- リポジトリとの協調動作

## 品質基準

- **判定精度**: 公開可否の正確な判定
- **変換品質**: プラットフォーム形式への適切な変換
- **安全性**: バックアップによるデータ保護
- **使いやすさ**: 明確なステップ表示とメッセージ
- **拡張性**: 新しいプラットフォームへの対応
