# 小説プロジェクト管理ユースケース仕様書

## 1. 概要

### 1.1 目的
DDD原則に基づき、小説プロジェクトの作成・管理・設定変更に関するビジネスロジックを実装する。プロジェクトのライフサイクル管理、メタデータ管理、ステータス管理を含む包括的なプロジェクト管理機能を提供。

### 1.2 スコープ
- 新規プロジェクトの作成・初期化
- プロジェクト設定の更新・管理
- プロジェクトステータスの管理・遷移
- プロジェクトメタデータの管理
- プロジェクトディレクトリ構造の管理
- プロジェクトのアーカイブ・復元

### 1.3 アーキテクチャ位置
```
Application Layer (Use Case)
├── ManagementUseCase                     ← Domain Layer
│   ├── CreateProjectRequest              └── Project (Entity)
│   ├── UpdateProjectRequest              └── ProjectFactory
│   ├── ProjectResponse                   └── ProjectStatus (Value Object)
│   ├── execute_create()                  └── ProjectRepository (Interface)
│   ├── execute_update()                  └── ProjectValidator (Service)
│   └── execute_archive()
└── Helper Functions
    ├── initialize_project_structure()
    └── validate_project_settings()
```

### 1.4 ビジネス価値
- **標準化されたプロジェクト管理**: 統一的なプロジェクト構造と管理プロセス
- **効率的な初期設定**: テンプレートベースの迅速なプロジェクト立ち上げ
- **柔軟な設定管理**: 動的なプロジェクト設定変更とメタデータ管理
- **安全なライフサイクル管理**: アーカイブ・復元による安全なプロジェクト管理

## 2. クラス設計

### 2.1 メインユースケースクラス
```python
class ManagementUseCase:
    """小説プロジェクト管理ユースケース"""

    def __init__(
        self,
        project_repository: ProjectRepository,
        file_system_adapter: FileSystemAdapter,
        template_service: TemplateService,
        validation_service: ValidationService
    ) -> None:
        """依存性注入による初期化"""
        self._project_repository = project_repository
        self._file_system = file_system_adapter
        self._template_service = template_service
        self._validation_service = validation_service
```

### 2.2 リクエスト・レスポンスクラス
```python
@dataclass(frozen=True)
class CreateProjectRequest:
    """プロジェクト作成リクエスト"""
    name: str
    author: str
    genre: str
    target_audience: str
    synopsis: str
    template_type: ProjectTemplateType = ProjectTemplateType.STANDARD
    metadata: dict[str, Any] = field(default_factory=dict)
    initial_settings: dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class UpdateProjectRequest:
    """プロジェクト更新リクエスト"""
    project_id: str
    name: str | None = None
    author: str | None = None
    genre: str | None = None
    target_audience: str | None = None
    synopsis: str | None = None
    settings: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class ProjectResponse:
    """プロジェクト操作レスポンス"""
    success: bool
    project: Project | None = None
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)
```

## 3. データ構造

### 3.1 Enums
```python
from enum import Enum, auto

class ProjectTemplateType(Enum):
    """プロジェクトテンプレートタイプ"""
    STANDARD = auto()        # 標準テンプレート
    FANTASY = auto()         # ファンタジー特化
    ROMANCE = auto()         # 恋愛特化
    MYSTERY = auto()         # ミステリー特化
    SCIFI = auto()          # SF特化
    CUSTOM = auto()          # カスタムテンプレート

class ProjectStatus(Enum):
    """プロジェクトステータス"""
    PLANNING = "企画中"
    WRITING = "執筆中"
    HIATUS = "休載中"
    COMPLETED = "完結"
    ARCHIVED = "アーカイブ済み"
    ABANDONED = "断念"

class DirectoryType(Enum):
    """ディレクトリタイプ"""
    PLANNING = "10_企画"
    PLOT = "20_プロット"
    SETTINGS = "30_設定集"
    MANUSCRIPT = "40_原稿"
    MANAGEMENT = "50_管理資料"
    BACKUP = "backup"
```

### 3.2 DataClasses
```python
@dataclass
class ProjectSettings:
    """プロジェクト設定"""
    quality_check_enabled: bool = True
    auto_backup_enabled: bool = True
    version_control_enabled: bool = True
    ai_assistance_enabled: bool = True
    notification_settings: NotificationSettings = field(default_factory=NotificationSettings)
    publishing_settings: PublishingSettings = field(default_factory=PublishingSettings)

@dataclass
class NotificationSettings:
    """通知設定"""
    deadline_reminder: bool = True
    quality_alert: bool = True
    backup_completion: bool = False
    publishing_reminder: bool = True

@dataclass
class PublishingSettings:
    """公開設定"""
    platform: str = "なろう"
    auto_publish: bool = False
    schedule_enabled: bool = False
    publish_days: list[str] = field(default_factory=list)
    publish_time: str = "20:00"
```

## 4. パブリックメソッド

### 4.1 プロジェクト作成
```python
def execute_create(self, request: CreateProjectRequest) -> ProjectResponse:
    """新規プロジェクト作成

    処理フロー:
    1. リクエスト検証
    2. プロジェクト名重複チェック
    3. プロジェクトエンティティ作成
    4. ディレクトリ構造初期化
    5. テンプレート適用
    6. 初期ファイル生成
    7. リポジトリ保存

    Args:
        request: プロジェクト作成リクエスト

    Returns:
        ProjectResponse: 作成結果
    """
```

### 4.2 プロジェクト更新
```python
def execute_update(self, request: UpdateProjectRequest) -> ProjectResponse:
    """プロジェクト設定更新

    処理フロー:
    1. プロジェクト存在確認
    2. 更新内容検証
    3. プロジェクトエンティティ更新
    4. 設定ファイル更新
    5. リポジトリ保存

    Args:
        request: プロジェクト更新リクエスト

    Returns:
        ProjectResponse: 更新結果
    """
```

### 4.3 プロジェクトアーカイブ
```python
def execute_archive(self, project_id: str, archive_reason: str = "") -> ProjectResponse:
    """プロジェクトアーカイブ

    処理フロー:
    1. プロジェクト存在確認
    2. アーカイブ可能性チェック
    3. バックアップ作成
    4. ステータス更新
    5. アーカイブ実行

    Args:
        project_id: プロジェクトID
        archive_reason: アーカイブ理由

    Returns:
        ProjectResponse: アーカイブ結果
    """
```

### 4.4 プロジェクトリストア
```python
def execute_restore(self, project_id: str) -> ProjectResponse:
    """プロジェクト復元

    処理フロー:
    1. アーカイブ存在確認
    2. 復元可能性チェック
    3. ディレクトリ復元
    4. ステータス更新
    5. 整合性確認

    Args:
        project_id: プロジェクトID

    Returns:
        ProjectResponse: 復元結果
    """
```

## 5. プライベートメソッド

### 5.1 検証メソッド
```python
def _validate_create_request(self, request: CreateProjectRequest) -> str | None:
    """作成リクエスト検証"""

def _check_project_name_duplication(self, name: str) -> bool:
    """プロジェクト名重複チェック"""

def _validate_project_settings(self, settings: dict[str, Any]) -> str | None:
    """プロジェクト設定検証"""
```

### 5.2 初期化メソッド
```python
def _initialize_directory_structure(self, project: Project) -> None:
    """ディレクトリ構造初期化"""

def _apply_template(self, project: Project, template_type: ProjectTemplateType) -> None:
    """テンプレート適用"""

def _create_initial_files(self, project: Project) -> None:
    """初期ファイル生成"""
```

### 5.3 ユーティリティメソッド
```python
def _create_project_entity(self, request: CreateProjectRequest) -> Project:
    """プロジェクトエンティティ作成"""

def _update_project_entity(self, project: Project, request: UpdateProjectRequest) -> Project:
    """プロジェクトエンティティ更新"""

def _create_backup(self, project: Project) -> str:
    """バックアップ作成"""
```

## 6. 依存関係

### 6.1 ドメイン層依存
- `Project`: プロジェクトエンティティ
- `ProjectFactory`: プロジェクトファクトリー
- `ProjectStatus`: プロジェクトステータス値オブジェクト
- `ProjectRepository`: プロジェクトリポジトリインターフェース
- `ProjectValidator`: プロジェクト検証サービス

### 6.2 インフラ層依存
- `FileSystemAdapter`: ファイルシステムアダプター
- `TemplateService`: テンプレートサービス
- `ValidationService`: 検証サービス

## 7. 設計原則遵守

### 7.1 DDD原則
- **エンティティの豊富なドメインモデル**: Projectエンティティにビジネスロジック集約
- **値オブジェクトの活用**: ProjectStatus, ProjectTemplateTypeなど
- **リポジトリパターン**: 永続化の抽象化
- **ドメインサービス**: ProjectValidatorによる複雑な検証ロジック

### 7.2 TDD原則
- **テストファースト**: 全機能にテストを先行作成
- **Red-Green-Refactor**: TDDサイクルの厳格な遵守
- **モックの活用**: 外部依存のモック化
- **高カバレッジ**: 90%以上のテストカバレッジ

## 8. 使用例

### 8.1 新規プロジェクト作成
```python
# リポジトリとサービスの準備
project_repository = YamlProjectRepository(base_path)
file_system = FileSystemAdapter()
template_service = TemplateService()
validation_service = ValidationService()

# ユースケース初期化
use_case = ManagementUseCase(
    project_repository,
    file_system,
    template_service,
    validation_service
)

# リクエスト作成
request = CreateProjectRequest(
    name="転生したら最強の魔法使いだった件",
    author="山田太郎",
    genre="ファンタジー",
    target_audience="10代後半～20代男性",
    synopsis="平凡なサラリーマンが異世界に転生し、最強の魔法使いとして活躍する物語",
    template_type=ProjectTemplateType.FANTASY,
    metadata={
        "keywords": ["転生", "魔法", "チート", "冒険"],
        "planned_episodes": 100,
        "update_frequency": "週3回"
    },
    initial_settings={
        "quality_check_enabled": True,
        "ai_assistance_enabled": True
    }
)

# 実行
response = use_case.execute_create(request)

if response.success:
    print(f"プロジェクト作成成功: {response.project.name}")
    print(f"プロジェクトID: {response.project.id}")
else:
    print(f"プロジェクト作成失敗: {response.message}")
```

### 8.2 プロジェクト設定更新
```python
# 更新リクエスト作成
update_request = UpdateProjectRequest(
    project_id="project-001",
    genre="ダークファンタジー",  # ジャンル変更
    settings={
        "quality_check_enabled": True,
        "auto_backup_enabled": True,
        "notification_settings": {
            "deadline_reminder": True,
            "quality_alert": True
        }
    },
    metadata={
        "status_note": "第2章から雰囲気を変更",
        "genre_change_reason": "読者の反応を見て方向転換"
    }
)

# 更新実行
response = use_case.execute_update(update_request)

if response.success:
    print(f"プロジェクト更新成功: {response.project.name}")
    print(f"新ジャンル: {response.project.genre}")
```

### 8.3 プロジェクトアーカイブ
```python
# アーカイブ実行
response = use_case.execute_archive(
    project_id="project-001",
    archive_reason="一時休載のため"
)

if response.success:
    print(f"アーカイブ成功: {response.details['archive_path']}")
    print(f"バックアップ: {response.details['backup_id']}")
```

## 9. エラーハンドリング

### 9.1 エラー分類
```python
class ProjectManagementError(Exception):
    """プロジェクト管理基底例外"""

class ProjectAlreadyExistsError(ProjectManagementError):
    """プロジェクト重複エラー"""

class ProjectNotFoundError(ProjectManagementError):
    """プロジェクト不存在エラー"""

class InvalidProjectSettingsError(ProjectManagementError):
    """無効な設定エラー"""

class ProjectArchiveError(ProjectManagementError):
    """アーカイブエラー"""
```

### 9.2 エラーメッセージ定義
```python
ERROR_MESSAGES = {
    "PROJECT_ALREADY_EXISTS": "プロジェクト名 '{name}' は既に存在します",
    "PROJECT_NOT_FOUND": "プロジェクトID '{project_id}' が見つかりません",
    "INVALID_PROJECT_NAME": "プロジェクト名は1文字以上50文字以下である必要があります",
    "INVALID_TEMPLATE_TYPE": "テンプレートタイプ '{template_type}' は無効です",
    "ARCHIVE_FAILED": "プロジェクトのアーカイブに失敗しました: {reason}",
    "RESTORE_FAILED": "プロジェクトの復元に失敗しました: {reason}",
    "DIRECTORY_CREATION_FAILED": "ディレクトリの作成に失敗しました: {path}",
    "SETTINGS_VALIDATION_FAILED": "設定の検証に失敗しました: {details}"
}
```

## 10. テスト観点

### 10.1 単体テスト
```python
class TestManagementUseCase:
    def test_create_project_success(self):
        """正常なプロジェクト作成"""

    def test_create_project_with_duplicate_name(self):
        """重複名でのプロジェクト作成"""

    def test_update_project_settings(self):
        """プロジェクト設定更新"""

    def test_archive_project(self):
        """プロジェクトアーカイブ"""

    def test_restore_archived_project(self):
        """アーカイブプロジェクト復元"""

    def test_invalid_project_name(self):
        """無効なプロジェクト名"""

    def test_template_application(self):
        """テンプレート適用"""
```

### 10.2 統合テスト
```python
class TestManagementIntegration:
    def test_full_project_lifecycle(self):
        """プロジェクトライフサイクル全体"""

    def test_concurrent_project_creation(self):
        """並行プロジェクト作成"""

    def test_file_system_integration(self):
        """ファイルシステム統合"""
```

## 11. 品質基準

### 11.1 パフォーマンス基準
- プロジェクト作成: 3秒以内
- プロジェクト更新: 1秒以内
- アーカイブ処理: 10秒以内（100話規模）

### 11.2 信頼性基準
- エラー率: 0.1%以下
- データ整合性: 100%保証
- バックアップ成功率: 99.9%以上

### 11.3 保守性基準
- コード複雑度: 10以下
- テストカバレッジ: 90%以上
- ドキュメント充実度: 全パブリックAPI文書化
