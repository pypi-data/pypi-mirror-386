# ロギング強化提案書

## 現状分析結果

### 良い点 ✅

1. **統一ロガーの実装**
   - `unified_logger.py`による一元管理
   - 環境別プリセット（development/production/MCP）
   - 構造化ログ（JSON形式）のサポート

2. **基本的なログレベル使用**
   - INFO: 正常系処理の追跡
   - WARNING: リトライ・フォールバック時
   - ERROR: 例外発生時
   - DEBUG: 詳細情報（verbose時）

3. **エラーハンドリングでのログ**
   - 例外発生時の`exc_info=True`使用
   - リトライ回数の記録
   - エラーコンテキストの保存

### 改善が必要な点 ⚠️

## 改善提案

### 1. 構造化ログの拡充

現状では`extra`パラメータの使用が限定的です。以下の改善を提案：

```python
# 現在の実装
self.logger.info("Claude Code実行成功 (%.0fms)", response.execution_time_ms)

# 改善案
self.logger.info(
    "Claude Code実行成功",
    extra={
        "extra_data": {
            "execution_time_ms": response.execution_time_ms,
            "request_id": session_id,
            "prompt_tokens": response.prompt_tokens,
            "completion_tokens": response.completion_tokens,
            "total_cost_usd": response.total_cost,
            "model": response.model_name
        }
    }
)
```

### 2. パフォーマンス計測の統合

```python
# performance_monitor デコレータと統合
@performance_monitor("execute_writing_step")
def execute_writing_step(self, step_id: int):
    start_time = time.time()
    try:
        result = self._execute_step_internal(step_id)
        elapsed_ms = (time.time() - start_time) * 1000

        self.logger.info(
            f"ステップ {step_id} 完了",
            extra={
                "extra_data": {
                    "step_id": step_id,
                    "elapsed_ms": elapsed_ms,
                    "success": True,
                    "memory_usage_mb": self._get_memory_usage()
                }
            }
        )
        return result
    except Exception as e:
        elapsed_ms = (time.time() - start_time) * 1000
        self.logger.error(
            f"ステップ {step_id} 失敗",
            extra={
                "extra_data": {
                    "step_id": step_id,
                    "elapsed_ms": elapsed_ms,
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                }
            },
            exc_info=True
        )
        raise
```

### 3. トレーサビリティの向上

```python
# リクエストID/セッションIDの伝播
class RequestContext:
    def __init__(self):
        self.request_id = str(uuid.uuid4())
        self.session_id = None
        self.user_id = None
        self.episode_number = None

    def to_dict(self):
        return {
            "request_id": self.request_id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "episode_number": self.episode_number
        }

# 使用例
def process_request(self, context: RequestContext):
    self.logger.info(
        "リクエスト処理開始",
        extra={"extra_data": context.to_dict()}
    )
```

### 4. デバッグポイントの追加

以下の箇所にDEBUGログを追加することを推奨：

1. **キャッシュ操作**
```python
def get(self, key: str) -> Any:
    if key in self.cache:
        value, timestamp = self.cache[key]
        if self.ttl is None or (time.time() - timestamp) < self.ttl:
            self.hits += 1
            self.logger.debug(
                "キャッシュヒット",
                extra={
                    "extra_data": {
                        "cache_key": key,
                        "hit_rate": self.get_hit_rate(),
                        "cache_size": len(self.cache)
                    }
                }
            )
            return value
```

2. **LLM呼び出し前後**
```python
self.logger.debug(
    "LLMリクエスト送信",
    extra={
        "extra_data": {
            "prompt_length": len(prompt),
            "max_tokens": max_tokens,
            "temperature": temperature,
            "model": model_name
        }
    }
)
```

3. **ファイルI/O操作**
```python
self.logger.debug(
    "ファイル読み込み",
    extra={
        "extra_data": {
            "file_path": str(file_path),
            "file_size_bytes": file_path.stat().st_size,
            "encoding": encoding
        }
    }
)
```

### 5. エラー分類の改善

```python
class ErrorCategory(Enum):
    VALIDATION = "validation"
    NETWORK = "network"
    FILESYSTEM = "filesystem"
    PARSING = "parsing"
    BUSINESS_LOGIC = "business_logic"
    EXTERNAL_SERVICE = "external_service"

def log_error_with_category(self, error: Exception, category: ErrorCategory):
    self.logger.error(
        f"{category.value}エラー: {error}",
        extra={
            "extra_data": {
                "error_category": category.value,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "stacktrace": traceback.format_exc() if self.logger.isEnabledFor(logging.DEBUG) else None
            }
        },
        exc_info=True
    )
```

### 6. 監視・アラート用メトリクス

```python
# 重要なビジネスイベント
self.logger.info(
    "原稿生成完了",
    extra={
        "extra_data": {
            "event_type": "manuscript_generated",
            "episode_number": episode_number,
            "word_count": word_count,
            "quality_score": quality_score,
            "generation_time_ms": elapsed_ms,
            "alert_level": "info" if quality_score > 80 else "warning"
        }
    }
)
```

### 7. ログサンプリング設定

高頻度イベントのサンプリング：

```python
class SampledLogger:
    def __init__(self, logger, sample_rate=0.1):
        self.logger = logger
        self.sample_rate = sample_rate

    def debug_sampled(self, message, **kwargs):
        if random.random() < self.sample_rate:
            self.logger.debug(f"[SAMPLED] {message}", **kwargs)
```

## 実装優先度

1. **高優先度**
   - 構造化ログの拡充（extra_data使用）
   - エラー分類とカテゴリ化
   - リクエストID/セッションIDの実装

2. **中優先度**
   - パフォーマンスメトリクスの統合
   - LLM呼び出しのデバッグログ
   - キャッシュ操作のログ

3. **低優先度**
   - ログサンプリング
   - 詳細なファイルI/Oログ

## 期待効果

- **デバッグ時間の短縮**: 50%削減（構造化ログによる検索性向上）
- **本番障害対応**: MTTR（平均復旧時間）30%改善
- **パフォーマンス分析**: ボトルネック特定が容易に
- **コスト最適化**: LLM使用状況の可視化

## 次のステップ

1. 優先度「高」の項目から段階的に実装
2. 各サービスクラスに構造化ログを追加
3. ログ分析ダッシュボードの構築（将来的に）