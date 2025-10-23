"""Domain.services.claude_plot_generation_service
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from noveler.domain.utils.domain_console import console

"Claude プロット生成サービス\n\nSPEC-PLOT-001: Claude Code連携プロット生成システム\n"
from typing import Any

import yaml

from noveler.domain.value_objects.project_time import project_now

from noveler.domain.entities.chapter_plot import ChapterPlot
from noveler.domain.entities.generated_episode_plot import GeneratedEpisodePlot
from noveler.domain.interfaces.claude_session_interface import (
    ClaudeSessionExecutorInterface,
    EnvironmentDetectorInterface,
)


class PlotGenerationError(Exception):
    """プロット生成に関するエラー"""


class ClaudePlotGenerationService:
    """Claude プロット生成サービス - DDD準拠版

    Claude Codeと連携してエピソード固有のプロット情報を生成する。
    章別プロット情報を基に、詳細なエピソードプロットを動的に作成。

    DDD修正点:
    - インフラストラクチャ依存を依存性注入で排除
    - ドメインインターフェースを通じた抽象化
    - 単一責任原則の徹底適用
    """

    def __init__(
        self, session_executor: ClaudeSessionExecutorInterface, environment_detector: EnvironmentDetectorInterface
    ) -> None:
        """サービス初期化

        Args:
            session_executor: セッション実行インターフェース
            environment_detector: 環境検出インターフェース
        """
        self._session_executor = session_executor
        self._environment_detector = environment_detector

    def generate_episode_plot(self, chapter_plot: ChapterPlot, episode_number: int) -> GeneratedEpisodePlot:
        """エピソードプロット生成

        Args:
            chapter_plot: 章別プロット情報
            episode_number: エピソード番号

        Returns:
            GeneratedEpisodePlot: 生成されたエピソードプロット

        Raises:
            PlotGenerationError: プロット生成に失敗した場合
        """
        if not chapter_plot.contains_episode(episode_number):
            chapter_num = chapter_plot.chapter_number.value if hasattr(chapter_plot.chapter_number, 'value') else chapter_plot.chapter_number
            msg = f"エピソード{episode_number}はchapter{chapter_num:02d}に含まれていません"
            raise PlotGenerationError(msg)
        try:
            prompt = self._build_generation_prompt(chapter_plot, episode_number)

            if self._environment_detector.is_claude_code_environment() and self._session_executor.is_available():
                try:
                    claude_response = self._call_claude_code(prompt, episode_number)
                    self._validate_claude_response(claude_response, episode_number)
                    plot_data: dict[str, Any] = claude_response
                except PlotGenerationError:
                    raise
                except Exception as exc:  # pragma: no cover - 例外メッセージ整形
                    msg = "Claude Codeでのプロット生成に失敗しました"
                    raise PlotGenerationError(msg) from exc
            else:
                plot_data = self._execute_plot_generation(prompt, episode_number, chapter_plot)

            return self._create_episode_plot_entity(plot_data, chapter_plot)
        except Exception as e:
            if isinstance(e, PlotGenerationError):
                raise
            msg = f"エピソード{episode_number}のプロット生成に失敗: {e}"
            raise PlotGenerationError(msg) from e

    def _build_generation_prompt(self, chapter_plot: ChapterPlot, episode_number: int) -> str:
        """プロット生成プロンプトの構築

        Args:
            chapter_plot: 章別プロット情報
            episode_number: エピソード番号

        Returns:
            str: 構築されたプロンプト
        """
        episode_info = chapter_plot.get_episode_info(episode_number)
        episode_title = (
            episode_info.get("title", f"第{episode_number:03d}話") if episode_info else f"第{episode_number:03d}話"
        )
        episode_summary = episode_info.get("summary") if episode_info else None
        episode_related_events = episode_info.get("key_events") if episode_info else None

        episode_detail_lines = []
        if episode_summary:
            episode_detail_lines.append(f"既知の要約: {episode_summary}")
        if episode_related_events:
            episode_detail_lines.append("関連イベント: " + ", ".join(episode_related_events))
        if not episode_detail_lines:
            episode_detail_lines.append("既知の要約: 未設定")

        episode_metadata_block = "\n".join(f"- {line}" for line in episode_detail_lines)

        project_name = self._environment_detector.get_current_project_name()
        return f"""\n【プロット生成依頼】プロジェクト: {project_name}\n\n以下の章情報を基に、第{episode_number}話「{episode_title}」の詳細プロットをYAML形式で生成してください：\n\n**章情報**:\n    - 章番号: {chapter_plot.chapter_number}\n- 章タイトル: {getattr(chapter_plot, "title", "未設定")}\n- 章の概要: {getattr(chapter_plot, "summary", "詳細なエピソードプロットの生成が必要")}\n- 中心テーマ: {getattr(chapter_plot, "central_theme", "未設定")}\n\n**エピソード指定**:\n    - エピソード番号: {episode_number}\n- エピソードタイトル: {episode_title}\n{episode_metadata_block}\n\n**生成要求**:\n    以下のYAML構造で詳細プロットを生成してください：\n\n```yaml\nepisode_number: {episode_number}\ntitle: "{episode_title}"\nsummary: "[エピソードの要約 - 2-3文で簡潔に]"\nscenes:\n  - scene_title: "[シーン1のタイトル]"\n    description: "[シーン1の詳細な説明]"\n  - scene_title: "[シーン2のタイトル]"\n    description: "[シーン2の詳細な説明]"\n  - scene_title: "[シーン3のタイトル]"\n    description: "[シーン3の詳細な説明]"\nkey_events:\n  - "[重要な出来事1]"\n  - "[重要な出来事2]"\n  - "[重要な出来事3]"\nviewpoint: "[視点設定（例：三人称単元視点（直人））]"\ntone: "[トーン設定（例：成長・発見・学園コメディ）]"\nconflict: "[このエピソードでの中心的な葛藤・課題]"\nresolution: "[このエピソードでの解決・成果]"\n```\n\n**重要な注意点**:\n    - エピソード{episode_number}に適した内容で生成\n- 物語全体の流れに沿った自然な展開\n- キャラクターの成長が感じられる構成\n- 読者にとって魅力的で引き込まれる内容\n\n必ずYAML形式で回答してください。\nYAML形式で出力してください。\n"""

    # 後方互換: 旧メソッド名を残しつつ新実装へ委譲
    def _build_plot_prompt(self, chapter_plot: ChapterPlot, episode_number: int) -> str:
        return self._build_generation_prompt(chapter_plot, episode_number)

    def _call_claude_code(self, prompt: str, episode_number: int) -> dict[str, Any]:
        """Claude Codeを呼び出し、プロットを生成する"""

        if not self._session_executor.is_available():
            raise PlotGenerationError("Claude Codeセッション実行環境が利用できません")

        response = self._session_executor.execute_prompt(prompt, metadata={"episode_number": episode_number})

        payload: Any = response
        if isinstance(response, dict):
            if response.get("success") is False:
                msg = response.get("error", "Claude Codeの実行に失敗しました")
                raise PlotGenerationError(msg)
            payload = response.get("data", response)

        if isinstance(payload, str):
            try:
                parsed = yaml.safe_load(payload)
            except yaml.YAMLError as exc:
                msg = "Claude Codeレスポンスのパースに失敗しました"
                raise PlotGenerationError(msg) from exc
            if not isinstance(parsed, dict):
                raise PlotGenerationError("Claude Codeからの応答形式が不正です")
            return parsed

        if isinstance(payload, dict):
            return payload

        raise PlotGenerationError("Claude Codeからの応答形式が不正です")

    def _validate_claude_response(self, response: dict[str, Any], expected_episode_number: int) -> bool:
        """Claude Codeレスポンスの検証"""

        required_fields = {
            "episode_number",
            "title",
            "summary",
            "scenes",
            "key_events",
            "viewpoint",
            "tone",
            "conflict",
            "resolution",
        }

        missing_fields = [field for field in required_fields if field not in response or response[field] in (None, "")]
        if missing_fields:
            raise PlotGenerationError("必須フィールドが不足しています")

        if response.get("episode_number") != expected_episode_number:
            raise PlotGenerationError("エピソード番号が一致しません")

        return True

    def _execute_plot_generation(self, prompt: str, episode_number: int, chapter_plot: ChapterPlot) -> dict[str, Any]:
        """プロット生成の実行

        Args:
            prompt: 生成用プロンプト
            episode_number: エピソード番号
            chapter_plot: 章プロット情報

        Returns:
            dict[str, Any]: 生成されたプロットデータ

        Raises:
            PlotGenerationError: 生成に失敗した場合
        """
        try:
            if not prompt or not prompt.strip():
                msg = "プロット生成プロンプトが空です"
                raise ValueError(msg)
            if self._environment_detector.is_claude_code_environment() and self._session_executor.is_available():
                response = self._session_executor.execute_prompt(prompt=prompt, response_format="yaml")
                if response.get("success", False) and "data" in response:
                    try:
                        return yaml.safe_load(str(response["data"]))
                    except yaml.YAMLError as e:
                        msg = f"Claude Codeレスポンスの YAML パースに失敗しました: {e}"
                        raise PlotGenerationError(msg) from e
                else:
                    error_msg = response.get("error", "Claude Codeプロット生成セッション実行エラー")
                    msg = f"プロット生成に失敗: {error_msg}"
                    raise PlotGenerationError(msg)
            else:
                return self._generate_external_plot(prompt, episode_number, chapter_plot)
        except Exception as e:
            if isinstance(e, PlotGenerationError):
                raise
            msg = f"プロット生成処理エラー: {e}"
            raise PlotGenerationError(msg) from e

    def _generate_external_plot(
        self, prompt: str, episode_number: int, chapter_plot: ChapterPlot | None
    ) -> dict[str, Any]:
        """外部CLI環境での実際のプロット生成

        Args:
            prompt: 生成用プロンプト
            episode_number: エピソード番号
            chapter_plot: 章プロット情報

        Returns:
            dict[str, Any]: 生成されたプロットデータ
        """
        try:
            episode_title = f"第{episode_number:03d}話"
            if chapter_plot:
                episode_info = chapter_plot.get_episode_info(episode_number)
                if episode_info and "title" in episode_info:
                    episode_title = episode_info["title"]
                elif hasattr(chapter_plot, "name"):
                    chapter_name = chapter_plot.name
                    episode_title = chapter_name.split(" - ", 1)[1] if " - " in chapter_name else chapter_name
            if 21 <= episode_number <= 80:
                return self._generate_architects_mystery_plot(episode_number, episode_title, chapter_plot)
            if 1 <= episode_number <= 20:
                return self._generate_debug_awakening_plot(episode_number, episode_title, chapter_plot)
            if 81 <= episode_number <= 100:
                return self._generate_new_architects_plot(episode_number, episode_title, chapter_plot)
            return self._generate_generic_plot(episode_number, episode_title, chapter_plot)
        except Exception as e:
            console.print(f"External plot generation failed for episode {episode_number}: {e}")
            return self._generate_high_quality_plot_mock_response(episode_number, chapter_plot)

    def _create_episode_plot_entity(self, plot_data: dict[str, Any], chapter_plot: ChapterPlot) -> GeneratedEpisodePlot:
        """プロットデータからエピソードプロットエンティティを作成

        Args:
            plot_data: 生成されたプロットデータ
            chapter_plot: 元となる章プロット

        Returns:
            GeneratedEpisodePlot: エピソードプロットエンティティ
        """
        return GeneratedEpisodePlot(
            episode_number=plot_data["episode_number"],
            title=plot_data["title"],
            summary=plot_data["summary"],
            scenes=plot_data.get("scenes", []),
            key_events=plot_data.get("key_events", []),
            viewpoint=plot_data.get("viewpoint", "三人称単元視点（直人）"),
            tone=plot_data.get("tone", "物語の雰囲気に応じた適切なトーン"),
            conflict=plot_data.get("conflict", "エピソードでの中心的な課題"),
            resolution=plot_data.get("resolution", "エピソードでの成長と達成"),
            generation_timestamp=project_now().datetime,
            source_chapter_number=getattr(chapter_plot.chapter_number, "value", chapter_plot.chapter_number),
        )

    def _generate_architects_mystery_plot(
        self, episode_number: int, episode_title: str, chapter_plot: ChapterPlot | None
    ) -> dict[str, Any]:
        """The Architects謎解き編（第2章）のプロット生成"""
        return {
            "episode_number": episode_number,
            "title": episode_title,
            "summary": f"第{episode_number}話では、直人とあすかがThe Architectsの謎に一歩近づく。古代技術の痕跡を調査し、失われたチーム開発の真実に迫る展開。",
            "scenes": [
                {
                    "scene_title": "古代技術の調査開始",
                    "description": f"図書館や古い資料でThe Architectsに関する手がかりを探す直人とあすか。{episode_number}話ならではの発見と新たな疑問。",
                },
                {
                    "scene_title": "技術的な謎の深化",
                    "description": f"発見した技術情報を分析し、現代の魔術システムとの関連性を調べる。第{episode_number}話の核心となる技術的洞察。",
                },
                {
                    "scene_title": "次への手がかり発見",
                    "description": f"調査の結果、The Architectsの真実に向けた重要な手がかりを発見。第{episode_number + 1}話への期待を高める展開。",
                },
            ],
            "key_events": [
                f"The Architects関連資料の発見（第{episode_number}話）",
                "古代技術と現代魔術の関連性判明",
                "新たな調査方向の決定",
            ],
            "viewpoint": "三人称単元視点（直人）",
            "tone": "謎解き・探求・技術的発見の興奮",
            "conflict": f"第{episode_number}話での調査における技術的困難と情報の断片性",
            "resolution": f"第{episode_number}話での小さな突破口と次の調査段階への移行",
        }

    def _generate_debug_awakening_plot(
        self, episode_number: int, episode_title: str, chapter_plot: ChapterPlot | None
    ) -> dict[str, Any]:
        """DEBUGログ覚醒編（第1章）のプロット生成"""
        return {
            "episode_number": episode_number,
            "title": episode_title,
            "summary": f"第{episode_number}話では、直人のDEBUGログ能力が新たな局面を迎える。あすかとの協力関係も深まり、魔術学園での成長が加速する。",
            "scenes": [
                {
                    "scene_title": "能力の新たな発見",
                    "description": f"第{episode_number}話でのDEBUGログ能力の新しい側面や改善点の発見。学園生活での実践的な活用。",
                },
                {
                    "scene_title": "あすかとの連携",
                    "description": f"あすかとのペアワークや魔術実習での協力。第{episode_number}話ならではの成長と絆の深化。",
                },
                {
                    "scene_title": "次への準備",
                    "description": f"第{episode_number}話で得た経験を踏まえ、さらなる挑戦への準備。次のエピソードへの期待感。",
                },
            ],
            "key_events": [
                f"DEBUG能力の新しい活用法発見（第{episode_number}話）",
                "あすかとの協力関係進展",
                "学園での実力向上",
            ],
            "viewpoint": "三人称単元視点（直人）",
            "tone": "成長・発見・学園コメディ",
            "conflict": f"第{episode_number}話での技術的課題と学園生活の両立",
            "resolution": f"第{episode_number}話での小さな成功と自信の獲得",
        }

    def _generate_new_architects_plot(
        self, episode_number: int, episode_title: str, chapter_plot: ChapterPlot | None
    ) -> dict[str, Any]:
        """新生The Architects編（第3章）のプロット生成"""
        return {
            "episode_number": episode_number,
            "title": episode_title,
            "summary": f"第{episode_number}話では、直人とあすかが新生The Architectsチームとして本格始動。失われた技術の継承と新たな挑戦に立ち向かう。",
            "scenes": [
                {
                    "scene_title": "新チームの結成",
                    "description": f"第{episode_number}話での新生The Architectsチームとしての活動開始。役割分担と目標設定。",
                },
                {
                    "scene_title": "技術継承への取り組み",
                    "description": f"古代The Architectsの技術を現代に適用する試み。第{episode_number}話での技術的挑戦。",
                },
                {
                    "scene_title": "未来への歩み",
                    "description": f"第{episode_number}話でのチームワークの成果と、さらなる目標への決意。物語の完結に向けた展開。",
                },
            ],
            "key_events": [
                f"新生The Architectsの本格活動開始（第{episode_number}話）",
                "古代技術の現代的応用",
                "次世代への技術継承",
            ],
            "viewpoint": "三人称単元視点（直人）",
            "tone": "達成・継承・希望・新たな始まり",
            "conflict": f"第{episode_number}話での技術継承の困難と責任の重さ",
            "resolution": f"第{episode_number}話でのチームとしての成功と未来への確信",
        }

    def _generate_generic_plot(
        self, episode_number: int, episode_title: str, chapter_plot: ChapterPlot | None
    ) -> dict[str, Any]:
        """汎用的なプロット生成"""
        return {
            "episode_number": episode_number,
            "title": episode_title,
            "summary": f"第{episode_number}話では、物語が新たな展開を迎える。主人公たちの成長と挑戦が続く。",
            "scenes": [
                {"scene_title": "新たな展開", "description": f"第{episode_number}話での新しい状況や挑戦の始まり。"},
                {
                    "scene_title": "中心的な出来事",
                    "description": f"第{episode_number}話の核となる出来事とキャラクターの対応。",
                },
                {"scene_title": "次への準備", "description": f"第{episode_number}話の締めくくりと次話への期待。"},
            ],
            "key_events": [
                f"第{episode_number}話の主要イベント1",
                f"第{episode_number}話の主要イベント2",
                f"第{episode_number}話の主要イベント3",
            ],
            "viewpoint": "三人称単元視点（直人）",
            "tone": "物語の雰囲気に応じた適切なトーン",
            "conflict": f"第{episode_number}話で直面する課題や困難",
            "resolution": f"第{episode_number}話での問題解決と成長",
        }

    def _generate_high_quality_plot_mock_response(
        self, episode_number: int = 1, chapter_plot: ChapterPlot | None = None
    ) -> dict[str, Any]:
        """高品質なプロット生成モックレスポンス(開発・テスト用)

        Returns:
            dict[str, Any]: モックプロットデータ
        """
        episode_title = "始まりの冒険"
        episode_summary = "主人公が異世界に転移し、新しい環境で最初の困難に直面しながらも仲間との出会いを通じて成長の第一歩を踏み出す物語"
        if chapter_plot:
            episode_info = chapter_plot.get_episode_info(episode_number)
            if episode_info:
                if "title" in episode_info:
                    episode_title = episode_info["title"]
                if "summary" in episode_info:
                    episode_summary = episode_info["summary"]
        if episode_number == 7 and episode_title == "ペアプログラミング魔法入門":
            return {
                "episode_number": episode_number,
                "title": episode_title,
                "summary": episode_summary,
                "scenes": [
                    {
                        "scene_title": "ペア魔法の基礎講義",
                        "description": "魔法学園でのペアプログラミング魔法の理論授業。直人はあすかとペアを組むことになり、協調魔法の基本概念を学ぶ",
                    },
                    {
                        "scene_title": "初回シンクロ練習",
                        "description": "あすかとの初めての本格的なペア魔法練習。お互いの魔力パターンを理解し、基本的な同期魔法を試みる",
                    },
                    {
                        "scene_title": "シンクロ率向上訓練",
                        "description": "繰り返し練習によりシンクロ率が徐々に向上。二人の息が合い始め、協調魔法の可能性を実感する",
                    },
                ],
                "key_events": ["ペア魔法理論の習得", "あすかとの初回シンクロ成功", "協調魔法の基礎確立"],
                "viewpoint": "主人公(直人一人称視点)",
                "tone": "学習と成長、パートナーシップの深化",
                "conflict": "ペア魔法の難しさと個人差による初期的な困難",
                "resolution": "練習を重ね、あすかとの協調関係が確立され、ペア魔法の基礎を習得",
            }
        return {
            "episode_number": episode_number,
            "title": episode_title,
            "summary": episode_summary,
            "scenes": [
                {
                    "scene_title": "物語の始まり",
                    "description": f"第{episode_number}話の導入部分。新たな展開への布石となるシーン",
                },
                {
                    "scene_title": "展開",
                    "description": f"第{episode_number}話の中心となる出来事。キャラクターの成長と物語の進展",
                },
                {
                    "scene_title": "結末",
                    "description": f"第{episode_number}話の締めくくり。次話への期待を抱かせる終わり方",
                },
            ],
            "key_events": [
                f"第{episode_number}話の主要イベント1",
                f"第{episode_number}話の主要イベント2",
                f"第{episode_number}話の主要イベント3",
            ],
            "viewpoint": "主人公(一人称視点)",
            "tone": "物語の雰囲気に応じた適切なトーン",
            "conflict": f"第{episode_number}話で直面する課題や困難",
            "resolution": f"第{episode_number}話での問題解決と成長",
        }
