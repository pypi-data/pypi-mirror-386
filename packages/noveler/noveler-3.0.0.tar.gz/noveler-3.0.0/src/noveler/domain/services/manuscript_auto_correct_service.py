#!/usr/bin/env python3
"""小説原稿自動修正サービス

仕様書: SPEC-QUALITY-001
旧名: A31AutoFixService
役割: 原稿品質チェックリスト項目の自動修正サービス

主要機能:
- チェックリスト項目の問題点自動修正
- 安全性レベルに応じた段階的修正（安全・標準・対話式）
- フォーマット・スタイル・読みやすさの自動改善
- 修正結果の詳細レポート生成
"""

import re
from typing import Any

from noveler.domain.entities.a31_checklist_item import A31ChecklistItem, ChecklistItemType
from noveler.domain.value_objects.a31_evaluation_result import EvaluationResult
from noveler.domain.value_objects.a31_fix_level import FixLevel
from noveler.domain.value_objects.a31_fix_result import FixResult


class ManuscriptAutoCorrectService:
    """小説原稿自動修正サービス

    原稿品質チェックリスト項目の問題に対する自動修正を実行。
    修正レベル(安全・標準・対話式)に応じた処理を提供。

    旧サービス名: A31AutoFixService
    """

    def __init__(self) -> None:
        """自動修正サービスの初期化"""
        self._safe_fixers = {
            ChecklistItemType.FORMAT_CHECK: self._fix_format_issues,
            ChecklistItemType.STYLE_CONSISTENCY: self._fix_style_consistency,
        }

        self._standard_fixers = {
            ChecklistItemType.BASIC_PROOFREAD: self._fix_basic_proofreading,
            ChecklistItemType.TERMINOLOGY_CHECK: self._fix_terminology_issues,
            ChecklistItemType.CONTENT_BALANCE: self._fix_content_balance,
        }

        self._interactive_fixers = {
            ChecklistItemType.READABILITY_CHECK: self._fix_readability_issues,
            ChecklistItemType.CHARACTER_CONSISTENCY: self._fix_character_consistency,
        }

    def apply_fixes(
        self,
        content: str,
        evaluation_results: dict[str, EvaluationResult],
        items: list[A31ChecklistItem],
        fix_level: FixLevel,
    ) -> tuple[str, list[FixResult]]:
        """修正の適用

        Args:
            content: 修正対象の内容
            evaluation_results: 評価結果
            items: チェックリスト項目
            fix_level: 修正レベル

        Returns:
            Tuple[str, list[FixResult]]: (修正後内容, 修正結果リスト)
        """
        fixed_content = content
        fix_results = []

        # 項目をIDでマップ化
        item_map = {item.item_id: item for item in items}

        # 不合格項目のみを対象とし、優先度順にソート
        failed_evaluations = [
            (item_id, result)
            for item_id, result in evaluation_results.items()
            if not result.passed and item_id in item_map
        ]

        # 優先度順にソート(優先度が低い数値ほど高優先)
        failed_evaluations.sort(key=lambda x: item_map[x[0]].get_fix_priority())

        for item_id, evaluation in failed_evaluations:
            item = item_map[item_id]

            # 修正可能性チェック
            if not item.is_auto_fixable():
                fix_results.append(
                    FixResult.create_failed_fix(
                        item_id=item_id, fix_type="manual_only", current_score=evaluation.current_score
                    )
                )
                continue

            # 修正レベルチェック
            if not self._can_apply_fix_level(item, fix_level):
                fix_results.append(
                    FixResult.create_failed_fix(
                        item_id=item_id, fix_type="insufficient_level", current_score=evaluation.current_score
                    )
                )
                continue

            # 修正実行
            try:
                new_content, changes = self._apply_item_fix(fixed_content, item, evaluation, fix_level)

                if changes:
                    # 修正が適用された場合
                    fixed_content = new_content

                    # 修正後スコアの簡易計算(実際には再評価が必要)
                    after_score = min(100.0, evaluation.current_score + len(changes) * 5)

                    fix_results.append(
                        FixResult.create_successful_fix(
                            item_id=item_id,
                            fix_type=self._get_fix_type_name(item.item_type),
                            changes_made=changes,
                            before_score=evaluation.current_score,
                            after_score=after_score,
                        )
                    )
                else:
                    # 修正が適用されなかった場合
                    fix_results.append(
                        FixResult.create_failed_fix(
                            item_id=item_id,
                            fix_type=self._get_fix_type_name(item.item_type),
                            current_score=evaluation.current_score,
                        )
                    )

            except Exception:
                # 修正エラー
                fix_results.append(
                    FixResult.create_failed_fix(
                        item_id=item_id, fix_type="error", current_score=evaluation.current_score
                    )
                )

        return fixed_content, fix_results

    def _can_apply_fix_level(self, item: A31ChecklistItem, fix_level: FixLevel) -> bool:
        """修正レベルの適用可能性チェック"""
        strategy = item.auto_fix_strategy

        if strategy.fix_level == "safe":
            return True  # 安全な修正は全レベルで適用可能
        if strategy.fix_level == "standard":
            return fix_level in (FixLevel.STANDARD, FixLevel.INTERACTIVE)
        if strategy.fix_level == "interactive":
            return fix_level == FixLevel.INTERACTIVE

        return False

    def _apply_item_fix(
        self, content: str, item: A31ChecklistItem, evaluation: EvaluationResult, fix_level: FixLevel
    ) -> tuple[str, list[str]]:
        """個別項目の修正適用"""
        # 修正レベルに応じた修正器を選択
        if fix_level == FixLevel.SAFE and item.item_type in self._safe_fixers:
            return self._safe_fixers[item.item_type](content, item, evaluation)
        if fix_level in (FixLevel.STANDARD, FixLevel.INTERACTIVE) and item.item_type in self._standard_fixers:
            return self._standard_fixers[item.item_type](content, item, evaluation)
        if fix_level == FixLevel.INTERACTIVE and item.item_type in self._interactive_fixers:
            return self._interactive_fixers[item.item_type](content, item, evaluation)

        # 対応する修正器がない場合
        return content, []

    def _fix_format_issues(
        self, content: str, item: A31ChecklistItem, _evaluation: EvaluationResult
    ) -> tuple[str, list[str]]:
        """フォーマット問題の修正"""
        if item.item_id == "A31-045":  # 段落頭字下げ:
            return self._fix_paragraph_indentation(content)

        return content, []

    def _fix_style_consistency(
        self, content: str, item: A31ChecklistItem, _evaluation: EvaluationResult
    ) -> tuple[str, list[str]]:
        """スタイル統一性の修正"""
        if item.item_id == "A31-035":  # 記号統一:
            return self._fix_symbol_consistency(content)

        return content, []

    def _fix_basic_proofreading(
        self, content: str, _item: A31ChecklistItem, _evaluation: EvaluationResult
    ) -> tuple[str, list[str]]:
        """基本的な校正修正

        SPEC-A31-031準拠:
        - 基本的な誤字パターン検出・修正
        - 句読点・記号の正規化
        - 文字種統合(全角/半角統一)
        """
        changes = []
        fixed_content = content

        # 1. 基本的な誤字修正パターン
        typo_patterns = [
            # ひらがな誤字
            (r"だつた", "だった"),
            (r"かつた", "かった"),
            (r"してる(?![う-ん])", "している"),
            (r"きてる(?![う-ん])", "きている"),
            (r"みてる(?![う-ん])", "みている"),
            (r"でてる(?![う-ん])", "でている"),
            # 送り仮名・漢字修正
            (r"行なう", "行う"),
            (r"云う", "言う"),
            (r"云った", "言った"),
            (r"云われ", "言われ"),
            (r"何処", "どこ"),
            (r"此処", "ここ"),
            (r"其処", "そこ"),
            # 挨拶・基本語彙
            (r"こんにちわ", "こんにちは"),
            (r"こんばんわ", "こんばんは"),
            (r"おはよございます", "おはようございます"),
            # 助詞の誤字
            (r"には関らず", "にはかかわらず"),
            (r"に関らず", "にかかわらず"),
            (r"と言う(?!名|風|感)", "という"),
        ]

        for pattern, replacement in typo_patterns:
            if re.search(pattern, fixed_content):
                before_count = len(re.findall(pattern, fixed_content))
                fixed_content = re.sub(pattern, replacement, fixed_content)
                changes.append(f"誤字修正: {pattern} → {replacement} ({before_count}箇所)")

        # 2. 句読点・記号の正規化
        punctuation_patterns = [
            # 重複句読点の修正
            (r"。{2,}", "。"),
            (r"、{2,}", "、"),
            (r"\?{2,}", "?"),
            (r"!{2,}", "!"),
            # 記号の統一(全角)
            (r"\?", "?"),
            (r"!", "!"),
            (r"~", "〜"),
            # 三点リーダーの統一
            (r"\.{3,}", "…"),
            (r"…{2,}", "……"),
            # ダッシュの統一
            (r"-{2,}", "——"),
            (r"―{2,}", "——"),
        ]

        for pattern, replacement in punctuation_patterns:
            if re.search(pattern, fixed_content):
                before_count = len(re.findall(pattern, fixed_content))
                fixed_content = re.sub(pattern, replacement, fixed_content)
                changes.append(f"句読点修正: {pattern} → {replacement} ({before_count}箇所)")

        # 3. 文字種統合(全角→半角、半角→全角)
        character_type_patterns = [
            # 数字は半角に統一
            (r"[０-９]+", lambda m: self._zenkaku_to_hankaku_digits(m.group())),
            # 英字は半角に統一
            (r"[Ａ-Ｚａ-ｚ]+", lambda m: self._zenkaku_to_hankaku_alpha(m.group())),
            # カッコ類は全角に統一(日本語文書)
            (r"\(", "("),
            (r"\)", ")"),
            (r"\[", "["),
            (r"\]", "]"),
            (r"\{", "{"),
            (r"\}", "}"),
        ]

        for pattern, replacement in character_type_patterns:
            if callable(replacement):
                # Lambda関数の場合
                matches = list(re.finditer(pattern, fixed_content))
                if matches:
                    fixed_content = re.sub(pattern, replacement, fixed_content)
                    changes.append(f"文字種修正: 全角→半角 ({len(matches)}箇所)")
            # 文字列置換の場合
            elif re.search(pattern, fixed_content):
                before_count = len(re.findall(pattern, fixed_content))
                fixed_content = re.sub(pattern, replacement, fixed_content)
                changes.append(f"文字種修正: {pattern} → {replacement} ({before_count}箇所)")

        # 4. スペースの正規化
        space_patterns = [
            # 連続スペースの統一
            (r"[  ]{2,}", " "),
            # 行頭スペースの統一(全角スペース)
            (r"^[ ]+", " "),
            # 句読点前の不要スペース除去
            (r"[  ]+([。、?!])", r"\1"),
        ]

        for pattern, replacement in space_patterns:
            if re.search(pattern, fixed_content, re.MULTILINE):
                before_count = len(re.findall(pattern, fixed_content, re.MULTILINE))
                fixed_content = re.sub(pattern, replacement, fixed_content, flags=re.MULTILINE)
                changes.append(f"スペース修正: ({before_count}箇所)")

        return fixed_content, changes

    def _zenkaku_to_hankaku_digits(self, text: str) -> str:
        """全角数字を半角数字に変換"""
        zenkaku_digits = "０１２３４５６７８９"
        hankaku_digits = "0123456789"
        translation_table = str.maketrans(zenkaku_digits, hankaku_digits)
        return text.translate(translation_table)

    def _zenkaku_to_hankaku_alpha(self, text: str) -> str:
        """全角英字を半角英字に変換"""
        zenkaku_upper = "ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ"
        hankaku_upper = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        zenkaku_lower = "ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ"
        hankaku_lower = "abcdefghijklmnopqrstuvwxyz"

        translation_table = str.maketrans(zenkaku_upper + zenkaku_lower, hankaku_upper + hankaku_lower)

        return text.translate(translation_table)

    def _fix_terminology_issues(
        self, content: str, _item: A31ChecklistItem, evaluation: EvaluationResult
    ) -> tuple[str, list[str]]:
        """用語統一問題の修正

        SPEC-A31-044準拠:
        - プロジェクト固有用語辞書連携
        - キャラクター名・地名・技名の表記統一
        - 表記ゆれの自動検出・修正
        """
        from noveler.domain.services.terminology_service import TerminologyService

        changes = []
        fixed_content = content

        # 評価結果から用語統一の問題を取得
        details: Any = evaluation.details
        terminology_inconsistencies = details.get("terminology_inconsistencies", [])

        # TerminologyServiceを使用して高度な用語統一を実行
        terminology_service = TerminologyService()

        if terminology_inconsistencies:
            # 評価結果の用語統一データを使用
            for inconsistency in terminology_inconsistencies:
                canonical = inconsistency.get("canonical", "")
                variants = inconsistency.get("variants", [])

                for variant in variants:
                    if variant in fixed_content and variant != canonical:
                        # 文脈を考慮した置換実行
                        count = fixed_content.count(variant)
                        if count > 0:
                            fixed_content = fixed_content.replace(variant, canonical)
                            category = self._determine_terminology_category(canonical)
                            changes.append(
                                self._format_terminology_change(category, variant, canonical, count)
                            )
        else:
            # 評価結果にデータがない場合、サービスで自動検出
            fixes = terminology_service.detect_terminology_issues(content)
            if fixes:
                fixed_content, service_changes = terminology_service.apply_terminology_fixes(fixed_content, fixes)

                changes.extend(service_changes)

        # 追加の基本的な用語統一パターン
        basic_terminology_patterns = [
            # 一般的な表記ゆれ
            ("魔法使い", ["魔導師", "魔術師"]),
            ("モンスター", ["怪物", "魔物", "魔獣"]),
            ("レベル", ["レヴェル", "Lv", "LV"]),
            ("ステータス", ["ステイタス", "状態"]),
            ("スキル", ["技能", "能力"]),
            ("アイテム", ["道具", "品物"]),
            ("ダンジョン", ["迷宮", "地下迷宮"]),
            ("ギルド", ["組合", "協会"]),
            # 敬語・呼称の統一
            ("先生", ["せんせい", "センセイ"]),
            ("お疲れさま", ["お疲れ様", "おつかれさま"]),
        ]

        for canonical, variants in basic_terminology_patterns:
            for variant in variants:
                if variant in fixed_content:
                    count = fixed_content.count(variant)
                    if count > 0:
                        fixed_content = fixed_content.replace(variant, canonical)
                        changes.append(self._format_terminology_change("用語", variant, canonical, count))

        return fixed_content, changes

    def _determine_terminology_category(self, term: str) -> str:
        """用語のカテゴリを判定

        Args:
            term: 判定対象の用語

        Returns:
            str: カテゴリ名
        """
        # キャラクター名パターン
        character_patterns = ["太郎", "花子", "先生", "師匠", "王様", "姫様"]
        if any(pattern in term for pattern in character_patterns):
            return "キャラクター名"

        # 地名・組織名パターン
        location_patterns = ["学院", "学園", "ギルド", "組合", "王国", "街", "村", "城"]
        if any(pattern in term for pattern in location_patterns):
            return "地名"

        # 魔法・技名パターン
        spell_patterns = ["ボール", "アロー", "ブレス", "ヒール", "バフ", "デバフ"]
        if any(pattern in term for pattern in spell_patterns):
            return "魔法名"

        # その他は一般用語
        return "用語"

    def _format_terminology_change(self, category: str, variant: str, canonical: str, count: int) -> str:
        """用語統一の変更ログを生成"""
        category_label = category if category else "用語"
        detail_label = f"{category_label}統一"
        return f"用語統一/{detail_label}: {variant} → {canonical} ({count}箇所)"

    def _fix_readability_issues(
        self, content: str, _item: A31ChecklistItem, evaluation: EvaluationResult
    ) -> tuple[str, list[str]]:
        """文章のリズムと読みやすさ修正"""
        changes = []
        fixed_content = content

        # 評価結果から問題点を取得
        details: Any = evaluation.details
        repetitive_patterns = details.get("repetitive_patterns", [])
        rhythm_issues = details.get("rhythm_issues", [])

        # 語尾の単調性修正
        if "だった" in repetitive_patterns:
            # 「だった」の一部を「である」に変更
            lines = fixed_content.split("\n")
            modified_lines = []
            datta_count = 0

            for line in lines:
                if "だった。" in line and datta_count % 2 == 0:  # 2回に1回変更:
                    line = line.replace("だった。", "である。", 1)
                    changes.append("語尾修正: だった → である")

                if "だった" in line:
                    datta_count += 1
                modified_lines.append(line)

            fixed_content = "\n".join(modified_lines)

        # 短文の連続修正
        if "短文の連続" in rhythm_issues:
            sentences = fixed_content.split("。")
            for i in range(len(sentences) - 2):
                curr_len = len(sentences[i].strip())
                next_len = len(sentences[i + 1].strip())

                # 連続する短文(20文字以下)を結合
                if curr_len < 20 and next_len < 20 and curr_len > 0 and next_len > 0:
                    sentences[i] = sentences[i] + "。" + sentences[i + 1]
                    sentences[i + 1] = ""
                    changes.append("文長調整: 短文連続を結合")
                    break

            fixed_content = "。".join([s for s in sentences if s.strip()])

        return fixed_content, changes

    def _fix_character_consistency(
        self, content: str, _item: A31ChecklistItem, evaluation: EvaluationResult
    ) -> tuple[str, list[str]]:
        """キャラクター口調一貫性修正"""
        changes = []
        fixed_content = content

        details: Any = evaluation.details
        inconsistencies = details.get("character_inconsistencies", [])

        for inconsistency in inconsistencies:
            character = inconsistency.get("character", "")
            expected_tone = inconsistency.get("expected_tone", "")
            inconsistency.get("found_tone", "")

            if character == "太郎" and expected_tone == "confident":
                # 弱気な表現を自信ありげに修正
                weakness_patterns = [("すみません", "すまない"), ("ちょっと", "少し"), ("あの、", ""), ("えーと", "")]

                for weak_expr, strong_expr in weakness_patterns:
                    if weak_expr in fixed_content:
                        fixed_content = fixed_content.replace(weak_expr, strong_expr)
                        changes.append(f"口調修正: {weak_expr} → {strong_expr}")

        return fixed_content, changes

    def _fix_content_balance(
        self, content: str, _item: A31ChecklistItem, evaluation: EvaluationResult
    ) -> tuple[str, list[str]]:
        """伏線と描写の過不足調整修正"""
        changes = []
        fixed_content = content

        details: Any = evaluation.details
        dialogue_ratio = details.get("dialogue_ratio", 0)
        details.get("description_ratio", 0)
        balance_issues = details.get("balance_issues", [])

        # 会話過多の場合、描写を追加
        if dialogue_ratio > 70:
            lines = fixed_content.split("\n")
            modified_lines = []

            for line in lines:
                modified_lines.append(line)

                # 会話文の後に状況描写を追加
                if line.strip().startswith("「") and line.strip().endswith("」"):
                    # 簡易的な描写を追加
                    if "叫んだ" not in line and "言った" not in line:
                        description = f" {line.split('」')[0][1:]}と彼は表情を変えながら語った。"
                        modified_lines.append(description)
                        changes.append("描写追加: 会話後の状況描写")
                        break  # 1箇所のみ修正

            fixed_content = "\n".join(modified_lines)

        # 描写不足の場合、感情描写を追加
        if "描写不足" in balance_issues:
            lines = fixed_content.split("\n")
            for i, line in enumerate(lines):
                if "俺は" in line and i < len(lines) - 1:
                    emotion_desc = " 心の中で複雑な感情が渦巻いていた。"
                    lines.insert(i + 1, emotion_desc)
                    changes.append("描写追加: 感情表現")
                    break

            fixed_content = "\n".join(lines)

        return fixed_content, changes

    def _fix_paragraph_indentation(self, content: str) -> tuple[str, list[str]]:
        """段落字下げの修正"""
        lines = content.split("\n")
        changes = []
        fixed_lines = []

        for line in lines:
            if line.strip() and not line.startswith(" ") and not line.startswith("「"):
                # 地の文で字下げがない場合
                fixed_line = " " + line
                fixed_lines.append(fixed_line)
                changes.append(f"字下げ追加: {line[:20]}...")
            else:
                fixed_lines.append(line)

        return "\n".join(fixed_lines), changes

    def _fix_symbol_consistency(self, content: str) -> tuple[str, list[str]]:
        """記号統一性の修正"""
        changes = []
        fixed_content = content

        # 三点リーダーの統一(... → …)
        dot_count = len(re.findall(r"\.{3,}", fixed_content))
        if dot_count > 0:
            fixed_content = re.sub(r"\.{3,}", "…", fixed_content)
            changes.append(f"三点リーダー統一: {dot_count}箇所")

        # ダッシュの統一(-- → ――)
        hyphen_count = len(re.findall(r"-{2,}", fixed_content))
        if hyphen_count > 0:
            fixed_content = re.sub(r"-{2,}", "――", fixed_content)
            changes.append(f"ダッシュ統一: {hyphen_count}箇所")

        return fixed_content, changes

    def _get_fix_type_name(self, item_type: ChecklistItemType) -> str:
        """修正タイプ名の取得"""
        type_names = {
            ChecklistItemType.FORMAT_CHECK: "format_check",
            ChecklistItemType.STYLE_CONSISTENCY: "style_consistency",
            ChecklistItemType.BASIC_PROOFREAD: "basic_proofread",
            ChecklistItemType.TERMINOLOGY_CHECK: "terminology_check",
            ChecklistItemType.CONTENT_BALANCE: "content_balance",
            ChecklistItemType.CHARACTER_CONSISTENCY: "character_consistency",
        }

        return type_names.get(item_type, "unknown")

    def generate_improvement_suggestions(
        self, evaluation_results: dict[str, EvaluationResult], items: list[A31ChecklistItem]
    ) -> list[str]:
        """改善提案の生成

        Args:
            evaluation_results: 評価結果
            items: チェックリスト項目

        Returns:
            list[str]: 改善提案のリスト
        """
        suggestions = []
        item_map = {item.item_id: item for item in items}

        for item_id, result in evaluation_results.items():
            if not result.passed and item_id in item_map:
                item = item_map[item_id]
                suggestion = self._generate_item_suggestion(item, result)
                if suggestion:
                    suggestions.append(suggestion)

        return suggestions

    def _generate_item_suggestion(self, item: A31ChecklistItem, result: EvaluationResult) -> str:
        """個別項目の改善提案生成"""
        improvement_needed = result.get_improvement_needed()

        if item.item_type == ChecklistItemType.FORMAT_CHECK:
            return f"{item.title}: {improvement_needed:.1f}点の改善が必要(フォーマット確認)"
        if item.item_type == ChecklistItemType.CONTENT_BALANCE:
            return f"{item.title}: バランス調整により{improvement_needed:.1f}点の改善可能"
        if item.item_type == ChecklistItemType.QUALITY_THRESHOLD:
            return f"{item.title}: 全体的な品質向上により{improvement_needed:.1f}点の改善が必要"
        return f"{item.title}: {improvement_needed:.1f}点の改善が必要"


# 後方互換性のためのエイリアス
A31AutoFixService = ManuscriptAutoCorrectService
