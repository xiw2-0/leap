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

    def test_get_quote_guard_stats_empty(self) -> None:
        """Test get_quote_guard_stats when no quote guard times have been recorded."""
        service = stats_service.StatsService()
        result = service.get_quote_guard_stats()

        # Should return total 0 and empty list for top 3 minutes
        self.assertEqual(result["total"], 0)
        # Adding type assertion for type checker
        top_3_minutes = result["top_3_minutes"]
        assert isinstance(top_3_minutes, list)
        self.assertEqual(len(top_3_minutes), 0)

    @patch('leap.services.stats_service.datetime')
    def test_record_and_get_quote_guard_stats_single_minute(self, mock_datetime: MagicMock) -> None:
        """Test recording and retrieving quote guard times for a single minute."""
        service = stats_service.StatsService()

        # Mock datetime.now() to return a fixed time
        mock_datetime.now.return_value.strftime.return_value = "10:30"

        # Record a quote guard time
        service.record_quote_guard_time()

        # Get quote guard stats
        result = service.get_quote_guard_stats()

        # Should have total 1 and one entry in top 3 minutes
        self.assertEqual(result["total"], 1)
        # Adding type assertion for type checker
        top_3_minutes = result["top_3_minutes"]
        assert isinstance(top_3_minutes, list)
        self.assertEqual(len(top_3_minutes), 1)
        self.assertEqual(top_3_minutes[0][0], "10:30")  # The minute string
        self.assertEqual(top_3_minutes[0][1], 1)        # The count

    @patch('leap.services.stats_service.datetime')
    def test_record_and_get_quote_guard_stats_multiple_minutes(self, mock_datetime: MagicMock) -> None:
        """Test recording and retrieving quote guard times for multiple minutes."""
        service = stats_service.StatsService()

        # Mock datetime.now() to return different fixed times
        # We'll record times for three different minutes with different counts
        times = ["10:30", "11:45", "10:30", "12:15", "11:45", "10:30"]

        # Create a mock for now() that will return a mock object with strftime
        # Each call to now().strftime("%H:%M") will return the next time in sequence
        strftime_mock = MagicMock()
        strftime_mock.strftime.side_effect = times
        mock_datetime.now.return_value = strftime_mock

        # Record quote guard times:
        # "10:30" appears 3 times
        # "11:45" appears 2 times
        # "12:15" appears 1 time
        service.record_quote_guard_time()  # 10:30
        service.record_quote_guard_time()  # 11:45
        service.record_quote_guard_time()  # 10:30
        service.record_quote_guard_time()  # 12:15
        service.record_quote_guard_time()  # 11:45
        service.record_quote_guard_time()  # 10:30

        # Get quote guard stats
        result = service.get_quote_guard_stats()

        # Total should be 6
        self.assertEqual(result["total"], 6)

        # Top 3 minutes should be ordered by count (descending)
        # Adding type assertion for type checker
        top_3_minutes = result["top_3_minutes"]
        assert isinstance(top_3_minutes, list)
        # Should have 3 entries since we have 3 distinct minutes
        self.assertEqual(len(top_3_minutes), 3)

        # The minute "10:30" should have the highest count (3)
        self.assertEqual(top_3_minutes[0][0], "10:30")
        self.assertEqual(top_3_minutes[0][1], 3)

        # The minute "11:45" should have count (2)
        self.assertEqual(top_3_minutes[1][0], "11:45")
        self.assertEqual(top_3_minutes[1][1], 2)

        # The minute "12:15" should have count (1)
        self.assertEqual(top_3_minutes[2][0], "12:15")
        self.assertEqual(top_3_minutes[2][1], 1)

    @patch('leap.services.stats_service.datetime')
    def test_record_and_get_quote_guard_stats_top_3_limit(self, mock_datetime: MagicMock) -> None:
        """Test that get_quote_guard_stats only returns top 3 minutes even if more exist."""
        service = stats_service.StatsService()

        # Simulate having multiple calls with controlled time values
        # We'll control the time format calls by providing a sequence
        time_calls = [
            # First set of different minutes
            "09:00", "09:01", "09:02", "09:03", "09:04", "09:05",
            # Second set to increase counts
            "09:00", "09:01", "09:02",
            "09:00", "09:01",                                       # Third set
            "09:00"                                                 # Final increment to 09:00
        ]

        # Create a mock for now() that will return a mock object with strftime
        # Each call to now().strftime("%H:%M") will return the next time in sequence
        strftime_mock = MagicMock()
        strftime_mock.strftime.side_effect = time_calls
        mock_datetime.now.return_value = strftime_mock

        # Record all the quote guard times according to our time sequence
        for _ in range(len(time_calls)):
            service.record_quote_guard_time()

        # Get quote guard stats
        result = service.get_quote_guard_stats()

        # Total should equal the length of our time_calls array
        self.assertEqual(result["total"], len(time_calls))  # Should be 13

        # Adding type assertion for type checker
        top_3_minutes = result["top_3_minutes"]
        assert isinstance(top_3_minutes, list)
        # Should only return top 3 minutes even though we have 6 distinct minutes
        self.assertEqual(len(top_3_minutes), 3)

        # Check the counts for each minute:
        # "09:00" appears 4 times (at indices 0, 6, 9, 12)
        # "09:01" appears 3 times (at indices 1, 7, 10)
        # "09:02" appears 2 times (at indices 2, 8)
        # "09:03", "09:04", "09:05" appear 1 time each

        # Create a dictionary for easier lookup
        minute_counts = {minute: count for minute, count in top_3_minutes}

        # The top 3 should be 09:00 (4), 09:01 (3), and 09:02 (2)
        self.assertEqual(minute_counts["09:00"], 4)
        self.assertEqual(minute_counts["09:01"], 3)
        self.assertEqual(minute_counts["09:02"], 2)

    def test_clear_quote_guard_stats(self) -> None:
        """Test clearing only quote guard stats."""
        service = stats_service.StatsService()

        # Record some quote guard times
        with patch('leap.services.stats_service.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "10:30"
            service.record_quote_guard_time()
            service.record_quote_guard_time()

        # Verify quote guard stats exist
        result_before = service.get_quote_guard_stats()
        self.assertEqual(result_before["total"], 2)
        # Adding type assertion for type checker
        top_3_minutes_before = result_before["top_3_minutes"]
        assert isinstance(top_3_minutes_before, list)
        self.assertEqual(len(top_3_minutes_before), 1)

        # Clear only quote guard stats
        service.clear_quote_guard_stats()

        # Verify only quote guard stats are cleared
        result_after = service.get_quote_guard_stats()
        self.assertEqual(result_after["total"], 0)
        # Adding type assertion for type checker
        top_3_minutes_after = result_after["top_3_minutes"]
        assert isinstance(top_3_minutes_after, list)
        self.assertEqual(len(top_3_minutes_after), 0)

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

    def test_clear_stats_includes_quote_guard_stats(self) -> None:
        """Test that clearing all stats also clears quote guard stats."""
        service = stats_service.StatsService()

        # Record some quote guard times
        with patch('leap.services.stats_service.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "10:30"
            service.record_quote_guard_time()

        # Verify quote guard stats exist
        result_before = service.get_quote_guard_stats()
        self.assertEqual(result_before["total"], 1)

        # Clear all stats
        service.clear_stats()

        # Verify quote guard stats are also cleared
        result_after = service.get_quote_guard_stats()
        self.assertEqual(result_after["total"], 0)

    def test_clear_stats(self) -> None:
        """Test clearing all stats."""
        service = stats_service.StatsService()

        # Record some data
        service.record_api_process_time("GET /test", 0.1)
        service.record_order_request_time(None, 123)
        service.record_data_delay([0.01, 0.02])

        # Record quote guard data
        with patch('leap.services.stats_service.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "10:30"
            service.record_quote_guard_time()

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
        self.assertEqual(service.get_quote_guard_stats()["total"], 0)

    def test_clear_api_stats_does_not_affect_quote_guard_stats(self) -> None:
        """Test that clearing API stats does not affect quote guard stats."""
        service = stats_service.StatsService()

        # Record both API and quote guard stats
        with patch('leap.services.stats_service.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "10:30"
            service.record_quote_guard_time()

        service.record_api_process_time("GET /test", 0.1)

        # Verify both exist
        quote_result_before = service.get_quote_guard_stats()
        api_result_before = service.get_api_stats()
        self.assertEqual(quote_result_before["total"], 1)
        self.assertIn("GET /test", api_result_before)

        # Clear only API stats
        service.clear_api_stats()

        # Verify quote guard stats still exist but API stats are cleared
        quote_result_after = service.get_quote_guard_stats()
        api_result_after = service.get_api_stats()
        self.assertEqual(quote_result_after["total"], 1)
        self.assertEqual(api_result_after, {})

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

        # Record quote guard data
        with patch('leap.services.stats_service.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "10:30"
            service.record_quote_guard_time()

        # Verify all types of data exist
        self.assertGreater(len(service.get_api_stats()), 0)
        # Should have REQUEST_TO_RESPONSE stat
        self.assertGreater(len(service.get_order_stats()), 0)
        self.assertGreater(service.get_data_stats()['p50'], 0.0)
        self.assertEqual(service.get_quote_guard_stats()["total"], 1)

        # Clear only API stats
        service.clear_api_stats()

        # Verify only API stats are cleared
        self.assertEqual(len(service.get_api_stats()), 0)  # API stats cleared
        self.assertGreater(len(service.get_order_stats()),
                           0)  # Order stats still there
        # Data stats still there
        self.assertGreater(service.get_data_stats()['p50'], 0.0)
        # Quote guard stats still there
        self.assertEqual(service.get_quote_guard_stats()["total"], 1)

    def test_clear_order_stats_does_not_affect_quote_guard_stats(self) -> None:
        """Test that clearing order stats does not affect quote guard stats."""
        service = stats_service.StatsService()

        # Record both order and quote guard stats
        with patch('leap.services.stats_service.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "10:30"
            service.record_quote_guard_time()

        service.record_order_request_time(123, 456)

        # Verify both exist
        quote_result_before = service.get_quote_guard_stats()
        self.assertEqual(quote_result_before["total"], 1)
        # Note: get_order_stats might return empty dict if no complete flow is recorded
        # but internal structures should be populated

        # Clear only order stats
        service.clear_order_stats()

        # Verify quote guard stats still exist but order stats are cleared
        quote_result_after = service.get_quote_guard_stats()
        order_result_after = service.get_order_stats()
        self.assertEqual(quote_result_after["total"], 1)
        self.assertEqual(order_result_after, {})

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

        # Record quote guard data
        with patch('leap.services.stats_service.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "10:30"
            service.record_quote_guard_time()

        # Verify all types of data exist
        self.assertGreater(len(service.get_api_stats()), 0)
        # Should have REQUEST_TO_RESPONSE stat
        self.assertGreater(len(service.get_order_stats()), 0)
        self.assertGreater(service.get_data_stats()['p50'], 0.0)
        self.assertEqual(service.get_quote_guard_stats()["total"], 1)

        # Clear only order stats
        service.clear_order_stats()

        # Verify only order stats are cleared
        self.assertGreater(len(service.get_api_stats()),
                           0)  # API stats still there
        self.assertEqual(len(service.get_order_stats()),
                         0)  # Order stats cleared
        # Data stats still there
        self.assertGreater(service.get_data_stats()['p50'], 0.0)
        # Quote guard stats still there
        self.assertEqual(service.get_quote_guard_stats()["total"], 1)

        # Internal structures for orders should be empty - verify through public methods
        self.assertEqual(len(service.get_order_stats()), 0)

    def test_clear_data_stats_does_not_affect_quote_guard_stats(self) -> None:
        """Test that clearing data stats does not affect quote guard stats."""
        service = stats_service.StatsService()

        # Record both data and quote guard stats
        with patch('leap.services.stats_service.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "10:30"
            service.record_quote_guard_time()

        service.record_data_delay([0.01, 0.02])

        # Verify both exist
        quote_result_before = service.get_quote_guard_stats()
        data_result_before = service.get_data_stats()
        self.assertEqual(quote_result_before["total"], 1)
        self.assertIn('p50', data_result_before)

        # Clear only data stats
        service.clear_data_stats()

        # Verify quote guard stats still exist but data stats are cleared
        quote_result_after = service.get_quote_guard_stats()
        data_result_after = service.get_data_stats()
        self.assertEqual(quote_result_after["total"], 1)
        self.assertEqual(data_result_after, {})

    def test_clear_data_stats(self) -> None:
        """Test clearing only data stats."""
        service = stats_service.StatsService()

        # Record various types of data
        service.record_api_process_time("GET /test", 0.1)
        service.record_order_request_time(None, 123)
        service.record_data_delay([0.01, 0.02])

        # Record quote guard data
        with patch('leap.services.stats_service.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "10:30"
            service.record_quote_guard_time()

        # Verify all types of data exist
        self.assertGreater(len(service.get_api_stats()), 0)
        # Add a state to make sure get_order_stats returns something
        service.record_order_state_time(123, 50)
        self.assertGreater(len(service.get_order_stats()), 0)
        self.assertGreater(service.get_data_stats()['p50'], 0.0)
        self.assertEqual(service.get_quote_guard_stats()["total"], 1)

        # Clear only data stats
        service.clear_data_stats()

        # Verify only data stats are cleared
        self.assertGreater(len(service.get_api_stats()),
                           0)  # API stats still there
        self.assertGreater(len(service.get_order_stats()),
                           0)     # Order stats still there
        self.assertEqual(service.get_data_stats(), {}
                         )      # Data stats cleared
        # Quote guard stats still there
        self.assertEqual(service.get_quote_guard_stats()["total"], 1)

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
