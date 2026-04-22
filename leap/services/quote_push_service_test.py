from unittest.mock import AsyncMock, MagicMock, patch
from typing import Any

import asyncio
import unittest
import sys
import fastapi


class TestQuotePushService(unittest.TestCase):
    def setUp(self):
        # Clear the module from cache to get a fresh singleton instance
        if 'leap.services.quote_push_service' in sys.modules:
            del sys.modules['leap.services.quote_push_service']

        # Re-import to get fresh class with fresh singleton state
        from leap.services.quote_push_service import QuotePushService
        self.quote_push_service = QuotePushService()

        # Mock the event loop
        self.loop_mock = MagicMock()
        self.quote_push_service.init(self.loop_mock)

    @patch('leap.services.quote_subscriber.QuoteSubscriber')
    def test_subscribe_to_quotes_initializes_last_tick_time(self, mock_quote_subscriber_class: Any):
        """Test that subscribing to quotes initializes last tick time for new stocks"""
        # Arrange
        mock_subscriber_instance = MagicMock()
        # Simulate successful subscription
        mock_subscriber_instance.subscribe.return_value = True
        mock_quote_subscriber_class.return_value = mock_subscriber_instance

        websocket = MagicMock(spec=fastapi.WebSocket)
        stock_codes = ["000001.SZ"]

        # Act - Use the public subscribe method
        result = self.quote_push_service.subscribe_to_quotes(
            websocket, stock_codes)

        # Assert
        self.assertEqual(result, stock_codes)

        # Use the public accessor method to verify the tick time was initialized
        last_tick_time = self.quote_push_service.get_last_tick_time(
            "000001.SZ")
        self.assertIsNotNone(last_tick_time)
        self.assertEqual(last_tick_time, 0.0)

    @patch('leap.services.quote_subscriber.QuoteSubscriber')
    def test_duplicate_subscription_does_not_reset_last_tick_time(self, mock_quote_subscriber_class: Any):
        """Test that resubscribing to a stock doesn't reset the last tick time"""
        # Arrange
        mock_subscriber_instance = MagicMock()
        # Simulate successful subscription
        mock_subscriber_instance.subscribe.return_value = True
        mock_quote_subscriber_class.return_value = mock_subscriber_instance

        websocket = MagicMock(spec=fastapi.WebSocket)
        stock_codes = ["000001.SZ"]

        # First, subscribe to establish an initial tick time
        self.quote_push_service.subscribe_to_quotes(websocket, stock_codes)

        # Then simulate processing a tick to set an initial tick time
        # Use the public push method with a mock tick
        datetime_mock = MagicMock()
        quote_data: dict[str, Any] = {
            'stock_code': '000001.SZ',
            'time': 1234567890.0,  # Set a specific time
            'lastPrice': 10.5,
            'open': 10.0,
            'high': 11.0,
            'low': 9.5,
            'lastClose': 10.2,
            'amount': 100000.0,
            'volume': 10000,
            'pvolume': 10000,
            'stockStatus': 1,
            'openInt': 0,
            'lastSettlementPrice': 10.2,
            'askPrice': [10.6, 10.7],
            'bidPrice': [10.4, 10.3],
            'askVol': [100, 200],
            'bidVol': [150, 250]
        }

        # Run the async method in an event loop to set the tick time
        async def run_test():
            await self.quote_push_service.push_quote_update_from_primary(datetime_mock, quote_data)

        asyncio.run(run_test())

        # Verify that the tick time was set
        initial_time = self.quote_push_service.get_last_tick_time("000001.SZ")
        self.assertEqual(initial_time, 1234567890.0)

        # Act - resubscribe to the same stock
        result = self.quote_push_service.subscribe_to_quotes(
            websocket, stock_codes)

        # Assert
        self.assertEqual(result, stock_codes)
        # Check that the last tick time was not reset
        last_tick_time = self.quote_push_service.get_last_tick_time(
            "000001.SZ")
        self.assertEqual(last_tick_time, 1234567890.0)

    @patch('leap.services.quote_subscriber.QuoteSubscriber')
    def test_unsubscribe_removes_tick_time_entry(self, mock_quote_subscriber_class: Any):
        """Test that unsubscribing removes the tick time entry when no more connections"""
        # Arrange
        mock_subscriber_instance = MagicMock()
        # Simulate successful subscription
        mock_subscriber_instance.subscribe.return_value = True
        mock_quote_subscriber_class.return_value = mock_subscriber_instance

        websocket = MagicMock(spec=fastapi.WebSocket)
        stock_code = "000001.SZ"

        # Setup subscription using public method
        self.quote_push_service.subscribe_to_quotes(websocket, [stock_code])

        # Verify initial state using public methods
        subscribers = self.quote_push_service.get_subscribers(stock_code)
        last_tick_time = self.quote_push_service.get_last_tick_time(stock_code)
        self.assertEqual(len(subscribers), 1)
        self.assertEqual(last_tick_time, 0.0)

        # Act
        self.quote_push_service.unsubscribe_from_quotes(
            websocket, [stock_code])

        # Assert using public methods
        subscribers_after = self.quote_push_service.get_subscribers(stock_code)
        last_tick_time_after = self.quote_push_service.get_last_tick_time(
            stock_code)

        # Both the subscription and tick time entry should be removed
        self.assertEqual(len(subscribers_after), 0)
        self.assertIsNone(last_tick_time_after)

    @patch('leap.services.quote_subscriber.QuoteSubscriber')
    def test_unsubscribe_all_removes_tick_time_entries(self, mock_quote_subscriber_class: Any):
        """Test that unsubscribing from all stocks removes all tick time entries"""
        # Arrange
        mock_subscriber_instance = MagicMock()
        # Simulate successful subscription
        mock_subscriber_instance.subscribe.return_value = True
        mock_quote_subscriber_class.return_value = mock_subscriber_instance

        websocket = MagicMock(spec=fastapi.WebSocket)
        stock_code_1 = "000001.SZ"
        stock_code_2 = "600000.SH"

        # Setup subscriptions using public methods
        self.quote_push_service.subscribe_to_quotes(
            websocket, [stock_code_1, stock_code_2])

        # Verify initial state using public methods
        subscribers_1_before = self.quote_push_service.get_subscribers(
            stock_code_1)
        subscribers_2_before = self.quote_push_service.get_subscribers(
            stock_code_2)
        time_1_before = self.quote_push_service.get_last_tick_time(
            stock_code_1)
        time_2_before = self.quote_push_service.get_last_tick_time(
            stock_code_2)

        self.assertEqual(len(subscribers_1_before), 1)
        self.assertEqual(len(subscribers_2_before), 1)
        self.assertEqual(time_1_before, 0.0)
        self.assertEqual(time_2_before, 0.0)

        # Act - unsubscribe from all stocks
        self.quote_push_service.unsubscribe_from_quotes(
            websocket, [])  # Empty list means all

        # Assert using public methods
        subscribers_1_after = self.quote_push_service.get_subscribers(
            stock_code_1)
        subscribers_2_after = self.quote_push_service.get_subscribers(
            stock_code_2)
        time_1_after = self.quote_push_service.get_last_tick_time(stock_code_1)
        time_2_after = self.quote_push_service.get_last_tick_time(stock_code_2)

        # Both the subscriptions and tick time entries should be removed
        self.assertEqual(len(subscribers_1_after), 0)
        self.assertEqual(len(subscribers_2_after), 0)
        self.assertIsNone(time_1_after)
        self.assertIsNone(time_2_after)

    @patch('leap.services.stats_service.StatsService')
    @patch('leap.services.quote_subscriber.QuoteSubscriber')
    def test_push_quote_update_with_newer_time(self, mock_quote_subscriber_class: Any, mock_stats_service: Any):
        """Test that push_quote_update_async sends tick when newer than last recorded time"""
        # Arrange
        mock_subscriber_instance = MagicMock()
        mock_subscriber_instance.subscribe.return_value = True
        mock_quote_subscriber_class.return_value = mock_subscriber_instance

        datetime_mock = MagicMock()
        quote_data: dict[str, Any] = {
            'stock_code': '000001.SZ',
            'time': 1234567895.0,  # Newer than default 0.0
            'lastPrice': 10.5,
            'open': 10.0,
            'high': 11.0,
            'low': 9.5,
            'lastClose': 10.2,
            'amount': 100000.0,
            'volume': 10000,
            'pvolume': 10000,
            'stockStatus': 1,
            'openInt': 0,
            'lastSettlementPrice': 10.2,
            'askPrice': [10.6, 10.7],
            'bidPrice': [10.4, 10.3],
            'askVol': [100, 200],
            'bidVol': [150, 250]
        }

        # Subscribe to the stock to have a WebSocket connection
        websocket = AsyncMock()
        self.quote_push_service.subscribe_to_quotes(websocket, ['000001.SZ'])

        # Run the async method in an event loop
        async def run_test():
            await self.quote_push_service.push_quote_update_from_primary(datetime_mock, quote_data)

        asyncio.run(run_test())

        # Assert
        # Verify that send_text was called
        websocket.send_text.assert_called_once()
        # Verify that the last tick time was updated using the public method
        updated_time = self.quote_push_service.get_last_tick_time('000001.SZ')
        self.assertEqual(updated_time, 1234567895.0)

    @patch('leap.services.stats_service.StatsService')
    @patch('leap.services.quote_subscriber.QuoteSubscriber')
    def test_push_quote_update_with_older_time(self, mock_quote_subscriber_class: Any, mock_stats_service: Any):
        """Test that push_quote_update_async does not send tick when older than last recorded time"""
        # Arrange
        mock_subscriber_instance = MagicMock()
        mock_subscriber_instance.subscribe.return_value = True
        mock_quote_subscriber_class.return_value = mock_subscriber_instance

        datetime_mock = MagicMock()
        quote_data: dict[str, Any] = {
            'stock_code': '000001.SZ',
            'time': 1234567890.0,  # Older than the set time
            'lastPrice': 10.5,
            'open': 10.0,
            'high': 11.0,
            'low': 9.5,
            'lastClose': 10.2,
            'amount': 100000.0,
            'volume': 10000,
            'pvolume': 10000,
            'stockStatus': 1,
            'openInt': 0,
            'lastSettlementPrice': 10.2,
            'askPrice': [10.6, 10.7],
            'bidPrice': [10.4, 10.3],
            'askVol': [100, 200],
            'bidVol': [150, 250]
        }

        # Subscribe to the stock to have a WebSocket connection
        websocket = AsyncMock()
        self.quote_push_service.subscribe_to_quotes(websocket, ['000001.SZ'])

        # First, set a higher last tick time by simulating a newer tick
        newer_quote_data: dict[str, Any] = {
            'stock_code': '000001.SZ',
            'time': 1234567895.0,  # Higher time value
            'lastPrice': 10.5,
            'open': 10.0,
            'high': 11.0,
            'low': 9.5,
            'lastClose': 10.2,
            'amount': 100000.0,
            'volume': 10000,
            'pvolume': 10000,
            'stockStatus': 1,
            'openInt': 0,
            'lastSettlementPrice': 10.2,
            'askPrice': [10.6, 10.7],
            'bidPrice': [10.4, 10.3],
            'askVol': [100, 200],
            'bidVol': [150, 250]
        }

        # Run the async method in an event loop to set the initial time
        async def run_first_test():
            await self.quote_push_service.push_quote_update_from_primary(datetime_mock, newer_quote_data)

        asyncio.run(run_first_test())

        # Now run the test with the older time
        async def run_test():
            await self.quote_push_service.push_quote_update_from_primary(datetime_mock, quote_data)

        asyncio.run(run_test())

        # Assert
        # Verify that send_text was NOT called because the tick was older
        websocket.send_text.assert_called_once()  # Only called for the newer tick
        # Verify that the last tick time was NOT updated using the public method
        unchanged_time = self.quote_push_service.get_last_tick_time(
            '000001.SZ')
        self.assertEqual(unchanged_time, 1234567895.0)

    @patch('leap.services.stats_service.StatsService')
    @patch('leap.services.quote_subscriber.QuoteSubscriber')
    def test_push_quote_update_with_same_time(self, mock_quote_subscriber_class: Any, mock_stats_service: Any):
        """Test that push_quote_update_async does not send tick when same as last recorded time"""
        # Arrange
        mock_subscriber_instance = MagicMock()
        mock_subscriber_instance.subscribe.return_value = True
        mock_quote_subscriber_class.return_value = mock_subscriber_instance

        datetime_mock = MagicMock()
        quote_data: dict[str, Any] = {
            'stock_code': '000001.SZ',
            'time': 1234567895.0,  # Same as the set time
            'lastPrice': 10.5,
            'open': 10.0,
            'high': 11.0,
            'low': 9.5,
            'lastClose': 10.2,
            'amount': 100000.0,
            'volume': 10000,
            'pvolume': 10000,
            'stockStatus': 1,
            'openInt': 0,
            'lastSettlementPrice': 10.2,
            'askPrice': [10.6, 10.7],
            'bidPrice': [10.4, 10.3],
            'askVol': [100, 200],
            'bidVol': [150, 250]
        }

        # Subscribe to the stock to have a WebSocket connection
        websocket = AsyncMock()
        self.quote_push_service.subscribe_to_quotes(websocket, ['000001.SZ'])

        # First, set the tick time by processing the same tick
        async def run_first_test():
            await self.quote_push_service.push_quote_update_from_primary(datetime_mock, quote_data)

        asyncio.run(run_first_test())

        # Now try to send the same tick again
        async def run_test():
            await self.quote_push_service.push_quote_update_from_primary(datetime_mock, quote_data)

        asyncio.run(run_test())

        # Assert
        # Verify that send_text was only called once (not twice)
        websocket.send_text.assert_called_once()
        # Verify that the last tick time was NOT updated by the duplicate
        unchanged_time = self.quote_push_service.get_last_tick_time(
            '000001.SZ')
        self.assertEqual(unchanged_time, 1234567895.0)

    @patch('leap.services.quote_subscriber.QuoteSubscriber')
    def test_concurrent_access_to_tick_times(self, mock_quote_subscriber_class: Any):
        """Test that the tick time tracking works correctly with concurrent access"""
        # Arrange
        mock_subscriber_instance = MagicMock()
        # Simulate successful subscription
        mock_subscriber_instance.subscribe.return_value = True
        mock_quote_subscriber_class.return_value = mock_subscriber_instance

        # This test simulates potential race conditions in async environments
        # Though Python's GIL helps with atomic dict operations, we still want to test the logic

        # Subscribe to multiple stocks to initialize their tick times
        websocket = MagicMock(spec=fastapi.WebSocket)
        self.quote_push_service.subscribe_to_quotes(
            websocket, ['000001.SZ', '600000.SH', '000850.SZ'])

        # Verify initial state using public methods
        initial_time_1 = self.quote_push_service.get_last_tick_time(
            '000001.SZ')
        initial_time_2 = self.quote_push_service.get_last_tick_time(
            '600000.SH')
        initial_time_3 = self.quote_push_service.get_last_tick_time(
            '000850.SZ')

        # All should be initialized to 0.0
        self.assertEqual(initial_time_1, 0.0)
        self.assertEqual(initial_time_2, 0.0)
        self.assertEqual(initial_time_3, 0.0)

        # Simulate receiving ticks for different stocks
        datetime_mock = MagicMock()

        # Simulate receiving ticks for different stocks
        quote_data_1: dict[str, Any] = {
            'stock_code': '000001.SZ',
            'time': 1234567890.0,
            'lastPrice': 10.5,
            'open': 10.0,
            'high': 11.0,
            'low': 9.5,
            'lastClose': 10.2,
            'amount': 100000.0,
            'volume': 10000,
            'pvolume': 10000,
            'stockStatus': 1,
            'openInt': 0,
            'lastSettlementPrice': 10.2,
            'askPrice': [10.6, 10.7],
            'bidPrice': [10.4, 10.3],
            'askVol': [100, 200],
            'bidVol': [150, 250]
        }

        quote_data_2: dict[str, Any] = {
            'stock_code': '600000.SH',
            'time': 1234567895.0,
            'lastPrice': 15.5,
            'open': 15.0,
            'high': 16.0,
            'low': 14.5,
            'lastClose': 15.2,
            'amount': 150000.0,
            'volume': 15000,
            'pvolume': 15000,
            'stockStatus': 1,
            'openInt': 0,
            'lastSettlementPrice': 15.2,
            'askPrice': [15.6, 15.7],
            'bidPrice': [15.4, 15.3],
            'askVol': [150, 250],
            'bidVol': [175, 275]
        }

        quote_data_3: dict[str, Any] = {
            'stock_code': '000850.SZ',
            'time': 1234567900.0,
            'lastPrice': 20.5,
            'open': 20.0,
            'high': 21.0,
            'low': 19.5,
            'lastClose': 20.2,
            'amount': 200000.0,
            'volume': 20000,
            'pvolume': 20000,
            'stockStatus': 1,
            'openInt': 0,
            'lastSettlementPrice': 20.2,
            'askPrice': [20.6, 20.7],
            'bidPrice': [20.4, 20.3],
            'askVol': [200, 300],
            'bidVol': [225, 325]
        }

        # Process the initial ticks
        async def run_tests():
            await self.quote_push_service.push_quote_update_from_primary(datetime_mock, quote_data_1)
            await self.quote_push_service.push_quote_update_from_primary(datetime_mock, quote_data_2)
            await self.quote_push_service.push_quote_update_from_primary(datetime_mock, quote_data_3)

        asyncio.run(run_tests())

        # Now update the tick times for the same stocks with NEWER times
        quote_data_1_updated = quote_data_1.copy()
        # Update to NEWER than 1234567890.0
        quote_data_1_updated['time'] = 1234567892.0

        # For stock 2, we'll try to update with an OLDER time than 1234567895.0,
        # so it should not update the stored time
        quote_data_2_older = quote_data_2.copy()
        # OLDER than 1234567895.0, should not update
        quote_data_2_older['time'] = 1234567893.0

        quote_data_3_updated = quote_data_3.copy()
        # Update to NEWER than 1234567900.0
        quote_data_3_updated['time'] = 1234567905.0

        async def run_update_tests():
            await self.quote_push_service.push_quote_update_from_primary(datetime_mock, quote_data_1_updated)
            # Should not update
            await self.quote_push_service.push_quote_update_from_primary(datetime_mock, quote_data_2_older)
            await self.quote_push_service.push_quote_update_from_primary(datetime_mock, quote_data_3_updated)

        asyncio.run(run_update_tests())

        # Verify the final values using public methods
        time_1 = self.quote_push_service.get_last_tick_time(
            '000001.SZ')  # Should be updated to 1234567892.0
        # Should stay at 1234567895.0 (not updated to 1234567893.0)
        time_2 = self.quote_push_service.get_last_tick_time('600000.SH')
        time_3 = self.quote_push_service.get_last_tick_time(
            '000850.SZ')  # Should be updated to 1234567905.0

        # Verify the final values
        self.assertEqual(time_1, 1234567892.0)
        # Because 1234567893.0 < 1234567895.0, it should not update
        self.assertEqual(time_2, 1234567895.0)
        self.assertEqual(time_3, 1234567905.0)

    def test_get_max_tick_time_empty_dict_returns_zero(self):
        """Test that get_max_tick_time returns 0.0 when no tick times are recorded"""
        # Act
        max_tick_time = self.quote_push_service.get_max_tick_time()

        # Assert
        self.assertEqual(max_tick_time, 0.0)

    @patch('leap.services.quote_subscriber.QuoteSubscriber')
    def test_get_max_tick_time_single_entry(self, mock_quote_subscriber_class: Any):
        """Test that get_max_tick_time returns the correct tick time when only one exists"""
        # Arrange
        mock_subscriber_instance = MagicMock()
        mock_subscriber_instance.subscribe.return_value = True
        mock_quote_subscriber_class.return_value = mock_subscriber_instance

        # Use public methods to set up the state
        websocket = MagicMock(spec=fastapi.WebSocket)
        self.quote_push_service.subscribe_to_quotes(websocket, ['000001.SZ'])

        # Manually update the tick time by pushing a quote
        datetime_mock = MagicMock()
        quote_data: dict[str, Any] = {
            'stock_code': '000001.SZ',
            'time': 1234567890.0,
            'lastPrice': 10.5,
            'open': 10.0,
            'high': 11.0,
            'low': 9.5,
            'lastClose': 10.2,
            'amount': 100000.0,
            'volume': 10000,
            'pvolume': 10000,
            'stockStatus': 1,
            'openInt': 0,
            'lastSettlementPrice': 10.2,
            'askPrice': [10.6, 10.7],
            'bidPrice': [10.4, 10.3],
            'askVol': [100, 200],
            'bidVol': [150, 250]
        }

        # Run the async method in an event loop to set the tick time
        async def run_test():
            await self.quote_push_service.push_quote_update_from_primary(datetime_mock, quote_data)

        asyncio.run(run_test())

        # Act
        max_tick_time = self.quote_push_service.get_max_tick_time()

        # Assert
        self.assertEqual(max_tick_time, 1234567890.0)

    @patch('leap.services.quote_subscriber.QuoteSubscriber')
    def test_get_max_tick_time_multiple_entries(self, mock_quote_subscriber_class: Any):
        """Test that get_max_tick_time returns the highest tick time among multiple entries"""
        # Arrange
        mock_subscriber_instance = MagicMock()
        mock_subscriber_instance.subscribe.return_value = True
        mock_quote_subscriber_class.return_value = mock_subscriber_instance

        # Use public methods to set up the state
        websocket = MagicMock(spec=fastapi.WebSocket)
        self.quote_push_service.subscribe_to_quotes(
            websocket, ['000001.SZ', '600000.SH', '000850.SZ'])

        # Manually update the tick times by pushing quotes
        datetime_mock = MagicMock()

        quote_data_1: dict[str, Any] = {
            'stock_code': '000001.SZ',
            'time': 1234567890.0,  # Lowest time
            'lastPrice': 10.5,
            'open': 10.0,
            'high': 11.0,
            'low': 9.5,
            'lastClose': 10.2,
            'amount': 100000.0,
            'volume': 10000,
            'pvolume': 10000,
            'stockStatus': 1,
            'openInt': 0,
            'lastSettlementPrice': 10.2,
            'askPrice': [10.6, 10.7],
            'bidPrice': [10.4, 10.3],
            'askVol': [100, 200],
            'bidVol': [150, 250]
        }

        quote_data_2: dict[str, Any] = {
            'stock_code': '600000.SH',
            'time': 1234567895.0,  # Middle time
            'lastPrice': 15.5,
            'open': 15.0,
            'high': 16.0,
            'low': 14.5,
            'lastClose': 15.2,
            'amount': 150000.0,
            'volume': 15000,
            'pvolume': 15000,
            'stockStatus': 1,
            'openInt': 0,
            'lastSettlementPrice': 15.2,
            'askPrice': [15.6, 15.7],
            'bidPrice': [15.4, 15.3],
            'askVol': [150, 250],
            'bidVol': [175, 275]
        }

        quote_data_3: dict[str, Any] = {
            'stock_code': '000850.SZ',
            'time': 1234567900.0,  # Highest time
            'lastPrice': 20.5,
            'open': 20.0,
            'high': 21.0,
            'low': 19.5,
            'lastClose': 20.2,
            'amount': 200000.0,
            'volume': 20000,
            'pvolume': 20000,
            'stockStatus': 1,
            'openInt': 0,
            'lastSettlementPrice': 20.2,
            'askPrice': [20.6, 20.7],
            'bidPrice': [20.4, 20.3],
            'askVol': [200, 300],
            'bidVol': [225, 325]
        }

        # Process all the quotes
        async def run_tests():
            await self.quote_push_service.push_quote_update_from_primary(datetime_mock, quote_data_1)
            await self.quote_push_service.push_quote_update_from_primary(datetime_mock, quote_data_2)
            await self.quote_push_service.push_quote_update_from_primary(datetime_mock, quote_data_3)

        asyncio.run(run_tests())

        # Act
        max_tick_time = self.quote_push_service.get_max_tick_time()

        # Assert - Should return the highest time (1234567900.0) which is the maximum
        self.assertEqual(max_tick_time, 1234567900.0)

    @patch('leap.services.quote_subscriber.QuoteSubscriber')
    def test_get_max_tick_time_after_removing_entries(self, mock_quote_subscriber_class: Any):
        """Test that get_max_tick_time retains the highest value after removing entries"""
        # Arrange
        mock_subscriber_instance = MagicMock()
        mock_subscriber_instance.subscribe.return_value = True
        mock_quote_subscriber_class.return_value = mock_subscriber_instance

        # Use public methods to set up the state
        websocket = MagicMock(spec=fastapi.WebSocket)
        self.quote_push_service.subscribe_to_quotes(
            websocket, ['000001.SZ', '600000.SH'])

        # Manually update the tick times by pushing quotes
        datetime_mock = MagicMock()

        quote_data_1: dict[str, Any] = {
            'stock_code': '000001.SZ',
            'time': 1234567890.0,  # Lower time
            'lastPrice': 10.5,
            'open': 10.0,
            'high': 11.0,
            'low': 9.5,
            'lastClose': 10.2,
            'amount': 100000.0,
            'volume': 10000,
            'pvolume': 10000,
            'stockStatus': 1,
            'openInt': 0,
            'lastSettlementPrice': 10.2,
            'askPrice': [10.6, 10.7],
            'bidPrice': [10.4, 10.3],
            'askVol': [100, 200],
            'bidVol': [150, 250]
        }

        quote_data_2: dict[str, Any] = {
            'stock_code': '600000.SH',
            'time': 1234567895.0,  # Higher time
            'lastPrice': 15.5,
            'open': 15.0,
            'high': 16.0,
            'low': 14.5,
            'lastClose': 15.2,
            'amount': 150000.0,
            'volume': 15000,
            'pvolume': 15000,
            'stockStatus': 1,
            'openInt': 0,
            'lastSettlementPrice': 15.2,
            'askPrice': [15.6, 15.7],
            'bidPrice': [15.4, 15.3],
            'askVol': [150, 250],
            'bidVol': [175, 275]
        }

        # Process both quotes
        async def run_tests():
            await self.quote_push_service.push_quote_update_from_primary(datetime_mock, quote_data_1)
            await self.quote_push_service.push_quote_update_from_primary(datetime_mock, quote_data_2)

        asyncio.run(run_tests())

        # Verify initial max
        initial_max = self.quote_push_service.get_max_tick_time()
        self.assertEqual(initial_max, 1234567895.0)

        # Now unsubscribe from the stock with the higher tick time
        self.quote_push_service.unsubscribe_from_quotes(
            websocket, ['600000.SH'])

        # Act - Check max after removal (should still be the highest ever seen)
        max_after_removal = self.quote_push_service.get_max_tick_time()

        # Assert - Should still return the highest value ever seen (1234567895.0)
        # even though that stock was removed
        self.assertEqual(max_after_removal, 1234567895.0)

        # Unsubscribe remaining stock and verify max is still preserved
        self.quote_push_service.unsubscribe_from_quotes(
            websocket, ['000001.SZ'])
        max_when_empty = self.quote_push_service.get_max_tick_time()
        # Still preserves the max value ever seen
        self.assertEqual(max_when_empty, 1234567895.0)

    def test_get_subscribed_stocks_empty_when_no_subscriptions(self):
        """Test that get_subscribed_stocks returns an empty list when no stocks are subscribed"""
        # Act
        subscribed_stocks = self.quote_push_service.get_subscribed_stocks()

        # Assert
        self.assertEqual(subscribed_stocks, [])

    @patch('leap.services.quote_subscriber.QuoteSubscriber')
    def test_get_subscribed_stocks_returns_correct_list(self, mock_quote_subscriber_class: Any):
        """Test that get_subscribed_stocks returns the correct list of subscribed stocks"""
        # Arrange
        mock_subscriber_instance = MagicMock()
        mock_subscriber_instance.subscribe.return_value = True
        mock_quote_subscriber_class.return_value = mock_subscriber_instance

        # Use public methods to subscribe to multiple stocks
        websocket = MagicMock(spec=fastapi.WebSocket)
        stock_codes = ['000001.SZ', '600000.SH', '000850.SZ']
        self.quote_push_service.subscribe_to_quotes(websocket, stock_codes)

        # Act
        subscribed_stocks = self.quote_push_service.get_subscribed_stocks()

        # Assert
        self.assertEqual(len(subscribed_stocks), 3)
        for stock_code in stock_codes:
            self.assertIn(stock_code, subscribed_stocks)

        # Verify that it contains exactly the stocks we subscribed to
        self.assertEqual(set(subscribed_stocks), set(stock_codes))

    @patch('leap.services.quote_subscriber.QuoteSubscriber')
    def test_get_subscribed_stocks_updates_after_unsubscribe(self, mock_quote_subscriber_class: Any):
        """Test that get_subscribed_stocks reflects changes after unsubscribing"""
        # Arrange
        mock_subscriber_instance = MagicMock()
        mock_subscriber_instance.subscribe.return_value = True
        mock_quote_subscriber_class.return_value = mock_subscriber_instance

        # Subscribe to multiple stocks
        websocket = MagicMock(spec=fastapi.WebSocket)
        stock_codes = ['000001.SZ', '600000.SH', '000850.SZ']
        self.quote_push_service.subscribe_to_quotes(websocket, stock_codes)

        # Verify initial state
        initial_subscribed = self.quote_push_service.get_subscribed_stocks()
        self.assertEqual(set(initial_subscribed), set(stock_codes))

        # Act - unsubscribe from one stock
        self.quote_push_service.unsubscribe_from_quotes(
            websocket, ['600000.SH'])

        # Assert - verify the list is updated after unsubscribe
        updated_subscribed = self.quote_push_service.get_subscribed_stocks()
        expected_stocks = ['000001.SZ', '000850.SZ']
        self.assertEqual(set(updated_subscribed), set(expected_stocks))

        # Act - unsubscribe from all remaining stocks
        self.quote_push_service.unsubscribe_from_quotes(websocket, [])

        # Assert - verify empty list after unsubscribing from all
        final_subscribed = self.quote_push_service.get_subscribed_stocks()
        self.assertEqual(final_subscribed, [])


if __name__ == '__main__':
    unittest.main()
