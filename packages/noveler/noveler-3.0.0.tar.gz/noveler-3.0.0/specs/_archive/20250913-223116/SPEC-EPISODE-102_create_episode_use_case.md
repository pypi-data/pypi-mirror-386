# SPEC-EPISODE-102: エピソード作成ユースケース仕様書

## SPEC-EPISODE-015: エピソード作成ユースケース


## 1. 概要

### 1.1 目的
DDD原則に基づき、新規エピソードの作成に関するビジネスロジックを実装する。エピソード番号の重複チェック、初期品質評価、メタデータ管理を含む包括的なエピソード作成機能を提供。

### 1.2 スコープ
- 新規エピソードの作成・検証・永続化
- ビジネスルールに基づく重複チェック・妥当性検証
- テンプレートベースのエピソード作成
- 自動番号付きエピソード作成
- 初期品質スコア計算・品質記録連携
- エラーハンドリング・レスポンス管理

### 1.3 アーキテクチャ位置
```
Application Layer (Use Case)
├── CreateEpisodeUseCase                    ← Domain Layer
│   ├── CreateEpisodeRequest               └── Episode (Entity)
│   ├── CreateEpisodeResponse              └── EpisodeFactory
│   └── execute()                          └── EpisodeNumber, QualityScore (Value Objects)
└── Helper Functions                        └── EpisodeRepository, ProjectRepository (Interfaces)
    ├── create_episode_from_template()
    └── create_episode_with_auto_numbering()
```

### 1.4 ビジネス価値
- **一貫したエピソード作成**: 標準化されたエピソード作成プロセス
- **品質の早期確保**: 作成時の初期品質評価による品質向上
- **作業効率の向上**: テンプレート・自動番号付きによる効率化
- **データ整合性**: 重複防止・妥当性検証による信頼性確保

## 2. 機能仕様

### 2.1 コアユースケース
```python
class CreateEpisodeUseCase:
    def __init__(
        self,
        episode_repository: EpisodeRepository,
        project_repository: ProjectRepository,
        quality_repository: Any = None  # オプショナル
    ) -> None:
        """依存性注入による初期化"""

    def execute(self, request: CreateEpisodeRequest) -> CreateEpisodeResponse:
        """エピソード作成メイン処理"""
```

### 2.2 リクエスト・レスポンス
```python
@dataclass(frozen=True)
class CreateEpisodeRequest:
    """エピソード作成リクエスト"""
    project_id: str
    episode_number: int
    title: str
    target_words: int
    initial_content: str = ""
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class CreateEpisodeResponse:
    """エピソード作成レスポンス"""
    success: bool
    episode: Episode | None = None
    error_message: str | None = None

    @classmethod
    def success_response(cls, episode: Episode) -> CreateEpisodeResponse

    @classmethod
    def error_response(cls, error_message: str) -> CreateEpisodeResponse
```

### 2.3 検証機能
```python
def _validate_request(self, request: CreateEpisodeRequest) -> CreateEpisodeResponse:
    """リクエスト基本検証（プロジェクト存在確認等）"""

def _validate_business_rules(self, request: CreateEpisodeRequest) -> str | None:
    """ビジネスルール検証（重複チェック等）"""
```

### 2.4 エピソード生成機能
```python
def _create_episode_entity(self, request: CreateEpisodeRequest) -> Episode:
    """エピソードエンティティ作成"""

def _calculate_quality_score(self, content: str) -> QualityScore:
    """初期品質スコア計算"""
```

### 2.5 ヘルパー関数
```python
def create_episode_from_template(
    project_id: str,
    template: dict[str, Any],
    episode_repository: EpisodeRepository,
    project_repository: ProjectRepository,
) -> CreateEpisodeResponse:
    """テンプレートからエピソード作成"""

def create_episode_with_auto_numbering(
    project_id: str,
    title: str,
    target_words: int,
    episode_repository: EpisodeRepository,
    project_repository: ProjectRepository,
    initial_content: str = "",
    tags: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> CreateEpisodeResponse:
    """自動番号付きエピソード作成"""
```

## 3. ビジネスルール仕様

### 3.1 前提条件検証
- **プロジェクト存在確認**: 指定されたプロジェクトIDが存在すること
- **リクエスト妥当性**: 必須フィールドが適切に設定されていること
- **パラメーター範囲**: エピソード番号・目標文字数が有効範囲内であること

### 3.2 ビジネスルール検証
- **エピソード番号重複防止**: 同一プロジェクト内でのエピソード番号重複チェック
- **タイトル制約**: タイトルの文字数・内容制限
- **目標文字数制約**: 目標文字数の妥当範囲（例：500-10000文字）

### 3.3 品質初期評価ルール
```python
def _calculate_quality_score(self, content: str) -> QualityScore:
    """品質スコア計算ロジック

    文字数ベース:
    - 1000文字未満: 50点
    - 1000-2000文字: 70点
    - 2000-3000文字: 80点
    - 3000文字以上: 85点

    内容多様性ボーナス:
    - 対話含有: +5点
    - 描写含有: +5点

    最大100点制限
    """
```

## 4. データ構造仕様

### 4.1 リクエストデータ構造
```python
# 基本的なエピソード作成リクエスト
request_example = CreateEpisodeRequest(
    project_id="project-001",
    episode_number=1,
    title="異世界転生",
    target_words=3000,
    initial_content="俺の名前は田中太郎、26歳の平凡なサラリーマンだった...",
    tags=["ファンタジー", "転生", "チート"],
    metadata={
        "genre": "ファンタジー",
        "mood": "コメディ",
        "difficulty": "初級",
        "estimated_time": 120,
        "reference_materials": ["世界観設定書", "キャラクター一覧"]
    }
)
```

### 4.2 レスポンスデータ構造
```python
# 成功レスポンス
success_response_example = CreateEpisodeResponse(
    success=True,
    episode=Episode(
        number=EpisodeNumber(1),
        title=EpisodeTitle("異世界転生"),
        content="俺の名前は田中太郎...",
        target_words=WordCount(3000)
    ),
    error_message=None
)

# エラーレスポンス
error_response_example = CreateEpisodeResponse(
    success=False,
    episode=None,
    error_message="エピソード番号1は既に存在します"
)
```

### 4.3 テンプレートデータ構造
```python
# エピソードテンプレート
template_example = {
    "number": 1,
    "title": "異世界転生",
    "target_words": 3000,
    "initial_content": "## プロローグ\n\n俺の名前は...",
    "tags": ["ファンタジー", "転生"],
    "metadata": {
        "chapter": 1,
        "arc": "序章",
        "pov": "主人公",
        "location": "異世界",
        "time_period": "導入部",
        "key_characters": ["田中太郎", "女神"],
        "plot_points": ["転生", "チート能力獲得", "世界観説明"],
        "foreshadowing": ["魔王の存在", "隠された過去"],
        "themes": ["成長", "友情", "冒険"]
    }
}
```

## 5. エラーハンドリング仕様

### 5.1 エラー分類
```python
# ドメイン例外
try:
    # エピソード作成処理
except DomainException as e:
    return CreateEpisodeResponse.error_response(str(e))

# バリデーション例外
except ValueError as e:
    return CreateEpisodeResponse.error_response(
        f"エピソード作成中にエラーが発生しました: {e!s}"
    )

# 予期しない例外
except Exception as e:
    return CreateEpisodeResponse.error_response(
        f"エピソード作成中にエラーが発生しました: {e!s}"
    )
```

### 5.2 具体的エラーメッセージ
```python
ERROR_MESSAGES = {
    "PROJECT_NOT_FOUND": "プロジェクトが存在しません: {project_id}",
    "EPISODE_NUMBER_EXISTS": "エピソード番号{episode_number}は既に存在します",
    "INVALID_EPISODE_NUMBER": "エピソード番号は1以上である必要があります",
    "INVALID_TITLE": "タイトルは1文字以上100文字以下である必要があります",
    "INVALID_TARGET_WORDS": "目標文字数は500文字以上10000文字以下である必要があります",
    "REPOSITORY_ERROR": "データ保存中にエラーが発生しました: {error}",
    "QUALITY_CALCULATION_ERROR": "品質スコア計算中にエラーが発生しました: {error}"
}
```

## 6. 使用例

### 6.1 基本的なエピソード作成
```python
# リポジトリ準備
episode_repository = YamlEpisodeRepository(project_path)
project_repository = YamlProjectRepository(base_path)

# ユースケース初期化
use_case = CreateEpisodeUseCase(episode_repository, project_repository)

# リクエスト作成
request = CreateEpisodeRequest(
    project_id="novel-project-001",
    episode_number=1,
    title="異世界転生",
    target_words=3000,
    initial_content="俺の名前は田中太郎、26歳の平凡なサラリーマンだった...",
    tags=["ファンタジー", "転生"],
    metadata={"chapter": 1, "arc": "序章"}
)

# エピソード作成実行
response = use_case.execute(request)

if response.success:
    print(f"エピソード作成成功: {response.episode.title}")
else:
    print(f"エピソード作成失敗: {response.error_message}")
```

### 6.2 テンプレートベース作成
```python
# テンプレート定義
template = {
    "number": 1,
    "title": "プロローグ - 異世界への扉",
    "target_words": 2500,
    "initial_content": "## プロローグ\n\n突然の光に包まれた俺は...",
    "tags": ["ファンタジー", "転生", "プロローグ"],
    "metadata": {
        "chapter": 0,
        "arc": "導入",
        "importance": "high"
    }
}

# テンプレートからエピソード作成
response = create_episode_from_template(
    project_id="novel-project-001",
    template=template,
    episode_repository=episode_repository,
    project_repository=project_repository
)
```

### 6.3 自動番号付き作成
```python
# 自動番号付きでエピソード作成（連載用）
response = create_episode_with_auto_numbering(
    project_id="novel-project-001",
    title="魔法学校入学",
    target_words=3200,
    episode_repository=episode_repository,
    project_repository=project_repository,
    initial_content="入学式の朝、俺は緊張していた...",
    tags=["学園", "魔法", "友情"]
)
```

## 7. テスト仕様

### 7.1 単体テスト
```python
class TestCreateEpisodeUseCase:
    def test_successful_episode_creation(self):
        """正常なエピソード作成テスト"""

    def test_duplicate_episode_number_validation(self):
        """重複エピソード番号検証テスト"""

    def test_project_not_found_validation(self):
        """存在しないプロジェクト検証テスト"""

    def test_quality_score_calculation(self):
        """品質スコア計算テスト"""

    def test_template_based_creation(self):
        """テンプレートベース作成テスト"""

    def test_auto_numbering_creation(self):
        """自動番号付き作成テスト"""
```

### 7.2 統合テスト
```python
class TestCreateEpisodeIntegration:
    def test_full_creation_workflow(self):
        """完全作成ワークフローテスト"""

    def test_repository_integration(self):
        """リポジトリ統合テスト"""

    def test_concurrent_creation(self):
        """並行作成テスト"""
```

## 8. 実装メモ

### 8.1 実装ファイル
- **メインクラス**: `scripts/application/use_cases/create_episode_use_case.py`
- **テストファイル**: `tests/unit/application/use_cases/test_create_episode_use_case.py`
- **統合テスト**: `tests/integration/test_create_episode_workflow.py`

### 8.2 設計方針
- **DDD原則の厳格遵守**: アプリケーション層でのビジネスロジック集約
- **単一責任原則**: エピソード作成のみに特化した設計
- **依存性注入**: テスタブルで拡張可能なアーキテクチャ
- **不変オブジェクト**: Request/Response の不変性による安全性確保

### 8.3 今後の改善点
- [ ] 非同期エピソード作成（大量作成時のパフォーマンス向上）
- [ ] AI による初期品質スコア精度向上
- [ ] テンプレートエンジンとの統合（高度なテンプレート処理）
- [ ] バージョン管理システムとの連携（自動コミット機能）
- [ ] リアルタイム協業機能（複数ユーザーによる共同作成）
