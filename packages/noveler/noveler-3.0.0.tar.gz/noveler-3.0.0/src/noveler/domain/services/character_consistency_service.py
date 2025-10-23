"""キャラクター一貫性チェックドメインサービス

キャラクター描写の一貫性を分析するドメインサービス。
"""

import re
from typing import Any

from noveler.domain.entities.episode import Episode
from noveler.domain.value_objects.consistency_violation import ConsistencyViolation


class CharacterConsistencyService:
    """キャラクター一貫性チェックサービス

    エピソード内のキャラクター描写が設定と一致しているかを
    分析し、違反を検出する。
    """

    def __init__(self, character_repository: object) -> None:
        """サービスを初期化

        Args:
            character_repository: キャラクターリポジトリ
        """
        self._character_repository = character_repository
        self._pattern_cache: dict[str, dict] = {}

    def analyze_consistency(
        self,
        episode: Episode,
        characters: list[dict[str, Any]],
        custom_rules: dict[str, Any] | None = None,
        consider_timeline: bool = True,
    ) -> list[ConsistencyViolation]:
        """エピソードの一貫性を分析

        Args:
            episode: 分析対象エピソード
            characters: キャラクタープロファイルリスト
            custom_rules: カスタムルール
            consider_timeline: 時系列を考慮するか

        Returns:
            検出された違反のリスト
        """
        violations: list[ConsistencyViolation] = []
        lines = episode.content.split("\n")

        # 文脈情報を構築
        context = self._build_context(episode, consider_timeline)

        for line_num, line in enumerate(lines, 1):
            # 各キャラクターについてチェック
            for character in characters:
                if not self._is_character_mentioned(line, character, context):
                    continue

                # 外見チェック
                violations.extend(self._check_appearance(line, line_num, character, context))

                # 性格チェック
                violations.extend(self._check_personality(line, line_num, character, context))

                # 話し方チェック
                violations.extend(self._check_speech_style(line, line_num, character, context))

                # カスタムルールチェック
                if custom_rules:
                    violations.extend(self._check_custom_rules(line, line_num, character, custom_rules, context))

        # 代名詞解決後の再チェック
        violations.extend(self._check_with_pronoun_resolution(episode, characters, context))

        unique: dict[tuple[str, str, int, str | None], ConsistencyViolation] = {}
        for violation in violations:
            key = (violation.character_name, violation.attribute, violation.line_number, violation.context)
            if key not in unique:
                unique[key] = violation

        return list(unique.values())

    def _build_context(self, episode: Episode, consider_timeline: bool) -> dict:
        """エピソードの文脈情報を構築"""
        context = {
            "episode_number": episode.number,
            "consider_timeline": consider_timeline,
            "changes": [],  # キャラクターの変化情報
            "active_magic": {},
        }

        # 髪を染める等の変化を検出
        if "染め" in episode.content or "変装" in episode.content:
            context["has_appearance_change"] = True
            # 変化の詳細を抽出(簡易版)
            context["changes"] = self._extract_changes(episode.content)

        return context

    def _extract_changes(self, content: str) -> list[dict]:
        """キャラクターの変化を抽出"""
        changes = []
        lines = content.split("\n")

        for index, line in enumerate(lines, 1):
            if "染め" in line or "変装" in line:
                changes.append({"line": index, "type": "appearance_change"})

        return changes

    def _is_character_mentioned(self, line: str, character: Any, context: dict) -> bool:
        """行内にキャラクターが言及されているか判定"""
        # キャラクター名の直接的な言及
        if character.name in line:
            context["last_character"] = character
            return True

        # 代名詞による言及(性別が分かる場合)
        gender = character.get_attribute("gender") if hasattr(character, "get_attribute") else None
        pronoun_match = (
            gender == "男性" and ("彼" in line or "彼の" in line)
        ) or (
            gender == "女性" and ("彼女" in line or "彼女の" in line)
        )

        if pronoun_match:
            return True

        last_character = context.get("last_character")
        if last_character and last_character.name == character.name and ("彼" in line or "彼女" in line):
            return True

        return False

    def _check_appearance(
        self, line: str, line_number: int, character: Any, context: dict
    ) -> list[ConsistencyViolation]:
        """外見の一貫性をチェック"""
        violations: list[ConsistencyViolation] = []

        # 髪色チェック
        if any(keyword in line for keyword in ["髪", "ヘア"]):
            hair_color = character.get_attribute("hair_color")
            if hair_color:
                # 変化が記録されている場合は考慮
                if context.get("has_appearance_change") and self._is_after_change(line_number, context):
                    return violations

                violation = self._check_hair_color(line, line_number, character, hair_color)
                if violation:
                    violations.append(violation)

        # 瞳の色チェック
        if any(keyword in line for keyword in ["瞳", "目", "眼"]):
            eye_color = character.get_attribute("eye_color")
            if eye_color:
                violation = self._check_eye_color(line, line_number, character, eye_color)
                if violation:
                    violations.append(violation)

        return violations

    def _is_after_change(self, line_number: int, context: dict) -> bool:
        """変化の後の行かどうか判定"""
        return any(change["line"] < line_number for change in context.get("changes", []))

    def _check_hair_color(
        self, line: str, line_number: int, character: dict[str, Any], expected: str
    ) -> ConsistencyViolation | None:
        """髪色の一貫性をチェック"""
        color_map = {
            "黒髪": ["黒い髪", "黒髪", "漆黒の髪"],
            "金髪": ["金髪", "金色の髪", "ブロンド"],
            "茶髪": ["茶髪", "茶色い髪", "栗色の髪"],
            "赤髪": ["赤い髪", "赤髪", "赤毛"],
            "白髪": ["白い髪", "白髪", "銀髪"],
        }

        for color, patterns in color_map.items():
            if color != expected and any(p in line for p in patterns):
                return ConsistencyViolation(
                    character_name=character.name,
                    attribute="hair_color",
                    expected=expected,
                    actual=color,
                    line_number=line_number,
                    context=line.strip(),
                )

        return None

    def _check_eye_color(
        self, line: str, line_number: int, character: dict[str, Any], expected: str
    ) -> ConsistencyViolation | None:
        """瞳の色の一貫性をチェック"""
        # 色のパターンを抽出
        color_patterns = {
            "黒": ["黒い瞳", "黒い目", "漆黒の瞳"],
            "茶色": ["茶色い瞳", "茶色の目", "褐色の瞳"],
            "青": ["青い瞳", "青い目", "碧眼"],
            "緑": ["緑の瞳", "緑色の目", "翠眼"],
            "灰色": ["灰色の瞳", "グレーの目"],
        }

        for color, patterns in color_patterns.items():
            matched_pattern = next((p for p in patterns if p in line), None)
            if matched_pattern:
                if color != expected and expected not in color:
                    actual_color = matched_pattern
                    for suffix in ("の瞳", "瞳", "の目", "目"):
                        if actual_color.endswith(suffix):
                            actual_color = actual_color[: -len(suffix)]
                            break

                    return ConsistencyViolation(
                        character_name=character.name,
                        attribute="eye_color",
                        expected=expected,
                        actual=actual_color,
                        line_number=line_number,
                        context=line.strip(),
                    )

        return None

    def _check_personality(
        self, line: str, line_number: int, character: Any, _context: dict
    ) -> list[ConsistencyViolation]:
        """性格の一貫性をチェック"""
        violations: list[ConsistencyViolation] = []
        personality = character.get_attribute("personality")

        if not personality:
            return violations

        # 性格と矛盾する行動パターン
        contradiction_patterns = {
            "内向的": ["元気に", "明るく", "活発に", "社交的"],
            "物静か": ["騒がしく", "うるさく", "大声で"],
            "真面目": ["ふざけて", "いい加減に", "適当に"],
            "臆病": ["勇敢に", "大胆に", "恐れず"],
        }

        if personality in contradiction_patterns:
            for pattern in contradiction_patterns[personality]:
                if pattern in line and character.name in line:
                    return [
                        ConsistencyViolation(
                            character_name=character.name,
                            attribute="personality",
                            expected=personality,
                            actual=pattern,
                            line_number=line_number,
                            context=line.strip(),
                        )
                    ]

        return violations

    def _check_speech_style(
        self, line: str, line_number: int, character: Any, _context: dict
    ) -> list[ConsistencyViolation]:
        """話し方の一貫性をチェック"""
        violations: list[ConsistencyViolation] = []
        speech_style = character.get_attribute("speech_style")

        if not speech_style:
            return violations

        if not self._is_character_speech(line, character):
            if speech_style == "丁寧語" and character.name in line and self._contains_casual_marker(line):
                snippet = self._extract_casual_snippet(line)
                violations.append(
                    ConsistencyViolation(
                        character_name=character.name,
                        attribute="speech_style",
                        expected=speech_style,
                        actual=f"{snippet}（例: 俺/負けねぇ）",
                        line_number=line_number,
                        context=line.strip(),
                    )
                )
            return violations

        # セリフ部分を抽出
        speech = self._extract_speech(line)
        if not speech:
            return violations

        # 話し方のパターンチェック
        if speech_style == "丁寧語":
            if not self._is_polite_speech(speech):
                violations.append(
                    ConsistencyViolation(
                        character_name=character.name,
                        attribute="speech_style",
                        expected=speech_style,
                        actual=speech,
                        line_number=line_number,
                        context=line.strip(),
                    )
                )

        return violations

    def _contains_casual_marker(self, text: str) -> bool:
        """カジュアルな口調を示すマーカーを検出"""
        markers = ["負けねぇ", "俺", "だが", "だぞ", "だぜ", "だよ", "だな", "だろ", "じゃん", "ねぇ"]
        return any(marker in text for marker in markers)

    def _extract_casual_snippet(self, text: str) -> str:
        """カジュアル表現のスニペットを抽出"""
        markers = ["負けねぇ", "俺", "だが", "だぞ", "だぜ", "だよ", "だな", "だろ", "じゃん", "ねぇ"]
        for marker in markers:
            if marker in text:
                return marker
        return text.strip()[:10]

    def _is_character_speech(self, line: str, character: dict[str, Any]) -> bool:
        """キャラクターのセリフかどうか判定"""
        # 「キャラクター名」が言った パターン
        if f"{character.name}が" in line and ("言った" in line or "答えた" in line):
            return True
        # 「セリフ」とキャラクター名 パターン
        return bool("「" in line and "」" in line and character.name in line)

    def _extract_speech(self, line: str) -> str | None:
        """セリフ部分を抽出"""
        match = re.search(r"「(.+?)」", line)
        if match:
            return match.group(1)
        return None

    def _is_polite_speech(self, speech: str) -> bool:
        """丁寧語かどうか判定"""
        polite_endings = ["です", "ます", "でしょう", "ません", "ございます"]
        casual_markers = ["だ", "よ", "ね", "さ", "ぜ", "ぞ"]

        # 文末が丁寧語で終わっている
        for ending in polite_endings:
            if speech.endswith(ending):
                return True

        # カジュアルマーカーがある場合は丁寧語ではない
        for marker in casual_markers:
            if speech.endswith(marker):
                return False

        # 敬語表現
        return bool(any(honorific in speech for honorific in ["おります", "いたします", "申し上げ"]))

    def _check_custom_rules(
        self, line: str, line_number: int, character: Any, custom_rules: dict[str, Any], context: dict
    ) -> list[ConsistencyViolation]:
        """カスタムルールをチェック"""
        violations: list[ConsistencyViolation] = []

        # 魔法の色の一貫性チェック
        if "magic_color_consistency" in custom_rules:
            magic_type = character.get_attribute("magic_type")
            if magic_type and magic_type in custom_rules["magic_color_consistency"]:
                expected_color = custom_rules["magic_color_consistency"][magic_type]

                # 魔法使用シーンの検出
                magic_keywords = ["魔法", "呪文", "魔術"]
                active_magic = context.setdefault("active_magic", {})

                if any(keyword in line for keyword in magic_keywords) and character.name in line:
                    active_magic[character.name] = magic_type

                current_magic = active_magic.get(character.name, magic_type)

                color_found = self._extract_color_mention(line)
                if color_found and color_found != expected_color and current_magic == magic_type:
                    violations.append(
                        ConsistencyViolation(
                            character_name=character.name,
                            attribute="magic_color",
                            expected=expected_color,
                            actual=color_found,
                            line_number=line_number,
                            context=line.strip(),
                        )
                    )

        return violations

    def _extract_color_mention(self, line: str) -> str | None:
        """行から色の言及を抽出"""
        colors = [
            "青い",
            "赤い",
            "金色",
            "銀色",
            "黒い",
            "白い",
            "緑色",
            "黄色",
            "赤",
            "青",
            "緑",
            "黄",
            "紫",
            "白",
            "黒",
            "金",
            "銀",
        ]
        for color in colors:
            if color in line:
                return color
        return None

    def _check_with_pronoun_resolution(
        self, episode: Episode, characters: list[Any], context: dict
    ) -> list[ConsistencyViolation]:
        """代名詞を解決してチェック"""
        violations: list[ConsistencyViolation] = []
        lines = episode.content.split("\n")
        character_context = self._build_character_context(lines, characters)

        for i, line in enumerate(lines):
            pronoun_violations = self._check_pronoun_references(line, i + 1, character_context, context)
            violations.extend(pronoun_violations)

        return violations

    def _build_character_context(self, lines: list[str], characters: list[dict[str, Any]]) -> dict[str, Any]:
        """キャラクターコンテキストを構築"""
        character_context = {}

        for line in lines:
            self._update_character_context(line, characters, character_context)

        return character_context

    def _update_character_context(
        self, line: str, characters: list[Any], character_context: dict[str, Any]
    ) -> None:
        """行ごとにキャラクターコンテキストを更新"""
        for character in characters:
            if character.name in line:
                self._assign_pronoun_mapping(character, character_context)
                character_context["last_character"] = character

    def _assign_pronoun_mapping(self, character: Any, character_context: dict[str, Any]) -> None:
        """性別に基づいて代名詞マッピングを作成"""
        gender = character.get_attribute("gender", "") if hasattr(character, "get_attribute") else ""
        if gender == "男性":
            character_context["彼"] = character
        elif gender == "女性":
            character_context["彼女"] = character

    def _check_pronoun_references(
        self, line: str, line_number: int, character_context: dict[str, Any], context: dict
    ) -> list[ConsistencyViolation]:
        """代名詞による記述をチェック"""
        violations: list[ConsistencyViolation] = []
        fallback_character = character_context.get("last_character")

        # 男性代名詞のチェック
        if "彼" in line:
            character = character_context.get("彼")
            if character is None and fallback_character is not None:
                gender = fallback_character.get_attribute("gender", "") if hasattr(fallback_character, "get_attribute") else ""
                if gender in ("", None, "男性"):
                    character = fallback_character
            if character and "彼の" in line:
                violations.extend(self._check_appearance(line, line_number, character, context))

        # 女性代名詞のチェック
        if "彼女" in line:
            character = character_context.get("彼女")
            if character is None and fallback_character is not None:
                gender = fallback_character.get_attribute("gender", "") if hasattr(fallback_character, "get_attribute") else ""
                if gender in ("", None, "女性"):
                    character = fallback_character
            if character and "彼女の" in line:
                violations.extend(self._check_appearance(line, line_number, character, context))

        return violations

    def get_appearance_patterns(self) -> dict[str, dict]:
        """外見描写のパターンを取得"""
        if "appearance" not in self._pattern_cache:
            self._pattern_cache["appearance"] = {
                "hair_color": {
                    "keywords": ["髪", "ヘア", "髪の毛", "頭髪"],
                    "patterns": ["の髪", "髪が", "髪は", "髪を"],
                },
                "eye_color": {"keywords": ["瞳", "目", "眼", "眸"], "patterns": ["の瞳", "瞳が", "目が", "眼が"]},
                "skin_color": {"keywords": ["肌", "皮膚"], "patterns": ["の肌", "肌が", "肌は"]},
            }
        return self._pattern_cache["appearance"]

    def get_personality_patterns(self) -> dict[str, dict]:
        """性格描写のパターンを取得"""
        if "personality" not in self._pattern_cache:
            self._pattern_cache["personality"] = {
                "cheerful": {
                    "indicators": ["明るい", "元気", "活発", "陽気"],
                    "behaviors": ["笑う", "はしゃぐ", "楽しそう"],
                },
                "quiet": {
                    "indicators": ["物静か", "無口", "寡黙", "静か"],
                    "behaviors": ["黙る", "静かに", "ひっそり"],
                },
                "passionate": {"indicators": ["熱血", "情熱的", "熱い"], "behaviors": ["燃える", "熱く語る", "興奮"]},
            }
        return self._pattern_cache["personality"]

    def get_speech_patterns(self) -> dict[str, dict]:
        """話し方のパターンを取得"""
        if "speech" not in self._pattern_cache:
            self._pattern_cache["speech"] = {
                "polite": {
                    "markers": ["です・ます", "でございます", "いたします"],
                    "endings": ["です", "ます", "ません", "でしょう"],
                },
                "masculine_casual": {"markers": ["俺", "だぜ", "だろ"], "endings": ["ぜ", "ぞ", "だ"]},
                "formal": {"markers": ["わたくし", "ございます", "おります"], "endings": ["ございます", "おります"]},
            }
        return self._pattern_cache["speech"]
