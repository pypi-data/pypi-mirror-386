"""Application service that produces user-friendly status and error messages."""

from noveler.presentation.shared.shared_utilities import console
import re
import secrets
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from noveler.domain.interfaces.logger_service_protocol import ILoggerService


class MessageType(Enum):
    """Enumeration representing supported message moods."""

    ERROR = "error"
    WARNING = "warning"
    SUCCESS = "success"
    INFO = "info"


@dataclass
class UserMessage:
    """Value object encapsulating a user-facing message."""

    original: str
    friendly: str
    solutions: list[str]
    message_type: MessageType
    note: str | None = None

    def get_display_text(self) -> str:
        """Return a formatted string suitable for console presentation."""
        lines = []
        lines.append("")
        lines.append("=" * 60)
        lines.append(self.friendly)
        lines.append("")
        if self.note:
            lines.append(f"📌 {self.note}")
            lines.append("")
        if self.solutions:
            lines.append("💡 解決方法:")
            for solution in self.solutions:
                if solution.startswith("  "):
                    lines.append(solution)
                else:
                    lines.append(f"  {solution}")
            lines.append("")
        if self.message_type == MessageType.ERROR:
            lines.append("🔍 技術的な詳細:")
            lines.append(f"  {self.original}")
            lines.append("")
        lines.append("=" * 60)
        lines.append("")
        return "\n".join(lines)


class MessageService:
    """Service that generates user-friendly status, warning, and error messages."""

    def __init__(self, logger_service: "ILoggerService") -> None:
        """Initialize the service and load predefined error messaging patterns.

        Args:
            logger_service: Logger injected via dependency inversion.
        """
        self.logger = logger_service
        self._initialize_patterns()

    def _initialize_patterns(self) -> None:
        """Populate regex patterns and associated remediation templates."""
        self.error_patterns = {
            "ModuleNotFoundError.*'([^']+)'": {
                "message": "📦 必要なプログラムが見つかりません:{0}",
                "solutions": [
                    "以下のコマンドでインストールしてください:",
                    "  pip install {0}",
                    "または、requirements.txtがある場合:",
                    "  pip install -r requirements.txt",
                ],
            },
            "ModuleNotFoundError.*": {
                "message": "📦 必要なプログラムパッケージが見つかりません",
                "solutions": [
                    "以下のコマンドでインストールしてください:",
                    "  pip install [パッケージ名]",
                    "または、requirements.txtがある場合:",
                    "  pip install -r requirements.txt",
                ],
            },
            "FileNotFoundError.*'([^']+)'": {
                "message": "📄 ファイルが見つかりません:{0}",
                "solutions": [
                    "ファイルパスを確認してください",
                    "ファイルが正しい場所にあるか確認してください",
                    "ファイル名のスペルを確認してください",
                ],
            },
            "FileNotFoundError.*": {
                "message": "📄 ファイルが見つかりません",
                "solutions": [
                    "ファイルパスを確認してください",
                    "ファイルが正しい場所にあるか確認してください",
                    "ファイル名のスペルを確認してください",
                ],
            },
            "PermissionError.*'([^']+)'": {
                "message": "🔒 ファイルにアクセスする権限がありません:{0}",
                "solutions": [
                    "ファイルが他のプログラムで開かれていないか確認",
                    "ファイルの読み取り権限を確認",
                    "管理者権限で実行してみてください",
                ],
            },
            "UnicodeDecodeError": {
                "message": "📝 ファイルの文字コードに問題があります",
                "solutions": [
                    "ファイルをUTF-8形式で保存し直してください",
                    "テキストエディタで「名前を付けて保存」→「エンコード:UTF-8」",
                    "メモ帳の場合:保存時に「UTF-8」を選択",
                ],
            },
            "YAMLError.*line (\\d+)": {
                "message": "📋 設定ファイル(YAML)の{0}行目に書式エラーがあります",
                "solutions": [
                    "インデント(字下げ)を確認してください",
                    "スペースとタブが混在していないか確認",
                    "コロン(:)の後にスペースがあるか確認",
                    "文字列に特殊文字がある場合は引用符で囲む",
                ],
            },
            "scanner.*could not find expected": {
                "message": "📋 YAML設定ファイルの書式に問題があります",
                "solutions": [
                    "括弧やクオートが正しく閉じられているか確認",
                    "インデントを確認(スペース2個または4個で統一)",
                    "オンラインYAMLチェッカーで検証してみてください",
                ],
            },
            "ConnectionError|requests\\.exceptions\\.ConnectionError": {
                "message": "🌐 インターネット接続に問題があります",
                "solutions": [
                    "インターネット接続を確認してください",
                    "プロキシ設定を確認してください",
                    "ファイアウォールが通信をブロックしていないか確認",
                ],
            },
            "TimeoutError|ReadTimeout": {
                "message": "⏰ 処理時間が長すぎて中断されました",
                "solutions": [
                    "もう一度実行してみてください",
                    "インターネット接続が不安定な可能性があります",
                    "大きなファイルの場合、時間をおいて再実行",
                ],
            },
            "novel.*command not found": {
                "message": "🛠️ novelコマンドが見つかりません",
                "solutions": [
                    "以下のコマンドを実行してください:",
                    "  source path/to/setup_env.sh",
                    "または新しいターミナルを開いてください",
                    "インストールが完了しているか確認してください",
                ],
            },
            "プロジェクトディレクトリで実行": {
                "message": "📁 プロジェクトフォルダで実行する必要があります",
                "solutions": [
                    "小説プロジェクトのフォルダに移動してください",
                    "例:cd 01_あなたの小説名",
                    "「プロジェクト設定.yaml」があるフォルダで実行",
                ],
            },
            "設定ファイルが存在しません": {
                "message": "⚙️ プロジェクト設定が見つかりません",
                "solutions": [
                    "「プロジェクト設定.yaml」ファイルが必要です",
                    '新規プロジェクト作成:novel new "作品名"',
                    "既存プロジェクトの場合:設定ファイルを確認",
                ],
            },
            "No module named 'janome'": {
                "message": "📚 日本語解析ライブラリ(janome)がありません",
                "solutions": [
                    "以下のコマンドでインストールしてください:",
                    "  pip install janome",
                    "または:pip install -r requirements.txt",
                ],
            },
            "No module named 'yaml'|No module named 'pyyaml'": {
                "message": "📄 YAML処理ライブラリがありません",
                "solutions": ["以下のコマンドでインストールしてください:", "  pip install PyYAML"],
            },
            "No module named 'requests'": {
                "message": "🌐 HTTP通信ライブラリ(requests)がありません",
                "solutions": ["以下のコマンドでインストールしてください:", "  pip install requests"],
            },
        }
        self.warning_patterns = {
            "形態素解析器が利用できません": {
                "message": "📝 より高度な日本語解析機能が利用できません",
                "note": "基本機能は動作しますが、詳細な解析には制限があります",
                "solutions": [
                    "より詳細な解析を行いたい場合:",
                    "  pip install janome",
                    "現在の機能でも十分使用できます",
                ],
            },
            "オプションパッケージ.*利用できません": {
                "message": "📦 オプション機能が利用できません",
                "note": "基本機能には影響ありません",
                "solutions": [
                    "必要に応じて以下をインストール:",
                    "  pip install lxml beautifulsoup4",
                    "すぐには必要ないので後でも大丈夫です",
                ],
            },
        }
        self.success_enhancements = {"✅": "🎉", "完了": "完了しました!", "成功": "成功しました!", "OK": "順調です!"}

    def create_user_message(self, message: str, message_type: MessageType) -> UserMessage:
        """Transform a technical message into a user-friendly representation.

        Args:
            message: Raw message string captured from the system.
            message_type: Classification that guides tone and remediation.

        Returns:
            UserMessage: Structured output containing friendly text and solutions.
        """
        patterns = self.error_patterns if message_type == MessageType.ERROR else self.warning_patterns
        for pattern, enhancement in patterns.items():
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                groups = match.groups()
                friendly_message = enhancement["message"].format(*groups) if groups else enhancement["message"]
                return UserMessage(
                    original=message,
                    friendly=friendly_message,
                    solutions=enhancement.get("solutions", []),
                    message_type=message_type,
                    note=enhancement.get("note"),
                )
        return UserMessage(
            original=message,
            friendly=self._general_improvement(message, message_type),
            solutions=self._general_solutions(message_type),
            message_type=message_type,
        )

    def _general_improvement(self, message: str, message_type: MessageType) -> str:
        """Produce a friendlier variant of the provided message."""
        replacements = {
            "traceback": "エラーの詳細",
            "exception": "エラー",
            "stderr": "エラー出力",
            "stdout": "実行結果",
            "argv": "コマンド引数",
            "subprocess": "外部プログラム実行",
            "encoding": "文字コード",
            "unicode": "文字コード",
            "path": "ファイルパス",
            "directory": "フォルダ",
            "module": "プログラムモジュール",
        }
        improved = message
        for tech_term, friendly_term in replacements.items():
            improved = re.sub("\\b" + tech_term + "\\b", friendly_term, improved, flags=re.IGNORECASE)
        if message_type == MessageType.ERROR:
            if not improved.startswith(("❌", "🚫", "⚠️")):
                improved = "❌ " + improved
        elif message_type == MessageType.WARNING:
            if not improved.startswith(("⚠️", "🔔", "💡")):
                improved = "⚠️ " + improved
        elif message_type == MessageType.SUCCESS and (not improved.startswith(("✅", "🎉", "👍"))):
            improved = "🎉 " + improved
        return improved

    def _general_solutions(self, message_type: MessageType) -> list[str]:
        """Return default solution hints based on message severity."""
        if message_type == MessageType.ERROR:
            return [
                "問題が解決しない場合:",
                "  1. novel doctor でシステム診断を実行",
                "  2. novel status で現在の状態を確認",
                "  3. 00_マスターガイド/00_クイックスタート.md で基本的な使い方を確認",
            ]
        if message_type == MessageType.WARNING:
            return ["この警告は通常、動作に影響しません", "気になる場合は novel doctor で詳細確認"]
        return []

    def enhance_success_message(self, message: str) -> str:
        """Add celebratory embellishments to a success message."""
        enhanced = message
        for old, new in self.success_enhancements.items():
            enhanced = enhanced.replace(old, new)
        encouragements = ["素晴らしい!", "完璧です!", "お疲れ様でした!", "順調に進んでいます!"]
        if any(word in message for word in ["完了", "成功", "作成", "保存"]):
            enhanced += f" {secrets.choice(encouragements)}"
        return enhanced

    def show_error(self, error: Exception, context: str | None) -> None:
        """Render an error to the console using the friendly formatting pipeline."""
        error_message = str(error)
        if context:
            error_message = f"{context}: {error_message}"
        user_message = self.create_user_message(error_message, MessageType.ERROR)
        console.print(user_message.get_display_text())

    def show_warning(self, message: str) -> None:
        """Render a warning to the console using the friendly formatting pipeline."""
        user_message = self.create_user_message(message, MessageType.WARNING)
        console.print(user_message.get_display_text())

    def show_success(self, message: str) -> None:
        """Render a success message with additional encouragement."""
        enhanced = self.enhance_success_message(message)
        console.print(f"\n{enhanced}\n")

    def check_common_issues(self) -> list[str]:
        """Return proactive advice for frequently observed setup issues."""
        advice = []

        def check_package_available(package_name: str) -> bool:
            """Return ``True`` when the given Python package can be imported."""
            try:
                __import__(package_name)
                return True
            except ImportError:
                return False

        missing_packages = [
            package for package in ["yaml", "requests", "janome"] if not check_package_available(package)
        ]
        if missing_packages:
            advice.append(
                f"📦 オプションパッケージ: {', '.join(missing_packages)} をインストールすると機能が向上します"
            )
        config_file = Path.cwd() / "プロジェクト設定.yaml"
        if not config_file.exists() and Path.cwd().name != "00_ガイド":
            advice.append(
                "⚙️ プロジェクト設定.yamlが見つかりません。novel new コマンドで新規作成するか、プロジェクトフォルダに移動してください"
            )
        return advice
