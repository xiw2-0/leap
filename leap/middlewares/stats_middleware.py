import fastapi
import time

from leap.services import stats_service
from starlette import types
from starlette.middleware import base


class StatsMiddleware(base.BaseHTTPMiddleware):

    def __init__(self, app: types.ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: fastapi.Request, call_next: base.RequestResponseEndpoint):
        start_time = time.perf_counter()

        # 调用下一个中间件或路由处理函数
        response = await call_next(request)

        process_time = time.perf_counter() - start_time
        response.headers["X-Process-Time"] = str(process_time)

        stats_service_instance: stats_service.StatsService = request.state.stats_service
        stats_service_instance.record_api_process_time(
            f"{request.method} {request.url.path}", process_time)

        return response
