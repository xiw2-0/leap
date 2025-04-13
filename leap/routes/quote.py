import datetime as dt
import fastapi
import time
import typing

from leap.models import quote
from leap.services import stats_service
from xtquant import xtdata  # type: ignore

router = fastapi.APIRouter()


@router.post("/realtime", summary="Get realtime quote from XT Data")
def get_realtime_quote(stocks: list[str]) -> list[quote.Tick]:
    tick_dict: dict[str, dict[str, typing.Any]
                    ] = xtdata.get_full_tick(code_list=stocks)  # type: ignore
    ticks = [
        quote.Tick(
            stock_code=stock,
            time=tick['timetag'],
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

    now = time.time()
    stats_service.StatsService().record_data_delay(
        [now - dt.datetime.strptime(tick.time, "%Y%m%d %H:%M:%S").timestamp() for tick in ticks])
    return ticks
