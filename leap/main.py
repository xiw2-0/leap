import fastapi

from leap.config import settings
from leap.routes import asset

app = fastapi.FastAPI(title=settings.PROJECT_NAME)

app.include_router(asset.router, prefix="/asset", tags=["asset"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)