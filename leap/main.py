import asyncio
import fastapi
import logging

from contextlib import asynccontextmanager
from leap.config import settings
from leap.middlewares import stats_middleware
from leap.routes import asset, push, trade, quote, stats, docs
from leap.services import push_service
from leap.utils.logging_config import setup_logging


@asynccontextmanager
async def lifespan(app: fastapi.FastAPI):
    # Start up
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting Leap application...")
    
    asyncio.create_task(push_service.PushService().notify_subscribers())

    yield

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