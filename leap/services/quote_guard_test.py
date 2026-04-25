from leap.services.quote_guard import QuoteGuard
from leap.services.stats_service import StatsService
from unittest.mock import AsyncMock, MagicMock

import datetime
import unittest


class TestQuoteGuard(unittest.TestCase):
    def setUp(self):
        self.mock_logger = MagicMock()
        self.mock_trading_calendar = MagicMock()
        self.mock_tencent_quote = MagicMock()
        self.mock_quote_push_service = MagicMock()
        self.stats_service = StatsService()  # Add the stats service

        self.quote_guard = QuoteGuard(
            work_sleep=1.0,
            latency_threshold=2.0,
            tencent_quote=self.mock_tencent_quote,
            quote_push_service=self.mock_quote_push_service,
            trading_calendar=self.mock_trading_calendar,
            stats_service=self.stats_service  # Pass the stats service
        )

    def test_is_guard_time_morning_session(self):
        """Test that morning session time is recognized as guard time"""
        # Test morning session start
        self.assertTrue(self.quote_guard.is_guard_time(
            datetime.time(9, 30)))
        # Test during morning session
        self.assertTrue(self.quote_guard.is_guard_time(
            datetime.time(10, 30)))
        # Test morning session end
        self.assertTrue(self.quote_guard.is_guard_time(
            datetime.time(11, 30)))

    def test_is_guard_time_afternoon_session(self):
        """Test that afternoon session time is recognized as guard time"""
        # Test afternoon session start
        self.assertTrue(self.quote_guard.is_guard_time(
            datetime.time(13, 0)))
        # Test during afternoon session
        self.assertTrue(self.quote_guard.is_guard_time(
            datetime.time(14, 30)))
        # Test afternoon session end
        self.assertTrue(self.quote_guard.is_guard_time(
            datetime.time(15, 0)))

    def test_is_guard_time_non_guard_periods(self):
        """Test that non-guard periods are not recognized as guard time"""
        # Test before morning session
        self.assertFalse(self.quote_guard.is_guard_time(
            datetime.time(8, 30)))
        # Test between sessions
        self.assertFalse(self.quote_guard.is_guard_time(
            datetime.time(12, 0)))
        # Test after afternoon session
        self.assertFalse(self.quote_guard.is_guard_time(
            datetime.time(15, 31)))

    def test_is_working_time_within_range(self):
        """Test that working time periods are correctly identified"""
        # Test start of working time
        self.assertTrue(self.quote_guard.is_working_time(
            datetime.time(9, 0)))
        # Test middle of working time
        self.assertTrue(self.quote_guard.is_working_time(
            datetime.time(12, 0)))
        # Test end of working time
        self.assertTrue(self.quote_guard.is_working_time(
            datetime.time(15, 30)))

    def test_is_working_time_outside_range(self):
        """Test that non-working time periods are correctly identified"""
        # Test before working time
        self.assertFalse(self.quote_guard.is_working_time(
            datetime.time(8, 59)))
        # Test after working time
        self.assertFalse(self.quote_guard.is_working_time(
            datetime.time(15, 31)))

    async def test_guard_method_stale_data_fetches_backup(self):
        """Test that guard fetches backup data when primary data is stale"""
        # Arrange
        self.mock_quote_push_service.get_max_tick_time.return_value = 1000.0  # Very old time
        self.mock_quote_push_service.get_subscribed_stocks.return_value = [
            "000001.SZ", "600000.SH"]

        mock_tick1 = MagicMock()
        mock_tick1.stock_code = "000001.SZ"
        mock_tick1.time = 1234567890000.0
        mock_tick2 = MagicMock()
        mock_tick2.stock_code = "600000.SH"
        mock_tick2.time = 1234567890000.0

        self.mock_tencent_quote.get_tick = AsyncMock(
            return_value=[mock_tick1, mock_tick2])
        self.mock_quote_push_service.push_quote_update_from_backup = AsyncMock()

        # Act
        await self.quote_guard.guard()

        # Assert
        # Verify that backup quotes were fetched
        self.mock_tencent_quote.get_tick.assert_called_once_with(
            ["000001.SZ", "600000.SH"])
        # Verify that backup push was called for each tick
        self.assertEqual(
            self.mock_quote_push_service.push_quote_update_from_backup.call_count, 2)

        # Verify that quote guard stats were recorded
        final_stats = self.stats_service.get_quote_guard_stats()
        final_total = final_stats["total"]
        self.assertEqual(final_total, 1)

    async def test_guard_method_fresh_data_no_backup(self):
        """Test that guard does not fetch backup data when primary data is fresh"""
        # Arrange
        # Set max tick time to be recent (within threshold)
        current_time_ms = 1234567890000.0
        threshold_ms = (3 + self.quote_guard.latency_threshold) * \
            1000  # 5 seconds in ms
        recent_time = current_time_ms - \
            (threshold_ms - 1000)  # Just under threshold
        self.mock_quote_push_service.get_max_tick_time.return_value = recent_time
        self.mock_quote_push_service.get_subscribed_stocks.return_value = [
            "000001.SZ"]

        # Get initial stats
        initial_stats = self.stats_service.get_quote_guard_stats()
        initial_total = initial_stats["total"]

        # Act
        await self.quote_guard.guard()

        # Assert
        # Verify that backup quotes were NOT fetched
        self.mock_tencent_quote.get_tick.assert_not_called()

        # Verify that quote guard stats were not recorded since guard wasn't activated
        final_stats = self.stats_service.get_quote_guard_stats()
        final_total = final_stats["total"]
        self.assertEqual(final_total, initial_total)

    async def test_guard_method_empty_subscriptions(self):
        """Test that guard handles case with no subscribed stocks"""
        # Arrange
        self.mock_quote_push_service.get_max_tick_time.return_value = 1000.0  # Very old time
        self.mock_quote_push_service.get_subscribed_stocks.return_value = []  # No subscriptions

        # Act
        await self.quote_guard.guard()

        # Assert
        # Verify that backup quotes were NOT fetched because there are no subscriptions
        self.mock_tencent_quote.get_tick.assert_not_called()

        # Verify that quote guard stats were recorded (guard was activated but no stocks to update)
        final_stats = self.stats_service.get_quote_guard_stats()
        final_total = final_stats["total"]
        self.assertEqual(final_total, 1)


if __name__ == '__main__':
    import unittest
    unittest.main()
