from leap.models import quote
from xtquant import xtdata  # type: ignore

import typing


class XtWholeQuote:
    """
    Service class to handle getting full tick data from XT quant system.
    """

    def get_tick(self, stocks: list[str]) -> list[quote.Tick]:
        """
        Get tick data for specified stocks from XT data source.

        Args:
            stocks: List of stock codes to get tick data for

        Returns:
            List of Tick objects containing the market data
        """
        tick_dict: dict[str, dict[str, typing.Any]] = xtdata.get_full_tick(  # type: ignore
            code_list=stocks)

        ticks = [
            quote.Tick(
                stock_code=stock,
                time=tick['time'],
                last_price=tick['lastPrice'],
                open=tick['open'],
                high=tick['high'],
                low=tick['low'],
                last_close=tick["lastClose"],
                amount=tick["amount"],
                volume=tick["volume"],
                pvolume=tick["pvolume"],
                stock_status=tick["stockStatus"],
                open_int=tick["openInt"],
                last_settlement_price=tick["lastSettlementPrice"],
                ask_prices=tick["askPrice"],
                bid_prices=tick["bidPrice"],
                ask_vols=tick["askVol"],
                bid_vols=tick["bidVol"],
            ) for stock, tick in tick_dict.items()
        ]

        return ticks
