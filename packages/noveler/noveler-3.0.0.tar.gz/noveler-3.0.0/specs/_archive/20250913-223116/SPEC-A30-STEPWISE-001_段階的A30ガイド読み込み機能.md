# SPEC-A30-STEPWISE-001: 段階的A30ガイド読み込み機能

## 🎯 目的
A30執筆ガイドの分割ファイル構造に対応し、執筆フェーズに応じて必要な情報のみを段階的に読み込むことで、パフォーマンス向上とトークン効率化を実現する。

## 📋 要件

### REQ-1.1: 執筆フェーズの定義
- **初稿フェーズ**: 軽量・高速処理を優先
- **仕上げフェーズ**: 品質基準に沿った詳細チェック
- **トラブルシューティングフェーズ**: 問題解決支援

### REQ-1.2: フェーズ別ファイル読み込み
- **初稿フェーズ**: A30_執筆ガイド.yaml（マスター版）+ 話別プロット
- **仕上げフェーズ**: マスター + A30_執筆ガイド（詳細ルール集）.yaml + A30_執筆ガイド（ステージ別詳細チェック項目）.yaml
- **トラブルシューティングフェーズ**: A30_執筆ガイド（シューティング事例集）.yaml の該当項目

### REQ-1.3: 統合設定管理システム連携
- `configuration_service_factory`を使用してファイルパス取得
- CommonPathServiceでハードコーディング排除
- 機能フラグによる段階制御

### REQ-1.4: エラーハンドリング
- ファイル読み込み失敗時の適切なフォールバック
- 段階的読み込み失敗時の単一ファイル読み込みへの自動切り替え

## 🏗️ 実装予定

### ドメイン層
- `WritingPhase`: 執筆フェーズ列挙型
- `StepwiseA30GuideLoader`: 段階的ガイド読み込みサービス
- `A30GuideContent`: 統合ガイドコンテンツエンティティ

### アプリケーション層
- `StepwiseA30LoadingUseCase`: 段階的読み込みユースケース

### インフラストラクチャ層
- `StepwiseA30FileRepository`: 分割ファイル対応リポジトリ
- `A30GuideServiceFactory`: ファクトリーパターン実装

### プレゼンテーション層
- `writing_commands.py`: 既存実装の拡張

## ✅ 受け入れ条件

### 機能要件
- [ ] 初稿フェーズでマスター版のみ読み込み、軽量動作確認
- [ ] 仕上げフェーズで詳細ルール・チェック項目読み込み確認
- [ ] トラブルシューティングフェーズで該当項目提示確認
- [ ] ファイル読み込み失敗時のフォールバック動作確認

### 非機能要件
- [ ] 初稿フェーズの読み込み時間50%短縮（従来比）
- [ ] 統合設定管理システム100%活用
- [ ] ハードコーディング0%達成
- [ ] 既存機能への影響なし

### 品質要件
- [ ] 全テストパス（ユニット・統合）
- [ ] B30品質基準100%遵守
- [ ] アーキテクチャ検証テストパス
- [ ] 型安全性確保（mypy）

## 🔧 実装アプローチ

### フェーズ1: ドメインモデル設計
```python
from enum import Enum
from dataclasses import dataclass
from pathlib import Path

class WritingPhase(Enum):
    DRAFT = "draft"          # 初稿フェーズ
    REFINEMENT = "refinement"  # 仕上げフェーズ
    TROUBLESHOOTING = "troubleshooting"  # トラブルシューティング

@dataclass
class A30GuideContent:
    master_guide: dict[str, any]
    detailed_rules: dict[str, any] | None = None
    quality_checklist: dict[str, any] | None = None
    troubleshooting_guide: dict[str, any] | None = None
    phase: WritingPhase = WritingPhase.DRAFT
```

### フェーズ2: 段階的読み込みサービス実装
```python
class StepwiseA30GuideLoader:
    def load_for_phase(self, phase: WritingPhase) -> A30GuideContent:
        match phase:
            case WritingPhase.DRAFT:
                return self._load_draft_content()
            case WritingPhase.REFINEMENT:
                return self._load_refinement_content()
            case WritingPhase.TROUBLESHOOTING:
                return self._load_troubleshooting_content()
```

### フェーズ3: 既存システム統合
```python
# RuamelYamlPromptRepository の拡張
class EnhancedRuamelYamlPromptRepository(RuamelYamlPromptRepository):
    def __init__(self, guide_loader: StepwiseA30GuideLoader):
        self._guide_loader = guide_loader

    async def generate_stepwise_prompt_with_phase(
        self,
        metadata: YamlPromptMetadata,
        phase: WritingPhase
    ) -> YamlPromptContent:
        # フェーズに応じたコンテンツ読み込み
        guide_content = self._guide_loader.load_for_phase(phase)
        # プロンプト生成処理...
```

## 🎯 成功指標
- 初稿フェーズの処理時間: 従来比50%短縮
- トークン使用量: 初稿フェーズで30%削減
- エラー率: フォールバック機能により10%削減
- 開発者体験: フェーズ指定による直感的操作実現
