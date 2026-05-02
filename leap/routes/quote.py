import fastapi
import time
from enum import Enum

from leap.models import quote
from leap.services import stats_service, sina_quote, tencent_quote, xt_whole_quote

router = fastapi.APIRouter()

TRADING_SESSIONS_SEC = [9 * 3600 + 30 * 60, 11 * 3600 +
                        30 * 60, 13 * 3600, 15 * 3600]  # 9:30-11:30, 13:00-15:00


class DataSource(str, Enum):
    XT = "xt"
    SINA = "sina"
    TENCENT = "tencent"


@router.get("/tick", summary="Get realtime tick quote from selected data source")
async def get_realtime_tick(
    request: fastapi.Request,
    stocks: list[str] = fastapi.Query(...),
    source: DataSource = fastapi.Query(
        DataSource.XT, description="Data source for quotes: xt, sina, or tencent")
) -> list[quote.Tick]:
    if source == DataSource.XT:
        xt_service: xt_whole_quote.XtWholeQuote = request.state.xt_whole_quote
        ticks = xt_service.get_tick(stocks)
    elif source == DataSource.SINA:
        sina_service: sina_quote.SinaQuote = request.state.sina_quote
        ticks = await sina_service.get_tick(stocks)
    elif source == DataSource.TENCENT:
        tencent_service: tencent_quote.TencentQuote = request.state.tencent_quote
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
        stats_svc: stats_service.StatsService = request.state.stats_service
        stats_svc.record_data_delay(
            [now_ms - tick.time for tick in ticks])
    return ticks
