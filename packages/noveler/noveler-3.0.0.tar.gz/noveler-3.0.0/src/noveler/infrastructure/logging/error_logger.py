"""
エラーロガー実装（Infrastructure層 - Imperative Shell）
SPEC-ERR-001: 統一エラーハンドリングシステム

実際のログ出力を行う（副作用あり）
"""

import json
from datetime import datetime
from pathlib import Path

from noveler.domain.services.error_classifier import ErrorLevel
from noveler.domain.value_objects.project_time import project_now
from noveler.infrastructure.logging.unified_logger import get_logger


class ErrorLogger:
    """
    エラーログ出力実装

    Imperative Shell:
    - ファイルへの書き込み（副作用）
    - 外部システムへの通知（副作用）
    """

    def __init__(self, log_file: Path | None = None, format: str = "text") -> None:
        """
        Args:
            log_file: ログファイルパス（オプション）
            format: ログフォーマット ("text" or "json")
        """
        self.log_file = log_file
        self.format = format
        self._setup_logger()

    def _setup_logger(self) -> None:
        """ロガーセットアップ（副作用）"""
        try:
            self.logger = get_logger("ErrorLogger")
        except Exception:

            class _Stub:
                def __init__(self):
                    import sys as _sys
                    self._stderr = _sys.stderr
                def log(self, *_args, **_kwargs):
                    pass
                def error(self, msg, *a, **k):
                    try:
                        self._stderr.write(str(msg)+"\n")
                    except Exception:
                        pass
                def warning(self, msg, *a, **k):
                    try:
                        self._stderr.write(str(msg)+"\n")
                    except Exception:
                        pass
                def info(self, *a, **k):
                    pass
                def debug(self, *a, **k):
                    pass
                def setLevel(self, *_):
                    pass
                def addHandler(self, *_):
                    pass
            self.logger = _Stub()

        if self.log_file:
            # 出力先ディレクトリが存在しない場合は作成
            try:
                self.log_file.parent.mkdir(parents=True, exist_ok=True)
            except Exception:
                pass

    def log(self, error: Exception, level: ErrorLevel, context: dict | None = None):
        """
        エラーをログに記録（副作用）

        Args:
            error: エラーオブジェクト
            level: エラーレベル
            context: 追加コンテキスト
        """
        if self.format == "json":
            log_entry = self.format_log_entry(error, level, context)
            self._write_json_log(log_entry)
        else:
            log_message = self._format_text_message(error, level, context)
            self._write_text_log(log_message, level)

    def format_log_entry(self, error: Exception, level: ErrorLevel,
                         context: dict | None = None) -> str:
        """
        構造化ログエントリーを生成

        Args:
            error: エラーオブジェクト
            level: エラーレベル
            context: 追加コンテキスト

        Returns:
            str: JSON形式のログエントリー
        """
        entry = {
            "timestamp": project_now().datetime.isoformat(),
            "level": level.value.upper(),
            "error_type": type(error).__name__,
            "message": str(error),
            "context": context or {}
        }

        return json.dumps(entry, ensure_ascii=False, default=str)

    def _format_text_message(self, error: Exception, level: ErrorLevel,
                            context: dict | None = None) -> str:
        """テキスト形式のメッセージ生成"""
        message = f"[{level.value.upper()}] {type(error).__name__}: {error}"

        if context:
            message += f" | Context: {context}"

        return message

    def _write_json_log(self, log_entry: str) -> None:
        """JSONログ書き込み（副作用）"""
        if self.log_file:
            with self.log_file.open("a", encoding="utf-8") as f:
                f.write(log_entry + "\n")

    def _write_text_log(self, message: str, level: ErrorLevel) -> None:
        """テキストログ書き込み（副作用）"""
        if self.log_file:
            try:
                with self.log_file.open("a", encoding="utf-8") as f:
                    f.write(f"{message}\n")
                return
            except Exception:
                pass
        # ロガーへ委譲（レベル名で分岐）
        method = {
            ErrorLevel.CRITICAL: "critical",
            ErrorLevel.ERROR: "error",
            ErrorLevel.WARNING: "warning",
            ErrorLevel.INFO: "info",
        }.get(level, "error")
        try:
            getattr(self.logger, method)(message)
        except Exception:
            try:
                # 最低限stderrへ
                import sys as _sys
                _sys.stderr.write(str(message)+"\n")
            except Exception:
                pass
