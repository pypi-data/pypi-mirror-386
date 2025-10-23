# SPEC-API-001: インフラストラクチャサービスのDDD実装

## 概要
レガシーなインフラストラクチャ機能をDDD設計に基づいて再実装する。Configuration管理、ファイルシステム操作、ロギング機能をドメインサービスとして抽象化し、TDDで実装する。

## 背景
現在のシステムには以下の問題がある：
- インフラストラクチャ層の実装が存在しない
- YAML設定ファイルの読み書きが未実装
- ファイル入出力処理が未実装
- ロギング処理が未実装

## 目的
- DDD原則に従ったインフラストラクチャサービスの実装
- ビジネスロジックからの技術的関心事の分離
- テスタブルで保守しやすい設計の実現

## 要件

### 機能要件
1. **Configuration管理**
   - YAML設定ファイルの読み込み
   - 設定の検証と型安全な取得
   - 階層的な設定の管理
   - デフォルト値のサポート

2. **ファイルシステム操作**
   - ファイルの読み書き
   - ディレクトリの作成・削除
   - ファイルの存在確認
   - エラーハンドリング

3. **ロギング**
   - ログレベルの管理（DEBUG, INFO, WARNING, ERROR, CRITICAL）
   - 構造化ログの出力
   - ファイルとコンソールへの出力
   - コンテキスト情報の付与

### 非機能要件
- テストカバレッジ90%以上
- 型安全性の確保
- 例外の適切なハンドリング
- ドメイン層からの依存性逆転

## 設計

### ドメインモデル

#### 値オブジェクト
```python
# ConfigurationKey: 設定キーを表す値オブジェクト
class ConfigurationKey:
    def __init__(self, key: str)
    def as_path_segments(self) -> List[str]
    def __str__(self) -> str

# FilePath: ファイルパスを表す値オブジェクト
class FilePath:
    def __init__(self, path: str)
    def exists(self) -> bool
    def is_absolute(self) -> bool
    def parent(self) -> FilePath
    def __str__(self) -> str

# LogLevel: ログレベルを表す値オブジェクト
class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
```

#### ドメインサービス
```python
# ConfigurationService: 設定管理のドメインサービス
class ConfigurationService:
    def load_configuration(self, file_path: FilePath) -> Dict[str, Any]
    def get_value(self, key: ConfigurationKey, default: Any = None) -> Any
    def validate_configuration(self, config: Dict[str, Any]) -> bool

# FileSystemService: ファイルシステム操作のドメインサービス
class FileSystemService:
    def read_file(self, file_path: FilePath) -> str
    def write_file(self, file_path: FilePath, content: str) -> None
    def create_directory(self, file_path: FilePath) -> None
    def delete_file(self, file_path: FilePath) -> None
    def list_files(self, directory: FilePath, pattern: str = "*") -> List[FilePath]

# LoggingService: ロギングのドメインサービス
class LoggingService:
    def log(self, level: LogLevel, message: str, context: Dict[str, Any] = None) -> None
    def debug(self, message: str, context: Dict[str, Any] = None) -> None
    def info(self, message: str, context: Dict[str, Any] = None) -> None
    def warning(self, message: str, context: Dict[str, Any] = None) -> None
    def error(self, message: str, context: Dict[str, Any] = None) -> None
    def critical(self, message: str, context: Dict[str, Any] = None) -> None
```

#### リポジトリインターフェース
```python
# ConfigurationRepository: 設定の永続化インターフェース
class ConfigurationRepository(ABC):
    @abstractmethod
    def load(self, file_path: FilePath) -> Dict[str, Any]

    @abstractmethod
    def save(self, file_path: FilePath, config: Dict[str, Any]) -> None

# LogRepository: ログの永続化インターフェース
class LogRepository(ABC):
    @abstractmethod
    def write_log(self, level: LogLevel, message: str, timestamp: datetime, context: Dict[str, Any]) -> None

    @abstractmethod
    def read_logs(self, start_date: datetime, end_date: datetime, level: Optional[LogLevel] = None) -> List[Dict[str, Any]]
```

### インフラストラクチャ層実装

#### アダプター実装
```python
# YamlConfigurationAdapter: YAML設定ファイルの読み書き実装
class YamlConfigurationAdapter(ConfigurationRepository):
    def load(self, file_path: FilePath) -> Dict[str, Any]
    def save(self, file_path: FilePath, config: Dict[str, Any]) -> None

# FileIOAdapter: ファイル入出力の実装
class FileIOAdapter:
    def read_text(self, file_path: FilePath) -> str
    def write_text(self, file_path: FilePath, content: str) -> None
    def ensure_directory(self, directory: FilePath) -> None

# FileLoggingAdapter: ファイルベースのログ実装
class FileLoggingAdapter(LogRepository):
    def write_log(self, level: LogLevel, message: str, timestamp: datetime, context: Dict[str, Any]) -> None
    def read_logs(self, start_date: datetime, end_date: datetime, level: Optional[LogLevel] = None) -> List[Dict[str, Any]]
```

## テストケース

### ユニットテスト
1. **ConfigurationKey値オブジェクト**
   - 有効なキーの作成
   - 無効なキーの拒否
   - パスセグメントへの変換

2. **FilePath値オブジェクト**
   - 有効なパスの作成
   - 相対パスと絶対パスの判定
   - 親ディレクトリの取得

3. **LogLevel値オブジェクト**
   - 各レベルの定義確認
   - 文字列変換

4. **ConfigurationService**
   - 設定ファイルの読み込み
   - 値の取得（存在する/しないキー）
   - デフォルト値の処理
   - 設定の検証

5. **FileSystemService**
   - ファイルの読み書き
   - ディレクトリの作成
   - ファイルの削除
   - ファイル一覧の取得

6. **LoggingService**
   - 各レベルでのログ出力
   - コンテキスト情報の付与
   - 構造化ログの生成

### 統合テスト
1. **設定管理フロー**
   - YAMLファイルからの設定読み込み
   - 設定の更新と保存
   - 設定の再読み込み

2. **ログ出力フロー**
   - ファイルへのログ出力
   - ログの読み込みとフィルタリング

## 実装順序
1. 値オブジェクトの実装とテスト
2. ドメインサービスインターフェースの定義
3. リポジトリインターフェースの定義
4. ドメインサービスの実装とテスト
5. インフラストラクチャ層アダプターの実装とテスト
6. 統合テストの実装

## 成功基準
- すべてのテストが通過すること
- テストカバレッジが90%以上であること
- 型チェックがエラーなく通過すること
- DDD原則に従った実装であること

## リスクと対策
- **リスク**: 既存コードとの互換性問題
- **対策**: アダプターパターンで段階的移行

## 関連仕様
- なし（新規実装）
