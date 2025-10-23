# SPEC-GENERAL-104: 離脱率分析ユースケース仕様書

## 概要
`DropoutAnalysisUseCase`は、エピソードの読者離脱率を分析し、改善提案を提供するユースケースです。アクセス統計データの解析、離脱パターンの特定、具体的な改善案の生成、分析レポートの作成機能を提供します。

## クラス設計

### DropoutAnalysisUseCase

**責務**
- アクセス統計データの読み込みと検証
- エピソード別離脱率の計算
- 離脱パターンの分析と特定
- 改善提案の生成
- 分析レポートの作成と保存

## データ構造

### AnalysisTarget (Enum)
```python
class AnalysisTarget(Enum):
    ALL_EPISODES = "all_episodes"            # 全エピソード
    RECENT_EPISODES = "recent_episodes"      # 最近のエピソード
    SPECIFIC_RANGE = "specific_range"        # 指定範囲
    HIGH_DROPOUT = "high_dropout"            # 高離脱率エピソード
```

### DropoutAnalysisRequest (DataClass)
```python
@dataclass
class DropoutAnalysisRequest:
    project_name: str                        # プロジェクト名
    target: AnalysisTarget = AnalysisTarget.ALL_EPISODES  # 分析対象
    start_episode: int | None = None         # 開始エピソード番号
    end_episode: int | None = None           # 終了エピソード番号
    threshold_dropout_rate: float = 0.15    # 高離脱率の閾値
    include_suggestions: bool = True         # 改善提案を含める
    generate_report: bool = True             # レポート生成フラグ
    output_path: Path | None = None          # 出力パス
```

### DropoutAnalysisResponse (DataClass)
```python
@dataclass
class DropoutAnalysisResponse:
    success: bool                            # 分析成功フラグ
    message: str                             # 結果メッセージ
    analyzed_episodes_count: int = 0         # 分析対象エピソード数
    high_dropout_episodes: list[int] = []    # 高離脱率エピソード
    average_dropout_rate: float = 0.0        # 平均離脱率
    analysis_summary: str = ""               # 分析サマリー
    suggestions: list[str] = []              # 改善提案
    report_file_path: Path | None = None     # レポートファイルパス
```

### EpisodeDropoutData (DataClass)
```python
@dataclass
class EpisodeDropoutData:
    episode_number: int                      # エピソード番号
    title: str                               # エピソードタイトル
    view_count: int                          # 閲覧数
    previous_view_count: int                 # 前エピソード閲覧数
    dropout_rate: float                      # 離脱率
    word_count: int                          # 文字数
    publish_date: str | None = None          # 公開日
```

## パブリックメソッド

### execute()

**シグネチャ**
```python
def execute(self, request: DropoutAnalysisRequest) -> DropoutAnalysisResponse:
```

**目的**
指定されたプロジェクトの読者離脱率を分析し、改善提案を生成する。

**引数**
- `request`: 離脱率分析リクエスト

**戻り値**
- `DropoutAnalysisResponse`: 分析結果

**処理フロー**
1. **プロジェクト検証**: プロジェクトの存在確認
2. **データ読み込み**: アクセス統計とエピソード情報の取得
3. **離脱率計算**: エピソード別離脱率の算出
4. **パターン分析**: 離脱パターンの特定
5. **改善提案生成**: 具体的な改善案の作成
6. **レポート生成**: 分析結果のレポート作成
7. **結果統合**: レスポンスの構築

## プライベートメソッド

### _calculate_dropout_rates()

**シグネチャ**
```python
def _calculate_dropout_rates(
    self,
    access_data: dict,
    episodes_data: dict,
    target_episodes: list[int]
) -> list[EpisodeDropoutData]:
```

**目的**
各エピソードの離脱率を計算し、統計データを作成する。

**計算式**
```python
dropout_rate = (previous_view_count - current_view_count) / previous_view_count
```

### _analyze_dropout_patterns()

**シグネチャ**
```python
def _analyze_dropout_patterns(
    self,
    dropout_data: list[EpisodeDropoutData]
) -> dict[str, any]:
```

**目的**
離脱パターンを分析し、傾向を特定する。

**分析項目**
- 高離脱率エピソードの特徴
- 文字数との相関
- 公開間隔との関係
- 時系列トレンド

### _generate_improvement_suggestions()

**シグネチャ**
```python
def _generate_improvement_suggestions(
    self,
    patterns: dict[str, any],
    high_dropout_episodes: list[EpisodeDropoutData]
) -> list[str]:
```

**目的**
分析結果に基づいた具体的な改善提案を生成する。

**提案例**
- 「エピソード5の文字数が平均の2倍です。分割を検討してください」
- 「離脱率が高いエピソードは展開が遅い傾向があります」
- 「公開間隔が2週間を超えると離脱率が上昇します」

### _create_analysis_report()

**シグネチャ**
```python
def _create_analysis_report(
    self,
    dropout_data: list[EpisodeDropoutData],
    patterns: dict[str, any],
    suggestions: list[str]
) -> str:
```

**目的**
分析結果を整理したマークダウンレポートを生成する。

**レポート構成**
```markdown
# 離脱率分析レポート

## 分析サマリー
- 分析対象: X エピソード
- 平均離脱率: XX.X%
- 高離脱率エピソード: X件

## エピソード別詳細
| エピソード | タイトル | 離脱率 | 文字数 |
|-----------|----------|--------|--------|

## 改善提案
1. ...
2. ...

## 分析パターン
- ...
```

### _get_target_episodes()

**シグネチャ**
```python
def _get_target_episodes(
    self,
    request: DropoutAnalysisRequest,
    available_episodes: list[int]
) -> list[int]:
```

**目的**
分析対象エピソードを決定する。

**対象選択ロジック**
- `ALL_EPISODES`: 全エピソード
- `RECENT_EPISODES`: 最新10エピソード
- `SPECIFIC_RANGE`: 指定範囲
- `HIGH_DROPOUT`: 閾値を超えるエピソード

## 依存関係

### リポジトリ
- `ProjectRepository`: プロジェクト情報の取得
- `AccessAnalysisRepository`: アクセス統計データの取得
- `EpisodeRepository`: エピソード情報の取得

### ドメインサービス
- `DropoutAnalyzer`: 離脱率計算とパターン分析
- `ImprovementSuggestionService`: 改善提案の生成

## 設計原則遵守

### DDD準拠
- ✅ エンティティ（`EpisodeDropoutData`）の適切な使用
- ✅ ドメインサービス（`DropoutAnalyzer`）の活用
- ✅ リポジトリパターンによるデータアクセス抽象化

### TDD準拠
- ✅ 明確な責務分離
- ✅ 包括的なエラーハンドリング
- ✅ 型安全な実装
- ✅ 列挙型による型安全性

## 使用例

```python
# 依存関係の準備
project_repo = YamlProjectRepository()
access_repo = YamlAccessAnalysisRepository()
episode_repo = YamlEpisodeRepository()
dropout_analyzer = DropoutAnalyzer()
suggestion_service = ImprovementSuggestionService()

# ユースケース作成
use_case = DropoutAnalysisUseCase(
    project_repository=project_repo,
    access_repository=access_repo,
    episode_repository=episode_repo,
    dropout_analyzer=dropout_analyzer,
    suggestion_service=suggestion_service
)

# 全エピソードの離脱率分析
request = DropoutAnalysisRequest(
    project_name="fantasy_adventure",
    target=AnalysisTarget.ALL_EPISODES,
    threshold_dropout_rate=0.2,  # 20%以上を高離脱率とする
    include_suggestions=True,
    generate_report=True,
    output_path=Path("./analysis_report.md")
)

response = use_case.execute(request)

if response.success:
    print(f"分析完了: {response.message}")
    print(f"分析対象エピソード: {response.analyzed_episodes_count}件")
    print(f"平均離脱率: {response.average_dropout_rate:.1%}")
    print(f"高離脱率エピソード: {len(response.high_dropout_episodes)}件")

    print("\n=== 改善提案 ===")
    for i, suggestion in enumerate(response.suggestions, 1):
        print(f"{i}. {suggestion}")

    if response.report_file_path:
        print(f"\nレポート保存先: {response.report_file_path}")
else:
    print(f"分析失敗: {response.message}")

# 最近のエピソードのみ分析
recent_request = DropoutAnalysisRequest(
    project_name="fantasy_adventure",
    target=AnalysisTarget.RECENT_EPISODES,
    include_suggestions=True
)

recent_response = use_case.execute(recent_request)

# 指定範囲の分析
range_request = DropoutAnalysisRequest(
    project_name="fantasy_adventure",
    target=AnalysisTarget.SPECIFIC_RANGE,
    start_episode=10,
    end_episode=20,
    threshold_dropout_rate=0.15
)

range_response = use_case.execute(range_request)
```

## 分析パターン例

### 文字数との相関分析
```python
# 長すぎるエピソードの特定
long_episodes = [ep for ep in dropout_data if ep.word_count > 8000]
high_dropout_long = [ep for ep in long_episodes if ep.dropout_rate > 0.2]

if high_dropout_long:
    suggestions.append(
        f"文字数が{sum(ep.word_count for ep in high_dropout_long)/len(high_dropout_long):.0f}文字を超えるエピソードで離脱率が高い傾向があります。分割を検討してください。"
    )
```

### 時系列トレンド分析
```python
# 最近の離脱率上昇トレンド
recent_dropout_rates = [ep.dropout_rate for ep in recent_episodes]
if len(recent_dropout_rates) >= 3:
    trend = calculate_trend(recent_dropout_rates)
    if trend > 0.05:  # 5%以上の上昇トレンド
        suggestions.append(
            "最近のエピソードで離脱率の上昇トレンドが見られます。内容やペースを見直してください。"
        )
```

## エラーハンドリング

### データ不足エラー
```python
if not access_data or len(access_data) < 2:
    return DropoutAnalysisResponse(
        success=False,
        message="離脱率分析に必要な最小データが不足しています（最低2エピソード必要）"
    )
```

### プロジェクト不存在
```python
if not self.project_repository.exists(request.project_name):
    return DropoutAnalysisResponse(
        success=False,
        message=f"プロジェクト '{request.project_name}' が見つかりません"
    )
```

### 計算エラー
```python
try:
    dropout_rate = (prev_views - curr_views) / prev_views
except ZeroDivisionError:
    dropout_rate = 0.0  # 前エピソードが0の場合
except Exception as e:
    logger.warning(f"離脱率計算エラー (Episode {episode_num}): {e}")
    dropout_rate = 0.0
```

## テスト観点

### 単体テスト
- 離脱率計算の正確性
- 各分析対象の正しい選択
- パターン分析の動作
- 改善提案生成の妥当性
- エラー条件での処理

### 統合テスト
- 実際のアクセスデータでの分析
- レポート生成機能の確認
- リポジトリとの協調動作

## 品質基準

- **正確性**: 離脱率計算の数学的正確性
- **実用性**: 具体的で実行可能な改善提案
- **視認性**: 分かりやすい分析レポート
- **柔軟性**: 複数の分析対象への対応
- **信頼性**: エラー処理とデータ検証の徹底
