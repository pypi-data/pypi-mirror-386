# SPEC-A31-COMPLETE-001: A31完全68項目自動チェックシステム

## 概要

A31原稿執筆チェックリストの全68項目を対象とした完全自動チェック・修正システムの実装。
SDD（仕様駆動開発）+ DDD（ドメイン駆動設計）+ TDD（テスト駆動開発）に準拠した高品質な実装を行う。

## 要件定義

### 機能要件

#### FR-001: 全68項目自動チェック機能
- **説明**: A31-001からA31-068まで全項目の自動チェック実行
- **入力**: プロジェクト名、エピソード番号、チェック対象項目リスト（オプション）
- **出力**: 各項目の合格/不合格判定、詳細評価結果、改善提案

#### FR-002: 階層化された自動修正機能
- **説明**: 修正レベル（safe/standard/aggressive）に応じた自動修正
- **safe**: フォーマット調整、記号統一など
- **standard**: 文体改善、基本的な構成調整など
- **aggressive**: 内容改善、大幅な構造変更など

#### FR-003: 優先度ベース修正実行
- **説明**: 各項目の優先度に基づく修正順序制御
- **優先度1**: 致命的問題（フォーマット、基本文法等）
- **優先度2**: 重要問題（文体統一、構成等）
- **優先度3**: 推奨改善（表現改善、詳細調整等）

#### FR-004: 包括的レポート生成
- **説明**: チェック結果の構造化されたレポート出力
- **フォーマット**: YAML、JSON、Markdown対応
- **内容**: 項目別詳細、統計情報、改善提案、実行履歴

### 非機能要件

#### NFR-001: パフォーマンス
- **チェック実行時間**: 1エピソード ≤ 5秒
- **メモリ使用量**: ≤ 100MB（通常のエピソードサイズ）
- **同時実行**: 最大3エピソードの並列処理対応

#### NFR-002: 信頼性
- **データ整合性**: 修正前の自動バックアップ
- **エラー回復**: 部分的失敗からの復旧機能
- **ロールバック**: 修正内容の取り消し機能

#### NFR-003: 拡張性
- **新項目追加**: 設定ファイル更新のみで対応
- **カスタムルール**: プロジェクト固有のチェック追加
- **プラグイン対応**: 外部チェッカーとの連携

## アーキテクチャ設計

### DDD レイヤー構造

```
scripts/
├── domain/                     # ドメイン層
│   ├── entities/
│   │   ├── a31_complete_checklist.py      # 完全チェックリストエンティティ
│   │   ├── a31_check_session.py           # チェックセッション
│   │   └── a31_evaluation_batch.py        # 評価バッチ
│   ├── value_objects/
│   │   ├── a31_check_result.py            # チェック結果
│   │   ├── a31_priority_level.py          # 優先度レベル
│   │   └── a31_scope_filter.py            # スコープフィルター
│   ├── services/
│   │   ├── a31_complete_evaluation_service.py  # 完全評価サービス
│   │   ├── a31_batch_auto_fix_service.py       # バッチ自動修正サービス
│   │   └── a31_reporting_service.py            # レポートサービス
│   └── repositories/
│       └── a31_complete_checklist_repository.py # 完全チェックリストリポジトリ
├── application/                # アプリケーション層
│   └── use_cases/
│       ├── a31_complete_check_use_case.py      # 完全チェックユースケース
│       └── a31_batch_auto_fix_use_case.py      # バッチ自動修正ユースケース
├── infrastructure/             # インフラ層
│   ├── repositories/
│   │   └── yaml_a31_complete_checklist_repository.py
│   ├── external/
│   │   └── claude_code_a31_evaluator.py       # Claude Code連携
│   └── formatters/
│       ├── yaml_a31_reporter.py
│       ├── json_a31_reporter.py
│       └── markdown_a31_reporter.py
└── presentation/               # プレゼンテーション層
    ├── cli/
    │   └── commands/
    │       └── a31_complete_command.py
    └── api/
        └── a31_complete_api.py
```

### コンポーネント設計

#### A31CompleteChecklistEntity
```python
@dataclass
class A31CompleteChecklist:
    """A31完全チェックリストエンティティ"""

    checklist_id: A31ChecklistId
    project_name: str
    episode_number: int
    all_items: list[A31ChecklistItem]  # 全68項目
    target_scope: A31ScopeFilter
    created_at: datetime

    def filter_by_priority(self, min_priority: A31PriorityLevel) -> list[A31ChecklistItem]:
        """優先度によるフィルタリング"""

    def filter_by_auto_fix_level(self, fix_level: FixLevel) -> list[A31ChecklistItem]:
        """修正レベルによるフィルタリング"""

    def get_phase_items(self, phase: str) -> list[A31ChecklistItem]:
        """フェーズ別項目取得"""
```

#### A31CompleteEvaluationService
```python
class A31CompleteEvaluationService:
    """A31完全評価サービス"""

    def evaluate_all_items(
        self,
        content: str,
        checklist: A31CompleteChecklist,
        evaluation_config: A31EvaluationConfig
    ) -> A31EvaluationBatch:
        """全項目評価実行"""

    def evaluate_by_phase(
        self,
        content: str,
        phase: str,
        items: list[A31ChecklistItem]
    ) -> dict[str, A31CheckResult]:
        """フェーズ別評価実行"""
```

## 実装計画

### Phase 1: ドメイン層実装
1. **A31CompleteChecklist** エンティティ
2. **A31CheckSession** エンティティ
3. **A31CheckResult** 値オブジェクト
4. **A31CompleteEvaluationService** ドメインサービス

### Phase 2: アプリケーション層実装
1. **A31CompleteCheckUseCase** ユースケース
2. **A31BatchAutoFixUseCase** ユースケース
3. エラーハンドリングとログ機能

### Phase 3: インフラ層実装
1. **YamlA31CompleteChecklistRepository** リポジトリ
2. **ClaudeCodeA31Evaluator** 外部連携
3. レポートフォーマッター群

### Phase 4: プレゼンテーション層実装
1. **A31CompleteCommand** CLIコマンド
2. 既存コマンド統合
3. ユーザーインターフェース改善

## テスト戦略

### 単体テスト（75%）
- 各ドメインエンティティのビジネスロジック
- 値オブジェクトの不変性とバリデーション
- ドメインサービスの評価アルゴリズム

### 統合テスト（20%）
- ユースケースの完全実行フロー
- リポジトリとファイルシステム連携
- 外部サービス（Claude Code）との統合

### E2Eテスト（5%）
- CLIコマンドの完全実行
- 実際のエピソードファイルでの検証
- パフォーマンステスト

## 品質基準

### コード品質
- **Cyclomatic Complexity**: ≤10 per method
- **Test Coverage**: ≥90%
- **Type Coverage**: 100%（mypy strict mode）

### パフォーマンス
- **単一項目チェック**: ≤100ms
- **全68項目チェック**: ≤5秒
- **メモリ使用量**: ≤100MB

### セキュリティ
- **入力検証**: 全ユーザー入力の検証
- **ファイル操作**: パストラバーサル攻撃防止
- **エラー情報**: 機密情報の漏洩防止

## 実装スケジュール

### Week 1: 設計・仕様確定
- [ ] 詳細設計レビュー
- [ ] テストケース設計
- [ ] 技術検証（PoC）

### Week 2: ドメイン層実装
- [ ] エンティティ実装
- [ ] 値オブジェクト実装
- [ ] ドメインサービス実装
- [ ] 単体テスト作成

### Week 3: アプリケーション・インフラ層実装
- [ ] ユースケース実装
- [ ] リポジトリ実装
- [ ] 外部連携実装
- [ ] 統合テスト作成

### Week 4: プレゼンテーション層・統合
- [ ] CLIコマンド実装
- [ ] 既存システム統合
- [ ] E2Eテスト作成
- [ ] パフォーマンス最適化

## 成功基準

### 機能基準
- [ ] 全68項目の自動チェック実行
- [ ] 3段階修正レベルの完全対応
- [ ] 優先度ベース修正順序制御
- [ ] 包括的レポート出力

### 品質基準
- [ ] テストカバレッジ ≥90%
- [ ] パフォーマンス基準達成
- [ ] セキュリティ基準準拠
- [ ] DDD/TDD/SDD完全準拠

### ユーザビリティ基準
- [ ] 直感的なCLIインターフェース
- [ ] 明確なエラーメッセージ
- [ ] 包括的なドキュメント
- [ ] 既存ワークフローとの統合

## リスク管理

### 技術リスク
- **複雑性管理**: 段階的実装によるリスク軽減
- **パフォーマンス**: 早期プロトタイプによる検証
- **統合問題**: 継続的統合テストによる早期発見

### スケジュールリスク
- **scope creep**: 明確な要件定義と変更管理
- **技術的債務**: リファクタリング時間の確保
- **テスト時間**: 並行開発によるテスト時間確保

## 承認

- **Product Owner**: [ ]
- **Technical Lead**: [ ]
- **QA Lead**: [ ]
- **Security Review**: [ ]

---

**Document Version**: 1.0
**Created**: 2025-08-03
**Last Updated**: 2025-08-03
**Next Review**: 2025-08-10
