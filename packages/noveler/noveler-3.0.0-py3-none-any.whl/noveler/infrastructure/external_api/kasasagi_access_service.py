"""KASASAGI APIを使用したアクセスデータサービス実装"""

import time
from datetime import datetime

import requests

from noveler.domain.analysis.entities import EpisodeAccess
from noveler.domain.analysis.services import AccessDataService
from noveler.domain.analysis.value_objects import DateRange, PageView, UniqueUser
from noveler.domain.value_objects.project_time import ProjectTimezone
from noveler.domain.writing.value_objects import EpisodeNumber


class KasasagiAccessService(AccessDataService):
    """KASASAGI APIを使用したアクセスデータ取得サービス"""

    def __init__(self, user_agent: str) -> None:
        self.user_agent = user_agent
        self.base_url = "https://kasasagi.hinaproject.com/access/top/ncode/"
        self.headers = {
            "User-Agent": self.user_agent,
        }
        self.request_interval = 1.0  # API利用規約に準拠

    def fetch_episode_access(self, ncode: str, date_range: DateRange) -> list[EpisodeAccess]:
        """エピソードのアクセスデータを取得"""
        try:
            # APIリクエスト
            url = ncode.get_kasasagi_url()
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()

            # レート制限対策
            time.sleep(self.request_interval)

            # JSONデータをパース
            data = response.json()

            # エピソードアクセス情報に変換
            episode_accesses = []
            for item in data.get("items", []):
                access = self._convert_to_episode_access(item)
                if access and self._should_include(access, date_range):
                    episode_accesses.append(access)

            return episode_accesses

        except requests.RequestException as e:
            # エラーハンドリング
            msg = f"KASASAGI APIへのアクセスに失敗しました: {e!s}"
            raise ValueError(msg) from e

    def fetch_daily_access(self, ncode: str, target_date: datetime) -> dict[int, EpisodeAccess]:
        """特定日のアクセスデータを取得"""
        date_range = DateRange(target_date, target_date)
        accesses = self.fetch_episode_access(ncode, date_range)

        # エピソード番号でインデックス化
        result = {}
        for access in accesses:
            if access.episode_number:
                result[access.episode_number.value] = access

        return result

    def is_data_available(self, ncode: str) -> bool:
        """データが利用可能かチェック"""
        try:
            url = ncode.get_kasasagi_url()
            response = requests.head(url, headers=self.headers, timeout=10)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def _convert_to_episode_access(self, raw_data: dict) -> EpisodeAccess | None:
        """生データをEpisodeAccessに変換"""
        try:
            # エピソード番号の抽出
            episode_num = raw_data.get("episode_number")
            if not episode_num:
                return None

            episode_number = EpisodeNumber(int(episode_num))

            # アクセスデータの抽出
            pv = raw_data.get("page_views", 0)
            uu = raw_data.get("unique_users", 0)

            # 日付の解析
            date_str = raw_data.get("date")
            access_date = None
            if date_str:
                jst = ProjectTimezone.jst().timezone
                access_date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=jst).date()

            return EpisodeAccess(
                episode_number=episode_number,
                date=access_date,
                page_views=PageView(pv) if pv >= 0 else None,
                unique_users=UniqueUser(uu) if uu >= 0 else None,
            )

        except (ValueError, KeyError):
            return None

    def _should_include(self, access: EpisodeAccess, date_range: DateRange | None) -> bool:
        """アクセスデータを含めるべきかチェック"""
        if not date_range:
            return True

        if not access.date:
            return False

        return date_range.contains(access.date)
