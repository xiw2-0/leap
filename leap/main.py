import fastapi

from leap.config import settings
from leap.routes import asset, push, trade

app = fastapi.FastAPI(title=settings.PROJECT_NAME)

app.include_router(asset.router, prefix="/asset", tags=["asset"])
app.include_router(trade.router, prefix="/trade", tags=["trade"])
app.include_router(push.router, prefix="/ws", tags=["websockets"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)