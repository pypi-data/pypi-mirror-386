"""ステータスマッピングサービスのテスト

仕様書: SPEC-DOMAIN-SERVICES
"""

import pytest

from noveler.domain.exceptions import InvalidStatusError
from noveler.domain.services.status_mapping_service import StatusMappingService


class TestStatusMappingService:
    """ステータスマッピングサービスのテスト

    仕様書: SPEC-DOMAIN-SERVICES
    """

    @pytest.mark.spec("SPEC-STATUS_MAPPING_SERVICE-MAP_SHORT_TO_FULL_ST")
    def test_map_short_to_full_status(self) -> None:
        """短縮形から完全形へのマッピング"""
        service = StatusMappingService()

        assert service.to_full("未着") == "未着手"
        assert service.to_full("執筆中") == "執筆中"
        assert service.to_full("執筆済") == "執筆済み"
        assert service.to_full("推敲済") == "推敲済み"
        assert service.to_full("公開済") == "公開済み"

    @pytest.mark.spec("SPEC-STATUS_MAPPING_SERVICE-MAP_FULL_TO_SHORT_ST")
    def test_map_full_to_short_status(self) -> None:
        """完全形から短縮形へのマッピング"""
        service = StatusMappingService()

        assert service.to_short("未着手") == "未着"
        assert service.to_short("執筆中") == "執筆中"
        assert service.to_short("執筆済み") == "執筆済"
        assert service.to_short("推敲済み") == "推敲済"
        assert service.to_short("公開済み") == "公開済"

    @pytest.mark.spec("SPEC-STATUS_MAPPING_SERVICE-ALREADY_FULL_STATUS")
    def test_already_full_status(self) -> None:
        """すでに完全形の場合はそのまま返す"""
        service = StatusMappingService()

        assert service.to_full("未着手") == "未着手"
        assert service.to_full("執筆済み") == "執筆済み"
        assert service.to_full("推敲済み") == "推敲済み"
        assert service.to_full("公開済み") == "公開済み"

    @pytest.mark.spec("SPEC-STATUS_MAPPING_SERVICE-ALREADY_SHORT_STATUS")
    def test_already_short_status(self) -> None:
        """すでに短縮形の場合はそのまま返す"""
        service = StatusMappingService()

        assert service.to_short("未着") == "未着"
        assert service.to_short("執筆済") == "執筆済"
        assert service.to_short("推敲済") == "推敲済"
        assert service.to_short("公開済") == "公開済"

    @pytest.mark.spec("SPEC-STATUS_MAPPING_SERVICE-INVALID_STATUS_RAISE")
    def test_invalid_status_raises_error(self) -> None:
        """無効なステータスでエラー"""
        service = StatusMappingService()

        with pytest.raises(InvalidStatusError, match=".*"):
            service.to_full("不明")

        with pytest.raises(InvalidStatusError, match=".*"):
            service.to_short("不明")

    @pytest.mark.spec("SPEC-STATUS_MAPPING_SERVICE-IS_VALID_STATUS")
    def test_is_valid_status(self) -> None:
        """有効なステータスの判定"""
        service = StatusMappingService()

        # 短縮形
        assert service.is_valid("未着") is True
        assert service.is_valid("執筆中") is True
        assert service.is_valid("執筆済") is True
        assert service.is_valid("推敲済") is True
        assert service.is_valid("公開済") is True

        # 完全形
        assert service.is_valid("未着手") is True
        assert service.is_valid("執筆済み") is True
        assert service.is_valid("推敲済み") is True
        assert service.is_valid("公開済み") is True

        # 無効
        assert service.is_valid("不明") is False
        assert service.is_valid("") is False
        assert service.is_valid(None) is False

    @pytest.mark.spec("SPEC-STATUS_MAPPING_SERVICE-GET_ALL_STATUSES")
    def test_get_all_statuses(self) -> None:
        """全ステータスの取得"""
        service = StatusMappingService()

        short_statuses = service.get_short_statuses()
        assert set(short_statuses) == {"未着", "未着手", "執筆中", "執筆済", "推敲済", "公開済"}

        full_statuses = service.get_full_statuses()
        assert set(full_statuses) == {"未着手", "執筆中", "執筆済み", "推敲済み", "公開済み"}
