# DDD + TDD実装チェックリスト

**新機能開発時は必ずこのチェックリストを使用すること**

## 📋 実装前チェックリスト

### 🧠 Phase 1: ドメインモデリング（必須先行）

- [ ] **ビジネス要求分析完了**
  - 何のビジネス価値を提供するか明確化
  - ユーザーストーリー/要求仕様を特定

- [ ] **ドメインエンティティ特定**
  - 一意性を持つビジネス概念を特定
  - エンティティの状態遷移を設計
  - 不変条件（ビジネスルール）を定義

- [ ] **値オブジェクト特定**
  - 同一性を持たない概念を特定
  - 不変性を保証する設計

- [ ] **ドメインサービス特定**
  - エンティティや値オブジェクトに属さないビジネスロジックを特定

- [ ] **リポジトリ設計**
  - 永続化が必要なエンティティを特定
  - インターフェースをドメイン層で設計
  - 検索・保存・削除メソッドを定義

### 🔴 Phase 2: TDD RED段階

- [ ] **ドメインエンティティテスト作成**
  - `tests/test_domain_[機能名].py` 作成
  - ビジネスルールをテストで表現
  - エンティティの状態遷移テスト
  - 不変条件違反時の例外テスト

- [ ] **ユースケーステスト作成**
  - `tests/test_application_[機能名].py` 作成
  - モックリポジトリを使用
  - 正常系・異常系の両方をテスト

- [ ] **テスト失敗確認**
  - `pytest tests/test_domain_[機能名].py` で失敗確認
  - エラーメッセージが期待通りか確認

### 🟢 Phase 3: TDD GREEN段階

- [ ] **ドメイン層実装**
  - `domain/[コンテキスト]/entities.py` でエンティティ実装
  - ビジネスロジックを含むリッチなモデル
  - `domain/[コンテキスト]/repositories.py` でインターフェース定義

- [ ] **アプリケーション層実装**
  - `application/use_cases/[機能名].py` でユースケース実装
  - ドメインオブジェクトの調整のみ実行
  - ビジネスロジックは含まない

- [ ] **インフラ層実装**
  - `infrastructure/persistence/[実装名]_repository.py` で実装
  - ドメインインターフェースを実装
  - ファイルシステム/DB等への永続化

- [ ] **テスト成功確認**
  - 全ドメインテストが成功
  - 全アプリケーションテストが成功

### 🔵 Phase 4: アーキテクチャ整備

- [ ] **依存関係確認**
  - Domain ← Application ← Infrastructure の方向性確認
  - ドメイン層が他層に依存していないことを確認

- [ ] **統合テスト作成・実行**
  - `tests/test_integration_[機能名].py` 作成
  - 実際のファイルシステムを使用したテスト
  - エンドツーエンドシナリオテスト

- [ ] **DDD品質ゲート確認**
  - 以下の全項目をクリア

## 🔍 DDD品質ゲート（必須）

### ドメイン層チェック
- [ ] **エンティティがビジネスロジックを持つ**
  - データクラスではなく振る舞いを持つ
  - 状態遷移を制御するメソッドが存在
  - ビジネスルールを検証するメソッドが存在

- [ ] **値オブジェクトが不変**
  - `@dataclass(frozen=True)` または同等の実装
  - バリデーションロジックを含む

- [ ] **リポジトリインターフェースがドメイン層に定義**
  - `domain/[コンテキスト]/repositories.py` に存在
  - インフラ層に依存しない抽象化

### アプリケーション層チェック
- [ ] **ユースケースがドメインロジックを調整のみ**
  - ビジネスルールを含まない
  - ドメインオブジェクトのメソッド呼び出しのみ
  - 外部システムとの協調

### インフラ層チェック
- [ ] **技術的関心事のみを扱う**
  - ファイルI/O、DB接続等
  - ドメインインターフェースの実装
  - ドメインオブジェクトとの変換

### テストカバレッジチェック
- [ ] **ドメインロジックのテストカバレッジ90%以上**
- [ ] **ユースケースの重要パスをカバー**
- [ ] **統合テストでエンドツーエンドを確認**

## 🚫 よくある違反パターン（避けること）

### ❌ 貧血ドメインモデル
```python
# NG: データのみのエンティティ
@dataclass
class Episode:
    title: str
    content: str
    status: str  # 文字列で管理
```

### ✅ リッチドメインモデル
```python
# OK: ビジネスロジックを持つエンティティ
@dataclass
class Episode:
    title: EpisodeTitle
    content: str
    status: EpisodeStatus

    def can_publish(self) -> bool:
        """公開可能性をビジネスルールで判定"""
        return (self.status == EpisodeStatus.REVISED and
                len(self.content) >= 2000)
```

### ❌ レイヤー違反
```python
# NG: ドメイン層でファイルI/O
class Episode:
    def save_to_file(self):
        with open(f"{self.title}.md", "w") as f:
            f.write(self.content)
```

### ✅ 適切な責務分離
```python
# OK: リポジトリ経由でインフラ層に委譲
class EpisodeService:
    def save_episode(self, episode: Episode):
        self.repository.save(episode)  # インフラ層で実装
```

## 📚 参考実装

既存の適切なDDD実装例：
- `domain/writing/entities.py` - リッチなエンティティ
- `application/use_cases/create_episode_from_plot.py` - ユースケース
- `infrastructure/persistence/ddd_episode_repository.py` - リポジトリ実装
- `tests/test_ddd_writing_system.py` - DDD準拠テスト

**このチェックリストを印刷して手元に置き、実装時に必ず確認すること！**
