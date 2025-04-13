import asyncio
import fastapi

from contextlib import asynccontextmanager
from leap.config import settings
from leap.middlewares import stats_middleware
from leap.routes import asset, push, trade, quote, stats, docs
from leap.services import push_service


@asynccontextmanager
async def lifespan(app: fastapi.FastAPI):
    # Start up
    asyncio.create_task(push_service.PushService().notify_subscribers())

    yield

    # Clean up

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
