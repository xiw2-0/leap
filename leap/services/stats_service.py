import collections

from leap.utils import singleton


@singleton.singleton
class StatsService(object):
    def __init__(self) -> None:
        self._api_stats: dict[str, list[float]] = collections.defaultdict(list)

    def add_api_process_time(self, api_name: str, process_time: float) -> None:
        self._api_stats[api_name].append(process_time)

    def get_api_stats(self) -> dict[str, float]:
        return {key: sum(value) / len(value) for key, value in self._api_stats.items()}
