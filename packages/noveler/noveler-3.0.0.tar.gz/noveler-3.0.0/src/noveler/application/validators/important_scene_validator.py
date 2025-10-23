#!/usr/bin/env python3

"""Application.validators.important_scene_validator
Where: Application validator checking important scene definitions.
What: Ensures important scenes align with plot and character constraints.
Why: Maintains scene significance accuracy as stories evolve.
"""

from __future__ import annotations

"""重要シーン管理・原稿内容の整合性検証

原稿と重要シーン.yamlの整合性をチェックし、以下を検証:
- 重要シーンの設計要素が原稿に反映されているか
- 感情の流れ（emotional_arc）が適切に描写されているか
- 五感描写（sensory_details）が効果的に使用されているか
- 重要な台詞（key_dialogues）が配置されているか

DDD準拠設計:
- Domain層のValidatorとして実装
- Infrastructure層のRepositoryを利用
- Application層から呼び出し
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from pathlib import Path


class SceneValidationSeverity(Enum):
    """重要シーン検証の重要度"""
    CRITICAL = "critical"  # 致命的: S級シーンで必須要素が未実装
    HIGH = "high"         # 高: A級シーンで重要要素に問題
    MEDIUM = "medium"     # 中: 改善推奨
    LOW = "low"          # 低: 軽微な改善点


@dataclass
class SceneValidationIssue:
    """重要シーン検証で発見された問題"""
    scene_id: str
    scene_title: str
    issue_type: str
    severity: SceneValidationSeverity
    message: str
    line_number: int | None = None
    suggestion: str | None = None
    expected_content: str | None = None
    actual_content: str | None = None


@dataclass
class SceneValidationResult:
    """重要シーン検証結果"""
    episode_number: int
    total_scenes_checked: int
    scenes_implemented: int
    missing_scenes: list[str]
    incomplete_scenes: list[str]
    issues: list[SceneValidationIssue]
    score: float

    def has_critical_issues(self) -> bool:
        """致命的な問題があるか"""
        return any(issue.severity == SceneValidationSeverity.CRITICAL for issue in self.issues)

    def get_issues_by_severity(self, severity: SceneValidationSeverity) -> list[SceneValidationIssue]:
        """重要度別で問題を取得"""
        return [issue for issue in self.issues if issue.severity == severity]


class ImportantSceneValidator:
    """重要シーン管理・原稿内容の整合性検証クラス

    SPEC-IMPORTANT-SCENE-VALIDATION-001: 重要シーン・原稿整合性検証システム
    """

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.scene_file = project_root / "50_管理資料" / "重要シーン.yaml"

    def validate_episode(self, episode_number: int, manuscript_content: str) -> SceneValidationResult:
        """指定エピソードの重要シーン実装状況を検証

        Args:
            episode_number: 検証対象の話数
            manuscript_content: 原稿内容

        Returns:
            SceneValidationResult: 検証結果
        """
        if not self.scene_file.exists():
            return self._create_no_scene_result(episode_number)

        try:
            scene_data = self._load_scene_data()
            return self._validate_episode_content(episode_number, manuscript_content, scene_data)
        except Exception as e:
            return self._create_error_result(episode_number, str(e))

    def _load_scene_data(self) -> dict[str, Any]:
        """重要シーン管理データを読み込み"""
        with self.scene_file.open(encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def _validate_episode_content(self, episode_number: int, manuscript_content: str,
                                scene_data: dict[str, Any]) -> SceneValidationResult:
        """エピソード内容の詳細検証"""
        issues = []
        implemented_count = 0
        missing_scenes = []
        incomplete_scenes = []

        scenes = scene_data.get("scenes", {})
        total_checked = 0

        # 全カテゴリーのシーンをチェック
        for category_name, category_scenes in scenes.items():
            if not isinstance(category_scenes, dict):
                continue

            for scene_id, scene_info in category_scenes.items():
                if not isinstance(scene_info, dict):
                    continue

                episodes = scene_info.get("episodes", [])
                if not self._is_target_episode(episode_number, episodes):
                    continue

                total_checked += 1

                # シーン実装状況を検証
                validation_result = self._validate_scene_implementation(
                    episode_number, manuscript_content, scene_id, scene_info, category_name
                )

                if validation_result.is_implemented:
                    implemented_count += 1

                    # 実装済みシーンの詳細品質チェック
                    quality_issues = self._validate_scene_quality(
                        manuscript_content, scene_id, scene_info, category_name
                    )
                    issues.extend(quality_issues)

                    if quality_issues:
                        incomplete_scenes.append(scene_id)
                else:
                    missing_scenes.append(scene_id)
                    issues.append(SceneValidationIssue(
                        scene_id=scene_id,
                        scene_title=scene_info.get("title", scene_id),
                        issue_type="missing_scene",
                        severity=self._determine_scene_severity(scene_info),
                        message=f"重要シーン「{scene_info.get('title', scene_id)}」が原稿で確認できません",
                        suggestion=f"シーンの実装を確認してください: {scene_info.get('description', '')}",
                        expected_content=scene_info.get("description", "")
                    ))

        # スコア計算
        score = self._calculate_validation_score(total_checked, implemented_count, issues)

        return SceneValidationResult(
            episode_number=episode_number,
            total_scenes_checked=total_checked,
            scenes_implemented=implemented_count,
            missing_scenes=missing_scenes,
            incomplete_scenes=incomplete_scenes,
            issues=issues,
            score=score
        )

    @dataclass
    class SceneImplementationResult:
        is_implemented: bool
        confidence: float
        found_elements: list[str]

    def _validate_scene_implementation(self, episode_number: int, manuscript_content: str,
                                     scene_id: str, scene_info: dict[str, Any],
                                     category: str) -> SceneImplementationResult:
        """シーン実装の基本検証"""
        found_elements = []
        total_score = 0.0
        checks = 0

        # タイトルとdescriptionをチェック
        title = scene_info.get("title", "")
        description = scene_info.get("description", "")

        if title:
            found, confidence = self._search_content_in_manuscript(manuscript_content, title)
            if found:
                found_elements.append(f"タイトル要素: {title}")
            total_score += confidence
            checks += 1

        if description:
            found, confidence = self._search_content_in_manuscript(manuscript_content, description)
            if found:
                found_elements.append(f"描写要素: {description[:30]}...")
            total_score += confidence
            checks += 1

        # 重要台詞をチェック
        key_dialogues = scene_info.get("key_dialogues", [])
        dialogue_matches = 0
        for dialogue in key_dialogues:
            if dialogue and dialogue.strip():
                # 台詞マーカー（「」）を除去してチェック
                clean_dialogue = dialogue.strip('「」"')
                found, confidence = self._search_content_in_manuscript(manuscript_content, clean_dialogue)
                if found:
                    found_elements.append(f"台詞: {dialogue}")
                    dialogue_matches += 1
                total_score += confidence
                checks += 1

        if checks == 0:
            return self.SceneImplementationResult(False, 0.0, [])

        average_confidence = total_score / checks
        is_implemented = average_confidence >= 0.4  # シーンは伏線より緩い基準

        return self.SceneImplementationResult(is_implemented, average_confidence, found_elements)

    def _validate_scene_quality(self, manuscript_content: str, scene_id: str,
                              scene_info: dict[str, Any], category: str) -> list[SceneValidationIssue]:
        """実装済みシーンの品質検証"""
        issues = []
        scene_info.get("title", scene_id)
        importance = scene_info.get("importance_level", "B")

        # 五感描写の検証
        sensory_issues = self._validate_sensory_details(manuscript_content, scene_id, scene_info, importance)
        issues.extend(sensory_issues)

        # 感情変化の検証
        emotional_issues = self._validate_emotional_arc(manuscript_content, scene_id, scene_info, importance)
        issues.extend(emotional_issues)

        # 重要台詞の検証
        dialogue_issues = self._validate_key_dialogues(manuscript_content, scene_id, scene_info, importance)
        issues.extend(dialogue_issues)

        return issues

    def _validate_sensory_details(self, manuscript_content: str, scene_id: str,
                                scene_info: dict[str, Any], importance: str) -> list[SceneValidationIssue]:
        """五感描写の検証"""
        issues = []
        sensory_details = scene_info.get("sensory_details", {})
        scene_title = scene_info.get("title", scene_id)

        if not sensory_details:
            return issues

        # S級、A級シーンでは五感描写をより厳しくチェック
        required_senses = 2 if importance in ["S", "A"] else 1
        implemented_senses = 0

        for sense_type, expected_content in sensory_details.items():
            if expected_content and expected_content.strip():
                found, confidence = self._search_content_in_manuscript(manuscript_content, expected_content)
                if found and confidence >= 0.6:
                    implemented_senses += 1
                elif importance in ["S", "A"]:
                    issues.append(SceneValidationIssue(
                        scene_id=scene_id,
                        scene_title=scene_title,
                        issue_type="missing_sensory_detail",
                        severity=SceneValidationSeverity.HIGH if importance == "S" else SceneValidationSeverity.MEDIUM,
                        message=f"五感描写（{sense_type}）が不十分です: {expected_content[:30]}...",
                        suggestion=f"より具体的な{sense_type}描写を追加してください",
                        expected_content=expected_content
                    ))

        if implemented_senses < required_senses:
            issues.append(SceneValidationIssue(
                scene_id=scene_id,
                scene_title=scene_title,
                issue_type="insufficient_sensory_details",
                severity=SceneValidationSeverity.HIGH if importance == "S" else SceneValidationSeverity.MEDIUM,
                message=f"五感描写が不足しています（実装: {implemented_senses}/{required_senses}）",
                suggestion="より多角的な五感描写でシーンを豊かにしてください"
            ))

        return issues

    def _validate_emotional_arc(self, manuscript_content: str, scene_id: str,
                              scene_info: dict[str, Any], importance: str) -> list[SceneValidationIssue]:
        """感情変化の検証"""
        issues = []
        emotional_arc = scene_info.get("emotional_arc", "")
        scene_title = scene_info.get("title", scene_id)

        if not emotional_arc:
            return issues

        # 感情キーワードを抽出（→で区切られた感情の流れ）
        emotions = [emotion.strip() for emotion in emotional_arc.split("→") if emotion.strip()]
        if len(emotions) < 2:
            return issues

        found_emotions = 0
        for emotion in emotions:
            found, confidence = self._search_emotion_in_manuscript(manuscript_content, emotion)
            if found and confidence >= 0.5:
                found_emotions += 1

        emotion_ratio = found_emotions / len(emotions) if emotions else 0

        # S級、A級シーンでは感情変化をより厳しくチェック
        required_ratio = 0.7 if importance in ["S", "A"] else 0.5

        if emotion_ratio < required_ratio:
            issues.append(SceneValidationIssue(
                scene_id=scene_id,
                scene_title=scene_title,
                issue_type="insufficient_emotional_arc",
                severity=SceneValidationSeverity.HIGH if importance == "S" else SceneValidationSeverity.MEDIUM,
                message=f"感情変化の描写が不足しています（検出: {found_emotions}/{len(emotions)}）",
                suggestion=f"感情の流れを明確に描写してください: {emotional_arc}",
                expected_content=emotional_arc
            ))

        return issues

    def _validate_key_dialogues(self, manuscript_content: str, scene_id: str,
                              scene_info: dict[str, Any], importance: str) -> list[SceneValidationIssue]:
        """重要台詞の検証"""
        issues = []
        key_dialogues = scene_info.get("key_dialogues", [])
        scene_title = scene_info.get("title", scene_id)

        if not key_dialogues:
            return issues

        found_dialogues = 0
        for dialogue in key_dialogues:
            if dialogue and dialogue.strip():
                clean_dialogue = dialogue.strip('「」"')
                found, confidence = self._search_content_in_manuscript(manuscript_content, clean_dialogue)
                if found and confidence >= 0.8:  # 台詞は高い精度を要求
                    found_dialogues += 1

        dialogue_ratio = found_dialogues / len(key_dialogues) if key_dialogues else 0

        # S級シーンでは重要台詞の実装を厳格にチェック
        required_ratio = 0.8 if importance == "S" else 0.6

        if dialogue_ratio < required_ratio:
            issues.append(SceneValidationIssue(
                scene_id=scene_id,
                scene_title=scene_title,
                issue_type="missing_key_dialogues",
                severity=SceneValidationSeverity.HIGH if importance == "S" else SceneValidationSeverity.MEDIUM,
                message=f"重要台詞の実装が不足しています（実装: {found_dialogues}/{len(key_dialogues)}）",
                suggestion="設計された重要台詞を適切に配置してください"
            ))

        return issues

    def _is_target_episode(self, current_episode: int, target_episodes: list[Any]) -> bool:
        """指定エピソードが対象かチェック"""
        if not target_episodes:
            return False

        for episode in target_episodes:
            if isinstance(episode, int):
                if current_episode == episode:
                    return True
            elif isinstance(episode, str):
                # "第001話" -> 1 に変換
                match = re.search(r"第(\d+)話", episode)
                if match:
                    target_num = int(match.group(1))
                    if current_episode == target_num:
                        return True
                # 数字のみの場合
                try:
                    target_num = int(episode)
                    if current_episode == target_num:
                        return True
                except ValueError:
                    continue

        return False

    def _search_content_in_manuscript(self, manuscript: str, expected_content: str) -> tuple[bool, float]:
        """原稿内で期待する内容を検索"""
        if not expected_content.strip():
            return False, 0.0

        manuscript_lower = manuscript.lower()
        expected_lower = expected_content.lower()

        # 直接一致検索
        if expected_lower in manuscript_lower:
            return True, 1.0

        # キーワード分割検索
        keywords = [word.strip() for word in expected_content.split() if len(word.strip()) > 1]
        if not keywords:
            return False, 0.0

        found_keywords = sum(1 for keyword in keywords if keyword.lower() in manuscript_lower)
        confidence = found_keywords / len(keywords)

        # シーンは伏線より緩い閾値
        return confidence >= 0.5, confidence

    def _search_emotion_in_manuscript(self, manuscript: str, emotion: str) -> tuple[bool, float]:
        """原稿内で感情表現を検索"""
        # 感情に関連するキーワードマップ
        emotion_keywords = {
            "喜び": ["嬉しい", "楽しい", "幸せ", "喜ぶ", "笑顔", "笑う", "微笑", "うれしい"],
            "悲しみ": ["悲しい", "辛い", "寂しい", "泣く", "涙", "哀しい", "かなしい"],
            "怒り": ["怒る", "腹立つ", "憤る", "むかつく", "激怒", "いらだつ", "おこる"],
            "恐怖": ["怖い", "恐ろしい", "不安", "怯える", "震える", "こわい"],
            "驚き": ["驚く", "びっくり", "衝撃", "呆然", "おどろく"],
            "困惑": ["困る", "戸惑う", "迷う", "混乱", "こまる"],
            "安堵": ["安心", "ほっと", "安らぐ", "ほっとする"],
            "緊張": ["緊張", "ドキドキ", "焦る", "緊迫"],
            "希望": ["希望", "期待", "願う", "望む"],
            "絶望": ["絶望", "諦める", "落胆", "あきらめる"]
        }

        manuscript_lower = manuscript.lower()

        # 直接感情語検索
        if emotion.lower() in manuscript_lower:
            return True, 1.0

        # 関連キーワード検索
        related_keywords = emotion_keywords.get(emotion, [emotion])
        found_count = sum(1 for keyword in related_keywords if keyword in manuscript_lower)

        if found_count > 0:
            confidence = min(found_count / len(related_keywords), 1.0)
            return confidence >= 0.3, confidence

        return False, 0.0

    def _determine_scene_severity(self, scene_info: dict[str, Any]) -> SceneValidationSeverity:
        """シーン不備の重要度を判定"""
        importance = scene_info.get("importance_level", "B")

        if importance == "S":
            return SceneValidationSeverity.CRITICAL
        if importance == "A":
            return SceneValidationSeverity.HIGH
        if importance == "B":
            return SceneValidationSeverity.MEDIUM
        return SceneValidationSeverity.LOW

    def _calculate_validation_score(self, total_checked: int, implemented_count: int,
                                  issues: list[SceneValidationIssue]) -> float:
        """検証スコアを計算"""
        if total_checked == 0:
            return 100.0

        base_score = 100.0

        # 実装率による基本スコア
        implementation_ratio = implemented_count / total_checked if total_checked > 0 else 1.0
        base_score *= implementation_ratio

        # 問題による減点
        for issue in issues:
            if issue.severity == SceneValidationSeverity.CRITICAL:
                base_score -= 20.0
            elif issue.severity == SceneValidationSeverity.HIGH:
                base_score -= 12.0
            elif issue.severity == SceneValidationSeverity.MEDIUM:
                base_score -= 6.0
            elif issue.severity == SceneValidationSeverity.LOW:
                base_score -= 2.0

        return max(base_score, 0.0)

    def _create_no_scene_result(self, episode_number: int) -> SceneValidationResult:
        """重要シーン管理ファイルが存在しない場合の結果"""
        return SceneValidationResult(
            episode_number=episode_number,
            total_scenes_checked=0,
            scenes_implemented=0,
            missing_scenes=[],
            incomplete_scenes=[],
            issues=[],
            score=100.0  # シーンがなければ問題なし
        )

    def _create_error_result(self, episode_number: int, error_message: str) -> SceneValidationResult:
        """エラー時の結果"""
        return SceneValidationResult(
            episode_number=episode_number,
            total_scenes_checked=0,
            scenes_implemented=0,
            missing_scenes=[],
            incomplete_scenes=[],
            issues=[SceneValidationIssue(
                scene_id="SYSTEM",
                scene_title="システムエラー",
                issue_type="validation_error",
                severity=SceneValidationSeverity.HIGH,
                message=f"重要シーン検証エラー: {error_message}",
                suggestion="重要シーン.yamlファイルの形式を確認してください"
            )],
            score=50.0
        )
