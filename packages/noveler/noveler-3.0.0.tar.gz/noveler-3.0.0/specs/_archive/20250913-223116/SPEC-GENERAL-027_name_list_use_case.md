# SPEC-GENERAL-027: 名前リスト管理ユースケース仕様書

## 1. 概要

### 1.1 目的
DDD原則に基づき、小説内で使用するキャラクター名・地名・組織名などの固有名詞を統合的に管理するビジネスロジックを実装する。名前の重複防止、一貫性保証、カテゴリ管理、使用履歴追跡を含む包括的な名前リスト管理機能を提供。

### 1.2 スコープ
- 固有名詞の登録・更新・削除・検索
- カテゴリ別名前管理（キャラクター、地名、組織、アイテム等）
- 名前の重複チェック・類似性検証
- 使用履歴・参照関係の追跡
- 名前の自動生成・提案機能
- エクスポート・インポート機能

### 1.3 アーキテクチャ位置
```
Application Layer (Use Case)
├── NameListUseCase                      ← Domain Layer
│   ├── RegisterNameRequest              └── NameEntry (Entity)
│   ├── UpdateNameRequest                └── NameCategory (Value Object)
│   ├── SearchNameRequest                └── NameUsage (Value Object)
│   ├── NameListResponse                 └── NameRepository (Interface)
│   ├── execute_register()               └── NameValidationService (Service)
│   ├── execute_search()                 └── NameSuggestionService (Service)
│   └── execute_analyze_usage()
└── Helper Functions
    ├── suggest_similar_names()
    └── generate_name_variations()
```

### 1.4 ビジネス価値
- **名前の一貫性保証**: 作品全体での固有名詞の統一性確保
- **重複・混乱の防止**: 類似名による読者の混乱を回避
- **効率的な名前管理**: 大規模作品での固有名詞管理を効率化
- **世界観の深化**: 体系的な命名による世界観の構築支援

## 2. クラス設計

### 2.1 メインユースケースクラス
```python
class NameListUseCase:
    """名前リスト管理ユースケース"""

    def __init__(
        self,
        name_repository: NameRepository,
        validation_service: NameValidationService,
        suggestion_service: NameSuggestionService,
        usage_tracker: UsageTracker
    ) -> None:
        """依存性注入による初期化"""
        self._name_repository = name_repository
        self._validation_service = validation_service
        self._suggestion_service = suggestion_service
        self._usage_tracker = usage_tracker
        self._name_cache = NameCache()
```

### 2.2 リクエスト・レスポンスクラス
```python
@dataclass(frozen=True)
class RegisterNameRequest:
    """名前登録リクエスト"""
    name: str
    category: NameCategory
    reading: str | None = None  # ふりがな
    description: str = ""
    attributes: dict[str, Any] = field(default_factory=dict)
    related_names: list[str] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)

@dataclass(frozen=True)
class UpdateNameRequest:
    """名前更新リクエスト"""
    name_id: str
    new_name: str | None = None
    reading: str | None = None
    description: str | None = None
    attributes: dict[str, Any] | None = None
    add_aliases: list[str] | None = None
    remove_aliases: list[str] | None = None

@dataclass(frozen=True)
class SearchNameRequest:
    """名前検索リクエスト"""
    query: str | None = None
    categories: list[NameCategory] | None = None
    attributes_filter: dict[str, Any] | None = None
    include_aliases: bool = True
    fuzzy_match: bool = False
    limit: int = 50

@dataclass(frozen=True)
class NameListResponse:
    """名前リスト操作レスポンス"""
    success: bool
    data: Any | None = None
    message: str = ""
    suggestions: list[NameSuggestion] = field(default_factory=list)
```

## 3. データ構造

### 3.1 Enums
```python
from enum import Enum, auto

class NameCategory(Enum):
    """名前カテゴリ"""
    CHARACTER_MAIN = "character_main"      # 主要キャラクター
    CHARACTER_SUB = "character_sub"        # サブキャラクター
    CHARACTER_MOB = "character_mob"        # モブキャラクター
    LOCATION_COUNTRY = "location_country"  # 国・地域
    LOCATION_CITY = "location_city"        # 都市・町
    LOCATION_LANDMARK = "location_landmark" # ランドマーク
    ORGANIZATION = "organization"          # 組織・団体
    ITEM_WEAPON = "item_weapon"           # 武器
    ITEM_MAGIC = "item_magic"             # 魔法・スキル
    ITEM_ARTIFACT = "item_artifact"       # アーティファクト
    CREATURE = "creature"                 # 生物・モンスター
    CUSTOM = "custom"                     # カスタム

class NameStatus(Enum):
    """名前ステータス"""
    ACTIVE = "active"           # 使用中
    DEPRECATED = "deprecated"   # 非推奨
    RESERVED = "reserved"       # 予約済み
    DELETED = "deleted"         # 削除済み

class ValidationLevel(Enum):
    """検証レベル"""
    STRICT = "strict"     # 厳格（完全一致も不可）
    NORMAL = "normal"     # 通常（類似警告）
    LENIENT = "lenient"   # 寛容（重複のみチェック）
```

### 3.2 DataClasses
```python
@dataclass
class NameEntry:
    """名前エントリ"""
    id: str
    name: str
    category: NameCategory
    reading: str | None
    description: str
    status: NameStatus
    attributes: dict[str, Any]
    aliases: list[str]
    related_names: list[str]
    created_at: datetime
    updated_at: datetime
    usage_count: int

@dataclass
class NameUsage:
    """名前使用情報"""
    name_id: str
    episode_number: int
    line_number: int
    context: str
    usage_type: str  # "mention", "dialogue", "description"
    timestamp: datetime

@dataclass
class NameSuggestion:
    """名前提案"""
    suggested_name: str
    category: NameCategory
    reason: str
    similarity_score: float
    base_pattern: str | None

@dataclass
class NameConflict:
    """名前競合情報"""
    existing_name: str
    new_name: str
    conflict_type: str  # "exact", "similar", "reading"
    similarity_score: float
    suggestion: str

@dataclass
class NameStatistics:
    """名前統計情報"""
    total_names: int
    by_category: dict[NameCategory, int]
    by_status: dict[NameStatus, int]
    most_used: list[tuple[str, int]]
    recently_added: list[NameEntry]
    unused_names: list[NameEntry]
```

## 4. パブリックメソッド

### 4.1 名前登録
```python
def execute_register(self, request: RegisterNameRequest) -> NameListResponse:
    """名前登録

    処理フロー:
    1. 名前フォーマット検証
    2. 重複・類似チェック
    3. カテゴリ別ルール適用
    4. 関連名検証
    5. エントリ作成
    6. リポジトリ保存
    7. キャッシュ更新

    Args:
        request: 名前登録リクエスト

    Returns:
        NameListResponse: 登録結果
    """
```

### 4.2 名前検索
```python
def execute_search(self, request: SearchNameRequest) -> NameListResponse:
    """名前検索

    処理フロー:
    1. 検索条件構築
    2. キャッシュチェック
    3. リポジトリ検索
    4. エイリアス展開
    5. ファジーマッチ適用
    6. 結果ソート
    7. ページング適用

    Args:
        request: 名前検索リクエスト

    Returns:
        NameListResponse: 検索結果
    """
```

### 4.3 名前更新
```python
def execute_update(self, request: UpdateNameRequest) -> NameListResponse:
    """名前更新

    処理フロー:
    1. 既存エントリ取得
    2. 更新内容検証
    3. 使用状況確認
    4. 影響範囲分析
    5. エントリ更新
    6. 関連更新伝播

    Args:
        request: 名前更新リクエスト

    Returns:
        NameListResponse: 更新結果
    """
```

### 4.4 使用状況分析
```python
def execute_analyze_usage(self, project_id: str) -> NameListResponse:
    """使用状況分析

    処理フロー:
    1. 全エピソード走査
    2. 名前使用箇所抽出
    3. 使用頻度集計
    4. 未使用名抽出
    5. 統計情報生成

    Args:
        project_id: プロジェクトID

    Returns:
        NameListResponse: 分析結果
    """
```

### 4.5 名前生成
```python
def execute_generate_names(self, category: NameCategory, count: int = 10) -> NameListResponse:
    """名前自動生成

    処理フロー:
    1. カテゴリ別パターン取得
    2. 既存名分析
    3. パターンベース生成
    4. 重複チェック
    5. 品質フィルタリング

    Args:
        category: 名前カテゴリ
        count: 生成数

    Returns:
        NameListResponse: 生成された名前リスト
    """
```

## 5. プライベートメソッド

### 5.1 検証メソッド
```python
def _validate_name_format(self, name: str, category: NameCategory) -> str | None:
    """名前フォーマット検証"""

def _check_duplication(self, name: str, category: NameCategory) -> list[NameConflict]:
    """重複チェック"""

def _check_similarity(self, name: str, threshold: float = 0.8) -> list[NameConflict]:
    """類似性チェック"""
```

### 5.2 分析メソッド
```python
def _analyze_name_pattern(self, names: list[str]) -> dict[str, Any]:
    """名前パターン分析"""

def _calculate_similarity_score(self, name1: str, name2: str) -> float:
    """類似度スコア計算"""

def _extract_usage_context(self, content: str, name: str) -> list[NameUsage]:
    """使用コンテキスト抽出"""
```

### 5.3 生成メソッド
```python
def _generate_by_pattern(self, pattern: str, count: int) -> list[str]:
    """パターンベース名前生成"""

def _apply_category_rules(self, names: list[str], category: NameCategory) -> list[str]:
    """カテゴリルール適用"""

def _filter_quality(self, names: list[str]) -> list[str]:
    """品質フィルタリング"""
```

## 6. 依存関係

### 6.1 ドメイン層依存
- `NameEntry`: 名前エントリエンティティ
- `NameCategory`: 名前カテゴリ値オブジェクト
- `NameUsage`: 名前使用情報値オブジェクト
- `NameRepository`: 名前リポジトリインターフェース
- `NameValidationService`: 名前検証ドメインサービス
- `NameSuggestionService`: 名前提案ドメインサービス

### 6.2 インフラ層依存
- `UsageTracker`: 使用状況追跡サービス
- `NameCache`: 名前キャッシュ
- `TextAnalyzer`: テキスト分析サービス

## 7. 設計原則遵守

### 7.1 DDD原則
- **エンティティ設計**: NameEntryに名前管理ロジック集約
- **値オブジェクト活用**: NameCategory, NameUsageの不変性
- **ドメインサービス**: 複雑な検証・提案ロジックの分離
- **ユビキタス言語**: 小説執筆領域の用語統一

### 7.2 TDD原則
- **境界値テスト**: 名前長、類似度閾値のテスト
- **エッジケース**: 特殊文字、多言語対応テスト
- **モックオブジェクト**: 外部サービス依存の分離
- **回帰テスト**: 名前変更の影響範囲テスト

## 8. 使用例

### 8.1 キャラクター名登録
```python
# ユースケース初期化
use_case = NameListUseCase(
    name_repository,
    validation_service,
    suggestion_service,
    usage_tracker
)

# 主人公登録
request = RegisterNameRequest(
    name="鈴木太郎",
    category=NameCategory.CHARACTER_MAIN,
    reading="すずきたろう",
    description="本作の主人公。異世界に転生した元サラリーマン",
    attributes={
        "age": 26,
        "gender": "male",
        "role": "protagonist",
        "abilities": ["剣術", "魔法"],
        "affiliation": "冒険者ギルド"
    },
    aliases=["太郎", "勇者様"],
    related_names=["鈴木花子", "山田次郎"]
)

response = use_case.execute_register(request)

if response.success:
    print(f"登録成功: {response.data['name_id']}")
else:
    print(f"登録失敗: {response.message}")
    if response.suggestions:
        print("提案:")
        for suggestion in response.suggestions:
            print(f"  - {suggestion.suggested_name}: {suggestion.reason}")
```

### 8.2 名前検索
```python
# ファジー検索でキャラクターを探す
search_request = SearchNameRequest(
    query="たろう",
    categories=[NameCategory.CHARACTER_MAIN, NameCategory.CHARACTER_SUB],
    fuzzy_match=True,
    include_aliases=True,
    limit=10
)

response = use_case.execute_search(search_request)

if response.success:
    results = response.data['results']
    print(f"検索結果: {len(results)}件")
    for entry in results:
        print(f"- {entry.name} ({entry.reading})")
        print(f"  カテゴリ: {entry.category.value}")
        print(f"  使用回数: {entry.usage_count}")
```

### 8.3 使用状況分析
```python
# プロジェクト全体の名前使用状況を分析
response = use_case.execute_analyze_usage("project-001")

if response.success:
    stats = response.data['statistics']
    print(f"総登録名: {stats.total_names}")
    print("\nカテゴリ別:")
    for category, count in stats.by_category.items():
        print(f"  {category.value}: {count}")

    print("\n最頻出TOP5:")
    for name, count in stats.most_used[:5]:
        print(f"  {name}: {count}回")

    print(f"\n未使用名: {len(stats.unused_names)}個")
```

### 8.4 名前自動生成
```python
# ファンタジー風の地名を生成
response = use_case.execute_generate_names(
    category=NameCategory.LOCATION_CITY,
    count=20
)

if response.success:
    generated_names = response.data['names']
    print("生成された地名:")
    for name in generated_names:
        print(f"  - {name}")
```

## 9. エラーハンドリング

### 9.1 エラー分類
```python
class NameListError(Exception):
    """名前リスト管理基底例外"""

class NameDuplicationError(NameListError):
    """名前重複エラー"""

class NameValidationError(NameListError):
    """名前検証エラー"""

class NameNotFoundError(NameListError):
    """名前不存在エラー"""

class NameUsageConflictError(NameListError):
    """名前使用競合エラー"""
```

### 9.2 エラーメッセージ定義
```python
ERROR_MESSAGES = {
    "NAME_ALREADY_EXISTS": "名前 '{name}' は既に登録されています（カテゴリ: {category}）",
    "SIMILAR_NAME_EXISTS": "類似した名前が存在します: '{existing}' (類似度: {score:.2f})",
    "INVALID_NAME_FORMAT": "名前の形式が無効です: {reason}",
    "NAME_NOT_FOUND": "名前が見つかりません: ID '{name_id}'",
    "NAME_IN_USE": "この名前は {usage_count} 箇所で使用されています",
    "CATEGORY_RULE_VIOLATION": "カテゴリ '{category}' のルールに違反しています: {rule}",
    "GENERATION_FAILED": "名前の生成に失敗しました: {reason}"
}
```

## 10. テスト観点

### 10.1 単体テスト
```python
class TestNameListUseCase:
    def test_register_unique_name(self):
        """ユニークな名前の登録"""

    def test_detect_duplicate_name(self):
        """重複名の検出"""

    def test_detect_similar_names(self):
        """類似名の検出"""

    def test_search_with_fuzzy_match(self):
        """ファジー検索"""

    def test_update_name_with_usage(self):
        """使用中の名前更新"""

    def test_generate_category_names(self):
        """カテゴリ別名前生成"""
```

### 10.2 統合テスト
```python
class TestNameListIntegration:
    def test_full_name_lifecycle(self):
        """名前のライフサイクル全体"""

    def test_cross_project_name_management(self):
        """プロジェクト横断名前管理"""

    def test_bulk_import_export(self):
        """大量インポート・エクスポート"""

    def test_concurrent_name_operations(self):
        """並行名前操作"""
```

## 11. 品質基準

### 11.1 パフォーマンス基準
- 名前登録: 100ms以内
- 検索処理: 200ms以内（1000件）
- 使用状況分析: 5秒以内（100話規模）

### 11.2 信頼性基準
- 重複検出率: 100%
- 類似検出精度: 95%以上
- データ整合性: 100%保証

### 11.3 保守性基準
- カテゴリ追加: 既存コード変更最小
- テストカバレッジ: 90%以上
- API後方互換性: 100%維持
