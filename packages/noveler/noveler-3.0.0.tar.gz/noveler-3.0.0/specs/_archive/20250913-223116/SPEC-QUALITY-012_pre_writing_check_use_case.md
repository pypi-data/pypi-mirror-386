# SPEC-QUALITY-012: 事前執筆チェックユースケース仕様書

## 1. 概要

### 1.1 目的
DDD原則に基づき、エピソード執筆開始前の必須チェック項目を管理するビジネスロジックを実装する。執筆品質の向上と離脱防止を目的とした包括的な事前チェックシステムを提供。

### 1.2 スコープ
- エピソードタイプ別のチェックリスト作成・管理
- 前話からの流れ確認・整合性チェック
- 離脱リスクポイント分析・予防提案
- 重要シーン設計確認・感覚描写準備
- チェック項目完了管理・レポート生成
- 執筆開始可能性の検証

### 1.3 アーキテクチャ位置
```
Application Layer (Use Case)
├── PreWritingCheckUseCase                      ← Domain Layer
│   ├── PreWritingCheckInput                   └── PreWritingCheck (Entity)
│   ├── CheckItemInput                         └── PreWritingCheckFactory
│   ├── PreWritingCheckOutput                  └── CheckItemType (Enum)
│   └── create_check_list(), validate_for_writing()  └── EpisodeNumber (Value Object)
└── Analysis Functions                          └── EpisodeRepository, ProjectRepository (Interfaces)
    ├── check_previous_flow()
    ├── analyze_dropout_risks()
    └── get_important_scenes()
```

### 1.4 ビジネス価値
- **執筆品質の事前確保**: チェックリストによる品質の底上げ
- **離脱率の削減**: 読者離脱ポイントの事前分析・対策
- **執筆効率の向上**: 準備不足による書き直しの防止
- **プロット整合性**: 前話との矛盾・不整合の事前発見

## 2. 機能仕様

### 2.1 コアユースケース
```python
class PreWritingCheckUseCase:
    def __init__(
        self,
        episode_repository: EpisodeRepository,
        project_repository: ProjectRepository,
        plot_repository: Any = None,      # PlotRepository
        scene_repository: Any = None      # SceneRepository
    ):
        """依存性注入による初期化"""

    def create_check_list(
        self,
        input_data: PreWritingCheckInput
    ) -> PreWritingCheckOutput:
        """チェックリスト作成"""

    def validate_for_writing(self, check_id: str) -> dict[str, Any]:
        """執筆開始可能性検証"""
```

### 2.2 入力・出力データ
```python
@dataclass
class PreWritingCheckInput:
    """事前チェック作成入力"""
    episode_number: int
    project_name: str
    check_type: str = "standard"  # standard, first_episode, climax

@dataclass
class CheckItemInput:
    """チェック項目更新入力"""
    check_id: str
    item_type: CheckItemType
    notes: str = ""
    action: str = "complete"  # complete or skip

@dataclass
class PreWritingCheckOutput:
    """事前チェック出力"""
    success: bool
    check_id: str
    episode_number: int
    project_name: str
    check_items: list[dict[str, Any]]
    completion_rate: float
    is_completed: bool
    created_at: datetime
    message: str = ""
```

### 2.3 分析機能
```python
def check_previous_flow(
    self,
    project_name: str,
    current_episode_number: int
) -> dict[str, Any]:
    """前話からの流れ確認"""

def analyze_dropout_risks(
    self,
    project_name: str,
    episode_number: int
) -> list[str]:
    """離脱リスクポイント分析"""

def get_important_scenes(
    self,
    project_name: str,
    episode_number: int
) -> list[dict[str, Any]]:
    """重要シーン情報取得"""
```

### 2.4 チェック管理機能
```python
def complete_check_item(
    self,
    input_data: CheckItemInput
) -> PreWritingCheckOutput:
    """チェック項目完了・スキップ"""

def get_check_history(
    self,
    project_name: str,
    episode_number: int
) -> list[dict[str, Any]]:
    """チェック履歴取得"""

def create_check_report(self, check_id: str) -> str:
    """チェックレポート生成"""
```

## 3. チェック種別仕様

### 3.1 標準チェック（standard）
```python
標準チェック項目 = [
    "前話からの流れ確認",
    "エピソード目標設定",
    "キャラクター状況把握",
    "重要シーン設計",
    "離脱リスク対策",
    "引きの設計",
    "感情描写準備"
]
```

### 3.2 第1話チェック（first_episode）
```python
第1話専用チェック項目 = [
    "主人公の魅力設定",
    "世界観の導入方法",
    "フック要素配置",
    "読者の疑問喚起",
    "キャラクター紹介計画",
    "次話への引き",
    "ジャンル期待値設定"
]
```

### 3.3 クライマックスチェック（climax）
```python
クライマックス専用チェック項目 = [
    "伏線回収確認",
    "キャラクター成長表現",
    "感情的盛り上がり設計",
    "読者満足度確保",
    "解決方法の妥当性",
    "余韻の設計",
    "完結感の演出"
]
```

## 4. 離脱リスク分析仕様

### 4.1 プロットパターン別リスク
```python
離脱リスクパターン = {
    "daily_life": "日常回は離脱率が高い傾向 - 小事件を含めることを推奨",
    "explanation": "説明回は離脱リスク大 - 会話や行動で情報を伝える工夫を",
    "introspection": "内省シーンは離脱ポイント - 短めに構成",
    "flashback": "回想シーンは離脱リスク - 現在時制との関連を明確に"
}
```

### 4.2 構造的離脱ポイント
```python
def analyze_dropout_risks(self, project_name: str, episode_number: int) -> list[str]:
    """離脱リスク分析ロジック"""
    risks = []

    # プロット分析
    if plot_info and plot_info.opening contains "説明":
        risks.append("冒頭が説明的 - アクションや会話から始めることを推奨")

    if plot_info and plot_info.middle contains "内省":
        risks.append("中盤の内省・回想シーンは離脱ポイント - 短めに")

    # エピソード位置分析
    if episode_number % 10 == 0:
        risks.append("区切りの話数は離脱しやすい - 新展開や衝撃的な引きを")

    return risks
```

### 4.3 デフォルト離脱防止策
```python
基本離脱防止策 = [
    "冒頭300字以内にフックを配置する",
    "章末に強い引きを確実に配置する",
    "感情表現を身体感覚で表現する",
    "読者の疑問を適度に維持する",
    "キャラクター間の関係性を進展させる"
]
```

## 5. データ構造仕様

### 5.1 チェックリスト作成入力
```python
# 標準チェック作成例
standard_input = PreWritingCheckInput(
    episode_number=5,
    project_name="転生したら最強の魔法使いだった件",
    check_type="standard"
)

# 第1話チェック作成例
first_episode_input = PreWritingCheckInput(
    episode_number=1,
    project_name="転生したら最強の魔法使いだった件",
    check_type="first_episode"
)

# クライマックスチェック作成例
climax_input = PreWritingCheckInput(
    episode_number=50,
    project_name="転生したら最強の魔法使いだった件",
    check_type="climax"
)
```

### 5.2 チェック出力構造
```python
# チェック作成成功レスポンス
success_output = PreWritingCheckOutput(
    success=True,
    check_id="550e8400-e29b-41d4-a716-446655440000",
    episode_number=5,
    project_name="転生したら最強の魔法使いだった件",
    check_items=[
        {
            "type": "PREVIOUS_FLOW",
            "title": "前話からの流れ確認",
            "status": "pending",
            "notes": "",
            "required": True
        },
        {
            "type": "EPISODE_GOAL",
            "title": "エピソード目標設定",
            "status": "pending",
            "notes": "",
            "required": True
        },
        # ... 他のチェック項目
    ],
    completion_rate=0.0,
    is_completed=False,
    created_at=datetime(2025, 7, 21, 14, 30, 22),
    message="チェックリストを作成しました"
)
```

### 5.3 前話流れ確認結果
```python
# 前話確認結果構造
previous_flow_result = {
    "has_previous": True,
    "previous_title": "第4話 - 魔法学校入学",
    "previous_ending": "明日からいよいよ授業が始まる。俺は期待と不安を胸に眠りについた。",
    "suggestions": [
        "前話の終わり方と今話の始まりが自然に繋がっているか",
        "時間経過が明確になっているか",
        "キャラクターの感情状態が連続しているか",
        "場所の移動がある場合、それが明確か"
    ]
}

# 第1話の場合
first_episode_flow = {
    "has_previous": False,
    "skip_reason": "第1話のため前話確認は不要"
}
```

### 5.4 重要シーン情報構造
```python
# 重要シーン情報
important_scenes = [
    {
        "scene_id": "scene_005_001",
        "title": "初回授業での魔法発動",
        "importance_level": "A",
        "sensory_details": {
            "visual": "光が周囲を包む瞬間",
            "auditory": "魔法陣が回る音",
            "tactile": "魔力が体を流れる感覚",
            "emotional": "驚きから確信への変化"
        },
        "notes": "主人公の成長を示す重要な転換点"
    },
    {
        "scene_id": "scene_005_002",
        "title": "クラスメイトとの初対面",
        "importance_level": "B",
        "sensory_details": {
            "visual": "多様なクラスメイトの外見",
            "emotional": "緊張から親近感への変化"
        },
        "notes": "人間関係構築の基盤シーン"
    }
]
```

## 6. 検証ロジック仕様

### 6.1 執筆開始可能性検証
```python
def validate_for_writing(self, check_id: str) -> dict[str, Any]:
    """執筆開始検証ロジック"""
    check = self._check_lists.get(check_id)

    issues = check.validate_for_writing()

    return {
        "can_start_writing": len(issues) == 0,
        "issues": issues,                    # 未解決の必須項目リスト
        "completion_rate": check.get_completion_rate(),
        "pending_items": [
            item.title for item in check.get_pending_items()
        ]
    }
```

### 6.2 必須チェック項目
```python
# 執筆開始に必須の項目（skipは許可）
REQUIRED_CHECKS = [
    CheckItemType.PREVIOUS_FLOW,    # 前話からの流れ
    CheckItemType.EPISODE_GOAL,     # エピソード目標
    CheckItemType.CHARACTER_STATE,  # キャラクター状況
    CheckItemType.IMPORTANT_SCENES  # 重要シーン設計
]

# 推奨項目（未完了でも執筆開始可）
RECOMMENDED_CHECKS = [
    CheckItemType.DROPOUT_RISKS,    # 離脱リスク対策
    CheckItemType.HOOK_DESIGN,      # 引きの設計
    CheckItemType.EMOTIONAL_PREP    # 感情描写準備
]
```

### 6.3 検証結果パターン
```python
# 検証成功パターン
validation_success = {
    "can_start_writing": True,
    "issues": [],
    "completion_rate": 100.0,
    "pending_items": []
}

# 検証失敗パターン
validation_failure = {
    "can_start_writing": False,
    "issues": [
        "前話からの流れが未確認です",
        "エピソード目標が未設定です"
    ],
    "completion_rate": 57.1,
    "pending_items": [
        "前話からの流れ確認",
        "エピソード目標設定"
    ]
}
```

## 7. エラーハンドリング仕様

### 7.1 ドメイン例外
```python
# プロジェクト存在エラー
try:
    check_list = use_case.create_check_list(input_data)
except DomainException as e:
    # "プロジェクトが存在しません: {project_name}"

# チェックリスト未発見エラー
try:
    result = use_case.complete_check_item(item_input)
except DomainException as e:
    # "チェックリストが見つかりません"
```

### 7.2 データ検証エラー
```python
# 無効なエピソード番号
if input_data.episode_number < 1:
    raise ValueError("エピソード番号は1以上である必要があります")

# 無効なチェック種別
valid_types = ["standard", "first_episode", "climax"]
if input_data.check_type not in valid_types:
    raise ValueError(f"無効なチェック種別: {input_data.check_type}")
```

### 7.3 リソース不足エラー
```python
# 前話未存在エラー（警告レベル）
if not previous_episode and current_episode_number > 1:
    warnings.append("前話が見つかりません - 連続性の確認ができません")

# プロット情報不足（情報レベル）
if not plot_repository:
    info_messages.append("プロット情報が利用できません - 基本チェックのみ実行")
```

## 8. 使用例

### 8.1 標準的な使用パターン
```python
# ユースケース初期化
episode_repository = YamlEpisodeRepository(project_path)
project_repository = YamlProjectRepository(base_path)

use_case = PreWritingCheckUseCase(
    episode_repository=episode_repository,
    project_repository=project_repository
)

# チェックリスト作成
input_data = PreWritingCheckInput(
    episode_number=5,
    project_name="転生したら最強の魔法使いだった件",
    check_type="standard"
)

result = use_case.create_check_list(input_data)
print(f"チェックID: {result.check_id}")
print(f"チェック項目数: {len(result.check_items)}")

# チェック項目を順次完了
for item in result.check_items:
    if item["required"]:
        # 必須項目の処理
        item_input = CheckItemInput(
            check_id=result.check_id,
            item_type=CheckItemType(item["type"]),
            notes="確認完了",
            action="complete"
        )

        updated_result = use_case.complete_check_item(item_input)
        print(f"完了率: {updated_result.completion_rate:.1f}%")

# 執筆開始可能性検証
validation = use_case.validate_for_writing(result.check_id)

if validation["can_start_writing"]:
    print("✅ 執筆開始可能です")
else:
    print("❌ 以下の項目を完了してください:")
    for issue in validation["issues"]:
        print(f"  - {issue}")
```

### 8.2 第1話専用チェック
```python
# 第1話用チェックリスト作成
first_input = PreWritingCheckInput(
    episode_number=1,
    project_name="新作ファンタジー小説",
    check_type="first_episode"
)

first_result = use_case.create_check_list(first_input)

# 第1話特有のチェック項目確認
for item in first_result.check_items:
    print(f"📋 {item['title']}: {item['status']}")
    if item['type'] == 'HOOK_ELEMENT':
        print("  → 読者を引き込む要素を冒頭300字以内に配置")
    elif item['type'] == 'PROTAGONIST_APPEAL':
        print("  → 主人公の魅力・特徴を明確に提示")

# レポート生成
report = use_case.create_check_report(first_result.check_id)
print(report)
```

### 8.3 離脱リスク分析統合例
```python
# プロットリポジトリ統合版
plot_repository = YamlPlotRepository(project_path)
scene_repository = YamlSceneRepository(project_path)

enhanced_use_case = PreWritingCheckUseCase(
    episode_repository=episode_repository,
    project_repository=project_repository,
    plot_repository=plot_repository,
    scene_repository=scene_repository
)

# 高度な離脱リスク分析
risks = enhanced_use_case.analyze_dropout_risks("project-001", 15)
print("🚨 離脱リスクポイント:")
for risk in risks:
    print(f"  • {risk}")

# 重要シーン分析
scenes = enhanced_use_case.get_important_scenes("project-001", 15)
print("\n🎯 重要シーン:")
for scene in scenes:
    print(f"  • {scene['title']} (重要度: {scene['importance_level']})")
    if scene['sensory_details']:
        print(f"    感覚描写: {', '.join(scene['sensory_details'].keys())}")

# 前話との連続性確認
flow_check = enhanced_use_case.check_previous_flow("project-001", 15)
if flow_check["has_previous"]:
    print(f"\n📖 前話: {flow_check['previous_title']}")
    print(f"前話の結末: {flow_check['previous_ending']}")
    print("確認ポイント:")
    for suggestion in flow_check['suggestions']:
        print(f"  ✓ {suggestion}")
```

### 8.4 チェック履歴活用例
```python
# チェック履歴の取得・分析
history = use_case.get_check_history("project-001", 10)

print("📊 チェック履歴分析:")
print(f"総チェック回数: {len(history)}")

if history:
    latest = history[0]
    print(f"最新チェック: {latest['timestamp']}")
    print(f"完了率: {latest['completion_rate']:.1f}%")
    print(f"ステータス: {'完了' if latest['is_completed'] else '進行中'}")

# 完了率推移の分析
completion_rates = [h['completion_rate'] for h in history]
if len(completion_rates) >= 2:
    trend = "向上" if completion_rates[0] > completion_rates[-1] else "低下"
    print(f"完了率トレンド: {trend}")
```

## 9. テスト仕様

### 9.1 単体テスト
```python
class TestPreWritingCheckUseCase:
    def test_create_standard_check_list(self):
        """標準チェックリスト作成テスト"""

    def test_create_first_episode_check_list(self):
        """第1話チェックリスト作成テスト"""

    def test_create_climax_check_list(self):
        """クライマックスチェックリスト作成テスト"""

    def test_complete_check_item_success(self):
        """チェック項目完了テスト"""

    def test_skip_check_item_success(self):
        """チェック項目スキップテスト"""

    def test_validate_for_writing_ready(self):
        """執筆開始可能検証テスト"""

    def test_validate_for_writing_not_ready(self):
        """執筆開始不可検証テスト"""

    def test_project_not_found_error(self):
        """プロジェクト不存在エラーテスト"""

    def test_check_list_not_found_error(self):
        """チェックリスト不存在エラーテスト"""
```

### 9.2 統合テスト
```python
class TestPreWritingCheckIntegration:
    def test_full_check_workflow(self):
        """完全チェックワークフローテスト"""

    def test_previous_flow_integration(self):
        """前話流れ確認統合テスト"""

    def test_dropout_risk_analysis_integration(self):
        """離脱リスク分析統合テスト"""

    def test_repository_integration(self):
        """リポジトリ統合テスト"""
```

### 9.3 ユースケーステスト
```python
class TestPreWritingCheckScenarios:
    def test_beginner_first_episode_scenario(self):
        """初心者第1話執筆シナリオ"""

    def test_experienced_writer_climax_scenario(self):
        """経験者クライマックス執筆シナリオ"""

    def test_series_continuation_scenario(self):
        """連載継続執筆シナリオ"""
```

## 10. 実装メモ

### 10.1 実装ファイル
- **メインクラス**: `scripts/application/use_cases/pre_writing_check_use_case.py`
- **テストファイル**: `tests/unit/application/use_cases/test_pre_writing_check_use_case.py`
- **統合テスト**: `tests/integration/test_pre_writing_check_workflow.py`

### 10.2 設計方針
- **DDD原則の厳格遵守**: アプリケーション層でのビジネスロジック集約
- **事前品質確保**: 書き始める前の品質担保メカニズム
- **柔軟なチェック体系**: エピソード種別に応じた最適化
- **データ駆動分析**: 過去データに基づく離脱リスク予測

### 10.3 今後の改善点
- [ ] 機械学習による離脱リスク予測精度向上
- [ ] 個人の執筆パターン学習機能
- [ ] チェック項目のカスタマイズ機能
- [ ] 自動シーン分析・提案機能
- [ ] リアルタイム品質監視統合
- [ ] 読者アンケート結果との相関分析
