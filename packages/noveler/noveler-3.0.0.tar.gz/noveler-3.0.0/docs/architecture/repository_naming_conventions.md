# Repository 命名規則

**目的**: NovelerプロジェクトにおけるRepository実装の命名一貫性を確保し、DDD原則への準拠を維持する。

---

## 原則

### Domain層（インターフェース）

**パターン**: `{Entity}Repository`

```python
# ✅ 正しい例
class EpisodeRepository(ABC):
    pass

class PlotRepository(ABC):
    pass

class ProjectRepository(ABC):
    pass
```

**特徴**:
- シンプルで抽象度が高い
- 技術的詳細を含まない
- DDD原則に完全準拠

**配置場所**: `src/noveler/domain/repositories/`

---

### Infrastructure層（実装）

#### 推奨パターン（優先順位順）

**1. `{Technology}{Entity}Repository`（最推奨）**

```python
# ✅ 推奨例
class YamlEpisodeRepository(EpisodeRepository):
    """YAML形式でのEpisode永続化実装"""

class FileEpisodeRepository(EpisodeRepository):
    """ファイルシステムでのEpisode永続化実装"""

class JsonPlotRepository(PlotRepository):
    """JSON形式でのPlot永続化実装"""

class MarkdownProjectRepository(ProjectRepository):
    """Markdown形式でのProject永続化実装"""
```

**使用条件**:
- 永続化技術が明確な場合（Yaml/File/Json/Markdown等）
- 実装の技術的特性を強調したい場合

**配置場所**: `src/noveler/infrastructure/repositories/`

**2. `{Technology}{Entity}RepositoryAdapter`（Adapterパターン使用時）**

```python
# ✅ 許容例（Ports/Adaptersアーキテクチャ明示時）
class FileEpisodeRepositoryAdapter(EpisodeRepository):
    """Ports/Adaptersパターンでのファイル永続化アダプタ"""
```

**使用条件**:
- Ports/Adaptersアーキテクチャを明示的に採用する場合
- 外部システムとの統合インターフェースを提供する場合

**配置場所**: `src/noveler/infrastructure/adapters/repositories/`

---

## 既存パターンの扱い

### ✅ 許容パターン（レガシー）

以下のパターンは既存コードで使用されており、**新規作成は非推奨**だが既存ファイルは維持:

- **`File*Repository`**: 12ファイル（レガシー、新規作成時は`*File*Repository`を使用）
- **`*Adapter`**: 33ファイル（Ports/Adaptersパターン使用時のみ許容）

### ❌ 禁止パターン

以下のパターンは**新規作成禁止**:

```python
# ❌ 禁止例
class EpisodeRepositoryImpl(EpisodeRepository):
    """'Impl'サフィックスは冗長"""

class RepositoryBase:
    """技術接頭辞なし（Infrastructure層では禁止）"""
```

**理由**:
- `*Impl`: 実装であることは自明なため冗長
- 無接頭辞: 技術的特性が不明瞭

---

## 重複禁止ルール

### 原則

**同名ファイルは異なるディレクトリに配置してはならない**

### 例外

以下のペアは許容:

```
✅ 許容される例外
src/noveler/domain/repositories/episode_repository.py       # インターフェース
src/noveler/infrastructure/repositories/yaml_episode_repository.py  # 実装
```

**理由**: Domain/Infrastructureの明確な分離はDDD原則に準拠

### ❌ 禁止例

```
❌ 同名ファイルの重複（混乱を招く）
infrastructure/adapters/file_episode_repository.py
infrastructure/adapters/repositories/file_episode_repository.py
infrastructure/persistence/file_episode_repository.py
```

**対策**: 配置場所に応じた命名（`file_episode_adapter.py`, `file_episode_persistence.py`等）

---

## 新規Repository作成手順

### 手動作成

#### 1. Domain層インターフェース作成

```bash
# ファイル作成
touch src/noveler/domain/repositories/{entity}_repository.py
```

```python
# src/noveler/domain/repositories/character_repository.py
from abc import ABC, abstractmethod
from noveler.domain.entities.character import Character

class CharacterRepository(ABC):
    """Character集約の永続化インターフェース"""

    @abstractmethod
    def save(self, character: Character) -> Character:
        pass

    @abstractmethod
    def find_by_id(self, character_id: str) -> Character | None:
        pass
```

#### 2. Infrastructure層実装作成

```bash
# ファイル作成
touch src/noveler/infrastructure/repositories/yaml_{entity}_repository.py
```

```python
# src/noveler/infrastructure/repositories/yaml_character_repository.py
from noveler.domain.repositories.character_repository import CharacterRepository
from noveler.domain.entities.character import Character

class YamlCharacterRepository(CharacterRepository):
    """YAML形式でのCharacter永続化実装"""

    def save(self, character: Character) -> Character:
        # 実装
        pass

    def find_by_id(self, character_id: str) -> Character | None:
        # 実装
        pass
```

### スクリプト使用（推奨）

```bash
# 使用例
./scripts/create_repository.sh yaml character

# 生成されるファイル:
# - src/noveler/domain/repositories/character_repository.py
# - src/noveler/infrastructure/repositories/yaml_character_repository.py
# - tests/unit/domain/repositories/test_character_repository.py
# - tests/unit/infrastructure/repositories/test_yaml_character_repository.py
```

---

## 検証方法

### 1. pre-commit hookによる自動検証

```bash
# コミット時に自動実行
git commit -m "feat: add new repository"

# 手動実行
python scripts/hooks/check_repository_naming.py
```

**検証内容**:
- Infrastructure層での技術接頭辞チェック
- 重複ファイル名検出
- 禁止パターン検出

### 2. importlinter契約検証

```bash
# DDD依存方向の検証
python -m importlinter
```

**検証契約**:
- Domain層はInfrastructure層をimportしない
- Application層はDomainインターフェースのみ参照

---

## 現状の統計（参考）

- **総Repository関連ファイル**: 154ファイル
  - Domain層（インターフェース）: 53ファイル
  - Infrastructure層（実装）: 82ファイル
  - Tests: 19ファイル

- **Infrastructure層の内訳**:
  - `Yaml*Repository`: 36ファイル（推奨パターン）
  - `File*Repository`: 12ファイル（レガシー）
  - `Json*Repository`: 3ファイル（推奨パターン）
  - `*Adapter`: 33ファイル（条件付き許容）

---

## 段階的改善計画

### Phase 1: 文書化とルール整備（完了）
- ✅ 本ドキュメント作成
- ✅ pre-commit hook追加
- ✅ 作成スクリプト整備

### Phase 2: 新規ファイルへの適用（進行中）
- 新規Repository作成時に推奨パターンを使用
- レビュー時に命名規則を確認

### Phase 3: 緊急対応（必要時のみ）
- 重複ファイル名の個別解消
- 禁止パターンの段階的削除

### Phase 4: レガシーパターンの段階的統一（長期）
- 月5-10ファイルずつリファクタリング
- テスト実行とimportlinter検証を徹底

---

## 関連ドキュメント

- **DDD原則**: [CLAUDE.md](../../CLAUDE.md#レイヤリング原則必須)
- **アーキテクチャガイド**: [docs/architecture/README.md](./README.md)
- **importlinter契約**: [.importlinter](./.importlinter)
- **作成スクリプト**: [scripts/create_repository.sh](../../scripts/create_repository.sh)
- **検証スクリプト**: [scripts/hooks/check_repository_naming.py](../../scripts/hooks/check_repository_naming.py)

---

## 変更履歴

- 2025-10-03: 初版作成（DDD準拠改善プロジェクトの一環）
