# 遅延インポート（PLC0415）維持箇所の方針

以下のモジュールは循環依存回避/重量依存/起動時間配慮のため、意図的に遅延インポート（importlib/guarded import）を維持します。該当箇所には `# noqa: PLC0415` または理由コメントを付記しています。

- sitecustomize.py — 起動時の環境適用順序に依存するため
- noveler/presentation/mcp/* — MCPブート時の循環回避/軽量化のため
- noveler/tools/* — 実行時のみ必要なUI/Console依存（ツール単体実行時）
- infrastructure/services/codemap_* — WebSocket/Async依存の重量モジュールを遅延読込

新規流入については importlib + 局所関数化を優先し、不可避な箇所には上記の方針で意図を明記してください。



### 追加の遅延import適用箇所（更新）
- `noveler.domain.services.progressive_check_manager`: get_logger/LLMIOLogger を importlib 遅延参照、PathService は manager 経由。
- `noveler.domain.services.configuration_loader_service`: configuration_service_factory を importlib 遅延参照。
- `noveler.domain.services.writing_steps.manuscript_generator_service`: ConfigurationManager を importlib で遅延参照。

