# 拡張エピソード完了ユースケース仕様書

## 概要
`EnhancedCompleteEpisodeUseCase`は、プロットバージョン管理を統合したエピソード完了処理を提供するユースケースです。Git変更検出、自動バージョニング、ユーザー確認を含む包括的なワークフローを実装し、プロットと原稿の一貫性を保証します。

## クラス設計

### EnhancedCompleteEpisodeUseCase

**責務**
- プロットバージョン管理統合
- Git変更の自動検出
- プロットバージョン提案の生成
- ユーザー確認によるバージョン作成
- 原稿とプロットの紐付け管理

## データ構造

### EnhancedCompleteResult (DataClass)
```python
@dataclass(frozen=True)
class EnhancedCompleteResult:
    success: bool                           # 処理成功フラグ
    episode_number: str                     # エピソード番号
    linked_version: str                     # 紐付けされたバージョン
    created_new_version: bool = False       # 新バージョン作成フラグ
    version_change_reason: str | None = None # バージョン変更理由
    message: str | None = None              # 結果メッセージ
    error_message: str | None = None        # エラーメッセージ
```

## パブリックメソッド

### execute()

**シグネチャ**
```python
def execute(
    self,
    episode_number: str,
    user_input_handler: Callable[[str], str] | None = None,
) -> EnhancedCompleteResult:
```

**目的**
エピソード完了時にプロットバージョン管理を統合した処理を実行し、適切なバージョンとの紐付けを行う。

**引数**
- `episode_number`: エピソード番号
- `user_input_handler`: ユーザー入力処理関数（テスト用）

**戻り値**
- `EnhancedCompleteResult`: 拡張完了処理結果

**処理フロー**
1. **現在プロットバージョン取得**: アクティブなプロットバージョンの確認
2. **Git変更検出**: 変更されたファイルの取得
3. **バージョン提案**: 自動バージョニングサービスによる提案生成
4. **分岐処理**:
   - **変更なし**: 現在バージョンに自動紐付け
   - **変更あり**: ユーザー確認による新バージョン作成
5. **紐付け作成**: `ManuscriptPlotLink`の作成・保存
6. **結果返却**: 処理結果の構築

**成功パターン**
- プロット変更なし → 現在バージョンに自動紐付け
- プロット変更あり + ユーザー承認 → 新バージョン作成・紐付け
- プロット変更あり + ユーザー拒否 → 現在バージョンに警告付き紐付け

**エラーパターン**
- プロットバージョン未初期化
- 新バージョン作成失敗
- Git操作エラー

## プライベートメソッド

### _auto_link_to_current()

**シグネチャ**
```python
def _auto_link_to_current(self, episode_number: str, current_version: PlotVersion) -> EnhancedCompleteResult:
```

**目的**
プロット変更がない場合に現在のバージョンに自動的に紐付けを行う。

**処理内容**
- `ManuscriptPlotLink`の作成
- 実装日時とGitコミット情報の設定
- リポジトリへの保存

### _handle_plot_changes()

**シグネチャ**
```python
def _handle_plot_changes(
    self,
    episode_number: str,
    current_version: PlotVersion,
    version_suggestion,
    user_input_handler: Callable[[str], str] | None,
) -> EnhancedCompleteResult:
```

**目的**
プロット変更が検出された場合のユーザー確認と処理分岐を管理する。

**処理内容**
1. **変更内容の表示**: 変更ファイル、推奨バージョン、変更理由
2. **ユーザー確認**: 新バージョン作成の承認取得
3. **処理分岐**: 承認・拒否に応じた適切な処理実行

**確認プロンプト例**
```
⚠️  プロットファイルが変更されています
第3章の構成を大幅に変更

推奨バージョン: v1.3.0
変更ファイル: 20_プロット/第3章.yaml, 20_プロット/全体構成.yaml

新しいプロットバージョンを作成しますか？ [Y/n]:
```

### _create_new_version_and_link()

**シグネチャ**
```python
def _create_new_version_and_link(
    self,
    episode_number: str,
    version_suggestion,
    user_input_handler: Callable[[str], str],
) -> EnhancedCompleteResult:
```

**目的**
ユーザー承認に基づいて新しいプロットバージョンを作成し、エピソードとの紐付けを行う。

**処理内容**
1. **バージョン番号確認**: デフォルト値の確認・カスタマイズ
2. **変更内容入力**: 変更内容の詳細記録
3. **新バージョン作成**: `CreatePlotVersionUseCase`の実行
4. **紐付け作成**: 新バージョンとエピソードの関連付け

### _auto_link_to_current_with_warning()

**シグネチャ**
```python
def _auto_link_to_current_with_warning(
    self,
    episode_number: str,
    current_version: PlotVersion,
    warning: str,
) -> EnhancedCompleteResult:
```

**目的**
プロット変更があるがユーザーが新バージョン作成を拒否した場合の警告付き紐付けを行う。

## Git統合機能

### 変更検出
```python
# Git変更ファイルの取得
changed_files = git_service.get_changed_files()

# プロット関連ファイルのフィルタリング
plot_changes = filter_plot_files(changed_files)
```

### バージョン提案
```python
# 自動バージョニングサービス
version_suggestion = auto_versioning.suggest_version_update(
    current_version=current_version.version_number,
    changed_files=changed_files,
    description="エピソード完了時の変更",
)
```

### コミット情報記録
```python
# 紐付け時のGitコミット記録
link = ManuscriptPlotLink(
    episode_number=episode_number,
    plot_version=version,
    implementation_date=datetime.now(),
    git_commit=git_service.get_current_commit(),
)
```

## 依存関係

### アプリケーション層
- `CreatePlotVersionUseCase`: プロットバージョン作成ユースケース

### ドメイン層
- `PlotVersion`: プロットバージョンエンティティ
- `ManuscriptPlotLink`: 原稿プロット紐付けエンティティ
- `AutoVersioningService`: 自動バージョニングサービス

### リポジトリ
- `PlotVersionRepository`: プロットバージョンリポジトリ
- `ManuscriptPlotLinkRepository`: 紐付けリポジトリ

### インフラ層
- `GitService`: Git操作サービス

## 設計原則遵守

### DDD準拠
- ✅ エンティティ（`PlotVersion`, `ManuscriptPlotLink`）の適切な使用
- ✅ ドメインサービス（`AutoVersioningService`）の活用
- ✅ リポジトリパターンによるデータアクセス抽象化
- ✅ ユースケース間の適切な連携

### TDD準拠
- ✅ 明確な責務分離
- ✅ テスタブルな設計（依存性注入）
- ✅ 型安全な実装
- ✅ 不変オブジェクトの使用

## 使用例

```python
# 依存関係の準備
plot_repo = YamlPlotVersionRepository()
link_repo = YamlManuscriptPlotLinkRepository()
git_service = GitService()

# ユースケース作成
use_case = EnhancedCompleteEpisodeUseCase(
    plot_repository=plot_repo,
    link_repository=link_repo,
    git_service=git_service
)

# 基本的なエピソード完了処理
result = use_case.execute(episode_number="005")

if result.success:
    print(f"エピソード {result.episode_number} の処理完了")
    print(f"紐付けバージョン: {result.linked_version}")

    if result.created_new_version:
        print(f"新バージョンを作成しました")
        print(f"変更理由: {result.version_change_reason}")
    else:
        print("既存バージョンに紐付けました")

    print(f"メッセージ: {result.message}")
else:
    print(f"処理失敗: {result.error_message}")

# テスト用の入力ハンドラー
def test_input_handler(prompt: str) -> str:
    if "新しいプロットバージョンを作成しますか？" in prompt:
        return "y"
    elif "バージョン番号" in prompt:
        return "v2.1.0"
    elif "変更内容を入力してください" in prompt:
        return "キャラクター設定の詳細化"
    return ""

# テスト実行
test_result = use_case.execute(
    episode_number="006",
    user_input_handler=test_input_handler
)
```

## ワークフロー例

### シナリオ1: プロット変更なし
```
1. エピソード006完了処理開始
2. Git変更検出 → プロット関連ファイル変更なし
3. 現在バージョン（v1.2.0）に自動紐付け
4. 結果: "第006話をv1.2.0に紐付けました"
```

### シナリオ2: プロット変更あり（承認）
```
1. エピソード007完了処理開始
2. Git変更検出 → 第4章.yaml が変更
3. バージョン提案生成 → v1.3.0 推奨
4. ユーザー確認 → 新バージョン作成に同意
5. 新バージョンv1.3.0作成
6. 第007話をv1.3.0に紐付け
7. 結果: "新バージョンv1.3.0を作成し、第007話を紐付けました"
```

### シナリオ3: プロット変更あり（拒否）
```
1. エピソード008完了処理開始
2. Git変更検出 → 全体構成.yaml が変更
3. バージョン提案生成 → v1.4.0 推奨
4. ユーザー確認 → 新バージョン作成を拒否
5. 現在バージョン（v1.3.0）に警告付き紐付け
6. 結果: "第008話をv1.3.0に紐付けました（ユーザーが新バージョン作成を拒否しました）"
```

## エラーハンドリング

### プロットバージョン未初期化
```python
if not current_version:
    return EnhancedCompleteResult(
        success=False,
        error_message="プロットバージョンが初期化されていません"
    )
```

### 新バージョン作成失敗
```python
if not create_result.success:
    return EnhancedCompleteResult(
        success=False,
        error_message=f"新バージョン作成に失敗: {create_result.error_message}"
    )
```

### Git操作エラー
- Git変更取得の失敗
- コミット情報取得の失敗

## テスト観点

### 単体テスト
- プロット変更なし時の自動紐付け
- プロット変更あり時のユーザー確認フロー
- 新バージョン作成と紐付け
- 各種エラー条件での動作
- テスト用入力ハンドラーの動作

### 統合テスト
- Git変更検出との連携
- プロットバージョンリポジトリとの協調
- 実際のユーザー入力での動作

## 品質基準

- **一貫性**: プロットと原稿の確実な紐付け
- **トレーサビリティ**: バージョン変更の追跡可能性
- **ユーザビリティ**: 分かりやすい確認プロンプト
- **自動化**: 変更なし時の自動処理
- **柔軟性**: ユーザー判断による処理分岐
