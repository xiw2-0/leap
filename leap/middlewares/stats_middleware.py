import fastapi
import time

from leap.services import stats_service
from starlette import types
from starlette.middleware import base


class StatsMiddleware(base.BaseHTTPMiddleware):

    def __init__(self, app: types.ASGIApp):
        super().__init__(app)

        self._stats_service = stats_service.StatsService()

    async def dispatch(self, request: fastapi.Request, call_next: base.RequestResponseEndpoint):
        start_time = time.perf_counter()

        # 调用下一个中间件或路由处理函数
        response = await call_next(request)

        process_time = time.perf_counter() - start_time
        response.headers["X-Process-Time"] = str(process_time)

        self._stats_service.add_api_process_time(
            f"{request.method} {request.url.path}", process_time)

        return response
