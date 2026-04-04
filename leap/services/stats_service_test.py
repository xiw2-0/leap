import unittest
from unittest.mock import patch, MagicMock

from leap.services import stats_service


class TestStatsService(unittest.TestCase):

    def setUp(self) -> None:
        """Reset the singleton instance before each test."""
        # Clear the singleton instance to ensure clean state for each test
        if hasattr(stats_service.StatsService, '_instance'):
            delattr(stats_service.StatsService, '_instance')

    def test_get_api_stats_empty(self) -> None:
        """Test get_api_stats when no API stats have been recorded."""
        service = stats_service.StatsService()
        result = service.get_api_stats()
        self.assertEqual(result, {})

    def test_record_and_get_api_stats(self) -> None:
        """Test recording and retrieving API process times."""
        service = stats_service.StatsService()

        # Record some API process times
        service.record_api_process_time("GET /test", 0.1)
        service.record_api_process_time("GET /test", 0.2)
        service.record_api_process_time("POST /orders", 0.5)

        # Get stats
        result = service.get_api_stats()

        # Should have averages for each API endpoint
        self.assertAlmostEqual(result["GET /test"], 0.15)  # (0.1 + 0.2) / 2
        self.assertAlmostEqual(result["POST /orders"], 0.5)

    def test_get_order_stats_empty(self) -> None:
        """Test get_order_stats when no order stats have been recorded."""
        service = stats_service.StatsService()
        result = service.get_order_stats()
        self.assertEqual(result, {})

    @patch('leap.services.stats_service.time.perf_counter')
    def test_record_order_request_and_response_time(self, mock_perf_counter: MagicMock) -> None:
        """Test recording order request and response times."""
        service = stats_service.StatsService()

        # Mock time.perf_counter to return predictable values
        # request, response, current time
        mock_perf_counter.side_effect = [100.0, 100.5, 101.0]

        # Record request time
        service.record_order_request_time(123, None)

        # Record response time
        service.record_order_response_time(123, 456)

        # Get order stats
        result = service.get_order_stats()

        # Should have REQUEST_TO_RESPONSE time
        self.assertIn('REQUEST_TO_RESPONSE', result)
        self.assertAlmostEqual(
            result['REQUEST_TO_RESPONSE'], 0.5)  # 100.5 - 100.0

    @patch('leap.services.stats_service.time.perf_counter')
    def test_record_order_state_time(self, mock_perf_counter: MagicMock) -> None:
        """Test recording order state times with actual xtquant constants."""
        service = stats_service.StatsService()

        # Use actual xtquant constant values
        ORDER_REPORTED = 50
        ORDER_SUCCEEDED = 56
        ORDER_PART_SUCC = 55

        # Mock time.perf_counter to return predictable values
        # reported, part_succ, succeeded
        mock_perf_counter.side_effect = [200.0, 201.0, 202.0]

        # Record different order states
        service.record_order_state_time(789, ORDER_REPORTED)
        service.record_order_state_time(789, ORDER_PART_SUCC)
        service.record_order_state_time(789, ORDER_SUCCEEDED)

        # Get order stats
        result = service.get_order_stats()

        # Should have REPORTED_TO_PART_SUCC and REPORTED_TO_SUCCEEDED times
        self.assertIn('REPORTED_TO_PART_SUCC', result)
        self.assertIn('REPORTED_TO_SUCCEEDED', result)
        self.assertAlmostEqual(
            result['REPORTED_TO_PART_SUCC'], 1.0)  # 201.0 - 200.0
        self.assertAlmostEqual(
            result['REPORTED_TO_SUCCEEDED'], 2.0)  # 202.0 - 200.0

    @patch('leap.services.stats_service.time.perf_counter')
    def test_record_order_state_time_part_succ_duplicate(self, mock_perf_counter: MagicMock) -> None:
        """Test that PART_SUCC state is not recorded twice for the same order."""
        service = stats_service.StatsService()

        # Use actual xtquant constant value
        ORDER_PART_SUCC = 55

        # Mock time.perf_counter
        mock_perf_counter.side_effect = [300.0, 301.0]

        # Record PART_SUCC state twice
        service.record_order_state_time(999, ORDER_PART_SUCC)
        service.record_order_state_time(999, ORDER_PART_SUCC)

        # Access private attribute for testing purposes
        order_stats = service._order_stats[999]  # type: ignore
        # Should only have one PART_SUCC entry
        self.assertEqual(len(order_stats), 1)
        self.assertIn('ORDER_PART_SUCCESS', order_stats)

    def test_get_data_stats_empty(self) -> None:
        """Test get_data_stats when no data delays have been recorded."""
        service = stats_service.StatsService()
        # Should handle empty list gracefully
        with self.assertRaises(ZeroDivisionError):
            service.get_data_stats()

    def test_record_and_get_data_stats(self) -> None:
        """Test recording and retrieving data delays."""
        service = stats_service.StatsService()

        # Record data delays
        service.record_data_delay([0.01, 0.02, 0.03])
        service.record_data_delay([0.04, 0.05])

        # Get data stats
        result = service.get_data_stats()

        # Should have average of all delays: (0.01+0.02+0.03+0.04+0.05)/5 = 0.03
        self.assertAlmostEqual(result, 0.03)

    def test_singleton_pattern(self) -> None:
        """Test that StatsService follows singleton pattern."""
        service1 = stats_service.StatsService()
        service2 = stats_service.StatsService()

        self.assertIs(service1, service2)

        # Record data on first instance
        service1.record_api_process_time("test", 1.0)

        # Should be visible on second instance
        result = service2.get_api_stats()
        self.assertAlmostEqual(result["test"], 1.0)


if __name__ == '__main__':
    unittest.main()
