# 全体構成統合ユースケース仕様書

## 概要
`MasterPlotIntegrationUseCase`は、マスタープロットの作成と関連する伏線設計・重要シーン抽出を統合的に実行するユースケースです。プロット作成オーケストレータ、伏線設計、シーン抽出の各ユースケースを調整し、包括的な物語設計支援を提供します。

## クラス設計

### MasterPlotIntegrationUseCase

**責務**
- マスタープロット作成の統合管理
- 伏線設計ユースケースとの連携
- シーン抽出ユースケースとの連携
- 複数ステップの実行状況管理
- 部分的成功の適切な処理

## データ構造

### MasterPlotIntegrationStatus (Enum)
```python
class MasterPlotIntegrationStatus(Enum):
    SUCCESS = "success"                      # 全ステップ成功
    MASTER_PLOT_FAILED = "master_plot_failed"        # マスタープロット作成失敗
    FORESHADOWING_FAILED = "foreshadowing_failed"    # 伏線設計失敗
    SCENE_EXTRACTION_FAILED = "scene_extraction_failed"  # シーン抽出失敗
    PARTIAL_SUCCESS = "partial_success"      # 部分的成功
    ERROR = "error"                          # システムエラー
```

### MasterPlotIntegrationRequest (DataClass)
```python
@dataclass
class MasterPlotIntegrationRequest:
    project_name: str                        # プロジェクト名
    auto_foreshadowing: bool = True          # 自動伏線設計フラグ
    auto_scenes: bool = True                 # 自動シーン抽出フラグ
    merge_existing: bool = True              # 既存データマージフラグ
```

### MasterPlotIntegrationResponse (DataClass)
```python
@dataclass
class MasterPlotIntegrationResponse:
    status: MasterPlotIntegrationStatus      # 実行ステータス
    message: str                             # 結果メッセージ
    master_plot_created: bool = False        # マスタープロット作成フラグ
    foreshadowing_created: bool = False      # 伏線作成フラグ
    scenes_extracted: bool = False           # シーン抽出フラグ
    master_plot_file: Path | None = None     # マスタープロットファイルパス
    foreshadowing_file: Path | None = None   # 伏線ファイルパス
    scene_file: Path | None = None           # シーンファイルパス
    foreshadowing_count: int = 0             # 作成された伏線数
    scene_count: int = 0                     # 抽出されたシーン数
```

## パブリックメソッド

### execute()

**シグネチャ**
```python
def execute(self, request: MasterPlotIntegrationRequest) -> MasterPlotIntegrationResponse:
```

**目的**
マスタープロット作成から伏線設計・シーン抽出までの統合ワークフローを実行する。

**引数**
- `request`: 統合実行リクエスト

**戻り値**
- `MasterPlotIntegrationResponse`: 統合実行結果

**処理フロー**
1. **プロジェクト確認**: プロジェクトの存在確認
2. **マスタープロット作成**: `PlotCreationOrchestrator`によるプロット生成
3. **伏線設計**: オプション有効時の自動伏線設計
4. **シーン抽出**: オプション有効時の重要シーン抽出
5. **結果統合**: 各ステップの結果を統合したレスポンス構築

**成功パターン**
- **完全成功**: 全ステップが正常完了
- **部分的成功**: 一部ステップが失敗したが有用な結果を提供

**エラーパターン**
- **プロジェクト不存在**: 指定プロジェクトが見つからない
- **マスタープロット作成失敗**: 基盤となるプロット作成に失敗
- **システムエラー**: 予期しない例外の発生

## ワークフロー詳細

### ステップ1: マスタープロット作成
```python
plot_request = PlotCreationRequest(
    stage_type=WorkflowStageType.MASTER_PLOT,
    project_root=project_root,
    parameters={},
    auto_confirm=True
)

plot_response = self.plot_orchestrator.execute_plot_creation(plot_request)
```

**成功条件**: `plot_response.success == True`
**失敗時**: `MASTER_PLOT_FAILED`ステータスで終了

### ステップ2: 伏線設計（オプション）
```python
if request.auto_foreshadowing:
    foreshadowing_request = ForeshadowingDesignRequest(
        project_name=request.project_name,
        source="master_plot",
        auto_extract=True,
        interactive=False,
        merge_existing=request.merge_existing
    )

    foreshadowing_response = foreshadowing_use_case.execute(foreshadowing_request)
```

**成功条件**: `foreshadowing_response.status == ForeshadowingDesignStatus.SUCCESS`
**失敗時**: `PARTIAL_SUCCESS`ステータス（マスタープロットは保持）

### ステップ3: シーン抽出（オプション）
```python
if request.auto_scenes:
    scene_request = SceneExtractionRequest(
        project_name=request.project_name,
        use_master_plot=True,
        use_foreshadowing=foreshadowing_created,
        merge_existing=request.merge_existing,
        auto_categorize=True
    )

    scene_response = scene_use_case.execute(scene_request)
```

**成功条件**: `scene_response.status == SceneExtractionStatus.SUCCESS`
**失敗時**: `PARTIAL_SUCCESS`ステータス（前段階の結果は保持）

## 部分的成功の処理

### 伏線設計失敗時
- マスタープロットは作成済み
- 伏線ファイルは未作成
- シーン抽出は実行されない
- ステータス: `PARTIAL_SUCCESS`

### シーン抽出失敗時
- マスタープロット・伏線は作成済み
- シーンファイルは未作成
- ステータス: `PARTIAL_SUCCESS`

## 依存関係

### アプリケーション層
- `PlotCreationOrchestrator`: プロット作成統合管理
- `ForeshadowingDesignUseCase`: 伏線設計ユースケース
- `SceneExtractionUseCase`: シーン抽出ユースケース

### ドメイン層
- `WorkflowStageType`: ワークフロー段階値オブジェクト
- `SceneExtractor`: シーン抽出ドメインサービス
- `ForeshadowingExtractor`: 伏線抽出ドメインサービス

### リポジトリ
- `ProjectRepository`: プロジェクトリポジトリ
- `PlotRepository`: プロットリポジトリ
- `YamlForeshadowingRepository`: 伏線リポジトリ
- `YamlSceneManagementRepository`: シーン管理リポジトリ

## 設計原則遵守

### DDD準拠
- ✅ ドメインサービス（`SceneExtractor`, `ForeshadowingExtractor`）の活用
- ✅ 値オブジェクト（`WorkflowStageType`）の適切な使用
- ✅ リポジトリパターンによるデータアクセス抽象化
- ✅ アプリケーションサービス間の適切な調整

### TDD準拠
- ✅ 明確な責務分離
- ✅ 包括的な例外処理
- ✅ 型安全な実装
- ✅ 列挙型による状態管理

## 使用例

```python
# 依存関係の準備
project_repo = YamlProjectRepository()
plot_repo = YamlPlotRepository()
foreshadowing_repo = YamlForeshadowingRepository()
scene_repo = YamlSceneManagementRepository()
plot_orchestrator = PlotCreationOrchestrator(...)
scene_extractor = SceneExtractor()
foreshadowing_extractor = ForeshadowingExtractor()

# ユースケース作成
use_case = MasterPlotIntegrationUseCase(
    project_repository=project_repo,
    plot_repository=plot_repo,
    foreshadowing_repository=foreshadowing_repo,
    scene_repository=scene_repo,
    plot_orchestrator=plot_orchestrator,
    scene_extractor=scene_extractor,
    foreshadowing_extractor=foreshadowing_extractor
)

# 完全統合実行
request = MasterPlotIntegrationRequest(
    project_name="fantasy_adventure",
    auto_foreshadowing=True,
    auto_scenes=True,
    merge_existing=True
)

response = use_case.execute(request)

# 結果の確認
print(f"統合ステータス: {response.status.value}")
print(f"メッセージ: {response.message}")

if response.status == MasterPlotIntegrationStatus.SUCCESS:
    print("全ステップが正常に完了しました")
    print(f"マスタープロット: {response.master_plot_file}")

    if response.foreshadowing_created:
        print(f"伏線設計: {response.foreshadowing_count}個作成")
        print(f"伏線ファイル: {response.foreshadowing_file}")

    if response.scenes_extracted:
        print(f"シーン抽出: {response.scene_count}個抽出")
        print(f"シーンファイル: {response.scene_file}")

elif response.status == MasterPlotIntegrationStatus.PARTIAL_SUCCESS:
    print("部分的に成功しました")
    if response.master_plot_created:
        print(f"✓ マスタープロット作成完了: {response.master_plot_file}")
    if response.foreshadowing_created:
        print(f"✓ 伏線設計完了: {response.foreshadowing_count}個")
    else:
        print("✗ 伏線設計は実行されませんでした")
    if response.scenes_extracted:
        print(f"✓ シーン抽出完了: {response.scene_count}個")
    else:
        print("✗ シーン抽出は実行されませんでした")

else:
    print(f"実行失敗: {response.message}")

# 最小構成での実行（マスタープロットのみ）
minimal_request = MasterPlotIntegrationRequest(
    project_name="simple_story",
    auto_foreshadowing=False,
    auto_scenes=False
)

minimal_response = use_case.execute(minimal_request)
```

## 実行結果例

### 完全成功
```
統合ステータス: success
メッセージ: 全体構成を作成しました。15個の主要伏線を設計しました。8個の主要シーンを抽出しました
マスタープロット: /project/20_プロット/全体構成.yaml
伏線設計: 15個作成
伏線ファイル: /project/50_管理資料/伏線管理.yaml
シーン抽出: 8個抽出
シーンファイル: /project/50_管理資料/重要シーン.yaml
```

### 部分的成功（伏線設計失敗）
```
統合ステータス: partial_success
メッセージ: 全体構成は作成されましたが、伏線設計に失敗しました: プロット情報が不十分です
✓ マスタープロット作成完了: /project/20_プロット/全体構成.yaml
✗ 伏線設計は実行されませんでした
✗ シーン抽出は実行されませんでした
```

### マスタープロット作成失敗
```
統合ステータス: master_plot_failed
メッセージ: 全体構成作成に失敗しました: プロジェクト設定ファイルが見つかりません
```

## 設定オプション

### auto_foreshadowing
- `True`: マスタープロット作成後に伏線を自動設計
- `False`: 伏線設計をスキップ

### auto_scenes
- `True`: 重要シーンを自動抽出
- `False`: シーン抽出をスキップ

### merge_existing
- `True`: 既存の伏線・シーンデータとマージ
- `False`: 新規作成（既存データは上書き）

## エラーハンドリング

### プロジェクト関連エラー
```python
if not self.project_repository.exists(request.project_name):
    return MasterPlotIntegrationResponse(
        status=MasterPlotIntegrationStatus.ERROR,
        message=f"プロジェクト '{request.project_name}' が見つかりません"
    )
```

### 予期しないエラー
```python
except Exception as e:
    return MasterPlotIntegrationResponse(
        status=MasterPlotIntegrationStatus.ERROR,
        message=f"予期しないエラーが発生しました: {str(e)}"
    )
```

## テスト観点

### 単体テスト
- 正常な統合ワークフロー
- 各ステップでの失敗処理
- 部分的成功の適切な処理
- 設定オプションの動作
- エラー条件での処理

### 統合テスト
- 実際のプロジェクトでの統合実行
- 各ユースケースとの協調動作
- ファイル作成・保存の確認

## 品質基準

- **統合性**: 複数ユースケースの適切な調整
- **堅牢性**: 部分的失敗時の適切な処理
- **透明性**: 各ステップの実行状況の明確な報告
- **柔軟性**: オプション設定による実行内容の調整
- **効率性**: 依存関係を考慮した最適な実行順序
