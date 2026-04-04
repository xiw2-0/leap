import collections
import time

from leap.utils import singleton
from xtquant import xtconstant  # type: ignore


@singleton.singleton
class StatsService(object):
    def __init__(self) -> None:
        self._api_stats: dict[str, list[float]] = collections.defaultdict(list)

        self._order_stats: dict[int, dict[str, float]] = {}
        self._request_id_to_request_time: dict[int, float] = {}

        self._ORDER_STATES = {
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

        self._data_stats: list[float] = []

    def get_api_stats(self) -> dict[str, float]:
        return {key: sum(value) / len(value) for key, value in self._api_stats.items()}

    def get_order_stats(self) -> dict[str, float]:
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

        return {key: sum(value) / len(value) for key, value in order_stats.items()}

    def get_data_stats(self) -> float:
        return sum(self._data_stats) / len(self._data_stats)

    def record_api_process_time(self, api_name: str, process_time: float) -> None:
        self._api_stats[api_name].append(process_time)

    def record_order_request_time(self, request_id: int | None, order_id: int | None):
        if request_id:
            self._request_id_to_request_time[request_id] = time.perf_counter()
        if order_id:
            self._order_stats[order_id] = {}
            self._order_stats[order_id]['REQUEST'] = time.perf_counter()

    def record_order_response_time(self, request_id: int, order_id: int):
        if order_id not in self._order_stats:
            self._order_stats[order_id] = {}
        self._order_stats[order_id]['REQUEST'] = self._request_id_to_request_time[request_id]
        self._order_stats[order_id]['RESPONSE'] = time.perf_counter()

    def record_order_state_time(self, order_id: int, state: int):
        if order_id not in self._order_stats:
            self._order_stats[order_id] = {}
        if state == xtconstant.ORDER_PART_SUCC and self._ORDER_STATES[state] in self._order_stats[order_id]:
            return
        self._order_stats[order_id][self._ORDER_STATES[state]
                                    ] = time.perf_counter()

    def record_data_delay(self, delays: list[float]):
        self._data_stats.extend(delays)