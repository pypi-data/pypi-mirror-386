# SPEC-CLI-102: CLIUXIntegration 仕様書

## 概要

CLIUXIntegrationは、シームレスなユーザーエクスペリエンスを実現するCLI統合レイヤーです。視覚的フィードバック、適応的インターフェース、コンテキスト認識、学習機能を通じて、直感的で効率的なCLI操作環境を提供します。

## クラス設計

```python
from typing import Dict, List, Optional, Any, Callable, Union, Protocol
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from enum import Enum
import asyncio
from datetime import datetime
from pathlib import Path
import threading
import queue

class UXMode(Enum):
    """UXモード"""
    MINIMAL = "minimal"          # 最小限の出力
    STANDARD = "standard"        # 標準出力
    RICH = "rich"               # リッチな視覚表示
    ADAPTIVE = "adaptive"       # 適応的表示

class ThemeMode(Enum):
    """テーマモード"""
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"
    HIGH_CONTRAST = "high_contrast"

class NotificationLevel(Enum):
    """通知レベル"""
    DEBUG = "debug"
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class UXConfig:
    """UX設定"""
    mode: UXMode = UXMode.STANDARD
    theme: ThemeMode = ThemeMode.AUTO
    animations: bool = True
    sound_feedback: bool = False
    verbose_level: int = 1  # 0-3
    show_hints: bool = True
    compact_output: bool = False
    color_enabled: bool = True

@dataclass
class TerminalInfo:
    """ターミナル情報"""
    width: int
    height: int
    color_support: bool
    unicode_support: bool
    mouse_support: bool
    hyperlink_support: bool
    terminal_type: str
    os_type: str

@dataclass
class UserBehavior:
    """ユーザー行動データ"""
    command_frequency: Dict[str, int] = field(default_factory=dict)
    error_patterns: Dict[str, int] = field(default_factory=dict)
    preferred_shortcuts: List[str] = field(default_factory=list)
    average_session_time: float = 0.0
    last_activities: List[str] = field(default_factory=list)
    skill_level: str = "beginner"  # "beginner", "intermediate", "expert"

@dataclass
class VisualComponent:
    """視覚コンポーネント"""
    type: str  # "text", "table", "chart", "progress", "menu"
    content: Any
    style: Dict[str, Any] = field(default_factory=dict)
    interactive: bool = False
    position: Optional[Tuple[int, int]] = None
    size: Optional[Tuple[int, int]] = None

@dataclass
class Notification:
    """通知"""
    level: NotificationLevel
    title: str
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    action: Optional[Callable] = None
    duration: Optional[float] = None
    persistent: bool = False

class CLIUXIntegration:
    """CLIユーザーエクスペリエンス統合"""

    def __init__(
        self,
        terminal_adapter: 'TerminalAdapter',
        theme_manager: 'ThemeManager',
        animation_engine: 'AnimationEngine',
        notification_system: 'NotificationSystem',
        learning_engine: 'LearningEngine'
    ):
        self.terminal_adapter = terminal_adapter
        self.theme_manager = theme_manager
        self.animation_engine = animation_engine
        self.notification_system = notification_system
        self.learning_engine = learning_engine
        self._terminal_info: Optional[TerminalInfo] = None
        self._ux_config = UXConfig()
        self._user_behavior = UserBehavior()
        self._active_components: Dict[str, VisualComponent] = {}
        self._notification_queue: queue.Queue = queue.Queue()
```

## データ構造

### リクエストモデル

```python
@dataclass
class RenderRequest:
    """レンダリングリクエスト"""
    components: List[VisualComponent]
    layout: str = "vertical"  # "vertical", "horizontal", "grid", "overlay"
    clear_screen: bool = False
    preserve_history: bool = True
    animation_config: Optional['AnimationConfig'] = None

@dataclass
class AnimationConfig:
    """アニメーション設定"""
    type: str  # "fade", "slide", "typewriter", "pulse", "progress"
    duration: float = 1.0
    easing: str = "ease-in-out"
    loop: bool = False
    auto_start: bool = True

@dataclass
class InteractionRequest:
    """インタラクションリクエスト"""
    prompt: str
    input_type: str  # "text", "choice", "confirm", "password", "file"
    validation: Optional[Callable] = None
    suggestions: List[str] = field(default_factory=list)
    default_value: Optional[str] = None
    timeout: Optional[float] = None

@dataclass
class FeedbackRequest:
    """フィードバックリクエスト"""
    message: str
    feedback_type: str  # "success", "error", "info", "warning"
    duration: float = 3.0
    position: str = "bottom"  # "top", "bottom", "center"
    blocking: bool = False
```

### レスポンスモデル

```python
@dataclass
class RenderResponse:
    """レンダリングレスポンス"""
    rendered: bool
    layout_info: Dict[str, Any]
    component_positions: Dict[str, Tuple[int, int]]
    animation_id: Optional[str] = None
    render_time: float = 0.0

@dataclass
class InteractionResponse:
    """インタラクションレスポンス"""
    user_input: str
    interaction_time: float
    cancelled: bool = False
    validation_passed: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AdaptationResponse:
    """適応レスポンス"""
    adaptations_applied: List[str]
    new_ux_config: UXConfig
    learning_updates: Dict[str, Any]
    recommendations: List[str] = field(default_factory=list)
```

## パブリックメソッド

```python
class CLIUXIntegration:

    def initialize_terminal(self) -> TerminalInfo:
        """
        ターミナルを初期化し、情報を取得

        Returns:
            ターミナル情報
        """
        pass

    def configure_ux(self, config: UXConfig) -> None:
        """
        UX設定を構成

        Args:
            config: UX設定
        """
        pass

    async def render_components(
        self,
        request: RenderRequest
    ) -> RenderResponse:
        """
        視覚コンポーネントをレンダリング

        Args:
            request: レンダリングリクエスト

        Returns:
            レンダリング結果
        """
        pass

    async def handle_interaction(
        self,
        request: InteractionRequest
    ) -> InteractionResponse:
        """
        ユーザーインタラクションを処理

        Args:
            request: インタラクションリクエスト

        Returns:
            インタラクション結果
        """
        pass

    def show_feedback(
        self,
        request: FeedbackRequest
    ) -> None:
        """
        フィードバックを表示

        Args:
            request: フィードバックリクエスト
        """
        pass

    def notify(
        self,
        notification: Notification
    ) -> str:
        """
        通知を送信

        Args:
            notification: 通知

        Returns:
            通知ID
        """
        pass

    async def adapt_to_user(
        self,
        user_action: str,
        context: Dict[str, Any]
    ) -> AdaptationResponse:
        """
        ユーザーに適応

        Args:
            user_action: ユーザーアクション
            context: コンテキスト

        Returns:
            適応結果
        """
        pass

    def create_progress_display(
        self,
        task_name: str,
        total_steps: int,
        style: str = "bar"
    ) -> 'ProgressDisplay':
        """
        進捗表示を作成

        Args:
            task_name: タスク名
            total_steps: 総ステップ数
            style: 表示スタイル

        Returns:
            進捗表示オブジェクト
        """
        pass

    def create_menu(
        self,
        title: str,
        items: List[str],
        multi_select: bool = False
    ) -> 'InteractiveMenu':
        """
        インタラクティブメニューを作成

        Args:
            title: メニュータイトル
            items: メニュー項目
            multi_select: 複数選択可能

        Returns:
            インタラクティブメニュー
        """
        pass

    def create_table_display(
        self,
        data: List[Dict[str, Any]],
        columns: Optional[List[str]] = None,
        sortable: bool = True
    ) -> 'TableDisplay':
        """
        テーブル表示を作成

        Args:
            data: テーブルデータ
            columns: 表示カラム
            sortable: ソート可能

        Returns:
            テーブル表示オブジェクト
        """
        pass

    def record_user_behavior(
        self,
        action: str,
        context: Dict[str, Any],
        success: bool
    ) -> None:
        """
        ユーザー行動を記録

        Args:
            action: アクション
            context: コンテキスト
            success: 成功フラグ
        """
        pass

    def get_smart_suggestions(
        self,
        current_context: str,
        partial_input: str = ""
    ) -> List[str]:
        """
        スマートサジェスチョンを取得

        Args:
            current_context: 現在のコンテキスト
            partial_input: 部分入力

        Returns:
            サジェスチョンリスト
        """
        pass
```

## プライベートメソッド

```python
class CLIUXIntegration:

    def _detect_terminal_capabilities(self) -> TerminalInfo:
        """ターミナル機能を検出"""
        pass

    def _adapt_to_terminal(self, terminal_info: TerminalInfo) -> None:
        """ターミナルに適応"""
        pass

    def _calculate_layout(
        self,
        components: List[VisualComponent],
        layout_type: str
    ) -> Dict[str, Tuple[int, int]]:
        """レイアウトを計算"""
        pass

    def _render_component(
        self,
        component: VisualComponent,
        position: Tuple[int, int]
    ) -> str:
        """コンポーネントをレンダリング"""
        pass

    def _apply_theme(
        self,
        content: str,
        component_type: str
    ) -> str:
        """テーマを適用"""
        pass

    def _animate_transition(
        self,
        from_state: str,
        to_state: str,
        config: AnimationConfig
    ) -> None:
        """トランジションアニメーション"""
        pass

    def _validate_user_input(
        self,
        input_value: str,
        validator: Callable,
        input_type: str
    ) -> Tuple[bool, List[str]]:
        """ユーザー入力を検証"""
        pass

    def _update_user_model(
        self,
        behavior_data: Dict[str, Any]
    ) -> None:
        """ユーザーモデルを更新"""
        pass

    def _generate_contextual_help(
        self,
        current_state: str,
        user_history: List[str]
    ) -> List[str]:
        """コンテキストヘルプを生成"""
        pass

    def _optimize_display_performance(self) -> None:
        """表示パフォーマンスを最適化"""
        pass
```

## ユーザーインターフェース

### 適応的インターフェース

```python
# 初心者向け表示
if user_behavior.skill_level == "beginner":
    show_detailed_help = True
    show_step_by_step_guide = True
    enable_confirmation_dialogs = True

# エキスパート向け表示
elif user_behavior.skill_level == "expert":
    show_minimal_output = True
    enable_advanced_shortcuts = True
    hide_basic_confirmations = True
```

### 視覚的フィードバック

```bash
# 成功フィードバック
✅ エピソード作成が完了しました
   📄 第001話_異世界転生.md が作成されました
   ⏱️ 実行時間: 1.2秒

# 進捗表示（アニメーション付き）
🚀 品質チェック実行中...
   ████████████████████████████████ 100% (5/5)
   ✅ 基本文章チェック
   ✅ 構成チェック
   ✅ キャラクター整合性
   ✅ 時系列チェック
   ✅ 伏線チェック

# エラー表示（構造化）
❌ エピソード作成に失敗しました

📋 エラー詳細:
   • ファイル名に使用できない文字が含まれています: "第1話/新章"
   • 必要なディレクトリが存在しません: 40_原稿/

💡 解決方法:
   1. ファイル名から '/' を削除してください
   2. 'novel init' でプロジェクトを初期化してください

🔧 修正コマンド:
   novel write new --title "第1話_新章"
```

### インタラクティブメニュー

```python
# カスタマイズ可能メニュー
class InteractiveMenu:
    def __init__(self, title: str, items: List[str]):
        self.title = title
        self.items = items
        self.selected_index = 0
        self.multi_select_mode = False
        self.search_enabled = True

    def render(self) -> str:
        """メニューをレンダリング"""
        menu_display = f"📋 {self.title}\n\n"

        for i, item in enumerate(self.items):
            if i == self.selected_index:
                menu_display += f"  ▶️  {item}\n"
            else:
                menu_display += f"     {item}\n"

        menu_display += "\n⌨️  矢印キー: 選択, Enter: 決定, /: 検索, q: 終了"
        return menu_display
```

### テーマシステム

```python
THEMES = {
    "light": {
        "primary": "#0066cc",
        "success": "#28a745",
        "warning": "#ffc107",
        "error": "#dc3545",
        "text": "#212529",
        "background": "#ffffff"
    },
    "dark": {
        "primary": "#66b3ff",
        "success": "#40d870",
        "warning": "#ffd43b",
        "error": "#ff6b6b",
        "text": "#f8f9fa",
        "background": "#212529"
    },
    "high_contrast": {
        "primary": "#ffffff",
        "success": "#00ff00",
        "warning": "#ffff00",
        "error": "#ff0000",
        "text": "#ffffff",
        "background": "#000000"
    }
}
```

## 依存関係

```python
from infrastructure.terminal.terminal_adapter import TerminalAdapter
from presentation.themes.theme_manager import ThemeManager
from presentation.animations.animation_engine import AnimationEngine
from infrastructure.notifications.notification_system import NotificationSystem
from domain.services.learning_engine import LearningEngine
from application.services.context_manager import ContextManager
from infrastructure.persistence.user_preference_repository import UserPreferenceRepository
```

## 設計原則遵守

### ユーザーエクスペリエンス原則
- **直感性**: 自然な操作フロー
- **一貫性**: 統一されたインターフェース
- **応答性**: 即座のフィードバック
- **適応性**: ユーザーに合わせた調整

### アクセシビリティ原則
- **視覚的多様性**: カラーブラインド対応
- **認知負荷軽減**: 段階的情報提示
- **キーボード操作**: マウス不要操作
- **スクリーンリーダー**: 音声読み上げ対応

### パフォーマンス原則
- **レスポンシブ**: < 100ms フィードバック
- **効率的**: 最小リソース使用
- **スケーラブル**: 大量データ対応
- **キャッシュ活用**: 繰り返し処理最適化

## 使用例

### 基本的な使用例

```python
# UX統合の初期化
ux_integration = CLIUXIntegration(
    terminal_adapter=terminal_adapter,
    theme_manager=theme_manager,
    animation_engine=animation_engine,
    notification_system=notification_system,
    learning_engine=learning_engine
)

# ターミナル情報取得と適応
terminal_info = ux_integration.initialize_terminal()
print(f"ターミナル: {terminal_info.terminal_type}")
print(f"色対応: {terminal_info.color_support}")
```

### 進捗表示

```python
# 進捗表示作成
progress = ux_integration.create_progress_display(
    task_name="品質チェック実行",
    total_steps=5,
    style="detailed"
)

# 段階的更新
await progress.update(1, "基本文章チェック中...")
await progress.update(2, "構成チェック中...")
await progress.update(3, "キャラクター整合性チェック中...")
await progress.complete("すべてのチェックが完了しました")
```

### インタラクティブ選択

```python
# メニュー作成
menu = ux_integration.create_menu(
    title="実行する操作を選択してください",
    items=[
        "新しいエピソードを作成",
        "既存エピソードを編集",
        "品質チェックを実行",
        "プロジェクト設定を変更"
    ]
)

# ユーザー選択を取得
selection = await menu.show()
print(f"選択された操作: {selection}")
```

### 適応的インターフェース

```python
# ユーザー行動を記録
ux_integration.record_user_behavior(
    action="write_episode",
    context={"episode_number": 1, "duration": 45.6},
    success=True
)

# ユーザーに適応
adaptation = await ux_integration.adapt_to_user(
    user_action="frequent_quality_check",
    context={"command_frequency": {"check": 15, "write": 3}}
)

print(f"適応結果: {adaptation.adaptations_applied}")
# 出力例: ['enabled_auto_check', 'shortened_feedback', 'added_quality_shortcuts']
```

### 通知システム

```python
# 成功通知
success_notification = Notification(
    level=NotificationLevel.SUCCESS,
    title="エピソード作成完了",
    message="第5話が正常に作成されました",
    duration=3.0
)
ux_integration.notify(success_notification)

# 警告通知（アクション付き）
warning_notification = Notification(
    level=NotificationLevel.WARNING,
    title="品質スコアが低下",
    message="前回より品質スコアが10ポイント低下しました",
    action=lambda: print("品質改善ガイドを表示"),
    persistent=True
)
ux_integration.notify(warning_notification)
```

### テーブル表示

```python
# エピソード一覧をテーブル表示
episode_data = [
    {"番号": 1, "タイトル": "異世界転生", "文字数": 2500, "品質": 85},
    {"番号": 2, "タイトル": "魔法学院", "文字数": 3200, "品質": 92},
    {"番号": 3, "タイトル": "初めての戦闘", "文字数": 2800, "品質": 78}
]

table = ux_integration.create_table_display(
    data=episode_data,
    columns=["番号", "タイトル", "文字数", "品質"],
    sortable=True
)

await table.show()
```

### アニメーション効果

```python
# タイプライター効果でテキスト表示
animation_config = AnimationConfig(
    type="typewriter",
    duration=2.0,
    easing="linear"
)

render_request = RenderRequest(
    components=[
        VisualComponent(
            type="text",
            content="新しいエピソードの作成を開始します...",
        )
    ],
    animation_config=animation_config
)

await ux_integration.render_components(render_request)
```

## エラーハンドリング

```python
class UXRenderingError(Exception):
    """UXレンダリングエラー"""
    pass

class TerminalCompatibilityError(Exception):
    """ターミナル互換性エラー"""
    def __init__(self, required_features: List[str], missing_features: List[str]):
        super().__init__(f"Required terminal features missing: {missing_features}")
        self.required_features = required_features
        self.missing_features = missing_features

class UserInteractionTimeout(Exception):
    """ユーザーインタラクションタイムアウト"""
    pass

class AdaptationError(Exception):
    """適応エラー"""
    pass

# 回復可能エラーハンドリング
class GracefulDegradation:
    """優雅な機能縮退"""

    @staticmethod
    def handle_rendering_error(error: UXRenderingError) -> str:
        """レンダリングエラーの場合は基本テキスト出力にフォールバック"""
        return "テキストモードで表示します"

    @staticmethod
    def handle_animation_error(error: Exception) -> None:
        """アニメーションエラーの場合は静的表示にフォールバック"""
        pass

    @staticmethod
    def handle_theme_error(error: Exception) -> Dict[str, str]:
        """テーマエラーの場合はデフォルトテーマを使用"""
        return THEMES["light"]
```

## テスト観点

### ユニットテスト
- コンポーネントレンダリング正確性
- テーマ適用の正確性
- ユーザー行動分析の精度
- 適応アルゴリズムの妥当性

### 統合テスト
- ターミナル検出と適応
- アニメーション実行
- 通知システム連携
- 学習エンジン統合

### ユーザビリティテスト
```gherkin
Feature: 適応的ユーザーインターフェース

  Scenario: 初回使用時のガイダンス
    Given 新規ユーザーがCLIを起動
    When 初回コマンドを実行
    Then 詳細なガイダンスが表示される
    And 次のステップが提案される

  Scenario: エキスパートユーザーの効率化
    Given 熟練ユーザーが頻繁にコマンドを使用
    When システムがパターンを学習
    Then インターフェースが簡素化される
    And ショートカットが提案される

  Scenario: エラーからの学習
    Given ユーザーが同じエラーを3回経験
    When 次回同様のコマンドを実行
    Then 事前に警告が表示される
    And 正しい方法が提案される
```

### アクセシビリティテスト
- カラーブラインド対応確認
- キーボード操作のみでの完全操作
- スクリーンリーダー対応テスト
- 高コントラストモード動作確認

## 品質基準

### レスポンシブネス基準
- ユーザー入力応答: < 50ms
- 画面更新: < 100ms
- アニメーション再生: 60fps維持
- 通知表示: < 200ms

### ユーザビリティ基準
- 学習曲線: 3回使用で80%のコマンドを習得
- エラー率: < 5% (同じエラーの繰り返し)
- 満足度: > 4.5/5 (ユーザー評価)
- 効率改善: 20%の操作時間短縮（適応後）

### アクセシビリティ基準
- WCAG 2.1 AA準拠
- 色覚異常者対応: 100%
- キーボード操作: 全機能対応
- 音声読み上げ: 主要機能対応

### パフォーマンス基準
- メモリ使用量: < 50MB
- CPU使用率: < 10% (通常操作時)
- 起動時間: < 1秒
- ファイルI/O: 最小限に抑制
