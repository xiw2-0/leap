import asyncio
import fastapi
import logging
import typing

from contextlib import asynccontextmanager
from leap.config import settings
from leap.middlewares import stats_middleware
from leap.routes import asset, push, trade, quote, stats, docs
from leap.services import trade_push_service, quote_push_service, quote_subscriber, asset_service, sina_quote, tencent_quote, stats_service, trade_service, broker, export_reader, trade_callback
from leap.utils.logging_config import setup_logging


@asynccontextmanager
async def lifespan(app: fastapi.FastAPI) -> typing.AsyncGenerator[dict[str, typing.Any], None]:
    # Start up
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting Leap application...")

    # Instantiate services
    sina_quote_svc = sina_quote.SinaQuote()
    tencent_quote_svc = tencent_quote.TencentQuote()

    stats_svc = stats_service.StatsService()

    broker_svc = broker.XtBroker()
    asset_svc = asset_service.AssetService(broker=broker_svc)
    trade_svc = trade_service.TradeService(broker=broker_svc, export_reader=export_reader.ExportReader(), stats_service=stats_svc)   
    
    trade_push_svc = trade_push_service.TradePushService(stats_service=stats_svc)
    trade_push_svc.init(asyncio.get_event_loop())

    trade_cb = trade_callback.TradeCallback(push_service=trade_push_svc)
    broker_svc.init(trade_cb=trade_cb)
    
    quote_push_svc = quote_push_service.QuotePushService(stats_svc)
    quote_sub = quote_subscriber.QuoteSubscriber(quote_push_svc)
    quote_push_svc.init(asyncio.get_event_loop(), quote_sub)

    yield {
        'asset_service': asset_svc,
        'sina_quote': sina_quote_svc,
        'tencent_quote': tencent_quote_svc,
        'stats_service': stats_svc,
        'trade_service': trade_svc,
        'trade_push_service': trade_push_svc,
        'quote_push_service': quote_push_svc,
    }

    # Clean up
    logger.info("Shutting down Leap application...")

app = fastapi.FastAPI(
    title=settings.PROJECT_NAME,
    docs_url=None,
    default_response_class=fastapi.responses.ORJSONResponse,
    lifespan=lifespan,
)

app.add_middleware(stats_middleware.StatsMiddleware)

app.include_router(asset.router, prefix="/asset", tags=["asset"])
app.include_router(trade.router, prefix="/trade", tags=["trade"])
app.include_router(quote.router, prefix="/quote", tags=["quote"])
app.include_router(stats.router, prefix="/stats", tags=["stats"])
app.include_router(push.router, prefix="/ws", tags=["websockets"])
app.include_router(docs.router, tags=["docs"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)