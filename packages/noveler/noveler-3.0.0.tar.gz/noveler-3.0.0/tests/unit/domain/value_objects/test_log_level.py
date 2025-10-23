"""LogLevel値オブジェクトのテスト"""

import pytest

from noveler.domain.value_objects.log_level import LogLevel


pytestmark = pytest.mark.vo_smoke


@pytest.mark.spec("SPEC-API-001")
class TestLogLevel:
    """LogLevel値オブジェクトのテスト"""

    @pytest.mark.spec("SPEC-API-001")
    def test_log_level_values(self) -> None:
        """各ログレベルが定義されていること"""
        assert LogLevel.DEBUG.value == "DEBUG"
        assert LogLevel.INFO.value == "INFO"
        assert LogLevel.WARNING.value == "WARNING"
        assert LogLevel.ERROR.value == "ERROR"
        assert LogLevel.CRITICAL.value == "CRITICAL"

    @pytest.mark.spec("SPEC-API-001")
    def test_string_conversion(self) -> None:
        """文字列変換が正しく行われること"""
        assert str(LogLevel.DEBUG) == "LogLevel.DEBUG"
        assert LogLevel.DEBUG.value == "DEBUG"
        assert repr(LogLevel.DEBUG) == "<LogLevel.DEBUG: 'DEBUG'>"

    @pytest.mark.spec("SPEC-API-001")
    def test_equality(self) -> None:
        """等価性の判定が正しく行われること"""
        assert LogLevel.DEBUG == LogLevel.DEBUG
        assert LogLevel.INFO == LogLevel.INFO
        assert LogLevel.DEBUG != LogLevel.INFO
        assert LogLevel.ERROR != LogLevel.WARNING

    @pytest.mark.spec("SPEC-API-001")
    def test_from_string(self) -> None:
        """文字列からLogLevelを作成できること"""
        assert LogLevel.from_string("DEBUG") == LogLevel.DEBUG
        assert LogLevel.from_string("INFO") == LogLevel.INFO
        assert LogLevel.from_string("WARNING") == LogLevel.WARNING
        assert LogLevel.from_string("ERROR") == LogLevel.ERROR
        assert LogLevel.from_string("CRITICAL") == LogLevel.CRITICAL

        # 小文字も受け付ける
        assert LogLevel.from_string("debug") == LogLevel.DEBUG
        assert LogLevel.from_string("info") == LogLevel.INFO

        # 無効な値
        with pytest.raises(ValueError, match="Invalid log level"):
            LogLevel.from_string("INVALID")

    @pytest.mark.spec("SPEC-API-001")
    def test_severity_comparison(self) -> None:
        """重要度の比較ができること"""
        # DEBUG < INFO < WARNING < ERROR < CRITICAL
        assert LogLevel.DEBUG.severity < LogLevel.INFO.severity
        assert LogLevel.INFO.severity < LogLevel.WARNING.severity
        assert LogLevel.WARNING.severity < LogLevel.ERROR.severity
        assert LogLevel.ERROR.severity < LogLevel.CRITICAL.severity

        # 逆順の確認
        assert LogLevel.CRITICAL.severity > LogLevel.ERROR.severity
        assert LogLevel.ERROR.severity > LogLevel.WARNING.severity

    @pytest.mark.spec("SPEC-API-001")
    def test_is_enabled_for(self) -> None:
        """指定したレベル以上のログが有効かを判定できること"""
        # DEBUGレベルの場合、全てのログが有効
        assert LogLevel.DEBUG.is_enabled_for(LogLevel.DEBUG) is True
        assert LogLevel.INFO.is_enabled_for(LogLevel.DEBUG) is True
        assert LogLevel.WARNING.is_enabled_for(LogLevel.DEBUG) is True
        assert LogLevel.ERROR.is_enabled_for(LogLevel.DEBUG) is True
        assert LogLevel.CRITICAL.is_enabled_for(LogLevel.DEBUG) is True

        # WARNINGレベルの場合
        assert LogLevel.DEBUG.is_enabled_for(LogLevel.WARNING) is False
        assert LogLevel.INFO.is_enabled_for(LogLevel.WARNING) is False
        assert LogLevel.WARNING.is_enabled_for(LogLevel.WARNING) is True
        assert LogLevel.ERROR.is_enabled_for(LogLevel.WARNING) is True
        assert LogLevel.CRITICAL.is_enabled_for(LogLevel.WARNING) is True

        # CRITICALレベルの場合
        assert LogLevel.DEBUG.is_enabled_for(LogLevel.CRITICAL) is False
        assert LogLevel.INFO.is_enabled_for(LogLevel.CRITICAL) is False
        assert LogLevel.WARNING.is_enabled_for(LogLevel.CRITICAL) is False
        assert LogLevel.ERROR.is_enabled_for(LogLevel.CRITICAL) is False
        assert LogLevel.CRITICAL.is_enabled_for(LogLevel.CRITICAL) is True

    @pytest.mark.spec("SPEC-API-001")
    def test_all_levels(self) -> None:
        """全てのログレベルを取得できること"""
        all_levels = LogLevel.all_levels()
        assert len(all_levels) == 5
        assert LogLevel.DEBUG in all_levels
        assert LogLevel.INFO in all_levels
        assert LogLevel.WARNING in all_levels
        assert LogLevel.ERROR in all_levels
        assert LogLevel.CRITICAL in all_levels
