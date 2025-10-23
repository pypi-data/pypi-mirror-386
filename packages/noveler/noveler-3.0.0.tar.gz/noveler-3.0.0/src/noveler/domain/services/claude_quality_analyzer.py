"""Claude品質分析ドメインサービス
仕様: Claude Code品質チェック統合システム
"""

import time

from noveler.domain.entities.claude_quality_check_session import ClaudeQualityCheckSession, QualityCheckStage
from noveler.domain.value_objects.claude_quality_check_request import (
    ClaudeQualityCheckRequest,
    ClaudeQualityCheckResult,
)


class ClaudeQualityAnalyzer:
    """Claude品質分析ドメインサービス

    Claude Codeへの品質評価プロンプト送信と結果解析を担当するドメインサービス
    自動チェック不可能な創作的品質を専門的に評価する
    """

    def __init__(self) -> None:
        """初期化"""
        self._analysis_cache: dict[str, dict] = {}

    def analyze_manuscript_quality(
        self, session: ClaudeQualityCheckSession, request: ClaudeQualityCheckRequest
    ) -> ClaudeQualityCheckResult:
        """原稿品質分析実行

        Args:
            session: 品質チェックセッション
            request: 品質チェックリクエスト

        Returns:
            ClaudeQualityCheckResult: 品質分析結果

        Raises:
            ValueError: 無効なリクエストの場合
            RuntimeError: 分析処理でエラーが発生した場合
        """
        start_time = time.perf_counter()

        try:
            # 段階1: 準備・原稿読み込み
            session.advance_to_stage(QualityCheckStage.MANUSCRIPT_ANALYSIS)
            manuscript_content = request.get_manuscript_content()
            session.add_execution_metadata("manuscript_length", str(len(manuscript_content)))

            # 段階2: 創作的品質評価
            session.advance_to_stage(QualityCheckStage.CREATIVE_EVALUATION)
            creative_score = self._evaluate_creative_quality(manuscript_content, request, session)
            session.record_intermediate_score("creative_quality", creative_score)

            # 段階3: 読者体験評価
            session.advance_to_stage(QualityCheckStage.READER_EXPERIENCE_CHECK)
            reader_experience_score = self._evaluate_reader_experience(manuscript_content, request, session)
            session.record_intermediate_score("reader_experience", reader_experience_score)

            # 段階4: 構成妥当性評価
            session.advance_to_stage(QualityCheckStage.STRUCTURAL_VALIDATION)
            structural_score = self._evaluate_structural_coherence(manuscript_content, request, session)
            session.record_intermediate_score("structural_coherence", structural_score)

            # 段階5: 結果編纂
            session.advance_to_stage(QualityCheckStage.RESULT_COMPILATION)
            return self._compile_analysis_result(
                request=request,
                creative_score=creative_score,
                reader_experience_score=reader_experience_score,
                structural_score=structural_score,
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
                session=session,
            )

        except Exception as e:
            session.fail_analysis(f"品質分析エラー: {e!s}")
            msg = f"品質分析に失敗しました: {e!s}"
            raise RuntimeError(msg) from e

    def _evaluate_creative_quality(
        self, manuscript_content: str, request: ClaudeQualityCheckRequest, session: ClaudeQualityCheckSession
    ) -> int:
        """創作的品質評価（40点満点）

        冒頭効果、キャラクター個性、感情表現、内面描写深度を評価
        """
        # 冒頭効果評価（10点）
        opening_score = self._evaluate_opening_effectiveness(manuscript_content, request)
        session.add_execution_metadata("opening_score", str(opening_score))

        # キャラクター個性評価（10点）
        character_score = self._evaluate_character_voice(manuscript_content, request)
        session.add_execution_metadata("character_score", str(character_score))

        # 感情表現評価（10点）
        emotion_score = self._evaluate_emotional_embodiment(manuscript_content, request)
        session.add_execution_metadata("emotion_score", str(emotion_score))

        # 内面描写深度評価（10点）
        depth_score = self._evaluate_depth_description(manuscript_content, request)
        session.add_execution_metadata("depth_score", str(depth_score))

        total_creative_score = opening_score + character_score + emotion_score + depth_score
        return min(total_creative_score, 40)  # 上限40点

    def _evaluate_reader_experience(
        self, manuscript_content: str, request: ClaudeQualityCheckRequest, session: ClaudeQualityCheckSession
    ) -> int:
        """読者体験評価（35点満点）

        継続性、没入感、スマホ読みやすさを評価
        """
        # 継続意欲評価（15点）
        engagement_score = self._evaluate_engagement_sustainability(manuscript_content, request)
        session.add_execution_metadata("engagement_score", str(engagement_score))

        # 没入感評価（10点）
        immersion_score = self._evaluate_immersion_quality(manuscript_content, request)
        session.add_execution_metadata("immersion_score", str(immersion_score))

        # スマホ読みやすさ評価（10点）
        readability_score = self._evaluate_smartphone_readability(manuscript_content, request)
        session.add_execution_metadata("readability_score", str(readability_score))

        total_experience_score = engagement_score + immersion_score + readability_score
        return min(total_experience_score, 35)  # 上限35点

    def _evaluate_structural_coherence(
        self, manuscript_content: str, request: ClaudeQualityCheckRequest, session: ClaudeQualityCheckSession
    ) -> int:
        """構成妥当性評価（25点満点）

        シーン目的、物語流れ、ペース配分を評価
        """
        # シーン目的明確性評価（10点）
        scene_purpose_score = self._evaluate_scene_purpose(manuscript_content, request)
        session.add_execution_metadata("scene_purpose_score", str(scene_purpose_score))

        # 物語流れ評価（10点）
        narrative_flow_score = self._evaluate_narrative_flow(manuscript_content, request)
        session.add_execution_metadata("narrative_flow_score", str(narrative_flow_score))

        # ペース配分評価（5点）
        pacing_score = self._evaluate_pacing_balance(manuscript_content, request)
        session.add_execution_metadata("pacing_score", str(pacing_score))

        total_structural_score = scene_purpose_score + narrative_flow_score + pacing_score
        return min(total_structural_score, 25)  # 上限25点

    def _evaluate_opening_effectiveness(self, manuscript_content: str, request: ClaudeQualityCheckRequest) -> int:
        """冒頭効果評価（10点満点）"""
        # 実装時はClaude APIを呼び出し
        # 現在はモック実装
        lines = manuscript_content.split("\n")[:5]  # 冒頭5行を確認

        # 簡単な評価ロジック（実際の実装では詳細な分析）
        opening_text = "\n".join(lines)
        score = 7  # デフォルトスコア

        # フック要素の存在チェック
        hook_indicators = ["？", "！", "「", "』", "――", "……", "突然", "瞬間", "しかし"]
        hook_count = sum(1 for indicator in hook_indicators if indicator in opening_text)
        score += min(hook_count, 3)

        return min(score, 10)

    def _evaluate_character_voice(self, manuscript_content: str, request: ClaudeQualityCheckRequest) -> int:
        """キャラクター個性評価（10点満点）"""
        # 会話文の多様性をチェック
        dialogue_lines = [line for line in manuscript_content.split("\n") if "「" in line or "『" in line]

        if not dialogue_lines:
            return 3  # 会話がない場合の低スコア

        # 語尾パターンの多様性チェック
        endings = []
        for line in dialogue_lines[:10]:  # 最初の10個の会話文をチェック
            if "」" in line:
                ending = line.split("」")[0][-3:]  # 語尾3文字
                endings.append(ending)

        unique_endings = len(set(endings))
        return min(unique_endings * 2, 10)

    def _evaluate_emotional_embodiment(self, manuscript_content: str, request: ClaudeQualityCheckRequest) -> int:
        """感情表現評価（10点満点）"""
        # 身体感覚表現の検索
        physical_expressions = [
            "心臓",
            "胸",
            "背筋",
            "喉",
            "手",
            "震え",
            "冷たい",
            "熱い",
            "痛み",
            "重い",
            "軽い",
            "跳ね",
            "凍り",
            "波打",
        ]

        expression_count = 0
        for expression in physical_expressions:
            expression_count += manuscript_content.count(expression)

        # 1000字あたりの身体感覚表現数でスコア計算
        density = (expression_count / max(len(manuscript_content), 1000)) * 1000
        score = min(int(density * 2), 10)

        return max(score, 3)  # 最低3点保証

    def _evaluate_depth_description(self, manuscript_content: str, request: ClaudeQualityCheckRequest) -> int:
        """内面描写深度評価（10点満点）"""
        # 5層深度の簡易チェック
        depth_indicators = {
            "sensory": ["見る", "聞く", "触れ", "匂い", "味"],
            "emotional": ["感じ", "思い", "気持ち", "心"],
            "cognitive": ["考え", "思考", "理解", "判断"],
            "memory": ["思い出", "記憶", "昔", "以前"],
            "symbolic": ["まるで", "ような", "みたい", "比べ"],
        }

        layer_scores = []
        for indicators in depth_indicators.values():
            count = sum(manuscript_content.count(indicator) for indicator in indicators)
            layer_score = min(count, 2)  # 各層最大2点
            layer_scores.append(layer_score)

        return sum(layer_scores)

    def _evaluate_engagement_sustainability(self, manuscript_content: str, request: ClaudeQualityCheckRequest) -> int:
        """継続意欲評価（15点満点）"""
        # シーンの変化点をカウント
        scene_markers = ["。", "――", "「", "』", "\n\n"]
        variety_score = min(sum(manuscript_content.count(marker) for marker in scene_markers) // 10, 10)

        # 文末の多様性
        sentences = [s.strip() for s in manuscript_content.split("。") if s.strip()]
        endings = [s[-3:] if len(s) >= 3 else s for s in sentences[-10:]]  # 最後の10文
        ending_variety = len(set(endings))
        variety_score += min(ending_variety, 5)

        return variety_score

    def _evaluate_immersion_quality(self, manuscript_content: str, request: ClaudeQualityCheckRequest) -> int:
        """没入感評価（10点満点）"""
        # メタ発言・作者コメントの検出
        meta_indicators = ["読者", "作者", "物語", "小説", "章", "話", "この後", "展開"]
        meta_count = sum(manuscript_content.count(indicator) for indicator in meta_indicators)

        # メタ発言が少ないほど高スコア
        return max(10 - meta_count, 0)

    def _evaluate_smartphone_readability(self, manuscript_content: str, request: ClaudeQualityCheckRequest) -> int:
        """スマホ読みやすさ評価（10点満点）"""
        paragraphs = [p.strip() for p in manuscript_content.split("\n\n") if p.strip()]

        # 段落長の評価
        appropriate_length_count = 0
        for paragraph in paragraphs:
            lines = paragraph.split("\n")
            if 1 <= len(lines) <= 4:  # 1-4行が適切:
                appropriate_length_count += 1

        return int(appropriate_length_count / len(paragraphs) * 10) if paragraphs else 5


    def _evaluate_scene_purpose(self, manuscript_content: str, request: ClaudeQualityCheckRequest) -> int:
        """シーン目的評価（10点満点）"""
        # 動作動詞の存在をチェック（シーンの能動性）
        action_verbs = ["する", "いく", "くる", "言う", "見る", "聞く", "感じる", "考える"]
        action_count = sum(manuscript_content.count(verb) for verb in action_verbs)

        # 1000字あたりの動作密度
        action_density = (action_count / max(len(manuscript_content), 1000)) * 1000
        score = min(int(action_density / 5), 10)

        return max(score, 3)

    def _evaluate_narrative_flow(self, manuscript_content: str, request: ClaudeQualityCheckRequest) -> int:
        """物語流れ評価（10点満点）"""
        # 接続詞・転換語の適切な使用
        connectors = ["そして", "しかし", "だが", "それから", "すると", "ところが", "やがて"]
        connector_count = sum(manuscript_content.count(conn) for conn in connectors)

        # 適度な接続詞使用でスコア計算
        flow_score = min(connector_count * 2, 10)
        return max(flow_score, 4)

    def _evaluate_pacing_balance(self, manuscript_content: str, request: ClaudeQualityCheckRequest) -> int:
        """ペース配分評価（5点満点）"""
        # 会話と地の文の比率チェック
        dialogue_chars = sum(len(line) for line in manuscript_content.split("\n") if "「" in line or "『" in line)
        total_chars = len(manuscript_content)

        if total_chars > 0:
            dialogue_ratio = dialogue_chars / total_chars
            # 30-70%が適切な範囲
            if 0.3 <= dialogue_ratio <= 0.7:
                return 5
            if 0.2 <= dialogue_ratio <= 0.8:
                return 3
            return 1

        return 2

    def _compile_analysis_result(
        self,
        request: ClaudeQualityCheckRequest,
        creative_score: int,
        reader_experience_score: int,
        structural_score: int,
        execution_time_ms: float,
        session: ClaudeQualityCheckSession,
    ) -> ClaudeQualityCheckResult:
        """分析結果編纂"""
        total_score = creative_score + reader_experience_score + structural_score

        # 改善提案生成
        improvement_suggestions = self._generate_improvement_suggestions(
            creative_score, reader_experience_score, structural_score, request
        )

        # 詳細フィードバック生成
        detailed_feedback = self._generate_detailed_feedback(
            creative_score, reader_experience_score, structural_score, request, session
        )

        return ClaudeQualityCheckResult(
            request=request,
            total_score=total_score,
            creative_quality_score=creative_score,
            reader_experience_score=reader_experience_score,
            structural_coherence_score=structural_score,
            detailed_feedback=detailed_feedback,
            improvement_suggestions=improvement_suggestions,
            execution_time_ms=execution_time_ms,
            is_success=True,
        )

    def _generate_improvement_suggestions(
        self,
        creative_score: int,
        reader_experience_score: int,
        structural_score: int,
        request: ClaudeQualityCheckRequest,
    ) -> list[str]:
        """改善提案生成"""
        suggestions = []

        if creative_score < 32:  # 80%以下:
            suggestions.append("感情表現を身体感覚で具体化してください（例：「悲しい」→「胸が締め付けられる」）")
            suggestions.append("キャラクターごとの口調や話し方をより差別化してください")

        if reader_experience_score < 28:  # 80%以下:
            suggestions.append("1段落を3-4行以内に収めてスマホ読みやすさを向上させてください")
            suggestions.append("メタ発言や作者コメントを除去して没入感を高めてください")

        if structural_score < 20:  # 80%以下:
            suggestions.append("各シーンの存在意義を明確にし、無駄な部分を削除してください")
            suggestions.append("章末に適切な引き（クリフハンガー）を設置してください")

        return suggestions[:5]  # 最大5つの提案

    def _generate_detailed_feedback(
        self,
        creative_score: int,
        reader_experience_score: int,
        structural_score: int,
        request: ClaudeQualityCheckRequest,
        session: ClaudeQualityCheckSession,
    ) -> str:
        """詳細フィードバック生成"""
        total_score = creative_score + reader_experience_score + structural_score

        feedback_parts = [
            "=== Claude Code品質評価結果 ===",
            f"エピソード: {request.get_context_summary()}",
            f"総合評価: {total_score}/100点",
            "",
            "【詳細スコア】",
            f"創作的品質: {creative_score}/40点",
            f"読者体験: {reader_experience_score}/35点",
            f"構成妥当性: {structural_score}/25点",
            "",
            "【分析メタデータ】",
        ]

        # セッションメタデータを追加
        for key, value in session.execution_metadata.items():
            feedback_parts.append(f"{key}: {value}")

        return "\n".join(feedback_parts)
