import unittest
from unittest.mock import patch, MagicMock

from leap.services import stats_service


class TestStatsService(unittest.TestCase):

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

        # Should have percentiles for each API endpoint
        self.assertIn("GET /test", result)
        self.assertIn("POST /orders", result)

        # Verify that percentiles are present for GET /test
        self.assertIn('p50', result["GET /test"])
        # For [0.1, 0.2], the interpolated median should be 0.15
        self.assertAlmostEqual(result["GET /test"]['p50'], 0.15, places=1)

        # Verify that percentiles are present for POST /orders
        self.assertIn('p50', result["POST /orders"])
        self.assertAlmostEqual(result["POST /orders"]['p50'], 0.5)

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
        # Need 3 calls: 1 for request_id_time, 1 for order_request_time, 1 for response_time
        # Request ID 123 stores time 100.0
        # Order ID 456 initially gets time 101.0 in its REQUEST slot
        # But then in record_order_response_time, it gets replaced with request_id time (100.0)
        # Response time is 100.5
        # So REQUEST_TO_RESPONSE = 100.5 - 100.0 = 0.5
        mock_perf_counter.side_effect = [100.0, 101.0, 100.5]

        # Record request time (this makes 2 calls to time.perf_counter)
        service.record_order_request_time(123, 456)

        # Record response time (this makes 1 call to time.perf_counter)
        service.record_order_response_time(123, 456)

        # Get order stats
        result = service.get_order_stats()

        # Should have REQUEST_TO_RESPONSE time with percentiles
        self.assertIn('REQUEST_TO_RESPONSE', result)
        self.assertIn('p50', result['REQUEST_TO_RESPONSE'])
        self.assertAlmostEqual(
            result['REQUEST_TO_RESPONSE']['p50'], 0.5, places=1)

    @patch('leap.services.stats_service.time.perf_counter')
    def test_record_multiple_order_request_and_response_times(self, mock_perf_counter: MagicMock) -> None:
        """Test recording multiple order request and response times to get meaningful percentiles."""
        service = stats_service.StatsService()

        # Mock time.perf_counter to return enough predictable values
        # Format: [req_id_time, order_req_time, response_time for each order]
        # Order 1: req_id_time=100.0, temp_order_time=100.1, final_req_time=100.0, response_time=100.5 => diff=0.5
        # Order 2: req_id_time=200.0, temp_order_time=200.1, final_req_time=200.0, response_time=201.0 => diff=1.0
        # Order 3: req_id_time=300.0, temp_order_time=300.1, final_req_time=300.0, response_time=302.0 => diff=2.0
        mock_perf_counter.side_effect = [
            100.0, 100.1, 100.5,    # First order: request_id_time, order_request_time, response_time
            200.0, 200.1, 201.0,    # Second order: request_id_time, order_request_time, response_time
            300.0, 300.1, 302.0     # Third order: request_id_time, order_request_time, response_time
        ]

        # Record first order
        service.record_order_request_time(1, 101)
        service.record_order_response_time(1, 101)

        # Record second order
        service.record_order_request_time(2, 102)
        service.record_order_response_time(2, 102)

        # Record third order
        service.record_order_request_time(3, 103)
        service.record_order_response_time(3, 103)

        # Get order stats
        result = service.get_order_stats()

        # Should have REQUEST_TO_RESPONSE time with percentiles
        self.assertIn('REQUEST_TO_RESPONSE', result)
        self.assertIn('p50', result['REQUEST_TO_RESPONSE'])
        self.assertIn('min', result['REQUEST_TO_RESPONSE'])
        self.assertIn('max', result['REQUEST_TO_RESPONSE'])
        self.assertIn('p90', result['REQUEST_TO_RESPONSE'])

        # Times: [0.5, 1.0, 2.0]
        # median should be 1.0
        self.assertAlmostEqual(
            result['REQUEST_TO_RESPONSE']['p50'], 1.0, places=1)
        self.assertAlmostEqual(
            result['REQUEST_TO_RESPONSE']['min'], 0.5, places=1)
        self.assertAlmostEqual(
            result['REQUEST_TO_RESPONSE']['max'], 2.0, places=1)

    def test_get_data_stats_empty(self) -> None:
        """Test get_data_stats when no data delays have been recorded."""
        service = stats_service.StatsService()
        # Should handle empty list gracefully
        result = service.get_data_stats()
        self.assertEqual(result, {})

    def test_record_and_get_data_stats(self) -> None:
        """Test recording and retrieving data delays."""
        service = stats_service.StatsService()

        # Record data delays
        service.record_data_delay([0.01, 0.02, 0.03])
        service.record_data_delay([0.04, 0.05])

        # Get data stats
        result = service.get_data_stats()

        # Should have percentiles: values [0.01, 0.02, 0.03, 0.04, 0.05], median is 0.03
        self.assertIn('p50', result)
        self.assertAlmostEqual(result['p50'], 0.03)

    def test_clear_stats(self) -> None:
        """Test clearing all stats."""
        service = stats_service.StatsService()

        # Record some data
        service.record_api_process_time("GET /test", 0.1)
        service.record_order_request_time(None, 123)
        service.record_data_delay([0.01, 0.02])

        # Verify data exists
        api_stats = service.get_api_stats()
        self.assertGreater(len(api_stats), 0)

        # Clear stats
        service.clear_stats()

        # Verify all stats are cleared
        api_stats = service.get_api_stats()
        self.assertEqual(len(api_stats), 0)

        # Check internal structures are empty by checking all stat types are empty
        self.assertEqual(len(service.get_api_stats()), 0)
        self.assertEqual(len(service.get_order_stats()), 0)
        self.assertEqual(service.get_data_stats(), {})

    def test_clear_api_stats(self) -> None:
        """Test clearing only API stats."""
        service = stats_service.StatsService()

        # Record various types of data
        service.record_api_process_time("GET /test", 0.1)

        # Record a complete order flow to ensure order stats exist
        service.record_order_request_time(456, 789)  # request_id, order_id
        # Creates REQUEST_TO_RESPONSE stat
        service.record_order_response_time(456, 789)
        service.record_data_delay([0.01, 0.02])

        # Verify all types of data exist
        self.assertGreater(len(service.get_api_stats()), 0)
        # Should have REQUEST_TO_RESPONSE stat
        self.assertGreater(len(service.get_order_stats()), 0)
        self.assertGreater(service.get_data_stats()['p50'], 0.0)

        # Clear only API stats
        service.clear_api_stats()

        # Verify only API stats are cleared
        self.assertEqual(len(service.get_api_stats()), 0)  # API stats cleared
        self.assertGreater(len(service.get_order_stats()),
                           0)  # Order stats still there
        # Data stats still there
        self.assertGreater(service.get_data_stats()['p50'], 0.0)

    def test_clear_order_stats(self) -> None:
        """Test clearing only order stats."""
        service = stats_service.StatsService()

        # Record various types of data
        service.record_api_process_time("GET /test", 0.1)

        # Record a complete order flow to ensure order stats exist
        service.record_order_request_time(456, 789)  # request_id, order_id
        # Creates REQUEST_TO_RESPONSE stat
        service.record_order_response_time(456, 789)
        service.record_data_delay([0.01, 0.02])

        # Verify all types of data exist
        self.assertGreater(len(service.get_api_stats()), 0)
        # Should have REQUEST_TO_RESPONSE stat
        self.assertGreater(len(service.get_order_stats()), 0)
        self.assertGreater(service.get_data_stats()['p50'], 0.0)

        # Clear only order stats
        service.clear_order_stats()

        # Verify only order stats are cleared
        self.assertGreater(len(service.get_api_stats()),
                           0)  # API stats still there
        self.assertEqual(len(service.get_order_stats()),
                         0)  # Order stats cleared
        # Data stats still there
        self.assertGreater(service.get_data_stats()['p50'], 0.0)

        # Internal structures for orders should be empty - verify through public methods
        self.assertEqual(len(service.get_order_stats()), 0)

    def test_clear_data_stats(self) -> None:
        """Test clearing only data stats."""
        service = stats_service.StatsService()

        # Record various types of data
        service.record_api_process_time("GET /test", 0.1)
        service.record_order_request_time(None, 123)
        service.record_data_delay([0.01, 0.02])

        # Verify all types of data exist
        self.assertGreater(len(service.get_api_stats()), 0)
        # Add a state to make sure get_order_stats returns something
        service.record_order_state_time(123, 50)
        self.assertGreater(len(service.get_order_stats()), 0)
        self.assertGreater(service.get_data_stats()['p50'], 0.0)

        # Clear only data stats
        service.clear_data_stats()

        # Verify only data stats are cleared
        self.assertGreater(len(service.get_api_stats()),
                           0)  # API stats still there
        self.assertGreater(len(service.get_order_stats()),
                           0)     # Order stats still there
        self.assertEqual(service.get_data_stats(), {}
                         )      # Data stats cleared

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

        # Should have REPORTED_TO_PART_SUCC and REPORTED_TO_SUCCEEDED times with percentiles
        self.assertIn('REPORTED_TO_PART_SUCC', result)
        self.assertIn('REPORTED_TO_SUCCEEDED', result)
        self.assertIn('p50', result['REPORTED_TO_PART_SUCC'])
        self.assertIn('p50', result['REPORTED_TO_SUCCEEDED'])
        # REPORTED_TO_PART_SUCC: 201.0 - 200.0 = 1.0
        self.assertAlmostEqual(
            result['REPORTED_TO_PART_SUCC']['p50'], 1.0)
        # REPORTED_TO_SUCCEEDED: 202.0 - 200.0 = 2.0
        self.assertAlmostEqual(
            result['REPORTED_TO_SUCCEEDED']['p50'], 2.0)

    @patch('leap.services.stats_service.time.perf_counter')
    def test_record_order_state_time_part_succ_duplicate(self, mock_perf_counter: MagicMock) -> None:
        """Test that PART_SUCC state is not recorded twice for the same order."""
        service = stats_service.StatsService()

        # Use actual xtquant constant value
        ORDER_REPORTED = 50
        ORDER_PART_SUCC = 55

        # Mock time.perf_counter
        mock_perf_counter.side_effect = [300.0, 301.0, 302.0]

        service.record_order_state_time(999, ORDER_REPORTED)
        # Record PART_SUCC state twice
        service.record_order_state_time(999, ORDER_PART_SUCC)
        service.record_order_state_time(999, ORDER_PART_SUCC)

        # Get order stats to indirectly verify only one PART_SUCC entry was kept
        result = service.get_order_stats()
        self.assertAlmostEqual(
            result['REPORTED_TO_PART_SUCC']['p50'], 1.0)


if __name__ == '__main__':
    unittest.main()
