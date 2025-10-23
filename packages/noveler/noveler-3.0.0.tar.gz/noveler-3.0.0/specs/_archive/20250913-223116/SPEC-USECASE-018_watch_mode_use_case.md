# ウォッチモードユースケース仕様書

## 1. 概要

### 1.1 目的
DDD原則に基づき、ファイル変更を監視してリアルタイムで品質チェック・分析・フィードバックを提供する機能を実装。執筆中の即時サポートにより、品質向上と効率的な執筆を実現。

### 1.2 スコープ
- ファイル変更の監視（作成・更新・削除・移動）
- リアルタイム品質チェック実行
- 増分分析（変更部分のみの効率的な分析）
- 自動修正・提案の即時反映
- 執筆統計のリアルタイム更新
- 通知・アラート機能

### 1.3 アーキテクチャ位置
```
Application Layer (Use Case)
├── WatchModeUseCase                        ← Domain Layer
│   ├── WatchModeRequest                    └── WatchSession (Entity)
│   ├── WatchModeResponse                   └── FileChangeEvent (Value Object)
│   └── execute()                           └── WatchConfiguration (Value Object)
└── Helper Functions                         └── WatchSessionRepository (Interface)
    ├── start_watch_session()
    └── configure_watch_rules()
```

### 1.4 ビジネス価値
- **即時フィードバック**: 執筆中のリアルタイム品質向上
- **生産性向上**: 自動チェックによる手動作業削減
- **品質維持**: 継続的な品質監視による一貫性確保
- **執筆フロー最適化**: 中断なしの自然な執筆体験

## 2. 機能仕様

### 2.1 コアユースケース
```python
class WatchModeUseCase:
    def __init__(
        self,
        file_watcher: FileWatcherService,
        quality_checker: QualityCheckService,
        notification_service: NotificationService,
        session_repository: WatchSessionRepository
    ) -> None:
        """依存性注入による初期化"""

    def execute(self, request: WatchModeRequest) -> WatchModeResponse:
        """ウォッチモード実行"""
```

### 2.2 リクエスト・レスポンス
```python
@dataclass(frozen=True)
class WatchModeRequest:
    """ウォッチモードリクエスト"""
    project_id: str
    watch_paths: list[str]
    configuration: WatchConfiguration
    session_name: str | None = None

@dataclass(frozen=True)
class WatchModeResponse:
    """ウォッチモードレスポンス"""
    success: bool
    session_id: str | None = None
    session: WatchSession | None = None
    error_message: str | None = None

    @classmethod
    def success_response(cls, session: WatchSession) -> WatchModeResponse

    @classmethod
    def error_response(cls, error_message: str) -> WatchModeResponse
```

### 2.3 監視機能
```python
def _setup_file_watcher(self, paths: list[str], config: WatchConfiguration) -> FileWatcher:
    """ファイル監視設定"""

def _handle_file_change(self, event: FileChangeEvent) -> None:
    """ファイル変更ハンドリング"""

def _perform_incremental_check(self, file_path: str, changes: list[Change]) -> CheckResult:
    """増分品質チェック実行"""

def _update_statistics(self, session: WatchSession, event: FileChangeEvent) -> None:
    """統計情報更新"""

def _send_notification(self, event: NotificationEvent) -> None:
    """通知送信"""
```

### 2.4 ヘルパー関数
```python
def start_watch_session(
    project_id: str,
    watch_paths: list[str] | None = None,
    auto_fix: bool = False,
    notification_level: NotificationLevel = NotificationLevel.NORMAL
) -> WatchSession:
    """ウォッチセッション開始"""

def configure_watch_rules(
    project_id: str,
    rules: dict[str, WatchRule],
    save_as_default: bool = False
) -> WatchConfiguration:
    """ウォッチルール設定"""
```

## 3. データ構造仕様

### 3.1 列挙型定義
```python
from enum import Enum, auto

class FileChangeType(Enum):
    """ファイル変更タイプ"""
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"
    MOVED = "moved"

class WatchMode(Enum):
    """ウォッチモード"""
    QUALITY_CHECK = auto()    # 品質チェックのみ
    AUTO_FIX = auto()        # 自動修正あり
    ANALYSIS = auto()        # 分析モード
    FULL = auto()           # 全機能

class NotificationLevel(Enum):
    """通知レベル"""
    SILENT = 0      # 通知なし
    ERROR_ONLY = 1  # エラーのみ
    NORMAL = 2      # 通常通知
    VERBOSE = 3     # 詳細通知

class CheckTrigger(Enum):
    """チェック実行トリガー"""
    ON_SAVE = "on_save"          # 保存時
    ON_PAUSE = "on_pause"        # 一定時間無操作時
    ON_CHAR_COUNT = "on_char_count"  # 文字数閾値到達時
    INTERVAL = "interval"        # 定期実行
```

### 3.2 データクラス定義
```python
@dataclass(frozen=True)
class WatchConfiguration:
    """ウォッチ設定"""
    mode: WatchMode = WatchMode.QUALITY_CHECK
    check_trigger: CheckTrigger = CheckTrigger.ON_SAVE
    auto_fix: bool = False
    notification_level: NotificationLevel = NotificationLevel.NORMAL
    check_interval_seconds: int = 300  # 5分
    pause_threshold_seconds: int = 10  # 10秒
    char_count_threshold: int = 500
    file_patterns: list[str] = field(default_factory=lambda: ["*.md", "*.txt"])
    ignore_patterns: list[str] = field(default_factory=lambda: ["*_backup*", "*.tmp"])

@dataclass(frozen=True)
class FileChangeEvent:
    """ファイル変更イベント"""
    file_path: str
    change_type: FileChangeType
    timestamp: datetime
    old_path: str | None = None  # MOVEDの場合
    size_bytes: int = 0
    changes: list[TextChange] = field(default_factory=list)

@dataclass(frozen=True)
class TextChange:
    """テキスト変更情報"""
    line_number: int
    old_content: str
    new_content: str
    change_type: ChangeType

@dataclass(frozen=True)
class WatchSession:
    """ウォッチセッション"""
    session_id: str
    project_id: str
    started_at: datetime
    configuration: WatchConfiguration
    watch_paths: list[str]
    statistics: WatchStatistics
    is_active: bool = True

@dataclass
class WatchStatistics:
    """ウォッチ統計"""
    total_changes: int = 0
    files_modified: int = 0
    quality_checks_run: int = 0
    auto_fixes_applied: int = 0
    errors_found: int = 0
    warnings_found: int = 0
    total_characters_written: int = 0
    active_writing_time_seconds: int = 0

@dataclass(frozen=True)
class CheckResult:
    """チェック結果"""
    file_path: str
    timestamp: datetime
    issues: list[QualityIssue]
    fixes_applied: list[AppliedFix]
    statistics: FileStatistics
    processing_time_ms: int

@dataclass(frozen=True)
class NotificationEvent:
    """通知イベント"""
    level: NotificationLevel
    title: str
    message: str
    timestamp: datetime
    file_path: str | None = None
    action_required: bool = False
    suggested_actions: list[str] = field(default_factory=list)
```

### 3.3 ウォッチルール
```python
@dataclass(frozen=True)
class WatchRule:
    """ウォッチルール"""
    rule_id: str
    name: str
    condition: WatchCondition
    actions: list[WatchAction]
    enabled: bool = True
    priority: int = 0

@dataclass(frozen=True)
class WatchCondition:
    """ウォッチ条件"""
    file_pattern: str | None = None
    change_type: FileChangeType | None = None
    content_pattern: str | None = None  # 正規表現
    min_file_size: int | None = None
    max_file_size: int | None = None

@dataclass(frozen=True)
class WatchAction:
    """ウォッチアクション"""
    action_type: ActionType
    parameters: dict[str, Any]

class ActionType(Enum):
    """アクションタイプ"""
    RUN_QUALITY_CHECK = auto()
    AUTO_FIX = auto()
    ANALYZE_TEXT = auto()
    SEND_NOTIFICATION = auto()
    UPDATE_STATISTICS = auto()
    TRIGGER_BACKUP = auto()
```

## 4. ビジネスルール仕様

### 4.1 監視ルール
```python
# デフォルト監視設定
DEFAULT_WATCH_RULES = {
    "quality_on_save": WatchRule(
        rule_id="default-quality",
        name="保存時品質チェック",
        condition=WatchCondition(
            file_pattern="*.md",
            change_type=FileChangeType.MODIFIED
        ),
        actions=[
            WatchAction(
                action_type=ActionType.RUN_QUALITY_CHECK,
                parameters={"categories": ["basic", "readability"]}
            )
        ]
    ),
    "auto_backup": WatchRule(
        rule_id="default-backup",
        name="自動バックアップ",
        condition=WatchCondition(
            change_type=FileChangeType.MODIFIED,
            min_file_size=1000  # 1KB以上
        ),
        actions=[
            WatchAction(
                action_type=ActionType.TRIGGER_BACKUP,
                parameters={"keep_versions": 5}
            )
        ]
    )
}
```

### 4.2 増分チェック戦略
```python
def determine_check_scope(changes: list[TextChange]) -> CheckScope:
    """チェック範囲決定

    戦略:
    - 5行以下の変更: 変更行のみチェック
    - 6-20行の変更: 変更段落全体をチェック
    - 21行以上の変更: ファイル全体をチェック
    - 構造的変更（見出し等）: 常に全体チェック
    """

    if has_structural_changes(changes):
        return CheckScope.FULL_FILE

    changed_lines = len(changes)
    if changed_lines <= 5:
        return CheckScope.CHANGED_LINES
    elif changed_lines <= 20:
        return CheckScope.CHANGED_PARAGRAPHS
    else:
        return CheckScope.FULL_FILE
```

### 4.3 通知ルール
```python
NOTIFICATION_RULES = {
    "critical_error": {
        "condition": lambda r: r.has_critical_errors(),
        "level": NotificationLevel.ERROR_ONLY,
        "title": "重大なエラーを検出",
        "action_required": True
    },
    "quality_degradation": {
        "condition": lambda r: r.quality_score_dropped_by(10),
        "level": NotificationLevel.NORMAL,
        "title": "品質スコアが低下",
        "action_required": False
    },
    "milestone_reached": {
        "condition": lambda s: s.total_characters_written >= 3000,
        "level": NotificationLevel.NORMAL,
        "title": "3000文字達成！",
        "action_required": False
    }
}
```

## 5. エラーハンドリング仕様

### 5.1 エラー分類
```python
class WatchModeError(Exception):
    """ウォッチモードエラー基底クラス"""

class FileWatcherError(WatchModeError):
    """ファイル監視エラー"""

class PermissionError(WatchModeError):
    """権限エラー"""

class WatcherInitializationError(WatchModeError):
    """監視初期化エラー"""

class CheckServiceError(WatchModeError):
    """チェックサービスエラー"""
```

### 5.2 エラーハンドリング実装
```python
def _handle_file_change_safely(self, event: FileChangeEvent) -> None:
    """安全なファイル変更処理"""
    try:
        result = self._perform_incremental_check(
            event.file_path,
            event.changes
        )
        self._process_check_result(result)
    except PermissionError:
        self._send_notification(NotificationEvent(
            level=NotificationLevel.ERROR_ONLY,
            title="ファイルアクセスエラー",
            message=f"{event.file_path}にアクセスできません",
            timestamp=datetime.now()
        ))
    except CheckServiceError as e:
        logger.error(f"品質チェックエラー: {e}")
        # チェックをスキップして監視を継続
    except Exception as e:
        logger.error(f"予期しないエラー: {e}")
        # セッションは継続するが、このイベントはスキップ
```

## 6. 使用例

### 6.1 基本的なウォッチモード起動
```python
# サービス準備
file_watcher = FileWatcherService()
quality_checker = QualityCheckService()
notification_service = DesktopNotificationService()
session_repository = YamlWatchSessionRepository()

# ユースケース初期化
use_case = WatchModeUseCase(
    file_watcher,
    quality_checker,
    notification_service,
    session_repository
)

# ウォッチ設定
config = WatchConfiguration(
    mode=WatchMode.AUTO_FIX,
    check_trigger=CheckTrigger.ON_SAVE,
    auto_fix=True,
    notification_level=NotificationLevel.NORMAL
)

# ウォッチモード開始
request = WatchModeRequest(
    project_id="novel-project-001",
    watch_paths=["40_原稿/"],
    configuration=config,
    session_name="執筆セッション2024-01-20"
)

response = use_case.execute(request)

if response.success:
    print(f"ウォッチモード開始: セッションID {response.session_id}")
    print("Ctrl+Cで終了します...")

    # セッション実行（ブロッキング）
    try:
        response.session.wait()
    except KeyboardInterrupt:
        print("\nウォッチモード終了")
else:
    print(f"エラー: {response.error_message}")
```

### 6.2 カスタムルールでのウォッチ
```python
# カスタムルール定義
custom_rules = {
    "dialogue_check": WatchRule(
        rule_id="custom-dialogue",
        name="会話文チェック",
        condition=WatchCondition(
            content_pattern=r'「.*」',  # 会話文を含む
            change_type=FileChangeType.MODIFIED
        ),
        actions=[
            WatchAction(
                action_type=ActionType.RUN_QUALITY_CHECK,
                parameters={
                    "categories": ["dialogue"],
                    "auto_fix_punctuation": True
                }
            )
        ]
    ),
    "long_sentence_alert": WatchRule(
        rule_id="custom-long-sentence",
        name="長文アラート",
        condition=WatchCondition(
            file_pattern="*.md"
        ),
        actions=[
            WatchAction(
                action_type=ActionType.ANALYZE_TEXT,
                parameters={
                    "check_sentence_length": True,
                    "max_length": 100
                }
            )
        ]
    )
}

# ルール設定
config = configure_watch_rules(
    project_id="novel-project-001",
    rules=custom_rules,
    save_as_default=True
)

# 簡易起動関数使用
session = start_watch_session(
    project_id="novel-project-001",
    auto_fix=True,
    notification_level=NotificationLevel.VERBOSE
)
```

### 6.3 統計情報の活用
```python
# セッション統計取得
stats = session.statistics

print(f"""
執筆統計レポート
================
総変更回数: {stats.total_changes}
修正ファイル数: {stats.files_modified}
品質チェック実行: {stats.quality_checks_run}
自動修正適用: {stats.auto_fixes_applied}
検出エラー: {stats.errors_found}
検出警告: {stats.warnings_found}
執筆文字数: {stats.total_characters_written}
アクティブ執筆時間: {stats.active_writing_time_seconds // 60}分
""")

# 時間当たりの執筆速度
if stats.active_writing_time_seconds > 0:
    chars_per_hour = (stats.total_characters_written /
                     stats.active_writing_time_seconds * 3600)
    print(f"執筆速度: {chars_per_hour:.0f}文字/時")
```

## 7. テスト仕様

### 7.1 単体テスト
```python
class TestWatchModeUseCase:
    def test_watch_session_creation(self):
        """ウォッチセッション作成テスト"""

    def test_file_change_detection(self):
        """ファイル変更検出テスト"""

    def test_incremental_check(self):
        """増分チェックテスト"""

    def test_notification_sending(self):
        """通知送信テスト"""

    def test_auto_fix_application(self):
        """自動修正適用テスト"""

    def test_statistics_update(self):
        """統計更新テスト"""
```

### 7.2 統合テスト
```python
class TestWatchModeIntegration:
    def test_full_watch_workflow(self):
        """完全ウォッチワークフローテスト"""

    def test_multiple_file_handling(self):
        """複数ファイル処理テスト"""

    def test_long_running_session(self):
        """長時間セッションテスト"""

    def test_error_recovery(self):
        """エラー復旧テスト"""
```

## 8. 設計原則遵守

### 8.1 DDD原則
- **エンティティ設計**: WatchSessionエンティティでセッション状態を管理
- **値オブジェクト**: FileChangeEvent、WatchConfigurationの不変性
- **ドメインサービス**: FileWatcherService、QualityCheckServiceの責務分離
- **イベント駆動**: ファイル変更イベントを中心とした設計

### 8.2 TDD原則
- **テスト駆動開発**: ファイル監視動作を先にテストで定義
- **モックファイルシステム**: テスト用仮想ファイルシステムで独立性確保
- **イベントシミュレーション**: 各種ファイル変更イベントのテストケース
- **非同期テスト**: 監視・通知の非同期処理テスト

## 9. 品質基準

### 9.1 パフォーマンス基準
- **監視遅延**: ファイル変更検出を100ms以内
- **チェック速度**: 増分チェックを1秒以内で完了
- **メモリ使用**: セッションあたり最大50MB
- **CPU使用率**: アイドル時1%以下

### 9.2 信頼性基準
- **イベント検出率**: 99.9%以上のファイル変更を検出
- **誤検出率**: 0.1%以下の誤検出
- **セッション継続性**: 24時間以上の安定動作
- **エラー復旧**: 自動復旧率95%以上

## 10. 実装メモ

### 10.1 実装ファイル
- **メインクラス**: `src/noveler/application/use_cases/start_file_watching_use_case.py`
- **テストファイル**: `tests/unit/application/use_cases/test_watch_mode_use_case.py`
- **統合テスト**: `tests/integration/test_watch_mode_workflow.py`

### 10.2 今後の改善点
- [ ] クラウド同期対応（複数デバイス間でのセッション共有）
- [ ] AIによる執筆パターン学習（個人最適化）
- [ ] 音声フィードバック（画面を見ずに品質確認）
- [ ] 協同執筆モード（複数人での同時監視）
- [ ] モバイルアプリ連携（スマートフォンへの通知）
