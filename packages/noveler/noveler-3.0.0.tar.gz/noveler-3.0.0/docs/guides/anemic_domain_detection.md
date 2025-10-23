# ドメインモデル貧血症の自動検知

## 概要

このガイドでは、pre-commit hookを使用してドメインモデル貧血症（Anemic Domain Model）アンチパターンを機械的に検知する仕組みについて説明します。

## ドメインモデル貧血症とは

ドメインモデル貧血症とは、ドメイン層のEntity/Value Objectがデータ構造だけを持ち、ビジネスロジックを持たない状態を指します。これはDDD（Domain-Driven Design）のアンチパターンです。

### 典型的な症状

1. **データクラスのみのEntity**
   ```python
   # ❌ 貧血症: ビジネスロジックがない
   @dataclass
   class Episode:
       episode_number: int
       title: str
       content: str
       status: str
   ```

2. **バリデーションなしのValue Object**
   ```python
   # ❌ 貧血症: 不変性・バリデーションの保証がない
   @dataclass
   class EpisodeNumber:
       value: int
   ```

3. **Service層へのロジック集中**
   ```python
   # ❌ 貧血症: ドメインロジックがServiceに漏れている
   class EpisodeService:
       def validate_episode_number(self, episode: Episode) -> bool:
           return 1 <= episode.episode_number <= 9999
   ```

### 正しいドメインモデル

```python
# ✅ 豊かなドメインモデル: ビジネスロジックをカプセル化
@dataclass
class Episode:
    episode_number: int
    title: str
    content: str
    status: str

    def __post_init__(self):
        """バリデーション"""
        if not 1 <= self.episode_number <= 9999:
            raise ValueError(f"Invalid episode number: {self.episode_number}")

    def complete(self) -> None:
        """ビジネスロジック: 完了状態に遷移"""
        if self.status == "completed":
            raise ValueError("Episode is already completed")
        self.status = "completed"

    def is_draft(self) -> bool:
        """ビジネスロジック: 下書き状態か判定"""
        return self.status == "draft"
```

## 検知パターン

### パターン1: ANEMIC_DATACLASS

**検知条件**:
- `@dataclass` デコレータがある
- ビジネスロジックメソッドが1つもない
- `__post_init__`, `__eq__`, `__hash__` もない

**対処法**:
```python
# Before
@dataclass
class Episode:
    episode_number: int
    title: str

# After
@dataclass
class Episode:
    episode_number: int
    title: str

    def __post_init__(self):
        if not self.title:
            raise ValueError("Title cannot be empty")

    def is_valid(self) -> bool:
        return 1 <= self.episode_number <= 9999
```

### パターン2: NO_VALIDATION

**検知条件**:
- Value Object層 (`/domain/value_objects/`) にある
- `__post_init__` バリデーションがない
- `__eq__` 等価性チェックもない

**対処法**:
```python
# Before
@dataclass
class EpisodeNumber:
    value: int

# After
@dataclass
class EpisodeNumber:
    value: int

    def __post_init__(self):
        if not 1 <= self.value <= 9999:
            raise ValueError(f"Invalid episode number: {self.value}")

    def __eq__(self, other):
        if not isinstance(other, EpisodeNumber):
            return False
        return self.value == other.value

    def __hash__(self):
        return hash(self.value)
```

## 検知対象外

以下のクラスは検知対象外として除外されます:

1. **Enumクラス**: `class ErrorSeverity(Enum):`
2. **プロトコル/インターフェース**: `class IEpisodeRepository:` または `class SomeProtocol:`
3. **テストフィクスチャ**: `tests/fixtures/domain/` 配下

## Pre-commit Hook統合

### 設定 (`.pre-commit-config.yaml`)

```yaml
- id: anemic-domain-check
  name: Anemic Domain Model Check
  entry: python scripts/hooks/check_anemic_domain.py
  language: system
  pass_filenames: false
  stages: [pre-commit]
  files: '^src/noveler/domain/(entities|value_objects)/.*\.py$'
```

### 動作

コミット時に自動的にチェックされます:

```bash
$ git commit -m "Add new Episode entity"
Anemic Domain Model Check................................................Failed
- hook id: anemic-domain-check
- exit code: 1

[ERROR] Anemic Domain Model detected:

File: src/noveler/domain/entities/episode.py
  [ANEMIC_DATACLASS] Class 'Episode' is a dataclass with no business logic methods.
  Consider adding validation or domain behavior methods.

Hints:
  - Add business logic methods to Entity classes
  - Add validation in __post_init__ for Value Objects
  - Move logic from Service layer to Domain layer
```

### 手動実行

特定のファイルをチェック:

```bash
python scripts/hooks/check_anemic_domain.py
```

全ファイルをチェック:

```bash
pre-commit run anemic-domain-check --all-files
```

## テスト

診断スクリプトで精度を確認できます:

```bash
python scripts/diagnostics/test_anemic_detection.py
```

出力例:
```
=== Anemic Domain Detection Test ===

[PASS] src/noveler/domain/value_objects/episode_number.py - Expected: OK, Got: OK
[PASS] src/noveler/domain/value_objects/error_response.py - Expected: OK, Got: OK
[PASS] src/noveler/domain/entities/episode_prompt.py - Expected: OK, Got: OK

=== Summary ===
Passed: 3/3
Failed: 0/3
```

## ベストプラクティス

### 1. Tell, Don't Ask原則

```python
# ❌ Bad: Serviceがドメインロジックを持つ
if episode.status == "draft":
    episode.status = "published"

# ✅ Good: Entityがドメインロジックを持つ
episode.publish()
```

### 2. Value Objectの不変性

```python
# ✅ Good: frozen=Trueで不変性を保証
@dataclass(frozen=True)
class EpisodeNumber:
    value: int

    def __post_init__(self):
        if not 1 <= self.value <= 9999:
            raise ValueError(f"Invalid episode number: {self.value}")
```

### 3. ファクトリメソッド

```python
@dataclass
class Episode:
    episode_number: int
    status: str

    @classmethod
    def create_draft(cls, episode_number: int) -> "Episode":
        """下書きエピソードを作成"""
        return cls(episode_number=episode_number, status="draft")

    @classmethod
    def create_published(cls, episode_number: int) -> "Episode":
        """公開済みエピソードを作成"""
        return cls(episode_number=episode_number, status="published")
```

## 参考資料

- **Martin Fowler: Anemic Domain Model**: https://martinfowler.com/bliki/AnemicDomainModel.html
- **DDD原則**: `docs/ddd/ddd_principles.md`
- **検知スクリプト**: `scripts/hooks/check_anemic_domain.py`
- **診断スクリプト**: `scripts/diagnostics/test_anemic_detection.py`

## トラブルシューティング

### Q: 誤検知された場合

**A**: 以下のいずれかの方法で対処:

1. ビジネスロジックメソッドを追加（推奨）
2. 最低限 `__post_init__` バリデーションを追加
3. データ転送用オブジェクトなら、Domain層から移動（`application/dtos/` など）

### Q: Windowsでエンコーディングエラーが出る

**A**: スクリプトは絵文字を使用しないように修正済みです。最新版を使用してください。

### Q: パフォーマンスへの影響は？

**A**: AST解析のみで実行ファイル不要のため、影響は最小限です（通常 < 1秒）。

---

## Service Logic Smell Check（補完機能）

### 概要

Anemic Domain Detectionに加えて、**Service層への業務ロジック漏出**を検知する補完的なチェック機能です。

ドメイン貧血症の根本原因は「業務ロジックがServiceに流出している」ことにあります。Service Logic Smell Checkは、この症状を直接検知します。

### 検知パターン

#### Pattern 1: Tell Don't Ask違反

```python
# ❌ Bad: ServiceがEntityのプロパティをチェックして処理
class EpisodeUseCase:
    def publish_episode(self, episode: Episode) -> None:
        if episode.status == "draft":  # ← Tell Don't Ask違反
            episode.status = "published"
```

**修正**:
```python
# ✅ Good: Entityがドメインロジックを持つ
class Episode:
    def publish(self) -> None:
        if self.status != "draft":
            raise ValueError("Only draft episodes can be published")
        self.status = "published"

class EpisodeUseCase:
    def publish_episode(self, episode: Episode) -> None:
        episode.publish()  # ← Entityに委譲
```

#### Pattern 2: 直接変更（Direct Mutation）

```python
# ❌ Bad: ServiceがEntityの内部状態を直接変更
class EpisodeUseCase:
    def update_title(self, episode: Episode, new_title: str) -> None:
        episode.title = new_title  # ← 直接変更
        episode.updated_at = datetime.now()
```

**修正**:
```python
# ✅ Good: Entityがメソッドで変更をカプセル化
class Episode:
    def update_title(self, new_title: str) -> None:
        if not new_title:
            raise ValueError("Title cannot be empty")
        self.title = new_title
        self.updated_at = datetime.now()

class EpisodeUseCase:
    def update_title(self, episode: Episode, new_title: str) -> None:
        episode.update_title(new_title)  # ← Entityに委譲
```

### Pre-commit Hook統合

#### 設定 (`.pre-commit-config.yaml`)

```yaml
- id: service-logic-smell-check
  name: Service Logic Smell Check (WARNING mode)
  entry: bash -c 'python scripts/hooks/check_service_logic_smell.py || { echo "[WARNING] Service Logic Smell detected (non-blocking)"; exit 0; }'
  language: system
  pass_filenames: false
  stages: [pre-commit]
  files: '^src/noveler/application/use_cases/.*\.py$'
```

**特徴**:
- **WARNING扱い**: 検知してもコミットはブロックしない（警告のみ）
- **対象**: `application/use_cases/` 層のみ
- **目的**: 段階的な改善促進（強制ではない）

#### 動作

コミット時に警告表示:

```bash
$ git commit -m "Add episode use case"
Service Logic Smell Check (WARNING mode)................................Failed
- hook id: service-logic-smell-check

[WARNING] Service Logic Smell detected (non-blocking)

File: src/noveler/application/use_cases/episode_use_case.py
  Line 42: if episode.status == "draft":
  [DOMAIN_PROPERTY_CHECK] Avoid checking domain properties directly (Tell, Don't Ask).

  Line 45: episode.title = new_title
  [DIRECT_ENTITY_MUTATION] Avoid direct entity mutation. Use a method instead.

Hints:
  - Move business logic from Service to Domain layer
  - Use Entity methods instead of direct property access
  - Follow "Tell, Don't Ask" principle

[INFO] This is a WARNING (non-blocking). Commit will proceed.
```

### 除外パターン

以下のパターンは**正当な使用**として除外されます:

1. **リクエスト検証**: `if not request.episode_number:`
2. **Repositoryへの問い合わせ**: `if repository.exists(episode_id):`
3. **ファクトリメソッド呼び出し**: `episode = Episode.create_draft(...)`
4. **DTOマッピング**: `response = EpisodeResponse(title=episode.title)`

### 手動実行

```bash
# 特定のUse Caseをチェック
python scripts/hooks/check_service_logic_smell.py

# 全ファイルをチェック
pre-commit run service-logic-smell-check --all-files
```

### ベストプラクティス

#### 1. Tell, Don't Ask原則の徹底

```python
# ❌ Ask (プロパティをチェックして処理)
if episode.status == "draft":
    episode.status = "published"

# ✅ Tell (メソッドで命令)
episode.publish()
```

#### 2. Entity/Value Objectへのロジック集約

```python
# ❌ Service層にロジック
def validate_episode_number(episode_number: int) -> bool:
    return 1 <= episode_number <= 9999

# ✅ Value Objectにロジック
@dataclass(frozen=True)
class EpisodeNumber:
    value: int

    def __post_init__(self):
        if not 1 <= self.value <= 9999:
            raise ValueError(f"Invalid: {self.value}")
```

#### 3. Use Caseの責務

Use Caseの正しい責務は：
- ✅ **トランザクション境界管理**
- ✅ **Repository呼び出し調整**
- ✅ **外部サービス統合**
- ❌ **業務ルール実装**（これはDomain層の責務）

### 2つのチェックの関係

| チェック | 対象層 | 検知内容 | ブロッキング |
|----------|--------|----------|--------------|
| **Anemic Domain Check** | Domain層 | ビジネスロジック欠如 | ✅ Yes（ERROR） |
| **Service Logic Smell Check** | Application層 | ロジック流出 | ❌ No（WARNING） |

**推奨ワークフロー**:
1. Anemic Domain Checkで貧血症を防止（強制）
2. Service Logic Smell Checkで流出を検知（警告）
3. 段階的にリファクタリング

### 参考資料

- **検知スクリプト**: `scripts/hooks/check_service_logic_smell.py`
- **Tell, Don't Ask原則**: https://martinfowler.com/bliki/TellDontAsk.html
- **Anemic Domain Modelとの関係**: Martin Fowler - Anemic Domain Model

---

## 検知を意図的に無効化する方法

### 1. ファイル単位で無効化

特定のファイルを`.pre-commit-config.yaml`の`exclude`に追加:

```yaml
exclude: |
  (?x)^(
    ...
    src/noveler/domain/entities/legacy_entity\.py|  # 追加
  )
```

### 2. Gitフックの一時的なスキップ

緊急時はフック全体をスキップ:

```bash
git commit -m "Urgent fix" --no-verify
```

**注意**: 誤用を避けるため、通常は使用しないでください。

### 3. 正当な理由で除外

以下の場合は検知対象外として設計されています：

- **DTOクラス**: `XxxRequest`, `XxxResponse`, `XxxDTO` suffix
- **インターフェース**: `IXxx` prefix, `XxxProtocol` suffix
- **Enumクラス**: `class Status(Enum)`
- **テストフィクスチャ**: `tests/fixtures/domain/` 配下

これらのパターンに該当する場合、リファクタリングは不要です。

---

## まとめ

- ✅ **Anemic Domain Check**: Domain層の品質を保証（強制）
- ⚠️ **Service Logic Smell Check**: Application層の品質を監視（警告）
- 📚 **ベストプラクティス**: Tell, Don't Ask + Rich Domain Model
- 🔧 **段階的改善**: WARNING modeで徐々にリファクタリング
