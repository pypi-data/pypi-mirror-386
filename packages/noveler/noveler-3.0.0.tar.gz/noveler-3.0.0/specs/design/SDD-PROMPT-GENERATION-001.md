# SDD: A24プロンプト生成機能 - Software Design Document

## 1. システム概要

### 1.1 目的
A24_話別プロット作成ガイド.mdを基盤として、Claude Codeでの話別プロット作成を支援する高精度なプロンプトを自動生成する機能を提供する。

### 1.2 システム境界
- **入力**: エピソード番号、プロジェクト情報、コンテキスト要素
- **処理**: A24ガイドベースのプロンプト構造化、コンテキスト統合
- **出力**: Claude Code最適化プロンプト（YAML構造化形式）

### 1.3 品質目標
- **精度**: A24ガイド単独比較で85-90%精度達成
- **再現性**: 同条件での一貫したプロンプト生成
- **保守性**: DDD原則に基づく疎結合アーキテクチャ

## 2. 機能要求

### 2.1 コア機能 (FR-001)
**名前**: A24ベースプロンプト生成
**説明**: A24ガイドの4段階プロセス（骨格構築→三幕構成設計→シーン肉付け→技術伏線統合）に基づくプロンプト生成
**入力**:
- episode_number: int (必須)
- project_name: str (必須)
- context_level: str (基本|拡張|完全) = "基本"
**出力**: PromptGenerationResult

### 2.2 コンテキスト統合機能 (FR-002)
**名前**: 智能コンテキスト統合
**説明**: 重要シーン.yaml、伏線管理.yaml等の関連ファイル情報を分析しプロンプトに統合
**依存**:
- 重要シーン.yaml（エピソード関連シーンの抽出）
- 伏線管理.yaml（該当エピソードの伏線要素）
- 章別プロット（前後コンテキスト）

### 2.3 品質最適化機能 (FR-003)
**名前**: Claude Code最適化
**説明**: Claude Codeの特性に合わせたプロンプト構造化と最適化
**特徴**:
- トークン数制限考慮（最大20,000トークン目安）
- 段階的指示構造（Stage 1-4明確分離）
- YAML出力フォーマット強制指定

## 3. 非機能要求

### 3.1 性能要求 (NFR-001)
- レスポンス時間: 3秒以内
- メモリ使用量: 100MB以内
- 同時実行: 単一プロセス想定

### 3.2 保守性要求 (NFR-002)
- テストカバレッジ: 90%以上
- DDD原則遵守
- SOLID原則準拠

### 3.3 拡張性要求 (NFR-003)
- 新規プロンプトテンプレート追加対応
- 異なるAIシステムへの拡張可能性

## 4. システム制約

### 4.1 技術制約 (CON-001)
- Python 3.11以上
- 既存DDD基盤との統合必須
- typer CLIフレームワーク使用

### 4.2 ビジネス制約 (CON-002)
- 既存novel plot episodeコマンドとの互換性維持
- A24ガイドフォーマット準拠
- 日本語コンテンツ特化

### 4.3 運用制約 (CON-003)
- Claude Code環境での動作必須
- プロジェクト構造依存度最小化

## 5. アーキテクチャ方針

### 5.1 DDD適用方針
```
Domain Layer:
- PromptTemplate (Entity)
- A24GuideContent (Value Object)
- ContextElement (Value Object)
- PromptGenerationService (Domain Service)

Application Layer:
- PromptGenerationUseCase (Use Case)

Infrastructure Layer:
- FileA24GuideRepository (Repository)
- YamlContextExtractor (External Service)
```

### 5.2 依存性管理
- Repository抽象化による外部ファイル依存分離
- Service抽象化によるAI最適化ロジック分離
- Factory Patternによるオブジェクト生成統合

## 6. インターフェース設計

### 6.1 CLI Command Interface
```bash
novel plot episode [EPISODE_NUMBER] --mode prompt-generation [OPTIONS]
```

### 6.2 Use Case Interface
```python
class PromptGenerationUseCaseRequest:
    episode_number: int
    project_name: str
    context_level: ContextLevel
    include_foreshadowing: bool = True
    include_important_scenes: bool = True
    optimization_target: OptimizationTarget = OptimizationTarget.CLAUDE_CODE

class PromptGenerationUseCaseResponse:
    success: bool
    generated_prompt: str
    token_estimate: int
    context_elements_count: int
    generation_time_ms: int
    error_message: str | None = None
```

## 7. データ設計

### 7.1 Core Domain Objects
```python
@dataclass(frozen=True)
class A24StagePrompt:
    stage_number: int
    stage_name: str
    instructions: list[str]
    validation_criteria: list[str]
    expected_output: str

@dataclass(frozen=True)
class ContextElement:
    element_type: ContextElementType  # FORESHADOWING, IMPORTANT_SCENE, CHAPTER_CONNECTION
    content: str
    priority: float
    integration_point: A24Stage
```

### 7.2 Repository Contracts
```python
class A24GuideRepository(ABC):
    @abstractmethod
    def get_stage_instructions(self, stage: A24Stage) -> list[str]:
        pass

    @abstractmethod
    def get_template_structure(self) -> dict[str, Any]:
        pass

class ProjectContextRepository(ABC):
    @abstractmethod
    def extract_foreshadowing_elements(self, episode_number: int) -> list[ContextElement]:
        pass

    @abstractmethod
    def extract_important_scenes(self, episode_number: int) -> list[ContextElement]:
        pass
```

## 8. 検証方法

### 8.1 機能検証
- A24ガイド4段階の完全再現検証
- 生成プロンプトのClaude Code実行成功率測定
- コンテキスト統合の精度評価

### 8.2 品質検証
- 単体テスト: 各ドメインサービス個別検証
- 統合テスト: ユースケース全体の動作確認
- E2Eテスト: CLI→プロンプト生成→YAML出力の全工程

## 9. 実装優先順位

### Phase 1: MVP (Minimum Viable Product)
1. A24GuideRepository実装
2. PromptGenerationService基本機能
3. CLI統合

### Phase 2: Context Enhancement
1. ProjectContextRepository実装
2. コンテキスト統合機能
3. 品質最適化

### Phase 3: Advanced Features
1. 複数最適化ターゲット対応
2. カスタムテンプレート対応
3. 性能チューニング

---

**承認者**: システムアーキテクト
**作成日**: 2025-08-07
**バージョン**: 1.0.0
