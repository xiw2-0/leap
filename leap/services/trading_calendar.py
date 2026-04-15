import httpx
import datetime
from typing import Dict, Optional, List, Any
import random


class TradingCalendar:
    """
    A service class to manage trading calendar data from SZSE (Shenzhen Stock Exchange).
    It caches trading days for the current month to avoid frequent API calls to SZSE.
    """

    def __init__(self):
        self.base_url = "https://www.szse.cn/api/report/exchange/onepersistenthour/monthList"
        self.headers = {
            "accept": "application/json, text/javascript, */*; q=0.01",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
            "connection": "keep-alive",
            "content-type": "application/json",
            "referer": "https://www.szse.cn/aboutus/calendar/",
            "sec-ch-ua": '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "Windows",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
            "x-request-type": "ajax",
            "x-requested-with": "XMLHttpRequest"
        }
        self.cache: Dict[str, bool] = {}
        self.current_month: Optional[str] = None

    def is_today_trading(self) -> bool:
        """
        Check if today is a trading day.

        Returns:
            True if today is a trading day, False otherwise.
        """
        today = datetime.date.today()
        today_str = today.strftime("%Y-%m-%d")

        # Check if the current month is different from the cached month
        current_month = today.strftime("%Y-%m")
        if self.current_month != current_month:
            # Need to fetch new month data
            self._update_cache_for_month(current_month)

        # Return the cached result for today, defaulting to False if not found
        return self.cache.get(today_str, False)

    def _update_cache_for_month(self, month: str) -> None:
        """
        Fetch and cache trading day data for the specified month.

        Args:
            month: Month in 'YYYY-MM' format
        """
        # Get the data for the month
        trading_days = self._fetch_month_data(month)

        # Clear the cache and update the current month
        self.cache.clear()
        self.current_month = month

        # Populate the cache with the new data
        for day_data in trading_days:
            date_str = day_data["jyrq"]
            is_trading_day = day_data["jybz"] == "1"
            self.cache[date_str] = is_trading_day

    def _fetch_month_data(self, month: str) -> List[Dict[str, Any]]:
        """
        Fetch trading day data for a specific month from SZSE API.

        Args:
            month: Month in 'YYYY-MM' format

        Returns:
            List of trading day data entries
        """
        # Generate a random value to append to the request to prevent caching
        random_val = random.random()

        params: Dict[str, Any] = {
            "month": month,
            "random": random_val
        }

        try:
            response = httpx.get(
                self.base_url,
                headers=self.headers,
                params=params,
                timeout=10.0
            )
            response.raise_for_status()

            data = response.json()
            return data.get("data", [])
        except Exception as e:
            print(
                f"Error fetching trading calendar data for month {month}: {str(e)}")
            # In case of error, return an empty list
            return []

if __name__ == "__main__":
    calendar = TradingCalendar()
    print(f"Is today a trading day? {calendar.is_today_trading()}")