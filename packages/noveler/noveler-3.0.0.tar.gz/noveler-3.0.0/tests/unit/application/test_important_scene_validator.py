#!/usr/bin/env python3
"""重要シーン検証機能のテスト"""

import pytest
import yaml
from pathlib import Path
from unittest.mock import Mock, patch

from noveler.application.validators.important_scene_validator import (
    ImportantSceneValidator,
    SceneValidationResult,
    SceneValidationSeverity,
    SceneValidationIssue
)


class TestImportantSceneValidator:
    """重要シーン検証機能のテストクラス"""

    @pytest.fixture
    def project_root(self, tmp_path):
        """テスト用プロジェクトルート"""
        return tmp_path / "test_project"

    @pytest.fixture
    def validator(self, project_root):
        """テスト用validator"""
        return ImportantSceneValidator(project_root)

    @pytest.fixture
    def sample_scene_data(self):
        """サンプルシーンデータ"""
        return {
            'scenes': {
                'opening': {
                    'first_encounter': {
                        'title': '運命的な出会い',
                        'description': '主人公とヒロインの初対面シーン',
                        'episodes': [1],
                        'importance_level': 'S',
                        'sensory_details': {
                            'visual': '夕暮れの街角、オレンジ色の光',
                            'auditory': '街の喧騒、風の音',
                            'tactile': 'ひんやりとした風',
                            'olfactory': '焼きたてのパンの香り'
                        },
                        'emotional_arc': '好奇心 → 驚き → 興味',
                        'key_dialogues': [
                            '「あなたは...まさか」',
                            '「運命なんて信じない」'
                        ]
                    }
                },
                'climax': {
                    'final_battle': {
                        'title': '最終決戦',
                        'description': '主人公と敵の最後の戦い',
                        'episodes': [45, 46],
                        'importance_level': 'S',
                        'sensory_details': {
                            'visual': '荒れ果てた戦場、光と闇',
                            'auditory': '剣戟の音、叫び声'
                        },
                        'emotional_arc': '緊張 → 絶望 → 希望 → 勝利',
                        'key_dialogues': [
                            '「これで終わりにしよう」'
                        ]
                    }
                },
                'emotional': {
                    'farewell': {
                        'title': '別れの時',
                        'description': '仲間との別れのシーン',
                        'episodes': [30],
                        'importance_level': 'A',
                        'sensory_details': {
                            'visual': '夕陽に照らされた駅のホーム'
                        },
                        'emotional_arc': '悲しみ → 感謝 → 希望',
                        'key_dialogues': [
                            '「ありがとう、すべてに」'
                        ]
                    }
                }
            }
        }

    def test_validate_episode_no_file(self, validator):
        """重要シーン管理ファイルが存在しない場合のテスト"""
        result = validator.validate_episode(1, "原稿内容")

        assert result.episode_number == 1
        assert result.total_scenes_checked == 0
        assert result.score == 100.0
        assert len(result.issues) == 0

    def test_validate_episode_with_implemented_scene(self, validator, project_root, sample_scene_data):
        """実装済みシーンのテスト"""
        # シーン管理ファイルを作成
        management_dir = project_root / "50_管理資料"
        management_dir.mkdir(parents=True)
        scene_file = management_dir / "重要シーン.yaml"

        with open(scene_file, 'w', encoding='utf-8') as f:
            yaml.dump(sample_scene_data, f, allow_unicode=True)

        # シーンが実装された原稿内容
        manuscript = """
        夕暮れの街角、オレンジ色の光が差し込んでいた。
        街の喧騒、風の音が聞こえる中、主人公は歩いていた。
        ひんやりとした風が頬を撫でて、焼きたてのパンの香りが漂った。

        そこで彼女と出会った。
        「あなたは...まさか」と彼女は驚いた。
        「運命なんて信じない。でも、今日は違う気がする」と主人公は答えた。

        それはまさに運命的な出会いの瞬間で、主人公とヒロインの初対面シーンだった。
        最初は好奇心だったが、徐々に驚きに変わり、そして興味を持つようになった。
        """

        result = validator.validate_episode(1, manuscript)

        assert result.episode_number == 1
        assert result.total_scenes_checked == 1
        assert result.scenes_implemented == 1
        assert result.score > 80.0  # 高スコア
        assert len(result.missing_scenes) == 0

    def test_validate_episode_missing_scene(self, validator, project_root, sample_scene_data):
        """未実装シーンのテスト"""
        management_dir = project_root / "50_管理資料"
        management_dir.mkdir(parents=True)
        scene_file = management_dir / "重要シーン.yaml"

        with open(scene_file, 'w', encoding='utf-8') as f:
            yaml.dump(sample_scene_data, f, allow_unicode=True)

        # シーンが実装されていない原稿
        manuscript = """
        主人公は街を歩いていた。
        特に印象的なことは何も起こらなかった。
        """

        result = validator.validate_episode(1, manuscript)

        assert result.episode_number == 1
        assert result.scenes_implemented == 0
        assert len(result.missing_scenes) == 1
        assert result.has_critical_issues()

        # S級シーンなので致命的問題になるはず
        critical_issues = result.get_issues_by_severity(SceneValidationSeverity.CRITICAL)
        assert len(critical_issues) >= 1

    def test_sensory_details_validation(self, validator, project_root, sample_scene_data):
        """五感描写検証のテスト"""
        management_dir = project_root / "50_管理資料"
        management_dir.mkdir(parents=True)
        scene_file = management_dir / "重要シーン.yaml"

        with open(scene_file, 'w', encoding='utf-8') as f:
            yaml.dump(sample_scene_data, f, allow_unicode=True)

        # 五感描写が不十分な原稿
        manuscript = """
        主人公とヒロインが出会った。
        「あなたは...まさか」と彼女は言った。
        「運命なんて信じない」と主人公は答えた。
        """

        result = validator.validate_episode(1, manuscript)

        # S級シーンで五感描写が不足しているので問題があるはず
        sensory_issues = [issue for issue in result.issues
                         if "sensory" in issue.issue_type or "五感" in issue.message]
        assert len(sensory_issues) > 0

    def test_emotional_arc_validation(self, validator, project_root):
        """感情変化検証のテスト"""
        scene_data = {
            'scenes': {
                'test': {
                    'emotional_scene': {
                        'title': 'テスト感情シーン',
                        'description': '感情変化のテストシーン',
                        'episodes': [1],
                        'importance_level': 'A',
                        'emotional_arc': '悲しみ → 怒り → 諦め → 希望',
                        'sensory_details': {},
                        'key_dialogues': []
                    }
                }
            }
        }

        management_dir = project_root / "50_管理資料"
        management_dir.mkdir(parents=True)
        scene_file = management_dir / "重要シーン.yaml"

        with open(scene_file, 'w', encoding='utf-8') as f:
            yaml.dump(scene_data, f, allow_unicode=True)

        # 感情変化が適切に描写された原稿
        manuscript = """
        これは感情変化のテストシーンとして描かれた物語だ。
        最初は深い悲しみに包まれていた。
        しかし徐々に怒りが湧き上がってきた。
        やがてその怒りも諦めに変わった。
        でも最後に、小さな希望の光が見えた。
        """

        result = validator.validate_episode(1, manuscript)

        # 適切な感情変化が描写されているので問題は少ないはず
        emotional_issues = [issue for issue in result.issues
                           if "emotional" in issue.issue_type or "感情" in issue.message]
        assert len(emotional_issues) == 0 or result.score > 70.0

    def test_key_dialogues_validation(self, validator, project_root, sample_scene_data):
        """重要台詞検証のテスト"""
        management_dir = project_root / "50_管理資料"
        management_dir.mkdir(parents=True)
        scene_file = management_dir / "重要シーン.yaml"

        with open(scene_file, 'w', encoding='utf-8') as f:
            yaml.dump(sample_scene_data, f, allow_unicode=True)

        # 重要台詞が欠けている原稿
        manuscript = """
        夕暮れの街角、オレンジ色の光が差し込む運命的な出会いの場所で彼女と出会った。
        街の喧騒、風の音が耳を打ち、ひんやりとした風が頬を撫でた。
        焼きたてのパンの香りが漂うが、重要な台詞は交わされなかった。
        主人公とヒロインの初対面シーンであることだけが静かに語られていた。
        """

        result = validator.validate_episode(1, manuscript)

        # 重要台詞が不足しているので問題があるはず
        dialogue_issues = [issue for issue in result.issues
                          if "dialogue" in issue.issue_type or "台詞" in issue.message]
        assert len(dialogue_issues) > 0

    def test_episode_number_matching(self, validator):
        """エピソード番号マッチングのテスト"""
        # 整数配列
        assert validator._is_target_episode(1, [1, 2, 3]) == True
        assert validator._is_target_episode(4, [1, 2, 3]) == False

        # 文字列配列
        assert validator._is_target_episode(1, ["第001話", "第002話"]) == True
        assert validator._is_target_episode(3, ["第001話", "第002話"]) == False

        # 混合配列
        assert validator._is_target_episode(1, [1, "第002話"]) == True
        assert validator._is_target_episode(2, [1, "第002話"]) == True
        assert validator._is_target_episode(3, [1, "第002話"]) == False

    def test_emotion_search_accuracy(self, validator):
        """感情表現検索の精度テスト"""
        manuscript = "主人公は深い悲しみに包まれ、悲しい涙を流した。"

        # 直接的な感情語
        found, confidence = validator._search_emotion_in_manuscript(manuscript, "悲しみ")
        assert found == True
        assert confidence == 1.0

        # 関連キーワード
        found, confidence = validator._search_emotion_in_manuscript(manuscript, "悲しい")
        assert found == True
        assert confidence > 0.3

        # 一致しない感情
        found, confidence = validator._search_emotion_in_manuscript(manuscript, "喜び")
        assert found == False

    def test_importance_level_severity_mapping(self, validator):
        """重要度レベルと重要度マッピングのテスト"""
        # S級 → CRITICAL
        scene_info = {'importance_level': 'S'}
        severity = validator._determine_scene_severity(scene_info)
        assert severity == SceneValidationSeverity.CRITICAL

        # A級 → HIGH
        scene_info = {'importance_level': 'A'}
        severity = validator._determine_scene_severity(scene_info)
        assert severity == SceneValidationSeverity.HIGH

        # B級 → MEDIUM
        scene_info = {'importance_level': 'B'}
        severity = validator._determine_scene_severity(scene_info)
        assert severity == SceneValidationSeverity.MEDIUM

        # その他 → LOW
        scene_info = {'importance_level': 'C'}
        severity = validator._determine_scene_severity(scene_info)
        assert severity == SceneValidationSeverity.LOW

    def test_score_calculation_with_implementation_ratio(self, validator):
        """実装率を含むスコア計算のテスト"""
        issues = [
            Mock(severity=SceneValidationSeverity.CRITICAL),
            Mock(severity=SceneValidationSeverity.HIGH)
        ]

        # 50%実装率の場合
        score = validator._calculate_validation_score(4, 2, issues)

        # 基本スコア(100 * 0.5 = 50) から減点(20 + 12 = 32)
        expected_score = 50.0 - 32.0
        assert score == max(expected_score, 0.0)

    def test_error_handling(self, validator, project_root):
        """エラーハンドリングのテスト"""
        # 無効なYAMLファイル
        management_dir = project_root / "50_管理資料"
        management_dir.mkdir(parents=True)
        scene_file = management_dir / "重要シーン.yaml"

        with open(scene_file, 'w', encoding='utf-8') as f:
            f.write("invalid: yaml: content: [")

        result = validator.validate_episode(1, "test content")

        assert result.episode_number == 1
        assert result.score == 50.0  # エラー時のスコア
        assert len(result.issues) == 1
        assert result.issues[0].issue_type == "validation_error"


@pytest.mark.spec('SPEC-IMPORTANT-SCENE-VALIDATION-001')
class TestImportantSceneValidationIntegration:
    """重要シーン検証統合テスト"""

    def test_multi_episode_scene(self, tmp_path):
        """複数話にまたがるシーンのテスト"""
        project_root = tmp_path / "novel_project"
        validator = ImportantSceneValidator(project_root)

        scene_data = {
            'scenes': {
                'climax': {
                    'final_battle': {
                        'title': '最終決戦',
                        'description': '3話にわたる壮大な戦い',
                        'episodes': [45, 46, 47],
                        'importance_level': 'S',
                        'sensory_details': {
                            'visual': '炎と氷の魔法が交錯する',
                            'auditory': '魔法の爆発音'
                        },
                        'emotional_arc': '緊張 → 絶望 → 希望 → 勝利',
                        'key_dialogues': [
                            '「最後の力を振り絞れ」'
                        ]
                    }
                }
            }
        }

        # ファイル作成
        management_dir = project_root / "50_管理資料"
        management_dir.mkdir(parents=True)

        with open(management_dir / "重要シーン.yaml", 'w', encoding='utf-8') as f:
            yaml.dump(scene_data, f, allow_unicode=True)

        # 第45話のテスト
        manuscript_ep45 = """
        いよいよ最終決戦が始まった。
        これは3話にわたる壮大な戦いの幕開けだった。
        炎と氷の魔法が交錯する光景の中、魔法の爆発音が響いた。
        緊張が極限まで高まっていた。
        """

        result_ep45 = validator.validate_episode(45, manuscript_ep45)
        assert result_ep45.total_scenes_checked == 1
        assert result_ep45.scenes_implemented == 1

        # 第46話のテスト
        manuscript_ep46 = """
        最終決戦は絶望的な状況に陥った。
        しかし「最後の力を振り絞れ」という声が聞こえた。
        希望の光が見え始めた。
        """

        result_ep46 = validator.validate_episode(46, manuscript_ep46)
        assert result_ep46.scenes_implemented == 1

        # 第47話のテスト
        manuscript_ep47 = """
        3話にわたる壮大な戦いの末、ついに勝利を収めた。
        最終決戦は終わり、長い戦いが幕を閉じた。
        """

        result_ep47 = validator.validate_episode(47, manuscript_ep47)
        assert result_ep47.scenes_implemented == 1

    def test_scene_quality_gradation(self, tmp_path):
        """シーン品質の段階的評価テスト"""
        project_root = tmp_path / "novel_project"
        validator = ImportantSceneValidator(project_root)

        scene_data = {
            'scenes': {
                'test': {
                    's_grade_scene': {
                        'title': 'S級シーン',
                        'episodes': [1],
                        'importance_level': 'S',
                        'sensory_details': {
                            'visual': '美しい夕焼け',
                            'auditory': '鳥のさえずり'
                        },
                        'emotional_arc': '平穏 → 驚き → 感動',
                        'key_dialogues': ['「これは素晴らしい」']
                    },
                    'b_grade_scene': {
                        'title': 'B級シーン',
                        'episodes': [2],
                        'importance_level': 'B',
                        'sensory_details': {
                            'visual': '普通の部屋'
                        },
                        'emotional_arc': '普通 → 少し興味深い',
                        'key_dialogues': ['「そうですね」']
                    }
                }
            }
        }

        management_dir = project_root / "50_管理資料"
        management_dir.mkdir(parents=True)

        with open(management_dir / "重要シーン.yaml", 'w', encoding='utf-8') as f:
            yaml.dump(scene_data, f, allow_unicode=True)

        # 不完全な実装（S級なのに品質が低い）
        poor_manuscript = """
        夕焼けがあった。
        何か言った。
        """

        result_s = validator.validate_episode(1, poor_manuscript)

        # B級シーンの不完全な実装
        result_b = validator.validate_episode(2, poor_manuscript)

        # S級の方がより厳しく評価されるはず
        s_issues = [issue for issue in result_s.issues if issue.severity == SceneValidationSeverity.HIGH]
        b_issues = [issue for issue in result_b.issues if issue.severity == SceneValidationSeverity.HIGH]

        assert len(s_issues) >= len(b_issues)  # S級の方が問題が多く検出される
