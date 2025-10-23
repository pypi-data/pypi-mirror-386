# SPEC-GENERAL-011: 伏線設計ユースケース仕様書

## 概要
`ForeshadowingDesignUseCase`は、プロット情報から伏線を抽出・設計し、伏線管理ファイルを作成・更新するユースケースです。全体構成および章別プロットから自動抽出、手動テンプレート作成、既存データとの統合機能を提供します。

## クラス設計

### ForeshadowingDesignUseCase

**責務**
- プロット情報からの伏線自動抽出
- 伏線管理ファイルの作成・更新
- 既存伏線データとの統合管理
- 手動編集用テンプレートの生成
- 伏線IDの重複回避と採番管理

## データ構造

### ForeshadowingDesignStatus (Enum)
```python
class ForeshadowingDesignStatus(Enum):
    SUCCESS = "success"                              # 成功
    PROJECT_NOT_FOUND = "project_not_found"          # プロジェクト不存在
    MASTER_PLOT_NOT_FOUND = "master_plot_not_found"  # 全体構成不存在
    CHAPTER_PLOT_NOT_FOUND = "chapter_plot_not_found" # 章別プロット不存在
    FORESHADOWING_FILE_NOT_FOUND = "foreshadowing_file_not_found" # 伏線ファイル不存在
    ERROR = "error"                                  # システムエラー
```

### ForeshadowingDesignRequest (DataClass)
```python
@dataclass
class ForeshadowingDesignRequest:
    project_name: str                    # プロジェクト名
    source: str = "master_plot"          # 抽出ソース（master_plot/chapter_plot/manual）
    auto_extract: bool = True            # 自動抽出フラグ
    interactive: bool = False            # 対話モードフラグ
    merge_existing: bool = True          # 既存データマージフラグ
    detailed_mode: bool = False          # 細かな伏線モード（章別プロット用）
```

### ForeshadowingDesignResponse (DataClass)
```python
@dataclass
class ForeshadowingDesignResponse:
    status: ForeshadowingDesignStatus    # 実行ステータス
    message: str                         # 結果メッセージ
    created_count: int = 0               # 新規作成数
    existing_count: int = 0              # 既存伏線数
    foreshadowing_file: Path | None = None # 伏線ファイルパス
    foreshadowing_summary: str = ""      # 伏線サマリー
```

## パブリックメソッド

### execute()

**シグネチャ**
```python
def execute(self, request: ForeshadowingDesignRequest) -> ForeshadowingDesignResponse:
```

**目的**
リクエスト設定に基づいて伏線設計処理を実行する。

**引数**
- `request`: 伏線設計リクエスト

**戻り値**
- `ForeshadowingDesignResponse`: 伏線設計結果

**処理フロー**
1. **プロジェクト確認**: プロジェクトの存在確認
2. **処理モード分岐**:
   - **手動モード**: テンプレート作成
   - **細かな伏線モード**: 章別プロットから抽出
   - **主要伏線モード**: 全体構成から抽出
3. **既存データ統合**: 必要に応じた既存伏線との統合
4. **結果保存**: 伏線管理ファイルの更新
5. **サマリー生成**: 処理結果の要約

## 処理モード詳細

### 主要伏線モード（デフォルト）
**対象**: 全体構成.yaml
**用途**: 物語の主要な伏線の設計
**処理**: `_extract_and_save_foreshadowings()`

### 細かな伏線モード
**対象**: 章別プロット（複数ファイル）
**用途**: 各章の詳細な伏線の追加
**処理**: `_extract_detailed_foreshadowings()`

### 手動モード
**対象**: テンプレートファイル
**用途**: 手動での伏線設計
**処理**: `_create_manual_template()`

## プライベートメソッド

### _extract_and_save_foreshadowings()

**シグネチャ**
```python
def _extract_and_save_foreshadowings(
    self,
    request: ForeshadowingDesignRequest,
    project_root: Path,
    foreshadowing_file: Path
) -> ForeshadowingDesignResponse:
```

**目的**
全体構成から主要伏線を抽出し、既存データと統合して保存する。

**処理内容**
1. 全体構成.yamlの読み込み
2. `ForeshadowingExtractor`による伏線抽出
3. 既存伏線との統合（merge_existing=Trueの場合）
4. 伏線管理ファイルの保存
5. サマリー生成

### _extract_detailed_foreshadowings()

**シグネチャ**
```python
def _extract_detailed_foreshadowings(
    self,
    request: ForeshadowingDesignRequest,
    project_root: Path,
    foreshadowing_file: Path
) -> ForeshadowingDesignResponse:
```

**目的**
章別プロットから細かな伏線を抽出し、既存の主要伏線に追加する。

**処理内容**
1. 主要伏線ファイルの存在確認
2. 章別プロットファイルの取得
3. 各章からの詳細伏線抽出
4. 既存伏線との統合
5. ファイル更新とサマリー生成

### _create_manual_template()

**シグネチャ**
```python
def _create_manual_template(
    self,
    project_root: Path,
    foreshadowing_file: Path
) -> ForeshadowingDesignResponse:
```

**目的**
手動編集用の伏線管理テンプレートを作成する。

### _merge_foreshadowings()

**シグネチャ**
```python
def _merge_foreshadowings(
    self,
    existing: list[Foreshadowing],
    new: list[Foreshadowing]
) -> list[Foreshadowing]:
```

**目的**
既存の伏線と新規の伏線を統合し、ID重複を回避する。

**処理内容**
1. 既存IDセットの作成
2. 新規伏線のID重複チェック
3. 重複時の新ID自動割り当て
4. 統合リストの生成

**ID採番ルール**
- 形式: `F001`, `F002`, `F003`...
- 重複時: 既存の最大番号+1で新ID生成

### _get_max_id_number()

**シグネチャ**
```python
def _get_max_id_number(self, foreshadowings: list[Foreshadowing]) -> int:
```

**目的**
伏線リストから最大のID番号を取得し、新ID生成のベースとする。

### _create_summary()

**シグネチャ**
```python
def _create_summary(self, foreshadowings: list[Foreshadowing]) -> str:
```

**目的**
抽出・作成された伏線の要約情報を生成する。

## 依存関係

### ドメイン層
- `Foreshadowing`: 伏線エンティティ
- `ForeshadowingId`: 伏線ID値オブジェクト
- `ForeshadowingExtractor`: 伏線抽出ドメインサービス

### リポジトリ
- `ProjectRepository`: プロジェクトリポジトリ
- `ForeshadowingRepository`: 伏線リポジトリ
- `PlotRepository`: プロットリポジトリ

## 設計原則遵守

### DDD準拠
- ✅ エンティティ（`Foreshadowing`）の適切な使用
- ✅ 値オブジェクト（`ForeshadowingId`）の活用
- ✅ ドメインサービス（`ForeshadowingExtractor`）の活用
- ✅ リポジトリパターンによるデータアクセス抽象化

### TDD準拠
- ✅ 明確な責務分離
- ✅ 包括的なエラーハンドリング
- ✅ 型安全な実装
- ✅ 列挙型による状態管理

## 使用例

```python
# 依存関係の準備
project_repo = YamlProjectRepository()
foreshadowing_repo = YamlForeshadowingRepository()
plot_repo = YamlPlotRepository()
foreshadowing_extractor = ForeshadowingExtractor()

# ユースケース作成
use_case = ForeshadowingDesignUseCase(
    project_repository=project_repo,
    foreshadowing_repository=foreshadowing_repo,
    plot_repository=plot_repo,
    foreshadowing_extractor=foreshadowing_extractor
)

# 主要伏線の自動抽出（デフォルト）
request = ForeshadowingDesignRequest(
    project_name="fantasy_adventure",
    source="master_plot",
    auto_extract=True,
    merge_existing=True
)

response = use_case.execute(request)

if response.status == ForeshadowingDesignStatus.SUCCESS:
    print(f"伏線設計完了: {response.message}")
    print(f"新規作成: {response.created_count}件")
    print(f"既存伏線: {response.existing_count}件")
    print(f"ファイル: {response.foreshadowing_file}")
    print(f"サマリー:\n{response.foreshadowing_summary}")
else:
    print(f"伏線設計失敗: {response.message}")

# 章別プロットからの細かな伏線追加
detailed_request = ForeshadowingDesignRequest(
    project_name="fantasy_adventure",
    source="chapter_plot",
    detailed_mode=True,
    merge_existing=True
)

detailed_response = use_case.execute(detailed_request)

# 手動編集用テンプレート作成
manual_request = ForeshadowingDesignRequest(
    project_name="new_project",
    source="manual",
    auto_extract=False
)

manual_response = use_case.execute(manual_request)

# 既存データを上書きする場合
overwrite_request = ForeshadowingDesignRequest(
    project_name="fantasy_adventure",
    merge_existing=False  # 既存データを上書き
)

overwrite_response = use_case.execute(overwrite_request)
```

## 伏線抽出例

### 全体構成からの主要伏線抽出
```yaml
# 入力: 20_プロット/全体構成.yaml
plot_points:
  - title: "魔法の剣の発見"
    foreshadowing: "古代魔法の封印が解かれる予兆"
  - title: "謎の老人の登場"
    foreshadowing: "実は伝説の魔法使いの生き残り"

# 出力: 50_管理資料/伏線管理.yaml
foreshadowings:
  - id: F001
    title: "古代魔法の封印解除"
    category: "世界設定"
    importance: "高"
    planting:
      episodes: [1, 3]
    resolution:
      episodes: [25]
  - id: F002
    title: "老人の正体"
    category: "キャラクター"
    importance: "中"
    planting:
      episodes: [2]
    resolution:
      episodes: [15]
```

### 章別プロットからの細かな伏線追加
```yaml
# 入力: 20_プロット/章別プロット/第1章.yaml
detailed_scenes:
  - scene: "酒場での会話"
    hints:
      - "バーテンダーが特定の名前に反応する"
      - "壁の絵画に隠された暗号"

# 追加出力:
  - id: F003
    title: "バーテンダーの秘密"
    category: "人物関係"
    importance: "低"
    planting:
      episodes: [4]
    hints: ["特定の名前への反応"]
```

## エラーハンドリング

### プロジェクト関連エラー
```python
if not self.project_repository.exists(request.project_name):
    return ForeshadowingDesignResponse(
        status=ForeshadowingDesignStatus.PROJECT_NOT_FOUND,
        message=f"プロジェクト '{request.project_name}' が見つかりません"
    )
```

### プロット関連エラー
```python
try:
    master_plot_data = self.plot_repository.load_master_plot(project_root)
except FileNotFoundError:
    return ForeshadowingDesignResponse(
        status=ForeshadowingDesignStatus.MASTER_PLOT_NOT_FOUND,
        message="全体構成.yamlが見つかりません。先に 'novel plot master' を実行してください。"
    )
```

### システムエラー
```python
except Exception as e:
    return ForeshadowingDesignResponse(
        status=ForeshadowingDesignStatus.ERROR,
        message=f"伏線設計中にエラーが発生しました: {str(e)}"
    )
```

## ワークフロー例

### 1. 新規プロジェクトでの伏線設計
```bash
# 1. 全体構成作成
novel plot master

# 2. 主要伏線の自動抽出
novel foreshadowing design --source master_plot

# 3. 章別プロット作成
novel plot chapter 1
novel plot chapter 2

# 4. 細かな伏線の追加
novel foreshadowing design --detailed
```

### 2. 既存プロジェクトでの伏線追加
```bash
# 既存伏線を保持して新規抽出
novel foreshadowing design --merge

# 上書きして再抽出
novel foreshadowing design --no-merge
```

## 統合機能

### ID重複回避
- 既存伏線ID: F001, F002, F005
- 新規伏線ID候補: F001（重複）
- 自動割り当て: F006（最大番号+1）

### データマージ
- 既存伏線は保持
- 新規伏線は適切なIDで追加
- 重複チェックによる安全な統合

## テスト観点

### 単体テスト
- 各処理モードの正常動作
- ID重複回避メカニズム
- 既存データとの統合
- エラー条件での動作
- サマリー生成の正確性

### 統合テスト
- 実際のプロットファイルでの伏線抽出
- リポジトリとの協調動作
- 複数章での細かな伏線抽出

## 品質基準

- **自動化**: プロットからの効率的な伏線抽出
- **一意性**: ID重複の確実な回避
- **統合性**: 既存データとの適切な統合
- **柔軟性**: 複数の抽出モードとソース対応
- **追跡可能性**: 明確なサマリーと処理履歴
