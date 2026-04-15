import fastapi
import time
import typing
from enum import Enum

from leap.models import quote
from leap.services import stats_service, sina_quote, tencent_quote
from xtquant import xtdata  # type: ignore

router = fastapi.APIRouter()

TRADING_SESSIONS_SEC = [9 * 3600 + 30 * 60, 11 * 3600 +
                        30 * 60, 13 * 3600, 15 * 3600]  # 9:30-11:30, 13:00-15:00


class DataSource(str, Enum):
    XT = "xt"
    SINA = "sina"
    TENCENT = "tencent"


@router.get("/tick", summary="Get realtime tick quote from selected data source")
async def get_realtime_quote(
    stocks: list[str] = fastapi.Query(...),
    source: DataSource = fastapi.Query(
        DataSource.XT, description="Data source for quotes: xt, sina, or tencent")
) -> list[quote.Tick]:
    if source == DataSource.XT:
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
    elif source == DataSource.SINA:
        sina_service = sina_quote.SinaQuote()
        ticks = await sina_service.get_tick(stocks)
    elif source == DataSource.TENCENT:
        tencent_service = tencent_quote.TencentQuote()
        ticks = await tencent_service.get_tick(stocks)
    else:
        # This should never happen due to enum validation
        raise fastapi.HTTPException(
            status_code=400, detail="Invalid data source")

    # Record only when in trading sessions (9:30-11:30, 13:00-15:00)
    localtime = time.localtime()
    localtime_sec = localtime.tm_hour * 3600 + \
        localtime.tm_min * 60 + localtime.tm_sec
    if TRADING_SESSIONS_SEC[0] <= localtime_sec <= TRADING_SESSIONS_SEC[1] or TRADING_SESSIONS_SEC[2] <= localtime_sec <= TRADING_SESSIONS_SEC[3]:
        now_ms = time.time() * 1000
        stats_service.StatsService().record_data_delay(
            [now_ms - tick.time for tick in ticks])
    return ticks
