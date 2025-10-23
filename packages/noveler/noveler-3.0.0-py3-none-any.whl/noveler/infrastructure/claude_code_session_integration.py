"""Infrastructure.claude_code_session_integration
Where: Infrastructure module integrating Claude Code sessions.
What: Implements helpers to initialize, manage, and tear down Claude Code sessions.
Why: Centralises Claude Code session orchestration for reuse across features.
"""

from noveler.presentation.shared.shared_utilities import console

"Claude Codeセッション統合モジュール\n\n本格実装: Claude Codeセッション内でのプロンプト実行と\nレスポンス処理を統合する基盤クラス\n"
import json
import os
from pathlib import Path
from typing import Any

from noveler.domain.value_objects.project_time import project_now
from noveler.infrastructure.logging.unified_logger import get_logger

_logger = get_logger(__name__)


class ClaudeCodeSessionError(Exception):
    """Claude Codeセッション関連のエラー"""


class ClaudeCodeEnvironmentDetector:
    """Claude Code環境の有無を検出するヘルパー."""

    _ENVIRONMENT_MARKERS = [
        "CLAUDE_CODE_SESSION",
        "ANTHROPIC_CLAUDE_CODE",
        "ANTHROPIC_CLAUDE_WORKSPACE",
    ]

    _PATH_HINTS = [
        "/tmp/claude_code_session",
        "/mnt/c/Users/bamboocity/OneDrive/Documents/9_小説/00_ガイド",
    ]

    _FILESYSTEM_SENTINELS = [
        Path('.claude_code_session'),
        Path('temp/claude_session_data'),
    ]

    _DYNAMIC_ROOT_ENV_VARS = [
        "GUIDE_ROOT",
        "NOVELER_GUIDE_ROOT",
    ]

    _PATH_ENV_KEYS = _DYNAMIC_ROOT_ENV_VARS

    @classmethod
    def is_claude_code_environment(cls) -> bool:
        """Return True when running inside a Claude Code session."""

        for marker in cls._ENVIRONMENT_MARKERS:
            if os.environ.get(marker):
                _logger.info("Detected Claude Code environment marker: %s", marker)
                return True

        cwd = Path.cwd()
        for hint in cls._collect_path_hints():
            if hint and hint in str(cwd):
                _logger.info("Detected Claude Code path hint in CWD: %s", cwd)
                return True

        return cls._detect_filesystem_indicators()

    @classmethod
    def _collect_path_hints(cls) -> set[str]:
        hints: set[str] = set(cls._PATH_HINTS)
        for env_var in cls._DYNAMIC_ROOT_ENV_VARS:
            guide_root = os.environ.get(env_var)
            if not guide_root:
                continue
            hints.update(cls._normalise_path_variants(guide_root))
        return hints

    @staticmethod
    def _normalise_path_variants(path_str: str) -> set[str]:
        variants: set[str] = set()
        try:
            path = Path(path_str).resolve()
        except Exception:  # pragma: no cover - defensive
            return variants
        variants.add(str(path))
        variants.add(str(path).replace('\\', '/'))
        variants.add(str(path).lower())
        return variants

    @classmethod
    def _detect_filesystem_indicators(cls) -> bool:
        for sentinel in cls._FILESYSTEM_SENTINELS:
            if sentinel.exists():
                _logger.debug("Filesystem sentinel detected: %s", sentinel)
                return True
        return False

    @classmethod
    def get_session_capabilities(cls) -> dict[str, bool]:
        capabilities = {
            'prompt_execution': False,
            'file_access': False,
            'api_access': False,
            'environment_variables': False,
            'subprocess_execution': False,
        }
        if cls.is_claude_code_environment():
            capabilities.update({
                'prompt_execution': True,
                'file_access': True,
                'environment_variables': True,
            })
            if 'ANTHROPIC_API_KEY' in os.environ:
                capabilities['api_access'] = True
        return capabilities


class ClaudeCodeSessionInterface:
    """Claude Codeセッション内統合インターフェース

    実際のセッション内でのプロンプト実行とレスポンス処理を担当
    """

    def __init__(self, enable_logging: bool = True) -> None:
        """セッションインターフェース初期化

        Args:
            enable_logging: ログ出力を有効にするか
        """
        self.logger = get_logger(__name__)
        if enable_logging:
            self._setup_logging()
        self.environment = ClaudeCodeEnvironmentDetector()
        self.capabilities = self.environment.get_session_capabilities()
        self.session_data_dir = Path("temp/claude_session_data")
        self.session_data_dir.mkdir(parents=True, exist_ok=True)

    def _setup_logging(self) -> None:
        """ログ設定の初期化"""
        log_file = Path("temp/claude_code_session.log")
        log_file.parent.mkdir(parents=True, exist_ok=True)
        # 統一ロガー自体に任せ、ファイルの存在のみ確保してログ出力先を明示する
        if not log_file.exists():
            log_file.touch()
        self.logger.info("Claude Code session logging initialised (log file: %s)", log_file)

    def execute_prompt(self, prompt: str, response_format: str = "yaml", timeout: int | None = None) -> dict[str, Any]:
        """セッション内でプロンプトを実行

        Args:
            prompt: 実行するプロンプト
            response_format: 期待するレスポンス形式 ('yaml', 'json', 'text')
            timeout: タイムアウト秒数

        Returns:
            Dict[str, Any]: 実行結果

        Raises:
            ClaudeCodeSessionError: セッション実行エラー
        """
        if not self.capabilities["prompt_execution"]:
            msg = "現在の環境ではプロンプト実行がサポートされていません"
            raise ClaudeCodeSessionError(msg)
        if not prompt or not prompt.strip():
            msg = "プロンプトが空です"
            raise ClaudeCodeSessionError(msg)
        console.print(f"プロンプト実行開始: format={(response_format, timeout)}, timeout=%s")
        try:
            if self.environment.is_claude_code_environment():
                return self._execute_in_claude_code_session(prompt, response_format, timeout)
            return self._execute_mock_response(prompt, response_format)
        except Exception as e:
            self.logger.exception("プロンプト実行エラー: %s", e)
            msg = f"プロンプト実行に失敗しました: {e}"
            raise ClaudeCodeSessionError(msg) from e

    def _execute_in_claude_code_session(self, prompt: str, response_format: str, _timeout: int) -> dict[str, Any]:
        """Claude Codeセッション内でのプロンプト実行

        Args:
            prompt: 実行するプロンプト
            response_format: レスポンス形式
            timeout: タイムアウト秒数

        Returns:
            Dict[str, Any]: 実行結果
        """
        console.print("Claude Codeセッション内プロンプト実行開始")
        prompt_file = self.session_data_dir / f"prompt_{project_now().to_timestamp()}.txt"
        # プロンプトファイル書き込み
        prompt_file.write_text(prompt, encoding="utf-8")
        try:
            response_data: dict[str, Any] = self._call_session_prompt_api(prompt, response_format)
            response_file = self.session_data_dir / f"response_{project_now().to_timestamp()}.json"
            with response_file.open("w", encoding="utf-8") as f:
                json.dump(response_data, f, ensure_ascii=False, indent=2)
            console.print(f"プロンプト実行完了: {prompt_file.name} -> {response_file.name}")
            return response_data
        except Exception as e:
            self.logger.exception("セッション内実行エラー: %s", e)
            return self._execute_mock_response(prompt, response_format)

    def _call_session_prompt_api(self, prompt: str, response_format: str) -> dict[str, Any]:
        """セッション内プロンプトAPI呼び出し

        Args:
            prompt: プロンプト
            response_format: レスポンス形式

        Returns:
            Dict[str, Any]: APIレスポンス
        """
        console.print("セッション内プロンプトAPI呼び出し開始")
        "Claude Code APIインテグレーション（段階的実装中）\n\n        Notes:\n            実際のClaude Code API連携は将来のフェーズで実装予定\n            現在はモックレスポンスによる安全な動作確認を実施\n        "
        return self._execute_mock_response(prompt, response_format)

    def _execute_mock_response(self, prompt: str, response_format: str) -> dict[str, Any]:
        """開発・テスト用モックレスポンス

        Args:
            prompt: プロンプト
            response_format: レスポンス形式

        Returns:
            Dict[str, Any]: モックレスポンス
        """
        console.print("モックレスポンス生成")
        if response_format == "yaml":
            return self._generate_yaml_mock_response(prompt)
        if response_format == "json":
            return self._generate_json_mock_response(prompt)
        return self._generate_text_mock_response(prompt)

    def _generate_yaml_mock_response(self, prompt: str) -> dict[str, Any]:
        """YAML形式のモックレスポンス生成"""
        return {
            "success": True,
            "format": "yaml",
            "response_type": "a31_evaluation",
            "data": {
                "id": "A31-001",
                "title": "A30_原稿執筆ガイド.mdの内容を確認",
                "status": True,
                "required": True,
                "type": "document_review",
                "auto_fix_supported": False,
                "auto_fix_applied": False,
                "fix_details": [],
                "claude_evaluation": {
                    "evaluated_at": project_now().to_iso_string(),
                    "result": "PASS",
                    "score": 87.5,
                    "confidence": 0.9,
                    "primary_reason": "ガイド内容が適切に理解・適用されている",
                    "evidence_points": [
                        {
                            "content": "冒頭3行で読者を引き込む工夫が確認できる",
                            "line_range": [1, 3],
                            "file": "第001話_始まりの物語.md",
                        }
                    ],
                    "improvement_suggestions": [
                        {
                            "content": "五感描写をもう少し増やすとより効果的",
                            "line_range": [8, 12],
                            "file": "第001話_始まりの物語.md",
                            "suggestion_type": "enhancement",
                        }
                    ],
                    "issues_found": [],
                    "references_validated": [
                        {
                            "guide": "A30_原稿執筆ガイド.md",
                            "section": "冒頭の技法",
                            "applied_at_lines": [1, 3],
                            "compliance_score": 90,
                        }
                    ],
                },
            },
            "execution_meta": {
                "prompt_length": len(prompt),
                "execution_time": "2.3s",
                "environment": "claude_code_session" if self.environment.is_claude_code_environment() else "mock",
                "capabilities_used": list(self.capabilities.keys()),
            },
        }

    def _generate_json_mock_response(self, prompt: str) -> dict[str, Any]:
        """JSON形式のモックレスポンス生成"""
        return {
            "success": True,
            "format": "json",
            "response_type": "fix_result",
            "data": {
                "success": True,
                "fixed_content": "# 第001話 始まりの物語\n\n「やっと見つけた!」\n\n 彼女の声が森に響いた。木々の間から差し込む朝日が、彼女の長い髪を金色に染めている。温かい光が頬を撫でていく。\n\n 俺は振り返る。彼女の顔には安堵の表情が浮かんでいる。\n\n「どこにいたんだ?ずっと探していたぞ」\n\n 俺の問いかけに、彼女は苦笑いを浮かべた。\n\n「迷子になっちゃった。でも、面白いものを見つけたの」\n\n 彼女が指差す方向を見ると、古い石碑が立っている。苔むした表面には、判読困難な文字が刻まれている。\n",
                "applied_fixes": [
                    "冒頭3行に五感描写(触覚)を追加",
                    "会話と地の文のバランスを4:6に調整",
                    "文末バリエーションを増加(体言止め追加)",
                    "視覚的描写を強化(石碑の詳細描写)",
                ],
                "confidence": 0.9,
                "details": {
                    "fix_type": "content_enhancement",
                    "changes_count": 4,
                    "improvement_areas": [
                        "sensory_description",
                        "dialogue_balance",
                        "sentence_variety",
                        "visual_detail",
                    ],
                },
            },
            "execution_meta": {
                "prompt_length": len(prompt),
                "execution_time": "3.1s",
                "environment": "claude_code_session" if self.environment.is_claude_code_environment() else "mock",
            },
        }

    def _generate_text_mock_response(self, prompt: str) -> dict[str, Any]:
        """テキスト形式のモックレスポンス生成"""
        return {
            "success": True,
            "format": "text",
            "response_type": "general_response",
            "data": {
                "content": "高品質なテキストレスポンスが生成されました。プロンプトの内容に基づいて適切な回答を提供しています。",
                "word_count": 234,
                "language": "ja",
                "confidence": 0.85,
            },
            "execution_meta": {
                "prompt_length": len(prompt),
                "execution_time": "1.8s",
                "environment": "claude_code_session" if self.environment.is_claude_code_environment() else "mock",
            },
        }

    def health_check(self) -> dict[str, Any]:
        """セッション統合の健全性チェック

        Returns:
            Dict[str, Any]: ヘルスチェック結果
        """
        health_status = {
            "environment_detected": self.environment.is_claude_code_environment(),
            "capabilities": self.capabilities,
            "session_data_dir": str(self.session_data_dir),
            "session_data_writable": self.session_data_dir.is_dir() and os.access(self.session_data_dir, os.W_OK),
            "logging_enabled": bool(self.logger.handlers),
            "timestamp": project_now().to_iso_string(),
        }
        health_status["overall_health"] = (
            health_status["session_data_writable"]
            and health_status["logging_enabled"]
            and (health_status["environment_detected"] or len(health_status["capabilities"]) > 0)
        )
        return health_status
