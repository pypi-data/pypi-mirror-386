# SPEC-IWW-001: 統合執筆ワークフロー仕様書

## 概要
`novel write`コマンドにYAML段階的執筆プロンプト生成機能を統合し、従来ワークフローを破壊することなく執筆支援機能を強化する。

## 要件

### 機能要件 (Functional Requirements)
- **FR-001**: 従来の`novel write <episode>`コマンド完全互換性保持
- **FR-002**: プロット解析によるYAML段階的執筆プロンプト自動生成
- **FR-003**: ruamel.yaml使用によるyamllint完全準拠出力
- **FR-004**: エラー時の適切なフォールバック（従来ワークフロー継続）
- **FR-005**: 生成されたYAMLファイルの自動検証・品質保証

### 非機能要件 (Non-Functional Requirements)
- **NFR-001**: プロンプト生成処理時間 < 2秒
- **NFR-002**: メモリ消費増加 < 50MB
- **NFR-003**: 既存テスト100%パス維持
- **NFR-004**: DDD準拠アーキテクチャ維持
- **NFR-005**: Type Safety 100%（mypy strict準拠）

### 制約 (Constraints)
- **CON-001**: 既存`WritingCommandHandler`の破壊的変更禁止
- **CON-002**: CLAUDE.md準拠のコーディング規約厳守
- **CON-003**: scripts.プレフィックス必須（統合インポート管理システム）
- **CON-004**: TDD実装（テスト先行開発）必須

## ユーザーストーリー
```
As a 小説家
I want novel writeコマンドで自動的に段階的執筆プロンプトが生成される
So that より効率的で品質の高い執筆ができる
```

## 受け入れ基準 (Acceptance Criteria)
- [ ] `novel write 13`実行で第013話用YAMLプロンプトが生成される
- [ ] 生成されたYAMLファイルがyamllint検証をパスする
- [ ] プロット解析結果がカスタム要件として反映される
- [ ] YAML生成失敗時でも従来ワークフローが正常動作する
- [ ] 全体処理時間が既存の120%以内に収まる

## リスク (Risks)
- **RISK-001**: YAML生成処理でのメモリリーク
- **RISK-002**: プロット解析失敗時の例外処理
- **RISK-003**: ruamel.yaml依存による環境互換性問題

## 実装戦略
1. **Phase 1**: TDD実装（テスト先行）
2. **Phase 2**: Domain層実装（Entity/Value Object）
3. **Phase 3**: Application層実装（Use Case）
4. **Phase 4**: Infrastructure層統合
5. **Phase 5**: Presentation層統合
