# SPEC-GENERAL-036: シーン管理ユースケース仕様書

## 概要
`SceneManagementUseCase`は、物語の重要シーンを管理するユースケースです。シーンの初期化、追加、一覧取得、詳細表示、チェックリスト生成、データ検証などの包括的なシーン管理機能を提供します。

## クラス設計

### SceneManagementUseCase

**責務**
- シーン管理ファイルの初期化
- 新規シーンの追加・重複チェック
- シーン一覧の取得・カテゴリ別集計
- シーン詳細情報の表示
- 進捗チェックリストの生成
- シーンデータの整合性検証

## データ構造

### SceneCategory (Enum)
```python
class SceneCategory(Enum):
    OPENING = "opening"              # 冒頭
    TURNING_POINT = "turning_point"  # 転換点
    CLIMAX = "climax"                # クライマックス
    EMOTIONAL = "emotional"          # 感動シーン
    ACTION = "action"                # アクションシーン
    MYSTERY = "mystery"              # 謎・伏線
    ENDING = "ending"                # エンディング
    FORESHADOWING = "foreshadowing"  # 伏線
    NORMAL = "normal"                # 通常シーン
```

### SceneInfo (DataClass)
```python
@dataclass
class SceneInfo:
    scene_id: str                           # シーンID
    category: SceneCategory                 # シーンカテゴリ
    title: str                              # シーンタイトル
    description: str                        # シーン説明
    episodes: list[int] = []                # 関連エピソード番号
    sensory_details: dict[str, str] = {}    # 五感描写詳細
    emotional_arc: str | None = None        # 感情の弧
    key_dialogues: list[str] = []           # 重要な台詞
    completion_status: str | None = None    # 完了ステータス
```

### ValidationIssue (DataClass)
```python
@dataclass
class ValidationIssue:
    severity: str                   # 重要度（error/warning/info）
    category: str                   # 問題カテゴリ
    scene_id: str | None = None     # 対象シーンID
    message: str = ""               # 問題メッセージ
```

## パブリックメソッド

### initialize_scenes()

**シグネチャ**
```python
def initialize_scenes(self, request: SceneInitRequest) -> SceneInitResponse:
```

**目的**
プロジェクトにシーン管理ファイルを初期化する。

**引数**
- `request.project_name`: プロジェクト名
- `request.project_directory`: プロジェクトディレクトリパス

**戻り値**
```python
SceneInitResponse:
    success: bool                   # 初期化成功フラグ
    scene_file_path: Path | None    # 作成されたシーンファイルパス
    message: str                    # 結果メッセージ
```

**処理内容**
1. シーン管理ファイルの初期化
2. ファイルパスの取得
3. 結果レスポンスの構築

### add_scene()

**シグネチャ**
```python
def add_scene(self, request: SceneAddRequest) -> SceneAddResponse:
```

**目的**
新しいシーンを重要シーン管理ファイルに追加する。

**引数**
```python
SceneAddRequest:
    project_name: str               # プロジェクト名
    project_directory: str          # プロジェクトディレクトリ
    category: SceneCategory         # シーンカテゴリ
    scene_id: str                   # シーンID
    title: str                      # シーンタイトル
    description: str                # シーン説明
    episodes: list[int] = []        # 関連エピソード
    sensory_details: dict[str, str] = {} # 五感描写
```

**戻り値**
```python
SceneAddResponse:
    success: bool                   # 追加成功フラグ
    scene_id: str                   # シーンID
    category: SceneCategory         # シーンカテゴリ
    message: str                    # 結果メッセージ
```

**処理内容**
1. シーンID重複チェック
2. シーンデータの追加
3. 結果レスポンスの構築

### list_scenes()

**シグネチャ**
```python
def list_scenes(self, request: SceneListRequest) -> SceneListResponse:
```

**目的**
シーン一覧を取得し、カテゴリ別の統計情報を提供する。

**引数**
```python
SceneListRequest:
    project_name: str                       # プロジェクト名
    project_directory: str                  # プロジェクトディレクトリ
    category: SceneCategory | None = None   # フィルタ対象カテゴリ
```

**戻り値**
```python
SceneListResponse:
    success: bool                           # 取得成功フラグ
    scenes: list[SceneInfo] = []            # シーン一覧
    total_by_category: dict[SceneCategory, int] = {} # カテゴリ別集計
    message: str                            # 結果メッセージ
```

**処理内容**
1. シーン一覧の取得（カテゴリフィルタ適用）
2. カテゴリ別集計の計算
3. 結果レスポンスの構築

### show_scene()

**シグネチャ**
```python
def show_scene(self, request: SceneShowRequest) -> SceneShowResponse:
```

**目的**
指定されたシーンの詳細情報を取得する。

**引数**
```python
SceneShowRequest:
    project_name: str               # プロジェクト名
    project_directory: str          # プロジェクトディレクトリ
    category: SceneCategory         # シーンカテゴリ
    scene_id: str                   # シーンID
```

**戻り値**
```python
SceneShowResponse:
    success: bool                   # 取得成功フラグ
    scene: SceneInfo | None         # シーン詳細情報
    message: str                    # 結果メッセージ
```

### generate_checklist()

**シグネチャ**
```python
def generate_checklist(self, request: SceneChecklistRequest) -> SceneChecklistResponse:
```

**目的**
シーンの進捗チェックリストを生成する。

**引数**
```python
SceneChecklistRequest:
    project_name: str               # プロジェクト名
    project_directory: str          # プロジェクトディレクトリ
    output_format: str = "markdown" # 出力フォーマット
    output_path: str | None = None  # 出力ファイルパス
```

**戻り値**
```python
SceneChecklistResponse:
    success: bool                   # 生成成功フラグ
    checklist_content: str          # チェックリスト内容
    total_scenes: int               # 総シーン数
    completed_scenes: int           # 完了シーン数
    output_path: Path | None        # 出力ファイルパス
    message: str                    # 結果メッセージ
```

**生成内容例**
```markdown
# 重要シーンチェックリスト

## 進捗状況: 3/8 完了

## climax
- ✅ **最終決戦** (ID: final_battle)
  - 主人公と魔王の最終対決
  - エピソード: 25, 26

## emotional
- ⬜ **別れのシーン** (ID: farewell_scene)
  - 仲間との感動的な別れ
  - エピソード: 24
```

### validate_scenes()

**シグネチャ**
```python
def validate_scenes(self, request: SceneValidateRequest) -> SceneValidateResponse:
```

**目的**
シーンデータの整合性を検証し、問題点を報告する。

**引数**
```python
SceneValidateRequest:
    project_name: str               # プロジェクト名
    project_directory: str          # プロジェクトディレクトリ
```

**戻り値**
```python
SceneValidateResponse:
    is_valid: bool                  # 検証結果
    issues: list[ValidationIssue]   # 問題一覧
    error_count: int                # エラー数
    warning_count: int              # 警告数
    message: str                    # 結果メッセージ
```

**検証項目**
- シーンデータの形式チェック
- 必須フィールドの存在確認
- エピソード番号の妥当性
- 重複IDの検出
- カテゴリの妥当性

## 依存関係

### ドメイン層
- `SceneManagementRepository`: シーン管理リポジトリインターフェース

### インフラ層
- `ProjectRepository`: プロジェクトリポジトリ

## 設計原則遵守

### DDD準拠
- ✅ リポジトリパターンによるデータアクセス抽象化
- ✅ 値オブジェクト（`SceneCategory`）の適切な使用
- ✅ エンティティ（`SceneInfo`）の適切な管理

### TDD準拠
- ✅ 明確な責務分離
- ✅ 包括的なエラーハンドリング
- ✅ 型安全な実装
- ✅ 列挙型による型安全性

## 使用例

```python
# 依存関係の準備
scene_repo = YamlSceneManagementRepository()
project_repo = YamlProjectRepository()

# ユースケース作成
use_case = SceneManagementUseCase(
    scene_repository=scene_repo,
    project_repository=project_repo
)

# シーン管理ファイルの初期化
init_request = SceneInitRequest(
    project_name="fantasy_adventure",
    project_directory="/path/to/project"
)

init_response = use_case.initialize_scenes(init_request)
if init_response.success:
    print(f"初期化完了: {init_response.scene_file_path}")

# 新しいシーンの追加
add_request = SceneAddRequest(
    project_name="fantasy_adventure",
    project_directory="/path/to/project",
    category=SceneCategory.CLIMAX,
    scene_id="final_battle",
    title="最終決戦",
    description="主人公と魔王の最終対決",
    episodes=[25, 26],
    sensory_details={
        "視覚": "炎と雷が交錯する戦場",
        "聴覚": "魔法の衝突音と咆哮",
        "触覚": "熱風と振動"
    }
)

add_response = use_case.add_scene(add_request)
if add_response.success:
    print(f"シーン追加完了: {add_response.message}")

# シーン一覧の取得
list_request = SceneListRequest(
    project_name="fantasy_adventure",
    project_directory="/path/to/project",
    category=SceneCategory.CLIMAX  # クライマックスシーンのみ
)

list_response = use_case.list_scenes(list_request)
if list_response.success:
    print(f"シーン数: {len(list_response.scenes)}")
    for scene in list_response.scenes:
        print(f"- {scene.title} ({scene.scene_id})")

# シーン詳細の表示
show_request = SceneShowRequest(
    project_name="fantasy_adventure",
    project_directory="/path/to/project",
    category=SceneCategory.CLIMAX,
    scene_id="final_battle"
)

show_response = use_case.show_scene(show_request)
if show_response.success and show_response.scene:
    scene = show_response.scene
    print(f"タイトル: {scene.title}")
    print(f"説明: {scene.description}")
    print(f"エピソード: {scene.episodes}")

# チェックリストの生成
checklist_request = SceneChecklistRequest(
    project_name="fantasy_adventure",
    project_directory="/path/to/project",
    output_format="markdown",
    output_path="/path/to/checklist.md"
)

checklist_response = use_case.generate_checklist(checklist_request)
if checklist_response.success:
    print(f"進捗: {checklist_response.completed_scenes}/{checklist_response.total_scenes}")
    print(checklist_response.checklist_content)

# シーンデータの検証
validate_request = SceneValidateRequest(
    project_name="fantasy_adventure",
    project_directory="/path/to/project"
)

validate_response = use_case.validate_scenes(validate_request)
print(f"検証結果: {'有効' if validate_response.is_valid else '無効'}")
print(f"エラー: {validate_response.error_count}件")
print(f"警告: {validate_response.warning_count}件")

for issue in validate_response.issues:
    print(f"[{issue.severity}] {issue.message}")
```

## シーンカテゴリ活用例

### ストーリー構造別シーン設計
```python
# 三幕構成に基づくシーン設計
opening_scenes = [
    SceneInfo("hook", SceneCategory.OPENING, "冒頭の引き", "読者を引き込む最初のシーン"),
    SceneInfo("inciting_incident", SceneCategory.TURNING_POINT, "きっかけ", "物語の始まりとなる事件")
]

climax_scenes = [
    SceneInfo("midpoint", SceneCategory.TURNING_POINT, "中間点", "物語の転換点"),
    SceneInfo("climax", SceneCategory.CLIMAX, "クライマックス", "最大の山場"),
    SceneInfo("resolution", SceneCategory.ENDING, "解決", "物語の結末")
]
```

### ジャンル別シーン管理
```python
# ミステリー小説の場合
mystery_scenes = [
    SceneInfo("crime_discovery", SceneCategory.MYSTERY, "事件発覚", "謎の発見"),
    SceneInfo("red_herring", SceneCategory.FORESHADOWING, "偽の手がかり", "読者を惑わす情報"),
    SceneInfo("revelation", SceneCategory.CLIMAX, "真相暴露", "謎解きのシーン")
]
```

## エラーハンドリング

### シーン追加時の重複チェック
```python
if self.scene_repository.scene_exists(project_path, category, scene_id):
    return SceneAddResponse(
        success=False,
        message=f"シーンID '{scene_id}' は既に存在します"
    )
```

### シーン不存在時の処理
```python
if not scene:
    return SceneShowResponse(
        success=False,
        message=f"シーン '{scene_id}' が見つかりません"
    )
```

### 検証エラーの分類
```python
# エラーと警告の分類
error_count = sum(1 for issue in issues if issue.severity == "error")
warning_count = sum(1 for issue in issues if issue.severity == "warning")
```

## テスト観点

### 単体テスト
- シーン初期化の正常動作
- シーン追加と重複チェック
- カテゴリ別フィルタリング
- チェックリスト生成の正確性
- 検証機能の動作
- エラー条件での処理

### 統合テスト
- 実際のプロジェクトでのシーン管理
- リポジトリとの協調動作
- ファイル出力機能の確認

## 品質基準

- **一意性**: シーンIDの重複防止
- **分類性**: カテゴリ別の適切な管理
- **追跡性**: 進捗状況の明確な把握
- **検証性**: データ整合性の確保
- **視認性**: 分かりやすいチェックリスト生成
