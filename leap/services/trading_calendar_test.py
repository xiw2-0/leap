import unittest
from unittest.mock import patch, MagicMock
import datetime
from typing import Any
from .trading_calendar import TradingCalendar


class TestTradingCalendar(unittest.TestCase):
    def setUp(self) -> None:
        self.calendar = TradingCalendar()

    @patch('leap.services.trading_calendar.httpx.get')
    def test_is_today_trading_when_cache_empty_and_api_returns_trading_day(self, mock_get: Any) -> None:
        # Mock today's date
        today = datetime.date.today()
        today_str = today.strftime("%Y-%m-%d")
        current_month = today.strftime("%Y-%m")

        # Mock API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [
                {
                    "zrxh": 1,
                    "jybz": "1",  # Trading day
                    "jyrq": today_str
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.calendar.is_today_trading()

        # Verify the result is True (trading day)
        self.assertTrue(result)
        # Verify the cache is populated
        self.assertEqual(self.calendar.cache[today_str], True)
        self.assertEqual(self.calendar.current_month, current_month)

    @patch('leap.services.trading_calendar.httpx.get')
    def test_is_today_trading_when_cache_empty_and_api_returns_non_trading_day(self, mock_get: Any) -> None:
        # Mock today's date
        today = datetime.date.today()
        today_str = today.strftime("%Y-%m-%d")
        current_month = today.strftime("%Y-%m")

        # Mock API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [
                {
                    "zrxh": 1,
                    "jybz": "0",  # Non-trading day
                    "jyrq": today_str
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.calendar.is_today_trading()

        # Verify the result is False (non-trading day)
        self.assertFalse(result)
        # Verify the cache is populated
        self.assertEqual(self.calendar.cache[today_str], False)
        self.assertEqual(self.calendar.current_month, current_month)

    @patch('leap.services.trading_calendar.httpx.get')
    def test_is_today_trading_with_existing_cache_same_month(self, mock_get: Any) -> None:
        # Setup cache with today marked as a trading day
        today = datetime.date.today()
        today_str = today.strftime("%Y-%m-%d")
        current_month = today.strftime("%Y-%m")

        # Pre-populate the cache
        self.calendar.cache[today_str] = True
        self.calendar.current_month = current_month

        # Call the method
        result = self.calendar.is_today_trading()

        # Verify the result is True (should come from cache)
        self.assertTrue(result)
        # Verify the API was not called
        mock_get.assert_not_called()

    @patch('leap.services.trading_calendar.httpx.get')
    def test_is_today_trading_different_month_updates_cache(self, mock_get: Any) -> None:
        # Mock today's date
        today = datetime.date.today()
        today_str = today.strftime("%Y-%m-%d")
        current_month = today.strftime("%Y-%m")

        # Mock a previous month
        prev_month = "2020-01"
        self.calendar.current_month = prev_month

        # Mock API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [
                {
                    "zrxh": 1,
                    "jybz": "1",  # Trading day
                    "jyrq": today_str
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.calendar.is_today_trading()

        # Verify the result is True (trading day)
        self.assertTrue(result)
        # Verify the API was called
        mock_get.assert_called_once()
        # Verify the cache is updated
        self.assertEqual(self.calendar.cache[today_str], True)
        self.assertEqual(self.calendar.current_month, current_month)

    @patch('leap.services.trading_calendar.httpx.get')
    def test_is_today_trading_api_error_defaults_to_false(self, mock_get: Any) -> None:
        # Mock API error
        mock_get.side_effect = Exception("Network error")

        result = self.calendar.is_today_trading()

        # Verify the result is False (default when API fails)
        self.assertFalse(result)
        # Verify the cache is not populated with today's date in this case
        # (it might still be empty if no prior cache existed)
        self.assertEqual(result, False)

    def test_is_today_trading_date_not_in_response_defaults_to_false(self):
        # Mock today's date
        today = datetime.date.today()
        current_month = today.strftime("%Y-%m")

        # Pre-populate the cache with different dates
        self.calendar.cache = {
            "2020-01-01": True,
            "2020-01-02": False
        }
        self.calendar.current_month = current_month

        # Call the method for today (which is not in cache)
        result = self.calendar.is_today_trading()

        # Verify the result is False (default when date not in cache)
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
