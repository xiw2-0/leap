import collections
import time

from xtquant import xtconstant  # type: ignore


def calculate_percentiles(values: list[float]) -> dict[str, float]:
    """
    Calculate and return a dictionary of percentiles for a list of values.
    Returns: {Min, P25, P50, P75, P90, P95, P99, P99.9, Max}
    """
    if not values:
        return {}

    sorted_values = sorted(values)
    n = len(sorted_values)

    def get_percentile(p: float) -> float:
        # Calculate index using linear interpolation method
        rank = (p / 100.0) * (n - 1)
        lower_idx = int(rank)
        upper_idx = min(lower_idx + 1, n - 1)

        # Linear interpolation between adjacent values
        weight = rank - lower_idx
        if lower_idx == upper_idx:
            return sorted_values[lower_idx]
        else:
            return sorted_values[lower_idx] * (1 - weight) + sorted_values[upper_idx] * weight

    return {
        'min': sorted_values[0],
        'p25': get_percentile(25),
        'p50': get_percentile(50),  # median
        'p75': get_percentile(75),
        'p90': get_percentile(90),
        'p95': get_percentile(95),
        'p99': get_percentile(99),
        'p99_9': get_percentile(99.9),
        'max': sorted_values[-1]
    }


class StatsService(object):
    def __init__(self) -> None:
        self._api_stats: dict[str, list[float]] = collections.defaultdict(list)

        self._order_stats: dict[int, dict[str, float]] = {}
        self._request_id_to_request_time: dict[int, float] = {}

        self._ORDER_STATES: dict[int, str] = {
            xtconstant.ORDER_UNKNOWN: 'ORDER_UNKNOWN',

            xtconstant.ORDER_UNREPORTED: 'ORDER_UNREPORTED',
            xtconstant.ORDER_WAIT_REPORTING: 'ORDER_WAIT_REPORTING',

            xtconstant.ORDER_REPORTED: 'ORDER_REPORTED',
            xtconstant.ORDER_REPORTED_CANCEL: 'ORDER_REPORTED_CANCEL',
            xtconstant.ORDER_CANCELED: 'ORDER_CANCELED',

            xtconstant.ORDER_PART_SUCC: 'ORDER_PART_SUCCESS',
            xtconstant.ORDER_PARTSUCC_CANCEL: 'ORDER_PARTSUCC_CANCEL',
            xtconstant.ORDER_PART_CANCEL: 'ORDER_PART_CANCEL',

            xtconstant.ORDER_SUCCEEDED: 'ORDER_SUCCEEDED',

            xtconstant.ORDER_JUNK: 'ORDER_JUNK',
        }

        self._data_stats: list[float] = []  # Fixed: was incorrectly set to {}

    def clear_stats(self) -> None:
        """Clear all stored statistics data."""
        self._api_stats.clear()
        self._order_stats.clear()
        self._request_id_to_request_time.clear()
        self._data_stats.clear()

    def clear_api_stats(self) -> None:
        """Clear only API statistics data."""
        self._api_stats.clear()

    def clear_order_stats(self) -> None:
        """Clear only order statistics data."""
        self._order_stats.clear()
        self._request_id_to_request_time.clear()

    def clear_data_stats(self) -> None:
        """Clear only data statistics data."""
        self._data_stats.clear()

    def get_api_stats(self) -> dict[str, dict[str, float]]:
        return {key: calculate_percentiles(value) for key, value in self._api_stats.items()}

    def get_order_stats(self) -> dict[str, dict[str, float]]:
        order_stats: dict[str, list[float]] = collections.defaultdict(list)
        for _, order_state_time in self._order_stats.items():
            if 'REQUEST' in order_state_time and 'RESPONSE' in order_state_time:
                order_stats['REQUEST_TO_RESPONSE'].append(
                    order_state_time['RESPONSE'] - order_state_time['REQUEST'])
            if 'REQUEST' in order_state_time and 'ORDER_REPORTED' in order_state_time:
                order_stats['REQUEST_TO_REPORTED'].append(
                    order_state_time['ORDER_REPORTED'] - order_state_time['REQUEST'])
            if 'ORDER_REPORTED' in order_state_time and 'ORDER_PART_SUCCESS' in order_state_time:
                order_stats['REPORTED_TO_PART_SUCC'].append(
                    order_state_time['ORDER_PART_SUCCESS'] - order_state_time['ORDER_REPORTED'])
            if 'ORDER_REPORTED' in order_state_time and 'ORDER_SUCCEEDED' in order_state_time:
                order_stats['REPORTED_TO_SUCCEEDED'].append(
                    order_state_time['ORDER_SUCCEEDED'] - order_state_time['ORDER_REPORTED'])

        return {key: calculate_percentiles(value) for key, value in order_stats.items()}

    def get_data_stats(self) -> dict[str, float]:
        return calculate_percentiles(self._data_stats)

    def record_api_process_time(self, api_name: str, process_time: float) -> None:
        self._api_stats[api_name].append(process_time)

    def record_order_request_time(self, request_id: int | None, order_id: int | None):
        if request_id:
            self._request_id_to_request_time[request_id] = time.perf_counter()
        if order_id:
            self._order_stats[order_id] = {}
            self._order_stats[order_id]['REQUEST'] = time.perf_counter()

    def record_order_response_time(self, request_id: int, order_id: int) -> None:
        if order_id not in self._order_stats:
            self._order_stats[order_id] = {}
        self._order_stats[order_id]['REQUEST'] = self._request_id_to_request_time[request_id]
        self._order_stats[order_id]['RESPONSE'] = time.perf_counter()

    def record_order_state_time(self, order_id: int, state: int) -> None:
        if order_id not in self._order_stats:
            self._order_stats[order_id] = {}
        if state == xtconstant.ORDER_PART_SUCC and self._ORDER_STATES[state] in self._order_stats[order_id]:
            return
        self._order_stats[order_id][self._ORDER_STATES[state]
                                    ] = time.perf_counter()

    def record_data_delay(self, delays: list[float]) -> None:
        self._data_stats.extend(delays)
