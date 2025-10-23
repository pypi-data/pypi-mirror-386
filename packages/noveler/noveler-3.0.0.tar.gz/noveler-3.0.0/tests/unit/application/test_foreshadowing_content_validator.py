#!/usr/bin/env python3
"""伏線内容検証機能のテスト"""

import pytest
import yaml
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

from noveler.application.validators.foreshadowing_content_validator import (
    ForeshadowingContentValidator,
    ForeshadowingValidationResult,
    ForeshadowingValidationSeverity,
    ForeshadowingValidationIssue
)


class TestForeshadowingContentValidator:
    """伏線内容検証機能のテストクラス"""

    @pytest.fixture
    def project_root(self, tmp_path):
        """テスト用プロジェクトルート"""
        return tmp_path / "test_project"

    @pytest.fixture
    def validator(self, project_root):
        """テスト用validator"""
        return ForeshadowingContentValidator(project_root)

    @pytest.fixture
    def sample_foreshadowing_data(self):
        """サンプル伏線データ"""
        return {
            'foreshadowing': {
                'F001': {
                    'title': '魔王の封印',
                    'importance': 5,
                    'planting': {
                        'episode': '第001話',
                        'content': '古い石碑に刻まれた文字',
                        'method': '主人公が発見'
                    },
                    'resolution': {
                        'episode': '第025話',
                        'method': '封印の真実が判明',
                        'impact': '世界の運命が決まる'
                    },
                    'hints': [
                        {
                            'episode': '第010話',
                            'content': '石碑の謎の記号'
                        }
                    ]
                },
                'F002': {
                    'title': 'サブキャラの正体',
                    'importance': 3,
                    'planting': {
                        'episode': '第001話',
                        'content': '謎めいた笑顔',
                        'method': '初登場シーンで示唆'
                    },
                    'resolution': {
                        'episode': '第015話',
                        'method': '正体が明かされる',
                        'impact': '主人公に衝撃'
                    }
                }
            }
        }

    def test_validate_episode_no_file(self, validator):
        """伏線管理ファイルが存在しない場合のテスト"""
        result = validator.validate_episode(1, "原稿内容")

        assert result.episode_number == 1
        assert result.total_foreshadowing_checked == 0
        assert result.score == 100.0
        assert len(result.issues) == 0

    def test_validate_episode_with_planted_foreshadowing(self, validator, project_root, sample_foreshadowing_data):
        """仕込み済み伏線のテスト"""
        # 伏線管理ファイルを作成
        management_dir = project_root / "50_管理資料"
        management_dir.mkdir(parents=True)
        foreshadowing_file = management_dir / "伏線管理.yaml"

        with open(foreshadowing_file, 'w', encoding='utf-8') as f:
            yaml.dump(sample_foreshadowing_data, f, allow_unicode=True)

        # 伏線が含まれた原稿内容
        manuscript = """
        主人公は遺跡を探索していた。
        古い石碑に刻まれた文字を発見した。
        それは何かの封印について記されているようだった。
        謎めいた笑顔を浮かべる仲間がいた。
        """

        result = validator.validate_episode(1, manuscript)

        assert result.episode_number == 1
        assert result.total_foreshadowing_checked == 2
        assert result.planted_count == 2  # 両方とも仕込み済み
        assert result.score > 80.0  # 高スコア

    def test_validate_episode_missing_planting(self, validator, project_root, sample_foreshadowing_data):
        """未仕込み伏線のテスト"""
        management_dir = project_root / "50_管理資料"
        management_dir.mkdir(parents=True)
        foreshadowing_file = management_dir / "伏線管理.yaml"

        with open(foreshadowing_file, 'w', encoding='utf-8') as f:
            yaml.dump(sample_foreshadowing_data, f, allow_unicode=True)

        # 伏線が含まれていない原稿
        manuscript = """
        主人公は街を歩いていた。
        何も特別なことは起こらなかった。
        """

        result = validator.validate_episode(1, manuscript)

        assert result.episode_number == 1
        assert result.planted_count == 0
        assert len(result.missing_plantings) == 2
        assert result.has_critical_issues()

        # 重要度5のF001は致命的問題になるはず
        critical_issues = result.get_issues_by_severity(ForeshadowingValidationSeverity.CRITICAL)
        assert len(critical_issues) >= 1
        assert any("魔王の封印" in issue.message for issue in critical_issues)

    def test_validate_episode_with_resolution(self, validator, project_root, sample_foreshadowing_data):
        """回収済み伏線のテスト"""
        management_dir = project_root / "50_管理資料"
        management_dir.mkdir(parents=True)
        foreshadowing_file = management_dir / "伏線管理.yaml"

        with open(foreshadowing_file, 'w', encoding='utf-8') as f:
            yaml.dump(sample_foreshadowing_data, f, allow_unicode=True)

        # 第25話での回収シーン
        manuscript = """
        ついに封印の真実が判明した。
        世界の運命が決まる瞬間だった。
        石碑に記された古代の秘密が明らかになった。
        """

        result = validator.validate_episode(25, manuscript)

        assert result.episode_number == 25
        assert result.resolved_count == 1  # F001が回収される
        assert result.score > 70.0

    def test_validate_hints(self, validator, project_root, sample_foreshadowing_data):
        """ヒント実装のテスト"""
        management_dir = project_root / "50_管理資料"
        management_dir.mkdir(parents=True)
        foreshadowing_file = management_dir / "伏線管理.yaml"

        with open(foreshadowing_file, 'w', encoding='utf-8') as f:
            yaml.dump(sample_foreshadowing_data, f, allow_unicode=True)

        # 第10話でのヒントシーン
        manuscript = """
        石碑の謎の記号が静かに浮かび上がった。
        それは何かの暗号のようだった。
        """

        result = validator.validate_episode(10, manuscript)

        # ヒントが含まれているので問題は少ないはず
        hint_issues = [issue for issue in result.issues if issue.issue_type == "missing_hint"]
        assert len(hint_issues) == 0

    def test_episode_number_parsing(self, validator):
        """エピソード番号解析のテスト"""
        # "第001話" 形式
        assert validator._is_target_episode(1, "第001話") == True
        assert validator._is_target_episode(1, "第002話") == False

        # 数字のみ形式
        assert validator._is_target_episode(1, "1") == True
        assert validator._is_target_episode(1, "2") == False

        # 無効な形式
        assert validator._is_target_episode(1, "invalid") == False
        assert validator._is_target_episode(1, "") == False

    def test_content_search_accuracy(self, validator):
        """内容検索の精度テスト"""
        manuscript = "主人公は古い石碑に刻まれた文字を発見した。"

        # 完全一致
        found, confidence = validator._search_content_in_manuscript(
            manuscript, "古い石碑に刻まれた文字", "主人公が発見"
        )
        assert found == True
        assert confidence == 1.0

        # 部分一致
        found, confidence = validator._search_content_in_manuscript(
            manuscript, "石碑 文字 発見", "主人公が発見"
        )
        assert found == True
        assert confidence >= 0.6

        # 一致なし
        found, confidence = validator._search_content_in_manuscript(
            manuscript, "魔法の杖", "主人公が発見"
        )
        assert found == False
        assert confidence < 0.6

    def test_severity_determination(self, validator):
        """重要度判定のテスト"""
        # 重要度5 → CRITICAL
        foreshadowing_info = {'importance': 5}
        severity = validator._determine_planting_severity(foreshadowing_info)
        assert severity == ForeshadowingValidationSeverity.CRITICAL

        # 重要度4 → HIGH
        foreshadowing_info = {'importance': 4}
        severity = validator._determine_planting_severity(foreshadowing_info)
        assert severity == ForeshadowingValidationSeverity.HIGH

        # 重要度3 → MEDIUM
        foreshadowing_info = {'importance': 3}
        severity = validator._determine_planting_severity(foreshadowing_info)
        assert severity == ForeshadowingValidationSeverity.MEDIUM

        # 重要度1-2 → LOW
        foreshadowing_info = {'importance': 1}
        severity = validator._determine_planting_severity(foreshadowing_info)
        assert severity == ForeshadowingValidationSeverity.LOW

    def test_score_calculation(self, validator):
        """スコア計算のテスト"""
        issues = [
            Mock(severity=ForeshadowingValidationSeverity.CRITICAL),
            Mock(severity=ForeshadowingValidationSeverity.HIGH),
            Mock(severity=ForeshadowingValidationSeverity.MEDIUM),
            Mock(severity=ForeshadowingValidationSeverity.LOW),
        ]

        score = validator._calculate_validation_score(4, 2, 1, issues)

        # 基本スコア100から各重要度に応じて減点されるはず
        expected_deductions = 25.0 + 15.0 + 8.0 + 3.0  # 51.0
        expected_score = 100.0 - expected_deductions
        assert score == max(expected_score, 0.0)

    def test_error_handling(self, validator, project_root):
        """エラーハンドリングのテスト"""
        # 無効なYAMLファイル
        management_dir = project_root / "50_管理資料"
        management_dir.mkdir(parents=True)
        foreshadowing_file = management_dir / "伏線管理.yaml"

        with open(foreshadowing_file, 'w', encoding='utf-8') as f:
            f.write("invalid: yaml: content: [")

        result = validator.validate_episode(1, "test content")

        assert result.episode_number == 1
        assert result.score == 50.0  # エラー時のスコア
        assert len(result.issues) == 1
        assert result.issues[0].issue_type == "validation_error"


@pytest.mark.spec('SPEC-FORESHADOWING-VALIDATION-001')
class TestForeshadowingValidationIntegration:
    """伏線検証統合テスト"""

    def test_real_world_scenario(self, tmp_path):
        """実際の使用シナリオのテスト"""
        project_root = tmp_path / "novel_project"
        validator = ForeshadowingContentValidator(project_root)

        # リアルな伏線データ
        foreshadowing_data = {
            'foreshadowing': {
                'F001': {
                    'title': '主人公の出生の秘密',
                    'importance': 5,
                    'planting': {
                        'episode': '第001話',
                        'content': '母親の形見のペンダント',
                        'method': '何気ない描写として'
                    },
                    'resolution': {
                        'episode': '第030話',
                        'method': 'ペンダントが王家の証であると判明',
                        'impact': '主人公の運命が変わる'
                    },
                    'hints': [
                        {
                            'episode': '第005話',
                            'content': '老人がペンダントを見て驚く'
                        },
                        {
                            'episode': '第015話',
                            'content': '同じ紋章が城で発見される'
                        }
                    ]
                }
            }
        }

        # ファイル作成
        management_dir = project_root / "50_管理資料"
        management_dir.mkdir(parents=True)

        with open(management_dir / "伏線管理.yaml", 'w', encoding='utf-8') as f:
            yaml.dump(foreshadowing_data, f, allow_unicode=True)

        # 第1話のテスト（仕込みシーン）
        manuscript_ep1 = """
        主人公は冒険に出る前に、亡き母親の形見のペンダントを首にかけた。
        それは何の変哲もない銀のペンダントだった。
        """

        result_ep1 = validator.validate_episode(1, manuscript_ep1)
        assert result_ep1.planted_count == 1
        assert result_ep1.score > 80.0

        # 第5話のテスト（ヒントシーン）
        manuscript_ep5 = """
        宿屋で出会った老人が、主人公のペンダントを見て驚いた。
        「そのペンダントは一体...」
        老人は何も言わずに立ち去った。
        老人がペンダントを見て驚く描写がそこにあった。
        """

        result_ep5 = validator.validate_episode(5, manuscript_ep5)
        hint_issues = [issue for issue in result_ep5.issues if issue.issue_type == "missing_hint"]
        assert len(hint_issues) == 0  # ヒントが適切に配置されている

        # 第30話のテスト（回収シーン）
        manuscript_ep30 = """
        ついにペンダントが王家の証であると判明した。
        主人公の運命が変わる瞬間だった。
        今まで知らなかった自分の出生の秘密が明らかになった。
        """

        result_ep30 = validator.validate_episode(30, manuscript_ep30)
        assert result_ep30.resolved_count == 1
        assert result_ep30.score > 85.0
