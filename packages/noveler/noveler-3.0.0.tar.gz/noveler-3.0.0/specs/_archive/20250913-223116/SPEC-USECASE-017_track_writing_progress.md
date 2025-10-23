# 執筆進捗トラッキングユースケース仕様書

## 概要
`TrackWritingProgress`は、執筆進捗の追跡と分析を行うユースケースです。エピソード単位の執筆状態管理、文字数カウント、進捗率計算、目標達成度の監視、執筆リズムの分析、統計レポートの生成を包括的に提供し、継続的な執筆活動を支援します。

## クラス設計

### TrackWritingProgress

**責務**
- 執筆進捗のリアルタイム追跡
- エピソード別執筆状態管理
- 文字数と進捗率の自動計算
- 目標設定と達成度監視
- 執筆リズムとパフォーマンス分析
- 進捗レポートとダッシュボードの生成
- アラートとリマインダーの管理

## データ構造

### ProgressMetric (Enum)
```python
class ProgressMetric(Enum):
    WORD_COUNT = "word_count"            # 文字数
    EPISODE_COUNT = "episode_count"      # エピソード数
    COMPLETION_RATE = "completion_rate"  # 完成率
    DAILY_OUTPUT = "daily_output"        # 日別出力
    WRITING_STREAK = "writing_streak"    # 継続執筆日数
    QUALITY_SCORE = "quality_score"      # 品質スコア
```

### WritingGoal (DataClass)
```python
@dataclass
class WritingGoal:
    goal_type: ProgressMetric              # 目標タイプ
    target_value: float                    # 目標値
    current_value: float                   # 現在値
    deadline: date | None = None           # 期限
    achievement_rate: float = 0.0          # 達成率
    is_achieved: bool = False              # 達成フラグ
    created_at: datetime = None            # 作成日時
    description: str = ""                  # 目標説明
```

### ProgressTrackRequest (DataClass)
```python
@dataclass
class ProgressTrackRequest:
    project_name: str                      # プロジェクト名
    metrics: list[ProgressMetric] = []     # 追跡する指標（空=全て）
    period_start: date | None = None       # 期間開始日
    period_end: date | None = None         # 期間終了日
    include_goals: bool = True             # 目標達成状況を含める
    include_trends: bool = True            # トレンド分析を含める
    generate_dashboard: bool = True        # ダッシュボード生成
    alert_thresholds: dict[str, float] = {} # アラート闾値
```

### ProgressTrackResponse (DataClass)
```python
@dataclass
class ProgressTrackResponse:
    success: bool                          # 追跡成功フラグ
    message: str                           # 結果メッセージ
    current_metrics: dict[ProgressMetric, float] = {}  # 現在の指標値
    goals_status: list[WritingGoal] = []   # 目標達成状況
    trend_analysis: dict[str, any] = {}    # トレンド分析結果
    alerts: list[str] = []                 # アラートメッセージ
    dashboard_path: Path | None = None     # ダッシュボードファイルパス
    summary_report: str = ""               # サマリーレポート
```

### WritingSession (DataClass)
```python
@dataclass
class WritingSession:
    session_id: str                        # セッションID
    episode_number: int                    # 対象エピソード番号
    start_time: datetime                   # 開始時刺
    end_time: datetime | None = None       # 終了時刺
    word_count_start: int = 0              # 開始時文字数
    word_count_end: int = 0                # 終了時文字数
    words_written: int = 0                 # 執筆文字数
    session_duration: int = 0              # セッション時間（秒）
    breaks_taken: int = 0                  # 休憩回数
    productivity_score: float = 0.0        # 生産性スコア
```

## パブリックメソッド

### track_progress()

**シグネチャ**
```python
def track_progress(self, request: ProgressTrackRequest) -> ProgressTrackResponse:
```

**目的**
指定されたプロジェクトの執筆進捗を追跡し、包括的なレポートを生成する。

**引数**
- `request`: 進捗追跡リクエスト

**戻り値**
- `ProgressTrackResponse`: 進捗追跡結果

**処理フロー**
1. **プロジェクト検証**: プロジェクトの存在とアクセス確認
2. **指標収集**: 各メトリックの現在値を収集
3. **目標達成度評価**: 設定された目標との比較
4. **トレンド分析**: 時系列データの分析
5. **アラート管理**: 闾値チェックとアラート生成
6. **ダッシュボード生成**: 視覚的レポートの作成
7. **結果統合**: レスポンスの構築

### start_writing_session()

**シグネチャ**
```python
def start_writing_session(self, project_name: str, episode_number: int) -> str:
```

**目的**
新しい執筆セッションを開始し、セッションIDを返す。

**戻り値**
- `str`: セッションID

### end_writing_session()

**シグネチャ**
```python
def end_writing_session(self, session_id: str) -> WritingSession:
```

**目的**
執筆セッションを終了し、統計情報を記録する。

### set_writing_goal()

**シグネチャ**
```python
def set_writing_goal(
    self,
    project_name: str,
    goal_type: ProgressMetric,
    target_value: float,
    deadline: date | None = None,
    description: str = ""
) -> WritingGoal:
```

**目的**
新しい執筆目標を設定する。

### update_goal_progress()

**シグネチャ**
```python
def update_goal_progress(self, project_name: str) -> list[WritingGoal]:
```

**目的**
全ての目標の達成状況を更新する。

## プライベートメソッド

### _collect_current_metrics()

**シグネチャ**
```python
def _collect_current_metrics(
    self,
    project_name: str,
    metrics: list[ProgressMetric]
) -> dict[ProgressMetric, float]:
```

**目的**
指定されたメトリックの現在値を収集する。

**メトリック収集内容**
- `WORD_COUNT`: 全エピソードの総文字数
- `EPISODE_COUNT`: 完成エピソード数
- `COMPLETION_RATE`: 全体進捗率（%）
- `DAILY_OUTPUT`: 日平均執筆数
- `WRITING_STREAK`: 連続執筆日数
- `QUALITY_SCORE`: 平均品質スコア

### _analyze_writing_trends()

**シグネチャ**
```python
def _analyze_writing_trends(
    self,
    project_name: str,
    period_start: date,
    period_end: date
) -> dict[str, any]:
```

**目的**
執筆パターンとトレンドを分析する。

**分析項目**
```python
trend_analysis = {
    "daily_word_count_trend": list[int],      # 日別文字数推移
    "weekly_productivity": dict[str, float],  # 週別生産性
    "peak_writing_hours": list[int],          # 執筆ピーク時間帯
    "average_session_length": float,          # 平均セッション時間
    "consistency_score": float,               # 一貫性スコア
    "burnout_risk": float,                    # 燃え尽きリスク
    "improvement_suggestions": list[str]      # 改善提案
}
```

### _check_alert_conditions()

**シグネチャ**
```python
def _check_alert_conditions(
    self,
    current_metrics: dict[ProgressMetric, float],
    goals: list[WritingGoal],
    thresholds: dict[str, float]
) -> list[str]:
```

**目的**
アラート条件をチェックし、通知メッセージを生成する。

**アラート種類**
- **遅れアラート**: 目標期限が近いが進捗が遅い
- **低生産性アラート**: 日別出力が闾値以下
- **久しぶりアラート**: 一定期間執筆がない
- **品質低下アラート**: 品質スコアが下降傾向

### _generate_progress_dashboard()

**シグネチャ**
```python
def _generate_progress_dashboard(
    self,
    project_name: str,
    metrics: dict[ProgressMetric, float],
    goals: list[WritingGoal],
    trends: dict[str, any]
) -> Path:
```

**目的**
インタラクティブな進捗ダッシュボードを生成する。

**HTMLダッシュボード構成**
```html
<!DOCTYPE html>
<html>
<head>
    <title>執筆進捗ダッシュボード</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>/* スタイル定義 */</style>
</head>
<body>
    <div class="dashboard-container">
        <h1>📝 {{project_name}} 執筆進捗</h1>

        <!-- メトリックカード -->
        <div class="metrics-grid">
            <div class="metric-card">
                <h3>総文字数</h3>
                <div class="metric-value">{{word_count}}</div>
            </div>
            <div class="metric-card">
                <h3>進捗率</h3>
                <div class="metric-value">{{completion_rate}}%</div>
            </div>
        </div>

        <!-- 目標達成状況 -->
        <div class="goals-section">
            <h2>🎯 目標達成状況</h2>
            <div class="goals-list">
                <!-- 目標リスト -->
            </div>
        </div>

        <!-- チャートセクション -->
        <div class="charts-section">
            <canvas id="trendChart"></canvas>
            <canvas id="productivityChart"></canvas>
        </div>

        <!-- アラートセクション -->
        <div class="alerts-section">
            <!-- アラート一覧 -->
        </div>
    </div>

    <script>
        // Chart.jsを使用したチャート描画
    </script>
</body>
</html>
```

### _calculate_productivity_metrics()

**シグネチャ**
```python
def _calculate_productivity_metrics(
    self,
    sessions: list[WritingSession]
) -> dict[str, float]:
```

**目的**
執筆セッションデータから生産性指標を計算する。

**計算指標**
```python
metrics = {
    "words_per_minute": float,           # 毎分執筆数
    "words_per_session": float,          # セッション平均文字数
    "session_efficiency": float,         # セッション効率
    "focus_duration": float,             # 集中持続時間
    "break_frequency": float,            # 休憩頻度
    "consistency_index": float           # 一貫性指数
}
```

## 依存関係

### ドメインサービス
- `ProgressCalculator`: 進捗率と指標達成度の計算
- `TrendAnalyzer`: 時系列データのトレンド分析
- `ProductivityAnalyzer`: 執筆生産性の分析
- `AlertManager`: アラート条件の管理

### リポジトリ
- `ProjectRepository`: プロジェクト情報の取得
- `EpisodeRepository`: エピソード情報の取得
- `ProgressRepository`: 進捗データの永続化
- `GoalRepository`: 目標データの管理

## 設計原則遵守

### DDD準拠
- ✅ エンティティ（`WritingGoal`, `WritingSession`）の適切な使用
- ✅ 値オブジェクト（列挙型）の活用
- ✅ ドメインサービス（各種Analyzer）の適切な活用
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
episode_repo = YamlEpisodeRepository()
progress_repo = ProgressRepository()
goal_repo = GoalRepository()
progress_calculator = ProgressCalculator()
trend_analyzer = TrendAnalyzer()
productivity_analyzer = ProductivityAnalyzer()
alert_manager = AlertManager()

# ユースケース作成
use_case = TrackWritingProgress(
    project_repository=project_repo,
    episode_repository=episode_repo,
    progress_repository=progress_repo,
    goal_repository=goal_repo,
    progress_calculator=progress_calculator,
    trend_analyzer=trend_analyzer,
    productivity_analyzer=productivity_analyzer,
    alert_manager=alert_manager
)

# 執筆目標の設定
goal = use_case.set_writing_goal(
    project_name="fantasy_adventure",
    goal_type=ProgressMetric.WORD_COUNT,
    target_value=100000,
    deadline=date(2025, 12, 31),
    description="10万文字達成目標"
)

print(f"目標設定完了: {goal.description}")

# 執筆セッションの開始
session_id = use_case.start_writing_session(
    project_name="fantasy_adventure",
    episode_number=5
)

print(f"執筆セッション開始: {session_id}")

# 執筆作業...
# (実際の執筆作業が行われる)

# 執筆セッションの終了
session = use_case.end_writing_session(session_id)

print(f"セッション終了: {session.words_written}文字執筆")
print(f"所要時間: {session.session_duration//60}分")

# 進捗追跡の実行
request = ProgressTrackRequest(
    project_name="fantasy_adventure",
    metrics=[ProgressMetric.WORD_COUNT, ProgressMetric.EPISODE_COUNT, ProgressMetric.COMPLETION_RATE],
    period_start=date(2025, 1, 1),
    period_end=date(2025, 1, 31),
    include_goals=True,
    include_trends=True,
    generate_dashboard=True,
    alert_thresholds={
        "daily_output_min": 500,
        "quality_score_min": 70.0,
        "days_without_writing": 3
    }
)

response = use_case.track_progress(request)

if response.success:
    print(f"進捗追跡完了: {response.message}")

    # 現在のメトリック表示
    print("\n=== 現在の指標 ===")
    for metric, value in response.current_metrics.items():
        print(f"{metric.value}: {value}")

    # 目標達成状況表示
    print("\n=== 目標達成状況 ===")
    for goal in response.goals_status:
        status = "✅ 達成" if goal.is_achieved else f"📊 {goal.achievement_rate:.1f}%"
        print(f"{goal.description}: {status}")

    # アラート表示
    if response.alerts:
        print("\n=== アラート ===")
        for alert in response.alerts:
            print(f"⚠️ {alert}")

    # ダッシュボードの表示
    if response.dashboard_path:
        print(f"\n📊 ダッシュボード: {response.dashboard_path}")

    print(f"\nサマリー\n{response.summary_report}")
else:
    print(f"進捗追跡失敗: {response.message}")

# 目標進捗の更新
updated_goals = use_case.update_goal_progress("fantasy_adventure")
print(f"\n目標更新完了: {len(updated_goals)}件")
```

## メトリック計算詳細

### 文字数カウント
```python
def calculate_word_count(project_name: str) -> int:
    total_words = 0
    for episode in get_all_episodes(project_name):
        if episode.status in ["completed", "published"]:
            total_words += episode.word_count
    return total_words
```

### 進捗率計算
```python
def calculate_completion_rate(project_name: str) -> float:
    project_info = get_project_info(project_name)
    planned_episodes = project_info.planned_episodes
    completed_episodes = len([ep for ep in get_all_episodes(project_name)
                             if ep.status == "completed"])
    return (completed_episodes / planned_episodes) * 100 if planned_episodes > 0 else 0
```

### 執筆リズム分析
```python
def analyze_writing_rhythm(sessions: list[WritingSession]) -> dict:
    daily_counts = defaultdict(int)
    hourly_distribution = defaultdict(int)

    for session in sessions:
        day = session.start_time.date()
        hour = session.start_time.hour
        daily_counts[day] += session.words_written
        hourly_distribution[hour] += 1

    return {
        "most_productive_days": sorted(daily_counts.items(), key=lambda x: x[1], reverse=True)[:7],
        "peak_hours": sorted(hourly_distribution.items(), key=lambda x: x[1], reverse=True)[:3],
        "average_daily_output": sum(daily_counts.values()) / len(daily_counts),
        "consistency_score": calculate_consistency(daily_counts)
    }
```

## アラートシステム

### アラートルール例
```python
alert_rules = {
    # 遅れアラート
    "deadline_approaching": {
        "condition": lambda goal: goal.deadline and
                     (goal.deadline - date.today()).days <= 7 and
                     goal.achievement_rate < 90,
        "message": lambda goal: f"目標「{goal.description}」の期限が近づいています（進捗: {goal.achievement_rate:.1f}%）"
    },

    # 低生産性アラート
    "low_productivity": {
        "condition": lambda metrics: metrics.get(ProgressMetric.DAILY_OUTPUT, 0) < 300,
        "message": lambda metrics: f"日平均出力が低下しています（{metrics[ProgressMetric.DAILY_OUTPUT]:.0f}文字/日）"
    },

    # 久しぶりアラート
    "long_absence": {
        "condition": lambda last_session: (datetime.now() - last_session.end_time).days >= 3,
        "message": lambda last_session: f"{(datetime.now() - last_session.end_time).days}日間執筆がありません"
    }
}
```

## ダッシュボードチャート例

### 日別文字数トレンド
```javascript
// Chart.jsでのチャート設定
const trendChart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: daily_labels,
        datasets: [{
            label: '日別文字数',
            data: daily_word_counts,
            borderColor: 'rgb(75, 192, 192)',
            tension: 0.1
        }]
    },
    options: {
        responsive: true,
        scales: {
            y: {
                beginAtZero: true,
                title: {
                    display: true,
                    text: '文字数'
                }
            }
        }
    }
});
```

### 目標達成状況プログレスバー
```html
<div class="goal-progress">
    <div class="goal-header">
        <h4>{{goal.description}}</h4>
        <span class="progress-text">{{achievement_rate}}% 達成</span>
    </div>
    <div class="progress-bar">
        <div class="progress-fill" style="width: {{achievement_rate}}%"></div>
    </div>
    <div class="goal-details">
        <span>現在: {{current_value}}</span>
        <span>目標: {{target_value}}</span>
        {% if deadline %}<span>期限: {{deadline}}</span>{% endif %}
    </div>
</div>
```

## エラーハンドリング

### プロジェクト不存在
```python
if not self.project_repository.exists(project_name):
    return ProgressTrackResponse(
        success=False,
        message=f"プロジェクト '{project_name}' が見つかりません"
    )
```

### データ収集エラー
```python
try:
    current_metrics = self._collect_current_metrics(project_name, request.metrics)
except DataCollectionError as e:
    logger.error(f"メトリック収集エラー: {e}")
    current_metrics = {metric: 0.0 for metric in request.metrics}
except Exception as e:
    return ProgressTrackResponse(
        success=False,
        message=f"進捗追跡中にエラーが発生しました: {str(e)}"
    )
```

### セッション管理エラー
```python
def end_writing_session(self, session_id: str) -> WritingSession:
    session = self.progress_repository.get_session(session_id)
    if not session:
        raise SessionNotFoundError(f"セッション {session_id} が見つかりません")

    if session.end_time:
        raise SessionAlreadyEndedError(f"セッション {session_id} は既に終了しています")
```

## テスト観点

### 単体テスト
- 各メトリック計算の正確性
- 目標設定と進捗更新
- アラート条件の判定
- トレンド分析の動作
- エラー条件での処理

### 統合テスト
- 実際のプロジェクトでの進捗追跡
- 長期間のデータ蓄積と分析
- ダッシュボード生成機能
- セッション管理の完全性

## 品質基準

- **正確性**: メトリック計算の数学的正確性
- **リアルタイム性**: 進捗情報の即座反映
- **使いやすさ**: 直感的なダッシュボードUI
- **カスタマイズ性**: 個人の執筆スタイルに合わせた設定
- **持続性**: 長期的なモチベーション維持支援
